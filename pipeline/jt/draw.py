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
from jt.project import ease_out, laea_forward, project_one, project_points, route_lonlat
from jt.themes import NEON, SUB, WHITE, YELLOW

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
        self.overlaps = 0
        self.blockers = []

    def block(self, rect) -> None:
        self.blockers.append(rect)

    def hits(self, rect) -> bool:
        if rect.left() < self.left or rect.right() > self.right:
            return True
        if rect.top() < self.top or rect.bottom() > self.bottom:
            return True
        for other in self.blockers:
            if rect.right() < other.left() or rect.left() > other.right():
                continue
            if rect.bottom() < other.top() or rect.top() > other.bottom():
                continue
            return True
        return False

    def point_blocked(self, x: float, y: float) -> bool:
        if x < self.left or x > self.right or y < self.top or y > self.bottom:
            return True
        for other in self.blockers:
            if other.left() <= x <= other.right() and other.top() <= y <= other.bottom():
                return True
        return False

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


def _badge(safe: Safe, text: str, x: float, y: float, theme) -> bool:
    """White pill, red type. Nudges off the title and the caption band, or skips."""
    if not text:
        return False
    font = safe.font("bold", 42)
    width = font.measureText(text)
    metrics = font.getMetrics()
    pad_x = 16 * safe.s
    pad_y = 8 * safe.s
    text_h = metrics.fDescent - metrics.fAscent
    bw = width + pad_x * 2
    bh = text_h + pad_y * 2
    paper = theme.get("paper", (248, 248, 252))
    ink = theme.get("ink", (196, 22, 58))
    offsets = ((0, -1.2), (0, 0.7), (1.05, -0.35), (-1.05, -0.35), (0, -2.0), (0, 1.5))
    for ox, oy in offsets:
        left = x - bw / 2 + ox * bw * 0.45
        top = y - bh / 2 + oy * bh
        rect = skia.Rect.MakeLTRB(left, top, left + bw, top + bh)
        if safe.hits(rect):
            continue
        fill = skia.Paint(AntiAlias=True)
        fill.setColor(skia.ColorSetARGB(255, int(paper[0]), int(paper[1]), int(paper[2])))
        safe.canvas.drawRRect(skia.RRect.MakeRectXY(rect, bh / 2, bh / 2), fill)
        baseline = top + (bh - text_h) / 2 - metrics.fAscent
        paint = skia.Paint(AntiAlias=True)
        paint.setColor(skia.ColorSetARGB(255, int(ink[0]), int(ink[1]), int(ink[2])))
        safe.canvas.drawString(text, left + pad_x, baseline, font, paint)
        safe.block(rect)
        return True
    return False


def _clip_chains(chains, safe: Safe):
    kept = []
    for chain in chains:
        cur = []
        for x, y in chain:
            if safe.point_blocked(x, y):
                if len(cur) >= 2:
                    kept.append(cur)
                cur = []
            else:
                cur.append((x, y))
        if len(cur) >= 2:
            kept.append(cur)
    return kept


def _glow(canvas, chains, color, scale: float):
    if not chains:
        return
    wide = _stroke(color, 16 * scale, alpha=64)
    core = _stroke(color, 3.4 * scale, alpha=255)
    for chain in chains:
        _polyline(canvas, chain, wide)
        _polyline(canvas, chain, core)


def _ring_paths(ring, view):
    """Projected pieces of one coastline ring. Fills only when the ring faces us."""
    lon = np.asarray(ring[:, 0], np.float64)
    lat = np.asarray(ring[:, 1], np.float64)
    if view.proj == "ortho":
        mid = len(lon) // 2
        # Cheap reject: the sample point is on the back of the globe.
        x1, y1, vis1 = project_points(lon[mid:mid + 1], lat[mid:mid + 1], view)
        if len(vis1) and not bool(vis1[0]):
            return []
    x, y, vis = project_points(lon, lat, view)
    if not np.any(vis):
        return []
    facing = float(np.mean(vis)) >= 0.72
    pieces = []
    cur = []
    for i in range(len(x)):
        if not vis[i]:
            if len(cur) >= 3 and facing:
                pieces.append(cur)
            cur = []
            continue
        if cur and abs(x[i] - cur[-1][0]) > 140:
            if len(cur) >= 3 and facing:
                pieces.append(cur)
            cur = []
        cur.append((float(x[i]), float(y[i])))
    if len(cur) >= 3 and facing:
        pieces.append(cur)
    return pieces


