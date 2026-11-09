#!/usr/bin/env python3
"""Paper cut-out from a public-domain photo (ep02 paper kit). Run with the scratchpad venv (numpy, onnxruntime) and -I:
  venv/bin/python -I paper_cut.py SPEC.json --model isnet-general-use.onnx --srcdir DOWNLOADS --outdir ../img/paper
SPEC (tools/paper_specs/*.json): {"name": "tourist", "src": "8a26766u.tif" (file in --srcdir; its page and licence in
       img/SOURCES.md), "box": [x0, y0, x1, y1],
       "keep": [[x, y], ...] (polygon, source px: everything outside is dropped), "drop": [[[x, y], ...], ...] (polygons removed),
       "add": [[[x, y], ...], ...] (polygons forced in), "h": 900 (output height), "erode": 2, "flip": false,
       "tint": [{"poly": [[x, y], ...], "color": "#C8302A", "levels": [lo, hi], "amt": 1.0, "pattern": "aloha"}],
       "parts": {"hat": [[x, y], ...]} (each part polygon is cut out of the body into OUT_<part>.png, with its anchor in the json)}
The matte comes from IS-Net (isnet-general-use, Apache-2.0, downloaded to the scratchpad and deleted after use: never in git), then:
largest component, holes filled, keep/drop/add polygons, eroded 2-3 px (no spill), edge colours pulled from the interior
(decontaminated), supersampled down to the output height. B&W photos are hand-tinted per polygon, keeping the photo's tones.
Writes OUT.png (RGBA) and OUT.json (size, parts and their anchors in output px)."""
import sys, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

spec = json.load(open(sys.argv[1]))
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
spec['model'] = arg('--model', spec.get('model'))
spec['out'] = os.path.join(arg('--outdir', '.'), spec['name'] + '.png') if 'name' in spec else spec['out']
srcp = os.path.join(arg('--srcdir', '.'), spec['src'])
Image.MAX_IMAGE_PIXELS = None
src = Image.open(srcp)
src = src.convert('RGB')
x0, y0, x1, y1 = spec['box']
crop = src.crop((x0, y0, x1, y1)); W, H = crop.size

def poly_mask(polys, shape):
    m = Image.new('L', (shape[1], shape[0]), 0); d = ImageDraw.Draw(m)
    for p in polys: d.polygon([(x - x0, y - y0) for x, y in p], fill=255)
    return np.asarray(m) > 127

