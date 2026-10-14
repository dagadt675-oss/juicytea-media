"""
Juicy Tea Map-Shorts Engine — Locked-Duration Retime & Unidirectional Drift Fill.
Enforces Rule 6 & Section 4.6:
- Move durations and peak velocities are strictly locked when retiming to words.json.
- Holds between moves are filled with unidirectional drift (1-3%/s scale, <=0.5% sw/s pan).
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Dict, List
import math
import numpy as np
from .camera import CameraAnchor, FPS


@dataclass(frozen=True)
class LockedCameraMove:
    move_id: str
    cue_word_index: int
    start_t: float
    duration: float          # LOCKED: never stretched when VO changes
    w_start: float
    w_end: float
    lon_start: float
    lon_end: float
    lat_start: float
    lat_end: float
    span_start: float
    span_end: float
    drift_scale_rate: float = -0.012  # -1.2%/s unidirectional scale drift during hold
    drift_lon_rate: float = 0.08      # deg/s unidirectional lon drift during hold
    drift_lat_rate: float = 0.02      # deg/s unidirectional lat drift during hold
    is_snap: bool = False

    def validate_duration(self) -> None:
        span_ratio = max(self.span_start, self.span_end) / max(
            min(self.span_start, self.span_end), 1e-6
        )
        is_small_correction = (span_ratio - 1.0) < 0.10 and abs(
            self.lon_end - self.lon_start
        ) < 2.0
        min_dur = 0.5 if is_small_correction else 0.8
        if not (min_dur <= self.duration <= 2.0):
            raise ValueError(
                f"Move '{self.move_id}' duration {self.duration:.2f}s violates "
                f"[{min_dur:.1f}s, 2.0s] rule."
            )

    @property
    def peak_zoom_velocity(self) -> float:
        return 1.875 * abs(math.log(self.span_end / self.span_start)) / self.duration


def retime_moves_to_words(
    moves: List[LockedCameraMove],
    words: List[Dict[str, float]],
    min_hold_gap: float = 0.15,
) -> List[LockedCameraMove]:
    """Shifts move start times to match words.json while locking move duration & velocity."""
    retimed: List[LockedCameraMove] = []
    cursor_t = 0.0

    for mv in moves:
        mv.validate_duration()
        if 0 <= mv.cue_word_index < len(words):
            word_t = float(words[mv.cue_word_index]["start"])
        else:
            word_t = mv.start_t

        new_start = max(word_t, cursor_t)
        retimed_mv = replace(mv, start_t=new_start)
        retimed.append(retimed_mv)
        cursor_t = new_start + mv.duration + min_hold_gap

    verify_retime_invariants(moves, retimed)
    return retimed


def build_anchors_with_drift(moves: List[LockedCameraMove]) -> List[CameraAnchor]:
    """
    Converts LockedCameraMove objects into a continuous CameraAnchor table,
    filling every hold gap between moves with unidirectional drift.
    """
    anchors: List[CameraAnchor] = []
    lon_offset = 0.0
    lat_offset = 0.0
    scale_factor = 1.0

    for i, mv in enumerate(moves):
        mv.validate_duration()
        if i > 0:
            prev = moves[i - 1]
            prev_end_t = prev.start_t + prev.duration
            hold_dt = max(0.0, mv.start_t - prev_end_t)
            if hold_dt > 0.0:
                lon_offset += prev.drift_lon_rate * hold_dt
                lat_offset += prev.drift_lat_rate * hold_dt
                scale_factor *= math.exp(prev.drift_scale_rate * hold_dt)

        s0 = float(np.clip(mv.span_start * scale_factor, 29.0, 168.0))
        s1 = float(np.clip(mv.span_end * scale_factor, 29.0, 168.0))

        if not anchors or mv.start_t > anchors[-1].t + 1e-3:
            anchors.append(
                CameraAnchor(
                    t=mv.start_t,
                    w=mv.w_start,
                    lon=mv.lon_start + lon_offset,
                    lat=mv.lat_start + lat_offset,
                    span=s0,
                    is_snap=mv.is_snap,
                )
            )
        anchors.append(
            CameraAnchor(
                t=mv.start_t + mv.duration,
                w=mv.w_end,
                lon=mv.lon_end + lon_offset,
                lat=mv.lat_end + lat_offset,
                span=s1,
                is_snap=mv.is_snap,
            )
        )
    return anchors


def verify_retime_invariants(
    original: List[LockedCameraMove], retimed: List[LockedCameraMove]
) -> None:
    """Asserts duration and peak velocity match within +-1 frame (1/60s) before and after retime."""
    frame_tol = 1.0 / FPS
    for orig, ret in zip(original, retimed):
        if abs(orig.duration - ret.duration) > frame_tol:
            raise AssertionError(
                f"Retime duration violation on {orig.move_id}: "
                f"{orig.duration:.4f}s vs {ret.duration:.4f}s"
            )
        if abs(orig.peak_zoom_velocity - ret.peak_zoom_velocity) > 1e-6:
            raise AssertionError(
                f"Retime peak velocity violation on {orig.move_id}: "
                f"{orig.peak_zoom_velocity:.4f} vs {ret.peak_zoom_velocity:.4f}"
            )
