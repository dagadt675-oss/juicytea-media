#!/usr/bin/env python3
"""Verify the Juicy Tea cut_in_two / greenland camera, labels, and loop tail.

The production modules already live in map_engine_code/pr34_latest. This
script checks them. It does not rewrite episodes or sanitize render.py:
the pasted choreography (one snap from 19° to 4.8°) cannot pass the 60 fps
zoom ceiling, and the old regex sanitizer corrupts function signatures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


def resolve_repo_root() -> Path:
    cwd = Path.cwd()
    candidates = [
        cwd,
        cwd / "pr34_latest",
        cwd / "map_engine_code" / "pr34_latest",
        cwd.parent,
        cwd.parent.parent,
    ]
    for candidate in candidates:
        if (candidate / "pipeline" / "jt" / "show" / "episodes.py").exists():
            return candidate
    raise SystemExit(f"pipeline not found from {cwd}")


def main() -> None:
    root = resolve_repo_root()
    sys.path.insert(0, str(root / "pipeline"))
    from jt.loop_tail import apply_seamless_audio_loop_tail
    from jt.show.camera import MIN_SPAN_DEG, project_point_merc_ortho_blend
    from jt.show.episodes import build_cut_in_two_episode, build_greenland_episode
    from jt.show.labels import resolve_2d_label_collisions
    from jt.show.moves import check_event_pacing, check_moves

    print(f"=== JUICY TEA CHECK  root={root}  min_span={MIN_SPAN_DEG} ===")
    if MIN_SPAN_DEG > 3.2:
        raise SystemExit(f"MIN_SPAN_DEG is {MIN_SPAN_DEG}, expected 3.2")

    for builder in (build_cut_in_two_episode, build_greenland_episode):
        spec = builder()
        rig = spec.build_rig()
        motion = check_moves(rig, snap_intervals=spec.snap_intervals())
        events = check_event_pacing(
            spec.event_timestamps, spec.total_duration, spec.first_highlight_t
        )
        print(
            f"[VERIFIED 60FPS] '{spec.episode_id}': "
            f"min_span={min(m.span_end for m in spec.moves):.1f}°, "
            f"max_w={max(m.w_end for m in spec.moves):.2f}, "
            f"max_span_ratio={motion['max_span_ratio']}, "
            f"max_event_gap={events['max_event_gap_s']}s"
        )

    c0, c1 = resolve_2d_label_collisions([(500.0, 600.0, 220.0, 42.0), (505.0, 602.0, 220.0, 42.0)])
    if abs(c0[1] - c1[1]) < 40.0 and abs(c0[0] - c1[0]) < 40.0:
        raise SystemExit("Label collision solver failed")
    print("[VERIFIED] 2D label collision solver separated the overlapping boxes.")

    x, y, visible = project_point_merc_ortho_blend(110.0, 4.5, 110.0, 4.5, 20.0, 0.0)
    if abs(x - 540.0) > 2.0 or not visible:
        raise SystemExit(f"Mercator center projection failed: {x}, {y}, {visible}")
    print("[VERIFIED] Mercator/orthographic blend projects the camera center.")

    tone = np.zeros((48_000 * 3, 2), dtype=np.float64)
    tone[10_000:20_000, :] = 0.4
    out = apply_seamless_audio_loop_tail(tone, tail_overlap_s=0.25)
    if out.shape[0] != tone.shape[0]:
        raise SystemExit("loop_tail trimmed the timeline")
    if abs(out[40_000, 0]) > 1e-9:
        raise SystemExit("loop_tail rewrote audio past the head crossfade")
    print("[VERIFIED] loop_tail keeps the start of the timeline.")
    print(
        "Render: python3 map_engine_code/pr34_latest/pipeline/examples/cut_in_two/render_video.py"
    )


if __name__ == "__main__":
    main()
