"""Spec-driven map beats for a GeoGlobeTales-style Short.

An episode is a JSON file. Each beat has a type the renderer knows:
extrude, colour, border, snap, prop, icon, cutout, pencil, slice,
countryball, stamp, counter, strike, skit, model, wipe, material.
The camera keys and the beats are data. Cues are one SFX hit per beat.
The tail eases toward the opening and stops one frame short, so the
last frame leads into frame 0.

Hub check for the proof: flag-icons has Sweden and Finland (the crosses
are drawn, the files stay the MIT source), and the library has the
ambientCG parchment the material beat samples. No lighthouse mesh is in
the hub, so the model beat is a drawn tower.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import skia

from jt.data import build_earth
from jt.project import project_one
from jt.show.basemap import build_plates, paint_plate, view_for
from jt.show.camera import Cam
from jt.show.cues import pack as pack_cues
from jt.show.labels import faces
from jt.show.moves import (
    apply_zoom_blur,
    border_glow,
    country_extrude_flag,
    ease_in,
    ease_out,
    landmark_pop,
    match_cut_dive,
)
from jt.show.polys import fill_iso

W, H = 1080, 1920
FPS = 30

SWE = (0, 82, 147)
FIN = (0, 150, 200)
YELLOW = (255, 214, 48)
PAPER = (244, 236, 214)

# Märket, the skerry the border kinks around.
ISLAND_LON, ISLAND_LAT = 19.1319, 60.3006

# Local meters. East is +x, north is +y. The island is a few hundred meters.
ISLAND = [
    (-170, -30), (-150, -80), (-40, -90), (50, -60), (160, -15),
    (150, 45), (60, 80), (-40, 70), (-160, 35),
]
ZIG = [(-30, -110), (50, -50), (-20, 0), (55, 45), (-10, 110)]
REDRAW = [(-30, -110), (-70, -40), (10, -20), (90, 15), (20, 55), (-40, 110)]
LOT = (230, -20, 150, 100)  # x, y, w, h meters


def _clamp(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _smooth(x: float) -> float:
    x = _clamp(x)
    return x * x * (3.0 - 2.0 * x)


def _window(t: float, t0: float, t1: float) -> float:
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return _clamp((t - t0) / (t1 - t0))


def load_episode(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not raw.get("beats"):
        raise ValueError("episode needs beats")
    if not raw.get("camera"):
        raise ValueError("episode needs camera keys")
    raw["duration"] = float(raw["duration"])
    raw["fps"] = int(raw.get("fps") or FPS)
    return raw


def cue_list(spec: dict) -> list[dict]:
    rows = []
    for beat in spec["beats"]:
        kind = beat.get("sfx") or _default_sfx(beat["type"])
        rows.append((float(beat["t"]), kind, beat.get("name") or beat["type"]))
    if spec.get("loop"):
        rows.append((float(spec["duration"]) - 2.05, "whoosh", "loop-tail"))
    return pack_cues(rows)


def _default_sfx(kind: str) -> str:
    return {
        "extrude": "pop",
        "colour": "draw",
        "border": "draw",
        "snap": "whoosh",
        "prop": "whoosh",
        "icon": "pop",
        "cutout": "pop",
        "pencil": "draw",
        "slice": "pop",
        "countryball": "pop",
        "stamp": "stamp",
        "counter": "tick",
        "strike": "stamp",
        "skit": "whoosh",
        "model": "thud",
        "wipe": "whoosh",
        "material": "whoosh",
        "arrow": "pop",
    }.get(kind, "tick")


class Episode:
    def __init__(self, spec: dict, earth=None):
        self.spec = spec
        self.duration = float(spec["duration"])
        self.fps = int(spec.get("fps") or FPS)
        self.frames = int(round(self.duration * self.fps))
        self.tail0 = self.duration - 2.05
        self.earth = earth if earth is not None else build_earth()
        self.plates = build_plates(self.earth)
        self._parchment = _load_parchment()

    def _keyed(self, t: float) -> tuple[Cam, str]:
        keys = self.spec["camera"]
        if t <= float(keys[0]["t"]):
            k = keys[0]
            return Cam(k.get("proj", "merc"), float(k["lon"]), float(k["lat"]), float(k["span"])), k.get("mode", "map")
        if t >= float(keys[-1]["t"]):
            k = keys[-1]
            return Cam(k.get("proj", "merc"), float(k["lon"]), float(k["lat"]), float(k["span"])), k.get("mode", "map")
        a, b = keys[0], keys[1]
        for left, right in zip(keys, keys[1:]):
            if float(left["t"]) <= t <= float(right["t"]):
                a, b = left, right
                break
        if b.get("ease") == "dive":
            span_t = match_cut_dive(t, float(a["t"]), float(b["t"]))["u"]
        elif b.get("ease") == "out":
            span_t = ease_out(_window(t, float(a["t"]), float(b["t"])))
        else:
            span_t = _smooth(_window(t, float(a["t"]), float(b["t"])))
        lon = float(a["lon"]) + (float(b["lon"]) - float(a["lon"])) * span_t
        lat = float(a["lat"]) + (float(b["lat"]) - float(a["lat"])) * span_t
        sa, sb = math.log(max(4.0, float(a["span"]))), math.log(max(4.0, float(b["span"])))
        span = math.exp(sa + (sb - sa) * span_t)
        mode = a.get("mode", "map")
        if a.get("mode") != b.get("mode") and span_t > 0.72:
            mode = b.get("mode", "map")
        if a.get("mode") != b.get("mode") and 0.42 < span_t <= 0.72:
            mode = "mix"
        cam = Cam(a.get("proj", "merc"), lon, lat, max(4.0, span))
        for t0, dlon in ((1.70, 3.2), (9.00, -2.6)):
            age = t - t0
            if 0.0 <= age <= 0.28:
                s = math.sin(math.pi * age / 0.28)
                cam = Cam(cam.proj, cam.lon + dlon * s, cam.lat + 1.4 * s, cam.span * (1.0 - 0.14 * s))
        return cam, mode

    def cam_at(self, t: float) -> tuple[Cam, str]:
        """Camera and a mode: map, island, or mix. The tail leads into frame 0."""
        if t >= self.tail0:
            opening, _mode = self._keyed(0.0)
            nxt, _nmode = self._keyed(1.0 / self.fps)
            u = _window(t, self.tail0, self.duration - 1.0 / self.fps)
            # A real pull-in from a wider globe. The last frame is one opening step short.
            end_span = opening.span + (opening.span - nxt.span)
            span = opening.span * 1.45 + (end_span - opening.span * 1.45) * u
            lon = opening.lon + 8.0 * (1.0 - u)
            return Cam(opening.proj, lon, opening.lat, max(4.0, span)), "map"
        return self._keyed(min(t, self.tail0))

    def blur_at(self, t: float) -> float:
        amount = 0.0
        for beat in self.spec["beats"]:
            if beat["type"] != "snap":
                continue
            dive = match_cut_dive(t, float(beat["t"]), float(beat["t"]) + float(beat.get("dur", 0.7)))
            amount = max(amount, dive["blur"])
        if t >= self.tail0:
            amount = max(amount, ease_in(_window(t, self.tail0, self.tail0 + 0.28)))
        return amount

    def render(self, t: float) -> np.ndarray:
        cam, mode = self.cam_at(t)
        if mode == "island":
            rgb = self._island(t, 1.0)
        elif mode == "mix":
            base = self._map(t, cam)
            over = self._island(t, 1.0)
            u = 0.65
            rgb = (base.astype(np.float32) * (1 - u) + over.astype(np.float32) * u).astype(np.uint8)
        else:
            rgb = self._map(t, cam)
        blur = self.blur_at(t)
        if blur >= 0.08:
            rgb = apply_zoom_blur(rgb, min(1.0, blur * 1.15), radial=True)
        return rgb

    def _map(self, t: float, cam: Cam) -> np.ndarray:
        plate = self.plates["satellite"]
        mix = self._material(t)
        img = paint_plate(plate, cam, W, H)
        if mix > 0.04 and self._parchment is not None:
            img = _crossfade(img, self._parchment_frame(cam), mix)
        rgba = np.dstack([img, np.full((H, W), 255, np.uint8)])
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        self._countries(canvas, cam, t)
        self._borders(canvas, cam, t)
        self._actors(canvas, cam, t, island=False)
        self._overlays(canvas, t)
        bgra = surface.makeImageSnapshot().toarray()
        return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])

    def _countries(self, canvas, cam: Cam, t: float) -> None:
        for beat in self.spec["beats"]:
            if beat["type"] not in ("extrude", "colour"):
                continue
            t0 = float(beat["t"])
            if t < t0:
                continue
            iso = beat["iso"]
            rgb = tuple(beat.get("color") or [200, 40, 40])
            if beat["type"] == "extrude":
                height = country_extrude_flag(t, t0, float(beat.get("dur", 0.7)))["height"]
                if height <= 0.02:
                    continue
                # The side of the extrusion, then the lid popped up.
                fill_iso(canvas, self.earth, cam, iso, tuple(int(c * 0.55) for c in rgb),
                         int(210 * height), dlat=-0.35 * height, shadow=0.2, w=W, h=H)
                fill_iso(canvas, self.earth, cam, iso, rgb, int(230 * height),
                         dlat=0.15 * height, stroke=(255, 255, 255), stroke_w=3.0, w=W, h=H)
                self._flag(canvas, cam, beat, height)
            else:
                fill_iso(canvas, self.earth, cam, iso, rgb, int(beat.get("alpha", 210)),
                         stroke=(255, 255, 255), stroke_w=3.5, w=W, h=H)

    def _flag(self, canvas, cam, beat, pop: float) -> None:
        lon = float(beat.get("flon", 18))
        lat = float(beat.get("flat", 62))
        p = project_one(lon, lat, view_for(cam, W, H))
        if p is None:
            return
        draw_flag(canvas, p[0], p[1] - 30 * pop, 70 * pop, 46 * pop, beat.get("flag", "se"))

    def _borders(self, canvas, cam, t: float) -> None:
        view = view_for(cam, W, H)
        for beat in self.spec["beats"]:
            if beat["type"] != "border":
                continue
            t0 = float(beat["t"])
            dur = float(beat.get("dur", 0.8))
            if t < t0:
                continue
            u = _clamp((t - t0) / dur)
            pts = [(float(p[0]), float(p[1])) for p in beat["points"]]
            if beat.get("style") == "zigzag" and t >= float(beat.get("zig", t0 + dur)):
                pts = [(float(p[0]), float(p[1])) for p in beat.get("zigzag") or pts]
                u = 1.0
            screen = []
            for lon, lat in pts:
                p = project_one(lon, lat, view)
                if p is not None:
                    screen.append(p)
            if len(screen) < 2:
                continue
            color = tuple(beat.get("color") or YELLOW)
            style = beat.get("style", "solid")
            glow = 0.0
            if style == "glow":
                glow = border_glow(t, float(beat.get("glow", t0)), 0.45)
            _polyline(canvas, screen, u, color, style if style != "glow" else "solid", 8 + 10 * glow, glow)

    def _island(self, t: float, alpha: float) -> np.ndarray:
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorSetARGB(255, 14, 48, 92))
        # A flat sea so the snap does not swap in a blurry satellite texture.
        # The island fills the frame, and each beat kicks the scale so the
        # close-up is not a still life on a flat field.
        kick = 0.0
        for hit in (10.2, 11.0, 12.25, 13.35, 14.85, 16.05, 17.7, 19.15):
            age = t - hit
            if 0.0 <= age <= 0.22:
                kick = max(kick, math.sin(math.pi * age / 0.22))
        s = 4.05 + 0.85 * kick
        ox = 540.0 + 280.0 * math.sin(t * 2.7)
        oy = 1000.0 + 190.0 * math.sin(t * 2.2)

        def pt(x, y):
            return ox + x * s, oy - y * s

        path = skia.Path()
        x0, y0 = pt(*ISLAND[0])
        path.moveTo(x0, y0)
        for xy in ISLAND[1:]:
            path.lineTo(*pt(*xy))
        path.close()
        sand = skia.Paint(AntiAlias=True)
        sand.setColor(skia.ColorSetARGB(int(255 * alpha), 196, 176, 120))
        canvas.drawPath(path, sand)
        shore = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6)
        shore.setColor(skia.ColorSetARGB(255, 255, 248, 230))
        canvas.drawPath(path, shore)
        zig_u = _window(t, 10.15, 11.1)
        redraw_u = _window(t, 16.05, 19.3)
        line = REDRAW if redraw_u > 0.02 else ZIG
        reveal = redraw_u if redraw_u > 0.02 else zig_u
        if reveal > 0.02:
            screen = [pt(*xy) for xy in line]
            glow = border_glow(t, 12.15, 0.5) if t < 16 else 0.35
            color = (220, 40, 48) if t >= 12.15 else YELLOW
            _polyline(canvas, screen, reveal, color, "solid", 10 + 14 * glow, glow)
        if redraw_u > 0.55:
            self._slice(canvas, path, pt, redraw_u)
        if t >= 13.2:
            self._lot(canvas, pt, landmark_pop(t, 13.35, 0.6))
        if 10.7 <= t <= 16.2:
            self._questions(canvas, t)
        if t >= 16.0:
            self._pencil(canvas, pt, _window(t, 16.05, 19.3))
        self._lighthouse_icon(canvas, pt(* (20, 8)), 1.0 if t >= 15.6 else 0.0)
        bgra = surface.makeImageSnapshot().toarray()
        return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])

    def _slice(self, canvas, island: skia.Path, pt, u: float) -> None:
        """Recolour the two sides of the redrawn line. A clip, not a texture."""
        west = skia.Path()
        west.moveTo(*pt(-400, -200))
        for xy in REDRAW:
            west.lineTo(*pt(*xy))
        west.lineTo(*pt(-400, 200))
        west.close()
        for clip, rgb in ((west, SWE), (None, (24, 150, 96))):
            canvas.save()
            if clip is not None:
                canvas.clipPath(clip, skia.ClipOp.kIntersect, True)
            else:
                canvas.clipPath(west, skia.ClipOp.kDifference, True)
            paint = skia.Paint(AntiAlias=True)
            paint.setColor(skia.ColorSetARGB(int(230 * _clamp(u)), *rgb))
            canvas.drawPath(island, paint)
            canvas.restore()

    def _lot(self, canvas, pt, pop: float) -> None:
        if pop <= 0.02:
            return
        x, y, w, h = LOT
        x0, y0 = pt(x, y + h / 2)
        x1, y1 = pt(x + w, y - h / 2)
        rect = skia.Rect.MakeLTRB(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        canvas.save()
        canvas.translate(rect.centerX(), rect.centerY())
        canvas.scale(0.7 + 0.3 * pop, 0.7 + 0.3 * pop)
        canvas.translate(-rect.centerX(), -rect.centerY())
        paint = skia.Paint(AntiAlias=True)
        paint.setColor(skia.ColorSetARGB(235, 90, 92, 98))
        canvas.drawRoundRect(rect, 8, 8, paint)
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3)
        pen.setColor(skia.ColorSetARGB(220, 255, 255, 255))
        for i in range(1, 5):
            yy = rect.top() + (rect.height() / 5) * i
            canvas.drawLine(rect.left() + 8, yy, rect.right() - 8, yy, pen)
        _label(canvas, "PARKING LOT", rect.centerX(), rect.bottom() + 36, 28)
        canvas.restore()

    def _questions(self, canvas, t: float) -> None:
        spots = [(780, 620), (860, 760), (800, 900)]
        for i, (x, y) in enumerate(spots):
            pop = landmark_pop(t, 10.85 + i * 0.18, 0.45)
            if pop <= 0.02:
                continue
            _question(canvas, x, y - 20 * (1 - pop), 92 * (0.45 + 0.55 * pop))

    def _pencil(self, canvas, pt, u: float) -> None:
        if u <= 0.01:
            return
        tip = _along(REDRAW, u)
        x, y = pt(*tip)
        ang = -0.9
        canvas.save()
        canvas.translate(x, y)
        canvas.rotate(math.degrees(ang))
        body = skia.Paint(AntiAlias=True)
        body.setColor(skia.ColorSetARGB(255, 242, 196, 48))
        canvas.drawRoundRect(skia.Rect.MakeXYWH(0, -18, 280, 36), 8, 8, body)
        wood = skia.Paint(AntiAlias=True)
        wood.setColor(skia.ColorSetARGB(255, 214, 164, 96))
        lead = skia.Path()
        lead.moveTo(0, -18)
        lead.lineTo(-36, 0)
        lead.lineTo(0, 18)
        lead.close()
        canvas.drawPath(lead, wood)
        graphite = skia.Paint(AntiAlias=True)
        graphite.setColor(skia.ColorSetARGB(255, 40, 40, 44))
        tip_path = skia.Path()
        tip_path.moveTo(-16, -8)
        tip_path.lineTo(-36, 0)
        tip_path.lineTo(-16, 8)
        tip_path.close()
        canvas.drawPath(tip_path, graphite)
        canvas.restore()

    def _lighthouse_icon(self, canvas, xy, pop: float) -> None:
        if pop <= 0.02:
            return
        draw_lighthouse(canvas, xy[0], xy[1], 46 * pop)

    def _actors(self, canvas, cam, t: float, island: bool) -> None:
        if island:
            return
        view = view_for(cam, W, H)
        for beat in self.spec["beats"]:
            if beat["type"] != "prop" or t < float(beat["t"]):
                continue
            u = _window(t, float(beat["t"]), float(beat.get("t1", beat["t"] + 2.2)))
            pts = beat.get("points") or []
            if len(pts) < 2:
                continue
            lon, lat = _along([(float(p[0]), float(p[1])) for p in pts], ease_out(u))
            p = project_one(lon, lat, view)
            if p is None:
                continue
            draw_hand_magnifier(canvas, p[0], p[1], 1.0)

    def _overlays(self, canvas, t: float) -> None:
        """Beats that are screen-space: stamps, counters, skit, wipe, balls."""
        for beat in self.spec["beats"]:
            if t < float(beat["t"]):
                continue
            kind = beat["type"]
            local = t - float(beat["t"])
            if kind == "icon" and beat.get("icon") == "thumb":
                pop = landmark_pop(t, float(beat["t"]), 0.45)
                draw_thumb(canvas, float(beat.get("x", 860)), float(beat.get("y", 420)), pop)
            elif kind == "stamp":
                draw_stamp(canvas, beat.get("text", "STAMP"), float(beat.get("x", 760)), float(beat.get("y", 380)), local)
            elif kind == "counter":
                draw_counter(canvas, t, beat)
            elif kind == "strike":
                draw_strike(canvas, beat.get("text", "70K"), float(beat.get("x", 540)), float(beat.get("y", 700)), local)
            elif kind == "countryball":
                draw_countryball(canvas, beat, local)
            elif kind == "skit":
                draw_skit(canvas, local, float(beat.get("dur", 2.0)))
            elif kind == "wipe":
                draw_film_wipe(canvas, _window(t, float(beat["t"]), float(beat["t"]) + float(beat.get("dur", 0.6))))
            elif kind == "model":
                pop = landmark_pop(t, float(beat["t"]), 0.5)
                draw_lighthouse(canvas, float(beat.get("x", 540)), float(beat.get("y", 900)), 120 * pop)
            elif kind == "arrow":
                pop = landmark_pop(t, float(beat["t"]), 0.4)
                if pop > 0.05:
                    _arrow(canvas, float(beat.get("x", 540)), float(beat.get("y", 800)), pop, float(beat.get("rot", -40)))

    def _material(self, t: float) -> float:
        mix = 0.0
        for beat in self.spec["beats"]:
            if beat["type"] != "material":
                continue
            mix = max(mix, _window(t, float(beat["t"]), float(beat.get("t1", beat["t"] + 1.0))))
        return mix

    def _parchment_frame(self, cam: Cam) -> np.ndarray:
        if self._parchment is None:
            return np.full((H, W, 3), 210, np.uint8)
        return paint_plate(self._parchment, cam, W, H)


def _load_parchment():
    path = Path("/workspace/asset_library/map_assets/basemaps/basemaps/parchment_paper/derived/parchment_aged_4096x2048.jpg")
    if not path.exists():
        return None
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB").resize((2048, 1024)))


def _crossfade(a: np.ndarray, b: np.ndarray, u: float) -> np.ndarray:
    u = _clamp(u)
    if b.shape[:2] != a.shape[:2]:
        import PIL.Image
        b = np.asarray(PIL.Image.fromarray(b).resize((a.shape[1], a.shape[0])))
    return (a.astype(np.float32) * (1 - u) + b.astype(np.float32) * u).astype(np.uint8)


def _along(pts, u: float):
    u = _clamp(u)
    if len(pts) == 1 or u <= 0:
        return pts[0]
    segs = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append(d)
        total += d
    if total <= 1e-6:
        return pts[-1]
    want = total * u
    acc = 0.0
    for (a, b), d in zip(zip(pts, pts[1:]), segs):
        if acc + d >= want:
            v = 0 if d == 0 else (want - acc) / d
            return (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)
        acc += d
    return pts[-1]


def _polyline(canvas, pts, u, color, style, width, glow):
    if len(pts) < 2 or u <= 0.01:
        return
    partial = _trim(pts, u)
    if glow > 0.05:
        wide = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width * 2.4)
        wide.setStrokeCap(skia.Paint.kRound_Cap)
        wide.setColor(skia.ColorSetARGB(int(90 * glow), color[0], color[1], color[2]))
        _stroke(canvas, partial, wide, dashed=False)
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(255, color[0], color[1], color[2]))
    _stroke(canvas, partial, pen, dashed=(style == "dashed"))


def _trim(pts, u: float):
    if u >= 0.999:
        return pts
    out = [pts[0]]
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(segs) or 1.0
    want = total * u
    acc = 0.0
    for (a, b), d in zip(zip(pts, pts[1:]), segs):
        if acc + d >= want:
            v = 0 if d == 0 else (want - acc) / d
            out.append((a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v))
            return out
        out.append(b)
        acc += d
    return out


def _stroke(canvas, pts, pen, dashed: bool):
    if not dashed:
        path = skia.Path()
        path.moveTo(*pts[0])
        for p in pts[1:]:
            path.lineTo(*p)
        canvas.drawPath(path, pen)
        return
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        steps = max(1, int(d / 28))
        for i in range(steps):
            if i % 2:
                continue
            u0, u1 = i / steps, min(1.0, (i + 0.55) / steps)
            canvas.drawLine(
                a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0,
                a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1, pen,
            )


def draw_flag(canvas, x, y, w, h, which: str) -> None:
    """Sweden or Finland. The crosses match the flag-icons shapes in the hub."""
    rect = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    paint = skia.Paint(AntiAlias=True)
    if which == "fi":
        paint.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        canvas.drawRect(rect, paint)
        paint.setColor(skia.ColorSetARGB(255, 0, 47, 108))
    else:
        paint.setColor(skia.ColorSetARGB(255, 0, 82, 147))
        canvas.drawRect(rect, paint)
        paint.setColor(skia.ColorSetARGB(255, 254, 204, 0))
    vx = rect.left() + w * 0.32
    hy = rect.top() + h * 0.45
    canvas.drawRect(skia.Rect.MakeXYWH(vx, rect.top(), w * 0.18, h), paint)
    canvas.drawRect(skia.Rect.MakeXYWH(rect.left(), hy, w, h * 0.22), paint)


def draw_hand_magnifier(canvas, x, y, pop: float) -> None:
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(pop, pop)
    skin = skia.Paint(AntiAlias=True)
    skin.setColor(skia.ColorSetARGB(255, 240, 196, 156))
    canvas.drawRoundRect(skia.Rect.MakeXYWH(-70, -20, 90, 70), 24, 24, skin)
    for i, fx in enumerate((-48, -16, 14)):
        canvas.drawRoundRect(skia.Rect.MakeXYWH(fx, -78 - (i % 2) * 10, 26, 64), 12, 12, skin)
    rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
    rim.setColor(skia.ColorSetARGB(255, 48, 48, 52))
    canvas.drawCircle(20, -110, 58, rim)
    glass = skia.Paint(AntiAlias=True)
    glass.setColor(skia.ColorSetARGB(60, 180, 220, 255))
    canvas.drawCircle(20, -110, 50, glass)
    canvas.drawRoundRect(skia.Rect.MakeXYWH(8, -58, 16, 40), 6, 6, rim)
    canvas.restore()


def draw_lighthouse(canvas, x, y, h: float) -> None:
    """A tower. The hub has no lighthouse mesh, so this is drawn."""
    if h < 4:
        return
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 245, 245, 248))
    path = skia.Path()
    path.moveTo(x - h * 0.28, y)
    path.lineTo(x + h * 0.28, y)
    path.lineTo(x + h * 0.16, y - h)
    path.lineTo(x - h * 0.16, y - h)
    path.close()
    canvas.drawPath(path, paint)
    paint.setColor(skia.ColorSetARGB(255, 180, 40, 40))
    canvas.drawRect(skia.Rect.MakeXYWH(x - h * 0.22, y - h * 0.72, h * 0.44, h * 0.12), paint)
    paint.setColor(skia.ColorSetARGB(255, 255, 220, 80))
    canvas.drawCircle(x, y - h - h * 0.06, h * 0.12, paint)


def draw_countryball(canvas, beat: dict, age: float) -> None:
    x = float(beat.get("x", 540))
    y = float(beat.get("y", 700))
    action = beat.get("action", "pop")
    pop = landmark_pop(age, 0.0, 0.4) if age < 0.5 else 1.0
    if action == "vibrate":
        x += math.sin(age * 40) * 8
    elif action == "dizzy":
        y += math.sin(age * 6) * 10
    elif action == "sit":
        y += 30
    elif action == "shoot":
        x += 40 * min(1.0, age)
    r = 70 * max(0.2, pop)
    if action == "army":
        for i in range(6):
            draw_countryball(canvas, {**beat, "x": x + (i - 2.5) * 80, "y": y, "action": "pop"}, age)
        return
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, *(beat.get("color") or SWE)))
    canvas.drawCircle(x, y, r, paint)
    draw_flag(canvas, x, y - r * 0.05, r * 1.3, r * 0.8, beat.get("flag", "se"))
    eye = skia.Paint(AntiAlias=True)
    eye.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    canvas.drawCircle(x - r * 0.28, y - r * 0.05, r * 0.18, eye)
    canvas.drawCircle(x + r * 0.28, y - r * 0.05, r * 0.18, eye)
    pupil = skia.Paint(AntiAlias=True)
    pupil.setColor(skia.ColorSetARGB(255, 20, 20, 24))
    canvas.drawCircle(x - r * 0.28, y - r * 0.02, r * 0.08, pupil)
    canvas.drawCircle(x + r * 0.28, y - r * 0.02, r * 0.08, pupil)
    if beat.get("hat") == "viking":
        horn = skia.Paint(AntiAlias=True)
        horn.setColor(skia.ColorSetARGB(255, 230, 210, 160))
        canvas.drawCircle(x - r * 0.7, y - r * 0.9, r * 0.18, horn)
        canvas.drawCircle(x + r * 0.7, y - r * 0.9, r * 0.18, horn)


def draw_stamp(canvas, text: str, x: float, y: float, age: float) -> None:
    pop = landmark_pop(age, 0.0, 0.35)
    if pop <= 0.02:
        return
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(-12)
    canvas.scale(pop, pop)
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8)
    pen.setColor(skia.ColorSetARGB(230, 196, 32, 36))
    rect = skia.Rect.MakeXYWH(-180, -54, 360, 108)
    canvas.drawRoundRect(rect, 12, 12, pen)
    _label(canvas, text, 0, 16, 54, (196, 32, 36))
    canvas.restore()


def draw_counter(canvas, t: float, beat: dict) -> None:
    t0, t1 = float(beat["t"]), float(beat.get("t1", beat["t"] + 1.5))
    u = _smooth(_window(t, t0, t1))
    value = float(beat.get("from", 1885)) + (float(beat.get("to", 1985)) - float(beat.get("from", 1885))) * u
    text = str(int(round(value)))
    _label(canvas, text, float(beat.get("x", 540)), float(beat.get("y", 360)), 92)


def draw_strike(canvas, text: str, x: float, y: float, age: float) -> None:
    _label(canvas, text, x, y, 96)
    if age > 0.25:
        u = _clamp((age - 0.25) / 0.3)
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
        pen.setColor(skia.ColorSetARGB(255, 196, 32, 36))
        # The K is the last letter. The strike grows across it.
        canvas.drawLine(x + 40, y - 20, x + 40 + 70 * u, y + 24, pen)


def draw_skit(canvas, age: float, dur: float) -> None:
    u = _clamp(age / 0.25)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(int(235 * u), 24, 28, 36))
    canvas.drawRoundRect(skia.Rect.MakeXYWH(80, 420, 920, 980), 36, 36, paint)
    skin = skia.Paint(AntiAlias=True)
    skin.setColor(skia.ColorSetARGB(255, 240, 196, 156))
    canvas.drawCircle(360, 860, 80, skin)
    canvas.drawCircle(720, 820, 70, skin)
    _label(canvas, "SIR, WE'VE LANDED.", 540, 620, 42)


def draw_film_wipe(canvas, u: float) -> None:
    if u <= 0 or u >= 1:
        return
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 12, 12, 14))
    band = H * u
    canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, band), paint)
    hole = skia.Paint(AntiAlias=True)
    hole.setColor(skia.ColorSetARGB(255, 40, 40, 44))
    for i in range(8):
        canvas.drawRect(skia.Rect.MakeXYWH(40, band - 80 - i * 36, 36, 24), hole)
        canvas.drawRect(skia.Rect.MakeXYWH(W - 76, band - 80 - i * 36, 36, 24), hole)


def draw_thumb(canvas, x, y, pop: float) -> None:
    if pop <= 0.02:
        return
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 255, 214, 48))
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(pop, pop)
    canvas.drawCircle(0, 0, 36, paint)
    canvas.drawRoundRect(skia.Rect.MakeXYWH(-12, -70, 24, 70), 10, 10, paint)
    canvas.restore()


def _question(canvas, x, y, r):
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    canvas.drawCircle(x, y, r, paint)
    _label(canvas, "?", x, y + r * 0.34, r * 0.95, (20, 24, 32))


def _arrow(canvas, x, y, pop, rot):
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(rot)
    canvas.scale(pop, pop)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    path = skia.Path()
    path.moveTo(0, -40)
    path.lineTo(28, 10)
    path.lineTo(8, 10)
    path.lineTo(8, 40)
    path.lineTo(-8, 40)
    path.lineTo(-8, 10)
    path.lineTo(-28, 10)
    path.close()
    canvas.drawPath(path, paint)
    canvas.restore()


def _label(canvas, text, x, y, size, color=(255, 255, 255)):
    font = skia.Font(faces()["bold"], size)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, color[0], color[1], color[2]))
    width = font.measureText(text)
    canvas.drawString(text, x - width / 2, y, font, paint)


def loop_step_ok(episode: Episode) -> bool:
    a = episode.cam_at(0.0)[0]
    pre = episode.cam_at((episode.frames - 1) / episode.fps)[0]
    nxt = episode.cam_at(1.0 / episode.fps)[0]
    return abs((a.span - pre.span) - (nxt.span - a.span)) < 0.15 and a.proj == pre.proj
