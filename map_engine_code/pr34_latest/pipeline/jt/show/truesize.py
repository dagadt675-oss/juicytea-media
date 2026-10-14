"""
Juicy Tea Map-Shorts Engine — True-Size Country Drag Module (Rule 8, Rule 9 & Section 6.2).
"""

from __future__ import annotations
from typing import Dict, Tuple
import math
import numpy as np
from .camera import smootherstep


def truesize_drag_state(
    t: float,
    start_t: float,
    duration_s: float,
    start_lon_lat: Tuple[float, float],
    end_lon_lat: Tuple[float, float],
    ref_lat: float,
) -> Dict[str, float | str | bool]:
    """
    Section 6.2 True-Size Drag:
    - Smootherstep path over 1.2 - 2.0s (peak velocity at midpoint, zero spring bounce).
    - Continuous sec^2(lat) area scaling recalculated on every frame.
    - Fixed format f"{mult:.1f}x" counter string so width never jumps.
    - Kenney SVG hand prop parallax timestamp at t - 1/30s without dark shadow circle.
    """
    duration_s = float(np.clip(duration_s, 1.2, 2.0))
    u = float(np.clip((t - start_t) / duration_s, 0.0, 1.0))
    s = float(smootherstep(u))

    lon = start_lon_lat[0] + s * (end_lon_lat[0] - start_lon_lat[0])
    lat = start_lon_lat[1] + s * (end_lon_lat[1] - start_lon_lat[1])

    cos_ref = max(math.cos(math.radians(ref_lat)), 0.05)
    cos_cur = max(math.cos(math.radians(lat)), 0.05)
    linear_scale = cos_ref / cos_cur
    area_mult = (cos_cur / cos_ref) ** 2

    return {
        "lon": lon,
        "lat": lat,
        "linear_scale": linear_scale,
        "counter_text": f"{area_mult:.1f}x",
        "hand_parallax_t": max(0.0, t - (1.0 / 30.0)),
        "draw_hand_shadow_circle": False,
    }
