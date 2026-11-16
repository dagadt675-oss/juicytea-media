#!/usr/bin/env python3
"""sfx_check.py: objective checks for generated sound, take picking and preparation for mix.py.

  sfx_check.py sfx  SFX_DONE_JSON SPOT_SFX_JSON OUT_DIR [--expect EXPECT_JSON] [--asr MODEL]
      Measures every take listed by sfx_gen.py (sfx_done.json), picks the best take per variant, trims the leading
      silence of one-shots (10 ms pre-roll), trims dead tails, normalises to -20 LUFS with the sample peak at -2 dBFS or
      lower (the ep01 sfx/norm convention, 48 kHz stereo 24-bit WAV), re-measures the sync point (onset, loudest moment
      or end of a rise) and writes OUT_DIR/<asset>_v<n>.wav plus OUT_DIR/selected.json and OUT_DIR/report.txt.
  sfx_check.py music CUES_DONE_JSON SPOT_MUSIC_JSON OUT_JSON [--asr MODEL]
      Measures every music cue: length vs its window, loudness, true peak, clipping, holes, spectrum, the energy of each
      planned section against its low/mid/high label, whether each planned stop, bloom or downbeat lands (and the
      offset that would make it land), key (Krumhansl profiles on a chroma) and tempo (onset autocorrelation) against
      the prompt (both rough: parallel major/minor and 3:4 tempo confusions are common), and voice-like content
      (vocals) with Silero VAD plus faster-whisper. Alternates named <cue id>_plan or _take<n> map to their cue.

EXPECT_JSON (episode intent checks, all optional, per asset id): centroid [lo, hi] Hz, max_sub_db, min_below150_db,
min_above250_db, max_above250_db, max_air_db, rising, pitch_up, pitch_down, abrupt_end, min_tail_s, max_dur,
sync ('onset' | 'peak' | 'end' | 'bed'), lowpass_hz / highpass_hz (applied before measuring and kept in the prepared
file); '_voice_check': [ids] adds the voice check to short sounds. Beds are de-clicked (isolated spikes of 5 ms or
less); a burst in the last 10 ms of a one-shot (a generation artefact) is cut; one-shots always end on a fade.

Measures: duration; integrated loudness (BS.1770, pyloudnorm); sample peak and 4x-oversampled true peak; clipped runs
(4+ consecutive samples at |x| >= 0.98) and samples over full scale; leading and trailing silence and holes of 0.3 s
or more inside the sound (10 ms RMS envelope against its own maximum); spectral centroid and band shares (sub < 100 Hz,
low < 250, body 250-700, presence 1-4 kHz, air > 4 kHz; 'above 250 Hz' is the phone-speaker check); loudness and
centroid slopes (risers rise, sinks fall); L/R correlation; loop seam jump and level match; steadiness of beds.
Voice check: Silero VAD seconds, and the faster-whisper transcript when VAD fires (a hallucinated 'Thank you.' on noise
is common, so a transcript alone is not a failure). No agent verdict on taste: the owner listens (PLAYBOOK_production 16)."""
import argparse, json, os, re, subprocess, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly, butter, sosfiltfilt

SR = 48000
BANDS = {'sub': (0, 100), 'low': (100, 250), 'body': (250, 700), 'mid': (700, 1000), 'presence': (1000, 4000), 'air': (4000, 24000)}

def load(path, sr=SR, ch=2):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', str(ch), '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()

def db(x): return 10 * np.log10(np.maximum(x, 1e-12))

def envelope(x, hop=480):
    p = (x.astype(np.float64) ** 2).mean(axis=1)
    n = len(p) // hop
    if n == 0: return np.array([db(p.mean())])
    return db(p[:n * hop].reshape(n, hop).mean(axis=1))  # 10 ms frames

def lufs(x, meter):
    y = x.astype(np.float64)
    if len(y) < int(0.42 * SR): y = np.pad(y, ((0, int(0.42 * SR) - len(y)), (0, 0)))
    v = meter.integrated_loudness(y)
    return float(v) if np.isfinite(v) else -99.0

def runs(mask, min_len):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            if j - i >= min_len: out.append((i, j))
            i = j
        else: i += 1
    return out

