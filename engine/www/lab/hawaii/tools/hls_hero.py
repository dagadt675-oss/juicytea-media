#!/usr/bin/env python3
"""hls_hero.py: NASA HLS v2 (S30 + L30) per-pixel median of Fmask-clear observations over one island box of the hero grid
(lab/hawaii/data, hero bbox), at the hero colour grid's resolution (default 8192^2: about 57 m), for hero_refine.py.

  python3 -I hls_hero.py --data DATA --box NAME --out OUT.npz [--size 8192] [--ranges 2023-05-01:2023-09-30,...] [--maxgroups 120] [--keep 44] [--base 24] [--target 6]

Read through the Microsoft Planetary Computer (public STAC + data API, no key; the imagery is NASA public domain). Nothing is cached on
disk: each scene's crop is read into memory. One observation = one sensor's pass on one date (the MGRS tiles of that pass are merged,
first valid texel wins, so the UTM 4 / 5 overlap is not counted twice). Passes are taken lowest tile cloud first: the first --base (24) with
any clear land, then only those that give a look to 1 % or more of the land texels still under --target (6) clear looks (windward
cloud forest, the Kona upslope), up to --keep (44). Fmask: cloud, adjacent, shadow and snow/ice texels dropped (grown by a texel: the mask is sampled
nearest at about 57 m), water only near the coast (Fmask calls dark basalt water), reflectance area-averaged. Output: colour (display values 0..1, HLS_LUT, NaN where never clear), count
(clear observations per texel), the box (grid rows / cols, lon / lat) and the used scene ids."""
import sys, os, io, json, math, time, gzip, argparse, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import region_bake as rb

Image.MAX_IMAGE_PIXELS = 400_000_000
PC = rb.PC
UA = {'User-Agent': 'hero-refine/1.0', 'Accept-Encoding': 'gzip'}
BOXES = {  # lon0, lat0, lon1, lat1 (land plus a margin; aligned to the grid below)
    'bigisland': (-156.10, 18.88, -154.78, 20.30),
    'mauinui': (-157.35, 20.48, -155.95, 21.25),
    'oahu': (-158.30, 21.23, -157.62, 21.75),
}

def fetch(url, tries=5, timeout=300):
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                b = r.read()
                if r.headers.get('Content-Encoding', '') == 'gzip': b = gzip.decompress(b)
                return b
        except urllib.error.HTTPError as e:
            if e.code in (404, 400, 422): raise
            err = e; time.sleep(2.0 * (k + 1))
        except Exception as e: err = e; time.sleep(2.0 * (k + 1))
    raise RuntimeError(f'fetch failed: {err}')

