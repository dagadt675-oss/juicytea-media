#!/usr/bin/env python3
"""terrain_bake.py: build the data for the drain / terrain stage (lab_drain.html).
Inputs (dl dir): etopo15.tif (ETOPO 2022 15", hero bbox), terr10_h.npy (AWS Terrarium z10 resampled to the same bbox),
modis8.jpg (GIBS MODIS 250 m clear day), bmng08.jpg (GIBS Blue Marble NG 500 m), skirt.tif (ETOPO 2022 30", wide bbox), skirt_bm.jpg.
Outputs (out dir): hero_h16.png / skirt_h16.png (RG 16-bit, h = v/65535*12000-7000 m), hero_light.png / skirt_light.png
(R = soft sun shadow, G = ambient occlusion), hero_color.jpg / skirt_color.jpg (land drape, sea pixels filled), meta.json."""
import sys, json, math, numpy as np
from PIL import Image
DL, OUT = sys.argv[1], sys.argv[2]
cfg = dict(hero_bbox=[-9, 34, -1, 38], skirt_bbox=[-24, 26, 12, 46], hero_wh=[4096, 2048], skirt_wh=[1800, 1000],
           vex=float(sys.argv[3]) if len(sys.argv) > 3 else 3.0, sun_az=float(sys.argv[4]) if len(sys.argv) > 4 else 165.0,
           sun_el=float(sys.argv[5]) if len(sys.argv) > 5 else 26.0, hmin=-7000.0, hrange=12000.0)
def rs(a, w, h, m=Image.BILINEAR): return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((w, h), m))
def blur(a, r):  # box blur via downsample/upsample (cheap low-pass)
    h, w = a.shape; return rs(rs(a, max(2, w // r), max(2, h // r), Image.BOX), w, h)
def pack16(h):
    v = np.clip((h - cfg['hmin']) / cfg['hrange'] * 65535, 0, 65535).astype(np.uint32)
    return Image.fromarray(np.stack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)], -1))
def fill_sea(rgb, land):  # push-pull fill: sea pixels get the colour of nearby land (avoids blue fringes on coastal land)
    lv = [(rgb * land[..., None], land.astype(np.float32))]
    while min(lv[-1][1].shape) > 4:
        c, m = lv[-1]; h, w = m.shape; h2, w2 = h // 2, w // 2
        c2 = c[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).sum((1, 3)); m2 = m[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).sum((1, 3))
        lv.append((c2, m2))
    est = lv[-1][0] / np.maximum(lv[-1][1], 1e-6)[..., None]
    for c, m in reversed(lv[:-1]):
        h, w = m.shape; up = np.stack([rs(est[..., k], w, h) for k in range(3)], -1)
        est = np.where(m[..., None] > 0, c / np.maximum(m, 1e-6)[..., None], up)
    return est
def bake_light(h, bbox, vex, az, el):
    H, W = h.shape; lat = np.linspace(bbox[3], bbox[1], H)[:, None]
    dxm = (bbox[2] - bbox[0]) / W * 111320 * np.cos(np.radians(lat)); dym = (bbox[3] - bbox[1]) / H * 111320
    he = np.maximum(h, -99999) * vex
    def shifted(dr, dc):  # value at (r+dr, c+dc), edge-clamped, dr/dc integer arrays per row allowed
        r = np.clip(np.arange(H)[:, None] + dr, 0, H - 1); c = np.clip(np.arange(W)[None, :] + dc, 0, W - 1); return he[r, c]
    def horizon(dirx, diry, dists):
        best = np.full(h.shape, -1.0, np.float32)
        for s in dists:
            dc = np.rint(dirx * s / dxm).astype(int); dr = np.rint(-diry * s / dym).astype(int)
            best = np.maximum(best, (shifted(dr, dc) - he) / s)
        return np.arctan(best)
    A = math.radians(az); E = math.radians(el)
    dists = np.geomspace(150, 60000, 56)
    hz = horizon(math.sin(A), math.cos(A), dists)
    pen = math.radians(2.2)
    shadow = np.clip((E - hz) / pen + 0.5, 0, 1)
    occ = np.zeros(h.shape, np.float32); nd = 12
    for k in range(nd):
        a = 2 * math.pi * k / nd; hz = horizon(math.sin(a), math.cos(a), np.geomspace(200, 25000, 18)); occ += np.sin(np.maximum(hz, 0))
    ao = np.clip(1 - occ / nd * 1.6, 0, 1)
    return shadow, ao
hb, sb = cfg['hero_bbox'], cfg['skirt_bbox']; W, H = cfg['hero_wh']
# ---- hero heightmap: ETOPO large scale + Terrarium (SRTM) high frequencies on land
et = np.asarray(Image.open(f'{DL}/etopo15.tif')).astype(np.float32)
et = rs(et, W, H)
tr = np.load(f'{DL}/terr10_h.npy').astype(np.float32)
land = np.clip(et / 40.0, 0, 1)  # soft land mask (0 at sea level, 1 above 40 m)
h = et + (tr - blur(tr, 6)) * land
h[(et > 0) & (h < 1)] = 1.0  # never let detail push land below sea level
print('hero h', h.min(), h.max())
pack16(h).save(f'{OUT}/hero_h16.png')
# ---- hero drape: BMNG colour, MODIS luminance detail (pan-sharpen), sea filled
bm = np.asarray(Image.open(f'{DL}/bmng08.jpg').convert('RGB').resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
mo = np.asarray(Image.open(f'{DL}/modis8.jpg').convert('RGB').resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
lm = mo.mean(2); detail = np.clip((lm + 0.02) / (blur(lm, 8) + 0.02), 0.6, 1.5)
col = np.clip(bm * detail[..., None] ** 0.9, 0, 1)
col = fill_sea(col, (et > 2).astype(np.float32))
Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/hero_color.jpg', quality=92)
sh, ao = bake_light(h, hb, cfg['vex'], cfg['sun_az'], cfg['sun_el'])
Image.fromarray(np.stack([(sh * 255).astype(np.uint8), (ao * 255).astype(np.uint8), np.zeros_like(ao, np.uint8)], -1)).save(f'{OUT}/hero_light.png')
# ---- skirt
sw, sh_ = cfg['skirt_wh']
sk = rs(np.asarray(Image.open(f'{DL}/skirt.tif')).astype(np.float32), sw, sh_, Image.BOX)
pack16(sk).save(f'{OUT}/skirt_h16.png')
sbm = np.asarray(Image.open(f'{DL}/skirt_bm.jpg').convert('RGB').resize((sw, sh_), Image.BICUBIC)).astype(np.float32) / 255
sbm = fill_sea(sbm, (sk > 2).astype(np.float32))
Image.fromarray((np.clip(sbm, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/skirt_color.jpg', quality=90)
s2, a2 = bake_light(sk, sb, cfg['vex'], cfg['sun_az'], cfg['sun_el'])
Image.fromarray(np.stack([(s2 * 255).astype(np.uint8), (a2 * 255).astype(np.uint8), np.zeros_like(a2, np.uint8)], -1)).save(f'{OUT}/skirt_light.png')
json.dump(cfg, open(f'{OUT}/meta.json', 'w'), indent=1); print('done', cfg)
