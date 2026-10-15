"""
Juicy Tea Map-Shorts Engine — Van Wijk Optimal Zoom-Pan Flyto Curve (Zero Blur).
Implements Section 4.1 & 4.3: rho = 1.42, smootherstep time parameterization, duration 1.0 - 1.6s.
"""

from __future__ import annotations
from typing import Tuple
import math
from .camera import smootherstep


def van_wijk_flyto(
    u_time: float,
    lon0: float,
    lat0: float,
    span0: float,
    lon1: float,
    lat1: float,
    span1: float,
    rho: float = 1.42,
) -> Tuple[float, float, float]:
    """
    Evaluates (lon, lat, span) at normalized time u_time in [0, 1] along a van Wijk & Nuij
    hyperbolic zoom-pan geodesic with C2 smootherstep time warping and zero motion blur.
    """
    u = float(smootherstep(u_time))
    dlon = ((lon1 - lon0 + 180.0) % 360.0) - 180.0
    dlat = lat1 - lat0
    dist = math.hypot(dlon * math.cos(math.radians(0.5 * (lat0 + lat1))), dlat)

    if dist < 1e-4:
        span = math.exp((1.0 - u) * math.log(span0) + u * math.log(span1))
        return lon0 + u * dlon, lat0 + u * dlat, span

    rho2 = rho * rho
    w0 = max(span0, 1e-3)
    w1 = max(span1, 1e-3)

    b0 = (w1 * w1 - w0 * w0 + (rho2 ** 2) * (dist ** 2)) / (2.0 * w0 * rho2 * dist)
    b1 = (w1 * w1 - w0 * w0 - (rho2 ** 2) * (dist ** 2)) / (2.0 * w1 * rho2 * dist)

    r0 = math.log(-b0 + math.sqrt(b0 * b0 + 1.0))
    r1 = math.log(-b1 + math.sqrt(b1 * b1 + 1.0))
    S = (r1 - r0) / rho

    if abs(S) < 1e-5:
        span = math.exp((1.0 - u) * math.log(w0) + u * math.log(w1))
        return lon0 + u * dlon, lat0 + u * dlat, span

    s = u * S
    cosh_r0 = math.cosh(r0)
    w_s = w0 * (cosh_r0 / math.cosh(rho * s + r0))
    u_s = (w0 / (rho2 * dist)) * (cosh_r0 * math.tanh(rho * s + r0) - math.sinh(r0))
    u_s = float(max(0.0, min(1.0, u_s)))

    lon = lon0 + u_s * dlon
    lat = lat0 + u_s * dlat
    span = float(max(28.0, min(170.0, w_s)))
    return lon, lat, span
