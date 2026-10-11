#!/usr/bin/env python3
"""Re-render only the Greenland stretches that changed, then splice.

    python3 render_segments.py

Quiet snap: 11.20–12.50 s. Sticker drag: just before the pickup through the
landing ripple. Everything else is decoded from the previous master.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from jt.show.greenland import CLOCK, FPS, N, Greenland, cue_payload  # noqa: E402
from jt.show.qa import motion_per_second, report, write_report  # noqa: E402
from jt.show.segments import render_range, splice  # noqa: E402

OUT = ROOT / "examples" / "greenland"
MASTER = OUT / "greenland_africa_polished.mp4"
DEST = OUT / "greenland_africa_polished_v2.mp4"


def main() -> None:
    q0 = int(round(11.20 * FPS))
    q1 = int(round(12.50 * FPS))
    d0 = int(math.floor((CLOCK.drag - 0.12) * FPS))
    d1 = int(math.floor((CLOCK.drop + 0.46) * FPS)) + 1
    print(f"quiet {q0}:{q1} drag {d0}:{d1} N {N}", flush=True)
    if not (0 <= q0 < q1 <= d0 < d1 <= N):
        raise SystemExit(f"bad ranges {q0} {q1} {d0} {d1}")
    show = Greenland()
    quiet = render_range(show, q0, q1)
    drag = render_range(show, d0, d1)
    pieces = [
        (0, q0, None),
        (q0, q1, quiet),
        (q1, d0, None),
        (d0, d1, drag),
        (d1, N, None),
    ]
    splice(MASTER, pieces, DEST, N)
    cues = cue_payload()
    (OUT / "greenland_cues.json").write_text(json.dumps(cues, indent=2) + "\n", encoding="utf-8")
    qa = report(DEST, cues["cues"])
    write_report(OUT / "qa.json", qa)
    motion = motion_per_second(DEST)
    write_report(OUT / "motion_per_second.json", motion)
    print(json.dumps({
        "structural_motion_mean": qa.get("structural_motion_mean"),
        "structural_event_gap_max": qa.get("structural_event_gap_max"),
        "structural_gaps_over_2_5s": qa.get("structural_gaps_over_2_5s"),
        "structural_pass": qa.get("structural_pass"),
        "motion_mean": motion.get("motion_mean"),
        "seconds_under_1": motion.get("seconds_under_1"),
        "pass": qa.get("pass"),
    }, indent=2))


if __name__ == "__main__":
    main()
