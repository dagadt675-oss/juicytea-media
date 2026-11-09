#!/usr/bin/env python3
"""region_bake.py: bake one terrain + seafloor region for the HawaiiStage (lab/hawaii/hterrain.js, any region via loadRegion).

Generalises hawaii_bake.py (Big Island hero + skirt) to any name, bbox and resolution.

  python3 -I region_bake.py --spec SPEC.json --only NAME[,NAME...] --out DATA --dl DL [--keep]
  python3 -I region_bake.py --name NAME --bbox LON0,LAT0,LON1,LAT1 --wh W,H [--bathy etopo15,ncei:DATASET,...]
                            [--land-z Z] [--modis N] [--hls LEVEL] --out DATA --dl DL

Writes DATA/NAME/h16.png (RG 16-bit, h = v / 65535 * hrange + hmin, row 0 = north), ao.png (L), color.jpg (land drape; sea pixels
filled with nearby land colour) and meta.json (bbox, size, pixel size, sources, colour dates, sea-level facts from this grid).
Longitudes may run past -180 (e.g. -181.6 for the Hancock Seamounts): every fetcher splits at the antimeridian.

Height sources, coarse to fine, each blended over the previous one with a feathered edge where it has data:
  etopo15 / etopo30   NOAA NCEI ETOPO 2022 15" / 30" surface (bathymetry + topography; public domain), THREDDS WCS
  ncei:DATASET        NOAA NCEI coastal / tsunami DEMs on THREDDS 'regional' (e.g. hawaii_6_mllw_2005 6", oahu_13_mhw_2011 1/3"),
                      read over OPeNDAP with a stride near the target pixel size (public domain)
  land detail         AWS Terrain Tiles / Terrarium zoom Z (Mapzen/Tilezen; USGS 3DEP, SRTM; credit 'Terrain Tiles') adds its high
                      frequencies on land only where no fine NCEI topo-bathy grid covers, and raises sub-pixel islands the coarse grids miss
Colour: NASA GIBS MODIS Terra/Aqua 250 m cloud-free composite (BMNG 500 m where empty), optionally NASA HLS 30 m (Sentinel-2 / Landsat,
GIBS) composited per pixel on top for close regions, or (colour.hls.source 'pc') HLS v2 with its Fmask cloud mask and dated USGS Landsat 8
Collection 2 scenes ('dated') from the Microsoft Planetary Computer (public STAC + data API, no key). All NASA and USGS imagery is public
domain. Downloads go to DL/NAME (deleted unless --keep). The README (lab/hawaii/README.md) lists every spec option.
Needs python3 + numpy + scipy + PIL; network to ngdc.noaa.gov, s3.amazonaws.com (elevation-tiles-prod), gibs.earthdata.nasa.gov and
planetarycomputer.microsoft.com."""
import sys, os, io, json, math, time, shutil, struct, argparse, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
from scipy import ndimage

HMIN, HRANGE = -8000.0, 17000.0
UA = {'User-Agent': 'myth-juice-region-bake/1.0'}
MODIS_DATES = ['2024-06-03', '2024-06-19', '2024-07-08', '2024-07-21', '2024-08-06', '2024-08-25', '2024-09-10', '2024-09-22',
               '2022-06-14', '2022-07-17', '2022-08-09', '2022-09-05', '2021-06-10', '2021-07-02', '2021-07-25', '2021-08-18',
               '2021-09-07', '2023-06-05', '2023-06-28', '2023-07-14', '2023-09-12', '2023-09-29', '2022-06-28', '2022-07-30']
LOG = print

def fetch(url, tries=4, timeout=90):
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read()
        except Exception as e: err = e; time.sleep(1.5 * (k + 1))
    raise RuntimeError(f'fetch failed {url}: {err}')

def cached(path, url, **kw):
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        b = fetch(url, **kw); open(path + '.part', 'wb').write(b); os.replace(path + '.part', path)
    return open(path, 'rb').read()

def split_lon(l0, l1):
    """[(a0, a1, shift)] with a0..a1 inside [-180, 180]; the true longitude is a + shift."""
    out = []
    if l0 < -180: out.append((l0 + 360, min(l1 + 360, 180.0), -360.0)); l0 = -180.0
    if l1 > 180: out.append((max(l0 - 360, -180.0), l1 - 360, 360.0)); l1 = 180.0
    if l1 > l0: out.append((l0, l1, 0.0))
    return out

# ---------- a regular lon/lat grid piece: dict(a = 2D array row 0 north, x0 = west edge of col 0, y0 = north edge of row 0, d = deg/px)
def mosaic(pieces, d=None):
    pieces = [p for p in pieces if p['a'].size]
    d = d or pieces[0]['d']; X0 = min(p['x0'] for p in pieces); Y0 = max(p['y0'] for p in pieces)
    offs = [(int(round((Y0 - p['y0']) / d)), int(round((p['x0'] - X0) / d))) for p in pieces]
    H = max(r + p['a'].shape[0] for (r, c), p in zip(offs, pieces)); W = max(c + p['a'].shape[1] for (r, c), p in zip(offs, pieces))
    shp = (H, W) + pieces[0]['a'].shape[2:]
    out = np.full(shp, np.nan, np.float32)
    for (r, c), p in zip(offs, pieces):
        a = p['a'].astype(np.float32); m = np.isfinite(a) if a.ndim == 2 else np.isfinite(a).all(-1)
        sl = out[r:r + a.shape[0], c:c + a.shape[1]]; sl[m] = a[m]
    return dict(a=out, x0=X0, y0=Y0, d=d)

def grid_axes(bb, W, H):
    lons = bb[0] + (np.arange(W) + 0.5) / W * (bb[2] - bb[0]); lats = bb[3] - (np.arange(H) + 0.5) / H * (bb[3] - bb[1])
    return lons, lats

def sample(piece, bb, W, H, order=1):
    """resample a lon/lat piece onto the target grid (pixel centres); box-prefilter when the source is finer. NaN outside / no data."""
    a, d = piece['a'], piece['d']
    tdx, tdy = (bb[2] - bb[0]) / W, (bb[3] - bb[1]) / H
    k = int(min(tdx, tdy) / d)
    x0, y0 = piece['x0'], piece['y0']
    if k >= 2:  # area-average k x k blocks (NaN-aware)
        h2, w2 = a.shape[0] // k, a.shape[1] // k; b = a[:h2 * k, :w2 * k].reshape(h2, k, w2, k, *a.shape[2:])
        with np.errstate(invalid='ignore'): a = np.nanmean(np.nanmean(b, 3), 1)
        d = d * k
    lons, lats = grid_axes(bb, W, H)
    cx = (lons - x0) / d - 0.5; ry = (y0 - lats) / d - 0.5
    RY, CX = np.meshgrid(ry, cx, indexing='ij')
    inside = (CX >= -0.5) & (CX <= a.shape[1] - 0.5) & (RY >= -0.5) & (RY <= a.shape[0] - 0.5)
    def one(ch):
        valid = np.isfinite(ch); f = np.where(valid, ch, 0).astype(np.float32)
        if not valid.all():  # fill holes from neighbours so bilinear does not pull NaN in, then mask back
            idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True); f = f[tuple(idx)]
        v = ndimage.map_coordinates(f, [np.clip(RY, 0, a.shape[0] - 1), np.clip(CX, 0, a.shape[1] - 1)], order=order, mode='nearest')
        vm = ndimage.map_coordinates(valid.astype(np.float32), [np.clip(RY, 0, a.shape[0] - 1), np.clip(CX, 0, a.shape[1] - 1)], order=1, mode='nearest')
        v[~inside | (vm < 0.5)] = np.nan
        return v.astype(np.float32)
    if a.ndim == 2: return one(a)
    return np.stack([one(a[..., i]) for i in range(a.shape[2])], -1)

def feather(valid, px):
    """0..1 weight: 1 well inside the covered area, ramping to 0 over px pixels at its edge."""
    if valid.all(): return np.ones(valid.shape, np.float32)
    dist = ndimage.distance_transform_edt(valid)
    return np.clip((dist - 0.5) / max(px, 1), 0, 1).astype(np.float32)

# ---------- ETOPO 2022 via THREDDS WCS (GeoTIFF float, pixel-is-area)
ETOPO = 'https://www.ngdc.noaa.gov/thredds/wcs/global/ETOPO2022'
def read_geotiff(b):
    im = Image.open(io.BytesIO(b)); a = np.asarray(im).astype(np.float32)
    sx, sy = im.tag_v2[33550][:2]; tp = im.tag_v2[33922]
    return dict(a=a, x0=tp[3], y0=tp[4], d=sx)

