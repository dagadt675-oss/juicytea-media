"""Greenland vs Africa, rebuilt on the current engine for the 52.43 s VO.

Every camera move starts on a word, eases in-out, then holds.
Pans and zooms are 0.5–1.2 s. The Greenland slide is 4.4 s.
Holds fill the rest of the voiceover. Nothing drifts, shakes, or blurs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import skia

from jt.data import build_earth
from jt.draw import _ring_paths
from jt.project import ang_lerp, project_points
from jt.show.basemap import build_plates, view_for
from jt.show.camera import Cam
from jt.show.clock import load_clock
from jt.show.cues import pack as pack_cues
from jt.show.faces import draw_face, gag_pose
from jt.show.greenland import (
    AFRICA,
    AFRICA_KM2,
    ALGERIA_KM2,
    CHINA_KM2,
    CONGO_KM2,
    EUROPE,
    EUROPE_KM2,
    GREENLAND_KM2,
    INDIA_KM2,
    USA_KM2,
    WORDS_PATH,
    _raster_shape,
    _usa_shape,
)
from jt.show.labels import Hud, leader_label, pill, strike
from jt.show.fast_render import RasterCache, SlotCache
from jt.show.lod import load_local, load_regional, paint_lod
from jt.show.pack import layout
from jt.show.polys import _path_of, group_shape, shape_from
from jt.show.props import contact_ripple, dashed_path, dust
from jt.show.truesize import (
    GREENLAND_HOME_LAT,
    GREENLAND_HOME_LON,
    display_multiplier,
    reproject_true,
)
from jt.show.vfx_core import (
    bezier_ease_out,
    click_squash,
    cloud_alpha_for_span,
    draw_atmosphere,
    draw_clouds,
    draw_svg,
    exp_zoom,
    icon_parallax,
    icon_pop,
    neon_passes,
)

# Pops were drawn as 18 frames at 30 fps, which is 0.6 s. Output frames are
# 60 fps so the same second is smoother, not faster.
MOTION_FPS = 30
FPS = 60
W, H = 1080, 1920
CLOCK = load_clock(WORDS_PATH)
N = max(2, math.ceil(CLOCK.audio_duration * FPS - 1e-9))
T_LAST = (N - 1) / FPS

HOME = (GREENLAND_HOME_LON, GREENLAND_HOME_LAT)
DEST = (17.0, 6.0)
CHIP = (22.0, 21.0)

# Durations. The slide is the only long move. The loop is the last half-second.
D_GREENLAND = 0.85
D_GLOBE = 0.90
D_EXCUSE = 0.80
D_HERES = 0.90
D_ROUND = 0.80
D_STRETCH = 0.90
D_POLES = 0.85
D_SIXTEEN = 1.00
D_SLIDE = 4.40
D_AFRICA = 0.70
D_ALGERIA = 0.85
D_CONGO = 0.80
D_PACK = 0.95
D_NEXT = 1.00
D_REMEMBER = 0.90
D_HUGE = 0.85
D_LOOP = 0.50

HUGE_T = CLOCK.t("HUGE", after=CLOCK.outro)
LOOP_T = T_LAST - D_LOOP

OPEN = Cam("merc", -6, 36, 150)
HAND_SVG = "/workspace/asset_library/extra/kenney/input-prompts/Touch/Vector/touch_hand_open.svg"

RED = (226, 42, 64)
GOLD = (255, 196, 48)
GREEN = (24, 150, 78)
BLUE = (36, 112, 210)
INK = (16, 16, 20)
PAPER = (244, 244, 246)
USA_C = (28, 118, 230)
CHN_C = (210, 40, 52)
IND_C = (230, 120, 28)
EUR_C = (118, 72, 210)


@dataclass(frozen=True)
class Move:
    name: str
    word: str
    t: float
    dur: float
    end: Cam
    desc: str


def _moves() -> list[Move]:
    b = CLOCK
    return [
        Move("greenland", "GREENLAND", b.t("GREENLAND"), D_GREENLAND,
             Cam("merc", -12, 44, 120), "push in on the Mercator lie"),
        Move("globe", "NOT", b.t("NOT"), D_GLOBE,
             Cam("ortho", -18, 42, 100), "projection cut, then ease on the globe"),
        Move("excuse", "ALGERIA", b.t("ALGERIA"), D_EXCUSE,
             Cam("ortho", -40, 72, 36), "push to Greenland and hold for Excuse me"),
        Move("heres", "HERE", b.heres, D_HERES,
             Cam("merc", -24, 58, 86), "projection cut, then pull back to the flat map"),
        Move("round", "ROUND", b.t("ROUND"), D_ROUND,
             Cam("merc", -30, 62, 70), "ease toward the poles"),
        Move("stretches", "STRETCHES", b.t("STRETCHES"), D_STRETCH,
             Cam("merc", -36, 66, 58), "ease into the stretch"),
        Move("poles", "POLES", b.t("POLES"), D_POLES,
             Cam("merc", -40, 70, 52), "land on Greenland for ~3× and ~9×"),
        Move("sixteen", "SIXTEEN", b.sixteen, D_SIXTEEN,
             Cam("merc", -42, 72, 40), "push in on the 16× lie"),
        Move("slide", "DRAG", b.drag, D_SLIDE,
             Cam("merc", 17, 4, 90), "slide Greenland onto Africa, counter 16× to 1×"),
        Move("africa", "AFRICA", b.africa14, D_AFRICA,
             Cam("merc", 17, 0, 84), "settle on the whole continent"),
        Move("algeria", "ALGERIA", b.algeria, D_ALGERIA,
             Cam("merc", 18, 12, 62), "frame Algeria and a true-size Greenland"),
        Move("congo", "CONGO", b.congo, D_CONGO,
             Cam("merc", 20, 8, 68), "widen so DR Congo fits, with left margin"),
        Move("pack", "USA", b.usa, D_PACK,
             Cam("merc", 17, 0, 84), "widen to the whole of Africa"),
        Move("next", "NEXT", b.outro, D_NEXT,
             Cam("merc", -2, 24, 112), "start the return"),
        Move("remember", "REMEMBER", b.t("REMEMBER", after=b.outro), D_REMEMBER,
             Cam("merc", -4, 32, 134), "ease back toward the lie"),
        Move("huge", "HUGE", HUGE_T, D_HUGE,
             Cam("merc", -6, 40, 164), "Greenland grows back into the lie"),
        Move("loop", "LYING", LOOP_T, D_LOOP,
             OPEN, "last 0.50 s eases onto frame 0"),
    ]


MOVES = _moves()


def _smooth(u: float) -> float:
    u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
    return u * u * (3.0 - 2.0 * u)


def _move_at(t: float) -> tuple[Cam, Move | None, Cam]:
    """Landed camera, the move in progress, and the camera that move leaves."""
    cam = OPEN
    for move in MOVES:
        end = move.t + move.dur
        if t < move.t:
            return cam, None, cam
        if t < end:
            return cam, move, move.end
        cam = move.end
    return cam, None, cam


def camera_at(t: float) -> Cam:
    left, move, right = _move_at(t)
    if move is None:
        return left
    u = 0.0 if move.dur <= 0 else (t - move.t) / move.dur
    s = _smooth(u)
    # A projection change is a cut on the word, then an ease inside the new one.
    if left.proj != right.proj:
        left = Cam(right.proj, left.lon, left.lat, left.span)
    return Cam(
        right.proj,
        ang_lerp(left.lon, right.lon, s),
        left.lat + (right.lat - left.lat) * s,
        exp_zoom(left.span, right.span, s),
    )


def journey(t: float) -> tuple[float, float, float]:
    """Sticker lon, lat, and slide progress 0..1. Holds still between moves."""
    slide_end = CLOCK.drag + D_SLIDE
    huge_end = HUGE_T + D_HUGE
    if t < CLOCK.drag:
        return HOME[0], HOME[1], 0.0
    if t < slide_end:
        u = _smooth((t - CLOCK.drag) / D_SLIDE)
        lon = ang_lerp(HOME[0], DEST[0], u)
        lat = HOME[1] + (DEST[1] - HOME[1]) * u
        return lon, lat, u
    if t < HUGE_T:
        return DEST[0], DEST[1], 1.0
    if t < huge_end:
        u = _smooth((t - HUGE_T) / D_HUGE)
        lon = ang_lerp(DEST[0], HOME[0], u)
        lat = DEST[1] + (HOME[1] - DEST[1]) * u
        return lon, lat, 1.0
    return HOME[0], HOME[1], 1.0


def _between(t: float, a: float, b: float) -> bool:
    return a <= t < b


def check_moves() -> None:
    """Fail if a move overlaps, runs long, or the loop misses frame 0."""
    prev_end = 0.0
    for move in MOVES:
        if move.t < prev_end - 1e-6:
            raise AssertionError(f"{move.name} overlaps the previous move")
        if move.name == "slide":
            if not 3.0 <= move.dur <= 5.0:
                raise AssertionError("slide duration")
        elif move.name == "loop":
            if not 0.45 <= move.dur <= 0.55:
                raise AssertionError("loop duration")
        elif not 0.50 <= move.dur <= 1.20:
            raise AssertionError(f"{move.name} duration {move.dur}")
        if move.t + move.dur > T_LAST + 1e-6:
            raise AssertionError(f"{move.name} runs past the last frame")
        prev_end = move.t + move.dur
        # Ends of an ease-in-out are slower than the middle.
        u0, u1 = _smooth(0.10), _smooth(0.50) - _smooth(0.40)
        if u0 >= u1:
            raise AssertionError("ease is not slow at the start")
    end = camera_at(T_LAST)
    if (end.proj, round(end.lon, 5), round(end.lat, 5), round(end.span, 5)) != (
        OPEN.proj, round(OPEN.lon, 5), round(OPEN.lat, 5), round(OPEN.span, 5)
    ):
        raise AssertionError("last frame is not the opening camera")
    # A hold does not move.
    hold_t = MOVES[0].t + MOVES[0].dur + 0.20
    a, b = camera_at(hold_t), camera_at(hold_t + 0.25)
    if abs(a.span - b.span) > 1e-6 or abs(a.lat - b.lat) > 1e-6 or abs(ang_lerp(a.lon, b.lon, 0)) > 1e-6:
        if abs(a.lon - b.lon) > 1e-4 or abs(a.lat - b.lat) > 1e-4 or abs(a.span - b.span) > 1e-4:
            raise AssertionError("hold is drifting")


def beat_rows() -> list[dict]:
    rows = [{
        "word": "(open)",
        "t": 0.0,
        "move": "hold the Mercator lie",
        "duration": 0.0,
        "hold": round(MOVES[0].t, 3),
    }]
    for i, move in enumerate(MOVES):
        nxt = MOVES[i + 1].t if i + 1 < len(MOVES) else T_LAST
        rows.append({
            "word": move.word,
            "t": round(move.t, 3),
            "move": move.desc,
            "duration": round(move.dur, 3),
            "hold": round(max(0.0, nxt - (move.t + move.dur)), 3),
        })
    return rows


def element_rows() -> list[dict]:
    b = CLOCK
    slide_end = b.drag + D_SLIDE
    africa_end = b.africa14 + D_AFRICA
    return [
        {"word": "BIG", "t": round(b.t("BIG"), 3), "move": "SAME SIZE pill", "duration": 0.0,
         "hold": round(b.t("NOT") - b.t("BIG"), 3)},
        {"word": "EXCUSE", "t": round(b.excuse0, 3), "move": "EXCUSE ME pill and smug face", "duration": 0.0,
         "hold": round(b.excuse1 - b.excuse0, 3)},
        {"word": "POLES", "t": round(b.t("POLES"), 3), "move": "~3× wider and ~9× area cards", "duration": 0.0,
         "hold": round(b.sixteen - b.t("POLES"), 3)},
        {"word": "SIXTEEN", "t": round(b.sixteen, 3), "move": "counter reads 16×", "duration": 0.0,
         "hold": round(b.drag - b.sixteen, 3)},
        {"word": "DRAG", "t": round(b.drag, 3), "move": "Bezier hand 1.15 s, sticker and counter ride the 4.40 s slide",
         "duration": D_SLIDE, "hold": round(b.shrinks[0] - slide_end, 3)},
        {"word": "SHRINK", "t": round(slide_end, 3), "move": "counter lands on 1×, then holds", "duration": 0.0,
         "hold": round(b.wait0 - slide_end, 3)},
        {"word": "WAIT", "t": round(b.wait0, 3), "move": "WAIT... WHAT?! pill", "duration": 0.0,
         "hold": round(b.wait1 - b.wait0, 3)},
        {"word": "DROP", "t": round(b.drop, 3), "move": "squash and dust, camera stays", "duration": 0.45,
         "hold": round(b.africa14 - (b.drop + 0.45), 3)},
        {"word": "FOURTEEN", "t": round(b.fourteen, 3), "move": "14th Greenland pops, then the set holds",
         "duration": 0.60, "hold": round(b.algeria - b.fourteen, 3)},
        {"word": "ALGERIA", "t": round(b.algeria, 3), "move": "true-size chip beside Algeria", "duration": D_ALGERIA,
         "hold": round(b.congo - (b.algeria + D_ALGERIA), 3)},
        {"word": "CONGO", "t": round(b.congo, 3), "move": "DR Congo lights up", "duration": D_CONGO,
         "hold": round(b.hi0 - (b.congo + D_CONGO), 3)},
        {"word": "HI", "t": round(b.hi0, 3), "move": "HI, TINY bubble, camera already framed", "duration": 0.0,
         "hold": round(b.hi1 - b.hi0, 3)},
        {"word": "USA", "t": round(b.usa, 3), "move": "USA pops", "duration": 0.60, "hold": round(b.china - b.usa, 3)},
        {"word": "CHINA", "t": round(b.china, 3), "move": "China pops", "duration": 0.60, "hold": round(b.india - b.china, 3)},
        {"word": "INDIA", "t": round(b.india, 3), "move": "India pops", "duration": 0.60, "hold": round(b.europe - b.india, 3)},
        {"word": "EUROPE", "t": round(b.europe, 3), "move": "Europe pops", "duration": 0.60,
         "hold": round(b.t("TOGETHER", after=b.europe - 1) - b.europe, 3)},
        {"word": "TOGETHER", "t": round(b.t("TOGETHER", after=b.europe - 1), 3), "move": "ALL FOUR FIT pill",
         "duration": 0.0, "hold": round(b.still - b.t("TOGETHER", after=b.europe - 1), 3)},
        {"word": "STILL", "t": round(b.still, 3), "move": "STILL BIGGER pill, clear of the USA label",
         "duration": 0.0, "hold": round(b.room - b.still, 3)},
        {"word": "ROOM", "t": round(b.room, 3), "move": "ROOM TO SPARE pill", "duration": 0.0,
         "hold": round(b.outro - b.room, 3)},
        {"word": "HUGE", "t": round(HUGE_T, 3), "move": "Greenland inflates back over 0.85 s", "duration": D_HUGE,
         "hold": round(LOOP_T - (HUGE_T + D_HUGE), 3)},
        {"word": "LYING", "t": round(b.lying, 3), "move": "THIS MAP IS LYING pill", "duration": 0.0,
         "hold": round(T_LAST - b.lying, 3)},
    ]


def cue_rows() -> list[dict]:
    b = CLOCK
    rows = [
        (b.t("GREENLAND"), "whoosh", "push-greenland"),
        (b.t("BIG"), "pop", "same-size"),
        (b.t("NOT"), "whoosh", "globe"),
        (b.t("ALGERIA"), "whoosh", "excuse-push"),
        (b.excuse0, "boing", "excuse-me"),
        (b.heres, "whoosh", "back-to-map"),
        (b.t("ROUND"), "whoosh", "round"),
        (b.t("STRETCHES"), "whoosh", "stretches"),
        (b.t("POLES"), "pop", "three-by-nine"),
        (b.sixteen, "whoosh", "sixteen"),
        (b.drag, "whoosh", "slide"),
        (b.drag + D_SLIDE, "tick", "true-size"),
        (b.wait0, "boing", "wait-what"),
        (b.drop, "thud", "drop"),
        (b.africa14, "whoosh", "africa"),
        (b.fourteen, "pop", "fourteen"),
        (b.algeria, "pop", "algeria"),
        (b.congo, "pop", "dr-congo"),
        (b.hi0, "boing", "hi-tiny"),
        (b.usa, "whoosh", "usa"),
        (b.china, "pop", "china"),
        (b.india, "pop", "india"),
        (b.europe, "pop", "europe"),
        (b.t("TOGETHER", after=b.europe - 1), "pop", "all-four-fit"),
        (b.still, "pop", "still-bigger"),
        (b.room, "pop", "room-to-spare"),
        (b.outro, "whoosh", "return"),
        (b.t("REMEMBER", after=b.outro), "whoosh", "remember"),
        (HUGE_T, "whoosh", "inflate"),
        (b.lying, "pop", "lying"),
        (LOOP_T, "whoosh", "loop"),
    ]
    return pack_cues(rows)


def _tile_times() -> list[float]:
    start = CLOCK.africa14 + D_AFRICA + 0.06
    end = CLOCK.fourteen
    if end <= start:
        end = start + 0.2
    return [start + i * (end - start) / 13.0 for i in range(14)]


def _neon(canvas, path, color, core: float) -> None:
    if path.countPoints() < 3:
        return
    passes = neon_passes(core)
    last = len(passes) - 1
    for index, (width, alpha) in enumerate(passes):
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
        pen.setStrokeCap(skia.Paint.kRound_Cap)
        pen.setStrokeJoin(skia.Paint.kRound_Join)
        if index < last:
            pen.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(1.0, width * 0.28)))
        pen.setColor(skia.ColorSetARGB(int(255 * alpha), color[0], color[1], color[2]))
        canvas.drawPath(path, pen)


def _sharp_grade(img: np.ndarray) -> np.ndarray:
    """Contrast and saturation only. No dither, no blur, so a hold stays still."""
    h, w = img.shape[:2]
    ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    radius = np.sqrt(xs * xs * 0.85 + ys * ys)
    vig = np.clip(1.0 - 0.10 * np.clip(radius - 0.62, 0, 1) ** 1.4, 0.90, 1.0)
    out = img.astype(np.float32) * vig[..., None]
    out = (out - 128.0) * 1.08 + 128.0
    luma = 0.2126 * out[:, :, 0] + 0.7152 * out[:, :, 1] + 0.0722 * out[:, :, 2]
    out = luma[..., None] + (out - luma[..., None]) * 1.12
    return np.clip(out, 0, 255).astype(np.uint8)


class Episode:
    def __init__(self):
        self.earth = build_earth()
        sat = build_plates(self.earth)["satellite"]
        regional = load_regional()
        self.plates = {
            "globe": sat,
            "regional": sat if regional is None else regional,
            "local": load_local(),
        }
        g = self.earth
        self.greenland = shape_from(g, "GRL", HOME[0], HOME[1], GREENLAND_KM2)
        self.algeria_shape = shape_from(g, "DZA", 2.6, 28.0, ALGERIA_KM2)
        self.usa = _usa_shape(g)
        self.china = shape_from(g, "CHN", 104.0, 35.0, CHINA_KM2)
        self.india = shape_from(g, "IND", 79.0, 22.0, INDIA_KM2)
        self.europe = group_shape(g, EUROPE, 10.0, 50.0, EUROPE_KM2)
        self._fit14 = None
        self._fit4 = None
        self.qc = {}
        self.cache_layers = True
        self._plate_cache = RasterCache()
        self._border_cache: dict[str, SlotCache] = {}

    def render(self, t: float) -> np.ndarray:
        cam = camera_at(t)
        left, move, right = _move_at(t)
        if move is not None and left.proj == right.proj:
            u = 0.0 if move.dur <= 0 else (t - move.t) / move.dur
            span_a, span_b = left.span, right.span
        else:
            u, span_a, span_b = 1.0, cam.span, cam.span
        key = (cam.proj, cam.lon, cam.lat, cam.span, u, span_a, span_b)

        def _plate():
            return paint_lod(cam, W, H, self.plates, u, span_a, span_b)

        if self.cache_layers:
            plate = self._plate_cache.take(key, _plate)
        else:
            plate = _plate()
        rgba = np.dstack([plate, np.full((H, W), 255, np.uint8)])
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        self._world(canvas, cam, t)
        self._lettering(canvas, cam, t)
        bgra = surface.makeImageSnapshot().toarray()
        rgb = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
        return _sharp_grade(rgb)

    def scene_state(self, t: float) -> tuple:
        """Everything that can change a pixel. Equal states are the same picture."""
        cam = camera_at(t)
        lon, lat, ju = journey(t)
        b = CLOCK
        mouths = (
            gag_pose(t, b.excuse0, b.excuse1, 2),
            gag_pose(t, b.wait0, b.wait1, 2),
            gag_pose(t, b.hi0, b.hi1, 2),
        )
        hand_age = t - b.drag
        if 0.0 <= hand_age <= 1.15:
            hand = (hand_age, icon_pop(hand_age * MOTION_FPS, 18), click_squash(hand_age - 0.20, 0.18))
        else:
            hand = None
        dust_age = (t - b.drop) if b.drop <= t <= b.drop + 0.50 else None
        strike = 0.0
        if b.t("NOT") <= t < b.t("NOT") + 0.30:
            strike = _smooth(min(1.0, (t - b.t("NOT")) / 0.28))
        if _between(t, b.africa14 + D_AFRICA, b.algeria):
            tiles = tuple(
                icon_pop((t - hit) * MOTION_FPS, 18) if t >= hit else 0.0
                for hit in _tile_times()
            )
            ntiles = sum(1 for hit in _tile_times() if t + 1e-6 >= hit)
        else:
            tiles, ntiles = (), 0
        if _between(t, b.usa, b.outro):
            packs = tuple(
                icon_pop((t - t0) * MOTION_FPS, 18) if t >= t0 else 0.0
                for t0 in (b.usa, b.china, b.india, b.europe)
            )
        else:
            packs = ()
        mult = display_multiplier(lat) if b.sixteen <= t < b.africa14 + D_AFRICA else None
        if b.excuse0 <= t <= b.excuse1 + 0.2:
            face = ("smug", mouths[0])
        elif b.drag + 0.3 <= t < b.drop and not _between(t, b.africa14 + D_AFRICA, b.outro):
            expr = "shocked" if (t >= b.shrinks[2] or b.wait0 <= t <= b.wait1) else "worried"
            face = (expr, mouths[1])
        elif b.hi0 - 0.05 <= t <= b.hi1 + 0.25:
            face = ("hi", mouths[2])
        elif _between(t, b.algeria, b.usa):
            face = ("sad",)
        else:
            face = None
        gates = (
            t < b.t("NOT"),
            t >= b.lying,
            b.t("BIG") <= t < b.t("NOT") + 0.30,
            b.excuse0 <= t <= b.excuse1 + 0.12,
            b.t("POLES") <= t < b.sixteen,
            b.sixteen <= t < b.africa14 + D_AFRICA,
            b.t("TOO", after=b.sixteen) <= t < b.drag,
            b.wait0 <= t <= b.wait1 + 0.1,
            b.africa14 + D_AFRICA <= t < b.algeria,
            _between(t, b.algeria, b.usa),
            t >= b.congo and t < b.usa,
            b.hi0 <= t <= b.hi1 + 0.2,
            _between(t, b.usa, b.outro),
            t >= b.still,
            b.t("TOGETHER", after=b.europe - 1) <= t < b.still,
            t >= b.room,
            t < b.drag or t >= HUGE_T + D_HUGE,
            b.drag <= t < HUGE_T + D_HUGE and not _between(t, b.africa14 + D_AFRICA, b.algeria)
            and not _between(t, b.algeria, b.usa) and not _between(t, b.usa, b.outro),
            _between(t, b.congo, b.usa),
            cam.span >= 130 and cam.proj == "merc",
            cam.proj == "ortho",
            b.drag <= t <= b.drag + D_SLIDE + 0.25,
            b.drag <= t < b.drop + 0.4,
            tint_hi := (t < b.algeria or t >= b.outro),
        )
        return (
            cam.proj, cam.lon, cam.lat, cam.span,
            lon, lat, ju, self._lift(t), self._squash(t)[1],
            mouths, hand, dust_age, strike, tiles, packs, mult, ntiles, face, gates,
        )

    def _border(self, name: str, cam, extra, build):
        """Reuse a coast path while the camera and the extra parameters stay put."""
        if not self.cache_layers:
            return build()
        slot = self._border_cache.get(name)
        if slot is None:
            slot = SlotCache()
            self._border_cache[name] = slot
        key = (cam.proj, cam.lon, cam.lat, cam.span, extra)
        return slot.take(key, build)

    def _path(self, rings, cam) -> skia.Path:
        view = view_for(cam, W, H)
        path = skia.Path()
        path.setFillType(skia.PathFillType.kEvenOdd)
        for ring in rings:
            for piece in _ring_paths(np.asarray(ring, np.float64), view):
                if len(piece) < 3:
                    continue
                path.moveTo(piece[0][0], piece[0][1])
                for x, y in piece[1:]:
                    path.lineTo(x, y)
                path.close()
        return path

    def _fill(self, canvas, path, rgb, alpha: int) -> None:
        if path.countPoints() < 3 or alpha <= 0:
            return
        paint = skia.Paint(AntiAlias=True)
        paint.setColor(skia.ColorSetARGB(int(alpha), rgb[0], rgb[1], rgb[2]))
        canvas.drawPath(path, paint)

    def _box(self, cam, rings):
        if not rings:
            return None
        view = view_for(cam, W, H)
        xs, ys = [], []
        for ring in rings:
            step = max(1, len(ring) // 70)
            arr = np.asarray(ring, np.float64)[::step]
            x, y, vis = project_points(arr[:, 0], arr[:, 1], view)
            if np.any(vis):
                xs.append(x[vis])
                ys.append(y[vis])
        if not xs:
            return None
        x = np.concatenate(xs)
        y = np.concatenate(ys)
        return float(x.min()), float(y.min()), float(x.max()), float(y.max())

    def _africa_box(self, cam):
        rings = []
        for iso in AFRICA:
            rings.extend(self.earth.rings.get(iso) or [])
        return self._box(cam, rings[::2] if len(rings) > 80 else rings)

    def _world(self, canvas, cam, t: float) -> None:
        if cam.proj == "merc" and cam.span >= 130:
            draw_clouds(canvas, 0.0, 1.0, W, H, alpha=0.16)
        if cam.proj == "ortho":
            view = view_for(cam, W, H)
            draw_atmosphere(canvas, view.cx, view.cy, view.r, 0.85)

        africa = self._border(
            "africa", cam, (),
            lambda: self._path([ring for iso in AFRICA for ring in (self.earth.rings.get(iso) or [])], cam),
        )
        tint = 96 if t < CLOCK.algeria or t >= CLOCK.outro else 70
        self._fill(canvas, africa, (255, 176, 48), tint)
        coast = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.0)
        coast.setColor(skia.ColorSetARGB(230, 255, 214, 120))
        canvas.drawPath(africa, coast)

        compare = _between(t, CLOCK.algeria, CLOCK.usa)
        if compare:
            alg = self._border("dza", cam, (), lambda: self._path(self.earth.rings.get("DZA") or [], cam))
            self._fill(canvas, alg, GREEN, 170)
            _neon(canvas, alg, (180, 255, 190), 2.4)
        if _between(t, CLOCK.congo, CLOCK.usa):
            drc = self._border("cod", cam, (), lambda: self._path(self.earth.rings.get("COD") or [], cam))
            self._fill(canvas, drc, BLUE, 170)
            _neon(canvas, drc, (170, 210, 255), 2.4)

        lon, lat, _u = journey(t)
        tiles = _between(t, CLOCK.africa14 + D_AFRICA, CLOCK.algeria)
        packing = _between(t, CLOCK.usa, CLOCK.outro)
        sticker = CLOCK.drag <= t < HUGE_T + D_HUGE and not tiles and not compare and not packing
        inplace = t < CLOCK.drag or t >= HUGE_T + D_HUGE
        if inplace:
            path = self._border("grl", cam, (), lambda: self._path(self.earth.rings.get("GRL") or [], cam))
            self._fill(canvas, path, RED, 188)
            _neon(canvas, path, (255, 230, 230), 3.2)
        if sticker:
            anchor = self._project(cam, lon, lat)
            canvas.save()
            if anchor is not None:
                canvas.translate(anchor[0], anchor[1] + self._lift(t))
                sx, sy = self._squash(t)
                canvas.scale(sx, sy)
                canvas.translate(-anchor[0], -anchor[1])

            def _sticker_path():
                moved = [
                    reproject_true(ring, HOME[0], HOME[1], lon, lat)
                    for ring in (self.earth.rings.get("GRL") or [])
                ]
                return self._path(moved, cam)

            path = self._border("sticker", cam, (lon, lat), _sticker_path)
            self._fill(canvas, path, RED, 210)
            _neon(canvas, path, (255, 236, 236), 3.0)
            canvas.restore()
            if CLOCK.drag <= t <= CLOCK.drag + D_SLIDE + 0.25 and cam.proj == "merc":
                progressed = 1.0 if t >= CLOCK.drag + D_SLIDE else _smooth((t - CLOCK.drag) / D_SLIDE)
                samples = []
                for i in range(25):
                    su = progressed * (i / 24.0)
                    samples.append((
                        ang_lerp(HOME[0], DEST[0], su),
                        HOME[1] + (DEST[1] - HOME[1]) * su,
                    ))
                dashed_path(canvas, cam, samples, W, H, 1.0, phase=0.0)
        if cam.proj == "merc" and CLOCK.drag <= t < CLOCK.drop + 0.4:
            eq = [(lon_i, 0.0) for lon_i in np.linspace(-30, 55, 24)]
            dashed_path(canvas, cam, eq, W, H, 1.0, phase=0.0)

        if tiles:
            self._paint_fourteen(canvas, cam, t)
        if compare:
            path = self._border(
                "chip", cam, CHIP,
                lambda: self._path(
                    [reproject_true(ring, HOME[0], HOME[1], CHIP[0], CHIP[1]) for ring in (self.earth.rings.get("GRL") or [])],
                    cam,
                ),
            )
            self._fill(canvas, path, RED, 210)
            _neon(canvas, path, (255, 236, 236), 2.6)
        if packing:
            self._paint_pack(canvas, cam, t)

        if CLOCK.drop <= t <= CLOCK.drop + 0.50 and sticker:
            anchor = self._project(cam, lon, lat)
            if anchor is not None:
                dust(canvas, anchor[0], anchor[1], t - CLOCK.drop)
                contact_ripple(canvas, anchor[0], anchor[1], t - CLOCK.drop)
        self._faces(canvas, cam, t)
        self._hand(canvas, cam, t)

    def _project(self, cam, lon, lat):
        from jt.project import project_one
        return project_one(lon, lat, view_for(cam, W, H))

    def _lift(self, t: float) -> float:
        age = t - CLOCK.drag
        if age < 0.0 or age > 0.48:
            return 0.0
        if age < 0.18:
            return -16.0 * _smooth(age / 0.18)
        return -16.0 * (1.0 - _smooth((age - 0.18) / 0.30))

    def _squash(self, t: float) -> tuple[float, float]:
        sy = click_squash(t - CLOCK.drop, 0.22)
        sx = 1.0 + (1.0 - sy) * 0.45
        return sx, sy

    def _faces(self, canvas, cam, t: float) -> None:
        if CLOCK.excuse0 <= t <= CLOCK.excuse1 + 0.2:
            box = self._box(cam, self.earth.rings.get("GRL") or [])
            if box and box[2] - box[0] > 48:
                mouth, bob = gag_pose(t, CLOCK.excuse0, CLOCK.excuse1, 2)
                draw_face(
                    canvas, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2,
                    box[2] - box[0], "smug", mouth=mouth, bob=bob, crown=1.0,
                )
        if CLOCK.drag + 0.3 <= t < CLOCK.drop and not _between(t, CLOCK.africa14 + D_AFRICA, CLOCK.outro):
            lon, lat, _u = journey(t)
            rings = [reproject_true(ring, HOME[0], HOME[1], lon, lat) for ring in (self.earth.rings.get("GRL") or [])]
            box = self._box(cam, rings)
            if box and box[2] - box[0] > 48:
                expr = "shocked" if t >= CLOCK.shrinks[2] else "worried" if t >= CLOCK.drag + D_SLIDE else "worried"
                if CLOCK.wait0 <= t <= CLOCK.wait1:
                    expr = "shocked"
                mouth, bob = gag_pose(t, CLOCK.wait0, CLOCK.wait1, 2)
                draw_face(
                    canvas, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2,
                    min(box[2] - box[0], 280), expr, mouth=mouth, bob=bob,
                )
        if CLOCK.hi0 - 0.05 <= t <= CLOCK.hi1 + 0.25:
            box = self._box(cam, self.earth.rings.get("DZA") or [])
            if box:
                mouth, bob = gag_pose(t, CLOCK.hi0, CLOCK.hi1, 2)
                fx = min(max(200.0, (box[0] + box[2]) / 2), W - 220.0)
                fy = min(max(360.0, (box[1] + box[3]) / 2 - 20.0), 1000.0)
                draw_face(canvas, fx, fy, max(80.0, box[2] - box[0]), "smug", mouth=mouth, bob=bob)
                self._mouth = (fx, fy + max(80.0, box[2] - box[0]) * 0.16)
        elif _between(t, CLOCK.algeria, CLOCK.usa):
            rings = [reproject_true(ring, HOME[0], HOME[1], CHIP[0], CHIP[1]) for ring in (self.earth.rings.get("GRL") or [])]
            box = self._box(cam, rings)
            if box and box[2] - box[0] > 40:
                draw_face(
                    canvas, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2,
                    box[2] - box[0], "sad",
                )

    def _hand(self, canvas, cam, t: float) -> None:
        age = t - CLOCK.drag
        if age < 0.0 or age > 1.15 or cam.proj != "merc":
            return
        lon, lat, _u = journey(t)
        anchor = self._project(cam, lon, lat)
        if anchor is None:
            return
        end = (anchor[0] + 36, anchor[1] + 70)
        start = (anchor[0] + 280, anchor[1] - 220)
        u = age / 1.15
        x, y = bezier_ease_out(u, start, (start[0] + 40, start[1] + 80), (end[0] + 120, end[1] - 30), end)
        prev = camera_at(t - 1.0 / MOTION_FPS)
        px, py = icon_parallax((cam.lon - prev.lon) * 30.0, (cam.lat - prev.lat) * 30.0, 0.015)
        pop = icon_pop(age * MOTION_FPS, 18)
        squash = click_squash(age - 0.20, 0.18)
        shade = skia.Paint(AntiAlias=True)
        shade.setColor(skia.ColorSetARGB(46, 10, 14, 20))
        canvas.drawCircle(x + px, y + py, 62 * pop, shade)
        try:
            draw_svg(canvas, HAND_SVG, x + px, y + py, 210.0, scale=pop * squash)
        except Exception:
            return

    def _solve(self, cam, shapes: list[tuple[str, object]], targets: dict[str, tuple[float, float]],
               rots: tuple[int, ...] = (0, 20, 40, 60, 90, 120, 150)):
        from scipy.ndimage import binary_closing

        scale = 0.24
        sw, sh = max(8, int(W * scale)), max(8, int(H * scale))
        path, n = _path_of(self.earth, cam, AFRICA, sw, sh)
        if n == 0:
            return {name: (fx, fy, 0.0) for name, (fx, fy) in targets.items()}, 1e-6, 1.0
        surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(sw, sh))
        mc = surf.getCanvas()
        mc.clear(skia.Color4f(0, 0, 0, 0))
        solid = skia.Paint(AntiAlias=True)
        solid.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        mc.drawPath(path, solid)
        land = binary_closing(surf.makeImageSnapshot().toarray()[:, :, 3] > 40, iterations=1)
        if int(land.sum()) < 30:
            return {name: (fx, fy, 0.0) for name, (fx, fy) in targets.items()}, 1e-6, 1.0
        px_small = math.sqrt(float(land.sum()) / (AFRICA_KM2 * 1e6))
        ys, xs = np.nonzero(land)
        x0, x1 = float(xs.min()), float(xs.max())
        y0, y1 = float(ys.min()), float(ys.max())
        bw, bh = max(1.0, x1 - x0), max(1.0, y1 - y0)
        items = []
        for name, shape in shapes:
            built = []
            for rot in rots:
                got = _raster_shape(shape, px_small, rot)
                if got is not None:
                    built.append((rot, got[0] > 40, got[1], got[2]))
            if built:
                items.append((name, built))
        mask_targets = {
            name: (x0 + fx * bw, y0 + fy * bh) for name, (fx, fy) in targets.items()
        }
        mode, places = layout(land, items, mask_targets) if items else ("overlap", {})
        out = {}
        for name, (fx, fy) in targets.items():
            if name in places:
                cx, cy, rot = places[name]
                out[name] = ((cx - x0) / bw, (cy - y0) / bh, float(rot))
            else:
                out[name] = (fx, fy, 0.0)
        full_box = self._africa_box(cam)
        ref_w = 1.0 if full_box is None else max(1.0, full_box[2] - full_box[0])
        px_full = px_small / scale
        print(f"fit {mode} pieces {len(places)}/{len(targets)}", flush=True)
        return out, px_full, ref_w

    def _paint_fourteen(self, canvas, cam, t: float) -> None:
        if self._fit14 is None:
            ref = Cam("merc", 17, 0, 84)
            names = [(f"g{i:02d}", self.greenland) for i in range(14)]
            grid = (
                (0.22, 0.18), (0.42, 0.14), (0.62, 0.16), (0.80, 0.22),
                (0.18, 0.36), (0.38, 0.34), (0.58, 0.38), (0.78, 0.40),
                (0.24, 0.56), (0.46, 0.54), (0.68, 0.58),
                (0.28, 0.74), (0.50, 0.76), (0.70, 0.72),
            )
            targets = {f"g{i:02d}": pair for i, pair in enumerate(grid)}
            self._fit14 = self._solve(ref, names, targets, rots=(0, 30, 60, 90, 120, 150))
        places, px_full, ref_w = self._fit14
        box = self._africa_box(cam)
        if box is None:
            return
        x0, y0, x1, y1 = box
        bw, bh = max(1.0, x1 - x0), max(1.0, y1 - y0)
        px = px_full * (bw / ref_w)
        path, n = _path_of(self.earth, cam, AFRICA, W, H)
        canvas.save()
        if n:
            canvas.clipPath(path, doAntiAlias=True)
        times = _tile_times()
        tones = ((186, 32, 48), (214, 72, 78))
        for index, hit in enumerate(times):
            name = f"g{index:02d}"
            if t < hit or name not in places:
                continue
            fx, fy, rot = places[name]
            pop = icon_pop((t - hit) * MOTION_FPS, 18)
            self.greenland.draw(
                canvas, x0 + fx * bw, y0 + fy * bh, px, tones[index % 2], 220,
                pop=pop, shadow=0.15, stroke=(255, 244, 236), stroke_w=2.0, rot=rot,
            )
        canvas.restore()

    def _paint_pack(self, canvas, cam, t: float) -> None:
        if self._fit4 is None:
            ref = Cam("merc", 17, 0, 84)
            shapes = (
                ("usa", self.usa),
                ("chn", self.china),
                ("ind", self.india),
                ("eur", self.europe),
            )
            targets = {
                "usa": (0.30, 0.28),
                "chn": (0.70, 0.26),
                "ind": (0.32, 0.60),
                "eur": (0.68, 0.58),
            }
            self._fit4 = self._solve(
                ref, list(shapes), targets,
                rots=(0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165),
            )
        places, px_full, ref_w = self._fit4
        box = self._africa_box(cam)
        if box is None:
            return
        x0, y0, x1, y1 = box
        bw, bh = max(1.0, x1 - x0), max(1.0, y1 - y0)
        px = px_full * (bw / ref_w)
        path, n = _path_of(self.earth, cam, AFRICA, W, H)
        specs = (
            ("usa", self.usa, USA_C, CLOCK.usa),
            ("chn", self.china, CHN_C, CLOCK.china),
            ("ind", self.india, IND_C, CLOCK.india),
            ("eur", self.europe, EUR_C, CLOCK.europe),
        )
        canvas.save()
        if n:
            canvas.clipPath(path, doAntiAlias=True)
        self._pack_boxes = {}
        for name, shape, rgb, t0 in specs:
            if t < t0 or name not in places:
                continue
            fx, fy, rot = places[name]
            ox, oy = x0 + fx * bw, y0 + fy * bh
            pop = icon_pop((t - t0) * MOTION_FPS, 18)
            shape.draw(
                canvas, ox, oy, px, rgb, 215, pop=pop, shadow=0.2,
                stroke=(255, 248, 244), stroke_w=2.2, rot=rot,
            )
            self._pack_boxes[name] = self._shape_box(shape, ox, oy, px * pop, rot)
        canvas.restore()

    def _lettering(self, canvas, cam, t: float) -> None:
        hud = Hud(canvas, W, H)
        b = CLOCK
        lie = t < b.t("NOT") or t >= b.lying
        if lie:
            pill(hud, "THIS MAP IS LYING", W * 0.5, 300, RED, size=54, pop=1.0, glow=RED, kind="lying", nudge=False)
        if t < b.t("NOT"):
            self._country_pills(hud, cam, t)
        if b.t("BIG") <= t < b.t("NOT") + 0.30:
            box = pill(hud, "SAME SIZE", W * 0.5, 620, PAPER, ink=INK, size=48, pop=1.0, kind="same", nudge=False)
            if t >= b.t("NOT") and box is not None:
                strike(canvas, box, _smooth(min(1.0, (t - b.t("NOT")) / 0.28)))
        if b.excuse0 <= t <= b.excuse1 + 0.12:
            pill(hud, "EXCUSE ME?", W * 0.5, 340, PAPER, ink=INK, size=64, pop=1.0, kind="gag", nudge=False)
        if b.t("POLES") <= t < b.sixteen:
            pill(hud, "~3× WIDER", W * 0.5, 300, GOLD, ink=INK, size=64, pop=1.0, kind="wide", nudge=False)
            pill(hud, "~9× AREA", W * 0.5, 420, GOLD, ink=INK, size=56, pop=1.0, kind="area", nudge=False)
        if b.sixteen <= t < b.africa14 + D_AFRICA:
            _lon, lat, _u = journey(t)
            mult = display_multiplier(lat)
            moving = b.drag <= t < b.drag + D_SLIDE
            text = f"{mult:.1f}×" if moving else f"{max(1, int(round(mult)))}×"
            pill(hud, text, W * 0.5, 360, (18, 16, 14), ink=GOLD, size=72, pop=1.0, glow=GOLD, kind="counter", nudge=False)
            if b.t("TOO", after=b.sixteen) <= t < b.drag:
                pill(hud, "TOO BIG", W * 0.5, 490, RED, size=40, pop=1.0, kind="toobig", nudge=False)
        if b.wait0 <= t <= b.wait1 + 0.1:
            pill(hud, "WAIT... WHAT?!", W * 0.5, 430, PAPER, ink=INK, size=52, pop=1.0, kind="gag", nudge=False)
        if b.africa14 + D_AFRICA <= t < b.algeria:
            n = sum(1 for hit in _tile_times() if t + 1e-6 >= hit)
            pill(hud, f"{max(1, n)}×", W * 0.5, 360, (18, 16, 14), ink=GOLD, size=72, pop=1.0, glow=GOLD, kind="fourteen", nudge=False)
        if _between(t, b.algeria, b.usa):
            self._compare_labels(hud, canvas, cam, t)
        if b.hi0 <= t <= b.hi1 + 0.2:
            mouth = getattr(self, "_mouth", (420.0, 640.0))
            bx = min(W - 200.0, max(240.0, mouth[0] + 210.0))
            by = min(1000.0, max(300.0, mouth[1] - 150.0))
            pill(hud, "HI, TINY.", bx, by, PAPER, ink=INK, size=48, pop=1.0, kind="gag", nudge=False)
        if _between(t, b.usa, b.outro):
            self._pack_labels(hud, canvas, t)
        if t >= b.lying:
            # Names return with the lie, drawn after the shapes.
            self._country_pills(hud, cam, t)
        self.qc = {
            "overlaps": hud.overlap_pairs(),
            "safe": hud.safe_hits(),
            "band": hud.band_hits(),
            "cam": (cam.proj, round(cam.lon, 2), round(cam.lat, 2), round(cam.span, 2)),
        }

    def _country_pills(self, hud, cam, t: float) -> None:
        gbox = self._box(cam, self.earth.rings.get("GRL") or [])
        abox = self._africa_box(cam)
        if gbox:
            gx = min(max(180.0, (gbox[0] + gbox[2]) / 2), W - 180.0)
            gy = min(1080.0, max(420.0, gbox[1] + (gbox[3] - gbox[1]) * 0.62))
            pill(hud, "GREENLAND", gx, gy, RED, size=40, pop=1.0, kind="greenland", nudge=False)
        if abox:
            ax = min(max(180.0, (abox[0] + abox[2]) / 2), W - 180.0)
            ay = min(1080.0, max(520.0, abox[1] + (abox[3] - abox[1]) * 0.38))
            pill(hud, "AFRICA", ax, ay, (120, 72, 16), ink=(255, 248, 230), size=40, pop=1.0, kind="africa", nudge=False)

    def _compare_labels(self, hud, canvas, cam, t: float) -> None:
        alg = self._box(cam, self.earth.rings.get("DZA") or [])
        drc = self._box(cam, self.earth.rings.get("COD") or [])
        chip_rings = [reproject_true(ring, HOME[0], HOME[1], CHIP[0], CHIP[1]) for ring in (self.earth.rings.get("GRL") or [])]
        chip = self._box(cam, chip_rings)
        avoid = [b for b in (alg, drc, chip) if b]
        if alg:
            leader_label(hud, canvas, "ALGERIA", "0.92M SQ MI", alg, avoid, GREEN, prefer="above", size=36)
        if chip:
            leader_label(hud, canvas, "GREENLAND", "0.84M SQ MI", chip, avoid, RED, prefer="right", size=36)
        if drc and t >= CLOCK.congo:
            cx = min(W - 190.0, max(190.0, (drc[0] + drc[2]) / 2))
            cy = min(1080.0, max(480.0, drc[1] + 56.0))
            pill(hud, "DR CONGO", cx, cy, BLUE, size=34, pop=1.0, kind="drc", nudge=False)

    def _pack_labels(self, hud, canvas, t: float) -> None:
        b = CLOCK
        boxes = getattr(self, "_pack_boxes", {})
        # STILL BIGGER is registered first so country labels dodge it.
        if t >= b.still:
            pill(hud, "STILL BIGGER", W * 0.5, 340, GOLD, ink=INK, size=46, pop=1.0, kind="still", nudge=False)
        if b.t("TOGETHER", after=b.europe - 1) <= t < b.still:
            pill(hud, "ALL FOUR FIT", W * 0.5, 340, PAPER, ink=INK, size=44, pop=1.0, kind="fit", nudge=False)
        if t >= b.room:
            pill(hud, "ROOM TO SPARE", W * 0.5, 1040, PAPER, ink=INK, size=44, pop=1.0, kind="room", nudge=False)
        specs = (
            ("usa", "USA", USA_C, b.usa),
            ("chn", "CHINA", CHN_C, b.china),
            ("ind", "INDIA", IND_C, b.india),
            ("eur", "EUROPE", EUR_C, b.europe),
        )
        for name, text, rgb, t0 in specs:
            if t < t0 + 0.15 or name not in boxes:
                continue
            x0, y0, x1, y1 = boxes[name]
            cx = min(W - 150.0, max(150.0, (x0 + x1) / 2))
            if name == "ind":
                cy = min(1080.0, max(520.0, y0 + 48.0))
            elif name == "eur":
                cy = min(860.0, max(520.0, y0 + 70.0))
            else:
                cy = min(980.0, max(520.0, (y0 + y1) / 2))
            pill(hud, text, cx, cy, rgb, size=36, pop=1.0, kind=name, nudge=False)

    def _shape_box(self, shape, ox, oy, px, rot) -> tuple[float, float, float, float]:
        turn = math.radians(rot)
        c, sn = math.cos(turn), math.sin(turn)
        xs, ys = [], []
        for poly in shape.polys:
            dx = (poly[:, 0] - shape.cx) * px
            dy = -((poly[:, 1] - shape.cy) * px)
            xs.append(ox + c * dx - sn * dy)
            ys.append(oy + sn * dx + c * dy)
        if not xs:
            return (ox - 40, oy - 40, ox + 40, oy + 40)
        x = np.concatenate(xs)
        y = np.concatenate(ys)
        return float(x.min()), float(y.min()), float(x.max()), float(y.max())


check_moves()
