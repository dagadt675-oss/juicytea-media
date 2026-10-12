"""Format B episodes from the approved slate.

Presets: penny_fall, earth_hole, rice_chessboard, brick_tower, crowd_island.
The penny fall is the full picture. The others resolve to a timeline, an
instancer point cloud, and the shared words.json clock.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import yaml

from engine.landmarks import MAN
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


def _wind(t: float, seed: float, scale: float) -> float:
    """Deterministic Graph-Editor-style noise. Same t always gives the same offset."""
    x = t * scale + seed
    return (
        math.sin(x)
        + 0.62 * math.sin(x * 2.37 + 1.3)
        + 0.28 * math.sin(x * 5.05 + seed * 1.7)
    ) / 1.9


def _held(rows, t):
    chosen = rows[0]
    for row in rows:
        if t + 1e-9 >= row[0]:
            chosen = row
    return chosen


# North-east skin of the NanoRay tower. The penny rides this corner from the
# 86th-floor parapet down to the north sidewalk, where the man stands.
_ESB_CORNERS = (
    (443.0, 2.0, -15.5),
    (400.0, 5.5, -11.5),
    (365.0, 6.2, -5.5),
    (340.0, 8.0, -4.0),
    (325.0, 11.5, 3.2),
    (311.35, 12.35, 4.85),
    (300.0, 14.8, 8.2),
    (280.0, 17.2, 11.0),
    (250.0, 19.6, 13.6),
    (180.0, 20.2, 14.2),
    (100.0, 21.0, 15.0),
    (92.0, 30.0, 66.6),
    (40.0, 14.0, 68.4),
    (0.0, 8.0, 67.8),
)

# Solid the camera is not allowed to enter. Bands above the lot follow the
# NanoRay setbacks, inset so the parapet and the coin stay outside. The
# bottom band is the lot, so a point in the roadway is not what this pushes.
_SHAFT_BANDS = (
    (450.0, 400.0, -2.0, 1.2, -20.2, -16.2),
    (400.0, 365.0, -6.0, 4.6, -24.0, -12.2),
    (365.0, 340.0, -7.5, 5.2, -27.0, -8.5),
    (340.0, 325.0, -11.0, 9.0, -39.0, 0.6),
    (325.0, 312.0, -14.5, 11.0, -42.0, 3.2),
    (312.0, 300.0, -16.5, 11.4, -44.5, 4.2),
    (300.0, 280.0, -18.5, 15.4, -47.0, 9.2),
    (280.0, 250.0, -20.5, 17.4, -49.0, 11.4),
    (250.0, 90.01, -22.0, 19.2, -56.0, 13.6),
    (90.0, 0.0, -28.5, 28.5, -64.5, 64.5),
)


def _shaft_box(z: float) -> tuple[float, float, float, float]:
    for zhi, zlo, xmin, xmax, ymin, ymax in _SHAFT_BANDS:
        if zlo - 0.01 <= z <= zhi + 0.01:
            return xmin, xmax, ymin, ymax
    return _SHAFT_BANDS[-1][2:]


def clear_of_shaft(point, margin: float = 1.2) -> tuple[float, float, float]:
    """Push a point that sits inside the tower solid out to the SE corner.

    Points already in open air are returned unchanged. The render also
    raycasts against the real meshes; this is the path-level check.
    """
    x, y, z = (float(point[0]), float(point[1]), float(point[2]))
    xmin, xmax, ymin, ymax = _shaft_box(z)
    if not (xmin < x < xmax and ymin < y < ymax):
        return (x, y, z)
    return (xmax + margin, ymax + margin, z)


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
    """33.40 s cut locked to episodes/penny_words.json.

    The counter changes on the spoken number. The picture keeps moving.
    Frame 0 and the last frame are the same ledge pose.
    """
    q = raw["quantity"]
    vt = terminal_mps(float(q["mass_kg"]), float(q["diameter_m"]), float(q["cd"]), float(q["air_kg_m3"]))
    drop = float(outline("empire")["deck_m"])
    fall_t = time_to_fall(drop, vt)
    mph = vt / MPH
    fps = int(raw["fps"])
    duration = float(raw["timing"]["duration_sec"])
    n = int(round(duration * fps))
    # Picture altitude in feet. The HUD steps on the words; this does not.
    altitude = [
        (0.00, 1250.0),
        (0.57, 1250.0),
        (1.10, 1210.0),
        (2.40, 1160.0),
        (5.34, 1000.0),
        (8.70, 860.0),
        (13.20, 620.0),
        (15.44, 500.0),
        (16.91, 200.0),
        (18.25, 100.0),
        (19.07, 80.0),
        (21.07, 5.6),
        (21.40, 8.6),
        (22.30, 2.4),
        (23.20, 0.4),
        (27.60, 0.35),
        (30.22, 320.0),
        (33.15, 1250.0),
        (33.40, 1250.0),
    ]
    frames = []
    prev_feet, prev_mph = None, None
    feet_from, mph_from = "1,250", "0"
    feet_change = mph_change = 0.0
    opening = None
    for i in range(n):
        t = i / fps
        alt_ft = _interp(altitude, min(t, duration))
        if t < 15.44 or t >= 33.15:
            feet = 1250
        elif t < 16.91:
            feet = 500
        elif t < 18.25:
            feet = 200
        elif t < 19.07:
            feet = 100
        elif t < 20.00:
            feet = 80
        elif t < 21.0:
            feet = 40
        else:
            feet = 0
        if t < 5.34 or t >= 33.15:
            speed_mph = 0
        elif t < 6.70:
            speed_mph = 10
        elif t < 7.675:
            speed_mph = 20
        else:
            speed_mph = 25
        if t < 0.57:
            phase = "hook"
        elif t < 13.31:
            phase = "fall"
        elif t < 14.90:
            phase = "guy"
        elif t < 19.07:
            phase = "descent"
        elif t < 21.07:
            phase = "rush"
        elif t < 24.16:
            phase = "hit"
        elif t < 27.60:
            phase = "walk"
        elif t < 33.15:
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
        # The slot shows the new digit once the roll crosses halfway. Center
        # that crossing on the spoken word so the counter matches the line.
        feet_roll = 1.0 if feet_from == feet_s else _fade(t, feet_change - 0.11, feet_change + 0.11)
        mph_roll = 1.0 if mph_from == mph_s else _fade(t, mph_change - 0.11, mph_change + 0.11)
        title_alpha = 1.0 - _fade(t, 1.85, 2.35)
        if t >= 33.15:
            title_alpha = _fade(t, 33.15, 33.30)
        ending_alpha = 0.0
        pill_title, pill_sub, pill_a = "", "", 0.0
        if 11.26 <= t <= 12.90:
            pill_title, pill_sub, pill_a = "NO AIR", "~200 MPH", 1.0
        metric = f"{int(feet) * FT:,.0f} m"
        z_vis = alt_ft * FT
        ledge_xy = _penny_xy(drop)
        # North-east lip of the NanoRay 86th-floor parapet. Outside the shaft
        # box, on the stone coping, in front of the curved rail.
        lip = (18.4, 12.2)
        parapet = 293.55
        ledge_penny = (lip[0], lip[1], parapet)
        if t < 0.57 or t >= 33.15:
            penny = ledge_penny
        else:
            # Hold the parapet until the spoken altitude actually drops past it,
            # so the coin never jumps upward off the 86th-floor ledge.
            z_fall = min(z_vis, parapet)
            xy = _penny_xy(z_fall)
            penny = (xy[0], xy[1], z_fall)
            if t < 2.4:
                off = _fade(t, 0.7, 2.2)
                penny = (
                    lip[0] + (xy[0] - lip[0]) * off + 0.08 * _wind(t, 1.1, 2.4),
                    lip[1] + (xy[1] - lip[1]) * off + 0.06 * _wind(t, 2.4, 2.1),
                    parapet + (min(z_vis, parapet) - parapet) * off,
                )
            elif t < 20.2:
                amp = _fade(t, 2.4, 3.2)
                if t > 18.4:
                    amp *= 1.0 - _fade(t, 18.4, 20.2)
                penny = (
                    penny[0] + 0.32 * amp * _wind(t, 1.1, 1.7),
                    penny[1] + 0.24 * amp * _wind(t, 2.4, 1.9),
                    penny[2],
                )
            if 20.40 <= t < 27.70:
                if t < 21.07:
                    u = _fade(t, 20.40, 21.07)
                    penny = (
                        penny[0] + (MAN[0] - penny[0]) * u,
                        penny[1] + (MAN[1] - penny[1]) * u,
                        penny[2],
                    )
                else:
                    hop = math.sin(min(1.0, max(0.0, (t - 21.07) / 0.36)) * math.pi)
                    if t < 21.55:
                        # On the forehead, toward the street camera, with a short hop.
                        penny = (MAN[0] - 0.02, MAN[1] - 0.16, 1.68 + 0.05 * hop)
                    else:
                        penny = (MAN[0] - 0.05, MAN[1] - 0.08, penny[2])
        # Shot 1: in the air just above the 86th-floor coping, looking out
        # and down so the coin is on the near ledge and the city is the drop.
        # Open air just outside the coping. Probed clear of the limestone.
        # 32 mm at about 0.9 m: the face fills roughly a third of the frame.
        hook_cam = (18.87, 12.75, parapet + 0.6)
        hook_tgt = (5.56, -2.71, 279.47)
        # 24 mm at about 2 m: the face stays near a tenth of the frame.
        drone_cam = (penny[0] + 1.21, penny[1] + 1.40, penny[2] + 0.70)
        if 2.4 <= t < 19.07 and not (13.31 <= t < 15.10):
            drone_cam = (
                drone_cam[0] + 0.10 * _wind(t, 8.2, 6.5),
                drone_cam[1] + 0.08 * _wind(t, 3.4, 7.1),
                drone_cam[2] + 0.06 * _wind(t, 5.5, 5.4),
            )
        drone_tgt = (penny[0] - 12.56, penny[1] - 14.59, penny[2] - 12.70)
        step = max(0.0, t - 23.9) * 0.9
        man_x, man_y = MAN[0] + step, MAN[1]
        # Street camera sits on the sidewalk, south of him, looking north
        # across the curb, the road, and the shopfronts.
        # On the north sidewalk, beside him, looking through him at the street.
        # South of him, a little to his right, so both palms face the lens
        # and the brick blocks stay behind him.
        up_cam = (man_x - 0.85, man_y - 2.55, 1.46)
        up_tgt = (man_x + 0.05, man_y + 0.25, 1.38)
        face_cam = up_cam
        face_tgt = up_tgt
        guy_cam = (MAN[0] + 2.4, MAN[1] + 0.6, 4.6)
        guy_tgt = (MAN[0], MAN[1], 1.15)
        if t < 2.4 or t >= 33.15:
            cam = hook_cam
            target = hook_tgt
            lens = 32.0
        elif t < 2.9:
            u = _fade(t, 2.4, 2.9)
            cam = _lerp(hook_cam, drone_cam, u)
            target = _lerp(hook_tgt, drone_tgt, u)
            lens = 50.0 + (24.0 - 50.0) * u
        elif t < 13.31:
            cam, target, lens = drone_cam, drone_tgt, 24.0
        elif t < 14.55:
            u = _fade(t, 13.31, 13.55)
            cam = _lerp(drone_cam, guy_cam, u)
            target = _lerp(drone_tgt, guy_tgt, u)
            lens = 24.0 + (24.0 - 24.0) * u
        elif t < 15.10:
            u = _fade(t, 14.55, 15.10)
            cam = _lerp(guy_cam, drone_cam, u)
            target = _lerp(guy_tgt, drone_tgt, u)
            lens = 24.0
        elif t < 19.07:
            cam, target, lens = drone_cam, drone_tgt, 24.0
        elif t < 19.45:
            u = _fade(t, 19.07, 19.45)
            cam = _lerp(drone_cam, up_cam, u)
            target = _lerp(drone_tgt, up_tgt, u)
            lens = 24.0 + (32.0 - 24.0) * u
        elif t < 27.71:
            cam, target, lens = up_cam, up_tgt, 32.0
        else:
            u = _fade(t, 30.2, 33.05)
            # Stay wide through the rise still, then meet the deck for the loop.
            wide = (175.0, 330.0, 72.0)
            wide_tgt = (0.0, -8.0, 175.0)
            cam = _lerp(wide, hook_cam, u)
            target = _lerp(wide_tgt, hook_tgt, u)
            cam = (cam[0] + math.sin(u * math.pi) * 16.0, cam[1], cam[2])
            lens = 28.0 + (50.0 - 28.0) * u
        if t >= 33.15:
            cam, target, penny, lens = hook_cam, hook_tgt, ledge_penny, 50.0
        cam = clear_of_shaft(cam, 1.2)
        if t < 0.57 or t >= 33.15:
            penny = ledge_penny
        else:
            penny = clear_of_shaft(penny, 0.8)
        if t < 0.57 or t >= 33.15:
            spin, tilt, roll = 0.08, 0.15, 0.02
        elif t < 1.35:
            flick = _fade(t, 1.05, 1.35)
            spin = 0.05 + flick * 1.2
            tilt = 0.15 + flick * 1.4
            roll = flick * 0.4
        else:
            damp = 1.0
            if t >= 21.07:
                damp = 1.0 - _fade(t, 21.07, 22.0)
            # Broadside near the drone still (t = 6.67) so the coin reads large,
            # still tumbling the rest of the way down.
            # Stand the disc toward the drone through the facade follow, then
            # let it tumble as it nears the street.
            upright = 1.0 - _fade(t, 17.2, 19.4)
            spin = (t - 6.67) * 5.4 + damp * 0.8 * _wind(t, 0.4, 2.5)
            tilt = upright * 1.35 + (1.0 - upright) * (0.45 + damp * 1.3 * _wind(t, 1.8, 2.9))
            roll = (t - 6.67) * 3.6 * upright + damp * 0.9 * _wind(t, 3.2, 2.2)
        frame = BFrame(
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
            rot=(spin, tilt, roll),
            lens=lens,
        )
        if i == 0:
            opening = frame
        frames.append(frame)
    if opening is not None and frames:
        last = frames[-1]
        frames[-1] = BFrame(
            frame=last.frame,
            t=last.t,
            phase="hold",
            primary=opening.primary,
            primary_unit=opening.primary_unit,
            secondary=opening.secondary,
            secondary_unit=opening.secondary_unit,
            label_primary=opening.label_primary,
            label_secondary=opening.label_secondary,
            title_alpha=1.0,
            ending_alpha=0.0,
            dissolve=0.0,
            pill_title="",
            pill_sub="",
            pill_alpha=0.0,
            penny=opening.penny,
            cam=opening.cam,
            target=opening.target,
            speed_mps=0.0,
            fallen_m=0.0,
            metric=opening.metric,
            roll=1.0,
            primary_prev=opening.primary,
            secondary_roll=1.0,
            secondary_prev=opening.secondary,
            rot=opening.rot,
            lens=opening.lens,
        )
    beats = [
        {"id": "hook", "narration": "This penny could kill someone.", "start": 0.0, "end": 2.4, "time_label": "1,250 ft / 0 mph"},
        {"id": "drop", "narration": "Dropped from twelve hundred and fifty feet.", "start": 2.4, "end": 5.34, "time_label": "1,250 ft"},
        {"id": "speed", "narration": "Ten miles an hour, twenty, twenty-five.", "start": 5.34, "end": 9.18, "time_label": "25 mph"},
        {"id": "vacuum", "narration": "With no air, it would hit at almost two hundred miles an hour.", "start": 9.18, "end": 13.31, "time_label": "25 mph"},
        {"id": "guy", "narration": "And there is a guy right under it.", "start": 13.31, "end": 15.44, "time_label": "25 mph"},
        {"id": "count", "narration": "Five hundred feet, two hundred, one hundred.", "start": 15.44, "end": 19.07, "time_label": "100 ft"},
        {"id": "rush", "narration": "", "start": 19.07, "end": 21.073, "time_label": "0 ft"},
        {"id": "bonk", "narration": "Bonk. It stings. That's it.", "start": 21.073, "end": 24.16, "time_label": "0 ft"},
        {"id": "leaf", "narration": "It tumbles like a leaf, so it tops out around twenty-five.", "start": 24.16, "end": 27.71, "time_label": "25 mph"},
        {"id": "rise", "narration": "On the real Empire State, wind and the lower roofs would stop it first, but people still swear.", "start": 27.71, "end": duration, "time_label": "1,250 ft"},
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
        "bonk_s": 21.073,
        "empire": {k: v for k, v in outline("empire").items() if k != "source"},
        "description": (
            "Empire State Building by NanoRay (CC-BY, Sketchfab). "
            "Shrugging by Rida.Sidi.Ben.Ali (CC-BY, Sketchfab)."
        ),
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
