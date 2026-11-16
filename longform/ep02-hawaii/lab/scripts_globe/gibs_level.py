# gibs_level.py LAYER TMS DATE LEVEL EXT OUT  -> whole-world mosaic at a GIBS EPSG:4326 level (tile span 288/2^L deg, 512 px)
import io, sys, math, urllib.request, concurrent.futures as cf
from PIL import Image
layer, tms, date, lvl, ext, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
span = 288 / 2**lvl; cols = math.ceil(360 / span); rows = math.ceil(180 / span)
def get(rc):
    r, c = rc
    d = f'{date}/' if date != '-' else 'default/'
    url = f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{date}/{tms}/{lvl}/{r}/{c}.{ext}' if date != '-' else f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{layer}/default/{tms}/{lvl}/{r}/{c}.{ext}'
    for _ in range(3):
        try: return rc, Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=60).read())).convert('RGB')
        except Exception as e: err = e
    print('fail', url, err, file=sys.stderr); return rc, None
img = Image.new('RGB', (cols * 512, rows * 512))
with cf.ThreadPoolExecutor(12) as ex:
    for (r, c), t in ex.map(get, [(r, c) for r in range(rows) for c in range(cols)]):
        if t: img.paste(t, (c * 512, r * 512))
W = round(360 / span * 512); H = round(180 / span * 512)
img = img.crop((0, 0, W, H)); img.save(out, quality=92); print(out, img.size)
