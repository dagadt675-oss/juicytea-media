# gibs_bbox.py LAYER TMS DATE LEVEL EXT OUT lon0 lat0 lon1 lat1  -> regional mosaic cropped exactly to bbox (EPSG:4326, tile span 288/2^L deg, 512 px)
import io, sys, math, urllib.request, concurrent.futures as cf
from PIL import Image
layer, tms, date, lvl, ext, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
lon0, lat0, lon1, lat1 = map(float, sys.argv[7:11])
span = 288 / 2**lvl; px = span / 512
c0, c1 = int((lon0 + 180) // span), int((lon1 + 180) // span); r0, r1 = int((90 - lat1) // span), int((90 - lat0) // span)
def get(rc):
    r, c = rc
    url = f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{date}/{tms}/{lvl}/{r}/{c}.{ext}'
    err = None
    for _ in range(3):
        try: return rc, Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read())).convert('RGB')
        except Exception as e: err = e
    print('fail', url, err, file=sys.stderr); return rc, None
img = Image.new('RGB', ((c1 - c0 + 1) * 512, (r1 - r0 + 1) * 512)); nf = 0
with cf.ThreadPoolExecutor(12) as ex:
    for (r, c), t in ex.map(get, [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]):
        if t: img.paste(t, ((c - c0) * 512, (r - r0) * 512))
        else: nf += 1
x0 = (lon0 + 180 - c0 * span) / px; y0 = (90 - lat1 - r0 * span) / px
img = img.crop((round(x0), round(y0), round(x0 + (lon1 - lon0) / px), round(y0 + (lat1 - lat0) / px)))
img.save(out, quality=93); print(out, img.size, 'failed tiles', nf)
