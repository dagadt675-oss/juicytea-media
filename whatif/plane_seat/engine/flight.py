"""Camera, cloud, and heatmap clock. Pure Python, periodic on 32.81 s.

The pose at t=0 is the pose at t=duration, and the step across that seam
matches an ordinary frame. Location swaps happen only while the lens is in
cloud or inside the cabin.
"""

from __future__ import annotations

import math

from .aircraft import AMBER, BRIGHT, GREEN, RED, ROUTE, TILE
from .clock import DURATION, word_end, word_time

# Camera keys: t, eye (plane-local metres), look-at, roll deg, lens mm.
# One eased orbit, periodic: top-down hook → rear 3/4 → side → top-down
# seat map → front 3/4 → the same top-down hook. Look targets sit below the
# fuselage so the jet lands in the upper-middle; the bottom quarter is UI.
# Roll stays 0. The first key matches the last key.
CAM_KEYS = [
    (0.00, (-4.0, -2.0, 58.0), (-6.0, 0.0, 0.2), 0.0, 26.0),
    (1.40, (-10.0, -8.0, 46.0), (-12.0, 0.0, 0.4), 0.0, 24.0),
    (4.40, (-34.0, -20.0, 16.0), (2.0, 0.0, 0.5), 0.0, 22.0),
    (8.20, (-26.0, -28.0, 16.0), (2.0, 0.0, 0.0), 0.0, 22.0),
    (11.60, (-4.0, -3.0, 52.0), (-12.0, 0.0, 0.3), 0.0, 24.0),
    (18.40, (-2.0, -2.5, 50.0), (-10.0, 0.0, 0.3), 0.0, 24.0),
    (24.20, (38.0, -22.0, 15.0), (-4.0, 0.0, 1.0), 0.0, 20.0),
    (29.40, (-2.0, -6.0, 48.0), (-12.0, 0.0, 0.4), 0.0, 25.0),
    (32.81, (-4.0, -2.0, 58.0), (-6.0, 0.0, 0.2), 0.0, 26.0),
]

# Cruise height eases a few tens of metres. The old 1,000 m jumps were the
# plane leaping in frame at each biome cut.
ALT_KEYS = [
    (0.00, 560.0),
    (8.00, 480.0),
    (16.00, 620.0),
    (24.00, 500.0),
    (32.81, 560.0),
]

PITCH_KEYS = [
    (0.00, 2.0),
    (4.20, 1.0),
    (12.00, 0.4),
    (24.00, 0.8),
    (32.55, 2.0),
]

ROLL_KEYS = [
    (0.00, 0.0),
    (8.00, 1.5),
    (16.00, -1.0),
    (24.00, 0.8),
    (32.55, 0.0),
]


def _smooth(a: float, b: float, x: float) -> float:
    if b <= a:
        return 0.0 if x < a else 1.0
    u = max(0.0, min(1.0, (x - a) / (b - a)))
    return u * u * (3.0 - 2.0 * u)


def _window(t: float, t0: float, t1: float, fade_in: float = 0.10, fade_out: float = 0.22) -> float:
    return _smooth(t0, t0 + fade_in, t) * (1.0 - _smooth(t1, t1 + fade_out, t))


def _gauss(t: float, center: float, width: float, height: float = 1.0) -> float:
    return height * math.exp(-((t - center) / width) ** 2)


def _pgauss(t: float, center: float, width: float, height: float = 1.0) -> float:
    dt = (t - center + DURATION * 0.5) % DURATION - DURATION * 0.5
    return height * math.exp(-((dt) / width) ** 2)


def _extend(keys: list[tuple]) -> list[tuple]:
    out = []
    width = len(keys[0][1]) if isinstance(keys[0][1], tuple) else 1
    for shift in (-DURATION, 0.0, DURATION):
        for time, value in keys:
            val = value if isinstance(value, tuple) else (value,)
            if len(val) != width:
                raise RuntimeError("key width mismatch")
            out.append((time + shift, val))
    out.sort(key=lambda item: item[0])
    return out


