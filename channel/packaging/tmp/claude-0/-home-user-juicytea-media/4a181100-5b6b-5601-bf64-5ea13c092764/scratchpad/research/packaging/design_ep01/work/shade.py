"""Shading + grade for the ep01 repack stills. grade(r, **look) -> float RGB (H,W,3) of the globe only, plus alpha."""
import numpy as np
from globe import smooth


def grade(r, ocean=(0.10, 0.13, 0.15), ocean_var=0.55, ocean_sat=0.25, land_sat=1.0, land_gain=1.15, ice_col=(0.97, 0.98, 1.0),
          ice_gain=1.25, rim=(0.75, 0.86, 0.92), rim_amt=0.55, warm=0.0, night_floor=0.05):
    day = r['day']; water = r['water'][..., None]; ice = r['ice'][..., None]
    lum = r['lum'][..., None]
    # ocean: keep bathymetry as luminance variation, recolour to a low-saturation slate so it does not read as navy
    ob = np.array(ocean)[None, None, :]
    ograd = ob * (1 - ocean_var) + ob * ocean_var * np.clip(lum / 0.18, 0, 2.2)
    ocol = ograd * (1 - ocean_sat) + (day * np.clip(np.array(ocean).mean() / (day.mean(-1, keepdims=True) + 1e-3), 0, 3)) * ocean_sat
    # land: satellite colours, a touch of contrast
    g = day.mean(-1, keepdims=True)
    lcol = np.clip((g + (day - g) * land_sat) * land_gain, 0, 1)
    if warm:
        lcol = lcol * np.array([1 + warm, 1 + warm * 0.4, 1 - warm * 0.6])
    icol = np.clip(np.array(ice_col)[None, None, :] * np.clip(lum * ice_gain, 0, 1.05), 0, 1)
    base = ocol * water + lcol * (1 - water)
    base = base * (1 - ice) + icol * ice
    ndl = r['ndl'][..., None]; amb = r['ambient']
    lit = smooth(-0.15, 0.35, r['ndl0'])[..., None]
    col = base * (amb + r['exposure'] * ndl) * (0.25 + 0.75 * lit) + base * night_floor
    # specular glint on water only, subtle
    fres = r['fres'][..., None]
    col = col * (1 - fres * rim_amt * 0.5) + np.array(rim)[None, None, :] * fres * rim_amt * (0.2 + 0.8 * lit)
    return np.clip(col, 0, 1), r['hit'].astype(np.float32)


def halo(H, W, cx, cy, R, col=(0.70, 0.82, 0.90), width=0.06, amt=0.55):
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.hypot(xx - cx, yy - cy) / R
    a = np.exp(-np.clip(dist - 1, 0, None) / width) * (dist > 0.995) * amt
    return np.array(col)[None, None, :] * a[..., None], a


def bg(H, W, top=(0.06, 0.06, 0.065), bot=(0.03, 0.03, 0.035), vign=0.35):
    yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    g = np.array(top)[None, None, :] * (1 - yy[..., None]) + np.array(bot)[None, None, :] * yy[..., None]
    v = 1 - vign * (((xx - 0.5) ** 2 + (yy - 0.5) ** 2) * 2)[..., None]
    return np.clip(g * v, 0, 1)


def to_img(a):
    from PIL import Image
    return Image.fromarray((np.clip(a, 0, 1) ** (1 / 1.0) * 255 + 0.5).astype(np.uint8))
