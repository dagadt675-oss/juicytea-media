#!/usr/bin/env python3
"""grab.py FRAME [COUNT] [--step S] [--w W] [--out DIR] [--video PATH] [--cols C]
Exact-frame grabber for reviewers. Frame n is the frame shown at time n/30 s of the film.
Writes COUNT frames starting at FRAME, every S-th frame (default 4 frames, step 1, width 960), as DIR/f_NNNNN.jpg,
plus one labelled tile DIR/tile_FRAME_COUNTxS.jpg (C columns, default 4) so a run of frames can be read in one image.
Default video: the delivered master (deliver/ep01/video_final.mp4); default DIR: review6/grab.
Examples:
  grab.py 10348 4            frames 10348..10351
  grab.py 2700 24 --step 2   every 2nd frame for 1.6 s from frame 2700
  grab.py 5400 1 --w 1920    one full-resolution frame"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def arg(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith('--') and not sys.argv[i - 1].startswith('--')]
    f0 = int(pos[0]); cnt = int(pos[1]) if len(pos) > 1 else 4
    step = int(arg('--step', 1)); w = int(arg('--w', 960)); cols = int(arg('--cols', 4))
    out = arg('--out', os.path.join(BASE, 'review6', 'grab')); video = arg('--video', os.path.join(BASE, 'deliver', 'ep01', 'video_final.mp4'))
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, '_g%d' % os.getpid()); os.makedirs(tmp)
    t = max(0.0, (f0 - 0.5) / 30.0)   # the first frame at or after this time is exactly frame f0
    n_dec = (cnt - 1) * step + 1
    subprocess.run(['ffmpeg', '-v', 'error', '-ss', '%.4f' % t, '-i', video, '-frames:v', str(n_dec), '-vf', f'scale={w}:-2', '-q:v', '2',
                    os.path.join(tmp, 'x_%05d.jpg')], check=True)
    got = sorted(os.listdir(tmp)); files = []
    for k, name in enumerate(got):
        if k % step: os.remove(os.path.join(tmp, name)); continue
        p = os.path.join(out, 'f_%05d.jpg' % (f0 + k)); os.replace(os.path.join(tmp, name), p); files.append((f0 + k, p))
    os.rmdir(tmp)
    if len(files) > 1:
        im0 = Image.open(files[0][1]); W, H = im0.size; LB = 24; rows = (len(files) + cols - 1) // cols
        sh = Image.new('RGB', (cols * W, rows * (H + LB)), (20, 20, 20)); d = ImageDraw.Draw(sh)
        try: fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
        except Exception: fnt = ImageFont.load_default()
        for j, (fn, p) in enumerate(files):
            x, y = (j % cols) * W, (j // cols) * (H + LB)
            sh.paste(Image.open(p), (x, y + LB)); tt = fn / 30.0
            d.text((x + 6, y + 2), 'frame %d  %d:%05.2f' % (fn, int(tt) // 60, tt % 60), fill=(255, 230, 80), font=fnt)
        tp = os.path.join(out, 'tile_%05d_%dx%d.jpg' % (f0, cnt, step)); sh.save(tp, quality=88); print(tp)
    else:
        print(files[0][1])

if __name__ == '__main__':
    main()
