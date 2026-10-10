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


def _penny(raw: dict) -> BEpisode:
    q = raw["quantity"]
    vt = terminal_mps(float(q["mass_kg"]), float(q["diameter_m"]), float(q["cd"]), float(q["air_kg_m3"]))
    drop = float(outline("empire")["deck_m"])
    fall_t = time_to_fall(drop, vt)
    timing = raw["timing"]
    hook = float(timing["hook_hold"])
    payoff = float(timing["payoff_hold"])
    dissolve = float(timing["dissolve"])
    duration = hook + fall_t + payoff + dissolve
    fps = int(raw["fps"])
    n = int(round(duration * fps))
    mph = vt / MPH
    deck_ft = drop / FT
    cam_off = tuple(raw["camera"]["offset_m"])
    penny_x = float(raw["camera"]["penny_x_m"])
    frames = []
    for i in range(n):
        t = i / fps
        if t < hook:
            phase = "hook"
            fallen, speed = 0.0, 0.0
        elif t < hook + fall_t:
            phase = "fall"
            fallen, speed = fall_distance_speed(t - hook, vt)
            fallen = min(fallen, drop)
        elif t < hook + fall_t + payoff:
            phase = "payoff"
            fallen, speed = drop, vt
        else:
            phase = "dissolve"
            fallen, speed = drop, vt
        z = drop - fallen
        penny = (penny_x, 0.0, z)
        cam = (penny[0] + cam_off[0], penny[1] + cam_off[1], penny[2] + cam_off[2])
        title_alpha = 1.0 - _fade(t, hook - 0.35, hook + 0.25)
        if phase == "dissolve":
            title_alpha = 0.0
        end_in = _fade(t, hook + fall_t, hook + fall_t + 0.45)
        end_out = _fade(t, hook + fall_t + payoff, hook + fall_t + payoff + dissolve * 0.5)
        ending_alpha = end_in * (1.0 - end_out) if phase in ("payoff", "dissolve") else 0.0
        diss = _fade(t, duration - dissolve, duration) if phase == "dissolve" else 0.0
        remaining_ft = max(0.0, (drop - fallen) / FT)
        speed_mph = speed / MPH
        # Integer mph. The 25 mph payoff then holds for the rest of the fall.
        shown = int(round(speed_mph))
        pill_title, pill_sub, pill_a = "", "", 0.0
        if phase == "hook":
            pill_title, pill_sub, pill_a = "86TH FLOOR", f"{deck_ft:,.0f} ft", title_alpha
        elif shown >= int(round(mph)) - 0 and phase == "fall" and speed_mph > mph * 0.97:
            pill_title, pill_sub, pill_a = "TERMINAL VELOCITY", f"{round(mph)} mph", 1.0
        elif phase == "payoff":
            pill_title, pill_sub, pill_a = "TERMINAL VELOCITY", f"{round(mph)} mph", 1.0 - ending_alpha
        frames.append(
            BFrame(
                frame=i,
                t=t,
                phase=phase,
                primary=f"{shown}",
                primary_unit="mph",
                secondary=f"{remaining_ft:,.0f}",
                secondary_unit="ft",
                label_primary="SPEED",
                label_secondary="TO GO",
                title_alpha=title_alpha,
                ending_alpha=ending_alpha,
                dissolve=diss,
                pill_title=pill_title,
                pill_sub=pill_sub,
                pill_alpha=pill_a,
                penny=penny,
                cam=cam,
                target=penny,
                speed_mps=speed,
                fallen_m=fallen,
            )
        )
    beats = [
        {"id": "hook", "narration": raw["hook"]["say"], "start": 0.0, "end": hook, "time_label": "0 mph"},
        {"id": "fall", "narration": raw["fall"]["say"], "start": hook, "end": hook + fall_t, "time_label": f"{round(mph)} mph"},
        {"id": "payoff", "narration": " ".join(raw["ending"]["lines"]), "start": hook + fall_t, "end": duration, "time_label": f"{round(mph)} mph"},
    ]
    ep = BEpisode(raw=raw, frames=frames, beats=beats, duration=duration)
    ep.notes = {
        "terminal_mps": vt,
        "terminal_mph": mph,
        "drop_m": drop,
        "fall_sec": fall_t,
        "empire": outline("empire"),
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
    h32 = height * ((2**32) / grains) ** (1.0 / 3.0)
    ep = _beat_episode(
        raw,
        primary_label="SQUARE",
        secondary_label="HEIGHT",
        samples=[
            (0.0, "1", "1 grain", "", "first"),
            (8.0, "32", f"{h32 / FT:,.0f} ft", "", "square32"),
            (16.0, "64", f"{height / FT:,.0f} ft", "", "last"),
            (24.0, "64", f"{orbit_m / 1000:.0f} km up", "", "orbit"),
        ],
    )
    ep.notes = {
        "grains": grains,
        "heap_height_m": height,
        "heap_radius_m": radius,
        "instance_cap": len(points),
        "camera_altitude_m": orbit_m,
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
        samples=[(float(item["t"]), item["depth"], item["name"], "", item["id"]) for item in layers],
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
    n = int(float(q["failure_n"]) / (float(q["mass_kg"]) * G))
    height = n * float(q["course_m"])
    ep = _beat_episode(
        raw,
        primary_label="BRICKS",
        secondary_label="HEIGHT",
        samples=[
            (0.0, "1", "0.4", "in", "first"),
            (8.0, f"{n // 2:,}", f"{(height * 0.5) / FT:,.0f}", "ft", "half"),
            (16.0, f"{n:,}", f"{height / FT:,.0f}", "ft", "failure"),
        ],
    )
    ep.notes = {"bricks": n, "height_m": height, "logo": False}
    return ep


def _crowd(raw: dict) -> BEpisode:
    q = raw["quantity"]
    people = int(q["people"])
    land_m2 = float(q["land_sq_mi"]) * 2.589988e6
    each = float(q["each_m2"])
    needed = people * each
    points = ellipse_points(4000, needed, seed=int(raw.get("seed", 8)))
    ep = _beat_episode(
        raw,
        primary_label="PEOPLE",
        secondary_label="FIT",
        samples=[
            (0.0, "1", "one", "", "person"),
            (10.0, f"{people / 2:,.0f}", "half", "", "half"),
            (20.0, f"{people:,}", "Rhode Island", "", "full"),
        ],
    )
    ep.notes = {
        "people": people,
        "needed_sq_mi": needed / 2.589988e6,
        "land_sq_mi": float(q["land_sq_mi"]),
        "fits": needed < land_m2,
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
