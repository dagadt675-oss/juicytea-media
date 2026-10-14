#!/usr/bin/env python3
"""No second copy of a country during the projection morph.

Two overlapping fills become one connected region, so the mask is the
coastline of each ring (a stroke of that same path). A ghost framing is a
second large coastline of one ring. A component counts when it is at least
30% of that ring's longest coastline and at least 80 pixels on the
downscale. The canvas has a margin so a coast that leaves the frame and
comes back is still one loop.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import skia
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.greenland import AFRICA  # noqa: E402
from jt.show.greenland_v5 import (  # noqa: E402
    H,
    T_LAST,
    W,
    Episode,
    _globe_mix,
    _smooth,
    camera_blend,
    camera_channels,
)

SCALE = 0.28
SW, SH = int(W * SCALE), int(H * SCALE)
# Margin so a coast that leaves the frame and comes back stays one loop.
PAD = 100


def _large(mask: np.ndarray) -> list[int]:
    tagged, n = label(mask)
    if n == 0:
        return []
    areas = np.bincount(tagged.ravel())[1:]
    areas = areas[areas > 0]
    if areas.size == 0:
        return []
    biggest = int(areas.max())
    if biggest < 80:
        return []
    keep = areas[areas >= max(80, int(0.30 * biggest))]
    return sorted((int(a) for a in keep), reverse=True)


def _mask(ep: Episode, rings, s: float) -> np.ndarray:
    surf = skia.Surface(SW + 2 * PAD, SH + 2 * PAD)
    canvas = surf.getCanvas()
    canvas.scale(SW / W, SH / H)
    canvas.translate(PAD / (SW / W), PAD / (SH / H))
    paint = skia.Paint(AntiAlias=False, Style=skia.Paint.kStroke_Style)
    paint.setStrokeWidth(2.5 / (SW / W))
    paint.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    canvas.drawPath(ep._blend_path(rings, s), paint)
    arr = surf.makeImageSnapshot().toarray()
    return arr[:, :, 3] > 40


def check_time(ep: Episode, t: float, countries: dict[str, list]) -> list[str]:
    merc, ortho, w = camera_blend(t)
    ep._merc, ep._ortho, ep._pw = merc, ortho, w
    s = _smooth(w)
    fails = []
    for iso, rings in countries.items():
        if not rings:
            continue
        for index, ring in enumerate(rings):
            got = _large(_mask(ep, [ring], s))
            if len(got) >= 2:
                fails.append(f"{iso} ring {index} t={t:.3f} large={got}")
    return fails


def morph_times() -> list[float]:
    """Every 0.1 s of a projection blend or a plate LoD blend, for the whole film."""
    times = []
    t = 0.0
    while t <= T_LAST + 1e-9:
        w, _lon, _lat, span = camera_channels(t)
        mix = _globe_mix(span)
        if 0.004 < w < 0.996 or 0.02 < mix < 0.98:
            times.append(round(t, 3))
        t += 0.1
    return times


def main() -> None:
    ep = Episode()
    countries = {"GRL": ep.earth.rings.get("GRL") or []}
    for iso in AFRICA:
        rings = ep.earth.rings.get(iso) or []
        if rings:
            countries[iso] = rings
    fails = []
    for t in morph_times():
        fails.extend(check_time(ep, t, countries))
        w, _lon, _lat, span = camera_channels(t)
        print(
            f"t {t:.3f} w {w:.3f} span {span:.1f} mix {_globe_mix(span):.2f} fails {len(fails)}",
            flush=True,
        )
    print(f"samples {len(morph_times())} fails {len(fails)} pass {not fails}")
    for row in fails[:40]:
        print(" ", row)
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
