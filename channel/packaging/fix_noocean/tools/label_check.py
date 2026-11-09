"""label_check.py IMG [...]: label vs surround contrast at 168x94 after a 1.1 px blur (playbook spec: 100+ levels), and bottom-band luma.
Label box = NO OCEAN at x 0.955 right-anchored, y 0.035, cap 0.155; text pixels = darkest 35% inside the box, surround = a 6 px ring outside it."""
import sys, numpy as np
from PIL import Image, ImageFilter
for p in sys.argv[1:]:
    im = Image.open(p).convert('RGB'); s = im.resize((168, 94), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1))
    a = np.asarray(s).astype(float); l = (a * [0.2126, 0.7152, 0.0722]).sum(-1)
    full = (np.asarray(im).astype(float) * [0.2126, 0.7152, 0.0722]).sum(-1)
    # find the text box from the full-size image: charcoal pixels (luma < 40) in the top 25% right 55%
    m = full[:int(0.25 * 720), int(0.45 * 1280):] < 40
    ys, xs = np.where(m); y0, y1 = ys.min(), ys.max(); x0, x1 = xs.min() + int(0.45 * 1280), xs.max() + int(0.45 * 1280)
    sy, sx = 94 / 720, 168 / 1280; Y0, Y1, X0, X1 = int(y0 * sy), int(np.ceil(y1 * sy)), int(x0 * sx), int(np.ceil(x1 * sx))
    box = l[Y0:Y1 + 1, X0:X1 + 1]; txt = np.sort(box.ravel())[:max(1, int(box.size * 0.35))].mean()
    ring = np.ones_like(l, bool); ring[max(Y0 - 6, 0):Y1 + 7, max(X0 - 6, 0):X1 + 7] = False
    ring2 = np.zeros_like(l, bool); ring2[max(Y0 - 6, 0):Y1 + 7, max(X0 - 6, 0):X1 + 7] = True; ring2[Y0:Y1 + 1, X0:X1 + 1] = False
    sur = l[ring2].mean()
    print(p.split('/')[-1], 'label cap px', y1 - y0 + 1, f'({(y1 - y0 + 1) / 720:.3f} of height, incl. any descender)', 'width', f'{(x1 - x0 + 1) / 1280:.2f}',
          '| 168x94 text', round(txt), 'surround', round(sur), 'contrast', round(sur - txt), '| bottom 15% luma', round(full[int(0.85 * 720):].mean()), 'bottom 30%', round(full[int(0.7 * 720):].mean()))
