"""Camera timing for the rebuilt Greenland episode. No pixels."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.greenland_v5 import (  # noqa: E402
    D_LOOP,
    D_SLIDE,
    MOVES,
    T_LAST,
    camera_at,
    check_moves,
)


def test_moves_hold_and_loop():
    check_moves()
    slide = next(m for m in MOVES if m.name == "slide")
    loop = next(m for m in MOVES if m.name == "loop")
    assert slide.dur == D_SLIDE
    assert loop.dur == D_LOOP
    # The camera keeps travelling. A nominal hold is a slow drift, not a stop.
    a = camera_at(2.40)
    b = camera_at(2.70)
    assert a.proj == b.proj == "merc"
    assert abs(a.span - b.span) > 1e-3 or abs(a.lon - b.lon) > 1e-3 or abs(a.lat - b.lat) > 1e-3
