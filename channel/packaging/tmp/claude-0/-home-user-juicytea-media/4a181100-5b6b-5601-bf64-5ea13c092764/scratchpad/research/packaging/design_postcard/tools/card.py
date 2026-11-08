"""Postcard compositor for the "Below the Postcard" thumbnails (PIL only).

make_card(face, w, ...)  -> RGBA physical off-white postcard (photo face, optional place name, stamp, postmark)
place(plate, card, ...)  -> plate with the tilted card + soft contact/ambient shadow
All geometry is in the plate's pixel space (plates are composed at 1920x1080 and downsampled to 1280x720).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageChops

FONTS = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_postcard/fonts/'
PAPER = (245, 240, 228)          # off-white card stock (#F5F0E4)
INK = (38, 36, 40)
ACCENT = (242, 176, 64)          # series accent: warm amber (stamp sun)
OKINA = 'ʻ'


def _font(name, size):
    return ImageFont.truetype(FONTS + name + '-latin.ttf', size)


def font_for_cap(name, cap_px):
    """Font size whose cap height (H) is cap_px."""
    f = _font(name, 400); bb = f.getbbox('H'); cap = bb[3] - bb[1]
    return _font(name, max(6, round(400 * cap_px / cap)))


def crop_aspect(im, aspect, fx=0.5, fy=0.5, zoom=1.0):
    W, H = im.size
    if W / H > aspect: h = H / zoom; w = h * aspect
    else: w = W / zoom; h = w / aspect
    x0 = (W - w) * fx; y0 = (H - h) * fy
    return im.crop((round(x0), round(y0), round(x0 + w), round(y0 + h)))


def _grain(size, amt, seed):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amt, (size[1], size[0]))
    return n


def stamp(w, seed=3):
    """Small perforated stamp: amber sun over a volcano silhouette and one wave. No words."""
    S = 4; W = w * S; H = round(w * 1.18) * S
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = W * 0.045                                  # perforation radius
    d.rectangle((0, 0, W, H), fill=(250, 247, 238, 255))
    step = r * 2.6
    for x in np.arange(step / 2, W, step):
        d.ellipse((x - r, -r, x + r, r), fill=(0, 0, 0, 0)); d.ellipse((x - r, H - r, x + r, H + r), fill=(0, 0, 0, 0))
    for y in np.arange(step / 2, H, step):
        d.ellipse((-r, y - r, r, y + r), fill=(0, 0, 0, 0)); d.ellipse((W - r, y - r, W + r, y + r), fill=(0, 0, 0, 0))
    m = W * 0.13; x0, y0, x1, y1 = m, m, W - m, H - m
    # field: pale sky to warm
    fld = Image.new('RGBA', (round(x1 - x0), round(y1 - y0)))
    fa = np.zeros((fld.height, fld.width, 4), np.uint8)
    t = np.linspace(0, 1, fld.height)[:, None]
    top = np.array([118, 178, 214]); bot = np.array([236, 214, 170])
    fa[..., :3] = (top * (1 - t[..., None]) + bot * t[..., None]).astype(np.uint8).repeat(fld.width, 1)
    fa[..., 3] = 255
    fld = Image.fromarray(fa, 'RGBA'); im.alpha_composite(fld, (round(x0), round(y0)))
    fw, fh = x1 - x0, y1 - y0
    # sun
    cx, cy, sr = x0 + fw * 0.66, y0 + fh * 0.33, fw * 0.17
    d.ellipse((cx - sr, cy - sr, cx + sr, cy + sr), fill=ACCENT + (255,))
    # volcano silhouette (broad shield) + ocean band
    base = y0 + fh * 0.80
    pts = [(x0, base), (x0 + fw * 0.10, base - fh * 0.08), (x0 + fw * 0.36, base - fh * 0.30), (x0 + fw * 0.46, base - fh * 0.34),
           (x0 + fw * 0.56, base - fh * 0.31), (x0 + fw * 0.86, base - fh * 0.07), (x1, base - fh * 0.02), (x1, base)]
    d.polygon(pts, fill=(44, 40, 46, 255))
    d.rectangle((x0, base, x1, y1), fill=(34, 132, 156, 255))
    d.line([(x0 + fw * 0.08, base + fh * 0.09), (x0 + fw * 0.30, base + fh * 0.06), (x0 + fw * 0.52, base + fh * 0.09), (x0 + fw * 0.74, base + fh * 0.06), (x1 - fw * 0.06, base + fh * 0.09)],
           fill=(220, 240, 244, 255), width=max(1, round(fw * 0.025)))
    d.rectangle((x0, y0, x1, y1), outline=(60, 56, 60, 255), width=max(1, round(W * 0.012)))
    return im.resize((w, round(w * 1.18)), Image.LANCZOS)


def postmark(w, seed=5, alpha=150):
    """Cancellation mark: double ring + wavy lines, no words."""
    S = 4; W = w * S; H = round(w * 0.62) * S
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = (40, 38, 46, alpha); lw = max(2, round(W * 0.012))
    R = H * 0.46; cx = R + lw; cy = H / 2
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=col, width=lw)
    d.ellipse((cx - R * 0.74, cy - R * 0.74, cx + R * 0.74, cy + R * 0.74), outline=col, width=max(1, lw // 2 + 1))
    xs = np.linspace(cx + R * 0.55, W - lw, 60)
    for k in range(4):
        yb = cy + (k - 1.5) * H * 0.17
        ys = yb + np.sin((xs - xs[0]) / (W * 0.09)) * H * 0.045
        d.line(list(zip(xs, ys)), fill=col, width=lw)
    im = im.resize((w, round(w * 0.62)), Image.LANCZOS)
    # ink wear
    a = np.asarray(im).copy(); rng = np.random.default_rng(seed)
    a[..., 3] = (a[..., 3] * np.clip(rng.normal(0.85, 0.25, a.shape[:2]), 0, 1)).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def make_card(face, w, aspect=1.5, border=0.045, text=None, cap_px=None, font='Oswald-700', track=0.04,
              text_pos='bl', text_col=(255, 252, 244), stamp_on=True, postmark_on=True, seed=1,
              face_sat=1.12, face_con=1.06, face_zoom=1.0, face_fx=0.5, face_fy=0.5, sheen=0.10):
    """Return an RGBA postcard of width w (aspect = w/h). cap_px is the cap height of the place name in card pixels."""
    S = 3; W = w * S; H = round(w / aspect) * S
    card = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # paper with grain and soft light falloff
    g = _grain((W, H), 3.2, seed)
    yy, xx = np.mgrid[0:H, 0:W]
    fall = 1.0 + 0.035 * (1 - xx / W) - 0.03 * (yy / H)
    pa = np.clip(np.array(PAPER)[None, None, :] * fall[..., None] + g[..., None], 0, 255).astype(np.uint8)
    paper = Image.fromarray(np.dstack([pa, np.full((H, W), 255, np.uint8)]), 'RGBA')
    # rounded-corner mask
    mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, H - 1), radius=round(W * 0.012), fill=255)
    card.paste(paper, (0, 0), mask)
    # photo
    b = round(W * border); pw, ph = W - 2 * b, H - 2 * b
    ph_im = crop_aspect(face.convert('RGB'), pw / ph, face_fx, face_fy, face_zoom).resize((pw, ph), Image.LANCZOS)
    ph_im = ImageEnhance.Color(ph_im).enhance(face_sat); ph_im = ImageEnhance.Contrast(ph_im).enhance(face_con)
    ph_rgba = ph_im.convert('RGBA')
    # place name
    if text:
        fnt = font_for_cap(font, cap_px * S)
        bb = fnt.getbbox('H'); cap_top = bb[1]
        # letter-spaced width
        adv = [fnt.getlength(ch) for ch in text]; sp = track * fnt.size
        tw = sum(adv) + sp * (len(text) - 1)
        mx = round(pw * 0.055)
        if tw > pw - 2 * mx: print(f'WARNING text {tw/S:.0f}px wider than photo {(pw-2*mx)/S:.0f}px')
        tx = mx if text_pos[1] == 'l' else (pw - tw) / 2 if text_pos[1] == 'c' else pw - mx - tw
        ty = (ph - mx * 0.9 - cap_px * S - cap_top) if text_pos[0] == 'b' else (mx - cap_top)
        lay = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        x = tx
        for ch, a in zip(text, adv):
            ld.text((x, ty), ch, font=fnt, fill=text_col + (255,)); x += a + sp
        sh = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); sh.putalpha(lay.getchannel('A').filter(ImageFilter.GaussianBlur(cap_px * S * 0.09)))
        sh = Image.fromarray(np.dstack([np.full((ph, pw, 3), (12, 16, 22), np.uint8), (np.asarray(sh.getchannel('A')) * 0.62).astype(np.uint8)]), 'RGBA')
        ph_rgba.alpha_composite(sh, (round(cap_px * S * 0.035), round(cap_px * S * 0.06)))
        ph_rgba.alpha_composite(lay)
    card.alpha_composite(ph_rgba, (b, b))
    # thin printed-edge inner shadow around the photo
    edge = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(edge).rectangle((b, b, b + pw - 1, b + ph - 1), outline=(0, 0, 0, 70), width=max(1, S))
    card.alpha_composite(edge)
    # stamp + postmark (top-right, overlapping the photo corner like a real card)
    if stamp_on:
        sw = round(W * 0.115); st = stamp(sw, seed)
        sx, sy = W - b - sw - round(W * 0.025), b + round(W * 0.022)
        sshadow = Image.new('RGBA', st.size, (0, 0, 0, 0)); sshadow.putalpha(st.getchannel('A').point(lambda v: v * 0.35))
        card.alpha_composite(sshadow.filter(ImageFilter.GaussianBlur(S * 1.5)), (sx + S, sy + 2 * S))
        card.alpha_composite(st, (sx, sy))
        if postmark_on:
            pm = postmark(round(sw * 1.55), seed)
            card.alpha_composite(pm, (sx - round(sw * 0.62), sy + round(sw * 0.55)))
    # gloss sheen (diagonal) + paper edge bevel
    sa = np.zeros((H, W), np.float32)
    dd = (xx / W * 0.8 + yy / H * 0.6)
    sa = np.exp(-((dd - 0.55) / 0.10) ** 2) * sheen * 255
    sheen_im = Image.fromarray(np.dstack([np.full((H, W, 3), 255, np.uint8), sa.astype(np.uint8)]), 'RGBA')
    card.alpha_composite(sheen_im)
    ed = ImageDraw.Draw(card)
    ed.rounded_rectangle((0, 0, W - 1, H - 1), radius=round(W * 0.012), outline=(205, 196, 180, 255), width=max(1, S))
    ed.line([(round(W * 0.012), S), (W - round(W * 0.012), S)], fill=(255, 255, 252, 200), width=S)
    card.putalpha(ImageChops.multiply(card.getchannel('A'), mask))
    return card.resize((w, round(w / aspect)), Image.LANCZOS)


def place(plate, card, cx, cy, angle, shadow=(-14, 16), blur=16, opacity=0.55, contact=0.0, contact_y=None):
    """Rotate card by angle (deg, +ccw) and composite centred at (cx, cy). Soft offset shadow; optional contact shadow."""
    out = plate.convert('RGBA')
    big = card.resize((card.width * 2, card.height * 2), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC, expand=True)
    rc = big.resize((big.width // 2, big.height // 2), Image.LANCZOS)
    x0, y0 = round(cx - rc.width / 2), round(cy - rc.height / 2)
    a = rc.getchannel('A')
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    sm = Image.new('L', out.size, 0); sm.paste(a, (x0 + shadow[0], y0 + shadow[1]))
    sm = sm.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * opacity)
    sh = Image.fromarray(np.dstack([np.full((out.height, out.width, 3), (8, 6, 10), np.uint8), np.asarray(sm)]), 'RGBA')
    out.alpha_composite(sh)
    if contact > 0 and contact_y is not None:
        cm = Image.new('L', out.size, 0); ImageDraw.Draw(cm).ellipse((x0 + rc.width * 0.05, contact_y - 10, x0 + rc.width * 0.95, contact_y + 14), fill=round(255 * contact))
        cm = cm.filter(ImageFilter.GaussianBlur(10))
        out.alpha_composite(Image.fromarray(np.dstack([np.zeros((out.height, out.width, 3), np.uint8), np.asarray(cm)]), 'RGBA'))
    out.alpha_composite(rc, (x0, y0))
    return out.convert('RGB'), (x0, y0, rc)


def grade(im, warm=0.0, con=1.0, sat=1.0, bright=1.0, vig=0.0, vig_bottom=0.0):
    im = ImageEnhance.Contrast(im).enhance(con); im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Brightness(im).enhance(bright)
    a = np.asarray(im).astype(np.float32)
    if warm:
        l = a.mean(2, keepdims=True) / 255
        a = a + warm * np.array([18, 8, -10]) * l
    H, W = a.shape[:2]
    if vig or vig_bottom:
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        f = 1 - vig * np.clip(r - 0.6, 0, 1) ** 1.5 - vig_bottom * np.clip((yy / H - 0.7) / 0.3, 0, 1) ** 1.6
        a = a * f[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def save_thumb(im, path, q=92):
    t = im.resize((1280, 720), Image.LANCZOS) if im.size != (1280, 720) else im
    t.save(path, 'JPEG', quality=q, optimize=True, progressive=True)
    return t
