#!/usr/bin/env python3
"""Regional GIBS patch (EPSG:4326, 512 px tiles, span 288/2^L deg) cropped to bounds -> JPEG for Globe.setPatch.
Usage: python3 -I gibs_patch.py LON0 LAT0 LON1 LAT1 OUT.jpg [--layer BlueMarble_ShadedRelief_Bathymetry --tms 500m --level 7 --ext jpeg]"""
import io, sys, math, urllib.request, concurrent.futures as cf
from PIL import Image
a = sys.argv; lon0, lat0, lon1, lat1 = map(float, a[1:5]); out = a[5]
opt = lambda k, d: type(d)(a[a.index('--' + k) + 1]) if '--' + k in a else d
layer, tms, lvl, ext = opt('layer', 'BlueMarble_ShadedRelief_Bathymetry'), opt('tms', '500m'), opt('level', 7), opt('ext', 'jpeg')
span = 288 / 2 ** lvl
c0, c1 = int((lon0 + 180) // span), int((lon1 + 180) // span); r0, r1 = int((90 - lat1) // span), int((90 - lat0) // span)
def get(rc):
    r, c = rc; url = f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{tms}/{lvl}/{r}/{c}.{ext}'
    for _ in range(3):
        try: return rc, Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read())).convert('RGB')
        except Exception as e: err = e
    print('fail', url, err, file=sys.stderr); return rc, None
img = Image.new('RGB', ((c1 - c0 + 1) * 512, (r1 - r0 + 1) * 512))
with cf.ThreadPoolExecutor(12) as ex:
    for (r, c), t in ex.map(get, [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]):
        if t: img.paste(t, ((c - c0) * 512, (r - r0) * 512))
ppd = 512 / span; x0 = (lon0 + 180 - c0 * span) * ppd; y0 = (90 - lat1 - r0 * span) * ppd
img = img.crop((round(x0), round(y0), round(x0 + (lon1 - lon0) * ppd), round(y0 + (lat1 - lat0) * ppd)))
img.save(out, quality=90); print(out, img.size, 'tiles', (c1 - c0 + 1) * (r1 - r0 + 1))
