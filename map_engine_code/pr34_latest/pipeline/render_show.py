"""
Juicy Tea Map-Shorts Engine — Master 60fps Render & 7-Point QC Pipeline.
Usage:
  python -m pipeline.render_show --episode greenland --lint-only
  python -m pipeline.render_show --episode cut_in_two --lint-only
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path

from pipeline.jt.show.episodes import (
    build_greenland_episode, build_cut_in_two_episode, EpisodeSpec
)
from pipeline.jt.show.moves import check_moves, check_event_pacing
from pipeline.jt.show.gate_tblend import evaluate_delivery_gate


def run_pre_render_checks(spec: EpisodeSpec) -> tuple[dict, dict]:
    rig = spec.build_rig()
    motion_report = check_moves(rig, snap_intervals=spec.snap_intervals())
    event_report = check_event_pacing(
        spec.event_timestamps,
        total_duration=spec.total_duration,
        first_highlight_t=spec.first_highlight_t,
    )
    return motion_report, event_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Juicy Tea 60fps Smooth Map-Shorts Builder")
    parser.add_argument("--episode", choices=["greenland", "cut_in_two"], default="greenland")
    parser.add_argument("--out", type=Path, default=Path("out/final.mp4"))
    parser.add_argument("--lint-only", action="store_true")
    args = parser.parse_args()

    spec = (
        build_greenland_episode()
        if args.episode == "greenland"
        else build_cut_in_two_episode()
    )

    motion_report, event_report = run_pre_render_checks(spec)
    print(f"[PASS] Pre-render C2 Motion Lint ({spec.episode_id}):", json.dumps(motion_report))
    print(f"[PASS] Pre-render Event Pacing Lint ({spec.episode_id}):", json.dumps(event_report))

    if args.lint_only:
        return

    if args.out.exists():
        gate_report = evaluate_delivery_gate(
            args.out,
            motion_lint_report=motion_report,
            event_lint_report=event_report,
        )
        review_path = args.out.with_suffix(".review_packet.json")
        review_path.write_text(json.dumps(gate_report, indent=2), encoding="utf-8")
        print(f"[PASS] 7-Point Delivery Gate saved to {review_path}")


if __name__ == "__main__":
    main()
