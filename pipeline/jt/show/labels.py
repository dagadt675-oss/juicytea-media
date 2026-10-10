"""Pills and big numbers. Text stays out of the caption band.

The band is y 0.64–0.72. Captions are burned later, so this layer never
draws a glyph there. Square miles are the primary unit; square kilometres
are the line under them, at least 36px.
"""

from __future__ import annotations

from pathlib import Path

import skia

FONT_BLACK = Path(__file__).resolve().parents[2] / "fonts" / "Montserrat-Black.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BAND = (0.64, 0.72)
KM2_PER_SQMI = 2.58998811

_FACES = None


def _face(path: str):
    if Path(path).exists():
        tf = skia.Typeface.MakeFromFile(str(path))
        if tf is not None:
            return tf
    tf = skia.Typeface.MakeFromFile(FONT_FALLBACK)
    if tf is None:
        raise RuntimeError("no usable font")
    return tf


def faces():
    global _FACES
    if _FACES is None:
        _FACES = {"black": _face(str(FONT_BLACK)), "bold": _face(FONT_BOLD)}
    return _FACES


# Text lives between the top 12% and the bottom 20%, and out of the
# caption band (captions are burned later).
SAFE_TOP = 0.12
SAFE_BOT = 0.80


class Hud:
    """Records every text box so QA can prove the safe zone and the caption band."""

    def __init__(self, canvas, w: int, h: int):
        self.canvas = canvas
        self.w = w
        self.h = h
        self.boxes: list[tuple[float, float, float, float]] = []
        self.caps: list[tuple[str, float]] = []

    def band_hits(self) -> int:
        y0, y1 = BAND[0] * self.h, BAND[1] * self.h
        n = 0
        for l, t, r, b in self.boxes:
            if b > y0 and t < y1 and r > 0 and l < self.w:
                n += 1
        return n

    def safe_hits(self) -> int:
        top = SAFE_TOP * self.h
        bot = SAFE_BOT * self.h
        n = 0
        for l, t, r, b in self.boxes:
            if t < top - 0.5 or b > bot + 0.5:
                n += 1
        return n

    def _blocked(self, cy: float, height: float) -> bool:
        top = cy - height / 2
        bot = cy + height / 2
        if top < SAFE_TOP * self.h or bot > SAFE_BOT * self.h:
            return True
        y0, y1 = BAND[0] * self.h, BAND[1] * self.h
        return bot > y0 and top < y1

    def dodge(self, cy: float, height: float) -> float:
        if not self._blocked(cy, height):
            return cy
        h = self.h
        slots = [
            SAFE_TOP * h + height / 2 + 6,
            BAND[0] * h - height / 2 - 8,
            BAND[1] * h + height / 2 + 8,
            SAFE_BOT * h - height / 2 - 6,
        ]
        best = None
        best_d = 1e9
        for slot in slots:
            if self._blocked(slot, height):
                continue
            d = abs(slot - cy)
            if d < best_d:
                best_d = d
                best = slot
        return cy if best is None else best


def _font(which: str, px: float) -> skia.Font:
    return skia.Font(faces()[which], max(10.0, px))


def pill(hud: Hud, text: str, cx: float, cy: float, fill, ink=(255, 255, 255),
         size: float = 58, pop: float = 1.0, glow=None, kind: str = "") -> tuple[float, float, float, float] | None:
    if not text or pop <= 0.04:
        return None
    # Stay near full size so a spring-in doesn't drop the cap height off the spec.
    pop = max(0.90, min(1.08, pop))
    font = _font("black", size * pop)
    width = font.measureText(text)
    metrics = font.getMetrics()
    pad_x, pad_y = 22 * pop, 12 * pop
    tw = width + pad_x * 2
    th = (metrics.fDescent - metrics.fAscent) + pad_y * 2
    cy = hud.dodge(cy, th)
    left = cx - tw / 2
    top = cy - th / 2
    # Keep it on the 9:16 frame.
    left = min(max(16, left), hud.w - tw - 16)
    top = min(max(16, top), hud.h - th - 16)
    rect = skia.Rect.MakeXYWH(left, top, tw, th)
    radius = th / 2
    if glow is not None:
        g = skia.Paint(AntiAlias=True)
        g.setColor(skia.ColorSetARGB(90, glow[0], glow[1], glow[2]))
        g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
        hud.canvas.drawRRect(skia.RRect.MakeRectXY(rect.makeOutset(4, 4), radius, radius), g)
    body = skia.Paint(AntiAlias=True)
    body.setColor(skia.ColorSetARGB(235, fill[0], fill[1], fill[2]))
    hud.canvas.drawRRect(skia.RRect.MakeRectXY(rect, radius, radius), body)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, ink[0], ink[1], ink[2]))
    baseline = top + pad_y - metrics.fAscent
    hud.canvas.drawString(text, left + pad_x, baseline, font, paint)
    box = (left, top, left + tw, top + th)
    hud.boxes.append(box)
    hud.caps.append((kind or text, 0.70 * size * pop))
    return box


def big_number(hud: Hud, text: str, cx: float, cy: float, size: float = 96, pop: float = 1.0):
    """Yellow number on a dark pill. Yellow is the number colour."""
    return pill(hud, text, cx, cy, (18, 16, 14), ink=(255, 226, 64), size=size, pop=pop, glow=(255, 210, 40))


def area_stack(hud: Hud, title: str, km2: float, cx: float, cy: float, pop: float = 1.0):
    """Primary square miles, secondary km² at a 36px cap (font size 54)."""
    mi = km2 / KM2_PER_SQMI / 1e6
    km = km2 / 1e6
    primary = f"{mi:.2f}M SQ MI"
    secondary = f"{km:.2f}M KM²"
    pill(hud, title, cx, cy - 118, (244, 244, 246), ink=(16, 16, 20), size=62, pop=pop, kind="area-title")
    pill(hud, primary, cx, cy, (255, 214, 48), ink=(22, 16, 8), size=84, pop=pop, kind="sqmi")
    pill(hud, secondary, cx, cy + 100, (28, 36, 48), ink=(236, 240, 244), size=54, pop=pop, kind="km2")


def strike(canvas, rect, pop: float):
    if rect is None or pop <= 0:
        return
    l, t, r, b = rect
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8 * pop)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(int(230 * pop), 226, 40, 64))
    canvas.drawLine(l + 8, t + 8, r - 8, b - 8, pen)
    canvas.drawLine(l + 8, b - 8, r - 8, t + 8, pen)
