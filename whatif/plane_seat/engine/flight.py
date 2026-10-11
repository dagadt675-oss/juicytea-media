"""Camera, cloud, and heatmap clock. Pure Python, periodic on 32.81 s.

The pose at t=0 is the pose at t=duration, and the step across that seam
matches an ordinary frame. Location swaps happen only while the lens is in
cloud or inside the cabin.
"""

from __future__ import annotations

import math

from .aircraft import AMBER, BRIGHT, GREEN, RED, TRAVEL, TILE
from .clock import DURATION, word_end, word_time

# Camera keys: t, eye (plane-local metres), look-at, roll deg, lens mm.
# The path is periodic. t=0 is the chase out of the cloud deck.
# Nose is +X, tail is -X, fuselage about 66 m, tube center near z=6.
# Chase cameras sit behind the tail. Interior eyes sit in the aisle.
CAM_KEYS = [
    (0.00, (-46.0, 16.0, 12.0), (-10.0, 0.0, 5.5), 0.0, 28.0),
    (1.25, (-36.0, 22.0, 12.0), (-6.0, 0.5, 6.2), -2.0, 30.0),
    (2.15, (-18.0, 18.0, 11.0), (2.0, 0.0, 6.0), -1.0, 30.0),
    (2.85, (6.0, 14.0, 10.0), (18.0, 0.0, 6.4), 4.0, 28.0),
    (3.30, (24.0, 8.0, 9.0), (32.0, 0.2, 6.5), 8.0, 26.0),
    (3.75, (8.0, 20.0, 14.0), (4.0, 0.0, 6.0), 18.0, 28.0),
    (4.70, (-4.0, 36.0, 16.0), (-2.0, 0.0, 5.0), 4.0, 26.0),
    (7.50, (-10.0, 42.0, 18.0), (-6.0, 0.0, 5.5), -3.0, 24.0),
    (9.80, (-22.0, 28.0, 20.0), (-16.0, 0.0, 6.0), -14.0, 26.0),
    (10.80, (-8.0, 48.0, 22.0), (-4.0, 0.0, 6.0), -4.0, 24.0),
    (13.80, (-14.0, 40.0, 18.0), (-12.0, 0.0, 5.8), -2.0, 26.0),
    (15.60, (-28.0, 26.0, 14.0), (-18.0, 0.5, 6.0), 2.0, 28.0),
    (16.80, (-24.0, 16.0, 10.0), (-16.0, 0.4, 6.2), 0.0, 30.0),
    (17.90, (-12.0, 18.0, 16.0), (-8.0, 0.0, 6.0), 6.0, 28.0),
    (18.70, (-2.0, 0.6, 16.0), (-2.0, 0.0, 5.5), 0.0, 24.0),
    (19.60, (-4.0, 0.2, 24.0), (-4.0, 0.0, 5.5), 0.0, 22.0),
    (20.40, (-8.0, 0.4, 20.0), (-14.0, 0.0, 5.5), 1.0, 24.0),
    (21.70, (-14.0, 0.6, 16.0), (-20.0, 0.0, 5.5), -1.0, 26.0),
    (23.00, (-12.0, 1.2, 14.0), (-16.0, 0.2, 5.5), 2.0, 28.0),
    (24.30, (-22.0, 0.4, 7.2), (-30.0, 0.0, 6.2), 8.0, 26.0),
    (25.10, (-40.0, 16.0, 12.0), (-18.0, 0.2, 6.2), 6.0, 28.0),
    (26.30, (-16.0, 1.6, 12.0), (-16.2, 0.2, 5.5), -4.0, 30.0),
    (27.50, (-16.4, 0.8, 9.5), (-16.6, 0.1, 5.5), 0.0, 34.0),
    (28.90, (-30.0, 18.0, 14.0), (-12.0, 0.0, 6.0), -3.0, 26.0),
    (30.60, (-48.0, 24.0, 16.0), (-10.0, 0.4, 6.0), 1.0, 24.0),
    (31.90, (-50.0, 21.0, 14.5), (-12.0, 0.6, 6.0), 0.4, 26.0),
    (32.45, (-44.5, 15.2, 11.6), (-10.2, 0.2, 5.4), 0.1, 28.0),
]

ALT_KEYS = [
    (0.00, 168.0),
    (1.30, 136.0),
    (3.50, 152.0),
    (4.15, 196.0),
    (6.80, 108.0),
    (9.80, 210.0),
    (10.20, 1650.0),
    (12.50, 1750.0),
    (16.20, 1680.0),
    (18.15, 320.0),
    (19.20, 168.0),
    (23.00, 150.0),
    (24.50, 198.0),
    (26.80, 118.0),
    (29.40, 390.0),
    (31.50, 300.0),
    (32.40, 200.0),
]

PITCH_KEYS = [
    (0.00, 7.0),
    (1.40, 2.0),
    (6.00, 0.5),
    (16.00, -1.5),
    (24.00, 1.0),
    (29.20, -2.0),
    (31.70, 9.0),
    (32.45, 8.0),
]

