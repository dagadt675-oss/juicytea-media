"""Physical quantities for scale-journey episodes.

True sizes stay in Python floats (float64). Blender only ever sees a
per-layer coordinate system — see ``camera.to_layer``.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# IAU / IERS conventional values.
AU_M = 149_597_870_700.0
LY_M = 9_460_730_472_580_800.0
EARTH_RADIUS_M = 6_371_000.0
MOON_RADIUS_M = 1_737_400.0
MOON_DISTANCE_M = 384_400_000.0
SUN_RADIUS_M = 695_700_000.0

_LADDER = (
    (1e-15, "fm"),
    (1e-12, "pm"),
    (1e-9, "nm"),
    (1e-6, "um"),
    (1e-3, "mm"),
    (1e-2, "cm"),
    (1.0, "m"),
    (1e3, "km"),
    (0.05 * AU_M, "AU"),
    (0.05 * LY_M, "ly"),
)


@dataclass(frozen=True)
class RiceParams:
    days: int = 64
    grain_length_m: float = 0.0066
    grain_width_m: float = 0.0021
    grain_thickness_m: float = 0.0017
    grain_mass_kg: float = 2.1e-5
    bulk_density_kg_m3: float = 800.0
    repose_deg: float = 34.0
    world_production_tonnes: float = 538_900_000.0


@dataclass(frozen=True)
class ShrinkParams:
    start_m: float = 1.70
    # size(t) = start_m * 2**(-t_seconds)


@dataclass(frozen=True)
class Metrics:
    param: float
    height_m: float
    radius_m: float
    grains: float
    mass_kg: float
    volume_m3: float
    visual: str  # grains | cone | person | orb


def _cone(volume_m3: float, repose_deg: float) -> tuple[float, float]:
    tan_t = math.tan(math.radians(repose_deg))
    height = (3.0 * volume_m3 * tan_t * tan_t / math.pi) ** (1.0 / 3.0)
    radius = height / tan_t
    return height, radius


def rice_metrics(day: float, p: RiceParams) -> Metrics:
    """Pile on day ``day`` (day 1 = 1 grain, day n = 2**(n-1) grains)."""
    day = min(max(float(day), 1.0), float(p.days))
    grains = 2.0 ** (day - 1.0)
    mass = grains * p.grain_mass_kg
    volume = mass / p.bulk_density_kg_m3
    height, radius = _cone(volume, p.repose_deg)
    # A lone grain lies on the desk: its vertical extent is its thickness,
    # and it is longer than the cone formula's tiny mound.
    if grains < 12.0:
        heap_h = p.grain_thickness_m * (1.0 + 0.42 * (grains - 1.0) ** 0.55)
        heap_r = p.grain_length_m * (0.55 + 0.22 * (grains - 1.0) ** 0.5)
        height = max(height, heap_h)
        radius = max(radius, heap_r)
    visual = "grains" if grains < 28.0 else "cone"
    return Metrics(day, height, radius, grains, mass, volume, visual)


def rice_day_for_height(height_m: float, p: RiceParams) -> float:
    if height_m <= rice_metrics(1.0, p).height_m:
        return 1.0
    if height_m >= rice_metrics(float(p.days), p).height_m:
        return float(p.days)
    lo, hi = 1.0, float(p.days)
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        if rice_metrics(mid, p).height_m < height_m:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def rice_day_for_volume(volume_m3: float, p: RiceParams) -> float:
    grains = volume_m3 * p.bulk_density_kg_m3 / p.grain_mass_kg
    if grains <= 1.0:
        return 1.0
    day = math.log2(grains) + 1.0
    return min(max(day, 1.0), float(p.days))


def harvest_years(grains: float, p: RiceParams) -> float:
    tonnes = grains * p.grain_mass_kg / 1000.0
    return tonnes / p.world_production_tonnes


def shrink_metrics(second: float, p: ShrinkParams) -> Metrics:
    second = max(0.0, float(second))
    height = p.start_m * 2.0 ** (-second)
    # The subject is "you". Radius is a stand-in shoulder half-width.
    radius = height * 0.14
    visual = "person" if height > 0.004 else "orb"
    return Metrics(second, height, radius, 0.0, 0.0, 0.0, visual)


def choose_unit(meters: float) -> tuple[str, float]:
    """Return (unit name, value in that unit)."""
    m = abs(float(meters))
    if m == 0.0:
        return "m", 0.0
    chosen = _LADDER[0]
    for threshold, name in _LADDER:
        if m + 1e-30 >= threshold:
            chosen = (threshold, name)
        else:
            break
    scale = {
        "fm": 1e-15,
        "pm": 1e-12,
        "nm": 1e-9,
        "um": 1e-6,
        "mm": 1e-3,
        "cm": 1e-2,
        "m": 1.0,
        "km": 1e3,
        "AU": AU_M,
        "ly": LY_M,
    }[chosen[1]]
    return chosen[1], m / scale


def decimals_for(value: float) -> int:
    v = abs(value)
    if v < 10.0:
        return 2
    if v < 100.0:
        return 1
    return 0


def format_length(meters: float) -> str:
    unit, value = choose_unit(meters)
    d = decimals_for(value)
    text = f"{value:.{d}f}"
    return f"{text} {unit}"


def format_count(n: float) -> str:
    n = float(n)
    if n < 1000:
        return str(int(round(n)))
    steps = (
        (1e18, "quintillion"),
        (1e15, "quadrillion"),
        (1e12, "trillion"),
        (1e9, "billion"),
        (1e6, "million"),
        (1e3, "thousand"),
    )
    for scale, name in steps:
        if n >= scale:
            return f"{n / scale:.2f} {name}"
    return str(int(n))


def format_mass_tonnes(kg: float) -> str:
    tonnes = kg / 1000.0
    return format_count(tonnes) + " tonnes"


def grain_layout(n: int, p: RiceParams, limit: int = 36) -> list[tuple[float, float, float, float]]:
    """Centres (x, y, z) and yaw in radians for up to ``limit`` grains, in metres.

    Grains lie on z = 0. Deterministic.
    """
    n = max(1, min(int(round(n)), limit))
    rng = random.Random(7)
    thick = p.grain_thickness_m
    length = p.grain_length_m
    out: list[tuple[float, float, float, float]] = []
    if n == 1:
        return [(0.0, 0.0, thick * 0.5, 0.55)]
    # Loose spiral, each grain resting on the table. Yaw jitters so it
    # doesn't look like a machine grid.
    for i in range(n):
        ang = i * 2.399963 + rng.uniform(-0.15, 0.15)
        rad = length * 0.55 * math.sqrt(i)
        yaw = ang + rng.uniform(-0.4, 0.4)
        out.append((rad * math.cos(ang), rad * math.sin(ang), thick * 0.5, yaw))
    return out
