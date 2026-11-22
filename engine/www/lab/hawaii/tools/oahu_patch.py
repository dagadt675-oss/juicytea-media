#!/usr/bin/env python3
"""oahu_patch.py --spec SPEC --out DATA_DIR --dl DL_DIR [--only NAME,NAME] [--keep]
A nested detail patch over a coarse parent, for an island seen from 5-70 km (ep02 'oahu_windward' in 'oahu_nuuanu', 2026-11-15:
s030-s041 pull back from the Pali and look across O'ahu, where the parent's 101 m texels drew 5-18 px each: melted Ko'olau cliffs,
smeared Kailua and Kane'ohe). detail_bake.py does patches with 3DEP land heights and a full-grid fuse; at this size its colour fuse
needs about 8 GB and 3DEP has no sea floor, so the coast would meet the parent's 101 m coast. Here:
  heights  NOAA NCEI coastal DEM (detail.height.source 'ncei:DATASET', topo-bathy, the parent's own source) on land and out to
           near_m from the coast, faded to the parent's heights (bicubic) by far_m, and to the parent at the grid edge (feather_m):
           the coast comes from one seamless grid and the open sea floor stays the parent's (drained-ocean shots, s034-s037).
  AO       its own (HBAO, rb.bake_ao) where the heights are its own, the parent's AO (bicubic) elsewhere, so the drained sea floor
           shades the same inside and outside the patch.
  colour   the parent's colour (bicubic) as the reference; USDA NAIP (NOAA Digital Coast 9668) read at the overview just finer than
           the texel, detail transfer on land as detail_bake.fuse (one luminance gain and one chroma factor for the whole patch,
           measured on a coarse pass, so tiles of 1024 texels carry no seams); the sea keeps the parent's colour.
  cres     0.6 m where the photo is used, the parent's texel elsewhere (the shader's detail texturing then matches the parent's on
           the sea floor), detail_bake's smooth rule, the edge fade.
Untrusted downloads: run with python -I. Needs rasterio (GDAL /vsicurl)."""
import sys, os, json, math, time, shutil, argparse
TOOLS = os.environ.get('HAWAII_TOOLS') or os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
import numpy as np
from PIL import Image
from scipy import ndimage
import region_bake as rb
import detail_bake as db

def LOG(*a): print(*a, flush=True)
def grid_size(bb, long_):
    kx, ky = db.px_size(bb, 1, 1); ar = kx / ky
    return (long_, max(8, int(round(long_ / ar)))) if ar >= 1 else (max(8, int(round(long_ * ar))), long_)

def photo_ndwi(mask, bb, W, H, px_m, hit):
  """NDWI (green - NIR) / (green + NIR) of the NAIP quads on the height grid, read only over the bounding boxes of mask's dilated
  components, at the overview just finer than the height texel; NaN where no photo."""
  import rasterio
  from rasterio.vrt import WarpedVRT
  from rasterio.enums import Resampling
  from rasterio.transform import from_bounds
  from rasterio.windows import Window
  zl, zn = ndimage.label(ndimage.binary_dilation(mask, iterations=3)); TRh = from_bounds(*bb, W, H); ndwi = np.full((H, W), np.nan, np.float32)
  for sl in ndimage.find_objects(zl):
      if sl is None: continue
      r0, r1, c0, c1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
      g_ = [bb[0] + c0 / W * (bb[2] - bb[0]), bb[3] - r1 / H * (bb[3] - bb[1]), bb[0] + c1 / W * (bb[2] - bb[0]), bb[3] - r0 / H * (bb[3] - bb[1])]
      for q in hit:
          qb = q['bbox']
          if qb[0] > g_[2] or qb[2] < g_[0] or qb[1] > g_[3] or qb[3] < g_[1]: continue
          href = '/vsicurl/' + q['href']
          with rasterio.open(href) as base: ovs = base.overviews(1); res0 = base.res[0]
          lvl = max([k for k, fct in enumerate(ovs) if res0 * fct * 1.5 <= px_m] or [-1])
          with rasterio.open(href, **({} if lvl < 0 else dict(overview_level=lvl))) as d_, \
               WarpedVRT(d_, crs='EPSG:4326', transform=TRh, width=W, height=H, resampling=Resampling.average, src_nodata=0, nodata=0) as vv:
              t = vv.read([2, 4], window=Window(c0, r0, c1 - c0, r1 - r0)).astype(np.float32)
          sub_ = ndwi[r0:r1, c0:c1]; ok = (t > 0).all(0) & ~np.isfinite(sub_)
          sub_[ok] = ((t[0] - t[1]) / np.maximum(t[0] + t[1], 1.0))[ok]
  return ndwi

