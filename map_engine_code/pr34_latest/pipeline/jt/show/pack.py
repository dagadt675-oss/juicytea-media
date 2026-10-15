"""
Juicy Tea Map-Shorts Engine — Coastline-Mask Packing & Puzzle-Fit Module (Rule 9 & Section 6.3).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from .camera import smootherstep


@dataclass(frozen=True)
class PackedPiece:
    country_id: str
    start_xy: Tuple[float, float]
    target_xy: Tuple[float, float]
    enter_t: float
    move_duration: float = 0.80  # 0.6 - 1.0s smootherstep arrival
    rotation_deg: float = 0.0    # 0.0 for puzzle-fit comparisons


def evaluate_packed_pieces(
    pieces: List[PackedPiece],
    t: float,
    stagger_s: float = 0.22,
) -> List[Dict[str, float | str]]:
    """
    Section 6.3 Packing & Puzzle-Fit:
    Each piece arrives individually over 0.6-1.0s on a smootherstep trajectory
    with 0.15-0.30s stagger, zero rotation for puzzle-fit comparisons.
    """
    stagger_s = float(np.clip(stagger_s, 0.15, 0.30))
    states = []
    for idx, p in enumerate(pieces):
        t0 = p.enter_t + idx * stagger_s
        dur = float(np.clip(p.move_duration, 0.60, 1.00))
        if t < t0:
            continue
        u = float(np.clip((t - t0) / dur, 0.0, 1.0))
        s = float(smootherstep(u))
        x = p.start_xy[0] + s * (p.target_xy[0] - p.start_xy[0])
        y = p.start_xy[1] + s * (p.target_xy[1] - p.start_xy[1])
        alpha = float(smootherstep(min(1.0, (t - t0) / 0.28)))
        states.append({
            "country_id": p.country_id,
            "x": x,
            "y": y,
            "alpha": alpha,
            "rotation_deg": 0.0,
        })
    return states