def draw_flat_map(canvas, earth, view, theme, highlight_ids, scale: float):
    """Anti-aliased flat country fills. No shade, no relief."""
    hi = {}
    for cid, rgb in (highlight_ids or {}).items():
        if cid >= len(earth.meta) or not earth.meta[cid]:
            continue
        if rgb[0] < 0:
            rgb = theme["hi"]
        hi[earth.meta[cid]["iso"]] = tuple(int(c) for c in rgb[:3])
    canvas.save()
    if view.proj == "ortho":
        clip = skia.Path()
        clip.addCircle(view.cx, view.cy, view.r)
        canvas.clipPath(clip, doAntiAlias=True)
    elif view.rect:
        x0, y0, x1, y1 = view.rect
        canvas.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), doAntiAlias=True)
    land_rgb = theme["land"]
    coast_rgb = theme.get("coast", (6, 12, 32))
    land_fill = skia.Paint(AntiAlias=True)
    land_fill.setColor(skia.ColorSetARGB(255, land_rgb[0], land_rgb[1], land_rgb[2]))
    coast = _stroke(coast_rgb, 1.6 * scale, 255)
    # Unhighlighted land first, neon country on top.
    later = []
    for iso, rings in earth.rings.items():
        if iso in hi:
            later.append(iso)
            continue
        for ring in rings:
            for piece in _ring_paths(ring, view):
                path = skia.Path()
                path.moveTo(piece[0][0], piece[0][1])
                for px, py in piece[1:]:
                    path.lineTo(px, py)
                path.close()
                canvas.drawPath(path, land_fill)
                canvas.drawPath(path, coast)
    for iso in later:
        rgb = hi[iso]
        fill = skia.Paint(AntiAlias=True)
        fill.setColor(skia.ColorSetARGB(255, rgb[0], rgb[1], rgb[2]))
        edge = _stroke(rgb, 2.2 * scale, 255)
        for ring in earth.rings.get(iso, []):
            for piece in _ring_paths(ring, view):
                path = skia.Path()
                path.moveTo(piece[0][0], piece[0][1])
                for px, py in piece[1:]:
                    path.lineTo(px, py)
                path.close()
                canvas.drawPath(path, fill)
                canvas.drawPath(path, edge)
    canvas.restore()


def draw_graticule(canvas, view, theme, phase: float):
    # Solid and densely sampled. Dashes at 20 points were the jagged grid.
    paint = _stroke((64, 96, 148), 1.3, alpha=120)
    for lon in range(-150, 181, 30):
        pts = [(lon, lat) for lat in np.linspace(-75, 75, 90)]
        for chain in _chain(pts, view):
            _polyline(canvas, chain, paint)
    for lat in range(-60, 76, 30):
        pts = [(lon, lat) for lon in np.linspace(-180, 180, 120)]
        for chain in _chain(pts, view):
            _polyline(canvas, chain, paint)


def _anchor(chains, safe: Safe):
    """A point on the line that sits in the open band, not on the title."""
    target = 0.46 * safe.h
    best = None
    best_d = 1e9
    for chain in chains:
        for x, y in chain[::3]:
            if safe.point_blocked(x, y):
                continue
            d = abs(y - target)
            if d < best_d:
                best_d = d
                best = (x, y)
    return best


