"""Satellite, darkened satellite, parchment, and light vector textures.

The Earth cache is sampled once into equirectangular plates. Frames sample
the plate with the same camera the vector highlights use, then crossfade
when the projection changes. No stock photos.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.ndimage import distance_transform_edt, zoom

from jt.project import Resolved, ortho_radius, resolve

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


def build_plates(earth) -> dict[str, np.ndarray]:
    """Four uint8 equirectangular RGB plates."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    ids = earth.ids
    th, tw = ids.shape
    land = ids > 0
    shade = _shade(earth)
    lat = _lat_rows(th)[:, None]
    # Bathymetry proxy from a half-res distance field.
    small = land[::2, ::2]
    dist = distance_transform_edt(~small).astype(np.float32)
    if dist.shape != land.shape:
        dist = zoom(dist, (land.shape[0] / dist.shape[0], land.shape[1] / dist.shape[1]), order=1)
    shallow = np.exp(-dist / 14.0).astype(np.float32)

    grl = 0
    for i, row in enumerate(earth.meta):
        if row and row.get("iso") == "GRL":
            grl = i
            break
    ice = np.clip((lat - 60.0) / 16.0, 0.0, 1.0) * land
    if grl:
        ice = np.maximum(ice, (ids == grl).astype(np.float32) * 0.85)

    deep = np.array([8, 42, 58], np.float32)
    shelf = np.array([36, 104, 122], np.float32)
    ocean = deep * (1.0 - 0.72 * shallow[..., None]) + shelf * (0.72 * shallow[..., None])
    # A little latitude falloff so the poles read colder.
    ocean *= (0.78 + 0.22 * (1.0 - np.abs(lat) / 90.0))[..., None]

    olive = np.array([78, 86, 48], np.float32)
    tan = np.array([168, 142, 96], np.float32)
    land_rgb = olive * (0.55 + 0.45 * (1.0 - shade[..., None])) + tan * (shade[..., None] * 0.55)
    ice_rgb = np.array([232, 236, 238], np.float32)
    land_rgb = land_rgb * (1.0 - 0.82 * ice[..., None]) + ice_rgb * (0.82 * ice[..., None])

    sat = np.where(land[..., None], land_rgb, ocean)
    border = _borders(ids)
    sat[border] *= 0.42
    sat = np.clip(sat, 0, 255).astype(np.uint8)

    dark = sat.astype(np.float32) * 0.62 + np.array([8, 14, 28], np.float32) * 0.38
    dark = np.clip(dark, 0, 255).astype(np.uint8)

    # Parchment: tan land, slate water, the same hillshade, paper grain.
    rng = np.random.default_rng(7)
    grain = rng.normal(0, 4.5, sat.shape).astype(np.float32)
    paper_land = np.array([186, 164, 122], np.float32) * (0.72 + 0.28 * shade[..., None])
    paper_sea = np.array([92, 122, 132], np.float32) * (0.85 + 0.15 * shallow[..., None])
    parchment = np.where(land[..., None], paper_land, paper_sea) + grain
    parchment[border] *= 0.55
    parchment = np.clip(parchment, 0, 255).astype(np.uint8)

    light_land = np.array([214, 228, 216], np.float32)
    light_sea = np.array([214, 230, 236], np.float32)
    light = np.where(land[..., None], light_land * (0.92 + 0.08 * shade[..., None]), light_sea)
    light[border] = (150, 164, 158)
    light = np.clip(light, 0, 255).astype(np.uint8)

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
