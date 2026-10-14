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

from jt.show.flyto import fly_lonlat  # noqa: E402
from jt.show.labels import Hud, pill  # noqa: E402
from jt.show.moves import apply_vignette, apply_zoom_blur, drop_in, match_cut_dive  # noqa: E402
from jt.show.model_drop import (  # noqa: E402
    bridge_heading,
    build_cues,
    draw,
    hero_view_m,
    parse_spec,
    progress,
    zoom_width,
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


def _projector(width_m, tilt_deg, heading):
    """Project geographic east/north. The bridge chord lies along screen X."""
    eye, right, up, forward, focal = _camera(width_m, tilt_deg)
    c, s = math.cos(heading), math.sin(heading)

    def project(east, north, up_m):
        x = east * c + north * s
        y = -east * s + north * c
        rel = np.array([x - eye[0], y - eye[1], up_m - eye[2]])
        vz = float(rel @ forward)
        if vz < 8.0:
            return None
        vx = float(rel @ right)
        vy = float(rel @ up)
        return (W / 2 + vx / vz * focal, H / 2 - vy / vz * focal)

    return project


def _regional(name: str, south: float, west: float, north: float, east: float) -> tuple[np.ndarray, tuple]:
    """NASA Blue Marble via GIBS. Public domain. Cached under the asset library."""
    path = Path("/workspace/asset_library/extra") / f"gibs_{name}.jpg"
    if not path.exists():
        url = (
            "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
            "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=BlueMarble_NextGeneration"
            "&FORMAT=image/jpeg&CRS=EPSG:4326"
            f"&BBOX={south},{west},{north},{east}&WIDTH=1600&HEIGHT=1600"
        )
        subprocess.run(["curl", "-fsSL", "-o", str(path), url], check=True)
    img = np.asarray(Image.open(path).convert("RGB"))
    return img, (south, west, north, east)


def _smooth_w(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _feather(lon, lat, bounds, margin=0.18):
    south, west, north, east = bounds
    nx = (lon - west) / max(1e-6, east - west)
    ny = (lat - south) / max(1e-6, north - south)
    inside = (nx > 0) & (nx < 1) & (ny > 0) & (ny < 1)
    edge = np.minimum(np.minimum(nx, 1 - nx), np.minimum(ny, 1 - ny))
    return inside.astype(np.float32) * _smooth_w(edge / margin)


def _sample_bbox(img, bounds, lat, lon):
    south, west, north, east = bounds
    row = (north - lat) / max(1e-6, north - south) * (img.shape[0] - 1)
    col = (lon - west) / max(1e-6, east - west) * (img.shape[1] - 1)
    row = np.clip(row, 0, img.shape[0] - 1.001)
    col = np.clip(col, 0, img.shape[1] - 1.001)
    r0 = np.floor(row).astype(np.int32)
    c0 = np.floor(col).astype(np.int32)
    fr = (row - r0)[..., None]
    fc = (col - c0)[..., None]
    a = img[r0, c0].astype(np.float32)
    b = img[r0, np.minimum(c0 + 1, img.shape[1] - 1)].astype(np.float32)
    c = img[np.minimum(r0 + 1, img.shape[0] - 1), c0].astype(np.float32)
    d = img[np.minimum(r0 + 1, img.shape[0] - 1), np.minimum(c0 + 1, img.shape[1] - 1)].astype(np.float32)
    return (a * (1 - fc) + b * fc) * (1 - fr) + (c * (1 - fc) + d * fc) * fr


def _hits(width_m, tilt_deg, heading):
    """Intersect each pixel's ray with the ground. Returns aligned x, y and a hit mask."""
    focal = 980.0
    tilt = math.radians(tilt_deg)
    dist = (width_m / 2) * focal / (W / 2)
    eye = np.array([0.0, -dist * math.sin(tilt), dist * math.cos(tilt)])
    forward = -eye / np.linalg.norm(eye)
    world_up = np.array([0.0, 1.0, 0.0]) if tilt < 0.04 else np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right = right / np.linalg.norm(right)
    up = np.cross(right, forward)
    ys, xs = np.mgrid[0:H, 0:W]
    cx = (xs - (W - 1) / 2) / focal
    cy = ((H - 1) / 2 - ys) / focal
    direction = cx[..., None] * right + cy[..., None] * up + forward
    dz = direction[..., 2]
    hit = dz < -1e-4
    t = np.zeros_like(dz)
    t[hit] = -eye[2] / dz[hit]
    hit &= t > 0
    point = eye + t[..., None] * direction
    # Rays that hit far past the plate are the black cap above an oblique view.
    far = np.hypot(point[..., 0], point[..., 1]) > width_m * 5.5
    hit = hit & ~far
    return point[..., 0], point[..., 1], hit, heading


def _to_lonlat(x, y, heading, lat0, lon0):
    c, s = math.cos(heading), math.sin(heading)
    east = x * c - y * s
    north = x * s + y * c
    lat = lat0 + np.degrees(north / 6378137.0)
    lon = lon0 + np.degrees(east / (6378137.0 * math.cos(math.radians(lat0))))
    return lat, lon


def _width_ok(bounds, lat, width_m) -> bool:
    """The frame is narrower than the plate, so the plate is not a rectangle sitting in the corner."""
    _south, west, _north, east = bounds
    bw = (east - west) * 111320.0 * math.cos(math.radians(lat))
    return width_m < 0.82 * bw


def render_ground(marble, regional, landsat, land_bounds, lat0, lon0, width_m, tilt_deg, heading) -> np.ndarray:
    """Full-frame plate. A finer level is used only when it covers the frame, so no plate edge shows."""
    x, y, hit, _h = _hits(width_m, tilt_deg, heading)
    lat, lon = _to_lonlat(x, y, heading, lat0, lon0)
    gsd = width_m / W
    color = _sample_equirect(marble, np.where(hit, lat, lat0), np.where(hit, lon, lon0))
    if regional is not None and _width_ok(regional[1], lat0, width_m):
        reg, bounds = regional
        wr = float(_smooth((14_000 - gsd) / (14_000 - 600))) * _feather(lon, lat, bounds, 0.2)
        sampled = _sample_bbox(reg, bounds, np.clip(lat, bounds[0], bounds[2]), np.clip(lon, bounds[1], bounds[3]))
        color = color * (1 - wr[..., None]) + sampled * wr[..., None]
    if landsat is not None and gsd < 500 and _width_ok(land_bounds, lat0, width_m):
        wl = float(_smooth((280 - gsd) / (280 - 40))) * _feather(lon, lat, land_bounds, 0.28)
        src = landsat["soft"] if gsd < 24 else landsat["sharp"]
        sampled = _sample_bbox(src, land_bounds, np.clip(lat, land_bounds[0], land_bounds[2]), np.clip(lon, land_bounds[1], land_bounds[3]))
        # Closer than the 30 m sample, flatten toward map colors so the upscale is not a pixel grid.
        if gsd < 16:
            lum = sampled.mean(axis=-1)
            flat = np.where(lum[..., None] < 78, np.array([12.0, 40.0, 82.0]), np.array([92.0, 122.0, 74.0]))
            mix = float(_smooth((16 - gsd) / 12)) * 0.72
            sampled = sampled * (1 - mix) + flat * mix
        color = color * (1 - wl[..., None]) + sampled * wl[..., None]
    rgb = np.clip(color, 0, 255).astype(np.uint8)
    if np.any(~hit):
        first = np.argmax(hit, axis=0)
        for col in range(W):
            row = int(first[col])
            if row <= 0 or not hit[row, col]:
                continue
            rgb[:row, col] = rgb[row, col]
    # A dark cap above the oblique horizon is stretched from the picture under it.
    row_max = rgb.max(axis=(1, 2))
    content = row_max > 36
    if content.any():
        first = int(np.argmax(content))
        if first > 2:
            band = rgb[first:min(H, first + 180)]
            stretched = np.asarray(Image.fromarray(band).resize((W, first + 30), Image.Resampling.BILINEAR))
            rgb[:first] = stretched[:first]
            seam = min(24, H - first)
            if seam > 4:
                fade = np.linspace(1, 0, seam, dtype=np.float32)[:, None, None]
                rgb[first:first + seam] = (
                    rgb[first:first + seam] * (1 - fade) + stretched[first:first + seam] * fade
                ).astype(np.uint8)
    return rgb



def _land_bounds(gt, shape, utm):
    src = osr.SpatialReference(); src.ImportFromEPSG(int(utm))
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst = osr.SpatialReference(); dst.ImportFromEPSG(4326)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    back = osr.CoordinateTransformation(src, dst)
    h, w = shape[:2]
    lats, lons = [], []
    for c, r in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        e = gt[0] + c * gt[1]
        n = gt[3] + r * gt[5]
        lon, lat, _z = back.TransformPoint(e, n)
        lats.append(lat); lons.append(lon)
    return (min(lats), min(lons), max(lats), max(lons))


def _label(canvas, text, pop):
    hud = Hud(canvas, W, H)
    pill(hud, text, W * 0.5, 280, (255, 214, 48), ink=(16, 16, 20), size=46, pop=pop, kind="bridge", nudge=False)


def render_shot(doc: dict, marble) -> None:
    from scipy.ndimage import gaussian_filter
    spec = parse_spec(doc["spec"])
    shot = doc["shot"]
    tex, gt = load_landsat(Path(shot["imagery"]))
    soft = np.clip(gaussian_filter(tex.astype(np.float32), sigma=(2.4, 2.4, 0)), 0, 255).astype(np.uint8)
    landsat = {"sharp": tex, "soft": soft}
    land_bounds = _land_bounds(gt, tex.shape, shot["utm"])
    if "brunei" in shot["imagery"] or "temburong" in shot["imagery"]:
        regional = _regional("brunei", 1.2, 112.2, 7.6, 117.6)
    else:
        regional = _regional("adriatic", 40.2, 14.8, 45.2, 20.2)
    lat0 = float(np.mean([p[0] for p in spec.polyline]))
    lon0 = float(np.mean([p[1] for p in spec.polyline]))
    heading0 = bridge_heading(spec)
    close_m = hero_view_m(spec, 0.60)
    dur = float(shot["duration"])
    n = int(round(dur * FPS))
    cues = build_cues(spec, float(shot["build_start"]), float(shot["build_dur"]))
    cues.append({"t": 2.55, "kind": "whoosh", "name": "match-cut-dive"})
    cues.sort(key=lambda row: (row["t"], row["name"]))
    (HERE / (Path(shot["out"]).stem + "_cues.json")).write_text(json.dumps({"cues": cues, "close_m": close_m}, indent=2) + "\n")
    dest = HERE / shot["out"]
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev_raw = None
    try:
        for i in range(n):
            t = i / FPS
            # 0.1–1.9 ease-out drop to the regional plate. 1.9–2.55 accelerating dive to the bridge.
            # Width and center follow d3 interpolateZoom (MapLibre / deck.gl flyTo). Timing is ease-out, then ease-in.
            intro = drop_in(t, 0.10, 1.90)
            dive = match_cut_dive(t, 1.90, 2.55)
            mid_m = close_m * 4.5
            if t < 1.90:
                blur = intro["blur"]
                radial = False
                lon, lat, width = fly_lonlat(
                    intro["u"], shot["wide_lon"], shot["wide_lat"], shot["wide_m"], lon0, lat0, mid_m,
                )
            elif t <= 2.55:
                blur = dive["blur"]
                radial = True
                lon, lat, width = fly_lonlat(dive["u"], lon0, lat0, mid_m, lon0, lat0, close_m)
            else:
                blur = 0.0
                radial = False
                lon, lat, width = lon0, lat0, close_m
            tilt = shot["tilt"] * _smooth((t - 2.45) / 0.55)
            hold = t - float(shot["untilt"])
            heading = heading0
            if hold > 0:
                heading += math.sin(hold * 1.3) * math.radians(1.7)
                width *= 1.0 + 0.014 * math.sin(hold * 1.15)
                tilt = shot["tilt"] + 1.4 * math.sin(hold * 0.85)
            near = width < close_m * 3
            frame = render_ground(
                marble, regional, landsat, land_bounds,
                lat0 if near else lat, lon0 if near else lon, width, tilt, heading,
            )
            surface = skia.Surface(W, H)
            canvas = surface.getCanvas()
            rgba = np.dstack([frame, np.full(frame.shape[:2], 255, np.uint8)])
            canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
            if t >= shot["build_start"] - 0.05:
                state = progress(spec, t, shot["build_start"], shot["build_dur"])
                draw(canvas, spec, state, _projector(width, tilt, heading), width, W, tilt=tilt)
            if spec.label and t > shot["build_start"] + shot["build_dur"] * 0.45:
                pulse = 1.0 + (0.045 * math.sin(t * 4.2) if hold > 0 else 0.0)
                _label(canvas, spec.label, pulse)
            bgra = surface.makeImageSnapshot().toarray()
            raw = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
            raw = apply_vignette(raw, 0.38)
            # Blur only while a move is fast. The settled plate and the span build stay sharp.
            out = apply_zoom_blur(raw, blur, radial=radial) if blur >= 0.05 else raw
            prev_raw = raw
            proc.stdin.write(out.tobytes())
            if i % 15 == 0:
                print(f"{shot['out']} {i}/{n} width {width:.0f} tilt {tilt:.1f}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    print("wrote", dest, "close_m", round(close_m))



def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    marble = np.load(MARBLE, mmap_mode="r")
    names = ["temburong", "peljesac"] if which == "both" else [which]
    for name in names:
        doc = json.loads((HERE / f"{name}.json").read_text())
        render_shot(doc, marble)


if __name__ == "__main__":
    main()
