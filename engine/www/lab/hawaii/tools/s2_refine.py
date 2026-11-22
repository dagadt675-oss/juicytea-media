#!/usr/bin/env python3
"""s2_refine.py: finer colour (and optionally finer heights) for high-mountain regions baked by region_bake.py, in place (round 3,
2026-11-16: everest and everest_wide, the s064 summit gag). Run after region_bake.py (rebuild_regions.sh does).

  python3 -I s2_refine.py --spec SPEC.json [--only NAME[,NAME...]] --out DATA --dl DL [--keep]

Spec entries with "baker": "s2_refine.py" (detail_bake.py skips them) and
  "detail": {"colour": {"source": "s2", "long": 2048, "months": [[from, to], ...], "n": 12, "edge_m": 200, "edge_to": NAME?},
             "height": {"source": "terrarium", "z": 13, "wh": [W, H]}?}
Same conventions as detail_bake.py's in-place re-bake (name, bbox, files, stack unchanged; color_base.jpg / h16_base.png / ao_base.png
keep the base bake as the reference, so a re-run never compounds; cres.png; meta res / detail), and its detail transfer (fuse): the
region's own graded HLS colour keeps the tone and the colour at its own scale, the imagery adds only what is finer.

Colour: ESA Copernicus Sentinel-2 L2A (Planetary Computer, free and open; credit 'Contains modified Copernicus Sentinel data'), the
per-pixel median of SCL-clear observations (vegetation, bare, water, unclassified, snow) in the same pre-monsoon window as the HLS
reference (snow in season, real snow). What differs from detail_bake.sentinel2 (made for Midway's small atoll):
  * the +1000 reflectance offset is keyed on each item's s2:processing_baseline (04.00 and later), not on the acquisition date: the
    Planetary Computer serves reprocessed items (baseline 05.x) for older dates too, and a 2019 scene with an offset read as none
    would be 0.1 too bright;
  * reprocessed duplicates (same date and MGRS tile, two processing runs) are one observation (the newest s2:generation_time), and
    items of one date (adjacent tiles of one pass, which overlap) are merged, so no pass counts twice in the median;
  * scenes are chosen per window by a quick SCL screen at a quarter of the size, greedily until every pixel has n clear passes (a
    tile that covers only a sliver of the box is still taken where it is the only one), not by the tile-wide cloud figure;
  * the imagery is read straight at the target grid (area average) in windows of at most 2048 px when the target is coarser than
    10 m (everest_wide: 88 km at 22 m), at 10 m and resized otherwise;
  * the display curve has no knee: region_bake.HLS_LUT maps reflectance 0.70 and above to 1.0 (sunlit snow is 0.75-0.95), which
    would flatten every snowfield to one value and leave the detail transfer nothing to transfer there. Above 0.29 the curve goes
    on with its own slope (0.68 per unit reflectance). Only ratios and residuals of the imagery are used, so the tone stays the
    reference's (whose snow the region's gain 0.7 holds at 0.70).
Heights (optional, e.g. everest_wide): Mapzen Terrarium at a finer zoom (SRTM 30 m in the Himalaya), packed in the fixed -8000..9000 m
range (hmin/hrange unchanged, so regions.json and the folder need not change together); AO re-baked, facts re-measured.
Needs numpy, scipy, PIL and network to planetarycomputer.microsoft.com (and s3.amazonaws.com for heights)."""
import sys, os, io, json, math, time, shutil, argparse, warnings, concurrent.futures as cf
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import region_bake as rb   # fetch, cached, post_json, PC, HLS_LUT, lum, grid_axes, terrarium, bake_ao, pack16, facts
import detail_bake as db   # read_h16, resample_bb, px_size, size_of, fuse, edge_ramp, sstep, cres_write, cres_read, resize1

Image.MAX_IMAGE_PIXELS = 400_000_000
LOG = print
CLEAR = [4, 5, 6, 7, 11]   # SCL: vegetation, not vegetated, water, unclassified, snow and ice
# the HLS display curve (region_bake.HLS_LUT) without its knee at 0.70: the same points up to 0.29, then its own 0.29-0.70 slope onward
_x, _y = rb.HLS_LUT
_k = (_y[-2] - _y[-3]) / (_x[-2] - _x[-3])
LUT_NK = (np.array(list(_x[:-1]) + [1.5]), np.array(list(_y[:-2]) + [_y[-3] + _k * (_x[-2] - _x[-3]), _y[-3] + _k * (1.5 - _x[-3])]))

