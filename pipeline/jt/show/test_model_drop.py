"""Span cuts and the ratchet/ding cue list. No pixels."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.flyto import fly_lonlat, interpolate_zoom  # noqa: E402
from jt.show.moves import drop_in, ease_in, ease_out, ease_out_back, match_cut_dive  # noqa: E402
from jt.show.model_drop import (  # noqa: E402
    build_cues,
    hero_view_m,
    parse_spec,
    path_meters,
    progress,
    span_segments,
    tilt_deg,
    zoom_width,
)
import numpy as np  # noqa: E402

PELJE = [72, 96, 118, 203.5, 285, 285, 285, 285, 285, 203.5, 118, 96, 72]


def main() -> None:
    spec = parse_spec({
        "type": "model_drop",
        "asset": "parametric:cable_stayed",
        "geo": [[42.92178, 17.52797], [42.93964, 17.5438]],
        "scale": "stylized",
        "at_word": "NINETEEN",
        "build": "span_by_span",
        "kind": "cable_stayed",
        "spans_m": PELJE,
        "tower_after": [3, 4, 5, 6, 7, 8],
        "label": "13 SPANS · 2.4 KM",
    })
    assert spec.at_word == "NINETEEN"
    assert len(spec.spans_m) == 13
    xy = path_meters(spec.polyline)
    spans = span_segments(xy, spec.spans_m)
    assert len(spans) == 13
    total = sum(s["length_m"] for s in spans)
    length = float(np.hypot(*(xy[-1] - xy[0])))
    assert abs(total - length) < 2.0, (total, length)
    # The five main spans stay the long ones, in proportion.
    lengths = sorted(s["length_m"] for s in spans)
    assert lengths[-1] / lengths[0] > 3.0
    cues = build_cues(spec, 2.7, 3.4)
    ratchets = [c for c in cues if c["kind"] == "ratchet"]
    dings = [c for c in cues if c["kind"] == "ding"]
    assert len(ratchets) == 13
    assert len(dings) == 1
    assert dings[0]["t"] > ratchets[-1]["t"]
    assert progress(spec, 2.7, 2.7, 3.4)["spans_done"] == 0.0
    assert progress(spec, 7.0, 2.7, 3.4)["spans_done"] >= 13.0
    widths = [zoom_width(t, 0.3, 2.6, 1_400_000, 32_000) for t in (0.3, 1.0, 1.8, 2.6)]
    assert widths[0] > widths[1] > widths[2] > widths[3]
    assert abs(widths[-1] - 32_000) < 1.0
    assert tilt_deg(1.0, 2.2, 2.8, 6.6) == 0.0
    assert tilt_deg(4.0, 2.2, 2.8, 6.6) > 20.0
    assert tilt_deg(7.4, 2.2, 2.8, 6.6) < tilt_deg(4.0, 2.2, 2.8, 6.6)
    assert ease_out(0) == 0 and abs(ease_out(1) - 1) < 1e-6
    assert ease_in(0.5) < ease_out(0.5)
    assert ease_out_back(1) == 1.0
    assert drop_in(0.1, 0.1, 1.9)["blur"] > drop_in(1.8, 0.1, 1.9)["blur"]
    assert drop_in(0.0, 0.1, 1.9)["blur"] == 0.0
    assert drop_in(3.0, 0.1, 1.9)["blur"] == 0.0
    assert match_cut_dive(2.5, 1.9, 2.55)["blur"] > match_cut_dive(2.0, 1.9, 2.55)["blur"]
    assert match_cut_dive(4.0, 1.9, 2.55)["blur"] == 0.0
    view = hero_view_m(spec, 0.60)
    assert 3_000 < view < 6_000, view
    # d3 interpolateZoom, pure zoom: the halfway frame is the geometric mean width.
    pure = interpolate_zoom((0.0, 0.0, 1_000_000.0), (0.0, 0.0, 10_000.0))
    assert abs(pure(0.0)[2] - 1_000_000.0) < 1.0
    assert abs(pure(1.0)[2] - 10_000.0) < 1.0
    assert abs(pure(0.5)[2] - math.sqrt(1_000_000.0 * 10_000.0)) < 50.0
    # A long pan pulls the path wider than a straight log zoom, which is the flyTo arc.
    arc = interpolate_zoom((0.0, 0.0, 400_000.0), (500_000.0, 0.0, 400_000.0), rho=1.42)
    straight = 400_000.0
    assert arc(0.5)[2] > straight * 1.2
    assert abs(arc(1.0)[0] - 500_000.0) < 1.0
    lon, lat, width = fly_lonlat(1.0, 114.0, 2.6, 1_500_000.0, 115.07, 4.90, 80_000.0)
    assert abs(lon - 115.07) < 1e-4 and abs(lat - 4.90) < 1e-4
    assert abs(width - 80_000.0) / 80_000.0 < 1e-4
    print("model_drop tests ok", f"{len(spans)} spans", f"{len(ratchets)} ratchets", f"hero {view:.0f} m")


if __name__ == "__main__":
    main()
