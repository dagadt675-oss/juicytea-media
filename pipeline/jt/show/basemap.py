"""Natural Earth II shaded relief, plus the camera sampler.

The basemap is the public-domain Natural Earth II raster (natural greens,
tans, blue ocean, shaded relief). Country fills are drawn on top of it.
Frames sample the plate with the same camera the vectors use.
"""

from __future__ import annotations

import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from jt.project import Resolved, ortho_radius, resolve

ROOT = Path(__file__).resolve().parents[2]
NE2_ZIP = ROOT / "data" / "NE2_50M_SR_W.zip"
NE2_CACHE = ROOT / "data" / "cache" / "ne2_50m_u8.npy"

_CACHE: dict[str, np.ndarray] | None = None


def _lat_rows(n: int) -> np.ndarray:
    # Row 0 is the north edge, matching the Earth raster.
    return 90.0 - (np.arange(n) + 0.5) * (180.0 / n)


def _borders(ids: np.ndarray) -> np.ndarray:
    b = np.zeros(ids.shape, np.bool_)
    b[:, 1:] |= ids[:, 1:] != ids[:, :-1]
    b[1:, :] |= ids[1:, :] != ids[:-1, :]
    return b


def _shade(earth) -> np.ndarray:
    return np.clip(earth.shade.astype(np.float32) / 220.0, 0.25, 1.15)


def _load_ne2() -> np.ndarray:
    """Natural Earth II, 10800×5400, row 0 at the north. Cached after the first read."""
    if NE2_CACHE.exists():
        return np.load(NE2_CACHE)
    tif = None
    for candidate in (
        Path("/tmp/ne2/NE2_50M_SR_W/NE2_50M_SR_W.tif"),
        ROOT / "data" / "NE2_50M_SR_W.tif",
    ):
        if candidate.exists():
            tif = candidate
            break
    if tif is None and NE2_ZIP.exists():
        dest = Path("/tmp/ne2")
        with zipfile.ZipFile(NE2_ZIP) as zf:
            zf.extract("NE2_50M_SR_W/NE2_50M_SR_W.tif", dest)
        tif = dest / "NE2_50M_SR_W" / "NE2_50M_SR_W.tif"
    if tif is None:
        raise FileNotFoundError("Natural Earth II raster is missing")
    arr = np.asarray(Image.open(tif).convert("RGB"))
    NE2_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(NE2_CACHE, arr)
    return arr