def spectrum(x):
    m = x.mean(axis=1).astype(np.float64)
    if len(m) < 4096: m = np.pad(m, (0, 4096 - len(m)))
    seg = 4096; hop = 2048; w = np.hanning(seg); P = np.zeros(seg // 2 + 1)
    for s in range(0, len(m) - seg + 1, hop): P += np.abs(np.fft.rfft(m[s:s + seg] * w)) ** 2
    f = np.fft.rfftfreq(seg, 1 / SR)
    return f, P

def spikes(x):
    """isolated clicks: runs of 5 ms or less where |x| exceeds 4x the 99.9th percentile (generation artefacts in beds)"""
    a = np.abs(x).max(axis=1); thr = 4 * np.percentile(a, 99.9)
    idx = np.where(a > thr)[0]; out = []
    for i in idx:
        if out and i - out[-1][1] <= int(0.005 * SR): out[-1][1] = i
        else: out.append([i, i])
    return [r_ for r_ in out if r_[1] - r_[0] <= int(0.005 * SR)], thr

def declick(x):
    """pull each isolated click down to the 99.9th-percentile level with 2 ms raised-cosine ramps"""
    runs_, thr = spikes(x); y = x.copy(); r = int(0.002 * SR)
    for a0, a1 in runs_:
        s0, s1 = max(0, a0 - r), min(len(y), a1 + r + 1)
        g = np.ones(s1 - s0); lo = thr / 4 / max(float(np.abs(y[a0:a1 + 1]).max()), 1e-9)
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, r))
        g[:] = lo
        if a0 - s0 >= r: g[:r] = 1 - (1 - lo) * ramp       # ramp down into the click
        if s1 - a1 - 1 >= r: g[-r:] = lo + (1 - lo) * ramp  # and back up after it
        y[s0:s1] *= g[:, None]
    return y, [round(float(a0) / SR, 3) for a0, _ in runs_]

