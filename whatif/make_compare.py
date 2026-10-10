"""Stack the zenith opening reference over our day-1 frame, and blend them.

    python3 make_compare.py path/to/day1.png
Writes refs/compare_opening.jpg and refs/overlay_check.jpg.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REF = ROOT / "refs" / "zenith_opening.jpg"
OUT_COMPARE = ROOT / "refs" / "compare_opening.jpg"
OUT_OVERLAY = ROOT / "refs" / "overlay_check.jpg"
FONT = ROOT / "fonts" / "Inter-SemiBold.ttf"


def _fit(image: Image.Image, width: int) -> Image.Image:
    height = max(1, int(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _caption(image: Image.Image, text: str) -> Image.Image:
    bar = 36
    canvas = Image.new("RGB", (image.width, image.height + bar), (18, 18, 20))
    canvas.paste(image, (0, bar))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT), 22) if FONT.exists() else ImageFont.load_default()
    draw.text((12, 6), text, fill=(240, 240, 240), font=font)
    return canvas


def main():
    ours_path = Path(sys.argv[1])
    ref = Image.open(REF).convert("RGB")
    ours = Image.open(ours_path).convert("RGB")
    width = 720
    top = _caption(_fit(ref, width), "zenith")
    bottom = _caption(_fit(ours, width), "ours")
    gap = 10
    stacked = Image.new("RGB", (width, top.height + gap + bottom.height), (12, 12, 14))
    stacked.paste(top, (0, 0))
    stacked.paste(bottom, (0, top.height + gap))
    stacked.save(OUT_COMPARE, quality=90)

    matched = ours.resize(ref.size, Image.Resampling.LANCZOS)
    Image.blend(ref, matched, 0.5).save(OUT_OVERLAY, quality=90)
    print(OUT_COMPARE)
    print(OUT_OVERLAY)


if __name__ == "__main__":
    main()
