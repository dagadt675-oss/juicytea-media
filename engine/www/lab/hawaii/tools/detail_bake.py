#!/usr/bin/env python3
"""detail_bake.py: close-up detail for regions baked by region_bake.py (run after it; rebuild_regions.sh does).

  python3 -I detail_bake.py --spec SPEC.json [--only NAME[,NAME...]] --out DATA --dl DL [--keep]

Two kinds of spec entry (regions_spec.json):
  * a region with "detail": re-bake that region at a higher resolution IN PLACE (same name, bbox, files and conventions, so every shot
    that uses it keeps working): colour from aerial orthoimagery fused with the region's own graded colour, heights from USGS 3DEP lidar
    DEMs over its own grid. The base bake is kept as color_base.jpg / h16_base.png / ao_base.png and is always the reference, so a re-run
    never compounds.
      "detail": {"colour": {"source": "naip", "long": 4096} | {"source": "s2", "long": 4096, "months": [[from, to], ...]},
                 "height": {"source": "3dep", "wh": [W, H]}}
  * a nested detail patch: an entry with "patch": {"parent": NAME, "feather_m": 120} and its own bbox (inside the parent), "wh" (height
    grid) and "detail" (as above, "colour.wh" or "colour.long" for its colour texture). It is written as a region of its own
    (DATA/NAME/, the same files) and the parent's "stack" lists it first; HawaiiStage.loadRegion then draws it as a fourth, finest layer
    (lab/hawaii/hterrain.js). Heights and colour fade into the parent's over feather_m at the patch edge (no seam), and fall back to the
    parent's where the lidar or the imagery has no data (the sea).

Sources (all public domain; SOURCES.md in the episode's data folder lists them per region):
  3dep  USGS 3D Elevation Program, best available bare-earth DEM (1 m lidar DEMs in Hawai'i: HI_NOAAMauiOahu_2020, HI_Hawaii_Island
        _Lidar_NOAA_2017, HI_FEMAR9Kauai_2019), read from the USGS 3DEPElevation ImageServer (exportImage, EPSG:4326, float32) at the
        target grid. Vertical datum: local mean sea level (the NCEI coastal grids under it are MHW, about 0.3 m higher: feathered).
  naip  USDA NAIP 2021-2023 Hawai'i, 0.6 m 4-band (NOAA Digital Coast, dataset 9668, cloud-optimised GeoTIFFs on Azure), read with
        rasterio over HTTP range requests (only the window and overview level needed), area-averaged onto the target grid. Quarter
        quads are taken highest sun first (closest to June), so the fewest cliffs are in baked shadow.
  s2    ESA Copernicus Sentinel-2 L2A 10 m (Planetary Computer), the per-pixel median of SCL-clear observations (free and open data;
        credit 'Contains modified Copernicus Sentinel data' in the description), for places NAIP does not cover (Midway).
Colour matching to the existing grade (the region's own colour is the reference): detail transfer. The reference keeps the tone and the
colour at its own scale (HLS 30 m), the imagery adds only what is finer: its luminance detail as a ratio to its local mean, plus its
residual colour detail times one chroma factor (after one luminance gain; PLAYBOOK_production 15: never a per-channel match of the
imagery as a whole). So a winter photo's baked cliff shadow or a cloud larger than the reference's texel takes the reference's tone, and
the photo's own hue (NAIP lava reads blue-grey, the film's HLS brown) never replaces the grade. Sea texels (h < 0.5 m) keep the reference.
Needs numpy, scipy, PIL, rasterio (pip install rasterio==1.4.3; RIO_PY in rebuild_regions.sh) and network to elevation.nationalmap.gov,
coastalimagery.blob.core.windows.net and planetarycomputer.microsoft.com."""
import sys, os, io, json, math, time, shutil, argparse, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import region_bake as rb   # fetch, cached, pack16, bake_ao, feather, facts, lum, PC helpers (same folder)

Image.MAX_IMAGE_PIXELS = 400_000_000
LOG = print
TDEP = 'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage'
NAIP_STAC = 'https://coastalimagery.blob.core.windows.net/digitalcoast/HI_NAIP_2021_9668/stac/'

def read_h16(path, hmin=rb.HMIN, hrange=rb.HRANGE):
    a = np.asarray(Image.open(path)).astype(np.float32); return (a[..., 0] * 256 + a[..., 1]) / 65535 * hrange + hmin

