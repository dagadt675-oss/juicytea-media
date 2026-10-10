#!/usr/bin/env python3
"""Fast checks that do not render a full video."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jt.captions import active_index, groups_for, switch_error  # noqa: E402
from jt.project import laea_forward, laea_inverse, project_one, resolve  # noqa: E402
from jt.spec import load_spec, pause_problems  # noqa: E402


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" — " + detail if detail else ""))
    return ok


def main() -> int:
    ok = True
    words = [
        {"text": "Which", "start": 0.10, "end": 0.30},
        {"text": "US", "start": 0.30, "end": 0.50},
        {"text": "state", "start": 0.50, "end": 0.80},
        {"text": "EAST?", "start": 0.80, "end": 1.20, "keyword": True},
    ]
    groups = groups_for(words)
    ok &= check("groups of three then punct", groups == [[0, 1, 2], [3]], str(groups))
    # Highlight appears 0.04 s before the word.
    ok &= check("early highlight", active_index(words, 0.80 - 0.04) == 3)
    ok &= check("not early by 0.2s", active_index(words, 0.80 - 0.20) == 2)
    err = switch_error(words)
    ok &= check("switch within 0.1s", err <= 0.10, f"{err:.3f}")

    spec = load_spec(Path(__file__).resolve().parent / "specs" / "alaska.yaml")
    ok &= check("alaska pauses", pause_problems(spec) == [], str(pause_problems(spec)))
    ok &= check("loop camera", spec.lines[0].camera.__dict__ == spec.lines[-1].camera.__dict__)

    view = resolve("ortho", -98, 43, 70, 1080, 1920)
    hit = project_one(-98, 43, view)
    ok &= check("ortho centre", hit is not None and abs(hit[0] - view.cx) < 1 and abs(hit[1] - view.cy) < 1, str(hit))

    lon, lat = 10.0, 48.0
    x, y = laea_forward([lon], [lat], lon, lat)
    lon2, lat2 = laea_inverse(x, y, lon, lat)
    ok &= check("laea roundtrip", abs(float(lon2[0]) - lon) < 1e-4 and abs(float(lat2[0]) - lat) < 1e-4,
                f"{float(lon2[0]):.4f},{float(lat2[0]):.4f}")

    # A point 10 degrees east of centre should land to the right.
    hit_e = project_one(-88, 43, view)
    ok &= check("ortho east", hit_e is not None and hit_e[0] > view.cx, str(hit_e))

    flat = resolve("merc", 0, 0, 40, 1080, 1920)
    origin = project_one(0, 0, flat)
    ok &= check("merc origin", origin is not None and abs(origin[0] - flat.cx) < 1.5, str(origin))

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
