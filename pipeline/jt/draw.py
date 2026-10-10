"""Safe-zone text drawer and the overlays every beat can ask for.

Every glyph goes through Safe. The box is inside x <= 880 (1080-space),
below the top 13.5% and above the bottom 22.5%, so antialiasing stays out of
the top 12%, bottom 20% and the x > 900 column.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia

from jt.captions import active_index
from jt.project import ease_out, laea_forward, project_one, project_points
from jt.themes import SUB, WHITE, YELLOW

BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
SEMI = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"
MED = "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def text_pixel_mask(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    white = (r > 200) & (g > 200) & (b > 190)
    yellow = (r > 200) & (g > 160) & (b < 90)
    orange = (r > 210) & (g > 90) & (g < 180) & (b < 80)
    cyan = (g > 200) & (b > 200) & (r < 140)
    return white | yellow | orange | cyan


def clamp_nontext(rgb: np.ndarray) -> None:
    mask = text_pixel_mask(rgb)
    if np.any(mask):
        rgb[mask] = (36, 58, 78)


def _face(path: str):
    if Path(path).exists():
        tf = skia.Typeface.MakeFromFile(path)
        if tf is not None:
            return tf
    tf = skia.Typeface.MakeFromFile(FALLBACK)
    if tf is None:
        raise RuntimeError("no usable font")
    return tf


FACES = None


def faces():
    global FACES
    if FACES is None:
        FACES = {"bold": _face(BOLD), "semi": _face(SEMI), "med": _face(MED)}
    return FACES


def _rgba(paint, color):
    r, g, b, a = color
    paint.setColor(skia.ColorSetARGB(a, r, g, b))


def parse_accent(text: str) -> list[tuple[str, bool]]:
    parts, buf, acc = [], "", False
    for ch in text:
        if ch == "*":
            if buf:
                parts.append((buf, acc))
                buf = ""
            acc = not acc
        else:
            buf += ch
    if buf:
        parts.append((buf, acc))
    return parts or [("", False)]


class Safe:
    """Clamps every string into the safe rectangle."""

    def __init__(self, canvas, w: int, h: int):
        self.canvas = canvas
        self.w = w
        self.h = h
        self.s = w / 1080.0
        self.left = 56 * self.s
        self.right = 868 * self.s
        self.top = 0.135 * h
        self.bottom = 0.775 * h
        self.spills = 0

    def font(self, which: str, ref_px: float):
        return skia.Font(faces()[which], max(8.0, ref_px * self.s))

    def text(self, text: str, x: float, baseline: float, font, color, align: str = "left"):
        if not text:
            return None
        width = font.measureText(text)
        metrics = font.getMetrics()
        if align == "center":
            x -= width / 2
        elif align == "right":
            x -= width
        top = baseline + metrics.fAscent
        bot = baseline + metrics.fDescent
        if x + width > self.right:
            x -= (x + width) - self.right
        if x < self.left:
            x += self.left - x
        if top < self.top:
            baseline += self.top - top
        if baseline + metrics.fDescent > self.bottom:
            baseline -= (baseline + metrics.fDescent) - self.bottom
        top = baseline + metrics.fAscent
        bot = baseline + metrics.fDescent
        if x < self.left - 1 or x + width > self.right + 1 or top < self.top - 1 or bot > self.bottom + 1:
            self.spills += 1
            return None
        paint = skia.Paint(AntiAlias=True)
        _rgba(paint, color)
        self.canvas.drawString(text, x, baseline, font, paint)
        return x, baseline, width, top, bot


def _pill(canvas, rect, radius=16):
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(214, 8, 10, 16))
    canvas.drawRRect(skia.RRect.MakeRectXY(rect, radius, radius), paint)


def _stroke(color, width, alpha=255, dash=None, phase=0):
    r, g, b = color[:3]
    paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    paint.setColor(skia.ColorSetARGB(alpha, r, g, b))
    if dash:
        paint.setPathEffect(skia.DashPathEffect.Make(dash, phase))
    return paint


def _polyline(canvas, pts, paint):
    if len(pts) < 2:
        return
    path = skia.Path()
    path.moveTo(pts[0][0], pts[0][1])
    for x, y in pts[1:]:
        path.lineTo(x, y)
    canvas.drawPath(path, paint)


def _chain(lonlat, view, band=None):
    """Project a lon/lat polyline, splitting on the horizon and on big jumps."""
    if len(lonlat) < 2:
        return []
    lon = np.array([p[0] for p in lonlat])
    lat = np.array([p[1] for p in lat]) if False else np.array([p[1] for p in lonlat])
    x, y, vis = project_points(lon, lat, view)
    chains = []
    cur = []
    for i in range(len(lon)):
        ok = bool(vis[i])
        if band is not None and ok:
            ok = band[0] <= y[i] <= band[1] and 8 <= x[i] <= view.cx * 2 + 400
        if not ok:
            if len(cur) >= 2:
                chains.append(cur)
            cur = []
            continue
        if cur and abs(x[i] - cur[-1][0]) > 180:
            if len(cur) >= 2:
                chains.append(cur)
            cur = []
        cur.append((float(x[i]), float(y[i])))
    if len(cur) >= 2:
        chains.append(cur)
    return chains


def draw_graticule(canvas, view, theme, phase: float):
    paint = _stroke(theme["line"], 1.6, alpha=110, dash=[9, 11], phase=phase * 52)
    for lon in range(-150, 181, 30):
        pts = [(lon, lat) for lat in np.linspace(-70, 78, 20)]
        for chain in _chain(pts, view):
            _polyline(canvas, chain, paint)
    for lat in range(-60, 76, 30):
        pts = [(lon, lat) for lon in np.linspace(-180, 180, 36)]
        for chain in _chain(pts, view):
            _polyline(canvas, chain, paint)


def draw_parallel(canvas, safe: Safe, view, theme, phase, lat, label, t):
    paint = _stroke(theme["line"], 3.2, alpha=200, dash=[14, 10], phase=(t * 42) % 48)
    pts = [(lon, lat) for lon in np.linspace(view.lon - view.span, view.lon + view.span, 40)]
    chains = _chain(pts, view)
    for chain in chains:
        _polyline(canvas, chain, paint)
    if label and chains:
        mid = chains[0][len(chains[0]) // 2]
        font = safe.font("semi", 56)
        safe.text(label, mid[0], mid[1] - 14 * safe.s, font, WHITE, "center")


def draw_meridian(canvas, safe: Safe, view, theme, lon, label, t):
    paint = _stroke(theme["line"], 3.4, alpha=210, dash=[14, 10], phase=(t * 48) % 48)
    pts = [(lon, lat) for lat in np.linspace(view.lat - view.span * 0.6, view.lat + view.span * 0.6, 28)]
    chains = _chain(pts, view)
    for chain in chains:
        _polyline(canvas, chain, paint)
    if label and chains:
        mid = chains[0][len(chains[0]) // 2]
        font = safe.font("semi", 56)
        safe.text(label, mid[0] + 12 * safe.s, mid[1], font, WHITE, "left")


def draw_marker(canvas, safe: Safe, view, theme, lat, lon, label, t):
    hit = project_one(lon, lat, view)
    if hit is None:
        return
    x, y = hit
    pulse = 0.5 + 0.5 * math.sin(t * 5.4)
    col = theme["marker"]
    canvas.drawCircle(x, y, 8 + 6 * pulse, _stroke(col, 3.5, 230))
    fill = skia.Paint(AntiAlias=True)
    fill.setColor(skia.ColorSetARGB(255, col[0], col[1], col[2]))
    canvas.drawCircle(x, y, 4.0, fill)
    font = safe.font("bold", 56)
    safe.text(label, x, y - 18 * safe.s, font, WHITE, "center")


def draw_ruler(canvas, safe: Safe, view, vis, local, t):
    a = vis.get("a") or vis.get("from")
    b = vis.get("b") or vis.get("to")
    p1 = project_one(a[1], a[0], view) if a else None
    p2 = project_one(b[1], b[0], view) if b else None
    if p1 is None or p2 is None:
        return
    grow = ease_out(min(1.0, local / 0.35))
    x2 = p1[0] + (p2[0] - p1[0]) * grow
    y2 = p1[1] + (p2[1] - p1[1]) * grow
    paint = _stroke((190, 168, 120), 4.0, 220, dash=[6, 8], phase=(t * 36) % 28)
    # Muted gold stays under the orange text mask (r < 210).
    canvas.drawLine(p1[0], p1[1], x2, y2, paint)
    for px, py in (p1, (x2, y2)):
        canvas.drawLine(px, py - 8, px, py + 8, _stroke((190, 168, 120), 3, 220))
    label = str(vis.get("label", ""))
    font = safe.font("bold", 56)
    safe.text(label, (p1[0] + x2) / 2, (p1[1] + y2) / 2 - 16 * safe.s, font, YELLOW, "center")


def draw_bignum(safe: Safe, vis, local):
    u = ease_out(min(1.0, local / 0.2))
    size = float(vis.get("size", 112)) * (1.16 - 0.16 * u)
    font = safe.font("bold", size)
    sub_font = safe.font("semi", 48)
    text = str(vis["text"])
    width = font.measureText(text)
    metrics = font.getMetrics()
    baseline = 0.355 * safe.h
    x = safe.left + 6 * safe.s
    if x + width > safe.right:
        # Shrink until it fits rather than spill.
        while size > 64 and x + font.measureText(text) > safe.right:
            size -= 4
            font = safe.font("bold", size)
    top = baseline + metrics.fAscent
    bot = baseline + metrics.fDescent
    pad = 12 * safe.s
    rect = skia.Rect.MakeLTRB(x - pad, top - pad, min(safe.right, x + font.measureText(text) + pad), bot + pad)
    if rect.bottom() > safe.bottom or rect.top() < safe.top:
        return
    _pill(safe.canvas, rect, 18 * safe.s)
    safe.text(text, x, baseline, font, YELLOW, "left")
    sub = vis.get("unit") or vis.get("sub") or ""
    if sub:
        safe.text(sub, x, baseline + (metrics.fDescent - sub_font.getMetrics().fAscent) + 8 * safe.s,
                  sub_font, WHITE, "left")


def draw_claim(safe: Safe, claim: str, sub: str, local: float):
    u = ease_out(min(1.0, local / 0.16))
    # Size the type so the slammed frame (scale 1.14) still clears x = 900.
    lines = claim.split("\n")
    parsed_for_fit = [parse_accent(line) for line in lines]
    max_w = (safe.right - safe.left) - 64 * safe.s
    size = 92.0
    while size > 64:
        probe = safe.font("bold", size * 1.14)
        widest = max(sum(probe.measureText(bit) for bit, _acc in parts) for parts in parsed_for_fit)
        if widest <= max_w:
            break
        size -= 2
    scale = 1.14 - 0.14 * u
    font = safe.font("bold", size * scale)
    sub_font = safe.font("med", 56)
    metrics = font.getMetrics()
    line_h = (metrics.fDescent - metrics.fAscent) + 6 * safe.s
    # Top of the first line sits just under the top safe edge.
    baseline = safe.top + 8 * safe.s - metrics.fAscent
    widths = []
    parsed = []
    for line in lines:
        parts = parse_accent(line)
        parsed.append(parts)
        widths.append(sum(font.measureText(bit) for bit, _acc in parts))
    block_w = max(widths) if widths else 0
    block_h = line_h * len(lines)
    if sub:
        block_h += (sub_font.getMetrics().fDescent - sub_font.getMetrics().fAscent) + 10 * safe.s
    cx = (safe.left + safe.right) / 2
    left = cx - block_w / 2
    top = baseline + metrics.fAscent - 14 * safe.s
    rect = skia.Rect.MakeLTRB(left - 22 * safe.s, top, left + block_w + 22 * safe.s,
                              top + block_h + 28 * safe.s)
    if rect.right() > safe.right + 8 * safe.s:
        shift = rect.right() - (safe.right + 4 * safe.s)
        rect.offset(-shift, 0)
        left -= shift
    if rect.left() < safe.left - 8 * safe.s:
        shift = safe.left - rect.left()
        rect.offset(shift, 0)
        left += shift
    if rect.bottom() > safe.bottom:
        return
    _pill(safe.canvas, rect, 20 * safe.s)
    y = baseline
    for parts, width in zip(parsed, widths):
        x = left + (block_w - width) / 2
        for bit, acc in parts:
            color = YELLOW if acc else WHITE
            paint = skia.Paint(AntiAlias=True)
            _rgba(paint, color)
            safe.canvas.drawString(bit, x, y, font, paint)
            x += font.measureText(bit)
        y += line_h
    # Wipe under the claim. Yellow, and the pill keeps it inside the safe rect.
    wipe_w = block_w * u
    bar = skia.Paint(AntiAlias=True)
    _rgba(bar, YELLOW)
    bar_y = baseline + metrics.fDescent + 2 * safe.s
    safe.canvas.drawRect(skia.Rect.MakeLTRB(left, bar_y, left + wipe_w, bar_y + 4 * safe.s), bar)
    if sub:
        safe.text(sub, left, y - sub_font.getMetrics().fAscent, sub_font, SUB, "left")


def draw_caption(safe: Safe, words, groups, t) -> dict | None:
    idx = active_index(words, t)
    if idx is None:
        return None
    group = next(g for g in groups if idx in g)
    # Fit 1–3 words at >= 64 px (1080 reference) inside the safe width.
    size = 72.0
    guard = 0
    while guard < 8:
        guard += 1
        font = safe.font("bold", size)
        pop = safe.font("bold", size * 1.06)
        tokens = [(words[i]["text"].upper(), i) for i in group]
        gap = 16 * safe.s

        def width_of(toks):
            total = 0.0
            for text, i in toks:
                f = pop if i == idx else font
                total += f.measureText(text)
            total += gap * (len(toks) - 1)
            return total

        max_w = (safe.right - safe.left) - 48 * safe.s
        if width_of(tokens) <= max_w or len(tokens) == 1:
            if width_of(tokens) > max_w and size > 64:
                size -= 4
                continue
            break
        # Drop the word farthest from the spoken one.
        if group[-1] != idx:
            group = group[:-1]
        else:
            group = group[1:]
    font = safe.font("bold", size)
    pop = safe.font("bold", size * 1.06)
    tokens = [(words[i]["text"].upper(), i) for i in group]
    gap = 16 * safe.s
    widths = [(pop if i == idx else font).measureText(text) for text, i in tokens]
    total = sum(widths) + gap * (len(tokens) - 1)
    metrics = pop.getMetrics()
    center = 0.68 * safe.h
    baseline = center - metrics.fAscent * 0.45
    x = (safe.left + safe.right) / 2 - total / 2
    x = min(max(x, safe.left + 8 * safe.s), safe.right - total - 8 * safe.s)
    top = baseline + metrics.fAscent
    bot = baseline + metrics.fDescent
    pad_x, pad_y = 18 * safe.s, 12 * safe.s
    rect = skia.Rect.MakeLTRB(x - pad_x, top - pad_y, x + total + pad_x, bot + pad_y)
    if rect.right() > safe.right:
        shift = rect.right() - safe.right
        x -= shift
        rect.offset(-shift, 0)
    if rect.left() < safe.left:
        shift = safe.left - rect.left()
        x += shift
        rect.offset(shift, 0)
    if rect.top() < safe.top or rect.bottom() > safe.bottom:
        safe.spills += 1
        return None
    _pill(safe.canvas, rect, 16 * safe.s)
    cursor = x
    for (text, i), tw in zip(tokens, widths):
        f = pop if i == idx else font
        color = YELLOW if i == idx else WHITE
        paint = skia.Paint(AntiAlias=True)
        _rgba(paint, color)
        # Optically center the popped word on the same baseline.
        safe.canvas.drawString(text, cursor, baseline, f, paint)
        cursor += tw + gap
    glyph_center = baseline + metrics.fAscent * 0.5
    return {
        "px": size,
        "center_frac": glyph_center / safe.h,
        "top_frac": rect.top() / safe.h,
        "bot_frac": rect.bottom() / safe.h,
    }


def draw_ghost(canvas, safe: Safe, earth, view, vis, local):
    iso = str(vis.get("country", "")).upper()
    rings = earth.rings.get(iso) or []
    if not rings:
        return
    src_lon = vis.get("src_lon")
    src_lat = vis.get("src_lat")
    if src_lon is None:
        sample = np.concatenate([r for r in rings[:4]])
        src_lon = float(np.mean(sample[:, 0]))
        src_lat = float(np.mean(sample[:, 1]))
    anchor = project_one(float(vis.get("anchor_lon", view.lon)),
                          float(vis.get("anchor_lat", view.lat)), view)
    if anchor is None:
        anchor = (view.cx, view.cy)
    if view.proj == "ortho":
        scale = view.r
    else:
        x0, y0, x1, y1 = view.rect
        scale = (x1 - x0) / math.radians(max(view.span, 1.0))
    u = ease_out(min(1.0, local / 0.45))
    acc = []
    for ring in rings:
        xs, ys = laea_forward(ring[:, 0], ring[:, 1], src_lon, src_lat)
        acc.append((xs, ys))
    cx = float(np.mean(np.concatenate([a[0] for a in acc])))
    cy = float(np.mean(np.concatenate([a[1] for a in acc])))
    slide = (1 - u) * 0.18 * safe.w
    path = skia.Path()
    path.setFillType(skia.PathFillType.kEvenOdd)
    for xs, ys in acc:
        sx = anchor[0] + (xs - cx) * scale + slide
        sy = anchor[1] - (ys - cy) * scale
        path.moveTo(float(sx[0]), float(sy[0]))
        for x, y in zip(sx[1:], sy[1:]):
            path.lineTo(float(x), float(y))
        path.close()
    fill = skia.Paint(AntiAlias=True)
    fill.setColor(skia.ColorSetARGB(int(70 + 50 * u), 46, 120, 110))
    canvas.drawPath(path, fill)
    canvas.drawPath(path, _stroke((120, 186, 160), 3, 180))
    label = str(vis.get("label", iso))
    font = safe.font("bold", 56)
    safe.text(label, anchor[0] + slide, anchor[1] - 20 * safe.s, font, WHITE, "center")


def draw_island(canvas, safe: Safe, vis, t):
    """Procedural split island for a feature too small for the coastline data."""
    s = safe.s
    card_w = min(safe.right - safe.left, 460 * s)
    card_h = 250 * s
    x0 = safe.left
    y0 = 0.33 * safe.h
    rect = skia.Rect.MakeLTRB(x0, y0, x0 + card_w, y0 + card_h)
    _pill(canvas, rect, 22 * s)
    cx, cy = x0 + card_w * 0.5, y0 + card_h * 0.46
    pulse = 1 + 0.015 * math.sin(t * 3)
    path_l, path_r = skia.Path(), skia.Path()
    pts = []
    for i in range(72):
        a = 2 * math.pi * i / 72
        rad = (1 + 0.14 * math.sin(3 * a) + 0.07 * math.sin(5 * a + 1.2)) * pulse
        px = cx + math.cos(a) * card_w * 0.28 * rad
        py = cy + math.sin(a) * card_h * 0.28 * rad
        pts.append((px, py))
    # Split on x = cx, ravine leans with time.
    lean = 8 * s * math.sin(t * 0.8)
    for i, (px, py) in enumerate(pts):
        path = path_l if px <= cx + lean else path_r
        if i == 0 or (pts[i - 1][0] <= cx + lean) != (px <= cx + lean):
            path.moveTo(cx + lean, py)
        path.lineTo(px, py)
    path_l.close()
    path_r.close()
    left = skia.Paint(AntiAlias=True)
    left.setColor(skia.ColorSetARGB(230, 36, 96, 170))
    right = skia.Paint(AntiAlias=True)
    right.setColor(skia.ColorSetARGB(230, 140, 64, 78))
    canvas.drawPath(path_l, left)
    canvas.drawPath(path_r, right)
    canvas.drawLine(cx + lean, cy - card_h * 0.22, cx - lean, cy + card_h * 0.22,
                    _stroke((232, 220, 200), 3, 180, dash=[5, 6], phase=t * 20))
    font = safe.font("bold", 40)
    # 40 px reference is under the 56 px caption rule; these are map labels on a
    # diagram, so bump them to 56.
    font = safe.font("bold", 56)
    safe.text(str(vis.get("left", "")), cx - card_w * 0.22, cy + 8 * s, font, WHITE, "center")
    safe.text(str(vis.get("right", "")), cx + card_w * 0.22, cy + 8 * s, font, WHITE, "center")
    if vis.get("ruler"):
        safe.text(str(vis["ruler"]), cx, y0 + card_h - 28 * s, font, YELLOW, "center")


def draw_highlight_stroke(canvas, earth, view, theme, ids: dict, t: float):
    if not ids:
        return
    width = 2.4 + 1.2 * (0.5 + 0.5 * math.sin(t * 3.2))
    paint = _stroke(theme["hi"], width, 180)
    # Stroke only a handful of rings so a zoomed frame stays cheap.
    seen = set()
    for cid in ids:
        if cid >= len(earth.meta) or not earth.meta[cid]:
            continue
        iso = earth.meta[cid]["iso"]
        if iso in seen:
            continue
        seen.add(iso)
        for ring in earth.rings.get(iso, [])[:6]:
            pts = [(float(p[0]), float(p[1])) for p in ring]
            for chain in _chain(pts, view):
                _polyline(canvas, chain, paint)


def draw_atmosphere(canvas, view, theme):
    if view.proj != "ortho":
        return
    canvas.drawCircle(view.cx, view.cy, view.r * 1.01, _stroke(theme["rim"], 16, 55))
    canvas.drawCircle(view.cx, view.cy, view.r * 1.045, _stroke(theme["rim"], 8, 30))


def overlay(canvas, safe: Safe, earth, view, visuals, claim, sub, words, groups, t, local, theme,
            highlight_ids=None) -> dict:
    draw_atmosphere(canvas, view, theme)
    # A faint moving grid is always on, so a hold is never a still photograph.
    draw_graticule(canvas, view, theme, t)
    draw_highlight_stroke(canvas, earth, view, theme, highlight_ids or {}, t)
    highlights = {}
    for vis in visuals:
        kind = vis.get("type")
        if kind == "latline":
            draw_parallel(canvas, safe, view, theme, t, float(vis["lat"]), vis.get("label", ""), t)
        elif kind == "lonline":
            draw_meridian(canvas, safe, view, theme, float(vis["lon"]), vis.get("label", ""), t)
        elif kind == "marker":
            draw_marker(canvas, safe, view, theme, float(vis["lat"]), float(vis["lon"]),
                        str(vis.get("label", "")), t)
        elif kind == "ruler":
            draw_ruler(canvas, safe, view, vis, local, t)
        elif kind == "bignum":
            draw_bignum(safe, vis, local)
        elif kind == "ghost":
            draw_ghost(canvas, safe, earth, view, vis, local)
        elif kind == "island":
            draw_island(canvas, safe, vis, t)
    # Country stroke uses the same highlight ids the sampler did. Passed via visuals.
    draw_claim(safe, claim, sub, local)
    cap = draw_caption(safe, words, groups, t)
    return {"caption": cap, "spills": safe.spills}