def _centripetal(p0, p1, p2, p3, u: float):
    def tj(ti, a, b):
        dist = math.sqrt(sum((bb - aa) ** 2 for aa, bb in zip(a, b)))
        return ti + dist ** 0.5

    def lerp(a, b, ta, tb, t):
        if tb <= ta:
            return a
        f = (t - ta) / (tb - ta)
        return tuple(ai + (bi - ai) * f for ai, bi in zip(a, b))

    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    if t2 <= t1:
        return p1
    t = t1 + max(0.0, min(1.0, u)) * (t2 - t1)
    a1 = lerp(p0, p1, t0, t1, t)
    a2 = lerp(p1, p2, t1, t2, t)
    a3 = lerp(p2, p3, t2, t3, t)
    b1 = lerp(a1, a2, t0, t2, t)
    b2 = lerp(a2, a3, t1, t3, t)
    return lerp(b1, b2, t1, t2, t)


def _sample(keys: list[tuple], t: float):
    extended = _extend(keys)
    # Bracket t inside the middle copy.
    i = 0
    for k in range(len(extended) - 1):
        if extended[k][0] <= t <= extended[k + 1][0]:
            i = k
            break
    t0 = extended[i][0]
    t1 = extended[i + 1][0]
    u = 0.0 if t1 <= t0 else (t - t0) / (t1 - t0)
    i0 = max(0, i - 1)
    i3 = min(len(extended) - 1, i + 2)
    return _centripetal(extended[i0][1], extended[i][1], extended[i + 1][1], extended[i3][1], u)


def _sample_cam(t: float):
    """Return eye, look, roll, lens. Keys are nested so each channel is centripetal in its own space."""
    eye = _sample([(k[0], k[1]) for k in CAM_KEYS], t)
    look = _sample([(k[0], k[2]) for k in CAM_KEYS], t)
    roll = _sample([(k[0], (k[3],)) for k in CAM_KEYS], t)[0]
    lens = _sample([(k[0], (k[4],)) for k in CAM_KEYS], t)[0]
    return eye, look, roll, lens


def cloud_cover(t: float) -> float:
    value = (
        _pgauss(t, 32.20, 0.75, 0.95)
        + _gauss(t, 4.08, 0.18, 1.0)
        + _gauss(t, 10.02, 0.20, 1.0)
        + _gauss(t, 18.05, 0.24, 0.88)
        + _gauss(t, 24.38, 0.18, 1.0)
        + _gauss(t, 28.55, 0.34, 1.0)
    )
    return max(0.0, min(1.0, value))


def _blocked(eye) -> bool:
    """True when a point is inside the tube, the fin, or a wing."""
    x, y, z = eye
    in_tube = -38.0 < x < 36.0 and abs(y) < 7.2 and 0.5 < z < 14.5
    in_fin = -38.0 < x < -2.0 and abs(y) < 5.0 and 0.5 < z < 21.5
    in_wing = -40.0 < x < 12.0 and abs(y) < 31.0 and 0.5 < z < 11.0
    return in_tube or in_fin or in_wing


def _keep_clear(eye):
    """Push a spline overshoot out past the wing and above the fin."""
    x, y, z = (float(v) for v in eye)
    if not _blocked((x, y, z)):
        return (x, y, z)
    side = -1.0 if y <= 0.0 else 1.0
    y = side * max(abs(y), 20.0)
    z = max(z, 20.0)
    return (x, y, z)


def biome_at(t: float) -> str:
    # Boundaries sit on cloud peaks so the ground swap is covered.
    if t < 4.08:
        return "city"
    if t < 10.02:
        return "forest"
    if t < 18.05:
        return "mountains"
    if t < 24.38:
        return "ocean"
    if t < 28.55:
        return "desert"
    if t < 31.85:
        return "cloudsea"
    return "city"


def _zone_colors(t: float) -> dict:
    """Red / yellow / green from the first frame. Numbers are the VO script:
    front 38 and middle 39 yellow, aisle 44 red, back 32 and best 28 green.
    """
    del t
    return {
        "front": AMBER,
        "mid": AMBER,
        "back": GREEN,
        "worst": RED,
        "best": BRIGHT,
    }


def _lid_open(t: float) -> float:
    """1 = crown lifted. Opens and closes over more than a second, and the
    loop starts and ends open so the hook matches the last frame."""
    if t < 1.15 or t > 30.6:
        return 1.0
    if t < 8.50:
        return 1.0 - _smooth(1.15, 2.70, t)
    return _smooth(8.50, 10.40, t)