def measure(x, loop=False):
    meter = pyln.Meter(SR)
    d = {'dur': round(len(x) / SR, 3)}
    e0 = envelope(x)  # a burst in the very last 10 ms frame is a generation artefact (a click at the cut), not content
    d['end_click'] = bool(len(e0) > 12 and e0[-1] - np.median(e0[-11:-1]) > 6 and not loop)
    if d['end_click']: x = x[:len(x) - int(0.02 * SR)]
    pk = float(np.abs(x).max()); d['peak_db'] = round(20 * np.log10(max(pk, 1e-9)), 1)
    up = resample_poly(x, 4, 1, axis=0); d['true_peak_db'] = round(20 * np.log10(max(float(np.abs(up).max()), 1e-9)), 1)
    d['over_fs'] = int((np.abs(x) > 1.0).sum())
    d['clip_runs'] = sum(len(runs(np.abs(x[:, c]) >= 0.98, 4)) for c in range(x.shape[1]))
    d['lufs'] = round(lufs(x, meter), 1)
    e = envelope(x); emax = float(e.max()); d['env_max_db'] = round(emax, 1)
    on_thr, off_thr, hole_thr = max(-60.0, emax - 30), max(-70.0, emax - 50), max(-60.0, emax - 45)
    act = np.where(e > on_thr)[0]
    first = int(act[0]) if len(act) else 0
    last_any = np.where(e > off_thr)[0]; last = int(last_any[-1]) if len(last_any) else len(e) - 1
    d['lead_s'] = round(first * 0.01, 3); d['tail_silence_s'] = round(max(0.0, d['dur'] - (last + 1) * 0.01), 3)
    hl = [(a, b) for a, b in runs(e[first:last + 1] < hole_thr, 30)]
    d['holes'] = [[round((first + a) * 0.01, 2), round((first + b) * 0.01, 2)] for a, b in hl]
    sm = np.convolve(e, np.ones(5) / 5, 'same'); d['peak_t'] = round(int(np.argmax(sm)) * 0.01, 3)
    loud = np.where(e > emax - 12)[0]; d['end_t'] = round((int(loud[-1]) + 1) * 0.01, 3) if len(loud) else d['dur']
    after = e[int(d['end_t'] * 100):int(d['end_t'] * 100) + 10]
    d['abrupt_end'] = bool(d['dur'] - d['end_t'] < 0.15 or (len(after) and after.min() < emax - 30))
    f, P = spectrum(x[first * 480:(last + 1) * 480] if last > first else x)
    tot = P.sum() + 1e-20
    d['centroid_hz'] = int((f * P).sum() / tot)
    d['bands_db'] = {k: round(float(db(P[(f >= lo) & (f < hi)].sum() / tot)), 1) for k, (lo, hi) in BANDS.items()}
    d['below150_db'] = round(float(db(P[f < 150].sum() / tot)), 1)
    d['above250_db'] = round(float(db(P[f >= 250].sum() / tot)), 1)
    # slopes over the active part, 100 ms steps
    seg = e[first:last + 1]
    if len(seg) >= 30:
        t = np.arange(len(seg)) * 0.01; d['loud_slope_db_s'] = round(float(np.polyfit(t, seg, 1)[0]), 2)
        cents = []
        for s in range(first * 480, (last + 1) * 480 - 4800, 4800):
            ff, PP = spectrum(x[s:s + 4800]); cents.append((ff * PP).sum() / (PP.sum() + 1e-20))
        d['centroid_slope_hz_s'] = round(float(np.polyfit(np.arange(len(cents)) * 0.1, cents, 1)[0]), 1) if len(cents) >= 3 else 0.0
    else:
        d['loud_slope_db_s'] = 0.0; d['centroid_slope_hz_s'] = 0.0
    L, R = x[:, 0].astype(np.float64), x[:, 1].astype(np.float64)
    d['lr_corr'] = round(float(np.corrcoef(L, R)[0, 1]), 2) if L.std() > 0 and R.std() > 0 else 1.0
    if loop:
        d['clicks_at'] = [round(float(a0) / SR, 3) for a0, _ in spikes(x)[0]][:10]
        rms = np.sqrt((x.astype(np.float64) ** 2).mean()) + 1e-12
        d['seam_jump'] = round(float(np.abs(x[-1] - x[0]).max() / rms), 2)
        n3 = int(0.3 * SR)
        d['seam_level_db'] = round(float(db((x[-n3:] ** 2).mean()) - db((x[:n3] ** 2).mean())), 1)
        sec = [float(db((x[s:s + SR] ** 2).mean())) for s in range(0, len(x) - SR + 1, SR // 2)]
        d['steady_std_db'] = round(float(np.std(sec)), 1) if sec else 0.0
    return d

# ----------------------------------------------------------------------------- voice check
_asr = None
def voice(path, model):
    global _asr
    from faster_whisper import vad
    a = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    ts = vad.get_speech_timestamps(a, vad.VadOptions(threshold=0.6, min_speech_duration_ms=250, min_silence_duration_ms=300, speech_pad_ms=0))
    secs = round(sum(t['end'] - t['start'] for t in ts) / 16000, 2)
    out = {'vad_speech_s': secs, 'text': ''}
    if secs >= 0.5 and model:
        if _asr is None:
            from faster_whisper import WhisperModel
            _asr = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=4)
        segs, _ = _asr.transcribe(a, language='en', beam_size=1, condition_on_previous_text=False, vad_filter=True)
        good = [s for s in segs if s.no_speech_prob < 0.5 and s.avg_logprob > -0.9]
        out['text'] = ' '.join(s.text.strip() for s in good)[:200]
    return out

# ----------------------------------------------------------------------------- SFX
def sync_kind(a):
    if a.get('loop'): return 'bed'
    s, L = a.get('sync_s', 0) or 0, a.get('length_s') or 1
    if s <= 0.1: return 'onset'
    if s >= 0.85 * L: return 'end'
    return 'peak'

def judge(m, a, exp, kind, req):
    """penalty points and reasons for one take (lower is better)"""
    pts, why = 0.0, []
    def bad(p, r): nonlocal pts; pts += p; why.append(r)
    if m['env_max_db'] < -60: bad(20, 'no audio')
    if m['clip_runs']: bad(6, f"clipped runs {m['clip_runs']}")
    if req and m['dur'] < 0.7 * req: bad(4, f"short {m['dur']} s of {req} s")
    if req: pts += 2 * abs(m['dur'] - req) / req
    if m['lr_corr'] < -0.2: bad(2, f"out-of-phase stereo (corr {m['lr_corr']})")
    if m.get('end_click'): bad(0.25, 'click in the last 10 ms (cut off in the prepared file)')
    if m['lufs'] < -45: bad(0.25, f"very quiet raw ({m['lufs']} LUFS, about +{-20 - m['lufs']:.0f} dB to normalise): listen for hiss")
    if kind not in ('bed', 'end') and not (exp or {}).get('rising') and m['dur'] < 3 and m['peak_t'] >= m['dur'] - 0.03:
        bad(1.5, 'loudest in the last 30 ms of the file (may be cut off)')
    if kind == 'bed':
        if m['holes']: bad(4, f"holes {m['holes'][:3]}")
        if m.get('clicks_at'): bad(0.5, f"isolated clicks at {m['clicks_at'][:4]} s (repaired in the prepared file)")
        if m.get('steady_std_db', 0) > 4: bad(2, f"unsteady bed (std {m['steady_std_db']} dB)")
        if abs(m.get('seam_level_db', 0)) > 3: bad(1, f"loop seam level jump {m['seam_level_db']} dB")
        if m['lead_s'] > 0.3: bad(2, f"bed starts late ({m['lead_s']} s)")
    else:
        if m['lead_s'] > 0.4: bad(1, f"late onset {m['lead_s']} s (trimmed)")
    if m.get('voice', {}).get('vad_speech_s', 0) >= 0.5 and m['voice'].get('text'): bad(6, f"voice-like: '{m['voice']['text'][:60]}'")
    e = exp or {}
    if 'centroid' in e and not (e['centroid'][0] <= m['centroid_hz'] <= e['centroid'][1]): bad(2, f"centroid {m['centroid_hz']} Hz outside {e['centroid']}")
    if 'max_sub_db' in e and m['bands_db']['sub'] > e['max_sub_db']: bad(2, f"sub share {m['bands_db']['sub']} dB > {e['max_sub_db']}")
    if 'min_below150_db' in e and m['below150_db'] < e['min_below150_db']: bad(2, f"below-150 Hz share {m['below150_db']} dB < {e['min_below150_db']}")
    if 'min_above250_db' in e and m['above250_db'] < e['min_above250_db']: bad(2, f"above-250 Hz share {m['above250_db']} dB < {e['min_above250_db']} (phone)")
    if 'max_above250_db' in e and m['above250_db'] > e['max_above250_db']: bad(2, f"above-250 Hz share {m['above250_db']} dB > {e['max_above250_db']} (meant to be low)")
    if 'max_air_db' in e and m['bands_db']['air'] > e['max_air_db']: bad(1.5, f"air/hiss share {m['bands_db']['air']} dB > {e['max_air_db']}")
    if e.get('rising') and m['loud_slope_db_s'] <= 0: bad(3, f"does not rise (slope {m['loud_slope_db_s']} dB/s)")
    if e.get('pitch_up') and m['centroid_slope_hz_s'] <= 0: bad(1.5, f"pitch/brightness does not rise ({m['centroid_slope_hz_s']} Hz/s)")
    if e.get('pitch_down') and m['centroid_slope_hz_s'] >= 0: bad(1.5, f"does not descend ({m['centroid_slope_hz_s']} Hz/s)")
    if e.get('abrupt_end') and not m['abrupt_end']: bad(2, 'does not end abruptly')
    if 'min_tail_s' in e and (m['dur'] - m['tail_silence_s'] - m['peak_t']) < e['min_tail_s']: bad(1.5, f"tail shorter than {e['min_tail_s']} s")
    if 'max_dur' in e and (m['dur'] - m['lead_s'] - m['tail_silence_s']) > e['max_dur']: bad(1, f"sounding length over {e['max_dur']} s")
    if kind == 'peak' and a.get('sync_s') is not None and req:
        off = abs((m['peak_t'] - m['lead_s']) - a['sync_s'])
        if off > max(0.25, 0.3 * req): pts += 0.5; why.append(f"loudest moment {m['peak_t']} s vs designed {a['sync_s']} s")
    return round(pts, 2), why

def prepare(x, m, kind):
    fixed = []
    if kind == 'bed':
        s0, s1 = 0, len(x); x, fixed = declick(x)
    else:
        s0 = max(0, int((m['lead_s'] - 0.01) * SR))
        s1 = min(len(x) - (int(0.02 * SR) if m.get('end_click') else 0), int((m['dur'] - m['tail_silence_s'] + 0.06) * SR))
    y = x[s0:s1].copy()
    if kind != 'bed':
        if s0 > 0: y[:int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))[:, None]
        n = min(len(y), int((0.02 if s1 < len(x) else 0.01) * SR)); y[-n:] *= np.linspace(1, 0, n)[:, None]  # one-shots always end on a fade
    meter = pyln.Meter(SR)
    g = -20.0 - lufs(y, meter)
    pk = 20 * np.log10(max(float(np.abs(y).max()), 1e-9)); tp = 20 * np.log10(max(float(np.abs(resample_poly(y, 4, 1, axis=0)).max()), 1e-9))
    g = min(g, -2.0 - pk, -1.0 - tp)
    return y * (10 ** (g / 20)), s0 / SR, round(g, 1), fixed

