#!/usr/bin/env python3
"""Five-second proof: Blue Marble globe down to the Neum corridor.

Imagery is Landsat 9 Collection 2 Level-2 (USGS, public domain), 30 m.
Terrain is SRTM GL1 (NASA/USGS, public domain), 30 m, draped on the image.
No Sentinel-2, Copernicus, ESRI, Mapbox, or Google pixels.

    python3 examples/neum_zoom/render_proof.py
"""

from __future__ import annotations

import gzip
import json
import math
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import skia
from PIL import Image
from osgeo import gdal, ogr, osr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = Path("/workspace/asset_library/extra/neum_proof")
MARBLE = ROOT / "data" / "cache" / "bmng_jul_10800.npy"
SHP = Path(
    "/workspace/asset_library/extra/natural_earth/10m_cultural/"
    "10m_cultural/ne_10m_admin_0_countries.shp"
)
W, H, FPS, N = 1080, 1920, 30, 150
# Native Landsat pixel. The close view shows one source pixel per screen pixel.
GSD = 30.0
NEUM_LON, NEUM_LAT = 17.616, 42.923
SR_SCALE, SR_OFF = 0.0000275, -0.2


def _smooth(x: float) -> float:
    x = 0.0 if x < 0 else 1.0 if x > 1 else x
    return x * x * (3.0 - 2.0 * x)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _read(path: Path, dtype, gdt):
    ds = gdal.Open(str(path))
    band = ds.GetRasterBand(1)
    raw = band.ReadRaster(0, 0, ds.RasterXSize, ds.RasterYSize, buf_type=gdt)
    arr = np.frombuffer(raw, dtype).reshape(ds.RasterYSize, ds.RasterXSize)
    return arr, ds.GetGeoTransform()


