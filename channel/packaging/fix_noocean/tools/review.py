"""review.py OUT.jpg IMG [...]: one review sheet per image row: full 640x360, 390x219 (Home card), 168x94 (compact card) shown at 1x and 2x (nearest),
plus the glance version of 168x94 (half size, 1.1 px blur, 5 px vertical smear, upscaled), all on the YouTube dark background #0f0f0f."""
import sys
from PIL import Image, ImageFilter, ImageDraw
def glance(im):
    g = im.resize((im.width // 2, im.height // 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1))
    k = ImageFilter.Kernel((1, 5), [1] * 5) if False else None
    import numpy as np
    a = np.asarray(g).astype(float); a = sum(np.roll(a, s, 0) for s in range(-2, 3)) / 5
    return Image.fromarray(a.clip(0, 255).astype('uint8'))
def round_corners(im, r):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    bg = Image.new('RGB', im.size, (15, 15, 15)); bg.paste(im, (0, 0), m); return bg
out = sys.argv[1]; ims = sys.argv[2:]
rowh = 380; W = 640 + 20 + 390 + 20 + 168 + 20 + 336 + 20 + 168 + 20
sheet = Image.new('RGB', (W, rowh * len(ims)), (15, 15, 15)); d = ImageDraw.Draw(sheet)
for i, p in enumerate(ims):
    im = Image.open(p).convert('RGB'); y = i * rowh + 10; x = 10
    sheet.paste(im.resize((640, 360), Image.LANCZOS), (x, y)); x += 660
    sheet.paste(round_corners(im.resize((390, 219), Image.LANCZOS), 12), (x, y)); x += 410
    s = round_corners(im.resize((168, 94), Image.LANCZOS), 8); sheet.paste(s, (x, y)); x += 188
    sheet.paste(s.resize((336, 188), Image.NEAREST), (x, y)); x += 356
    gl = glance(im.resize((168, 94), Image.LANCZOS)); sheet.paste(gl.resize((168, 94), Image.NEAREST), (x, y))
    d.text((x, y + 100), p.split('/')[-1], fill=(170, 170, 170))
sheet.save(out, quality=90)