def etopo(bb, res, dl):
    d = 15 / 3600 if res == '15s' else 30 / 3600; m = 3 * d; pieces = []
    for a0, a1, sh in split_lon(bb[0], bb[2]):
        if res == '30s': tiles = [('ETOPO_2022_v1_30s_N90W180_surface.nc', (-180, -90, 180, 90))]
        else:
            tiles = []
            for tw in range(int(math.floor(a0 / 15)) * 15, int(math.ceil(a1 / 15)) * 15, 15):
                for ts in range(int(math.floor(bb[1] / 15)) * 15, int(math.ceil(bb[3] / 15)) * 15, 15):
                    tn = ts + 15
                    name = f"{'N' if tn >= 0 else 'S'}{abs(tn):02d}{'W' if tw < 0 else 'E'}{abs(tw):03d}"
                    tiles.append((f'ETOPO_2022_v1_15s_{name}_surface.nc', (tw, ts, tw + 15, tn)))
        for fn, tb in tiles:
            q = (max(a0 - m, tb[0]), max(bb[1] - m, tb[1]), min(a1 + m, tb[2]), min(bb[3] + m, tb[3]))
            if q[2] <= q[0] or q[3] <= q[1]: continue
            url = f'{ETOPO}/{res}/{res}_surface_elev_netcdf/{fn}?service=WCS&version=1.0.0&request=GetCoverage&coverage=z&bbox={q[0]:.6f},{q[1]:.6f},{q[2]:.6f},{q[3]:.6f}&format=GeoTIFF_Float'
            p = read_geotiff(cached(f'{dl}/etopo{res}_{fn[18:26]}_{q[0]:.3f}_{q[1]:.3f}.tif', url))
            p['x0'] += 360 * round((q[0] - p['x0']) / 360) + sh  # the WCS reports a piece requested from lon -180 at +180
            pieces.append(p)
    return mosaic(pieces, d)

# ---------- NCEI regional DEMs via OPeNDAP binary (.dods) with a stride
NCEI = 'https://www.ngdc.noaa.gov/thredds/dodsC/regional'
def dods_arrays(b, dtypes):
    i = b.index(b'\nData:\n') + 7; out = []
    for dt in dtypes:
        n = struct.unpack('>I', b[i:i + 4])[0]; i += 8; sz = np.dtype(dt).itemsize
        out.append(np.frombuffer(b[i:i + n * sz], dt).astype(np.float64 if 'f8' in dt else np.float32)); i += n * sz
    return out

def ncei(ds, bb, dl, tdeg):
    lat = dods_arrays(cached(f'{dl}/{ds}_lat.dods', f'{NCEI}/{ds}.nc.dods?lat'), ['>f8'])[0]
    lon = dods_arrays(cached(f'{dl}/{ds}_lon.dods', f'{NCEI}/{ds}.nc.dods?lon'), ['>f8'])[0]
    dlat, dlon = abs(lat[1] - lat[0]), abs(lon[1] - lon[0]); pieces = []
    for a0, a1, sh in split_lon(bb[0], bb[2]):
        jj = np.where((lon >= a0 - 3 * dlon) & (lon <= a1 + 3 * dlon))[0]; ii = np.where((lat >= bb[1] - 3 * dlat) & (lat <= bb[3] + 3 * dlat))[0]
        if not len(jj) or not len(ii): continue
        s = max(1, int(tdeg / dlon / 1.5))
        while ((ii[-1] - ii[0]) // s + 1) * ((jj[-1] - jj[0]) // s + 1) > 30e6: s += 1
        q = f'Band1[{ii[0]}:{s}:{ii[-1]}][{jj[0]}:{s}:{jj[-1]}]'
        b = cached(f'{dl}/{ds}_{ii[0]}_{jj[0]}_{s}.dods', f'{NCEI}/{ds}.nc.dods?{q}', timeout=600)
        a, la, lo = dods_arrays(b, ['>f4', '>f8', '>f8'])
        a = a.reshape(len(la), len(lo)); a[(a < -15000) | (a > 9000)] = np.nan
        if la[1] < la[0]: pass
        else: a = a[::-1]; la = la[::-1]
        d = abs(lo[1] - lo[0]) if len(lo) > 1 else dlon * s
        pieces.append(dict(a=a, x0=lo[0] - d / 2 + sh, y0=la[0] + d / 2, d=d))
        LOG(f'  ncei {ds} stride {s} -> {a.shape} {d * 3600:.2f}"')
    return mosaic(pieces) if pieces else None

# ---------- AWS Terrain Tiles (Terrarium PNG, web mercator) sampled at the target grid
def terrarium(z, bb, W, H, dl):
    n = 2 ** z
    def ly(lat): r = math.radians(max(min(lat, 85.0511), -85.0511)); return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n
    X0, X1 = int(math.floor((bb[0] + 180) / 360 * n)), int(math.floor((bb[2] + 180) / 360 * n))
    Y0, Y1 = int(math.floor(ly(bb[3]))), int(math.floor(ly(bb[1])))
    def get(xy):
        x, y = xy; xm = x % n
        b = cached(f'{dl}/terr_{z}_{xm}_{y}.png', f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{xm}/{y}.png')
        a = np.asarray(Image.open(io.BytesIO(b)).convert('RGB')).astype(np.float32)
        return xy, a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    mos = np.zeros(((Y1 - Y0 + 1) * 256, (X1 - X0 + 1) * 256), np.float32)
    with cf.ThreadPoolExecutor(16) as ex:
        for (x, y), a in ex.map(get, [(x, y) for y in range(Y0, Y1 + 1) for x in range(X0, X1 + 1)]):
            mos[(y - Y0) * 256:(y - Y0 + 1) * 256, (x - X0) * 256:(x - X0 + 1) * 256] = a
    void = mos < -11000  # data voids (-32768) are filled from the nearest valid cell and returned as NaN
    if void.any():
        idx = ndimage.distance_transform_edt(void, return_distances=False, return_indices=True); mos = mos[tuple(idx)]
    med = ndimage.median_filter(mos, size=3); spike = np.abs(mos - med) > 800  # single-cell spikes (bad cells in the Himalaya: -2,900 m)
    mos = np.where(spike, med, mos)
    LOG(f'  terrarium z{z}: {(X1 - X0 + 1) * (Y1 - Y0 + 1)} tiles' + (f', {int(void.sum())} void px' if void.any() else '') + (f', {int(spike.sum())} spikes' if spike.any() else ''))
    lons, lats = grid_axes(bb, W, H)
    mx = ((lons + 180) / 360 * n - X0) * 256 - 0.5
    my = np.array([(ly(l) - Y0) * 256 - 0.5 for l in lats])
    # source finer than target: prefilter with a box of the size ratio
    tpx = (bb[2] - bb[0]) / W / 360 * n * 256
    if tpx >= 2: mos = ndimage.uniform_filter(mos, size=int(tpx))
    MY, MX = np.meshgrid(my, mx, indexing='ij')
    out = ndimage.map_coordinates(mos, [MY, MX], order=1, mode='nearest').astype(np.float32)
    if void.any(): out[ndimage.map_coordinates(void.astype(np.float32), [MY, MX], order=1, mode='nearest') > 0.5] = np.nan
    return out

# ---------- NASA GIBS (EPSG:4326 tiles of 512 px, span 288 / 2^L deg)
def gibs(layer, tms, date, lvl, ext, bb, dl, pool=12, alpha=False):
    span = 288 / 2 ** lvl; d = span / 512; pieces = []
    for a0, a1, sh in split_lon(bb[0], bb[2]):
        c0, c1 = int((a0 + 180) // span), int((a1 + 180 - 1e-9) // span); r0, r1 = int((90 - bb[3]) // span), int((90 - bb[1] - 1e-9) // span)
        def get(rc):
            r, c = rc; f = f'{dl}/gibs_{layer[:24]}_{date}_{lvl}_{r}_{c}.{ext}'
            try: b = cached(f, f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{date}/{tms}/{lvl}/{r}/{c}.{ext}', tries=3, timeout=60)
            except Exception: return rc, None
            im = Image.open(io.BytesIO(b)); a = np.asarray(im.convert('RGBA')).astype(np.float32) / 255
            if not alpha: a[..., 3] = (a[..., :3].sum(-1) > 0.012).astype(np.float32)  # jpeg: black = missing
            return rc, a
        img = np.full(((r1 - r0 + 1) * 512, (c1 - c0 + 1) * 512, 4), 0, np.float32)
        with cf.ThreadPoolExecutor(pool) as ex:
            for (r, c), a in ex.map(get, [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]):
                if a is not None: img[(r - r0) * 512:(r - r0 + 1) * 512, (c - c0) * 512:(c - c0 + 1) * 512] = a
        rgb = img[..., :3].copy(); rgb[img[..., 3] < 0.5] = np.nan
        pieces.append(dict(a=rgb, x0=-180 + c0 * span + sh, y0=90 - r0 * span, d=d))
    return mosaic(pieces, d)

def lum(c): return c @ np.array([0.2126, 0.7152, 0.0722], np.float32)

def resize3(a, w, h):
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(a[..., k]).astype(np.float32), 'F').resize((w, h), Image.BICUBIC)) for k in range(a.shape[2])], -1)

