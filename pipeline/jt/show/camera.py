"""Globe-to-map camera. Ease curves, snap segments, and a loop tail.

A segment whose projections differ is a crossfade, not a cut. Inside one
segment the centre and the span move one way. The tail eases onto the
opening camera and lands on it exactly at the last frame.
"""

from __future__ import annotations

from dataclasses import dataclass

from jt.loop_tail import tail_progress
from jt.project import ang_lerp


@dataclass(frozen=True)
class Cam:
    proj: str
    lon: float
    lat: float
    span: float


@dataclass(frozen=True)
class CamState:
    """`b` is set only while two projections crossfade. `u` is 0 on `a` and 1 on `b`."""

    a: Cam
    b: Cam | None = None
    u: float = 0.0

    def front(self) -> Cam:
        if self.b is not None and self.u >= 0.5:
            return self.b
        return self.a


def _ease(u: float, kind: str) -> float:
    u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
    if kind == "linear":
        return u
    if kind == "out":
        return 1.0 - (1.0 - u) * (1.0 - u)
    return u * u * (3.0 - 2.0 * u)


def mix(a: Cam, b: Cam, u: float) -> Cam:
    u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
    return Cam(
        b.proj,
        ang_lerp(a.lon, b.lon, u),
        a.lat + (b.lat - a.lat) * u,
        a.span + (b.span - a.span) * u,
    )


@dataclass(frozen=True)
class Key:
    t: float
    cam: Cam


class CameraTrack:
    def __init__(self, keys: list[Key], tail0: float, tail1: float):
        if len(keys) < 2:
            raise ValueError("camera needs at least two keys")
        self.keys = keys
        self.open = keys[0].cam
        self.tail0 = float(tail0)
        self.tail1 = float(tail1)
        if not (keys[0].t <= tail0 <= tail1):
            raise ValueError("tail must sit on the camera track")

    def _raw(self, t: float) -> CamState:
        keys = self.keys
        if t <= keys[0].t:
            return CamState(keys[0].cam)
        for i in range(len(keys) - 1):
            a, b = keys[i], keys[i + 1]
            if t > b.t:
                continue
            span = b.t - a.t
            u = 0.0 if span <= 1e-6 else (t - a.t) / span
            kind = "out" if i == 0 else "in_out"
            s = _ease(u, kind)
            if a.cam.proj != b.cam.proj:
                return CamState(a.cam, b.cam, s)
            return CamState(mix(a.cam, b.cam, s))
        return CamState(keys[-1].cam)

    def at(self, t: float) -> CamState:
        if t >= self.tail1:
            return CamState(self.open)
        if t > self.tail0:
            u = tail_progress(t, self.tail0, self.tail1)
            start = self._raw(self.tail0).front()
            return CamState(mix(start, self.open, u))
        return self._raw(t)
