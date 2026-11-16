#!/usr/bin/env python3
"""vo_proc.py vo.wav vo_proc.wav [--lufs -17] [--peak -3.5] [--hpf 70] [--ratio 2.5] [--deess 6]
Prepares a raw narration stem for mix.py (PLAYBOOK_craft section 11; ep02 spot_notes section 8): a 70 Hz high-pass,
a split-band de-esser (5-10 kHz, at most --deess dB), a gentle RMS compressor (soft knee 6 dB, attack 5 ms, release 90 ms,
threshold 3 dB above the median speech level), loudness to --lufs (BS.1770) and a 4x oversampled true-peak limiter at --peak.
Nothing moves in time (all filters are causal or zero-latency), so timing.json still holds. Mono 48 kHz 24-bit out.
Prints the before/after loudness, peak and peak-to-loudness ratio."""
import argparse, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt, sosfiltfilt
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from mix import load, db, SR, true_peak_env, limiter_gain

def env_db(x, win):
    """Centred moving mean-square in dB (cumulative-sum form of np.convolve(x**2, ones(win)/win, 'same'))."""
    c = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)])
    h = win // 2; i = np.arange(len(x)); lo = np.clip(i - h, 0, len(x)); hi = np.clip(i - h + win, 0, len(x))
    return 10 * np.log10((c[hi] - c[lo]) / win + 1e-12)

def smooth_gain(gdb, attack, release):
    """One-pole attack/release smoothing of a gain-reduction curve in dB (more negative = more reduction), at 1 kHz."""
    a, r = np.exp(-1 / (attack * 1000)), np.exp(-1 / (release * 1000)); out = np.empty_like(gdb); e = 0.0
    for i, v in enumerate(gdb):
        c = a if v < e else r; e = c * e + (1 - c) * v; out[i] = e
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--lufs', type=float, default=-17.0); ap.add_argument('--peak', type=float, default=-3.5)
    ap.add_argument('--hpf', type=float, default=70.0); ap.add_argument('--ratio', type=float, default=2.5)
    ap.add_argument('--deess', type=float, default=6.0)
    a = ap.parse_args()
    x = load(a.inp, 1)[:, 0].astype(np.float64); N = len(x)
    meter = pyln.Meter(SR)
    l0 = meter.integrated_loudness(x); p0 = 20 * np.log10(np.abs(x).max() + 1e-12)
    # 1. high-pass
    x = sosfilt(butter(2, a.hpf, 'hp', fs=SR, output='sos'), x)
    # 2. de-esser: reduce only the 5-10 kHz band when it dominates the full band (sibilants)
    sos_b = butter(4, [5000, 10000], 'bandpass', fs=SR, output='sos')
    s = sosfiltfilt(sos_b, x)  # zero phase, so x - s + s*g recombines cleanly
    B = 48; n = N // B
    ef = env_db(x, 240)[:n * B].reshape(n, B).max(1); es = env_db(s, 240)[:n * B].reshape(n, B).max(1)
    over = (es - ef) + 9.0  # sibilant when the band is within 9 dB of the full band
    gdb = -np.clip(over, 0, a.deess) * (es > -45)
    gdb = smooth_gain(gdb, 0.002, 0.06)
    g = np.interp(np.arange(N), np.arange(n) * B + B / 2, db(gdb))
    x = x - s + s * g
    deess_max = float(-gdb.min())
    # 3. compressor on a 10 ms RMS detector, soft knee
    lv = env_db(x, 480)[:n * B].reshape(n, B).mean(1)
    speech = lv > -45
    thr = float(np.median(lv[speech])) + 3.0; knee = 6.0; R = a.ratio
    o = lv - thr
    red = np.where(o <= -knee / 2, 0.0, np.where(o >= knee / 2, o * (1 - 1 / R), (1 - 1 / R) * (o + knee / 2) ** 2 / (2 * knee)))
    cg = smooth_gain(-red, 0.005, 0.09)
    x = x * np.interp(np.arange(N), np.arange(n) * B + B / 2, db(cg))
    # 4. loudness, then 5. true-peak limiter
    x *= db(a.lufs - meter.integrated_loudness(x))
    pk = true_peak_env(x[:, None])
    gr = limiter_gain(pk, db(a.peak), {'lookahead_ms': 3, 'release_ms': 80})
    x = x * gr
    x *= db(a.lufs - meter.integrated_loudness(x))  # tiny makeup after limiting (well under 0.2 dB)
    x = x * np.minimum(1.0, db(a.peak + 0.3) / max(true_peak_env(x[:, None]).max(), 1e-9))
    sf.write(a.out, x.astype(np.float32), SR, subtype='PCM_24')
    l1 = meter.integrated_loudness(x); p1 = 20 * np.log10(true_peak_env(x[:, None]).max())
    print(f'in  {l0:.1f} LUFS, sample peak {p0:.1f} dBFS, PLR {p0 - l0:.1f} dB')
    print(f'out {l1:.1f} LUFS, true peak {p1:.1f} dBTP, PLR {p1 - l1:.1f} dB; de-ess max {deess_max:.1f} dB; '
          f'compressor threshold {thr:.1f} dBFS ratio {R}, max reduction {float(-cg.min()):.1f} dB, median {float(np.median(-cg[speech])):.1f} dB; '
          f'limiter max {20 * np.log10(gr.min()):.1f} dB')

if __name__ == '__main__':
    main()
