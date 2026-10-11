"""Voice clock. Same schema as ``engine.spec.words_document``."""

from __future__ import annotations

from ui._load import sibling_spec


def voice_clock(duration: float, beats: list[dict]) -> dict:
    """beats need narration, start, end. Returns {duration, words:[{w,t0,t1}]}."""
    resolved = {"duration": duration, "beats": beats}
    return sibling_spec().words_document(resolved)
