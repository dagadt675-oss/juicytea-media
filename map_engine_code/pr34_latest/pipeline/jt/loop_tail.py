"""
Juicy Tea Map-Shorts Engine — Seamless Audio Loop Tail Module (Rule 7 & Section 8).
"""

from __future__ import annotations
import numpy as np

SAMPLE_RATE: int = 48000


def apply_seamless_audio_loop_tail(
    audio_stereo: np.ndarray,
    tail_overlap_s: float = 0.25,
) -> np.ndarray:
    """
    Eliminates dead silence at the end of the Short and wraps the final decay tail
    smoothly into Frame 0 using a smootherstep equal-power crossfade.
    """
    n_tail = int(round(tail_overlap_s * SAMPLE_RATE))
    if audio_stereo.shape[0] <= n_tail * 2:
        return audio_stereo

    rms_env = np.sqrt(np.mean(audio_stereo ** 2, axis=1))
    active_idx = np.where(rms_env > 1e-3)[0]
    if len(active_idx) > 0:
        last_active = min(audio_stereo.shape[0], int(active_idx[-1]) + int(0.12 * SAMPLE_RATE))
        audio_stereo = audio_stereo[:last_active]

    u = np.linspace(0.0, 1.0, n_tail, dtype=np.float64)[:, None]
    s = u * u * u * (u * (u * 6.0 - 15.0) + 10.0)

    tail_segment = audio_stereo[-n_tail:].copy()
    head_segment = audio_stereo[:n_tail].copy()
    audio_stereo[:n_tail] = head_segment * np.sqrt(s) + tail_segment * np.sqrt(1.0 - s)
    return audio_stereo