def resize1(a, w, h, method=Image.BILINEAR):
    return np.asarray(Image.fromarray(np.ascontiguousarray(a, dtype=np.float32), 'F').resize((w, h), method))

def resample_bb(a, src_bb, bb, w, h, order=1):
    """a (row 0 north) over src_bb sampled at the pixel centres of the w x h grid over bb (inside src_bb)."""
    H, W = a.shape[:2]; lons, lats = rb.grid_axes(bb, w, h)
    RY, CX = np.meshgrid((src_bb[3] - lats) / (src_bb[3] - src_bb[1]) * H - 0.5, (lons - src_bb[0]) / (src_bb[2] - src_bb[0]) * W - 0.5, indexing='ij')
    if a.ndim == 2: return ndimage.map_coordinates(a, [RY, CX], order=order, mode='nearest').astype(np.float32)
    return np.stack([ndimage.map_coordinates(a[..., k], [RY, CX], order=order, mode='nearest') for k in range(a.shape[2])], -1).astype(np.float32)

def px_size(bb, W, H):
    lat = (bb[1] + bb[3]) / 2; return (bb[2] - bb[0]) / W * 111320 * math.cos(math.radians(lat)), (bb[3] - bb[1]) / H * 111320

# ---------- heights: USGS 3DEP (best available, 1 m lidar DEMs in Hawai'i) through the 3DEPElevation ImageServer
def dem_3dep(bb, W, H, dl):
    """the target grid's pixel centres sampled (bilinear) from a mosaic of 3DEP tiles on a grid of SQUARE pixels in degrees (the finer of
    the target's two pixel sizes). The ImageServer silently changes the extent of a request whose pixels are not square in degrees: the
    first tiled bake took each tile as covering the requested box and left 8-75 m steps along the tile seams (a dark 'fin' on the Pali
    cliffs in the stills). Square requests come back exactly as asked; each tile is still placed by its own GeoTIFF georeference."""
    T, M = 2000, 6   # exportImage allows 8000 x 8000, but large requests time out (502); M = margin pixels around the box
    d = min((bb[2] - bb[0]) / W, (bb[3] - bb[1]) / H)
    NX, NY = int(math.ceil((bb[2] - bb[0]) / d)) + 2 * M, int(math.ceil((bb[3] - bb[1]) / d)) + 2 * M
    X0, Y0 = bb[0] - M * d, bb[3] + M * d   # west and north edges of the request grid
    mos = np.full((NY, NX), np.nan, np.float32)
    jobs = [(r0, c0, min(T, NY - r0), min(T, NX - c0)) for r0 in range(0, NY, T) for c0 in range(0, NX, T)]
    def get(j):
        r0, c0, h, w = j
        sb = [X0 + c0 * d, Y0 - (r0 + h) * d, X0 + (c0 + w) * d, Y0 - r0 * d]
        url = (f'{TDEP}?bbox={sb[0]:.9f},{sb[1]:.9f},{sb[2]:.9f},{sb[3]:.9f}&bboxSR=4326&imageSR=4326&size={w},{h}&format=tiff&pixelType=F32'
               f'&noData=-9999&interpolation=RSP_BilinearInterpolation&compression=None&f=image')
        b = rb.cached(f'{dl}/3dep_sq_{r0}_{c0}_{w}x{h}.tif', url, tries=6, timeout=600)
        im = Image.open(io.BytesIO(b)); a = np.asarray(im).astype(np.float32); tp, sc = im.tag_v2[33922], im.tag_v2[33550]
        a[(a < -9000) | (a > 9000)] = np.nan
        err = (abs(tp[3] - sb[0]) / d, abs(tp[4] - sb[3]) / d, abs(sc[0] / d - 1), abs(sc[1] / d - 1))
        if a.shape != (h, w) or max(err[:2]) > 0.01 or max(err[2:]) > 1e-4: raise RuntimeError(f'3dep tile {j} came back as {a.shape}, tiepoint/scale off by {err}')
        return j, a
    with cf.ThreadPoolExecutor(3) as ex:
        for (r0, c0, h, w), a in ex.map(get, jobs): mos[r0:r0 + h, c0:c0 + w] = a
    lons, lats = rb.grid_axes(bb, W, H)
    RY, CX = np.meshgrid((Y0 - lats) / d - 0.5, (lons - X0) / d - 0.5, indexing='ij')
    v = np.isfinite(mos); f = np.where(v, mos, 0).astype(np.float32)
    out = ndimage.map_coordinates(f, [RY, CX], order=1, mode='nearest').astype(np.float32)
    out[ndimage.map_coordinates(v.astype(np.float32), [RY, CX], order=1, mode='nearest') < 0.999] = np.nan
    LOG(f'  3dep: {len(jobs)} square-pixel tiles ({d * 111320:.2f} m), all at the requested extent')
    LOG(f'  3dep {W}x{H}: {np.isfinite(out).mean() * 100:.1f} % with data, {np.nanmin(out):.1f}..{np.nanmax(out):.1f} m')
    return out