def to_display_nk(refl):
    out = np.interp(np.nan_to_num(refl, nan=0.0), *LUT_NK).astype(np.float32); out[~np.isfinite(refl)] = np.nan
    return out

def s2_items(bb, ranges):
    """L2A items over bb in the date ranges, one per (date, MGRS tile): the newest processing."""
    best = {}
    for m0, m1 in ranges:
        body = dict(collections=['sentinel-2-l2a'], bbox=[round(x, 6) for x in bb], datetime=f'{m0}T00:00:00Z/{m1}T23:59:59Z', limit=500)
        url = f'{rb.PC}/stac/v1/search'
        for _ in range(20):
            d = rb.post_json(url, body)
            for f in d['features']:
                p = f['properties']; k = (p['datetime'][:10], p.get('s2:mgrs_tile', f['id'].split('_')[5]))
                it = dict(id=f['id'], date=k[0], tile=k[1], cloud=float(p.get('eo:cloud_cover', 100)), bbox=f['bbox'],
                          baseline=float(p.get('s2:processing_baseline', '0') or 0), gen=p.get('s2:generation_time', ''))
                if k not in best or it['gen'] > best[k]['gen']: best[k] = it
            nxt = [l for l in d.get('links', []) if l.get('rel') == 'next']
            if not nxt: break
            url = nxt[0]['href']; body = nxt[0].get('body', body)
    return sorted(best.values(), key=lambda it: (it['cloud'], it['date']))

def npy(it, assets, sb, w, h, path, resampling):
    q = '&'.join(f'assets={a}' for a in assets)
    url = (f'{rb.PC}/data/v1/item/bbox/{sb[0]:.7f},{sb[1]:.7f},{sb[2]:.7f},{sb[3]:.7f}/{w}x{h}.npy?collection=sentinel-2-l2a&item={it["id"]}'
           f'&{q}&resampling={resampling}')
    return np.load(io.BytesIO(rb.cached(path, url, tries=5, timeout=600)), allow_pickle=False)

def overlaps(a, b): return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

