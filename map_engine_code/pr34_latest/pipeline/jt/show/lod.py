"""Layered imagery. Globe, regional relief, then a local plate.

The crossfade sits in the middle of an ease-in-out zoom, where the move
is fastest, so the swap is hard to see. No blur is applied here.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from jt.show.basemap import ROOT, crossfade, paint_plate

# Wider than this is the globe. Narrower than LOCAL is the deep plate.
GLOBE_SPAN = 48.0
LOCAL_SPAN = 9.0

HYP_NPY = ROOT / "data" / "cache" / "hyp_50m_5400.npy"
LOCAL_JPG = ROOT / "data" / "cache" / "sentinel_local.jpg"
LOCAL_JSON = ROOT / "data" / "cache" / "sentinel_local.json"


def lod_swap(time_u: float) -> float:
    """Weight of the incoming plate. Near 0 at the start, near 1 at the end,
    and the steep part is around the middle of the zoom."""
    x = 0.0 if time_u < 0.40 else 1.0 if time_u > 0.60 else (time_u - 0.40) / 0.20
    return x * x * (3.0 - 2.0 * x)


def level_for(span: float) -> str:
    if span >= GLOBE_SPAN:
        return "globe"
    if span >= LOCAL_SPAN:
        return "regional"
    return "local"


def load_local() -> tuple[np.ndarray, tuple[float, float, float, float]] | None:
    """A deep-zoom plate plus west, south, east, north. None if it was not fetched."""
    pairs = (
        (LOCAL_JPG, LOCAL_JSON),
        (ROOT.parent / "assets" / "found" / "sentinel_local.jpg",
         ROOT.parent / "assets" / "found" / "sentinel_local.json"),
    )
    for jpg, meta_path in pairs:
        if jpg.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            img = np.asarray(Image.open(jpg).convert("RGB"))
            box = (float(meta["west"]), float(meta["south"]), float(meta["east"]), float(meta["north"]))
            return img, box
    return None


def load_regional() -> np.ndarray | None:
    if HYP_NPY.exists():
        return np.load(HYP_NPY)
    jpeg = ROOT.parent / "assets" / "found" / "HYP_50M_SR_W.jpg"
    if jpeg.exists():
        return np.asarray(Image.open(jpeg).convert("RGB"))
    return None


def _sample_bounded(plate: np.ndarray, bbox, lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    west, south, east, north = bbox
    th, tw = plate.shape[:2]
    inside = (lon >= west) & (lon <= east) & (lat >= south) & (lat <= north)
    col = (lon - west) / max(1e-6, east - west) * (tw - 1)
    row = (north - lat) / max(1e-6, north - south) * (th - 1)
    col = np.clip(col, 0, tw - 1)
    row = np.clip(row, 0, th - 1)
    c0 = np.floor(col).astype(np.int32)
    r0 = np.floor(row).astype(np.int32)
    c1 = np.clip(c0 + 1, 0, tw - 1)
    r1 = np.clip(r0 + 1, 0, th - 1)
    fc = (col - c0).astype(np.float32)[..., None]
    fr = (row - r0).astype(np.float32)[..., None]
    p00 = plate[r0, c0].astype(np.float32)
    p01 = plate[r0, c1].astype(np.float32)
    p10 = plate[r1, c0].astype(np.float32)
    p11 = plate[r1, c1].astype(np.float32)
    sampled = (p00 * (1 - fc) + p01 * fc) * (1 - fr) + (p10 * (1 - fc) + p11 * fc) * fr
    return np.clip(sampled, 0, 255).astype(np.uint8), inside


def paint_named(name: str, plates: dict, cam, w: int, h: int) -> np.ndarray:
    if name == "local" and plates.get("local") is not None:
        regional = paint_plate(plates["regional"], cam, w, h)
        img, bbox = plates["local"]
        # Reuse the mercator/ortho lon-lat from a full sample of the regional plate's grid
        # by painting the local image only where the view overlaps its box.
        from jt.show.basemap import view_for, _merc, _inv_merc
        view = view_for(cam, w, h)
        if cam.proj == "ortho":
            xs = np.arange(w, dtype=np.float64)[None, :]
            ys = np.arange(h, dtype=np.float64)[:, None]
            x = (xs - view.cx) / view.r
            y = -(ys - view.cy) / view.r
            rho2 = x * x + y * y
            inside_disk = rho2 <= 1.0
            z = np.sqrt(np.clip(1.0 - rho2, 0.0, 1.0))
            lat0 = np.radians(cam.lat)
            lon0 = np.radians(cam.lon)
            sin_lat = np.clip(z * np.sin(lat0) + y * np.cos(lat0), -1.0, 1.0)
            lat = np.degrees(np.arcsin(sin_lat))
            lon = np.degrees(lon0 + np.arctan2(x, z * np.cos(lat0) - y * np.sin(lat0)))
        else:
            xs = np.arange(w, dtype=np.float64)[None, :]
            ys = np.arange(h, dtype=np.float64)[:, None]
            scale = w / max(cam.span, 1.0)
            lon = cam.lon + (xs - view.cx) / scale
            merc = float(_merc(cam.lat)) - (ys - view.cy) / scale
            lat = _inv_merc(merc)
            inside_disk = np.ones((h, w), np.bool_)
        sampled, inside = _sample_bounded(img, bbox, lon, lat)
        use = inside & inside_disk
        out = regional.copy()
        out[use] = sampled[use]
        return out
    plate = plates["globe"] if name not in plates or plates[name] is None else plates[name]
    return paint_plate(plate, cam, w, h)


def paint_lod(cam, w: int, h: int, plates: dict, time_u: float = 1.0,
              span_a: float | None = None, span_b: float | None = None) -> np.ndarray:
    """One frame. If this zoom crosses a level, blend at mid-zoom."""
    sa = float(cam.span if span_a is None else span_a)
    sb = float(cam.span if span_b is None else span_b)
    start, end = level_for(sa), level_for(sb)
    if start == end:
        return paint_named(level_for(cam.span), plates, cam, w, h)
    mix = lod_swap(time_u)
    a = paint_named(start, plates, cam, w, h)
    b = paint_named(end, plates, cam, w, h)
    return crossfade(a, b, mix)