def draw_parallel(canvas, safe: Safe, view, theme, phase, lat, label, t, draw_line=True, with_label=True):
    half = max(view.span * 0.55, 8)
    pts = [(lon, lat) for lon in np.linspace(view.lon - half, view.lon + half, 160)]
    chains = _clip_chains(_chain(pts, view), safe) if draw_line else _chain(pts, view)
    if draw_line:
        _glow(canvas, chains, theme["line"], safe.s)
    if with_label and label:
        # Anchor in the open band, using the unclipped line so the pill can sit
        # beside the stroke even where the stroke runs under the title.
        hit = _anchor(_chain(pts, view), safe)
        if hit and not safe.point_blocked(hit[0], hit[1]):
            _badge(safe, str(label), hit[0], hit[1], theme)


def draw_meridian(canvas, safe: Safe, view, theme, lon, label, t, draw_line=True, with_label=True):
    pts = [(lon, lat) for lat in np.linspace(view.lat - view.span * 0.65, view.lat + view.span * 0.65, 160)]
    chains = _clip_chains(_chain(pts, view), safe) if draw_line else _chain(pts, view)
    if draw_line:
        _glow(canvas, chains, theme["line"], safe.s)
    if with_label and label:
        hit = _anchor(_chain(pts, view), safe)
        if hit and not safe.point_blocked(hit[0], hit[1]):
            _badge(safe, str(label), hit[0], hit[1], theme)


def _route_anchor(pts, view, safe: Safe, mode: str):
    """A free point on the route: the northern crest of a great circle, else the middle."""
    best = None
    best_key = None
    for i, (lon, lat) in enumerate(pts):
        hit = project_one(lon, lat, view)
        if hit is None or safe.point_blocked(hit[0], hit[1]):
            continue
        key = (-lat, abs(i - (len(pts) - 1) / 2.0)) if mode == "great" else abs(i - (len(pts) - 1) / 2.0)
        if best_key is None or key < best_key:
            best_key = key
            best = hit
    return best


def draw_route(canvas, safe: Safe, view, theme, vis, draw_line=True, with_label=True):
    """Great-circle arc or Mercator rhumb. One stroke, optional pill."""
    a = vis.get("a") or [0, 0]
    b = vis.get("b") or [0, 0]
    mode = str(vis.get("mode", "great"))
    pts = route_lonlat(mode, float(a[0]), float(a[1]), float(b[0]), float(b[1]), 200)
    raw = _chain(pts, view)
    if draw_line:
        chains = _clip_chains(raw, safe)
        if vis.get("style") == "dashed":
            wide = _stroke(theme["line"], 12 * safe.s, alpha=48)
            core = _stroke(theme["line"], 3.6 * safe.s, 255, dash=[12 * safe.s, 9 * safe.s])
            for chain in chains:
                _polyline(canvas, chain, wide)
                _polyline(canvas, chain, core)
        else:
            _glow(canvas, chains, theme["line"], safe.s)
    if with_label and vis.get("label"):
        hit = _route_anchor(pts, view, safe, mode)
        if hit is not None:
            _badge(safe, str(vis["label"]), hit[0], hit[1], theme)


def draw_marker(canvas, safe: Safe, view, theme, lat, lon, label, t):
    hit = project_one(lon, lat, view)
    if hit is None:
        return
    x, y = hit
    if safe.point_blocked(x, y):
        return
    col = theme["marker"]
    phase = (t * 0.85) % 1.0
    for shift in (0.0, 0.5):
        p = (phase + shift) % 1.0
        radius = (12 + 46 * p) * safe.s
        alpha = int(190 * (1.0 - p))
        canvas.drawCircle(x, y, radius, _stroke(col, 3.0 * safe.s, alpha))
    fill = skia.Paint(AntiAlias=True)
    fill.setColor(skia.ColorSetARGB(255, col[0], col[1], col[2]))
    canvas.drawCircle(x, y, 8.0 * safe.s, fill)
    core = skia.Paint(AntiAlias=True)
    paper = theme.get("paper", (248, 248, 252))
    core.setColor(skia.ColorSetARGB(255, paper[0], paper[1], paper[2]))
    canvas.drawCircle(x, y, 3.2 * safe.s, core)
    if label:
        _badge(safe, str(label), x, y, theme)


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
            color = NEON if acc else WHITE
            paint = skia.Paint(AntiAlias=True)
            _rgba(paint, color)
            safe.canvas.drawString(bit, x, y, font, paint)
            x += font.measureText(bit)
        y += line_h
    # Neon rule under the title, the same red as the stressed word.
    wipe_w = block_w * u
    bar = skia.Paint(AntiAlias=True)
    _rgba(bar, NEON)
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
    cursor = x
    outline_w = max(3.0, 6.5 * safe.s)
    for (text, i), tw in zip(tokens, widths):
        f = pop if i == idx else font
        color = YELLOW if i == idx else WHITE
        stroke = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
        stroke.setStrokeWidth(outline_w)
        stroke.setColor(skia.ColorSetARGB(255, 0, 0, 0))
        safe.canvas.drawString(text, cursor, baseline, f, stroke)
        paint = skia.Paint(AntiAlias=True)
        _rgba(paint, color)
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


