#!/usr/bin/env python3
"""bed_floor.py FILE [FILE...]: noise-floor profile of ambience beds (octave bands: p10/p50/p90 of 46 ms frames in dBFS,
spread p90-p10, spectral flatness of the quietest 20% frames above 4 kHz, temporal std of the 8-16 kHz band)."""
import sys, subprocess, numpy as np
from scipy.signal import stft
SR = 48000
def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
EDGES = [(31, 125), (125, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 12000), (12000, 16000), (16000, 20000)]
def profile(y):
    f, t, Z = stft(y, SR, nperseg=2048, noverlap=2048 - 512)
    P = np.abs(Z) ** 2
    out = {}
    for lo, hi in EDGES:
        b = (f >= lo) & (f < hi); e = 10 * np.log10(P[b].sum(0) + 1e-14)
        out[f'{lo}-{hi}'] = (np.percentile(e, 10), np.percentile(e, 50), np.percentile(e, 90))
    hf = (f >= 4000) & (f < 16000)
    tot = P.sum(0); q = tot <= np.percentile(tot, 20)
    Pq = P[hf][:, q] + 1e-14
    flat = np.exp(np.mean(np.log(Pq), 0)) / np.mean(Pq, 0)
    e816 = 10 * np.log10(P[(f >= 8000) & (f < 16000)].sum(0) + 1e-14)
    return out, float(np.median(flat)), float(np.std(e816))
for p in sys.argv[1:]:
    y = load(p); out, flat, sd = profile(y)
    print(p.rsplit('/', 1)[-1], f'len {len(y)/SR:.1f}s  HF flatness(quiet20%) {flat:.3f}  8-16k std {sd:.1f} dB')
    for k, (a, b, c) in out.items(): print(f'   {k:>11s}  p10 {a:6.1f}  p50 {b:6.1f}  p90 {c:6.1f}  spread {c-a:5.1f}')
