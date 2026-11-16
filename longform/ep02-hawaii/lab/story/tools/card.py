#!/usr/bin/env python3
"""Turn a MODNet cut-out (RGBA) into a 'paper cut-out card' for the Archive-in-World story mode:
fill matte holes, add a paper edge, apply the shared archival split-tone grade, trim and resize.
Usage: python3 -I card.py IN_cut.png OUT_card.png [--h 1300] [--edge 9] [--tone 0.55] [--bw]"""
import sys, numpy as np
from PIL import Image, ImageFilter, ImageDraw
a = sys.argv
src, dst = a[1], a[2]
opt = lambda k, d: type(d)(a[a.index('--' + k) + 1]) if '--' + k in a else d
H = opt('h', 1300); EDGE = opt('edge', 9); TONE = opt('tone', 0.55)
im = Image.open(src).convert('RGBA')
s = H / im.height; im = im.resize((round(im.width * s), H), Image.LANCZOS)
rgb = np.asarray(im, dtype=np.float32)[..., :3] / 255.0
al = np.asarray(im, dtype=np.float32)[..., 3] / 255.0
# 1) fill holes in the matte: background regions not connected to the top/left/right border
pad = 4
CL = opt('close', 0)
fg = Image.fromarray(((al >= 0.5) * 255).astype(np.uint8))
if CL: fg = fg.filter(ImageFilter.MaxFilter(CL)).filter(ImageFilter.MinFilter(CL))
m = Image.fromarray(255 - np.asarray(fg))
mp = Image.new('L', (im.width + 2 * pad, im.height + pad), 255)  # open at top/left/right, closed at bottom
mp.paste(m, (pad, pad))
ImageDraw.floodfill(mp, (0, 0), 128)
reach = np.asarray(mp, dtype=np.uint8)[pad:pad + im.height, pad:pad + im.width]
holes = (reach == 255)
filled = Image.fromarray(((holes | (np.asarray(fg) > 127)) * 255).astype(np.uint8))
interior = np.asarray(filled.filter(ImageFilter.MinFilter(9)), dtype=np.float32) / 255.0
al = np.maximum(np.where(holes, 1.0, al), interior)
# 2) paper edge: dilate the silhouette, round it, keep anti-aliased
sil = Image.fromarray((al * 255).astype(np.uint8))
P = EDGE + 6
silp = Image.new('L', (im.width + 2 * P, im.height + P), 0); silp.paste(sil, (P, P))
dil = silp.filter(ImageFilter.MaxFilter(2 * EDGE + 1 if (2 * EDGE + 1) % 2 else 2 * EDGE + 1)).filter(ImageFilter.GaussianBlur(EDGE * 0.45))
d = np.asarray(dil, dtype=np.float32) / 255.0
d = np.clip((d - 0.35) / 0.3, 0, 1)
# straight crop at the bottom stays straight (card base)
Wp, Hp = silp.size
out = np.zeros((Hp, Wp, 4), np.float32)
rng = np.random.default_rng(3)
paper = np.array([0.95, 0.93, 0.885], np.float32)
noise = (rng.random((Hp, Wp)) - 0.5) * 0.035
out[..., :3] = paper[None, None, :] + noise[..., None]
out[..., 3] = d
# 3) grade the photo: shared archival split-tone (shadows teal-ink, highlights warm paper), mild contrast
L = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
sh = np.array([0.055, 0.13, 0.16], np.float32); hi = np.array([0.98, 0.9, 0.76], np.float32)
Lc = np.clip((L - 0.5) * 1.08 + 0.52, 0, 1)
tone = sh[None, None, :] * (1 - Lc[..., None]) + hi[None, None, :] * Lc[..., None]
if '--bw' in a: graded = tone
else: graded = rgb * (1 - TONE) + (tone * 0.6 + rgb * 0.4) * TONE
ph = np.zeros((Hp, Wp, 3), np.float32); pa = np.zeros((Hp, Wp), np.float32)
ph[P:P + im.height, P:P + im.width] = graded; pa[P:P + im.height, P:P + im.width] = al
out[..., :3] = out[..., :3] * (1 - pa[..., None]) + ph * pa[..., None]
out[..., 3] = np.maximum(out[..., 3], pa)
o = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')
o = o.crop(o.getbbox())
o.save(dst, optimize=True)
print('card', dst, o.size, 'holes filled px', int(holes.sum()))
