#!/usr/bin/env python3
"""build_mix.py SOUND_DIR TIMING_JSON VO_PROC_WAV OUT_JSON [--strict] [--norm -16] [--duck -12]
Builds the ep02 mix spec for engine/tools/mix.py from the spotting session (re-recording mixer pass, 2026-11-09).

Inputs in SOUND_DIR (scratchpad audio/ep02_sound): spot_sfx.json, spot_music.json (built by build_spot.py from TIMING_JSON),
sfx/selected.json (chosen take per asset with its measured sync point and level) and music/selected.json (chosen cue files).
The spot files must be built on the same timing.json (md5 check), so every time stays marker-accurate.

What it does on top of the spot:
- Places every generated SFX by its measured sync point (spot_notes section 14): the film time of the sync point stays where the
  spot put it (t + design_sync - src_in); a file whose sync comes earlier than designed starts later; a file with a longer
  pre-roll than designed keeps at most 0.7 s extra pre-roll (the rest is trimmed with src_in and a short fade-in). Comic sounds
  never start earlier than spotted, and no start moves into a restraint window it was not in. 'dur' keeps the spotted tail
  after the sync point.
- Adds the measured level correction (-level_vs_norm_db) where the peak cap left a file under the -20 LUFS convention.
- Puts beds on the ambience bus (own duck), everything else on the SFX bus.
- Music: loudness-matches every cue (norm_lufs), equal-power fades, the measured offsets (M05 bloom on "up", M12's own stop on the
  payoff dropout, M14 back-timed to the last frame), stop-downs with 30-40 ms ramps, gag dips with 0.25 s ramps, solemn dips
  with 1 s ramps, nested Nihoa dips (no bump between -3 and -6).
- Writes a 'qc' block (reveals, restraint windows, comic ids, cards) that engine/tools/mix_qc.py reads; mix.py ignores it."""
import argparse, hashlib, json

MUSIC_OVR = {
    # skip 0.5 s of the 0.68 s silent lead so the 2 s fade-in acts on sound
    'M02_halape_1975_night': {'offset': 0.5},
    # the sound producer's measure: the biggest rise lands on "up" (191.39 s) with a 0.16 s offset
    'M05_island_stands_up': {'offset': 0.16},
    # the composition-plan take stops by itself at file 77.80 s (-13 dB to -34 dB within 0.25 s); delaying the cue 1.12 s puts
    # that stop on the planned payoff dropout (677.89 s) together with the riser; a 60 ms fade only cleans the cut
    'M12_newborn_and_descent': {'offset': -1.12, 'fade_out': 0.06},
    # natural end (last sample above -60 dBFS) on the last frame; a 0.5 s fade on the last note's release only
    'M14_refill_theme_finale': {'back_time': True, 'fade_out': 0.5},
}

