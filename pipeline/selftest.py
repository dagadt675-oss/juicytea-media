#!/usr/bin/env python3
"""Fast checks that do not render a full video."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jt.captions import active_index, groups_for, switch_error  # noqa: E402
from jt.project import laea_forward, laea_inverse, project_one, project_points, resolve, route_lonlat  # noqa: E402
from jt.render import _reversals, direction_changes  # noqa: E402
from jt.spec import load_spec, pause_problems, silent_timeline  # noqa: E402


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

    pac = resolve("merc", -170, 42, 132, 1080, 1920)
    nrt = project_one(140.3929, 35.7720, pac)
    lax = project_one(-118.4081, 33.9425, pac)
    ok &= check("pacific pins", nrt is not None and lax is not None and nrt[0] < pac.cx < lax[0], f"{nrt} {lax}")

    great = route_lonlat("great", 33.9425, -118.4081, 35.7720, 140.3929, 181)
    rhumb = route_lonlat("rhumb", 33.9425, -118.4081, 35.7720, 140.3929, 61)
    crest = max(great, key=lambda p: p[1])
    ok &= check("gc crest", 47.4 <= crest[1] <= 48.0 and -172.0 <= crest[0] <= -169.0, f"{crest[1]:.2f}N {crest[0]:.2f}")
    ok &= check("arc north of rhumb", crest[1] > max(p[1] for p in rhumb) + 8.0, f"{crest[1]:.2f}")
    lons = np.array([p[0] for p in rhumb])
    lats = np.array([p[1] for p in rhumb])
    x, y, vis = project_points(lons, lats, pac)
    chord = np.abs((y[-1] - y[0]) * x - (x[-1] - x[0]) * y + x[-1] * y[0] - y[-1] * x[0])
    dev = float(chord.max() / max(math.hypot(x[-1] - x[0], y[-1] - y[0]), 1.0))
    ok &= check("rhumb straight on mercator", bool(np.all(vis)) and dev < 2.0, f"{dev:.2f}px")

    route = load_spec(Path(__file__).resolve().parent / "specs" / "lax_tokyo.yaml")
    clock = silent_timeline(route)
    starts = [ln["start"] for ln in clock["beats"]]
    want_starts = [0.03, 3.93, 7.24, 8.14, 10.81, 14.28, 20.25, 23.05]
    ok &= check("eight silent beats", len(clock["beats"]) == 8 and clock["words"] == [], str(len(clock["beats"])))
    ok &= check("voice length", abs(clock["duration"] - 24.2) < 0.02, str(clock["duration"]))
    ok &= check("sentence starts", starts == want_starts, str(starts))
    joined = " ".join(ln["say"] for ln in clock["beats"])
    low = joined.lower()
    ok &= check(
        "us script",
        joined.startswith("Your flight from LA to Tokyo curves up toward Alaska.")
        and "three hundred miles shorter" in low
        and "great circle that bends north" in low
        and "it's not a mistake" in low
        and "over alaska" not in low
        and "exactly the great circle" not in low
        and "hundreds of kilometers" not in low,
        joined[:90],
    )
    pills = []
    for ln in route.lines:
        for vis in ln.visuals:
            if vis.get("type") in ("tag", "callout"):
                pills.append(f"{vis.get('text', '')} {vis.get('sub', '')}".strip())
    blob = " | ".join(pills)
    ok &= check("lie pill", "YOUR MAP IS LYING" in blob, blob)
    ok &= check("payoff pill", "≈300 MI SHORTER" in blob and "480 KM" in blob, blob)
    ok &= check("no alaska overclaim", "OVER ALASKA" not in blob.upper() and "TOWARD ALASKA" not in blob.upper(), blob)
    reveal = next(ln for ln in route.lines if "bends north" in ln.say)
    modes = [v.get("mode") for v in reveal.visuals if v.get("type") == "route"]
    morph = next(v for v in reveal.visuals if v.get("mode") == "morph")
    ok &= check("arc lifts off the rhumb", modes == ["rhumb", "morph"], str(modes))
    ok &= check(
        "bend covers bends-north",
        float(morph["bend_at"]) <= 19.114 <= float(morph["bend_end"])
        and float(morph["bend_at"]) <= 19.415 <= float(morph["bend_end"]),
        f"{morph['bend_at']}–{morph['bend_end']}",
    )
    payoff = next(v for v in route.lines[1].visuals if v.get("type") == "callout")
    # "three" starts at 5.488 in words.json. The spring begins just before that.
    ok &= check("pill lands on the miles", 5.20 <= float(payoff["at"]) <= 5.488, str(payoff["at"]))
    opening_route = next(v for v in route.lines[0].visuals if v.get("type") == "route")
    ok &= check("opening arc is already drawing", float(opening_route.get("from", 0)) >= 0.4)
    from jt.loop_tail import tail_progress
    samples = [tail_progress(23.85 + i * 0.03, 23.85, 24.1667) for i in range(12)]
    ok &= check(
        "loop tail is one direction",
        samples[0] == 0.0 and samples[-1] == 1.0 and all(b >= a for a, b in zip(samples, samples[1:])),
        str([round(s, 3) for s in samples]),
    )
    turns = direction_changes(route, clock, 1080, 1920)
    ok &= check("no camera sway", turns == 0, str(turns))
    alaska_clock = {"duration": 2.0 * len(spec.lines), "words": [],
                    "lines": [{"start": 2.0 * i} for i in range(len(spec.lines))]}
    alaska_turns = direction_changes(spec, alaska_clock, 1080, 1920)
    ok &= check("alaska camera does not sway", alaska_turns <= 1, str(alaska_turns))
    ok &= check("one ease is not a sway", _reversals([0, 1, 2, 3, 3], 0.02) <= 1)
    ok &= check(
        "oscillation fails the gate",
        _reversals([0, 1, 2, 1, 0, 1], 0.02) > 1,
        str(_reversals([0, 1, 2, 1, 0, 1], 0.02)),
    )

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
