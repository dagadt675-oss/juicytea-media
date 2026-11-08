"""Minimal ray-cast globe for ep01 repackage stills (same NASA Blue Marble day texture + DEM normal map as the film engine).
render(cam, W, H) -> dict with float RGB (0..1) of the shaded globe on transparent bg, alpha mask, lat/lon, water/ice masks, N.dot(L).
Coordinates: x=cos(lat)cos(lon), y=cos(lat)sin(lon), z=sin(lat) (z = north), Earth radius 1."""
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
TEX = '/home/user/juicytea-media/engine/www/tex/'
_cache = {}


def tex(name):
    if name not in _cache:
        _cache[name] = np.asarray(Image.open(TEX + name).convert('RGB'))
    return _cache[name]


def ll2v(lat, lon, r=1.0):
    la, lo = np.radians(lat), np.radians(lon)
    return np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]) * r


def sample(img, lat, lon):
    """bilinear sample of an equirect image (lon -180..180 left->right, lat 90..-90 top->bottom)"""
    h, w, _ = img.shape
    u = (lon + 180.0) / 360.0 * w - 0.5
    v = (90.0 - lat) / 180.0 * h - 0.5
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
    fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    u0m = u0 % w; u1 = (u0 + 1) % w
    v0c = np.clip(v0, 0, h - 1); v1 = np.clip(v0 + 1, 0, h - 1)
    a = img[v0c, u0m].astype(np.float32); b = img[v0c, u1].astype(np.float32)
    c = img[v1, u0m].astype(np.float32); d = img[v1, u1].astype(np.float32)
    return ((a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv) / 255.0


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def camera(eye, target, up_hint, fov, W, H):
    eye = np.asarray(eye, float); target = np.asarray(target, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up_hint); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    tanv = np.tan(np.radians(fov) / 2); tanh = tanv * W / H
    xs = (np.arange(W) + 0.5) / W * 2 - 1; ys = 1 - (np.arange(H) + 0.5) / H * 2
    X, Y = np.meshgrid(xs * tanh, ys * tanv)
    d = f[None, None, :] + X[..., None] * r[None, None, :] + Y[..., None] * u[None, None, :]
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    return eye, d, (f, r, u)


def render(eye, target, up_hint=(0, 0, 1), fov=34, W=1280, H=720, sun=None, relief=0.9, exposure=1.25, ambient=0.10, mod=None):
    eye, d, (f, r, u) = camera(eye, target, np.asarray(up_hint, float), fov, W, H)
    # ray-sphere
    b = np.einsum('ijk,k->ij', d, eye); c = eye @ eye - 1.0
    disc = b * b - c
    hit = disc > 0
    t = -b - np.sqrt(np.where(hit, disc, 0))
    P = eye[None, None, :] + t[..., None] * d
    P /= np.linalg.norm(P, axis=-1, keepdims=True)
    lat = np.degrees(np.arcsin(np.clip(P[..., 2], -1, 1))); lon = np.degrees(np.arctan2(P[..., 1], P[..., 0]))
    day = sample(tex('day_8k.jpg'), lat, lon)
    nm = sample(tex('normal_4k.png'), lat, lon) * 2 - 1
    up = P
    east = np.stack([-np.sin(np.radians(lon)), np.cos(np.radians(lon)), np.zeros_like(lon)], -1)
    north = np.cross(up, east)
    n = nm[..., 0:1] * east + nm[..., 1:2] * north + nm[..., 2:3] * up
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    n = up * (1 - relief) + n * relief; n /= np.linalg.norm(n, axis=-1, keepdims=True)
    extra = {}
    if mod is not None:
        day, n, extra = mod(lat, lon, day, n, up, east, north)
    if sun is None:
        sun = -f * 0.6 + u * 0.45 - r * 0.45
    L = np.asarray(sun, float); L /= np.linalg.norm(L)
    ndl = np.clip(np.einsum('ijk,k->ij', n, L), 0, None)
    ndl0 = np.einsum('ijk,k->ij', up, L)
    water = smooth(0.03, 0.16, day[..., 2] - np.maximum(day[..., 0], day[..., 1] * 0.9))
    lum = day @ np.array([0.299, 0.587, 0.114])
    sat = day.max(-1) - day.min(-1)
    ice = smooth(0.55, 0.75, lum) * smooth(0.18, 0.08, sat) * (1 - water)
    view = -d
    fres = (1 - np.clip(np.einsum('ijk,ijk->ij', up, view), 0, 1)) ** 3
    return dict(hit=hit, lat=lat, lon=lon, day=day, ndl=ndl, ndl0=ndl0, water=water, ice=ice, lum=lum, fres=fres,
                exposure=exposure, ambient=ambient, P=P, d=d, eye=eye, basis=(f, r, u), L=L, t=t, n=n, extra=extra)


def project(eye, basis, fov, W, H, pts):
    """3D points (N,3) -> pixel coords (N,2) for the same camera"""
    f, r, u = basis; tanv = np.tan(np.radians(fov) / 2); tanh = tanv * W / H
    v = np.asarray(pts, float) - eye
    z = v @ f; x = (v @ r) / z / tanh; y = (v @ u) / z / tanv
    return np.stack([(x + 1) / 2 * W, (1 - y) / 2 * H], -1)


def orbit(lat, lon, alt, tilt=0.0, heading=0.0):
    """engine-style camera: above (lat,lon) at altitude alt (Earth radii), tilted `tilt` deg from nadir toward `heading` (0=north, 90=east).
    returns eye, target, up_hint"""
    P = ll2v(lat, lon); eye = P * (1 + alt)
    la, lo = np.radians(lat), np.radians(lon)
    east = np.array([-np.sin(lo), np.cos(lo), 0.0]); north = np.cross(P, east)
    hd = np.radians(heading); hz = north * np.cos(hd) + east * np.sin(hd)
    t = np.radians(tilt)
    fwd = -P * np.cos(t) + hz * np.sin(t)
    up = hz * np.cos(t) + P * np.sin(t)
    return eye, eye + fwd, up


def look(lat, lon, rng, tilt=0.0, heading=0.0, r=1.0):
    """camera looking at surface point (lat,lon) [radius r] from distance rng, tilted `tilt` deg from the local vertical,
    viewing toward `heading` (0 = north is up in frame). returns eye, target, up_hint"""
    P = ll2v(lat, lon); T = P * r
    lo = np.radians(lon)
    east = np.array([-np.sin(lo), np.cos(lo), 0.0]); north = np.cross(P, east)
    hd = np.radians(heading); hz = north * np.cos(hd) + east * np.sin(hd)
    t = np.radians(tilt)
    eye = T + rng * (P * np.cos(t) - hz * np.sin(t))
    return eye, T, hz * np.cos(t) + P * np.sin(t)
