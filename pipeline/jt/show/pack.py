"""Place country shapes inside a land mask.

True-size masks are searched with a correlation. A fit is fully inside the
mask and clear of shapes already placed. If that has no answer, each shape
still sits inside the mask and the overlaps are allowed.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import fftconvolve


def _valid(field: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    return fftconvolve(field.astype(np.float32), kernel[::-1, ::-1], mode="valid")


def place_one(land: np.ndarray, occupied: np.ndarray | None, mask: np.ndarray,
              mcx: float, mcy: float, target: tuple[float, float], allow_overlap: bool,
              tol: float = 0.015):
    """Return (cx, cy, overlap_px) for the shape centroid, or None if it cannot sit inside.

    A 1.5% fringe counts as inside. Coastlines rasterized at different
    resolutions disagree by about that much, and a stricter test rejects a
    shape that is sitting on the coast.
    """
    sh, sw = mask.shape
    lh, lw = land.shape
    filled = float(mask.sum())
    if sh > lh or sw > lw or filled < 1:
        return None
    kernel = mask.astype(np.float32)
    outside = _valid((~land).astype(np.float32), kernel)
    over = _valid(occupied.astype(np.float32), kernel) if occupied is not None else np.zeros_like(outside)
    inside = outside <= max(6.0, tol * filled)
    if not np.any(inside):
        return None

    def pick(ys, xs, cost):
        cx = xs + mcx
        cy = ys + mcy
        i = int(np.argmin((cx - target[0]) ** 2 + (cy - target[1]) ** 2))
        return float(cx[i]), float(cy[i]), float(cost)

    if not allow_overlap:
        ok = inside & (over < 0.5)
        ys, xs = np.nonzero(ok)
        if len(xs) == 0:
            return None
        return pick(ys, xs, 0.0)
    # Prefer a spot near the target that is only partly covered. Stacking
    # two countries on the same centre hides both, even when overlap is allowed.
    ys, xs = np.nonzero(inside)
    cx = xs + mcx
    cy = ys + mcy
    filled = max(1.0, float(mask.sum()))
    dist = np.hypot(cx - target[0], cy - target[1]) / max(lh, lw)
    score = over[ys, xs] / filled + dist
    i = int(np.argmin(score))
    return float(cx[i]), float(cy[i]), float(over[ys[i], xs[i]])


def _stamp(occupied: np.ndarray, mask: np.ndarray, cx: float, cy: float, mcx: float, mcy: float) -> None:
    top = int(round(cy - mcy))
    left = int(round(cx - mcx))
    sh, sw = mask.shape
    y0 = max(0, top)
    x0 = max(0, left)
    y1 = min(occupied.shape[0], top + sh)
    x1 = min(occupied.shape[1], left + sw)
    if y1 <= y0 or x1 <= x0:
        return
    patch = mask[y0 - top:y1 - top, x0 - left:x1 - left]
    occupied[y0:y1, x0:x1] |= patch.astype(bool)


def layout(land: np.ndarray, items: list, targets: dict[str, tuple[float, float]]):
    """items: (name, variants) with variants (rot, mask, mcx, mcy).

    Returns ("fit" or "overlap", {name: (cx, cy, rot)}). Coordinates are
    centers in the land mask. None when a shape cannot fit inside at all.
    """

    def run(allow_overlap: bool):
        occupied = np.zeros(land.shape, np.bool_)
        placed = {}
        order = sorted(items, key=lambda it: max(int(v[1].sum()) for v in it[1]), reverse=True)
        for name, variants in order:
            target = targets.get(name, (land.shape[1] * 0.5, land.shape[0] * 0.35))
            best = None
            for rot, mask, mcx, mcy in variants:
                occ = occupied if allow_overlap or occupied.any() else None
                hit = place_one(land, occ, mask, mcx, mcy, target, allow_overlap)
                if hit is None:
                    continue
                cx, cy, cost = hit
                dist = (cx - target[0]) ** 2 + (cy - target[1]) ** 2
                score = cost * 1.0e6 + dist
                if best is None or score < best[0]:
                    best = (score, cx, cy, rot, mask, mcx, mcy, cost)
            if best is None:
                return None
            _, cx, cy, rot, mask, mcx, mcy, cost = best
            _stamp(occupied, mask, cx, cy, mcx, mcy)
            placed[name] = (cx, cy, rot, cost)
        return placed

    hard = run(False)
    if hard is not None:
        return "fit", {name: (cx, cy, rot) for name, (cx, cy, rot, _) in hard.items()}
    soft = run(True)
    if soft is None:
        return "overlap", {}
    mode = "fit" if all(cost < 0.5 for *_, cost in soft.values()) else "overlap"
    return mode, {name: (cx, cy, rot) for name, (cx, cy, rot, _) in soft.items()}
