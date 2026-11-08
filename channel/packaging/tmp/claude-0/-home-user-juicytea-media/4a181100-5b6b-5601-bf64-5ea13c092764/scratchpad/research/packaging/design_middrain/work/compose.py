"""Compose ep02 mid-drain thumbnail candidates from our own Hawaii renders.
python3 compose.py <variant> -> ../cand_<n>.jpg (1280x720). All drawing is PIL; fonts are the engine's own (woff2 -> ttf)."""
import sys, json, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
W, H = 1280, 720
D = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_middrain'
WK = D + '/work'
LINES = json.load(open(WK + '/lines.json'))
def font(name, size): return ImageFont.truetype(f'{WK}/fonts/{name}.ttf', size)

def plate(name, contrast=1.06, sat=1.06, bright=1.0):
    im = Image.open(f'{WK}/r_{name}.jpg').convert('RGB').resize((W, H), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(contrast); im = ImageEnhance.Color(im).enhance(sat)
    if bright != 1.0: im = ImageEnhance.Brightness(im).enhance(bright)
    return im

def whiten_foam(im, dbg, band=5, amt=0.85):
    """The renderer's foam rim reads as a grey line at 30 km; lift it to white foam along the real waterline."""
    a = np.asarray(im).astype(np.float32)
    yw = np.array(LINES[dbg]['water'])
    lum = a.mean(2); mx = a.max(2); mn = a.min(2); satv = (mx - mn) / (mx + 1)
    m = np.zeros((H, W), np.float32)
    for x in range(W):
        y = yw[x]
        if y < 0: continue
        y0, y1 = max(0, y - band - 3), min(H, y + 3)
        col = (lum[y0:y1, x] > 120) & (satv[y0:y1, x] < 0.28)
        m[y0:y1, x] = col
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255 * amt
    foam = np.array([238, 246, 248], np.float32)
    a = a * (1 - m[..., None]) + foam * m[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def text_layer(txt, fnt, fill, halo=None, halo_w=0, shadow=None, shadow_blur=8, shadow_off=(0, 3), spacing=0, align='left'):
    """Render text (single or multi line) to an RGBA layer sized to fit; returns (layer, cap_height_px)."""
    lines = txt.split('\n')
    asc, desc = fnt.getmetrics()
    capb = fnt.getbbox('H'); cap = capb[3] - capb[1]
    lh = int(cap * 1.18) + spacing
    widths = [fnt.getlength(l) for l in lines]
    pad = 40
    Wl = int(max(widths)) + 2 * pad; Hl = lh * (len(lines) - 1) + cap + 2 * pad
    L = Image.new('RGBA', (Wl, Hl), (0, 0, 0, 0))
    def draw_into(img, color, stroke=0):
        d = ImageDraw.Draw(img)
        for i, l in enumerate(lines):
            x = pad + (0 if align == 'left' else (max(widths) - widths[i]) / (2 if align == 'center' else 1))
            y = pad + i * lh - capb[1]
            d.text((x, y), l, font=fnt, fill=color, stroke_width=stroke, stroke_fill=color)
    if shadow:
        S = Image.new('RGBA', L.size, (0, 0, 0, 0)); draw_into(S, shadow, max(halo_w, 2))
        S = S.filter(ImageFilter.GaussianBlur(shadow_blur)); L.alpha_composite(S, shadow_off)
    if halo:
        Hh = Image.new('RGBA', L.size, (0, 0, 0, 0)); draw_into(Hh, halo, halo_w); Hh = Hh.filter(ImageFilter.GaussianBlur(1.0)); L.alpha_composite(Hh)
    T = Image.new('RGBA', L.size, (0, 0, 0, 0)); draw_into(T, fill); L.alpha_composite(T)
    return L, cap, pad

def paste_text(im, txt, fnt, xy, **kw):
    L, cap, pad = text_layer(txt, fnt, **kw)
    base = im.convert('RGBA'); base.alpha_composite(L, (int(xy[0] - pad), int(xy[1] - pad)))
    return base.convert('RGB'), cap

def pin_layer(r, color=(229, 50, 45), ss=4):
    """Map pin (teardrop) of head radius r, tip at the bottom centre. Returns RGBA and tip offset."""
    R = r * ss; h = int(R * 2.75); w = int(R * 2.3)
    L = Image.new('RGBA', (w, h + R), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    cx, cy = w // 2, int(R * 1.1); tip = (cx, int(cy + R * 1.62))
    # teardrop: circle + tangent triangle to tip
    ang = math.asin(R / (tip[1] - cy))
    pL = (cx - R * math.cos(ang), cy + R * math.sin(ang)); pR = (cx + R * math.cos(ang), cy + R * math.sin(ang))
    def shape(dr, c, k=0):
        dr.ellipse([cx - R - k, cy - R - k, cx + R + k, cy + R + k], fill=c)
        dr.polygon([(pL[0] - k, pL[1]), (pR[0] + k, pR[1]), (tip[0], tip[1] + k * 1.6)], fill=c)
    shape(d, (255, 255, 255, 255), k=int(R * 0.12))      # white keyline (map-marker style)
    shape(d, color + (255,))
    d.ellipse([cx - R * 0.38, cy - R * 0.38, cx + R * 0.38, cy + R * 0.38], fill=(255, 255, 255, 255))
    L = L.resize((L.width // ss, L.height // ss), Image.LANCZOS)
    return L, (tip[0] // ss, tip[1] // ss + int(R * 0.12 * 1.6) // ss)

def tourist_layer(h=22, ss=8, shirt=(214, 52, 48)):
    """Tiny paper cut-out tourist (sun hat, aloha shirt, shorts) with a white paper border. Symbolic token, not to scale."""
    Hs = h * ss; w = int(Hs * 0.6); L = Image.new('RGBA', (w + 8 * ss, Hs + 8 * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    o = 4 * ss; cx = o + w // 2
    def fig(dr, k, cols):
        hat, skin, sh, shorts, leg = cols
        u = Hs / 22.0
        dr.ellipse([cx - 4.2 * u - k, 1.2 * u - k, cx + 4.2 * u + k, 3.6 * u + k], fill=hat)          # brim
        dr.ellipse([cx - 2.2 * u - k, 0 - k, cx + 2.2 * u + k, 2.8 * u + k], fill=hat)               # crown
        dr.ellipse([cx - 1.9 * u - k, 2.6 * u - k, cx + 1.9 * u + k, 6.2 * u + k], fill=skin)        # head
        dr.rounded_rectangle([cx - 3.2 * u - k, 6.4 * u - k, cx + 3.2 * u + k, 13.2 * u + k], radius=1.2 * u, fill=sh)  # shirt
        dr.rectangle([cx - 4.4 * u - k, 7.0 * u - k, cx - 3.0 * u + k, 11.8 * u + k], fill=skin)    # arms
        dr.rectangle([cx + 3.0 * u - k, 7.0 * u - k, cx + 4.4 * u + k, 11.8 * u + k], fill=skin)
        dr.rectangle([cx - 3.0 * u - k, 13.0 * u - k, cx + 3.0 * u + k, 16.2 * u + k], fill=shorts) # shorts
        dr.rectangle([cx - 2.6 * u - k, 16.0 * u - k, cx - 0.6 * u + k, 21.4 * u + k], fill=leg)     # legs
        dr.rectangle([cx + 0.6 * u - k, 16.0 * u - k, cx + 2.6 * u + k, 21.4 * u + k], fill=leg)
    W8 = (250, 248, 242, 255)
    fig(d, 1.6 * ss, [W8] * 5)                                                                     # paper border
    fig(d, 0, [(226, 196, 120, 255), (205, 150, 112, 255), shirt + (255,), (232, 222, 196, 255), (205, 150, 112, 255)])
    # aloha print dots on the shirt
    u = Hs / 22.0
    for (dx, dy) in [(-1.8, 8), (1.2, 9.4), (-0.6, 11.4), (2.0, 7.4), (-2.4, 12.2)]:
        d.ellipse([cx + dx * u - 0.5 * u, dy * u - 0.5 * u, cx + dx * u + 0.5 * u, dy * u + 0.5 * u], fill=(250, 236, 200, 255))
    L = L.resize((L.width // ss, L.height // ss), Image.LANCZOS)
    return L, (L.width // 2, L.height - 4)

def drop_shadow(layer, blur=4, off=(2, 3), alpha=0.45):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    S = Image.new('RGBA', layer.size, (0, 0, 0, 0)); S.putalpha(a); return S, off

def put(base, layer, xy, shadow=None):
    b = base.convert('RGBA')
    if shadow:
        S, off = drop_shadow(layer, *shadow); b.alpha_composite(S, (int(xy[0] + off[0]), int(xy[1] + off[1])))
    b.alpha_composite(layer, (int(xy[0]), int(xy[1]))); return b.convert('RGB')

def postcard(photo, w=540, word='HAWAIʻI', fnt='BarlowCondensed-800', cap_px=88, stamp=True):
    """Off-white postcard: our render as the photo, plain condensed type, a small volcano stamp (picture, no words)."""
    h = int(w * 0.68); bw = int(w * 0.045)
    C = Image.new('RGBA', (w, h), (244, 239, 228, 255))
    ph = Image.open(photo).convert('RGB'); pw, phh = w - 2 * bw, h - 2 * bw
    s = max(pw / ph.width, phh / ph.height); ph = ph.resize((int(ph.width * s) + 1, int(ph.height * s) + 1), Image.LANCZOS)
    ph = ph.crop(((ph.width - pw) // 2, (ph.height - phh) // 2, (ph.width - pw) // 2 + pw, (ph.height - phh) // 2 + phh))
    ph = ImageEnhance.Color(ph).enhance(1.12)
    C.paste(ph, (bw, bw))
    # word
    f = None; size = 40
    while True:
        f = font(fnt, size); cb = f.getbbox('H')
        if cb[3] - cb[1] >= cap_px: break
        size += 2
    L, cap, pad = text_layer(word, f, fill=(255, 255, 255, 255), shadow=(10, 30, 40, 170), shadow_blur=5, shadow_off=(0, 3))
    tx = bw + int(w * 0.05); ty = h - bw - int(h * 0.07) - cap
    C.alpha_composite(L, (tx - pad, ty - pad))
    if stamp:
        sw, sh = int(w * 0.15), int(w * 0.18); sx, sy = w - bw - sw - int(w * 0.03), bw + int(w * 0.03)
        S = Image.new('RGBA', (sw, sh), (0, 0, 0, 0)); d = ImageDraw.Draw(S)
        d.rectangle([0, 0, sw - 1, sh - 1], fill=(250, 246, 236, 255))
        # perforation
        r = max(2, sw // 22)
        for x in range(r, sw, 3 * r):
            d.ellipse([x - r, -r, x + r, r], fill=(0, 0, 0, 0)); d.ellipse([x - r, sh - r, x + r, sh + r], fill=(0, 0, 0, 0))
        for y in range(r, sh, 3 * r):
            d.ellipse([-r, y - r, r, y + r], fill=(0, 0, 0, 0)); d.ellipse([sw - r, y - r, sw + r, y + r], fill=(0, 0, 0, 0))
        m = int(sw * 0.14)
        d.rectangle([m, m, sw - m, sh - m], fill=(44, 124, 132, 255))           # teal sea
        d.rectangle([m, int(sh * 0.62), sw - m, sh - m], fill=(28, 92, 104, 255))
        d.polygon([(m, int(sh * 0.66)), (sw // 2 - 2, int(sh * 0.30)), (sw // 2 + 4, int(sh * 0.30)), (sw - m, int(sh * 0.66))], fill=(40, 34, 36, 255))  # shield volcano
        d.ellipse([int(sw * 0.62), int(sh * 0.16), int(sw * 0.76), int(sh * 0.28)], fill=(244, 196, 96, 255))  # sun
        C.alpha_composite(S, (sx, sy))
    # paper grain
    g = (np.random.RandomState(3).rand(h, w) * 10 - 5).astype(np.int16)
    a = np.asarray(C).astype(np.int16); a[..., :3] = (a[..., :3] + g[..., None]).clip(0, 255); C = Image.fromarray(a.astype(np.uint8), 'RGBA')
    return C

def sink_card(base, card, center, angle, water_y, wcol=(30, 170, 200)):
    """Place a tilted card standing in the water: the part below water_y is tinted by the water, with a foam line."""
    R = card.rotate(angle, resample=Image.BICUBIC, expand=True)
    x0, y0 = int(center[0] - R.width / 2), int(center[1] - R.height / 2)
    b = base.convert('RGBA')
    S, off = drop_shadow(R, 10, (6, 8), 0.35); b.alpha_composite(S, (x0 + off[0], y0 + off[1]))
    a = np.asarray(R).astype(np.float32)
    yy = np.arange(R.height)[:, None] + y0
    under = (yy > water_y).astype(np.float32)
    k = under[..., None] * 0.72
    rgb = a[..., :3] * (1 - k) + np.array(wcol, np.float32) * k
    alpha = a[..., 3] * (1 - under * 0.25)
    R2 = Image.fromarray(np.dstack([rgb, alpha]).clip(0, 255).astype(np.uint8), 'RGBA')
    b.alpha_composite(R2, (x0, y0))
    # foam where the card meets the water
    d = ImageDraw.Draw(b); cols = np.nonzero(a[..., 3].max(0) > 0)[0]
    xs = cols.min() + x0, cols.max() + x0
    F = Image.new('RGBA', b.size, (0, 0, 0, 0)); fd = ImageDraw.Draw(F)
    fd.ellipse([xs[0] - 14, water_y - 7, xs[1] + 14, water_y + 9], outline=(240, 248, 250, 235), width=5)
    F = F.filter(ImageFilter.GaussianBlur(1.6)); b.alpha_composite(F)
    return b.convert('RGB')
