#!/usr/bin/env python3
"""mix.py mix.json out.wav [--stems DIR] [--report report.json]
mix.json (ep01 keys, unchanged meaning):
{
  "duration": 900.0,
  "vo": "vo.wav", "vo_gain_db": 0,
  "music": [{"file": "cue1.mp3", "start": 0, "end": 120, "gain_db": -16, "fade_in": 1.5, "fade_out": 3, "offset": 0, "loop": false}],
  "sfx": [{"file": "whoosh.mp3", "t": 12.3, "gain_db": -8}],
  "duck": {"db": -8, "attack": 0.06, "release": 0.45},
  "dips": [[272.95, 273.95, -12]],
  "target_lufs": -14, "true_peak": -1.5
}
Mixes at 48 kHz stereo: music ducked under the VO envelope, SFX placed at times, loudness-normalised (BS.1770 via pyloudnorm)
and true-peak limited (4x oversampled look-ahead limiter).

Optional keys added for ep02 (2026-11-08); a spec without them mixes exactly as before:
  music cue:  "curve": "eqp" (equal-power fades, for overlapping crossfades; default "lin"),
              "norm_lufs": -16 (loudness-match the file to this before gain_db), negative "offset" (delay: pads silence),
              "back_time": true (offset chosen so the file's natural end, last sample above -60 dBFS, lands on "end"),
              "id" (free text, reported).
  sfx / amb event: "id", "bus": "sfx" | "amb", "src_in" (s into the file), "dur" (s kept), "t_out" (film end time),
              "loop": true (repeat to t_out with "loop_xfade" s equal-power seams, default 1.0), "fade_in", "fade_out",
              "curve", "pitch_st" (varispeed in semitones), "eq" (list of {"type": hp|lp|hs|ls|peak, "f", "db", "q"} or a
              string such as "high-shelf -6 dB above 5 kHz"), "norm_lufs", "enabled": false (skipped; any value but true
              or absent skips), "strict_off": true (skipped when the spec has "strict": true).
  "amb": [...]  a second event list mixed on the ambience bus (same keys as sfx); events with "bus": "amb" go there too.
  "duck":     "threshold_db" (VO activity gate, default -42), "hold" (s the duck stays down after the voice stops, default 0),
              "lookahead" (s the duck starts before the voice, default 0).
  "amb_duck": {"db", "attack", "release", "hold", "lookahead", "threshold_db"}: ducking of the ambience bus (default none).
  "dips":     entries [t0, t1, db], [t0, t1, db, ramp_s], [t0, t1, db, "note"] or {"t0", "t1", "db", "ramp", "ramp_in",
              "ramp_out", "note"}; ramps default 0.25 s; a positive db is a lift (dips multiply).
  "amb_dips": the same, applied to the ambience bus.
  "loudness_passes": 3 (re-measure after the limiter and correct the gain; default 1 = ep01 behaviour).
  "limiter": {"lookahead_ms": 5, "release_ms": 120}.
  "stems_dir": "dir" (or --stems DIR): writes vo.wav, music.wav, sfx.wav, amb.wav (24-bit, 48 kHz stereo) carrying the same
              loudness gain and limiter gain as the mix, so the four stems sum to the mix.
  --report path: JSON with loudness, limiter, per-bus loudness and the event list as placed.
"""
import json, subprocess, sys, argparse, re
from fractions import Fraction
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly, lfilter, sosfilt, butter
SR = 48000

def load(path, ch=2):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()

def db(x): return 10 ** (x / 20)

_CACHE = {}
def load_cached(path, ch=2):
    k = (path, ch)
    if k not in _CACHE: _CACHE[k] = load(path, ch)
    return _CACHE[k]

_NORM = {}
def norm_gain(path, target):
    """Linear gain that brings the whole file to target LUFS (cached per file)."""
    k = (path, target)
    if k not in _NORM:
        y = load_cached(path).astype(np.float64)
        lu = pyln.Meter(SR).integrated_loudness(y) if len(y) > SR // 2 else -70.0
        _NORM[k] = db(target - lu) if np.isfinite(lu) else 1.0
    return _NORM[k]