def _sign_landsat() -> dict:
    body = json.dumps({
        "collections": ["landsat-c2-l2"],
        "intersects": {"type": "Point", "coordinates": [NEUM_LON, NEUM_LAT]},
        "query": {
            "eo:cloud_cover": {"lt": 5},
            "platform": {"in": ["landsat-8", "landsat-9"]},
        },
        "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}],
        "limit": 1,
    }).encode()
    req = urllib.request.Request(
        "https://planetarycomputer.microsoft.com/api/stac/v1/search",
        data=body, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        feat = json.load(resp)["features"][0]
    hrefs = {}
    for key in ("red", "green", "blue"):
        raw = feat["assets"][key]["href"]
        sign = (
            "https://planetarycomputer.microsoft.com/api/sas/v1/sign?href="
            + urllib.parse.quote(raw, safe="")
        )
        with urllib.request.urlopen(sign, timeout=60) as resp:
            hrefs[key] = json.load(resp)["href"]
    return {
        "id": feat["id"],
        "datetime": feat["properties"].get("datetime"),
        "cloud": feat["properties"].get("eo:cloud_cover"),
        "hrefs": hrefs,
    }


def prepare() -> dict:
    """Window a clear Landsat 9 scene and the two SRTM tiles under Neum."""
    DATA.mkdir(parents=True, exist_ok=True)
    meta_path = DATA / "scene.json"
    if not (DATA / "b4.tif").exists():
        meta = _sign_landsat()
        bounds = (17.28, 42.50, 17.98, 43.34)
        names = {"red": "b4.tif", "green": "b3.tif", "blue": "b2.tif"}
        for key, name in names.items():
            gdal.Warp(
                str(DATA / name), "/vsicurl/" + meta["hrefs"][key],
                outputBounds=bounds, outputBoundsSRS="EPSG:4326",
                dstSRS="EPSG:32633", xRes=GSD, yRes=GSD,
                resampleAlg="bilinear", creationOptions=["COMPRESS=DEFLATE"],
            )
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    else:
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {
            "id": "LC09_L2SP_188030_20260819_02_T1",
            "datetime": "2026-08-19T09:34:14Z",
            "cloud": 0.47,
        }
    if not (DATA / "dem.tif").exists():
        for name in ("N42E017", "N43E017"):
            lat = name[:3]
            gz = DATA / f"{name}.hgt.gz"
            if not gz.exists():
                urllib.request.urlretrieve(
                    f"https://elevation-tiles-prod.s3.amazonaws.com/skadi/{lat}/{name}.hgt.gz",
                    gz,
                )
            hgt = DATA / f"{name}.hgt"
            if not hgt.exists():
                hgt.write_bytes(gzip.open(gz, "rb").read())
        red = gdal.Open(str(DATA / "b4.tif"))
        gt = red.GetGeoTransform()
        gdal.Warp(
            str(DATA / "dem.tif"),
            [str(DATA / "N42E017.hgt"), str(DATA / "N43E017.hgt")],
            format="GTiff",
            outputBounds=(gt[0], gt[3] + gt[5] * red.RasterYSize, gt[0] + gt[1] * red.RasterXSize, gt[3]),
            outputBoundsSRS="EPSG:32633",
            width=red.RasterXSize, height=red.RasterYSize,
            dstSRS="EPSG:32633", resampleAlg="bilinear",
            creationOptions=["COMPRESS=DEFLATE"],
        )
    return meta


def _transformer():
    src = osr.SpatialReference()
    src.ImportFromEPSG(4326)
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(32633)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return osr.CoordinateTransformation(src, dst), osr.CoordinateTransformation(dst, src)


def _borders() -> list[np.ndarray]:
    to_utm, _back = _transformer()
    ds = ogr.Open(str(SHP))
    layer = ds.GetLayer()
    layer.SetSpatialFilterRect(17.15, 42.35, 18.15, 43.5)
    layer.SetAttributeFilter("ADM0_A3 IN ('BIH','HRV')")
    lines = []
    for feat in layer:
        geom = feat.GetGeometryRef()
        geom.FlattenTo2D()
        for i in range(geom.GetGeometryCount() or 1):
            ring = geom.GetGeometryRef(i) if geom.GetGeometryCount() else geom
            # walk every linestring inside
            parts = [ring]
            if ring.GetGeometryCount():
                parts = [ring.GetGeometryRef(j) for j in range(ring.GetGeometryCount())]
            for part in parts:
                pts = []
                count = part.GetPointCount()
                for k in range(count):
                    lon, lat, _z = part.GetPoint(k)
                    if not (17.2 <= lon <= 18.1 and 42.4 <= lat <= 43.45):
                        if len(pts) > 1:
                            lines.append(np.asarray(pts, np.float64))
                        pts = []
                        continue
                    e, n, _z = to_utm.TransformPoint(lon, lat)
                    pts.append((e, n))
                if len(pts) > 1:
                    lines.append(np.asarray(pts, np.float64))
    return lines


def build_texture(marble: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple, tuple, list]:
    red, gt = _read(DATA / "b4.tif", np.uint16, gdal.GDT_UInt16)
    green, _ = _read(DATA / "b3.tif", np.uint16, gdal.GDT_UInt16)
    blue, _ = _read(DATA / "b2.tif", np.uint16, gdal.GDT_UInt16)
    dem, _ = _read(DATA / "dem.tif", np.float32, gdal.GDT_Float32)
    dem = np.where(dem < -100, 0, dem).astype(np.float32)
    refl = np.clip(np.stack([red, green, blue], -1).astype(np.float32) * SR_SCALE + SR_OFF, 0, None)
    stretched = np.empty_like(refl)
    for i in range(3):
        lo, hi = np.percentile(refl[:, :, i], (2, 98))
        stretched[:, :, i] = np.clip((refl[:, :, i] - lo) / max(1e-6, hi - lo), 0, 1)
    # Pull the stretched scene a third of the way toward the Blue Marble color
    # of this same coast, so the zoom does not jump families.
    marble_mean = _marble_mean(marble, gt, red.shape)
    local = stretched.reshape(-1, 3).mean(axis=0)
    gain = (0.67 * local + 0.33 * marble_mean) / np.maximum(local, 1e-3)
    matched = np.clip(stretched * gain, 0, 1)
    dy, dx = np.gradient(dem, GSD, GSD)
    az, alt = math.radians(315), math.radians(42)
    sx, sy, sz = math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)
    nx, ny, nz = -dx, -dy, np.ones_like(dx)
    shade = np.clip((nx * sx + ny * sy + nz * sz) / np.sqrt(nx * nx + ny * ny + nz * nz), 0, 1)
    water = (dem < 1.0) & (refl[:, :, 2] + 0.01 < refl[:, :, 1])
    shade = np.where(water, 0.92, shade)
    rgb = np.clip(matched * (0.60 + 0.40 * shade[..., None]), 0, 1)
    tex = (rgb * 255).astype(np.uint8)
    to_utm, _back = _transformer()
    e, n, _z = to_utm.TransformPoint(NEUM_LON, NEUM_LAT)
    col = (e - gt[0]) / gt[1]
    row = (gt[3] - n) / (-gt[5])
    return tex, dem, gt, (col, row), _borders()


