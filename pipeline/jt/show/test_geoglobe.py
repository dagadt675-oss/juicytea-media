"""Beat types, cue gaps, and the loop step. One frame per feature."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.cues import lint_gaps  # noqa: E402
from jt.show.geoglobe import (  # noqa: E402
    Episode,
    cue_list,
    draw_countryball,
    draw_film_wipe,
    draw_lighthouse,
    draw_skit,
    draw_stamp,
    draw_strike,
    load_episode,
    loop_step_ok,
)
import skia  # noqa: E402

SPEC = ROOT / "examples" / "market" / "market.json"


def _blank():
    surface = skia.Surface(320, 180)
    return surface


def main() -> None:
    spec = load_episode(SPEC)
    assert 15.0 <= spec["duration"] <= 25.0
    cues = cue_list(spec)
    worst, bad = lint_gaps(cues, spec["duration"], 2.0)
    assert not bad, bad
    show = Episode(spec)
    assert loop_step_ok(show), "loop step"
    frame = show.render(0.8)
    assert frame.shape == (1920, 1080, 3)
    # The other beat types draw without a map underneath.
    surface = _blank()
    canvas = surface.getCanvas()
    draw_countryball(canvas, {"x": 80, "y": 90, "flag": "se", "hat": "viking", "action": "vibrate", "color": [0, 82, 147]}, 0.4)
    draw_stamp(canvas, "NONSTOP", 200, 40, 0.4)
    draw_strike(canvas, "70K", 200, 120, 0.5)
    draw_skit(canvas, 0.4, 2.0)
    draw_film_wipe(canvas, 0.4)
    draw_lighthouse(canvas, 40, 160, 50)
    draw_countryball(canvas, {"x": 160, "y": 90, "action": "army", "flag": "fi", "color": [0, 80, 160]}, 0.5)
    print("geoglobe tests ok", f"cue gap {worst:.2f}s", f"{show.frames} frames")


if __name__ == "__main__":
    main()
