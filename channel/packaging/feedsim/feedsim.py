#!/usr/bin/env python3
"""YouTube DARK MODE feed simulator (PIL, deterministic). See README.md in this folder.

  python3 -I feedsim.py SPEC.json --out DIR/PREFIX [--layouts home,upnext,sidebar] [--seed N] [--scale 1]
                       [--glance] [--report] [--pos layout=K ...] [--n layout=K ...]

Layouts (geometry in CSS px / iOS pt; --scale 1 = true layout pixel scale, 3 = iPhone screenshot density):
  home     mobile Home feed, 390 pt wide, full-bleed 16:9 card, 36 pt avatar, title 2 lines, 1 meta line.
           Writes PREFIX_home.jpg (one 390x844 phone screen scrolled so the candidate is on screen)
           and PREFIX_home_scroll.jpg (the whole scroll).
  upnext   mobile watch page: pinned player, then the compact 'Up next' list (168x94 thumbs, title 3 lines).
           Writes PREFIX_upnext.jpg (phone screen, player pinned, list scrolled to the candidate)
           and PREFIX_upnext_scroll.jpg (player + info + whole list).
  sidebar  desktop watch page at 1280 px: player + the right column of 168x94 cards, title 2 lines.
           Writes PREFIX_sidebar.jpg (1280x720 viewport, above the fold) and PREFIX_sidebar_page.jpg.
--glance also writes *_glance.jpg next to each screen: downscaled, blurred and slightly motion-smeared, as the
card is seen in peripheral vision while scrolling. --report prints thumbnail pop metrics and the candidate's rank,
and every run writes PREFIX_<layout>.json with the rectangles of every card (candidate flagged).

SPEC (paths relative to the spec file; hosts thumbs relative to hosts.json):
{ "candidate": {item} | "candidates": [{item}, ...],
  "competitors": [{item}, ...],  "hosts": "../refs/hosts/hosts.json#ep01" (string or list),
  "exclude": [ids], "now_playing": "<id>" | {item},  "seed": 1,  "n": {"home": 6, "upnext": 10, "sidebar": 10},
  "pos": {"home": 2}, "style": {"home_title_px": 16, ...} }
item = {thumb, title, channel, views, age, duration, avatar?, watched? (0-1 red bar), badge? ("New"), id?}
"""
import argparse, colorsys, hashlib, json, math, os, random, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, 'fonts')
FALLBACK = {400: '/usr/share/fonts/opentype/inter/Inter-Regular.otf', 500: '/usr/share/fonts/opentype/inter/Inter-Medium.otf',
            700: '/usr/share/fonts/opentype/inter/Inter-Bold.otf'}
ROBOTO = {400: 'Roboto-Regular.ttf', 500: 'Roboto-Medium.ttf', 700: 'Roboto-Bold.ttf'}
GATE = os.path.normpath(os.path.join(HERE, '../../niche/work/gate.py'))

# YouTube dark theme tokens
BG = (15, 15, 15); TEXT = (241, 241, 241); TEXT2 = (170, 170, 170); CHIP = (39, 39, 39); BORDER = (48, 48, 48)
RED = (255, 0, 0); WHITE = (255, 255, 255)

STYLE = dict(
    # mobile Home (iOS/Android app 2025-26, approx.)
    home_title_px=16, home_title_lh=22, home_meta_px=12, home_meta_lh=18, home_avatar=36, home_badge_margin=8,
    # mobile Up next compact list
    up_title_px=14, up_title_lh=20, up_title_lines=3, up_meta_px=12, up_meta_lh=18, up_thumb=(168, 94),
    # desktop sidebar (ytd-compact-video-renderer)
    sb_title_px=14, sb_title_lh=20, sb_title_lines=2, sb_meta_px=12, sb_meta_lh=18, sb_thumb=(168, 94),
    badge_px=12, badge_alpha=0.70,
)


# ---------------------------------------------------------------- text
class Fonts:
    def __init__(self, scale):
        self.s = scale; self.c = {}; self.missing = {}

    def get(self, px, w=400, fb=False):
        k = (px, w, fb)
        if k not in self.c:
            path = FALLBACK[w] if fb else os.path.join(FONT_DIR, ROBOTO[w])
            if not fb and not os.path.exists(path):
                sys.exit(f'missing {path}: download Roboto into {FONT_DIR} (see README)')
            self.c[k] = ImageFont.truetype(path, max(1, round(px * self.s)))
        return self.c[k]

    @staticmethod
    def _sig(font, ch):
        sz = int(font.size * 2); im = Image.new('L', (sz, sz), 0)
        ImageDraw.Draw(im).text((2, 2), ch, font=font, fill=255)
        return im.tobytes(), font.getlength(ch)

    def has(self, font, ch):
        """False when the font would draw its .notdef box for ch (Roboto from Google Fonts lacks e.g. the okina)."""
        if ch.isspace():
            return True
        key = (id(font), ch)
        if key not in self.missing:
            nk = (id(font), None)
            if nk not in self.missing: self.missing[nk] = self._sig(font, '\U0010FFFD')
            self.missing[key] = self._sig(font, ch) != self.missing[nk]
        return self.missing[key]

    def runs(self, s, px, w):
        f, fb = self.get(px, w), self.get(px, w, True)
        out = []
        for ch in s:
            ff = f if self.has(f, ch) else fb
            if out and out[-1][1] is ff: out[-1][0] += ch
            else: out.append([ch, ff])
        return out

    def width(self, s, px, w=400):
        return sum(f.getlength(t) for t, f in self.runs(s, px, w))

    def draw(self, d, x, y_mid, s, px, w=400, fill=TEXT):
        """x, y_mid in output pixels; text vertically centred on y_mid like a CSS line box."""
        for t, f in self.runs(s, px, w):
            d.text((x, y_mid), t, font=f, fill=fill, anchor='lm'); x += f.getlength(t)
        return x


