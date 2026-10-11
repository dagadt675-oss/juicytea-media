"""Procedural textures baked once per render. No third-party art."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def write_all(dest: Path) -> dict[str, str]:
    dest.mkdir(parents=True, exist_ok=True)
    paths = {
        "facade": dest / "facade.png",
        "bokeh": dest / "bokeh_warm.png",
        "stars": dest / "stars.png",
    }
    if not paths["facade"].exists():
        _facade(paths["facade"])
    if not paths["bokeh"].exists():
        _bokeh(paths["bokeh"])
    if not paths["stars"].exists():
        _stars(paths["stars"])
    return {k: str(v) for k, v in paths.items()}


def _facade(path: Path) -> None:
    rng = random.Random(11)
    img = Image.new("RGB", (512, 1024), (62, 66, 78))
    draw = ImageDraw.Draw(img)
    # Subtle floor bands so the massing reads even when windows are dark.
    for y in range(0, 1024, 64):
        shade = 58 + (y // 64) % 2 * 8
        draw.rectangle((0, y, 512, y + 64), fill=(shade, shade + 2, shade + 10))
    for row in range(16):
        for col in range(8):
            x = 18 + col * 62
            y = 16 + row * 64
            roll = rng.random()
            if roll > 0.72:
                color = (255, 186, 92)
            elif roll > 0.55:
                color = (255, 214, 150)
            elif roll > 0.38:
                color = (126, 168, 196)
            else:
                color = (18, 22, 32)
            draw.rounded_rectangle((x, y, x + 36, y + 44), radius=2, fill=color)
            if color[0] > 200:
                draw.rectangle((x + 4, y + 6, x + 16, y + 20), fill=(255, 232, 180))
    img.save(path)


def _bokeh(path: Path) -> None:
    rng = random.Random(3)
    img = Image.new("RGB", (720, 1280), (28, 18, 16))
    draw = ImageDraw.Draw(img)
    for i in range(18):
        x = rng.randint(-40, 760)
        y = rng.randint(80, 1100)
        r = rng.randint(30, 120)
        color = rng.choice([(255, 176, 90), (255, 214, 150), (120, 150, 180), (255, 140, 70)])
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
    img = img.filter(ImageFilter.GaussianBlur(radius=22))
    # Warm sky wash on top.
    wash = Image.new("RGB", img.size, (255, 168, 110))
    img = Image.blend(img, wash, 0.18)
    img.save(path, quality=90)


def _stars(path: Path) -> None:
    rng = random.Random(19)
    img = Image.new("RGB", (2048, 1024), (0, 0, 0))
    pix = img.load()
    for _ in range(900):
        x = rng.randrange(2048)
        y = rng.randrange(1024)
        v = rng.choice((180, 210, 255, 255, 140))
        pix[x, y] = (v, v, min(255, v + 15))
    for _ in range(40):
        x = rng.randrange(2, 2046)
        y = rng.randrange(2, 1022)
        pix[x, y] = (255, 244, 230)
        pix[x + 1, y] = (200, 200, 210)
        pix[x, y + 1] = (200, 200, 210)
    img.save(path, quality=95)
