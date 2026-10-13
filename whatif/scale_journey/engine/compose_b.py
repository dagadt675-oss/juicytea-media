"""Format B screen UI. Counter and type come from the shared whatif.ui."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from PIL import Image

from ui._load import sibling_overlay

_WORDS = Path(__file__).resolve().parents[1] / "episodes" / "penny_words.json"

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


@lru_cache(maxsize=1)
def _caption_tokens() -> tuple[dict, ...]:
    if not _WORDS.exists():
        return ()
    words = json.loads(_WORDS.read_text(encoding="utf-8")).get("words") or []
    tokens = []
    index = 0
    while index < len(words):
        word = words[index]
        cap = word.get("cap")
        if cap:
            tokens.append({"text": cap, "t0": float(word["t0"]), "t1": float(word.get("cap_t1", word["t1"]))})
            index += 1
            while index < len(words) and words[index].get("cap") == "":
                index += 1
            continue
        if cap == "":
            index += 1
            continue
        tokens.append({"text": str(word["w"]), "t0": float(word["t0"]), "t1": float(word["t1"])})
        index += 1
    return tuple(tokens)


def _karaoke(img: Image.Image, t: float) -> None:
    tokens = _caption_tokens()
    if not tokens:
        return
    active = 0
    for index, token in enumerate(tokens):
        if token["t0"] <= t:
            active = index
    window = tokens[max(0, active - 2) : active + 4]
    if not window:
        return
    w, h = img.size
    font = _font(SANS, 46)
    y = int(h * 0.68)
    parts = []
    for token in window:
        on = token["t0"] <= t < token["t1"] or (token is tokens[active] and t >= token["t0"])
        parts.append((token["text"] + " ", (255, 176, 64) if on else (255, 248, 242), on))
    # The active token stays highlighted through its span only.
    parts = []
    for token in window:
        on = token["t0"] <= t < token["t1"]
        parts.append((token["text"] + "  ", (255, 176, 64) if on else (255, 248, 242)))
    total = sum(font.getlength(text) for text, _color in parts)
    x = w / 2 - total / 2
    for text, color in parts:
        _shadow_text(img, (x, y), text, font, fill=_alpha(color, 255), anchor="lt", radius=8, opacity=160)
        x += font.getlength(text)


def _guy_ring(img: Image.Image, fr) -> None:
    if getattr(fr, "phase", "") != "guy":
        return
    from PIL import ImageDraw

    w, h = img.size
    draw = ImageDraw.Draw(img)
    cx, cy = w * 0.50, h * 0.46
    rx, ry = w * 0.09, w * 0.09
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=(220, 40, 40, 230), width=6)


def _ghost(img: Image.Image, fr) -> None:
    if fr.pill_alpha <= 0.02 or not fr.pill_title:
        return
    w, _h = img.size
    font = _font(SANS, 42)
    label = f"{fr.pill_title}   {fr.pill_sub}"
    _shadow_text(
        img,
        (w / 2, int(img.size[1] * 0.22)),
        label,
        font,
        fill=_alpha((210, 225, 255), int(210 * fr.pill_alpha)),
        anchor="mt",
        radius=8,
        opacity=int(120 * fr.pill_alpha),
    )


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
    anchor_y = title_bottom if fr.title_alpha > 0.02 else int(h * 0.04)
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
    _guy_ring(img, fr)
    _ghost(img, fr)
    _karaoke(img, float(fr.t))
    _reveal(img, ep, fr)
    return img.convert("RGB")
