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
            if age >= slot * 0.9:
                done = i + 1.0
            elif age > 0:
                done = i + _smooth(age / (slot * 0.9))
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


def draw(canvas, spec: ModelDrop, state: dict, project, view_m: float, frame_w: float) -> None:
    """Draw the model. `project(east, north, up) -> (x, y) or None`."""
    spans = state["spans"]
    done = float(state["spans_done"])
    if not spans or done <= 0.02:
        return
    gsd = view_m / max(1.0, frame_w)
    if spec.scale == "stylized":
        deck_m = max(spec.deck_m, 14.0 * gsd)
        tower_m = max(spec.tower_m, 110.0 * gsd)
    else:
        deck_m = spec.deck_m
        tower_m = spec.tower_m
    deck_z = 18.0 if spec.scale == "stylized" else 8.0
    lift = state.get("drop", 0.0) * tower_m + state.get("fly", 0.0) * view_m * 0.15

    def P(pt, up):
        return _project_point(project, float(pt[0]), float(pt[1]), up + lift)

    # Contact shadow first, under every finished and partial span.
    shadow = skia.Paint(AntiAlias=True)
    shadow.setColor(skia.ColorSetARGB(54, 16, 20, 28))
    shadow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
    for span in spans:
        frac = _span_frac(done, span["index"])
        if frac <= 0.02:
            continue
        _deck(canvas, span, frac, deck_m * 1.15, 0.0, P, shadow, None, (0, 0))

    fill = skia.Paint(AntiAlias=True)
    fill.setColor(skia.ColorSetARGB(245, 226, 230, 234))
    rim = skia.Paint(AntiAlias=True)
    rim.setColor(skia.ColorSetARGB(255, 255, 250, 242))
    edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.6)
    edge.setColor(skia.ColorSetARGB(255, 22, 28, 36))
    for span in spans:
        frac = _span_frac(done, span["index"])
        if frac <= 0.02:
            continue
        _deck(canvas, span, frac, deck_m, deck_z, P, fill, edge, (0, 0))
        _deck(canvas, span, frac, deck_m * 0.55, deck_z + 2.2, P, rim, None, (-1.4, -1.0))
        if span["index"] in spec.tower_after and frac > 0.45:
            _tower_at(canvas, span["b"], span, tower_m, deck_z, P, frac)
            _cables_at(canvas, spec.kind, span["b"], span, tower_m, deck_z, deck_m, P, frac)


def _span_frac(done: float, index: int) -> float:
    if done >= index + 1:
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


def _deck(canvas, span, frac, width, up, project, fill, edge, nudge) -> None:
    a = span["a"]
    b = span["a"] + (span["b"] - span["a"]) * frac
    direction = _unit(b - a)
    side = np.array([-direction[1], direction[0]]) * (width / 2)
    corners = [
        project(a + side, up),
        project(b + side, up),
        project(b - side, up),
        project(a - side, up),
    ]
    if nudge != (0, 0):
        corners = [None if c is None else (c[0] + nudge[0], c[1] + nudge[1]) for c in corners]
    _quad(canvas, corners, fill)
    if edge is not None:
        _quad(canvas, corners, edge)


def _tower_at(canvas, mid, span, height, deck_z, project, frac) -> None:
    grow = min(1.0, max(0.0, (frac - 0.35) / 0.4))
    if grow <= 0.02:
        return
    direction = _unit(span["b"] - span["a"])
    side = np.array([-direction[1], direction[0]]) * 7.0
    top = height * grow
    body = skia.Paint(AntiAlias=True)
    body.setColor(skia.ColorSetARGB(250, 244, 240, 230))
    edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2)
    edge.setColor(skia.ColorSetARGB(255, 22, 28, 36))
    corners = [
        project(mid - side, deck_z),
        project(mid - side * 0.45, deck_z + top),
        project(mid + side * 0.45, deck_z + top),
        project(mid + side, deck_z),
    ]
    _quad(canvas, corners, body)
    _quad(canvas, corners, edge)


def _cables_at(canvas, kind, mid, span, height, deck_z, deck_m, project, frac) -> None:
    if frac < 0.55:
        return
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.7)
    pen.setColor(skia.ColorSetARGB(220, 36, 44, 54))
    top = project(mid, deck_z + height * min(1.0, (frac - 0.35) / 0.4))
    if top is None:
        return
    if kind == "suspension":
        anchors = (span["a"], span["b"])
        for anchor in anchors:
            p = project(anchor, deck_z + 4)
            if p is None:
                continue
            path = skia.Path()
            path.moveTo(top[0], top[1])
            # A shallow catenary in screen space.
            sag = (p[0], (top[1] + p[1]) / 2 + 18)
            path.quadTo(sag[0], sag[1], p[0], p[1])
            canvas.drawPath(path, pen)
        return
    # Cable-stayed fan to a few points on this span.
    for u in (0.2, 0.45, 0.7, 0.92):
        pt = span["a"] + (span["b"] - span["a"]) * u
        p = project(pt, deck_z + 3)
        if p is None:
            continue
        canvas.drawLine(top[0], top[1], p[0], p[1], pen)


def zoom_width(t: float, t0: float, t1: float, wide_m: float, close_m: float) -> float:
    """Smooth exponential zoom. Settled width is close_m."""
    if t <= t0:
        return wide_m
    if t >= t1:
        return close_m
    u = _smooth((t - t0) / (t1 - t0))
    return math.exp(math.log(wide_m) + (math.log(close_m) - math.log(wide_m)) * u)


def tilt_deg(t: float, t_in: float, t_hold: float, t_out: float, degrees: float = 28.0) -> float:
    """Rise to an oblique view for the model, then back to top-down."""
    rise = _smooth((t - t_in) / max(0.2, t_hold - t_in))
    fall = _smooth((t - t_out) / 0.7)
    return degrees * rise * (1.0 - fall)
