"""Format B screen UI. Counter and type come from the shared whatif.ui."""

from __future__ import annotations

from PIL import Image

from ui._load import sibling_overlay

_ov = sibling_overlay()
SERIF, SANS = _ov.SERIF, _ov.SANS
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

from ui.counter import draw_scale_counter


def _lines(text: str, width_chars: int = 22) -> list[str]:
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


def _title_line(img: Image.Image, center_x: float, y: int, line: str, font, alpha: float, highlight: str) -> None:
    if highlight and highlight in line:
        pre, mid, post = line.partition(highlight)
    else:
        pre, mid, post = line, "", ""
    parts = ((pre, (255, 255, 255)), (mid, (255, 122, 40)), (post, (255, 255, 255)))
    total = sum(font.getlength(text) for text, _color in parts if text)
    x = center_x - total / 2
    for text, color in parts:
        if not text:
            continue
        _shadow_text(
            img,
            (x, y),
            text,
            font,
            fill=_alpha(color, 255 * alpha),
            anchor="lt",
            radius=10,
            opacity=int(170 * alpha),
        )
        x += font.getlength(text)


def _reveal(img: Image.Image, ep, fr) -> None:
    if fr.ending_alpha <= 0.02:
        return
    w, h = img.size
    lines = list(ep.raw.get("ending", {}).get("lines") or [])
    if not lines:
        return
    y = int(h * 0.46)
    highlight = lines[0]
    for index, line in enumerate(lines):
        size = 72 if index == 0 else 52
        font = _font(SANS, size)
        color = (255, 122, 40) if line == highlight else (255, 248, 242)
        _shadow_text(
            img,
            (w / 2, y),
            line,
            font,
            fill=_alpha(color, 255 * fr.ending_alpha),
            anchor="mt",
            radius=12,
            opacity=int(180 * fr.ending_alpha),
        )
        y += int(size * 1.15)


def compose_b(plate: Image.Image, ep, fr) -> Image.Image:
    img = plate.convert("RGBA")
    w, h = img.size
    title_bottom = int(h * 0.04)
    if fr.title_alpha > 0.02:
        font = _font(SERIF, 72)
        y = int(h * 0.038)
        highlight = ep.raw.get("title_highlight", "")
        for line in _lines(ep.raw["title"], 22):
            _title_line(img, w / 2, y, line, font, fr.title_alpha, highlight)
            y += int(font.size * 1.02)
        title_bottom = y + 8
    anchor_y = title_bottom if fr.title_alpha > 0.2 else int(h * 0.04)
    img, _box = draw_scale_counter(
        img,
        fr.label_primary,
        fr.primary,
        fr.primary_unit,
        previous=fr.primary_prev or None,
        roll=fr.roll,
        second_label=fr.label_secondary,
        second_number=fr.secondary,
        second_unit=fr.secondary_unit,
        second_previous=fr.secondary_prev or None,
        second_roll=fr.secondary_roll,
        align="center",
        anchor_y=anchor_y,
    )
    _reveal(img, ep, fr)
    return img.convert("RGB")
