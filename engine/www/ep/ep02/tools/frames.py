#!/usr/bin/env python3
"""frames.py ITEM[+-s] ... : film frame numbers (30 fps) for timing markers or segment ids, for still.cjs --frames.
  python3 -I frames.py drained most+2.5 s004 s169.end tall56-0.1    ->  80,186,326,20399,20370
ITEM = marker (word start), marker.end, segment id (start) or sid.end; an optional +/-seconds offset. Reads ../timing.json."""
import sys, json, os, re
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'timing.json')))
M, S = d['markers'], {s['id']: s for s in d['segments']}
out = []
for a in sys.argv[1:]:
    m = re.match(r'^([A-Za-z0-9_]+)(\.end)?([+-][0-9.]+)?$', a)
    if not m: sys.exit(f'bad item {a}')
    k, end, off = m.group(1), m.group(2), float(m.group(3) or 0)
    src = M.get(k) or S.get(k)
    if src is None: sys.exit(f'unknown marker or segment {k}')
    out.append(round((src['end' if end else 'start'] + off) * 30))
print(','.join(map(str, out)))
