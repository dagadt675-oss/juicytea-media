#!/usr/bin/env python3
"""hawaii_bake.py DL OUT : bake the Hawaii terrain stage data for lab_hawaii.html (run by fetch_hawaii.sh).
Inputs (DL): etopo15.tif (ETOPO 2022 15", hero bbox), terr11_h.npy (AWS Terrarium z11 on the hero grid), skirt.tif (ETOPO 2022 30", wide bbox),
modis/*.jpg (GIBS MODIS 250 m, several dates), bmng.jpg / skirt_bm.jpg (GIBS Blue Marble NG), everest_h.npy (Terrarium z12).
Outputs (OUT): hero_h16.png, skirt_h16.png, everest_h16.png (RG 16-bit, h = v/65535*hrange+hmin, row 0 = north),
hero_ao.png / skirt_ao.png (ambient occlusion, L), hero_color.jpg / skirt_color.jpg (land drape; sea pixels filled with nearby land colour),
meta.json (bboxes, sizes, packing, DEM summits, Maui Nui saddle levels from the data).
Sun shadows are not baked: the page ray-marches the height texture toward the sun, so any sun direction and exaggeration work."""
import sys, os, json, math, glob, numpy as np
from collections import deque
from PIL import Image
DL, OUT = sys.argv[1], sys.argv[2]
cfg = dict(hero_bbox=[-158.3, 17.9, -153.8, 21.8], skirt_bbox=[-168.0, 12.0, -144.0, 30.0], everest_bbox=[86.700, 27.805, 87.150, 28.205],
           hero_wh=[4096, 4096], skirt_wh=[1800, 1350], everest_wh=[1024, 1024], hmin=-8000.0, hrange=17000.0, vex=1.0)
def rs(a, w, h, m=Image.BILINEAR): return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((w, h), m))
def blur(a, r): h, w = a.shape; return rs(rs(a, max(2, w // r), max(2, h // r), Image.BOX), w, h)
def pack16(h):
    v = np.clip((h - cfg['hmin']) / cfg['hrange'] * 65535, 0, 65535).astype(np.uint32)
    return Image.fromarray(np.stack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)], -1))
def fill_sea(rgb, land):  # push-pull fill: sea pixels get the colour of nearby land (no blue fringes on coastal land)
    lv = [(rgb * land[..., None], land.astype(np.float32))]
    while min(lv[-1][1].shape) > 4:
        c, m = lv[-1]; h, w = m.shape; h2, w2 = h // 2, w // 2
        lv.append((c[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).sum((1, 3)), m[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).sum((1, 3))))
    est = lv[-1][0] / np.maximum(lv[-1][1], 1e-6)[..., None]
    for c, m in reversed(lv[:-1]):
        h, w = m.shape; up = np.stack([rs(est[..., k], w, h) for k in range(3)], -1)
        est = np.where(m[..., None] > 0, c / np.maximum(m, 1e-6)[..., None], up)
    return est
def bake_ao(h, bbox, vex, rmax=25000):
    H, W = h.shape; lat = np.linspace(bbox[3], bbox[1], H)[:, None]
    dxm = (bbox[2] - bbox[0]) / W * 111320 * np.cos(np.radians(lat)); dym = (bbox[3] - bbox[1]) / H * 111320
    he = h * vex; occ = np.zeros(h.shape, np.float32); nd = 12
    for k in range(nd):
        a = 2 * math.pi * k / nd; best = np.full(h.shape, -1.0, np.float32)
        for s in np.geomspace(300, rmax, 16):
            dc = np.rint(math.sin(a) * s / dxm).astype(int); dr = int(round(-math.cos(a) * s / dym))
            r = np.clip(np.arange(H)[:, None] + dr, 0, H - 1); c = np.clip(np.arange(W)[None, :] + dc, 0, W - 1)
            best = np.maximum(best, (he[r, c] - he) / s)
        occ += np.sin(np.maximum(np.arctan(best), 0))
    return np.clip(1 - occ / nd * 1.8, 0, 1)