def photo_land(fine, zcfg, bb, W, H, px_m, hit):
  """The NCEI fills to low land where the photo is not water; returns (fine, km2 of the zero fill made land, km2 of shallow cells made land)."""
  v = np.isfinite(fine); k2 = px_m * px_m / 1e6; thr = zcfg.get('ndwi_water', 0.15); land_m = zcfg.get('land_m', 1.0)
  zf = v & (np.abs(fine) < 0.05)
  sh = np.zeros_like(zf); shm = zcfg.get('shallow_m', 0)
  if shm > 0:
      ddeep = ndimage.distance_transform_edt(~(v & (fine < -1.0))) * px_m
      sh = v & (fine > -shm) & (fine <= -0.05) & (ddeep > zcfg.get('sep_m', 150.0))
  ndwi = photo_ndwi(zf | sh, bb, W, H, px_m, hit)
  wat = ndimage.median_filter(np.nan_to_num(ndwi, nan=9.0), size=3)
  zland = zf & (wat < thr)
  LOG(f'  zero fill: {float(zf.sum()) * k2:.1f} km2 at exactly 0 m; the photo shows land on {float(zland.sum()) * k2:.1f} km2 (now {land_m} m), '
      f'water on {float((zf & (wat >= thr) & (wat < 8)).sum()) * k2:.1f} km2, no photo on {float((zf & (wat >= 8)).sum()) * k2:.1f} km2')
  sland = np.zeros_like(zf)
  if shm > 0:
      cand = sh & (wat < zcfg.get('shallow_ndwi', thr)); land = (v & (fine > 0.5)) | zland
      lab, n = ndimage.label(cand | land); keep = np.zeros(n + 1, bool); keep[np.unique(lab[land])] = True; keep[0] = False
      sland = cand & keep[lab]
      LOG(f'  shallow fill: {float(sh.sum()) * k2:.1f} km2 at -{shm}..-0.05 m and over {zcfg.get("sep_m", 150.0):.0f} m from water deeper than 1 m; '
          f'the photo shows land on {float(cand.sum()) * k2:.1f} km2, {float(sland.sum()) * k2:.1f} km2 of it joins land (now {land_m} m)')
  fine = fine.copy(); fine[zland | sland] = land_m
  return fine, float(zland.sum()) * k2, float(sland.sum()) * k2

