"""Mercator scale, and the vertex shift that undoes it.

Mercator is conformal. Local scale is sec(latitude) in every direction,
so area is exaggerated by sec(latitude) squared. Sliding every vertex of a
polygon by the same latitude delta is the true-size reprojection: each
vertex then sits at a new latitude and the map scale at that vertex changes
on its own. No uniform screen-space shrink.
"""

from __future__ import annotations

import math

import numpy as np

# sec(70°)^2 is about 8.5. The on-screen claim rounds that to ~3x wide, ~9x area.
# sec(75.96°)^2 is 16, the Greenland claim.
REF_LAT_70 = 70.0
GREENLAND_HOME_LAT = 74.319387
GREENLAND_HOME_LON = -39.335251


def sec_lat(lat_deg: float) -> float:
    lat = max(-89.0, min(89.0, float(lat_deg)))
    return 1.0 / math.cos(math.radians(lat))


def area_factor(lat_deg: float) -> float:
    s = sec_lat(lat_deg)
    return s * s


def linear_factor(lat_deg: float) -> float:
    return sec_lat(lat_deg)


def display_multiplier(lat_deg: float, home_lat: float = GREENLAND_HOME_LAT, home_label: float = 16.0) -> float:
    """Map the live sec^2 onto the spoken scale. Home latitude reads `home_label`, the equator reads 1."""
    a = area_factor(lat_deg)
    a0 = area_factor(home_lat)
    if a0 <= 1.001:
        return 1.0
    x = 1.0 + (home_label - 1.0) * (a - 1.0) / (a0 - 1.0)
    return max(1.0, x)


def reproject_true(ring: np.ndarray, lon0: float, lat0: float, lon1: float, lat1: float) -> np.ndarray:
    """Move a ring onto a new centroid, undoing Mercator's east-west stretch.

    Longitude offsets are stored as true easting (degrees times cos(latitude)).
    At the destination they are written back as longitude using sec(lat1), which
    is exactly the exaggeration Mercator will then apply. At the home latitude
    the ring is unchanged. At the equator it has its true width.
    """
    lon = np.asarray(ring[:, 0], np.float64)
    lat = np.clip(np.asarray(ring[:, 1], np.float64), -89.0, 89.0)
    dx = (lon - lon0) * np.cos(np.radians(lat))
    dy = lat - lat0
    sec = 1.0 / max(0.08, math.cos(math.radians(float(lat1))))
    out = np.empty((len(ring), 2), np.float64)
    out[:, 0] = lon1 + dx * sec
    out[:, 1] = np.clip(lat1 + dy, -85.0, 85.0)
    return out


def shift_vertices(ring: np.ndarray, dlon: float, dlat: float) -> np.ndarray:
    """Move a lon/lat ring. Latitude is clipped so Mercator stays finite."""
    out = np.empty((len(ring), 2), np.float64)
    out[:, 0] = np.asarray(ring[:, 0], np.float64) + dlon
    out[:, 1] = np.clip(np.asarray(ring[:, 1], np.float64) + dlat, -85.0, 85.0)
    return out


def lat_after(home_lat: float, u: float, extra: float = 0.0) -> float:
    """u=0 keeps the home latitude. u=1 puts the centroid on the equator, then `extra`."""
    return float(home_lat) * (1.0 - u) + extra


def km_ring(ring: np.ndarray, lon0: float, lat0: float) -> np.ndarray:
    """Local equirectangular kilometres. Y grows north."""
    m = 111_320.0
    lon = np.asarray(ring[:, 0], np.float64)
    lat = np.asarray(ring[:, 1], np.float64)
    x = (lon - lon0) * math.cos(math.radians(lat0)) * m
    y = (lat - lat0) * m
    return np.stack([x, y], 1)


def shoelace(xy: np.ndarray) -> float:
    if len(xy) < 3:
        return 0.0
    x = xy[:, 0]
    y = xy[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) * 0.5)
