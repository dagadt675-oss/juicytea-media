#!/usr/bin/env python3
"""fill_rest.py CONFIG_JSON: fill unplanned music rests inside a cue file, keeping the file's timeline (same length, every sample
outside the patch identical to what mix.py decodes from the original: ffmpeg to 48 kHz stereo float).

Each patch: region [t0, t1] (file s); the fill is the cue's own audio from `beats` beats earlier (beat-aligned loop extension,
the local beat period measured from the onset-strength autocorrelation around the region), shaped by a gain curve in dB
(`gain_pts`: [[t, dB], ...], linear in dB between points), faded in with an equal-power ramp `xin` s from t0 and out with an
equal-power ramp `xout` s ending at t1, and added to the original (whose decay keeps sounding underneath).
Writes OUT as 32-bit float WAV (no clipping risk), prints 0.25 s envelopes before/after and the loudness change.

CONFIG: {"cues": [{"in": file, "out": wav, "patches": [{"t0":..,"t1":..,"beats":8,"xin":0.4,"xout":0.15,"gain_pts":[[t,db],..]}]}]}
"""
import sys, json, subprocess
import numpy as np, soundfile as sf, pyloudnorm as pyln, librosa
SR = 48000


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def env(y, a, b, hop=0.25):
    m = y.mean(1); w = int(SR * hop); i0, i1 = int(a * SR), int(b * SR)
    seg = m[i0:i1]; n = len(seg) // w
    return 10 * np.log10((seg[:n * w].reshape(n, w) ** 2).mean(1) + 1e-12)


def local_period(y, t0, beats):
    """Beat period near t0: median beat interval of librosa's beat tracker over the whole cue within the 14 s before t0,
    refined within +-2 % by the onset-strength autocorrelation at that lag."""
    m = librosa.resample(y.mean(1), orig_sr=SR, target_sr=22050)
    hop = 128; fr = 22050 / hop
    oe_all = librosa.onset.onset_strength(y=m, sr=22050, hop_length=hop)
    tempo, bt = librosa.beat.beat_track(y=m, sr=22050, hop_length=512, units='time')
    bt = bt[(bt > t0 - 14) & (bt < t0)]
    p0 = float(np.median(np.diff(bt)))
    oe = oe_all[int(max(0, t0 - 14) * fr):int(t0 * fr)]; oe = oe - oe.mean()
    ac = np.correlate(oe, oe, 'full')[len(oe) - 1:]
    L = beats * p0 * fr; lo, hi = int(L * 0.98), int(L * 1.02) + 1
    k = lo + int(np.argmax(ac[lo:hi]))
    return k / fr / beats, 60.0 / p0


def eqp(n, up=True):
    x = np.linspace(0, 1, n); r = np.sin(x * np.pi / 2)
    return r if up else r[::-1]


def main():
    cfg = json.load(open(sys.argv[1])); report = []
    for c in cfg['cues']:
        y = load(c['in']); out = y.copy(); lu0 = pyln.Meter(SR).integrated_loudness(y)
        rec = {'in': c['in'], 'out': c['out'], 'patches': []}
        for p in c['patches']:
            t0, t1 = p['t0'], p['t1']
            per, tempo = local_period(y, t0, p['beats'])
            shift = per * p['beats']; s_shift = int(round(shift * SR))
            i0, i1 = int(t0 * SR), int(t1 * SR); n = i1 - i0
            fill = y[i0 - s_shift:i1 - s_shift].copy()
            tt = t0 + np.arange(n) / SR
            pts = np.array(p['gain_pts'], float)
            g = 10 ** (np.interp(tt, pts[:, 0], pts[:, 1]) / 20)
            w = np.ones(n)
            nin, nout = int(p['xin'] * SR), int(p['xout'] * SR)
            w[:nin] = eqp(nin, True); w[n - nout:] *= eqp(nout, False)
            out[i0:i1] += fill * (g * w)[:, None]
            a, b = t0 - 2, t1 + 1
            before, after = env(y, a, b), env(out, a, b)
            r = {'t0': t0, 't1': t1, 'tempo_bpm': round(tempo, 2), 'beat_s': round(per, 4), 'shift_s': round(shift, 3),
                 'source': [round(t0 - shift, 3), round(t1 - shift, 3)],
                 'env_from': a, 'env_before': [round(v, 1) for v in before], 'env_after': [round(v, 1) for v in after],
                 'min_in_region_before': round(float(env(y, t0, t1).min()), 1), 'min_in_region_after': round(float(env(out, t0, t1).min()), 1)}
            rec['patches'].append(r)
            print(f"{c['in'].rsplit('/', 1)[-1]} patch {t0}-{t1}: tempo {tempo:.1f} beat {per:.4f} shift {shift:.3f} s "
                  f"(source {t0 - shift:.2f}-{t1 - shift:.2f}); region min {r['min_in_region_before']} -> {r['min_in_region_after']} dBFS")
            print('   before', ' '.join(f'{a + k / 4:.2f}:{v:.0f}' for k, v in enumerate(before)))
            print('   after ', ' '.join(f'{a + k / 4:.2f}:{v:.0f}' for k, v in enumerate(after)))
        lu1 = pyln.Meter(SR).integrated_loudness(out)
        pk = float(np.abs(out).max())
        sf.write(c['out'], out.astype(np.float32), SR, subtype='FLOAT')
        rec.update({'lufs_in': round(lu0, 3), 'lufs_out': round(lu1, 3), 'norm_lufs_for_same_gain': round(-16.0 + (lu1 - lu0), 3),
                    'peak_out': round(pk, 4), 'len_in_s': len(y) / SR, 'len_out_s': len(out) / SR})
        print(f"   LUFS {lu0:.2f} -> {lu1:.2f} (norm_lufs {-16 + lu1 - lu0:.3f} keeps the cue gain), peak {pk:.3f}, len {len(y)/SR:.3f} -> {len(out)/SR:.3f}")
        report.append(rec)
    json.dump(report, open(cfg.get('report', sys.argv[1].replace('.json', '_report.json')), 'w'), indent=1)


if __name__ == '__main__':
    main()
