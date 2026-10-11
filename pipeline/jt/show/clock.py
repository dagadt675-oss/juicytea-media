"""Beat clock read from words.json.

A new take is a new file at the same path. Render again and the picture
moves with the words. Nothing else has to be edited.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

FPS = 30


def _clean(token: str) -> str:
    return token.strip(".,?!…:;\"'").upper()


@dataclass
class Clock:
    words: list
    audio_duration: float
    tail0: float
    tail1: float
    frames: int
    duration: float
    sixteen: float
    heres: float
    excuse0: float
    excuse1: float
    wait0: float
    wait1: float
    hi0: float
    hi1: float
    algeria: float
    congo: float
    drag: float
    shrinks: tuple
    fourteen: float
    drop: float
    usa: float
    china: float
    india: float
    europe: float
    still: float
    room: float
    lying: float
    africa14: float
    outro: float

    def t(self, needle: str, after: float = 0.0, nth: int = 0) -> float:
        hits = []
        want = _clean(needle)
        for word in self.words:
            if float(word["t0"]) < after - 1e-6:
                continue
            token = _clean(str(word["w"]))
            if token == want or want in token:
                hits.append(float(word["t0"]))
        if len(hits) <= nth:
            raise KeyError(f"word {needle!r} after {after} not in words.json")
        return hits[nth]


def load_clock(path: str | Path) -> Clock:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    words = list(raw["words"])
    audio = float(raw["duration"])
    last = max(float(w["t1"]) for w in words)
    frames = max(2, math.ceil(audio * FPS - 1e-9))
    tail1 = (frames - 1) / FPS
    # The return starts when the last word ends, and must finish on the last frame.
    tail0 = min(last, tail1 - (1.0 / FPS))
    clock = Clock(
        words=words,
        audio_duration=audio,
        tail0=tail0,
        tail1=tail1,
        frames=frames,
        duration=frames / FPS,
        sixteen=0, heres=0, excuse0=0, excuse1=0, wait0=0, wait1=0,
        hi0=0, hi1=0, algeria=0, congo=0, drag=0, shrinks=(),
        fourteen=0, drop=0, usa=0, china=0, india=0, europe=0,
        still=0, room=0, lying=0, africa14=0, outro=0,
    )
    # Fill from the words. The second "Algeria" is the comparison, not the hook.
    clock.sixteen = clock.t("SIXTEEN")
    clock.heres = clock.t("HERE")
    excuse = next(w for w in words if "excuse" in str(w["w"]).lower())
    clock.excuse0, clock.excuse1 = float(excuse["t0"]), float(excuse["t1"])
    wait = next(w for w in words if "wait" in str(w["w"]).lower())
    clock.wait0, clock.wait1 = float(wait["t0"]), float(wait["t1"])
    hi = next(w for w in words if str(w["w"]).lower().startswith("hi"))
    clock.hi0, clock.hi1 = float(hi["t0"]), float(hi["t1"])
    clock.algeria = clock.t("ALGERIA", after=10)
    clock.congo = clock.t("CONGO", after=10)
    clock.drag = clock.t("DRAG")
    clock.shrinks = tuple(clock.t("SHRINK", nth=i) for i in range(3))
    clock.fourteen = clock.t("FOURTEEN")
    clock.drop = clock.t("DROP")
    clock.usa = clock.t("USA")
    clock.china = clock.t("CHINA")
    clock.india = clock.t("INDIA")
    clock.europe = clock.t("EUROPE")
    clock.still = clock.t("STILL")
    clock.room = clock.t("ROOM")
    clock.lying = clock.t("LYING")
    # "Africa is FOURTEEN", not the earlier "drop it on Africa".
    clock.africa14 = clock.t("AFRICA", after=clock.drop + 0.8)
    clock.outro = clock.t("NEXT", after=clock.room - 0.2)
    return clock
