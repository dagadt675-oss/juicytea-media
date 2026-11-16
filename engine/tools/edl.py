#!/usr/bin/env python3
"""edl.py EDL_JSON OUT_DIR [--mix audio/mix_v3.json] [--timing engine/www/ep/ep01/timing.json] [--dry]
Tightens the finished film in post, without new narration or re-rendering.
EDL_JSON: {"cuts": [[a, b, "why"], ...],
           "moves": [{"src": [a, b], "dst": [c, d], "why": "..."}]}   seconds of the current film, snapped to whole frames.
  cut:  [a, b) is removed.
  move: [a, b) is taken out of its place and plays where [c, d) was; [c, d) is removed.
The music is laid on the main timeline and keeps playing straight through every join and every moved piece, so it never
jumps; narration, SFX, captions and markers travel with their picture.
Writes to OUT_DIR:
  ranges.json       picture/narration source ranges in output order (frames [k, m) and seconds)
  vo_cut.wav        narration stem in the new order (8 ms fades at every join, so no clicks)
  mix_cut.json      mix spec on the new timeline (SFX moved with their range or dropped; music cues and dips re-timed)
  timing_cut.json   word/segment/marker timing on the new timeline (captions, chapters)
  report.json       the map, the new duration, the description chapters and the end screen on the new timeline
Then: mix.py OUT_DIR/mix_cut.json OUT_DIR/mix_cut.wav; make_srt.py OUT_DIR/timing_cut.json captions.srt;
assemble_edl.py VIDEO OUT_DIR/ranges.json OUT_DIR/mix_cut.wav OUT.mp4."""
import json, os, sys
import numpy as np, soundfile as sf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
def arg(k, d): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
def fr(t): return int(round(t * FPS))

def build(edl, dur):
    cuts = [(fr(c[0]), fr(c[1]), c[2] if len(c) > 2 else '') for c in edl.get('cuts', [])]
    moves = [(fr(m['src'][0]), fr(m['src'][1]), fr(m['dst'][0]), fr(m['dst'][1]), m.get('why', '')) for m in edl.get('moves', [])]
    removed = sorted([(a, b) for a, b, _ in cuts] + [(a, b) for a, b, _, _, _ in moves] + [(c, d) for _, _, c, d, _ in moves])
    for (a0, b0), (a1, b1) in zip(removed, removed[1:]):
        assert b0 <= a1, f'overlapping ranges {a0/FPS}-{b0/FPS} / {a1/FPS}-{b1/FPS}'
    N = fr(dur)
    keep, p = [], 0
    for a, b in removed:
        if a > p: keep.append((p, a))
        p = max(p, b)
    if p < N: keep.append((p, N))
    # entries in output order; an insert sits at its anchor c (where the replaced range started) on the main timeline
    entries = [{'kind': 'main', 'k': a, 'm': b, 'anchor': a} for a, b in keep]
    pf = {(fr(m['src'][0]), fr(m['src'][1])): fr(m['picture_from']) for m in edl.get('moves', []) if 'picture_from' in m}
    entries += [{'kind': 'moved', 'k': a, 'm': b, 'anchor': c, 'hold_until': pf.get((a, b))} for a, b, c, d, _ in moves]
    entries.sort(key=lambda e: (e['anchor'], 0 if e['kind'] == 'moved' else 1))
    o = 0
    for e in entries:
        e['out'] = o; o += e['m'] - e['k']
    return entries, o, cuts, moves