def _marble_mean(marble: np.ndarray, gt, shape) -> np.ndarray:
    h, w = shape
    # Four corners of the Landsat window, in lon/lat via the inverse UTM.
    _fwd, back = _transformer()
    corners = []
    for c, r in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        e = gt[0] + (c + 0.5) * gt[1]
        n = gt[3] + (r + 0.5) * gt[5]
        lon, lat, _z = back.TransformPoint(e, n)
        corners.append((lon, lat))
    lons = [p[0] for p in corners]
    lats = [p[1] for p in corners]
    samples = []
    for lat in np.linspace(min(lats), max(lats), 24):
        for lon in np.linspace(min(lons), max(lons), 24):
            rr = int(np.clip((90 - lat) / 180 * marble.shape[0], 0, marble.shape[0] - 1))
            cc = int(np.clip((lon + 180) / 360 * marble.shape[1], 0, marble.shape[1] - 1))
            samples.append(marble[rr, cc])
    return np.mean(samples, axis=0).astype(np.float32) / 255.0


def _sample_equirect(marble: np.ndarray, lat, lon) -> np.ndarray:
    rr = (90.0 - lat) / 180.0 * marble.shape[0]
    cc = (lon + 180.0) / 360.0 * marble.shape[1]
    rr = np.clip(rr, 0, marble.shape[0] - 1.001)
    cc = np.clip(cc, 0, marble.shape[1] - 1.001)
    r0 = np.floor(rr).astype(np.int32)
    c0 = np.floor(cc).astype(np.int32)
    fr = (rr - r0)[..., None]
    fc = (cc - c0)[..., None]
    a = marble[r0, c0].astype(np.float32)
    b = marble[r0, np.minimum(c0 + 1, marble.shape[1] - 1)].astype(np.float32)
    c = marble[np.minimum(r0 + 1, marble.shape[0] - 1), c0].astype(np.float32)
    d = marble[np.minimum(r0 + 1, marble.shape[0] - 1), np.minimum(c0 + 1, marble.shape[1] - 1)].astype(np.float32)
    return (a * (1 - fc) + b * fc) * (1 - fr) + (c * (1 - fc) + d * fc) * fr


def render_globe(marble: np.ndarray, lon0: float, lat0: float, width_m: float) -> np.ndarray:
    """Orthographic Earth. width_m is the ground width of the frame at the center."""
    ys, xs = np.mgrid[0:H, 0:W]
    # scale > 1 leaves space around the disk, so the opening reads as a globe.
    scale = (width_m / 2) / 6378137.0
    rx = (xs - (W - 1) / 2) / (W / 2) * scale
    ry = ((H - 1) / 2 - ys) / (W / 2) * scale
    rho2 = rx * rx + ry * ry
    vis = rho2 < 1.0
    rz = np.zeros_like(rx)
    rz[vis] = np.sqrt(1.0 - rho2[vis])
    clon, slon = math.cos(math.radians(lon0)), math.sin(math.radians(lon0))
    clat, slat = math.cos(math.radians(lat0)), math.sin(math.radians(lat0))
    # East, north, and outward, so the disk is the Earth under (lon0, lat0).
    px = (-slon) * rx + (-slat * clon) * ry + (clat * clon) * rz
    py = (clon) * rx + (-slat * slon) * ry + (clat * slon) * rz
    pz = clat * ry + slat * rz
    lat = np.degrees(np.arcsin(np.clip(pz, -1, 1)))
    lon = np.degrees(np.arctan2(py, px))
    rgb = np.zeros((H, W, 3), np.float32)
    rgb[:] = (6, 12, 22)
    if np.any(vis):
        rgb[vis] = _sample_equirect(marble, lat[vis], lon[vis])
    # Soft limb so the disk reads as a globe.
    limb = np.clip((1.0 - rho2) * 8.0, 0, 1)
    rgb = rgb * (0.35 + 0.65 * limb[..., None])
    rgb[~vis] = (6, 12, 22)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def render_marble_flat(marble: np.ndarray, lon0, lat0, width_m: float) -> np.ndarray:
    m_per_deg_lon = 111320.0 * math.cos(math.radians(lat0))
    m_per_deg_lat = 110540.0
    half_w = width_m / 2
    half_h = half_w * (H / W)
    ys, xs = np.mgrid[0:H, 0:W]
    lon = lon0 + ((xs - (W - 1) / 2) / (W / 2)) * (half_w / m_per_deg_lon)
    lat = lat0 + (((H - 1) / 2 - ys) / (W / 2)) * (half_w / m_per_deg_lat)
    return np.clip(_sample_equirect(marble, lat, lon), 0, 255).astype(np.uint8)