hb, sb = cfg['hero_bbox'], cfg['skirt_bbox']; W, H = cfg['hero_wh']
# ---- hero heightmap: ETOPO 2022 15" everywhere + Terrarium (USGS/SRTM) high frequencies on land only
et = rs(np.asarray(Image.open(f'{DL}/etopo15.tif')).astype(np.float32), W, H, Image.BICUBIC)
tr = np.load(f'{DL}/terr11_h.npy').astype(np.float32)
land = np.clip(et / 30.0, 0, 1)
h = et + (tr - blur(tr, 5)) * land
h[(et > 0) & (h < 1)] = 1.0
print('hero h', h.min(), h.max())
pack16(h).save(f'{OUT}/hero_h16.png', optimize=False, compress_level=6)
# ---- hero colour: per-pixel cloud-free MODIS composite (mean of the 4-20 % luminance ranks; trade-wind clouds sit on the windward slopes on most days), BMNG where MODIS is missing
files = sorted(glob.glob(f'{DL}/modis/*.jpg')); print('modis dates', len(files))
cw, ch = 2048, 2048
stack = np.stack([np.asarray(Image.open(f).convert('RGB').resize((cw, ch), Image.BILINEAR)).astype(np.float32) / 255 for f in files])
lum = stack @ np.array([0.2126, 0.7152, 0.0722], np.float32); lum = np.where(lum < 0.01, 9.0, lum)  # missing (black) tiles rank last
order = np.argsort(lum, axis=0); n = len(files); lo, hi = int(n * 0.04), max(int(n * 0.20), int(n * 0.04) + 1)
sel = np.take_along_axis(stack, order[lo:hi, ..., None].repeat(3, -1), axis=0).mean(0)
bm = np.asarray(Image.open(f'{DL}/bmng.jpg').convert('RGB').resize((cw, ch), Image.BICUBIC)).astype(np.float32) / 255
col = np.where((sel.sum(-1) < 0.03)[..., None], bm, sel)
landc = rs(h, cw, ch) > 2
# residual cloud specks (bright, grey) on land: treat as holes and fill from the surrounding clear land colour
mx, mn_ = col.max(-1), col.min(-1); lumc = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
cloud = (lumc > 0.30) & ((mx - mn_) / np.maximum(mx, 1e-3) < 0.22)
cloud = rs(cloud.astype(np.float32), cw // 4, ch // 4, Image.BOX); cloud = rs(cloud, cw, ch) > 0.02  # dilate a little
print('cloud px on land', float((cloud & landc).sum()) / max(landc.sum(), 1))
col = fill_sea(col, (landc & ~cloud).astype(np.float32))
col = np.stack([rs(col[..., k], W, H, Image.BICUBIC) for k in range(3)], -1)
Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/hero_color.jpg', quality=90)
del stack, order
# ---- hero AO at half resolution
h2 = rs(h, W // 2, H // 2, Image.BOX)
Image.fromarray((bake_ao(h2, hb, cfg['vex']) * 255).astype(np.uint8)).save(f'{OUT}/hero_ao.png')
# ---- skirt
sw, sh_ = cfg['skirt_wh']
sk = rs(np.asarray(Image.open(f'{DL}/skirt.tif')).astype(np.float32), sw, sh_, Image.BOX)
pack16(sk).save(f'{OUT}/skirt_h16.png')
sbm = np.asarray(Image.open(f'{DL}/skirt_bm.jpg').convert('RGB').resize((sw, sh_), Image.BICUBIC)).astype(np.float32) / 255
sbm = fill_sea(sbm, (sk > 2).astype(np.float32))
Image.fromarray((np.clip(sbm, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/skirt_color.jpg', quality=90)
Image.fromarray((bake_ao(sk, sb, cfg['vex'], 60000) * 255).astype(np.uint8)).save(f'{OUT}/skirt_ao.png')
# ---- Everest (same AWS Terrain Tiles)
ev = np.load(f'{DL}/everest_h.npy').astype(np.float32)
pack16(ev).save(f'{OUT}/everest_h16.png')
# ---- facts from the data: summits and Maui Nui saddles (the level at which two islands' land first connects)
def ll2rc(lon, lat, bb, Wd, Hd): return int(round((bb[3] - lat) / (bb[3] - bb[1]) * (Hd - 1))), int(round((lon - bb[0]) / (bb[2] - bb[0]) * (Wd - 1)))
def peak(a, bb, lon, lat, r=40):
    Hd, Wd = a.shape; rr, cc = ll2rc(lon, lat, bb, Wd, Hd); win = a[max(rr - r, 0):rr + r, max(cc - r, 0):cc + r]
    i = np.unravel_index(np.argmax(win), win.shape); return float(win[i])
def saddle(a, bb, A, B):  # highest level L such that A and B are joined by land (a > L), 4-connected
    from scipy import ndimage
    Hd, Wd = a.shape; ra, rb = ll2rc(*A, bb, Wd, Hd), ll2rc(*B, bb, Wd, Hd)
    def conn(L):
        lab, _ = ndimage.label(a > L); return lab[ra] != 0 and lab[ra] == lab[rb]
    lo, hi = -2000.0, 0.0  # conn(lo) True, conn(hi) False
    while hi - lo > 1: mid = (lo + hi) / 2; (lo, hi) = (mid, hi) if conn(mid) else (lo, mid)
    return round(lo)
crop_bb = [-157.4, 20.4, -155.9, 21.3]
r0, c0 = ll2rc(crop_bb[0], crop_bb[3], hb, W, H); r1, c1 = ll2rc(crop_bb[2], crop_bb[1], hb, W, H); hc = h[r0:r1, c0:c1]
etc = et[r0:r1, c0:c1]
isl = dict(maui=(-156.25, 20.71), molokai=(-156.87, 21.11), lanai=(-156.92, 20.83), kahoolawe=(-156.60, 20.55))
sad = {}
for a_, b_ in [('maui', 'molokai'), ('maui', 'lanai'), ('molokai', 'lanai'), ('maui', 'kahoolawe')]:
    sad[f'{a_}-{b_}'] = dict(hero_grid=saddle(hc, crop_bb, isl[a_], isl[b_]), etopo15=saddle(etc, crop_bb, isl[a_], isl[b_]))
print('saddles', sad)
cfg['facts'] = dict(
    mauna_loa_dem_m=round(peak(h, hb, -155.6054, 19.4756)), mauna_kea_dem_m=round(peak(h, hb, -155.4681, 19.8207)),
    everest_dem_m=round(float(ev.max())), hero_min_m=round(float(h.min())), maui_nui_saddles_m=sad,
    note='DEM summits are smoothed by the grid (Mauna Loa survey 4,169 m, Mauna Kea 4,207 m, Everest 8,849 m).')
cfg['modis_dates'] = [os.path.basename(f)[:-4] for f in files]
json.dump(cfg, open(f'{OUT}/meta.json', 'w'), indent=1); print('done', json.dumps(cfg['facts']))
