#!/usr/bin/env python3
"""audio_scan.py MIX_JSON FINAL_MIX_WAV TIMING_JSON OUT_JSON
Rebuilds the buses with mix.build() (VO, ducked music, SFX + ambience), scales them by the same loudness gain as the final mix,
and reports what a listener could trip over:
  - masking:   speech windows where music+SFX come within 8 dB of the voice
  - sfx_loud:  SFX hits louder than the voice's typical level by more than 3 dB
  - dead_air:  > 1.2 s where voice, music and SFX are all quiet (mid-film)
  - vo_cuts:   abrupt voice offsets/onsets (a word tail or onset chopped by take trimming)
  - clicks:    sample discontinuities in quiet passages of the final mix
  - music_cues: every cue with its window and fades, and the gaps/overlaps between consecutive cues
  - pacing:    words per minute per 30 s window and narration pauses > 1.2 s (from TIMING_JSON)
Levels are dBFS of the final mix scale."""
import json, sys
import numpy as np, soundfile as sf, pyloudnorm as pyln
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from mix import load, db, SR, build

def rms_db(x, win, hop):
    x = x.astype(np.float64)
    if x.ndim == 2: x = x.mean(axis=1)
    c = np.convolve(x ** 2, np.ones(win) / win, 'same')[::hop]
    return 10 * np.log10(c + 1e-12)

