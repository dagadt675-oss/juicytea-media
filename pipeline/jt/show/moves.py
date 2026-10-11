"""Reusable camera moves, matched to the Budapest zoom reference.

The fast part of a zoom carries directional blur so a resolution change
never reads as mud. When the move slows, the blur is gone and the plate
is sharp. None of these draws a black field; the caller keeps a full-bleed
plate under every effect.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image


def _clamp(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def ease_out(u: float) -> float:
    """Fastest at the start. The intro drop."""
    u = _clamp(u)
    return 1.0 - (1.0 - u) ** 3


def ease_in(u: float) -> float:
    """Accelerates, fastest on the last frame. The match-cut dive."""
    u = _clamp(u)
    return u ** 3


def ease_in_out(u: float) -> float:
    u = _clamp(u)
    return u * u * (3.0 - 2.0 * u)


def ease_out_back(u: float) -> float:
    """Overshoot, then settle. Landmark pops and span drops."""
    u = _clamp(u)
    c1 = 1.70158
    c3 = c1 + 1.0
    t = u - 1.0
    return 1.0 + c3 * t ** 3 + c1 * t ** 2


def _window(t: float, t0: float, t1: float) -> float:
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return _clamp((t - t0) / (t1 - t0))


def drop_in(t: float, t0: float, t1: float) -> dict:
    """Intro drop. u is the zoom (0 wide, 1 arrived). blur is heavy while fast.

    Outside the window the plate is sharp: blur 0 before the drop and after it lands.
    """
    if t < t0 or t > t1:
        return {"u": 0.0 if t < t0 else 1.0, "blur": 0.0, "kind": "drop_in"}
    x = _window(t, t0, t1)
    u = ease_out(x)
    # Derivative of 1-(1-x)^3 is 3(1-x)^2, largest at x=0.
    speed = 3.0 * (1.0 - x) ** 2
    return {"u": u, "blur": min(1.0, speed * 0.55), "kind": "drop_in"}


def match_cut_dive(t: float, t0: float, t1: float) -> dict:
    """Ease-in dive. Radial blur spikes on the last fraction, then cuts to sharp."""
    if t < t0 or t > t1:
        return {"u": 0.0 if t < t0 else 1.0, "blur": 0.0, "radial": True, "kind": "match_cut_dive"}
    x = _window(t, t0, t1)
    u = ease_in(x)
    spike = max(0.0, (x - 0.72) / 0.28)
    return {"u": u, "blur": spike ** 1.4, "radial": True, "kind": "match_cut_dive"}


def country_extrude_flag(t: float, t0: float, dur: float = 0.55) -> dict:
    """Height of a 3D country extrude and the flag-fill crossfade."""
    u = ease_out(_window(t, t0, t0 + dur))
    return {"height": u, "flag": ease_in_out(_window(t, t0 + dur * 0.25, t0 + dur)), "border": u}


def river_trace(t: float, t0: float, dur: float = 0.8) -> float:
    """0–1 reveal along a polyline."""
    return ease_in_out(_window(t, t0, t0 + dur))


def border_glow(t: float, t0: float, dur: float = 0.7) -> float:
    return ease_out(_window(t, t0, t0 + dur))


def district_fill(t: float, t0: float, dur: float, count: int) -> int:
    """How many districts have filled. They stagger across `dur`."""
    if count <= 0 or t < t0:
        return 0
    u = _clamp((t - t0) / max(0.05, dur))
    return min(count, int(math.floor(u * count)) + 1)


def landmark_pop(t: float, t0: float, dur: float = 0.38) -> float:
    """Scale of a model popping in. Ease-out-back, so it overshoots then sits."""
    if t < t0:
        return 0.0
    return ease_out_back(_window(t, t0, t0 + dur))


def snap_explode(t: float, t0: float) -> dict:
    """Fast push-in, a particle burst, then a snap back out. About 0.45 s."""
    x = t - t0
    if x < 0 or x > 0.45:
        return {"push": 0.0, "particles": 0.0, "back": 0.0}
    if x < 0.16:
        return {"push": ease_in(x / 0.16), "particles": 0.0, "back": 0.0}
    if x < 0.28:
        return {"push": 1.0, "particles": (x - 0.16) / 0.12, "back": 0.0}
    return {"push": 1.0, "particles": 1.0 - (x - 0.28) / 0.17, "back": ease_out((x - 0.28) / 0.17)}


def apply_zoom_blur(img: np.ndarray, amount: float, radial: bool = False) -> np.ndarray:
    """Radial zoom blur. Kernel is glfx.js zoomBlur (MIT, Evan Wallace, 2011).

    Copyright (C) 2011 by Evan Wallace

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

    Samples are taken along the ray to the center and weighted by
    4 * (p - p * p), the same kernel as glfx `zoomBlur`. Eight taps stand in
    for the shader's forty so a full frame stays cheap.
    """
    if amount < 0.05:
        return img
    h, w = img.shape[:2]
    strength = (0.62 if radial else 0.28) * float(amount)
    strength = min(0.72, strength)
    # p = (tap + 0.5) / n hides the fixed tap count the way glfx's random offset does.
    n = 8
    acc = np.zeros((h, w, img.shape[2]), np.float32)
    total = 0.0
    src = Image.fromarray(img)
    for tap in range(n):
        p = (tap + 0.5) / n
        weight = 4.0 * (p - p * p)
        k = p * strength
        scale = 1.0 / max(1e-3, 1.0 - k)
        bw = max(2, int(round(w * scale)))
        bh = max(2, int(round(h * scale)))
        big = src.resize((bw, bh), Image.Resampling.BILINEAR)
        left = (bw - w) // 2
        top = (bh - h) // 2
        crop = np.asarray(big.crop((left, top, left + w, top + h)), dtype=np.float32)
        acc += crop * weight
        total += weight
    return np.clip(acc / total, 0, 255).astype(np.uint8)


def apply_vignette(img: np.ndarray, strength: float = 0.42) -> np.ndarray:
    """Darken the corners. The center stays the plate; corners do not go empty."""
    h, w = img.shape[:2]
    ys = np.linspace(-1.0, 1.0, h)[:, None]
    xs = np.linspace(-1.0, 1.0, w)[None, :]
    r = np.sqrt(xs * xs * 0.72 + ys * ys)
    vig = np.clip(1.0 - strength * np.clip(r - 0.35, 0, 1) ** 1.4, 0.48, 1.0)
    return np.clip(img.astype(np.float32) * vig[..., None], 0, 255).astype(np.uint8)