def run_sfx(a):
    done = json.load(open(a.done)); spot = json.load(open(a.spot)); exp = json.load(open(a.expect)) if a.expect else {}
    os.makedirs(a.out, exist_ok=True)
    assets = spot['assets']; sel, lines, fails = {}, [], []
    for aid, takes in sorted(done['files'].items()):
        A = assets[aid]; kind = exp.get(aid, {}).get('sync', sync_kind(A)); req = takes[0]['dur']
        meas = []
        E = exp.get(aid, {})
        for t in takes:
            x = load(t['file'])
            if E.get('lowpass_hz'): x = sosfiltfilt(butter(4, E['lowpass_hz'], 'low', fs=SR, output='sos'), x, axis=0).astype(np.float32)
            if E.get('highpass_hz'): x = sosfiltfilt(butter(4, E['highpass_hz'], 'high', fs=SR, output='sos'), x, axis=0).astype(np.float32)
            m = measure(x, loop=(kind == 'bed'))
            if kind == 'bed' or m['dur'] >= 1.5 or aid in exp.get('_voice_check', []): m['voice'] = voice(t['file'], a.asr)
            pts, why = judge(m, A, exp.get(aid), kind, req)
            meas.append({'variant': t['variant'], 'take': t['take'], 'file': t['file'], 'score': pts, 'why': why, 'm': m, 'x': x})
        out_vars = []
        for v in sorted({q['variant'] for q in meas}):
            cand = sorted([q for q in meas if q['variant'] == v], key=lambda q: (q['score'], -q['m']['lufs']))  # tie: the fuller (louder) generation
            best = cand[0]
            y, cut_s, gain, declicked = prepare(best['x'], best['m'], kind)
            fn = os.path.join(a.out, f'{aid}_v{v}.wav'); sf.write(fn, y, SR, subtype='PCM_24')
            m2 = measure(y, loop=(kind == 'bed'))
            if kind == 'onset': sync = round(max(0.0, best['m']['lead_s'] - cut_s), 3)
            elif kind == 'peak': sync = round(best['m']['peak_t'] - cut_s, 3)
            elif kind == 'end': sync = round(best['m']['end_t'] - cut_s, 3)
            else: sync = 0.0
            rec = {'variant': v, 'file': fn, 'take': best['take'], 'raw': best['file'], 'score': best['score'], 'flags': best['why'],
                   'other_takes': [{'take': q['take'], 'score': q['score'], 'flags': q['why']} for q in cand[1:]],
                   'trimmed_lead_s': round(cut_s, 3), 'norm_gain_db': gain, 'declicked_at_s': declicked, 'sync_s_measured': sync,
                   'level_vs_norm_db': round(m2['lufs'] + 20.0, 1),  # below 0: peak cap kept it under -20 LUFS; add -this to the mix gain_db
                   'sync_shift_vs_design_s': round(sync - (A.get('sync_s') or 0), 3) if kind != 'bed' else 0.0,
                   'raw_metrics': {k: v2 for k, v2 in best['m'].items()}, 'final': {k: m2[k] for k in ('dur', 'lufs', 'peak_db', 'true_peak_db', 'clip_runs', 'lead_s')}}
            out_vars.append(rec)
            hard = [w for w in best['why'] if not w.startswith(('loudest moment', 'late onset'))]
            if best['score'] >= 2 or hard: fails.append(f"{aid} v{v} (take {best['take']}, score {best['score']}): " + '; '.join(best['why']))
            mm = best['m']
            lines.append(f"{aid:22s} v{v} t{best['take']}/{len(cand)} {kind:5s} dur {mm['dur']:5.2f}/{req} LUFS {mm['lufs']:6.1f} TP {mm['true_peak_db']:5.1f} "
                         f"lead {mm['lead_s']:.2f} cen {mm['centroid_hz']:5d} >250 {mm['above250_db']:5.1f} sub {mm['bands_db']['sub']:5.1f} "
                         f"sync {sync:5.2f} (design {A.get('sync_s')}) score {best['score']}" + (f" | {'; '.join(best['why'])}" if best['why'] else ''))
        if len(out_vars) > 1:
            cs = [r_['raw_metrics']['centroid_hz'] for r_ in out_vars]
            if max(cs) > 4 * max(1, min(cs)): fails.append(f"{aid}: variants differ in character (centroid {min(cs)}-{max(cs)} Hz), so they may not read as one device")
        sel[aid] = {'kind': kind, 'filters': {k: E[k] for k in ('lowpass_hz', 'highpass_hz') if k in E}, 'design_sync_s': A.get('sync_s'), 'prompt': A['gen_prompt'], 'requested_s': req, 'variants': out_vars}
    json.dump(sel, open(os.path.join(a.out, 'selected.json'), 'w'), indent=1)
    rep = [f"{len(sel)} sounds, {sum(len(v['variants']) for v in sel.values())} prepared files from {sum(len(t) for t in done['files'].values())} takes",
           f"flagged ({len(fails)}):"] + ['  ' + f for f in fails] + ['', 'per file:'] + lines
    open(os.path.join(a.out, 'report.txt'), 'w').write('\n'.join(rep) + '\n'); print('\n'.join(rep[:len(fails) + 3]))