def ramp(n, curve='lin', up=True):
    if n <= 0: return np.ones(0, np.float32)
    x = np.linspace(0, 1, n, dtype=np.float64)
    r = np.sin(x * np.pi / 2) if curve == 'eqp' else x
    return (r if up else r[::-1]).astype(np.float32)

def apply_fades(y, fi, fo, curve='lin'):
    fi, fo = int(fi * SR), int(fo * SR)
    if fi: k = min(fi, len(y)); y[:k] *= ramp(fi, curve, True)[:k][:, None]
    if fo: k = min(fo, len(y)); y[len(y) - k:] *= ramp(fo, curve, False)[fo - k:][:, None]
    return y

def varispeed(y, st):
    """Pitch and speed together by st semitones (tape style)."""
    if not st: return y
    r = Fraction(2 ** (st / 12)).limit_denominator(400)
    return resample_poly(y, r.denominator, r.numerator, axis=0).astype(np.float32)

def biquad(kind, f, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f / SR; c, s = np.cos(w), np.sin(w); al = s / (2 * q)
    if kind == 'lp': b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'hp': b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'peak': b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind in ('hs', 'ls'):
        sq = 2 * np.sqrt(A) * al; sg = 1 if kind == 'hs' else -1
        b = [A * ((A + 1) + sg * (A - 1) * c + sq), -2 * sg * A * ((A - 1) + sg * (A + 1) * c), A * ((A + 1) + sg * (A - 1) * c - sq)]
        a = [(A + 1) - sg * (A - 1) * c + sq, 2 * sg * ((A - 1) - sg * (A + 1) * c), (A + 1) - sg * (A - 1) * c - sq]
    else: raise ValueError(f'eq type {kind}')
    return np.array(b) / a[0], np.array(a) / a[0]

def parse_eq(eq):
    if not eq: return []
    if isinstance(eq, dict): return [eq]
    if isinstance(eq, list): return eq
    s = eq.lower(); m = re.search(r'(-?\d+(?:\.\d+)?)\s*db', s); f = re.search(r'(\d+(?:\.\d+)?)\s*(k?)hz', s)
    fr = float(f.group(1)) * (1000 if f and f.group(2) else 1) if f else 1000.0
    g = float(m.group(1)) if m else 0.0
    kind = 'hs' if 'high-shelf' in s or 'high shelf' in s else 'ls' if 'low-shelf' in s or 'low shelf' in s else \
           'lp' if 'low-pass' in s or 'lowpass' in s else 'hp' if 'high-pass' in s or 'highpass' in s else 'peak'
    return [{'type': kind, 'f': fr, 'db': g}]

def apply_eq(y, eq):
    for b in parse_eq(eq):
        bb, aa = biquad(b['type'], b['f'], b.get('db', 0.0), b.get('q', 0.707))
        y = lfilter(bb, aa, y, axis=0).astype(np.float32)
    return y

def loop_to(y, L, xf):
    """Repeat y to length L with equal-power crossfades of xf samples at each seam."""
    if len(y) >= L or len(y) == 0: return y[:L]
    xf = int(min(xf, len(y) // 3)); out = np.zeros((L, y.shape[1]), np.float32)
    fin, fout = ramp(xf, 'eqp', True)[:, None], ramp(xf, 'eqp', False)[:, None]
    pos = 0; first = True
    while pos < L:
        seg = y.copy()
        if not first and xf: seg[:xf] *= fin
        if xf: seg[len(seg) - xf:] *= fout
        n = min(len(seg), L - pos); out[pos:pos + n] += seg[:n]
        pos += len(seg) - xf; first = False
    return out

def event_enabled(e, spec):
    en = e.get('enabled', True)
    if en is not True: return False
    if spec.get('strict') and e.get('strict_off'): return False
    return True

def place_event(e, N):
    """Returns (s0, y) for one sfx/amb event, or None if it falls outside the film."""
    y = load_cached(e['file'])
    if e.get('norm_lufs') is not None: y = y * norm_gain(e['file'], e['norm_lufs'])
    y = y[int(e.get('src_in', 0) * SR):]
    if e.get('pitch_st'): y = varispeed(y, e['pitch_st'])
    if e.get('eq'): y = apply_eq(y, e['eq'])
    s0 = int(e['t'] * SR)
    if s0 >= N: return None
    if e.get('t_out') is not None:
        L = int(round(e['t_out'] * SR)) - s0
        y = loop_to(y, L, e.get('loop_xfade', 1.0) * SR) if e.get('loop') else y[:L]
    if e.get('dur') is not None: y = y[:int(e['dur'] * SR)]
    y = (y * db(e.get('gain_db', -8))).astype(np.float32)
    if e.get('fade_in') or e.get('fade_out'): y = apply_fades(y, e.get('fade_in', 0), e.get('fade_out', 0), e.get('curve', 'lin'))
    if s0 < 0: y = y[-s0:]; s0 = 0
    return s0, y[:N - s0]

def natural_end(path, floor_db=-60):
    y = np.abs(load_cached(path)).max(axis=1); idx = np.where(y > db(floor_db))[0]
    return (idx[-1] + 1) / SR if len(idx) else len(y) / SR

def place_cue(m, dur):
    """Returns (s0, y, info) for one music cue, with the exact ep01 behaviour when no new keys are set."""
    y = load_cached(m['file'])
    if m.get('norm_lufs') is not None: y = y * norm_gain(m['file'], m['norm_lufs'])
    y = y * db(m.get('gain_db', -16))
    s0, s1 = int(m['start'] * SR), int(min(dur, m['end']) * SR)
    L = s1 - s0
    off_s = m.get('offset', 0)
    if m.get('back_time'): off_s = natural_end(m['file']) - (min(dur, m['end']) - m['start'])
    off = int(off_s * SR) if off_s >= 0 else -int(round(-off_s * SR))
    y = y[off:] if off >= 0 else np.concatenate([np.zeros((-off, 2), np.float32), y])
    if m.get('loop') and len(y) < L: y = np.tile(y, (L // len(y) + 1, 1))
    y = y[:L].copy()
    curve = m.get('curve', 'lin')
    if curve == 'lin':  # ep01 code path, kept bit-exact
        fi, fo = int(m.get('fade_in', 1.0) * SR), int(m.get('fade_out', 2.0) * SR)
        if fi: y[:fi] *= np.linspace(0, 1, min(fi, len(y)))[:, None]
        if fo: y[-fo:] *= np.linspace(1, 0, min(fo, len(y)))[:, None]
    else:
        y = apply_fades(y, m.get('fade_in', 1.0), m.get('fade_out', 2.0), curve)
    return s0, y, {'id': m.get('id', m['file'].rsplit('/', 1)[-1]), 'start': m['start'], 'end': m['end'], 'offset_used': round(off_s, 3),
                   'audio_ends_at': round(m['start'] + len(y) / SR, 3), 'ends_early': len(y) < L - SR // 10}

def vo_activity(vo_mono, d):
    """VO activity at 100 Hz (hop 480): RMS over 10 ms above threshold_db; each active run is extended forward by
    "hold" s and started "lookahead" s early. With neither key set this is the ep01 activity."""
    hop = 480
    rms = np.sqrt(np.convolve(vo_mono ** 2, np.ones(hop) / hop, 'same'))[::hop]
    act = (rms > db(d.get('threshold_db', -42))).astype(np.float32)
    n = len(act); idx = np.arange(n); on = act > 0
    h = int(round(d.get('hold', 0) * 100)); la = int(round(d.get('lookahead', 0) * 100))
    if h > 0:
        last = np.maximum.accumulate(np.where(on, idx, -10 ** 9)); act = np.maximum(act, (idx - last <= h).astype(np.float32))
    if la > 0:
        nxt = np.minimum.accumulate(np.where(on, idx, 10 ** 9)[::-1])[::-1]; act = np.maximum(act, (nxt - idx <= la).astype(np.float32))
    return act

def duck_gain(act, d, N):
    hop = 480
    ca, cr = np.exp(-1 / (d['attack'] * 100)), np.exp(-1 / (d['release'] * 100))
    g = np.empty_like(act); e = 0.0
    for i, v in enumerate(act): c = ca if v > e else cr; e = c * e + (1 - c) * v; g[i] = e
    gain = db(d['db'] * g)
    return np.interp(np.arange(N), np.arange(len(gain)) * hop, gain).astype(np.float32)

def dip_env(dips, N):
    env = np.ones(N, np.float32)
    for dp in dips:
        if isinstance(dp, dict):
            d0, d1, ddb = dp['t0'], dp['t1'], dp['db']; r_in = dp.get('ramp_in', dp.get('ramp', 0.25)); r_out = dp.get('ramp_out', dp.get('ramp', 0.25))
        else:
            d0, d1, ddb = dp[0], dp[1], dp[2]
            r = dp[3] if len(dp) > 3 and isinstance(dp[3], (int, float)) else 0.25; r_in = r_out = r
        a, b = int(d0 * SR), int(d1 * SR); lo = db(ddb)
        seg = np.full(max(0, b - a), lo, np.float32)
        ki, ko = min(int(r_in * SR), len(seg) // 2), min(int(r_out * SR), len(seg) // 2)
        if ki: seg[:ki] = np.linspace(1, lo, ki)
        if ko: seg[-ko:] = np.linspace(lo, 1, ko)
        n = max(0, min(b, N) - a)
        env[a:a + n] *= seg[:n]
    return env

def build(spec):
    """Builds the buses. Returns dict: vo (N,2), music (N,2, ducked and dipped), sfx (N,2), amb (N,2, ducked and dipped),
    music_gain (N,), amb_gain (N,), cues (info list), events (placed list), act (100 Hz VO activity used for the duck)."""
    dur = spec['duration']; N = int(dur * SR)
    bus_m = np.zeros((N, 2), np.float32); bus_s = np.zeros((N, 2), np.float32); bus_a = np.zeros((N, 2), np.float32)
    vo = np.zeros((N, 2), np.float32)
    if spec.get('vo'):
        v = load(spec['vo'], 1)[:, 0] * db(spec.get('vo_gain_db', 0))
        n = min(N, len(v)); vo[:n, 0] = v[:n]; vo[:n, 1] = v[:n]
    cues = []
    for m in spec.get('music', []):
        if m.get('enabled', True) is not True: continue
        s0, y, info = place_cue(m, dur); bus_m[s0:s0 + len(y)] += y; cues.append(info)
    placed = []
    events = [(e, e.get('bus', 'sfx')) for e in spec.get('sfx', [])] + [(e, 'amb') for e in spec.get('amb', [])]
    for e, bus in events:
        if not event_enabled(e, spec): continue
        r = place_event(e, N)
        if r is None: continue
        s0, y = r
        (bus_a if bus == 'amb' else bus_s)[s0:s0 + len(y)] += y
        placed.append({'id': e.get('id'), 'bus': bus, 't': round(s0 / SR, 3), 't_end': round((s0 + len(y)) / SR, 3), 'file': e['file'].rsplit('/', 1)[-1],
                       'gain_db': e.get('gain_db', -8)})
    d = spec.get('duck', {'db': -8, 'attack': 0.06, 'release': 0.45})
    act = vo_activity(vo[:, 0], d)
    gain = duck_gain(act, d, N)
    dips = spec.get('dips', [])
    if dips: gain = gain * dip_env(dips, N)
    ad = spec.get('amb_duck')
    again = duck_gain(vo_activity(vo[:, 0], ad), ad, N) if ad else np.ones(N, np.float32)
    if spec.get('amb_dips'): again = again * dip_env(spec['amb_dips'], N)
    bus_m *= gain[:, None]; bus_a *= again[:, None]
    return {'vo': vo, 'music': bus_m, 'sfx': bus_s, 'amb': bus_a, 'music_gain': gain, 'amb_gain': again, 'cues': cues, 'events': placed, 'act': act}

def true_peak_env(mix, chunk=SR * 10, pad=2048):
    """Per-sample max |x| over the 4x oversampled signal (chunked to bound memory)."""
    N = len(mix); pk = np.empty(N, np.float32)
    for a in range(0, N, chunk):
        b = min(N, a + chunk); a0, b0 = max(0, a - pad), min(N, b + pad)
        up = resample_poly(mix[a0:b0].astype(np.float64), 4, 1, axis=0)
        p = np.abs(up).max(axis=1)[:(b0 - a0) * 4].reshape(-1, 4).max(axis=1)
        pk[a:b] = p[a - a0:a - a0 + (b - a)]
    return pk

def limiter_gain(pk, tp, lim):
    """Control-rate (1 ms blocks) gain computer with look-ahead and release, as in the ep01 mix.py."""
    N = len(pk); need = np.minimum(1.0, tp / np.maximum(pk, 1e-9))
    B = 48; nb = (N + B - 1) // B
    needb = np.pad(need, (0, nb * B - N), constant_values=1.0).reshape(nb, B).min(axis=1)
    from scipy.ndimage import minimum_filter1d
    la = int(lim.get('lookahead_ms', 5)); needb = minimum_filter1d(needb, size=2 * la + 1)
    rel = np.exp(-1 / (lim.get('release_ms', 120) / 1000 * 1000)); grb = np.empty_like(needb); e = 1.0
    for i in range(nb):
        v = needb[i]; e = v if v < e else rel * e + (1 - rel) * v; grb[i] = e
    gr = np.interp(np.arange(N), np.arange(nb) * B + B / 2, grb).astype(np.float32)
    return np.minimum(gr, need).astype(np.float32)

def master(mix, spec):
    """Loudness normalisation + true-peak limiting. Returns (total linear gain per sample as (g_lin, gr), info)."""
    meter = pyln.Meter(SR); target = spec.get('target_lufs', -14); tp = db(spec.get('true_peak', -1.5)); lim = spec.get('limiter', {})
    lufs = meter.integrated_loudness(mix.astype(np.float64))
    g = db(target - lufs)
    pk0 = true_peak_env(mix)
    passes = int(spec.get('loudness_passes', 1)); hist = []
    for p in range(passes):
        gr = limiter_gain(pk0 * g, tp, lim)
        lufs2 = meter.integrated_loudness((mix * (g * gr)[:, None]).astype(np.float64))
        hist.append(round(float(lufs2), 2))
        if p < passes - 1:
            if abs(lufs2 - target) < 0.05: break
            g *= db(target - lufs2)
    return g, gr, {'lufs_raw': round(float(lufs), 2), 'lufs_out': hist[-1], 'passes': hist, 'gain_db': round(float(20 * np.log10(g)), 2),
                   'limiter_max_gr_db': round(float(20 * np.log10(gr.min())), 2), 'limiter_active_s': round(float((gr < 0.999).sum() / SR), 2)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('out'); ap.add_argument('--stems'); ap.add_argument('--report')
    a = ap.parse_args()
    spec = json.load(open(a.spec)); outp = a.out
    B = build(spec)
    mix = B['vo'] + B['music'] + B['sfx'] + B['amb']
    g, gr, info = master(mix, spec)
    tot = (g * gr)[:, None]
    sf.write(outp, mix * tot, SR, subtype='PCM_24')
    print(f'mixed {spec["duration"]:.1f} s -> {outp}; LUFS {info["lufs_raw"]:.1f} -> {info["lufs_out"]:.1f}; limiter max GR {info["limiter_max_gr_db"]:.1f} dB')
    sd = a.stems or spec.get('stems_dir')
    if sd:
        import os; os.makedirs(sd, exist_ok=True)
        for k in ('vo', 'music', 'sfx', 'amb'): sf.write(os.path.join(sd, f'{k}.wav'), B[k] * tot, SR, subtype='PCM_24')
        print('stems ->', sd)
    if a.report:
        meter = pyln.Meter(SR); buses = {}
        for k in ('vo', 'music', 'sfx', 'amb'):
            x = (B[k] * tot).astype(np.float64)
            lu = meter.integrated_loudness(x) if np.abs(x).max() > 0 else float('-inf')
            buses[k] = round(float(lu), 2) if np.isfinite(lu) else None
        json.dump({'master': info, 'bus_lufs': buses, 'cues': B['cues'], 'events': B['events']}, open(a.report, 'w'), indent=1)

if __name__ == '__main__':
    main()
