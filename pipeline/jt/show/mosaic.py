"""Equal-area pieces inside a land mask.

Each land pixel belongs to one piece, so the painted mosaic does not
overlap and does not leave the coastline. A sprite that is larger than
its cell is clipped; that clipped part is the remainder.
"""

from __future__ import annotations

import numpy as np


def lloyd_seeds(mask: np.ndarray, n: int, rounds: int = 6) -> np.ndarray:
    """n centroids inside `mask`, spread so the cells have similar area."""
    ys, xs = np.nonzero(mask)
    if len(xs) < n:
        raise ValueError("land mask is smaller than the piece count")
    step = max(1, len(xs) // (n * 30))
    pool_x = xs[::step]
    pool_y = ys[::step]
    # Farthest-point seeds, then a few Lloyd passes.
    start = int(np.argmax((pool_x - pool_x.mean()) ** 2 + (pool_y - pool_y.mean()) ** 2))
    seeds = [(float(pool_x[start]), float(pool_y[start]))]
    for _ in range(n - 1):
        sx = np.array([s[0] for s in seeds])
        sy = np.array([s[1] for s in seeds])
        d2 = (pool_x[:, None] - sx) ** 2 + (pool_y[:, None] - sy) ** 2
        pick = int(np.argmax(d2.min(axis=1)))
        seeds.append((float(pool_x[pick]), float(pool_y[pick])))
    seeds_a = np.array(seeds, np.float64)
    for _ in range(rounds):
        d2 = (xs[:, None] - seeds_a[:, 0]) ** 2 + (ys[:, None] - seeds_a[:, 1]) ** 2
        owner = d2.argmin(axis=1)
        for i in range(n):
            take = owner == i
            if not np.any(take):
                continue
            seeds_a[i, 0] = float(xs[take].mean())
            seeds_a[i, 1] = float(ys[take].mean())
    return seeds_a


def cell_ids(mask: np.ndarray, seeds: np.ndarray) -> np.ndarray:
    """-1 off the land, otherwise the owning piece."""
    labels = np.full(mask.shape, -1, np.int16)
    ys, xs = np.nonzero(mask)
    d2 = (xs[:, None] - seeds[:, 0]) ** 2 + (ys[:, None] - seeds[:, 1]) ** 2
    labels[ys, xs] = d2.argmin(axis=1).astype(np.int16)
    return labels


def piece_order(seeds: np.ndarray) -> list[int]:
    """North to south, so the drops read as a sweep down the continent."""
    return list(np.argsort(seeds[:, 1]))


def sprite_coverage(labels: np.ndarray, sprite: np.ndarray, seed_xy: tuple[float, float], owner: int) -> tuple[int, int, int]:
    """Return (overlap_px, outside_px, total_px) for one sprite centred on seed_xy."""
    sh, sw = sprite.shape
    top = int(round(float(seed_xy[1]) - sh / 2.0))
    left = int(round(float(seed_xy[0]) - sw / 2.0))
    total = int(np.count_nonzero(sprite))
    y0 = max(0, top)
    x0 = max(0, left)
    y1 = min(labels.shape[0], top + sh)
    x1 = min(labels.shape[1], left + sw)
    if y1 <= y0 or x1 <= x0:
        return 0, total, total
    view = sprite[y0 - top:y1 - top, x0 - left:x1 - left].astype(bool)
    owners = labels[y0:y1, x0:x1]
    on_canvas = int(np.count_nonzero(view))
    outside = (total - on_canvas) + int(np.count_nonzero(view & (owners < 0)))
    overlap = int(np.count_nonzero(view & (owners >= 0) & (owners != owner)))
    return overlap, outside, total
