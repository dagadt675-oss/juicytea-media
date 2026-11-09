#!/usr/bin/env python3
"""Animation strip from rendered frames: strip.py FRAMEDIR OUT.jpg (rows of frame numbers are fixed for lab_type.html)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
F, OUT = sys.argv[1], sys.argv[2]
rows = [[6, 15, 24, 36, 51, 75], [150, 159, 168, 180, 195, 225], [300, 309, 321, 333, 345, 375]]
tw, th = 480, 270; fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
sh = Image.new('RGB', (16 + 6 * (tw + 8), 50 + 3 * (th + 34)), (22, 24, 28)); d = ImageDraw.Draw(sh)
d.text((16, 14), 'BUILD-ON ANIMATION (each shot is a pure function of time; t = seconds into the shot)', font=fnt, fill=(255, 196, 80))
for r, row in enumerate(rows):
    for c, f in enumerate(row):
        im = Image.open(os.path.join(F, 'f%06d.jpg' % f)).resize((tw, th), Image.LANCZOS); x = 16 + c * (tw + 8); y = 50 + r * (th + 34)
        sh.paste(im, (x, y)); d.text((x, y + th + 6), '%s  t=%.1f s' % ('ABC'[r], (f % 150) / 30), font=fnt, fill=(200, 206, 216))
sh.save(OUT, quality=85); print('ok', OUT)
