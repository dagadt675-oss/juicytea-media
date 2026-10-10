"""Gold style kit.

Palette and layout are measured from the Canada Short storyboard
(pipeline/style/gold_canada.md). Motion is a single overshoot, a one-shot
pulse, or a drift that only travels one way. Nothing here moves the camera.
"""

from __future__ import annotations

import math

import numpy as np
import skia

from jt.project import ease_out

# Medians from the 1080 gold file, one frame per second.
OCEAN = (8, 8, 24)          # #080818
LAND = (40, 48, 72)         # #283048
NEON_RGB = (232, 34, 71)    # #E82247  Canada
PAPER = (248, 248, 248)     # #F8F8F8
INK = (18, 18, 22)
GOLD = (254, 212, 10)       # #FED40A  karaoke stress + latitude line
CYAN = (5, 174, 224)        # #05AEE0  Italy
PURPLE = (200, 29, 159)     # #C81D9F  California-border pill
COAST = (168, 184, 204)

# Fill, ink. ghost has no fill.
PILLS = {
    "white": (PAPER, INK),
    "red": (NEON_RGB, (255, 255, 255)),
    "yellow": (GOLD, (22, 16, 8)),
    "purple": (PURPLE, (255, 255, 255)),
    "blue": ((3, 89, 169), (255, 255, 255)),
    "ghost": (None, (255, 255, 255)),
}

BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def pop_scale(local: float, punch: bool = False, enter: bool = True) -> float:
    """Scale in, pass 1 once, then hold. One overshoot, never a second bounce.

    enter=False starts at 1, for a count-up that pops after it arrives.
    punch is the short zoom on a punchline word.
    """
    amp = 0.18 if punch else 0.09
    dur = 0.26 if punch else 0.36
    start = 1.0 if not enter else (0.70 if punch else 0.62)
    if local <= 0.0:
        return start
    if local >= dur:
        return 1.0
    u = local / dur
    peak = 1.0 + amp
    # Rise fast, then settle. The peak is the only time the scale is above 1.
    if u < 0.55:
        return start + (peak - start) * ease_out(u / 0.55)
    return peak + (1.0 - peak) * ease_out((u - 0.55) / 0.45)


def grow(local: float, dur: float = 0.7) -> float:
    if dur <= 0:
        return 1.0
    return ease_out(max(0.0, min(1.0, local / dur)))


def trim_polyline(pts, u: float):
    """Keep the fraction u of the polyline. Returns (points, tip or None)."""
    if len(pts) < 2:
        return list(pts), (pts[-1] if pts else None)
    if u >= 0.999:
        return list(pts), pts[-1]
    if u <= 0.001:
        return [pts[0]], pts[0]
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    target = total * u
    out = [pts[0]]
    acc = 0.0
    for i, length in enumerate(seg):
        if acc + length >= target:
            t = 0.0 if length <= 1e-6 else (target - acc) / length
            tip = (
                pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t,
            )
            out.append(tip)
            return out, tip
        acc += length
        out.append(pts[i + 1])
    return out, out[-1]


def pulse_rgb(rgb, local: float):
    """One brightening, then the highlight holds. Not a loop."""
    if local < 0.0 or local > 0.48:
        return rgb
    bump = math.sin(math.pi * (local / 0.48))
    hot = (255, 110, 138)
    return tuple(int(c + (h - c) * 0.62 * bump) for c, h in zip(rgb[:3], hot))


def pin_pose(local: float, s: float = 1.0):
    """Drop in, squash once on landing, then three ripples that die."""
    drop = 0.26
    if local <= 0.0:
        return -34.0 * s, 0.72, 1.18, []
    if local < drop:
        u = ease_out(local / drop)
        dy = -34.0 * s * (1.0 - u)
        return dy, 0.72 + 0.28 * u, 1.18 - 0.18 * u, []
    landed = local - drop
    squ = 0.10
    if landed < squ:
        u = landed / squ
        sy = 0.84 + 0.16 * u
        sx = 1.12 - 0.12 * u
    else:
        sx, sy = 1.0, 1.0
    ripples = []
    for i, start in enumerate((0.0, 0.16, 0.32)):
        age = landed - start
        if 0.0 <= age <= 0.55:
            ripples.append((age / 0.55, 1.0 - age / 0.55))
    return 0.0, sx, sy, ripples


