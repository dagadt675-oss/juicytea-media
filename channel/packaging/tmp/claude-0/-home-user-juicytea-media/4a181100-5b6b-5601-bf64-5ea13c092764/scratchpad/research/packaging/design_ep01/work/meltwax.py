"""Arm B ('Spin a Globe and Earth Looks Like It's Melting'): a wax-white globe (present-day coastlines, GPlates coast_000)
on a hot amber backdrop; the southern tips of South America and Africa droop and drip like candle wax.
Usage: python3 meltwax.py OUT.jpg [preview] [key=val ...]"""
import sys, json, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_ep01/work')
from globe import render, ll2v, project, smooth
from shade import bg, to_img
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

args = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a)
prev = 'preview' in sys.argv[2:]
SS = 1 if prev else 2
W, H = 1280 * SS, 720 * SS
G = lambda k, d: float(args.get(k, d))
CAM = dict(lat=G('lat', -34), lon=G('lon', -22), dist=G('dist', 2.55), fov=G('fov', 50), lift=G('lift', 0.0), shift=G('shift', 0.0))
EW, EH = 7200, 3600
polys = json.load(open('/home/user/juicytea-media/engine/www/paleo/coast_000.json'))
im = Image.new('L', (EW, EH), 0); d = ImageDraw.Draw(im)
P = lambda lat, lon: ((lon + 180) / 360 * EW, (90 - lat) / 180 * EH)
for p in polys:
    if len(p) > 2:
        d.polygon([P(la, lo) for lo, la in p], fill=255)
DR = json.loads(args['drips']) if 'drips' in args else [
    dict(lat=-49.0, lon=-69.8, L=15.0, wt=3.6, wn=1.5, rb=2.0, sway=0.7, ph=0.4),
    dict(lat=-31.0, lon=21.0, L=21.0, wt=4.6, wn=1.8, rb=2.4, sway=1.0, ph=1.9),
    dict(lat=-33.5, lon=26.5, L=8.0, wt=2.2, wn=1.0, rb=1.25, sway=0.4, ph=0.9),
]
for q in DR:
    left, right = [], []
    for s in np.linspace(0, 1, 120):
        la = q['lat'] - s * (q['L'] - q['rb'])
        w = q['wt'] * (1 + 0.15 * np.exp(-((s - 0.25) / 0.12) ** 2)) + (q['wn'] - q['wt']) * smooth(0.2, 0.95, s)
        w *= 1 + 0.06 * np.sin(s * 15 + q['ph'])
        lo = q['lon'] + q['sway'] * np.sin(s * 4 + q['ph']) * smooth(0.1, 0.5, s) / np.cos(np.radians(la))
        hw = w / 2 / np.cos(np.radians(la))
        left.append(P(la, lo - hw)); right.append(P(la, lo + hw))
    d.polygon(left + right[::-1], fill=255)
    bl = q['lat'] - q['L'] + q['rb']; blo = q['lon'] + q['sway'] * np.sin(4 + q['ph']) / np.cos(np.radians(bl))
    rx = q['rb'] / np.cos(np.radians(bl)) / 360 * EW; ry = q['rb'] / 180 * EH
    cxp, cyp = P(bl, blo); d.ellipse([cxp - rx, cyp - ry, cxp + rx, cyp + ry * 1.05], fill=255)
LAND = gaussian_filter(np.asarray(im).astype(np.float32) / 255, 0.8)
HGT = gaussian_filter(LAND, G('hblur', 10))


def esample(arr, lat, lon):
    v = np.clip(((90 - lat) / 180 * EH).astype(int), 0, EH - 1); u = np.clip(((lon + 180) / 360 * EW).astype(int), 0, EW - 1)
    return arr[v, u]


WAX = np.array([float(v) for v in args.get('wax', '0.93,0.905,0.855').split(',')])
SEA = np.array([float(v) for v in args.get('sea', '0.10,0.125,0.135').split(',')])


def mod(lat, lon, day, n, up, east, north):
    l = esample(LAND, lat, lon)[..., None]
    c = SEA * (1 - l) + WAX * l
    h = 0.0040; cl = np.maximum(np.cos(np.radians(lat)), 0.05)
    dx = esample(HGT, lat, lon + h / cl * 57.3) - esample(HGT, lat, lon - h / cl * 57.3)
    dy = esample(HGT, lat + h * 57.3, lon) - esample(HGT, lat - h * 57.3, lon)
    k = G('bevel', 2.2)
    nn = up - (east * dx[..., None] + north * dy[..., None]) * k
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    return c, nn, dict(land=l[..., 0])


