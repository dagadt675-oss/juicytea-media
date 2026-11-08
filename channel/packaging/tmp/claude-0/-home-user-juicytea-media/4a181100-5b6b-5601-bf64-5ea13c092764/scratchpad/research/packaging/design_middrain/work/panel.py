"""panel.py TAG N -> feeds/middrain/TAG_panel.jpg: per candidate row = home card (+neighbour), upnext list +-1, sidebar list +-1, and the glance versions."""
import json, sys
from PIL import Image, ImageDraw
F = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/feeds/middrain'
tag = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
rows = []
def crop_around(img_p, js_p, pad_cards=1, scale=1.0):
    im = Image.open(img_p); js = json.load(open(js_p)); cards = js['cards']
    k = [i for i, c in enumerate(cards) if c['tag'] == 'candidate'][0]
    lo = max(0, k - pad_cards); hi = min(len(cards) - 1, k + pad_cards)
    sx = im.width / (js.get('w', im.width)) if False else 1
    x0 = min(c['card'][0] for c in cards[lo:hi + 1]) - 6; y0 = cards[lo]['card'][1] - 6
    x1 = max(c['card'][2] for c in cards[lo:hi + 1]) + 6; y1 = cards[hi]['card'][3] + 6
    bn = img_p.split('/')[-1]; f = im.width / 390 if ('home' in bn or 'upnext' in bn) else im.width / 1280
    c = im.crop((int(x0 * f), int(y0 * f), int(x1 * f), int(y1 * f)))
    return c
for i in range(1, n + 1):
    p = f'{F}/{tag}_{i}'
    a = crop_around(f'{p}_home_scroll.jpg', f'{p}_home_scroll.json', 0)
    b = crop_around(f'{p}_upnext_scroll.jpg', f'{p}_upnext_scroll.json', 1)
    c = crop_around(f'{p}_sidebar.jpg', f'{p}_sidebar.json', 1)
    g = Image.open(f'{p}_sidebar_glance.jpg'); gj = json.load(open(f'{p}_sidebar.json'))
    k = [c_ for c_ in gj['cards'] if c_['tag'] == 'candidate'][0]['card']; s = g.width / 1280
    gl = g.crop((int((k[0] - 6) * s), int((k[1] - 110) * s), int((k[2] + 6) * s), int((k[3] + 110) * s))).resize((int((k[2] - k[0] + 12)), int((k[3] - k[1] + 220))))
    hh = max(a.height, b.height, c.height, gl.height)
    row = Image.new('RGB', (a.width + b.width + c.width + gl.width + 50, hh + 10), (40, 40, 40))
    x = 5
    for im in (a, b, c, gl): row.paste(im, (x, 5)); x += im.width + 12
    rows.append(row)
Wp = max(r.width for r in rows); Hp = sum(r.height for r in rows)
P = Image.new('RGB', (Wp, Hp), (40, 40, 40)); y = 0
for r in rows: P.paste(r, (0, y)); y += r.height
P.save(f'{F}/{tag}_panel.jpg', quality=88); print(f'{F}/{tag}_panel.jpg', P.size)
