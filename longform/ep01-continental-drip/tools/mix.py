#!/usr/bin/env python3
"""mix.py mix.json out.wav
mix.json: {
  "duration": 900.0,
  "vo": "vo.wav", "vo_gain_db": 0,
  "music": [{"file": "cue1.mp3", "start": 0, "end": 120, "gain_db": -16, "fade_in": 1.5, "fade_out": 3, "offset": 0, "loop": false}],
  "sfx": [{"file": "whoosh.mp3", "t": 12.3, "gain_db": -8}],
  "duck": {"db": -8, "attack": 0.06, "release": 0.45},
  "target_lufs": -14, "true_peak": -1.5
}
Mixes at 48 kHz stereo: music ducked under the VO envelope, SFX placed at times, loudness-normalised (BS.1770 via pyloudnorm)
and true-peak limited (4x oversampled look-ahead limiter)."""
import json, subprocess, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly
SR = 48000

def load(path, ch=2):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()

def db(x): return 10 ** (x / 20)

def main():
    spec = json.load(open(sys.argv[1])); outp = sys.argv[2]
    N = int(spec['duration'] * SR)
    bus_m = np.zeros((N, 2), np.float32); bus_s = np.zeros((N, 2), np.float32); vo = np.zeros((N, 2), np.float32)
    if spec.get('vo'):
        v = load(spec['vo'], 1)[:, 0] * db(spec.get('vo_gain_db', 0))
        n = min(N, len(v)); vo[:n, 0] = v[:n]; vo[:n, 1] = v[:n]
    for m in spec.get('music', []):
        y = load(m['file']) * db(m.get('gain_db', -16))
        s0, s1 = int(m['start'] * SR), int(min(spec['duration'], m['end']) * SR)
        L = s1 - s0
        off = int(m.get('offset', 0) * SR)
        y = y[off:]
        if m.get('loop') and len(y) < L: y = np.tile(y, (L // len(y) + 1, 1))
        y = y[:L].copy()
        fi, fo = int(m.get('fade_in', 1.0) * SR), int(m.get('fade_out', 2.0) * SR)
        if fi: y[:fi] *= np.linspace(0, 1, min(fi, len(y)))[:, None]
        if fo: y[-fo:] *= np.linspace(1, 0, min(fo, len(y)))[:, None]
        bus_m[s0:s0 + len(y)] += y
    for e in spec.get('sfx', []):
        y = load(e['file']) * db(e.get('gain_db', -8))
        s0 = int(e['t'] * SR)
        if s0 >= N: continue
        y = y[:N - s0]; bus_s[s0:s0 + len(y)] += y
    # ducking: VO envelope (RMS over 20 ms) -> gain reduction on music
    d = spec.get('duck', {'db': -8, 'attack': 0.06, 'release': 0.45})
    hop = 480
    rms = np.sqrt(np.convolve(vo[:, 0] ** 2, np.ones(hop) / hop, 'same'))[::hop]
    act = (rms > db(-42)).astype(np.float32)
    # smooth activity at control rate (100 Hz)
    ca, cr = np.exp(-1 / (d['attack'] * 100)), np.exp(-1 / (d['release'] * 100))
    g = np.empty_like(act); e = 0.0
    for i, v in enumerate(act): c = ca if v > e else cr; e = c * e + (1 - c) * v; g[i] = e
    gain = db(d['db'] * g)
    gain = np.interp(np.arange(N), np.arange(len(gain)) * hop, gain).astype(np.float32)
    mix = vo + bus_m * gain[:, None] + bus_s
    # loudness normalisation
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(mix.astype(np.float64))
    mix *= db(spec.get('target_lufs', -14) - lufs)
    # true-peak limiter: 4x oversampled peak envelope, look-ahead 5 ms, release 120 ms
    tp = db(spec.get('true_peak', -1.5))
    up = resample_poly(mix, 4, 1, axis=0)
    pk = np.abs(up).max(axis=1).reshape(-1, 4).max(axis=1)[:N]
    need = np.minimum(1.0, tp / np.maximum(pk, 1e-9))
    # control-rate (1 ms blocks) gain computer with 5 ms look-ahead and 120 ms release
    B = 48
    nb = (N + B - 1) // B
    needb = np.pad(need, (0, nb * B - N), constant_values=1.0).reshape(nb, B).min(axis=1)
    from scipy.ndimage import minimum_filter1d
    needb = minimum_filter1d(needb, size=11)
    rel = np.exp(-1 / (0.12 * 1000)); grb = np.empty_like(needb); e = 1.0
    for i in range(nb):
        v = needb[i]; e = v if v < e else rel * e + (1 - rel) * v; grb[i] = e
    gr = np.interp(np.arange(N), np.arange(nb) * B + B / 2, grb).astype(np.float32)
    gr = np.minimum(gr, need)  # never exceed the instantaneous requirement
    mix *= gr[:, None]
    lufs2 = meter.integrated_loudness(mix.astype(np.float64))
    sf.write(outp, mix, SR, subtype='PCM_24')
    print(f'mixed {spec["duration"]:.1f} s -> {outp}; LUFS {lufs:.1f} -> {lufs2:.1f}; limiter max GR {20*np.log10(gr.min()):.1f} dB')

if __name__ == '__main__':
    main()
