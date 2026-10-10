"""Log-scale camera and scene-layer swapping.

Each layer is built in its own Blender unit system where the subject is a
few units tall. Python keeps true metres. Nothing sent to Blender is far
enough from the origin for float32 to fall apart — that is the whole point
of the swap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .quantity import AU_M, LY_M


@dataclass(frozen=True)
class Layer:
    id: str
    h_min: float
    h_max: float
    meters_per_bu: float
    family: str  # macro | space | room | micro
    # Fade width in log10(height) decades, inside each edge.
    fade: float = 0.20


# Ranges overlap on purpose so two neighbouring plates can crossfade.
LAYERS: tuple[Layer, ...] = (
    Layer("interior", 1.0e-4, 0.55, 0.01, "macro"),
    Layer("city", 0.22, 1400.0, 1.0, "macro"),
    Layer("aerial", 550.0, 6.0e4, 25.0, "macro"),
    Layer("orbit", 2.5e4, 8.0e6, 2.0e5, "space"),
    Layer("cislunar", 4.0e6, 8.0e8, 2.0e7, "space"),
    Layer("solar", 4.0e8, 2.0e13, 5.0e10, "space"),
    Layer("galaxy", 8.0e12, 2.0e21, 1.0e18, "space"),
    Layer("cosmic", 8.0e20, 2.0e27, 1.0e24, "space"),
    Layer("room", 0.28, 2.4, 0.05, "room"),
    Layer("tabletop", 1.5e-3, 0.45, 0.002, "micro"),
    Layer("fibers", 1.5e-5, 3.0e-3, 5.0e-5, "micro"),
    Layer("cells", 4.0e-7, 4.0e-5, 1.0e-6, "micro"),
    Layer("viruses", 8.0e-9, 8.0e-7, 2.0e-8, "micro"),
    Layer("molecules", 8.0e-11, 1.5e-8, 5.0e-10, "micro"),
    Layer("atoms", 2.0e-12, 2.0e-10, 5.0e-12, "micro"),
    Layer("atom_void", 2.0e-14, 4.0e-12, 1.0e-13, "micro"),
    Layer("nucleus", 2.0e-16, 4.0e-14, 1.0e-15, "micro"),
    Layer("proton", 2.0e-17, 3.0e-15, 1.0e-16, "micro"),
)

_FAMILIES = {
    "out": ("macro", "space"),
    "in": ("room", "micro"),
}


def layers_for(direction: str) -> list[Layer]:
    fam = _FAMILIES[direction]
    return [layer for layer in LAYERS if layer.family in fam]


def _smooth(edge0: float, edge1: float, x: float) -> float:
    if edge1 <= edge0:
        return 1.0 if x >= edge1 else 0.0
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def layer_weights(height_m: float, direction: str) -> dict[str, float]:
    h = max(float(height_m), 1e-30)
    log_h = math.log10(h)
    raw: dict[str, float] = {}
    usable = layers_for(direction)
    for layer in usable:
        a = math.log10(layer.h_min)
        b = math.log10(layer.h_max)
        fade = layer.fade
        if log_h <= a or log_h >= b:
            w = 0.0
        else:
            w_in = _smooth(a, a + fade, log_h)
            w_out = 1.0 - _smooth(b - fade, b, log_h)
            w = min(w_in, w_out)
        if w > 0.0:
            raw[layer.id] = w
    if not raw:
        # Clamp to the nearest layer so a spec that overshoots still frames.
        nearest = min(usable, key=lambda layer: min(abs(math.log10(layer.h_min) - log_h), abs(math.log10(layer.h_max) - log_h)))
        raw[nearest.id] = 1.0
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def layer_by_id(layer_id: str) -> Layer:
    for layer in LAYERS:
        if layer.id == layer_id:
            return layer
    raise KeyError(layer_id)


@dataclass(frozen=True)
class Pose:
    """Camera in true metres. Looks at ``target``. No roll, no lateral offset."""

    cam: tuple[float, float, float]
    target: tuple[float, float, float]
    distance_m: float
    pitch_deg: float


def framing_distance(height_m: float, framing: float, fov_y: float) -> float:
    """Distance at which ``height_m`` subtends ``framing`` of the vertical FOV."""
    ang = max(1e-4, framing * fov_y)
    return (max(height_m, 1e-30) * 0.5) / math.tan(ang * 0.5)


def fov_y(lens_mm: float, sensor_height_mm: float) -> float:
    return 2.0 * math.atan(sensor_height_mm / (2.0 * lens_mm))


def fov_x(lens_mm: float, sensor_height_mm: float, width: int, height: int) -> float:
    sensor_w = sensor_height_mm * (width / height)
    return 2.0 * math.atan(sensor_w / (2.0 * lens_mm))


def pose_for(
    height_m: float,
    direction: str,
    hold_distance_m: float,
    framing: float,
    pitch_deg: float,
    look_frac: float,
    lens_mm: float,
    sensor_height_mm: float,
) -> Pose:
    """Monotonic dolly. Zoom out never gets closer than the hook; zoom in never gets farther."""
    fy = fov_y(lens_mm, sensor_height_mm)
    d_frame = framing_distance(height_m, framing, fy)
    if direction == "out":
        dist = max(hold_distance_m, d_frame)
    elif direction == "in":
        dist = min(hold_distance_m, d_frame)
    else:
        raise ValueError(direction)
    pitch = math.radians(pitch_deg)
    target_z = max(height_m, 0.0) * look_frac
    cam = (
        0.0,
        -dist * math.cos(pitch),
        target_z + dist * math.sin(pitch),
    )
    target = (0.0, 0.0, target_z)
    return Pose(cam, target, dist, pitch_deg)


def to_bu(point_m: tuple[float, float, float], meters_per_bu: float) -> tuple[float, float, float]:
    s = 1.0 / meters_per_bu
    return (point_m[0] * s, point_m[1] * s, point_m[2] * s)


def project(
    pose: Pose,
    point_m: tuple[float, float, float],
    width: int,
    height: int,
    lens_mm: float,
    sensor_height_mm: float,
) -> tuple[float, float] | None:
    """Pixel coordinate (x right, y down). Matches a Blender camera with
    sensor fit VERTICAL, track-to -Z, up +Y.
    """
    vx = pose.target[0] - pose.cam[0]
    vy = pose.target[1] - pose.cam[1]
    vz = pose.target[2] - pose.cam[2]
    fl = math.sqrt(vx * vx + vy * vy + vz * vz) or 1.0
    forward = (vx / fl, vy / fl, vz / fl)
    # Blender camera looks down local -Z. Local +Y is up (track-to UP_Y, world +Z).
    z_axis = (-forward[0], -forward[1], -forward[2])
    dot_up = z_axis[2]
    ux = -z_axis[0] * dot_up
    uy = -z_axis[1] * dot_up
    uz = 1.0 - z_axis[2] * dot_up
    ul = math.sqrt(ux * ux + uy * uy + uz * uz)
    if ul < 1e-8:
        return None
    up = (ux / ul, uy / ul, uz / ul)
    rx = up[1] * z_axis[2] - up[2] * z_axis[1]
    ry = up[2] * z_axis[0] - up[0] * z_axis[2]
    rz = up[0] * z_axis[1] - up[1] * z_axis[0]
    right = (rx, ry, rz)
    rel = (
        point_m[0] - pose.cam[0],
        point_m[1] - pose.cam[1],
        point_m[2] - pose.cam[2],
    )
    x = rel[0] * right[0] + rel[1] * right[1] + rel[2] * right[2]
    y = rel[0] * up[0] + rel[1] * up[1] + rel[2] * up[2]
    z = rel[0] * forward[0] + rel[1] * forward[1] + rel[2] * forward[2]
    if z <= 1e-8:
        return None
    fy = fov_y(lens_mm, sensor_height_mm)
    aspect = width / height
    x_ndc = (x / z) / (math.tan(fy * 0.5) * aspect)
    y_ndc = (y / z) / math.tan(fy * 0.5)
    sx = (x_ndc * 0.5 + 0.5) * width
    sy = (1.0 - (y_ndc * 0.5 + 0.5)) * height
    return sx, sy


def visible_half_width(pose: Pose, lens_mm: float, sensor_height_mm: float, width: int, height: int) -> float:
    fx = fov_x(lens_mm, sensor_height_mm, width, height)
    return pose.distance_m * math.tan(fx * 0.5)


def place_proxy(
    object_height_m: float,
    pile_height_m: float,
    pile_radius_m: float,
    pose: Pose,
    lens_mm: float,
    sensor_height_mm: float,
    width: int,
    height: int,
    side: float = 1.0,
) -> tuple[float, float, float]:
    """World position of a reference object's base, in metres.

    Put it on the right, inside the frame at the moment the pile matches
    its height, and far enough out that a good portion stands above the slope.
    """
    half = visible_half_width(pose, lens_mm, sensor_height_mm, width, height)
    # Start well inside the frame, then walk outward until the top clears the cone.
    x = side * min(half * 0.48, max(pile_radius_m * 0.28, object_height_m * 0.45))
    limit = half * 0.62
    if pile_radius_m > 1e-6 and pile_height_m > 0:
        for _ in range(24):
            slope = pile_height_m * max(0.0, 1.0 - abs(x) / pile_radius_m)
            stick = object_height_m - slope
            if stick >= object_height_m * 0.72 or abs(x) >= limit:
                break
            x = side * min(limit, abs(x) * 1.22 + object_height_m * 0.08)
    # Pull the prop slightly toward the camera so a tower behind it
    # doesn't swallow the leader target.
    return (x, -abs(x) * 0.35, 0.0)


def float32_ok(coords: list[tuple[float, float, float]], min_span: float) -> bool:
    """True when these layer-local coordinates survive float32."""
    if min_span <= 0:
        return False
    peak = 0.0
    for c in coords:
        for v in c:
            peak = max(peak, abs(v))
            if abs(v) > 50_000.0:
                return False
    # ulp(float32) around `peak` is about 2**(exponent-23).
    if peak < 1e-8:
        return False
    exp = math.floor(math.log2(peak))
    ulp = 2.0 ** (exp - 23)
    return min_span > 800.0 * ulp


# Re-export astronomical constants used by space builders via the job.
SPACE = {
    "au_m": AU_M,
    "ly_m": LY_M,
}
