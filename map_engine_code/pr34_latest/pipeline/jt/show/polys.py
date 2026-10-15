"""
Juicy Tea Map-Shorts Engine — True Coastline & Horizon-Arc Polygon Clipping (Section 5).
"""

from __future__ import annotations
from typing import List, Tuple
import math
import numpy as np


def clip_polygon_to_globe_rim(
    pts_xy: np.ndarray,
    visible_mask: np.ndarray,
    globe_center: Tuple[float, float],
    globe_radius: float,
) -> np.ndarray:
    """
    Section 5 Coastline Fill Rule:
    Never chord-closes a half-clipped globe rim or viewport-clipped polygon.
    Replaces horizon crossings with smooth circular arc points along the true globe rim.
    """
    if np.all(visible_mask):
        return pts_xy
    if not np.any(visible_mask):
        return np.zeros((0, 2), dtype=np.float64)

    cx, cy = globe_center
    out: List[np.ndarray] = []
    n = len(pts_xy)

    for i in range(n):
        if visible_mask[i]:
            out.append(pts_xy[i])
            nxt = (i + 1) % n
            if not visible_mask[nxt]:
                j = nxt
                while not visible_mask[j] and j != i:
                    j = (j + 1) % n
                a0 = math.atan2(pts_xy[i, 1] - cy, pts_xy[i, 0] - cx)
                a1 = math.atan2(pts_xy[j, 1] - cy, pts_xy[j, 0] - cx)
                da = ((a1 - a0 + math.pi) % (2.0 * math.pi)) - math.pi
                arc_angles = np.linspace(a0, a0 + da, 16)
                for ang in arc_angles[1:-1]:
                    out.append(
                        np.array([cx + globe_radius * math.cos(ang), cy + globe_radius * math.sin(ang)])
                    )

    return np.asarray(out, dtype=np.float64) if out else np.zeros((0, 2), dtype=np.float64)
