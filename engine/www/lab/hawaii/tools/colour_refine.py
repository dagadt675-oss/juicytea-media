#!/usr/bin/env python3
"""colour_refine.py --data DIR --region NAME (--dl DL_DIR | --naip-index JSON) [--long 8192] [--sigma-m 3] [--out DIR]
Second pass for a NAIP close-up region baked by detail_bake.py (2026-11-15, ep02 pali_lookout): its colour at twice the texels.
detail_bake.py holds the colour at long 4096 (memory: its fuse needs about 8 GB at 8192), so a 0.6 m photo lands on a 1.44 m grid and
the close ground shots magnify that (s026-s029, the Pali Lookout lower third: streaky, soft crowns, olive mush). This pass works in
tiles of 1024 texels and keeps the bake's tone: on the new grid (long --long, at most 8192 = SwiftShader's MAX_TEXTURE_SIZE)
  out = B_lp * D + k * (n - n_lp * D),   D = L(n) / L(n_lp)   (the detail transfer of detail_bake.fuse, one scale finer)
B = the bake up-sampled (bicubic), n = the same NAIP quarter quads (highest sun first, read at native 0.6 m, cubic), _lp = a gaussian of
--sigma-m (3 m: the bake keeps the tone and colour at 3 m and above, the photo gives everything finer), k = one chroma factor (the bake's
median chroma over the photo's at 3 m). Weight per texel = the photo was used by the bake (cres.png <= 0.8 m, fading out by 1.2 m;
cres also carries the patch's edge fade, so the edge stays the bake's) x the photo agrees with the bake at 3 m (no baked winter shadow,
cloud or change) x photo coverage. Elsewhere the up-sampled bake. cres.png, heights and AO are not touched. Writes color.jpg (q 90) and
updates meta.json (res.colour_texel_m, res.colour_wh, bytes, detail.colour.refine). Leaves a colour already at --long alone (exit 0).
The NAIP index is detail_bake.py's (DL_DIR/naip_hi_2021_items.json, fetched from the NOAA STAC catalog if missing).
Untrusted input: run with python -I. Needs rasterio (GDAL /vsicurl to coastalimagery.blob.core.windows.net)."""
import sys, os, json, math, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage

def lum(c): return c @ np.array([0.2126, 0.7152, 0.0722], np.float32)
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def ngauss(a, m, s):
    w = ndimage.gaussian_filter(m.astype(np.float32), s)
    return np.stack([ndimage.gaussian_filter(np.where(m, a[..., k], 0).astype(np.float32), s) for k in range(a.shape[2])], -1) / np.maximum(w, 1e-4)[..., None]

ap = argparse.ArgumentParser()
ap.add_argument('--data', required=True); ap.add_argument('--region', required=True); ap.add_argument('--naip-index'); ap.add_argument('--dl')
ap.add_argument('--long', type=int, default=8192); ap.add_argument('--sigma-m', type=float, default=3.0); ap.add_argument('--out', default=None)
ap.add_argument('--tile', type=int, default=1024)
a = ap.parse_args()
t0 = time.time(); src = os.path.join(a.data, a.region); out_dir = a.out or src; os.makedirs(out_dir, exist_ok=True)
meta = json.load(open(os.path.join(src, 'meta.json'))); bb = meta['bbox']
col0 = Image.open(os.path.join(src, meta['files']['color'])).convert('RGB'); W0, H0 = col0.size
if max(W0, H0) >= a.long: print(f'{a.region}: colour already {W0}x{H0}, nothing to refine at long {a.long}'); sys.exit(0)
if not (a.naip_index or a.dl): sys.exit('give --dl (detail_bake.py download folder) or --naip-index')
f = a.long / max(W0, H0); W, H = int(round(W0 * f)), int(round(H0 * f))
lat = (bb[1] + bb[3]) / 2; pxm = ((bb[2] - bb[0]) / W * 111320 * math.cos(math.radians(lat)), (bb[3] - bb[1]) / H * 111320)
s = a.sigma_m / min(pxm); M = int(math.ceil(4 * s)) + 8
print(f'{a.region}: colour {W0}x{H0} -> {W}x{H} ({pxm[0]:.3f} x {pxm[1]:.3f} m), low-pass sigma {a.sigma_m} m = {s:.2f} texels', flush=True)
c0 = [Image.fromarray(np.asarray(col0)[..., k].astype(np.float32) / 255, 'F') for k in range(3)]; del col0
cr = Image.open(os.path.join(src, meta['files']['cres'])); cra = np.asarray(cr).astype(np.float32)
if cra.ndim == 3: cra = cra[..., 0]
cres_m = 2 ** (cra / 25.0 - 2); kw = ndimage.gaussian_filter(sstep(math.log2(1.2), math.log2(0.8), np.log2(cres_m)).astype(np.float32), 0.75)
kwI = Image.fromarray(kw, 'F'); CW, CH = kwI.size
def up(img, x0, y0, x1, y1, fx, fy, filt):   # crop of an image in output texels -> its own pixels, resized
    return np.asarray(img.resize((x1 - x0, y1 - y0), filt, box=(x0 * fx, y0 * fy, x1 * fx, y1 * fy)))
