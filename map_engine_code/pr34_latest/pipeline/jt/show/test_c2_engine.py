"""60 fps C2 checks for the refactored camera, icon pop, and event pacing."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.episodes import build_cut_in_two_episode, build_greenland_episode  # noqa: E402
from jt.show.moves import check_event_pacing, check_moves  # noqa: E402
from jt.show.retime import retime_moves_to_words  # noqa: E402
from jt.show.vfx_core import icon_pop_scale, label_pop_state  # noqa: E402


def main() -> None:
    words = [{"start": i * 0.42, "end": i * 0.42 + 0.35} for i in range(220)]
    for builder in (build_greenland_episode, build_cut_in_two_episode):
        spec = builder()
        rig = spec.build_rig()
        motion = check_moves(rig, snap_intervals=spec.snap_intervals())
        events = check_event_pacing(
            spec.event_timestamps,
            total_duration=spec.total_duration,
            first_highlight_t=spec.first_highlight_t,
        )
        retime_moves_to_words(spec.moves, words)
        assert motion["ok"] and events["ok"]
        assert motion["max_pan_vel"] <= 0.8
        assert motion["max_pan_step_pct"] <= 0.08
        assert events["max_event_gap_s"] <= 1.5
        if spec.episode_id == "cut_in_two":
            assert spec.total_duration == 92.55
            assert min(move.span_end for move in spec.moves) <= 5.0
            assert max(move.w_end for move in spec.moves) >= 0.85
            end = rig.evaluate_all(spec.total_duration)
            start = rig.evaluate_all(0.0)
            assert abs(((end["lon"] - start["lon"] + 180) % 360) - 180) < 0.05
            assert abs(end["lat"] - start["lat"]) < 0.05
            assert abs(end["span"] - start["span"]) < 0.05
            assert abs(end["w"] - start["w"]) < 0.05
        print(spec.episode_id, motion["max_pan_vel"], events["max_event_gap_s"])

    assert abs(icon_pop_scale(0.62 * 0.60) - 1.15) < 1e-9
    samples = np.linspace(0.0, 0.6, 61)
    scales = np.array([icon_pop_scale(float(t)) for t in samples])
    assert float(scales.max()) <= 1.15 + 1e-9
    assert abs(icon_pop_scale(0.6) - 1.0) < 1e-9
    assert abs(label_pop_state(0.62 * 0.30, 0.30)[0] - 1.06) < 1e-6
    print("c2 engine ok")


if __name__ == "__main__":
    main()
