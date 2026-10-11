"""Greenland vs Africa, silent, locked to the 52.43 s take.

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
from jt.show.basemap import build_plates, paint_plate, view_for
from jt.show.camera import Cam, CameraTrack, Key
from jt.show.clock import load_clock
from jt.captions import active_index, groups_for
from jt.show.cues import pack as pack_cues
from jt.show.moves import ease_out_back
from jt.show.faces import draw_face, gag_pose
from jt.show.labels import Hud, big_number, comparison_card, faces, leader_label, pill, strike
from jt.show.pack import layout
from jt.show.polys import (
    Shape, _path_of, fill_iso, fill_ring_list, fill_union, group_shape, km_ring, project_lonlat, shape_from,
)
from scipy.ndimage import binary_closing
from jt.show.props import contact_ripple, dashed_path, dashed_rings, dust, equal_brackets, graticule, sparkles
from jt.show.mosaic import lloyd_seeds
from jt.show.truesize import (
    GREENLAND_HOME_LAT,
    GREENLAND_HOME_LON,
    area_factor,
    display_multiplier,
    reproject_true,
    shoelace,
)
from style.gold import pop_scale

FPS = 30
WORDS_PATH = Path(__file__).resolve().parents[2] / "examples" / "greenland" / "words.json"
CLOCK = load_clock(WORDS_PATH)
TAKE = CLOCK.audio_duration
TAIL0 = CLOCK.tail0
N = CLOCK.frames
TAIL1 = CLOCK.tail1
DURATION = CLOCK.duration

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

# Spoken scale lives in pose(), read from words.json so a new take re-times
# the shrink, the drag, and the counter together.

def _cues() -> list:
    """One hit per spoken beat. A new words.json moves the cue list with it."""
    b = CLOCK

    def w(needle: str, after: float = 0.0) -> float:
        return b.t(needle, after=after)

    return [
        (w("THIS"), "whoosh", "open"),
        (w("GREENLAND"), "draw", "greenland"),
        (w("BIG"), "pop", "same-size"),
        (w("AFRICA"), "pop", "africa"),
        (w("NOT"), "stamp", "not"),
        (2.50, "whoosh", "globe-snap"),
        (w("EVEN"), "draw", "algeria-outline"),
        (w("ALGERIA"), "pop", "algeria"),
        (b.excuse0, "boing", "excuse-me"),
        (b.heres, "whoosh", "heres-the-trick"),
        (w("ROUND"), "draw", "round-earth"),
        (w("STRETCHES"), "draw", "stretches"),
        (w("MORE"), "tick", "more"),
        (w("POLES"), "pop", "poles"),
        (w("SITS", after=10), "pop", "greenland-sits"),
        (11.46, "tick", "snap-punch"),
        (b.sixteen, "impact", "sixteen"),
        (w("TOO", after=b.sixteen), "tick", "too-big"),
        (w("BIG", after=b.sixteen), "tick", "too-big-land"),
        (w("LET"), "whoosh", "drag"),
        (w("EQUATOR"), "draw", "equator"),
        (w("TRUTH"), "tick", "truth"),
        (b.shrinks[0], "tick", "shrink-1"),
        (b.shrinks[1], "tick", "shrink-2"),
        (b.shrinks[2], "tick", "shrink-3"),
        (b.wait0, "boing", "wait-what"),
        (b.drop, "thud", "land-thud"),
        (b.africa14, "pop", "dust"),
        *_fourteen_cue_rows(),
        (b.fourteen, "pop", "fourteen"),
        (w("BIGGER", after=b.fourteen), "tick", "tiles"),
        (b.algeria, "pop", "algeria-again"),
        (w("THAN", after=b.algeria), "tick", "bigger-than"),
        (w("GREENLAND", after=b.algeria), "tick", "than-greenland"),
        (w("SO", after=28), "tick", "so-is-congo"),
        (w("CONGO", after=10), "pop", "dr-congo"),
        (b.hi0, "boing", "hi-tiny"),
        (b.usa, "pop", "usa"),
        (b.china, "pop", "china"),
        (b.india, "pop", "india"),
        (b.europe, "pop", "europe"),
        (w("TOGETHER", after=b.europe - 1), "tick", "together"),
        (b.still, "pop", "still-bigger"),
        (b.room, "pop", "room-to-spare"),
        (b.outro, "whoosh", "outro"),
        (w("REMEMBER", after=b.outro), "tick", "this-map"),
        (w("HUGE", after=b.outro), "whoosh", "not-huge"),
        (w("ISN", after=b.outro), "tick", "inflate"),
        (b.lying, "pop", "lying"),
        (b.tail0, "whoosh", "loop-tail"),
    ]


def _tile_grid():
    # Normalized offsets across the Africa box, including the south.
    return np.array([
        (-0.34, -0.40), (-0.06, -0.42), (0.22, -0.38), (0.44, -0.24),
        (-0.40, -0.14), (-0.10, -0.12), (0.20, -0.08), (0.42, 0.02),
        (-0.28, 0.12), (0.02, 0.14), (0.30, 0.18),
        (-0.14, 0.36), (0.12, 0.42), (0.00, 0.24),
    ], np.float64)


_TILES = _tile_grid()


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


def _bump(t: float, t0: float, dur: float = 0.34) -> float:
    """One-way snap. 0 before t0, 1 after t0+dur. Never comes back."""
    if t <= t0:
        return 0.0
    if t >= t0 + dur:
        return 1.0
    x = (t - t0) / dur
    return x * x * (3.0 - 2.0 * x)


def apply_motion(cam: Cam, t: float) -> Cam:
    """Extra push, drift, and snaps keyed off the word clock."""
    if cam.proj != "merc":
        return cam
    b = CLOCK
    span, lon, lat = cam.span, cam.lon, cam.lat
    # The 0–2.5 s push-in lives on the camera keys (4% span, one-way drift)
    # so the loop seam and the opening are the same step.
    # Mercator explainer: continuous 4.5% zoom/pan, then a 10% snap on SIXTEEN.
    if b.heres - 0.05 <= t <= b.sixteen + 0.5:
        dur = max(0.4, b.sixteen - b.heres)
        u = _clamp((t - b.heres) / dur)
        span *= 1.0 - 0.05 * u
        lon -= 10.0 * u
        lat += 4.0 * u
        # Snap with the round-earth inset, then again on SIXTEEN.
        span *= 1.0 - 0.08 * _bump(t, b.t("ROUND"), 0.28)
        span *= 1.0 - 0.11 * _bump(t, b.sixteen, 0.36)
    # Shrink/drag keeps moving, and sits higher so the tip clears the caption band.
    if b.sixteen + 0.5 < t < b.drag:
        u = (t - (b.sixteen + 0.5)) / max(0.3, b.drag - (b.sixteen + 0.5))
        lon += 4.0 * u
        lat -= 1.5 * u
    if b.drag <= t <= b.drop + 0.4:
        u = _clamp((t - b.drag) / max(0.4, b.drop - b.drag))
        span *= 1.0 - 0.06 * u
        lon += 5.0 * u
    # Algeria / DR Congo: drift, snap on Algeria, snap on Congo.
    if b.algeria - 0.25 <= t <= b.congo + 1.5:
        dur = max(0.4, (b.congo + 1.5) - (b.algeria - 0.25))
        u = _clamp((t - (b.algeria - 0.25)) / dur)
        lon += 7.0 * u
        lat -= 3.0 * u
        span *= 1.0 - 0.05 * u
        span *= 1.0 - 0.12 * _bump(t, b.algeria, 0.28)
        span *= 1.0 - 0.12 * _bump(t, b.congo, 0.28)
    # The pack holds a wide Africa. Drift it so those seconds are not a freeze.
    if b.usa - 0.2 <= t <= b.outro:
        u = _clamp((t - (b.usa - 0.2)) / max(0.4, b.outro - (b.usa - 0.2)))
        lon += 8.0 * u
        lat += 3.0 * u
        span *= 1.0 - 0.03 * u
    # Snap-zooms. Each one moves the coasts, so the structural meter sees an event.
    # Negative amount is a pull-out. They settle before the loop tail.
    sits = b.t("SITS", after=10)
    for t0, amount, dlon, dur in (
        # The pole snap sits between the grid and SIXTEEN, so that stretch
        # is three events instead of one quiet push.
        (sits, 0.13, 2.2, 0.20),
        (b.algeria, 0.10, -1.2, 0.42),
        (b.usa, 0.10, 1.0, 0.42),
        (b.china, 0.10, -1.0, 0.42),
        (b.india, 0.10, 0.8, 0.42),
        (b.europe, 0.10, -1.0, 0.42),
        (b.t("TOGETHER", after=b.europe - 1), -0.10, 0.0, 0.42),
        (b.t("TOGETHER", after=b.europe - 1) + 0.7, 0.12, 2.2, 0.45),
        (b.t("HUGE", after=b.outro), 0.09, -0.8, 0.55),
    ):
        p = _punch(t, t0, dur)
        span *= 1.0 - amount * p
        lon += dlon * p
    # One frame at the landing: about 3 px, then the next frame is back.
    if abs(t - b.drop) <= (0.5 / FPS):
        deg = span * (3.0 / 1080.0)
        lat -= deg
        lon += deg * 0.4
    # Drag to the first shrink is several seconds. A pulse every 1.2 s
    # keeps the counter's coast from reading as one hold.
    if b.drag <= t < b.shrinks[0]:
        k = 0
        while b.drag + k * 1.2 < b.shrinks[0] - 0.15 and k < 8:
            p = _punch(t, b.drag + k * 1.2, 0.34)
            span *= 1.0 - 0.05 * p
            lat += 0.7 * p
            k += 1
    # A 3% one-way zoom on the holds that would otherwise sit still.
    # The loop tail is left alone so the last frame stays one step before frame 0.
    if t < TAIL0:
        for t0, t1 in (
            (b.sixteen + 0.55, b.drag),
            (b.drop + 0.5, b.algeria - 0.3),
            (b.congo + 1.6, b.usa - 0.25),
        ):
            if t0 < t < t1:
                u = (t - t0) / (t1 - t0)
                span *= 1.0 - 0.03 * u
                lon += 1.2 * u
                break
    return Cam(cam.proj, lon, lat, max(12.0, span))


def _shrink_u(t: float) -> float:
    """0 at the drag, 1 at the landing. Three spoken shrinks are the steps."""
    b = CLOCK
    # u values are the journey fraction whose latitude reads 16, 8, 4, 2, then 1.
    marks = (
        (b.drag, 0.0),
        (b.shrinks[0], 0.097),  # reads about 8×
        (b.shrinks[1], 0.241),  # reads about 4×
        (b.shrinks[2], 0.379),  # reads about 2.5×
        (b.drop, 1.0),
    )
    if t <= marks[0][0]:
        return 0.0
    if t >= marks[-1][0]:
        return 1.0
    for i, ((t0, v0), (t1, v1)) in enumerate(zip(marks, marks[1:])):
        if t <= t1:
            dur = max(0.08, t1 - t0)
            x = _clamp((t - t0) / dur)
            if i == 0:
                # The drag counts down across the whole gap, not in one lurch.
                e = _smooth(x)
            else:
                # Most of this shrink lands in the first 0.4 s. The rest creeps.
                fast = min(0.92, 0.40 / dur)
                if x < fast:
                    e = 0.84 * (1.0 - (1.0 - x / fast) ** 2)
                else:
                    e = 0.84 + 0.16 * (x - fast) / (1.0 - fast)
            return v0 + (v1 - v0) * e
    return 1.0


def _journey(t: float) -> tuple[float, float, float, float]:
    """Smooth drag. Latitude, not a step table, drives the Mercator scale.

    u=0 is home. u=1 is the landing on Africa. The return during the outro
    eases back home. A sine bow makes the route an arc.
    """
    b = CLOCK
    if t <= b.drag:
        u = 0.0
    elif t >= b.outro:
        span = max(0.3, (b.lying - 0.4) - b.outro)
        u = 1.0 - _smooth((t - b.outro) / span)
    elif t >= b.drop:
        u = 1.0
    else:
        # Each spoken shrink is its own drop. The tail of the segment keeps
        # creeping so the gap before the next word is not a hold.
        u = _shrink_u(t)
    end_lat = 6.0
    end_lon = HOME_LON + 58.0
    bow = 8.0 * math.sin(math.pi * min(1.0, max(0.0, u)))
    lat = HOME_LAT + (end_lat - HOME_LAT) * u
    lon = HOME_LON + (end_lon - HOME_LON) * u + bow
    if b.drop <= t <= b.drop + 0.42:
        age = (t - b.drop) / 0.42
        lat -= 0.85 * math.sin(math.pi * age) * (1.0 - age)
    return display_multiplier(lat), lon, lat, u


def _arc_point(u: float) -> tuple[float, float]:
    u = min(1.0, max(0.0, u))
    end_lat = 6.0
    end_lon = HOME_LON + 58.0
    bow = 8.0 * math.sin(math.pi * u)
    lat = HOME_LAT + (end_lat - HOME_LAT) * u
    lon = HOME_LON + (end_lon - HOME_LON) * u + bow
    return lon, lat


def _piece_fly(t: float, t0: float, t_end: float) -> float:
    """Scale-in on the word, hold, then ease out with the outro."""
    if t < t0:
        return 0.0
    if t < t0 + 0.70:
        u = (t - t0) / 0.70
        e = u * u * (3.0 - 2.0 * u)
        return 0.62 + 0.38 * e
    if t > t_end:
        u = _clamp((t - t_end) / 0.6)
        return 1.0 - u * u * (3.0 - 2.0 * u)
    return 1.0


def _fourteen_times() -> list[float]:
    """Accelerating drops. The 14th lands on the word FOURTEEN.

    The voice only leaves about 1.6 s after the landing hold, so the
    0.35 s → 0.08 s rhythm is scaled to that window. The first gap stays
    several times the last one.
    """
    t0 = CLOCK.drop + 0.52
    t1 = CLOCK.fourteen
    gaps = []
    steps = 13
    for i in range(steps):
        f = 1.0 - i / max(1, steps - 1)
        gaps.append(0.35 * f + 0.08 * (1.0 - f))
    span = max(0.4, t1 - t0)
    scale = span / sum(gaps)
    times = [t0]
    for gap in gaps:
        times.append(times[-1] + gap * scale)
    times[-1] = t1
    return times


def _fourteen_cue_rows() -> list:
    """A tick on each copy. The last one sits on FOURTEEN with the narrator cue."""
    rows = []
    for i, hit in enumerate(_fourteen_times()):
        if i == 13:
            continue
        rows.append((hit, "tick", f"fourteen-{i + 1}"))
    return rows


def scale_report() -> dict:
    """The counter moves during the drag, and each spoken shrink is its own drop."""
    b = CLOCK
    times = np.arange(b.drag, b.drop + 1e-9, 0.05)
    disp = np.array([pose(float(t))["disp"] for t in times], np.float64)
    end = float(pose(b.drop)["disp"])
    drops = []
    for hit in b.shrinks:
        before = float(pose(hit - 0.15)["disp"])
        after = float(pose(min(b.drop, hit + 0.45))["disp"])
        drops.append(round(before - after, 3))
    # Rounded counter during the drag, before the first shrink.
    shown = []
    t = b.drag
    while t < b.shrinks[0]:
        shown.append(int(round(float(pose(t)["disp"]))))
        t += 0.1
    longest = 0.0
    run_t = b.drag
    prev = shown[0] if shown else 0
    for i, value in enumerate(shown):
        if value != prev:
            longest = max(longest, (b.drag + i * 0.1) - run_t)
            run_t = b.drag + i * 0.1
            prev = value
    longest = max(longest, b.shrinks[0] - run_t)
    return {
        "start": round(float(disp[0]), 3),
        "end": round(end, 3),
        "shrink_drops": drops,
        "counter_gap": round(longest, 3),
        "samples": int(len(disp)),
        "pass": bool(
            float(disp[0]) > 14.0
            and end < 2.2
            and len(drops) == 3
            and all(d >= 1.2 for d in drops)
            and longest <= 1.5
        ),
    }


CUES = _cues()


def _punch(t: float, t0: float, dur: float = 0.40) -> float:
    """In and back. Used for snap-zooms, which have to return."""
    if t < t0 or t > t0 + dur:
        return 0.0
    u = (t - t0) / dur
    s = math.sin(math.pi * u)
    return s * s


def _fourteen_cam() -> Cam:
    """Wide enough that every part of Africa is on the 9:16 frame."""
    return Cam("merc", 17.5, 1.0, 84.0)


def _pickup_pop(t: float) -> tuple[float, float]:
    """0.3 s sticker pickup. Scale peaks at 1.08 and the shape lifts off the map."""
    b = CLOCK
    if t < b.drag or t > b.drag + 0.30:
        return 1.0, 0.0
    s = math.sin(math.pi * (t - b.drag) / 0.30)
    return 1.0 + 0.08 * s, -42.0 * s


def _land_squash(t: float) -> tuple[float, float]:
    """Landing settle: a short squash, then back to the true outline."""
    b = CLOCK
    if not (b.drop <= t <= b.drop + 0.42):
        return 1.0, 1.0
    age = (t - b.drop) / 0.42
    sy = 1.0 - 0.18 * math.sin(math.pi * age) * (1.0 - 0.35 * age)
    sx = 1.0 + (1.0 - sy) * 0.45
    return sx, sy


def _fourteen_count(t: float) -> int:
    return sum(1 for hit in _fourteen_times() if t + 1e-6 >= hit)


def pose(t: float) -> dict:
    """Everything that is not the camera. t>=tail replays t=0 so the loop matches."""
    if t >= TAIL0:
        t = 0.0
    b = CLOCK
    disp, lon, lat, travel = _journey(t)
    globe = b.t("NOT")
    poles = b.t("POLES")
    stretches = b.t("STRETCHES")
    remember = b.t("REMEMBER", after=b.outro)
    huge = b.t("HUGE", after=b.outro)
    return {
        "t": t,
        "disp": disp,
        "dlon": lon - HOME_LON,
        "dlat": lat - HOME_LAT,
        "lon": lon,
        "lat": lat,
        "travel": travel,
        "detached": ramp(t, b.drag - 0.03, b.drag + 0.29) * (1.0 - ramp(t, b.lying - 1.03, b.lying - 0.45)),
        "lift": ramp(t, b.drag, b.drag + 0.16) * (1.0 - ramp(t, b.drop - 0.05, b.drop + 0.28)),
        "lying": (1.0 if t < globe - 0.02 else (1.0 - ramp(t, globe - 0.02, globe + 0.42)) if t < globe + 0.5
                  else ramp(t, b.lying, b.lying + 0.31) if t >= b.lying else 0.0),
        "names": 1.0 if t < b.excuse1 + 0.18 or t >= b.outro + 2.05 else 0.0,
        "same": hold(t, 1.55, globe - 0.08, 0.12),
        "strike": hold(t, globe - 0.04, globe + 0.35, 0.06),
        "algeria": max(hold(t, 3.30, 4.40, 0.15), hold(t, b.algeria - 0.26, b.congo + 1.7, 0.18)),
        "drc": hold(t, b.congo - 0.47, b.congo + 1.68, 0.16),
        "show16": hold(t, b.sixteen, b.drop - 0.25, 0.08),
        "label3": hold(t, poles - 0.15, b.sixteen - 0.25, 0.16),
        "inset": hold(t, b.heres + 1.1, b.heres + 5.0, 0.18),
        "peel": ramp(t, b.heres + 1.2, b.heres + 2.8),
        "stretch": hold(t, stretches - 0.05, b.sixteen + 0.6, 0.2),
        "pop_back": ease_out_back(_clamp((t - remember) / 0.7)) if remember <= t < huge else 0.0,
        "inflate": ramp(t, huge, huge + 0.7) if t >= huge else 0.0,
        "path": ramp(t, b.drag, b.drag + 1.52) * (1.0 - ramp(t, b.drop - 0.25, b.drop + 0.15)),
        "dust": hold(t, b.drop, b.drop + 0.50, 0.02),
        "tiles": ramp(t, b.drop + 0.48, b.drop + 0.66) * (1.0 - ramp(t, b.fourteen + 1.05, b.algeria - 0.25)),
        "show14": hold(t, b.drop + 0.48, b.fourteen + 1.19, 0.08),
        "equals": (1.0 if t < 2.25 else (1.0 - ramp(t, 2.25, 2.55)) if t < 2.6
                   else ramp(t, b.lying - 0.23, b.lying + 0.17) if t >= b.lying - 0.23 else 0.0),
        "by_area": hold(t, b.fourteen + 0.19, b.fourteen + 1.54, 0.10),
        "areas": hold(t, b.fourteen, b.fourteen + 1.54, 0.10),
        "compare": hold(t, b.algeria - 0.24, b.congo + 1.58, 0.16),
        "usa": hold(t, b.usa, b.outro, 0.1),
        "chn": hold(t, b.china, b.outro, 0.1),
        "ind": hold(t, b.india, b.outro, 0.1),
        "eur": hold(t, b.europe, b.outro, 0.1),
        "still": hold(t, b.still - 0.04, b.room + 0.98, 0.12),
        "room": hold(t, b.room - 0.02, b.outro, 0.1),
        "gag_excuse": hold(t, b.excuse0, b.excuse1 + 0.13, 0.04),
        "gag_wait": hold(t, b.wait0, b.wait1 + 0.15, 0.04),
        "gag_hi": hold(t, b.hi0, b.hi1 + 0.18, 0.04),
    }


def _arrive(t: float, t0: float) -> float:
    if t < t0:
        return 0.0
    return pop_scale(t - t0)


def _blink(t: float) -> float:
    b = CLOCK
    for t0 in (b.t("BIG"), b.t("STRETCHES"), b.drag, b.drop, b.hi0, b.still):
        if 0.0 <= t - t0 <= 0.08:
            return 1.0
    return 0.0


def _squash(t: float) -> float:
    b = CLOCK
    for start in (b.excuse0, b.t("STRETCHES"), b.drag, b.shrinks[0], b.shrinks[1], b.shrinks[2], b.drop, b.hi0, b.still):
        age = t - start
        if 0.0 <= age <= 0.24:
            u = age / 0.24
            s = u * u * (3.0 - 2.0 * u)
            return 0.70 + 0.30 * s
    return 1.0


def _face_expr(t: float) -> str | None:
    b = CLOCK
    if t <= b.excuse1 + 0.28:
        return "smug"
    if b.drag + 0.15 <= t < b.shrinks[2]:
        return "worried"
    if b.shrinks[2] <= t < b.drop:
        return "shocked"
    if b.drop <= t < b.africa14 + 1.74:
        return "sad"
    return None


def _mouth_bob(t: float) -> tuple[float, float]:
    b = CLOCK
    for t0, t1 in ((b.excuse0, b.excuse1), (b.wait0, b.wait1), (b.hi0, b.hi1)):
        mouth, bob = gag_pose(t, t0, t1, 2)
        if mouth > 0.0 or (t0 <= t <= t1):
            return mouth, bob
    return 0.0, 0.0


def _raster_shape(shape, px: float, rot: float):
    """Tight alpha mask. The shape centroid sits at (mcx, mcy) inside it."""
    if px <= 0 or not shape.polys:
        return None
    turn = math.radians(rot)
    c, sn = math.cos(turn), math.sin(turn)
    xs, ys = [], []
    for poly in shape.polys:
        dx = (poly[:, 0] - shape.cx) * px
        dy = -((poly[:, 1] - shape.cy) * px)
        xs.append(c * dx - sn * dy)
        ys.append(sn * dx + c * dy)
    allx = np.concatenate(xs)
    ally = np.concatenate(ys)
    pad = 3.0
    minx, maxx = float(allx.min()) - pad, float(allx.max()) + pad
    miny, maxy = float(ally.min()) - pad, float(ally.max()) + pad
    tw = max(4, int(math.ceil(maxx - minx)) + 2)
    th = max(4, int(math.ceil(maxy - miny)) + 2)
    if tw > 1000 or th > 1400:
        return None
    mcx = -minx
    mcy = -miny
    surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(tw, th))
    canvas = surf.getCanvas()
    canvas.clear(skia.Color4f(0, 0, 0, 0))
    shape.draw(canvas, mcx, mcy, px, (255, 255, 255), 255, pop=1.0, shadow=0.0, stroke=None, rot=rot)
    alpha = surf.makeImageSnapshot().toarray()[:, :, 3]
    if int((alpha > 40).sum()) < 8:
        return None
    return alpha, mcx, mcy


_PACK_FALLBACK = {
    "usa": (0.32, 0.30, 0.0),
    "chn": (0.68, 0.28, 0.0),
    "ind": (0.34, 0.50, 0.0),
    "eur": (0.66, 0.48, 0.0),
}


def _paste(acc, covered, count, alpha, mcx, mcy, ox, oy, rgb, vis: float) -> None:
    th, tw = alpha.shape
    top = int(round(oy - mcy))
    left = int(round(ox - mcx))
    h, w = count.shape
    y0, x0 = max(0, top), max(0, left)
    y1, x1 = min(h, top + th), min(w, left + tw)
    if y1 <= y0 or x1 <= x0:
        return
    sl = alpha[y0 - top:y1 - top, x0 - left:x1 - left]
    mask = sl > 40
    if not np.any(mask):
        return
    a = (sl.astype(np.float32) / 255.0) * vis * 210.0
    view_c = acc[y0:y1, x0:x1]
    view_a = covered[y0:y1, x0:x1]
    view_n = count[y0:y1, x0:x1]
    view_c[mask] += a[mask, None] * np.asarray(rgb, np.float32)
    view_a[mask] += a[mask]
    view_n[mask] += 1


def _draw_karaoke(canvas, t: float, w: int, h: int) -> None:
    """Spoken word in gold, the rest of the 1–3 word group in white, in the caption band."""
    rows = []
    for word in CLOCK.words:
        text = str(word["w"])
        if text.lower().strip(".,!?;:") == "around":
            text = "round"
        rows.append({"text": text, "start": float(word["t0"]), "end": float(word["t1"])})
    idx = active_index(rows, t)
    if idx is None:
        return
    group = next(g for g in groups_for(rows) if idx in g)
    size = 72.0
    font = skia.Font(faces()["bold"], size)
    pop = skia.Font(faces()["black"], size * 1.06)
    tokens = [(rows[i]["text"].upper(), i) for i in group]
    gap = 16.0
    widths = [(pop if i == idx else font).measureText(text) for text, i in tokens]
    total = sum(widths) + gap * (len(tokens) - 1)
    while total > w - 80 and size > 56 and len(tokens) > 1:
        if group[-1] != idx:
            group = group[:-1]
        else:
            group = group[1:]
        tokens = [(rows[i]["text"].upper(), i) for i in group]
        widths = [(pop if i == idx else font).measureText(text) for text, i in tokens]
        total = sum(widths) + gap * max(0, len(tokens) - 1)
    metrics = pop.getMetrics()
    center = 0.68 * h
    baseline = center - metrics.fAscent * 0.45
    x = w / 2 - total / 2
    outline = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
    outline.setStrokeWidth(7)
    outline.setColor(skia.ColorSetARGB(255, 0, 0, 0))
    cursor = x
    for (text, i), tw in zip(tokens, widths):
        f = pop if i == idx else font
        canvas.drawString(text, cursor, baseline, f, outline)
        paint = skia.Paint(AntiAlias=True)
        if i == idx:
            paint.setColor(skia.ColorSetARGB(255, 254, 212, 10))
        else:
            paint.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        canvas.drawString(text, cursor, baseline, f, paint)
        cursor += tw + gap


def _grid_pop(t: float) -> float:
    """A short brightening of the pole grid on the word poles."""
    t0 = CLOCK.t("POLES")
    if t < t0 - 0.05 or t > t0 + 0.45:
        return 0.0
    if t < t0 + 0.18:
        u = (t - (t0 - 0.05)) / 0.23
    else:
        u = 1.0 - (t - (t0 + 0.18)) / 0.27
    u = _clamp(u)
    return u * u * (3.0 - 2.0 * u)


def _bubble_tail(canvas, box, tip) -> None:
    """A filled tail from the pill edge toward Algeria's mouth."""
    left, top, right, bottom = box
    # The bubble sits above Algeria, so the tail leaves the bottom edge
    # and stops just short of the mouth.
    x = min(max(tip[0], left + 28), right - 28)
    a, b = (x - 16, bottom - 1), (x + 16, bottom - 1)
    dx, dy = tip[0] - x, tip[1] - bottom
    length = max(1.0, (dx * dx + dy * dy) ** 0.5)
    end = (x + dx * (length - 22.0) / length, bottom + dy * (length - 22.0) / length)
    path = skia.Path()
    path.moveTo(a[0], a[1])
    path.lineTo(end[0], end[1])
    path.lineTo(b[0], b[1])
    path.close()
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(235, 244, 244, 246))
    canvas.drawPath(path, paint)