# NAIP quarter quads: the ones the bake used (meta), in its order (highest sun first)
if a.naip_index: idx = json.load(open(a.naip_index))
else:
    import detail_bake as db; idx = db.naip_items(os.path.join(a.dl, a.region))   # cached as DL_DIR/naip_hi_2021_items.json
byname = {v['href'].split('/')[-1][:-4]: v for v in idx.values()}
quads = [q.split(' ')[0] for q in meta['detail']['colour']['quads']]
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.windows import Window
env = rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif', GDAL_HTTP_MAX_RETRY='5', GDAL_HTTP_RETRY_DELAY='3',
                   VSI_CACHE='TRUE', VSI_CACHE_SIZE=256 << 20, GDAL_CACHEMAX=512)
env.__enter__()
tr = from_bounds(*bb, W, H); vrts = []
for q in quads:
    ds = rasterio.open('/vsicurl/' + byname[q]['href'])
    vrts.append((q, ds, WarpedVRT(ds, crs='EPSG:4326', transform=tr, width=W, height=H, resampling=Resampling.cubic, src_nodata=0, nodata=0)))
def read_naip(x0, y0, x1, y1):
    h, w = y1 - y0, x1 - x0; out = np.zeros((h, w, 3), np.float32); have = np.zeros((h, w), bool)
    for q, ds, v in vrts:
        qb = byname[q]['bbox']; gx0 = bb[0] + x0 / W * (bb[2] - bb[0]); gx1 = bb[0] + x1 / W * (bb[2] - bb[0])
        gy1 = bb[3] - y0 / H * (bb[3] - bb[1]); gy0 = bb[3] - y1 / H * (bb[3] - bb[1])
        if qb[0] > gx1 or qb[2] < gx0 or qb[1] > gy1 or qb[3] < gy0: continue
        t = v.read([1, 2, 3], window=Window(x0, y0, w, h)).astype(np.float32)
        ok = (t > 0).all(0) & ~have
        if ok.any(): out[ok] = np.moveaxis(t, 0, -1)[ok] / 255.0; have |= ok
        if have.all(): break
    return out, have
# 1) one luminance gain and one chroma factor for the whole region, at the low-pass scale, on a coarse grid (about 4 x sigma texels)
cs = max(1, int(round(s * 1.5))); cw, ch = W // cs, H // cs
B = np.stack([np.asarray(c0[k].resize((cw, ch), Image.BOX)) for k in range(3)], -1)
K = np.asarray(kwI.resize((cw, ch), Image.BILINEAR)) > 0.9
nn = np.zeros((ch, cw, 3), np.float32); nh = np.zeros((ch, cw), bool)
for q, ds, _ in vrts:
    with WarpedVRT(ds, crs='EPSG:4326', transform=from_bounds(*bb, cw, ch), width=cw, height=ch, resampling=Resampling.average, src_nodata=0, nodata=0) as v:
        t = v.read([1, 2, 3]).astype(np.float32)   # GDAL picks the overview
    ok = (t > 0).all(0) & ~nh; nn[ok] = np.moveaxis(t, 0, -1)[ok] / 255.0; nh |= ok
