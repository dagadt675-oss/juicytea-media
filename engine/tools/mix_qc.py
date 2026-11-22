#!/usr/bin/env python3
"""mix_qc.py MIX_JSON FINAL_WAV STEMS_DIR TIMING_JSON OUT_JSON
Measures a finished mix against PLAYBOOK_craft section 11 and the ep02 sound principles (R1-R4, R12, R16, R18, R22),
on the real files: the final mix and the four stems that mix.py --stems writes (vo, music, sfx, amb as .wav, or losslessly packed .flac; they carry the same
loudness and limiter gain as the mix, so they sum to it). Prints a PASS/FAIL table and writes every number to OUT_JSON.

Checks (gate in brackets; [info] = reported, no gate):
  loudness     ffmpeg ebur128 peak=true on the final: integrated -14 +-0.5 LU, true peak <= -1.5 dBTP, LRA [info]
  clipping     samples at or above 0 dBFS in the final (0)
  silence      ffmpeg silencedetect -45 dB, 0.3 s on the final, ignoring the first and last 0.5 s (none)
  stems_sum    max |vo+music+sfx+amb - final| (<= 1e-3, 24-bit rounding)
  vo_music     3 s short-term K-weighted loudness, voice minus music, over windows that are >= 60 % narration (timing.json
               words): p10 >= 15 LU, median 17-23 LU; also voice minus ambience (p10 >= 15) and voice minus music+ambience
  segments     voice minus music per narration sentence (timing.json segments, K-weighted mean square): min >= 12 LU
  band_1_4k    voice minus music+sfx+amb in the 1-4 kHz band, 100 ms windows inside words: >= 15 dB in >= 95 % of windows
  momentary    400 ms windows inside words where music+amb come within 10 LU of the voice (count, [info])
  pumping      speech gaps of 0.25-1.5 s in which the music duck rises >= 4 dB (<= 2 per minute)
  reveals      breathing room before each reveal in spec.qc.reveals: the longest narration pause in the 4 s before the word, and
               the music drop (quietest 300 ms in those 4 s against the median of the 8 s before) and the clear room (voice over the 4 s
               before minus music over the last 1.5 s); pass with a pause >= 0.5 s, a music drop >= 6 dB or a clear room >= 25 LU
  holes        music stem under -60 dBFS for >= 0.3 s mid-film [info: compare with spec.qc.intended_music_holes]
  hush         SFX one-shots starting inside spec.qc.hush windows (0; ambience-level swells of bed material are listed, not gated)
  comic        comic SFX that overlap the next narration word (0)
  density      one-shots per minute [info] and in any 10 s (<= 7); same file more than twice in 60 s (0)
"""
import json, subprocess, sys, re, os
import numpy as np, soundfile as sf
from scipy.signal import lfilter, butter, sosfiltfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mix import load, db, SR, vo_activity, duck_gain

KB1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
KB2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])

def kpow(x):
    """K-weighted power summed over channels (BS.1770 at 48 kHz)."""
    y = lfilter(*KB2, lfilter(*KB1, x.astype(np.float64), axis=0), axis=0)
    return (y ** 2).sum(axis=1) if y.ndim == 2 else y ** 2

def win_lufs(p, w, hop):
    c = np.concatenate([[0.0], np.cumsum(p)]); idx = np.arange(0, len(p) - w, hop)
    return -0.691 + 10 * np.log10((c[idx + w] - c[idx]) / w + 1e-15), idx

def seg_lufs(p, a, b):
    a, b = int(a * SR), int(b * SR)
    return -0.691 + 10 * np.log10(p[a:b].mean() + 1e-15) if b > a else -150.0

def ffmpeg_stats(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    s = r[r.rfind('Summary'):]
    g = lambda k: float(re.search(k + r':\s+(-?[\d.]+)', s).group(1))
    out = {'integrated_lufs': g('I'), 'lra_lu': g('LRA'), 'true_peak_dbtp': g('Peak')}
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'silencedetect=n=-45dB:d=0.3', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r)]; en = [float(x) for x in re.findall(r'silence_end: (-?[\d.]+)', r)]
    out['silences'] = [[round(a, 2), round(b, 2)] for a, b in zip(st, en + [None] * (len(st) - len(en))) if b is None or b > 0]
    return out

def runs(mask, t, min_len):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            if t[min(j, len(t) - 1)] - t[i] >= min_len: out.append([round(float(t[i]), 2), round(float(t[min(j, len(t) - 1)]), 2)])
            i = j
        else: i += 1
    return out

