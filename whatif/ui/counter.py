"""Left counter. Same fonts, shadow, and screen slot as format A."""

from __future__ import annotations

from PIL import Image, ImageDraw

from ui._load import sibling_overlay

_ov = sibling_overlay()
SANS, SANS_SEMI, SERIF = _ov.SANS, _ov.SANS_SEMI, _ov.SERIF
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

# Normalized. The karaoke band is y 0.64–0.78 and stays empty.
CAPTION_Y0 = 0.64
CAPTION_Y1 = 0.78


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
