"""Small props shared by map shows: dust, sparkle, equal bars, a dashed path."""

from __future__ import annotations

import math

import numpy as np
import skia

from jt.project import project_one
from jt.show.basemap import view_for


def dust(canvas, x: float, y: float, age: float):
    if age < 0 or age > 0.55:
        return
    u = age / 0.55
    paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4 * (1 - u))
    paint.setColor(skia.ColorSetARGB(int(160 * (1 - u)), 210, 196, 170))
    rx = 18 + 90 * u
    ry = 8 + 28 * u
    canvas.drawOval(skia.Rect.MakeXYWH(x - rx, y - ry * 0.3, rx * 2, ry * 2), paint)


def sparkles(canvas, x: float, y: float, t: float, n: int = 5):
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(230, 255, 230, 90))
    for i in range(n):
        ang = i * 1.27 + t * 0.4
        rad = 18 + (i % 3) * 14
        px = x + math.cos(ang) * rad
        py = y + math.sin(ang) * rad * 0.6
        _star(canvas, px, py, 7 + (i % 2) * 3, paint)


def _star(canvas, x, y, r, paint):
    path = skia.Path()
    path.moveTo(x, y - r)
    path.lineTo(x + r * 0.28, y - r * 0.28)
    path.lineTo(x + r, y)
    path.lineTo(x + r * 0.28, y + r * 0.28)
    path.lineTo(x, y + r)
    path.lineTo(x - r * 0.28, y + r * 0.28)
    path.lineTo(x - r, y)
    path.lineTo(x - r * 0.28, y - r * 0.28)
    path.close()
    canvas.drawPath(path, paint)


def equal_brackets(canvas, left, right, pop: float = 1.0):
    """Two brackets of one shared length, and an equals sign in the gap.

    `left` and `right` are (x0, y0, x1, y1) boxes. The mark sells 'same size'
    even when the landmasses are not the same shape.
    """
    if pop < 0.08 or left is None or right is None:
        return
    if left[0] > right[0]:
        left, right = right, left
    length = min(left[3] - left[1], right[3] - right[1]) * 0.62 * pop
    if length < 24:
        return
    paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8)
    paint.setStrokeCap(skia.Paint.kRound_Cap)
    paint.setColor(skia.ColorSetARGB(int(240 * min(1.0, pop)), 255, 255, 255))

    def bracket(x, cy, arm):
        y0, y1 = cy - length / 2, cy + length / 2
        canvas.drawLine(x, y0, x, y1, paint)
        canvas.drawLine(x, y0, x + arm, y0, paint)
        canvas.drawLine(x, y1, x + arm, y1, paint)

    bracket(left[2] + 16, (left[1] + left[3]) / 2, -28)
    bracket(right[0] - 16, (right[1] + right[3]) / 2, 28)
    mx = (left[2] + right[0]) / 2
    my = ((left[1] + left[3]) + (right[1] + right[3])) / 4
    bar = 46
    canvas.drawLine(mx - bar, my - 16, mx + bar, my - 16, paint)
    canvas.drawLine(mx - bar, my + 16, mx + bar, my + 16, paint)


def equal_bars(canvas, x0: float, x1: float, y: float, length: float, pop: float):
    if pop <= 0.02:
        return
    paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8)
    paint.setStrokeCap(skia.Paint.kRound_Cap)
    paint.setColor(skia.ColorSetARGB(int(230 * pop), 244, 244, 246))
    for x in (x0, x1):
        canvas.drawLine(x - length / 2, y, x + length / 2, y, paint)


def dashed_path(canvas, cam, lonlat, w: int, h: int, grow: float):
    if grow <= 0.02 or cam.proj != "merc":
        return
    view = view_for(cam, w, h)
    pts = []
    for lon, lat in lonlat:
        p = project_one(float(lon), float(lat), view)
        if p is None:
            if len(pts) >= 2:
                break
            continue
        pts.append(p)
    if len(pts) < 2:
        return
    # Keep the grown fraction of the polyline.
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    target = total * min(1.0, grow)
    kept = [pts[0]]
    acc = 0.0
    for i, length in enumerate(seg):
        if acc + length >= target:
            t = 0.0 if length <= 1e-9 else (target - acc) / length
            kept.append((
                pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t,
            ))
            break
        acc += length
        kept.append(pts[i + 1])
    path = skia.Path()
    path.moveTo(kept[0][0], kept[0][1])
    for x, y in kept[1:]:
        path.lineTo(x, y)
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5)
    pen.setColor(skia.ColorSetARGB(220, 255, 244, 220))
    pen.setPathEffect(skia.DashPathEffect.Make([10, 12], 0))
    canvas.drawPath(path, pen)


def graticule(canvas, cam, w: int, h: int, emphasis: float = 0.0):
    if cam.proj != "merc":
        return
    view = view_for(cam, w, h)
    y0, y1 = 0.64 * h, 0.72 * h

    def stroke(points, color, width):
        if len(points) < 2:
            return
        path = skia.Path()
        path.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, y)
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
        pen.setColor(skia.ColorSetARGB(color[3], color[0], color[1], color[2]))
        canvas.drawPath(path, pen)

    def chain(samples):
        run = []
        runs = []
        for lon, lat in samples:
            p = project_one(float(lon), float(lat), view)
            if p is None or y0 <= p[1] <= y1:
                if len(run) >= 2:
                    runs.append(run)
                run = []
                continue
            run.append(p)
        if len(run) >= 2:
            runs.append(run)
        return runs

    lons = np.linspace(cam.lon - cam.span * 0.95, cam.lon + cam.span * 0.95, 48)
    for lat in range(-45, 76, 15):
        hot = abs(lat - 70) < 1 and emphasis > 0.2
        color = (255, 214, 90, int(210 * emphasis)) if hot else (170, 198, 206, 110)
        width = 4.0 if hot else 1.4
        for run in chain((lon, lat) for lon in lons):
            stroke(run, color, width)
    lats = np.linspace(-50, 78, 40)
    for lon in range(-60, 61, 20):
        for run in chain((lon, lat) for lat in lats):
            stroke(run, (170, 198, 206, 80), 1.2)
