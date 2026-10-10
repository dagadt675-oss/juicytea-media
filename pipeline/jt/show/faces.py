"""Country faces. White eyes, black pupils, a few mouths. No portraits.

`mouth` is 0..1 and is driven by the gag word times. `bob` is a one-syllable
rise in pixels, also locked to those words.
"""

from __future__ import annotations

import math

import skia


def gag_pose(t: float, t0: float, t1: float, syllables: int = 2) -> tuple[float, float]:
    """Mouth open and upward bob. Zero outside the gag. One hump per syllable."""
    if t < t0 or t > t1 or t1 <= t0:
        return 0.0, 0.0
    x = (t - t0) / (t1 - t0)
    phase = (x * syllables) % 1.0
    hump = math.sin(math.pi * phase)
    return hump, hump * 9.0


def draw_face(canvas, x: float, y: float, size: float, expr: str, mouth: float = 0.0,
              bob: float = 0.0, blink: float = 0.0, crown: float = 0.0):
    if size < 16:
        return
    y -= bob
    s = size / 78.0
    canvas.save()
    canvas.translate(x, y)

    def eye(cx, cy, open_h):
        if blink > 0.65:
            pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2 * s)
            pen.setColor(skia.ColorSetARGB(255, 255, 255, 255))
            canvas.drawLine(cx - 11 * s, cy, cx + 11 * s, cy, pen)
            return
        white = skia.Paint(AntiAlias=True)
        white.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        h = max(3.0, open_h) * s
        canvas.drawOval(skia.Rect.MakeXYWH(cx - 13 * s, cy - h * 0.5, 26 * s, h), white)
        pupil = skia.Paint(AntiAlias=True)
        pupil.setColor(skia.ColorSetARGB(255, 16, 16, 20))
        canvas.drawCircle(cx + 1.5 * s, cy + 1.0 * s, 5.2 * s, pupil)

    # Brows and eye opening depend on the expression.
    eye_h = 22.0
    brow = 0.0
    if expr == "smug":
        eye_h = 12.0
        brow = 4.0
    elif expr == "shocked":
        eye_h = 28.0
        brow = -6.0
    elif expr == "worried":
        eye_h = 20.0
        brow = -3.0
    elif expr == "sad":
        eye_h = 16.0
        brow = 2.0
    elif expr == "happy":
        eye_h = 14.0
        brow = -2.0
    elif expr == "angry":
        eye_h = 16.0
        brow = 6.0

    eye(-18 * s, -6 * s, eye_h)
    eye(18 * s, -6 * s, eye_h)

    brow_paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.4 * s)
    brow_paint.setStrokeCap(skia.Paint.kRound_Cap)
    brow_paint.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    canvas.drawLine(-30 * s, (-22 + brow) * s, -8 * s, (-18 - brow * 0.3) * s, brow_paint)
    canvas.drawLine(8 * s, (-18 - brow * 0.3) * s, 30 * s, (-22 + brow) * s, brow_paint)

    _mouth(canvas, s, expr, mouth)

    if crown > 0.05:
        _crown(canvas, s, crown)
    canvas.restore()


def _mouth(canvas, s: float, expr: str, mouth: float):
    ink = skia.Paint(AntiAlias=True)
    ink.setColor(skia.ColorSetARGB(255, 20, 16, 16))
    white = skia.Paint(AntiAlias=True)
    white.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.3 * s)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    open_amt = max(0.0, min(1.0, mouth))
    if expr == "shocked":
        ry = (8 + 14 * open_amt) * s
        canvas.drawOval(skia.Rect.MakeXYWH(-12 * s, 10 * s, 24 * s, ry), ink)
        canvas.drawOval(skia.Rect.MakeXYWH(-7 * s, 13 * s, 14 * s, max(4 * s, ry * 0.45)), white)
        return
    if expr == "sad":
        canvas.drawArc(skia.Rect.MakeXYWH(-16 * s, 16 * s, 32 * s, 18 * s), 200, 140, False, pen)
        return
    if expr == "worried":
        canvas.drawArc(skia.Rect.MakeXYWH(-14 * s, 14 * s, 28 * s, 16 * s), 200, 140, False, pen)
        return
    if expr in ("happy", "smug"):
        # Smirk / smile. Mouth opens downward on the gag.
        canvas.drawArc(skia.Rect.MakeXYWH(-16 * s, 8 * s, 32 * s, 18 * s + 10 * open_amt * s), 20, 140, False, pen)
        if open_amt > 0.25:
            canvas.drawOval(skia.Rect.MakeXYWH(-8 * s, 16 * s, 16 * s, 8 * open_amt * s), ink)
        return
    canvas.drawLine(-12 * s, 16 * s, 12 * s, 16 * s, pen)


def _crown(canvas, s: float, pop: float):
    k = 0.65 + 0.35 * min(1.0, pop)
    path = skia.Path()
    path.moveTo(-18 * s, -30 * s * k)
    path.lineTo(-18 * s, -42 * s * k)
    path.lineTo(-8 * s, -34 * s * k)
    path.lineTo(0, -48 * s * k)
    path.lineTo(8 * s, -34 * s * k)
    path.lineTo(18 * s, -42 * s * k)
    path.lineTo(18 * s, -30 * s * k)
    path.close()
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 244, 196, 46))
    canvas.drawPath(path, paint)
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6 * s)
    pen.setColor(skia.ColorSetARGB(255, 90, 60, 10))
    canvas.drawPath(path, pen)
