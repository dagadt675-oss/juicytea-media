"""Greenland vs Africa, silent, locked to the 42.411 s take.

Frame 0 is the flat Mercator lie: Greenland painted as large as Africa,
with the THIS MAP IS LYING pill already settled (the loop has to land on
that frame, not on a pop). The globe snap, the three gag mouths, the
16×→1× counter and the 14× tiles all hit the word times in words.json.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia

from jt.data import build_earth
from jt.project import project_one
from jt.show.basemap import build_plates, crossfade, paint_plate, view_for
from jt.show.camera import Cam, CameraTrack, Key
from jt.show.cues import pack as pack_cues
from jt.show.faces import draw_face, gag_pose
from jt.show.labels import Hud, area_stack, big_number, pill, strike
from jt.show.polys import (
    Shape, fill_iso, fill_many, fill_ring_list, group_shape, km_ring, project_lonlat, shape_from,
)
from jt.show.props import dashed_path, dust, graticule, sparkles
from jt.show.truesize import (
    GREENLAND_HOME_LAT,
    GREENLAND_HOME_LON,
    area_factor,
    reproject_true,
    shoelace,
)
from style.gold import pop_scale

FPS = 30
TAKE = 42.411
TAIL0 = 42.211
N = math.ceil(TAKE * FPS - 1e-9)          # 1273
TAIL1 = (N - 1) / FPS                     # last frame, 42.40 s
DURATION = N / FPS                        # container, 42.433 s — covers the take

HOME_LAT = GREENLAND_HOME_LAT
HOME_LON = GREENLAND_HOME_LON

AFRICA_KM2 = 30.37e6
GREENLAND_KM2 = 2.166e6
ALGERIA_KM2 = 2.381741e6
CONGO_KM2 = 2.344858e6
USA_KM2 = 9.833517e6
CHINA_KM2 = 9.596960e6
INDIA_KM2 = 3.287263e6
EUROPE_KM2 = 6.2e6

AFRICA = (
    "ZWE", "ZMB", "UGA", "TUN", "TGO", "TZA", "SWZ", "SDS", "SDN", "ZAF",
    "SOM", "SLE", "SEN", "RWA", "NGA", "NER", "NAM", "MOZ", "MAR", "SAH",
    "MRT", "MLI", "MWI", "MDG", "LBY", "LBR", "LSO", "KEN", "GNB", "GIN",
    "GHA", "GMB", "GAB", "ETH", "ERI", "GNQ", "EGY", "DJI", "CIV", "COD",
    "COG", "TCD", "CAF", "CMR", "BDI", "BFA", "BWA", "BEN", "AGO", "DZA",
)
EUROPE = (
    "FRA", "DEU", "ESP", "ITA", "GBR", "POL", "UKR", "ROU", "NOR", "SWE",
    "FIN", "GRC", "PRT", "CZE", "HUN", "BLR", "AUT", "BGR", "SRB", "CHE",
    "BEL", "NLD", "DNK", "IRL", "SVK", "HRV", "BIH", "LTU", "LVA", "EST",
    "SVN", "ALB", "MKD", "MDA", "LUX",
)

RED = (226, 42, 64)
GOLD = (232, 176, 42)
GREEN = (32, 138, 78)
BLUE = (46, 108, 186)
INK = (16, 16, 20)
PAPER = (244, 244, 246)

# Spoken scale. The shape's latitude is the latitude whose Mercator area
# factor equals this number, so the counter and the vertex shrink agree.
_DISP = (
    (0.00, 16.0),
    (15.028, 16.0),
    (17.919, 8.0),
    (18.395, 8.0),
    (18.78, 4.0),
    (19.358, 4.0),
    (19.78, 2.0),
    (20.252, 2.0),
    (20.58, 1.0),
    (37.20, 1.0),
    (41.05, 16.0),
    (42.30, 16.0),
)
_DLON = (
    (0.00, 0.0),
    (15.028, 0.0),
    (20.58, 46.0),
    (22.45, 46.0),
    (23.12, 59.0),
    (36.40, 59.0),
    (41.05, 0.0),
    (42.30, 0.0),
)
_EXTRA = (
    (0.00, 0.0),
    (22.40, 0.0),
    (23.12, 5.5),
    (36.20, 5.5),
    (39.6, 0.0),
    (42.30, 0.0),
)

CUES = [
    (0.08, "whoosh", "open"),
    (0.94, "draw", "greenland"),
    (1.55, "pop", "same-size"),
    (1.84, "pop", "africa"),
    (2.46, "stamp", "not"),
    (2.55, "whoosh", "globe-snap"),
    (3.35, "draw", "algeria-outline"),
    (3.61, "pop", "algeria"),
    (4.44, "boing", "excuse-me"),
    (5.32, "whoosh", "heres-the-trick"),
    (6.54, "draw", "round-earth"),
    (8.00, "draw", "stretches"),
    (8.94, "tick", "more"),
    (9.82, "pop", "poles"),
    (11.19, "pop", "greenland-sits"),
    (12.71, "impact", "sixteen"),
    (13.77, "tick", "too-big"),
    (14.83, "whoosh", "drag"),
    (15.95, "draw", "equator"),
    (17.48, "tick", "truth"),
    (18.40, "tick", "shrink-1"),
    (19.36, "tick", "shrink-2"),
    (20.25, "tick", "shrink-3"),
    (21.01, "boing", "wait-what"),
    (22.45, "impact", "drop"),
    (23.05, "pop", "dust"),
    (24.36, "pop", "fourteen"),
    (25.05, "tick", "tiles"),
    (25.40, "stamp", "by-area"),
    (26.16, "pop", "algeria-again"),
    (27.08, "tick", "bigger-than"),
    (28.40, "pop", "dr-congo"),
    (29.25, "boing", "hi-tiny"),
    (30.89, "whoosh", "clear"),
    (31.16, "pop", "usa"),
    (31.66, "pop", "china"),
    (31.98, "pop", "india"),
    (32.71, "pop", "europe"),
    (33.49, "tick", "together"),
    (34.79, "pop", "still-bigger"),
    (36.07, "pop", "room-to-spare"),
    (37.28, "whoosh", "outro"),
    (38.32, "tick", "this-map"),
    (39.29, "whoosh", "not-huge"),
    (40.68, "tick", "inflate"),
    (41.53, "pop", "lying"),
    (42.21, "whoosh", "loop-tail"),
]

_TILES = np.array([
    (-0.16, -0.12), (0.04, -0.16), (0.20, -0.08), (-0.06, 0.02),
    (0.14, 0.06), (-0.20, 0.10), (0.02, 0.16), (0.18, 0.16),
    (-0.10, -0.22), (0.12, -0.24), (-0.18, 0.00), (0.22, 0.02),
    (0.00, 0.24), (0.16, 0.24),
], np.float64)


def _clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return a if x < a else b if x > b else x


def _smooth(x: float) -> float:
    x = _clamp(x)
    return x * x * (3.0 - 2.0 * x)


def ramp(t: float, a: float, b: float) -> float:
    if b <= a:
        return 1.0 if t >= a else 0.0
    return _smooth((t - a) / (b - a))


def hold(t: float, a: float, b: float, fade: float = 0.18) -> float:
    if t < a - fade or t > b + fade:
        return 0.0
    if t < a:
        return ramp(t, a - fade, a)
    if t > b:
        return 1.0 - ramp(t, b, b + fade)
    return 1.0


def knots(t: float, rows: tuple) -> float:
    if t <= rows[0][0]:
        return float(rows[0][1])
    if t >= rows[-1][0]:
        return float(rows[-1][1])
    for (t0, v0), (t1, v1) in zip(rows, rows[1:]):
        if t0 <= t <= t1:
            if t1 <= t0:
                return float(v1)
            return float(v0) + (float(v1) - float(v0)) * _smooth((t - t0) / (t1 - t0))
    return float(rows[-1][1])


def lat_for_display(d: float) -> float:
    """Latitude whose normalized Mercator area factor reads `d` (16 at home, 1 at 0°)."""
    d = max(1.0, min(16.0, d))
    a0 = area_factor(HOME_LAT)
    a = 1.0 + (a0 - 1.0) * (d - 1.0) / 15.0
    cos_lat = 1.0 / math.sqrt(a)
    return math.degrees(math.acos(min(1.0, max(0.0, cos_lat))))


def pose(t: float) -> dict:
    """Everything that is not the camera. t>=tail replays t=0 so the loop matches."""
    if t >= TAIL0:
        t = 0.0
    disp = knots(t, _DISP)
    extra = knots(t, _EXTRA)
    dlon = knots(t, _DLON)
    base_lat = lat_for_display(disp)
    return {
        "t": t,
        "disp": disp,
        "dlon": dlon,
        "dlat": (base_lat + extra) - HOME_LAT,
        "lon": HOME_LON + dlon,
        "lat": base_lat + extra,
        "detached": ramp(t, 15.00, 15.32) * (1.0 - ramp(t, 40.50, 41.08)),
        "lift": ramp(t, 15.00, 15.45) * (1.0 - ramp(t, 22.45, 22.85)),
        "lying": (1.0 if t < 2.48 else (1.0 - ramp(t, 2.48, 2.92)) if t < 3.0
                  else ramp(t, 41.53, 41.84) if t >= 41.53 else 0.0),
        "names": 1.0 if t < 5.20 or t >= 39.35 else 0.0,
        "same": hold(t, 1.55, 2.42, 0.12),
        "strike": hold(t, 2.46, 2.85, 0.06),
        "algeria": max(hold(t, 3.30, 4.40, 0.15), hold(t, 25.90, 30.25, 0.18)),
        "drc": hold(t, 28.15, 30.30, 0.16),
        "show16": max(hold(t, 12.70, 22.35, 0.12), hold(t, 39.20, 41.15, 0.12)),
        "label3": hold(t, 8.70, 12.35, 0.16),
        "inset": hold(t, 6.45, 10.35, 0.18),
        "peel": ramp(t, 6.55, 8.15),
        "stretch": hold(t, 7.95, 13.6, 0.2),
        "path": ramp(t, 15.03, 16.55) * (1.0 - ramp(t, 22.2, 22.6)),
        "dust": hold(t, 22.45, 22.95, 0.02),
        "tiles": ramp(t, 24.363, 25.22) * (1.0 - ramp(t, 25.55, 25.95)),
        "show14": hold(t, 24.30, 25.75, 0.10),
        "by_area": hold(t, 24.55, 25.90, 0.10),
        "areas": hold(t, 24.36, 25.90, 0.10),
        "compare": hold(t, 25.92, 30.20, 0.16),
        "usa": hold(t, 31.158, 37.15, 0.1),
        "chn": hold(t, 31.657, 37.15, 0.1),
        "ind": hold(t, 31.982, 37.15, 0.1),
        "eur": hold(t, 32.714, 37.15, 0.1),
        "still": hold(t, 34.75, 37.05, 0.12),
        "room": hold(t, 36.05, 37.15, 0.1),
        "gag_excuse": hold(t, 4.442, 5.15, 0.04),
        "gag_wait": hold(t, 21.013, 21.95, 0.04),
        "gag_hi": hold(t, 29.245, 29.98, 0.04),
    }


def _arrive(t: float, t0: float) -> float:
    if t < t0:
        return 0.0
    return pop_scale(t - t0)


def _blink(t: float) -> float:
    for t0 in (16.40, 27.70, 35.55):
        if 0.0 <= t - t0 <= 0.07:
            return 1.0
    return 0.0


def _face_expr(t: float) -> str | None:
    if 4.25 <= t <= 5.22:
        return "smug"
    if 17.4 <= t < 20.85:
        return "worried"
    if 20.85 <= t < 22.55:
        return "shocked"
    if 22.55 <= t < 25.7 or 34.5 <= t < 37.15:
        return "sad"
    return None


def _mouth_bob(t: float) -> tuple[float, float]:
    for t0, t1, n in ((4.442, 5.022, 2), (21.013, 21.803, 2), (29.245, 29.800, 2)):
        mouth, bob = gag_pose(t, t0, t1, n)
        if mouth > 0.0 or (t0 <= t <= t1):
            return mouth, bob
    return 0.0, 0.0


def _keys() -> list[Key]:
    rows = [
        (0.00, "merc", -8, 24, 100),
        (2.40, "merc", -6, 26, 92),
        (2.48, "merc", -6, 26, 92),
        (2.92, "ortho", -22, 40, 128),
        (3.70, "ortho", -18, 36, 108),
        (4.22, "ortho", -16, 33, 86),
        (4.52, "ortho", -40, 68, 48),
        (5.08, "ortho", -40, 70, 44),
        (5.55, "merc", -14, 36, 90),
        (8.50, "merc", -12, 46, 78),
        (11.30, "merc", -30, 56, 62),
        (13.50, "merc", -38, 62, 52),
        (15.30, "merc", -40, 72, 68),
        (18.20, "merc", -28, 50, 62),
        (20.80, "merc", 2, 14, 54),
        (23.40, "merc", 18, 6, 46),
        (26.40, "merc", 10, 14, 62),
        (29.60, "merc", 12, 12, 58),
        (31.50, "merc", 18, 4, 44),
        (34.40, "merc", 17, 3, 40),
        (36.80, "merc", 12, 8, 48),
        (39.60, "merc", -4, 20, 84),
        (41.20, "merc", -6, 23, 96),
        (TAIL0, "merc", -3, 21, 90),
    ]
    return [Key(t, Cam(p, lon, lat, span)) for t, p, lon, lat, span in rows]


def _usa_shape(earth) -> Shape:
    main, ak = [], []
    for ring in earth.rings.get("USA") or []:
        if len(ring) < 40:
            continue
        lon = float(np.mean(ring[:, 0]))
        lat = float(np.mean(ring[:, 1]))
        if -125 <= lon <= -67 and 25 <= lat <= 49:
            main.append(ring)
        elif lat > 54 and -170 <= lon <= -141:
            ak.append(ring)
    ak = sorted(ak, key=len, reverse=True)[:3]
    polys = [km_ring(r, -98.0, 39.0) for r in main]
    ak_polys = [km_ring(r, -152.0, 64.0) for r in ak]
    if polys and ak_polys:
        north = max(float(p[:, 1].max()) for p in polys)
        south = min(float(p[:, 1].min()) for p in ak_polys)
        left = min(float(p[:, 0].min()) for p in polys)
        ak_left = min(float(p[:, 0].min()) for p in ak_polys)
        shift = np.array([left - ak_left + 180_000.0, north - south + 160_000.0])
        ak_polys = [p + shift for p in ak_polys]
    polys = polys + ak_polys
    measured = sum(shoelace(p) for p in polys)
    target = USA_KM2 * 1e6
    if measured > 1 and polys:
        scale = (target / measured) ** 0.5
        polys = [p * scale for p in polys]
    return Shape(polys, target)


class Greenland:
    def __init__(self, earth=None):
        self.earth = earth if earth is not None else build_earth()
        self.plates = build_plates(self.earth)
        self.track = CameraTrack(_keys(), TAIL0, TAIL1)
        g = self.earth
        self.greenland = shape_from(g, "GRL", HOME_LON, HOME_LAT, GREENLAND_KM2)
        self.algeria_shape = shape_from(g, "DZA", 2.6, 28.0, ALGERIA_KM2)
        self.usa = _usa_shape(g)
        self.china = shape_from(g, "CHN", 104.0, 35.0, CHINA_KM2)
        self.india = shape_from(g, "IND", 79.0, 22.0, INDIA_KM2)
        self.europe = group_shape(g, EUROPE, 10.0, 50.0, EUROPE_KM2)
        self._samples = self._africa_samples()

    def _africa_samples(self) -> np.ndarray:
        chunks = []
        for iso in AFRICA:
            for ring in self.earth.rings.get(iso) or []:
                if len(ring) >= 4:
                    chunks.append(np.asarray(ring[::24], np.float64))
        if not chunks:
            return np.zeros((1, 2))
        return np.vstack(chunks)

    def _cam(self, t: float, w: int, h: int):
        state = self.track.at(t)
        st = pose(t)
        # Keep the travelling Greenland in frame. Span stays on the track.
        follow = hold(st["t"], 15.45, 36.6, 0.4) * (1.0 - st["compare"])
        if follow > 0.02 and state.b is None and state.a.proj == "merc":
            cam = state.a
            state = type(state)(Cam("merc",
                                    cam.lon + (st["lon"] - cam.lon) * follow,
                                    cam.lat + (st["lat"] - cam.lat) * follow,
                                    cam.span))
        return state

    def render(self, t: float, w: int = 1080, h: int = 1920) -> tuple[np.ndarray, int]:
        state = self._cam(t, w, h)
        if state.b is None:
            base = self._land(state.a, t, w, h)
            cam = state.a
            blend = 0.0
        else:
            base = crossfade(self._land(state.a, t, w, h), self._land(state.b, t, w, h), state.u)
            cam = state.front()
            blend = state.u
        rgba = np.dstack([base, np.full((h, w), 255, np.uint8)])
        surface = skia.Surface(w, h)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        hud_hits = self._draw(canvas, cam, t, w, h, blend)
        bgra = surface.makeImageSnapshot().toarray()
        rgb = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
        return rgb, hud_hits

    def _land(self, cam: Cam, t: float, w: int, h: int) -> np.ndarray:
        st = pose(t)
        plate = self.plates["satellite" if cam.proj == "ortho" else "satellite_dark"]
        img = paint_plate(plate, cam, w, h)
        rgba = np.dstack([img, np.full((h, w), 255, np.uint8)])
        surface = skia.Surface(w, h)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        if cam.proj == "ortho":
            view = view_for(cam, w, h)
            rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
            rim.setColor(skia.ColorSetARGB(140, 186, 220, 228))
            canvas.drawCircle(view.cx, view.cy, view.r - 2, rim)
        graticule(canvas, cam, w, h, st["stretch"])
        fill_many(canvas, self.earth, cam, AFRICA, GOLD, 168, stroke=(255, 236, 190), w=w, h=h)
        if st["algeria"] > 0.05:
            fill_iso(canvas, self.earth, cam, "DZA", GREEN, int(200 * st["algeria"]),
                     stroke=(230, 255, 236), w=w, h=h)
        if st["drc"] > 0.05:
            fill_iso(canvas, self.earth, cam, "COD", BLUE, int(200 * st["drc"]),
                     stroke=(220, 236, 255), w=w, h=h)
        inplace = 1.0 - st["detached"]
        if inplace > 0.04:
            fill_iso(canvas, self.earth, cam, "GRL", RED, int(200 * inplace),
                     stroke=(255, 244, 244), stroke_w=2.6, w=w, h=h)
        packing = st["usa"] > 0.15 or st["chn"] > 0.15
        if st["detached"] > 0.04 and st["compare"] < 0.45 and st["tiles"] < 0.15 and not packing:
            moved = [
                reproject_true(ring, HOME_LON, HOME_LAT, st["lon"], st["lat"])
                for ring in (self.earth.rings.get("GRL") or [])
            ]
            fill_ring_list(
                canvas, moved, cam, RED, int(220 * st["detached"]),
                stroke=(255, 244, 244), stroke_w=2.8,
                shadow=0.5 + 1.1 * st["lift"], w=w, h=h,
            )
        self._overlays(canvas, cam, st, w, h)
        self._faces(canvas, cam, st, t, w, h)
        bgra = surface.makeImageSnapshot().toarray()
        return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])

    def _bbox(self, cam, w, h):
        view = view_for(cam, w, h)
        pts = []
        step = max(1, len(self._samples) // 400)
        for lon, lat in self._samples[::step]:
            p = project_one(float(lon), float(lat), view)
            if p is not None:
                pts.append(p)
        if len(pts) < 4:
            return None
        arr = np.asarray(pts)
        return float(arr[:, 0].min()), float(arr[:, 1].min()), float(arr[:, 0].max()), float(arr[:, 1].max())

    def _px_per_m(self, cam, w, h) -> tuple[float, tuple | None]:
        box = self._bbox(cam, w, h)
        if box is None:
            return 0.0, None
        bw = max(8.0, box[2] - box[0])
        bh = max(8.0, box[3] - box[1])
        africa_px = bw * bh * 0.52
        return math.sqrt(africa_px / (AFRICA_KM2 * 1e6)), box

    def _overlays(self, canvas, cam, st, w, h):
        if st["path"] > 0.05 and cam.proj == "merc":
            samples = []
            for i in range(28):
                u = i / 27
                # Walk the same latitude the shape will walk, at the drag's longitude.
                d = 16.0 + (1.0 - 16.0) * u
                lat = lat_for_display(d)
                lon = HOME_LON + 46.0 * u
                samples.append((lon, lat))
            dashed_path(canvas, cam, samples, w, h, st["path"])
        px, box = self._px_per_m(cam, w, h)
        if px <= 0 or box is None or cam.proj != "merc":
            return
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if st["tiles"] > 0.04:
            appeared = ramp(st["t"], 24.363, 25.22)
            n = int(round(appeared * 14))
            for i in range(n):
                ox = cx + _TILES[i, 0] * (x1 - x0)
                oy = cy + _TILES[i, 1] * (y1 - y0)
                pop = min(1.0, max(0.0, appeared * 14 - i) * 1.6)
                self.greenland.draw(
                    canvas, ox, oy, px, RED, int(115 * min(1.0, st["tiles"] * 4)),
                    pop=pop, shadow=0.35,
                )
        if st["compare"] > 0.2 and cam.proj == "merc":
            # Same vertex reprojection as the shrink, parked in the Sahara
            # so it can sit next to Algeria and DR Congo at true size.
            moved = [
                reproject_true(ring, HOME_LON, HOME_LAT, 8.0, 20.0)
                for ring in (self.earth.rings.get("GRL") or [])
            ]
            fill_ring_list(
                canvas, moved, cam, RED, int(225 * st["compare"]),
                stroke=(255, 244, 244), stroke_w=2.6, shadow=1.0, w=w, h=h,
            )
        packs = (
            ("usa", self.usa, (48, 108, 176), 0.30, 0.34),
            ("chn", self.china, (196, 62, 54), 0.70, 0.32),
            ("ind", self.india, (214, 120, 46), 0.30, 0.70),
            ("eur", self.europe, (96, 86, 176), 0.68, 0.70),
        )
        for key, shape, rgb, fx, fy in packs:
            vis = st[key]
            if vis < 0.08:
                continue
            ox = x0 + fx * (x1 - x0)
            oy = y0 + fy * (y1 - y0)
            ox += (1.0 - min(1.0, vis)) * 180
            shape.draw(canvas, ox, oy, px * 0.82, rgb, int(225 * min(1.0, vis * 1.3)), pop=min(1.15, 0.7 + vis), shadow=1.0)
        if 22.45 <= st["t"] <= 23.05:
            p = project_lonlat(cam, st["lon"], st["lat"], w, h)
            if p:
                dust(canvas, p[0], p[1], st["t"] - 22.45)
        if st["room"] > 0.4:
            sparkles(canvas, cx, cy - 20, st["t"], 6)
        if st["inset"] > 0.08:
            self._inset(canvas, st, w, h)

    def _inset(self, canvas, st, w, h):
        side = 250
        cam = Cam("ortho", -25, 42, 130)
        tile = paint_plate(self.plates["satellite"], cam, side, side)
        rgba = np.dstack([tile, np.full((side, side), 255, np.uint8)])
        canvas.save()
        cx, cy = w * 0.78, h * 0.52
        canvas.translate(cx, cy)
        canvas.translate(-side / 2, -side / 2)
        clip = skia.Path()
        clip.addCircle(side / 2, side / 2, side * 0.46)
        canvas.clipPath(clip, doAntiAlias=True)
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5)
        rim.setColor(skia.ColorSetARGB(220, 244, 244, 246))
        canvas.drawCircle(side / 2, side / 2, side * 0.46, rim)
        canvas.restore()

    def _faces(self, canvas, cam, st, t, w, h):
        expr = _face_expr(st["t"])
        mouth, bob = _mouth_bob(st["t"])
        blink = _blink(st["t"])
        if expr and st["compare"] < 0.35 and st["tiles"] < 0.2 and st["t"] < 24.2:
            anchor = project_lonlat(cam, st["lon"], st["lat"], w, h)
            if anchor and 4.25 <= st["t"] <= 5.22:
                # The gag is a close-up of Greenland, not of the travelling chip.
                anchor = project_lonlat(cam, HOME_LON, HOME_LAT, w, h)
            if anchor:
                if 4.25 <= st["t"] <= 5.22:
                    size = 120.0
                else:
                    size = max(48.0, min(110.0, 42.0 + 5.0 * st["disp"]))
                draw_face(
                    canvas, anchor[0], anchor[1], size, expr, mouth=mouth, bob=bob,
                    blink=blink, crown=st["gag_excuse"],
                )
        if st["compare"] > 0.35:
            chip = project_lonlat(cam, 8.0, 20.0, w, h)
            if chip:
                draw_face(canvas, chip[0], chip[1], 52, "sad")
        if st["gag_hi"] > 0.2 or (st["compare"] > 0.55 and 29.0 <= st["t"] <= 30.1):
            anchor = project_lonlat(cam, 2.6, 28.0, w, h)
            if anchor:
                m, b = gag_pose(st["t"], 29.245, 29.800, 2)
                draw_face(canvas, anchor[0], anchor[1] - 20, 84, "smug", mouth=m, bob=b, crown=0.0)
        if st["still"] > 0.35 or st["room"] > 0.2:
            box = self._bbox(cam, w, h)
            if box:
                draw_face(canvas, (box[0] + box[2]) / 2, box[1] + 70, 78, "happy", mouth=0.2 if st["room"] > 0.5 else 0.0)

    def _draw(self, canvas, cam, t: float, w: int, h: int, blend: float) -> int:
        st = pose(t)
        hud = Hud(canvas, w, h)
        # Screen pills. Geographic ones wait out the middle of a crossfade.
        geo = blend < 0.15 or blend > 0.85
        if st["lying"] > 0.05:
            pop = 1.0 if st["t"] < 2.4 or st["t"] > 41.9 else max(st["lying"], 0.7)
            if 41.53 <= st["t"] <= 41.9:
                pop = _arrive(st["t"], 41.53)
            pill(hud, "THIS MAP IS LYING", w * 0.5, h * 0.145, RED, size=40, pop=pop, glow=RED)
        if st["names"] > 0.4 and geo:
            g = project_lonlat(cam, HOME_LON, min(HOME_LAT, 70), w, h)
            a = project_lonlat(cam, 18.0, 2.0, w, h)
            if g:
                pill(hud, "GREENLAND", g[0], g[1] + 70, RED, size=28, pop=1.0)
            if a:
                pill(hud, "AFRICA", a[0], a[1], (90, 62, 16), ink=(255, 244, 220), size=28, pop=1.0)
        if st["same"] > 0.05:
            box = pill(hud, "SAME SIZE?", w * 0.5, h * 0.42, PAPER, ink=INK, size=40, pop=max(0.7, st["same"]))
            if st["strike"] > 0.05 and box:
                strike(canvas, box, st["strike"])
        if st["gag_excuse"] > 0.2:
            pill(hud, "EXCUSE ME?", w * 0.5, h * 0.30, PAPER, ink=INK, size=36, pop=1.0)
        if st["label3"] > 0.1 and geo:
            p = project_lonlat(cam, -18.0, 70.0, w, h)
            cy = p[1] if p else h * 0.28
            cx = p[0] if p else w * 0.62
            pill(hud, "~3× WIDER, ~9× AREA (70°N)", cx, cy - 36, (255, 214, 70), ink=INK, size=28,
                 pop=max(0.75, st["label3"]))
        if st["show16"] > 0.08:
            pop = _arrive(st["t"], 12.705) if st["t"] < 30 else 1.0
            if st["t"] >= 39.2:
                pop = 1.0
            big_number(hud, f"{max(1, int(round(st['disp'])))}×", w * 0.5, h * 0.23, size=92, pop=max(0.2, pop) if st["t"] >= 12.70 else 0.0)
        if st["gag_wait"] > 0.15:
            pill(hud, "WAIT... WHAT?!", w * 0.5, h * 0.33, PAPER, ink=INK, size=36, pop=1.0)
        if st["show14"] > 0.08:
            n = max(1, int(round(ramp(st["t"], 24.363, 25.15) * 14)))
            big_number(hud, f"{n}×", w * 0.5, h * 0.16, size=96, pop=_arrive(st["t"], 24.36))
        if st["by_area"] > 0.15:
            pill(hud, "BY AREA", w * 0.5, h * 0.245, RED, size=30, pop=1.0)
        if st["areas"] > 0.15:
            area_stack(hud, "AFRICA", AFRICA_KM2, w * 0.27, h * 0.84, pop=1.0)
            area_stack(hud, "GREENLAND", GREENLAND_KM2, w * 0.73, h * 0.84, pop=1.0)
        if st["compare"] > 0.25 and geo:
            alg = project_lonlat(cam, 2.6, 28.0, w, h)
            drc = project_lonlat(cam, 23.5, -2.5, w, h)
            chip = project_lonlat(cam, 8.0, 20.0, w, h)
            if alg:
                pill(hud, "ALGERIA  0.92M SQ MI", alg[0], max(120, alg[1] - 80), GREEN, size=26, pop=1.0)
            if chip:
                pill(hud, "GREENLAND  0.84M SQ MI", chip[0], chip[1] + 120, RED, size=26, pop=1.0)
            if drc and st["drc"] > 0.2:
                pill(hud, "DR CONGO  0.91M SQ MI", drc[0], drc[1] + 80, BLUE, size=26, pop=1.0)
        if st["gag_hi"] > 0.15 and geo:
            alg = project_lonlat(cam, 2.6, 28.0, w, h)
            if alg:
                pill(hud, "HI, TINY.", alg[0] + 210, alg[1] - 120, PAPER, ink=INK, size=34, pop=1.0)
        if st["usa"] > 0.3:
            pill(hud, "USA", w * 0.30, h * 0.50, (48, 108, 176), size=28, pop=1.0)
        if st["chn"] > 0.3:
            pill(hud, "CHINA", w * 0.72, h * 0.50, (196, 62, 54), size=28, pop=1.0)
        if st["ind"] > 0.3:
            pill(hud, "INDIA", w * 0.30, h * 0.78, (214, 120, 46), size=28, pop=1.0)
        if st["eur"] > 0.3:
            pill(hud, "EUROPE", w * 0.72, h * 0.60, (96, 86, 176), size=28, pop=1.0)
        if st["still"] > 0.15:
            pill(hud, "STILL BIGGER", w * 0.5, h * 0.145, (255, 214, 70), ink=INK, size=40, pop=_arrive(st["t"], 34.79))
        if st["room"] > 0.15:
            pill(hud, "ROOM TO SPARE", w * 0.5, h * 0.80, PAPER, ink=INK, size=40, pop=_arrive(st["t"], 36.07))
        return hud.band_hits()


def cue_payload() -> dict:
    return {
        "id": "greenland_africa",
        "take": "chris_f0",
        "take_duration": TAKE,
        "picture_duration": round(DURATION, 3),
        "fps": FPS,
        "frames": N,
        "loop_tail": [TAIL0, round(TAIL1, 3)],
        "audio_targets": {
            "voice_wpm": 185,
            "music_under_voice_db": 21,
            "lufs": -14,
            "lra": 2,
            "true_peak_dbtp": -1,
            "note": "Silent picture. These are the mix targets for the voice pass.",
        },
        "cues": pack_cues(CUES),
    }


def timeline_payload(words_path: Path | None = None) -> dict:
    payload = {
        "id": "greenland_africa",
        "take_duration": TAKE,
        "picture_duration": round(DURATION, 3),
        "fps": FPS,
        "frames": N,
        "loop_tail": {"start": TAIL0, "end": round(TAIL1, 3)},
        "beats": [
            {"id": "hook", "t0": 0.08, "t1": 4.222, "say": "This map says Greenland is as big as Africa. It's not even as big as Algeria."},
            {"id": "excuse", "t0": 4.442, "t1": 5.022, "speaker": "greenland", "say": "Excuse me?"},
            {"id": "trick", "t0": 5.322, "t1": 14.087, "say": "Here's the trick. Sixteen times too big."},
            {"id": "drag", "t0": 14.691, "t1": 17.919, "say": "So let's drag Greenland down to the equator."},
            {"id": "shrink", "t0": 18.07, "t1": 20.763, "say": "Watch it shrink. And shrink. And SHRINK."},
            {"id": "wait", "t0": 21.013, "t1": 21.803, "speaker": "greenland", "say": "Wait... what?!"},
            {"id": "drop", "t0": 22.303, "t1": 23.244, "say": "Now drop it on Africa."},
            {"id": "fourteen", "t0": 23.864, "t1": 25.397, "say": "Africa is FOURTEEN times bigger."},
            {"id": "algeria", "t0": 25.919, "t1": 29.065, "say": "Even Algeria is bigger than Greenland. So is D.R. Congo."},
            {"id": "hitiny", "t0": 29.245, "t1": 29.800, "speaker": "algeria", "say": "Hi, tiny."},
            {"id": "pack", "t0": 30.16, "t1": 33.933, "say": "USA, China, India, and Europe."},
            {"id": "still", "t0": 34.27, "t1": 35.361, "say": "Africa is STILL bigger."},
            {"id": "room", "t0": 35.861, "t1": 36.755, "say": "With room to spare."},
            {"id": "outro", "t0": 37.278, "t1": 42.211, "say": "The map is lying."},
        ],
    }
    if words_path and words_path.exists():
        import json
        raw = json.loads(words_path.read_text(encoding="utf-8"))
        payload["sentences"] = raw.get("sentences") or []
        payload["words"] = raw.get("words") or []
    return payload
