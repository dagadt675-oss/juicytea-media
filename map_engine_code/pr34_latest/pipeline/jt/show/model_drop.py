"""Zoom-to-spot and a 3D model drop-in, driven by one spec entry.

A show names a real thing at a place. The camera eases to that ground, tilts
a little, and the model builds there in the map palette. Bridges are a
parametric kit (beam, cable-stayed, suspension) that follows a polyline.
The polyline is the caller's. This module does not fetch OSM.

Hub check for these proofs: the library has Kenney and Quaternius street
bridges and footbridges, and private landmark meshes (Empire State, One WTC,
Liberty, Queen Mary). None of those is a sea crossing, so the kit is used.

Spec::

    {type: model_drop, asset: <hub id or library path or "parametric:...">,
     geo: [lat, lon] or [[lat, lon], ...], scale: true|stylized,
     heading, at_word, build: extrude|span_by_span|drop|fly_in,
     kind: beam|cable_stayed|suspension, spans_m: [...], label: str}
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import skia

from jt.show.cues import pack as pack_cues
from jt.show.flyto import fly_lonlat
from jt.show.moves import ease_out_back


@dataclass
class ModelDrop:
    asset: str
    geo: list
    scale: str = "stylized"
    heading: float | None = None
    at_word: str | None = None
    build: str = "span_by_span"
    kind: str = "beam"
    spans_m: list[float] = field(default_factory=list)
    deck_m: float = 24.0
    tower_m: float = 100.0
    label: str | None = None
    # Stations, in span index, that carry a tower (cable-stayed or suspension).
    tower_after: list[int] = field(default_factory=list)

    @property
    def polyline(self) -> list[tuple[float, float]]:
        if not self.geo:
            return []
        if isinstance(self.geo[0], (int, float)):
            return [(float(self.geo[0]), float(self.geo[1]))]
        return [(float(p[0]), float(p[1])) for p in self.geo]


def parse_spec(raw: dict) -> ModelDrop:
    if raw.get("type") not in (None, "model_drop"):
        raise ValueError(f"not a model_drop spec: {raw.get('type')}")
    spans = [float(s) for s in raw.get("spans_m") or []]
    towers = [int(i) for i in raw.get("tower_after") or []]
    return ModelDrop(
        asset=str(raw.get("asset") or "parametric:beam"),
        geo=list(raw.get("geo") or []),
        scale=str(raw.get("scale") or "stylized"),
        heading=None if raw.get("heading") is None else float(raw["heading"]),
        at_word=raw.get("at_word"),
        build=str(raw.get("build") or "span_by_span"),
        kind=str(raw.get("kind") or "beam"),
        spans_m=spans,
        deck_m=float(raw.get("deck_m") or 24.0),
        tower_m=float(raw.get("tower_m") or 100.0),
        label=raw.get("label"),
        tower_after=towers,
    )


def _smooth(x: float) -> float:
    x = 0.0 if x < 0.0 else 1.0 if x > 1.0 else x
    return x * x * (3.0 - 2.0 * x)


def path_meters(latlon: list[tuple[float, float]]) -> np.ndarray:
    """Local east/north meters. Row 0 is the first vertex."""
    if len(latlon) == 1:
        return np.zeros((1, 2), np.float64)
    arr = np.asarray(latlon, np.float64)
    lat0 = float(arr[:, 0].mean())
    lon0 = float(arr[:, 1].mean())
    east = np.radians(arr[:, 1] - lon0) * 6378137.0 * math.cos(math.radians(lat0))
    north = np.radians(arr[:, 0] - lat0) * 6378137.0
    return np.stack([east, north], 1)


def _resample(xy: np.ndarray, count: int = 64) -> np.ndarray:
    if len(xy) < 2:
        return xy
    step = np.hypot(np.diff(xy[:, 0]), np.diff(xy[:, 1]))
    cum = np.concatenate([[0.0], np.cumsum(step)])
    total = float(cum[-1]) or 1.0
    targets = np.linspace(0.0, total, count)
    x = np.interp(targets, cum, xy[:, 0])
    y = np.interp(targets, cum, xy[:, 1])
    return np.stack([x, y], 1)


def span_segments(xy: np.ndarray, lengths: list[float]) -> list[dict]:
    """Cut the path into spans. Lengths are scaled so they fill the path."""
    if len(xy) < 2:
        return []
    step = np.hypot(np.diff(xy[:, 0]), np.diff(xy[:, 1]))
    cum = np.concatenate([[0.0], np.cumsum(step)])
    total = float(cum[-1])
    if not lengths:
        lengths = [total]
    scale = total / sum(lengths) if sum(lengths) else 1.0
    cuts = [0.0]
    acc = 0.0
    for length in lengths:
        acc += length * scale
        cuts.append(min(total, acc))
    cuts[-1] = total
    out = []
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        if b <= a + 0.5:
            continue
        pa = np.array([np.interp(a, cum, xy[:, 0]), np.interp(a, cum, xy[:, 1])])
        pb = np.array([np.interp(b, cum, xy[:, 0]), np.interp(b, cum, xy[:, 1])])
        out.append({
            "index": len(out),
            "a": pa,
            "b": pb,
            "along0": a,
            "along1": b,
            "length_m": b - a,
        })
    return out


def schedule(spec: ModelDrop, t0: float, dur: float) -> list[dict]:
    """When each span starts. The last one finishes at t0+dur."""
    xy = _resample(path_meters(spec.polyline), 128)
    spans = span_segments(xy, spec.spans_m)
    n = max(1, len(spans))
    times = []
    for i, span in enumerate(spans):
        u = i / n
        # Slight acceleration, still readable.
        start = t0 + dur * (u ** 0.85)
        times.append({**span, "t": start})
    return times


def build_cues(spec: ModelDrop, t0: float, dur: float) -> list[dict]:
    """Ratchet as each span starts, ding when the last one lands, whoosh on the zoom."""
    rows = [(max(0.0, t0 - 0.4), "whoosh", "zoom-to-spot")]
    spans = schedule(spec, t0, dur)
    for span in spans:
        rows.append((span["t"], "ratchet", f"span-{span['index'] + 1}"))
    if spans:
        rows.append((spans[-1]["t"] + dur / max(1, len(spans)) * 0.85, "ding", "build-done"))
    return pack_cues(rows)


def progress(spec: ModelDrop, t: float, t0: float, dur: float) -> dict:
    """How much of the model is up at time t. spans_done is a float."""
    spans = schedule(spec, t0, dur)
    n = max(1, len(spans))
    if t <= t0:
        done = 0.0
    elif spec.build == "drop":
        done = n * _smooth((t - t0) / dur)
    elif spec.build == "fly_in":
        done = n * _smooth((t - t0) / dur)
    elif spec.build == "extrude":
        done = n * _smooth((t - t0) / dur)
    else:
        done = 0.0
        slot = dur / n
        for i, span in enumerate(spans):
            age = t - span["t"]
            if age >= slot:
                done = i + 1.0
            elif age > 0:
                # Ease-out-back: the span overshoots as it lands, then sits.
                done = i + ease_out_back(age / slot)
                break
        else:
            if t >= spans[-1]["t"]:
                done = float(n)
    fly = 0.0
    if spec.build == "fly_in":
        fly = 1.0 - _smooth((t - t0) / min(0.6, dur))
    drop = 0.0
    if spec.build == "drop":
        u = _smooth((t - t0) / min(0.45, dur))
        drop = (1.0 - u) * 1.15
    return {"spans_done": done, "span_count": n, "fly": fly, "drop": drop, "spans": spans}


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.hypot(v[0], v[1])) or 1.0
    return v / n


def _project_point(project, east: float, north: float, up: float):
    return project(east, north, up)


def hero_view_m(spec: ModelDrop, fraction: float = 0.60) -> float:
    """Ground width that puts the bridge across `fraction` of the frame.

    The chord is measured along the bridge, which the camera lays left to right.
    """
    xy = path_meters(spec.polyline)
    if len(xy) < 2:
        return 8_000.0
    delta = xy[-1] - xy[0]
    heading = math.atan2(float(delta[1]), float(delta[0]))
    c, s = math.cos(heading), math.sin(heading)
    along = xy[:, 0] * c + xy[:, 1] * s
    extent = float(along.max() - along.min()) or 1.0
    return extent / fraction


def bridge_heading(spec: ModelDrop) -> float:
    """Radians from east toward north, so the chord runs left to right."""
    xy = path_meters(spec.polyline)
    if len(xy) < 2:
        return 0.0
    delta = xy[-1] - xy[0]
    return math.atan2(float(delta[1]), float(delta[0]))


def draw(canvas, spec: ModelDrop, state: dict, project, view_m: float, frame_w: float, tilt: float = 30.0) -> None:
    """Low-poly bridge. Each span drops in whole, then its pier and, where asked, a pylon."""
    spans = state["spans"]
    done = float(state["spans_done"])
    if not spans or done <= 0.02:
        return
    gsd = view_m / max(1.0, frame_w)
    sin_t = max(0.35, math.sin(math.radians(max(18.0, tilt))))
    if spec.scale == "stylized":
        # Screen-space targets, so a hero framing reads as a model rather than a stroke.
        deck_m = max(spec.deck_m, 22.0 * gsd / sin_t)
        thick_m = max(spec.deck_m * 0.45, 18.0 * gsd / sin_t)
        tower_m = max(spec.tower_m, 78.0 * gsd / sin_t)
    else:
        deck_m = spec.deck_m
        thick_m = max(6.0, spec.deck_m * 0.22)
        tower_m = spec.tower_m
    deck_z = thick_m * 0.15
    length = sum(s["length_m"] for s in spans) or 1.0

    def P(pt, up):
        return _project_point(project, float(pt[0]), float(pt[1]), up)

    for span in spans:
        frac = _span_frac(done, span["index"])
        if frac <= 0.04:
            continue
        _span_model(canvas, spec, span, spans, frac, deck_m, thick_m, tower_m, deck_z, length, P)


def _span_frac(done: float, index: int) -> float:
    if done >= index + 1.25:
        return 1.0
    if done <= index:
        return 0.0
    return done - index


def _quad(canvas, corners, paint) -> None:
    if any(c is None for c in corners):
        return
    path = skia.Path()
    path.moveTo(corners[0][0], corners[0][1])
    for x, y in corners[1:]:
        path.lineTo(x, y)
    path.close()
    canvas.drawPath(path, paint)


def _ends(span, frac: float) -> tuple[np.ndarray, np.ndarray]:
    """Whole span, slightly shortened so the pieces read as separate drops."""
    gap = 0.045
    a = span["a"] * (1 - gap) + span["b"] * gap
    b = span["b"] * (1 - gap) + span["a"] * gap
    # A span that is still dropping is fully formed; frac only sets the height.
    _ = frac
    return a, b


def _drop_z(frac: float, tower_m: float) -> float:
    if frac >= 1.0:
        # The ease-out-back overshoot presses the span into the water, then releases.
        return -min(0.18, frac - 1.0) * tower_m * 0.35
    u = max(0.0, frac)
    return (1.0 - u) ** 2 * tower_m * 1.35


def _span_model(canvas, spec, span, spans, frac, deck_m, thick, tower_m, deck_z, length, project) -> None:
    a, b = _ends(span, frac)
    z_off = _drop_z(frac, tower_m)
    squash = 1.0
    if frac > 0.72:
        w = math.sin(math.pi * min(1.0, (frac - 0.72) / 0.28))
        squash = 1.0 - 0.16 * w
    top_z = deck_z + z_off + thick * squash
    bot_z = deck_z + z_off
    direction = _unit(b - a)
    side = np.array([-direction[1], direction[0]])
    half = side * (deck_m / 2)
    # Shadow on the water, wider than the deck.
    shade = skia.Paint(AntiAlias=True)
    shade.setColor(skia.ColorSetARGB(70, 10, 16, 28))
    shade.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12))
    _quad(canvas, [
        project(a + half * 1.35, 1.0), project(b + half * 1.35, 1.0),
        project(b - half * 1.35, 1.0), project(a - half * 1.35, 1.0),
    ], shade)
    side_paint = skia.Paint(AntiAlias=True)
    side_paint.setColor(skia.ColorSetARGB(255, 176, 186, 196))
    top_paint = skia.Paint(AntiAlias=True)
    top_paint.setColor(skia.ColorSetARGB(255, 246, 244, 236))
    edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4.0)
    edge.setColor(skia.ColorSetARGB(255, 22, 28, 36))
    rim = skia.Paint(AntiAlias=True)
    rim.setColor(skia.ColorSetARGB(255, 255, 252, 244))
    # Side faces, then the roadway, then a light rim on the near edge.
    corners_bot = [a + half, b + half, b - half, a - half]
    corners_top = corners_bot
    for i in range(4):
        p = corners_bot[i]
        q = corners_bot[(i + 1) % 4]
        _quad(canvas, [project(p, bot_z), project(q, bot_z), project(q, top_z), project(p, top_z)], side_paint)
        _quad(canvas, [project(p, bot_z), project(q, bot_z), project(q, top_z), project(p, top_z)], edge)
    _quad(canvas, [project(p, top_z) for p in corners_top], top_paint)
    _quad(canvas, [project(p, top_z) for p in corners_top], edge)
    _quad(canvas, [
        project(a + half * 0.72, top_z + thick * 0.08),
        project(b + half * 0.72, top_z + thick * 0.08),
        project(b - half * 0.15, top_z + thick * 0.08),
        project(a - half * 0.15, top_z + thick * 0.08),
    ], rim)
    _pier(canvas, (a + b) * 0.5, direction, deck_m * 0.28, bot_z, project, edge)
    if span["index"] in spec.tower_after and frac > 0.55:
        _tower_at(canvas, span["b"], span, tower_m * min(1.0, (frac - 0.45) / 0.4), top_z, project, frac)
        _cables_at(canvas, spec.kind, span["b"], span, spans, tower_m, top_z, project, frac)
    _ = length


def _pier(canvas, mid, direction, width, top_z, project, edge) -> None:
    side = np.array([-direction[1], direction[0]]) * (width / 2)
    along = direction * (width / 2)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 150, 160, 170))
    footprint = [mid - side - along, mid + side - along, mid + side + along, mid - side + along]
    for i in range(4):
        p = footprint[i]
        q = footprint[(i + 1) % 4]
        _quad(canvas, [project(p, 0.0), project(q, 0.0), project(q, top_z), project(p, top_z)], paint)
        _quad(canvas, [project(p, 0.0), project(q, 0.0), project(q, top_z), project(p, top_z)], edge)


def _tower_at(canvas, mid, span, height, deck_z, project, frac) -> None:
    if height <= 1 or frac < 0.5:
        return
    direction = _unit(span["b"] - span["a"])
    side = np.array([-direction[1], direction[0]])
    leg = side * max(8.0, height * 0.045)
    body = skia.Paint(AntiAlias=True)
    body.setColor(skia.ColorSetARGB(255, 244, 240, 230))
    edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.6)
    edge.setColor(skia.ColorSetARGB(255, 22, 28, 36))
    top = deck_z + height
    # A-frame: two legs meeting near the top, plus a crossbeam.
    for sign in (-1.0, 1.0):
        foot = mid + side * sign * height * 0.16
        crown = mid + side * sign * height * 0.035
        _quad(canvas, [
            project(foot - leg, deck_z),
            project(foot + leg, deck_z),
            project(crown + leg * 0.45, top),
            project(crown - leg * 0.45, top),
        ], body)
        _quad(canvas, [
            project(foot - leg, deck_z),
            project(foot + leg, deck_z),
            project(crown + leg * 0.45, top),
            project(crown - leg * 0.45, top),
        ], edge)
    beam_y = deck_z + height * 0.72
    _quad(canvas, [
        project(mid - side * height * 0.14, beam_y),
        project(mid + side * height * 0.14, beam_y),
        project(mid + side * height * 0.14, beam_y + height * 0.06),
        project(mid - side * height * 0.14, beam_y + height * 0.06),
    ], body)


def _cables_at(canvas, kind, mid, span, spans, height, deck_z, project, frac) -> None:
    if frac < 0.62:
        return
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4)
    pen.setColor(skia.ColorSetARGB(230, 28, 34, 42))
    top = project(mid, deck_z + height)
    if top is None:
        return
    neighbors = [span]
    nxt = span["index"] + 1
    if nxt < len(spans):
        neighbors.append(spans[nxt])
    if kind == "suspension":
        for piece in neighbors:
            for anchor in (piece["a"], piece["b"]):
                p = project(anchor, deck_z)
                if p is None:
                    continue
                path = skia.Path()
                path.moveTo(top[0], top[1])
                path.quadTo((top[0] + p[0]) / 2, (top[1] + p[1]) / 2 + 22, p[0], p[1])
                canvas.drawPath(path, pen)
        return
    for piece in neighbors:
        for u in (0.18, 0.42, 0.66, 0.9):
            pt = piece["a"] + (piece["b"] - piece["a"]) * u
            p = project(pt, deck_z)
            if p is None:
                continue
            canvas.drawLine(top[0], top[1], p[0], p[1], pen)


def zoom_width(t: float, t0: float, t1: float, wide_m: float, close_m: float) -> float:
    """Van Wijk zoom (d3 interpolateZoom) with smoothstep timing. Settled width is close_m."""
    if t <= t0:
        return wide_m
    if t >= t1:
        return close_m
    u = _smooth((t - t0) / (t1 - t0))
    _lon, _lat, width = fly_lonlat(u, 0.0, 0.0, wide_m, 0.0, 0.0, close_m)
    return width


def tilt_deg(t: float, t_in: float, t_hold: float, t_out: float, degrees: float = 28.0) -> float:
    """Rise to an oblique view for the model, then back to top-down."""
    rise = _smooth((t - t_in) / max(0.2, t_hold - t_in))
    fall = _smooth((t - t_out) / 0.7)
    return degrees * rise * (1.0 - fall)
