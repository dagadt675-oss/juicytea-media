#!/usr/bin/env python3
"""vtt2txt.py file.vtt -> prints de-duplicated transcript with [mm:ss] stamps every ~15 s"""
import re, sys
lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
out, last, stamp, cur_t = [], '', -999, 0
for ln in lines:
    m = re.match(r'(\d+):(\d+):(\d+)\.\d+ -->', ln)
    if m:
        cur_t = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)); continue
    if not ln.strip() or ln.startswith(('WEBVTT', 'Kind:', 'Language:')) or '-->' in ln: continue
    txt = re.sub(r'<[^>]+>', '', ln).strip()
    if not txt or txt == last: continue
    last = txt
    if cur_t - stamp >= 15:
        out.append(f'\n[{cur_t//60:02d}:{cur_t%60:02d}] '); stamp = cur_t
    out.append(txt + ' ')
# remove rolling duplicates (auto-subs repeat the previous line)
s = ''.join(out)
print(s)