def modis_composite(bb, cw, ch, dl, n, lvl):
    """per-pixel cloud-free composite on the native MODIS grid (mean of the 4-20 % luminance ranks), then resized to cw x ch."""
    d = 288 / 2 ** lvl / 512
    mw, mh = max(8, min(cw, int(round((bb[2] - bb[0]) / d)))), max(8, min(ch, int(round((bb[3] - bb[1]) / d))))
    dates = MODIS_DATES[:max(1, (n + 1) // 2)]; stack = []
    for dte in dates:
        for s in ('Terra', 'Aqua'):
            p = gibs(f'MODIS_{s}_CorrectedReflectance_TrueColor', '250m', dte, lvl, 'jpg', bb, dl)
            stack.append(sample(p, bb, mw, mh))
    stack = np.stack(stack); L = lum(stack); L = np.where(np.isfinite(L), L, 9.0)
    order = np.argsort(L, axis=0); k = len(stack); lo, hi = int(k * 0.04), max(int(k * 0.20), int(k * 0.04) + 1)
    sel = np.take_along_axis(stack, order[lo:hi, ..., None].repeat(3, -1), axis=0)
    with np.errstate(invalid='ignore'): col = np.nanmean(sel, 0)
    bm = sample(gibs('BlueMarble_NextGeneration', '500m', '2004-07-01', min(lvl - 1, 7), 'jpeg', bb, dl), bb, mw, mh)
    miss = ~np.isfinite(col).all(-1) | (np.nan_to_num(col).sum(-1) < 0.03)
    col[miss] = bm[miss]
    col = np.nan_to_num(col, nan=0.3)
    if (mw, mh) != (cw, ch): col = np.clip(resize3(col, cw, ch), 0, 1)
    return col, [f'{s}_{d}' for d in dates for s in ('Terra', 'Aqua')]

def hls_composite(bb, cw, ch, dl, lvl, want=8, months=('2024-03-01', '2024-10-31'), centre=None, pct=0.3):
    """probe the centre tile on every day for both HLS sensors, keep the clearest dates, composite per pixel (pct luminance percentile)."""
    from datetime import date, timedelta
    span = 288 / 2 ** lvl; lon, lat = centre or ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
    lon = lon + 360 if lon < -180 else lon
    c, r = int((lon + 180) // span), int((90 - lat) // span)
    cands = []  # months: one [first, last] day range, or a list of ranges (e.g. two summers: high sun lights the NE-facing cliffs)
    for m0, m1 in ([months] if isinstance(months[0], str) else months):
        d0, d1 = date.fromisoformat(m0), date.fromisoformat(m1)
        cands += [(L, (d0 + timedelta(k)).isoformat()) for k in range((d1 - d0).days + 1) for L in ('HLS_S30_Nadir_BRDF_Adjusted_Reflectance', 'HLS_L30_Nadir_BRDF_Adjusted_Reflectance')]
    def probe(ld):
        L, dte = ld
        try: b = fetch(f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{L}/default/{dte}/31.25m/{lvl}/{r}/{c}.png', tries=2, timeout=40)
        except Exception: return ld, 0, 9
        try: a = np.asarray(Image.open(io.BytesIO(b)).convert('RGBA')).astype(np.float32) / 255; v = a[..., 3] > 0.5
        except Exception: return ld, 0, 9   # a GIBS error page instead of a tile (seen once in round 3)
        return ld, float(v.mean()), float(lum(a[..., :3])[v].mean()) if v.any() else 9
    with cf.ThreadPoolExecutor(16) as ex: res = list(ex.map(probe, cands))
    ok = sorted([x for x in res if x[1] > 0.6], key=lambda x: x[2])
    LOG(f'  hls probe: {len(ok)} of {len(cands)} sensor-days have data; clearest {[(x[0][1], x[0][0][4:7], round(x[2], 3)) for x in ok[:want]]}')
    if not ok: return None, []
    stack, used = [], []
    for (L, dte), fr, lm in ok[:want]:
        p = gibs(L, '31.25m', dte, lvl, 'png', bb, dl, alpha=True); stack.append(sample(p, bb, cw, ch)); used.append(f'{L[4:7]}_{dte}')
    stack = np.stack(stack); Lm = lum(stack); valid = np.isfinite(Lm); nv = valid.sum(0)
    Lm = np.where(valid, Lm, np.inf); order = np.argsort(Lm, axis=0)
    k = np.clip(np.floor(pct * (nv - 1)), 0, None).astype(int)
    pick = np.take_along_axis(order, k[None], axis=0)[0]
    col = np.take_along_axis(stack, pick[None, ..., None].repeat(3, -1), axis=0)[0]
    col[nv == 0] = np.nan
    return col, used

# ---------- NASA HLS v2 with its Fmask cloud mask, and USGS Landsat Collection 2 Level-2, read through the Microsoft Planetary Computer
# (public STAC + data API, no key; the imagery itself is NASA / USGS public domain). The GIBS HLS layers above have no cloud mask, so a
# ridge that is under cloud on most days (the windward Ko'olau) keeps cloud in any luminance percentile; Fmask removes it per scene.
PC = 'https://planetarycomputer.microsoft.com/api'
# surface reflectance -> the 8-bit value NASA GIBS renders for HLS true colour (measured 2026-11-09 on HLS.S30.T04QFJ.2023240, 58,000 clear
# Ko'olau pixels, the median per 0.02 reflectance bin, the same curve within 0.03 for R, G and B), so Fmask composites keep the tone of the
# GIBS-based regions and the luminance gains measured on them still apply (O'ahu: 0.758 on the GIBS composite, 0.734 re-measured on this one)
HLS_LUT = (np.array([0.0, .01, .03, .05, .07, .09, .11, .13, .15, .17, .19, .21, .23, .25, .27, .29, .70, 1.5]),
           np.array([0.0, .07, .241, .370, .444, .497, .540, .576, .601, .627, .654, .668, .682, .689, .711, .722, 1.0, 1.0]))

def post_json(url, body, tries=4, timeout=90):
    err = None
    for k in range(tries):
        try:
            rq = urllib.request.Request(url, data=json.dumps(body).encode(), headers=dict(UA, **{'Content-Type': 'application/json'}))
            with urllib.request.urlopen(rq, timeout=timeout) as r: return json.load(r)
        except Exception as e: err = e; time.sleep(1.5 * (k + 1))
    raise RuntimeError(f'post failed {url}: {err}')

def pc_search(colls, bb, ranges):
    """STAC items over bbox in the date ranges: [(collection, id, date, tile cloud %)]."""
    out = []
    for m0, m1 in ranges:
        d = post_json(f'{PC}/stac/v1/search', dict(collections=colls, bbox=[round(x, 6) for x in bb], datetime=f'{m0}T00:00:00Z/{m1}T23:59:59Z', limit=1000))
        out += [(f['collection'], f['id'], f['properties']['datetime'][:10], f['properties'].get('eo:cloud_cover', 100)) for f in d['features']]
    return out

def pc_npy(coll, item, assets, bb, w, h, dl, resampling='nearest'):
    """one item's bands over bbox (EPSG:4326, pixel-is-area) as (len(assets) + 1, h, w): the last band is the data mask (255 = data)."""
    q = '&'.join(f'assets={a}' for a in assets)
    url = f'{PC}/data/v1/item/bbox/{bb[0]:.6f},{bb[1]:.6f},{bb[2]:.6f},{bb[3]:.6f}/{w}x{h}.npy?collection={coll}&item={item}&{q}&resampling={resampling}'
    b = cached(f'{dl}/pc_{item}_{"-".join(assets)}_{w}x{h}_{resampling}.npy', url, timeout=300)
    return np.load(io.BytesIO(b), allow_pickle=False)

def to_display(refl):  # reflectance (NaN = none) -> GIBS-like display value 0..1
    out = np.interp(np.nan_to_num(refl, nan=0.0), *HLS_LUT).astype(np.float32); out[~np.isfinite(refl)] = np.nan
    return out

def resize_nan(a, w, h):  # bicubic resize of an H x W x 3 image with NaN holes (holes stay NaN)
    v = np.isfinite(a).all(-1)
    if not v.any(): return np.full((h, w, 3), np.nan, np.float32)
    idx = ndimage.distance_transform_edt(~v, return_distances=False, return_indices=True); f = a[tuple(idx)]
    o = resize3(f, w, h); vm = np.asarray(Image.fromarray(v.astype(np.float32), 'F').resize((w, h), Image.BILINEAR)) > 0.5
    o[~vm] = np.nan
    return o

def hlsfm_composite(bb, cw, ch, dl, ranges, want=24, snow=False, stat=50):
    """HLS v2 (Sentinel-2 S30 + Landsat L30, 30 m) per-pixel composite of Fmask-clear observations (cloud, cloud-adjacent and cloud-shadow
    pixels dropped; snow kept only with snow=True, e.g. Everest) over the date ranges; stat = the percentile of the clear samples (50 =
    median). Returns (colour cw x ch in display values, NaN where no scene was clear, used dates, stats)."""
    lat = (bb[1] + bb[3]) / 2
    nw = max(8, int(round((bb[2] - bb[0]) * 111320 * math.cos(math.radians(lat)) / 30))); nh = max(8, int(round((bb[3] - bb[1]) * 111320 / 30)))
    rw, rh = min(nw, cw), min(nh, ch); native = rw >= 0.9 * nw
    items = sorted(pc_search(['hls2-s30', 'hls2-l30'], bb, ranges), key=lambda x: x[3])
    cand = items[:max(3 * want, 36)]
    def get(it):
        coll, iid, dte, cc = it
        try:
            if native:
                a = pc_npy(coll, iid, ['B04', 'B03', 'B02', 'Fmask'], bb, rw, rh, dl); bands, fm, ok = a[:3], a[3], a[4] > 0
            else:  # coarser than 30 m: reflectance area-averaged, the mask sampled (and grown by a pixel below)
                a = pc_npy(coll, iid, ['B04', 'B03', 'B02'], bb, rw, rh, dl, 'average'); m = pc_npy(coll, iid, ['Fmask'], bb, rw, rh, dl, 'nearest')
                bands, fm, ok = a[:3], m[0], (a[3] > 0) & (m[1] > 0)
        except Exception as e:
            LOG(f'  hls-pc {iid}: {e}'); return it, None
        fm = fm.astype(np.int32); ok = ok & (bands > -9000).all(0)
        bad = (fm & 0b1110) != 0                   # Fmask bits: 1 cloud, 2 adjacent to cloud or shadow, 3 cloud shadow, 4 snow/ice
        if not snow: bad |= (fm & 16) != 0
        if not native: bad = ndimage.binary_dilation(bad, iterations=1)
        clear = ok & ~bad
        return it, (np.moveaxis(bands, 0, -1).astype(np.float32) / 10000.0, clear)
    with cf.ThreadPoolExecutor(6) as ex: res = [r for r in ex.map(get, cand) if r[1] is not None and r[1][1].mean() > 0.02]
    res.sort(key=lambda r: -r[1][1].mean()); res = res[:want]
    LOG(f'  hls-pc: {len(items)} scenes in range, {len(cand)} fetched, {len(res)} used; clear share {[round(float(r[1][1].mean()), 2) for r in res[:12]]}')
    if not res: return None, [], {}
    clr = np.stack([r[1][1] for r in res]); S = np.where(clr[..., None], np.stack([r[1][0] for r in res]), np.nan)
    with np.errstate(invalid='ignore'), __import__('warnings').catch_warnings():
        __import__('warnings').simplefilter('ignore'); comp = np.nanpercentile(S, stat, axis=0)
    n = clr.sum(0); stats = dict(scenes=len(res), clear_obs_median=int(np.median(n)), never_clear_pct=round(float((n == 0).mean() * 100), 2))
    LOG(f'  hls-pc: clear observations per pixel median {stats["clear_obs_median"]}, never clear {stats["never_clear_pct"]} %')
    col = to_display(comp)
    if (rw, rh) != (cw, ch): col = resize_nan(col, cw, ch)
    return col, sorted(f'{r[0][1][4:7]}_{r[0][2]}' for r in res), stats

def landsat_dated(scenes, bb, cw, ch, dl):
    """one date of USGS Landsat Collection 2 Level-2 surface reflectance (one or two WRS rows of the same pass, first clear wins) over bbox
    at 30 m: (colour cw x ch in display values with NaN under cloud, NIR reflectance at 30 m, clear mask at 30 m, (rw, rh))."""
    lat = (bb[1] + bb[3]) / 2
    rw = max(8, int(round((bb[2] - bb[0]) * 111320 * math.cos(math.radians(lat)) / 30))); rh = max(8, int(round((bb[3] - bb[1]) * 111320 / 30)))
    rgb = np.full((rh, rw, 3), np.nan, np.float32); nir = np.full((rh, rw), np.nan, np.float32)
    for iid in scenes:
        a = pc_npy('landsat-c2-l2', iid, ['red', 'green', 'blue', 'nir08', 'qa_pixel'], bb, rw, rh, dl).astype(np.float32)
        qa = a[4].astype(np.int64); ok = (a[5] > 0) & (a[0] > 0)
        clear = ok & ((qa & (0b11110)) == 0)             # QA_PIXEL bits 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow
        take = clear & ~np.isfinite(nir)
        for k in range(3): rgb[..., k][take] = a[k][take] * 0.0000275 - 0.2
        nir[take] = a[3][take] * 0.0000275 - 0.2
    col = to_display(rgb)
    return (resize_nan(col, cw, ch) if (rw, rh) != (cw, ch) else col), nir, np.isfinite(nir), (rw, rh)

def sea_colour(h):
    """colour for sea-floor texels (used by the stage only from -6 to +4 m, under shallow water or when drained): by depth, never by
    satellite brightness or the nearest land. A pale carbonate sand flat at 0 m to the film's reef-flat warm grey (SEABED.reef, linear
    0.074 / 0.066 / 0.058 after the stage's land gain) by -6 m."""
    t = np.clip(-h / 6.0, 0, 1)[..., None]
    return np.array([0.36, 0.345, 0.32], np.float32) * (1 - t) + np.array([0.30, 0.285, 0.265], np.float32) * t

def rock_stack(h, bb, W, H, ft, px_m):
    """model a sea stack or pinnacle that no grid resolves (spec 'features'): lobes = [[dx_m, dy_m, rx_m, ry_m, top_m], ...] in a frame
    rotated by az (deg, 0 = the x axis points east), steep walls and a rounded crown, plus crag noise; an optional reef platform
    (platform: [radius_m, depth_m] or [rx_m, ry_m, depth_m], domain-warped) under it. Returns the new grid and the rock mask (0..1)."""
    lons, lats = grid_axes(bb, W, H); mx = (lons - ft['lon']) * 111320 * math.cos(math.radians(ft['lat'])); my = (lats - ft['lat']) * 111320
    X, Y = np.meshgrid(mx, my); a = math.radians(ft.get('az', 0)); u = X * math.cos(a) + Y * math.sin(a); v = -X * math.sin(a) + Y * math.cos(a)
    rng = np.random.default_rng(ft.get('seed', 7)); r = np.hypot(X, Y)
    def noise(scale_m):
        n = ndimage.gaussian_filter(rng.standard_normal(h.shape), max(0.6, scale_m / px_m)); return n / max(float(np.abs(n).max()), 1e-6)
    nz, crag, w1, w2 = noise(4.0), noise(1.5), noise(60.0), noise(60.0)
    rock = np.zeros_like(h)
    for dx, dy, rx, ry, top in ft['lobes']:
        d = np.hypot((u - dx) / rx, (v - dy) / ry) * (1 + 0.22 * nz)
        rock = np.maximum(rock, top * np.clip(1 - d ** 3.5, 0, 1) ** 0.25)   # near-vertical walls, a narrow crown
    rock = rock * (1 + 0.14 * crag) * (rock > 0.5)                              # crags and ledges on the faces
    if rock.max() > 0: rock *= max(l[4] for l in ft['lobes']) / float(rock.max())   # the crags never raise the surveyed top
    out = h.copy()
    if ft.get('platform'):
        rx, ry, dep = ft['platform'] if len(ft['platform']) == 3 else (ft['platform'][0], ft['platform'][0], ft['platform'][1])
        wu, wv = u + 0.8 * rx * w1, v + 0.8 * ry * w2                            # domain-warped ellipse: an irregular reef flat, not a disc
        re = np.hypot(wu / rx, wv / ry); w = np.clip(1.6 - re, 0, 1) ** 1.5
        out = out * (1 - w) + dep * w
    m = rock > 0.5
    out = np.where(m, np.maximum(out, rock), out)
    return out.astype(np.float32), np.clip(rock / 3.0, 0, 1).astype(np.float32)

def fill_sea(rgb, land):  # push-pull fill (from hawaii_bake.py): sea pixels get the colour of nearby land
    def rs(a, w, h): return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((w, h), Image.BILINEAR))
    lv = [(rgb * land[..., None], land.astype(np.float32))]
    while min(lv[-1][1].shape) > 4:
        c, m = lv[-1]; h, w = m.shape; h2, w2 = h // 2, w // 2
        lv.append((c[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).sum((1, 3)), m[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).sum((1, 3))))
    est = lv[-1][0] / np.maximum(lv[-1][1], 1e-6)[..., None]
    if lv[-1][1].sum() == 0: est[:] = 0.3
    for c, m in reversed(lv[:-1]):
        h, w = m.shape; up = np.stack([rs(est[..., k], w, h) for k in range(3)], -1)
        est = np.where(m[..., None] > 0, c / np.maximum(m, 1e-6)[..., None], up)
    return est

def bake_ao(h, bb, px_m, tangent=False):
    """horizon-based sky occlusion, 12 directions. Default: the horizon above the horizontal (what every region baked before 2026-11-09
    uses). tangent=True: the horizon above the local slope in that direction (HBAO), so a steep but open cliff face is not counted as
    occluded by itself (the stage already shades by the normal: sky * ao * (0.55 + 0.45 n.y)); valleys and amphitheatres still darken.
    On the Pali grid it lifts 35-55 degree faces only a little (median 0.41 to 0.44): the near-black Pali shade was the stage's
    sky-only lighting on a face turned from the sun, not the AO."""
    H, W = h.shape; lat = np.linspace(bb[3], bb[1], H)[:, None]
    dxm = (bb[2] - bb[0]) / W * 111320 * np.cos(np.radians(lat)); dym = (bb[3] - bb[1]) / H * 111320
    occ = np.zeros(h.shape, np.float32); nd = 12; s0, s1 = 2 * px_m, min(25000.0, 260 * px_m)
    for k in range(nd):
        a = 2 * math.pi * k / nd; best = np.full(h.shape, -1.0 if not tangent else -1e9, np.float32); t0 = None
        for s in np.geomspace(s0, s1, 16):
            dc = np.rint(math.sin(a) * s / dxm).astype(int); dr = int(round(-math.cos(a) * s / dym))
            r = np.clip(np.arange(H)[:, None] + dr, 0, H - 1); c = np.clip(np.arange(W)[None, :] + dc, 0, W - 1)
            g = (h[r, c] - h) / s
            if t0 is None: t0 = g
            best = np.maximum(best, g)
        if tangent: occ += np.maximum(np.sin(np.arctan(best)) - np.sin(np.arctan(t0)), 0)
        else: occ += np.sin(np.maximum(np.arctan(best), 0))
    return np.clip(1 - occ / nd * 1.8, 0, 1)

def pack16(h):
    v = np.clip((h - HMIN) / HRANGE * 65535, 0, 65535).astype(np.uint32)
    return Image.fromarray(np.stack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)], -1))

