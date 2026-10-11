"""Left-side Anton counter, leader lines, hook title, ending card.

The karaoke band (default y 1229–1382) is left empty of type, rules, and
leader lines. 3D plates show through it.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .quantity import choose_unit, decimals_for
from .spec import Episode, Frame, ending_lines, highlight_phrase, title_lines

FONT_PATH = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "Anton-Regular.ttf"

ORANGE = (255, 79, 26, 255)
WHITE = (255, 248, 242, 255)
SHADOW = (0, 0, 0, 150)


@lru_cache(maxsize=32)
def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


@lru_cache(maxsize=4)
def _vignette(width: int, height: int) -> Image.Image:
    yy, xx = np.mgrid[0:height, 0:width]
    nx = (xx - width / 2) / (width * 0.52)
    ny = (yy - height / 2) / (height * 0.55)
    r = np.sqrt(nx * nx + ny * ny)
    alpha = np.clip((r - 0.45) / 1.15, 0.0, 0.34)
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    arr[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def _band(ep: Episode) -> tuple[int, int]:
    band = ep.raw.get("caption_band", [1229, 1382])
    return int(band[0]), int(band[1])


def _hits_band(box, band) -> bool:
    y0, y1 = band
    return box[3] > y0 and box[1] < y1


def _fit(text: str, max_w: float, size: int, floor: int = 28) -> ImageFont.FreeTypeFont:
    size = int(size)
    while size > floor and _font(size).getlength(text) > max_w:
        size -= 2
    return _font(size)


def _tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking, stroke=4):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill, stroke_width=stroke, stroke_fill=SHADOW)
        x += font.getlength(ch) + tracking
    return x


def _highlighted(draw, xy, text, highlight, font, fill, hi):
    x, y = xy
    if highlight and highlight in text:
        pre, mid, post = text.partition(highlight)
        parts = ((pre, fill), (mid, hi), (post, fill))
    else:
        parts = ((text, fill),)
    for chunk, color in parts:
        if not chunk:
            continue
        draw.text((x, y), chunk, font=font, fill=color, stroke_width=5, stroke_fill=SHADOW)
        x += font.getlength(chunk)
    return x


def _slot_strings(param: float, param_next: float) -> tuple[str, str, float]:
    cur = math.floor(param + 1e-9)
    frac = param - cur
    delta = param_next - param
    if delta <= 1e-8:
        text = str(int(cur))
        return text, text, 0.0
    remaining = (1.0 - frac) / delta
    if remaining < 6.0:
        u = 1.0 - remaining / 6.0
        u = u * u * (3.0 - 2.0 * u)
        return str(int(cur)), str(int(cur + 1)), u
    text = str(int(cur))
    return text, text, 0.0


def _draw_slot(base: Image.Image, xy, old: str, new: str, u: float, font, fill) -> tuple[int, int, int, int]:
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 6
    width = int(max(font.getlength(old), font.getlength(new)) + 18)
    tall = Image.new("RGBA", (max(width, 1), line_h * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tall)
    draw.text((2, 2), old, font=font, fill=fill, stroke_width=5, stroke_fill=SHADOW)
    draw.text((2, line_h + 2), new, font=font, fill=fill, stroke_width=5, stroke_fill=SHADOW)
    top = int(round(u * line_h))
    crop = tall.crop((0, top, width, top + line_h))
    base.alpha_composite(crop, (int(xy[0]), int(xy[1])))
    return (int(xy[0]), int(xy[1]), int(xy[0] + width), int(xy[1] + line_h))


def _draw_length(base, xy, meters: float, font, fill) -> tuple[int, int, int, int]:
    """Whole-number slot. The last displayed digit decides when the reel trips,
    and the entire token slides so columns never collide."""
    unit, value = choose_unit(meters)
    decimals = decimals_for(value)
    scale = 10 ** decimals
    scaled = max(0.0, value) * scale
    whole = math.floor(scaled + 1e-8)
    frac = max(0.0, scaled - whole)
    shown = f"{whole / scale:.{decimals}f}"
    nxt = f"{(whole + 1) / scale:.{decimals}f}"
    # Trip the reel only in the last part of the digit, so the number sits still
    # and then ticks instead of smearing.
    u = 0.0
    if frac > 0.78:
        u = (frac - 0.78) / 0.22
        u = u * u * (3.0 - 2.0 * u)
    box = _draw_slot(base, xy, shown, nxt, u, font, fill)
    unit_font = _font(max(26, font.size - 22))
    draw = ImageDraw.Draw(base)
    ux = box[2] + 8
    uy = box[1] + max(0, (box[3] - box[1] - unit_font.getmetrics()[0]) // 3)
    draw.text((ux, uy), unit, font=unit_font, fill=ORANGE, stroke_width=3, stroke_fill=SHADOW)
    unit_w = unit_font.getlength(unit)
    return (box[0], box[1], int(ux + unit_w), box[3])


def _particles(base: Image.Image, t: float, band: tuple[int, int], phase: str) -> None:
    if phase == "dissolve":
        return
    draw = ImageDraw.Draw(base)
    n = 26
    for i in range(n):
        speed = 22 + (i % 6) * 9
        x = (53 + i * 83) % base.size[0]
        y = (1180 - (t * speed + i * 71)) % 1500
        if band[0] - 8 <= y <= band[1] + 8:
            continue
        if x < 560 and 300 <= y <= 760:
            continue
        r = 1.4 + (i % 3)
        alpha = 50 + (i % 4) * 12
        color = (255, 214, 170, alpha) if phase != "ending" else (255, 244, 230, alpha)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def compose(plate: Image.Image, ep: Episode, fr: Frame) -> tuple[Image.Image, list[tuple[int, int, int, int]]]:
    """Draw UI on a copy of ``plate``. Returns the image and graphic boxes."""
    img = plate.convert("RGBA")
    vig = _vignette(img.size[0], img.size[1])
    img = Image.alpha_composite(img, vig)
    band = _band(ep)
    boxes: list[tuple[int, int, int, int]] = []
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    _particles(layer, fr.t, band, fr.phase)

    # Hook title, top-left, fades as the zoom gets going.
    if fr.title_opacity > 0.02:
        lines = title_lines(ep)
        highlight = str(ep.raw.get("hook", {}).get("highlight", ""))
        y = 118
        alpha = fr.title_opacity
        for line in lines:
            fnt = _fit(line, 960, 64)
            # Fade by drawing into a sublayer.
            sub = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sd = ImageDraw.Draw(sub)
            _highlighted(sd, (68, y), line, highlight, fnt, WHITE, ORANGE)
            if alpha < 0.999:
                arr = np.array(sub)
                arr[..., 3] = (arr[..., 3].astype(np.float32) * alpha).astype(np.uint8)
                sub = Image.fromarray(arr, "RGBA")
            layer = Image.alpha_composite(layer, sub)
            ascent, descent = fnt.getmetrics()
            w = int(fnt.getlength(line))
            boxes.append((68, y, 68 + w, y + ascent + descent))
            y += ascent + descent - 6
        draw = ImageDraw.Draw(layer)

    # Stable counter block. Sits under the title and well above the caption band.
    counter = ep.raw["counter"]
    x0, y0 = 68, 430
    label_font = _font(26)
    _tracked(draw, (x0, y0), counter["primary"]["label"], label_font, ORANGE, 4, stroke=3)
    lab_w = int(label_font.getlength(counter["primary"]["label"]) + 4 * max(0, len(counter["primary"]["label"]) - 1))
    ascent, descent = label_font.getmetrics()
    boxes.append((x0, y0, x0 + lab_w, y0 + ascent + descent))

    old, new, u = _slot_strings(fr.param, fr.param_next)
    num_font = _font(118)
    slot_box = _draw_slot(layer, (x0, y0 + 34), old, new, u, num_font, WHITE)
    boxes.append(slot_box)
    draw = ImageDraw.Draw(layer)

    y1 = slot_box[3] + 8
    _tracked(draw, (x0, y1), counter["secondary"]["label"], label_font, ORANGE, 4, stroke=3)
    lab2 = int(label_font.getlength(counter["secondary"]["label"]) + 4 * len(counter["secondary"]["label"]))
    boxes.append((x0, y1, x0 + lab2, y1 + ascent + descent))
    sec_font = _font(68)
    sec_box = _draw_length(layer, (x0, y1 + 32), fr.metrics.height_m, sec_font, WHITE)
    boxes.append(sec_box)
    draw = ImageDraw.Draw(layer)

    # Fact line, top-left, only once the title is gone.
    if fr.fact and fr.fact_opacity > 0.02 and fr.title_opacity < 0.15:
        fnt = _fit(fr.fact, 940, 34, floor=22)
        sub = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sub)
        sd.text((68, 132), fr.fact, font=fnt, fill=WHITE, stroke_width=4, stroke_fill=SHADOW)
        arr = np.array(sub)
        arr[..., 3] = (arr[..., 3].astype(np.float32) * fr.fact_opacity).astype(np.uint8)
        layer = Image.alpha_composite(layer, Image.fromarray(arr, "RGBA"))
        fa, fd = fnt.getmetrics()
        boxes.append((68, 132, 68 + int(fnt.getlength(fr.fact)), 132 + fa + fd))
        draw = ImageDraw.Draw(layer)

    # Leader labels. Park them on the right, above the caption band.
    parked_y = 760
    for item in fr.labels:
        if item["opacity"] <= 0.02:
            continue
        screen = item["screen"]
        label = item["label"]
        sub = item["sub"]
        fnt = _font(28)
        sub_f = _font(22)
        block_w = int(max(fnt.getlength(label), sub_f.getlength(sub) if sub else 0)) + 8
        block_h = 62
        lx = 1080 - 72 - block_w
        ly = parked_y
        parked_y += 88
        if ly + block_h >= band[0] - 16:
            break
        subl = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(subl)
        sd.text((lx, ly), label, font=fnt, fill=WHITE, stroke_width=3, stroke_fill=SHADOW)
        if sub:
            sd.text((lx, ly + 32), sub, font=sub_f, fill=ORANGE, stroke_width=2, stroke_fill=SHADOW)
        if screen is not None:
            ax, ay = screen
            # Stop the line at the caption band rather than crossing it.
            x1, y1p = lx - 8, ly + 16
            if ay > band[0] - 8:
                # Anchor is in or below the band: keep the line in the upper picture.
                if y1p < band[0] - 12:
                    ay = min(ay, band[0] - 14)
                else:
                    ax = ay = None
            if ax is not None and 0 <= ax <= img.size[0] and 40 <= ay <= band[0] - 10:
                sd.line((x1, y1p, ax, ay), fill=(255, 248, 242, 230), width=2)
                sd.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), fill=ORANGE)
                # The line's bbox must stay out of the band. Record a tight box.
                boxes.append((int(min(x1, ax)), int(min(y1p, ay)), int(max(x1, ax)) + 2, int(max(y1p, ay)) + 2))
        arr = np.array(subl)
        arr[..., 3] = (arr[..., 3].astype(np.float32) * item["opacity"]).astype(np.uint8)
        layer = Image.alpha_composite(layer, Image.fromarray(arr, "RGBA"))
        boxes.append((lx, ly, lx + block_w, ly + block_h))

    if fr.ending_opacity > 0.02:
        lines = ending_lines(ep)
        highlight = highlight_phrase(ep, "ending")
        y = 128
        alpha = fr.ending_opacity
        for line in lines:
            fnt = _fit(line, 920, 52)
            w = fnt.getlength(line)
            x = (img.size[0] - w) / 2
            sub = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sd = ImageDraw.Draw(sub)
            _highlighted(sd, (x, y), line, highlight, fnt, WHITE, ORANGE)
            arr = np.array(sub)
            arr[..., 3] = (arr[..., 3].astype(np.float32) * alpha).astype(np.uint8)
            layer = Image.alpha_composite(layer, Image.fromarray(arr, "RGBA"))
            ascent, descent = fnt.getmetrics()
            boxes.append((int(x), y, int(x + w), y + ascent + descent))
            y += ascent + descent + 8

    img = Image.alpha_composite(img, layer)
    # Drop any box that only records a particle-free graphic which we already
    # placed above the band. Filter defensively.
    safe = [b for b in boxes if not _hits_band(b, band)]
    return img.convert("RGB"), safe