def bake(R, A):
  t0 = time.time()
  name = R['name']; bb = [float(x) for x in R['bbox']]; P = R['patch']; det = R['detail']; hc, cc = det['height'], det['colour']
  dl = f'{A.dl}/{name}_patch'; od = f'{A.out}/{name}'; os.makedirs(dl, exist_ok=True); os.makedirs(od, exist_ok=True)
  pm = json.load(open(f'{A.out}/{P["parent"]}/meta.json')); pbb = pm['bbox']
  if not (bb[0] >= pbb[0] and bb[1] >= pbb[1] and bb[2] <= pbb[2] and bb[3] <= pbb[3]): raise SystemExit(f'{name} is not inside {P["parent"]}')
  W, H = grid_size(bb, hc.get('long', 4096)); pxw, pxh = db.px_size(bb, W, H); px_m = (pxw + pxh) / 2
  LOG(f'== {name} (patch in {P["parent"]}) bbox {bb}: heights {W}x{H} ({px_m:.1f} m)')
  # ---------- heights
  ph = db.read_h16(f'{A.out}/{P["parent"]}/{pm["files"]["h16"]}', pm.get('hmin', rb.HMIN), pm.get('hrange', rb.HRANGE))
  base_h = db.resample_bb(ph, pbb, bb, W, H, order=3); del ph
  ds = hc['source'].split(':', 1)[1]; tdeg = (bb[2] - bb[0]) / W; fine = np.full((H, W), np.nan, np.float32); ncei_d = None
  nx = hc.get('pieces', 2)
  for k in range(nx):   # in lon strips (each under region_bake.ncei's 30 Mpx cap at full resolution)
      a0 = bb[0] + (bb[2] - bb[0]) * k / nx; a1 = bb[0] + (bb[2] - bb[0]) * (k + 1) / nx; sub = [a0 - 0.002, bb[1], a1 + 0.002, bb[3]]
      p = rb.ncei(ds, sub, dl, tdeg)
      if p is None: continue
      ncei_d = p['d']; a = rb.sample(p, bb, W, H, order=1 if p['d'] <= tdeg * 1.5 else 3); m = np.isfinite(a) & ~np.isfinite(fine); fine[m] = a[m]; del p, a
  import rasterio
  from rasterio.vrt import WarpedVRT
  from rasterio.enums import Resampling
  from rasterio.transform import from_bounds
  from rasterio.windows import Window
  items = db.naip_items(dl)   # cached as A.dl/naip_hi_2021_items.json
  hit = [q for q in items.values() if q['bbox'][0] < bb[2] and q['bbox'][2] > bb[0] and q['bbox'][1] < bb[3] and q['bbox'][3] > bb[1]]
  hit.sort(key=lambda q: (abs(int(q['date'][5:7]) + int(q['date'][8:10]) / 31 - 6.6), q['date']))   # highest sun first (as detail_bake.naip)
  env = rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif', GDAL_HTTP_MAX_RETRY='5', GDAL_HTTP_RETRY_DELAY='3',
                     VSI_CACHE='TRUE', VSI_CACHE_SIZE=128 << 20, GDAL_CACHEMAX=512)
  env.__enter__()
  # the grid's fills: NCEI filled ground it had no source for with exactly 0 m (Kailua town and Kailua Bay, the south of Kane'ohe
  # Bay, Pearl Harbor's lochs: about 43 km2) and, in Kailua town, with flat blocks a few decimetres below 0 m; the stage draws both
  # as sea level, so a town reads as a flooded flat with rectangular ponds. The photo decides (photo_land): where NAIP is not water,
  # the exact-zero fill becomes low land (zero_fill.land_m); the shallow cells (zero_fill.shallow_m below 0 m, at least sep_m from
  # water deeper than 1 m) do too, but only where they join land, so surf and sand bars on the reef stay sea.
  zcfg = hc.get('zero_fill'); zf_land = sh_land = 0
  if zcfg:
      fine, zf_land, sh_land = photo_land(fine, zcfg, bb, W, H, px_m, hit)
  v = np.isfinite(fine); cover = float(v.mean())
  land = v & (fine > 0.5)
  d_sea = ndimage.distance_transform_edt(~land) * px_m
  near_m, far_m = hc.get('near_m', 250.0), hc.get('far_m', 800.0)
  w = np.where(land, 1.0, 1.0 - db.sstep(near_m, far_m, d_sea)).astype(np.float32) * rb.feather(v, 3)
  h = base_h * (1 - w) + np.nan_to_num(fine) * w; del fine
  fm = P.get('feather_m', 600); e = db.edge_ramp(H, W, int(round(fm / px_m))); h = (base_h * (1 - e) + h * e).astype(np.float32); w = w * e
  h[(h > 0) & (h < 1)] = 1.0
  la0, la1 = float((base_h > 0.5).mean()), float((h > 0.5).mean())
  dsea = np.abs(h - base_h)[d_sea > far_m + 50]; LOG(f'  ncei {ds} {ncei_d * 3600 if ncei_d else 0:.2f}" cover {cover * 100:.1f} %; land {la0 * 100:.2f} % of the grid in the parent, '
      f'{la1 * 100:.2f} % now; |h - parent| beyond {far_m:.0f} m offshore: max {float(dsea.max()) if dsea.size else 0:.3f} m')
  if dsea.size and float(dsea.max()) > 1.0: raise SystemExit(f'{name}: sea floor changed beyond far_m')
  im16, hmin, hrange = db.pack16_tight(h); im16.save(f'{od}/h16.png', compress_level=6); del im16
  # ---------- AO
  f = 2 if W * H > 2.5e6 else 1; aw, ah = W // f, H // f
  h2 = np.asarray(Image.fromarray(h, 'F').resize((aw, ah), Image.BOX)) if f > 1 else h
  ao = rb.bake_ao(h2, bb, px_m * f, True); del h2
  pa = np.asarray(Image.open(f'{A.out}/{P["parent"]}/{pm["files"]["ao"]}')).astype(np.float32) / 255
  if pa.ndim == 3: pa = pa[..., 0]
  pao = db.resample_bb(pa, pbb, bb, aw, ah, order=3); wa = np.asarray(Image.fromarray(w.astype(np.float32), 'F').resize((aw, ah), Image.BILINEAR))
  ao = pao * (1 - wa) + ao * wa; Image.fromarray((np.clip(ao, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{od}/ao.png'); del ao, pao, pa
  LOG(f'  heights {h.min():.0f}..{h.max():.0f} m, AO {aw}x{ah} ({time.time() - t0:.0f} s)')
  # ---------- colour
  CW, CH = grid_size(bb, cc.get('long', 4096)); cpx = sum(db.px_size(bb, CW, CH)) / 2
  pcol = np.asarray(Image.open(f'{A.out}/{P["parent"]}/{pm["files"]["color"]}').convert('RGB')).astype(np.float32) / 255
  pcs = [ndimage.spline_filter(pcol[..., k], order=3) for k in range(3)]; PH, PW = pcol.shape[:2]; del pcol
  ref_m = max(pm.get('res', {}).get('colour_src_m', 30.0), pm.get('res', {}).get('colour_texel_m', pm['px_m']))
  s = max(1.0, 0.5 * ref_m / cpx)
  def geo(x0, y0, x1, y1, w_, h_): return [bb[0] + x0 / w_ * (bb[2] - bb[0]), bb[3] - y1 / h_ * (bb[3] - bb[1]), bb[0] + x1 / w_ * (bb[2] - bb[0]), bb[3] - y0 / h_ * (bb[3] - bb[1])]
  def ref_tile(x0, y0, x1, y1):
      lons, lats = rb.grid_axes(geo(x0, y0, x1, y1, CW, CH), x1 - x0, y1 - y0)
      RY, CX = np.meshgrid((pbb[3] - lats) / (pbb[3] - pbb[1]) * PH - 0.5, (lons - pbb[0]) / (pbb[2] - pbb[0]) * PW - 0.5, indexing='ij')
      return np.clip(np.stack([ndimage.map_coordinates(c, [RY, CX], order=3, mode='nearest', prefilter=False) for c in pcs], -1), 0, 1).astype(np.float32)
  def h_tile(x0, y0, x1, y1):
      lons, lats = rb.grid_axes(geo(x0, y0, x1, y1, CW, CH), x1 - x0, y1 - y0)
      RY, CX = np.meshgrid((bb[3] - lats) / (bb[3] - bb[1]) * H - 0.5, (lons - bb[0]) / (bb[2] - bb[0]) * W - 0.5, indexing='ij')
      return ndimage.map_coordinates(h, [RY, CX], order=1, mode='nearest').astype(np.float32)
  TR = from_bounds(*bb, CW, CH); quads = []
  for q in hit:
      href = '/vsicurl/' + q['href']
      with rasterio.open(href) as base:
          ovs = base.overviews(1); lvl = -1
          for k, fct in enumerate(ovs):
              if base.res[0] * fct * 1.5 <= cpx: lvl = k
          rres = base.res[0] * (ovs[lvl] if lvl >= 0 else 1)
      ds_ = rasterio.open(href, **({} if lvl < 0 else dict(overview_level=lvl)))
      quads.append(dict(q=q, ds=ds_, vrt=WarpedVRT(ds_, crs='EPSG:4326', transform=TR, width=CW, height=CH, resampling=Resampling.average, src_nodata=0, nodata=0), rres=rres, nov=len(ovs)))
  LOG(f'  naip: {len(quads)} quarter quads over the patch, read at {quads[0]["rres"]:.1f} m for {cpx:.2f} m texels')
  def naip_tile(x0, y0, x1, y1):
      g = geo(x0, y0, x1, y1, CW, CH); out = np.full((y1 - y0, x1 - x0, 3), np.nan, np.float32); have = np.zeros((y1 - y0, x1 - x0), bool); used = set()
      for Q in quads:
          qb = Q['q']['bbox']
          if qb[0] > g[2] or qb[2] < g[0] or qb[1] > g[3] or qb[3] < g[1]: continue
          t = Q['vrt'].read([1, 2, 3], window=Window(x0, y0, x1 - x0, y1 - y0)).astype(np.float32)
          ok = (t > 0).all(0) & ~have
          if ok.any(): out[ok] = np.moveaxis(t, 0, -1)[ok] / 255.0; have |= ok; used.add(Q['q']['href'].split('/')[-1][:-4])
          if have.all(): break
      return out, used
  # coarse pass: one gain and one chroma factor (fuse measures them per call; per tile they would step at tile edges)
  cs = 8; gw, gh = CW // cs, CH // cs
  lons, lats = rb.grid_axes(bb, gw, gh)
  RY, CX = np.meshgrid((pbb[3] - lats) / (pbb[3] - pbb[1]) * PH - 0.5, (lons - pbb[0]) / (pbb[2] - pbb[0]) * PW - 0.5, indexing='ij')
  Rc = np.clip(np.stack([ndimage.map_coordinates(c, [RY, CX], order=3, mode='nearest', prefilter=False) for c in pcs], -1), 0, 1)
  RYh, CXh = np.meshgrid((bb[3] - lats) / (bb[3] - bb[1]) * H - 0.5, (lons - bb[0]) / (bb[2] - bb[0]) * W - 0.5, indexing='ij')
  Lc_land = ndimage.map_coordinates(h, [RYh, CXh], order=1) > 0.5
  Ic = np.full((gh, gw, 3), np.nan, np.float32); hv = np.zeros((gh, gw), bool)
  for Q in quads:
      with rasterio.open('/vsicurl/' + Q['q']['href'], overview_level=Q['nov'] - 1) as d2, \
           WarpedVRT(d2, crs='EPSG:4326', transform=from_bounds(*bb, gw, gh), width=gw, height=gh, resampling=Resampling.average, src_nodata=0, nodata=0) as vv:
          t = vv.read([1, 2, 3]).astype(np.float32)   # the coarsest overview (about 19 m) for a 67 m grid
      ok = (t > 0).all(0) & ~hv; Ic[ok] = np.moveaxis(t, 0, -1)[ok] / 255.0; hv |= ok
  sc = max(1.0, s / cs); rl = ndimage.gaussian_filter(Rc, (sc, sc, 0)); il = db.nan_gauss(Ic, hv, sc); Lr, Li = rb.lum(rl), rb.lum(il)
  meas = hv & Lc_land & (ndimage.distance_transform_edt(Lc_land) > max(1.0, 30 / (cpx * cs))) & (Lr > 0.03)
  g = float(np.median(Lr[meas]) / max(float(np.median(Li[meas])), 1e-3))
  ci = np.linalg.norm(il - Li[..., None], axis=-1) * g; cr_ = np.linalg.norm(rl - Lr[..., None], axis=-1)
  beta = float(np.clip(np.median(cr_[meas]) / max(float(np.median(ci[meas])), 1e-4), 0.4, 1.2))
  ratio_c = Li * g / np.maximum(Lr, 1e-3)
  LOG(f'  coarse pass {gw}x{gh}: gain {g:.3f}, chroma {beta:.3f} on {int(meas.sum())} texels; photo much darker than the reference on '
      f'{float(((ratio_c < 0.6) & meas).mean() / max(meas.mean(), 1e-9) * 100):.1f} %, much brighter on {float(((ratio_c > 1.6) & meas).mean() / max(meas.mean(), 1e-9) * 100):.1f} % of land')
  del Rc, Ic, rl, il, RY, CX, RYh, CXh
  # tiles
  T = A.tile; M = int(math.ceil(4 * 400.0 / max(cpx, 10.0 * 1.0))) + int(math.ceil(4 * s)) + 8; M = max(M, 200)
  col = np.zeros((CH, CW, 3), np.uint8); lres = np.zeros((CH // 4, CW // 4), np.float32); nfe = int(round(fm / cpx))
  st = dict(land=0.0, kept=0.0, filled=0.0); used_all = set()
  for y0 in range(0, CH, T):
      for x0 in range(0, CW, T):
          y1, x1 = min(CH, y0 + T), min(CW, x0 + T); X0, Y0, X1, Y1 = max(0, x0 - M), max(0, y0 - M), min(CW, x1 + M), min(CH, y1 + M)
          ref = ref_tile(X0, Y0, X1, Y1); lt = h_tile(X0, Y0, X1, Y1) > 0.5
          yy = np.arange(Y0, Y1)[:, None]; xx = np.arange(X0, X1)[None, :]
          et = db.sstep(0, nfe, np.minimum(np.minimum(yy, CH - 1 - yy), np.minimum(xx, CW - 1 - xx)).astype(np.float32)) if nfe > 0 else np.ones((Y1 - Y0, X1 - X0), np.float32)
          out = ref; wk = np.zeros(lt.shape, np.float32)
          if lt.any():
              img, used = naip_tile(X0, Y0, X1, Y1); used_all |= used; v_ = np.isfinite(img).all(-1)
              if v_.any():
                  rl = ndimage.gaussian_filter(ref, (s, s, 0)); il = db.nan_gauss(img, v_, s); Lr = rb.lum(rl)
                  n = np.nan_to_num(img) * g; nl = il * g; Ln, Lnl = rb.lum(n), rb.lum(nl)
                  D = np.clip(Ln / np.maximum(Lnl, 1e-3), 0.35, 2.5)
                  o = rl * D[..., None] + beta * (n - nl * D[..., None])
                  ratio = Lnl / np.maximum(Lr, 1e-3); keep = v_ & lt
                  wv = np.clip(ndimage.gaussian_filter(keep.astype(np.float32), max(1.0, 3.0 / cpx)), 0, 1) * keep
                  agree = np.clip(ndimage.gaussian_filter((db.sstep(0.42, 0.65, ratio) * (1 - db.sstep(1.7, 2.4, ratio))).astype(np.float32), max(1.0, 0.5 * s)), 0, 1)
                  wk = wv * agree; wf = wv * (1 - agree)
                  fill = db.nc_fill(o, wk * lt, ref, cpx) if (wf > 0.02).any() else ref
                  out = ref * (1 - wv[..., None]) + o * wk[..., None] + fill * wf[..., None]
                  c = (slice(y0 - Y0, y1 - Y0), slice(x0 - X0, x1 - X0)); st['land'] += float(lt[c].sum()); st['kept'] += float(wk[c][lt[c]].sum()); st['filled'] += float(wf[c][lt[c]].sum())
          out = np.clip(ref * (1 - et[..., None]) + out * et[..., None], 0, 1)
          lr = np.log2(np.maximum(2.0 ** (wk * math.log2(0.6) + (1 - wk) * math.log2(ref_m)), 0.25)); lr = math.log2(ref_m) * (1 - et) + lr * et
          Lc = rb.lum(out); s1, s2 = max(0.7, 3.0 / cpx), max(1.5, 8.0 / cpx)
          hp = Lc - ndimage.gaussian_filter(Lc, s1); con = np.sqrt(ndimage.gaussian_filter(hp * hp, s2)) / np.maximum(ndimage.gaussian_filter(Lc, s2), 0.02)
          pres = db.sstep(0.025, 0.07, con); lr = pres * lr + (1 - pres) * np.maximum(lr, math.log2(max(ref_m, 7.0)))
          c = (slice(y0 - Y0, y1 - Y0), slice(x0 - X0, x1 - X0))
          col[y0:y1, x0:x1] = (out[c] * 255 + 0.5).astype(np.uint8)
          q = lr[c]; qh, qw = (y1 - y0) // 4, (x1 - x0) // 4
          if qh and qw: lres[y0 // 4:y0 // 4 + qh, x0 // 4:x0 // 4 + qw] = q[:qh * 4, :qw * 4].reshape(qh, 4, qw, 4).mean((1, 3))
      LOG(f'  colour rows {y0}-{y1} ({time.time() - t0:.0f} s)')
  for Q in quads: Q['vrt'].close(); Q['ds'].close()
  env.__exit__(None, None, None)
  Image.fromarray(col).save(f'{od}/color.jpg', quality=90); del col
  Image.fromarray(np.clip(np.round((lres + 2) * 25), 0, 255).astype(np.uint8), 'L').save(f'{od}/cres.png')
  kept = st['kept'] / max(st['land'], 1) * 100; filled = st['filled'] / max(st['land'], 1) * 100
  dates = sorted({q['date'] for q in hit if q['href'].split('/')[-1][:-4] in used_all})
  # ---------- meta
  meta = dict(name=name, bbox=bb, hmin=hmin, hrange=hrange, vex=1.0, wh=[W, H], px_m=round(px_m, 2),
              sources=[dict(id=f'region:{P["parent"]}', px_m=pm['px_m']), dict(id=hc['source'], res_arcsec=round((ncei_d or 0) * 3600, 2), cover=round(cover, 3),
                       near_m=near_m, far_m=far_m, zero_fill_land_km2=round(zf_land, 1), shallow_fill_land_km2=round(sh_land, 1), note='NOAA NCEI coastal topo-bathy DEM on land and the near shore, the parent beyond; its exact-zero fill, and flat shallow fill joining land, set to low land where the NAIP photo is not water')],
              colour=dict(ortho=dict(cc, source='USDA NAIP 2021-2023 Hawaii 0.6 m (NOAA Digital Coast 9668)', read_m=round(quads[0]['rres'], 1), gain=round(g, 3), chroma=round(beta, 3),
                                     imagery_pct=round(kept, 1), filled_pct=round(filled, 1), ref_scale_m=round(ref_m, 1),
                                     method='detail transfer: reference tone and colour at its own scale, imagery detail finer')),
              purpose=R.get('purpose', ''), gaps=R.get('gaps', []), patch=dict(parent=P['parent'], feather_m=fm),
              files=dict(h16='h16.png', ao='ao.png', color='color.jpg', cres='cres.png'),
              res=dict(height_m=round(px_m, 2), height_src_m=round((ncei_d or 0) * 111320, 1), colour_texel_m=round(cpx, 2), height_interp=[], colour_src_m=0.6, colour_wh=[CW, CH]),
              detail=dict(colour=dict(cc, source='USDA NAIP 2021-2023 Hawaii 0.6 m (NOAA Digital Coast 9668)', quads_n=len(used_all), dates=dates, read_m=round(quads[0]['rres'], 1),
                                      gain=round(g, 3), chroma=round(beta, 3), imagery_pct=round(kept, 1), filled_pct=round(filled, 1)),
                          height=dict(hc), baker='lab/hawaii/tools/oahu_patch.py'))
  meta['facts'] = rb.facts(h, bb, R.get('facts', {}), px_m)
  meta['bytes'] = {k: os.path.getsize(f'{od}/{v_}') for k, v_ in meta['files'].items()}
  meta['bake_s'] = round(time.time() - t0, 1); meta['baked'] = time.strftime('%Y-%m-%d')
  json.dump(meta, open(f'{od}/meta.json', 'w'), indent=1, ensure_ascii=False)
  if not A.keep: shutil.rmtree(dl, ignore_errors=True)
  LOG(f'  done {name} in {time.time() - t0:.0f} s: heights {W}x{H} {px_m:.1f} m, colour {CW}x{CH} {cpx:.2f} m (photo kept on {kept:.1f} % of land, '
      f'filled {filled:.1f} %), {len(used_all)} quads {dates[:1]}..{dates[-1:]}, {sum(meta["bytes"].values()) / 1e6:.1f} MB')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True); ap.add_argument('--only'); ap.add_argument('--out', required=True); ap.add_argument('--dl', required=True)
    ap.add_argument('--keep', action='store_true'); ap.add_argument('--tile', type=int, default=1024)
    A = ap.parse_args(); only = set(A.only.split(',')) if A.only else None
    for R in json.load(open(A.spec))['regions']:   # the spec entries this tool bakes ("baker": "oahu_patch.py"; detail_bake.py skips them)
        if R.get('baker') == 'oahu_patch.py' and (not only or R['name'] in only): bake(R, A)
