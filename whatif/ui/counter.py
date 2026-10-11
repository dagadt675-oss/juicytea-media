"""Left counter.

Format B uses the slate's Anton slot stack: US unit big, metric small,
each shown value held by the caller. The caption band and the shadow
helper still come from the shared format A overlay.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ui._load import sibling_overlay

_ov = sibling_overlay()
SANS, SANS_SEMI, SERIF = _ov.SANS, _ov.SANS_SEMI, _ov.SERIF
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

# Normalized. The karaoke band is y 0.64–0.78 and stays empty.
CAPTION_Y0 = 0.64
CAPTION_Y1 = 0.78

ANTON = Path(__file__).resolve().parents[1] / "scale_journey" / "assets" / "fonts" / "Anton-Regular.ttf"
ORANGE = (255, 122, 40, 255)


@lru_cache(maxsize=32)
def _anton(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ANTON), size)


def _fit_anton(text: str, max_w: float, size: int, floor: int = 36) -> ImageFont.FreeTypeFont:
    size = int(size)
    while size > floor and _anton(size).getlength(text) > max_w:
        size -= 2
    return _anton(size)


def draw_counter(image: Image.Image, label: str, number: str, unit: str | None = None) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Draw the shared left counter. Returns the image and the ink box."""
    img = image.convert("RGBA")
    width, height = img.size
    label_font = _font(SANS, max(16, int(width * 0.020)))
    number_font = _font(SERIF, max(54, int(width * 0.078)))
    unit_font = _font(SANS_SEMI, max(18, int(width * 0.028)))
    x = int(width * 0.055)
    y = int(height * 0.40)
    _shadow_text(img, (x, y), label, label_font, fill=_alpha((255, 255, 255), 230), anchor="lt", radius=4, opacity=120)
    num_y = y + int(height * 0.028)
    _shadow_text(img, (x, num_y), number, number_font, fill=(255, 255, 255, 255), anchor="lt", radius=6, opacity=140)
    probe = ImageDraw.Draw(img)
    bbox = probe.textbbox((x, num_y), number, font=number_font, anchor="lt")
    bottom = bbox[3]
    right = bbox[2]
    if unit:
        unit_x = bbox[2] + int(width * 0.014)
        unit_y = bbox[3] - int(height * 0.004)
        _shadow_text(img, (unit_x, unit_y), unit, unit_font, fill=_alpha((255, 255, 255), 235), anchor="ls", radius=4, opacity=120)
        ub = probe.textbbox((unit_x, unit_y), unit, font=unit_font, anchor="ls")
        right = max(right, ub[2])
        bottom = max(bottom, ub[3])
    box = (x, y, int(right), int(bottom))
    band0 = int(CAPTION_Y0 * height)
    if box[3] > band0:
        raise RuntimeError(f"counter entered the caption band: {box} vs {band0}")
    return img, box


def _stroke(base: Image.Image, xy, text, font, fill, stroke=5):
    draw = ImageDraw.Draw(base)
    draw.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 150), anchor="lt")
    return draw.textbbox(xy, text, font=font, anchor="lt")


