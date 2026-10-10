"""Point clouds for heaps and crowds.

The picture instances a capped set of meshes. The counter still shows the
real count. A heap of 2^64 grains is not 2^64 objects.
"""

from __future__ import annotations

import math
import random


def cone_points(n: int, radius: float, height: float, seed: int = 1, cap: int = 8000) -> list[tuple[float, float, float]]:
    count = max(1, min(int(n), cap))
    rng = random.Random(seed)
    points = []
    for _ in range(count):
        # Volume-uniform sample of a cone standing on z=0.
        u = rng.random()
        h = height * (u ** (1.0 / 3.0))
        # At height h the cone radius is radius * (1 - h/height) if the tip is at z=height
        # and the base is at z=0. Base is wide.
        local_r = radius * (1.0 - h / height) if height else 0.0
        ang = rng.random() * math.tau
        rad = local_r * math.sqrt(rng.random())
        points.append((rad * math.cos(ang), rad * math.sin(ang), h))
    return points


def ellipse_points(n: int, area_m2: float, seed: int = 1, cap: int = 5000) -> list[tuple[float, float, float]]:
    """People standing in an ellipse of the given area. z is 0."""
    count = max(1, min(int(n), cap))
    # 2:1 ellipse, area = pi * a * b, a = 2b => area = 2 pi b^2
    b = math.sqrt(area_m2 / (2.0 * math.pi))
    a = 2.0 * b
    rng = random.Random(seed)
    points = []
    # Rejection keeps them inside the ellipse.
    guard = 0
    while len(points) < count and guard < count * 20:
        guard += 1
        x = rng.uniform(-a, a)
        y = rng.uniform(-b, b)
        if (x / a) ** 2 + (y / b) ** 2 <= 1.0:
            points.append((x, y, 0.0))
    return points
