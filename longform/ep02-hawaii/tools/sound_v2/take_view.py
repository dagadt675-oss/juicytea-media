#!/usr/bin/env python3
"""take_view.py FILE [FILE...] [--to S]: compact view of a music take: 0.5 s short-term loudness (LUFS-ish, 0.4 s window), onset
(first 10 ms frame above -40 dBFS, and the strongest attack in the first 2 s with its rise in dB over 50 ms), spectral flatness
and centroid per 2 s, and the 0.5 s level of the first downbeat against the median."""
import sys, subprocess
import numpy as np
from scipy.signal import stft
SR = 48000
args = [a for a in sys.argv[1:] if not a.startswith('--')]
to = float(sys.argv[sys.argv.index('--to') + 1]) if '--to' in sys.argv else None
if to is not None: args = [a for a in args if a != str(sys.argv[sys.argv.index('--to') + 1])]


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


for p in args:
    y = load(p)
    if to: y = y[:int(to * SR)]
    w = SR // 100; n = len(y) // w
    e10 = 10 * np.log10((y[:n * w].reshape(n, w) ** 2).mean(1) + 1e-12)
    first = np.argmax(e10 > -40) / 100
    rise = e10[5:200] - e10[:195]
    k = int(np.argmax(rise)); att_t = (k + 5) / 100
    h = SR // 2; m = len(y) // h
    e05 = 10 * np.log10((y[:m * h].reshape(m, h) ** 2).mean(1) + 1e-12)
    med = np.median(e05)
    f, t, Z = stft(y, SR, nperseg=2048, noverlap=1024); P = np.abs(Z) ** 2 + 1e-14
    fl = np.exp(np.mean(np.log(P), 0)) / np.mean(P, 0); cen = (f[:, None] * P).sum(0) / P.sum(0)
    print(f"{p.rsplit('/', 1)[-1]}  len {len(y)/SR:.2f}  first>-40dBFS {first:.2f} s  strongest early attack {att_t:.2f} s (+{rise[k]:.1f} dB/50ms)"
          f"  first 0.5 s vs median {e05[0] - med:+.1f} dB, first 1 s max vs median {e05[:2].max() - med:+.1f} dB")
    print('   0.5s dB  ', ' '.join(f'{i/2:.1f}:{v:.0f}' for i, v in enumerate(e05)))
    seg = 2.0
    rows = []
    for s0 in np.arange(0, len(y) / SR - 0.1, seg):
        sel = (t >= s0) & (t < s0 + seg)
        rows.append(f'{s0:.0f}:{np.median(fl[sel]):.3f}/{np.median(cen[sel]):.0f}')
    print('   flat/cen ', ' '.join(rows))
