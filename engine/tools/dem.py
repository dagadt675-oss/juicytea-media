#!/usr/bin/env python3
"""dem.py Z W H outprefix [lon0 lat0 lon1 lat1]
Fetch AWS Terrarium elevation tiles (Mapzen/Tilezen, sources SRTM/GMTED/ETOPO1 etc.) at zoom Z,
reproject to an equirectangular grid W x H over the bbox (default world, lat clipped at +-85.05 and edge-extended),
and write: <prefix>_h.npy (float32 metres), <prefix>_hgt16.png (RG = (h+11000)*... 16-bit packed), <prefix>_normal.png, <prefix>_shade.png."""
import io, sys, math, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
Z, W, H, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
bb = [float(x) for x in sys.argv[5:9]] if len(sys.argv) >= 9 else [-180, -90, 180, 90]
n = 2 ** Z
def lat2y(lat): lat = max(min(lat, 85.0511), -85.0511); r = math.radians(lat); return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n
def lon2x(lon): return (lon + 180) / 360 * n
x0, x1 = int(math.floor(lon2x(bb[0]))), int(math.ceil(lon2x(bb[2]))) - 1
y0, y1 = int(math.floor(lat2y(bb[3]))), int(math.ceil(lat2y(bb[1]))) - 1
x0 = max(0, x0); x1 = min(n - 1, x1); y0 = max(0, y0); y1 = min(n - 1, y1)
def get(xy):
    x, y = xy
    url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png'
    for _ in range(4):
        try:
            im = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read())).convert('RGB')
            a = np.asarray(im).astype(np.float32)
            return xy, a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        except Exception as e: err = e
    print('fail', url, err, file=sys.stderr); return xy, np.zeros((256, 256), np.float32)
mos = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), np.float32)
with cf.ThreadPoolExecutor(16) as ex:
    for (x, y), a in ex.map(get, [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]):
        mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a
# reproject: for each output pixel, find mercator pixel (bilinear)
lons = bb[0] + (np.arange(W) + 0.5) / W * (bb[2] - bb[0])
lats = bb[3] - (np.arange(H) + 0.5) / H * (bb[3] - bb[1])
mx = ((lons + 180) / 360 * n - x0) * 256 - 0.5
lr = np.radians(np.clip(lats, -85.0511, 85.0511))
my = ((1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / np.pi) / 2 * n - y0) * 256 - 0.5
MX, MY = np.meshgrid(mx, my)
MX = np.clip(MX, 0, mos.shape[1] - 1.001); MY = np.clip(MY, 0, mos.shape[0] - 1.001)
ix, iy = MX.astype(int), MY.astype(int); fx, fy = MX - ix, MY - iy
h = (mos[iy, ix] * (1 - fx) * (1 - fy) + mos[iy, ix + 1] * fx * (1 - fy) + mos[iy + 1, ix] * (1 - fx) * fy + mos[iy + 1, ix + 1] * fx * fy).astype(np.float32)
np.save(out + '_h.npy', h)
# 16-bit packing into RG: v = (h + 11000) / 20000 * 65535
v = np.clip((h + 11000) / 20000 * 65535, 0, 65535).astype(np.uint32)
rgb = np.stack([(v >> 8).astype(np.uint8), (v & 255).astype(np.uint8), np.zeros_like(v, np.uint8)], -1)
Image.fromarray(rgb).save(out + '_hgt16.png')
# normals (equirect, exaggerated), scale: metres per pixel in x varies with latitude
R = 6371000.0
dlon = math.radians((bb[2] - bb[0]) / W); dlat = math.radians((bb[3] - bb[1]) / H)
coslat = np.cos(np.radians(lats))[:, None]
ex = float(sys.argv[9]) if len(sys.argv) > 9 else 18.0
hl = np.maximum(h, 0) * ex + np.minimum(h, 0) * ex * 0.25
gx = (np.roll(hl, -1, 1) - np.roll(hl, 1, 1)) / (2 * R * dlon * np.maximum(coslat, 0.05))
gy = (np.roll(hl, 1, 0) - np.roll(hl, -1, 0)) / (2 * R * dlat)
nz = 1 / np.sqrt(gx ** 2 + gy ** 2 + 1)
nrm = np.stack([-gx * nz, -gy * nz, nz], -1)  # tangent space: x=east, y=north, z=up
Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(out + '_normal.png')
# simple hillshade preview (sun from NW)
L = np.array([-0.5, 0.5, 0.7]); L /= np.linalg.norm(L)
shade = np.clip((nrm @ L), 0, 1)
Image.fromarray((shade * 255).astype(np.uint8)).save(out + '_shade.png')
print(out, h.shape, float(h.min()), float(h.max()))