eye = ll2v(CAM['lat'], CAM['lon'], CAM['dist'])
f0 = -eye / np.linalg.norm(eye); r0 = np.cross(f0, [0, 0, 1.0]); r0 /= np.linalg.norm(r0); u0 = np.cross(r0, f0)
tgt = -u0 * CAM['lift'] - r0 * CAM['shift']
f = tgt - eye; f /= np.linalg.norm(f); r_ = np.cross(f, [0, 0, 1.0]); r_ /= np.linalg.norm(r_); u = np.cross(r_, f)
sun = -f * G('sf', 0.75) + u * G('su', 0.60) - r_ * G('sr', 0.55)
R = render(eye, tgt, (0, 0, 1), CAM['fov'], W, H, sun=sun, exposure=1.0, ambient=0.3, mod=mod)
a = R['hit'].astype(np.float32)
lit = smooth(-0.2, 0.5, R['ndl0'])
land = R['extra']['land']
col = R['day'] * (G('amb', 0.28) + G('exp', 0.85) * R['ndl'])[..., None] * (0.35 + 0.65 * lit)[..., None]
# warm bounce from the hot backdrop on the lower/shadow side of the wax
col = col + (land * (1 - lit) * 0.08)[..., None] * np.array([0.85, 0.9, 0.95])
V = -R['d']; L = R['L']; Hh = V + L[None, None, :]; Hh /= np.linalg.norm(Hh, axis=-1, keepdims=True)
nh = np.clip(np.einsum('ijk,ijk->ij', R['n'], Hh), 0, 1)
col = col + ((nh ** 40 * 0.55 + nh ** 6 * 0.06) * land)[..., None] * np.array([1.0, 0.98, 0.94])
fres = R['fres'][..., None]
col = col * (1 - 0.30 * fres) + np.array([0.80, 0.86, 0.90]) * 0.30 * fres * (0.4 + 0.6 * lit[..., None])
col = np.clip(col, 0, 1)
ys, xs = np.nonzero(a > 0.5)
cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; Rg = (xs.max() - xs.min()) / 2
bgtop = tuple(float(v) for v in args.get('bgtop', '0.98,0.70,0.30').split(','))
bgbot = tuple(float(v) for v in args.get('bgbot', '0.80,0.40,0.13').split(','))
B = bg(H, W, top=bgtop, bot=bgbot, vign=0.35)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glare = np.exp(-(((xx / W - 0.12) / 0.35) ** 2 + ((yy / H - 0.05) / 0.45) ** 2))
B = np.clip(B + glare[..., None] * np.array([0.10, 0.10, 0.06]), 0, 1)
sh = np.exp(-(((xx - cx - 0.14 * Rg) / (1.05 * Rg)) ** 2 + ((yy - cy - 0.16 * Rg) / (1.0 * Rg)) ** 2) ** 2 * 1.3)
B = B * (1 - 0.28 * sh[..., None])
img = B * (1 - a[..., None]) + col * a[..., None]
HANG = json.loads(args['hang']) if 'hang' in args else []
proj = lambda p: project(eye, R['basis'], CAM['fov'], W, H, np.atleast_2d(p))[0]
hang_info = []
for hq, q in zip(HANG, DR):
    # last visible point of the drip centreline = where it pours over the silhouette
    last = None
    for s_ in np.linspace(0, 1, 400):
        la = q['lat'] - s_ * (q['L'] - q['rb'])
        lo = q['lon'] + q['sway'] * np.sin(s_ * 4 + q['ph']) * smooth(0.1, 0.5, s_) / np.cos(np.radians(la))
        Pp = ll2v(la, lo)
        if Pp @ (eye - Pp) > 0.02: last = proj(Pp)
    if last is None: continue
    x0, y0 = last; y0 = y0 - hq.get('up', 0.01) * Rg
    Lh = hq['len'] * Rg; w0 = hq['w'] * Rg; br = hq['bulb'] * Rg
    ys_ = np.arange(int(y0), int(y0 + Lh + br * 1.1))
    t = (ys_ - y0) / Lh
    xc = x0 + hq.get('drift', 0.0) * Rg * t ** 2
    wid = w0 * (1 - 0.45 * smooth(0, 0.85, t)) * (1 + 0.12 * np.exp(-((t - 0.35) / 0.1) ** 2))
    tb = (ys_ - (y0 + Lh)) / br
    wid = np.maximum(np.where(t < 1, wid, 0), 2 * br * np.sqrt(np.clip(1 - tb ** 2, 0, 1)))
    for i, y in enumerate(ys_):
        if y < 0 or y >= H or wid[i] < 1: continue
        hw = wid[i] / 2; xr = np.arange(max(int(xc[i] - hw - 2), 0), min(int(xc[i] + hw + 3), W))
        sx = (xr - xc[i]) / hw; cov = np.clip(hw - np.abs(xr - xc[i]) + 0.5, 0, 1)
        nz = np.sqrt(np.clip(1 - np.clip(sx, -1, 1) ** 2, 0, 1))
        dif = 0.40 + 0.62 * np.clip(-0.5 * sx + 0.86 * nz, 0, 1)
        cc = WAX[None, :] * dif[:, None] + (np.exp(-((sx + 0.42) / 0.14) ** 2) * nz * 0.35)[:, None]
        cc = cc + ((1 - nz) * 0.08)[:, None] * np.array([1.0, 0.55, 0.2])
        img[y, xr] = img[y, xr] * (1 - cov[:, None]) + np.clip(cc, 0, 1) * cov[:, None]
    hang_info.append(dict(x=float(x0 / SS), y=float(y0 / SS), end=float((y0 + Lh) / SS)))
im = to_img(img)
if SS > 1:
    im = im.resize((1280, 720), Image.LANCZOS)
im.save(sys.argv[1], quality=94)
json.dump(dict(cam=CAM, drips=DR, data='coastlines: GPlates coast_000 (MULLER2019 present day)'), open(sys.argv[1].rsplit('.', 1)[0] + '.json', 'w'), indent=1)
print('saved', sys.argv[1])
