#!/usr/bin/env python3
"""6–8 s proofs: Temburong, then Pelješac.

    python3 examples/model_drop/render_tests.py temburong
    python3 examples/model_drop/render_tests.py peljesac
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia
from PIL import Image
from osgeo import gdal, osr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.model_drop import (  # noqa: E402
    build_cues,
    parse_spec,
    progress,
    tilt_deg,
    zoom_width,
    draw,
)

HERE = Path(__file__).resolve().parent
MARBLE = ROOT / "data" / "cache" / "bmng_jul_10800.npy"
W, H, FPS = 1080, 1920, 30


def _smooth(x: float) -> float:
    x = 0.0 if x < 0 else 1.0 if x > 1 else x
    return x * x * (3.0 - 2.0 * x)


def _read(path, dtype, gdt):
    ds = gdal.Open(str(path))
    band = ds.GetRasterBand(1)
    raw = band.ReadRaster(0, 0, ds.RasterXSize, ds.RasterYSize, buf_type=gdt)
    arr = np.frombuffer(raw, dtype).reshape(ds.RasterYSize, ds.RasterXSize)
    return arr, ds.GetGeoTransform()


def load_landsat(folder: Path) -> tuple[np.ndarray, tuple]:
    red, gt = _read(folder / "b4.tif", np.uint16, gdal.GDT_UInt16)
    green, _ = _read(folder / "b3.tif", np.uint16, gdal.GDT_UInt16)
    blue, _ = _read(folder / "b2.tif", np.uint16, gdal.GDT_UInt16)
    refl = np.clip(np.stack([red, green, blue], -1).astype(np.float32) * 0.0000275 - 0.2, 0, None)
    out = np.empty_like(refl)
    for i in range(3):
        lo, hi = np.percentile(refl[:, :, i], (2, 98))
        out[:, :, i] = np.clip((refl[:, :, i] - lo) / max(1e-6, hi - lo), 0, 1)
    return (out * 255).astype(np.uint8), gt


def _ll_of(east, north, lat0, lon0):
    lat = lat0 + math.degrees(north / 6378137.0)
    lon = lon0 + math.degrees(east / (6378137.0 * math.cos(math.radians(lat0))))
    return lat, lon


def _pix(lon, lat, gt, utm):
    src = osr.SpatialReference()
    src.ImportFromEPSG(4326)
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(utm)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    e, n, _z = osr.CoordinateTransformation(src, dst).TransformPoint(lon, lat)
    col = (e - gt[0]) / gt[1]
    row = (gt[3] - n) / (-gt[5])
    return col, row


def _sample_equirect(marble, lat, lon):
    rr = np.clip((90.0 - lat) / 180.0 * marble.shape[0], 0, marble.shape[0] - 1.001)
    cc = np.clip((lon + 180.0) / 360.0 * marble.shape[1], 0, marble.shape[1] - 1.001)
    r0 = np.floor(rr).astype(np.int32)
    c0 = np.floor(cc).astype(np.int32)
    fr = (rr - r0)[..., None]
    fc = (cc - c0)[..., None]
    a = marble[r0, c0].astype(np.float32)
    b = marble[r0, np.minimum(c0 + 1, marble.shape[1] - 1)].astype(np.float32)
    c = marble[np.minimum(r0 + 1, marble.shape[0] - 1), c0].astype(np.float32)
    d = marble[np.minimum(r0 + 1, marble.shape[0] - 1), np.minimum(c0 + 1, marble.shape[1] - 1)].astype(np.float32)
    return (a * (1 - fc) + b * fc) * (1 - fr) + (c * (1 - fc) + d * fc) * fr


def render_wide(marble, lon0, lat0, width_m) -> np.ndarray:
    ys, xs = np.mgrid[0:H, 0:W]
    scale = (width_m / 2) / 6378137.0
    if scale > 0.85:
        rx = (xs - (W - 1) / 2) / (W / 2) * scale
        ry = ((H - 1) / 2 - ys) / (W / 2) * scale
        rho2 = rx * rx + ry * ry
        vis = rho2 < 1.0
        rz = np.zeros_like(rx)
        rz[vis] = np.sqrt(1.0 - rho2[vis])
        clon, slon = math.cos(math.radians(lon0)), math.sin(math.radians(lon0))
        clat, slat = math.cos(math.radians(lat0)), math.sin(math.radians(lat0))
        px = (-slon) * rx + (-slat * clon) * ry + (clat * clon) * rz
        py = clon * rx + (-slat * slon) * ry + (clat * slon) * rz
        pz = clat * ry + slat * rz
        lat = np.degrees(np.arcsin(np.clip(pz, -1, 1)))
        lon = np.degrees(np.arctan2(py, px))
        rgb = np.zeros((H, W, 3), np.float32)
        rgb[:] = (6, 12, 22)
        rgb[vis] = _sample_equirect(marble, lat[vis], lon[vis])
        limb = np.clip((1.0 - rho2) * 8.0, 0, 1)
        rgb *= (0.35 + 0.65 * limb[..., None])
        rgb[~vis] = (6, 12, 22)
        return np.clip(rgb, 0, 255).astype(np.uint8)
    m_lon = 111320.0 * math.cos(math.radians(lat0))
    m_lat = 110540.0
    half = width_m / 2
    lon = lon0 + ((xs - (W - 1) / 2) / (W / 2)) * (half / m_lon)
    lat = lat0 + (((H - 1) / 2 - ys) / (W / 2)) * (half / m_lat)
    return np.clip(_sample_equirect(marble, lat, lon), 0, 255).astype(np.uint8)


def _camera(width_m, tilt_deg):
    tilt = math.radians(tilt_deg)
    focal = 980.0
    dist = (width_m / 2) * focal / (W / 2)
    eye = np.array([0.0, -dist * math.sin(tilt), dist * math.cos(tilt)])
    forward = -eye / np.linalg.norm(eye)
    world_up = np.array([0.0, 1.0, 0.0]) if tilt < 0.04 else np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return eye, right, up, forward, focal


def _projector(width_m, tilt_deg):
    eye, right, up, forward, focal = _camera(width_m, tilt_deg)

    def project(east, north, up_m):
        rel = np.array([east - eye[0], north - eye[1], up_m - eye[2]])
        vz = float(rel @ forward)
        if vz < 12.0:
            return None
        vx = float(rel @ right)
        vy = float(rel @ up)
        return (W / 2 + vx / vz * focal, H / 2 - vy / vz * focal)

    return project


def render_plate(tex, gt, utm, lat0, lon0, width_m, tilt_deg) -> np.ndarray:
    """Landsat on a flat plane, nadir or oblique. One source pixel stays one pixel at 30 m."""
    if tilt_deg < 1.2:
        col_c, row_c = _pix(lon0, lat0, gt, utm)
        gsd = width_m / W
        # Source is 30 m. Crop that many source pixels across the frame.
        crop_w = width_m / 30.0
        crop_h = crop_w * (H / W)
        x0 = int(round(col_c - crop_w / 2))
        y0 = int(round(row_c - crop_h / 2))
        x1 = int(round(col_c + crop_w / 2))
        y1 = int(round(row_c + crop_h / 2))
        pad = np.zeros((max(1, y1 - y0), max(1, x1 - x0), 3), np.uint8)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(tex.shape[1], x1), min(tex.shape[0], y1)
        if sx1 > sx0 and sy1 > sy0:
            pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = tex[sy0:sy1, sx0:sx1]
        view = np.array(Image.fromarray(pad).resize((W, H), Image.Resampling.BICUBIC))
        return view
    # Oblique mesh. Texture coordinates are Landsat pixels.
    xs = np.linspace(-width_m * 0.7, width_m * 0.7, 72)
    ys = np.linspace(-width_m * 0.85, width_m * 1.15, 84)
    east, north = np.meshgrid(xs, ys)
    lats = lat0 + np.degrees(north / 6378137.0)
    lons = lon0 + np.degrees(east / (6378137.0 * math.cos(math.radians(lat0))))
    cols, rows = _pix_grid(lons, lats, gt, utm)
    eye, right, up, forward, focal = _camera(width_m, tilt_deg)
    rel_x = east - eye[0]
    rel_y = north - eye[1]
    rel_z = 0.0 - eye[2]
    vx = rel_x * right[0] + rel_y * right[1] + rel_z * right[2]
    vy = rel_x * up[0] + rel_y * up[1] + rel_z * up[2]
    vz = rel_x * forward[0] + rel_y * forward[1] + rel_z * forward[2]
    inside = (cols >= 1) & (cols < tex.shape[1] - 1) & (rows >= 1) & (rows < tex.shape[0] - 1)
    good = (vz > 20) & inside
    sx = W / 2 + vx / np.maximum(vz, 1.0) * focal
    sy = H / 2 - vy / np.maximum(vz, 1.0) * focal
    ny, nx = sx.shape
    ii, jj = np.mgrid[0:ny - 1, 0:nx - 1]
    a = (ii * nx + jj).ravel()
    b = a + 1
    c = a + nx
    d = c + 1
    flat = good.ravel()
    keep = flat[a] & flat[b] & flat[c] & flat[d]
    tris = np.concatenate([np.stack([a, b, c], -1), np.stack([b, d, c], -1)])
    idx = tris[np.concatenate([keep, keep])].ravel()
    positions = [skia.Point(float(sx.ravel()[i]), float(sy.ravel()[i])) for i in range(sx.size)]
    texs = [skia.Point(float(cols.ravel()[i]), float(rows.ravel()[i])) for i in range(sx.size)]
    verts = skia.Vertices.MakeCopy(
        skia.Vertices.kTriangles_VertexMode, positions, texs, None, [int(v) for v in idx],
    )
    surface = skia.Surface(W, H)
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f(0.04, 0.08, 0.12, 1))
    paint = skia.Paint(AntiAlias=True)
    rgba = np.dstack([tex, np.full(tex.shape[:2], 255, np.uint8)])
    paint.setShader(skia.Image.fromarray(rgba).makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp))
    canvas.drawVertices(verts, paint)
    bgra = surface.makeImageSnapshot().toarray()
    return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])


def _pix(lon, lat, gt, utm):
    src = osr.SpatialReference()
    src.ImportFromEPSG(4326)
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(int(utm))
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    e, n, _z = osr.CoordinateTransformation(src, dst).TransformPoint(float(lon), float(lat))
    return (e - gt[0]) / gt[1], (gt[3] - n) / (-gt[5])


def _pix_grid(lons, lats, gt, utm):
    # Vectorized UTM zone from the epsg number: 326xx -> zone xx, northern.
    zone = int(utm) - 32600
    lon0 = (zone - 1) * 6 - 180 + 3
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    k0 = 0.9996
    lat = np.radians(lats)
    lon = np.radians(lons)
    N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    T = np.tan(lat) ** 2
    C = ep2 * np.cos(lat) ** 2
    A = (lon - math.radians(lon0)) * np.cos(lat)
    M = a * (
        (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
        - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * np.sin(2 * lat)
        + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * np.sin(4 * lat)
        - (35 * e2 ** 3 / 3072) * np.sin(6 * lat)
    )
    easting = k0 * N * (A + (1 - T + C) * A ** 3 / 6 + (5 - 18 * T + T ** 2 + 72 * C - 58 * ep2) * A ** 5 / 120) + 500000.0
    northing = k0 * (M + N * np.tan(lat) * (A ** 2 / 2 + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24))
    col = (easting - gt[0]) / gt[1]
    row = (gt[3] - northing) / (-gt[5])
    return col, row


def _label(img, text):
    surface = skia.Surface(W, H)
    canvas = surface.getCanvas()
    rgba = np.dstack([img, np.full(img.shape[:2], 255, np.uint8)])
    canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
    face = skia.Typeface.MakeFromFile(str(ROOT / "fonts" / "Montserrat-Black.ttf"))
    if face is None:
        face = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    font = skia.Font(face, 40)
    blob = skia.TextBlob.MakeFromString(text, font)
    bounds = blob.bounds()
    cx, cy = W / 2, 250
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(214, 14, 16, 20))
    canvas.drawRoundRect(skia.Rect.MakeXYWH(cx - bounds.width() / 2 - 26, cy - 38, bounds.width() + 52, 64), 16, 16, paint)
    fill = skia.Paint(AntiAlias=True)
    fill.setColor(skia.ColorSetARGB(255, 255, 236, 64))
    canvas.drawTextBlob(blob, cx - bounds.width() / 2, cy + 8, fill)
    bgra = surface.makeImageSnapshot().toarray()
    return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])


def render_shot(doc: dict, marble) -> None:
    spec = parse_spec(doc["spec"])
    shot = doc["shot"]
    tex, gt = load_landsat(Path(shot["imagery"]))
    lat0 = float(np.mean([p[0] for p in spec.polyline]))
    lon0 = float(np.mean([p[1] for p in spec.polyline]))
    dur = float(shot["duration"])
    n = int(round(dur * FPS))
    cues = build_cues(spec, float(shot["build_start"]), float(shot["build_dur"]))
    (HERE / (Path(shot["out"]).stem + "_cues.json")).write_text(json.dumps({"cues": cues}, indent=2) + "\n")
    dest = HERE / shot["out"]
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = None
    try:
        for i in range(n):
            t = i / FPS
            u = _smooth((t - 0.15) / (shot["zoom_end"] - 0.15))
            lon = shot["wide_lon"] + (lon0 - shot["wide_lon"]) * u
            lat = shot["wide_lat"] + (lat0 - shot["wide_lat"]) * u
            width = zoom_width(t, 0.15, shot["zoom_end"], shot["wide_m"], shot["close_m"])
            tilt = tilt_deg(t, shot["zoom_end"] - 0.35, shot["zoom_end"] + 0.35, shot["untilt"], shot["tilt"])
            base = render_wide(marble, lon, lat, width)
            fade = _smooth((shot["close_m"] * 2.2 - width) / (shot["close_m"] * 1.1))
            if fade > 0.02:
                plate = render_plate(tex, gt, shot["utm"], lat0, lon0, max(width, shot["close_m"]), tilt if fade > 0.85 else 0.0)
                frame = (base.astype(np.float32) * (1 - fade) + plate.astype(np.float32) * fade).astype(np.uint8)
            else:
                frame = base
            if fade > 0.7:
                surface = skia.Surface(W, H)
                canvas = surface.getCanvas()
                rgba = np.dstack([frame, np.full(frame.shape[:2], 255, np.uint8)])
                canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
                state = progress(spec, t, shot["build_start"], shot["build_dur"])
                draw(canvas, spec, state, _projector(max(width, shot["close_m"]), tilt if fade > 0.85 else 0.0), max(width, shot["close_m"]), W)
                bgra = surface.makeImageSnapshot().toarray()
                frame = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
            if spec.label and t > shot["build_start"] + shot["build_dur"] * 0.55:
                frame = _label(frame, spec.label)
            # Motion blur only while the zoom is still moving fast.
            if prev is not None and t < shot["zoom_end"] * 0.72:
                frame = ((frame.astype(np.uint16) + prev.astype(np.uint16)) // 2).astype(np.uint8)
            prev = frame
            proc.stdin.write(frame.tobytes())
            if i % 15 == 0:
                print(f"{shot['out']} {i}/{n} width {width:.0f} tilt {tilt:.1f}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    print("wrote", dest)


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    marble = np.load(MARBLE, mmap_mode="r")
    names = ["temburong", "peljesac"] if which == "both" else [which]
    for name in names:
        doc = json.loads((HERE / f"{name}.json").read_text())
        render_shot(doc, marble)


if __name__ == "__main__":
    main()