# ---------- facts from the baked grid
def subwin(bb, W, H, sb):  # pixel window of sub-bbox sb inside the grid -> (exact sub bbox, (r0, c0, r1, c1))
    r0, c0 = rc_of(bb, W, H, sb[0], sb[3]); r1, c1 = rc_of(bb, W, H, sb[2], sb[1]); r0, c0 = max(r0, 0), max(c0, 0); r1, c1 = min(r1, H - 1), min(c1, W - 1)
    return [bb[0] + c0 / W * (bb[2] - bb[0]), bb[3] - (r1 + 1) / H * (bb[3] - bb[1]), bb[0] + (c1 + 1) / W * (bb[2] - bb[0]), bb[3] - r0 / H * (bb[3] - bb[1])], (r0, c0, r1, c1)
def rc_of(bb, W, H, lon, lat): return int(round((bb[3] - lat) / (bb[3] - bb[1]) * H - 0.5)), int(round((lon - bb[0]) / (bb[2] - bb[0]) * W - 0.5))
def saddle(h, bb, A, B, lo=-7000.0):
    H, W = h.shape; ra, rb = rc_of(bb, W, H, *A), rc_of(bb, W, H, *B)
    def conn(L): lab, _ = ndimage.label(h > L); return lab[ra] != 0 and lab[ra] == lab[rb]
    hi = float(min(h[ra], h[rb]))
    if not conn(lo): return None
    while hi - lo > 1: mid = (lo + hi) / 2; (lo, hi) = (mid, hi) if conn(mid) else (lo, mid)
    return round(lo)