def _camera(width_m: float, tilt_deg: float):
    """Eye in meters, looking at the origin. +x east, +y north, +z up."""
    tilt = math.radians(tilt_deg)
    # Focal length so a nadir view of width_m fills the frame.
    focal = 900.0
    dist = (width_m / 2) * focal / (W / 2)
    eye = np.array([0.0, -dist * math.sin(tilt), dist * math.cos(tilt)], np.float64)
    forward = -eye / np.linalg.norm(eye)
    world_up = np.array([0.0, 1.0, 0.0]) if tilt < 0.04 else np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return eye, right, up, forward, focal


def render_terrain(tex, dem, gt, neum_px, lines, width_m, tilt_deg) -> np.ndarray:
    col_c, row_c = neum_px
    ox, pw, _a, oy, _b, ph = gt
    # Keep the mesh under Skia's vertex-list limit. Geometry is ~300 m;
    # the texture sample is still the 30 m Landsat pixel.
    xs = np.linspace(-20_000, 20_000, 100)
    ys = np.linspace(-24_000, 48_000, 160)
    x, y = np.meshgrid(xs, ys)
    east = (ox + (col_c + 0.5) * pw) + x
    north = (oy + (row_c + 0.5) * ph) + y
    cc = np.clip((east - ox) / pw, 0, tex.shape[1] - 1.001)
    rr = np.clip((oy - north) / (-ph), 0, tex.shape[0] - 1.001)
    r0 = np.floor(rr).astype(np.int32)
    c0 = np.floor(cc).astype(np.int32)
    zz = dem[r0, c0]
    neum_e = ox + (col_c + 0.5) * pw
    neum_n = oy + (row_c + 0.5) * ph
    x = east - neum_e
    y = north - neum_n
    z = np.maximum(zz, 0) * 2.6
    eye, right, up, forward, focal = _camera(width_m, tilt_deg)
    rel_x = x - eye[0]
    rel_y = y - eye[1]
    rel_z = z - eye[2]
    vx = rel_x * right[0] + rel_y * right[1] + rel_z * right[2]
    vy = rel_x * up[0] + rel_y * up[1] + rel_z * up[2]
    vz = rel_x * forward[0] + rel_y * forward[1] + rel_z * forward[2]
    sx = W / 2 + vx / np.maximum(vz, 1.0) * focal
    sy = H / 2 - vy / np.maximum(vz, 1.0) * focal
    ny, nx = sx.shape
    ii, jj = np.mgrid[0:ny - 1, 0:nx - 1]
    a = (ii * nx + jj).ravel()
    b = a + 1
    c = a + nx
    d = c + 1
    front = vz.ravel()
    keep = (front[a] > 40) & (front[b] > 40) & (front[c] > 40) & (front[d] > 40)
    tris = np.concatenate([np.stack([a, b, c], -1), np.stack([b, d, c], -1)])
    # The second triangle reuses the same keep mask, so repeat it.
    keep2 = np.concatenate([keep, keep])
    idx = tris[keep2].ravel()
    positions = [skia.Point(float(sx.ravel()[i]), float(sy.ravel()[i])) for i in range(sx.size)]
    texs = [skia.Point(float(cc.ravel()[i]), float(rr.ravel()[i])) for i in range(sx.size)]
    verts = skia.Vertices.MakeCopy(
        skia.Vertices.kTriangles_VertexMode, positions, texs, None, [int(i) for i in idx],
    )
    image = _skia_image(tex)
    surface = skia.Surface(W, H)
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f(0.03, 0.06, 0.10, 1))
    paint = skia.Paint(AntiAlias=True)
    paint.setShader(image.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp))
    canvas.drawVertices(verts, paint)
    _draw_border(canvas, lines, neum_e, neum_n, eye, right, up, forward, focal, gt, None)
    return _snapshot(surface)


