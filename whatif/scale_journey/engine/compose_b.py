"""Format B screen UI. Counter and type come from the shared whatif.ui."""

from __future__ import annotations

from PIL import Image

from ui._load import sibling_overlay

_ov = sibling_overlay()
SERIF, SANS = _ov.SERIF, _ov.SANS
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

from ui.counter import draw_counter
from ui.pills import draw_pill


def _lines(text: str, width_chars: int = 28) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        trial = " ".join(cur + [word])
        if len(trial) > width_chars and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines


def compose_b(plate: Image.Image, ep, fr) -> Image.Image:
    img = plate.convert("RGBA")
    w, h = img.size
    if fr.title_alpha > 0.02:
        font = _font(SERIF, max(40, int(w * 0.048)))
        y = int(h * 0.08)
        for line in _lines(ep.raw["title"], 26):
            _shadow_text(
                img,
                (w / 2, y),
                line,
                font,
                fill=_alpha((255, 255, 255), 255 * fr.title_alpha),
                anchor="mt",
                radius=12,
                opacity=int(160 * fr.title_alpha),
            )
            y += int(font.size * 1.05)
    img, _box = draw_counter(img, fr.label_primary, fr.primary, fr.primary_unit)
    # Second line of the same counter stack, still above the caption band.
    sub_y = int(h * 0.53)
    label_font = _font(SANS, max(16, int(w * 0.020)))
    num_font = _font(SERIF, max(36, int(w * 0.046)))
    x = int(w * 0.055)
    _shadow_text(img, (x, sub_y), fr.label_secondary, label_font, fill=_alpha((255, 255, 255), 220), anchor="lt", radius=3, opacity=100)
    _shadow_text(
        img,
        (x, sub_y + int(h * 0.025)),
        f"{fr.secondary} {fr.secondary_unit}".strip(),
        num_font,
        fill=(255, 255, 255, 255),
        anchor="lt",
        radius=5,
        opacity=120,
    )
    if fr.pill_alpha > 0.02 and fr.pill_title:
        img, _pill = draw_pill(
            img,
            fr.pill_title,
            fr.pill_sub,
            None,
            (w * 0.58, h * 0.30),
            fr.pill_alpha,
        )
    if fr.ending_alpha > 0.02:
        font = _font(SERIF, max(36, int(w * 0.044)))
        y = int(h * 0.10)
        for line in ep.raw["ending"]["lines"]:
            _shadow_text(
                img,
                (w / 2, y),
                line,
                font,
                fill=_alpha((255, 255, 255), 255 * fr.ending_alpha),
                anchor="mt",
                radius=10,
                opacity=int(150 * fr.ending_alpha),
            )
            y += int(font.size * 1.15)
    return img.convert("RGB")
