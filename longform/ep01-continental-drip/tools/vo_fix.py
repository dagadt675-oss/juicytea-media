#!/usr/bin/env python3
"""vo_fix.py IN_WAV OUT_WAV
Repairs the narration stem in place (nothing moves in time):
  - silences the stray take fragments (the first ~0.1 s of the next word left at the end of a take), each found on a
    20 ms loudness envelope as a burst after the word had already decayed, right before the take's hard end
  - replaces the mispronounced 'Wegener' in 'So Wegener was right.' (9:50.6) with the clean 'Wegener' from 8:58.07,
    same length, 15 ms equal-power crossfades at both joins"""
import sys
import numpy as np, soundfile as sf

SILENCE = [(28.46, 28.60), (257.20, 257.42), (550.08, 550.30), (639.48, 639.63), (723.42, 723.54), (844.28, 844.40), (919.82, 919.96)]
SRC, DST, LEN = 538.065, 590.61, 0.50
FADE_S, XF = 0.010, 0.015

def main():
    x, sr = sf.read(sys.argv[1], dtype='float32')
    mono = x.ndim == 1
    y = x.copy() if not mono else x[:, None].copy()
    f = int(FADE_S * sr)
    for a, b in SILENCE:
        i, j = int(a * sr), int(b * sr)
        g = np.zeros(j - i, np.float32); g[:f] = np.linspace(1, 0, f); g[-f:] = np.linspace(0, 1, f)
        y[i:j] *= g[:, None]
    n, s0, d0, xf = int(LEN * sr), int(SRC * sr), int(DST * sr), int(XF * sr)
    src = y[s0:s0 + n].copy(); dst = y[d0:d0 + n].copy()
    w = np.ones(n, np.float32)
    ramp = np.sin(np.linspace(0, np.pi / 2, xf)).astype(np.float32)
    w[:xf] = ramp; w[-xf:] = ramp[::-1]
    v = np.sqrt(1 - w ** 2)
    y[d0:d0 + n] = src * w[:, None] + dst * v[:, None]
    sf.write(sys.argv[2], y[:, 0] if mono else y, sr, subtype='PCM_24')
    print('silenced', len(SILENCE), 'fragments; Wegener %.3f-%.3f -> %.3f-%.3f' % (SRC, SRC + LEN, DST, DST + LEN))

if __name__ == '__main__':
    main()