def wrap(F, s, px, w, maxw, max_lines):
    """Greedy word wrap + -webkit-line-clamp ellipsis. maxw in output px."""
    words, lines, cur = s.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd) if cur else wd
        if F.width(t, px, w) <= maxw:
            cur = t; continue
        if cur: lines.append(cur)
        cur = wd
        while F.width(cur, px, w) > maxw:  # break overlong words
            k = len(cur)
            while k > 1 and F.width(cur[:k], px, w) > maxw: k -= 1
            lines.append(cur[:k]); cur = cur[k:]
    if cur: lines.append(cur)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while last and F.width(last.rstrip() + '…', px, w) > maxw: last = last[:-1]
        lines = lines[:max_lines - 1] + [last.rstrip(' ,;:-') + '…']
    return lines


def ellipsize(F, s, px, w, maxw):
    if F.width(s, px, w) <= maxw: return s
    while s and F.width(s.rstrip() + '…', px, w) > maxw: s = s[:-1]
    return s.rstrip() + '…'


# ---------------------------------------------------------------- images
_img_cache = {}


def load_thumb(path):
    if path not in _img_cache:
        im = Image.open(path).convert('RGB'); a = np.asarray(im).astype(int)
        rows = np.where(a.max(axis=(1, 2)) > 20)[0]  # trim hqdefault letterbox bars
        if len(rows) and (rows[0] > 5 or rows[-1] < a.shape[0] - 6): im = im.crop((0, rows[0], im.width, rows[-1] + 1))
        W, H = im.size; t = 16 / 9
        if abs(W / H - t) > 0.01:  # cover-crop to 16:9
            if W / H > t: nw = round(H * t); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
            else: nh = round(W / t); im = im.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
        _img_cache[path] = im
    return _img_cache[path]


def fit(im, w, h):
    return im.resize((w, h), Image.LANCZOS, reducing_gap=3.0)


