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
# Nose is +X, tail is -X, tube center near z=6. The path is periodic.
# Every eye stays on the -Y side and above the wing, so the spline cannot
# pass through the fuselage, the fin, or a wing. Roll stays 0: the horizon
# is level and the jet sits upright in the 9:16 frame. t=0 matches the end.
CAM_KEYS = [
    # High rear 3/4. The fuselage runs up the phone, the horizon stays level.
    # Eyes stay above the wing (z >= 18) and off the fin (|y| >= 10).
    (0.00, (-64.0, -8.0, 30.0), (0.0, 0.0, 6.2), 0.0, 26.0),
    (2.60, (-60.0, -10.0, 28.0), (8.0, 0.0, 6.0), 0.0, 26.0),
    (4.50, (-60.0, -9.0, 32.0), (8.0, 0.0, 6.0), 0.0, 24.0),
    (7.20, (-58.0, -8.0, 28.0), (2.0, 0.0, 5.0), 0.0, 24.0),
    (9.40, (-60.0, -8.0, 26.0), (4.0, 0.0, 5.5), 0.0, 24.0),
    (11.40, (-50.0, -11.0, 42.0), (2.0, 0.0, 6.2), 0.0, 24.0),
    (14.40, (-48.0, -10.0, 40.0), (1.0, 0.0, 6.4), 0.0, 24.0),
    (17.40, (-50.0, -10.0, 38.0), (0.0, 0.0, 6.4), 0.0, 24.0),
    (20.60, (-24.0, -8.0, 24.0), (2.0, 0.0, 6.8), 0.0, 28.0),
    (23.30, (-18.0, -4.0, 26.0), (2.0, 0.0, 7.0), 0.0, 28.0),
    (27.20, (-28.0, -4.0, 26.0), (-8.0, 0.0, 7.0), 0.0, 28.0),
    (29.50, (-42.0, -9.0, 28.0), (0.0, 0.0, 6.4), 0.0, 24.0),
    (32.55, (-64.0, -8.0, 30.0), (0.0, 0.0, 6.2), 0.0, 26.0),
]

# Metres above the ground. Flat biomes stay a flyover. The mountain beat
# stays above the range. Nothing descends into the city at the loop.
ALT_KEYS = [
    (0.00, 640.0),
    (3.20, 680.0),
    (4.20, 980.0),
    (6.60, 320.0),
    (9.60, 340.0),
    (10.40, 2200.0),
    (16.80, 2100.0),
    (18.40, 720.0),
    (24.00, 680.0),
    (28.40, 700.0),
    (31.40, 660.0),
    (32.55, 640.0),
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
    # Vertical only: a sideways drift can tuck the lens into a wing.
    drift_z = 0.18 * math.sin(2.0 * math.pi * t / DURATION)
    eye = (eye[0], eye[1], eye[2] + drift_z)
    eye = _keep_clear(eye)
    alt = _sample([(k[0], (k[1],)) for k in ALT_KEYS], t)[0]
    pitch = _sample([(k[0], (k[1],)) for k in PITCH_KEYS], t)[0]
    roll = _sample([(k[0], (k[1],)) for k in ROLL_KEYS], t)[0]
    yaw = 0.35 * math.sin(2.0 * math.pi * t / DURATION)

    shake_amp = _gauss(t, word_time(44), 0.08, 1.0)
    shake = (
        shake_amp * 0.045 * math.sin(t * 86.0),
        shake_amp * 0.03 * math.sin(t * 74.0 + 1.7),
        shake_amp * 0.02 * math.sin(t * 91.0 + 0.4),
    )
    eye = _keep_clear(tuple(eye[i] + shake[i] for i in range(3)))

    cover = cloud_cover(t)
    # The lens never enters the cabin. Seat beats are an open roof seen from
    # outside, which is the only way to show the rows without a black frame.
    inside = False
    xray = _window(t, 10.90, 17.95, 0.30, 0.35)
    cutaway = _window(t, 19.20, 28.45, 0.30, 0.40) > 0.5
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
        "inside": inside,
        "xray": xray,
        "interior": False,
        "cutaway": cutaway,
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
