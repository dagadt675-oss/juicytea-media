"""Compact review of feedsim output: one row per candidate (home, upnext, sidebar column, and glances).
usage: review.py FEED_PREFIX ncand out.jpg"""
import sys, json, os
from PIL import Image, ImageDraw
pre, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
rows = []
for i in range(1, n + 1):
    p = f'{pre}_{i}'
    home = Image.open(p + '_home.jpg').resize((273, 591))
    up = Image.open(p + '_upnext.jpg').resize((273, 591))
    sb = Image.open(p + '_sidebar.jpg').crop((870, 80, 1280, 720)).resize((338, 528))
    hg = Image.open(p + '_home_glance.jpg').resize((273, 591))
    ug = Image.open(p + '_upnext_glance.jpg').resize((273, 591))
    sg = Image.open(p + '_sidebar_glance.jpg').crop((435, 40, 640, 360)).resize((338, 528))
    row = Image.new('RGB', (273 * 4 + 338 * 2 + 50, 610), (40, 40, 40)); d = ImageDraw.Draw(row)
    x = 5
    for im in (home, up, sb, hg, ug, sg):
        row.paste(im, (x, 15)); x += im.size[0] + 8
    d.text((6, 1), f'cand_{i}: home | upnext | sidebar | glances', fill=(255, 255, 0))
    rows.append(row)
sh = Image.new('RGB', (rows[0].size[0], sum(r.size[1] for r in rows)))
y = 0
for r in rows: sh.paste(r, (0, y)); y += r.size[1]
sh.save(out, quality=80)