def _reserve_caption(safe: Safe):
    """Keep the route and pills out of the karaoke slot (y 0.64–0.72) and below it.

    A silent short leaves that band empty so karaoke can be composited later.
    """
    safe.block(skia.Rect.MakeLTRB(0, 0.58 * safe.h, safe.w, safe.h))


def _reserve_title(safe: Safe):
    """Pills stay below the title. The line is allowed under the title card."""
    safe.block(skia.Rect.MakeLTRB(0, 0, safe.w, 0.34 * safe.h))


def overlay(canvas, safe: Safe, earth, view, visuals, claim, sub, words, groups, t, local, theme,
            highlight_ids=None) -> dict:
    _reserve_caption(safe)
    flat = bool(theme.get("flat"))
    if flat:
        draw_flat_map(canvas, earth, view, theme, highlight_ids or {}, safe.s)
    else:
        draw_atmosphere(canvas, view, theme)
        draw_highlight_stroke(canvas, earth, view, theme, highlight_ids or {}, t)
    # The line is drawn before the title is reserved, so it can pass behind the card.
    for vis in visuals:
        kind = vis.get("type")
        if kind == "latline":
            draw_parallel(canvas, safe, view, theme, t, float(vis["lat"]), "", t, draw_line=True, with_label=False)
        elif kind == "lonline":
            draw_meridian(canvas, safe, view, theme, float(vis["lon"]), "", t, draw_line=True, with_label=False)
        elif kind == "route":
            draw_route(canvas, safe, view, theme, vis, draw_line=True, with_label=False)
    _reserve_title(safe)
    if any(v.get("type") == "graticule" for v in visuals):
        draw_graticule(canvas, view, theme, t)
    for vis in visuals:
        kind = vis.get("type")
        if kind == "latline":
            draw_parallel(canvas, safe, view, theme, t, float(vis["lat"]), vis.get("label", ""), t,
                          draw_line=False, with_label=True)
            continue
        if kind == "lonline":
            draw_meridian(canvas, safe, view, theme, float(vis["lon"]), vis.get("label", ""), t,
                          draw_line=False, with_label=True)
            continue
        if kind in ("highlight", "graticule"):
            continue
        if kind == "marker":
            draw_marker(canvas, safe, view, theme, float(vis["lat"]), float(vis["lon"]),
                        str(vis.get("label", "")), t)
        elif kind == "route":
            draw_route(canvas, safe, view, theme, vis, draw_line=False, with_label=True)
        elif kind == "ruler":
            draw_ruler(canvas, safe, view, vis, local, t)
        elif kind == "bignum":
            _badge(safe, str(vis.get("text", "")), safe.w * 0.50, safe.h * 0.46, theme)
        elif kind == "ghost":
            draw_ghost(canvas, safe, earth, view, vis, local)
        elif kind == "island":
            draw_island(canvas, safe, vis, t)
    # Country stroke uses the same highlight ids the sampler did. Passed via visuals.
    draw_claim(safe, claim, sub, local)
    cap = draw_caption(safe, words, groups, t) if words else None
    return {"caption": cap, "spills": safe.spills, "overlaps": safe.overlaps}
