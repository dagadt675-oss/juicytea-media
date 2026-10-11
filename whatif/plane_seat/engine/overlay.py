"""Karaoke captions and stat pills. Drawn after the beauty pass.

Captions sit in x 90–900, y 1120–1420. Pills sit in y 300–1050.
Numbers use the words.json cap field. TIME stays in caps.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .clock import (
    CAPTION_X0,
    CAPTION_X1,
    CAPTION_Y0,
    CAPTION_Y1,
    HEIGHT,
    PILL_Y0,
    PILL_Y1,
    WIDTH,
    caption_lines,
)
from .flight import pose_at

FONT_PATH = Path(__file__).resolve().parents[2] / "scale_journey" / "assets" / "fonts" / "Anton-Regular.ttf"

TONES = {
    "white": (255, 255, 255),
    "yellow": (255, 214, 32),
    "green": (55, 235, 130),
    "amber": (255, 164, 28),
    "red": (255, 58, 46),
    "bright": (150, 255, 80),
}

_WISP = None
_FLARE = None


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def _smooth(a: float, b: float, x: float) -> float:
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    u = (x - a) / (b - a)
    return u * u * (3.0 - 2.0 * u)


def _wisps() -> Image.Image:
    global _WISP
    if _WISP is not None:
        return _WISP
    img = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    rng = random.Random(11)
    for _ in range(26):
        x = rng.randint(-200, WIDTH - 100)
        y = rng.randint(-80, HEIGHT - 200)
        w = rng.randint(360, 980)
        h = rng.randint(36, 160)
        draw.ellipse((x, y, x + w, y + h), fill=rng.randint(90, 200))
    _WISP = img.filter(ImageFilter.GaussianBlur(22))
    return _WISP


def _flare() -> Image.Image:
    global _FLARE
    if _FLARE is not None:
        return _FLARE
    size = 720
    img = Image.new("L", (size, size), 0)
    pix = img.load()
    c = size / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            if d < 1:
                pix[x, y] = int(255 * (1 - d) ** 2.2)
    _FLARE = img
    return _FLARE


def _line_layout(tokens: list[dict], font: ImageFont.FreeTypeFont, stroke: int):
    space = max(8, int(font.size * 0.22))
    pieces = []
    x = 0
    for tok in tokens:
        gap = 2 if tok["text"] == "%" else (space if pieces else 0)
        bbox = font.getbbox(tok["text"], stroke_width=stroke)
        width = bbox[2] - bbox[0]
        pieces.append({"x": x + gap, "tok": tok, "bbox": bbox, "width": width})
        x += gap + width
    return pieces, x


def caption_layout(t: float) -> dict | None:
    lines = caption_lines(t)
    if not lines:
        return None
    stroke = 8
    max_w = (CAPTION_X1 - CAPTION_X0) - stroke * 2
    max_h = (CAPTION_Y1 - CAPTION_Y0) - stroke * 2
    chosen = None
    for size in range(96, 70, -2):
        font = _font(size)
        built = []
        widest = 0
        for line in lines:
            pieces, width = _line_layout(line, font, stroke)
            built.append(pieces)
            widest = max(widest, width)
        step = int(size * 1.02)
        block_h = size + step * (len(lines) - 1)
        if widest <= max_w and block_h <= max_h:
            chosen = (font, built, widest, block_h, step, size)
            break
    if chosen is None:
        size = 72
        font = _font(size)
        built = []
        widest = 0
        for line in lines:
            pieces, width = _line_layout(line, font, stroke)
            built.append(pieces)
            widest = max(widest, width)
        step = int(size * 1.02)
        block_h = size + step * (len(lines) - 1)
        chosen = (font, built, widest, block_h, step, size)
    font, built, widest, block_h, step, size = chosen
    left = (CAPTION_X0 + CAPTION_X1) / 2 - widest / 2
    top = (CAPTION_Y0 + CAPTION_Y1) / 2 - block_h / 2
    placed = []
    for i, pieces in enumerate(built):
        row = []
        for piece in pieces:
            bb = piece["bbox"]
            x = left + piece["x"] - bb[0]
            y = top + i * step - bb[1]
            row.append({**piece, "draw_x": x, "draw_y": y})
        placed.append(row)
    return {
        "font": font,
        "lines": placed,
        "stroke": stroke,
        "box": (left - stroke, top - stroke, left + widest + stroke, top + block_h + stroke),
        "size": size,
    }


def _accent(name: str) -> tuple[int, int, int]:
    return {
        "amber": TONES["amber"],
        "green": TONES["green"],
        "red": TONES["red"],
        "bright": TONES["bright"],
        "gold": (255, 196, 90),
    }[name]


def pill_specs(pose: dict) -> list[dict]:
    """Stat pills. Copy is the label, not the karaoke line."""
    items = []
    card = pose["show_card"]
    if card > 0.02:
        items.append({"text": "TIME  ·  FAA RECORDS", "sub": "17 CRASHES", "accent": "gold", "alpha": card, "y": 390, "size": 52})
    y = 400
    for flag, text, accent in (
        ("show_38", "FRONT   38% DIED", "amber"),
        ("show_39", "MIDDLE   39%", "amber"),
        ("show_32", "BACK   32%", "green"),
    ):
        alpha = pose[flag]
        if alpha > 0.02:
            items.append({"text": text, "sub": "", "accent": accent, "alpha": alpha, "y": y, "size": 48})
            y += 118
    if pose["show_44"] > 0.02:
        items.append({"text": "WORST  ·  AISLE  ·  MID-CABIN", "sub": "44%", "accent": "red", "alpha": pose["show_44"], "y": 430, "size": 42, "big": 120})
    if pose["show_28"] > 0.02:
        items.append({"text": "BEST  ·  MIDDLE SEAT  ·  BACK", "sub": "28%", "accent": "bright", "alpha": pose["show_28"], "y": 430, "size": 42, "big": 120})
    return items


def _draw_pill(img: Image.Image, spec: dict) -> tuple[int, int, int, int]:
    alpha = spec["alpha"]
    font = _font(spec["size"])
    draw = ImageDraw.Draw(img)
    text = spec["text"]
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    big_h = 0
    big_w = 0
    big_font = None
    if spec.get("big") and spec.get("sub"):
        big_font = _font(spec["big"])
        bb = draw.textbbox((0, 0), spec["sub"], font=big_font)
        big_w, big_h = bb[2] - bb[0], bb[3] - bb[1]
    width = max(tw, big_w) + 72
    height = th + (big_h + 16 if big_h else 0) + 36
    x0 = (WIDTH - width) / 2
    y0 = spec["y"]
    x1, y1 = x0 + width, y0 + height
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pen = ImageDraw.Draw(layer)
    fill_a = int(185 * alpha)
    pen.rounded_rectangle((x0, y0, x1, y1), radius=22, fill=(12, 10, 14, fill_a))
    accent = _accent(spec["accent"])
    pen.rectangle((x0, y0, x0 + 12, y1), fill=(*accent, int(255 * alpha)))
    tx = x0 + (width - tw) / 2
    ty = y0 + 16
    pen.text((tx, ty), text, font=font, fill=(255, 255, 255, int(255 * alpha)))
    if big_font is not None:
        pen.text(
            (x0 + (width - big_w) / 2, ty + th + 8),
            spec["sub"],
            font=big_font,
            fill=(*accent, int(255 * alpha)),
        )
    elif spec.get("sub"):
        sub_font = _font(36)
        sb = draw.textbbox((0, 0), spec["sub"], font=sub_font)
        sw = sb[2] - sb[0]
        pen.text((x0 + (width - sw) / 2, ty + th + 4), spec["sub"], font=sub_font, fill=(*accent, int(240 * alpha)))
    img.alpha_composite(layer)
    return (int(x0), int(y0), int(x1), int(y1))


def _draw_x(img: Image.Image, alpha: float) -> None:
    if alpha <= 0.02:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pen = ImageDraw.Draw(layer)
    cx, cy, r = 540, 760, 132
    color = (255, 54, 42, int(235 * alpha))
    pen.line((cx - r, cy - r, cx + r, cy + r), fill=color, width=26)
    pen.line((cx + r, cy - r, cx - r, cy + r), fill=color, width=26)
    img.alpha_composite(layer)


def _screen(base: Image.Image, color: tuple[int, int, int], mask: Image.Image) -> None:
    tint = Image.new("RGBA", base.size, (*color, 0))
    tint.putalpha(mask)
    # Normal composite. Wisps are bright; a soft light is enough at 1-sample plates.
    base.alpha_composite(tint)


def composite(base: Image.Image, t: float, atmosphere: bool = True, pills: bool = True) -> Image.Image:
    pose = pose_at(t)
    img = base.convert("RGBA")
    if img.size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    flare = pose["flare"] if atmosphere else 0.0
    if flare > 0.04:
        mask = _flare().resize((720, 720))
        mask = mask.point(lambda p, f=flare: int(p * min(1.0, f) * 0.85))
        layer = Image.new("L", img.size, 0)
        layer.paste(mask, (520, -40))
        _screen(img, (255, 214, 150), layer)

    cover = pose["cloud"] if atmosphere else 0.0
    if cover > 0.02:
        wisp = _wisps()
        shift = int((t * 70) % HEIGHT)
        rolled = Image.new("L", (WIDTH, HEIGHT))
        rolled.paste(wisp, (0, -shift))
        rolled.paste(wisp, (0, HEIGHT - shift))
        alpha = rolled.point(lambda p, c=cover: int(p * c * 0.55))
        _screen(img, (255, 246, 230), alpha)
        white = _smooth(0.62, 0.97, cover)
        if white > 0.01:
            veil = Image.new("RGBA", img.size, (255, 236, 206, int(235 * white)))
            img.alpha_composite(veil)

    if pills:
        for spec in pill_specs(pose):
            _draw_pill(img, spec)
    _draw_x(img, pose["show_x"])

    layout = caption_layout(t)
    if layout is not None:
        plate = layout["box"]
        pad = 18
        rect = (
            max(CAPTION_X0, plate[0] - pad),
            max(CAPTION_Y0, plate[1] - pad),
            min(CAPTION_X1, plate[2] + pad),
            min(CAPTION_Y1, plate[3] + pad),
        )
        plate_a = int(50 + 170 * _smooth(0.15, 0.85, cover))
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(rect, radius=18, fill=(8, 8, 12, plate_a))
        img.alpha_composite(layer)
        pen = ImageDraw.Draw(img)
        for line in layout["lines"]:
            for piece in line:
                tok = piece["tok"]
                tone = tok["tone"]
                if tok["active"] and tone == "green":
                    fill = (170, 255, 190, 255)
                else:
                    rgb = TONES[tone]
                    fill = (*rgb, 255)
                pen.text(
                    (piece["draw_x"], piece["draw_y"]),
                    tok["text"],
                    font=layout["font"],
                    fill=fill,
                    stroke_width=layout["stroke"],
                    stroke_fill=(0, 0, 0, 255),
                )
    return img.convert("RGB")


def measure_safe(t: float) -> dict:
    """Boxes used by the unit test. Independent of a beauty plate."""
    layout = caption_layout(t)
    pose = pose_at(t)
    pills = []
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    for spec in pill_specs(pose):
        pills.append(_draw_pill(img, spec))
    return {"caption": None if layout is None else layout["box"], "pills": pills, "size": None if layout is None else layout["size"]}