def search(bb, ranges):
    out = []
    for m0, m1 in ranges:
        body = dict(collections=['hls2-s30', 'hls2-l30'], bbox=[round(x, 6) for x in bb], datetime=f'{m0}T00:00:00Z/{m1}T23:59:59Z', limit=1000)
        url = f'{PC}/stac/v1/search'
        while True:
            d = rb.post_json(url, body)
            out += [dict(coll=f['collection'], id=f['id'], date=f['properties']['datetime'][:10], cc=f['properties'].get('eo:cloud_cover', 100), bbox=f['bbox']) for f in d['features']]
            nx = [l for l in d.get('links', []) if l.get('rel') == 'next']
            if not nx or not d['features']: break
            body = nx[0].get('body', body); url = nx[0]['href']
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True); ap.add_argument('--box', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--size', type=int, default=8192)
    ap.add_argument('--ranges', default='2023-05-01:2023-09-30,2024-05-01:2024-09-30,2025-05-01:2025-09-30')
    ap.add_argument('--maxgroups', type=int, default=120); ap.add_argument('--keep', type=int, default=44); ap.add_argument('--base', type=int, default=24)
    ap.add_argument('--target', type=int, default=6); ap.add_argument('--threads', type=int, default=4)
    a = ap.parse_args()
    meta = json.load(open(f'{a.data}/meta.json')); hb = meta['hero_bbox']; S = a.size
    dx = (hb[2] - hb[0]) / S; dy = (hb[3] - hb[1]) / S
    b = BOXES[a.box]
    c0 = int(math.floor((b[0] - hb[0]) / dx)); c1 = int(math.ceil((b[2] - hb[0]) / dx))
    r0 = int(math.floor((hb[3] - b[3]) / dy)); r1 = int(math.ceil((hb[3] - b[1]) / dy))
    W, H = c1 - c0, r1 - r0; X0 = hb[0] + c0 * dx; Y1 = hb[3] - r0 * dy
    bb = [X0, Y1 - H * dy, X0 + W * dx, Y1]
    lat = (bb[1] + bb[3]) / 2; px_m = dx * 111320 * math.cos(math.radians(lat))
    print(f'box {a.box}: cols {c0}..{c1} rows {r0}..{r1} ({W}x{H}), bbox {[round(x, 5) for x in bb]}, texel {px_m:.1f} x {dy * 111320:.1f} m', flush=True)
    # land: hero heights (4096^2, h > 2 m as hawaii_bake.py), bilinear onto the box grid, grown by 2 texels (coastal texels too)
    h16 = np.asarray(Image.open(f'{a.data}/hero_h16.png')).astype(np.float32); hh = (h16[..., 0] * 256 + h16[..., 1]) / 65535 * meta['hrange'] + meta['hmin']
    f = hh.shape[0] / S
    yy = (np.arange(r0, r1) + 0.5) * f - 0.5; xx = (np.arange(c0, c1) + 0.5) * f - 0.5
    hbox = ndimage.map_coordinates(hh, np.meshgrid(yy, xx, indexing='ij'), order=1, mode='nearest')
    land = ndimage.binary_dilation(hbox > 2, iterations=2); li = np.flatnonzero(land); NL = li.size
    # Fmask's water bit marks most dark basalt as water (66 % of Mauna Loa's summit flows, S30 2025-07-30): trusted only within
    # 3.5 texels (about 200 m) of the DEM coast, where it is the sea; inland it is ignored (the DEM says land)
    coast = ndimage.distance_transform_edt(hbox > 2) < 3.5
    print(f'land texels {NL} ({NL / land.size * 100:.1f} % of the box)', flush=True)
    ranges = [tuple(r.split(':')) for r in a.ranges.split(',')]
    items = search(bb, ranges)
    groups = {}
    for it in items: groups.setdefault((it['coll'], it['date']), []).append(it)
    order = sorted(groups.items(), key=lambda kv: np.mean([i['cc'] for i in kv[1]]))
    print(f'{len(items)} items in {len(groups)} passes; best tile cloud {[round(float(np.mean([i["cc"] for i in v])), 1) for k, v in order[:10]]}', flush=True)

    def get_item(it):
        ib = it['bbox']
        x0 = max(ib[0], bb[0]); x1 = min(ib[2], bb[2]); y0 = max(ib[1], bb[1]); y1 = min(ib[3], bb[3])
        if x1 <= x0 or y1 <= y0: return None
        cc0 = max(0, int(math.floor((x0 - bb[0]) / dx))); cc1 = min(W, int(math.ceil((x1 - bb[0]) / dx)))
        rr0 = max(0, int(math.floor((bb[3] - y1) / dy))); rr1 = min(H, int(math.ceil((bb[3] - y0) / dy)))
        if not land[rr0:rr1, cc0:cc1].any(): return None
        q = (bb[0] + cc0 * dx, bb[3] - rr1 * dy, bb[0] + cc1 * dx, bb[3] - rr0 * dy); w, h = cc1 - cc0, rr1 - rr0
        base = f'{PC}/data/v1/item/bbox/{q[0]:.7f},{q[1]:.7f},{q[2]:.7f},{q[3]:.7f}/{w}x{h}.npy?collection={it["coll"]}&item={it["id"]}'
        try:
            rgb = np.load(io.BytesIO(fetch(base + '&assets=B04&assets=B03&assets=B02&resampling=average')), allow_pickle=False)
            fm = np.load(io.BytesIO(fetch(base + '&assets=Fmask&resampling=nearest')), allow_pickle=False)
        except Exception as e:
            print(f'  {it["id"]}: {str(e)[:120]}', flush=True); return None
        fmv = fm[0].astype(np.int32); ok = (rgb[3] > 0) & (fm[1] > 0) & (rgb[:3] > 0).all(0) & (rgb[:3] < 16000).all(0)
        bad = (fmv & 0b11110) != 0                  # Fmask bits 1 cloud, 2 adjacent, 3 shadow, 4 snow / ice
        bad = ndimage.binary_dilation(bad, iterations=1) | (((fmv & 32) != 0) & coast[rr0:rr1, cc0:cc1])   # 5 water: near the coast only
        return (rr0, rr1, cc0, cc1), rgb[:3].astype(np.uint16), ok & ~bad, ok

    def get_group(kv):
        (coll, dte), its = kv
        obs = np.zeros((NL, 3), np.uint16); got = np.zeros(NL, bool); seen = np.zeros(NL, bool)
        full = np.zeros((H, W), bool); fullv = np.zeros((H, W), bool); tmp = np.zeros((3, H, W), np.uint16)
        for it in sorted(its, key=lambda i: i['cc']):
            r = get_item(it)
            if r is None: continue
            (rr0, rr1, cc0, cc1), rgb, clear, ok = r
            sl = (slice(rr0, rr1), slice(cc0, cc1)); take = clear & ~full[sl]
            for k in range(3): tmp[k][sl][take] = rgb[k][take]
            full[sl] |= take; fullv[sl] |= ok
        got = full.ravel()[li]; seen = fullv.ravel()[li]
        for k in range(3): obs[:, k] = tmp[k].ravel()[li]
        return (coll, dte, [i['id'] for i in its]), obs, got, seen

    kept = []; cnt = np.zeros(NL, np.int32); t0 = time.time(); done = 0
    with cf.ThreadPoolExecutor(a.threads) as ex:
        it = iter(order[:a.maxgroups])
        while True:
            batch = [x for _, x in zip(range(a.threads), it)]
            if not batch: break
            for (key, obs, got, seen) in ex.map(get_group, batch):
                done += 1
                cf_land = float(got.mean())
                if cf_land < 0.02: print(f'  {key[0][5:8]} {key[1]}: clear {cf_land * 100:.1f} % of land (seen {seen.mean() * 100:.0f} %), skipped', flush=True); continue
                gain = float((got & (cnt < a.target)).mean())   # the land texels this pass gives a needed look (fewer than target so far)
                if len(kept) >= a.base and gain < 0.01:
                    print(f'  {key[0][5:8]} {key[1]}: clear {cf_land * 100:.1f} %, adds a needed look on {gain * 100:.2f} % of land, skipped', flush=True); continue
                if len(kept) >= a.keep: break
                kept.append((key, obs, got, cf_land)); cnt += got
                print(f'  {key[0][5:8]} {key[1]}: clear {cf_land * 100:.1f} % of land (seen {seen.mean() * 100:.0f} %, needed {gain * 100:.1f} %); kept {len(kept)}; land with >= 5 looks {(cnt >= 5).mean() * 100:.1f} %, p5 {np.percentile(cnt, 5):.0f}, p10 {np.percentile(cnt, 10):.0f}, median {np.median(cnt):.0f} ({time.time() - t0:.0f} s)', flush=True)
            if len(kept) >= a.keep or (len(kept) >= 12 and np.percentile(cnt, 5) >= a.target): break
    # per-texel median of the clear looks (chunked: a float stack of all looks would not fit)
    K = len(kept); med = np.full((NL, 3), np.nan, np.float32); CH = 200000
    for s0 in range(0, NL, CH):
        s1 = min(NL, s0 + CH)
        st = np.stack([k[1][s0:s1] for k in kept]).astype(np.float32) / 10000.0; m = np.stack([k[2][s0:s1] for k in kept])
        st[~m] = np.nan
        with np.errstate(invalid='ignore'), __import__('warnings').catch_warnings():
            __import__('warnings').simplefilter('ignore'); med[s0:s1] = np.nanmedian(st, 0)
    col = np.full((H, W, 3), np.nan, np.float32); colf = col.reshape(-1, 3); colf[li] = rb.to_display(med)
    count = np.zeros((H, W), np.uint8); count.ravel()[li] = np.minimum(cnt, 255)
    used = sorted(sum([k[0][2] for k in kept], []))
    np.savez_compressed(a.out, col=col.astype(np.float16), count=count, land=land, rc=np.array([r0, r1, c0, c1]), bbox=np.array(bb), size=S,
                        used=np.array(used), passes=np.array([f'{k[0][0]}_{k[0][1]}' for k in kept]))
    print(f'done: {K} passes kept of {done} read, land never clear {(cnt == 0).mean() * 100:.2f} %, < 3 looks {(cnt < 3).mean() * 100:.2f} %, median looks {np.median(cnt):.0f}; {time.time() - t0:.0f} s', flush=True)

if __name__ == '__main__': main()
