"""review.py VER : crop each candidate's neighbourhood from the feedsim outputs (upnext list, sidebar list, home card)
and their glance versions into one review image, feeds/design_postcard/<VER>_review.jpg (2x zoom for the compact lists)."""
import json, sys
from PIL import Image, ImageDraw
F = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/feeds/design_postcard/'
V = sys.argv[1]; ids = sys.argv[2].split(',') if len(sys.argv) > 2 else ['1', '2', '3', '4']


def crop(lay, n, pad=110, glance=False, zoom=2):
    j = json.load(open(F + f'{V}_{n}_{lay}.json'))
    c = [k for k in j['cards'] if k['tag'] != 'competitor'][0]
    im = Image.open(F + f'{V}_{n}_{lay}{"_glance" if glance else ""}.jpg')
    s = 0.5 if glance else 1.0
    x0, y0, x1, y1 = c['card']
    if lay == 'sidebar': x0 = x0 - 6
    box = [round(v * s) for v in (x0 - 8, y0 - pad, x1 + 8, y1 + pad)]
    box[1] = max(0, box[1]); box[3] = min(im.height, box[3])
    cr = im.crop(box)
    z = zoom / s if glance else zoom
    return cr.resize((round(cr.width * z), round(cr.height * z)), Image.LANCZOS)


cols = []
for n in ids:
    parts = [crop('upnext', n), crop('upnext', n, glance=True), crop('sidebar', n), crop('home', n, pad=10, zoom=1.2)]
    w = max(p.width for p in parts); h = sum(p.height for p in parts) + 40 + 10 * len(parts)
    col = Image.new('RGB', (w, h), '#222'); d = ImageDraw.Draw(col); d.text((8, 8), f'cand {n}', fill='#fff')
    y = 40
    for p in parts: col.paste(p, (0, y)); y += p.height + 10
    cols.append(col)
W = sum(c.width for c in cols) + 10 * (len(cols) + 1); H = max(c.height for c in cols) + 20
S = Image.new('RGB', (W, H), '#111'); x = 10
for c in cols: S.paste(c, (x, 10)); x += c.width + 10
S.save(F + f'{V}_review.jpg', quality=88); print(F + f'{V}_review.jpg', S.size)
