"""Arm A ('South America Points at Antarctica. So Does Africa.'): the real Blue Marble Earth seen from the south-Atlantic
side as an object on a pale warm backdrop; the tapering tips of South America and Africa aim down at a luminous Antarctica.
Usage: python3 target.py OUT.jpg [preview] [key=val ...]"""
import sys, json, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_ep01/work')
from globe import render, ll2v, project
from shade import grade, bg, to_img
from PIL import Image

args = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a)
prev = 'preview' in sys.argv[2:]
SS = 1 if prev else 2
W, H = 1280 * SS, 720 * SS
G = lambda k, d: float(args.get(k, d))
CAM = dict(lat=G('lat', -44), lon=G('lon', -17), dist=G('dist', 2.32), fov=G('fov', 56), lift=G('lift', 0.0), shift=G('shift', 0.0))
eye = ll2v(CAM['lat'], CAM['lon'], CAM['dist'])
f0 = -eye / np.linalg.norm(eye); r0 = np.cross(f0, [0, 0, 1.0]); r0 /= np.linalg.norm(r0); u0 = np.cross(r0, f0)
tgt = -u0 * CAM['lift'] - r0 * CAM['shift']
f = tgt - eye; f /= np.linalg.norm(f); r_ = np.cross(f, [0, 0, 1.0]); r_ /= np.linalg.norm(r_); u = np.cross(r_, f)
sun = -f * G('sf', 0.85) + u * G('su', 0.55) - r_ * G('sr', 0.45)
R = render(eye, tgt, (0, 0, 1), CAM['fov'], W, H, sun=sun, exposure=G('exp', 1.6), ambient=G('amb', 0.22))
col, a = grade(R, ocean=tuple(float(v) for v in args.get('ocean', '0.125,0.15,0.16').split(',')), ocean_sat=0.0, ocean_var=0.7,
               ice_gain=G('ice', 1.12), rim_amt=0.28, land_gain=G('land', 1.22))
ys, xs = np.nonzero(a > 0.5)
cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; Rg = (xs.max() - xs.min()) / 2
bgtop = tuple(float(v) for v in args.get('bgtop', '0.91,0.885,0.845').split(','))
bgbot = tuple(float(v) for v in args.get('bgbot', '0.66,0.632,0.598').split(','))
B = bg(H, W, top=bgtop, bot=bgbot, vign=0.30)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
sh = np.exp(-(((xx - cx - 0.12 * Rg) / (1.05 * Rg)) ** 2 + ((yy - cy - 0.14 * Rg) / (1.0 * Rg)) ** 2) ** 2 * 1.3)
B = B * (1 - 0.22 * sh[..., None])
img = B * (1 - a[..., None]) + col * a[..., None]
im = to_img(img)
if SS > 1:
    im = im.resize((1280, 720), Image.LANCZOS)
im.save(sys.argv[1], quality=94)
proj = lambda p: project(eye, R['basis'], CAM['fov'], W, H, np.atleast_2d(p))[0] / SS
json.dump(dict(cam=CAM, globe=dict(cx=float(cx / SS), cy=float(cy / SS), R=float(Rg / SS)),
               tips=dict(cape_horn=[float(v) for v in proj(ll2v(-55.98, -67.27))], cape_agulhas=[float(v) for v in proj(ll2v(-34.83, 20.0))],
                         south_pole=[float(v) for v in proj(ll2v(-90, 0))])),
          open(sys.argv[1].rsplit('.', 1)[0] + '.json', 'w'), indent=1)
print('saved', sys.argv[1])
