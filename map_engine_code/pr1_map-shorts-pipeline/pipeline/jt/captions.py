"""Karaoke groups. 1–3 uppercase words. The spoken word is the yellow one.

The highlight index changes 0.04 s before the word start, inside the ±0.1 s window.
"""

from __future__ import annotations

import re

EARLY = 0.04
LINGER = 0.28
PUNCT = (".", "?", "!", ",", ";", ":")


def tokenize(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def is_keyword(token: str) -> bool:
    letters = [c for c in token if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def groups_for(words: list[dict]) -> list[list[int]]:
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        tok = w["text"]
        if tok.endswith(PUNCT) or len(cur) >= 3:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def active_index(words: list[dict], t: float) -> int | None:
    if not words or t + EARLY < words[0]["start"]:
        return None
    idx = 0
    for i, w in enumerate(words):
        if t + EARLY >= w["start"]:
            idx = i
        else:
            break
    w = words[idx]
    nxt = words[idx + 1]["start"] if idx + 1 < len(words) else 1e9
    if t > w["end"] + LINGER and t + EARLY < nxt:
        return None
    return idx


def switch_error(words: list[dict]) -> float:
    """Largest gap between a word start and the moment it becomes yellow."""
    if not words:
        return 0.0
    worst = 0.0
    prev = None
    t = words[0]["start"] - 0.2
    end = words[-1]["end"] + LINGER + 0.05
    while t <= end:
        idx = active_index(words, t)
        if idx is not None and idx != prev:
            worst = max(worst, abs((t) - (words[idx]["start"] - EARLY)))
            prev = idx
        t += 0.01
    return worst
