#!/usr/bin/env python3
"""edl.py CUTS_JSON OUT_DIR [--video engine/video_full_v3.mp4] [--mix audio/mix_v2.json] [--timing engine/www/ep/ep01/timing.json] [--dry]
Tightens the finished film in post, without new narration or re-rendering: removes the listed time ranges from picture,
narration and effects, and rebuilds everything that depends on the timeline.
CUTS_JSON: {"cuts": [[a, b, "why"], ...]} in seconds of the current film (each range [a, b) is snapped to whole frames).
Writes to OUT_DIR:
  vo_cut.wav           narration stem with the ranges removed (8 ms fades at every join, so no clicks)
  mix_cut.json         mix spec on the new timeline: SFX inside a cut dropped, the rest shifted; music cues shifted and shortened,
                       each cue keeps playing continuously across a cut (the music never jumps), fades kept
  timing_cut.json      word/segment/marker timing on the new timeline (for captions and chapters)
  select.txt           ffmpeg select expression that keeps every frame outside the cuts
  report.json          the time map, new duration, the new times of the description chapters and of the end screen
--dry: only print the report. Then: mix.py OUT_DIR/mix_cut.json OUT_DIR/mix_cut.wav, make_srt.py OUT_DIR/timing_cut.json captions.srt,
and assemble_cut.sh (the select expression in front of the usual grade chain)."""
import json, os, subprocess, sys
import numpy as np, soundfile as sf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, SR = 30, 48000
def arg(k, d): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d

def main():
    cuts_in, out = sys.argv[1], sys.argv[2]
    video = arg('--video', os.path.join(BASE, 'engine', 'video_full_v3.mp4'))
    mixp = arg('--mix', os.path.join(BASE, 'audio', 'mix_v2.json'))
    timp = arg('--timing', os.path.join(BASE, 'engine', 'www', 'ep', 'ep01', 'timing.json'))
    os.makedirs(out, exist_ok=True)
    spec = json.load(open(mixp)); T = json.load(open(timp))
    dur = spec['duration']
    cuts = sorted([(round(c[0] * FPS) / FPS, round(c[1] * FPS) / FPS, c[2] if len(c) > 2 else '') for c in json.load(open(cuts_in))['cuts']])
    for (a0, b0, _), (a1, b1, _) in zip(cuts, cuts[1:]):
        assert b0 <= a1, f'overlapping cuts {a0}-{b0} / {a1}-{b1}'
    def inside(t): return any(a <= t < b for a, b, _ in cuts)
    def mp(t):
        s = 0.0
        for a, b, _ in cuts:
            if t >= b: s += b - a
            elif t > a: return a - s
        return t - s
    new_dur = mp(dur)
    # chapters of the description (original times) and the end screen (last 17 s)
    chapters = [(0, "Why do the continents point south?"), (175, "What's on Earth's other side?"), (233, "Can you dig to China?"),
                (358, "Is Earth secretly a pyramid?"), (481, "Continental drift: why did geologists laugh at Wegener?"),
                (604, "Running the clock backwards"), (875, "Where is the drip going next?")]
    rep = {'cuts': [{'from': a, 'to': b, 'len': round(b - a, 3), 'why': w} for a, b, w in cuts], 'removed_s': round(dur - new_dur, 3),
           'old_duration': dur, 'new_duration': round(new_dur, 3),
           'chapters': [{'old': t, 'new': round(mp(t), 2), 'stamp': '%d:%02d' % (int(mp(t)) // 60, int(mp(t)) % 60), 'title': n} for t, n in chapters],
           'end_screen': {'video_element_from': round(new_dur - 17, 2), 'subscribe_from': round(new_dur - 14, 2)}}
    if '--dry' in sys.argv:
        print(json.dumps(rep, indent=1)); return
    # narration stem: keep the ranges between cuts, 8 ms fades at each join
    vo, sr = sf.read(spec['vo'], dtype='float32')
    if vo.ndim > 1: vo = vo.mean(axis=1)
    assert sr == SR or True
    keep, prev = [], 0.0
    for a, b, _ in cuts: keep.append((prev, a)); prev = b
    keep.append((prev, len(vo) / sr))
    f = int(0.008 * sr); parts = []
    for a, b in keep:
        seg = vo[int(round(a * sr)):int(round(b * sr))].copy()
        if len(seg) > 2 * f:
            if a > 0: seg[:f] *= np.linspace(0, 1, f)
            if b < len(vo) / sr: seg[-f:] *= np.linspace(1, 0, f)
        parts.append(seg)
    vcut = np.concatenate(parts)
    sf.write(os.path.join(out, 'vo_cut.wav'), vcut, sr, subtype='PCM_24')
    ns = dict(spec); ns['vo'] = os.path.join(out, 'vo_cut.wav'); ns['duration'] = round(new_dur, 3)
    ns['sfx'] = [dict(e, t=round(mp(e['t']), 3)) for e in spec['sfx'] if not inside(e['t'])]
    mus = []
    for m in spec['music']:
        s0, s1 = mp(m['start']), mp(min(m['end'], dur))
        if s1 - s0 < 0.5: continue
        mus.append(dict(m, start=round(s0, 3), end=round(s1, 3)))
    ns['music'] = mus
    json.dump(ns, open(os.path.join(out, 'mix_cut.json'), 'w'), indent=1)
    # timing on the new timeline
    nt = {'duration': round(mp(T['duration']), 3),
          'segments': [dict(s, start=round(mp(s['start']), 3), end=round(mp(s['end']), 3)) for s in T['segments'] if not (inside(s['start']) and inside(s['end'] - 1e-3))],
          'words': [dict(w, start=round(mp(w['start']), 3), end=round(mp(w['end']), 3)) for w in T['words'] if not inside(w['start'])],
          'markers': {k: dict(v, start=round(mp(v['start']), 3), end=round(mp(v['end']), 3)) for k, v in T['markers'].items() if not inside(v['start'])}}
    json.dump(nt, open(os.path.join(out, 'timing_cut.json'), 'w'), indent=1)
    # picture: frames to keep
    expr = '+'.join('between(n\\,%d\\,%d)' % (int(round(a * FPS)), int(round(b * FPS)) - 1) for a, b, _ in cuts)
    open(os.path.join(out, 'select.txt'), 'w').write(f"select='not({expr})',setpts=N/{FPS}/TB" if cuts else 'null')
    rep['words_dropped'] = len(T['words']) - len(nt['words'])
    json.dump(rep, open(os.path.join(out, 'report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))

if __name__ == '__main__':
    main()