def _slot(base: Image.Image, xy, old: str, new: str, roll: float, font, fill) -> tuple[int, int, int, int]:
    """Slide the whole token. roll 0 is the old value, roll 1 is the new one.

    The window is tall enough for the stroke, and the returned box hugs the
    token that is actually on screen so the unit does not jump ahead.
    """
    shown = new if roll >= 0.5 or old == new else old
    if roll >= 0.999 or old == new:
        box = _stroke(base, xy, shown, font, fill)
        return tuple(int(v) for v in box)
    stroke = 5
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + stroke * 2 + 10
    pad = stroke + 2
    width = int(max(font.getlength(old), font.getlength(new)) + pad * 2 + 8)
    tall = Image.new("RGBA", (max(width, 1), line_h * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tall)
    draw.text((pad, pad), old, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
    draw.text((pad, line_h + pad), new, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
    top = int(round(min(1.0, max(0.0, roll)) * line_h))
    crop = tall.crop((0, top, width, top + line_h))
    base.alpha_composite(crop, (int(xy[0]), int(xy[1])))
    text_w = font.getlength(shown)
    glyph_bottom = int(xy[1] + pad + ascent + descent)
    return (int(xy[0]), int(xy[1]), int(xy[0] + pad + text_w), glyph_bottom)


def _centered_column(img, origin, label, number, previous, roll, unit, num_px, unit_px):
    """One big readout. origin is the top-left of the column."""
    width = img.size[0]
    x, y = origin
    label_font = _font(SANS, max(22, int(width * 0.028)))
    _shadow_text(img, (x, y), label, label_font, fill=_alpha((255, 122, 40), 255), anchor="lt", radius=3, opacity=140)
    num_font = _anton(num_px)
    num_y = y + int(label_font.size * 1.15)
    box = _slot(img, (x, num_y), previous or number, number, roll, num_font, (255, 248, 242, 255))
    unit_font = _anton(unit_px)
    unit_x = box[2] + int(width * 0.012)
    ub = _stroke(img, (unit_x, box[3] - int(unit_font.size * 0.92)), (unit or "").upper(), unit_font, ORANGE, stroke=4)
    right = max(box[2], int(ub[2]))
    bottom = max(box[3], int(ub[3]))
    return (x, y, right, bottom)


def draw_scale_counter(
    image: Image.Image,
    label: str,
    number: str,
    unit: str | None = None,
    metric: str | None = None,
    previous: str | None = None,
    roll: float = 1.0,
    second_label: str | None = None,
    second_number: str | None = None,
    second_unit: str | None = None,
    second_previous: str | None = None,
    second_roll: float = 1.0,
    align: str = "left",
    anchor_y: int | None = None,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Anton height/speed stack. Above the caption band."""
    img = image.convert("RGBA")
    width, height = img.size
    if align == "center" and second_label and second_number:
        y = anchor_y if anchor_y is not None else int(height * 0.045)
        # Measure both columns, then center the pair. Numbers stay at least 80 px.
        height_px = 112
        speed_px = 88
        probe = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        left = _centered_column(probe, (0, 0), label, number, previous, roll, unit, height_px, 42)
        right = _centered_column(probe, (0, 0), second_label, second_number, second_previous, second_roll, second_unit, speed_px, 36)
        gap = int(width * 0.06)
        pair = (left[2] - left[0]) + gap + (right[2] - right[0])
        x0 = int((width - pair) / 2)
        left_box = _centered_column(img, (x0, y), label, number, previous, roll, unit, height_px, 42)
        x1 = left_box[2] + gap
        right_box = _centered_column(img, (x1, y), second_label, second_number, second_previous, second_roll, second_unit, speed_px, 36)
        box = (left_box[0], y, right_box[2], max(left_box[3], right_box[3]))
        band0 = int(CAPTION_Y0 * height)
        if box[3] > band0:
            raise RuntimeError(f"counter entered the caption band: {box} vs {band0}")
        return img, box
    x = int(width * 0.055)
    y = int(height * 0.175)
    label_font = _font(SANS, max(15, int(width * 0.018)))
    _shadow_text(img, (x, y), label, label_font, fill=_alpha((255, 122, 40), 255), anchor="lt", radius=3, opacity=110)
    num_font = _fit_anton(number, width * 0.62, max(72, int(width * 0.118)))
    num_y = y + int(height * 0.026)
    box = _slot(img, (x, num_y), previous or number, number, roll, num_font, (255, 248, 242, 255))
    unit_font = _fit_anton(unit or "ft", width * 0.22, max(28, int(width * 0.042)))
    unit_x = box[2] + int(width * 0.012)
    unit_y = box[3] - int(unit_font.size * 0.92)
    if unit:
        ub = _stroke(img, (unit_x, unit_y), unit.upper(), unit_font, ORANGE, stroke=4)
        box = (box[0], min(box[1], y), max(box[2], int(ub[2])), max(box[3], int(ub[3])))
    bottom = box[3]
    if metric:
        metric_font = _font(SANS, max(14, int(width * 0.018)))
        my = bottom + int(height * 0.006)
        _shadow_text(img, (x, my), metric, metric_font, fill=_alpha((255, 255, 255), 210), anchor="lt", radius=3, opacity=90)
        mb = ImageDraw.Draw(img).textbbox((x, my), metric, font=metric_font, anchor="lt")
        bottom = int(mb[3])
    if second_label and second_number:
        sy = bottom + int(height * 0.016)
        _shadow_text(img, (x, sy), second_label, label_font, fill=_alpha((255, 122, 40), 255), anchor="lt", radius=3, opacity=100)
        sfont = _fit_anton(second_number, width * 0.40, max(40, int(width * 0.058)))
        sb = _slot(img, (x, sy + int(height * 0.022)), second_previous or second_number, second_number, second_roll, sfont, (255, 248, 242, 255))
        bottom = sb[3]
        right = sb[2]
        if second_unit:
            ufont = _fit_anton(second_unit, width * 0.18, max(22, int(width * 0.032)))
            ub = _stroke(img, (sb[2] + int(width * 0.028), sb[3] - int(ufont.size * 0.9)), second_unit.upper(), ufont, ORANGE, stroke=3)
            right = int(ub[2])
            bottom = max(bottom, int(ub[3]))
        box = (x, y, max(box[2], right), bottom)
    else:
        box = (x, y, box[2], bottom)
    band0 = int(CAPTION_Y0 * height)
    if box[3] > band0:
        raise RuntimeError(f"counter entered the caption band: {box} vs {band0}")
    return img, box