def build_plates(earth) -> dict[str, np.ndarray]:
    """Natural-color relief, plus a parchment grade kept for other episodes."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    sat = _load_ne2()
    # A hair of darkening so a bright fill still reads. The hues stay natural.
    dark = np.clip(sat.astype(np.float32) * 0.96, 0, 255).astype(np.uint8)
    ids = earth.ids
    th, tw = ids.shape
    land = ids > 0
    shade = _shade(earth)
    if shade.shape != (th, tw):
        shade = np.ones((th, tw), np.float32)
    paper_land = np.array([186, 164, 122], np.float32) * (0.72 + 0.28 * shade[..., None])
    paper_sea = np.array([92, 122, 132], np.float32)
    # Parchment is built at the admin-raster size. The sampler only needs it
    # when an episode asks for that grade.
    parchment = np.where(land[..., None], paper_land, paper_sea)
    parchment = np.clip(parchment, 0, 255).astype(np.uint8)

    light = np.clip(np.where(
        land[..., None],
        np.array([214, 228, 216], np.float32),
        np.array([214, 230, 236], np.float32),
    ), 0, 255).astype(np.uint8)
    _CACHE = {"satellite": sat, "satellite_dark": dark, "parchment": parchment, "light": light}
    return _CACHE


def view_for(cam, w: int, h: int) -> Resolved:
    return resolve(cam.proj, cam.lon, cam.lat, max(4.0, cam.span), w, h)


def _merc(lat):
    lat = np.clip(lat, -85.0, 85.0)
    return np.degrees(np.log(np.tan(np.pi / 4.0 + np.radians(lat) / 2.0)))


def _inv_merc(y):
    return np.degrees(2.0 * np.arctan(np.exp(np.radians(y))) - np.pi / 2.0)


def _sample(plate: np.ndarray, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    th, tw = plate.shape[:2]
    col = np.mod(lon + 180.0, 360.0) / 360.0 * (tw - 1)
    row = (90.0 - lat) / 180.0 * (th - 1)
    row = np.clip(row, 0, th - 1)
    # Bilinear in pixel space. Longitude wraps.
    c0 = np.floor(col).astype(np.int32)
    r0 = np.floor(row).astype(np.int32)
    c1 = (c0 + 1) % tw
    r1 = np.clip(r0 + 1, 0, th - 1)
    fc = (col - c0).astype(np.float32)[..., None]
    fr = (row - r0).astype(np.float32)[..., None]
    p00 = plate[r0, c0].astype(np.float32)
    p01 = plate[r0, c1].astype(np.float32)
    p10 = plate[r1, c0].astype(np.float32)
    p11 = plate[r1, c1].astype(np.float32)
    return (p00 * (1 - fc) + p01 * fc) * (1 - fr) + (p10 * (1 - fc) + p11 * fc) * fr


@lru_cache(maxsize=1)
def _stars(h: int, w: int) -> np.ndarray:
    rng = np.random.default_rng(3)
    img = np.zeros((h, w, 3), np.float32)
    # Space, lighter toward the lower limb so the globe sits in a sky.
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img[:] = (np.array([5, 8, 16], np.float32) * (1 - y) + np.array([14, 22, 36], np.float32) * y)
    n = 180
    ys = rng.integers(0, h, n)
    xs = rng.integers(0, w, n)
    mag = rng.uniform(0.35, 1.0, n)
    for x, yy, m in zip(xs, ys, mag):
        val = 180 * m
        img[yy, x] = val
        if m > 0.8 and 1 <= yy < h - 1 and 1 <= x < w - 1:
            img[yy, x - 1:x + 2] = np.maximum(img[yy, x - 1:x + 2], val * 0.45)
    return img


def paint_plate(plate: np.ndarray, cam, w: int, h: int) -> np.ndarray:
    """RGB uint8 frame of one plate through one camera."""
    view = view_for(cam, w, h)
    if cam.proj == "ortho":
        bg = _stars(h, w).copy()
        xs = np.arange(w, dtype=np.float64)[None, :]
        ys = np.arange(h, dtype=np.float64)[:, None]
        x = (xs - view.cx) / view.r
        y = -(ys - view.cy) / view.r
        rho2 = x * x + y * y
        inside = rho2 <= 1.0
        z = np.sqrt(np.clip(1.0 - rho2, 0.0, 1.0))
        lat0 = np.radians(cam.lat)
        lon0 = np.radians(cam.lon)
        sin_lat = np.clip(z * np.sin(lat0) + y * np.cos(lat0), -1.0, 1.0)
        lat = np.degrees(np.arcsin(sin_lat))
        lon = np.degrees(lon0 + np.arctan2(x, z * np.cos(lat0) - y * np.sin(lat0)))
        sampled = _sample(plate, lon, lat)
        bg[inside] = sampled[inside]
        # Limb shade: darken the last few pixels of the disk.
        edge = inside & (rho2 > 0.90)
        bg[edge] *= 0.78
        return np.clip(bg, 0, 255).astype(np.uint8)

    xs = np.arange(w, dtype=np.float64)[None, :]
    ys = np.arange(h, dtype=np.float64)[:, None]
    scale = w / max(cam.span, 1.0)
    lon = cam.lon + (xs - view.cx) / scale
    merc0 = float(_merc(cam.lat))
    merc = merc0 - (ys - view.cy) / scale
    lat = _inv_merc(merc)
    sampled = _sample(plate, lon, lat)
    return np.clip(sampled, 0, 255).astype(np.uint8)


def crossfade(a: np.ndarray, b: np.ndarray, u: float) -> np.ndarray:
    if u <= 0.0:
        return a
    if u >= 1.0:
        return b
    return np.clip(a.astype(np.float32) * (1.0 - u) + b.astype(np.float32) * u, 0, 255).astype(np.uint8)