# per-event decisions that the generic rule cannot make (id: changes, reason)
EVENT_OVR = {
    'x079': ({'t': 245.83, 'src_in': 2.3, 'dur': 0.62, 'fade_in': 0.06, 'fade_out': 0.15},
             'jeep_climb peaks at its last sample (2.97 s): play its loudest 0.62 s under the road shot and stop at the whip back '
             '(246.45), before the flag-droop gag in the gap'),
    'x045': ({'fade_out': 0.08}, 'rubble_emerge peaks on its last sample: an 80 ms fade avoids a hard cut on "field"'),
}
EXTRA_PREROLL = 0.7
# (marker of the reveal word, thin start, why): reveals that sit mid-sentence with no pause or stop-down in the 4 s before them
REVEAL_THINS = [
    ('tall33', 232.3, -10, 0.25, 'the music falls away under "thirty-three thousand feet" and comes back with the hit on "tall"'),
]
# gain trims after the 1-4 kHz speech-band check (mix_qc band_1_4k, tools/band_events.py): broadband water and wind one-shots
# that sat on narration words at or above the voice in the speech band
EVENT_GAIN = {
    'x004': (-3, 'water rush peaks on "Maui" (band margin -1.6 dB)'),
    'x019': (-5, 'water rush peaks on "drowned" (band margin -6.1 dB)'),
    'x076': (-3, 'Everest summit wind under "On Everest, getting to the top" (1.4 dB)'),
    'x100': (-6, 'wave wash under "Waves had carved it ... centuries" (-1.7 dB; still 14.7 dB after -4)'),
    'x059': (-4, 'drain start v2 (+5.6 dB level fix) under "all the way down": 1-4 kHz margin 10.1 dB, broadband 19 dB over the voice'),
    'x153': (-3, 'radio pulse on "plain language" (-0.6 dB)'),
    'x162': (-3, 'drain flow swell under "every island has drowned" (2.2 dB)'),
    'x149': (-3, 'radio-room static bed under 37 s of dense AF narration (hiss in the speech band)'),
}


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sound'); ap.add_argument('timing'); ap.add_argument('vo'); ap.add_argument('out')
    ap.add_argument('--strict', action='store_true', help='switch off the AF-ruse gag sounds (owner decision 1)')
    ap.add_argument('--norm', type=float, default=-16.0, help='music cue loudness before gain_db (LUFS)')
    ap.add_argument('--duck', type=float, default=-12.0, help='music duck depth under the voice (dB)')
    ap.add_argument('--amb-duck', type=float, default=-6.0, help='ambience duck depth under the voice (dB)')
    ap.add_argument('--tp', type=float, default=-1.7, help='limiter true-peak ceiling (dBTP)')
    ap.add_argument('--band-db', type=float, default=-15.0, help='extra speech-band cut on the ambience bus under the voice (dB)')
    ap.add_argument('--band-lo', type=float, default=600.0); ap.add_argument('--band-hi', type=float, default=7000.0)
    ap.add_argument('--sfx-band-db', type=float, default=-8.0, help='speech-band cut on the SFX bus while the voice speaks (dB)')
    a = ap.parse_args()
    S = a.sound
    spot_s = json.load(open(f'{S}/spot_sfx.json')); spot_m = json.load(open(f'{S}/spot_music.json'))
    sel_s = json.load(open(f'{S}/sfx/selected.json')); sel_m = {c['id']: c for c in json.load(open(f'{S}/music/selected.json'))['cues']}
    timing = json.load(open(a.timing)); mk = timing['markers']
    h = md5(a.timing)
    assert h == spot_s['meta']['timing_md5'] == spot_m['meta']['timing_md5'], f'timing.json changed ({h}): re-run build_spot.py first'
    dur = spot_s['meta']['film_end_s']

    # ---- music
    music = []
    for c in spot_m['cues']:
        s = sel_m[c['id']]
        m = {'id': c['id'], 'file': s['file'], 'start': c['t_in'], 'end': c['t_out'], 'gain_db': c['gain_db'],
             'fade_in': c['fade_in'], 'fade_out': c['fade_out'], 'offset': c.get('offset', 0.0), 'curve': 'eqp', 'norm_lufs': a.norm,
             'raw_lufs': s.get('raw_lufs'), 'transition_in': c.get('transition_in'), 'transition_out': c.get('transition_out')}
        m.update(MUSIC_OVR.get(c['id'], {}))
        music.append(m)

    # ---- dips: stop-downs fast, gags 0.25 s, solemn 1 s; adjacent same-sign dips nested so the level steps without a bump
    raw = sorted([list(d) for d in spot_m['dips']], key=lambda d: d[0])
    dips = []
    for i, (t0, t1, ddb, note) in enumerate(raw):
        if ddb <= -20: r = {'ramp_in': 0.04, 'ramp_out': 0.03}
        elif ddb <= -9: r = {'ramp': 0.25}
        else: r = {'ramp': 1.0}
        nxt = raw[i + 1] if i + 1 < len(raw) else None
        prv = raw[i - 1] if i > 0 else None
        if nxt and abs(nxt[0] - t1) < 0.01 and -9 < ddb < 0 and -9 < nxt[2] < 0:
            dips.append({'t0': t0, 't1': nxt[1], 'db': ddb, 'ramp': 1.0, 'note': note + ' (spans the next step)'})
            continue
        if prv and abs(prv[1] - t0) < 0.01 and -9 < ddb < 0 and -9 < prv[2] < 0:
            dips.append({'t0': t0, 't1': t1, 'db': ddb - prv[2], 'ramp': 1.0, 'note': note + f' (nested: {prv[2]} + {ddb - prv[2]} = {ddb} dB)'})
            continue
        dips.append({'t0': t0, 't1': t1, 'db': ddb, **r, 'note': note})
    for t0, t1, ddb, note in spot_m.get('lifts', []):
        dips.append({'t0': t0, 't1': t1, 'db': ddb, 'ramp': 1.5, 'note': note})
    # breathing room before mid-sentence reveals that have no narration pause and no stop-down in the 4 s before the word:
    # the music thins 6 dB from the comma before the number and comes back with the hit (mixer pass 2026-11-09)
    for name, t0, ddb, rin, why in REVEAL_THINS:
        t1 = mk[name]['start'] - 0.06
        dips.append({'t0': t0, 't1': t1, 'db': ddb, 'ramp_in': rin, 'ramp_out': 0.05, 'note': f'reveal thin before {name}: {why}'})

    # ---- events
    windows = [(w['t0'], w['t1'], w['what']) for w in spot_s['restraint']]
    sfx, amb, log = [], [], []
    for e in spot_s['events']:
        asset = spot_s['assets'][e['asset']]
        out = {k: e[k] for k in ('id', 'kind', 'asset', 'marker', 'seg', 'job', 'enabled', 'strict_off', 'pitch_st', 'eq',
                                 'loop', 'fade_in', 'fade_out', 'src_in', 'dur', 't_out') if k in e}
        out['t'] = e['t']; out['gain_db'] = e['gain_db']
        if asset['source'] == 'library':
            out['file'] = asset['file']
        else:
            sa = sel_s[e['asset']]
            vi = e.get('variant', 0)
            v = next(x for x in sa['variants'] if x['variant'] == vi)
            out['file'] = v['file']; out['variant'] = vi
            lvl = -v['level_vs_norm_db']
            if lvl: out['gain_db'] = round(e['gain_db'] + lvl, 2); out['level_fix_db'] = lvl
            if e['kind'] != 'bed' and sa.get('kind') != 'bed':  # bed material used as a swell keeps its spotted src_in
                D, M = sa['design_sync_s'], v['sync_s_measured']; s_d = e.get('src_in', 0.0)
                sync_t = e['t'] + D - s_d
                want = max(0.0, D - s_d)
                if M <= want: keep = M
                elif s_d > 0 or e['kind'] == 'comic': keep = want
                else: keep = min(M, want + EXTRA_PREROLL)
                t_new = sync_t - keep; src_new = M - keep
                for w0, w1, what in windows:  # never move a start into a restraint window it was not in
                    if e['t'] >= w1 > t_new:
                        t_new = e['t']; keep = sync_t - t_new; src_new = M - keep
                if e['kind'] == 'comic' and t_new < e['t']:
                    t_new = e['t']; keep = sync_t - t_new; src_new = M - keep
                src_new = max(0.0, src_new)
                if abs(t_new - e['t']) > 0.004 or abs(src_new - s_d) > 0.004:
                    out['t'] = round(t_new, 3); out['spot_t'] = e['t']
                    if src_new > 0.004: out['src_in'] = round(src_new, 3)
                    else: out.pop('src_in', None)
                    if src_new > s_d + 0.02: out['fade_in'] = max(out.get('fade_in', 0.0), round(min(0.15, keep / 2), 3))
                    if 'dur' in e:
                        tail = e['t'] + e['dur'] - sync_t
                        out['dur'] = round(max(0.05, keep + tail), 3)
                    out['sync_t'] = round(sync_t, 3)
                    log.append(f"{e['id']} {e['asset']} v{vi}: t {e['t']} -> {out['t']}, src_in {s_d} -> {out.get('src_in', 0)}, "
                               f"sync {round(sync_t, 2)} (design {D}, measured {M})")
        if e['id'] in EVENT_GAIN:
            gd, why = EVENT_GAIN[e['id']]
            out['gain_db'] = round(out['gain_db'] + gd, 2); out['gain_trim'] = f'{gd} dB: {why}'; log.append(f"{e['id']} gain {gd} dB: {why}")
        if e['id'] in EVENT_OVR:
            ch, why = EVENT_OVR[e['id']]
            out.update(ch); out.pop('sync_t', None); out['override'] = why; log.append(f"{e['id']} override: {why}")
        (amb if e['kind'] == 'bed' else sfx).append(out)

    # ---- marker cross-check: every hero hit sits 0.06-0.10 s before its marker word (visual lead)
    heroes = {'x009': 'ft400', 'x048': 'slides', 'x054': 'miles', 'x064': 'up', 'x073': 'tall33', 'x112': 'seven', 'x139': 'old28',
              'x187': 'tall56', 'x188': 'tall56'}
    ev = {x['id']: x for x in sfx}
    marker_check = {i: round(mk[m]['start'] - ev[i]['t'], 3) for i, m in heroes.items()}
    assert all(0 <= v <= 0.12 for v in marker_check.values()), marker_check

    reveals = [{'name': n, 't': mk[n]['start'], 'word': mk[n]['word']} for n in
               ('ft400', 'slides', 'miles', 'up', 'tall33', 'seven', 'old28', 'threemi', 'tall56')]
    spec = {
        'episode': 'ep02 Why Can\'t You See Most of Hawaii? (Look Down)', 'version': 'v1',
        'built_by': 'longform/ep02-hawaii/tools/build_mix.py', 'timing_md5': h,
        'duration': dur, 'vo': a.vo, 'vo_gain_db': 0,
        'music': music, 'sfx': sfx, 'amb': amb, 'dips': dips,
        'duck': {'db': a.duck, 'attack': 0.08, 'release': 0.6, 'hold': 0.8, 'lookahead': 0.05, 'threshold_db': -42,
                 'band': {'lo': 800, 'hi': 5000, 'db': -4}},
        'amb_duck': {'db': a.amb_duck, 'attack': 0.15, 'release': 1.0, 'hold': 0.8, 'lookahead': 0.1, 'threshold_db': -42,
                     'band': {'lo': a.band_lo, 'hi': a.band_hi, 'db': a.band_db}},
        'sfx_duck': {'db': 0, 'attack': 0.03, 'release': 0.12, 'hold': 0, 'lookahead': 0.03, 'threshold_db': -42,
                     'band': {'lo': 800, 'hi': 5000, 'db': a.sfx_band_db}},
        'strict': bool(a.strict),
        'target_lufs': -14, 'true_peak': a.tp, 'loudness_passes': 3, 'limiter': {'lookahead_ms': 5, 'release_ms': 120},
        'qc': {'reveals': reveals,
               'restraint': spot_s['restraint'],
               'hush': [[76.21, 88.89, '1975: Two people died'], [379.79, 392.95, 'Nihoa: buried their dead'],
                        [524.27, 565.31, 'Midway losses and war graves']],
               'comic_ids': [x['id'] for x in sfx if x.get('kind') == 'comic'],
               'chapter_cards_s': spot_s['meta']['chapter_cards_s'],
               'intended_music_holes': [[480.24, 480.64, '1942 hard cut'], [677.89, 679.05, 'payoff dropout']],
               'marker_check_s': marker_check},
        'placement_log': log,
    }
    json.dump(spec, open(a.out, 'w'), indent=1, ensure_ascii=False)
    print(f'{len(music)} cues, {len(dips)} dips/lifts, {len(sfx)} sfx, {len(amb)} beds; {len(log)} placement changes; strict={a.strict}')
    for l in log: print('  ', l)


if __name__ == '__main__':
    main()
