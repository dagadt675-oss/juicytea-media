# clouds.py N20.jpg SNPP.jpg BASE_day.jpg OUT.jpg PREVIEW.jpg
# Cloud alpha from two VIIRS CorrectedReflectance true-colour mosaics of the same day (NOAA-20 and Suomi-NPP fly ~50 min apart).
# Per satellite: "whiteness above the cloud-free Blue Marble" = (min(RGB) - min(RGB)_base) / (1 - min(RGB)_base), low saturation.
# Sun glint and swath seams land in different places on the two passes, clouds barely move in 50 min -> take the MIN of both.
# Ice sheets are already white in the base, so they cancel out; sea ice / snow is faded towards the poles.
import sys, numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
W, H = 8192, 4096
def ld(p):
    im = Image.open(p).convert('RGB')
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255
def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
base = ld(sys.argv[3]); mb = base.min(-1); del base
def alpha(p):
    X = ld(p); mx, mn = X.max(-1), X.min(-1)
    white = (mn - mb) / np.maximum(1 - mb, 0.2)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    a = ss(0.05, 0.62, white) * (1 - ss(0.22, 0.45, sat))
    a[mx < 0.03] = -1  # no data
    return a
a1 = alpha(sys.argv[1]); a2 = alpha(sys.argv[2])
v1, v2 = a1 >= 0, a2 >= 0
a = np.where(v1 & v2, np.minimum(a1, a2), np.where(v1, a1, np.where(v2, a2, 0)))
del a1, a2
lat = 90 - (np.arange(H) + 0.5) / H * 180
polar = np.where(lat < 0, 1 - 0.62 * ss(55, 72, -lat), 1 - 0.5 * ss(66, 82, lat))   # sea ice / snow look like cloud near the poles
a = np.clip(a, 0, 1) * polar[:, None]
im = Image.fromarray((a * 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(0.8))
im.save(sys.argv[4], quality=90)
im.resize((1280, 640), Image.LANCZOS).save(sys.argv[5], quality=85)
print(sys.argv[4], im.size, 'mean alpha', round(float(a.mean()), 3))
