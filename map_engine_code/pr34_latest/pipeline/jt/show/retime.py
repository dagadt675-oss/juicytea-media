"""Locked-duration retime. Close-up spans may go down to 3.2 degrees."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Dict, List

import numpy as np

from .camera import MAX_SPAN_DEG, MIN_SPAN_DEG, CameraAnchor, FPS


@dataclass(frozen=True)
class LockedCameraMove:
    move_id: str
    cue_word_index: int
    start_t: float
    duration: float
    w_start: float
    w_end: float
    lon_start: float
    lon_end: float
    lat_start: float
    lat_end: float
    span_start: float
    span_end: float
    drift_scale_rate: float = -0.012
    drift_lon_rate: float = 0.05
    drift_lat_rate: float = 0.015
    is_snap: bool = False

    def validate_duration(self) -> None:
        span_ratio = max(self.span_start, self.span_end) / max(min(self.span_start, self.span_end), 1e-6)
        is_small = (span_ratio - 1.0) < 0.10 and abs(self.lon_end - self.lon_start) < 2.0
        min_dur = 0.5 if is_small else 0.8
        if not (min_dur <= self.duration <= 2.0):
            raise ValueError(
                f"Move '{self.move_id}' duration {self.duration:.2f}s violates [{min_dur:.1f}s, 2.0s]."
            )

    @property
    def peak_zoom_velocity(self) -> float:
        return 1.875 * abs(math.log(self.span_end / self.span_start)) / self.duration


def retime_moves_to_words(
    moves: List[LockedCameraMove],
    words: List[Dict[str, float]],
    min_hold_gap: float = 0.15,
) -> List[LockedCameraMove]:
    retimed: List[LockedCameraMove] = []
    cursor_t = 0.0
    for move in moves:
        move.validate_duration()
        if 0 <= move.cue_word_index < len(words):
            word_t = float(words[move.cue_word_index]["start"])
        else:
            word_t = move.start_t
        new_start = max(word_t, cursor_t)
        retimed.append(replace(move, start_t=new_start))
        cursor_t = new_start + move.duration + min_hold_gap
    verify_retime_invariants(moves, retimed)
    return retimed


def build_anchors_with_drift(moves: List[LockedCameraMove]) -> List[CameraAnchor]:
    anchors: List[CameraAnchor] = []
    for index, move in enumerate(moves):
        move.validate_duration()
        if index > 0:
            previous = anchors[-1]
            hold_dt = max(0.0, move.start_t - previous.t)
            if hold_dt > 0.05:
                drifted_span = float(
                    np.clip(
                        previous.span * math.exp(move.drift_scale_rate * hold_dt),
                        MIN_SPAN_DEG + 0.1,
                        MAX_SPAN_DEG - 1.0,
                    )
                )
                drifted_lon = previous.lon + move.drift_lon_rate * hold_dt * (previous.span / 45.0)
                drifted_lat = previous.lat + move.drift_lat_rate * hold_dt * (previous.span / 45.0)
                anchors.append(
                    CameraAnchor(
                        t=move.start_t,
                        w=move.w_start,
                        lon=drifted_lon,
                        lat=drifted_lat,
                        span=drifted_span,
                        is_snap=move.is_snap,
                    )
                )
        else:
            anchors.append(
                CameraAnchor(
                    t=move.start_t,
                    w=move.w_start,
                    lon=move.lon_start,
                    lat=move.lat_start,
                    span=float(np.clip(move.span_start, MIN_SPAN_DEG + 0.1, MAX_SPAN_DEG - 1.0)),
                    is_snap=move.is_snap,
                )
            )
        anchors.append(
            CameraAnchor(
                t=move.start_t + move.duration,
                w=move.w_end,
                lon=move.lon_end,
                lat=move.lat_end,
                span=float(np.clip(move.span_end, MIN_SPAN_DEG + 0.1, MAX_SPAN_DEG - 1.0)),
                is_snap=move.is_snap,
            )
        )
    return anchors


def verify_retime_invariants(original: List[LockedCameraMove], retimed: List[LockedCameraMove]) -> None:
    frame_tol = 1.0 / FPS
    for orig, ret in zip(original, retimed):
        if abs(orig.duration - ret.duration) > frame_tol:
            raise AssertionError(f"Retime duration violation on {orig.move_id}")
        if abs(orig.peak_zoom_velocity - ret.peak_zoom_velocity) > 1e-6:
            raise AssertionError(f"Retime peak velocity violation on {orig.move_id}")
