"""Public-domain Natural Earth land, baked into Earth and leather albedos.

Natural Earth 110m land is public domain (naturalearthdata.com). The raster
is built locally from the vendored shapefile so the short does not need a
network at render time.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import shapefile

ASSETS = Path(__file__).resolve().parent / "assets"
SHP = ASSETS / "ne110m" / "ne_110m_land.shp"
TW, TH = 2048, 1024


def _split_dateline(pts: list[tuple[float, float]]) -> list[list[tuple[float, float]]]:
    if len(pts) < 3:
        return []
    chunks: list[list[tuple[float, float]]] = [[pts[0]]]
    for p0, p1 in zip(pts, pts[1:]):
        if abs(p1[0] - p0[0]) > 180:
            chunks.append([p1])
        else:
            chunks[-1].append(p1)
    return [c for c in chunks if len(c) >= 3]


def land_mask() -> np.ndarray:
    """uint8 mask, 255 = land. Equirectangular, lon -180..180, lat 90..-90."""
    reader = shapefile.Reader(str(SHP))
    img = Image.new("L", (TW, TH), 0)
    draw = ImageDraw.Draw(img)
    for shp in reader.shapes():
        pts = shp.points
        parts = list(shp.parts) + [len(pts)]
        for a, b in zip(parts, parts[1:]):
            ring = [(float(x), float(y)) for x, y in pts[a:b]]
            for chunk in _split_dateline(ring):
                poly = [((lon + 180.0) / 360.0 * TW, (90.0 - lat) / 180.0 * TH) for lon, lat in chunk]
                draw.polygon(poly, fill=255)
    mask = np.asarray(img, np.uint8)
    # Close tiny coastal gaps so Africa's outline stays solid at phone size.
    im = Image.fromarray(mask, "L").filter(ImageFilter.MaxFilter(3))
    im = im.filter(ImageFilter.MinFilter(3))
    return np.asarray(im, np.uint8)


def _smooth_noise(rng: np.random.Generator, h: int, w: int, octaves: int = 4) -> np.ndarray:
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    total = 0.0
    for o in range(octaves):
        gh, gw = max(2, h // (2 ** (4 - o))), max(2, w // (2 ** (4 - o)))
        g = rng.random((gh, gw), dtype=np.float32)
        up = np.asarray(Image.fromarray(g, "F").resize((w, h), Image.Resampling.BICUBIC), np.float32)
        out += up * amp
        total += amp
        amp *= 0.5
    return out / total


def build_textures() -> dict:
    rng = np.random.default_rng(15)
    land = land_mask().astype(np.float32) / 255.0
    # Soft coast for shallows.
    coast = np.asarray(
        Image.fromarray((land * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(2)),
        np.float32,
    ) / 255.0
    # Flat fills. Noise here turns into shaded-relief / cell artifacts at
    # phone size, so latitude does the only shading and the coast is a line.
    yy = np.linspace(1, 0, TH, dtype=np.float32)[:, None]
    lat = np.linspace(90, -90, TH, dtype=np.float32)[:, None]
    ocean = np.empty((TH, TW, 3), np.float32)
    deep = np.array([10, 48, 112], np.float32)
    mid = np.array([18, 96, 168], np.float32)
    gradient = (deep * (1 - yy) + mid * yy)[:, None, :]
    ocean[:] = gradient
    shall = np.clip((coast - land) * 4.0, 0, 1)[..., None]
    ocean = ocean * (1 - 0.65 * shall) + np.array([64, 168, 186], np.float32) * (0.65 * shall)
    ice = np.clip((np.abs(lat) - 72.0) / 8.0, 0, 1)[..., None]
    ocean = ocean * (1 - ice) + np.array([214, 228, 234], np.float32) * ice

    land_col = np.empty((TH, TW, 3), np.float32)
    land_col[:] = np.array([176, 148, 98], np.float32)
    trop = np.clip(1 - np.abs(lat) / 28.0, 0, 1)[..., None]
    land_col = land_col * (1 - 0.45 * trop) + np.array([86, 128, 70], np.float32) * (0.45 * trop)
    snow = np.clip((np.abs(lat) - 64.0) / 10.0, 0, 1)[..., None]
    land_col = land_col * (1 - snow) + np.array([230, 234, 236], np.float32) * snow
    # One-pixel coast so the spin reads without a relief map.
    eroded = np.asarray(
        Image.fromarray((land * 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(5)),
        np.float32,
    ) / 255.0
    coast_line = np.clip(land - eroded, 0, 1)[..., None]
    land_col = land_col * (1 - 0.55 * coast_line) + np.array([48, 40, 32], np.float32) * (0.55 * coast_line)

    earth = ocean * (1 - land)[..., None] + land_col * land[..., None]
    earth = np.clip(earth, 0, 255)

    # Smooth leather. Continents are a flat gold stamp, not a noisy heightfield.
    leather = np.broadcast_to(np.array([124, 68, 32], np.float32), (TH, TW, 3)).copy()
    gold = np.array([214, 168, 72], np.float32)
    leather_rgb = leather * (1 - land)[..., None] + gold * land[..., None]
    leather_rgb = leather_rgb * (1 - 0.45 * coast_line) + np.array([64, 36, 18], np.float32) * (0.45 * coast_line)
    leather_rgb = np.clip(leather_rgb, 0, 255)
    pebble = np.zeros((TH, TW), np.float32)

    return {
        "earth": earth.astype(np.float32),
        "leather": leather_rgb.astype(np.float32),
        "land": land.astype(np.float32),
        "pebble": pebble.astype(np.float32),
    }


_CACHE: dict | None = None


def textures() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = build_textures()
    return _CACHE
