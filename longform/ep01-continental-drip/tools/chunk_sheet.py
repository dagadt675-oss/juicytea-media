#!/usr/bin/env python3
"""chunk_sheet.py CHUNKDIR OUTDIR i0 i1 [step_s] — sample rendered chunks c_i0..c_i1 every step_s seconds, write labelled contact sheets."""
import os, subprocess, sys, glob
from PIL import Image, ImageDraw, ImageFont
cd, out, i0, i1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
step = float(sys.argv[5]) if len(sys.argv) > 5 else 2.5
os.makedirs(out, exist_ok=True)
for i in range(i0, i1 + 1):
    p = os.path.join(cd, f'c_{i:05d}.mp4')
    if not os.path.exists(p): continue
    t = 0.0
    while t < 15.0 - 1e-6:
        f = i * 450 + int(round(t * 30)); dst = os.path.join(out, f'f{f:06d}.jpg')
        if not os.path.exists(dst):
            subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', p, '-frames:v', '1', '-vf', 'scale=384:216', '-q:v', '4', dst])
        t += step
fs = sorted(glob.glob(os.path.join(out, 'f*.jpg')))
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
except Exception: font = ImageFont.load_default()
cols, per = 6, 42; tw, th = 384, 216
for k in range(0, len(fs), per):
    part = fs[k:k + per]; rows = (len(part) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw, rows * (th + 20)), (20, 20, 20)); dr = ImageDraw.Draw(sh)
    for j, f in enumerate(part):
        im = Image.open(f); x, y = (j % cols) * tw, (j // cols) * (th + 20); sh.paste(im, (x, y))
        fr = int(os.path.basename(f)[1:7]); tt = fr / 30
        dr.text((x + 4, y + th + 2), f'{int(tt // 60)}:{tt % 60:05.2f}  f{fr}', fill=(255, 220, 80), font=font)
    sh.save(os.path.join(out, f'sheet_{k // per:02d}.jpg'), quality=85)
print(len(fs), 'frames,', (len(fs) + per - 1) // per, 'sheets')
