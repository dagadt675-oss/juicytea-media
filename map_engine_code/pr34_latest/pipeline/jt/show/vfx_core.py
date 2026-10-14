"""
Juicy Tea Map-Shorts Engine — C2-Continuous VFX Curves (Icon Pop, Label Pop & Moving Fade-Out).
Note: During holds, the camera maintains continuous unidirectional drift (Rule 4).
"""

from __future__ import annotations
from typing import Tuple
from .camera import smootherstep


def icon_pop_scale(elapsed_s: float, duration_s: float = 0.60, peak: float = 1.15) -> float:
    """
    C2-continuous easeOutBack curve reaching 115% peak over 0.60s (36 frames @ 60fps)
    and settling smoothly to 100% with zero velocity break at the peak.
    Replaces the broken linear-ramp + smoothstep icon_pop (Section 11.2 #6).
    """
    if elapsed_s <= 0.0:
        return 0.0
    if elapsed_s >= duration_s:
        return 1.0
    # Two quintic smoothersteps joined at the peak. Each piece has zero velocity
    # and zero acceleration at its ends, so the 115% crest is C2 — no velocity break.
    peak_at = 0.62 * duration_s
    if elapsed_s <= peak_at:
        return float(peak * smootherstep(elapsed_s / peak_at))
    settle = (elapsed_s - peak_at) / (duration_s - peak_at)
    return float(peak + (1.0 - peak) * smootherstep(settle))


def label_pop_state(elapsed_s: float, duration_s: float = 0.30) -> Tuple[float, float]:
    """
    Section 6.1 Label Pop: 0.25-0.35s, <= 8% overshoot (1.06), smootherstep alpha in first 60%.
    """
    if elapsed_s <= 0.0:
        return 0.0, 0.0
    if elapsed_s >= duration_s:
        return 1.0, 1.0
    scale = icon_pop_scale(elapsed_s, duration_s=duration_s, peak=1.06)
    alpha = float(smootherstep(min(1.0, elapsed_s / (0.60 * duration_s))))
    return scale, alpha


def element_fade_and_exit_offset(
    t: float,
    enter_t: float,
    exit_t: float,
    fade_in_s: float = 0.28,
    fade_out_s: float = 0.28,
    exit_drift_px: Tuple[float, float] = (18.0, -12.0),
) -> Tuple[float, float, float]:
    """
    Enforces >= 0.25s smooth fade-in/out and keeps exiting elements moving for >= 0.40s
    so no element freezes before vanishing or disappears in 1 frame.
    Returns (alpha, dx_px, dy_px).
    """
    fade_in_s = max(fade_in_s, 0.25)
    fade_out_s = max(fade_out_s, 0.25)
    exit_move_s = max(fade_out_s, 0.40)

    if t <= enter_t or t >= exit_t + fade_out_s:
        return 0.0, 0.0, 0.0
    if t < enter_t + fade_in_s:
        alpha = float(smootherstep((t - enter_t) / fade_in_s))
        return alpha, 0.0, 0.0
    if t > exit_t:
        u_fade = min(1.0, (t - exit_t) / fade_out_s)
        u_move = min(1.0, (t - exit_t) / exit_move_s)
        alpha = float(1.0 - smootherstep(u_fade))
        s_move = float(smootherstep(u_move))
        return alpha, exit_drift_px[0] * s_move, exit_drift_px[1] * s_move
    return 1.0, 0.0, 0.0