def window_composite(items, sb, w, h, dl, n, cap):
    """per-pixel median reflectance (h, w, 3; NaN = never clear) over sub-box sb, and stats."""
    os.makedirs(dl, exist_ok=True)
    cand = [it for it in items if overlaps(it['bbox'], sb)]
    by_tile = {}
    for it in cand: by_tile.setdefault(it['tile'], []).append(it)
    cand = [it for t in by_tile.values() for it in t[:3 * n]]   # the clearest by tile-wide cloud cover, per tile
    qw, qh = max(16, w // 4), max(16, h // 4)
    def screen(it):
        try: s = npy(it, ['SCL'], sb, qw, qh, f'{dl}/q_{it["id"]}.npy', 'nearest')
        except Exception as e: LOG(f'   screen {it["id"]}: {str(e)[:120]}'); return it, None
        return it, (s[-1] > 0) & np.isin(s[0].astype(int), CLEAR)
    with cf.ThreadPoolExecutor(4) as ex: scr = [(it, m) for it, m in ex.map(screen, cand) if m is not None and m.mean() > 0.01]
    scr.sort(key=lambda r: -r[1].sum())
    cnt = np.zeros((qh, qw), np.int32); chosen = []
    for it, m in scr:   # greedy: take a pass while it adds clear ground where fewer than n passes are clear
        if len(chosen) >= cap: break
        if (m & (cnt < n)).sum() > 0.002 * m.size: chosen.append(it); cnt += m
    LOG(f'   window {w}x{h}: {len(cand)} candidates, {len(scr)} with clear ground, {len(chosen)} chosen; screen: pixels with < 3 clear '
        f'{(cnt < 3).mean() * 100:.2f} %, median clear passes {int(np.median(cnt))}')
    def full(it):
        a = npy(it, ['B04', 'B03', 'B02'], sb, w, h, f'{dl}/rgb_{it["id"]}.npy', 'average')
        s = npy(it, ['SCL'], sb, w, h, f'{dl}/scl_{it["id"]}.npy', 'nearest')
        ok = (a[-1] > 0) & (s[-1] > 0) & np.isin(s[0].astype(int), CLEAR)
        off = 1000 if it['baseline'] >= 4.0 else 0   # L2A processing baseline 04.00 and later: DN = 10000 * reflectance + 1000
        v = np.clip(np.moveaxis(a[:3], 0, -1).astype(np.int32) - off, 1, 65535).astype(np.uint16)
        return it, v, ok
    dates = {}
    with cf.ThreadPoolExecutor(4) as ex:
        for it, v, ok in ex.map(full, chosen):   # one layer per date: adjacent tiles of one pass overlap
            if it['date'] not in dates: dates[it['date']] = [np.zeros((h, w, 3), np.uint16), np.zeros((h, w), bool), []]
            L = dates[it['date']]; new = ok & ~L[1]; L[0][new] = v[new]; L[1] |= new; L[2].append(it['id'])
    keys = sorted(dates); S = np.stack([dates[k][0] for k in keys]) if keys else np.zeros((0, h, w, 3), np.uint16)
    V = np.stack([dates[k][1] for k in keys]) if keys else np.zeros((0, h, w), bool)
    med = np.full((h, w, 3), np.nan, np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for r in range(0, h, 64):
            f = S[:, r:r + 64].astype(np.float32) / 10000.0; f[~V[:, r:r + 64]] = np.nan
            med[r:r + 64] = np.nanmedian(f, 0)
    nc = V.sum(0)
    st = dict(passes=len(keys), items=sum(len(dates[k][2]) for k in keys), dates=keys, clear_median=int(np.median(nc)) if nc.size else 0,
              baselines=sorted({f'{it["baseline"]:05.2f}' for it in chosen}))
    return med, nc, st

def sentinel2_grid(bb, W, H, dl, ranges, n=12, cap=28, T=2048):
    """the S2 L2A median reflectance on the W x H grid over bb: read at the target grid in windows of at most T px when its texel
    is coarser than 12 m, else at 10 m and resized (bicubic, holes kept)."""
    items = s2_items(bb, ranges)
    LOG(f'  s2: {len(items)} L2A items (one per date and tile) in {len(ranges)} windows; tiles {sorted({it["tile"] for it in items})}')
    pxw, pxh = db.px_size(bb, W, H)
    if (pxw + pxh) / 2 >= 12.0: FW, FH = W, H
    else:
        lat = (bb[1] + bb[3]) / 2; FW = int(round((bb[2] - bb[0]) * 111320 * math.cos(math.radians(lat)) / 10)); FH = int(round((bb[3] - bb[1]) * 111320 / 10))
    nx, ny = math.ceil(FW / T), math.ceil(FH / T)
    cols = [round(FW * i / nx) for i in range(nx + 1)]; rows = [round(FH * j / ny) for j in range(ny + 1)]
    out = np.full((FH, FW, 3), np.nan, np.float32); ncl = np.zeros((FH, FW), np.int16); stats = []
    dx, dy = (bb[2] - bb[0]) / FW, (bb[3] - bb[1]) / FH
    for j in range(ny):
        for i in range(nx):
            r0, r1, c0, c1 = rows[j], rows[j + 1], cols[i], cols[i + 1]
            sb = [bb[0] + c0 * dx, bb[3] - r1 * dy, bb[0] + c1 * dx, bb[3] - r0 * dy]
            t0 = time.time(); wdl = f'{dl}/w{j}_{i}'
            med, nc, st = window_composite(items, sb, c1 - c0, r1 - r0, wdl, n, cap)
            out[r0:r1, c0:c1] = med; ncl[r0:r1, c0:c1] = nc; st['window'] = [r0, c0, r1, c1]; stats.append(st)
            LOG(f'   window {j},{i}: {st["passes"]} passes ({st["items"]} items), median clear {st["clear_median"]}, never clear '
                f'{(nc == 0).mean() * 100:.2f} %, {time.time() - t0:.0f} s')
            if not KEEP: shutil.rmtree(wdl, ignore_errors=True)   # the window's downloads (about 20 MB per pass)
    return out, ncl, (FW, FH), stats

def edge_target(name, OUT, bb, CW, CH):
    """another region's final colour (and real resolution) resampled onto this grid: the fade target at the grid edge, where that
    region (the next layer out) meets this one."""
    m = json.load(open(f'{OUT}/{name}/meta.json')); ob = m['bbox']
    if not (bb[0] >= ob[0] and bb[1] >= ob[1] and bb[2] <= ob[2] and bb[3] <= ob[3]): raise SystemExit(f'edge_to {name} does not contain the grid')
    c = np.asarray(Image.open(f'{OUT}/{name}/{m["files"]["color"]}').convert('RGB')).astype(np.float32) / 255
    col = db.resample_bb(c, ob, bb, CW, CH, order=3).clip(0, 1)
    if m['files'].get('cres'):
        cr = np.asarray(Image.open(f'{OUT}/{name}/{m["files"]["cres"]}')).astype(np.float32)
        res = 2.0 ** (db.resample_bb(cr, ob, bb, CW, CH) / 25.0 - 2.0)
    else: res = np.full((CH, CW), m.get('res', {}).get('colour_src_m', 30.0), np.float32)
    return col, res

def repair_ref(img, ref, land, px_m, ref_m):
    """the reference where it is much darker than the imagery at its own scale (ratio over 1.5-2.2): HLS holes the base filled near
    black and HLS shadow the S2 median does not have (the summit pyramid, 2026-11-16). detail_bake.fuse would treat that ground as
    'imagery much brighter: cloud' and fill it from its neighbours, which left dark contour rings around every hole (its thresholds
    crossed on the hole's blurred rim). An SCL-clear median has no cloud left, so there the reference takes the imagery's tone at the
    reference's scale (times the one luminance gain) in the grade's own median hue, blended smoothly; fuse then adds the detail."""
    v = np.isfinite(img).all(-1); s = max(1.0, 0.5 * ref_m / px_m)
    rl = ndimage.gaussian_filter(ref, (s, s, 0)); il = db.nan_gauss(img, v, s); Li, Lr = rb.lum(il), rb.lum(rl)
    meas = v & land & (Lr > 0.03)
    if meas.sum() < 500: return ref, dict(repaired_pct=0.0)
    g = float(np.median(Lr[meas]) / max(float(np.median(Li[meas])), 1e-3)); q = Li * g / np.maximum(Lr, 1e-3)
    ok = meas & (q > 0.77) & (q < 1.3)
    tint = np.median(rl[ok] / np.maximum(Lr[ok], 1e-3)[:, None], 0).astype(np.float32)
    wr = np.clip(ndimage.gaussian_filter((db.sstep(1.5, 2.2, q) * (v & land)).astype(np.float32), s), 0, 1)
    alt = np.clip((Li * g)[..., None] * tint[None, None, :], 0, 1)
    out = ref * (1 - wr[..., None]) + alt * wr[..., None]
    st = dict(repaired_pct=round(float((wr > 0.5)[land].mean() * 100), 2) if land.any() else 0.0, repair_gain=round(g, 3), repair_tint=[round(float(x), 3) for x in tint])
    LOG(f'  reference repaired (much darker than the imagery at the {ref_m:.0f} m scale: HLS holes and shadow) on {st["repaired_pct"]} % of land, tint {st["repair_tint"]}')
    return out.astype(np.float32), st

KEEP = False

def bake(R, OUT, DLROOT, keep=False):
    global KEEP; KEEP = keep
    t0 = time.time(); name = R['name']; bb = [float(x) for x in R['bbox']]; det = R.get('detail', {})
    dl = f'{DLROOT}/{name}_s2'; od = f'{OUT}/{name}'; os.makedirs(dl, exist_ok=True)
    LOG(f'== {name} (in place, s2_refine) bbox {bb}')
    meta = json.load(open(f'{od}/meta.json')); W0, H0 = meta['wh']
    if 'detail' not in meta:   # fresh from region_bake: keep the base bake as the reference for this and every later re-run
        for f, b in (('h16', 'h16_base.png'), ('color', 'color_base.jpg'), ('ao', 'ao_base.png')): shutil.copyfile(f'{od}/{meta["files"][f]}', f'{od}/{b}')
        meta['base'] = dict(wh=[W0, H0], px_m=meta['px_m'], sources=meta['sources'], facts=meta['facts'], hmin=meta['hmin'], hrange=meta['hrange'])
    else: meta['sources'] = meta['base']['sources']
    base = meta['base']; W0, H0 = base['wh']
    bh = db.read_h16(f'{od}/h16_base.png', base.get('hmin', rb.HMIN), base.get('hrange', rb.HRANGE))
    pcol = np.asarray(Image.open(f'{od}/color_base.jpg').convert('RGB')).astype(np.float32) / 255
    # ---- heights: the base (byte-identical) or a finer Terrarium zoom
    hcfg = det.get('height'); hsrc = {}
    if hcfg and hcfg.get('source') == 'terrarium':
        W, H = hcfg['wh']; hdl = f'{dl}/terr'; os.makedirs(hdl, exist_ok=True)
        h = rb.terrarium(hcfg['z'], bb, W, H, hdl); h = np.where(np.isfinite(h), h, db.resample_bb(bh, bb, bb, W, H)).astype(np.float32)
        px_m = sum(db.px_size(bb, W, H)) / 2
        z = hcfg['z']; src_m = 156543.03 / 2 ** z * math.cos(math.radians((bb[1] + bb[3]) / 2))
        hsrc = dict(id=f'terrarium_z{z}', res_m=round(src_m, 1), note=f'Mapzen Terrarium z{z} (SRTM 30 m here), {W}x{H}')
        meta['sources'] = list(base['sources']) + [hsrc]
        rb.pack16(h).save(f'{od}/h16.png', compress_level=6)   # fixed -8000..9000 m (regions.json hmin / hrange unchanged)
        meta['hmin'], meta['hrange'] = rb.HMIN, rb.HRANGE
        ao = rb.bake_ao(h, bb, px_m, R.get('ao') == 'tangent'); Image.fromarray((np.clip(ao, 0, 1) * 255).astype(np.uint8)).save(f'{od}/ao.png')
        d = db.resample_bb(bh, bb, bb, W, H) - h
        LOG(f'  heights {W}x{H} ({px_m:.1f} m) from z{z}: {h.min():.0f}..{h.max():.0f} m; |new - base| p50 {np.median(np.abs(d)):.1f} m, p99 {np.percentile(np.abs(d), 99):.1f} m')
    else:
        h = bh; W, H = W0, H0; px_m = base['px_m']
        shutil.copyfile(f'{od}/h16_base.png', f'{od}/h16.png'); shutil.copyfile(f'{od}/ao_base.png', f'{od}/ao.png')
        meta['hmin'], meta['hrange'] = base.get('hmin', rb.HMIN), base.get('hrange', rb.HRANGE)
    # ---- colour
    ccfg = det['colour']; CW, CH = db.size_of(ccfg, bb, W, H)
    ref = db.resample_bb(pcol, bb, bb, CW, CH, order=3).clip(0, 1)
    cpx = sum(db.px_size(bb, CW, CH)) / 2
    ref_m = ccfg.get('ref_m') or max(30.0, sum(db.px_size(bb, pcol.shape[1], pcol.shape[0])) / 2)   # HLS 30 m, or the base's texel if coarser
    hc = db.resample_bb(h, bb, bb, CW, CH); land = hc > 0.5
    comp_path = f'{dl}/{name}_s2_{CW}x{CH}.npz'
    if os.path.exists(comp_path):
        z = np.load(comp_path, allow_pickle=False); comp, ncl = z['comp'], z['ncl']; st2 = json.loads(str(z['st'])); LOG(f'  s2 composite reused: {comp_path}')
    else:
        comp, ncl, (FW, FH), wst = sentinel2_grid(bb, CW, CH, dl, ccfg.get('months'), ccfg.get('n', 12), ccfg.get('cap', 28))
        if (FW, FH) != (CW, CH):
            comp = rb.resize_nan(comp, CW, CH); ncl = np.round(db.resize1(ncl.astype(np.float32), CW, CH)).astype(np.int16)
        dates = sorted({d for s in wst for d in s['dates']})
        st2 = dict(passes=len(dates), dates=dates, windows=len(wst), baselines=sorted({b for s in wst for b in s['baselines']}), read_wh=[FW, FH])
        np.savez(comp_path, comp=comp.astype(np.float32), ncl=ncl, st=json.dumps(st2))
    L = rb.lum(np.nan_to_num(comp)); fin = np.isfinite(comp).all(-1)
    hi6, hi65 = land & (hc >= 6000), land & (hc >= 6500)
    st2.update(never_clear_pct=round(float((~fin).mean() * 100), 2),
               never_clear_above_6500_pct=round(float((~fin[hi65]).mean() * 100), 2) if hi65.any() else None,
               refl_ge_070_above_6000_pct=round(float(((L >= 0.70) & fin)[hi6].sum() / max((fin & hi6).sum(), 1) * 100), 1) if hi6.any() else None,
               clear_passes_median=int(np.median(ncl)))
    LOG(f'  s2 {CW}x{CH}: {st2["passes"]} passes, never clear {st2["never_clear_pct"]} % (above 6,500 m {st2["never_clear_above_6500_pct"]} %); '
        f'reflectance >= 0.70 on {st2["refl_ge_070_above_6000_pct"]} % of the clear ground above 6,000 m (the HLS curve would clip it)')
    img = to_display_nk(np.where(fin[..., None], comp, np.nan))
    ref, rst = repair_ref(img, ref, land, cpx, ref_m) if ccfg.get('repair', True) else (ref, {})
    col, st, ref, wimg = db.fuse(img, ref, land, cpx, ref_m, 10.0); st.update(rst)
    cmeta = dict(source='Copernicus Sentinel-2 L2A 10 m, median of SCL-clear observations (Planetary Computer)', curve='HLS display curve without the 0.70 knee',
                 **{k: v for k, v in st2.items()}, **st)
    res_ref = np.full((CH, CW), ref_m, np.float32)
    res_map = 2.0 ** (wimg * np.log2(10.0) + (1 - wimg) * np.log2(np.maximum(res_ref, 0.25)))
    # fade to the reference at the grid edge (the base bake's colour, or edge_to: the next layer out's final colour), which the next
    # layer meets
    edge_m = ccfg.get('edge_m', det.get('edge_m', 200)); e = db.edge_ramp(CH, CW, int(round(edge_m / cpx)))
    tgt, tres = (edge_target(ccfg['edge_to'], OUT, bb, CW, CH) if ccfg.get('edge_to') else (ref, res_ref))
    col = tgt * (1 - e[..., None]) + col * e[..., None]; res_map = tres * (1 - e) + res_map * e
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(f'{od}/color.jpg', quality=90)
    # cres: the imagery's 10 m where it was kept, the reference's scale where it was not (never clear, filled) and at the edge fade.
    # No smoothness rule: detail_bake.py's (local contrast at 3-8 m under 3 %: the photo shows nothing of 8 m or less) is made for
    # NAIP's 0.6 m and calls every S2 texel smooth (97.7 % of everest even at 10-30 m: snow is smooth), which would hand the whole
    # region back to the procedural octaves up to 36 m; an SCL-clear median has no shadow or cloud fill left to find
    db.cres_write(f'{od}/cres.png', res_map)
    cmeta['cres_10m_pct'] = round(float((res_map < 12.0)[land].mean() * 100), 1) if land.any() else 0.0
    LOG(f'  cres: 10 m on {cmeta["cres_10m_pct"]} % of land')
    # ---- meta (detail_bake.py's in-place shape)
    meta.update(wh=[W, H], px_m=round(px_m, 2), files=dict(h16='h16.png', ao='ao.png', color='color.jpg', cres='cres.png'),
                res=dict(height_m=round(px_m, 2), height_src_m=hcfg.get('src_m', 30.0) if hcfg else R.get('height_src_m', 30.0), colour_texel_m=round(cpx, 2),
                         height_interp=[], colour_src_m=10.0, colour_wh=[CW, CH]),
                detail=dict(colour=dict(ccfg, **cmeta), height=hcfg or {}, baker='s2_refine.py'), bake_s=round(time.time() - t0, 1), baked=time.strftime('%Y-%m-%d'))
    meta['colour'] = dict(meta.get('colour', {}), ortho=dict(ccfg, **{k: v for k, v in cmeta.items() if k != 'dates'}))
    meta['facts'] = rb.facts(h, bb, R.get('facts', {}), px_m) if hcfg else base['facts']
    meta['bytes'] = {k: os.path.getsize(f'{od}/{v}') for k, v in meta['files'].items()}
    json.dump(meta, open(f'{od}/meta.json', 'w'), indent=1, ensure_ascii=False)
    if not keep:
        for f in os.listdir(dl):
            p = f'{dl}/{f}'
            if os.path.isdir(p): shutil.rmtree(p, ignore_errors=True)
            elif not f.endswith('.npz'): os.remove(p)
    LOG(f'  done {name} in {time.time() - t0:.0f} s: colour {CW}x{CH} {cpx:.2f} m (ref {ref_m:.0f} m), heights {W}x{H} {px_m:.1f} m, '
        f'{sum(meta["bytes"].values()) / 1e6:.1f} MB')
    return meta

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True); ap.add_argument('--only'); ap.add_argument('--out', required=True); ap.add_argument('--dl', required=True)
    ap.add_argument('--keep', action='store_true')
    A = ap.parse_args()
    S = json.load(open(A.spec)); only = set(A.only.split(',')) if A.only else None
    todo = [R for R in S['regions'] if R.get('baker') == 's2_refine.py' and (not only or R['name'] in only)]
    # outer layers first: an inner layer's edge_to reads the outer layer's final colour
    todo.sort(key=lambda R: 0 if not R.get('detail', {}).get('colour', {}).get('edge_to') else 1)
    for R in todo: bake(R, A.out, A.dl, A.keep)