m = K & nh
g = float(np.median(lum(B)[m]) / max(float(np.median(lum(nn)[m])), 1e-3))
r = lum(nn) * g / np.maximum(lum(B), 1e-3); m2 = m & (r > 0.65) & (r < 1.6)
ci = np.linalg.norm(nn * g - (lum(nn) * g)[..., None], axis=-1); cb = np.linalg.norm(B - lum(B)[..., None], axis=-1)
k_chroma = float(np.clip(np.median(cb[m2]) / max(float(np.median(ci[m2])), 1e-4), 0.4, 1.2))
print(f'  coarse pass ({cw}x{ch}, {cs} texels): gain {g:.3f}, chroma {k_chroma:.3f} on {m2.mean() * 100:.1f} % of the grid', flush=True)
del B, nn, K, ci, cb, r
# 2) tiles
res = np.zeros((H, W, 3), np.uint8); fx, fy = W0 / W, H0 / H; kfx, kfy = CW / W, CH / H; T = a.tile; wsum = 0.0; n_t = 0
for y0 in range(0, H, T):
    for x0 in range(0, W, T):
        y1, x1 = min(H, y0 + T), min(W, x0 + T); X0, Y0, X1, Y1 = max(0, x0 - M), max(0, y0 - M), min(W, x1 + M), min(H, y1 + M)
        Bt = np.stack([up(c0[k], X0, Y0, X1, Y1, fx, fy, Image.BICUBIC) for k in range(3)], -1)
        kt = np.clip(up(kwI, X0, Y0, X1, Y1, kfx, kfy, Image.BILINEAR), 0, 1)
        if kt.max() < 0.01: out = Bt
        else:
            n, have = read_naip(X0, Y0, X1, Y1)
            if not have.any(): out = Bt
            else:
                rl = ndimage.gaussian_filter(Bt, (s, s, 0)); il = ngauss(n, have, s)
                Ln, Lil, Lr = lum(n), lum(il), lum(rl)
                Dd = np.clip(Ln / np.maximum(Lil, 1e-3), 0.35, 2.5)
                o = rl * Dd[..., None] + k_chroma * g * (n - il * Dd[..., None])
                ratio = Lil * g / np.maximum(Lr, 1e-3)
                ag = ndimage.gaussian_filter((sstep(0.5, 0.7, ratio) * (1 - sstep(1.5, 1.9, ratio))).astype(np.float32), s)
                hv = np.clip(ndimage.gaussian_filter(have.astype(np.float32), 2.0) * 2 - 1, 0, 1) * have
                wt = (kt * ag * hv)[..., None]
                out = Bt * (1 - wt) + o * wt; wsum += float(wt[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0].sum()); n_t += 1
        res[y0:y1, x0:x1] = (np.clip(out[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0], 0, 1) * 255 + 0.5).astype(np.uint8)
    print(f'  rows {y0}-{y1} done ({time.time() - t0:.0f} s)', flush=True)
for q, ds, v in vrts: v.close(); ds.close()
env.__exit__(None, None, None)
cf = os.path.join(out_dir, meta['files']['color']); tmp = cf + '.tmp.jpg'
Image.fromarray(res).save(tmp, quality=90); os.replace(tmp, cf)
used = wsum / (W * H) * 100
meta['res']['colour_texel_m'] = round(min(pxm), 2); meta['res']['colour_wh'] = [W, H]
meta['bytes']['color'] = os.path.getsize(cf)
meta['detail']['colour']['refine'] = dict(tool='lab/hawaii/tools/colour_refine.py', long=a.long, base_long=max(W0, H0), sigma_m=a.sigma_m, gain=round(g, 3),
    chroma=round(k_chroma, 3), refined_pct=round(used, 1), when=time.strftime('%Y-%m-%d'),
    method='detail transfer one scale finer: the bake keeps tone and colour at 3 m and above, the same NAIP quads at 0.6 m give the finer detail')
json.dump(meta, open(os.path.join(out_dir, 'meta.json.tmp'), 'w'), indent=1, ensure_ascii=False); os.replace(os.path.join(out_dir, 'meta.json.tmp'), os.path.join(out_dir, 'meta.json'))
print(f'{a.region}: colour {W}x{H}, refined on {used:.1f} % of texels, {meta["bytes"]["color"] / 1e6:.1f} MB, {time.time() - t0:.0f} s', flush=True)