def facts(h, bb, F, px_m):
    H, W = h.shape; out = {}; pts = F.get('points', {})
    km_px = px_m / 1000
    if F.get('saddles'):
        out['saddles_m'] = {f'{a}-{b}': saddle(h, bb, pts[a], pts[b]) for a, b in F['saddles']}
        out['saddles_note'] = 'highest sea level (m) at which the two points are joined by dry land on this grid (4-connected); null = not joined above -7,000 m'
    for nm, (lon, lat, rkm, *kind) in F.get('peaks', {}).items():
        r, c = rc_of(bb, W, H, lon, lat); rr = max(1, int(rkm / km_px))
        win = h[max(r - rr, 0):r + rr + 1, max(c - rr, 0):c + rr + 1].copy()
        if kind and kind[0] == 'sea': win[win >= 0] = -1e9
        i = np.unravel_index(np.argmax(win), win.shape)
        pr, pc = max(r - rr, 0) + i[0], max(c - rr, 0) + i[1]
        out.setdefault('peaks_m', {})[nm] = dict(h=round(float(win[i])), lon=round(bb[0] + (pc + 0.5) / W * (bb[2] - bb[0]), 4), lat=round(bb[3] - (pr + 0.5) / H * (bb[3] - bb[1]), 4))
    for nm, (lon, lat) in F.get('depths', {}).items():
        r, c = rc_of(bb, W, H, lon, lat)
        if 0 <= r < H and 0 <= c < W: out.setdefault('point_h_m', {})[nm] = round(float(h[r, c]))
    for L in F.get('joined_at', []):
        lab, _ = ndimage.label(h > L); groups = {}
        for nm, p in pts.items():
            r, c = rc_of(bb, W, H, *p)
            if 0 <= r < H and 0 <= c < W and lab[r, c]: groups.setdefault(int(lab[r, c]), []).append(nm)
        cell = (px_m / 1000) ** 2
        out.setdefault('land_groups_at', {})[str(L)] = [dict(names=v, area_km2=round(float((lab == k).sum()) * cell)) for k, v in groups.items()]
    for L in F.get('wet_at', []):
        lab, n = ndimage.label(h < L); sizes = ndimage.sum(np.ones_like(h), lab, range(1, n + 1)) if n else []
        big = np.argsort(sizes)[::-1][:4]; lst = []
        for k in big:
            rr, cc = np.where(lab == k + 1)
            lst.append(dict(area_km2=round(float(sizes[k]) * (px_m / 1000) ** 2), lon=[round(bb[0] + cc.min() / W * (bb[2] - bb[0]), 3), round(bb[0] + cc.max() / W * (bb[2] - bb[0]), 3)],
                            lat=[round(bb[3] - rr.max() / H * (bb[3] - bb[1]), 3), round(bb[3] - rr.min() / H * (bb[3] - bb[1]), 3)]))
        out.setdefault('water_left_at', {})[str(L)] = dict(bodies=int(n), largest=lst)
    cell = (px_m / 1000) ** 2
    out['land_area_km2_at_0m'] = round(float((h > 0).sum()) * cell, 1)
    out['h_range_m'] = [round(float(h.min())), round(float(h.max()))]
    return out