def main():
    spec_p, final_p, stems, timing_p, outp = sys.argv[1:6]
    spec = json.load(open(spec_p)); timing = json.load(open(timing_p)); qc = spec.get('qc', {})
    dur = spec['duration']; res = {}; gates = []
    def gate(name, ok, value, rule): gates.append({'check': name, 'pass': bool(ok), 'value': value, 'rule': rule})

    # --- final file
    fs = ffmpeg_stats(final_p); res['final'] = fs
    fin, fsr = sf.read(final_p, dtype='float32'); assert fsr == SR
    clip = int((np.abs(fin) >= 0.99997).sum()); res['final']['clipped_samples'] = clip
    res['final']['sample_peak_dbfs'] = round(float(20 * np.log10(np.abs(fin).max())), 2)
    sil = [s for s in fs['silences'] if s[0] > 0.5 and (s[1] is None or s[1] < dur - 0.5)]
    gate('integrated', abs(fs['integrated_lufs'] + 14) <= 0.5, fs['integrated_lufs'], '-14 +-0.5 LUFS')
    gate('true_peak', fs['true_peak_dbtp'] <= -1.5, fs['true_peak_dbtp'], '<= -1.5 dBTP')
    gate('clipping', clip == 0, clip, '0 samples at 0 dBFS')
    gate('silence', not sil, sil, 'no -45 dB / 0.3 s silence mid-film')

    # --- stems
    stem = lambda k: next(p for p in (os.path.join(stems, f'{k}.wav'), os.path.join(stems, f'{k}.flac')) if os.path.exists(p))
    S = {k: sf.read(stem(k), dtype='float32')[0] for k in ('vo', 'music', 'sfx', 'amb')}
    n = min(len(fin), *(len(x) for x in S.values()))
    diff = float(np.abs(S['vo'][:n] + S['music'][:n] + S['sfx'][:n] + S['amb'][:n] - fin[:n]).max())
    gate('stems_sum', diff <= 1e-3, round(diff, 6), 'stems sum to the mix')
    P = {k: kpow(v[:n]) for k, v in S.items()}
    P['bed'] = kpow(S['music'][:n] + S['amb'][:n]); P['bg'] = kpow(S['music'][:n] + S['amb'][:n] + S['sfx'][:n])
    del fin

    # narration mask from timing words (100 Hz)
    words = timing['words']; m100 = np.zeros(int(dur * 100) + 1, bool)
    for w in words: m100[int(w['start'] * 100):int(w['end'] * 100)] = True

    # --- 3 s short-term
    W, H = 3 * SR, SR
    L = {k: win_lufs(P[k], W, H)[0] for k in ('vo', 'music', 'amb', 'bed')}
    idx = win_lufs(P['vo'], W, H)[1]
    frac = np.array([m100[i // 480:(i + W) // 480].mean() for i in idx])
    sp = (frac >= 0.6) & (L['vo'] > -40)
    def stats(d):
        d = d[np.isfinite(d)]
        return {'median': round(float(np.median(d)), 1), 'p10': round(float(np.percentile(d, 10)), 1), 'p90': round(float(np.percentile(d, 90)), 1),
                'min': round(float(d.min()), 1), 'n': int(len(d))}
    res['vo_minus_music_3s'] = stats((L['vo'] - L['music'])[sp]); res['vo_minus_amb_3s'] = stats((L['vo'] - L['amb'])[sp])
    res['vo_minus_bed_3s'] = stats((L['vo'] - L['bed'])[sp])
    vm = res['vo_minus_music_3s']
    gate('vo_music_p10', vm['p10'] >= 15, vm['p10'], 'voice minus music >= 15 LU in 90% of speech windows')
    gate('vo_music_median', 17 <= vm['median'] <= 23, vm['median'], 'median 17-23 LU')
    gate('vo_amb_p10', res['vo_minus_amb_3s']['p10'] >= 15, res['vo_minus_amb_3s']['p10'], 'voice minus ambience >= 15 LU in 90%')

    # --- per narration segment
    segs = []
    for s in timing['segments']:
        v, mu, be = seg_lufs(P['vo'], s['start'], s['end']), seg_lufs(P['music'], s['start'], s['end']), seg_lufs(P['bed'], s['start'], s['end'])
        segs.append({'seg': s['id'], 't0': s['start'], 't1': s['end'], 'vo': round(v, 1), 'vo_minus_music': round(v - mu, 1), 'vo_minus_bed': round(v - be, 1)})
    segs.sort(key=lambda x: x['vo_minus_music'])
    res['segments_worst10'] = segs[:10]
    res['segments_vo_minus_music'] = stats(np.array([x['vo_minus_music'] for x in segs]))
    gate('segments_min', segs[0]['vo_minus_music'] >= 12, segs[0]['vo_minus_music'], 'every sentence: voice >= 12 LU over music')

    # --- 1-4 kHz band, 100 ms windows inside words
    sos = butter(4, [1000, 4000], 'bandpass', fs=SR, output='sos')
    vb = sosfiltfilt(sos, S['vo'][:n].mean(1).astype(np.float64))
    bb = sosfiltfilt(sos, (S['music'][:n] + S['sfx'][:n] + S['amb'][:n]).mean(1).astype(np.float64))
    w = SR // 10
    Lv = 10 * np.log10(np.add.reduceat(vb ** 2, np.arange(0, n - w, w)) / w + 1e-15)
    Lb = 10 * np.log10(np.add.reduceat(bb ** 2, np.arange(0, n - w, w)) / w + 1e-15)
    k = min(len(Lv), len(Lb)); tw = np.arange(k) * 0.1
    inw = np.array([m100[int(t * 100):int(t * 100) + 10].mean() > 0.8 for t in tw])
    spb = inw & (Lv[:k] > np.median(Lv[:k][inw]) - 10)
    mb = (Lv[:k] - Lb[:k])[spb]
    res['band_1_4k'] = {'windows': int(spb.sum()), 'median_db': round(float(np.median(mb)), 1), 'p5_db': round(float(np.percentile(mb, 5)), 1),
                        'pct_below_15': round(100 * float((mb < 15).mean()), 1), 'pct_below_10': round(100 * float((mb < 10).mean()), 1)}
    low = runs(spb & ((Lv[:k] - Lb[:k]) < 10), tw, 0.1)
    res['band_1_4k']['under_10db_runs'] = low[:40]
    gate('band_1_4k', res['band_1_4k']['pct_below_15'] <= 5, res['band_1_4k']['pct_below_15'], '<= 5% of speech windows under 15 dB at 1-4 kHz')

    # --- momentary 400 ms
    Mv, mi = win_lufs(P['vo'], int(0.4 * SR), int(0.1 * SR)); Mb, _ = win_lufs(P['bed'], int(0.4 * SR), int(0.1 * SR))
    tm = mi / SR; inm = np.array([m100[int(t * 100):int(t * 100) + 40].mean() > 0.9 for t in tm]) & (Mv > -35)
    close = runs(inm & ((Mv - Mb) < 10), tm, 0.1)
    res['momentary_bed_within_10LU'] = {'count': len(close), 'runs': close[:40]}

    # --- pumping (rebuild the duck control from the raw voice, exactly as mix.py does)
    d = spec.get('duck', {'db': -8, 'attack': 0.06, 'release': 0.45})
    vraw = load(spec['vo'], 1)[:, 0] * db(spec.get('vo_gain_db', 0)); N = int(dur * SR)
    vr = np.zeros(N, np.float32); vr[:min(N, len(vraw))] = vraw[:N]
    act = vo_activity(vr, d); g = duck_gain(act, d, N)[::480]; gdb = 20 * np.log10(np.maximum(g, 1e-6))
    pumps, kk = [], 0
    while kk < len(act):
        if act[kk] == 0:
            j = kk
            while j < len(act) and act[j] == 0: j += 1
            if 0.25 <= (j - kk) / 100 <= 1.5 and kk > 0 and j < len(act) and gdb[kk:j].max() - gdb[kk] >= 4: pumps.append(round(kk / 100, 2))
            kk = j
        else: kk += 1
    ppm = len(pumps) / (dur / 60)
    res['pumping'] = {'events': len(pumps), 'per_min': round(ppm, 2), 'times': pumps[:60]}
    gate('pumping', ppm <= 2, round(ppm, 2), '<= 2 duck pumps per minute')

    # --- reveals: narration pause before the word and music drop
    musp = kpow(S['music'][:n]); rev = []
    wm3 = int(0.3 * SR); mus300, i300 = win_lufs(musp, wm3, wm3 // 3); t300 = (i300 + wm3 / 2) / SR
    for r in qc.get('reveals', []):
        t = r['t']
        gaps = [(a['end'], b['start']) for a, b in zip(words, words[1:]) if t - 4.0 <= b['start'] <= t + 0.01 and b['start'] - a['end'] >= 0.05]
        pause = max([round(b - a, 2) for a, b in gaps], default=0.0)
        sel = (t300 >= t - 4.0) & (t300 <= t - 0.05); ref_sel = (t300 >= t - 12.0) & (t300 < t - 4.0)
        low = float(mus300[sel].min()) if sel.any() else -150.0; ref = float(np.median(mus300[ref_sel])) if ref_sel.any() else -150.0
        drop = round(ref - low, 1)
        room = round(seg_lufs(P['vo'], t - 4.0, t) - seg_lufs(musp, t - 1.5, t - 0.05), 1)
        ok = pause >= 0.5 or drop >= 6 or room >= 25
        rev.append({'name': r['name'], 't': t, 'longest_pause_in_4s_before': pause, 'music_min_300ms_in_4s_before_lufs': round(low, 1),
                    'music_median_12_to_4s_before_lufs': round(ref, 1), 'music_drop_db': drop,
                    'vo_minus_music_last_1.5s_lu': room, 'breathing_room': bool(ok)})
    res['reveals'] = rev
    bad = [x['name'] for x in rev if not x['breathing_room']]
    gate('reveals', not bad, bad, 'pause >= 0.5 s, music drop >= 6 dB or music >= 25 LU under the voice before every reveal')

    # --- music holes
    wm = SR // 20; ml = 10 * np.log10(np.add.reduceat(S['music'][:n].mean(1).astype(np.float64) ** 2, np.arange(0, n - wm, wm)) / wm + 1e-15)
    th = np.arange(len(ml)) * 0.05
    holes = [h for h in runs(ml < -60, th, 0.3) if 1 < h[0] < dur - 1]
    res['music_holes'] = holes; res['music_holes_intended'] = qc.get('intended_music_holes')

    # --- events: hush, comic, density, repeats
    evs = [e for e in spec.get('sfx', []) if e.get('enabled', True) is True and not (spec.get('strict') and e.get('strict_off')) and e.get('bus', 'sfx') == 'sfx']
    hush = [[e['id'], e['asset'], e['t'], h[2]] for e in evs for h in qc.get('hush', []) if h[0] <= e['t'] < h[1] and e.get('kind') != 'swell']
    res['hush_violations'] = hush
    res['hush_ambience_swells'] = [[e['id'], e['asset'], e['t'], h[2]] for e in evs for h in qc.get('hush', []) if h[0] <= e['t'] < h[1] and e.get('kind') == 'swell']
    gate('hush', not hush, hush, 'no SFX one-shot inside a hush window')
    comic = []
    for e in evs:
        if e['id'] not in qc.get('comic_ids', []): continue
        length = e.get('dur') or sf.info(e['file']).duration
        cand = [w for w in words if w['start'] < e['t'] + length and w['end'] > e['t'] + 0.05]
        if cand: comic.append({'id': e['id'], 't': e['t'], 'len': round(length, 2), 'overlaps': [c['w'] for c in cand]})
    res['comic_overlaps'] = comic
    gate('comic', not comic, comic, 'comic SFX sit in gaps, never on a word')
    ts = sorted(e['t'] for e in evs)
    per_min = [sum(1 for t in ts if m * 60 <= t < (m + 1) * 60) for m in range(int(dur // 60) + 1)]
    max10 = max(sum(1 for t in ts if a <= t < a + 10) for a in np.arange(0, dur, 0.5))
    res['density'] = {'one_shots': len(ts), 'per_minute': per_min, 'max_in_10s': int(max10)}
    gate('density_10s', max10 <= 7, int(max10), '<= 7 one-shots in any 10 s')
    reps = []
    byf = {}
    for e in evs: byf.setdefault((e['file'], e.get('pitch_st', 0), e.get('src_in', 0)), []).append(e['t'])
    for f, tt in byf.items():
        tt.sort()
        for i in range(len(tt) - 2):
            if tt[i + 2] - tt[i] < 60: reps.append([os.path.basename(f[0]), tt[i], tt[i + 2]])
    res['identical_3x_in_60s'] = reps
    gate('repeats', not reps, reps, 'no identical sound more than twice in 60 s')

    res['gates'] = gates; res['pass'] = all(g_['pass'] for g_ in gates)
    json.dump(res, open(outp, 'w'), indent=1)
    for g_ in gates: print(f"{'PASS' if g_['pass'] else 'FAIL'}  {g_['check']:<16} {json.dumps(g_['value'])[:90]:<92} ({g_['rule']})")
    print('vo-music 3s', res['vo_minus_music_3s'], '| vo-amb', res['vo_minus_amb_3s'], '| vo-bed', res['vo_minus_bed_3s'])
    print('band', {k: v for k, v in res['band_1_4k'].items() if k != 'under_10db_runs'}, '| momentary close', res['momentary_bed_within_10LU']['count'])
    print('loudness', {k: v for k, v in res['final'].items() if k != 'silences'})
    for r in rev: print('reveal', r)
    print('music holes', holes)
    print('OVERALL', 'PASS' if res['pass'] else 'FAIL')

if __name__ == '__main__':
    main()