# --- IS-Net matte (rembg's preprocessing: 1024x1024, mean 0.5, std 1.0, min-max normalised output)
import onnxruntime as ort
sess = ort.InferenceSession(spec['model'], providers=['CPUExecutionProvider'])
x = np.asarray(crop.resize((1024, 1024), Image.BILINEAR), dtype=np.float32) / 255.0
x = (x - 0.5) / 1.0
y = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
y = (y - y.min()) / max(y.max() - y.min(), 1e-6)
soft = np.asarray(Image.fromarray((y * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), dtype=np.float32) / 255.0
m = soft > spec.get('thr', 0.5)
if spec.get('keep'): m &= poly_mask([spec['keep']], m.shape)
for p in spec.get('drop', []): m &= ~poly_mask([p], m.shape)
for p in spec.get('add', []): m |= poly_mask([p], m.shape)
lab, n = ndi.label(m)
if n > 1:
    sizes = ndi.sum(m, lab, range(1, n + 1)); keepc = [i + 1 for i, s in enumerate(sizes) if s >= spec.get('minFrac', 0.08) * sizes.max()]
    m = np.isin(lab, keepc)
m = ndi.binary_fill_holes(m)
m = ndi.binary_opening(m, iterations=1)
e = spec.get('erode', 2)
if e: m = ndi.binary_erosion(m, iterations=e)

rgb = np.asarray(crop, dtype=np.float32) / 255.0
# --- hand tint (B&W sources): luminance remapped by levels, multiplied by the tint, optional aloha print
rng = np.random.default_rng(7)
def aloha(shape, scale):
    # pale hibiscus-like flowers: 5-petal rosettes with a dot centre, scattered (seeded), drawn at 4x and downsampled
    im = Image.new('L', (shape[1], shape[0]), 0); d = ImageDraw.Draw(im)
    r = scale; nflow = int(shape[0] * shape[1] / (r * r * 7))
    for _ in range(nflow):
        cx, cy, a0 = rng.uniform(0, shape[1]), rng.uniform(0, shape[0]), rng.uniform(0, 6.283)
        rr = r * rng.uniform(0.7, 1.15)
        for k in range(5):
            a = a0 + k * 6.283 / 5; px, py = cx + math.cos(a) * rr * 0.55, cy + math.sin(a) * rr * 0.55
            d.ellipse([px - rr * 0.42, py - rr * 0.42, px + rr * 0.42, py + rr * 0.42], fill=230)
        d.ellipse([cx - rr * 0.16, cy - rr * 0.16, cx + rr * 0.16, cy + rr * 0.16], fill=90)
        for k in range(2):   # a leaf or two
            a = a0 + 0.6 + k * 2.6; px, py = cx + math.cos(a) * rr * 1.05, cy + math.sin(a) * rr * 1.05
            d.ellipse([px - rr * 0.32, py - rr * 0.18, px + rr * 0.32, py + rr * 0.18], fill=120)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255.0
for t in spec.get('tint', []):
    tm = poly_mask([t['poly']], m.shape).astype(np.float32)
    tm = ndi.gaussian_filter(tm, 1.2)
    L = rgb.mean(axis=2)
    lo, hi = t.get('levels', [0.0, 1.0]); Ln = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    c = np.array([int(t['color'][i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32) / 255.0
    out = Ln[..., None] * c[None, None, :] * t.get('gain', 1.6)
    out = np.clip(out, 0, 1)
    if t.get('pattern') == 'aloha':
        p = aloha(m.shape, t.get('scale', 34))
        pc = np.array([0.98, 0.93, 0.80], dtype=np.float32)         # cream flowers
        out = out * (1 - p[..., None] * 0.75) + (pc * (0.35 + 0.75 * Ln[..., None])) * p[..., None] * 0.75
    a = tm * t.get('amt', 1.0)
    if t.get('lumKey'):   # tint only pixels in this luminance range (e.g. the light shirt, not the dark tie on it)
        k0, k1 = t['lumKey']; Ls = ndi.gaussian_filter(L, 1.0); a = a * np.clip((Ls - k0) / max(k1 - k0, 1e-3), 0, 1)
    rgb = rgb * (1 - a[..., None]) + out * a[..., None]
# --- edge decontamination: every pixel within 4 px of the edge takes the colour of the nearest interior pixel 4 px in
inner = ndi.binary_erosion(m, iterations=4)
if inner.any():
    _, (iy, ix) = ndi.distance_transform_edt(~inner, return_indices=True)
    band = m & ~inner
    rgb[band] = rgb[iy[band], ix[band]] * 0.5 + rgb[band] * 0.5
# --- parts: cut out of the body (kept separately with their anchor)
meta = {'box': spec['box'], 'parts': {}}
scale = spec.get('h', 900) / H
def save(mask, path):
    a = (mask * 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([(np.clip(rgb, 0, 1) * 255).astype(np.uint8), a]), 'RGBA')
    if spec.get('flip'): im = im.transpose(Image.FLIP_LEFT_RIGHT)
    bb = im.getbbox(); im = im.crop(bb)
    # supersampled downscale: anti-aliased edges
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    im.save(path, optimize=True); return bb, im.size
body = m.copy()
for name, poly in spec.get('parts', {}).items():
    pm = poly_mask([poly], m.shape) & m
    body &= ~pm
    bb, sz = save(pm, spec['out'].replace('.png', f'_{name}.png'))
    meta['parts'][name] = {'file': os.path.basename(spec['out'].replace('.png', f'_{name}.png')), 'bbox_src': [bb[0] + x0, bb[1] + y0, bb[2] + x0, bb[3] + y0], 'size': sz}
# the head under a removed hat: fill the crown with the hair tone (a plain paper crown)
if spec.get('crown'):
    cm = poly_mask([spec['crown']['poly']], m.shape); body |= cm
    c = np.array([int(spec['crown']['color'][i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32) / 255.0
    sh = ndi.gaussian_filter(cm.astype(np.float32), 2.0)
    rgb[cm] = c * (0.85 + 0.15 * sh[cm][..., None])
bb, sz = save(body, spec['out'])
meta['size'] = sz; meta['bbox_src'] = [bb[0] + x0, bb[1] + y0, bb[2] + x0, bb[3] + y0]
for name, p in meta['parts'].items():   # part offset relative to the body image (output px, top-left)
    p['at'] = [round((p['bbox_src'][0] - meta['bbox_src'][0]) * scale, 1), round((p['bbox_src'][1] - meta['bbox_src'][1]) * scale, 1)]
meta['src'] = spec['src']
json.dump(meta, open(spec['out'].replace('.png', '.json'), 'w'), indent=1)
print(json.dumps(meta))