def dated_variant(dv, h, col, col_sat, bb, W, H, px_m, od, dl):
    """one dated Landsat scene on the region's own grid, written as h16_<date>.png, color_<date>.jpg and sat_<date>.jpg (make_index.py
    lists it as its own region, e.g. 'lalo_2018_before', sharing the base AO). Inside the focus circle (dv.focus = [lon, lat, r_km]) land is
    that date's dry land: dry sand reflects near-infrared, water of any depth absorbs it, so the 30 m NIR reflectance unmixed between water
    (0.02) and dry sand (0.30) gives each pixel's land share. Outside the focus the heights are the base grid's. Cloud holes in the picture
    are filled from the region's composite (logged; none may fall inside the focus)."""
    tag = dv['date']; dc, nir, clear, (rw, rh) = landsat_dated(dv['scenes'], bb, W, H, dl)
    lons, lats = grid_axes(bb, W, H); fx, fy, frk = dv['focus']
    rk = np.hypot((lons[None] - fx) * 111.32 * math.cos(math.radians(fy)), (lats[:, None] - fy) * 111.32); foc = rk <= frk
    v = np.isfinite(dc).all(-1); clear_focus = float(v[foc].mean())
    # land share at 30 m, then on the grid
    # end-members: open water 0.02 (lagoon around East Island 0.008-0.016), dry coral sand 0.60 (95th percentile of the island's core on
    # 9 July 2018, 0.59-0.69)
    frac = np.clip((np.nan_to_num(nir, nan=0.0) - 0.02) / (0.60 - 0.02), 0, 1)
    nl, nt = np.meshgrid(np.linspace(bb[0], bb[2], rw, endpoint=False) + (bb[2] - bb[0]) / rw / 2, np.linspace(bb[3], bb[1], rh, endpoint=False) - (bb[3] - bb[1]) / rh / 2)
    foc30 = np.hypot((nl - fx) * 111.32 * math.cos(math.radians(fy)), (nt - fy) * 111.32) <= frk
    px30 = (bb[2] - bb[0]) / rw * 111320 * math.cos(math.radians(fy)) * (bb[3] - bb[1]) / rh * 111320
    land_m2 = float((frac * foc30 * np.isfinite(nir)).sum() * px30)
    fr = np.asarray(Image.fromarray(frac.astype(np.float32), 'F').resize((W, H), Image.BILINEAR))
    # land on the grid = the pixels with the highest sand share inside the focus, as many as the unmixed area fills (area-preserving:
    # a sliver that is sub-pixel at 30 m still shows as a few grid pixels)
    gpx = (bb[2] - bb[0]) / W * 111320 * math.cos(math.radians(fy)) * (bb[3] - bb[1]) / H * 111320
    k = int(round(land_m2 / gpx)); vals = np.sort(fr[foc])[::-1]
    thr = max(float(vals[k - 1]) if 0 < k <= len(vals) else 1.1, 0.02)
    hv = h.copy(); land = foc & (fr >= thr) if k > 0 else np.zeros_like(foc)
    hv[foc & (h > 0) & ~land] = -2.0                                   # gone: a sand shoal under about 2 m of water
    hv[land] = np.maximum(hv[land], 0.8 + 2.7 * np.clip(fr[land] / max(float(fr[foc].max()), 1e-3), 0, 1))   # a low sand islet, 0.8-3.5 m
    pack16(hv).save(f'{od}/h16_{tag}.png', compress_level=6)
    cv = col.copy(); take = land & v; cv[take] = dc[take]
    # land of the base grid that is under water on this date: sea floor by depth (that day's picture of the shoal is bright sand seen
    # through 1-2 m of water; drawn under the stage's own water it read as a white island still there)
    gone = foc & (hv <= 0.5) & (h > 0.5); cv[gone] = sea_colour(hv[gone])
    Image.fromarray((np.clip(cv, 0, 1) * 255).astype(np.uint8)).save(f'{od}/color_{tag}.jpg', quality=90)
    sw = feather(v, 3)[..., None]; sv = col_sat * (1 - sw) + np.nan_to_num(dc) * sw
    Image.fromarray((np.clip(sv, 0, 1) * 255).astype(np.uint8)).save(f'{od}/sat_{tag}.jpg', quality=88)
    out = dict(date=tag, scenes=dv['scenes'], source='USGS Landsat 8 Collection 2 Level-2 surface reflectance (Planetary Computer)',
               files=dict(h16=f'h16_{tag}.png', ao='ao.png', color=f'color_{tag}.jpg', sat=f'sat_{tag}.jpg'), focus=dv['focus'],
               clear_in_focus=round(clear_focus, 3), filled_from_composite_pct=round(float((~v).mean() * 100), 1),
               land_m2_in_focus=round(land_m2, -2), land_px_on_grid=int(land.sum()), purpose=dv.get('purpose', ''), note=dv.get('note', ''))
    out['bytes'] = {k: os.path.getsize(f'{od}/{f}') for k, f in out['files'].items()}
    LOG(f'  dated {dv["name"]} {tag}: focus clear {clear_focus:.2f}, land {land_m2:.0f} m2 (30 m NIR unmixing), {int(land.sum())} grid px, '
        f'{out["filled_from_composite_pct"]} % of the picture filled from the composite')
    return out