def main():
    edlp, out = sys.argv[1], sys.argv[2]
    mixp = arg('--mix', os.path.join(BASE, 'audio', 'mix_v3.json'))
    timp = arg('--timing', os.path.join(BASE, 'engine', 'www', 'ep', 'ep01', 'timing.json'))
    os.makedirs(out, exist_ok=True)
    spec = json.load(open(mixp)); T = json.load(open(timp)); edl = json.load(open(edlp))
    dur = spec['duration']
    entries, total, cuts, moves = build(edl, dur)
    def mp(t):
        """source time -> output time for anything that travels with its picture (None if removed)"""
        f = t * FPS
        for e in entries:
            if e['k'] <= f < e['m']: return (e['out'] + f - e['k']) / FPS
        return None
    def mmain(t):
        """main-timeline time -> output time, for the music bed (inserted pieces count where they sit)"""
        f, o = t * FPS, 0.0
        for e in entries:
            if e['kind'] == 'main':
                if f < e['k']: return o / FPS
                if f < e['m']: return (o + f - e['k']) / FPS
            elif e['anchor'] >= f: return o / FPS
            o += e['m'] - e['k']
        return o / FPS
    new_dur = total / FPS
    chapters = [(0, "Why do the continents point south?"), (175.62, "What's on Earth's other side?"), (233.26, "Can you dig to China?"),
                (357.96, "Is Earth secretly a pyramid?"), (481.79, "Why did geologists laugh at Wegener?"),
                (604.67, "Where are the drips pointing?"), (694.40, "Was the answer hidden in a joke?"),
                (775.93, "What doesn't drip?"), (875.69, "Where is the drip going next?")]
    def stamp(t): return '%d:%02d' % (int(t) // 60, int(t) % 60)
    rep = {'cuts': [{'from': a / FPS, 'to': b / FPS, 'len': round((b - a) / FPS, 3), 'why': w} for a, b, w in cuts],
           'moves': [{'src': [a / FPS, b / FPS], 'replaces': [c / FPS, d / FPS], 'why': w} for a, b, c, d, w in moves],
           'old_duration': dur, 'new_duration': round(new_dur, 3), 'removed_s': round(dur - new_dur, 3),
           'chapters': [{'old': t, 'new': (round(mp(t), 2) if mp(t) is not None else None), 'stamp': stamp(mp(t)) if mp(t) is not None else None, 'title': n} for t, n in chapters],
           'end_screen': {'video_element_from': round(new_dur - 17, 2), 'subscribe_from': round(new_dur - 14, 2)},
           'ranges': [{'kind': e['kind'], 'src': [round(e['k'] / FPS, 3), round(e['m'] / FPS, 3)], 'out': round(e['out'] / FPS, 3)} for e in entries]}
    if '--dry' in sys.argv:
        print(json.dumps(rep, indent=1)); return
    json.dump([{'k': e['k'], 'm': e['m'], 'kind': e['kind'], 'hold_until': e.get('hold_until')} for e in entries], open(os.path.join(out, 'ranges.json'), 'w'), indent=1)
    # narration in the new order
    vo, sr = sf.read(spec['vo'], dtype='float32')
    if vo.ndim > 1: vo = vo.mean(axis=1)
    f8 = int(0.008 * sr); parts = []
    for e in entries:
        a, b = e['k'] / FPS, e['m'] / FPS
        seg = vo[int(round(a * sr)):min(len(vo), int(round(b * sr)))].copy()
        need = int(round((b - a) * sr))
        if len(seg) < need: seg = np.concatenate([seg, np.zeros(need - len(seg), np.float32)])
        def quiet(i):
            w = vo[max(0, i - 240):i + 240]
            return len(w) == 0 or 20 * np.log10(np.sqrt((w.astype(np.float64) ** 2).mean()) + 1e-12) < -55
        fa = f8 if quiet(int(round(a * sr))) else int(0.002 * sr); fb = f8 if quiet(int(round(b * sr))) else int(0.002 * sr)
        if len(seg) > fa + fb:
            seg[:fa] *= np.linspace(0, 1, fa); seg[-fb:] *= np.linspace(1, 0, fb)
        parts.append(seg)
    sf.write(os.path.join(out, 'vo_cut.wav'), np.concatenate(parts), sr, subtype='PCM_24')
    ns = dict(spec); ns['vo'] = os.path.join(out, 'vo_cut.wav'); ns['duration'] = round(new_dur, 3)
    ns['sfx'] = [dict(e, t=round(mp(e['t']), 3)) for e in spec['sfx'] if mp(e['t']) is not None]
    ns['music'] = [dict(m, start=round(mmain(m['start']), 3), end=round(mmain(min(m['end'], dur)), 3)) for m in spec['music']]
    ns['music'] = [m for m in ns['music'] if m['end'] - m['start'] >= 0.5]
    ns['dips'] = [[round(mmain(a), 3), round(mmain(b), 3), g] for a, b, g in spec.get('dips', []) if mp(a) is not None]
    json.dump(ns, open(os.path.join(out, 'mix_cut.json'), 'w'), indent=1)
    def mv(x):
        s, e = mp(x['start']), mp(max(x['start'], x['end'] - 1e-3))
        return None if s is None or e is None else dict(x, start=round(s, 3), end=round(e + 1e-3, 3))
    words = sorted([w for w in (mv(w) for w in T['words']) if w], key=lambda w: w['start'])
    segs = sorted([s for s in (mv(s) for s in T['segments']) if s], key=lambda s: s['start'])
    marks = {k: v for k, v in ((k, mv(v)) for k, v in T['markers'].items()) if v}
    json.dump({'duration': round(new_dur, 3), 'segments': segs, 'words': words, 'markers': marks}, open(os.path.join(out, 'timing_cut.json'), 'w'), indent=1)
    rep['words_dropped'] = len(T['words']) - len(words)
    json.dump(rep, open(os.path.join(out, 'report.json'), 'w'), indent=1)
    print(json.dumps({k: rep[k] for k in ('old_duration', 'new_duration', 'removed_s', 'chapters', 'end_screen', 'words_dropped')}, indent=1))

if __name__ == '__main__':
    main()
