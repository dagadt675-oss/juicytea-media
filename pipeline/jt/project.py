"""Orthographic, Mercator and Lambert azimuthal equal-area.

Screen y grows downward. Forward projections return pixel coordinates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def ang_delta(a: float, b: float) -> float:
    return (b - a + 180.0) % 360.0 - 180.0


def ang_lerp(a: float, b: float, u: float) -> float:
    return a + ang_delta(a, b) * u


def ease_in_out(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def ease_out(u: float) -> float:
    """Speed is highest at the start, so frame 0 is already moving."""
    u = max(0.0, min(1.0, u))
    return 1.0 - (1.0 - u) * (1.0 - u)


@dataclass
class Resolved:
    proj: str
    lon: float
    lat: float
    span: float
    cx: float
    cy: float
    r: float
    rect: tuple[int, int, int, int] | None
    whip_dark: float = 0.0


def ortho_radius(span: float, width: int) -> float:
    span = max(4.0, min(float(span), 150.0))
    return (width * 0.46) / math.sin(math.radians(span / 2.0))


def resolve(proj: str, lon: float, lat: float, span: float, w: int, h: int,
            whip_dark: float = 0.0) -> Resolved:
    if proj == "ortho":
        r = ortho_radius(span, w)
        return Resolved(proj, lon, lat, span, 0.47 * w, 0.46 * h, r, None, whip_dark)
    x0, x1 = int(0.04 * w), int(0.96 * w)
    y0, y1 = int(0.305 * h), int(0.615 * h)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return Resolved(proj, lon, lat, span, cx, cy, 0.0, (x0, y0, x1, y1), whip_dark)


def _cosc(lon, lat, lon0, lat0):
    lon, lat, lon0, lat0 = map(np.radians, (lon, lat, lon0, lat0))
    return (np.sin(lat0) * np.sin(lat)
            + np.cos(lat0) * np.cos(lat) * np.cos(lon - lon0))


def project_points(lon, lat, view: Resolved):
    """Forward-project arrays. Returns x, y, visible (bool)."""
    lon = np.asarray(lon, np.float64)
    lat = np.asarray(lat, np.float64)
    if view.proj == "ortho":
        lonr, latr = np.radians(lon), np.radians(lat)
        lon0, lat0 = np.radians(view.lon), np.radians(view.lat)
        dlon = lonr - lon0
        cosc = (np.sin(lat0) * np.sin(latr)
                + np.cos(lat0) * np.cos(latr) * np.cos(dlon))
        vis = cosc > 0.05
        x = view.cx + view.r * np.cos(latr) * np.sin(dlon)
        y = view.cy - view.r * (
            np.cos(lat0) * np.sin(latr)
            - np.sin(lat0) * np.cos(latr) * np.cos(dlon))
        return x, y, vis
    if view.proj == "merc":
        x0, y0, x1, y1 = view.rect
        scale = (x1 - x0) / max(view.span, 1.0)
        lat_c = np.clip(lat, -80, 80)
        lat0 = float(np.clip(view.lat, -80, 80))
        merc = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat_c) / 2)))
        merc0 = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat0) / 2)))
        x = view.cx + (lon - view.lon) * scale
        y = view.cy - (merc - merc0) * scale
        vis = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
        return x, y, vis
    # LAEA, x/y in radians about the view centre, same scale as the sampler.
    x0, y0, x1, y1 = view.rect
    pr = (x1 - x0) / math.radians(max(view.span, 1.0))
    xr, yr = laea_forward(lon, lat, view.lon, view.lat)
    x = view.cx + xr * pr
    y = view.cy - yr * pr
    vis = np.isfinite(x) & np.isfinite(y) & (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    return x, y, vis


def project_one(lon: float, lat: float, view: Resolved):
    x, y, vis = project_points([lon], [lat], view)
    if not bool(vis[0]):
        return None
    return float(x[0]), float(y[0])


def laea_forward(lon, lat, lon0, lat0):
    lam = np.radians(np.asarray(lon, np.float64) - lon0)
    phi = np.radians(np.asarray(lat, np.float64))
    phi0 = math.radians(lat0)
    denom = 1.0 + math.sin(phi0) * np.sin(phi) + math.cos(phi0) * np.cos(phi) * np.cos(lam)
    denom = np.maximum(denom, 1e-6)
    k = np.sqrt(2.0 / denom)
    x = k * np.cos(phi) * np.sin(lam)
    y = k * (math.cos(phi0) * np.sin(phi) - math.sin(phi0) * np.cos(phi) * np.cos(lam))
    return x, y


def laea_inverse(x, y, lon0, lat0):
    phi0 = math.radians(lat0)
    rho = np.hypot(x, y)
    c = 2.0 * np.arcsin(np.clip(rho / 2.0, 0.0, 1.0))
    sin_c, cos_c = np.sin(c), np.cos(c)
    near = rho < 1e-8
    rho_safe = np.where(near, 1.0, rho)
    phi = np.arcsin(np.clip(
        cos_c * math.sin(phi0) + y * sin_c * math.cos(phi0) / rho_safe, -1, 1))
    lam = np.arctan2(
        x * sin_c,
        rho * math.cos(phi0) * cos_c - y * math.sin(phi0) * sin_c)
    phi = np.where(near, phi0, phi)
    lam = np.where(near, 0.0, lam)
    return lon0 + np.degrees(lam), np.degrees(phi)


def lerp_camera(a, b, u: float):
    from jt.spec import Camera
    e = ease_in_out(u)
    span = a.span + (b.span - a.span) * e
    span *= 1.0 + 0.06 * math.sin(e * math.pi)
    return Camera(
        a.proj,
        ang_lerp(a.lon, b.lon, e),
        a.lat + (b.lat - a.lat) * e,
        span,
    )
