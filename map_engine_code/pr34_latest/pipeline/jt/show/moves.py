"""
Juicy Tea Map-Shorts Engine — 60fps Motion, Acceleration, Jerk & Event Pacing Linter.
Enforces Sections 4.3, 4.4, 7, and 12.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import math
import numpy as np
from .camera import ContinuousCameraRig, FPS


def check_moves(
    rig: ContinuousCameraRig,
    snap_intervals: List[Tuple[float, float]] | None = None,
) -> Dict[str, float | bool]:
    """
    Samples all 4 camera channels at 60 fps and enforces:
    - No hard-clamping needed: w in [0, 1], span in [28, 170]
    - Max zoom ratio per frame <= 1.02
    - Max |d ln(span)/dt| <= 0.6/s normal, <= 1.2/s during snap-zoom
    - Max pan speed <= 0.8 screen_widths/s
    - Max |dw/dt| <= 1.2/s
    - Max pan acceleration <= 2.0 screen_widths/s^2
    - Max zoom acceleration |d^2 ln(span)/dt^2| <= 3.0/s^2
    - Max frame-to-frame velocity step (jerk limit) <= 8% of peak move velocity
    - Frame 0 starts in motion
    """
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

    for f in range(n_frames + 1):
        t = f * dt
        st = rig.evaluate_all(t)
        w, span = st["w"], st["span"]

        if not (-1e-3 <= w <= 1.001):
            raise ValueError(f"w={w:.4f} out of [0,1] at t={t:.2f}s (fix anchors, do not clamp!)")
        if not (28.0 <= span <= 170.0):
            raise ValueError(f"span={span:.2f} out of [28,170] at t={t:.2f}s")

        cos_lat = max(math.cos(math.radians(st["lat"])), 0.15)
        vx_sw = (st["dlon"] * cos_lat) / span
        vy_sw = st["dlat"] / span
        pan_vel = math.hypot(vx_sw, vy_sw)

        ax_sw = (st["ddlon"] * cos_lat) / span
        ay_sw = st["ddlat"] / span
        pan_acc = math.hypot(ax_sw, ay_sw)

        zoom_vel = abs(st["dlog_span"])
        zoom_acc = abs(st["ddlog_span"])
        dw_vel = abs(st["dw"])

        in_snap = any(s0 - 0.05 <= t <= s1 + 0.05 for s0, s1 in snap_intervals)
        zoom_ceiling = 1.2 if in_snap else 0.6

        if zoom_vel > zoom_ceiling + 1e-2:
            raise ValueError(
                f"Zoom velocity {zoom_vel:.3f}/s exceeds ceiling {zoom_ceiling}/s at t={t:.2f}s"
            )
        if pan_vel > 0.8 + 1e-2:
            raise ValueError(f"Pan velocity {pan_vel:.3f} sw/s exceeds 0.8 sw/s at t={t:.2f}s")
        if dw_vel > 1.2 + 1e-2:
            raise ValueError(f"Morph speed |dw/dt|={dw_vel:.3f}/s exceeds 1.2/s at t={t:.2f}s")
        if pan_acc > 2.0 + 2e-2:
            raise ValueError(f"Pan accel {pan_acc:.3f} sw/s^2 exceeds 2.0 sw/s^2 at t={t:.2f}s")
        if zoom_acc > 3.0 + 2e-2:
            raise ValueError(f"Zoom accel {zoom_acc:.3f}/s^2 exceeds 3.0/s^2 at t={t:.2f}s")

        if prev_state is not None:
            s_ratio = max(span, prev_state["span"]) / min(span, prev_state["span"])
            max_span_ratio = max(max_span_ratio, s_ratio)
            if s_ratio > 1.02 + 1e-4:
                raise ValueError(
                    f"Frame span ratio {s_ratio:.4f} exceeds 1.02 limit at frame {f} (t={t:.2f}s)"
                )

        pan_vels.append(pan_vel)
        zoom_vels.append(zoom_vel)
        max_zoom_vel = max(max_zoom_vel, zoom_vel)
        max_pan_vel = max(max_pan_vel, pan_vel)
        max_dw = max(max_dw, dw_vel)
        max_pan_acc = max(max_pan_acc, pan_acc)
        max_zoom_acc = max(max_zoom_acc, zoom_acc)
        prev_state = st

    peak_pan = max(max_pan_vel, 0.05)
    peak_zoom = max(max_zoom_vel, 0.05)
    max_pan_step_pct = float(np.max(np.abs(np.diff(pan_vels))) / peak_pan)
    max_zoom_step_pct = float(np.max(np.abs(np.diff(zoom_vels))) / peak_zoom)

    if max_pan_step_pct > 0.08:
        raise ValueError(f"Pan frame velocity step {max_pan_step_pct:.1%} > 8% ceiling (jerk spike).")
    if max_zoom_step_pct > 0.08:
        raise ValueError(f"Zoom frame velocity step {max_zoom_step_pct:.1%} > 8% ceiling (jerk spike).")

    st0 = rig.evaluate_all(0.0)
    if abs(st0["dlog_span"]) + abs(st0["dlon"]) + abs(st0["dlat"]) < 1e-3:
        raise ValueError("Frame 0 is static! Video must start in motion.")

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
    """
    Enforces Section 7 Event Pacing Rules:
    - First highlight in [0.0, 1.0s]
    - Max gap between visual events <= 1.5s (drift does NOT count as an event)
    - Target mean gap: 1.0 - 1.3s
    """
    if first_highlight_t > 1.0:
        raise ValueError(f"First highlight at {first_highlight_t:.2f}s exceeds 1.0s rule.")

    times = sorted(set([0.0] + [float(t) for t in event_timestamps] + [float(total_duration)]))
    gaps = np.diff(times)
    max_gap = float(np.max(gaps)) if len(gaps) > 0 else total_duration
    mean_gap = float(np.mean(gaps)) if len(gaps) > 0 else total_duration

    if max_gap > 1.5 + 1e-6:
        bad_idx = int(np.argmax(gaps))
        raise ValueError(
            f"Dead event window of {max_gap:.2f}s (> 1.5s limit) between "
            f"t={times[bad_idx]:.2f}s and t={times[bad_idx + 1]:.2f}s."
        )

    return {
        "ok": True,
        "max_event_gap_s": round(max_gap, 3),
        "mean_event_gap_s": round(mean_gap, 3),
        "event_count": len(event_timestamps),
    }
