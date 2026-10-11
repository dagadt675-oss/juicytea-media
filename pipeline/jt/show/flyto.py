# Copyright 2010-2021 Mike Bostock
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
# THIS SOFTWARE.
#
"""Camera flight along the van Wijk & Nuij zoom-pan path.

Direct port of d3-interpolate `src/zoom.js` (ISC, Mike Bostock). That is the
same curve MapLibre GL JS `Map.flyTo` (BSD-3-Clause) and deck.gl
`FlyToInterpolator` / math.gl `flyToViewport` (MIT) use. rho 1.42 is the
MapLibre default, the value picked in the van Wijk user study. rho √2 is the
d3 default.

`x`, `y`, and `w` share one unit. `w` is the visible width: larger means
zoomed out. `t` runs from 0 to 1 along the path. Suggested duration is in
milliseconds, the absolute value of d3's `interpolator.duration`.
"""

from __future__ import annotations

import math

_EPSILON2 = 1e-12


def _r(b: float) -> float:
    """log(-b + sqrt(b^2 + 1)), as in the paper, via asinh so large b stays stable."""
    return -math.asinh(b)


def interpolate_zoom(p0: tuple[float, float, float], p1: tuple[float, float, float], rho: float = 1.42):
    """Return i(t) -> (x, y, w). i.duration is the suggested length in ms."""
    rho = max(1e-3, float(rho))
    rho2 = rho * rho
    ux0, uy0, w0 = (float(p0[0]), float(p0[1]), float(p0[2]))
    ux1, uy1, w1 = (float(p1[0]), float(p1[1]), float(p1[2]))
    dx = ux1 - ux0
    dy = uy1 - uy0
    d2 = dx * dx + dy * dy
    if w0 <= 0 or w1 <= 0:
        raise ValueError("view width must be positive")

    if d2 < _EPSILON2:
        s_len = math.log(w1 / w0) / rho

        def interp(t: float) -> tuple[float, float, float]:
            return (
                ux0 + t * dx,
                uy0 + t * dy,
                w0 * math.exp(rho * t * s_len),
            )
    else:
        d1 = math.sqrt(d2)
        b0 = (w1 * w1 - w0 * w0 + rho2 * rho2 * d2) / (2 * w0 * rho2 * d1)
        b1 = (w1 * w1 - w0 * w0 - rho2 * rho2 * d2) / (2 * w1 * rho2 * d1)
        r0 = _r(b0)
        r1 = _r(b1)
        s_len = (r1 - r0) / rho

        def interp(t: float) -> tuple[float, float, float]:
            s = t * s_len
            cosh_r0 = math.cosh(r0)
            u = w0 / (rho2 * d1) * (cosh_r0 * math.tanh(rho * s + r0) - math.sinh(r0))
            return (
                ux0 + u * dx,
                uy0 + u * dy,
                w0 * cosh_r0 / math.cosh(rho * s + r0),
            )

    interp.duration = abs(s_len) * 1000.0 * rho / math.sqrt(2.0)  # type: ignore[attr-defined]
    return interp


def fly_lonlat(
    t: float,
    lon0: float,
    lat0: float,
    w0: float,
    lon1: float,
    lat1: float,
    w1: float,
    rho: float = 1.42,
) -> tuple[float, float, float]:
    """(lon, lat, width_m) at t. Centers are placed in local meters about the destination."""
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    m_lat = 110540.0
    m_lon = 111320.0 * math.cos(math.radians(lat1))
    x0 = (lon0 - lon1) * m_lon
    y0 = (lat0 - lat1) * m_lat
    path = interpolate_zoom((x0, y0, w0), (0.0, 0.0, w1), rho)
    x, y, w = path(t)
    if m_lon == 0:
        return lon1, lat1, w
    return lon1 + x / m_lon, lat1 + y / m_lat, w