# ---------- the bake
def bake(R, OUT, DLROOT, keep=False):
    t0 = time.time(); name = R['name']; bb = [float(x) for x in R['bbox']]; W, H = R['wh']
    dl = f'{DLROOT}/{name}'; od = f'{OUT}/{name}'; os.makedirs(dl, exist_ok=True); os.makedirs(od, exist_ok=True)
    midlat = (bb[1] + bb[3]) / 2; px_m = ((bb[2] - bb[0]) / W * 111320 * math.cos(math.radians(midlat)) + (bb[3] - bb[1]) / H * 111320) / 2
    tdeg = min((bb[2] - bb[0]) / W, (bb[3] - bb[1]) / H)
    LOG(f'== {name} bbox {bb} {W}x{H} ~{px_m:.0f} m/px')
    srcs = []; h = None; fine_topo = np.zeros((H, W), np.float32); cubic_src = 0.0
    for s in R.get('bathy', ['etopo15']):
        if s.startswith('region:'):  # a baked parent region (already cleaned of false land), e.g. a fine nest for one modelled rock
            pn = s.split(':', 1)[1]; pm = json.load(open(f'{OUT}/{pn}/meta.json')); pbb, (pw, phh) = pm['bbox'], pm['wh']
            a16 = np.asarray(Image.open(f'{OUT}/{pn}/h16.png')).astype(np.float32); ph = (a16[..., 0] * 256 + a16[..., 1]) / 65535 * HRANGE + HMIN
            lons, lats = grid_axes(bb, W, H); RY, CX = np.meshgrid((pbb[3] - lats) / (pbb[3] - pbb[1]) * phh - 0.5, (lons - pbb[0]) / (pbb[2] - pbb[0]) * pw - 0.5, indexing='ij')
            a = ndimage.map_coordinates(ph, [RY, CX], order=1, mode='nearest').astype(np.float32)
            srcs.append(dict(id=s, res_arcsec=round((pbb[2] - pbb[0]) / pw * 3600, 2), px_m=pm['px_m']))
        elif s.startswith('etopo'):
            p = etopo(bb, s[5:] + 's', dl); a = sample(p, bb, W, H, order=3 if p['d'] > tdeg * 1.5 else 1)
            if p['d'] > tdeg * 1.5: cubic_src = max(cubic_src, p['d'])
            srcs.append(dict(id=s, res_arcsec=round(p['d'] * 3600, 2)))
        else:
            ds = s.split(':', 1)[1]; p = ncei(ds, bb, dl, tdeg)
            if p is None: LOG(f'  {ds}: no overlap'); continue
            a = sample(p, bb, W, H, order=3 if p['d'] > tdeg * 1.5 else 1); srcs.append(dict(id=s, res_arcsec=round(p['d'] * 3600, 2), cover=round(float(np.isfinite(a).mean()), 3)))
        v = np.isfinite(a)
        if h is None: h = np.where(v, a, 0).astype(np.float32); continue
        w = feather(v, max(3, int(0.03 * min(W, H)))); h = h * (1 - w) + np.nan_to_num(a) * w
        if not s.startswith('ncei:hawaii_'):  # 1/3" and 3" coastal grids carry USGS land topography too
            fine_topo = np.maximum(fine_topo, w)
    base_m = min(x['res_arcsec'] for x in srcs) / 3600 * 111320
    land_cfg = R.get('land'); hls_early = None
    if land_cfg:
        z = land_cfg['z']; lb = land_cfg.get('bbox', bb)
        tr = terrarium(z, bb if lb == bb else bb, W, H, dl) if not land_cfg.get('bbox') else None
        if tr is None:  # only the land bbox: sample into a sub-window
            r0, c0 = rc_of(bb, W, H, lb[0], lb[3]); r1, c1 = rc_of(bb, W, H, lb[2], lb[1]); r0, c0 = max(r0, 0), max(c0, 0); r1, c1 = min(r1, H - 1), min(c1, W - 1)
            sub = [bb[0] + c0 / W * (bb[2] - bb[0]), bb[3] - (r1 + 1) / H * (bb[3] - bb[1]), bb[0] + (c1 + 1) / W * (bb[2] - bb[0]), bb[3] - r0 / H * (bb[3] - bb[1])]
            tr = np.full((H, W), np.nan, np.float32); tr[r0:r1 + 1, c0:c1 + 1] = terrarium(z, sub, c1 - c0 + 1, r1 - r0 + 1, dl)
        tv = np.isfinite(tr); trf = np.where(tv, tr, 0)
        mask = land_cfg.get('mask')
        if mask:
            # ETOPO 2022 15" carries spikes at the small NW Hawaiian islands (Gardner 859 m over 9 km2, La Perouse 251 m), and the land
            # tiles share some ghosts there (a 10 km2 blob east of Nihoa): land counts only where the land tiles show > 2 m AND
            # (mask 'hls') the HLS 30 m composite is not water there, or (keep boxes) inside a listed box; the rest is refilled from
            # the nearest seafloor and smoothed
            ok = tv & (trf > 2.0)
            if mask == 'hls':
                hl0 = R['colour']['hls']; sub, (r0, c0, r1, c1) = subwin(bb, W, H, hl0.get('bbox', bb))
                hc = hls_composite(sub, c1 - c0 + 1, r1 - r0 + 1, dl, hl0.get('level', 11), hl0.get('n', 8), tuple(hl0.get('months', ('2024-03-01', '2024-10-31'))), hl0.get('centre'), hl0.get('pct', 0.3))
                hls_early = hc
                lw = np.zeros((H, W), bool); lf = np.zeros((H, W), bool); hcol = np.zeros((H, W, 3), np.float32)
                if hc[0] is not None:
                    hn = np.nan_to_num(hc[0]); landish = np.isfinite(hc[0]).all(-1) & (hn[..., 0] >= 0.95 * hn[..., 2]) & (lum(hn) > 0.05)
                    lw[r0:r1 + 1, c0:c1 + 1] = ndimage.binary_dilation(landish, iterations=2); lf[r0:r1 + 1, c0:c1 + 1] = landish
                    hcol[r0:r1 + 1, c0:c1 + 1] = hn
                ok &= lw
                # vote per islet: surf on a reef crest passes the per-pixel test in specks, and the land tiles carry ghost heights
                # there (about 20 false islets each on the SE rim of Lalo and the W rim of Kure), so an islet stays only if at least
                # 'vote' (default 15 %) of its pixels look like land AND its mean HLS colour is not water-blue (red >= 0.85 blue;
                # Gardner's grey basalt is 0.91, surf specks on dark water far lower)
                lk, nk = ndimage.label(ok)
                if nk:
                    idx = range(1, nk + 1); fr = np.asarray(ndimage.mean(lf, lk, idx))
                    mr, mb = (np.asarray(ndimage.mean(hcol[..., k], lk, idx)) for k in (0, 2))
                    weak = 1 + np.where((fr < land_cfg.get('vote', 0.15)) | (mr < 0.85 * mb))[0]
                    if len(weak): ok &= ~np.isin(lk, weak); LOG(f'  land vote: {len(weak)} of {nk} islets dropped (surf or ghost land)')
            if 'keep' in land_cfg:
                kp = np.zeros((H, W), bool); lons, lats = grid_axes(bb, W, H)
                for k0 in land_cfg['keep']: kp |= ((lats[:, None] > k0[1]) & (lats[:, None] < k0[3])) & ((lons[None] > k0[0]) & (lons[None] < k0[2]))
                ok &= kp
            bogus = ((h > 0) | ok ^ (tv & (trf > 2.0))) & ~ok & (fine_topo < 0.5)
            trf = np.where(ok | (fine_topo >= 0.5), trf, np.minimum(trf, 0.0))  # the replace / raise steps below must not re-add it
            if bogus.any():
                # the spike's shallow skirt goes too: everything above mask_floor (default -10 m) connected to a false island is refilled
                floor = land_cfg.get('mask_floor', -10.0)
                lab, _ = ndimage.label(h > floor); ids = np.unique(lab[bogus]); ids = ids[ids > 0]
                grow = ndimage.binary_dilation(np.isin(lab, ids) | bogus, iterations=2)
                # a coarse grid upsampled with a cubic spline rings around each spike: '+'-shaped pits 10-20 m deep reach about two
                # source pixels out (seen around every Lalo islet), so the zone also takes that ring around every ETOPO land pixel,
                # false or real islet (only around the spikes: a ring around the whole shallow skirt would flatten real bank relief)
                ring = int(math.ceil(2.0 * cubic_src / tdeg)) if cubic_src else 2
                spike = h > 0
                if ring > 2 and spike.any(): grow |= ndimage.distance_transform_edt(~spike) <= ring
                grow &= ~ok
                src = ~grow & ~ok & (h <= floor)  # refill only from real seafloor, never from the spike or the confirmed land
                idx = ndimage.distance_transform_edt(~src, return_distances=False, return_indices=True)
                fill = h[tuple(idx)]; fill = np.minimum(ndimage.gaussian_filter(fill, max(2.0, ring / 3.0)), -1.0)
                if ring > 2 and ok.any():  # a shallow apron (reef flat, about -1.5 m) fading out over 120 m instead of a moat at the islet
                    ap = np.clip(1.0 - ndimage.distance_transform_edt(~ok) * px_m / 120.0, 0, 1)
                    fill = fill * (1 - ap) + np.maximum(fill, -1.5) * ap
                h = np.where(grow, fill, h)
                LOG(f'  land mask: {int(bogus.sum())} px of unconfirmed ETOPO land refilled from the seafloor ({int(grow.sum())} px zone, ring {ring} px)')
        k = max(2.0, base_m / px_m)
        low = ndimage.uniform_filter(trf, size=int(round(k)) | 1)
        land = np.clip(h / 30.0, 0, 1) * (1 - fine_topo) * tv
        h = np.where(tv & (h > 0), trf, h) if land_cfg.get('replace') else h + (trf - low) * land
        # sub-pixel islands the coarse grids flatten (pinnacles, sand islets): trust the land tiles where they are clearly above sea level
        isl = tv & (trf > 2.0) & (h > -60) & (fine_topo < 0.5)
        h = np.where(isl, np.maximum(h, trf), h)
        if land_cfg.get('cap') is not None:  # sand-islet atolls: land tiles carry ghost heights (11-93 m at French Frigate Shoals)
            h = np.where(h > 0, np.minimum(h, land_cfg['cap']), h)
        srcs.append(dict(id=f'terrarium_z{z}', res_m=round(156543.03 * math.cos(math.radians(midlat)) / 2 ** z, 1), land_only=True, cap_m=land_cfg.get('cap')))
        tp = land_cfg.get('top')
        if tp:  # the land tiles smooth a small steep island (Nihoa: 179 m on the grid, 273 m surveyed): scale its land to the survey top
            r, c = rc_of(bb, W, H, tp['lon'], tp['lat']); lab, _ = ndimage.label(h > 0); rr = max(1, int(tp.get('r_km', 1.0) * 1000 / px_m))
            win = lab[max(r - rr, 0):r + rr + 1, max(c - rr, 0):c + rr + 1]; ids = np.unique(win[win > 0])
            if len(ids):
                isl = np.isin(lab, ids); cur = float(h[isl].max()); f = tp['m'] / cur
                h = np.where(isl, h * f, h)
                srcs.append(dict(id='survey_top', top_from_m=round(cur), top_to_m=tp['m'], factor=round(f, 3), note=tp.get('note', '')))
                LOG(f'  land top: {cur:.0f} m on the grid -> {tp["m"]} m surveyed (land heights x {f:.3f})')
    rock_m = np.zeros((H, W), np.float32)
    for ft in R.get('features', []):  # modelled features no grid resolves (sea stacks, pinnacles) at their surveyed positions
        h, rm = rock_stack(h, bb, W, H, ft, px_m); rock_m = np.maximum(rock_m, rm)
        srcs.append(dict(id=f'model:{ft["name"]}', lon=ft['lon'], lat=ft['lat'], top_m=max(l[4] for l in ft['lobes']), note=ft.get('note', '')))
        LOG(f'  feature {ft["name"]}: top {float(h[rm > 0].max()) if (rm > 0).any() else 0:.1f} m over {int((rm > 0.5).sum())} px')
    h = h.astype(np.float32)  # float64 (the apron and stack maths) misread by Image.fromarray(h, 'F') zeroed 80 % of Lalo's AO
    coast = np.isfinite(h)
    h[(h > 0) & (h < 1)] = 1.0
    LOG(f'  h {h.min():.0f}..{h.max():.0f} ({time.time() - t0:.0f} s)')
    pack16(h).save(f'{od}/h16.png', compress_level=6)
    # ---- colour
    cw, ch = W, H
    col_meta = {}
    if R.get('colour', {}).get('modis', True):
        mc = R.get('colour', {})
        col, dates = modis_composite(bb, cw, ch, dl, mc.get('modis_n', 48), mc.get('modis_level', 8)); col_meta['modis'] = dates
    else:  # Blue Marble NG only (wide context layers)
        col = np.clip(np.nan_to_num(sample(gibs('BlueMarble_NextGeneration', '500m', '2004-07-01', R['colour'].get('bmng_level', 6), 'jpeg', bb, dl), bb, cw, ch), nan=0.3), 0, 1)
        col_meta['bmng'] = 'BlueMarble_NextGeneration 2004-07'
    hl = R.get('colour', {}).get('hls'); hls_cov = np.zeros((H, W), bool)
    if hl:
        sub, (r0, c0, r1, c1) = subwin(bb, W, H, hl.get('bbox', bb))
        months = hl.get('months', ('2024-03-01', '2024-10-31')); ranges = [months] if isinstance(months[0], str) else months
        pc = hl.get('source') == 'pc'; st = {}
        if pc:  # HLS v2 with Fmask from the Planetary Computer (clouds removed per scene)
            hc, used, st = hlsfm_composite(sub, c1 - c0 + 1, r1 - r0 + 1, dl, ranges, hl.get('n', 24), hl.get('snow', False), hl.get('stat', 50))
        else:
            hc, used = hls_early if hls_early is not None else hls_composite(sub, c1 - c0 + 1, r1 - r0 + 1, dl, hl.get('level', 11), hl.get('n', 8), tuple(months), hl.get('centre'), hl.get('pct', 0.3))
        if hc is not None:
            v = np.isfinite(hc).all(-1); hsub = h[r0:r1 + 1, c0:c1 + 1]
            # one luminance gain (hue kept) so HLS land matches the brightness the stage grade was tuned on (MODIS), only with enough
            # shared land; there, HLS pixels far brighter (cloud) or darker (cloud shadow) than the 48-day MODIS composite are dropped
            # (GIBS source only: Fmask has already removed them, and MODIS itself is cloudy where it matters, e.g. the Ko'olau crest)
            m = v & (ndimage.minimum_filter(hsub, size=max(3, int(500 / px_m))) > 5)
            g = np.full(3, hl.get('gain', 0.7), np.float32); mc = col[r0:r1 + 1, c0:c1 + 1]  # 0.7: between the gains measured on Maui Nui (0.63) and O'ahu (0.76)
            if m.sum() > 2000 and hl.get('match', True):
                g[:] = np.clip(np.median(lum(mc[m])) / max(float(np.median(lum(hc[m]))), 1e-3), 0.6, 1.6)
                if not pc:
                    lh, lm = lum(np.nan_to_num(hc) * g), lum(mc)
                    bad = m & ((lh > 1.5 * lm + 0.06) | (lh < 0.5 * lm - 0.01))
                    v = v & ~ndimage.binary_dilation(bad, iterations=2)
                    LOG(f'  hls: gain {g[0]:.3f}, {int(bad.sum())} cloud/shadow px left to MODIS')
                else: LOG(f'  hls: gain {g[0]:.3f} (median MODIS / HLS luminance over {int(m.sum())} land px)')
            if hl.get('sat') is not None:  # one chroma factor about luminance (hue kept), only with a measured reason in the spec
                lh = lum(np.nan_to_num(hc))[..., None]; hc = lh + (hc - lh) * hl['sat']
            w = feather(v, 6)[..., None]; hls_cov[r0:r1 + 1, c0:c1 + 1] = w[..., 0] > 0.5
            col[r0:r1 + 1, c0:c1 + 1] = col[r0:r1 + 1, c0:c1 + 1] * (1 - w) + np.nan_to_num(hc * g) * w
            col_meta['hls'] = dict(level=hl.get('level', 11), dates=used, gain=[round(float(x), 3) for x in g], bbox=[round(x, 4) for x in sub])
            if pc: col_meta['hls'].update(source='HLS v2 S30+L30 with Fmask (Planetary Computer)', stat=hl.get('stat', 50), **st)
            if hl.get('sat') is not None: col_meta['hls']['sat'] = hl['sat']
    files = dict(h16='h16.png', ao='ao.png', color='color.jpg')
    col_sat = col.copy()
    if R.get('colour', {}).get('sat'):  # the satellite picture including the sea (reef rings, lagoons) before the land-only fill
        Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(f'{od}/sat.jpg', quality=88); files['sat'] = 'sat.jpg'
    sea_mode = R.get('colour', {}).get('sea')   # 'depth': sea-floor texels coloured by depth (sea_colour), beaches keep their own colour
    landc = h > (0.5 if sea_mode in ('depth', 'sat') else 2)
    lumc = lum(col); mx_, mn_ = col.max(-1), col.min(-1)
    # residual cloud specks in the MODIS composite (never on HLS pixels: their clouds were handled above, and snow and sand are bright)
    cloud = (lumc > 0.30) & ((mx_ - mn_) / np.maximum(mx_, 1e-3) < 0.22) & ~((h < 6) & landc) & ~hls_cov
    cloud = ndimage.maximum_filter(cloud, size=3)
    col = fill_sea(col, (landc & ~cloud).astype(np.float32)) if landc.any() else col
    if sea_mode in ('depth', 'sat'):  # 'sat': the HLS picture of the shallow sea floor where HLS covers (lagoons, reef flats seen
        # through clear water, e.g. Kane'ohe Bay), by depth elsewhere; 'depth': by depth everywhere (regions shown drained)
        sc = sea_colour(h)
        if sea_mode == 'sat': sc = np.where(hls_cov[..., None], col_sat, sc)
        ws = np.clip((0.5 - h) / 1.5, 0, 1)[..., None]; col = col * (1 - ws) + sc * ws
        col_meta['sea'] = ('the HLS picture where HLS covers, else ' if sea_mode == 'sat' else '') + \
            'by depth (sand flat at 0 m to the film reef grey by -6 m), never the nearest land colour'
    if rock_m.any():  # modelled rock: dark basalt, guano-pale on the upper third (seabird roost)
        top = np.where(rock_m > 0, h, 0); tmax = max(float(top.max()), 1.0); gu = np.clip((h - 0.72 * tmax) / (0.2 * tmax), 0, 1)[..., None]
        gn = ndimage.gaussian_filter(np.random.default_rng(3).standard_normal(h.shape), 1.2); gn /= max(float(np.abs(gn).max()), 1e-6)
        gu = gu * np.clip(0.2 + 1.4 * gn, 0, 1)[..., None] * 0.8                 # streaks and patches of guano on the crown, not a cap
        rc = np.array([0.20, 0.17, 0.15], np.float32) * (1 - gu) + np.array([0.66, 0.64, 0.60], np.float32) * gu
        col = col * (1 - rock_m[..., None]) + rc * rock_m[..., None]
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(f'{od}/color.jpg', quality=90)
    # ---- AO at half resolution (full for small grids)
    f = 2 if W * H > 2.5e6 else 1
    h2 = np.asarray(Image.fromarray(h, 'F').resize((W // f, H // f), Image.BOX)) if f > 1 else h
    ao_tan = R.get('ao') == 'tangent'
    Image.fromarray((bake_ao(h2, bb, px_m * f, ao_tan) * 255).astype(np.uint8)).save(f'{od}/ao.png')
    variants = {}
    for dv in R.get('dated', []):  # dated scenes of the same grid (e.g. East Island before and after Hurricane Walaka, 2018)
        variants[dv['name']] = dated_variant(dv, h, col, col_sat, bb, W, H, px_m, od, dl)
    meta = dict(name=name, bbox=bb, wh=[W, H], px_m=round(px_m, 1), hmin=HMIN, hrange=HRANGE, vex=1.0,
                files=files, sources=srcs, colour=col_meta,
                facts=facts(h, bb, R.get('facts', {}), px_m), purpose=R.get('purpose', ''), gaps=R.get('gaps', []),
                bake_s=round(time.time() - t0, 1), baked=time.strftime('%Y-%m-%d'))
    if ao_tan: meta['ao'] = 'tangent (horizon above the local slope)'
    meta['bytes'] = {k: os.path.getsize(f'{od}/{v}') for k, v in meta['files'].items()}
    if variants: meta['variants'] = variants
    json.dump(meta, open(f'{od}/meta.json', 'w'), indent=1, ensure_ascii=False)
    if not keep: shutil.rmtree(dl, ignore_errors=True)
    LOG(f'  done {name} in {time.time() - t0:.0f} s, {sum(meta["bytes"].values()) / 1e6:.1f} MB; facts {json.dumps(meta["facts"], ensure_ascii=False)[:600]}')
    return meta

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec'); ap.add_argument('--only'); ap.add_argument('--out', required=True); ap.add_argument('--dl', required=True)
    ap.add_argument('--keep', action='store_true'); ap.add_argument('--name'); ap.add_argument('--bbox'); ap.add_argument('--wh')
    ap.add_argument('--bathy', default='etopo15'); ap.add_argument('--land-z', type=int); ap.add_argument('--modis', type=int, default=48); ap.add_argument('--hls', type=int)
    A = ap.parse_args()
    if A.spec:
        S = json.load(open(A.spec)); only = set(A.only.split(',')) if A.only else None
        for R in S['regions']:
            if R.get('legacy') or (only and R['name'] not in only): continue
            bake(R, A.out, A.dl, A.keep)
    else:
        R = dict(name=A.name, bbox=[float(x) for x in A.bbox.split(',')], wh=[int(x) for x in A.wh.split(',')], bathy=A.bathy.split(','),
                 land=dict(z=A.land_z) if A.land_z else None, colour=dict(modis_n=A.modis, hls=dict(level=A.hls) if A.hls else None))
        bake(R, A.out, A.dl, A.keep)
