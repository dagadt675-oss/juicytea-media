"""Format B screen UI. Counter and type come from the shared whatif.ui."""

from __future__ import annotations

from PIL import Image, ImageDraw

from ui._load import sibling_overlay

_ov = sibling_overlay()
SERIF, SANS = _ov.SERIF, _ov.SANS
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

from ui.counter import draw_scale_counter


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
            radius=8,
            opacity=int(150 * alpha),
        )
        x += font.getlength(text)


def _edge_note(img: Image.Image, fr) -> None:
    """The counter stays at the face-on 25 mph. This is the separate edge-on claim."""
    if fr.phase != "edge":
        return
    w, h = img.size
    fade = min(1.0, max(0.0, (fr.t - 27.15) / 0.4)) * (1.0 - min(1.0, max(0.0, (fr.t - 30.6) / 0.35)))
    if fade < 0.04:
        return
    a = int(230 * fade)
    label = _font(SANS, max(15, int(w * 0.018)))
    sub = _font(SANS, max(20, int(w * 0.028)))
    x = int(w * 0.055)
    y = int(h * 0.40)
    _shadow_text(img, (x, y), "EDGE-ON", label, fill=_alpha((255, 122, 40), a), anchor="lt", radius=3, opacity=int(120 * fade))
    _shadow_text(img, (x, y + int(h * 0.028)), "up to 65 mph", sub, fill=_alpha((255, 248, 242), a), anchor="lt", radius=3, opacity=int(120 * fade))


def _leader(img: Image.Image, fr) -> None:
    """Thin anchored callout, the same idea as the reference's Earth line."""
    if fr.phase != "liberty":
        return
    w, h = img.size
    fade = min(1.0, max(0.0, (fr.t - 20.2) / 0.45)) * (1.0 - min(1.0, max(0.0, (fr.t - 26.4) / 0.45)))
    if fade < 0.04:
        return
    y = int(h * 0.40)
    x0, x1 = int(w * 0.58), int(w * 0.86)
    a = int(230 * fade)
    draw = ImageDraw.Draw(img)
    draw.line((x0, y, x1 - 8, y), fill=(255, 248, 242, a), width=2)
    draw.ellipse((x1 - 7, y - 5, x1 + 3, y + 5), fill=(255, 122, 40, a))
    label = _font(SANS, max(15, int(w * 0.018)))
    sub = _font(SANS, max(18, int(w * 0.026)))
    _shadow_text(img, (x0, y - int(h * 0.042)), "STATUE OF LIBERTY", label, fill=_alpha((255, 122, 40), a), anchor="lt", radius=3, opacity=int(120 * fade))
    _shadow_text(img, (x0, y - int(h * 0.018)), "305 ft", sub, fill=_alpha((255, 248, 242), a), anchor="lt", radius=3, opacity=int(120 * fade))


def compose_b(plate: Image.Image, ep, fr) -> Image.Image:
    img = plate.convert("RGBA")
    w, h = img.size
    _leader(img, fr)
    _edge_note(img, fr)
    if fr.title_alpha > 0.02:
        font = _font(SERIF, max(40, int(w * 0.046)))
        y = int(h * 0.055)
        highlight = ep.raw.get("title_highlight", "")
        for line in _lines(ep.raw["title"], 24):
            _title_line(img, w / 2, y, line, font, fr.title_alpha, highlight)
            y += int(font.size * 1.08)
    shown = fr.primary_prev if fr.primary_prev and fr.roll < 0.5 else fr.primary
    metric = fr.metric or None
    if fr.primary_unit == "ft" and shown.replace(",", "").isdigit():
        metric = f"{int(round(int(shown.replace(',', '')) * 0.3048)):,} m"
    img, _box = draw_scale_counter(
        img,
        fr.label_primary,
        fr.primary,
        fr.primary_unit,
        metric=metric,
        previous=fr.primary_prev or None,
        roll=fr.roll,
        second_label=fr.label_secondary,
        second_number=fr.secondary,
        second_unit=fr.secondary_unit,
        second_previous=fr.secondary_prev or None,
        second_roll=fr.secondary_roll,
    )
    if fr.ending_alpha > 0.02:
        font = _font(SERIF, max(36, int(w * 0.044)))
        y = int(h * 0.062)
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
