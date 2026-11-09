#!/usr/bin/env python3
"""make_srt.py timing.json out.srt — closed captions from ElevenLabs word timings (upload as a caption track; never burned in).
Cues: <= 2 lines x 42 chars, <= 6 s, break at segment / sentence ends first, then at commas; never overlap."""
import json, sys, textwrap
t = json.load(open(sys.argv[1])); W = t['words']
MAXC, MAXL, MAXD = 42, 2, 6.0
def fmt(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def fits(words):
    lines = textwrap.wrap(' '.join(w['w'] for w in words), MAXC)
    return len(lines) <= MAXL
cues, cur = [], []
for i, w in enumerate(W):
    if cur and (w['seg'] != cur[-1]['seg'] or not fits(cur + [w]) or w['end'] - cur[0]['start'] > MAXD):
        cues.append(cur); cur = []
    cur.append(w)
    end_sent = w['w'][-1] in '.?!' or w['w'].endswith(('."', '?"', ".'", "?'"))
    soft = w['w'][-1] in ',:;'
    n = len(' '.join(x['w'] for x in cur))
    nxt = W[i + 1] if i + 1 < len(W) else None
    if end_sent and (n > 18 or (nxt and nxt['start'] - w['end'] > 0.35)):
        cues.append(cur); cur = []
    elif soft and n > 46:
        cues.append(cur); cur = []
if cur: cues.append(cur)
def wrap2(words):
    full = ' '.join(words)
    if len(full) <= MAXC: return full
    best = None
    for i in range(1, len(words)):
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        if len(a) > MAXC or len(b) > MAXC: continue
        score = abs(len(a) - len(b)) - (8 if words[i - 1][-1] in ',.;:?!' else 0)
        if best is None or score < best[0]: best = (score, a + '\n' + b)
    return best[1] if best else '\n'.join(textwrap.wrap(full, MAXC))
out = []
for k, c in enumerate(cues):
    a = c[0]['start']; b = c[-1]['end'] + 0.25
    if k + 1 < len(cues): b = min(b, cues[k + 1][0]['start'] - 0.04)
    b = max(b, a + 0.7)
    if k + 1 < len(cues): b = min(b, cues[k + 1][0]['start'] - 0.04)
    txt = wrap2([w['w'] for w in c])
    out.append(f'{k + 1}\n{fmt(a)} --> {fmt(b)}\n{txt}\n')
open(sys.argv[2], 'w').write('\n'.join(out))
print(len(cues), 'cues; longest', max(c[-1]['end'] - c[0]['start'] for c in cues), 's')
