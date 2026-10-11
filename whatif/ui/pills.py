"""Reference labels. Same type as the format A ticker, pinned to a screen point."""

from __future__ import annotations

from PIL import Image, ImageDraw

from ui._load import sibling_overlay

_ov = sibling_overlay()
SANS, SANS_SEMI = _ov.SANS, _ov.SANS_SEMI
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

from ui.counter import CAPTION_Y0


def draw_pill(
    image: Image.Image,
    title: str,
    sub: str,
    anchor_xy: tuple[float, float] | None,
    origin: tuple[float, float],
    alpha: float = 1.0,
) -> tuple[Image.Image, tuple[int, int, int, int] | None]:
    if alpha <= 0.02:
        return image, None
    img = image.convert("RGBA")
    width, height = img.size
    title_font = _font(SANS_SEMI, max(18, int(width * 0.026)))
    sub_font = _font(SANS, max(15, int(width * 0.020)))
    x, y = origin
    fill = _alpha((255, 255, 255), 255 * alpha)
    sub_fill = _alpha((255, 255, 255), 220 * alpha)
    _shadow_text(img, (x, y), title, title_font, fill=fill, anchor="lt", radius=4, opacity=int(120 * alpha))
    _shadow_text(img, (x, y + int(height * 0.028)), sub, sub_font, fill=sub_fill, anchor="lt", radius=3, opacity=int(100 * alpha))
    probe = ImageDraw.Draw(img)
    b1 = probe.textbbox((x, y), title, font=title_font, anchor="lt")
    b2 = probe.textbbox((x, y + int(height * 0.028)), sub, font=sub_font, anchor="lt")
    box = (int(min(b1[0], b2[0])), int(min(b1[1], b2[1])), int(max(b1[2], b2[2])), int(max(b1[3], b2[3])))
    band0 = int(CAPTION_Y0 * height)
    if box[3] >= band0:
        raise RuntimeError(f"pill entered the caption band: {box}")
    if anchor_xy is not None:
        ax, ay = anchor_xy
        if ay < band0 - 8:
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer)
            draw.line((box[0] - 6, (box[1] + box[3]) / 2, ax, ay), fill=(255, 255, 255, int(210 * alpha)), width=2)
            r = 5
            draw.ellipse((ax - r, ay - r, ax + r, ay + r), fill=(255, 255, 255, int(230 * alpha)))
            img.alpha_composite(layer)
    return img, box
