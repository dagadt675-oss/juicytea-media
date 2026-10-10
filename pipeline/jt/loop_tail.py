"""Seamless loop tail.

The last fraction of a picture eases, in one direction, into the opening
frame. The last frame is that opening frame, so a loop has nothing to snap.

`voice.loop_tail` is the time the return starts, after the last spoken word.
Everything before that time is left alone.
"""

from __future__ import annotations

import numpy as np


def tail_start(spec) -> float | None:
    raw = (getattr(spec, "voice", None) or {}).get("loop_tail")
    if raw in (None, "", False):
        return None
    return float(raw)


def last_frame_time(duration: float, fps: int = 30) -> float:
    """Time of the last frame. The duration itself is past that frame."""
    n = max(2, int(round(float(duration) * fps)))
    return (n - 1) / float(fps)


def tail_progress(t: float, start: float, end: float) -> float:
    """Monotonic blend. 0 at `start`, 1 at `end`, flat outside.

    Smoothstep keeps the slope at zero on both ends, so the handoff
    does not kick.
    """
    if end <= start or t <= start:
        return 0.0
    if t >= end:
        return 1.0
    x = (t - start) / (end - start)
    return x * x * (3.0 - 2.0 * x)


def opening_span(camera) -> float:
    """Span of frame 0, before any later tighten."""
    span = float(camera.span)
    push = getattr(camera, "push", None)
    if push:
        span *= float(push)
    return span


def ease_span_toward_open(span: float, open_span: float, u: float) -> float:
    """One direction: from the live span toward the opening span."""
    u = max(0.0, min(1.0, float(u)))
    return float(span) + (float(open_span) - float(span)) * u


def blend_toward_open(live: np.ndarray, opening: np.ndarray, u: float) -> np.ndarray:
    """u=0 is the live picture. u=1 is exactly the opening frame."""
    if u <= 0.0 or opening is None:
        return live
    if u >= 1.0:
        return opening.copy()
    a = live.astype(np.float32)
    b = opening.astype(np.float32)
    return np.clip(a * (1.0 - u) + b * u, 0, 255).astype(np.uint8)


def split_shots(spans: list[tuple[float, float]], start: float | None):
    """The return is its own shot, so its one-way ease is not a sway."""
    if start is None:
        return list(spans)
    out = []
    for a, b in spans:
        if a < start < b:
            out.append((a, start))
            out.append((start, b))
        else:
            out.append((a, b))
    return out
