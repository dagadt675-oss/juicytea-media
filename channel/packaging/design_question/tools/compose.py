"""Compose ep02 'question + one image' thumbnails from our own Hawaii renders.
usage: python3 -I compose.py VERSION_JSON OUTDIR
VERSION_JSON: {"cand_1": {"plate": path, "crop": [cx, cy, zoom], "grade": {...}, "text": [...]}, ...}
All drawing is PIL only: crop/zoom, tone grade, soft dodge/burn masks, optional text with a soft shadow (never a box).
"""
import json, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageChops
import numpy as np

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
W, H = 1280, 720


def crop_zoom(im, cx=0.5, cy=0.5, zoom=1.0):
    w, h = im.size
    cw, ch = w / zoom, h / zoom
    x0 = min(max(cx * w - cw / 2, 0), w - cw); y0 = min(max(cy * h - ch / 2, 0), h - ch)
    return im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch))).resize((W, H), Image.LANCZOS)


def radial(cx, cy, rx, ry, power=2.0):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - cx * W) / (rx * W)) ** 2 + ((y - cy * H) / (ry * H)) ** 2)
    return np.clip(1 - d, 0, 1) ** power


def vgrad(y0, y1):
    """0 above y0 (frame fraction), ramps to 1 at y1 (smoothstep)."""
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None].repeat(W, 1)
    t = np.clip((y - y0) / max(y1 - y0, 1e-3), 0, 1)
    return t * t * (3 - 2 * t)


