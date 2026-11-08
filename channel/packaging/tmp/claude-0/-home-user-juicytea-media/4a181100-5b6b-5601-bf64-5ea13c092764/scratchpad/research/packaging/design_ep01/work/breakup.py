"""Arm C ('Why the Continents Point South (It's a Breakup)'): the southern continents about 115 million years ago
(GPlates / EarthByte, Mueller et al. 2019 reconstructed coastlines, the same data as the film's Gondwana sequence),
drawn simplified as pale stone pieces: South America and Africa still joined in the north, the South Atlantic tearing
open from the south as a lit seam of new ocean, Antarctica below. Usage: python3 breakup.py OUT.jpg [preview] [key=val ...]"""
import sys, json, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_ep01/work')
from globe import render, ll2v, project, smooth
from shade import bg, to_img
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, distance_transform_edt

args = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a)
prev = 'preview' in sys.argv[2:]
SS = 1 if prev else 2
W, H = 1280 * SS, 720 * SS
G = lambda k, d: float(args.get(k, d))
T = int(G('T', 115))
CAM = dict(lat=G('lat', -50), lon=G('lon', -14), dist=G('dist', 2.25), fov=G('fov', 56), lift=G('lift', 0.0), shift=G('shift', 0.0))

# ---- paleo land raster (equirect, 0.05 deg)
EW, EH = 7200, 3600
polys = json.load(open(f'/home/user/juicytea-media/engine/www/paleo/coast_{T:03d}.json'))
im = Image.new('L', (EW, EH), 0); d = ImageDraw.Draw(im)
for p in polys:
    if len(p) > 2:
        d.polygon([((lo + 180) / 360 * EW, (90 - la) / 180 * EH) for lo, la in p], fill=255)
LAND = gaussian_filter(np.asarray(im).astype(np.float32) / 255, 1.0)
# rift glow: young ocean inside the South Atlantic gap (ocean within ~3 deg of land, inside the rift box)
box = (-33.0, 4.0, -60.0, -10.0)   # lon0, lon1, lat0, lat1
lon_g = (np.arange(EW) + 0.5) / EW * 360 - 180; lat_g = 90 - (np.arange(EH) + 0.5) / EH * 180
inbox = ((lon_g[None, :] > box[0]) & (lon_g[None, :] < box[1]) & (lat_g[:, None] > box[2]) & (lat_g[:, None] < box[3]))
dist = distance_transform_edt(LAND < 0.5) * 0.05                     # degrees to nearest land
# all ocean in the gap, brightest where it is narrowest (the 'zipper'), fading where it has opened wide
soft = gaussian_filter(inbox.astype(np.float32), 50)
RIFT = gaussian_filter((LAND < 0.5).astype(np.float32) * np.exp(-dist / G('riftd', 1.6)), 4) * soft * (LAND < 0.5)
EDGE = np.clip(gaussian_filter(LAND, 6) - LAND, 0, 1)                 # just outside the coasts (shelf glow)


def esample(arr, lat, lon):
    v = np.clip(((90 - lat) / 180 * EH).astype(int), 0, EH - 1); u = np.clip(((lon + 180) / 360 * EW).astype(int), 0, EW - 1)
    return arr[v, u]


STONE = np.array([float(v) for v in args.get('stone', '0.88,0.86,0.815').split(',')])
SEA = np.array([float(v) for v in args.get('sea', '0.11,0.135,0.145').split(',')])
GLOW = np.array([float(v) for v in args.get('glow', '0.45,0.92,0.95').split(',')])


def mod(lat, lon, day, n, up, east, north):
    l = esample(LAND, lat, lon)[..., None]; rf = esample(RIFT, lat, lon)[..., None]; ed = esample(EDGE, lat, lon)[..., None]
    sea = SEA * (1 - 0.25 * ed) + 0 * ed
    c = sea * (1 - l) + STONE * l
    # bevel normal from the land mask gradient (pieces read as raised cut-outs)
    h = 0.0035
    dx = (esample(LAND, lat, lon + h / np.maximum(np.cos(np.radians(lat)), 0.05) * 57.3) - esample(LAND, lat, lon - h / np.maximum(np.cos(np.radians(lat)), 0.05) * 57.3))
    dy = (esample(LAND, lat + h * 57.3, lon) - esample(LAND, lat - h * 57.3, lon))
    k = G('bevel', 0.9)
    nn = up - (east * dx[..., None] + north * dy[..., None]) * k
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    return c, nn, dict(land=l[..., 0], rift=rf[..., 0])


eye = ll2v(CAM['lat'], CAM['lon'], CAM['dist'])
f0 = -eye / np.linalg.norm(eye); r0 = np.cross(f0, [0, 0, 1.0]); r0 /= np.linalg.norm(r0); u0 = np.cross(r0, f0)
tgt = -u0 * CAM['lift'] - r0 * CAM['shift']
f = tgt - eye; f /= np.linalg.norm(f); r_ = np.cross(f, [0, 0, 1.0]); r_ /= np.linalg.norm(r_); u = np.cross(r_, f)
sun = -f * G('sf', 0.80) + u * G('su', 0.55) - r_ * G('sr', 0.50)
R = render(eye, tgt, (0, 0, 1), CAM['fov'], W, H, sun=sun, exposure=1.0, ambient=0.3, mod=mod)
a = R['hit'].astype(np.float32)
lit = smooth(-0.2, 0.5, R['ndl0'])
ndl = R['ndl']
day = R['day']
col = day * (G('amb', 0.30) + G('exp', 0.85) * ndl)[..., None] * (0.35 + 0.65 * lit)[..., None]
# luminous new ocean: additive glow, strongest at the seam's centre, independent of sun
rift = R['extra']['rift'] * (1 - R['extra']['land'])
col = col + (rift ** 0.8)[..., None] * GLOW[None, None, :] * G('gamt', 0.95)
# soft halo of the seam onto the nearby stone edges
halo = gaussian_filter(rift, 6 * SS) * R['extra']['land']
col = col + halo[..., None] * GLOW * 0.35
# limb haze
fres = R['fres'][..., None]
col = col * (1 - 0.35 * fres) + np.array([0.62, 0.70, 0.72]) * 0.35 * fres * (0.3 + 0.7 * lit[..., None])
col = np.clip(col, 0, 1)
ys, xs = np.nonzero(a > 0.5)
cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; Rg = (xs.max() - xs.min()) / 2
bgtop = tuple(float(v) for v in args.get('bgtop', '0.105,0.105,0.11').split(','))
bgbot = tuple(float(v) for v in args.get('bgbot', '0.06,0.06,0.065').split(','))
B = bg(H, W, top=bgtop, bot=bgbot, vign=0.25)
# faint cyan bounce around the globe from the seam side (keeps the frame from sinking into a dark page)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.hypot(xx - cx, yy - cy) / Rg
B = B + (np.exp(-np.clip(rr - 1, 0, None) / 0.10) * (rr > 1))[..., None] * np.array([0.30, 0.36, 0.37]) * G('rim', 0.55)
img = B * (1 - a[..., None]) + col * a[..., None]
im = to_img(img)
if SS > 1:
    im = im.resize((1280, 720), Image.LANCZOS)
im.save(sys.argv[1], quality=94)
json.dump(dict(cam=CAM, T=T, data='GPlates web service, MULLER2019 coastlines, coast_%03d.json' % T), open(sys.argv[1].rsplit('.', 1)[0] + '.json', 'w'), indent=1)
print('saved', sys.argv[1])
