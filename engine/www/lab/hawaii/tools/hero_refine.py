#!/usr/bin/env python3
"""hero_refine.py: finer land colour for the Big Island hero layer (lab/hawaii/data/hero_color.jpg, legacy 'bigisland'), in place.

  python3 -I hero_refine.py --data DATA --base hero_color_base.jpg --comp bi.npz[,mauinui.npz,oahu.npz] --out hero_color.jpg
      [--size 8192] [--ref-m 250] [--chroma 1.0] [--detail 1.0] [--min-looks 1.5] [--preview DIR]

The base colour (hawaii_bake.py: MODIS 250 m / Blue Marble composite, 4096^2) is the reference and keeps the tone: it is resized to
--size (bicubic) and, on land inside each island box, detail from a NASA HLS 30 m Fmask composite on the same grid (hls_hero.py) is
transferred onto it (detail_bake.fuse's method: reference low-pass at ref_m times the imagery's luminance ratio to its own low-pass,
plus its residual chroma times one factor; where the imagery disagrees at that scale, the kept neighbours' colour). --chroma scales
that chroma factor (0 = luminance detail only), --detail the luminance ratio's log amplitude. Where the composite has few clear looks
(windward cloud) the imagery's share fades (--min-looks), and land it never saw clear takes the kept neighbours' colour. Sea texels near the coast are re-filled from the new land colour (push-pull,
as hawaii_bake.py). Same grid, bbox and conventions: only the colour texture's size and content change.
The base: when --base is missing, or --out is smaller than --size (a fresh hawaii_bake.py colour), --out is first copied to --base.
Writes meta.json in --data: res (colour texel and source, m; heights unchanged), colour_refine (passes, scenes, parameters, stats)
and sources (make_index.py copies all three into regions.json 'bigisland')."""
import sys, os, json, math, argparse, time, shutil
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import region_bake as rb
import detail_bake as db

Image.MAX_IMAGE_PIXELS = 400_000_000
sstep = db.sstep

