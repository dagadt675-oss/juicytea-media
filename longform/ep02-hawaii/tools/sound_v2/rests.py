#!/usr/bin/env python3
"""rests.py SPEC_JSON MUSIC_STEM [--drop DB] [--min S] [--json OUT]: find unplanned music rests in the mixed music stem.

A rest = a run of 0.25 s RMS frames at least DROP dB (default 15) below the rolling median of the music stem over +-6 s,
lasting MIN s (default 0.5) or more, that does not overlap a planned dip (db <= -9, ramps included), an intended music hole,
a cue fade-in/fade-out region not covered by another cue, or time with no cue at all.
"""
import sys, json, subprocess, argparse
import numpy as np
from scipy.ndimage import median_filter
SR = 48000
ap = argparse.ArgumentParser()
ap.add_argument('spec'); ap.add_argument('stem')
ap.add_argument('--drop', type=float, default=15.0); ap.add_argument('--min', type=float, default=0.5)
ap.add_argument('--json'); ap.add_argument('--spot', help='spot_music.json: classify candidates (card / xfade / pre_sync / unplanned)')
a = ap.parse_args()
spec = json.load(open(a.spec))
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.stem, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
y = np.frombuffer(raw, np.float32).astype(np.float64)
w = SR // 4; n = len(y) // w
env = 10 * np.log10((y[:n * w].reshape(n, w) ** 2).mean(1) + 1e-12)
t = np.arange(n) / 4.0
ref = median_filter(env, size=49, mode='nearest')
low = env < ref - a.drop
# exclusions
excl = []
for d in spec['dips']:
    if d['db'] <= -9: excl.append((d['t0'] - d.get('ramp_in', 0) - 0.25, d['t1'] + d.get('ramp_out', 0) + 0.25, 'dip ' + d.get('note', '')[:30]))
for h in spec['qc'].get('intended_music_holes', []): excl.append((h[0] - 0.25, h[1] + 0.25, 'hole ' + h[2]))
cues = spec['music']
cover = np.zeros(n, bool)
for c in cues:
    cover |= (t >= c['start']) & (t < c['end'])
for c in cues:
    for (u0, u1) in [(c['start'], c['start'] + c['fade_in']), (c['end'] - c['fade_out'], c['end'])]:
        others = [o for o in cues if o is not c and o['start'] <= u0 and o['end'] >= u1]
        if not others: excl.append((u0 - 0.25, u1 + 0.25, 'fade ' + c['id'][:3]))
mask = low & cover
for e0, e1, _ in excl: mask &= ~((t >= e0) & (t < e1))
runs = []; i = 0
while i < n:
    if mask[i]:
        j = i
        while j + 1 < n and mask[j + 1]: j += 1
        if (j - i + 1) / 4.0 >= a.min:
            seg = env[i:j + 1]
            runs.append({'t0': round(t[i], 2), 't1': round(t[j] + 0.25, 2), 'dur': round((j - i + 1) / 4.0, 2),
                         'min_db': round(float(seg.min()), 1), 'ref_db': round(float(np.median(ref[i:j + 1])), 1),
                         'cue': [c['id'][:3] for c in cues if c['start'] <= t[i] < c['end']]})
        i = j + 1
    else: i += 1
cards = list(spec['qc'].get('chapter_cards_s', {}).values())
syncs = []
if a.spot:
    for c in json.load(open(a.spot))['cues']:
        syncs += [s['t'] for s in c.get('sync_points', [])]
edges = [c['start'] for c in cues] + [c['end'] for c in cues]
for r in runs:
    if any(r['t0'] - 1.0 <= k <= r['t1'] + 1.0 for k in cards): r['class'] = 'card'
    elif any(r['t0'] - 1.5 <= k <= r['t1'] + 1.5 for k in edges): r['class'] = 'xfade'
    elif any(r['t1'] <= k <= r['t1'] + 1.5 for k in syncs): r['class'] = 'pre_sync'
    else: r['class'] = 'unplanned'
out = {'stem': a.stem, 'drop_db': a.drop, 'min_s': a.min, 'rests': runs, 'n': len(runs),
       'classes': 'card: within 1 s of a chapter card; xfade: within 1.5 s of a cue start/end; pre_sync: a spotted sync point within 1.5 s after the rest; else unplanned'}
for r in runs:
    m, s = divmod(r['t0'], 60)
    print(f"rest {int(m)}:{s:04.1f}  {r['t0']:.2f}-{r['t1']:.2f}  dur {r['dur']:.2f}  min {r['min_db']} vs ref {r['ref_db']}  {r['cue']}  {r.get('class', '')}")
print('rests found:', len(runs), ' unplanned:', sum(r.get('class') == 'unplanned' for r in runs))
out['unplanned'] = [r for r in runs if r.get('class') == 'unplanned']
if a.json: json.dump(out, open(a.json, 'w'), indent=1)
