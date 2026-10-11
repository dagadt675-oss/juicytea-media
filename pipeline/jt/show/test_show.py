"""Clock, Mercator scale, cue gaps, and the loop pose. No pixels required."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.camera import CameraTrack  # noqa: E402
from jt.show.pack import layout  # noqa: E402
from jt.show.cues import lint_gaps, pack  # noqa: E402
from jt.show.faces import gag_pose  # noqa: E402
from jt.show.greenland import (  # noqa: E402
    CUES,
    DURATION,
    N,
    TAIL0,
    TAIL1,
    _keys,
    lat_for_display,
    pose,
)
from jt.show.truesize import area_factor, linear_factor, reproject_true  # noqa: E402
import numpy as np  # noqa: E402


def main() -> None:
    # sec(70°) ≈ 2.92 linear, ≈ 8.5 area. The pill rounds that to ~3× and ~9×.
    assert abs(linear_factor(70) - 2.924) < 0.01
    assert abs(area_factor(70) - 8.55) < 0.05
    assert abs(lat_for_display(16) - 74.32) < 0.15
    assert lat_for_display(1) < 0.2
    ring = np.array([[-50.0, 74.0], [-30.0, 74.0], [-30.0, 78.0], [-50.0, 74.0]])
    home = reproject_true(ring, -40.0, 74.0, -40.0, 74.0)
    equ = reproject_true(ring, -40.0, 74.0, 10.0, 0.0)
    assert abs(abs(home[1, 0] - home[0, 0]) - 20.0) < 0.5
    assert abs(equ[1, 0] - equ[0, 0]) < 7.0

    open_pose = pose(0.0)
    end_pose = pose(TAIL1)
    for key in ("lying", "detached", "dlon", "dlat", "disp", "same", "tiles", "compare"):
        assert abs(open_pose[key] - end_pose[key]) < 1e-6, key
    assert open_pose["lying"] == 1.0
    assert open_pose["disp"] == 16.0
    assert pose(12.80)["disp"] == 16.0
    from jt.show.greenland import CLOCK, scale_report
    report = scale_report()
    assert report["pass"], report
    assert abs(pose(CLOCK.drag)["disp"] - 16.0) < 0.05
    assert pose(CLOCK.drop)["disp"] < 2.2

    mouth, bob = gag_pose(4.60, 4.442, 5.022, 2)
    assert mouth > 0.4 and bob > 0.0
    assert gag_pose(6.0, 4.442, 5.022, 2) == (0.0, 0.0)
    assert gag_pose(21.2, 21.013, 21.803, 2)[0] > 0.2
    assert gag_pose(29.4, 29.245, 29.800, 2)[0] > 0.2

    cues = pack(CUES)
    names = {row["name"] for row in cues}
    assert "snap-punch" not in names
    assert "open" in names and "lying" in names
    # Quiet stretches are allowed. Do not invent cues to fill them.
    worst, _bad = lint_gaps(cues, DURATION, 2.0)
    assert cues == sorted(cues, key=lambda row: (row["t"], row["name"]))

    track = CameraTrack(_keys(), TAIL0, TAIL1)
    a = track.at(0.0).front()
    pre = track.at(TAIL1).front()
    nxt = track.at(1.0 / 30.0).front()
    assert a.proj == pre.proj == nxt.proj == "merc"
    # Last frame is one opening step before frame 0, so last→first matches first→second.
    assert abs((a.span - pre.span) - (nxt.span - a.span)) < 1e-6
    assert abs((a.lat - pre.lat) - (nxt.lat - a.lat)) < 1e-6
    assert abs(a.span - pre.span) > 1e-3
    mid = track.at((TAIL0 + TAIL1) / 2).front()
    assert mid.proj == "merc"
    # Two blocks fit inside a field without overlap. Four fat blocks do not.
    field = np.zeros((40, 40), np.bool_)
    field[2:38, 2:38] = True
    block = np.zeros((10, 10), np.bool_)
    block[1:9, 1:9] = True
    items = [(name, [(0.0, block, 5.0, 5.0)]) for name in ("a", "b")]
    mode, placed = layout(field, items, {"a": (10, 10), "b": (28, 28)})
    assert mode == "fit" and set(placed) == {"a", "b"}
    fat = np.ones((24, 24), np.bool_)
    crowded = [(name, [(0.0, fat, 12.0, 12.0)]) for name in ("a", "b", "c", "d")]
    mode, placed = layout(field, crowded, {n: (20, 20) for n in "abcd"})
    assert mode == "overlap" and len(placed) == 4
    assert N >= 1357
    assert abs(DURATION - N / 30) < 1e-9
    assert abs(TAIL1 - (N - 1) / 30) < 1e-9
    print("show tests ok", f"cue gap {worst:.2f}s", f"{N} frames")


if __name__ == "__main__":
    main()
