"""
Juicy Tea Map-Shorts Engine — Production Episode Specifications:
1. 'greenland' (Refactored v17: C2 spline, zero black flash at 4.63-4.98s, Cyan #00E5FF karaoke)
2. 'cut_in_two' (Full engine implementation of docs/refs/cut_in_two_script_v2.md)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from .retime import LockedCameraMove, build_anchors_with_drift
from .camera import ContinuousCameraRig


@dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    total_duration: float
    first_highlight_t: float
    moves: List[LockedCameraMove]
    event_timestamps: List[float]
    map_has_yellow: bool = True

    def build_rig(self) -> ContinuousCameraRig:
        anchors = build_anchors_with_drift(self.moves)
        return ContinuousCameraRig(anchors, total_duration=self.total_duration)

    def snap_intervals(self) -> List[Tuple[float, float]]:
        return [
            (m.start_t, m.start_t + m.duration)
            for m in self.moves
            if m.is_snap
        ]


def build_greenland_episode() -> EpisodeSpec:
    total_dur = 52.42
    moves = [
        LockedCameraMove("gr_open_snap", 0, 0.0, 1.35, 0.0, 0.0, -42.0, -41.0, 72.0, 69.0, 84.0, 58.0, is_snap=True),
        LockedCameraMove("gr_to_africa", 6, 4.0, 1.85, 0.0, 0.30, -40.7, -14.0, 69.0, 42.0, 56.0, 78.0),
        LockedCameraMove("gr_drag_true", 15, 8.2, 1.80, 0.30, 0.0, -13.8, 14.0, 42.0, 14.0, 76.0, 64.0),
        LockedCameraMove("gr_pack_14x", 28, 14.0, 1.50, 0.0, 0.0, 14.3, 19.5, 14.0, 6.0, 61.0, 50.0),
        # Wide span + 2.0s so the Africa→Atlantic morph stays under 0.8 sw/s and 2.0 sw/s^2.
        LockedCameraMove("gr_globe_morph", 45, 21.5, 2.00, 0.0, 1.0, 19.9, -8.0, 6.1, 38.0, 90.0, 110.0),
        LockedCameraMove("gr_denmark_fly", 64, 29.8, 1.60, 1.0, 0.25, -7.5, 10.0, 38.1, 56.0, 62.0, 48.0),
        LockedCameraMove("gr_arctic_orbit", 85, 38.2, 1.65, 0.25, 1.0, 10.5, -24.0, 56.1, 68.0, 45.0, 64.0),
        LockedCameraMove("gr_loop_prep", 108, 46.8, 1.65, 1.0, 0.0, -23.5, -41.8, 68.1, 71.8, 60.0, 84.0),
    ]
    events = [round(t * 1.15, 2) for t in range(1, int(total_dur / 1.15) + 1) if t * 1.15 < total_dur]
    return EpisodeSpec(
        episode_id="greenland",
        total_duration=total_dur,
        first_highlight_t=0.25,
        moves=moves,
        event_timestamps=events,
        map_has_yellow=True,
    )


def build_cut_in_two_episode() -> EpisodeSpec:
    total_dur = 64.00
    moves = [
        # 1.80s so |dw/dt| for the full globe→map morph stays <= 1.2/s.
        LockedCameraMove("cit_hook_croatia", 0, 0.0, 1.80, 1.0, 0.0, 17.5, 17.6, 43.5, 42.9, 68.0, 46.0, is_snap=True),
        LockedCameraMove("cit_neum_zoom", 9, 4.5, 1.45, 0.0, 0.0, 17.8, 17.62, 42.9, 42.92, 44.0, 34.0),
        LockedCameraMove("cit_peljesac_bridge", 21, 9.8, 1.35, 0.0, 0.0, 17.8, 17.53, 42.95, 42.93, 33.0, 38.0),
        # Long geographic hops use a wide span and the 2.0s duration cap so peak pan stays <= 0.8 sw/s.
        LockedCameraMove("cit_fly_brunei", 36, 16.0, 2.00, 0.0, 0.80, 17.8, 56.0, 42.98, 24.0, 96.0, 110.0),
        LockedCameraMove("cit_temburong_split", 50, 22.5, 2.00, 0.80, 0.0, 56.3, 94.0, 24.1, 8.0, 112.0, 124.0),
        LockedCameraMove("cit_fly_kaliningrad", 68, 30.2, 2.00, 0.0, 0.65, 94.4, 58.0, 8.1, 32.0, 120.0, 100.0),
        LockedCameraMove("cit_kaliningrad_zoom", 82, 36.8, 2.00, 0.65, 0.0, 58.3, 24.0, 32.1, 52.0, 96.0, 64.0),
        LockedCameraMove("cit_fly_nakhchivan", 98, 43.8, 1.65, 0.0, 0.35, 24.4, 44.5, 52.1, 39.5, 38.0, 46.0),
        LockedCameraMove("cit_fly_cyprus", 116, 51.2, 1.60, 0.35, 0.0, 44.9, 33.4, 39.6, 35.1, 43.5, 36.0),
        LockedCameraMove("cit_loop_return", 138, 59.0, 1.85, 0.0, 1.0, 33.8, 17.6, 35.2, 43.4, 34.0, 68.0),
    ]
    events = [round(t * 1.18, 2) for t in range(1, int(total_dur / 1.18) + 1) if t * 1.18 < total_dur]
    return EpisodeSpec(
        episode_id="cut_in_two",
        total_duration=total_dur,
        first_highlight_t=0.20,
        moves=moves,
        event_timestamps=events,
        map_has_yellow=True,
    )
