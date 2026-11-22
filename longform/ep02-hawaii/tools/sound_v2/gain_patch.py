#!/usr/bin/env python3
"""gain_patch.py CONFIG_JSON: in-file level ride on a music cue (a gain curve in dB over file time, linear in dB between points,
0 dB outside the first and last point). Used where a new take's soft passage is pushed below the music floor by the stacked
cue normalisation, cue gain and voice duck, so that the mix spec's dips list stays identical to v1. Output is a 32-bit float WAV
of the same length; samples before the first point and after the last point are identical to the ffmpeg decode mix.py uses.
Prints the loudness change and the norm_lufs that keeps the cue gain (so the rest of the cue, e.g. a hit, does not move).
CONFIG: {"cues": [{"in": file, "out": wav, "gain_pts": [[t, dB], ...]}], "report": path}"""
import sys, json, subprocess
import numpy as np, soundfile as sf, pyloudnorm as pyln
SR = 48000


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def env(y, a, b, hop=0.25):
    m = y.mean(1); w = int(SR * hop); seg = m[int(a * SR):int(b * SR)]; n = len(seg) // w
    return 10 * np.log10((seg[:n * w].reshape(n, w) ** 2).mean(1) + 1e-12)


cfg = json.load(open(sys.argv[1])); rep = []
for c in cfg['cues']:
    y = load(c['in']); pts = np.array(c['gain_pts'], float)
    t = np.arange(len(y)) / SR
    g = np.ones(len(y)); inside = (t >= pts[0, 0]) & (t <= pts[-1, 0])
    g[inside] = 10 ** (np.interp(t[inside], pts[:, 0], pts[:, 1]) / 20)
    out = y * g[:, None]
    lu0, lu1 = pyln.Meter(SR).integrated_loudness(y), pyln.Meter(SR).integrated_loudness(out)
    sf.write(c['out'], out.astype(np.float32), SR, subtype='FLOAT')
    back = sf.read(c['out'], always_2d=True)[0]
    same = bool(np.array_equal(back[~inside].astype(np.float32), y[~inside].astype(np.float32)))
    a, b = pts[0, 0] - 1, pts[-1, 0] + 0.5
    r = {'in': c['in'], 'out': c['out'], 'gain_pts': c['gain_pts'], 'lufs_in': round(lu0, 3), 'lufs_out': round(lu1, 3),
         'norm_lufs_for_same_gain': round(-16.0 + (lu1 - lu0), 3), 'peak_out': round(float(np.abs(out).max()), 4),
         'outside_patch_identical': same, 'len_s': len(y) / SR, 'env_from': a,
         'env_before': [round(v, 1) for v in env(y, a, b)], 'env_after': [round(v, 1) for v in env(out, a, b)]}
    print(f"{c['in'].rsplit('/', 1)[-1]}: LUFS {lu0:.3f} -> {lu1:.3f} (norm_lufs {r['norm_lufs_for_same_gain']}), outside identical {same}")
    print('   before', ' '.join(f'{a + k / 4:.2f}:{v:.0f}' for k, v in enumerate(r['env_before'])))
    print('   after ', ' '.join(f'{a + k / 4:.2f}:{v:.0f}' for k, v in enumerate(r['env_after'])))
    rep.append(r)
json.dump(rep, open(cfg['report'], 'w'), indent=1)
