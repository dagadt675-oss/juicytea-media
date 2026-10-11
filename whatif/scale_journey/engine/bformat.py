"""Format B episodes from the approved slate.

Presets: penny_fall, earth_hole, rice_chessboard, brick_tower, crowd_island.
The penny fall is the full picture. The others resolve to a timeline, an
instancer point cloud, and the shared words.json clock.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import yaml

from ui.outlines import OUTLINES, outline
from ui.words import voice_clock

from .instancer import cone_points, ellipse_points

G = 9.80665
MPH = 0.44704
FT = 0.3048


def terminal_mps(mass_kg: float, diameter_m: float, cd: float, rho: float = 1.204) -> float:
    area = math.pi * (diameter_m * 0.5) ** 2
    return math.sqrt((2.0 * mass_kg * G) / (rho * area * cd))


def fall_distance_speed(t: float, vt: float) -> tuple[float, float]:
    """Distance and speed for a drag-limited fall, from rest. t in seconds."""
    if t <= 0.0:
        return 0.0, 0.0
    k = G / vt
    v = vt * math.tanh(k * t)
    y = (vt * vt / G) * math.log(math.cosh(k * t))
    return y, v


def time_to_fall(distance_m: float, vt: float) -> float:
    lo, hi = 0.0, 10.0
    while fall_distance_speed(hi, vt)[0] < distance_m:
        hi *= 1.6
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if fall_distance_speed(mid, vt)[0] < distance_m:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _load(path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data.get("format") != "B":
        raise ValueError(f"{path} is not format B")
    return data


@dataclass
class BFrame:
    frame: int
    t: float
    phase: str
    primary: str
    primary_unit: str
    secondary: str
    secondary_unit: str
    label_primary: str
    label_secondary: str
    title_alpha: float
    ending_alpha: float
    dissolve: float
    pill_title: str
    pill_sub: str
    pill_alpha: float
    # Penny world position, metres. Unused presets leave these at 0.
    penny: tuple[float, float, float] = (0.0, 0.0, 0.0)
    cam: tuple[float, float, float] = (0.0, 0.0, 0.0)
    target: tuple[float, float, float] = (0.0, 0.0, 0.0)
    speed_mps: float = 0.0
    fallen_m: float = 0.0
    metric: str = ""
    roll: float = 1.0
    primary_prev: str = ""
    secondary_roll: float = 1.0
    secondary_prev: str = ""
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0)
    lens: float = 18.0


@dataclass
class BEpisode:
    raw: dict
    frames: list[BFrame] = field(default_factory=list)
    beats: list[dict] = field(default_factory=list)
    duration: float = 0.0
    notes: dict = field(default_factory=dict)

    @property
    def fps(self) -> int:
        return int(self.raw["fps"])

    @property
    def width(self) -> int:
        return int(self.raw["width"])

    @property
    def height(self) -> int:
        return int(self.raw["height"])

    @property
    def id(self) -> str:
        return self.raw["id"]


def _fade(t, t0, t1) -> float:
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    u = (t - t0) / (t1 - t0)
    return u * u * (3 - 2 * u)


def resolve_b(path) -> BEpisode:
    raw = _load(path)
    preset = raw["preset"]
    if preset == "penny_fall":
        return _penny(raw)
    if preset == "rice_chessboard":
        return _rice(raw)
    if preset == "earth_hole":
        return _hole(raw)
    if preset == "brick_tower":
        return _bricks(raw)
    if preset == "crowd_island":
        return _crowd(raw)
    raise ValueError(f"unknown format B preset {preset}")


def _lerp(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(len(a)))


def _interp(keys, t) -> float:
    if t <= keys[0][0]:
        return float(keys[0][1])
    if t >= keys[-1][0]:
        return float(keys[-1][1])
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            if t1 == t0:
                return float(v1)
            u = (t - t0) / (t1 - t0)
            u = u * u * (3.0 - 2.0 * u)
            return float(v0 + (v1 - v0) * u)
    return float(keys[-1][1])


def _held(rows, t):
    chosen = rows[0]
    for row in rows:
        if t + 1e-9 >= row[0]:
            chosen = row
    return chosen


# Southeast corner the coin must clear, measured on the Free Standard
# Empire State mesh after the tip is scaled to 443.2 m. The crown ledge
# is the hook. Lower values step out so the fall stays in open air.
# Local southeast corner of the tower shaft (scan junk farther out is ignored).
# The coin stays a few metres outside this corner, so the windows stay in frame.
_ESB_CORNERS = (
    (443.0, 18.0, 16.0),
    (381.0, 18.0, 16.0),
    (300.0, 42.0, 40.0),
    (200.0, 50.0, 48.0),
    (120.0, 70.0, 62.0),
    (60.0, 105.0, 95.0),
    (20.0, 120.0, 108.0),
    (0.0, 124.0, 102.0),
)


def _penny_xy(z: float) -> tuple[float, float]:
    keys = _ESB_CORNERS
    if z >= keys[0][0]:
        return keys[0][1], keys[0][2]
    if z <= keys[-1][0]:
        return keys[-1][1], keys[-1][2]
    for (z0, x0, y0), (z1, x1, y1) in zip(keys, keys[1:]):
        if z1 <= z <= z0:
            u = (z0 - z) / (z0 - z1) if z0 != z1 else 0.0
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return keys[-1][1], keys[-1][2]


def _penny(raw: dict) -> BEpisode:
    """Beat clock from the slate. Physics still supplies the 25 mph payoff.

    The picture is 40 s, not the ~34 s real fall: the counter holds each
    slate altitude, and the last four seconds rise back to the ledge.
    """
    q = raw["quantity"]
    vt = terminal_mps(float(q["mass_kg"]), float(q["diameter_m"]), float(q["cd"]), float(q["air_kg_m3"]))
    drop = float(outline("empire")["deck_m"])
    fall_t = time_to_fall(drop, vt)
    mph = vt / MPH
    fps = int(raw["fps"])
    duration = float(raw["timing"]["duration_sec"])
    n = int(round(duration * fps))
    # Visual altitude keeps moving. The counter holds; the picture does not.
    altitude = [
        (0.0, 1250.0),
        (2.7, 1250.0),
        (3.4, 1220.0),
        (7.0, 1000.0),
        (11.0, 780.0),
        (16.0, 480.0),
        (21.0, 240.0),
        (26.0, 90.0),
        (31.0, 18.0),
        (33.4, 4.0),
        (34.3, 0.2),
        (34.7, 1.15),
        (35.3, 0.15),
        (36.1, 0.15),
        (36.25, 1250.0),
        (40.0, 1250.0),
    ]
    # Speed reaches the ~25 mph terminal quickly, then holds. Height ticks with the picture.
    frames = []
    prev_feet, prev_mph = None, None
    feet_from, mph_from = "1,250", "0"
    feet_change = mph_change = 0.0
    for i in range(n):
        t = i / fps
        alt_ft = _interp(altitude, min(t, 40.0))
        if t < 2.7 or t >= 36.2:
            feet = 1250
        else:
            feet = max(0, int(round(alt_ft / 20.0)) * 20)
        if t < 3.0 or t >= 36.2:
            speed_mph = 0
        else:
            # Face-on terminal is ~25 mph and is reached in the first part of the fall.
            speed_mph = int(round(25.0 * _fade(t, 3.05, 5.4)))
        if t < 3.0:
            phase = "hook"
        elif t < 6.0:
            phase = "fall"
        elif t < 12.0:
            phase = "floors"
        elif t < 20.0:
            phase = "drag"
        elif t < 27.0:
            phase = "liberty"
        elif t < 31.0:
            phase = "edge"
        elif t < 36.0:
            phase = "hit"
        elif t < 39.2:
            phase = "rise"
        else:
            phase = "hold"
        feet_s = f"{int(feet):,}"
        mph_s = str(int(speed_mph))
        if feet_s != prev_feet:
            feet_from = prev_feet or feet_s
            feet_change = t
            prev_feet = feet_s
        if mph_s != prev_mph:
            mph_from = prev_mph or mph_s
            mph_change = t
            prev_mph = mph_s
        feet_roll = 1.0
        mph_roll = 1.0 if mph_from == mph_s else _fade(t, mph_change, mph_change + 0.28)
        title_alpha = 1.0 if phase in ("hook", "hold") or t >= 36.2 else 1.0 - _fade(t, 2.6, 3.3)
        ending_alpha = 0.0
        if 34.45 <= t < 36.15:
            ending_alpha = _fade(t, 34.45, 34.85) * (1.0 - _fade(t, 35.85, 36.12))
        pill_title, pill_sub, pill_a = "", "", 0.0
        if phase == "hook":
            pill_title, pill_sub, pill_a = "102ND FLOOR", "1,250 ft", 1.0
        elif phase == "fall":
            pill_title, pill_sub, pill_a = "TERMINAL VELOCITY", "25 mph", _fade(t, 3.15, 3.6)
        elif phase == "floors":
            pill_title, pill_sub, pill_a = "STATUE OF LIBERTY", "305 ft, further down", 1.0
        elif phase == "drag":
            pill_title, pill_sub, pill_a = "AIR HOLDS IT", "25 mph", 1.0
        elif phase == "liberty":
            pill_title, pill_sub, pill_a = "STATUE OF LIBERTY", "305 ft", 1.0
        elif phase == "hold":
            pill_title, pill_sub, pill_a = "102ND FLOOR", "1,250 ft", 1.0
        metric = f"{int(feet) * FT:,.0f} m"
        z_vis = alt_ft * FT
        ledge_xy = _penny_xy(drop)
        ledge_penny = (ledge_xy[0], ledge_xy[1], drop + 0.12)
        if t < 3.0 or t >= 36.2:
            penny = ledge_penny
        else:
            xy = _penny_xy(z_vis)
            penny = (xy[0], xy[1], z_vis + 0.08)
        hook_cam = (ledge_penny[0] + 6.5, ledge_penny[1] + 8.0, ledge_penny[2] + 8.0)
        hook_tgt = (ledge_penny[0] - 22.0, ledge_penny[1] - 18.0, ledge_penny[2] - 55.0)
        # Close chase. The coin stays large, the facade is the scale reference.
        # East of the coin, looking back at the facade and down the south street.
        chase_cam = (penny[0] + 2.4, penny[1] + 0.3, penny[2] + 1.4)
        chase_tgt = (penny[0] - 1.2, penny[1] + 2.2, penny[2] - 5.0)
        tight_cam = (penny[0] + 1.6, penny[1] + 0.15, penny[2] + 1.05)
        tight_tgt = (penny[0] - 0.6, penny[1] + 2.6, penny[2] - 4.2)
        hit_cam = (penny[0] + 1.5, penny[1] + 2.0, max(1.6, penny[2] + 1.2))
        hit_tgt = (penny[0] + 0.35, penny[1] + 0.7, max(0.7, penny[2] + 0.7))
        if t < 3.0 or t >= 36.2:
            cam, target, lens = hook_cam, hook_tgt, 16.0
        elif t < 4.4:
            u = _fade(t, 3.0, 4.4)
            cam = _lerp(hook_cam, chase_cam, u)
            target = _lerp(hook_tgt, chase_tgt, u)
            lens = 16.0 + (24.0 - 16.0) * u
        elif t < 18.0:
            cam, target, lens = chase_cam, chase_tgt, 24.0
        elif t < 31.0:
            u = _fade(t, 18.0, 22.0)
            cam = _lerp(chase_cam, tight_cam, u)
            target = _lerp(chase_tgt, tight_tgt, u)
            lens = 24.0 + (32.0 - 24.0) * u
        elif t < 33.2:
            u = _fade(t, 31.0, 33.2)
            cam = _lerp(tight_cam, hit_cam, u)
            target = _lerp(tight_tgt, hit_tgt, u)
            lens = 32.0 + (28.0 - 32.0) * u
        else:
            cam, target, lens = hit_cam, hit_tgt, 28.0
        if 33.2 <= t < 35.4:
            spin = (t - 33.2) * 16.0
            tilt = 0.35
        elif t < 3.0 or t >= 36.2:
            spin, tilt = 1.15, 0.25
        else:
            spin, tilt = 0.4 + t * 0.35, 0.45 + 0.25 * math.sin(t * 1.3)
        frames.append(
            BFrame(
                frame=i,
                t=t,
                phase=phase,
                primary=feet_s,
                primary_unit="ft",
                secondary=mph_s,
                secondary_unit="mph",
                label_primary="HEIGHT",
                label_secondary="SPEED",
                title_alpha=title_alpha,
                ending_alpha=ending_alpha,
                dissolve=0.0,
                pill_title=pill_title,
                pill_sub=pill_sub,
                pill_alpha=pill_a,
                penny=penny,
                cam=cam,
                target=target,
                speed_mps=vt if speed_mph == 25 else 0.0,
                fallen_m=max(0.0, drop - penny[2]),
                metric=metric,
                roll=feet_roll,
                primary_prev=feet_from,
                secondary_roll=mph_roll,
                secondary_prev=mph_from,
                rot=(spin, tilt, 0.05),
                lens=lens,
            )
        )
    say = raw.get("say", {})
    beats = [
        {"id": "hook", "narration": say.get("hook", raw["hook"]["say"]), "start": 0.0, "end": 3.0, "time_label": "1,250 ft / 0 mph"},
        {"id": "fall", "narration": say.get("fall", ""), "start": 3.0, "end": 6.0, "time_label": "1,200 ft / 25 mph"},
        {"id": "floors", "narration": say.get("floors", ""), "start": 6.0, "end": 12.0, "time_label": "1,000 ft / 25 mph"},
        {"id": "drag", "narration": say.get("drag", ""), "start": 12.0, "end": 20.0, "time_label": "700 ft / 25 mph"},
        {"id": "liberty", "narration": say.get("liberty", ""), "start": 20.0, "end": 27.0, "time_label": "305 ft / 25 mph"},
        {"id": "edge", "narration": say.get("edge", ""), "start": 27.0, "end": 31.0, "time_label": "25 mph"},
        {"id": "hit", "narration": say.get("hit", ""), "start": 31.0, "end": 36.0, "time_label": "0 ft"},
        {"id": "rise", "narration": say.get("rise", ""), "start": 36.0, "end": 40.0, "time_label": "1,250 ft"},
    ]
    ep = BEpisode(raw=raw, frames=frames, beats=beats, duration=duration)
    ep.notes = {
        "terminal_mps": vt,
        "terminal_mph": mph,
        "drop_m": drop,
        "drop_ft": drop / FT,
        "fall_sec": fall_t,
        "picture_sec": duration,
        "liberty_ft": 305.0,
        "empire": {k: v for k, v in outline("empire").items() if k != "source"},
    }
    return ep


def _rice(raw: dict) -> BEpisode:
    """All 64 squares. The heap is instanced. The camera is the thing that reaches orbit."""
    q = raw["quantity"]
    grains = 2**64 - 1
    mass = grains * float(q["grain_mass_kg"])
    volume = mass / float(q["bulk_density_kg_m3"])
    repose = math.radians(float(q["repose_deg"]))
    tan_t = math.tan(repose)
    height = (3.0 * volume * tan_t * tan_t / math.pi) ** (1.0 / 3.0)
    radius = height / tan_t
    points = cone_points(8000, radius, height, seed=int(raw.get("seed", 3)))
    # ISS-ish camera altitude. The heap is a few kilometres, not orbital.
    orbit_m = float(q["camera_altitude_m"])
    grain = float(q["grain_mass_kg"])
    mass_t = mass / 1000.0
    world_t = float(q.get("world_harvest_t", 544.7e6))
    years = mass_t / world_t
    square56_t = (2**55) * grain / 1000.0
    ep = _beat_episode(
        raw,
        primary_label="SQUARE",
        secondary_label="GRAINS",
        samples=[
            (0.0, "1", "1", "grain", "first"),
            (3.0, "10", "512", "grains", "pinch"),
            (8.0, "20", "29", "lb", "bag"),
            (13.0, "30", "13", "t", "house"),
            (19.0, "40", "14,000", "t", "town"),
            (25.0, "50", "14 million", "t", "mountain"),
            (32.0, "56", "900 million", "t", "year"),
            (38.0, "64", "2^64 − 1", "grains", "last"),
            (46.0, "64", "hundreds of years", "", "reality"),
        ],
    )
    ep.notes = {
        "grains": grains,
        "heap_height_m": height,
        "heap_radius_m": radius,
        "instance_cap": len(points),
        "camera_altitude_m": orbit_m,
        "years": years,
        "square56_t": square56_t,
        "world_harvest_t": world_t,
        "points_sample": points[:3],
    }
    return ep


def _feet(metres: float) -> float:
    return metres / FT


def _hole(raw: dict) -> BEpisode:
    """Descent through the layers, out in the Indian Ocean, then the way back."""
    layers = raw["layers"]
    one_way = float(raw["timing"]["one_way_sec"])
    ep = _beat_episode(
        raw,
        primary_label="DEPTH",
        secondary_label="LAYER",
        samples=[
            (float(item["t"]), item["depth"], item.get("temp") or item["name"], item.get("unit", ""), item["id"])
            for item in layers
        ],
    )
    ep.notes = {
        "one_way_sec": one_way,
        "loop": "pingpong",
        "exit": raw["exit"],
        "antipode": raw["antipode"],
    }
    return ep


def _bricks(raw: dict) -> BEpisode:
    q = raw["quantity"]
    course = float(q["course_m"])
    if "bricks" in q:
        n = int(q["bricks"])
    else:
        n = int(float(q["failure_n"]) / (float(q["mass_kg"]) * G))
    height = n * course
    dad = int(round((6 * FT) / course))
    liberty = int(round((305 * FT) / course))
    empire = int(round((1454 * FT) / course))
    burj = int(round((2717 * FT) / course))
    ep = _beat_episode(
        raw,
        primary_label="BRICKS",
        secondary_label="HEIGHT",
        samples=[
            (0.0, "1", "0.4", "in", "first"),
            (3.0, f"{dad:,}", "6", "ft", "dad"),
            (7.0, f"{liberty:,}", "305", "ft", "liberty"),
            (12.0, f"{empire:,}", "1,454", "ft", "empire"),
            (18.0, f"{burj:,}", "2,717", "ft", "burj"),
            (24.0, "300,000", "", "", "strain"),
            (32.0, f"{n:,}", "about 2 mi", "", "failure"),
            (38.0, "record", "115", "ft", "record"),
        ],
    )
    ep.notes = {"bricks": n, "height_m": height, "logo": False, "kind": q.get("kind", "2x2")}
    return ep


def _crowd(raw: dict) -> BEpisode:
    q = raw["quantity"]
    people = int(q["people"])
    land = float(q["land_sq_mi"])
    land_m2 = land * 2.589988e6
    per_m2 = people / land_m2
    # Standing room at the density that fills the state. Concert-tight, about 3/m².
    each = 1.0 / per_m2
    points = ellipse_points(4000, land_m2, seed=int(raw.get("seed", 8)))
    ep = _beat_episode(
        raw,
        primary_label="PEOPLE",
        secondary_label="PLACE",
        samples=[
            (0.0, "1", "one person", "", "person"),
            (3.0, f"{int(q.get('stadium', 107601)):,}", "a stadium", "", "stadium"),
            (8.0, "8.8 million", "New York City", "", "nyc"),
            (14.0, "340 million", "the United States", "", "us"),
            (20.0, f"{people:,}", "Rhode Island", "", "full"),
            (30.0, f"{per_m2:.1f}", "per m²", "", "density"),
            (36.0, "jump", "less than an atom", "", "jump"),
        ],
    )
    ep.notes = {
        "people": people,
        "per_m2": per_m2,
        "each_m2": each,
        "needed_sq_mi": land,
        "land_sq_mi": land,
        "fits": per_m2 < 4.0,
        "instances": len(points),
    }
    return ep


def _beat_episode(raw, primary_label, secondary_label, samples) -> BEpisode:
    """Timeline-only episodes. No per-frame camera. Enough for words.json and tests."""
    fps = int(raw["fps"])
    timing = raw["timing"]
    duration = float(timing["duration_sec"])
    n = int(round(duration * fps))
    hook = float(timing.get("hook_hold", 2.0))
    frames = []
    for i in range(n):
        t = i / fps
        phase = "hook" if t < hook else "journey"
        # Step the counter on the samples, holding each at least 0.8 s.
        chosen = samples[0]
        for sample in samples:
            if t + 1e-6 >= sample[0]:
                chosen = sample
        frames.append(
            BFrame(
                frame=i,
                t=t,
                phase=phase,
                primary=str(chosen[1]),
                primary_unit="",
                secondary=str(chosen[2]),
                secondary_unit=str(chosen[3]),
                label_primary=primary_label,
                label_secondary=secondary_label,
                title_alpha=1.0 if t < hook else 0.0,
                ending_alpha=1.0 if t > duration - 3.5 else 0.0,
                dissolve=1.0 if i == n - 1 else 0.0,
                pill_title=str(chosen[4]),
                pill_sub=str(chosen[2]),
                pill_alpha=0.0 if t < hook else 1.0,
            )
        )
    beats = []
    for sample in samples:
        say = raw.get("say", {}).get(sample[4], sample[4])
        beats.append(
            {
                "id": sample[4],
                "narration": say,
                "start": float(sample[0]),
                "end": float(sample[0]) + 3.0,
                "time_label": f"{sample[1]} {sample[2]}".strip(),
            }
        )
    return BEpisode(raw=raw, frames=frames, beats=beats, duration=duration)


def words_for(ep: BEpisode) -> dict:
    return voice_clock(ep.duration, ep.beats)


def timeline_for(ep: BEpisode) -> dict:
    return {
        "id": ep.id,
        "title": ep.raw["title"],
        "format": "B",
        "preset": ep.raw["preset"],
        "fps": ep.fps,
        "width": ep.width,
        "height": ep.height,
        "duration_sec": ep.duration,
        "frame_count": len(ep.frames),
        "caption_band": {"y0": int(0.64 * ep.height), "y1": int(0.78 * ep.height)},
        "loop_to_frame": 0,
        "notes": {k: v for k, v in ep.notes.items() if k != "points_sample"},
        "beats": [
            {"id": b["id"], "start": b["start"], "end": b["end"], "narration": b["narration"], "time_label": b.get("time_label", "")}
            for b in ep.beats
        ],
        "words": words_for(ep),
    }