def sky_mask(a):
    """a: float HxWx3 0..1. Sky = run of pale bluish pixels connected to the top edge, per column."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    l = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cand = (b > r + 0.04) & (l > 0.50)
    m = np.zeros(cand.shape, bool)
    for x in range(cand.shape[1]):
        col = cand[:, x]; k = np.argmin(col) if not col.all() else len(col)
        m[:k, x] = True
    return m


def hero_mask(dry, c):
    """Soft 0..1 mask of the hero (the island above old sea level)."""
    a = np.asarray(dry).astype(np.float32) / 255.0
    sky = sky_mask(a)
    if c.get('wet'):
        w = np.asarray(crop_zoom(Image.open(c['wet']).convert('RGB'), *c.get('crop', [0.5, 0.5, 1.0]))).astype(np.float32) / 255.0
        mx, mn = w.max(-1), w.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-3)
        water = (w[..., 2] > w[..., 1]) & (w[..., 2] > w[..., 0] + 0.15) & (sat > 0.45) & (w[..., 2] > 0.30)
        wm = Image.fromarray((water * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
        water = np.asarray(wm) > 128
        land = ~water & ~sky
        lm = Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
        land = (np.asarray(lm) > 128) & ~water & ~sky
        import scipy.ndimage as ndi
        lab, n = ndi.label(land)
        if n:
            sizes = ndi.sum(land, lab, range(1, n + 1)); keep = [i + 1 for i, sz in enumerate(sizes) if sz >= c.get('min_blob', 0.25) * sizes.max()]
            land = ndi.binary_fill_holes(np.isin(lab, keep))
    else:  # hero = everything between the sky and the bright cream shoreline line
        l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        y0, y1 = int(c['line_band'][0] * H), int(c['line_band'][1] * H)
        wh = a.min(-1) - 2 * np.clip(a[..., 2] - a[..., 0], 0, None)
        rows = np.argmax(wh[y0:y1], axis=0) + y0
        med = np.median(rows); rows = np.where(np.abs(rows - med) > 25, med, rows)
        rows = np.convolve(np.pad(rows, 15, mode='edge'), np.ones(31) / 31, mode='valid').astype(int)
        yy = np.arange(H)[:, None]
        land = (yy < rows[None, :] + 2) & ~sky
    m = Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2.5))
    return np.asarray(m).astype(np.float32)[..., None] / 255.0


def tone(a, g):
    if 'exposure' in g: a = a * g['exposure']
    if 'lift' in g: a = 1 - (1 - np.clip(a, 0, 1)) ** g['lift']
    if 'warm' in g: a = a * np.array(g['warm'], dtype=np.float32)
    if 'sat' in g:
        l = (a * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True); a = l + (a - l) * g['sat']
    if 'contrast' in g:
        m = 0.45; a = (a - m) * g['contrast'] + m
    return a


def grade(im, g, mask=None):
    a = np.asarray(im).astype(np.float32) / 255.0
    if mask is not None and ('hero' in g or 'bg' in g):
        sky = Image.fromarray((sky_mask(a) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
        sky = (np.asarray(sky).astype(np.float32) / 255.0)[..., None] * (1 - mask)
        bgw = np.clip(1 - mask - sky, 0, 1)
        a = tone(a.copy(), g.get('hero', {})) * mask + tone(a.copy(), g.get('bg', {})) * bgw + tone(a.copy(), g.get('sky', {})) * sky
    if 'exposure' in g: a = a * g['exposure']
    if 'gamma' in g: a = np.clip(a, 0, 1) ** (1 / g['gamma'])
    if 'contrast' in g:
        m = 0.45; a = (a - m) * g['contrast'] + m
    for d in g.get('dodge', []):        # [cx, cy, rx, ry, amount]
        k = radial(*d[:4])[..., None] * d[4]; a = a * (1 + k)
    for b in g.get('burn_bottom', []):  # [y0, y1, amount]  darken toward the bottom
        k = vgrad(b[0], b[1])[..., None] * b[2]; a = a * (1 - k)
    if 'warm' in g:                     # small white-balance shift (r, g, b multipliers)
        a = a * np.array(g['warm'], dtype=np.float32)
    if 'sat' in g:
        l = (a * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True); a = l + (a - l) * g['sat']
    if 'vignette' in g:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x / W - 0.5) / 0.75) ** 2 + ((y / H - 0.5) / 0.75) ** 2)
        a = a * (1 - g['vignette'] * np.clip(r - 0.35, 0, 1) ** 1.5)[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def draw_text(im, t):
    """t: {"s": text, "font": file, "cap": cap height as frame fraction, "x": frac, "y": frac (top of caps), "anchor": l|r|c,
           "fill": [r,g,b], "shadow": [r,g,b,alpha], "blur": px, "track": px letter spacing}"""
    font_path = os.path.join(FONTS, t.get('font', 'BarlowCondensed-800-latin.ttf'))
    cap_px = t['cap'] * H
    probe = ImageFont.truetype(font_path, 200)
    bb = probe.getbbox('H'); cap200 = bb[3] - bb[1]
    size = int(round(200 * cap_px / cap200)); f = ImageFont.truetype(font_path, size)
    track = t.get('track', 0)
    # measure with tracking
    widths = [f.getlength(c) for c in t['s']]; total = sum(widths) + track * (len(t['s']) - 1)
    bbH = f.getbbox('H'); top_off = bbH[1]
    x = t['x'] * W; y = t['y'] * H - top_off
    if t.get('anchor', 'l') == 'r': x -= total
    elif t.get('anchor') == 'c': x -= total / 2
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl, ds = ImageDraw.Draw(layer), ImageDraw.Draw(sh)
    cx = x
    sc = tuple(t.get('shadow', [0, 0, 0, 170])); off = t.get('shadow_off', [0, 3])
    for c, w in zip(t['s'], widths):
        ds.text((cx + off[0], y + off[1]), c, font=f, fill=sc)
        dl.text((cx, y), c, font=f, fill=tuple(t.get('fill', [255, 255, 255])) + (255,))
        cx += w + track
    sh = sh.filter(ImageFilter.GaussianBlur(t.get('blur', 6)))
    out = Image.alpha_composite(im.convert('RGBA'), sh)
    out = Image.alpha_composite(out, layer)
    real_cap = cap_px
    return out.convert('RGB'), {'text': t['s'], 'cap_frac': round(real_cap / H, 3), 'font_px': size,
                                'x0': round(x), 'x1': round(x + total), 'y_top': round(t['y'] * H)}


def main():
    cfg = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    log = {}
    for name, c in cfg.items():
        if name.startswith('_'): continue
        im = Image.open(c['plate']).convert('RGB')
        im = crop_zoom(im, *c.get('crop', [0.5, 0.5, 1.0]))
        mask = hero_mask(im, c) if (c.get('wet') or c.get('line_band')) else None
        if mask is not None and c.get('debug_mask'):
            Image.fromarray((mask[..., 0] * 255).astype(np.uint8)).save(os.path.join(outdir, name + '_mask.png'))
        if mask is not None:
            hm = mask[..., 0] > 0.5
            a0 = np.asarray(im).astype(np.float32); l0 = (a0 * [0.2126, 0.7152, 0.0722]).sum(-1)
        im = grade(im, c.get('grade', {}), mask)
        texts = []
        for t in c.get('text', []):
            im, info = draw_text(im, t); texts.append(info)
        p = os.path.join(outdir, name + '.jpg')
        q = 92
        while True:
            im.save(p, quality=q, optimize=True, progressive=True)
            if os.path.getsize(p) < 1_900_000 or q <= 70: break
            q -= 4
        a = np.asarray(im).astype(np.float32)
        luma = (a * [0.2126, 0.7152, 0.0722]).sum(-1)
        hero_bg = None
        if mask is not None:
            sky = sky_mask(a0 / 255.0); bgm = (~hm) & (~sky)
            hero_bg = [round(float(luma[hm].mean()), 1), round(float(luma[bgm].mean()), 1), round(float(hm.mean()), 3)]
        log[name] = {'hero_bg_luma_heroarea': hero_bg, 'file': p, 'bytes': os.path.getsize(p), 'luma_mean': round(float(luma.mean()), 1),
                     'luma_p90': round(float(np.percentile(luma, 90)), 1), 'words': sum(len(t['text'].split()) for t in texts), 'text': texts}
    json.dump(log, open(os.path.join(outdir, 'compose_log.json'), 'w'), indent=1)
    for k, v in log.items(): print(k, v['bytes'], 'luma', v['luma_mean'], 'p90', v['luma_p90'], 'words', v['words'], [(t['text'], t['cap_frac']) for t in v['text']])


if __name__ == '__main__':
    main()
