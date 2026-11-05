#!/usr/bin/env python3
"""review_frames.py OUTDIR T0 T1 [FPS] [--w 640]
Low-CPU frame dump of the rendered film between absolute times T0..T1 (seconds) from the 450-frame chunks
(engine/chunks/ep01_1920x1080/c_NNNNN.mp4, chunk i covers [15*i, 15*i+15) s). One nice'd ffmpeg pass per chunk.
Writes OUTDIR/t_SSSS.SS.jpg (absolute time in the name) and labelled contact sheets OUTDIR/sheet_NN.jpg (6x5 = 30 frames each).
Missing (not yet rendered) chunks are listed and skipped."""
import os, sys, glob, subprocess, math
from PIL import Image, ImageDraw, ImageFont
CD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine', 'chunks', 'ep01_1920x1080')
out, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
fps = float(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else 2.0
w = int(sys.argv[sys.argv.index('--w') + 1]) if '--w' in sys.argv else 640
os.makedirs(out, exist_ok=True)
missing = []
for i in range(int(t0 // 15), int(math.ceil(t1 / 15))):
    p = os.path.join(CD, f'c_{i:05d}.mp4')
    if not os.path.exists(p): missing.append(i); continue
    tmp = os.path.join(out, f'_c{i}'); os.makedirs(tmp, exist_ok=True)
    subprocess.run(['nice', '-n', '19', 'ffmpeg', '-v', 'error', '-i', p, '-vf', f'fps={fps},scale={w}:-2', '-q:v', '3', os.path.join(tmp, 'g_%04d.jpg')], check=True)
    for k, f in enumerate(sorted(glob.glob(os.path.join(tmp, 'g_*.jpg')))):
        t = 15 * i + k / fps
        if t0 - 1e-6 <= t < t1: os.replace(f, os.path.join(out, f't_{t:07.2f}.jpg'))
        else: os.remove(f)
    os.rmdir(tmp)
fs = sorted(glob.glob(os.path.join(out, 't_*.jpg')))
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
except Exception: font = ImageFont.load_default()
cols, per = 6, 30
for k in range(0, len(fs), per):
    part = fs[k:k + per]; im0 = Image.open(part[0]); tw, th = im0.size; rows = (len(part) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw, rows * (th + 22)), (18, 18, 18)); dr = ImageDraw.Draw(sh)
    for j, f in enumerate(part):
        x, y = (j % cols) * tw, (j // cols) * (th + 22); sh.paste(Image.open(f), (x, y))
        t = float(os.path.basename(f)[2:-4]); dr.text((x + 4, y + th + 3), f'{int(t // 60)}:{t % 60:05.2f}  ({t:.2f}s)', fill=(255, 220, 80), font=font)
    sh.save(os.path.join(out, f'sheet_{k // per:02d}.jpg'), quality=85)
print(f'{len(fs)} frames, {(len(fs) + per - 1) // per} sheets in {out}; missing chunks: {missing}')