# ----------------------------------------------------------------------------- music
def short_term(x, win=1.0, hop=0.25):
    meter = pyln.Meter(SR, block_size=0.4); n, h = int(win * SR), int(hop * SR); out = []
    for s in range(0, max(1, len(x) - n + 1), h):
        v = meter.integrated_loudness(x[s:s + n].astype(np.float64)); out.append(v if np.isfinite(v) else -70.0)
    return np.array(out)

# Krumhansl-Kessler key profiles; chroma from the STFT (60-2000 Hz), log-compressed
KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

def key_estimate(x):
    m = x.mean(axis=1).astype(np.float64); seg, hop = 8192, 4096; w = np.hanning(seg)
    f = np.fft.rfftfreq(seg, 1 / SR); band = (f >= 60) & (f <= 2000)
    pc = np.round(12 * np.log2(f[band] / 440.0)).astype(int) % 12
    pc = (pc + 9) % 12  # A=9 when C=0
    chroma = np.zeros(12)
    for s0 in range(0, len(m) - seg + 1, hop):
        P = np.abs(np.fft.rfft(m[s0:s0 + seg] * w))[band] ** 2
        chroma += np.bincount(pc, weights=np.log1p(P / (P.mean() + 1e-12)), minlength=12)
    best = max(((np.corrcoef(np.roll(prof, k), chroma)[0, 1], f"{NOTES[k]} {name}") for k in range(12) for prof, name in ((KK_MAJ, 'major'), (KK_MIN, 'minor'))))
    return best[1], round(float(best[0]), 2), chroma / (chroma.max() + 1e-12)