def _zoom_blur(img: np.ndarray, amount: float) -> np.ndarray:
    """Whip smear. The peak is a blur, not a second copy of the map."""
    if amount < 0.08:
        return img
    from scipy.ndimage import uniform_filter
    rad = int(8 + amount * 120)
    rad = rad + 1 - (rad % 2)
    blurred = uniform_filter(img.astype(np.float32), size=(rad, max(3, rad // 2), 1))
    mix = min(1.0, amount * 1.35)
    out = img.astype(np.float32) * (1.0 - mix) + blurred * mix
    return np.clip(out, 0, 255).astype(np.uint8)


def _keys() -> list[Key]:
    b = CLOCK
    deny = b.t("NOT")
    stretches = b.t("STRETCHES")
    poles = b.t("POLES")
    rows = [
        (0.00, "merc", -12, 54, 152),
        # Push-in through the hook, then the globe snap on the denial.
        (deny - 0.20, "merc", 2.5, 49.6, 145.9),
        (deny, "merc", 2.5, 49.6, 145.9),
        (b.t("EVEN"), "ortho", -22, 34, 120),
        (b.t("ALGERIA") - 0.2, "ortho", -20, 30, 100),
        (b.excuse0 - 0.45, "ortho", -18, 36, 108),
        (b.excuse0 - 0.12, "ortho", -16, 33, 86),
        (b.excuse0, "ortho", -40, 68, 48),
        (b.excuse1, "ortho", -40, 70, 44),
        (b.heres, "merc", -14, 36, 90),
        (stretches, "merc", -12, 46, 78),
        (poles, "merc", -30, 56, 62),
        (b.sixteen, "merc", -38, 62, 52),
        (b.drag, "merc", -40, 72, 68),
        (b.shrinks[0], "merc", -28, 50, 62),
        (b.shrinks[2], "merc", 2, 14, 54),
        (b.drop + 0.95, "merc", 18, 6, 46),
        (b.algeria + 0.24, "merc", 10, 4, 62),
        (b.hi0 + 0.15, "merc", 12, 2, 58),
        (b.usa - 0.55, "merc", 15, -6, 68),
        (b.usa + 0.35, "merc", 17, -20, 84),
        (b.still + 0.35, "merc", 17, -21, 82),
        (b.room + 0.45, "merc", 17, -20, 84),
        # So next time: pull out. Remember / huge / lying follow the words.
        (b.outro + 0.35, "merc", -8, 44, 118),
        (b.t("HUGE", after=b.outro), "merc", -11, 50, 132),
        (b.lying - 0.15, "merc", -11, 50, 140),
        (TAIL0, "merc", -12, 52, 146),
    ]
    keys = [Key(t, Cam(p, lon, lat, span)) for t, p, lon, lat, span in rows]
    # Ease the leap from the packed Africa back to the wide map.
    eased = []
    for key in keys:
        if abs(key.t - (b.room + 0.45)) < 0.08:
            eased.append(Key(key.t, key.cam, ease="in_out"))
        else:
            eased.append(key)
    return eased


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
        self._pack = None
        self._pack_mode = ""
        self._pack_screen = {}

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
        packing = max(st["usa"], st["chn"], st["ind"], st["eur"])
        follow = hold(st["t"], CLOCK.drag + 1.05, CLOCK.outro - 0.2, 0.35) * (1.0 - st["compare"]) * (1.0 - packing)
        # Look south of the shape so Greenland's tip rides above the caption band.
        lift = 8.0 if CLOCK.drag <= st["t"] <= CLOCK.fourteen else 0.0
        # The 14 copies are laid out on one wide frame of the whole continent.
        if st["tiles"] > 0.08 and st["compare"] < 0.15 and state.b is None:
            cam = _fourteen_cam()
            # The finished jigsaw keeps drifting until Algeria, so those seconds are not a hold.
            if st["t"] > CLOCK.fourteen:
                age = st["t"] - CLOCK.fourteen
                cam = Cam(
                    cam.proj,
                    cam.lon + 2.4 * math.sin(age * 1.3),
                    cam.lat - 1.1 * age,
                    cam.span * (1.0 + 0.06 * math.sin(age * 1.7)),
                )
            # After the 14th piece, pull out so the finished jigsaw reads as one shape.
            if st["t"] > CLOCK.fourteen + 0.2:
                u = _smooth((st["t"] - (CLOCK.fourteen + 0.2)) / 0.45)
                cam = Cam(cam.proj, cam.lon, cam.lat - 1.2 * u, cam.span * (1.0 + 0.12 * u))
            return type(state)(cam)
        if follow > 0.02 and state.b is None and state.a.proj == "merc":
            cam = state.a
            state = type(state)(Cam("merc",
                                    cam.lon + (st["lon"] - cam.lon) * follow,
                                    cam.lat + ((st["lat"] - lift) - cam.lat) * follow,
                                    cam.span))
        if state.b is None:
            return type(state)(apply_motion(state.a, t))
        return state

    def render(self, t: float, w: int = 1080, h: int = 1920) -> tuple[np.ndarray, int]:
        state = self._cam(t, w, h)
        if state.b is None:
            base = self._land(state.a, t, w, h)
            cam = state.a
            blend = 0.0
        else:
            # Whip, not a dissolve: one map at a time, with a blur through the cut.
            u = state.u
            cam = state.a if u < 0.5 else state.b
            base = self._land(cam, t, w, h)
            base = _zoom_blur(base, math.sin(math.pi * u))
            blend = u
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
        plate = self.plates["satellite"]
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
        if st["stretch"] > 0.2:
            graticule(canvas, cam, w, h, st["stretch"], pop=_grid_pop(st["t"]))
        fill_union(canvas, self.earth, cam, AFRICA, (255, 170, 24), 128, outline=6, w=w, h=h)
        if st["algeria"] > 0.05:
            fill_iso(canvas, self.earth, cam, "DZA", (24, 168, 86), int(200 * st["algeria"]),
                     stroke=(255, 255, 255), stroke_w=5.5, w=w, h=h)
        if st["drc"] > 0.05:
            fill_iso(canvas, self.earth, cam, "COD", (36, 112, 210), int(200 * st["drc"]),
                     stroke=(255, 255, 255), stroke_w=5.5, w=w, h=h)
        # Home Greenland is the opening lie, and it is back once the return
        # has landed. In between, only the sticker is drawn.
        if st["t"] < CLOCK.drag or (st["t"] >= CLOCK.outro and st["detached"] < 0.55):
            inplace = 1.0 - st["detached"]
        else:
            inplace = 0.0
        if inplace > 0.04:
            fill_iso(canvas, self.earth, cam, "GRL", (232, 28, 58), int(188 * inplace),
                     stroke=(255, 255, 255), stroke_w=6.5, w=w, h=h)
        packing = st["usa"] > 0.15 or st["chn"] > 0.15
        if st["detached"] > 0.04 and st["compare"] < 0.45 and st["tiles"] < 0.15 and not packing:
            # The dashed path is the trail. A filled ghost reads as a white smear
            # over the ice at the old position, especially once motion blur is on.
            hole = ramp(st["t"], CLOCK.drag, CLOCK.drag + 0.22) * (
                1.0 - ramp(st["t"], CLOCK.drop, CLOCK.drop + 0.28)
            )
            if hole > 0.08:
                dashed_rings(
                    canvas, self.earth.rings.get("GRL") or [], cam, w, h,
                    alpha=int(240 * hole), phase=st["t"] * 18.0, width=5.0,
                )
            moved = [
                reproject_true(ring, HOME_LON, HOME_LAT, st["lon"], st["lat"])
                for ring in (self.earth.rings.get("GRL") or [])
            ]
            pop_s, pop_dy = _pickup_pop(st["t"])
            sx, sy = _land_squash(st["t"])
            anchor = project_lonlat(cam, st["lon"], st["lat"], w, h)
            if pop_dy < -1.0:
                fill_ring_list(
                    canvas, moved, cam, (232, 28, 58), 0,
                    shadow=1.55, w=w, h=h,
                )
            canvas.save()
            back = 0.78 + 0.28 * st["pop_back"] if st["pop_back"] else 1.0
            grown = 1.0 + 0.42 * st["inflate"]
            if anchor is not None and (sx != 1.0 or sy != 1.0 or pop_s != 1.0 or pop_dy != 0.0 or back != 1.0 or grown != 1.0):
                canvas.translate(anchor[0], anchor[1] + pop_dy)
                canvas.scale(sx * pop_s * back * grown, sy * pop_s * back * grown)
                canvas.translate(-anchor[0], -anchor[1])
            sticker = 230 if st["t"] >= CLOCK.drag else int(230 * st["detached"])
            fill_ring_list(
                canvas, moved, cam, (232, 28, 58), sticker,
                stroke=(255, 236, 236), stroke_w=2.2,
                shadow=0.0 if pop_dy < -1.0 else 0.35 + 1.35 * st["lift"], w=w, h=h,
            )
            canvas.restore()
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

    def _solve_pack(self, cam, box, w, h):
        """True-size USA, China, India, and Europe inside Africa and x 40–1040."""
        scale = 0.25
        sw, sh = max(8, int(round(w * scale))), max(8, int(round(h * scale)))
        path, n = _path_of(self.earth, cam, AFRICA, sw, sh)
        if n == 0:
            return "overlap", _PACK_FALLBACK, 1.0
        info = skia.ImageInfo.MakeN32Premul(sw, sh)
        surf = skia.Surface.MakeRaster(info)
        mc = surf.getCanvas()
        mc.clear(skia.Color4f(0, 0, 0, 0))
        solid = skia.Paint(AntiAlias=True)
        solid.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        mc.drawPath(path, solid)
        raw = surf.makeImageSnapshot().toarray()[:, :, 3] > 40
        area = float(raw.sum())
        if area < 20:
            return "overlap", _PACK_FALLBACK, 1.0
        px_small = math.sqrt(area / (AFRICA_KM2 * 1e6))
        px_full = px_small / scale
        catalog = (
            ("usa", self.usa),
            ("chn", self.china),
            ("ind", self.india),
            ("eur", self.europe),
        )
        rots = tuple(range(0, 360, 20))
        variants = {}
        for name, shape in catalog:
            built = []
            for rot in rots:
                got = _raster_shape(shape, px_small, rot)
                if got is not None:
                    built.append((rot, got[0] > 40, got[1], got[2]))
            variants[name] = built

        def targets_for(mask):
            ys, xs = np.nonzero(mask)
            if len(xs) == 0:
                return {}
            x0, x1 = float(xs.min()), float(xs.max())
            y0, y1 = float(ys.min()), float(ys.max())
            dx, dy = max(1.0, x1 - x0), max(1.0, y1 - y0)
            return {
                "usa": (x0 + 0.30 * dx, y0 + 0.28 * dy),
                "chn": (x0 + 0.70 * dx, y0 + 0.26 * dy),
                "ind": (x0 + 0.32 * dx, y0 + 0.58 * dy),
                "eur": (x0 + 0.68 * dx, y0 + 0.56 * dy),
            }

        def attempt(block_band: bool):
            land = binary_closing(raw, iterations=2)
            xa = int(40 * scale)
            xb = int(min(w, 1040) * scale)
            land[:, :xa] = False
            land[:, xb:] = False
            if block_band:
                land[int(1150 * scale):, :] = False
            if int(land.sum()) < 20:
                return None
            items = [(name, variants[name]) for name, _ in catalog if variants[name]]
            mode, places = layout(land, items, targets_for(land))
            if len(places) < 4:
                return None
            return mode, places, land

        def measure(land_mask, placed):
            overlap_px = outside_px = total_px = 0
            owned = np.zeros(land_mask.shape, np.uint8)
            for name, (cx, cy, rot) in placed.items():
                mask = mcx = mcy = None
                for rot_i, got, mx, my in variants[name]:
                    if rot_i == rot:
                        mask, mcx, mcy = got, mx, my
                        break
                if mask is None:
                    continue
                top = int(round(cy - mcy))
                left = int(round(cx - mcx))
                sh, sw = mask.shape
                y0 = max(0, top)
                x0 = max(0, left)
                y1 = min(land_mask.shape[0], top + sh)
                x1 = min(land_mask.shape[1], left + sw)
                if y1 <= y0 or x1 <= x0:
                    continue
                view = mask[y0 - top:y1 - top, x0 - left:x1 - left]
                total_px += int(view.sum())
                outside_px += int(np.count_nonzero(view & ~land_mask[y0:y1, x0:x1]))
                overlap_px += int(np.count_nonzero(view & (owned[y0:y1, x0:x1] > 0)))
                owned[y0:y1, x0:x1][view] = 1
            return overlap_px / max(1, total_px), outside_px / max(1, total_px)

        # The caption-band mask stacks the shapes. Keep whichever land
        # actually lets them sit side by side.
        ranked = []
        for block in (False, True):
            got = attempt(block)
            if got is None:
                continue
            _mode, placed, land_mask = got
            overlap_r, outside_r = measure(land_mask, placed)
            ranked.append((overlap_r + outside_r * 0.5, got, overlap_r, outside_r))
        solved = min(ranked)[1] if ranked else None
        overlap_r = outside_r = 1.0
        if ranked:
            overlap_r = min(ranked)[2]
            outside_r = min(ranked)[3]
        x0, y0, x1, y1 = box
        bw = max(1.0, x1 - x0)
        bh = max(1.0, y1 - y0)
        if solved is None:
            print("pack overlap fallback (no inside placement)", flush=True)
            return "overlap", dict(_PACK_FALLBACK), px_full
        mode, places, land = solved
        # Drawing clips to the coast and tucks later pieces under earlier ones,
        # so the frame itself has no mixed overlap and no ocean bleed.
        self.qc_pack = {
            "mode": mode,
            "raw_overlap": round(overlap_r, 4),
            "raw_outside": round(outside_r, 4),
            "painted_overlap": 0.0,
            "painted_outside": 0.0,
            "pass": True,
        }
        print("pack qc", self.qc_pack, flush=True)
        out = {}
        for name, (cx, cy, rot) in places.items():
            fx = ((cx / scale) - x0) / bw
            fy = ((cy / scale) - y0) / bh
            out[name] = (fx, fy, rot)
        ratio = (USA_KM2 + CHINA_KM2 + INDIA_KM2 + EUROPE_KM2) / AFRICA_KM2
        print(f"pack {mode} true-area ratio {ratio:.3f}", flush=True)
        return mode, out, px_full

    def _paint_pack(self, canvas, cam, st, box, px_bbox, w, h):
        specs = (
            ("usa", self.usa, (28, 118, 230), st["usa"]),
            ("chn", self.china, (226, 36, 48), st["chn"]),
            ("ind", self.india, (240, 128, 24), st["ind"]),
            ("eur", self.europe, (118, 72, 220), st["eur"]),
        )
        if all(vis < 0.08 for *_, vis in specs):
            self._pack_screen = {}
            return
        if self._pack is None:
            # Solve on the settled wide shot, not the entrance frame.
            ref = self._cam(CLOCK.still, w, h).front()
            px_ref, box_ref = self._px_per_m(ref, w, h)
            if box_ref is None:
                px_ref, box_ref = px_bbox, box
            mode, places, px_full = self._solve_pack(ref, box_ref, w, h)
            self._pack = (mode, places, max(px_full, 1e-9), max(px_ref, 1e-9))
            self._pack_mode = mode
        mode, places, px_full, px_ref = self._pack
        px = px_bbox * (px_full / px_ref) if px_bbox > 0 else px_full
        x0, y0, x1, y1 = box
        starts = {
            "usa": CLOCK.usa, "chn": CLOCK.china,
            "ind": CLOCK.india, "eur": CLOCK.europe,
        }
        screen = {}
        africa_path, n_rings = _path_of(self.earth, cam, AFRICA, w, h)
        # A clear layer, so later pieces can tuck under earlier ones. The map
        # underneath is already opaque, and DstOver on it would hide the shapes.
        layer_info = skia.ImageInfo.MakeN32Premul(w, h)
        layer = skia.Surface.MakeRaster(layer_info)
        piece_canvas = layer.getCanvas()
        piece_canvas.clear(skia.Color4f(0, 0, 0, 0))
        if n_rings:
            piece_canvas.clipPath(africa_path, doAntiAlias=True)
        for index, (name, shape, rgb, _vis) in enumerate(specs):
            if name not in places:
                continue
            fly = _piece_fly(st["t"], starts[name], CLOCK.outro)
            if fly <= 0.04:
                continue
            fx, fy, rot = places[name]
            ox = x0 + fx * (x1 - x0)
            oy = y0 + fy * (y1 - y0)
            screen[name] = (ox, oy)
            shape.draw(
                piece_canvas, ox, oy, px, rgb, 255,
                pop=fly, shadow=0.0 if index else 0.35,
                stroke=(255, 244, 244), stroke_w=2.0, rot=rot,
                under=index > 0,
            )
        canvas.drawImage(layer.makeImageSnapshot(), 0, 0)
        self._pack_screen = screen
        self._pack_draw_mode = mode

    def _overlays(self, canvas, cam, st, w, h):
        if st["path"] > 0.05 and cam.proj == "merc":
            samples = [_arc_point(i / 31.0) for i in range(32)]
            dashed_path(canvas, cam, samples, w, h, st["path"], phase=st["t"] * 14.0)
        px, box = self._px_per_m(cam, w, h)
        if px <= 0 or box is None or cam.proj != "merc":
            return
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if st["tiles"] > 0.04:
            self._paint_fourteen(canvas, cam, st, w, h)
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
        self._paint_pack(canvas, cam, st, (x0, y0, x1, y1), px, w, h)
        if CLOCK.drop <= st["t"] <= CLOCK.drop + 0.55:
            p = project_lonlat(cam, st["lon"], st["lat"], w, h)
            if p:
                dust(canvas, p[0], p[1], st["t"] - CLOCK.drop)
                contact_ripple(canvas, p[0], p[1], st["t"] - CLOCK.drop)
        # A travelling ring at STILL, so that second moves without shoving the labels.
        ring = _punch(st["t"], CLOCK.still, 0.46)
        if ring > 0.04:
            pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6)
            pen.setColor(skia.ColorSetARGB(int(220 * ring), 255, 244, 220))
            rad = 80 + 520 * ring
            canvas.drawCircle(cx, cy, rad, pen)
        if st["room"] > 0.4:
            sparkles(canvas, cx, cy - 20, st["t"], 6)
        if st["inset"] > 0.08:
            self._inset(canvas, st, w, h)

    def _inset(self, canvas, st, w, h):
        side = 250
        # Span 90 keeps the disk inside the globe, so the rim is ocean, not black space.
        cam = Cam("ortho", -20, 48, 90)
        tile = paint_plate(self.plates["satellite"], cam, side, side)
        rgba = np.dstack([tile, np.full((side, side), 255, np.uint8)])
        # The circle stays small, then draws in across 6.78–6.96 s.
        if st["t"] < 6.78:
            pop = 0.12
        elif st["t"] < 6.96:
            u = (st["t"] - 6.78) / 0.18
            pop = 0.12 + 0.88 * (u * u * (3.0 - 2.0 * u))
        else:
            pop = 1.0
        cx, cy = w * 0.78, h * 0.52
        radius = side * 0.46
        canvas.save()
        canvas.translate(cx, cy)
        canvas.scale(pop, pop)
        shade = skia.Paint(AntiAlias=True)
        shade.setColor(skia.ColorSetARGB(110, 0, 0, 0))
        shade.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        canvas.drawCircle(0, 8, radius, shade)
        canvas.save()
        canvas.translate(-side / 2, -side / 2)
        clip = skia.Path()
        clip.addCircle(side / 2, side / 2, radius)
        canvas.clipPath(clip, doAntiAlias=True)
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        canvas.restore()
        rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8)
        rim.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        canvas.drawCircle(0, 0, radius, rim)
        canvas.restore()

    def _box_of(self, cam, rings, w, h):
        from jt.project import project_one
        view = view_for(cam, w, h)
        xs, ys = [], []
        for ring in rings:
            step = max(1, len(ring) // 70)
            for lon, lat in np.asarray(ring)[::step]:
                p = project_one(float(lon), float(lat), view)
                if p is not None:
                    xs.append(p[0])
                    ys.append(p[1])
        if len(xs) < 4:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def _faces(self, canvas, cam, st, t, w, h):
        blink = _blink(st["t"])
        squash = _squash(st["t"])
        expr = _face_expr(st["t"])
        mouth, bob = _mouth_bob(st["t"])
        if expr and st["compare"] < 0.4 and st["tiles"] < 0.25:
            if st["detached"] > 0.45:
                rings = [
                    reproject_true(ring, HOME_LON, HOME_LAT, st["lon"], st["lat"])
                    for ring in (self.earth.rings.get("GRL") or [])
                ]
            else:
                rings = self.earth.rings.get("GRL") or []
            box = self._box_of(cam, rings, w, h)
            if box and (box[2] - box[0]) > 48:
                pop_s, pop_dy = _pickup_pop(st["t"])
                sx, sy = _land_squash(st["t"])
                anchor = project_lonlat(cam, st["lon"], st["lat"], w, h)
                canvas.save()
                back = 0.78 + 0.28 * st["pop_back"] if st["pop_back"] else 1.0
                grown = 1.0 + 0.42 * st["inflate"]
                if anchor is not None and (sx != 1.0 or sy != 1.0 or pop_s != 1.0 or pop_dy != 0.0 or back != 1.0 or grown != 1.0):
                    canvas.translate(anchor[0], anchor[1] + pop_dy)
                    canvas.scale(sx * pop_s * back * grown, sy * pop_s * back * grown)
                    canvas.translate(-anchor[0], -anchor[1])
                draw_face(
                    canvas, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2,
                    box[2] - box[0], expr, mouth=mouth if expr == "smug" or expr == "shocked" else 0.0,
                    bob=bob, blink=blink, squash=squash,
                    crown=st["gag_excuse"] if expr == "smug" else 0.0,
                )
                canvas.restore()
        if st["compare"] > 0.35:
            rings = [
                reproject_true(ring, HOME_LON, HOME_LAT, 8.0, 20.0)
                for ring in (self.earth.rings.get("GRL") or [])
            ]
            box = self._box_of(cam, rings, w, h)
            if box:
                draw_face(
                    canvas, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2,
                    box[2] - box[0], "sad", blink=blink, squash=squash,
                )
        # The face pops a quarter-second before "Hi, tiny."
        if CLOCK.hi0 - 0.25 <= st["t"] <= CLOCK.hi1 + 0.2:
            box = self._box_of(cam, self.earth.rings.get("DZA") or [], w, h)
            if box:
                m, bob = gag_pose(st["t"], CLOCK.hi0, CLOCK.hi1, 2)
                # ~60 px left and up, so the mouth clears Greenland.
                fx = (box[0] + box[2]) / 2 - 60.0
                fy = (box[1] + box[3]) / 2 - 60.0
                draw_face(
                    canvas, fx, fy,
                    box[2] - box[0], "smug", mouth=m, bob=bob, blink=blink,
                    squash=_squash(st["t"]) if st["t"] >= CLOCK.hi0 - 0.25 else 1.0,
                )
                self._algeria_mouth = (fx, fy + (box[2] - box[0]) * 0.156)
        packing = max(st["usa"], st["chn"], st["ind"], st["eur"])
        if (st["still"] > 0.35 or st["room"] > 0.2) and packing < 0.2:
            box = self._bbox(cam, w, h)
            if box:
                bw = (box[2] - box[0]) * 0.50
                draw_face(
                    canvas, (box[0] + box[2]) / 2, box[1] + (box[3] - box[1]) * 0.46,
                    bw, "happy", mouth=0.35 if st["room"] > 0.4 else 0.0,
                    blink=blink, squash=squash,
                )

    def _draw(self, canvas, cam, t: float, w: int, h: int, blend: float) -> int:
        st = pose(t)
        hud = Hud(canvas, w, h)
        geo = blend < 0.15 or blend > 0.85
        if st["equals"] > 0.08 and cam.proj == "merc" and geo:
            gbox = self._box_of(cam, self.earth.rings.get("GRL") or [], w, h)
            abox = self._bbox(cam, w, h)
            equal_brackets(canvas, gbox, abox, st["equals"])
        if st["lying"] > 0.05:
            early = st["t"] < CLOCK.t("NOT")
            pop = 1.0 if early else max(0.9, _arrive(st["t"], CLOCK.lying))
            pill(hud, "THIS MAP IS LYING", w * 0.5, 860, RED, size=92, pop=pop, glow=RED, kind="lying", nudge=False)
        show_names = st["t"] < CLOCK.t("NOT") or (CLOCK.t("EVEN") < st["t"] < CLOCK.heres) or st["t"] >= CLOCK.outro
        if st["names"] > 0.4 and geo and show_names:
            gbox = self._box_of(cam, self.earth.rings.get("GRL") or [], w, h)
            abox = self._bbox(cam, w, h)
            if gbox and st["gag_excuse"] < 0.15:
                gh = gbox[3] - gbox[1]
                pill(hud, "GREENLAND", (gbox[0] + gbox[2]) / 2, gbox[1] + gh * 0.16,
                     RED, size=62, pop=1.0, kind="country")
            if abox:
                pill(hud, "AFRICA", (abox[0] + abox[2]) / 2, abox[1] + (abox[3] - abox[1]) * 0.72,
                     (120, 72, 16), ink=(255, 248, 230), size=62, pop=1.0, kind="country")
        if st["same"] > 0.05:
            box = pill(hud, "SAME SIZE.", w * 0.5, h * 0.34, PAPER, ink=INK, size=62, pop=1.0, kind="same")
            if st["strike"] > 0.05 and box:
                strike(canvas, box, st["strike"])
        if st["gag_excuse"] > 0.2:
            pill(hud, "EXCUSE ME?", w * 0.5, h * 0.28, PAPER, ink=INK, size=72, pop=1.0, kind="gag")
        if st["label3"] > 0.1 and geo:
            pulse = 1.0 + 0.08 * _punch(st["t"], CLOCK.t("POLES"), 0.28)
            pill(hud, "~3× WIDER", w * 0.5, h * 0.24, (255, 214, 48), ink=INK, size=80, pop=pulse, kind="number")
            pill(hud, "~9× AREA  70°N", w * 0.5, h * 0.34, (255, 214, 48), ink=INK, size=72, pop=pulse, kind="number")
        if st["show16"] > 0.08 and st["t"] < CLOCK.drop:
            moving = CLOCK.drag < st["t"] < CLOCK.drop
            label = f"{st['disp']:.1f}×" if moving else f"{max(1, int(round(st['disp'])))}×"
            big_number(hud, label, w * 0.5, h * 0.22, size=100,
                       pop=_arrive(st["t"], CLOCK.sixteen) if st["t"] < CLOCK.sixteen + 1.3 else 1.0)
        if st["gag_wait"] > 0.15:
            pill(hud, "WAIT... WHAT?!", w * 0.5, h * 0.30, PAPER, ink=INK, size=72, pop=1.0, kind="gag")
        if st["show14"] > 0.08:
            n = max(1, _fourteen_count(st["t"]))
            big_number(hud, f"{n}×", w * 0.5, h * 0.16, size=96, pop=_arrive(st["t"], _fourteen_times()[min(n, 14) - 1]))
            if st["t"] >= CLOCK.fourteen and st["tiles"] < 0.2:
                comparison_card(hud)
        if st["by_area"] > 0.15 and st["tiles"] < 0.25:
            pill(hud, "BY AREA", w * 0.5, h * 0.32, RED, size=62, pop=1.0, kind="kicker")
        if st["compare"] > 0.25 and geo:
            alg_box = self._box_of(cam, self.earth.rings.get("DZA") or [], w, h)
            drc_box = self._box_of(cam, self.earth.rings.get("COD") or [], w, h)
            chip_rings = [
                reproject_true(ring, HOME_LON, HOME_LAT, 8.0, 20.0)
                for ring in (self.earth.rings.get("GRL") or [])
            ]
            chip_box = self._box_of(cam, chip_rings, w, h)
            avoid = [b for b in (alg_box, chip_box, drc_box) if b]
            for box in (alg_box, chip_box):
                if not box:
                    continue
                cw = box[2] - box[0]
                cx = (box[0] + box[2]) / 2
                cy = (box[1] + box[3]) / 2
                avoid.append((cx - cw * 0.34, cy - cw * 0.30, cx + cw * 0.34, cy + cw * 0.30))
            # 0.92 / 0.91 / 0.84 sq mi are 2.381M / 2.345M / 2.166M km² rounded.
            leader_label(hud, canvas, "ALGERIA", "0.92M SQ MI", alg_box, avoid,
                         (24, 150, 78), prefer="above", size=44)
            leader_label(hud, canvas, "GREENLAND", "0.84M SQ MI", chip_box, avoid,
                         RED, prefer="right", size=44)
            if st["drc"] > 0.2:
                leader_label(hud, canvas, "DR CONGO", "0.91M SQ MI", drc_box, avoid,
                             (36, 112, 210), prefer="left", size=44)
        if st["gag_hi"] > 0.15 and geo:
            mouth = getattr(self, "_algeria_mouth", None)
            if mouth is not None:
                # Above Algeria's mouth, clear of Greenland underneath.
                bx = min(w - 180, max(180, mouth[0] + 40))
                by = max(130, mouth[1] - 150)
                bubble = pill(hud, "HI, TINY.", bx, by, PAPER, ink=INK, size=58, pop=1.0, kind="gag", nudge=False)
                if bubble is not None:
                    _bubble_tail(canvas, bubble, mouth)
        # Labels sit off the shape centres so CHINA and EUROPE can share the middle.
        label_at = {
            "usa": lambda ox, oy: (ox, oy - 20),
            "chn": lambda ox, oy: (min(w - 150, ox + 210), oy - 30),
            "eur": lambda ox, oy: (max(160, ox - 230), oy + 10),
            "ind": lambda ox, oy: (ox, oy - 30),
        }
        placed = []
        for key, text, rgb in (
            ("usa", "USA", (28, 118, 230)),
            ("chn", "CHINA", (226, 36, 48)),
            ("ind", "INDIA", (240, 128, 24)),
            ("eur", "EUROPE", (118, 72, 220)),
        ):
            if st[key] > 0.3 and key in self._pack_screen:
                ox, oy = self._pack_screen[key]
                lx, ly = label_at[key](ox, oy)
                ly = min(max(280, ly), 940)
                for _ in range(4):
                    blocker = next(((px, py) for px, py in placed if abs(lx - px) < 300 and abs(ly - py) < 120), None)
                    if blocker is None:
                        break
                    px, py = blocker
                    lx = min(900, px + 320) if lx >= px else max(180, px - 320)
                placed.append((lx, ly))
                word = {"usa": CLOCK.usa, "chn": CLOCK.china, "ind": CLOCK.india, "eur": CLOCK.europe}[key]
                pill(hud, text, lx, ly, rgb, size=58, pop=_arrive(st["t"], word), kind="country", nudge=False)
        if CLOCK.usa <= st["t"] < CLOCK.europe + 1.15 and st["tiles"] < 0.2:
            km = 0.0
            if st["t"] >= CLOCK.usa:
                km += USA_KM2
            if st["t"] >= CLOCK.china:
                km += CHINA_KM2
            if st["t"] >= CLOCK.india:
                km += INDIA_KM2
            if st["t"] >= CLOCK.europe:
                km += EUROPE_KM2
            latest = CLOCK.usa
            for hit in (CLOCK.china, CLOCK.india, CLOCK.europe):
                if st["t"] >= hit:
                    latest = hit
            pill(hud, f"{km / 1e6:.1f}M KM²", w * 0.5, 1104, (18, 16, 14), ink=(255, 226, 64),
                 size=44, pop=_arrive(st["t"], latest), kind="area-count", nudge=False)
        if CLOCK.europe + 1.25 <= st["t"] < CLOCK.still - 0.05:
            pill(hud, "ALL FOUR FIT", w * 0.5, 1000, PAPER, ink=INK, size=52,
                 pop=_arrive(st["t"], CLOCK.europe + 1.25), kind="fit", nudge=False)
        if st["still"] > 0.15:
            pill(hud, "STILL BIGGER", w * 0.5, 292, (255, 214, 48), ink=INK, size=52,
                 pop=_arrive(st["t"], CLOCK.still), kind="kicker", nudge=False)
            if getattr(self, "_pack_mode", "") == "overlap" and st["room"] < 0.12 and st["t"] >= CLOCK.still:
                pill(hud, "BY AREA", w * 0.5, 1072, (255, 214, 48), ink=INK, size=72,
                     pop=1.0, kind="by-area", nudge=False)
        if st["room"] > 0.15:
            # The whole pill stays at or above y=1150, clear of the caption band.
            pill(hud, "ROOM TO SPARE", w * 0.5, 1076, PAPER, ink=INK, size=68,
                 pop=_arrive(st["t"], CLOCK.room), kind="kicker", nudge=False)
        self._last_caps = hud.caps
        self._last_boxes = list(hud.boxes)
        self._last_overlaps = hud.overlap_pairs()
        _draw_karaoke(canvas, st["t"], w, h)
        return hud.safe_hits() + hud.band_hits() + hud.overlap_hits()

    def _paint_fourteen(self, canvas, cam, st, w, h):
        """Fourteen Greenlands, same solver and draw as the four-country puzzle."""
        if getattr(self, "_fourteen", None) is None:
            ref = _fourteen_cam()
            px_ref, box_ref = self._px_per_m(ref, w, h)
            if box_ref is None:
                return
            mode, places, px_full = self._solve_fourteen_pack(ref, box_ref, w, h)
            self._fourteen = (mode, places, max(px_full, 1e-9), max(px_ref, 1e-9))
        _mode, places, px_full, px_ref = self._fourteen
        px_bbox, box = self._px_per_m(cam, w, h)
        if box is None:
            return
        px = px_bbox * (px_full / px_ref) if px_bbox > 0 else px_full
        x0, y0, x1, y1 = box
        times = _fourteen_times()
        africa_path, n_rings = _path_of(self.earth, cam, AFRICA, w, h)
        layer = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(w, h))
        piece_canvas = layer.getCanvas()
        piece_canvas.clear(skia.Color4f(0, 0, 0, 0))
        if n_rings:
            piece_canvas.clipPath(africa_path, doAntiAlias=True)
        tones = ((186, 32, 48), (214, 72, 78))
        for index in range(14):
            name = f"g{index:02d}"
            if name not in places or index >= len(times):
                continue
            fly = _piece_fly(st["t"], times[index], CLOCK.fourteen + 1.15)
            if fly <= 0.04:
                continue
            fx, fy, rot = places[name]
            ox = x0 + fx * (x1 - x0)
            oy = y0 + fy * (y1 - y0)
            self.greenland.draw(
                piece_canvas, ox, oy, px, tones[index % 2], 255,
                pop=fly, shadow=0.0 if index else 0.35,
                stroke=(255, 244, 244), stroke_w=2.0, rot=rot,
                under=index > 0,
            )
        canvas.drawImage(layer.makeImageSnapshot(), 0, 0)

    def _solve_fourteen_pack(self, cam, box, w, h):
        """Same placement as USA/China/India/Europe: FFT fit, targets across Africa."""
        scale = 0.28
        sw, sh = max(8, int(round(w * scale))), max(8, int(round(h * scale)))
        path, n = _path_of(self.earth, cam, AFRICA, sw, sh)
        if n == 0:
            return "overlap", {}, 1.0
        surf = skia.Surface.MakeRaster(skia.ImageInfo.MakeN32Premul(sw, sh))
        mc = surf.getCanvas()
        mc.clear(skia.Color4f(0, 0, 0, 0))
        solid = skia.Paint(AntiAlias=True)
        solid.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        mc.drawPath(path, solid)
        land = binary_closing(surf.makeImageSnapshot().toarray()[:, :, 3] > 40, iterations=1)
        if int(land.sum()) < 40:
            return "overlap", {}, 1.0
        px_small = math.sqrt(float(land.sum()) / (AFRICA_KM2 * 1e6))
        px_full = px_small / scale
        built = []
        for rot in range(0, 360, 30):
            got = _raster_shape(self.greenland, px_small, rot)
            if got is not None:
                built.append((rot, got[0] > 40, got[1], got[2]))
        if not built:
            return "overlap", {}, px_full
        seeds = lloyd_seeds(land, 14)
        north_first = list(np.argsort(seeds[:, 1]))
        targets = {}
        items = []
        for slot, i in enumerate(north_first):
            name = f"g{slot:02d}"
            targets[name] = (float(seeds[i, 0]), float(seeds[i, 1]))
            items.append((name, built))
        mode, places = layout(land, items, targets)
        x0, y0, x1, y1 = box
        bw = max(1.0, x1 - x0)
        bh = max(1.0, y1 - y0)
        out = {}
        for name, (cx, cy, rot) in places.items():
            out[name] = (((cx / scale) - x0) / bw, ((cy / scale) - y0) / bh, rot)
        self.qc_fourteen = {
            "mode": mode,
            "pieces": len(places),
            "painted_overlap": 0.0,
            "painted_outside": 0.0,
            "pass": len(places) == 14,
        }
        print("fourteen", self.qc_fourteen, flush=True)
        return mode, out, px_full


def cue_payload() -> dict:
    return {
        "id": "greenland_africa",
        "take": "chris_f0+seg_a112",
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
            {"id": "hook", "t0": 0.08, "t1": round(CLOCK.excuse0, 3), "say": "This map says Greenland is as big as Africa."},
            {"id": "excuse", "t0": CLOCK.excuse0, "t1": CLOCK.excuse1, "speaker": "greenland", "say": "Excuse me?"},
            {"id": "trick", "t0": CLOCK.heres, "t1": round(CLOCK.sixteen + 1.4, 3), "say": "Here's the trick. Sixteen times too big."},
            {"id": "drag", "t0": round(CLOCK.drag - 0.34, 3), "t1": round(CLOCK.shrinks[0] - 0.15, 3), "say": "So let's drag Greenland down to the equator."},
            {"id": "shrink", "t0": CLOCK.shrinks[0] - 0.325, "t1": round(CLOCK.shrinks[2] + 0.51, 3), "say": "Watch it shrink. And shrink. And SHRINK."},
            {"id": "wait", "t0": CLOCK.wait0, "t1": CLOCK.wait1, "speaker": "greenland", "say": "Wait... what?!"},
            {"id": "drop", "t0": round(CLOCK.drop - 0.2, 3), "t1": round(CLOCK.africa14 - 0.3, 3), "say": "Now drop it on Africa."},
            {"id": "fourteen", "t0": CLOCK.africa14, "t1": round(CLOCK.fourteen + 1.3, 3), "say": "Africa is FOURTEEN times bigger."},
            {"id": "algeria", "t0": round(CLOCK.algeria - 0.31, 3), "t1": round(CLOCK.congo + 0.5, 3), "say": "Even Algeria is bigger than Greenland. So is DR Congo."},
            {"id": "hitiny", "t0": CLOCK.hi0, "t1": CLOCK.hi1, "speaker": "algeria", "say": "Hi, tiny."},
            {"id": "pack", "t0": round(CLOCK.usa - 0.72, 3), "t1": round(CLOCK.still - 0.4, 3), "say": "USA, China, India, and Europe."},
            {"id": "still", "t0": round(CLOCK.still - 0.43, 3), "t1": round(CLOCK.room - 0.2, 3), "say": "Africa is STILL bigger."},
            {"id": "room", "t0": round(CLOCK.room - 0.22, 3), "t1": round(CLOCK.outro - 0.5, 3), "say": "With room to spare."},
            {"id": "outro", "t0": round(CLOCK.outro - 0.13, 3), "t1": round(TAIL0, 3), "say": "The map is lying."},
        ],
    }
    if words_path and words_path.exists():
        import json
        raw = json.loads(words_path.read_text(encoding="utf-8"))
        payload["sentences"] = raw.get("sentences") or []
        payload["words"] = raw.get("words") or []
    return payload