def fuse(img, ref, land, px_m, ref_m, cfac=1.0, dfac=1.0, wl=None):
    """detail_bake.fuse with two knobs (cfac on the chroma factor, dfac on the luminance ratio's log amplitude) and the imagery's
    low-pass over land only (img is NaN off land): no dark sea halo on coastal land."""
    v = np.isfinite(img).all(-1); s = max(1.0, 0.5 * ref_m / px_m)
    rl = ndimage.gaussian_filter(ref, (s, s, 0)); il = db.nan_gauss(img, v, s)
    Li, Lr = rb.lum(il), rb.lum(rl); st = {}
    meas = v & land & (ndimage.distance_transform_edt(land) > 3) & (Lr > 0.03)
    g = float(np.median(Lr[meas]) / max(float(np.median(Li[meas])), 1e-3))
    ci = np.linalg.norm(il - Li[..., None], axis=-1) * g; cr = np.linalg.norm(rl - Lr[..., None], axis=-1)
    beta = float(np.clip(np.median(cr[meas]) / max(float(np.median(ci[meas])), 1e-4), 0.4, 1.2)) * cfac
    n = np.nan_to_num(img) * g; nl = il * g; Ln = rb.lum(n); Lnl = rb.lum(nl)
    D = np.clip(Ln / np.maximum(Lnl, 1e-3), 0.35, 2.5)
    if dfac != 1.0: D = np.exp(np.log(D) * dfac)
    out = rl * D[..., None] + beta * (n - nl * D[..., None])
    ratio = Lnl / np.maximum(Lr, 1e-3)
    keep = v & land
    wv = np.clip(ndimage.gaussian_filter(keep.astype(np.float32), 1.0), 0, 1) * keep
    agree = np.clip(ndimage.gaussian_filter((sstep(0.42, 0.65, ratio) * (1 - sstep(1.7, 2.4, ratio))).astype(np.float32), max(1.0, 0.5 * s)), 0, 1)
    # wl: the share of the imagery to trust by its number of clear looks; the rest of the ground it covers, and land it never saw clear
    # (holes), take the kept neighbours' colour (45-400 m around), else the reference
    wl = np.ones_like(wv) if wl is None else wl
    hole = (land & ~v).astype(np.float32)
    wk = wv * agree * wl; wf = wv * (1 - agree * wl) + hole
    fill = db.nc_fill(out, wk * land, ref, px_m) if (wf > 0.02).any() else ref
    out = ref * (1 - wv - hole)[..., None] + out * wk[..., None] + fill * wf[..., None]
    st.update(gain=round(g, 3), chroma=round(beta, 3), imagery_pct=round(float(wk[land].mean() * 100), 1), filled_pct=round(float(wf[land].mean() * 100), 1),
              dark_pct=round(float(((ratio < 0.6) & keep).sum() / max(keep.sum(), 1) * 100), 2), bright_pct=round(float(((ratio > 1.6) & keep).sum() / max(keep.sum(), 1) * 100), 2))
    return np.clip(out, 0, 1).astype(np.float32), st, wk, wf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True); ap.add_argument('--base', required=True); ap.add_argument('--comp', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--size', type=int, default=8192); ap.add_argument('--ref-m', type=float, default=250.0)
    ap.add_argument('--chroma', type=float, default=1.0); ap.add_argument('--detail', type=float, default=1.0); ap.add_argument('--min-looks', type=float, default=1.5)
    ap.add_argument('--preview', default=None); ap.add_argument('--quality', type=int, default=90)
    a = ap.parse_args(); t0 = time.time()
    meta = json.load(open(f'{a.data}/meta.json')); hb = meta['hero_bbox']; S = a.size
    if os.path.exists(a.out) and (not os.path.exists(a.base) or Image.open(a.out).size[0] < S):
        shutil.copyfile(a.out, a.base)   # a fresh hawaii_bake.py colour: it is the base (the reference tone)
    base = Image.open(a.base).convert('RGB')
    up = np.array(base.resize((S, S), Image.BICUBIC) if base.size != (S, S) else base)   # uint8, the reference at the target size
    h16 = np.asarray(Image.open(f'{a.data}/hero_h16.png')).astype(np.float32); hh = (h16[..., 0] * 256 + h16[..., 1]) / 65535 * meta['hrange'] + meta['hmin']
    stats = {}; rec = {}
    for cp in a.comp.split(','):
        d = np.load(cp); r0, r1, c0, c1 = [int(x) for x in d['rc']]; assert int(d['size']) == S, 'composite grid size differs'
        img = d['col'].astype(np.float32); cnt = d['count'].astype(np.float32); H, W = img.shape[:2]
        f = hh.shape[0] / S; yy = (np.arange(r0, r1) + 0.5) * f - 0.5; xx = (np.arange(c0, c1) + 0.5) * f - 0.5
        hbox = ndimage.map_coordinates(hh, np.meshgrid(yy, xx, indexing='ij'), order=1, mode='nearest'); land = hbox > 2
        bb = [float(x) for x in d['bbox']]; lat = (bb[1] + bb[3]) / 2; px_m = (bb[2] - bb[0]) / W * 111320 * math.cos(math.radians(lat))
        img[~land] = np.nan
        ref = up[r0:r1, c0:c1].astype(np.float32) / 255.0
        # few clear looks (windward cloud): the imagery's share, faded over about 2 texels (1 look 0.35, 2 looks 0.9 at the default 1.5)
        wl = np.clip(ndimage.gaussian_filter(sstep(a.min_looks - 1.5, a.min_looks + 1.0, cnt).astype(np.float32), 1.0), 0, 1)
        out, st, wk, wf = fuse(img, ref, land, px_m, a.ref_m, a.chroma, a.detail, wl)
        # sea texels: the push-pull fill of the new land colour within 6 texels of the coast (the stage draws the colour map from -6 m up)
        near = ~land & (ndimage.distance_transform_edt(~land) <= 6)
        fs = rb.fill_sea(out, land)
        tw = (sstep(6.0, 3.0, ndimage.distance_transform_edt(~land)) * near)[..., None]
        out = out * (1 - tw) + fs * tw
        st.update(box=os.path.basename(cp), texel_m=round(px_m, 1), looks_faded_pct=round(float((1 - wl[land]).mean() * 100), 1), hole_pct=round(float((land & ~np.isfinite(img).all(-1)).sum() / max(land.sum(), 1) * 100), 2))
        print(json.dumps(st), flush=True); stats[os.path.basename(cp)] = st
        rec[os.path.splitext(os.path.basename(cp))[0]] = dict(bbox=[round(float(x), 5) for x in bb], rc=[int(x) for x in d['rc']],
            passes=[str(x) for x in d['passes']], scenes=[str(x) for x in d['used']], looks=dict(never_clear_pct=round(float((cnt[land] == 0).mean() * 100), 2),
            under3_pct=round(float((cnt[land] < 3).mean() * 100), 1), median=float(np.median(cnt[land]))), fuse=st)
        up[r0:r1, c0:c1] = np.clip(np.round(out * 255), 0, 255).astype(np.uint8)
        if a.preview:
            os.makedirs(a.preview, exist_ok=True); nm = os.path.splitext(os.path.basename(cp))[0]
            Image.fromarray(np.clip(np.round(out * 255), 0, 255).astype(np.uint8)).save(f'{a.preview}/{nm}_out.png')
            Image.fromarray(np.clip(np.round(ref * 255), 0, 255).astype(np.uint8)).save(f'{a.preview}/{nm}_ref.png')
            Image.fromarray(np.stack([np.round(wk * 255), np.round(wf * 255), np.round(wl * 255)], -1).astype(np.uint8)).save(f'{a.preview}/{nm}_w.png')   # R kept, G filled, B looks weight
    tmp = a.out + '.tmp.jpg'
    Image.fromarray(up).save(tmp, quality=a.quality); os.replace(tmp, a.out)
    prm = dict(size=S, ref_m=a.ref_m, chroma=a.chroma, detail=a.detail, min_looks=a.min_looks, quality=a.quality)
    lat = (hb[1] + hb[3]) / 2; W0 = meta['hero_wh'][0]
    meta['res'] = dict(height_m=round((hb[2] - hb[0]) / W0 * 111320 * 0.94, 1), height_src_m=70,
                       colour_texel_m=round((hb[2] - hb[0]) / S * 111320 * math.cos(math.radians(lat)), 1), colour_src_m=30, colour_wh=[S, S],
                       colour_src_note='30 m (NASA HLS v2) detail on the land of the refined boxes only (' + ', '.join(rec) + '); the rest of the layer and the sea stay MODIS 250 m / Blue Marble')
    meta['colour_refine'] = dict(tool='lab/hawaii/tools/hls_hero.py + hero_refine.py', date=time.strftime('%Y-%m-%d'), base='hero_color_base.jpg (hawaii_bake.py, MODIS 250 m / Blue Marble, the tone)',
                                 method='detail transfer: reference tone and colour at ref_m, HLS detail finer; few clear looks fade to the reference, never-clear land takes the kept neighbours',
                                 source='NASA HLS v2 (HLSS30 + HLSL30) via Microsoft Planetary Computer, Fmask-clear per-texel median', params=prm, boxes=rec)
    meta['sources'] = ['ETOPO 2022 15"', 'Terrarium z11 (land)', 'GIBS MODIS 250 m composite', 'NASA HLS v2 30 m (Big Island land detail)']
    tm = f'{a.data}/meta.json.tmp'; json.dump(meta, open(tm, 'w'), indent=1, ensure_ascii=False); os.replace(tm, f'{a.data}/meta.json')
    print(f'wrote {a.out} ({os.path.getsize(a.out) / 1e6:.1f} MB) in {time.time() - t0:.0f} s', flush=True)

if __name__ == '__main__': main()
