"""
Juicy Tea Map-Shorts Engine — Refactored Greenland Live Engine Module.
All camera holds use continuous unidirectional drift (1-3%/s scale, <=0.5% sw/s pan).
Uniform Catmull-Rom and hard clamps have been replaced by ContinuousCameraRig (camera.py).
"""

from __future__ import annotations
from typing import Tuple
from .camera import (
    FPS, WIDTH, HEIGHT, ContinuousCameraRig, blend_xy_morph,
    superellipse_silhouette, globe_lod_mix
)
from .episodes import build_greenland_episode
from .moves import check_moves, check_event_pacing

_SPEC = build_greenland_episode()
_RIG: ContinuousCameraRig = _SPEC.build_rig()


def camera_channels(t: float) -> Tuple[float, float, float, float]:
    """Returns C2-continuous (w, lon, lat, span) with zero hard clamping and Hermite loop."""
    return _RIG.camera_channels(t)


def validate_greenland_rig() -> dict:
    """Runs the 60fps C2 motion and 1.5s event pacing linters on the Greenland rig."""
    m_rep = check_moves(_RIG, snap_intervals=_SPEC.snap_intervals())
    e_rep = check_event_pacing(
        _SPEC.event_timestamps,
        total_duration=_SPEC.total_duration,
        first_highlight_t=_SPEC.first_highlight_t,
    )
    return {"motion": m_rep, "events": e_rep}
