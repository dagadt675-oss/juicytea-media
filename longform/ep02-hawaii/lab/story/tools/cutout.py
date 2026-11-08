#!/usr/bin/env python3
"""Cut a person out of a public-domain portrait with MODNet (portrait matting, ONNX, CPU).
Usage: python3 -I cutout.py MODEL.onnx IN.jpg OUT_PREFIX [--maxside 1400]
Writes OUT_PREFIX_cut.png (RGBA subject, alpha = matte) and OUT_PREFIX_bg.jpg (clean plate: subject
removed and filled by iterative blur in-painting, for 2.5D parallax)."""
import sys, numpy as np, onnxruntime as ort
from PIL import Image, ImageFilter
model, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
maxside = int(sys.argv[sys.argv.index('--maxside') + 1]) if '--maxside' in sys.argv else 1400
im = Image.open(src).convert('RGB')
s = maxside / max(im.size)
if s < 1: im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
W, H = im.size
# MODNet reference resize: short side 512, both sides multiple of 32
ref = 512
if max(H, W) < ref or min(H, W) > ref:
    if W >= H: rh = ref; rw = int(W / H * ref)
    else: rw = ref; rh = int(H / W * ref)
else: rh, rw = H, W
rh -= rh % 32; rw -= rw % 32
x = np.asarray(im.resize((rw, rh), Image.BILINEAR), dtype=np.float32) / 255.0
x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
iname = sess.get_inputs()[0].name
m = sess.run(None, {iname: x})[0][0, 0]
matte = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
# tighten: slight contrast on alpha so edges are crisp but not aliased
a = np.asarray(matte, dtype=np.float32) / 255.0
a = np.clip((a - 0.12) / 0.76, 0, 1)
A = Image.fromarray((a * 255).astype(np.uint8))
cut = im.copy(); cut.putalpha(A)
bb = A.getbbox(); cut = cut.crop(bb)
cut.save(out + '_cut.png', optimize=True)
# clean plate: dilate the subject mask, fill by repeated blur diffusion from the surroundings
mk = A.filter(ImageFilter.MaxFilter(31))
mk_np = np.asarray(mk, dtype=np.float32) / 255.0
img = np.asarray(im, dtype=np.float32)
known = (mk_np < 0.05).astype(np.float32)
fill = img * known[..., None]; wsum = known.copy()
for r in [4, 8, 16, 32, 64, 96]:
    pass
cur = img.copy(); kn = known.copy()
small = 4
for it in range(6):
    num = Image.fromarray(np.clip(cur * kn[..., None], 0, 255).astype(np.uint8))
    den = Image.fromarray((kn * 255).astype(np.uint8))
    rad = 6 * (2 ** it)
    numb = np.asarray(num.filter(ImageFilter.GaussianBlur(rad)), dtype=np.float32)
    denb = np.asarray(den.filter(ImageFilter.GaussianBlur(rad)), dtype=np.float32) / 255.0
    est = numb / np.maximum(denb[..., None], 1e-3)
    newk = np.clip(denb * 4, 0, 1)
    cur = cur * kn[..., None] + est * (1 - kn[..., None])
    kn = np.maximum(kn, (newk > 0.5).astype(np.float32))
plate = Image.fromarray(np.clip(cur, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
plate.save(out + '_bg.jpg', quality=88)
print('ok', src, (W, H), 'cut bbox', bb, 'alpha mean %.2f' % a.mean())
