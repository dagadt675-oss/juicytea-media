"""60 fps motion, acceleration, jerk and event-pacing linter. Spans may be 3.2–170°."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np

from .camera import MAX_SPAN_DEG, MIN_SPAN_DEG, ContinuousCameraRig, FPS


def check_moves(
    rig: ContinuousCameraRig,
    snap_intervals: List[Tuple[float, float]] | None = None,
) -> Dict[str, float | bool]:
    snap_intervals = snap_intervals or []
    n_frames = int(round(rig.total_duration * FPS))
    dt = 1.0 / FPS
    prev_state = None
    max_span_ratio = 1.0
    max_zoom_vel = 0.0
    max_pan_vel = 0.0
    max_dw = 0.0
    max_pan_acc = 0.0
    max_zoom_acc = 0.0
    pan_vels: List[float] = []
    zoom_vels: List[float] = []

    for frame in range(n_frames + 1):
        t = frame * dt
        state = rig.evaluate_all(t)
        w, span = state["w"], state["span"]
        if not (-1e-3 <= w <= 1.001):
            raise ValueError(f"w={w:.4f} out of [0,1] at t={t:.2f}s")
        if not (MIN_SPAN_DEG <= span <= MAX_SPAN_DEG):
            raise ValueError(f"span={span:.2f} out of range at t={t:.2f}s")

        cos_lat = max(math.cos(math.radians(state["lat"])), 0.15)
        eff_span = max(span, 22.0)
        pan_vel = math.hypot((state["dlon"] * cos_lat) / eff_span, state["dlat"] / eff_span)
        pan_acc = math.hypot((state["ddlon"] * cos_lat) / eff_span, state["ddlat"] / eff_span)
        zoom_vel = abs(state["dlog_span"])
        zoom_acc = abs(state["ddlog_span"])
        dw_vel = abs(state["dw"])
        in_snap = any(s0 - 0.10 <= t <= s1 + 0.10 for s0, s1 in snap_intervals)
        zoom_ceiling = 1.2 if in_snap else 0.6

        if zoom_vel > zoom_ceiling + 2e-2:
            raise ValueError(f"Zoom velocity {zoom_vel:.3f}/s exceeds {zoom_ceiling}/s at t={t:.2f}s")
        if pan_vel > 0.8 + 2e-2:
            raise ValueError(f"Pan velocity {pan_vel:.3f} sw/s exceeds 0.8 sw/s at t={t:.2f}s")
        if dw_vel > 1.2 + 2e-2:
            raise ValueError(f"Morph speed |dw/dt|={dw_vel:.3f}/s exceeds 1.2/s at t={t:.2f}s")
        if pan_acc > 2.0 + 3e-2:
            raise ValueError(f"Pan accel {pan_acc:.3f} sw/s^2 exceeds 2.0 at t={t:.2f}s")
        if zoom_acc > 3.0 + 3e-2:
            raise ValueError(f"Zoom accel {zoom_acc:.3f}/s^2 exceeds 3.0 at t={t:.2f}s")
        if prev_state is not None:
            ratio = max(span, prev_state["span"]) / min(span, prev_state["span"])
            max_span_ratio = max(max_span_ratio, ratio)
            if ratio > 1.02 + 2e-4:
                raise ValueError(f"Frame span ratio {ratio:.4f} exceeds 1.02 at t={t:.2f}s")
        pan_vels.append(pan_vel)
        zoom_vels.append(zoom_vel)
        max_zoom_vel = max(max_zoom_vel, zoom_vel)
        max_pan_vel = max(max_pan_vel, pan_vel)
        max_dw = max(max_dw, dw_vel)
        max_pan_acc = max(max_pan_acc, pan_acc)
        max_zoom_acc = max(max_zoom_acc, zoom_acc)
        prev_state = state

    peak_pan = max(max_pan_vel, 0.05)
    peak_zoom = max(max_zoom_vel, 0.05)
    max_pan_step_pct = float(np.max(np.abs(np.diff(pan_vels))) / peak_pan)
    max_zoom_step_pct = float(np.max(np.abs(np.diff(zoom_vels))) / peak_zoom)
    if max_pan_step_pct > 0.08:
        raise ValueError(f"Pan frame velocity step {max_pan_step_pct:.1%} > 8%.")
    if max_zoom_step_pct > 0.08:
        raise ValueError(f"Zoom frame velocity step {max_zoom_step_pct:.1%} > 8%.")
    start = rig.evaluate_all(0.0)
    if abs(start["dlog_span"]) + abs(start["dlon"]) + abs(start["dlat"]) < 1e-3:
        raise ValueError("Frame 0 is static.")
    return {
        "ok": True,
        "max_span_ratio": round(max_span_ratio, 5),
        "max_zoom_vel": round(max_zoom_vel, 4),
        "max_pan_vel": round(max_pan_vel, 4),
        "max_dw": round(max_dw, 4),
        "max_pan_acc": round(max_pan_acc, 4),
        "max_zoom_acc": round(max_zoom_acc, 4),
        "max_pan_step_pct": round(max_pan_step_pct, 4),
        "max_zoom_step_pct": round(max_zoom_step_pct, 4),
    }


def check_event_pacing(
    event_timestamps: List[float],
    total_duration: float,
    first_highlight_t: float,
) -> Dict[str, float | bool]:
    if first_highlight_t > 1.0:
        raise ValueError(f"First highlight at {first_highlight_t:.2f}s exceeds 1.0s.")
    times = sorted(set([0.0] + [float(t) for t in event_timestamps] + [float(total_duration)]))
    gaps = np.diff(times)
    max_gap = float(np.max(gaps)) if len(gaps) else total_duration
    mean_gap = float(np.mean(gaps)) if len(gaps) else total_duration
    if max_gap > 1.5 + 1e-6:
        bad = int(np.argmax(gaps))
        raise ValueError(f"Dead event window of {max_gap:.2f}s between {times[bad]:.2f}s and {times[bad+1]:.2f}s.")
    return {
        "ok": True,
        "max_event_gap_s": round(max_gap, 3),
        "mean_event_gap_s": round(mean_gap, 3),
        "event_count": len(event_timestamps),
    }
