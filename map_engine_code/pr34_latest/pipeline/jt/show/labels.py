"""Pills and big numbers. Text stays out of the caption band.

The band is y 0.64–0.72. Captions are burned later, so this layer never
draws a glyph there. Square miles are the primary unit; square kilometres
are the line under them, at least 36px.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import skia
except ImportError:
    skia = None

FONT_BLACK = Path(__file__).resolve().parents[2] / "fonts" / "Montserrat-Black.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Karaoke is burned later, centered near y=1300, covering about 1150–1450.
BAND = (1150 / 1920, 1450 / 1920)
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

    def overlap_hits(self) -> int:
        """Pairs of pills whose boxes actually cross. Touching edges do not count."""
        return len(self.overlap_pairs())

    def overlap_pairs(self) -> list[tuple[str, str]]:
        pairs = []
        boxes = self.boxes
        names = [c[0] for c in self.caps] if len(self.caps) == len(boxes) else [str(i) for i in range(len(boxes))]
        for i in range(len(boxes)):
            a = boxes[i]
            for j in range(i + 1, len(boxes)):
                b = boxes[j]
                if a[2] <= b[0] + 0.5 or b[2] <= a[0] + 0.5:
                    continue
                if a[3] <= b[1] + 0.5 or b[3] <= a[1] + 0.5:
                    continue
                pairs.append((names[i], names[j]))
        return pairs

    def hits_rect(self, rect) -> bool:
        l, t, r, b = rect
        for box in self.boxes:
            if r <= box[0] + 0.5 or box[2] <= l + 0.5 or b <= box[1] + 0.5 or box[3] <= t + 0.5:
                continue
            return True
        return False

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
         size: float = 58, pop: float = 1.0, glow=None, kind: str = "",
         nudge: bool = True) -> tuple[float, float, float, float] | None:
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
    if nudge:
        cy = hud.dodge(cy, th)
    left = cx - tw / 2
    top = cy - th / 2
    # Keep it on the 9:16 frame.
    left = min(max(16, left), hud.w - tw - 16)
    top = min(max(16, top), hud.h - th - 16)
    rect = skia.Rect.MakeXYWH(left, top, tw, th)
    radius = th / 2
    shadow = skia.Paint(AntiAlias=True)
    shadow.setColor(skia.ColorSetARGB(46, 16, 18, 24))
    shadow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    hud.canvas.drawRRect(skia.RRect.MakeRectXY(rect.makeOffset(0, 6), radius, radius), shadow)
    if glow is not None:
        g = skia.Paint(AntiAlias=True)
        g.setColor(skia.ColorSetARGB(48, glow[0], glow[1], glow[2]))
        g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16))
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


def comparison_card(hud: Hud) -> None:
    """One 2-column card in the strip above the bottom safe zone, under the caption band."""
    w, h = hud.w, hud.h
    # The whole card stays above the caption band (bottom edge y <= 1150).
    bottom = 1144.0
    top = bottom - 156.0
    left, right = 24.0, w - 24.0
    rect = skia.Rect.MakeLTRB(left, top, right, bottom)
    body = skia.Paint(AntiAlias=True)
    body.setColor(skia.ColorSetARGB(228, 16, 18, 24))
    hud.canvas.drawRRect(skia.RRect.MakeRectXY(rect, 22, 22), body)
    rim = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2)
    rim.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    hud.canvas.drawRRect(skia.RRect.MakeRectXY(rect, 22, 22), rim)

    # The strip under the caption band and above the bottom 20% is 138px.
    # Names sit on the cap-40 line, miles just under that, km² at a 36px cap.
    name_font = _font("black", 42)
    sq_font = _font("black", 50)
    km_font = _font("black", 52)
    name_c = skia.Paint(AntiAlias=True)
    name_c.setColor(skia.ColorSetARGB(255, 244, 244, 246))
    sq_c = skia.Paint(AntiAlias=True)
    sq_c.setColor(skia.ColorSetARGB(255, 255, 214, 48))
    km_c = skia.Paint(AntiAlias=True)
    km_c.setColor(skia.ColorSetARGB(255, 210, 216, 224))
    columns = (
        (w * 0.27, "AFRICA", "11.73M SQ MI", "30.37M KM²"),
        (w * 0.73, "GREENLAND", "0.84M SQ MI", "2.17M KM²"),
    )
    base_name = top + 40
    base_sq = top + 88
    base_km = top + 134
    for cx, name, sq, km in columns:
        hud.canvas.drawString(name, cx - name_font.measureText(name) / 2, base_name, name_font, name_c)
        hud.canvas.drawString(sq, cx - sq_font.measureText(sq) / 2, base_sq, sq_font, sq_c)
        hud.canvas.drawString(km, cx - km_font.measureText(km) / 2, base_km, km_font, km_c)
    hud.boxes.append((left, top, right, bottom))
    hud.caps.append(("comparison-card", 36.4))


def leader_label(hud: Hud, canvas, name: str, sq: str, shape, avoid, fill,
                 prefer: str = "right", size: float = 44) -> tuple | None:
    """Two-line name + square miles, outside every shape and face, with a short leader."""
    if shape is None:
        return None
    font = _font("black", size)
    sub = _font("black", size - 2)
    tw = max(font.measureText(name), sub.measureText(sq)) + 28
    th = (size * 1.15) + ((size - 2) * 1.05) + 16
    sx0, sy0, sx1, sy1 = shape
    scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    gap = 18.0
    order = {
        "above": [(scx, sy0 - gap - th / 2), (sx0 + tw / 2, sy0 - gap - th / 2), (sx1 - tw / 2, sy0 - gap - th / 2)],
        "right": [(sx1 + gap + tw / 2, scy), (sx1 + gap + tw / 2, sy0 + th), (sx1 + gap + tw / 2, sy1 - th)],
        "left": [(sx0 - gap - tw / 2, scy), (sx0 - gap - tw / 2, sy1 - th / 2), (sx0 - gap - tw / 2, sy0 + th)],
        "below": [(scx, sy1 + gap + th / 2), (sx0 + tw / 2, sy1 + gap + th / 2), (sx1 - tw / 2, sy1 + gap + th / 2)],
    }.get(prefer, [])
    # A few frame-edge fallbacks that stay in the safe band.
    order = list(order) + [
        (hud.w * 0.78, SAFE_TOP * hud.h + th / 2 + 10),
        (hud.w * 0.22, SAFE_TOP * hud.h + th / 2 + 10),
        (hud.w * 0.5, BAND[0] * hud.h - th / 2 - 10),
    ]
    chosen = None
    for cx, cy in order:
        left = min(max(12.0, cx - tw / 2), hud.w - tw - 12.0)
        top = min(max(SAFE_TOP * hud.h + 4, cy - th / 2), BAND[0] * hud.h - th - 6)
        rect = (left, top, left + tw, top + th)
        if any(_hits_shape(rect, block) for block in avoid) or hud.hits_rect(rect):
            continue
        chosen = rect
        break
    if chosen is None:
        return None
    left, top, right, bot = chosen
    body = skia.Paint(AntiAlias=True)
    body.setColor(skia.ColorSetARGB(235, fill[0], fill[1], fill[2]))
    hud.canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(left, top, right, bot), 16, 16), body)
    ink = skia.Paint(AntiAlias=True)
    ink.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    sub_ink = skia.Paint(AntiAlias=True)
    sub_ink.setColor(skia.ColorSetARGB(255, 255, 236, 140))
    hud.canvas.drawString(name, left + 14, top + 8 - font.getMetrics().fAscent, font, ink)
    hud.canvas.drawString(sq, left + 14, top + size + 10 - sub.getMetrics().fAscent, sub, sub_ink)
    hud.boxes.append(chosen)
    hud.caps.append((name, 0.70 * size))
    pcx, pcy = (left + right) / 2, (top + bot) / 2
    if abs(pcx - scx) >= abs(pcy - scy):
        tx = sx1 if pcx >= scx else sx0
        ty = min(max(pcy, sy0 + 8), sy1 - 8)
        x0 = right if pcx < scx else left
        y0 = pcy
    else:
        tx = min(max(pcx, sx0 + 8), sx1 - 8)
        ty = sy1 if pcy >= scy else sy0
        x0 = pcx
        y0 = bot if pcy < scy else top
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(230, 255, 255, 255))
    canvas.drawLine(x0, y0, tx, ty, pen)
    return chosen


def _hits_shape(rect, shape) -> bool:
    l, t, r, b = rect
    sl, st, sr, sb = shape
    return not (r <= sl or sr <= l or b <= st or sb <= t)


def _draw_pill_box(hud, text, left, top, tw, th, font, fill, ink, size, kind):
    rect = skia.Rect.MakeXYWH(left, top, tw, th)
    body = skia.Paint(AntiAlias=True)
    body.setColor(skia.ColorSetARGB(235, fill[0], fill[1], fill[2]))
    hud.canvas.drawRRect(skia.RRect.MakeRectXY(rect, th / 2, th / 2), body)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(255, ink[0], ink[1], ink[2]))
    metrics = font.getMetrics()
    hud.canvas.drawString(text, left + 16, top + 8 - metrics.fAscent, font, paint)
    hud.boxes.append((left, top, left + tw, top + th))
    hud.caps.append((kind or text, 0.70 * size))


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
    if rect is None or pop <= 0 or skia is None:
        return
    l, t, r, b = rect
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8 * pop)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setColor(skia.ColorSetARGB(int(230 * pop), 226, 40, 64))
    canvas.drawLine(l + 8, t + 8, r - 8, b - 8, pen)
    canvas.drawLine(l + 8, b - 8, r - 8, t + 8, pen)


# High-contrast pills. Background and text fade as one layer, so a white
# theme never flashes white text and a red theme never fades toward white.
PILL_THEMES: Dict[str, Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]] = {
    "red": ((212, 38, 42, 248), (255, 255, 255, 255)),
    "dark": ((16, 22, 34, 245), (255, 255, 255, 255)),
    "blue": ((14, 116, 218, 248), (255, 255, 255, 255)),
    "yellow": ((245, 197, 24, 250), (14, 18, 26, 255)),
    "white": ((248, 250, 252, 250), (14, 18, 26, 255)),
}


@dataclass(frozen=True)
class MapLabelItem:
    text: str
    lon: float
    lat: float
    enter_t: float
    exit_t: float
    color_rgba: Tuple[int, int, int, int] = (255, 255, 255, 255)
    font_size: float = 38.0


@dataclass(frozen=True)
class PillBannerItem:
    text: str
    screen_x: float
    screen_y: float
    enter_t: float
    exit_t: float
    theme: str = "dark"


def resolve_2d_label_collisions(
    boxes: List[Tuple[float, float, float, float]],
    min_gap_px: float = 14.0,
    iterations: int = 12,
) -> List[Tuple[float, float]]:
    """Push overlapping label boxes apart. Returns adjusted centers."""
    centers = [[float(b[0]), float(b[1])] for b in boxes]
    sizes = [(float(b[2]), float(b[3])) for b in boxes]
    count = len(boxes)
    for _ in range(iterations):
        moved = False
        for i in range(count):
            for j in range(i + 1, count):
                dx = centers[j][0] - centers[i][0]
                dy = centers[j][1] - centers[i][1]
                overlap_x = (sizes[i][0] + sizes[j][0]) * 0.5 + min_gap_px - abs(dx)
                overlap_y = (sizes[i][1] + sizes[j][1]) * 0.5 + min_gap_px - abs(dy)
                if overlap_x > 0.0 and overlap_y > 0.0:
                    moved = True
                    if overlap_y <= overlap_x * 1.4:
                        sign_y = 1.0 if dy >= 0.0 else -1.0
                        shift = 0.52 * overlap_y * sign_y
                        centers[i][1] -= shift
                        centers[j][1] += shift
                    else:
                        sign_x = 1.0 if dx >= 0.0 else -1.0
                        shift = 0.52 * overlap_x * sign_x
                        centers[i][0] -= shift
                        centers[j][0] += shift
        if not moved:
            break
    return [
        (max(110.0, min(880.0, c[0])), max(250.0, min(1200.0, c[1])))
        for c in centers
    ]


def draw_pill_banner(canvas, pill_item: PillBannerItem, t: float) -> None:
    """Rounded pill on one alpha layer so the fill and the ink fade together."""
    if skia is None:
        return
    from .vfx_core import element_fade_and_exit_offset, label_pop_state

    alpha, dx, dy = element_fade_and_exit_offset(
        t, pill_item.enter_t, pill_item.exit_t, fade_in_s=0.30, fade_out_s=0.32
    )
    if alpha <= 0.01:
        return
    pop_scale, _ = label_pop_state(t - pill_item.enter_t, duration_s=0.30)
    bg_rgba, fg_rgba = PILL_THEMES.get(pill_item.theme, PILL_THEMES["dark"])
    typeface = skia.Typeface.MakeFromName("Inter", skia.FontStyle.Bold())
    font = skia.Font(typeface, 40.0)
    text_w = font.measureText(pill_item.text)
    pad_x, pad_y = 28.0, 18.0
    box_w = text_w + 2.0 * pad_x
    box_h = 40.0 + 2.0 * pad_y
    cx = max(80.0 + box_w * 0.5, min(890.0 - box_w * 0.5, pill_item.screen_x + dx))
    cy = max(245.0 + box_h * 0.5, min(1210.0 - box_h * 0.5, pill_item.screen_y + dy))
    canvas.save()
    canvas.saveLayerAlphaf(None, float(alpha))
    canvas.translate(cx, cy)
    canvas.scale(pop_scale, pop_scale)
    rect = skia.Rect.MakeLTRB(-box_w * 0.5, -box_h * 0.5, box_w * 0.5, box_h * 0.5)
    bg_paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style, Color=skia.Color(*bg_rgba))
    border_paint = skia.Paint(
        AntiAlias=True,
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=3.0,
        Color=skia.Color(255, 255, 255, 55),
    )
    canvas.drawRoundRect(rect, 18.0, 18.0, bg_paint)
    canvas.drawRoundRect(rect, 18.0, 18.0, border_paint)
    fg_paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style, Color=skia.Color(*fg_rgba))
    canvas.drawSimpleText(pill_item.text, -text_w * 0.5, 14.0, font, fg_paint)
    canvas.restore()
    canvas.restore()