def _draw_border(canvas, lines, neum_e, neum_n, eye, right, up, forward, focal, gt, crop):
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4.0)
    pen.setColor(skia.ColorSetARGB(230, 255, 214, 40))
    ox, pw, _a, oy, _b, ph = gt
    for line in lines:
        path = skia.Path()
        started = False
        for e, n in line[::3]:
            if crop is None:
                x = e - neum_e
                y = n - neum_n
                if abs(x) > 20_000 or y < -24_000 or y > 48_000:
                    started = False
                    continue
                # Sit the line just above the drape so it stays on the land.
                z = 80.0 * 2.6
                vx = (x - eye[0]) * right[0] + (y - eye[1]) * right[1] + (z - eye[2]) * right[2]
                vy = (x - eye[0]) * up[0] + (y - eye[1]) * up[1] + (z - eye[2]) * up[2]
                vz = (x - eye[0]) * forward[0] + (y - eye[1]) * forward[1] + (z - eye[2]) * forward[2]
                if vz < 8:
                    started = False
                    continue
                sx = W / 2 + vx / vz * focal
                sy = H / 2 - vy / vz * focal
            else:
                col0, row0, cw, ch = crop
                col = (e - ox) / pw
                row = (oy - n) / (-ph)
                sx = (col - col0) / cw * W
                sy = (row - row0) / ch * H
            if not started:
                path.moveTo(sx, sy)
                started = True
            else:
                path.lineTo(sx, sy)
        canvas.drawPath(path, pen)


def render_landsat_nadir(tex, gt, neum_px, lines, width_m) -> np.ndarray:
    col_c, row_c = neum_px
    crop_w = width_m / GSD
    crop_h = crop_w * (H / W)
    col0 = col_c - crop_w / 2
    row0 = row_c - crop_h / 2
    # Pull a window and scale to the frame. At 30 m/px this is 1:1.
    x0 = int(math.floor(col0))
    y0 = int(math.floor(row0))
    x1 = int(math.ceil(col0 + crop_w))
    y1 = int(math.ceil(row0 + crop_h))
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(tex.shape[1], x1)
    y1 = min(tex.shape[0], y1)
    view = np.array(Image.fromarray(tex[y0:y1, x0:x1]).resize((W, H), Image.Resampling.BICUBIC))
    surface = skia.Surface(W, H)
    canvas = surface.getCanvas()
    canvas.drawImage(_skia_image(view), 0, 0)
    ox, pw, _a, oy, _b, ph = gt
    neum_e = ox + (neum_px[0] + 0.5) * pw
    neum_n = oy + (neum_px[1] + 0.5) * ph
    _draw_border(canvas, lines, neum_e, neum_n, None, None, None, None, None, gt, (col0, row0, crop_w, crop_h))
    return _snapshot(surface)


def _skia_image(rgb: np.ndarray):
    if rgb.shape[-1] == 3:
        rgba = np.dstack([rgb, np.full(rgb.shape[:2], 255, np.uint8)])
    else:
        rgba = rgb
    return skia.Image.fromarray(np.ascontiguousarray(rgba))


def _snapshot(surface) -> np.ndarray:
    bgra = surface.makeImageSnapshot().toarray()
    return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])