ROLL_KEYS = [
    (0.00, 0.0),
    (3.10, 2.0),
    (3.65, 26.0),
    (4.60, 6.0),
    (9.40, -4.0),
    (10.05, -20.0),
    (10.90, -4.0),
    (24.10, 6.0),
    (24.90, 16.0),
    (25.80, 3.0),
    (32.40, 0.4),
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


def _inside(eye) -> bool:
    x, y, z = eye
    return abs(y) < 2.4 and 8.5 < z < 20.0 and -22.0 < x < 12.0


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
    """Front and middle stay the same amber. Scatter is a per-seat mix in the shader."""
    aisle = _smooth(word_time(41), word_time(41) + 0.16, t) * (1.0 - _smooth(24.20, 24.50, t))
    best = _smooth(word_time(47), word_time(47) + 0.14, t) * (1.0 - _smooth(28.85, 29.20, t))

    def mix(a, b, u):
        return tuple(ai + (bi - ai) * u for ai, bi in zip(a, b))

    return {
        "front": AMBER,
        "mid": AMBER,
        "back": GREEN,
        "worst": mix(AMBER, RED, aisle),
        "best": mix(GREEN, BRIGHT, best),
    }


def pose_at(t: float) -> dict:
    """World-ready pose. t is wrapped onto [0, duration)."""
    t = t % DURATION
    eye, look, cam_roll, lens = _sample_cam(t)
    # A slow periodic drift so a key with a flat tangent still moves.
    drift = (
        0.35 * math.sin(2.0 * math.pi * t / DURATION),
        0.22 * math.sin(4.0 * math.pi * t / DURATION),
        0.12 * math.cos(2.0 * math.pi * t / DURATION),
    )
    eye = tuple(eye[i] + drift[i] for i in range(3))
    alt = _sample([(k[0], (k[1],)) for k in ALT_KEYS], t)[0]
    pitch = _sample([(k[0], (k[1],)) for k in PITCH_KEYS], t)[0]
    roll = _sample([(k[0], (k[1],)) for k in ROLL_KEYS], t)[0]
    roll += 1.15 * math.sin(2.0 * math.pi * t / DURATION)
    yaw = 1.4 * math.sin(2.0 * math.pi * t / DURATION)

    shake_amp = _gauss(t, word_time(44), 0.08, 1.0)
    shake = (
        shake_amp * 0.045 * math.sin(t * 86.0),
        shake_amp * 0.03 * math.sin(t * 74.0 + 1.7),
        shake_amp * 0.02 * math.sin(t * 91.0 + 0.4),
    )
    eye = tuple(eye[i] + shake[i] for i in range(3))

    cover = cloud_cover(t)
    inside = _inside(eye)
    # X-ray is a short beat on each third, not the whole flight.
    xray = max(
        _gauss(t, word_time(26), 1.05),
        _gauss(t, word_time(31), 1.05),
        _gauss(t, word_time(34), 1.15),
    )
    interior = _smooth(22.45, 22.75, t) * (1.0 - _smooth(27.45, 27.85, t))
    scatter = _smooth(word_time(59), word_time(59) + 0.10, t) * (1.0 - _smooth(word_time(63), word_time(63) + 0.05, t))
    colors = _zone_colors(t)
    distance = TRAVEL * (t / DURATION)

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
        "inside": inside or interior > 0.5,
        "xray": 0.0 if interior > 0.4 else xray,
        "interior": interior > 0.5,
        "scroll": distance % TILE,
        "distance": distance,
        "explode": 0.50 * _smooth(10.55, 11.20, t) * (1.0 - _smooth(17.20, 17.80, t)),
        "colors": colors,
        "strength": {
            "front": 1.0 + 1.15 * _gauss(t, word_time(11), 0.10) + 0.65 * _gauss(t, word_time(26), 0.16),
            "mid": 1.0 + 0.65 * _gauss(t, word_time(31), 0.16),
            "back": 1.25 + 0.95 * _gauss(t, word_time(1), 0.13) + 1.05 * _gauss(t, word_time(34), 0.15) + 0.75 * _gauss(t, word_time(47), 0.14),
        },
        "glint": _gauss(t, word_time(7), 0.16),
        "icons": icons,
        "icon_split": _smooth(word_time(21), word_time(21) + 0.18, t),
        "show_card": _window(t, word_time(15), 9.70),
        "show_17": _window(t, word_time(17), 9.55, 0.08, 0.25),
        "show_38": _window(t, word_time(26), 17.70),
        "show_39": _window(t, word_time(31), 17.85),
        "show_32": _window(t, word_time(34), 18.05),
        "show_44": _window(t, word_time(44), 24.15, 0.06, 0.18),
        "show_28": _window(t, word_time(54), 28.45, 0.06, 0.20),
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