# ---------- colour: NAIP 2021-2023 Hawai'i (NOAA Digital Coast COGs)
def naip_items(dl):
    path = os.path.join(os.path.dirname(dl.rstrip('/')), 'naip_hi_2021_items.json')
    if os.path.exists(path): return json.load(open(path))
    cat = json.loads(rb.fetch(NAIP_STAC + 'catalog.json')); names = [l['href'][2:] for l in cat['links'] if l['rel'] == 'item']
    def get(n):
        try: j = json.loads(rb.fetch(NAIP_STAC + n, tries=3)); return n, dict(bbox=j['bbox'], date=j['properties']['datetime'][:10], href=list(j['assets'].values())[0]['href'])
        except Exception: return n, None
    with cf.ThreadPoolExecutor(16) as ex: items = {n: v for n, v in ex.map(get, names) if v}
    json.dump(items, open(path, 'w')); LOG(f'  naip index: {len(items)} quarter quads'); return items

def naip(bb, W, H, dl):
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import from_bounds
    items = naip_items(dl)
    hit = [v for v in items.values() if v['bbox'][0] < bb[2] and v['bbox'][2] > bb[0] and v['bbox'][1] < bb[3] and v['bbox'][3] > bb[1]]
    hit.sort(key=lambda v: (abs(int(v['date'][5:7]) + int(v['date'][8:10]) / 31 - 6.6), v['date']))   # highest sun first
    if not hit: return None, []
    tpx = min(px_size(bb, W, H)); tr = from_bounds(*bb, W, H)
    out = np.zeros((4, H, W), np.float32); have = np.zeros((H, W), bool); used = []
    env = dict(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif', GDAL_HTTP_MAX_RETRY='5', GDAL_HTTP_RETRY_DELAY='3', VSI_CACHE='TRUE')
    with rasterio.Env(**env):
        for v in hit:
            with rasterio.open('/vsicurl/' + v['href']) as base:
                ovs = base.overviews(1); lvl = -1                          # read the coarsest overview still at least 1.5x finer than the target
                for k, f in enumerate(ovs):
                    if base.res[0] * f * 1.5 <= tpx: lvl = k
            kw = {} if lvl < 0 else dict(overview_level=lvl)
            with rasterio.open('/vsicurl/' + v['href'], **kw) as ds:
                tmp = np.zeros((4, H, W), np.float32)
                reproject(rasterio.band(ds, [1, 2, 3, 4]), tmp, dst_transform=tr, dst_crs='EPSG:4326', resampling=Resampling.average, src_nodata=0, dst_nodata=0)
                ok = (tmp[:3] > 0).all(0) & ~have
                if ok.any(): out[:, ok] = tmp[:, ok]; have |= ok; used.append(f'{v["href"].split("/")[-1][:-4]} ({v["date"]}, {base.res[0] * (ovs[lvl] if lvl >= 0 else 1):.1f} m read)')
            if have.all(): break
    rgb = np.moveaxis(out[:3], 0, -1) / 255.0; rgb[~have] = np.nan
    LOG(f'  naip {W}x{H} ({tpx:.2f} m): {have.mean() * 100:.1f} % covered by {len(used)} quarter quads: {used}')
    return rgb.astype(np.float32), used

# ---------- colour: Sentinel-2 L2A 10 m median of clear observations (Planetary Computer), where NAIP does not reach
def sentinel2(bb, W, H, dl, ranges, want=16):
    lat = (bb[1] + bb[3]) / 2
    nw = max(8, int(round((bb[2] - bb[0]) * 111320 * math.cos(math.radians(lat)) / 10))); nh = max(8, int(round((bb[3] - bb[1]) * 111320 / 10)))
    items = []
    for m0, m1 in ranges:
        d = rb.post_json(f'{rb.PC}/stac/v1/search', dict(collections=['sentinel-2-l2a'], bbox=[round(x, 6) for x in bb], datetime=f'{m0}T00:00:00Z/{m1}T23:59:59Z', limit=500))
        items += [(f['id'], f['properties']['datetime'][:10], f['properties'].get('eo:cloud_cover', 100)) for f in d['features']]
    items.sort(key=lambda x: x[2]); cand = items[:max(2 * want, 24)]
    def get(it):
        iid = it[0]
        try:
            a = rb.pc_npy('sentinel-2-l2a', iid, ['B04', 'B03', 'B02'], bb, nw, nh, dl, 'average'); s = rb.pc_npy('sentinel-2-l2a', iid, ['SCL'], bb, nw, nh, dl, 'nearest')
        except Exception as e: LOG(f'  s2 {iid}: {e}'); return it, None
        scl = s[0].astype(int); ok = (a[3] > 0) & (s[1] > 0) & np.isin(scl, [4, 5, 6, 7, 11])   # vegetation, bare, water, unclassified, snow
        # L2A baseline 04.00 and later (2022-01-25 on) carry a +1000 offset in the reflectance
        off = 1000 if it[1] >= '2022-01-25' else 0
        return it, (np.moveaxis(a[:3], 0, -1).astype(np.float32) - off) / 10000.0, ok
    with cf.ThreadPoolExecutor(6) as ex: res = [r for r in ex.map(get, cand) if r[1] is not None and r[2].mean() > 0.05]
    res.sort(key=lambda r: -r[2].mean()); res = res[:want]
    if not res: return None, [], {}
    S = np.where(np.stack([r[2] for r in res])[..., None], np.stack([r[1] for r in res]), np.nan)
    with np.errstate(invalid='ignore'), __import__('warnings').catch_warnings():
        __import__('warnings').simplefilter('ignore'); comp = np.nanmedian(S, 0)
    col = rb.to_display(comp)   # the HLS display curve (measured on GIBS): same tone family as the region's HLS colour
    st = dict(scenes=len(res), never_clear_pct=round(float((~np.isfinite(comp).all(-1)).mean() * 100), 2))
    if (nw, nh) != (W, H): col = rb.resize_nan(col, W, H)
    LOG(f'  s2 {W}x{H} from {nw}x{nh}: {len(res)} scenes, never clear {st["never_clear_pct"]} %')
    return col, sorted(f'S2_{r[0][1]}' for r in res), st

# ---------- fusion with the reference grade
def nan_gauss(a, valid, s):
    w = ndimage.gaussian_filter(valid.astype(np.float32), s)
    if a.ndim == 2: return ndimage.gaussian_filter(np.where(valid, a, 0).astype(np.float32), s) / np.maximum(w, 1e-4)
    return np.stack([ndimage.gaussian_filter(np.where(valid, a[..., k], 0).astype(np.float32), s) for k in range(a.shape[2])], -1) / np.maximum(w, 1e-4)[..., None]

def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def fuse(img, ref, land, px_m, ref_m, src_m):
    """img (imagery, NaN = none) and ref (the region's graded colour on the same grid), display values 0..1; land = h > 0.5 m.
    Detail transfer: the reference keeps the tone and colour at its own scale (ref_m, e.g. HLS 30 m), the imagery adds what is finer:
      out = ref_lp * D + beta * (n - n_lp * D),  D = L(n) / L(n_lp)  (luminance detail, a ratio: no gain can drift the tone)
    n = the imagery times one luminance gain, beta = one chroma factor (median chroma of the reference over the imagery's, at the
    reference's scale, clear land only). So a winter photo's baked cliff shadow or a cloud bigger than the reference's texel takes the
    reference's (summer) tone, and the imagery's own hue never replaces the grade (NAIP lava reads blue-grey, the film's HLS brown).
    Returns (colour, stats)."""
    v = np.isfinite(img).all(-1); s = max(1.0, 0.5 * ref_m / px_m)
    meas = v & land & (ndimage.distance_transform_edt(land) > max(1.0, 30 / px_m))
    rl = ndimage.gaussian_filter(ref, (s, s, 0)); il = nan_gauss(img, v, s)
    Li, Lr = rb.lum(il), rb.lum(rl); st = {}
    if meas.sum() < 500: g, beta = 1.0, 0.8
    else:
        g = float(np.median(Lr[meas]) / max(float(np.median(Li[meas])), 1e-3))
        ci = np.linalg.norm(il - Li[..., None], axis=-1) * g; cr = np.linalg.norm(rl - Lr[..., None], axis=-1)
        beta = float(np.clip(np.median(cr[meas]) / max(float(np.median(ci[meas])), 1e-4), 0.4, 1.2)); st.update(meas_px=int(meas.sum()))
    n = np.nan_to_num(img) * g; nl = il * g; Ln = rb.lum(n); Lnl = rb.lum(nl)
    D = np.clip(Ln / np.maximum(Lnl, 1e-3), 0.35, 2.5)
    out = rl * D[..., None] + beta * (n - nl * D[..., None])
    ratio = Lnl / np.maximum(Lr, 1e-3)   # where the imagery disagrees with the reference at its scale (baked shadow, cloud, change)
    keep = v & land
    wk = np.clip(ndimage.gaussian_filter(keep.astype(np.float32), max(1.0, 3.0 / px_m)), 0, 1) * keep
    out = ref * (1 - wk[..., None]) + out * wk[..., None]
    st.update(gain=round(g, 3), chroma=round(beta, 3), dark_pct=round(float(((ratio < 0.6) & keep).sum() / max(keep.sum(), 1) * 100), 2),
              bright_pct=round(float(((ratio > 1.6) & keep).sum() / max(keep.sum(), 1) * 100), 2), covered_pct=round(float(v.mean() * 100), 1),
              ref_scale_m=round(ref_m, 1), method='detail transfer: reference tone and colour at its own scale, imagery detail finer')
    LOG(f'  fuse: gain {g:.3f}, chroma {beta:.3f}; imagery much darker than the reference (baked shadow) on {st["dark_pct"]} % of land, '
        f'much brighter (cloud, bare change) on {st["bright_pct"]} %, at the {ref_m:.0f} m scale')
    return np.clip(out, 0, 1).astype(np.float32), st

def edge_ramp(H, W, n):  # 0 at the grid edge to 1 at n texels inside
    if n <= 0: return np.ones((H, W), np.float32)
    y = np.minimum(np.arange(H), np.arange(H)[::-1])[:, None]; x = np.minimum(np.arange(W), np.arange(W)[::-1])[None, :]
    return sstep(0, n, np.minimum(y, x).astype(np.float32)).astype(np.float32)

def colour_src(cfg):
    return {'naip': 0.6, 's2': 10.0}.get(cfg.get('source'), 30.0)

def get_colour(cfg, bb, W, H, dl):
    if cfg.get('bbox'):   # imagery only over a sub-window (e.g. Midway's atoll inside a mostly open-ocean region), NaN elsewhere
        sub, (r0, c0, r1, c1) = rb.subwin(bb, W, H, cfg['bbox']); c, m = get_colour(dict(cfg, bbox=None), sub, c1 - c0 + 1, r1 - r0 + 1, dl)
        out = np.full((H, W, 3), np.nan, np.float32)
        if c is not None: out[r0:r1 + 1, c0:c1 + 1] = c
        m['bbox'] = [round(x, 5) for x in sub]; return out, m
    if cfg['source'] == 'naip': c, used = naip(bb, W, H, dl); return c, dict(source='USDA NAIP 2021-2023 Hawaii 0.6 m (NOAA Digital Coast 9668)', quads=used)
    if cfg['source'] == 's2':
        c, used, st = sentinel2(bb, W, H, dl, cfg.get('months', [['2023-01-01', '2024-12-31']]), cfg.get('n', 16))
        return c, dict(source='Copernicus Sentinel-2 L2A 10 m, median of SCL-clear observations (Planetary Computer)', dates=used, **st)
    raise ValueError(cfg['source'])

def size_of(cfg, bb, W0, H0):
    if cfg.get('wh'): return cfg['wh']
    L = cfg.get('long', 4096); kx, ky = px_size(bb, 1, 1); ar = kx / ky   # keep square texels in metres
    return (L, max(8, int(round(L / ar)))) if ar >= 1 else (max(8, int(round(L * ar))), L)

# ---------- one entry
def bake(R, OUT, DLROOT, keep=False, regs=None):
    t0 = time.time(); name = R['name']; bb = [float(x) for x in R['bbox']]; det = R.get('detail', {}); patch = R.get('patch')
    dl = f'{DLROOT}/{name}_detail'; od = f'{OUT}/{name}'; os.makedirs(dl, exist_ok=True); os.makedirs(od, exist_ok=True)
    LOG(f'== {name} ({"patch in " + patch["parent"] if patch else "in place"}) bbox {bb}')
    if patch:   # the reference: the parent's final heights and colour, resampled onto the patch grid
        pm = json.load(open(f'{OUT}/{patch["parent"]}/meta.json')); pbb = pm['bbox']
        if not (bb[0] >= pbb[0] and bb[1] >= pbb[1] and bb[2] <= pbb[2] and bb[3] <= pbb[3]): raise SystemExit(f'{name} is not inside {patch["parent"]}')
        W, H = R['wh']; ph = read_h16(f'{OUT}/{patch["parent"]}/{pm["files"]["h16"]}')
        base_h = resample_bb(ph, pbb, bb, W, H); pcol = np.asarray(Image.open(f'{OUT}/{patch["parent"]}/{pm["files"]["color"]}').convert('RGB')).astype(np.float32) / 255
        ref_m = max(pm.get('res', {}).get('colour_src_m', 30.0), pm.get('res', {}).get('colour_texel_m', pm['px_m']))
        meta = dict(name=name, bbox=bb, hmin=rb.HMIN, hrange=rb.HRANGE, vex=1.0, sources=[dict(id=f'region:{patch["parent"]}', px_m=pm['px_m'])], colour={},
                    purpose=R.get('purpose', ''), gaps=R.get('gaps', []), patch=dict(parent=patch['parent'], feather_m=patch.get('feather_m', 120)))
        base_ao = None
    else:
        meta = json.load(open(f'{od}/meta.json')); W0, H0 = meta['wh']
        if 'detail' not in meta:   # fresh from region_bake: keep the base bake as the reference for this and every later re-run
            for f, b in (('h16', 'h16_base.png'), ('color', 'color_base.jpg'), ('ao', 'ao_base.png')): shutil.copyfile(f'{od}/{meta["files"][f]}', f'{od}/{b}')
            meta['base'] = dict(wh=[W0, H0], px_m=meta['px_m'], sources=meta['sources'], facts=meta['facts'])
        else: meta['sources'] = meta['base']['sources']
        bh = read_h16(f'{od}/h16_base.png'); W0, H0 = bh.shape[1], bh.shape[0]
        W, H = det.get('height', {}).get('wh', [W0, H0])
        base_h = bh if (W, H) == (W0, H0) else resample_bb(bh, bb, bb, W, H)
        pcol = np.asarray(Image.open(f'{od}/color_base.jpg').convert('RGB')).astype(np.float32) / 255; pbb = bb
        base_ao = f'{od}/ao_base.png'
        c = meta.get('colour', {}); ref_m = 30.0 if c.get('hls') else 250.0
    pxw, pxh = px_size(bb, W, H); px_m = (pxw + pxh) / 2
    # ---- heights
    h = base_h.copy(); hcfg = det.get('height'); hsrc = {}
    if hcfg and hcfg.get('source') == '3dep':
        d = dem_3dep(bb, W, H, dl); v = np.isfinite(d) & (d > 0.5)   # land only: the service returns about 0 m over the sea (no bathymetry)
        w = rb.feather(v, max(2, int(round(6 / px_m)))) if v.any() else np.zeros((H, W), np.float32)   # into the base at the lidar's own edge (coast)
        h = base_h * (1 - w) + np.nan_to_num(d) * w
        hsrc = dict(id='3dep', res_m=1.0, cover=round(float(v.mean()), 3), note='USGS 3DEP best available (1 m lidar DEMs here), 3DEPElevation ImageServer')
        meta['sources'] = list(meta['sources']) + [hsrc]
    if patch:   # fade to the parent at the edge
        e = edge_ramp(H, W, int(round(patch.get('feather_m', 120) / px_m))); h = base_h * (1 - e) + h * e
    h = h.astype(np.float32); h[(h > 0) & (h < 1)] = 1.0
    if hcfg or patch:
        rb.pack16(h).save(f'{od}/h16.png', compress_level=6)
        f = 2 if W * H > 2.5e6 else 1
        h2 = np.asarray(Image.fromarray(h, 'F').resize((W // f, H // f), Image.BOX)) if f > 1 else h
        ao = rb.bake_ao(h2, bb, px_m * f, True)
        if patch:   # the parent's AO at the edge (its horizon reaches further than a small patch)
            pa = np.asarray(Image.open(f'{OUT}/{patch["parent"]}/{pm["files"]["ao"]}')).astype(np.float32) / 255
            pao = resample_bb(pa, pbb, bb, ao.shape[1], ao.shape[0]); ea = edge_ramp(ao.shape[0], ao.shape[1], max(4, int(round(400 / (px_m * f)))))
            ao = pao * (1 - ea) + ao * ea
        Image.fromarray((np.clip(ao, 0, 1) * 255).astype(np.uint8)).save(f'{od}/ao.png')
    elif base_ao: shutil.copyfile(base_ao, f'{od}/ao.png'); shutil.copyfile(f'{od}/h16_base.png', f'{od}/h16.png')
    LOG(f'  h {W}x{H} ({px_m:.2f} m) {h.min():.0f}..{h.max():.0f} ({time.time() - t0:.0f} s)')
    # ---- colour
    ccfg = det.get('colour'); CW, CH = size_of(ccfg, bb, W, H) if ccfg else (pcol.shape[1], pcol.shape[0])
    ref = resample_bb(pcol, pbb, bb, CW, CH, order=3).clip(0, 1)
    cpx = sum(px_size(bb, CW, CH)) / 2
    land = resample_bb(h, bb, bb, CW, CH) > 0.5
    col = ref; cmeta = {}
    if ccfg:
        img, cmeta = get_colour(ccfg, bb, CW, CH, dl)
        if img is not None:
            col, st = fuse(img, ref, land, cpx, ref_m, colour_src(ccfg)); cmeta.update(st)
    if patch:
        e = edge_ramp(CH, CW, int(round(patch.get('feather_m', 120) / cpx))); col = ref * (1 - e[..., None]) + col * e[..., None]
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(f'{od}/color.jpg', quality=90)
    # ---- meta
    meta.update(wh=[W, H], px_m=round(px_m, 2), files=dict(h16='h16.png', ao='ao.png', color='color.jpg'),
                res=dict(height_m=round(px_m, 2), height_src_m=1.0 if hsrc else meta.get('base', {}).get('px_m', px_m), colour_texel_m=round(cpx, 2),
                         colour_src_m=colour_src(ccfg) if ccfg else ref_m, colour_wh=[CW, CH]),
                detail=dict(colour=dict(ccfg or {}, **cmeta), height=hcfg or {}), bake_s=round(time.time() - t0, 1), baked=time.strftime('%Y-%m-%d'))
    meta['colour'] = dict(meta.get('colour', {}), ortho=dict(ccfg or {}, **{k: v for k, v in cmeta.items() if k not in ('quads', 'dates')}))
    meta['facts'] = rb.facts(h, bb, R.get('facts', {}), px_m)
    meta['bytes'] = {k: os.path.getsize(f'{od}/{v}') for k, v in meta['files'].items()}
    json.dump(meta, open(f'{od}/meta.json', 'w'), indent=1, ensure_ascii=False)
    if not keep: shutil.rmtree(dl, ignore_errors=True)
    LOG(f'  done {name} in {time.time() - t0:.0f} s: heights {W}x{H} {px_m:.2f} m, colour {CW}x{CH} {cpx:.2f} m, {sum(meta["bytes"].values()) / 1e6:.1f} MB; '
        f'facts {json.dumps(meta["facts"], ensure_ascii=False)[:300]}')
    return meta

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True); ap.add_argument('--only'); ap.add_argument('--out', required=True); ap.add_argument('--dl', required=True)
    ap.add_argument('--keep', action='store_true')
    A = ap.parse_args()
    S = json.load(open(A.spec)); only = set(A.only.split(',')) if A.only else None
    todo = [R for R in S['regions'] if (R.get('detail') or R.get('patch')) and (not only or R['name'] in only)]
    todo.sort(key=lambda R: 1 if R.get('patch') else 0)   # in-place upgrades first: a patch fades into its parent's final data
    for R in todo: bake(R, A.out, A.dl, A.keep)
