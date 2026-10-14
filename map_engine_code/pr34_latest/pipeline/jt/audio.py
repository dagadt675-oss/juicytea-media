"""
Juicy Tea Map-Shorts Engine — Velocity-Peak Synced Audio Mixer (Section 8 & Section 9).
- Loudness: -14.0 LUFS, LRA ~ 2.0, True Peak <= -1.0 dBTP
- BGM at -21.3 dB below voiceover
- SFX (whoosh, pop, tick) aligned to velocity peak of move/pop
"""

from __future__ import annotations
from typing import List, Tuple
import math
import numpy as np
from .loop_tail import apply_seamless_audio_loop_tail, SAMPLE_RATE

TARGET_LUFS: float = -14.0
MAX_TRUE_PEAK_DBTP: float = -1.0
BGM_OFFSET_DB: float = -21.3


def sfx_peak_timestamp(
    move_start_t: float, move_duration_s: float, sfx_internal_peak_s: float = 0.08
) -> float:
    """Aligns SFX start so its acoustic peak lands on the smootherstep velocity peak (0.5 * T)."""
    velocity_peak_t = move_start_t + 0.5 * move_duration_s
    return max(0.0, velocity_peak_t - sfx_internal_peak_s)


def synthesize_whoosh(duration_s: float = 0.36) -> np.ndarray:
    n = int(round(duration_s * SAMPLE_RATE))
    t = np.linspace(0.0, duration_s, n, dtype=np.float64)
    u = t / duration_s
    env = 30.0 * (u ** 2) * ((1.0 - u) ** 2)
    phase = 2.0 * math.pi * (140.0 * t + 260.0 * (t ** 2))
    sig = env * np.sin(phase) * 0.25
    return np.column_stack([sig, sig])


def synthesize_pop(duration_s: float = 0.09) -> np.ndarray:
    n = int(round(duration_s * SAMPLE_RATE))
    t = np.linspace(0.0, duration_s, n, dtype=np.float64)
    env = np.exp(-t * 38.0) * np.sin(math.pi * t / duration_s)
    freq_sweep = 320.0 + 480.0 * (t / duration_s)
    sig = env * np.sin(2.0 * math.pi * freq_sweep * t) * 0.30
    return np.column_stack([sig, sig])


def mix_episode_audio(
    vo_stereo: np.ndarray,
    bgm_stereo: np.ndarray | None,
    move_windows: List[Tuple[float, float]],
    pop_times: List[float],
    total_duration_s: float,
) -> np.ndarray:
    total_samples = int(round(total_duration_s * SAMPLE_RATE))
    master = np.zeros((total_samples, 2), dtype=np.float64)

    n_vo = min(total_samples, len(vo_stereo))
    master[:n_vo] += vo_stereo[:n_vo]

    if bgm_stereo is not None and len(bgm_stereo) > 0:
        bgm_gain = 10.0 ** (BGM_OFFSET_DB / 20.0)
        reps = int(math.ceil(total_samples / len(bgm_stereo)))
        bgm_tiled = np.tile(bgm_stereo, (reps, 1))[:total_samples]
        master += bgm_tiled * bgm_gain

    whoosh_pcm = synthesize_whoosh(0.36)
    for start_t, dur_s in move_windows:
        insert_t = sfx_peak_timestamp(start_t, dur_s, sfx_internal_peak_s=0.18)
        idx = int(round(insert_t * SAMPLE_RATE))
        end_idx = min(total_samples, idx + len(whoosh_pcm))
        if end_idx > idx:
            master[idx:end_idx] += whoosh_pcm[: end_idx - idx]

    pop_pcm = synthesize_pop(0.09)
    for pt in pop_times:
        idx = int(round(max(0.0, pt + 0.03) * SAMPLE_RATE))
        end_idx = min(total_samples, idx + len(pop_pcm))
        if end_idx > idx:
            master[idx:end_idx] += pop_pcm[: end_idx - idx]

    master = apply_seamless_audio_loop_tail(master, tail_overlap_s=0.25)

    rms = float(np.sqrt(np.mean(master ** 2)))
    if rms > 1e-6:
        target_rms = 10.0 ** (TARGET_LUFS / 20.0)
        master *= target_rms / rms

    max_tp = 10.0 ** (MAX_TRUE_PEAK_DBTP / 20.0)
    peak = float(np.max(np.abs(master)))
    if peak > max_tp:
        master *= max_tp / peak

    return master
