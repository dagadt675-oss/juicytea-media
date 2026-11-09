# sheet.py OUTDIR : builds 1080p + phone (390x219) stills and compare.jpg from OUTDIR/final/<shot>_<mode>/f000000.jpg
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
O = sys.argv[1]
SHOTS = [('atlantic', 'WHOLE GLOBE (ep01 ch5 framing, Florida highlight)'),
         ('froward', 'LOW OBLIQUE over Cape Froward (ep01 ch1 s018, same patch)'),
         ('dusk', 'DUSK over the Mediterranean (real terminator, city lights)')]
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f_big, f_mid, f_small = ImageFont.truetype(B, 34), ImageFont.truetype(B, 24), ImageFont.truetype(R, 20)
def metrics(im):
    a = np.asarray(im.convert('RGB').resize((96, 54), Image.BILINEAR)).astype(np.float32)
    l = a @ np.array([0.299, 0.587, 0.114], np.float32)
    return l.mean(), (l < 18).mean() * 100
PW, PH = 390, 219; HW, HH = 940, 529; G = 20
rows = []
for shot, title in SHOTS:
    pair = {}
    for m in ('before', 'after'):
        im = Image.open(f'{O}/final/{shot}_{m}/f000000.jpg').convert('RGB')
        im.save(f'{O}/{shot}_{m}_1080.jpg', quality=90)
        ph = im.resize((PW, PH), Image.LANCZOS); ph.save(f'{O}/{shot}_{m}_phone.jpg', quality=92)
        im60 = Image.open(f'{O}/final/{shot}_{m}/f000060.jpg').convert('RGB')
        pair[m] = (im, ph, metrics(im), im60)
    rows.append((shot, title, pair))
W = G + 2 * (HW + G)
blockH = 52 + HH + 14 + PH + 46
H = 110 + len(rows) * (blockH + G)
sheet = Image.new('RGB', (W, H), (14, 16, 22)); d = ImageDraw.Draw(sheet)
d.text((G, 22), 'CINEMATIC GLOBE  -  left: BEFORE (ep01 engine)   right: AFTER (lab/globe/cineglobe.js)', font=f_big, fill=(244, 246, 250))
d.text((G, 68), 'top of each block: full 1920x1080 frame (scaled)   bottom: the same frame at 390x219, actual phone pixels (upright phone, 16:9 player)', font=f_small, fill=(154, 167, 184))
y = 110
for shot, title, pair in rows:
    d.text((G, y + 10), title, font=f_mid, fill=(255, 210, 63))
    for i, m in enumerate(('before', 'after')):
        im, ph, (lm, blk), _ = pair[m]
        x = G + i * (HW + G)
        sheet.paste(im.resize((HW, HH), Image.LANCZOS), (x, y + 52))
        tag = 'BEFORE  ep01' if m == 'before' else 'AFTER  cinematic'
        d.rectangle((x, y + 52, x + 260, y + 52 + 38), fill=(6, 9, 15)); d.text((x + 10, y + 58), tag, font=f_mid, fill=(255, 90, 54) if m == 'after' else (200, 205, 215))
        py = y + 52 + HH + 14
        sheet.paste(ph, (x, py))
        d.text((x + PW + 18, py + 8), 'phone size (390 x 219)', font=f_small, fill=(154, 167, 184))
        d.text((x + PW + 18, py + 40), f'mean luma {lm:.0f}/255', font=f_small, fill=(220, 224, 232))
        d.text((x + PW + 18, py + 68), f'near-black pixels {blk:.0f}%', font=f_small, fill=(220, 224, 232))
    y += blockH + G
sheet.save(f'{O}/compare.jpg', quality=88)
print(f'{O}/compare.jpg', sheet.size, os.path.getsize(f'{O}/compare.jpg') // 1024, 'KB')
for shot, _, pair in rows:
    print(shot, {m: tuple(round(v, 1) for v in pair[m][2]) for m in pair})