def round_mask(w, h, r, ss=4):
    m = Image.new('L', (w * ss, h * ss), 0)
    if r <= 0: return Image.new('L', (w, h), 255)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def circle(img, path, x, y, d, name=''):
    S = 4; m = Image.new('L', (d * S, d * S), 0); ImageDraw.Draw(m).ellipse((0, 0, d * S - 1, d * S - 1), fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    if path and os.path.exists(path):
        av = Image.open(path).convert('RGB').resize((d, d), Image.LANCZOS)
    else:  # default avatar: initial on a hashed colour
        h = int(hashlib.md5(name.encode()).hexdigest()[:2], 16) / 255
        av = Image.new('RGB', (d, d), tuple(int(c * 255) for c in colorsys.hls_to_rgb(h, 0.45, 0.5)))
        dd = ImageDraw.Draw(av); f = ImageFont.truetype(os.path.join(FONT_DIR, ROBOTO[500]), max(6, d // 2))
        dd.text((d / 2, d / 2), (name[:1] or '?').upper(), font=f, fill=WHITE, anchor='mm')
    img.paste(av, (int(x), int(y)), m)


def rect_alpha(img, box, fill, alpha, r):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    reg = img.crop((x0, y0, x1, y1)).convert('RGBA')
    ov = Image.new('RGBA', reg.size, fill + (0,)); ov.putalpha(round_mask(x1 - x0, y1 - y0, r).point(lambda v: int(v * alpha)))
    img.paste(Image.alpha_composite(reg, ov).convert('RGB'), (x0, y0))


def kebab(d, x, y, s, col=TEXT):
    for k in (-1, 0, 1):
        cy = y + k * 5 * s; d.ellipse((x - 1.6 * s, cy - 1.6 * s, x + 1.6 * s, cy + 1.6 * s), fill=col)


def pill(d, F, x, y, text, px=14, w=500, h=32, sel=False, s=1, pad=12, r=None):
    tw = F.width(text, px, w); W = tw + 2 * pad * s
    d.rounded_rectangle((x, y, x + W, y + h * s), radius=(r if r is not None else h / 2) * s, fill=TEXT if sel else CHIP)
    F.draw(d, x + pad * s, y + h * s / 2, text, px, w, BG if sel else TEXT)
    return x + W


class Ctx:
    def __init__(self, scale, style):
        self.s = scale; self.F = Fonts(scale); self.st = dict(STYLE, **(style or {}))

    def p(self, v): return int(round(v * self.s))


def thumb_block(c, img, it, x, y, w, h, radius, badge_margin, rects=None, tag=None):
    """Paste a thumbnail (display size w x h layout px) with duration badge and watched bar."""
    s = c.s; W, H = c.p(w), c.p(h); X, Y = c.p(x), c.p(y)
    t = fit(load_thumb(it['thumb']), W, H)
    if it.get('watched'):
        d0 = ImageDraw.Draw(t); bh = c.p(4)
        d0.rectangle((0, H - bh, W, H), fill=(113, 113, 113)); d0.rectangle((0, H - bh, int(W * it['watched']), H), fill=RED)
    img.paste(t, (X, Y), round_mask(W, H, c.p(radius)))
    dur = it.get('duration')
    if dur:
        px = c.st['badge_px']; tw = c.F.width(dur, px, 500); bw, bh = tw + c.p(8), c.p(18)
        bx1, by1 = X + W - c.p(badge_margin), Y + H - c.p(badge_margin) - (c.p(4) if it.get('watched') else 0)
        rect_alpha(img, (bx1 - bw, by1 - bh, bx1, by1), (0, 0, 0), c.st['badge_alpha'], c.p(4))
        c.F.draw(ImageDraw.Draw(img), bx1 - bw + c.p(4), by1 - bh / 2, dur, px, 500, WHITE)
    if rects is not None: rects.append(dict(tag=tag, id=it.get('id'), title=it.get('title'), thumb=[X, Y, X + W, Y + H]))
    return t


# ---------------------------------------------------------------- chrome (status bar, headers, nav)
def status_bar(c, img, y=0, h=47):
    d = ImageDraw.Draw(img); s = c.s
    c.F.draw(d, c.p(38), c.p(y + h / 2 + 2), '9:41', 15, 700, WHITE)
    bx = c.p(390 - 24 - 25)  # battery
    d.rounded_rectangle((bx, c.p(y + h / 2 - 4), bx + c.p(24), c.p(y + h / 2 + 7)), radius=c.p(3), outline=WHITE, width=max(1, c.p(1)))
    d.rounded_rectangle((bx + c.p(2), c.p(y + h / 2 - 2), bx + c.p(19), c.p(y + h / 2 + 5)), radius=c.p(2), fill=WHITE)
    for k in range(4):  # signal bars
        x = c.p(390 - 92 + k * 5); d.rectangle((x, c.p(y + h / 2 + 7 - 3 - 2.5 * k), x + c.p(3), c.p(y + h / 2 + 7)), fill=WHITE)
    cx, cy = c.p(390 - 60), c.p(y + h / 2 + 7)  # wifi
    for rr in (10, 6.5, 3):
        d.pieslice((cx - c.p(rr), cy - c.p(rr), cx + c.p(rr), cy + c.p(rr)), 225, 315, fill=WHITE)
        d.pieslice((cx - c.p(rr - 1.6), cy - c.p(rr - 1.6), cx + c.p(rr - 1.6), cy + c.p(rr - 1.6)), 225, 315, fill=BG) if rr > 3 else None


def yt_logo(c, d, x, y_mid, h=20):
    w = h * 1.42
    d.rounded_rectangle((c.p(x), c.p(y_mid - h / 2), c.p(x + w), c.p(y_mid + h / 2)), radius=c.p(h * 0.28), fill=RED)
    tx = x + w * 0.40; d.polygon([(c.p(tx), c.p(y_mid - h * 0.22)), (c.p(tx), c.p(y_mid + h * 0.22)), (c.p(tx + h * 0.36), c.p(y_mid))], fill=WHITE)
    c.F.draw(d, c.p(x + w + 2), c.p(y_mid), 'YouTube', h * 0.95, 700, WHITE)


def icon_search(c, d, x, y, r=8):
    d.ellipse((c.p(x - r), c.p(y - r), c.p(x + r * 0.6), c.p(y + r * 0.6)), outline=TEXT, width=max(1, c.p(2)))
    d.line((c.p(x + r * 0.45), c.p(y + r * 0.45), c.p(x + r * 1.1), c.p(y + r * 1.1)), fill=TEXT, width=max(1, c.p(2)))


def icon_bell(c, d, x, y):
    w = max(1, c.p(1.8))
    d.arc((c.p(x - 6), c.p(y - 9), c.p(x + 6), c.p(y + 3)), 180, 360, fill=TEXT, width=w)
    d.line((c.p(x - 6), c.p(y - 3), c.p(x - 6), c.p(y + 3)), fill=TEXT, width=w); d.line((c.p(x + 6), c.p(y - 3), c.p(x + 6), c.p(y + 3)), fill=TEXT, width=w)
    d.line((c.p(x - 6), c.p(y + 3), c.p(x - 9), c.p(y + 6)), fill=TEXT, width=w); d.line((c.p(x + 6), c.p(y + 3), c.p(x + 9), c.p(y + 6)), fill=TEXT, width=w)
    d.line((c.p(x - 9), c.p(y + 6), c.p(x + 9), c.p(y + 6)), fill=TEXT, width=w)
    d.pieslice((c.p(x - 3), c.p(y + 5), c.p(x + 3), c.p(y + 11)), 0, 180, fill=TEXT)


def icon_cast(c, d, x, y):
    d.rounded_rectangle((c.p(x - 10), c.p(y - 8), c.p(x + 10), c.p(y + 8)), radius=c.p(2), outline=TEXT, width=max(1, c.p(2)))
    d.rectangle((c.p(x - 11), c.p(y + 2), c.p(x - 6), c.p(y + 9)), fill=BG)
    d.arc((c.p(x - 16), c.p(y + 0), c.p(x - 4), c.p(y + 12)), 270, 360, fill=TEXT, width=max(1, c.p(2)))
    d.ellipse((c.p(x - 11), c.p(y + 6), c.p(x - 8), c.p(y + 9)), fill=TEXT)


def bottom_nav(c, img, y):
    d = ImageDraw.Draw(img); d.rectangle((0, c.p(y), c.p(390), c.p(y + 49 + 34)), fill=BG)
    d.line((0, c.p(y), c.p(390), c.p(y)), fill=(33, 33, 33), width=1)
    labels = ['Home', 'Shorts', '', 'Subscriptions', 'You']
    for k, lab in enumerate(labels):
        cx = 390 * (k + 0.5) / 5
        if k == 2:
            d.ellipse((c.p(cx - 18), c.p(y + 6), c.p(cx + 18), c.p(y + 42)), outline=TEXT, width=max(1, c.p(1.5)))
            d.line((c.p(cx - 8), c.p(y + 24), c.p(cx + 8), c.p(y + 24)), fill=TEXT, width=max(1, c.p(2)))
            d.line((c.p(cx), c.p(y + 16), c.p(cx), c.p(y + 32)), fill=TEXT, width=max(1, c.p(2))); continue
        if k == 0:
            d.polygon([(c.p(cx - 9), c.p(y + 17)), (c.p(cx), c.p(y + 9)), (c.p(cx + 9), c.p(y + 17)), (c.p(cx + 9), c.p(y + 28)), (c.p(cx - 9), c.p(y + 28))], fill=TEXT)
        elif k == 4:
            circle(img, None, c.p(cx - 11), c.p(y + 7), c.p(22), 'Y')
        else:
            d.rounded_rectangle((c.p(cx - 9), c.p(y + 9), c.p(cx + 9), c.p(y + 27)), radius=c.p(4), outline=TEXT, width=max(1, c.p(2)))
        tw = c.F.width(lab, 10, 400); c.F.draw(d, c.p(cx) - tw / 2, c.p(y + 38), lab, 10, 400, TEXT)
    d.rounded_rectangle((c.p(195 - 67), c.p(y + 49 + 21), c.p(195 + 67), c.p(y + 49 + 26)), radius=c.p(3), fill=WHITE)


def chips_row(c, img, y, labels, x0=12, x_max=390, h=32):
    d = ImageDraw.Draw(img); x = c.p(x0)
    for k, lab in enumerate(labels):
        if x > c.p(x_max): break
        x = pill(d, c.F, x, c.p(y), lab, 14, 500, h, sel=(k == 0), s=c.s, r=8) + c.p(8)


# ---------------------------------------------------------------- layouts
def card_home(c, img, it, y, rects, tag):
    st = c.st; th = round(390 * 9 / 16)
    thumb_block(c, img, it, 0, y, 390, th, 0, st['home_badge_margin'], rects, tag)
    d = ImageDraw.Draw(img); ty = y + th + 12; A = st['home_avatar']
    circle(img, it.get('avatar'), c.p(12), c.p(ty), c.p(A), it.get('channel', ''))
    tx, tw = 12 + A + 12, 390 - (12 + A + 12) - 36
    lines = wrap(c.F, it['title'], st['home_title_px'], 500, c.p(tw), 2)
    for k, ln in enumerate(lines):
        c.F.draw(d, c.p(tx), c.p(ty + st['home_title_lh'] * (k + 0.5)), ln, st['home_title_px'], 500, TEXT)
    my = ty + st['home_title_lh'] * len(lines) + 2
    meta = ellipsize(c.F, f"{it.get('channel','')} · {it.get('views','')} · {it.get('age','')}", st['home_meta_px'], 400, c.p(tw))
    c.F.draw(d, c.p(tx), c.p(my + st['home_meta_lh'] / 2), meta, st['home_meta_px'], 400, TEXT2)
    kebab(d, c.p(390 - 18), c.p(ty + 10), c.s)
    rects[-1]['card'] = [0, c.p(y), c.p(390), c.p(max(my + st['home_meta_lh'], ty + A) + 4)]
    return max(my + st['home_meta_lh'], ty + A) + 24


def compact(c, img, it, x, y, tw_total, title_px, title_lh, lines_max, meta_px, meta_lh, thumb_wh, gap, menu_w, rects, tag, meta_dot,
            badges=False):
    W, H = thumb_wh
    thumb_block(c, img, it, x, y, W, H, 8, 4, rects, tag)
    d = ImageDraw.Draw(img); tx = x + W + gap; tw = tw_total - W - gap - menu_w
    lines = wrap(c.F, it['title'], title_px, 500, c.p(tw), lines_max)
    for k, ln in enumerate(lines):
        c.F.draw(d, c.p(tx), c.p(y + title_lh * (k + 0.5)), ln, title_px, 500, TEXT)
    yy = y + title_lh * len(lines) + 2
    for ln in (it.get('channel', ''), f"{it.get('views','')} {meta_dot} {it.get('age','')}"):
        c.F.draw(d, c.p(tx), c.p(yy + meta_lh / 2), ellipsize(c.F, ln, meta_px, 400, c.p(tw)), meta_px, 400, TEXT2); yy += meta_lh
    if badges and it.get('badge'):
        bw = c.F.width(it['badge'], 12, 500) + c.p(8)
        d.rounded_rectangle((c.p(tx), c.p(yy + 3), c.p(tx) + bw, c.p(yy + 21)), radius=c.p(2), fill=CHIP)
        c.F.draw(d, c.p(tx + 4), c.p(yy + 12), it['badge'], 12, 500, TEXT); yy += 22
    kebab(d, c.p(x + tw_total - menu_w / 2 + 4), c.p(y + 10), c.s)
    bottom = max(y + H, yy)
    rects[-1]['card'] = [c.p(x), c.p(y), c.p(x + tw_total), c.p(bottom)]
    return bottom


def player(c, img, it, x, y, w, h, radius, frac=0.18, desktop=False):
    W, H = c.p(w), c.p(h)
    fr = fit(load_thumb(it['thumb']), W, H).convert('RGBA')
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for k in range(c.p(48)):  # bottom gradient for the controls
        gd.line((0, H - 1 - k, W, H - 1 - k), fill=(0, 0, 0, int(150 * (1 - k / c.p(48)))))
    fr = Image.alpha_composite(fr, g).convert('RGB'); d = ImageDraw.Draw(fr)
    by = H - (c.p(40) if desktop else c.p(2))
    d.rectangle((c.p(12) if desktop else 0, by - c.p(1.5), W - (c.p(12) if desktop else 0), by + c.p(1.5)), fill=(120, 120, 120))
    x1 = (c.p(12) if desktop else 0) + int((W - (c.p(24) if desktop else 0)) * frac)
    d.rectangle((c.p(12) if desktop else 0, by - c.p(1.5), x1, by + c.p(1.5)), fill=RED)
    if desktop:
        d.ellipse((x1 - c.p(6), by - c.p(6), x1 + c.p(6), by + c.p(6)), fill=RED)
        cy = H - c.p(20)
        d.polygon([(c.p(22), cy - c.p(8)), (c.p(22), cy + c.p(8)), (c.p(36), cy)], fill=WHITE)
        tot = it.get('duration', '10:00'); m, s_ = divmod(int(sum(int(p) * 60 ** i for i, p in enumerate(reversed(tot.split(':')))) * frac), 60)
        c.F.draw(d, c.p(110), cy, f'{m}:{s_:02d} / {tot}', 13, 400, WHITE)
    img.paste(fr, (c.p(x), c.p(y)), round_mask(W, H, c.p(radius)))


def shift(c, rects, off, vis_top, vis_bottom):
    """Move rects by the scroll offset; keep cards at least partly on screen; flag fully visible thumbnails."""
    out = []
    for r in rects:
        t = [r['thumb'][0], r['thumb'][1] - c.p(off), r['thumb'][2], r['thumb'][3] - c.p(off)]
        cd = [r['card'][0], r['card'][1] - c.p(off), r['card'][2], r['card'][3] - c.p(off)]
        if cd[3] <= c.p(vis_top) or cd[1] >= c.p(vis_bottom): continue
        out.append(dict(r, thumb=t, card=cd, visible=bool(t[1] >= c.p(vis_top) and t[3] <= c.p(vis_bottom))))
    return out


def render_home(c, cand, comps, n, pos, rng):
    items = comps[:n - 1]; pos = min(pos, len(items)); items = items[:pos] + [cand] + items[pos:]
    top = 47 + 48 + 48
    body_h = sum(round(390 * 9 / 16) + 12 + 2 * c.st['home_title_lh'] + 2 + c.st['home_meta_lh'] + 24 + 6 for _ in items) + 40
    img = Image.new('RGB', (c.p(390), c.p(top + body_h + 83)), BG); rects = []; y = top
    for k, it in enumerate(items):
        y = card_home(c, img, it, y, rects, 'candidate' if k == pos else 'competitor')
    full_h = y + 83; img = img.crop((0, 0, c.p(390), c.p(full_h)))
    def chrome(im, yoff):
        d = ImageDraw.Draw(im); d.rectangle((0, 0, c.p(390), c.p(top)), fill=BG)
        status_bar(c, im); yt_logo(c, d, 14, 47 + 24)
        icon_cast(c, d, 390 - 120, 47 + 24); icon_bell(c, d, 390 - 74, 47 + 24); icon_search(c, d, 390 - 28, 47 + 23)
        chips_row(c, im, 47 + 48 + 8, ['All', 'Geography', 'Science', 'Documentaries', 'History', 'Podcasts'])
    scroll = img.copy(); chrome(scroll, 0); bottom_nav(c, scroll, full_h - 83)
    # one phone screen with the candidate fully visible at a seeded scroll offset
    cr = rects[pos]['card']; ch = (cr[3] - cr[1]) / c.s; view = 844 - top - 83
    lo, hi = cr[3] / c.s - top - view + 8, cr[1] / c.s - top - 8  # offsets that keep the card on screen
    off = max(0, min(lo + rng.random() * max(0, hi - lo), full_h - 83 - 844 + 83))
    screen = Image.new('RGB', (c.p(390), c.p(844)), BG)
    screen.paste(img.crop((0, c.p(top + off), c.p(390), c.p(top + off + view))), (0, c.p(top)))
    chrome(screen, off); bottom_nav(c, screen, 844 - 83)
    srects = shift(c, rects, off, top, 844 - 83)
    return {'home': (screen, srects), 'home_scroll': (scroll, [dict(r, visible=True) for r in rects])}


def watch_info_mobile(c, img, np_it, y):
    d = ImageDraw.Draw(img); s = c.s
    lines = wrap(c.F, np_it['title'], 18, 500, c.p(366), 2)
    for k, ln in enumerate(lines): c.F.draw(d, c.p(12), c.p(y + 12 + 24 * (k + 0.5)), ln, 18, 500, TEXT)
    y += 12 + 24 * len(lines) + 4
    x = c.F.draw(d, c.p(12), c.p(y + 9), f"{np_it.get('views','')}  {np_it.get('age','')}  ", 12, 400, TEXT2)
    c.F.draw(d, x, c.p(y + 9), '...more', 12, 500, TEXT); y += 18 + 10
    circle(img, np_it.get('avatar'), c.p(12), c.p(y + 8), c.p(32), np_it.get('channel', ''))
    x = c.F.draw(d, c.p(52), c.p(y + 24), np_it.get('channel', ''), 14, 500, TEXT)
    c.F.draw(d, x + c.p(8), c.p(y + 24), np_it.get('subs', '1.2M'), 12, 400, TEXT2)
    sw = c.F.width('Subscribe', 14, 500) + c.p(32)
    d.rounded_rectangle((c.p(378) - sw, c.p(y + 6), c.p(378), c.p(y + 42)), radius=c.p(18), fill=TEXT)
    c.F.draw(d, c.p(378) - sw + c.p(16), c.p(y + 24), 'Subscribe', 14, 500, BG); y += 48 + 6
    x = c.p(12)
    for lab in ['82K  |', 'Share', 'Remix', 'Save', 'Download', 'Clip']:
        if x > c.p(390): break
        x = pill(d, c.F, x, c.p(y), lab, 14, 500, 36, s=s, pad=14) + c.p(8)
    y += 36 + 12
    d.rounded_rectangle((c.p(12), c.p(y), c.p(378), c.p(y + 74)), radius=c.p(12), fill=CHIP)
    x = c.F.draw(d, c.p(24), c.p(y + 20), 'Comments', 14, 500, TEXT); c.F.draw(d, x + c.p(6), c.p(y + 20), '2.3K', 14, 400, TEXT2)
    circle(img, None, c.p(24), c.p(y + 38), c.p(24), 'K')
    c.F.draw(d, c.p(56), c.p(y + 50), ellipsize(c.F, 'This is the clearest explanation I have seen of this.', 13, 400, c.p(300)), 13, 400, TEXT)
    y += 74 + 8
    return y


def render_upnext(c, cand, comps, np_it, n, pos, rng):
    st = c.st; items = comps[:n - 1]; pos = min(pos, len(items)); items = items[:pos] + [cand] + items[pos:]
    TW, TH = st['up_thumb']; ph = round(390 * 9 / 16)
    big = Image.new('RGB', (c.p(390), c.p(47 + ph + 420 + len(items) * (TH + 60) + 40)), BG); rects = []
    y = watch_info_mobile(c, big, np_it, 47 + ph)
    chips_row(c, big, y + 8, ['All', 'Related', 'From ' + np_it.get('channel', ''), 'Recently uploaded', 'Watched'])
    y += 48; list_top = y
    for k, it in enumerate(items):
        b = compact(c, big, it, 12, y, 390 - 24, st['up_title_px'], st['up_title_lh'], st['up_title_lines'],
                    st['up_meta_px'], st['up_meta_lh'], (TW, TH), 12, 24, rects, 'candidate' if k == pos else 'competitor', '·')
        y = b + 14
    full_h = y + 34; big = big.crop((0, 0, c.p(390), c.p(full_h)))
    status_bar(c, big); player(c, big, np_it, 0, 47, 390, ph, 0, 0.23)
    # phone screen: status bar + pinned player, list scrolled so that the candidate is on screen
    pinned = 47 + ph; view = 844 - pinned - 34
    cr = rects[pos]['card']; lo, hi = cr[3] / c.s - pinned - view + 8, cr[1] / c.s - pinned - 8
    off = max(0, lo + rng.random() * max(0, hi - lo)); off = min(off, max(0, full_h - 844))
    screen = Image.new('RGB', (c.p(390), c.p(844)), BG)
    screen.paste(big.crop((0, c.p(pinned + off), c.p(390), c.p(pinned + off + view))), (0, c.p(pinned)))
    screen.paste(big.crop((0, 0, c.p(390), c.p(pinned))), (0, 0))
    ImageDraw.Draw(screen).rounded_rectangle((c.p(195 - 67), c.p(844 - 13), c.p(195 + 67), c.p(844 - 8)), radius=c.p(3), fill=WHITE)
    srects = shift(c, rects, off, pinned, 844 - 34)
    return {'upnext': (screen, srects), 'upnext_scroll': (big, [dict(r, visible=True) for r in rects])}


def render_sidebar(c, cand, comps, np_it, n, pos, rng):
    st = c.st; items = comps[:n - 1]; pos = min(pos, len(items)); items = items[:pos] + [cand] + items[pos:]
    PW = 1280; px0 = 24; pw = PW - 24 * 3 - 402; ph = round(pw * 9 / 16); sx = px0 + pw + 24
    H = max(56 + 24 + 44 + len(items) * 112 + 40, 56 + 24 + ph + 260)
    img = Image.new('RGB', (c.p(PW), c.p(H)), BG); d = ImageDraw.Draw(img); rects = []
    # masthead
    for k in range(3): d.rectangle((c.p(24), c.p(20 + k * 6), c.p(42), c.p(21.5 + k * 6)), fill=TEXT)
    yt_logo(c, d, 72, 28, 20)
    sw = 536; sx0 = (PW - sw) / 2 - 20
    d.rounded_rectangle((c.p(sx0), c.p(8), c.p(sx0 + sw), c.p(48)), radius=c.p(20), fill=(18, 18, 18), outline=BORDER, width=max(1, c.p(1)))
    d.rounded_rectangle((c.p(sx0 + sw - 64), c.p(8), c.p(sx0 + sw), c.p(48)), radius=c.p(20), fill=(34, 34, 34))
    d.rectangle((c.p(sx0 + sw - 64), c.p(8), c.p(sx0 + sw - 44), c.p(48)), fill=(34, 34, 34))
    c.F.draw(d, c.p(sx0 + 16), c.p(28), 'Search', 16, 400, (136, 136, 136)); icon_search(c, d, sx0 + sw - 34, 27)
    d.ellipse((c.p(sx0 + sw + 12), c.p(8), c.p(sx0 + sw + 52), c.p(48)), fill=(34, 34, 34))
    pill(d, c.F, c.p(PW - 210), c.p(10), '+  Create', 14, 500, 36, s=c.s, pad=14)
    icon_bell(c, d, PW - 92, 28); circle(img, None, c.p(PW - 56), c.p(12), c.p(32), 'Y')
    # player + below-player block
    player(c, img, np_it, px0, 80, pw, ph, 12, 0.18, desktop=True)
    y = 80 + ph + 12
    for k, ln in enumerate(wrap(c.F, np_it['title'], 20, 700, c.p(pw), 2)):
        c.F.draw(d, c.p(px0), c.p(y + 28 * (k + 0.5)), ln, 20, 700, TEXT); y += 28
    y += 8; circle(img, np_it.get('avatar'), c.p(px0), c.p(y), c.p(40), np_it.get('channel', ''))
    c.F.draw(d, c.p(px0 + 52), c.p(y + 11), np_it.get('channel', ''), 16, 500, TEXT)
    c.F.draw(d, c.p(px0 + 52), c.p(y + 30), np_it.get('subs', '1.2M subscribers'), 12, 400, TEXT2)
    pill(d, c.F, c.p(px0 + 52 + max(c.F.width(np_it.get('channel', ''), 16, 500) / c.s, 90) + 24), c.p(y + 2), 'Subscribe', 14, 500, 36, sel=True, s=c.s, pad=16)
    x = c.p(px0 + pw - 380)
    for lab in ['82K  |', 'Share', 'Save', '...']:
        x = pill(d, c.F, x, c.p(y + 2), lab, 14, 500, 36, s=c.s, pad=16) + c.p(8)
    y += 52
    d.rounded_rectangle((c.p(px0), c.p(y), c.p(px0 + pw), c.p(y + 104)), radius=c.p(12), fill=CHIP)
    c.F.draw(d, c.p(px0 + 12), c.p(y + 22), f"{np_it.get('views','')}  {np_it.get('age','')}", 14, 500, TEXT)
    for k, w_ in enumerate((0.92, 0.85, 0.4)):
        d.rounded_rectangle((c.p(px0 + 12), c.p(y + 44 + k * 20), c.p(px0 + 12 + (pw - 24) * w_), c.p(y + 52 + k * 20)), radius=c.p(4), fill=(58, 58, 58))
    # sidebar
    chips_row(c, img, 80, ['All', 'From ' + np_it.get('channel', ''), 'Related', 'For you', 'Recently uploaded'], x0=sx, x_max=sx + 402 - 40)
    d.rectangle((c.p(sx + 402), c.p(76), c.p(PW), c.p(116)), fill=BG)
    y = 80 + 32 + 12
    for k, it in enumerate(items):
        b = compact(c, img, it, sx, y, 402, st['sb_title_px'], st['sb_title_lh'], st['sb_title_lines'], st['sb_meta_px'],
                    st['sb_meta_lh'], st['sb_thumb'], 8, 24, rects, 'candidate' if k == pos else 'competitor', '•', True)
        y = b + 8
    page = img.crop((0, 0, c.p(PW), c.p(max(y + 24, 80 + ph + 260))))
    return {'sidebar': (page.crop((0, 0, c.p(PW), c.p(720))), shift(c, rects, 0, 0, 720)),
            'sidebar_page': (page, [dict(r, visible=True) for r in rects])}


# ---------------------------------------------------------------- glance + metrics
def glance(img, scale=0.5, blur=1.1, smear=5):
    """Peripheral-vision proxy: downscale, Gaussian blur, short vertical smear (scroll motion)."""
    sm = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
    sm = sm.filter(ImageFilter.GaussianBlur(blur))
    if smear > 1:
        a = np.asarray(sm).astype(np.float32); acc = np.zeros_like(a)
        for k in range(smear): acc += np.roll(a, k - smear // 2, axis=0)
        sm = Image.fromarray(np.clip(acc / smear, 0, 255).astype(np.uint8))
    return sm


def thumb_metrics(img, box):
    t = img.crop(tuple(int(v) for v in box)).convert('RGB'); a = np.asarray(t).astype(np.float32)
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    rg, yb = a[..., 0] - a[..., 1], 0.5 * (a[..., 0] + a[..., 1]) - a[..., 2]
    colf = math.hypot(rg.std(), yb.std()) + 0.3 * math.hypot(rg.mean(), yb.mean())
    hsv = np.asarray(t.convert('HSV')).astype(np.float32) / 255; S, V = hsv[..., 1], hsv[..., 2]
    bright = float(((V > 0.6) & ((S > 0.45) | (V > 0.85))).mean())
    gy, gx = np.gradient(lum); edge = float((np.hypot(gx, gy) > 40).mean())
    return dict(luma=float(lum.mean()), p90luma=float(np.percentile(lum, 90)), colorful=float(colf), brightsat=bright, edges=edge)


def feat(im):
    """Identical to research/niche/work/sim_lib.py feat(): 16x9 LAB layout + saturated-hue histogram."""
    s = np.asarray(im.resize((16, 9), Image.BOX).convert('LAB')).astype(float).ravel() / 255
    hsv = np.asarray(im.resize((160, 90)).convert('HSV')).astype(float) / 255
    H, S = hsv[..., 0] * 360, hsv[..., 1]; m = S > 0.25
    hh, _ = np.histogram(H[m], bins=12, range=(0, 360)); hh = hh / (m.size)
    return np.concatenate([s, hh * 3])


def report(name, img, rects):
    """Pop metrics of every fully visible thumbnail, as displayed. 'distinct' = mean sim_lib feature distance to
    the other visible thumbnails (how much a card differs from its neighbours; higher pops more)."""
    rows = [(r, thumb_metrics(img, r['thumb'])) for r in rects if r.get('visible')]
    if len(rows) < 2:
        return []
    fs = [feat(img.crop(tuple(int(v) for v in r['thumb']))) for r, _ in rows]
    for k, (_, m) in enumerate(rows):
        m['distinct'] = float(np.mean([np.linalg.norm(fs[k] - fs[j]) for j in range(len(rows)) if j != k]))
    keys = ['luma', 'p90luma', 'colorful', 'brightsat', 'edges', 'distinct']
    print(f'\n[{name}] {len(rows)} visible cards. Candidate rank (1 = highest) among visible cards:')
    out = []
    for k in keys:
        vals = sorted([m[k] for _, m in rows], reverse=True)
        cv = [m[k] for r, m in rows if r['tag'] == 'candidate']
        if cv:
            rank = vals.index(cv[0]) + 1; med = float(np.median([m[k] for r, m in rows if r['tag'] != 'candidate']))
            print(f'  {k:10s} cand={cv[0]:7.3f}  competitor median={med:7.3f}  rank {rank}/{len(rows)}')
            out.append(dict(metric=k, cand=cv[0], comp_median=med, rank=rank, of=len(rows)))
    return out


# ---------------------------------------------------------------- spec
def load_spec(path):
    sp = json.load(open(path)); base = os.path.dirname(os.path.abspath(path))
    def norm(it, b):
        it = dict(it)
        for k in ('thumb', 'avatar'):
            if it.get(k) and not os.path.isabs(it[k]): it[k] = os.path.normpath(os.path.join(b, it[k]))
        return it
    comps = [norm(i, base) for i in sp.get('competitors', [])]
    hs = sp.get('hosts', []); hs = [hs] if isinstance(hs, str) else hs
    for h in hs:
        f, _, setname = h.partition('#'); f = os.path.normpath(os.path.join(base, f)); hb = os.path.dirname(f)
        db = json.load(open(f))
        for nm in (setname.split('+') if setname else db.keys()):
            comps += [norm(i, hb) for i in db[nm] if i.get('thumb')]
    seen, uniq = set(), []
    for i in comps:
        k = i.get('id') or i['thumb']
        if k not in seen and k not in set(sp.get('exclude', [])): seen.add(k); uniq.append(i)
    cands = [norm(i, base) for i in (sp.get('candidates') or [sp['candidate']])]
    for i in uniq + cands:  # YouTube's grey 'New' chip (desktop sidebar) for uploads under a week old
        if 'badge' not in i and re.match(r'^\d+\s*(s|sec|seconds?|min|minutes?|h|hr|hours?|d|days?)\s+ago', i.get('age', '')):
            i['badge'] = 'New'
    npi = sp.get('now_playing')
    if isinstance(npi, dict): npi = norm(npi, base)
    elif isinstance(npi, str): npi = next(i for i in uniq if i.get('id') == npi)
    else:
        def vc(i):
            try: return i.get('view_count') or 0
            except Exception: return 0
        npi = max(uniq, key=vc)
    return sp, cands, uniq, npi


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec'); ap.add_argument('--out', required=True)
    ap.add_argument('--layouts', default='home,upnext,sidebar'); ap.add_argument('--seed', type=int)
    ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--glance', action='store_true')
    ap.add_argument('--glance-scale', type=float, default=0.5); ap.add_argument('--report', action='store_true')
    ap.add_argument('--pos', nargs='*', default=[]); ap.add_argument('--n', nargs='*', default=[])
    ap.add_argument('--quality', type=int, default=92)
    ap.add_argument('--sheet', action='store_true', help='also write PREFIX_sheet.jpg: the three screens + glances side by side')
    ap.add_argument('--gate', action='store_true', help='run research/niche/work/gate.py on each candidate thumbnail')
    a = ap.parse_args()
    sp, cands, comps, npi = load_spec(a.spec)
    seed = a.seed if a.seed is not None else sp.get('seed', 1)
    nmap = dict(dict(home=6, upnext=10, sidebar=10), **sp.get('n', {}))
    nmap.update({k: int(v) for k, v in (x.split('=') for x in a.n)})
    pmap = dict(sp.get('pos', {})); pmap.update({k: int(v) for k, v in (x.split('=') for x in a.pos)})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    summary = {}
    for ci, cand in enumerate(cands):
        prefix = a.out if len(cands) == 1 else f'{a.out}_{ci + 1}'
        for lay in a.layouts.split(','):
            rng = random.Random(f'{seed}:{lay}')  # same seed -> same neighbours/positions for every candidate
            pool = [i for i in comps if i is not npi] if lay != 'home' else list(comps)
            rng.shuffle(pool); n = nmap[lay]
            vis = {'home': n, 'upnext': n, 'sidebar': 5}[lay]  # sidebar: keep the candidate above the fold
            pos = pmap.get(lay, rng.randrange(0, min(n, vis)))
            c = Ctx(a.scale, sp.get('style'))
            cand = dict(cand, id=cand.get('id', 'CANDIDATE'))
            out = {'home': lambda: render_home(c, cand, pool, n, pos, rng),
                   'upnext': lambda: render_upnext(c, cand, pool, npi, n, pos, rng),
                   'sidebar': lambda: render_sidebar(c, cand, pool, npi, n, pos, rng)}[lay]()
            for name, (im, rects) in out.items():
                fn = f'{prefix}_{name}.jpg'; im.save(fn, quality=a.quality); print(fn, im.size)
                meta = dict(layout=name, seed=seed, scale=a.scale, position=pos, now_playing=npi.get('title') if lay != 'home' else None, cards=rects)
                if a.report and name in ('home_scroll', 'upnext', 'upnext_scroll', 'sidebar'):
                    meta['metrics'] = report(f'{os.path.basename(prefix)} {name}', im, rects)
                    summary[f'{os.path.basename(prefix)}:{name}'] = meta['metrics']
                json.dump(meta, open(f'{prefix}_{name}.json', 'w'), indent=1)
                if a.glance and name in ('home', 'upnext', 'sidebar'):
                    g = glance(im, a.glance_scale); g.save(f'{prefix}_{name}_glance.jpg', quality=a.quality); print(f'{prefix}_{name}_glance.jpg', g.size)
        if a.sheet:
            make_sheet(prefix, [l for l in ('home', 'upnext', 'sidebar') if l in a.layouts.split(',')], a.quality)
        if a.gate:
            import subprocess
            subprocess.run([sys.executable, '-I', GATE, cand['thumb']])
    return summary


def make_sheet(prefix, layouts, quality):
    """Phone screens at true scale, desktop viewport at true scale, glances under each; one image for review."""
    ims = [Image.open(f'{prefix}_{l}.jpg') for l in layouts]
    gl = [Image.open(f'{prefix}_{l}_glance.jpg') if os.path.exists(f'{prefix}_{l}_glance.jpg') else None for l in layouts]
    W = sum(i.width for i in ims) + 24 * (len(ims) + 1); H = max(i.height for i in ims) + max((g.height for g in gl if g), default=0) + 72
    sh = Image.new('RGB', (W, H), (40, 40, 40)); d = ImageDraw.Draw(sh); x = 24
    f = ImageFont.truetype(os.path.join(FONT_DIR, ROBOTO[500]), 14)
    for l, im, g in zip(layouts, ims, gl):
        d.text((x, 6), l + ' (true scale)', font=f, fill=(200, 200, 200)); sh.paste(im, (x, 26))
        if g:
            d.text((x, 30 + im.height + 4), 'glance', font=f, fill=(200, 200, 200)); sh.paste(g, (x, 30 + im.height + 22))
        x += im.width + 24
    sh.save(f'{prefix}_sheet.jpg', quality=quality); print(f'{prefix}_sheet.jpg', sh.size)


if __name__ == '__main__':
    main()
