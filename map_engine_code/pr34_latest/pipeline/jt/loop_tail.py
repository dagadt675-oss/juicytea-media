"""
Juicy Tea Map-Shorts Engine — Seamless Audio Loop Tail.

The crossfade only blends the last fraction of a second onto frame 0.
It does not trim, shift, or replace the start of the voice.
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE: int = 48000


def apply_seamless_audio_loop_tail(
    audio_stereo: np.ndarray,
    tail_overlap_s: float = 0.25,
) -> np.ndarray:
    """Equal-power smootherstep crossfade of the tail onto the head."""
    n_tail = int(round(tail_overlap_s * SAMPLE_RATE))
    if audio_stereo.shape[0] <= n_tail * 2:
        return audio_stereo

    u = np.linspace(0.0, 1.0, n_tail, dtype=np.float64)[:, None]
    fade = u * u * u * (u * (u * 6.0 - 15.0) + 10.0)

    out = audio_stereo.copy()
    tail_segment = out[-n_tail:].copy()
    head_segment = out[:n_tail].copy()
    out[:n_tail] = head_segment * np.sqrt(fade) + tail_segment * np.sqrt(1.0 - fade)
    return out