def tempo_estimate(x):
    m = x.mean(axis=1).astype(np.float64); seg, hop = 2048, 480; w = np.hanning(seg); prev = None; flux = []
    for s0 in range(0, len(m) - seg + 1, hop):
        P = np.log1p(np.abs(np.fft.rfft(m[s0:s0 + seg] * w)))
        if prev is not None: flux.append(np.maximum(P - prev, 0).sum())
        prev = P
    o = np.array(flux) - np.mean(flux)
    ac = np.correlate(o, o, 'full')[len(o) - 1:]
    lags = np.arange(len(ac)); bpm = 60.0 / (lags[1:] * hop / SR); a = ac[1:]
    ok = (bpm >= 60) & (bpm <= 180)
    return round(float(bpm[ok][np.argmax(a[ok])]), 1)

def key_matches(est, want):
    """'D Lydian' is a D-major-family mode; relative keys (same notes) count as a match"""
    if not want: return None
    tonic, mode = want.split()[0], want.split()[1].lower()
    fam = {'lydian': 'major', 'mixolydian': 'major', 'ionian': 'major', 'dorian': 'minor', 'aeolian': 'minor', 'phrygian': 'minor'}.get(mode, mode)
    nt = {'Db': 'C#', 'D#': 'Eb', 'Gb': 'F#', 'G#': 'Ab', 'A#': 'Bb'}.get(tonic, tonic)
    k = NOTES.index(nt); et, em = est.split(); ek = NOTES.index(et)
    rel = (k + 9) % 12 if fam == 'major' else (k + 3) % 12
    return (ek == k and em == fam) or (ek == rel and em != fam)