def _label(img: np.ndarray, text: str, sub: str) -> np.ndarray:
    surface = skia.Surface(W, H)
    canvas = surface.getCanvas()
    canvas.drawImage(_skia_image(img), 0, 0)
    font_path = ROOT / "fonts" / "Montserrat-Black.ttf"
    face = skia.Typeface.MakeFromFile(str(font_path)) if font_path.exists() else None
    if face is None:
        face = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(210, 12, 14, 18))
    font = skia.Font(face, 42)
    blob = skia.TextBlob.MakeFromString(text, font)
    bounds = blob.bounds()
    cx, cy = W / 2, 250
    rect = skia.Rect.MakeXYWH(cx - bounds.width() / 2 - 22, cy - 40, bounds.width() + 44, 96)
    canvas.drawRoundRect(rect, 18, 18, paint)
    fill = skia.Paint(AntiAlias=True)
    fill.setColor(skia.ColorSetARGB(255, 255, 236, 64))
    canvas.drawTextBlob(blob, cx - bounds.width() / 2, cy, fill)
    small = skia.Font(face, 26)
    sub_blob = skia.TextBlob.MakeFromString(sub, small)
    sw = sub_blob.bounds().width()
    fill.setColor(skia.ColorSetARGB(255, 255, 248, 236))
    canvas.drawTextBlob(sub_blob, cx - sw / 2, cy + 36, fill)
    return _snapshot(surface)


def shot(t: float) -> dict:
    z = _smooth((t - 0.45) / 2.55)
    width = math.exp(_lerp(math.log(16_000_000), math.log(W * GSD), z))
    arrive = _smooth(min(1.0, z * 1.25))
    lon = _lerp(15.6, NEUM_LON, arrive)
    lat = _lerp(44.2, NEUM_LAT, arrive)
    # Landsat only covers ~50 km in this window. Blend once the view fits in it.
    alpha = _smooth((50_000 - width) / (50_000 - 36_000)) if width < 50_000 else 0.0
    tilt = 50.0 * _smooth((t - 3.35) / 1.25)
    if t < 3.35:
        tilt = 0.0
    return {"lon": lon, "lat": lat, "width": width, "alpha": alpha, "tilt": tilt}


def render_frame(t, marble, tex, dem, gt, neum_px, lines) -> np.ndarray:
    st = shot(t)
    if st["width"] > 1_400_000:
        base = render_globe(marble, st["lon"], st["lat"], st["width"])
    else:
        base = render_marble_flat(marble, st["lon"], st["lat"], st["width"])
    if st["alpha"] <= 0.02:
        img = base
    else:
        if st["tilt"] < 1.0:
            close = render_landsat_nadir(tex, gt, neum_px, lines, max(st["width"], W * GSD))
        else:
            close = render_terrain(tex, dem, gt, neum_px, lines, W * GSD, st["tilt"])
        a = st["alpha"]
        img = (base.astype(np.float32) * (1 - a) + close.astype(np.float32) * a).astype(np.uint8)
    if t > 3.5:
        gsd = st["width"] / W
        img = _label(img, "NEUM", f"Croatia  ·  Bosnia    {gsd:.0f} m/px")
    return img


def center_gsd(tex_shape, gt, neum_px) -> float:
    """Ground meters per screen pixel at the settled nadir frame."""
    return (W * GSD) / W


def main() -> None:
    meta = prepare()
    marble = np.load(MARBLE, mmap_mode="r")
    tex, dem, gt, neum_px, lines = build_texture(marble)
    print("neum pixel", [round(v, 1) for v in neum_px], "tex", tex.shape, "borders", len(lines), flush=True)
    print("scene", meta.get("id"), meta.get("datetime"), "cloud", meta.get("cloud"), flush=True)
    dest = OUT / "neum_zoom_proof.mp4"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "18", "-preset", "veryfast",
        "-movflags", "+faststart",
        str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(N):
            frame = render_frame(i / FPS, marble, tex, dem, gt, neum_px, lines)
            if i in (0, 60, 100, 149):
                Image.fromarray(frame).save(OUT / f"frame_{i / FPS:04.2f}.png")
            proc.stdin.write(frame.tobytes())
            if i % 15 == 0:
                print(f"frame {i}/{N} {shot(i / FPS)}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    report = {
        "scene": meta.get("id"),
        "acquired": meta.get("datetime"),
        "cloud_cover_pct": meta.get("cloud"),
        "imagery": "USGS Landsat 9 Collection 2 Level-2 surface reflectance, public domain",
        "terrain": "NASA/USGS SRTM GL1 1-arc-second, public domain",
        "display_gsd_m": GSD,
        "source_gsd_m": GSD,
        "frames": N,
        "fps": FPS,
        "duration_s": N / FPS,
        "center": {"lon": NEUM_LON, "lat": NEUM_LAT},
    }
    (OUT / "proof_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
