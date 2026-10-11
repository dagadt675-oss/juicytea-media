"""Format B screen UI. Counter and type come from the shared whatif.ui."""

from __future__ import annotations

from PIL import Image, ImageDraw

from ui._load import sibling_overlay

_ov = sibling_overlay()
SERIF, SANS = _ov.SERIF, _ov.SANS
_alpha, _font, _shadow_text = _ov._alpha, _ov._font, _ov._shadow_text

from ui.counter import CAPTION_Y0, draw_scale_counter
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


def _streaks(img: Image.Image, fr) -> None:
    if fr.phase not in ("fall", "floors", "drag", "liberty", "edge"):
        return
    draw = ImageDraw.Draw(img)
    w, h = img.size
    band = int(CAPTION_Y0 * h)
    for i in range(7):
        x = int(w * (0.62 + i * 0.05))
        span = 70 + (i % 3) * 30
        shift = int((fr.t * 420 + i * 90) % (band * 0.45))
        y0 = int(h * 0.16) + shift
        y1 = min(band - 8, y0 + span)
        if y1 <= y0:
            continue
        draw.line((x, y0, x, y1), fill=(255, 255, 255, 54), width=2)


def _liberty_ghost(img: Image.Image, fr) -> None:
    """Screen silhouette. The follow camera is too close to frame a 305 ft statue."""
    if fr.phase != "liberty":
        return
    w, h = img.size
    liberty_z = 305.0 * 0.3048
    dz = liberty_z - fr.penny[2]
    y = int(h * 0.50 - dz * 3.4)
    y = max(int(h * 0.30), min(int(h * 0.56), y))
    x = int(w * 0.80)
    fade = 1.0 - min(1.0, abs(dz) / 80.0)
    fade *= min(1.0, max(0.0, (fr.t - 20.0) / 0.6))
    if fade < 0.05:
        return
    a = int(170 * fade)
    draw = ImageDraw.Draw(img)
    green = (176, 214, 168, a)
    draw.rectangle((x - 28, y + 70, x + 28, y + 108), fill=green)
    draw.polygon([(x - 34, y + 72), (x + 34, y + 72), (x + 18, y - 10), (x - 18, y - 10)], fill=green)
    draw.ellipse((x - 14, y - 36, x + 14, y - 8), fill=green)
    draw.rectangle((x + 8, y - 78, x + 16, y - 20), fill=green)
    draw.ellipse((x + 4, y - 92, x + 22, y - 74), fill=green)


def compose_b(plate: Image.Image, ep, fr) -> Image.Image:
    img = plate.convert("RGBA")
    w, h = img.size
    _streaks(img, fr)
    _liberty_ghost(img, fr)
    if fr.title_alpha > 0.02:
        font = _font(SERIF, max(40, int(w * 0.046)))
        y = int(h * 0.055)
        for line in _lines(ep.raw["title"], 24):
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
    img, _box = draw_scale_counter(
        img,
        fr.label_primary,
        fr.primary,
        fr.primary_unit,
        metric=fr.metric or None,
        previous=fr.primary_prev or None,
        roll=fr.roll,
        second_label=fr.label_secondary,
        second_number=fr.secondary,
        second_unit=fr.secondary_unit,
        second_previous=fr.secondary_prev or None,
        second_roll=fr.secondary_roll,
    )
    if fr.pill_alpha > 0.02 and fr.pill_title:
        img, _pill = draw_pill(
            img,
            fr.pill_title,
            fr.pill_sub,
            None,
            (w * 0.055, h * 0.42),
            fr.pill_alpha,
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