EVENT_UP = re.compile(r'bloom|arrival|downbeat|hit|swell|HARD IN|lift|returns|stride|chord|stands|massive', re.I)
EVENT_DOWN = re.compile(r'STOP|stop-down|drops|dropout|thins|near silence|rings out|stop', re.I)

def run_music(a):
    done = json.load(open(a.done)); spot = json.load(open(a.spot)); cues = {c['id']: c for c in spot['cues']}
    res = []
    for c in done['cues']:
        sc = cues.get(c['id']) or cues[re.sub(r'_(plan|take\d+|alt\w*)$', '', c['id'])]  # alternates map to their spotted cue
        x = load(c['file']); m = measure(x)
        m['voice'] = voice(c['file'], a.asr)
        win = sc['t_out'] - sc['t_in']
        r = {'id': c['id'], 'file': c['file'], 'window_s': round(win, 2), 'requested_s': c['dur'] + 3, 'ends_early': m['dur'] < win + 0.1,
             'metrics': {k: v for k, v in m.items() if k not in ('end_t', 'abrupt_end')}}
        st = short_term(x); tt = np.arange(len(st)) * 0.25 + 0.5
        secs = []
        for s in sc.get('sections', []):
            t0, t1 = s['t0'] - sc['t_in'], s['t1'] - sc['t_in']
            v = st[(tt >= t0) & (tt < t1)]
            secs.append({'name': s['name'], 't0': round(t0, 2), 't1': round(t1, 2), 'energy': s.get('energy'), 'median_lufs': round(float(np.median(v)), 1) if len(v) else None})
        r['sections'] = secs
        lv = {k: [q['median_lufs'] for q in secs if q['energy'] == k and q['median_lufs'] is not None] for k in ('low', 'mid', 'high')}
        mean = {k: round(float(np.mean(v)), 1) for k, v in lv.items() if v}
        r['energy_mean_by_label'] = mean
        order = [mean[k] for k in ('low', 'mid', 'high') if k in mean]
        r['energy_order_ok'] = all(b >= a2 - 1.0 for a2, b in zip(order, order[1:]))
        vals = [q['median_lufs'] for q in secs if q['median_lufs'] is not None]
        r['section_spread_lu'] = round(max(vals) - min(vals), 1) if vals else 0.0
        hits = []
        for sp in sc.get('sync_points', []):
            t = sp['t'] - sc['t_in']; what = sp['what']
            up, down = bool(EVENT_UP.search(what)), bool(EVENT_DOWN.search(what))
            if not (up or down) or t < 0.5: continue
            d1 = np.diff(st)  # change per 0.25 s
            sel_ = (tt[1:] >= t - 4) & (tt[1:] <= t + 4)
            if not sel_.any(): continue
            idx = np.where(sel_)[0]
            k = idx[np.argmax(d1[idx])] if up and not down else idx[np.argmin(d1[idx])]
            found = round(float(tt[1:][k]), 2); delta = round(float(d1[k]), 1)
            hits.append({'t_rel': round(t, 2), 'what': what, 'type': 'down' if down else 'up', 'found_at': found, 'step_lu': delta,
                         'offset_s': round(found - t, 2), 'lands': abs(found - t) <= 0.5 and abs(delta) >= 1.5})
        r['sync'] = hits
        want_key = re.search(r'\b([A-G][#b]?) (major|minor|Lydian|Dorian|Mixolydian)', c.get('prompt', '')); want_bpm = re.search(r'(\d{2,3}) ?bpm', c.get('prompt', ''))
        est, conf, _ = key_estimate(x); bpm = tempo_estimate(x)
        r['key'] = {'requested': want_key.group(0) if want_key else None, 'estimated': est, 'corr': conf,
                    'match': key_matches(est, want_key.group(0)) if want_key else None}
        r['tempo'] = {'requested_bpm': int(want_bpm.group(1)) if want_bpm else None, 'estimated_bpm': bpm,
                      'match': (min(abs(bpm - int(want_bpm.group(1)) * k) for k in (0.5, 1, 2)) <= 4) if want_bpm else None}
        e_ = envelope(x); r['first_0_5s_vs_cue_db'] = round(float(e_[:50].max() - np.median(e_)), 1)
        r['flags'] = []
        if r['ends_early']: r['flags'].append(f"ends early: {m['dur']} s for a {win:.1f} s window")
        if m['clip_runs']: r['flags'].append(f"clipped runs {m['clip_runs']}")
        r['holes_in_window'] = [h for h in m['holes'] if h[0] < win]  # holes in the +3 s spare tail are never heard
        if r['holes_in_window']: r['flags'].append(f"holes inside the window {r['holes_in_window'][:4]}")
        if m['voice']['vad_speech_s'] >= 1.0 and m['voice']['text']: r['flags'].append(f"voice-like content {m['voice']['vad_speech_s']} s: '{m['voice']['text'][:80]}'")
        if not r['energy_order_ok']: r['flags'].append(f"energy labels not in order: {mean}")
        if m['lead_s'] > 0.15: r['flags'].append(f"starts late: {m['lead_s']} s")
        miss = [h for h in hits if not h['lands']]
        if miss: r['flags'].append(f"{len(miss)} of {len(hits)} planned events do not land within 0.5 s")
        if r['key']['match'] is False: r['flags'].append(f"key: asked {r['key']['requested']}, sounds like {r['key']['estimated']} (corr {r['key']['corr']})")
        if r['tempo']['match'] is False: r['flags'].append(f"tempo: asked {r['tempo']['requested_bpm']} bpm, measured about {r['tempo']['estimated_bpm']}")
        res.append(r)
        print(f"{c['id']:34s} {m['dur']:6.1f}/{win:5.1f} s LUFS {m['lufs']:6.1f} TP {m['true_peak_db']:5.1f} lead {m['lead_s']:.2f} cen {m['centroid_hz']:5d} "
              f"pres {m['bands_db']['presence']:5.1f} spread {r['section_spread_lu']:4.1f} sync {sum(h['lands'] for h in hits)}/{len(hits)} vad {m['voice']['vad_speech_s']}"
              + (' | ' + '; '.join(r['flags']) if r['flags'] else ''), flush=True)
    json.dump(res, open(a.out, 'w'), indent=1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['sfx', 'music']); ap.add_argument('done'); ap.add_argument('spot'); ap.add_argument('out')
    ap.add_argument('--expect'); ap.add_argument('--asr', default='small.en')
    a = ap.parse_args()
    run_sfx(a) if a.mode == 'sfx' else run_music(a)

if __name__ == '__main__':
    main()
