#!/usr/bin/env python3
"""gate.py IN OUT [--flo 3000] [--thr0 3] [--thr1 9] [--floor -12] [--pct 20] [--json REPORT]
Spectral gate for a stationary hiss floor in an ambience bed (no level renormalising: content keeps its level, only the floor drops).

Per channel STFT (2048 / hop 512 at 48 kHz). Noise level per bin = the `pct` percentile of its power over time, median-smoothed over
9 bins. Gain per bin and frame: `floor` dB where the bin is less than thr0 dB over the noise level, 0 dB above thr1, linear in dB
between; smoothed over 5 frames (53 ms) and 5 bins against musical noise; applied only above `flo` (cosine ramp from flo/2 to flo),
so the low and mid body of the bed is untouched. Output has the input's length, channels and sample rate (PCM 24-bit).
Report: octave-band p10/p50/p90 before and after, HF flatness of the quietest 20 % frames, frame-to-frame flutter of the 4-16 kHz
band in quiet frames (musical-noise proxy), and the criteria: 8-16 kHz p10 drop >= 6 dB, 125-4000 Hz p90 within 2 dB,
4-16 kHz p90 drop <= 3 dB (splashes and drops survive)."""
import argparse, json
import numpy as np, soundfile as sf
from scipy.signal import stft, istft
from scipy.ndimage import median_filter, uniform_filter

ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--flo', type=float, default=3000); ap.add_argument('--thr0', type=float, default=3); ap.add_argument('--thr1', type=float, default=9)
ap.add_argument('--floor', type=float, default=-12); ap.add_argument('--pct', type=float, default=20); ap.add_argument('--json')
ap.add_argument('--dry', action='store_true', help='measure only, do not write OUT')
a = ap.parse_args()

y, sr = sf.read(a.inp, always_2d=True); y = y.astype(np.float64)
N, H = 2048, 512


def gate_ch(x):
    f, t, Z = stft(x, sr, nperseg=N, noverlap=N - H, boundary='even', padded=True)
    P = 10 * np.log10(np.abs(Z) ** 2 + 1e-20)
    noise = median_filter(np.percentile(P, a.pct, axis=1), size=9, mode='nearest')
    snr = P - noise[:, None]
    gdb = np.clip((snr - a.thr0) / (a.thr1 - a.thr0), 0, 1) * (0 - a.floor) + a.floor
    g = 10 ** (gdb / 20)
    g = uniform_filter(g, size=(5, 5), mode='nearest')
    w = np.clip((f - a.flo / 2) / (a.flo / 2), 0, 1); w = 0.5 - 0.5 * np.cos(np.pi * w)
    g = 1 - w[:, None] * (1 - g)
    _, xr = istft(Z * g, sr, nperseg=N, noverlap=N - H, boundary=True)
    return xr[:len(x)] if len(xr) >= len(x) else np.pad(xr, (0, len(x) - len(xr)))


EDGES = [(31, 125), (125, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 12000), (12000, 16000)]


def prof(z):
    m = z.mean(1)
    f, t, Z = stft(m, sr, nperseg=N, noverlap=N - H)
    P = np.abs(Z) ** 2
    bands = {}
    for lo, hi in EDGES:
        e = 10 * np.log10(P[(f >= lo) & (f < hi)].sum(0) + 1e-14)
        bands[f'{lo}-{hi}'] = [round(float(np.percentile(e, q)), 2) for q in (10, 50, 90)]
    tot = P.sum(0); q = tot <= np.percentile(tot, 20)
    hf = (f >= 4000) & (f < 16000)
    Pq = P[hf][:, q] + 1e-14
    flat = float(np.median(np.exp(np.mean(np.log(Pq), 0)) / np.mean(Pq, 0)))
    e416 = 10 * np.log10(P[hf].sum(0) + 1e-14)
    flutter = float(np.median(np.abs(np.diff(e416))[q[1:]]))
    agg = lambda lo, hi, k: 10 * np.log10(P[(f >= lo) & (f < hi)].sum(0) + 1e-14)
    return {'bands': bands, 'hf_flatness_quiet': round(flat, 3), 'flutter_4_16k_quiet_db': round(flutter, 2),
            'p10_8_16k': round(float(np.percentile(agg(8000, 16000, 0), 10)), 2),
            'p90_125_4k': round(float(np.percentile(agg(125, 4000, 0), 90)), 2),
            'p90_4_16k': round(float(np.percentile(agg(4000, 16000, 0), 90)), 2),
            'p98_4_16k': round(float(np.percentile(agg(4000, 16000, 0), 98)), 2),
            'p50_125_4k': round(float(np.percentile(agg(125, 4000, 0), 50)), 2)}


out = np.stack([gate_ch(y[:, c]) for c in range(y.shape[1])], 1)
b, g = prof(y), prof(out)
crit = {'hiss_floor_drop_8_16k_db': round(b['p10_8_16k'] - g['p10_8_16k'], 2),
        'content_p90_125_4k_change_db': round(g['p90_125_4k'] - b['p90_125_4k'], 2),
        'hf_content_p90_4_16k_drop_db': round(b['p90_4_16k'] - g['p90_4_16k'], 2),
        'hf_peaks_p98_4_16k_drop_db': round(b['p98_4_16k'] - g['p98_4_16k'], 2),
        'flutter_rise_db': round(g['flutter_4_16k_quiet_db'] - b['flutter_4_16k_quiet_db'], 2)}
crit['pass'] = bool(crit['hiss_floor_drop_8_16k_db'] >= 6 and abs(crit['content_p90_125_4k_change_db']) <= 2
                    and crit['hf_content_p90_4_16k_drop_db'] <= 3 and g['flutter_4_16k_quiet_db'] <= b['flutter_4_16k_quiet_db'] + 1.0)
rep = {'in': a.inp, 'out': None if a.dry else a.out, 'params': {k: getattr(a, k) for k in ('flo', 'thr0', 'thr1', 'floor', 'pct')},
       'before': b, 'after': g, 'criteria': crit, 'peak_in': round(float(np.abs(y).max()), 4), 'peak_out': round(float(np.abs(out).max()), 4)}
print(a.inp.rsplit('/', 1)[-1], json.dumps(a.__dict__ | {}, default=str)[:0], rep['params'])
for k in b['bands']: print(f'   {k:>11s} before {b["bands"][k]}  after {g["bands"][k]}')
print('   flatness', b['hf_flatness_quiet'], '->', g['hf_flatness_quiet'], ' flutter', b['flutter_4_16k_quiet_db'], '->', g['flutter_4_16k_quiet_db'])
print('   criteria', crit)
if not a.dry:
    sf.write(a.out, out.astype(np.float32), sr, subtype='PCM_24')
if a.json: json.dump(rep, open(a.json, 'w'), indent=1)
