"""SFX cue list. One cue per visual change, so a later mix can drop a hit on it.

Kinds: pop, whoosh, draw, stamp, boing, tick, impact.
"""

from __future__ import annotations

import json
from pathlib import Path


def pack(cues: list[tuple[float, str, str]]) -> list[dict]:
    out = []
    for t, kind, name in cues:
        out.append({"t": round(float(t), 3), "kind": kind, "name": name})
    out.sort(key=lambda row: (row["t"], row["name"]))
    return out


def lint_gaps(cues: list[dict], duration: float, limit: float = 2.0) -> tuple[float, list[tuple[float, float, float]]]:
    """No silent stretch longer than `limit` seconds, including the head and the tail."""
    times = [0.0]
    times.extend(float(c["t"]) for c in cues)
    times.append(float(duration))
    times = sorted(times)
    worst = 0.0
    bad = []
    for a, b in zip(times, times[1:]):
        gap = b - a
        if gap > worst:
            worst = gap
        if gap > limit + 1e-6:
            bad.append((a, b, gap))
    return worst, bad


def write_cues(path: Path, cues: list[dict], meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(meta)
    payload["cues"] = cues
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