def pose_at(t: float) -> dict:
    """World-ready pose. t is wrapped onto [0, duration)."""
    t = t % DURATION
    eye, look, cam_roll, lens = _sample_cam(t)
    # A slow periodic drift so a key with a flat tangent still moves.
    # Vertical only: a sideways drift can tuck the lens into a wing.
    drift_z = 0.18 * math.sin(2.0 * math.pi * t / DURATION)
    eye = (eye[0], eye[1], eye[2] + drift_z)
    alt = _sample([(k[0], (k[1],)) for k in ALT_KEYS], t)[0]
    pitch = 0.0
    roll = 0.0
    yaw = 0.0
    cover = cloud_cover(t)
    inside = False
    lid = _lid_open(t)
    xray = 0.0
    cutaway = lid > 0.35
    scatter = 0.0
    colors = _zone_colors(t)
    distance = ROUTE * (t / DURATION)

    t17 = word_time(17)
    t17_end = word_end(17)
    icons = []
    for i in range(17):
        start = t17 + (t17_end - t17) * 0.82 * (i / 16.0)
        icons.append(_smooth(start, start + 0.055, t))

    return {
        "t": t,
        "altitude": alt,
        "pitch": pitch,
        "roll": roll,
        "yaw": yaw,
        "eye": eye,
        "look": look,
        "cam_roll": cam_roll,
        "lens": lens,
        "biome": biome_at(t),
        "cloud": cover,
        "inside": inside,
        "xray": xray,
        "interior": False,
        "cutaway": cutaway,
        "scroll": distance % TILE,
        "distance": distance,
        "explode": 0.0,
        "lid": lid,
        "colors": colors,
        "strength": {
            "front": 1.0 + 1.15 * _gauss(t, word_time(11), 0.10) + 0.65 * _gauss(t, word_time(26), 0.16),
            "mid": 1.0 + 0.65 * _gauss(t, word_time(31), 0.16),
            "back": 1.25 + 0.95 * _gauss(t, word_time(1), 0.13) + 1.05 * _gauss(t, word_time(34), 0.15) + 0.75 * _gauss(t, word_time(47), 0.14),
        },
        "glint": _gauss(t, word_time(7), 0.16),
        "icons": icons,
        "icon_split": _smooth(word_time(21), word_time(21) + 0.18, t),
        "show_title": _window(t, 0.0, 1.25, 0.0, 0.22) + _window(t, 31.55, 32.81, 0.30, 0.0),
        "show_17": _window(t, 4.45, 9.55, 0.12, 0.20),
        "show_38": _window(t, 2.95, 4.45, 0.12, 0.16) + _window(t, 10.20, 12.70, 0.12, 0.20),
        "show_39": _window(t, word_time(31), 15.50, 0.12, 0.20),
        "show_32": _window(t, 1.45, 2.95, 0.12, 0.16) + _window(t, 7.50, 9.00, 0.12, 0.16) + _window(t, word_time(34), 19.20, 0.12, 0.18),
        "show_44": _window(t, 19.40, word_end(44) + 0.35, 0.12, 0.22),
        "show_28": _window(t, word_time(54), word_end(54) + 0.45, 0.12, 0.22),
        "show_x": _window(t, word_time(11), word_time(11) + 0.48, 0.03, 0.16),
        "flare": min(1.0, 0.12 + 0.9 * _gauss(t, word_time(8), 0.16) + 0.75 * _gauss(t, 24.78, 0.18)),
        "beacon": 0.25 + 0.75 * max(0.0, math.cos(2.0 * math.pi * (t / DURATION) * 28.0)) ** 8,
        "scatter": scatter,
    }


def pose_delta(a: dict, b: dict) -> float:
    eye = math.sqrt(sum((a["eye"][i] - b["eye"][i]) ** 2 for i in range(3)))
    alt = abs(a["altitude"] - b["altitude"])
    ang = abs(a["pitch"] - b["pitch"]) + abs(a["roll"] - b["roll"])
    return eye + alt * 0.05 + ang * 0.08


def hidden_swap(t: float) -> bool:
    """True when a ground swap at this instant would be covered."""
    pose = pose_at(t)
    return pose["cloud"] >= 0.68 or pose["inside"]
