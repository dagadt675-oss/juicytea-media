#!/usr/bin/env python3
"""gibs.py LAYER DATE LEVEL EXT out.jpg [lon0 lat0 lon1 lat1]
Stitch NASA GIBS (public domain) EPSG:4326 tiles (TileMatrixSet 500m, 512 px tiles) into one image.
Level n: tile spans 288/2^n degrees. Whole world by default (-180,-90,180,90)."""
import io, sys, math, urllib.request, concurrent.futures as cf
from PIL import Image
layer, date, lvl, ext, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
bb = [float(x) for x in sys.argv[6:10]] if len(sys.argv) >= 10 else [-180, -90, 180, 90]
span = 288 / 2**lvl; px = 512
c0 = int(math.floor((bb[0] + 180) / span)); c1 = int(math.ceil((bb[2] + 180) / span)) - 1
r0 = int(math.floor((90 - bb[3]) / span)); r1 = int(math.ceil((90 - bb[1]) / span)) - 1
def get(rc):
    r, c = rc
    url = f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{date}/500m/{lvl}/{r}/{c}.{ext}'
    for attempt in range(4):
        try:
            return rc, Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read())).convert('RGB')
        except Exception as e:
            err = e
    print('fail', url, err, file=sys.stderr); return rc, None
W, H = (c1 - c0 + 1) * px, (r1 - r0 + 1) * px
img = Image.new('RGB', (W, H))
with cf.ThreadPoolExecutor(12) as ex:
    for (r, c), t in ex.map(get, [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]):
        if t: img.paste(t, ((c - c0) * px, (r - r0) * px))
# crop to exact bbox
x0 = (bb[0] + 180 - c0 * span) / span * px; x1 = (bb[2] + 180 - c0 * span) / span * px
y0 = (90 - bb[3] - r0 * span) / span * px; y1 = (90 - bb[1] - r0 * span) / span * px
img = img.crop((round(x0), round(y0), round(x1), round(y1)))
img.save(out, quality=93)
print(out, img.size)