def main():
    spec = json.load(open(sys.argv[1])); final = sys.argv[2]; timing = json.load(open(sys.argv[3])); outp = sys.argv[4]
    N = int(spec['duration'] * SR)
    # buses rebuilt by mix.build() itself (2026-11-09), so every mix.py key counts: norm_lufs, offsets, trims, loops, EQ, the
    # ambience bus and its duck, dips. Before this, the scan rebuilt ep01-style buses and ignored dips. The ambience bus is
    # counted with the SFX bus ("sfx" levels below = SFX + ambience).
    B = build(spec)
    vo = B['vo'][:, 0].copy(); bus_m = B['music']; bus_s = B['sfx'] + B['amb']
    en = [m for m in spec.get('music', []) if m.get('enabled', True) is True]
    cues = [{'file': m['file'].rsplit('/', 1)[-1], 'start': m['start'], 'end': m['end'], 'audio_ends_at': round(c['audio_ends_at'], 2),
             'ends_early': c['ends_early'], 'fade_in': m.get('fade_in', 1.0), 'fade_out': m.get('fade_out', 2.0), 'gain_db': m.get('gain_db')}
            for m, c in zip(en, B['cues'])]
    mix = np.stack([vo, vo], 1) + bus_m + bus_s
    meter = pyln.Meter(SR); lg = db(spec.get('target_lufs', -14) - meter.integrated_loudness(mix.astype(np.float64)))
    vo *= lg; bus_m *= lg; bus_s *= lg

    # 50 ms windows
    W, H = 2400, 2400
    Lv, Lm, Ls = rms_db(vo, W, H), rms_db(bus_m, W, H), rms_db(bus_s, W, H)
    Lb = 10 * np.log10(10 ** (Lm / 10) + 10 ** (Ls / 10))
    t = np.arange(len(Lv)) * H / SR
    speech = Lv > -40
    vo_typ = float(np.median(Lv[speech]))
    def runs(mask, min_len):
        out, i = [], 0
        while i < len(mask):
            if mask[i]:
                j = i
                while j < len(mask) and mask[j]: j += 1
                if (j - i) * H / SR >= min_len: out.append([round(t[i], 2), round(t[min(j, len(t) - 1)], 2), i, j])
                i = j
            else: i += 1
        return out
    mask_m = speech & (Lv - Lb < 8)
    masking = [{'t0': a, 't1': b, 'min_margin_db': round(float((Lv[i:j] - Lb[i:j]).min()), 1)} for a, b, i, j in runs(mask_m, 0.3)]
    sfx_loud = []
    for a, b, i, j in runs(Ls > vo_typ + 3, 0.05):
        sfx_loud.append({'t0': a, 't1': b, 'peak_db': round(float(Ls[i:j].max()), 1), 'vs_voice_db': round(float(Ls[i:j].max() - vo_typ), 1)})
    quiet = (Lv < -50) & (Lb < -45)
    dead = [{'t0': a, 't1': b} for a, b, i, j in runs(quiet, 1.2) if 2 < a < spec['duration'] - 3]

    # abrupt voice offsets / onsets on a 2 ms envelope
    w2, h2 = 240, 96
    E = rms_db(vo, w2, h2); te = np.arange(len(E)) * h2 / SR
    vo_cuts = []
    k = 8  # 8 hops = 16 ms
    for i in range(k, len(E) - k):
        if E[i - 1] > -32 and E[i + k] < E[i - 1] - 30 and E[i:i + k].max() < E[i - 1] + 1 and E[i + k] < -60:
            if not vo_cuts or te[i] - vo_cuts[-1]['t'] > 0.2:
                vo_cuts.append({'t': round(te[i], 3), 'kind': 'offset', 'before_db': round(float(E[i - 1]), 1), 'after_db': round(float(E[i + k]), 1)})
        if E[i + 1] > -32 and E[i - k] < E[i + 1] - 30 and E[i - k] < -60 and (E[i + 1] - E[i - 2]) > 25:
            if not vo_cuts or te[i] - vo_cuts[-1]['t'] > 0.2:
                vo_cuts.append({'t': round(te[i], 3), 'kind': 'onset', 'before_db': round(float(E[i - k]), 1), 'after_db': round(float(E[i + 1]), 1)})

    # clicks in the final mix: |x[n]-x[n-1]| far above the local 5 ms RMS in quiet passages
    fm, fsr = sf.read(final, dtype='float32')
    x = fm.mean(axis=1) if fm.ndim == 2 else fm
    dx = np.abs(np.diff(x))
    loc = np.sqrt(np.convolve(x.astype(np.float64) ** 2, np.ones(240) / 240, 'same'))[1:]
    cand = np.where((dx > 0.05) & (dx > 12 * loc))[0]
    clicks = []
    for c in cand:
        tt = round(c / fsr, 3)
        if not clicks or tt - clicks[-1]['t'] > 0.05: clicks.append({'t': tt, 'jump': round(float(dx[c]), 3), 'local_rms': round(float(loc[c]), 4)})

    # music cue gaps / overlaps
    cs = sorted(cues, key=lambda c: c['start'])
    trans = []
    for a, b in zip(cs, cs[1:]):
        trans.append({'from': a['file'], 'to': b['file'], 'a_end': a['audio_ends_at'], 'b_start': b['start'],
                      'gap_s': round(b['start'] - a['audio_ends_at'], 2), 'a_fade_out': a['fade_out'], 'b_fade_in': b['fade_in']})

    # narration pacing
    words = timing['words']
    wpm = []
    for s in range(0, int(spec['duration']), 30):
        nw = sum(1 for w in words if s <= w['start'] < s + 30)
        wpm.append({'t0': s, 'wpm': nw * 2})
    pauses = []
    for a, b in zip(words, words[1:]):
        gap = b['start'] - a['end']
        if gap > 1.2: pauses.append({'after_word': a.get('word', a.get('w')), 't0': round(a['end'], 2), 't1': round(b['start'], 2), 'gap': round(gap, 2)})
    per_sec = [{'t': s, 'voice_db': round(float(Lv[s * 20:(s + 1) * 20].max()), 1), 'music_db': round(float(Lm[s * 20:(s + 1) * 20].mean()), 1),
                'sfx_db': round(float(Ls[s * 20:(s + 1) * 20].max()), 1)} for s in range(int(len(Lv) / 20))]
    out = {'voice_typical_db': round(vo_typ, 1), 'masking': masking, 'sfx_loud': sfx_loud, 'dead_air': dead, 'vo_cuts': vo_cuts,
           'clicks': clicks[:300], 'clicks_total': len(clicks), 'music_cues': cues, 'music_transitions': trans, 'wpm_30s': wpm,
           'narration_pauses_over_1_2s': pauses, 'levels_per_second': per_sec}
    json.dump(out, open(outp, 'w'), indent=1)
    print(f'voice typ {vo_typ:.1f} dB; masking {len(masking)}; sfx_loud {len(sfx_loud)}; dead_air {len(dead)}; vo_cuts {len(vo_cuts)}; '
          f'clicks {len(clicks)}; cues {len(cues)} (ending early {sum(c["ends_early"] for c in cues)}); pauses>1.2s {len(pauses)}')

if __name__ == '__main__':
    main()
