#!/usr/bin/env python3
"""band_diff.py STEMS_A STEMS_B TIMING DUR: the mix_qc band_1_4k windows (100 ms, inside words, voice 1-4 kHz minus music+sfx+amb)
for two stem sets, listing the windows under 15 dB in B that were >= 15 dB in A, and the reverse, with the word at each window."""
import sys, json
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
SR = 48000
A, B, tp, dur = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
timing = json.load(open(tp)); words = timing['words']
m100 = np.zeros(int(dur * 100) + 1, bool)
for w in words: m100[int(w['start'] * 100):int(w['end'] * 100)] = True
sos = butter(4, [1000, 4000], 'bandpass', fs=SR, output='sos')

def margins(d):
    S = {k: sf.read(f'{d}/{k}.flac', dtype='float32')[0] for k in ('vo', 'music', 'sfx', 'amb')}
    n = min(len(x) for x in S.values())
    vb = sosfiltfilt(sos, S['vo'][:n].mean(1).astype(np.float64))
    bb = sosfiltfilt(sos, (S['music'][:n] + S['sfx'][:n] + S['amb'][:n]).mean(1).astype(np.float64))
    w = SR // 10
    Lv = 10 * np.log10(np.add.reduceat(vb ** 2, np.arange(0, n - w, w)) / w + 1e-15)
    Lb = 10 * np.log10(np.add.reduceat(bb ** 2, np.arange(0, n - w, w)) / w + 1e-15)
    k = min(len(Lv), len(Lb)); tw = np.arange(k) * 0.1
    inw = np.array([m100[int(t * 100):int(t * 100) + 10].mean() > 0.8 for t in tw])
    spb = inw & (Lv[:k] > np.median(Lv[:k][inw]) - 10)
    return tw, spb, Lv[:k] - Lb[:k]

ta, sa, ma = margins(A); tb, sb, mb = margins(B)
k = min(len(ta), len(tb)); both = sa[:k] & sb[:k]
word = lambda t: next(((w.get('word') or w.get('text') or w.get('w')) for w in words if w['start'] <= t + 0.05 <= w['end']), '?')
newlow = [(round(float(ta[i]), 1), word(ta[i]), round(float(ma[i]), 1), round(float(mb[i]), 1)) for i in range(k) if both[i] and mb[i] < 15 <= ma[i]]
gone = [(round(float(ta[i]), 1), word(ta[i]), round(float(ma[i]), 1), round(float(mb[i]), 1)) for i in range(k) if both[i] and ma[i] < 15 <= mb[i]]
print('windows A', int(sa.sum()), 'B', int(sb.sum()), 'below15 A', int((ma[sa] < 15).sum()), 'B', int((mb[sb] < 15).sum()))
print('NEW under 15 dB in B (t, word, A, B):', len(newlow)); [print('  ', x) for x in newlow]
print('no longer under 15 dB in B:', len(gone)); [print('  ', x) for x in gone]
tall = [(round(float(ta[i]), 1), word(ta[i]), round(float(ma[i]), 1), round(float(mb[i]), 1), bool(sb[i])) for i in range(k) if 678.9 <= ta[i] <= 680.2]
print('windows 678.9-680.2 (t, word, A, B, counted):'); [print('  ', x) for x in tall]
