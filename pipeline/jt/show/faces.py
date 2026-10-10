"""Country faces sized to the landmass. Eyes are the thing you see on a phone.

An eye is about 20% of the country width: white, a dark rim, a large pupil.
Brows and a mouth change with the expression. `mouth` is 0..1 and flaps on
the gag word times. `squash` is the vertical scale, below 1 on a pop.
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
    return hump, hump * max(6.0, 0.04)


def draw_face(canvas, x: float, y: float, country_w: float, expr: str,
              mouth: float = 0.0, bob: float = 0.0, blink: float = 0.0,
              squash: float = 1.0, crown: float = 0.0):
    country_w = float(country_w)
    if country_w < 36:
        return
    eye_w = country_w * 0.20
    gap = eye_w * 0.42
    canvas.save()
    canvas.translate(x, y - bob * (eye_w / 40.0))
    sy = max(0.55, min(1.15, squash))
    sx = 1.0 + (1.0 - sy) * 0.65
    canvas.scale(sx, sy)
    _eyes(canvas, eye_w, gap, expr, blink)
    _brows(canvas, eye_w, gap, expr)
    _mouth(canvas, eye_w, expr, mouth)
    if crown > 0.05:
        _crown(canvas, eye_w, crown)
    canvas.restore()


def _eyes(canvas, eye_w: float, gap: float, expr: str, blink: float):
    aspect = {
        "smug": 0.50,
        "shocked": 1.05,
        "sad": 0.78,
        "worried": 0.88,
        "happy": 0.58,
    }.get(expr, 0.82)
    if blink > 0.65:
        aspect = 0.10
    eye_h = max(6.0, eye_w * aspect)
    white = skia.Paint(AntiAlias=True)
    white.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(2.0, eye_w * 0.07))
    rim.setColor(skia.ColorSetARGB(255, 22, 18, 24))
    pupil = skia.Paint(AntiAlias=True)
    pupil.setColor(skia.ColorSetARGB(255, 18, 16, 22))
    for sign in (-1.0, 1.0):
        cx = sign * (eye_w * 0.5 + gap * 0.5)
        rect = skia.Rect.MakeXYWH(cx - eye_w / 2, -eye_h / 2, eye_w, eye_h)
        canvas.drawOval(rect, white)
        canvas.drawOval(rect, rim)
        if blink <= 0.65:
            pr = eye_w * (0.28 if expr != "shocked" else 0.22)
            px = cx + eye_w * 0.06
            py = eye_h * 0.06
            canvas.drawCircle(px, py, pr, pupil)
            shine = skia.Paint(AntiAlias=True)
            shine.setColor(skia.ColorSetARGB(230, 255, 255, 255))
            canvas.drawCircle(px - pr * 0.35, py - pr * 0.35, pr * 0.28, shine)


def _brows(canvas, eye_w: float, gap: float, expr: str):
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(3.0, eye_w * 0.10))
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    rise = {"smug": 0.10, "shocked": -0.22, "sad": 0.16, "worried": -0.12, "happy": -0.06}.get(expr, 0.0)
    y = -eye_w * (0.62 + max(0.0, -rise))
    half = eye_w * 0.46
    for sign in (-1.0, 1.0):
        cx = sign * (eye_w * 0.5 + gap * 0.5)
        tilt = sign * eye_w * rise
        canvas.drawLine(cx - half, y + tilt, cx + half, y - tilt * 0.4, pen)


def _mouth(canvas, eye_w: float, expr: str, mouth: float):
    open_amt = max(0.0, min(1.0, mouth))
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(3.0, eye_w * 0.09))
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    ink = skia.Paint(AntiAlias=True)
    ink.setColor(skia.ColorSetARGB(255, 28, 16, 22))
    y = eye_w * 0.78
    mw = eye_w * 1.15
    if expr == "shocked":
        ry = eye_w * (0.28 + 0.45 * open_amt)
        canvas.drawOval(skia.Rect.MakeXYWH(-mw * 0.38, y, mw * 0.76, ry), ink)
        rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(2.0, eye_w * 0.06))
        rim.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        canvas.drawOval(skia.Rect.MakeXYWH(-mw * 0.38, y, mw * 0.76, ry), rim)
        return
    if expr == "sad":
        canvas.drawArc(skia.Rect.MakeXYWH(-mw / 2, y, mw, eye_w * 0.55), 200, 140, False, pen)
        return
    if expr == "worried":
        canvas.drawArc(skia.Rect.MakeXYWH(-mw * 0.42, y, mw * 0.84, eye_w * 0.42), 200, 140, False, pen)
        return
    # smug / happy: a smile that opens on the gag
    canvas.drawArc(
        skia.Rect.MakeXYWH(-mw / 2, y - eye_w * 0.05, mw, eye_w * (0.45 + 0.35 * open_amt)),
        15, 150, False, pen,
    )
    if open_amt > 0.2:
        canvas.drawOval(
            skia.Rect.MakeXYWH(-mw * 0.22, y + eye_w * 0.12, mw * 0.44, eye_w * 0.28 * open_amt),
            ink,
        )


def _crown(canvas, eye_w: float, pop: float):
    k = 0.7 + 0.3 * min(1.0, pop)
    s = eye_w * 0.55 * k
    path = skia.Path()
    y0 = -eye_w * 1.15
    path.moveTo(-s, y0)
    path.lineTo(-s, y0 - s * 0.7)
    path.lineTo(-s * 0.35, y0 - s * 0.28)
    path.lineTo(0, y0 - s)
    path.lineTo(s * 0.35, y0 - s * 0.28)
    path.lineTo(s, y0 - s * 0.7)
    path.lineTo(s, y0)
    path.close()
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, 255, 204, 48))
    canvas.drawPath(path, paint)
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(2.0, eye_w * 0.04))
    pen.setColor(skia.ColorSetARGB(255, 90, 60, 10))
    canvas.drawPath(path, pen)