def _typeface():
    tf = skia.Typeface.MakeFromFile(BOLD)
    if tf is None:
        tf = skia.Typeface.MakeFromFile(FALLBACK)
    if tf is None:
        raise RuntimeError("no usable font")
    return tf


_FACE = None


def face():
    global _FACE
    if _FACE is None:
        _FACE = _typeface()
    return _FACE


def font(px: float):
    return skia.Font(face(), max(8.0, px))


def _paint(r, g, b, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setColor(skia.ColorSetARGB(int(a), int(r), int(g), int(b)))
    return p


def draw_pill(canvas, text: str, x: float, y: float, pop: float, s: float = 1.0):
    """White capsule, red ink. pop is a scale around the centre, usually pop_scale."""
    pop = max(0.05, float(pop))
    f = font(40 * s * pop)
    width = f.measureText(text)
    metrics = f.getMetrics()
    pad_x, pad_y = 16 * s * pop, 8 * s * pop
    text_h = metrics.fDescent - metrics.fAscent
    bw, bh = width + pad_x * 2, text_h + pad_y * 2
    left, top = x - bw / 2, y - bh / 2
    rect = skia.Rect.MakeLTRB(left, top, left + bw, top + bh)
    canvas.drawRRect(skia.RRect.MakeRectXY(rect, bh / 2, bh / 2), _paint(*PAPER))
    baseline = top + (bh - text_h) / 2 - metrics.fAscent
    canvas.drawString(text, left + pad_x, baseline, f, _paint(*INK))
    return rect


def draw_tip(canvas, x: float, y: float, s: float = 1.0):
    canvas.drawCircle(x, y, 11 * s, _paint(228, 32, 68, 70))
    canvas.drawCircle(x, y, 5.5 * s, _paint(255, 150, 170, 255))
    canvas.drawCircle(x, y, 2.4 * s, _paint(*NEON_RGB))


def draw_sweep(canvas, w: int, h: int, local: float):
    """One soft band crosses left to right at the start of a beat. It does not return."""
    if not (0.06 <= local <= 0.70):
        return
    u = (local - 0.06) / 0.64
    x = -0.28 * w + u * 1.40 * w
    canvas.save()
    canvas.rotate(-16, w / 2, h / 2)
    canvas.drawRect(skia.Rect.MakeLTRB(x, -h, x + 0.12 * w, h * 2), _paint(255, 255, 255, 16))
    canvas.restore()


def highlight_glint(canvas, path, local: float, w: int, h: int):
    """One soft glint clipped to the highlighted shape, then it is gone."""
    if path is None or path.countPoints() < 3 or not (0.04 <= local <= 0.50):
        return
    u = (local - 0.04) / 0.46
    canvas.save()
    canvas.clipPath(path, doAntiAlias=True)
    canvas.rotate(-18, w / 2.0, h / 2.0)
    x = -0.40 * w + u * 1.70 * w
    band = 0.09 * w
    canvas.drawRect(skia.Rect.MakeLTRB(x - band, -h, x + band * 0.45, h * 2), _paint(255, 214, 224, 36))
    canvas.drawRect(skia.Rect.MakeLTRB(x, -h, x + band * 0.22, h * 2), _paint(255, 236, 242, 58))
    canvas.restore()


def draw_sparkles(canvas, x: float, y: float, local: float, s: float = 1.0, seed: int = 1):
    """A short burst. Gone after half a second."""
    if not (0.12 <= local <= 0.62):
        return
    age = (local - 0.12) / 0.50
    rng = np.random.default_rng(seed)
    for i in range(7):
        ang = float(rng.uniform(0, math.tau))
        dist = (10 + 46 * age) * s * float(rng.uniform(0.6, 1.0))
        alpha = int(220 * (1.0 - age))
        px = x + math.cos(ang) * dist
        py = y + math.sin(ang) * dist
        canvas.drawCircle(px, py, (2.4 - 1.2 * age) * s, _paint(255, 186, 196, alpha))


# 50m Canada/US rings fill the Great Lakes. The gold film shows them as navy holes.
LAKES = (
    # Superior
    ((46.55, -92.10), (46.75, -90.80), (47.00, -89.40), (47.40, -88.20), (47.90, -87.20),
     (48.30, -88.40), (48.15, -89.60), (47.60, -90.70), (47.00, -91.60), (46.70, -92.05)),
    # Michigan
    ((41.75, -86.60), (42.50, -86.70), (44.20, -86.60), (45.70, -86.10), (45.90, -85.20),
     (45.40, -85.40), (44.00, -86.20), (43.00, -86.20), (42.00, -86.40)),
    # Huron
    ((43.05, -82.45), (43.80, -82.20), (44.80, -81.80), (45.80, -82.20), (46.00, -83.80),
     (45.20, -83.60), (44.00, -82.80), (43.30, -82.50)),
    # Erie. Keeps the water south of the Ontario shore.
    ((41.68, -83.35), (41.48, -82.95), (41.42, -82.40), (41.50, -81.70), (41.70, -81.05),
     (42.05, -80.30), (42.25, -79.80), (42.60, -79.15), (42.82, -79.20), (42.70, -79.85),
     (42.50, -80.55), (42.25, -81.35), (41.95, -82.15), (41.80, -82.70), (41.70, -83.15)),
    # Ontario
    ((43.30, -79.10), (43.45, -77.80), (43.70, -76.60), (44.05, -76.40), (43.85, -77.40),
     (43.50, -78.80), (43.28, -79.20)),
)


def draw_lakes(canvas, project, s: float = 1.0):
    """Navy holes for the Great Lakes. project(lon, lat) -> (x, y) or None."""
    paint = _paint(*OCEAN)
    edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
    edge.setStrokeWidth(1.4 * s)
    edge.setColor(skia.ColorSetARGB(255, 168, 184, 204))
    for ring in LAKES:
        path = skia.Path()
        started = False
        for lat, lon in ring:
            hit = project(lon, lat)
            if hit is None:
                continue
            if not started:
                path.moveTo(hit[0], hit[1])
                started = True
            else:
                path.lineTo(hit[0], hit[1])
        if not started:
            continue
        path.close()
        canvas.drawPath(path, paint)
        canvas.drawPath(path, edge)


def draw_snow(canvas, w: int, h: int, t: float, s: float = 1.0):
    """White specks falling down. One direction. The caption slot stays clear."""
    y0b, y1b = 0.64 * h, 0.72 * h
    for i in range(48):
        x = (i * 137 + 30) % w
        y = ((i * 91) + t * 42.0) % (h + 20) - 10
        if y0b <= y <= y1b:
            continue
        canvas.drawCircle(x, y, (1.4 + (i % 3) * 0.5) * s, _paint(236, 242, 248, 200))


def draw_react(canvas, x: float, y: float, local: float, s: float = 1.0):
    """A small popped face for the hook. One overshoot, then it holds."""
    if local < 0.02:
        return
    sc = pop_scale(local, punch=True)
    r = 34 * s * sc
    canvas.drawCircle(x, y - r * 0.85, 14 * s * sc, _paint(120, 210, 240))
    canvas.drawCircle(x, y, r, _paint(*GOLD))
    for sx in (-1, 1):
        canvas.drawCircle(x + sx * 11 * s * sc, y - 6 * s * sc, 7 * s * sc, _paint(255, 255, 255))
        canvas.drawCircle(x + sx * 11 * s * sc, y - 4 * s * sc, 3.2 * s * sc, _paint(20, 16, 8))
    canvas.drawCircle(x, y + 12 * s * sc, 6 * s * sc, _paint(20, 16, 8))


def draw_motes(canvas, w: int, h: int, t: float, s: float = 1.0):
    """Specks drifting right, including across a land-filled hold. They never reverse.

    The caption slot (y 0.64–0.72) stays clear.
    """
    spots = (
        (0.08, 40.0, 2.6),
        (0.20, 180.0, 3.2),
        (0.34, 300.0, 2.4),
        (0.48, 90.0, 3.0),
        (0.58, 240.0, 2.6),
        (0.78, 150.0, 3.2),
        (0.90, 20.0, 2.4),
    )
    for yf, phase, rad in spots:
        x = (phase + t * 28.0) % (w + 48) - 24
        canvas.drawCircle(x, yf * h, rad * s, _paint(186, 208, 226, 168))


def draw_counter(canvas, x: float, y: float, value: int, unit: str, local: float, s: float = 1.0):
    u = grow(local, 0.85)
    shown = int(round(value * u))
    pop = pop_scale(max(0.0, local - 0.7), punch=True, enter=False)
    f = font(120 * s * pop)
    label = f"{shown}"
    width = f.measureText(label)
    metrics = f.getMetrics()
    text_h = metrics.fDescent - metrics.fAscent
    pad_x, pad_y = 28 * s, 10 * s
    unit_f = font(36 * s * pop)
    unit_w = unit_f.measureText(unit) if unit else 0
    bw = width + (unit_w + 12 * s if unit else 0) + pad_x * 2
    bh = text_h + pad_y * 2
    left, top = x - bw / 2, y - bh / 2
    rect = skia.Rect.MakeLTRB(left, top, left + bw, top + bh)
    canvas.drawRRect(skia.RRect.MakeRectXY(rect, 28 * s, 28 * s), _paint(*PAPER))
    baseline = top + (bh - text_h) / 2 - metrics.fAscent
    canvas.drawString(label, left + pad_x, baseline, f, _paint(*INK))
    if unit:
        canvas.drawString(unit, left + pad_x + width + 10 * s, baseline, unit_f, _paint(*INK))
    return rect


def draw_stamp(canvas, x: float, y: float, local: float, s: float = 1.0, text: str = "X"):
    """A stamp that scales in once and holds. Not a wobble."""
    if local < 0.05:
        return None
    u = ease_out(min(1.0, (local - 0.05) / 0.28))
    # Own scale-in, then one extra pop. enter=False so it does not shrink first.
    scale = (0.55 + 0.45 * u) * pop_scale(local, punch=True, enter=False)
    f = font(180 * s * scale)
    width = f.measureText(text)
    metrics = f.getMetrics()
    canvas.save()
    canvas.rotate(-14, x, y)
    paint = _paint(228, 32, 68, int(230 * min(1.0, u * 1.4)))
    stroke = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
    stroke.setStrokeWidth(10 * s * scale)
    stroke.setColor(skia.ColorSetARGB(int(230 * min(1.0, u * 1.4)), 228, 32, 68))
    baseline = y - (metrics.fAscent + metrics.fDescent) / 2
    canvas.drawString(text, x - width / 2, baseline, f, stroke)
    canvas.restore()
    return skia.Rect.MakeLTRB(x - width / 2, y - 80 * s, x + width / 2, y + 80 * s)


def drift_field(frame: np.ndarray, t: float, xs, ys) -> None:
    """Stars and slower clouds, both moving right. Ocean only; land covers them."""
    h, w = frame.shape[:2]
    # Clouds first, slower, so stars read as a nearer layer.
    cloud = np.array([18, 24, 42], np.uint8)
    for i in range(4):
        cx = int((i * 280 + 40 + t * 10.0) % (w + 180) - 90)
        cy = int((0.08 + 0.05 * (i % 3)) * h)
        rr = 26 + 10 * (i % 3)
        y0, y1 = max(0, cy - rr), min(h, cy + rr)
        x0, x1 = max(0, cx - rr * 2), min(w, cx + rr * 2)
        if y1 <= y0 or x1 <= x0:
            continue
        yy = np.arange(y0, y1)[:, None]
        xx = np.arange(x0, x1)[None, :]
        mask = ((xx - cx) / (rr * 2)) ** 2 + ((yy - cy) / rr) ** 2 <= 1.0
        frame[y0:y1, x0:x1][mask] = cloud
    col = (110, 136, 168)
    shift = t * 26.0
    for x, y in zip(xs, ys):
        xi = int((float(x) + shift) % w)
        yi = int(y) % h
        frame[yi, xi] = col
        if xi + 1 < w:
            frame[yi, xi + 1] = col
