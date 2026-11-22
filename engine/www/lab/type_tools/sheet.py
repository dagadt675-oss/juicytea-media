#!/usr/bin/env python3
"""Before/after compare sheet + phone-size stills.
usage: sheet.py OUTDIR BEFORE_A AFTER_A [BEFORE_B AFTER_B ...] --names "0:25 ...|3:02 ..." """
import sys, os
from PIL import Image, ImageDraw, ImageFont
args = sys.argv[1:]
names = []
if '--names' in args:
    i = args.index('--names'); names = args[i + 1].split('|'); args = args[:i] + args[i + 2:]
out = args[0]; pairs = list(zip(args[1::2], args[2::2]))
os.makedirs(out, exist_ok=True)
PW, PH = 390, 219          # upright phone, 16:9 player width in points
FW, FH = 960, 540          # full-size panel in the sheet (half of 1080p)
def font(sz, bold=True):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
F1, F2, F3 = font(30), font(20), font(16, False)
M, G = 24, 24
blockH = 36 + FH + 14 + 26 + PH + 34
Wd = M * 2 + FW * 2 + G
Ht = 90 + len(pairs) * blockH + M
sheet = Image.new('RGB', (Wd, Ht), (22, 24, 28)); d = ImageDraw.Draw(sheet)
d.text((M, 22), 'PHONE-FIRST TYPE + MAP GRAPHICS   left: ep01 BEFORE   right: AFTER (same information, new graphics)', font=F1, fill=(240, 240, 240))
d.text((M, 60), 'top: 1920x1080 shown at 50%      bottom: 390x219 = what an upright phone shows, at 1:1 pixels', font=F3, fill=(170, 176, 186))
y = 90
for k, (b, a) in enumerate(pairs):
    nm = names[k] if k < len(names) else f'shot {k+1}'
    d.text((M, y + 4), nm, font=F2, fill=(255, 196, 80))
    y += 36
    for j, (src, tag) in enumerate([(b, 'before'), (a, 'after')]):
        im = Image.open(src).convert('RGB').resize((1920, 1080), Image.LANCZOS)
        base = os.path.splitext(os.path.basename(src))[0]
        key = f'{tag}_{chr(65 + k)}'
        im.save(os.path.join(out, key + '_full.jpg'), quality=88)
        ph = im.resize((PW, PH), Image.LANCZOS); ph.save(os.path.join(out, key + '_phone.jpg'), quality=92)
        x = M + j * (FW + G)
        sheet.paste(im.resize((FW, FH), Image.LANCZOS), (x, y))
        d.rectangle([x, y, x + 120, y + 30], fill=(200, 60, 40) if tag == 'before' else (40, 150, 90))
        d.text((x + 10, y + 4), tag.upper(), font=F2, fill=(255, 255, 255))
        py = y + FH + 14
        d.text((x, py), 'phone, 1:1', font=F3, fill=(170, 176, 186))
        sheet.paste(ph, (x, py + 26))
    y += FH + 14 + 26 + PH + 34
sheet.save(os.path.join(out, 'compare.jpg'), quality=86)
print('ok', os.path.join(out, 'compare.jpg'), sheet.size)
