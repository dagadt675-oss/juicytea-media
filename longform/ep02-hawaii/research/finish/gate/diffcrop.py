"""diffcrop.py A B OUT [--k 3] [--cw 480 --ch 270] [--label a,b]: where B differs from A most.
Prints full SSIM (gray, downscaled 2x), mean abs diff, % px changed (>8 levels), and per crop the same numbers; writes OUT:
row 0 = A and B downscaled to 640 wide + a diff map; rows 1..k = A crop | B crop at 1x around the k biggest blurred-diff peaks."""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

a_p, b_p, out = sys.argv[1:4]
opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
K, CW, CH = int(opt('--k', 3)), int(opt('--cw', 480)), int(opt('--ch', 270))
la, lb = opt('--label', 'A,B').split(',')
A = Image.open(a_p).convert('RGB'); B = Image.open(b_p).convert('RGB')
a = np.asarray(A).astype(np.float32); b = np.asarray(B).astype(np.float32)

def ssim(x, y):
    x = x.astype(np.float64); y = y.astype(np.float64); C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    f = lambda z: ndimage.gaussian_filter(z, 1.5)
    mx, my = f(x), f(y); vx = f(x * x) - mx * mx; vy = f(y * y) - my * my; c = f(x * y) - mx * my
    return float((((2 * mx * my + C1) * (2 * c + C2)) / ((mx * mx + my * my + C1) * (vx + vy + C2))).mean())

g = lambda z: z.mean(-1)
d = np.abs(a - b).max(-1)
print(f'full ssim={ssim(g(a), g(b)):.4f} mad={np.abs(a - b).mean():.2f} changed%={(d > 8).mean() * 100:.2f} max={d.max():.0f}')
H, W = d.shape; db = ndimage.gaussian_filter(d, 12)
crops = []; dd = db.copy()
for _ in range(K):
    y, x = np.unravel_index(np.argmax(dd), dd.shape)
    if dd[y, x] < 0.5: break
    x0 = int(np.clip(x - CW // 2, 0, W - CW)); y0 = int(np.clip(y - CH // 2, 0, H - CH)); crops.append((x0, y0))
    dd[max(0, y0 - CH // 2):y0 + CH + CH // 2, max(0, x0 - CW // 2):x0 + CW + CW // 2] = 0
tw = 640; th = round(tw * H / W)
dm = Image.fromarray(np.clip(d * 4, 0, 255).astype(np.uint8)).convert('RGB').resize((tw, th))
rowh = max(th, CH) + 20
S = Image.new('RGB', (max(3 * tw + 12, 2 * CW + 6), 20 + th + len(crops) * rowh), (20, 20, 20)); D = ImageDraw.Draw(S)
for i, (im, lab) in enumerate([(A, la), (B, lb), (dm, 'diff x4')]):
    S.paste(im.resize((tw, th)), (i * (tw + 6), 18)); D.text((i * (tw + 6) + 2, 2), lab, fill=(230, 230, 230))
for j, (x0, y0) in enumerate(crops):
    ca = a[y0:y0 + CH, x0:x0 + CW]; cb = b[y0:y0 + CH, x0:x0 + CW]; dc = np.abs(ca - cb).max(-1)
    s = f'crop{j} ({x0},{y0}) ssim={ssim(g(ca), g(cb)):.4f} changed%={(dc > 8).mean() * 100:.1f}'
    print(s)
    yy = 20 + th + j * rowh
    S.paste(A.crop((x0, y0, x0 + CW, y0 + CH)), (0, yy + 18)); S.paste(B.crop((x0, y0, x0 + CW, y0 + CH)), (CW + 6, yy + 18))
    D.text((2, yy + 2), s + f'  left {la} | right {lb}', fill=(230, 230, 230))
S.save(out, quality=88)
