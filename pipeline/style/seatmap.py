"""Top-down A320 seat map, drawn with the same pills and neon as the map kit.

The fuselage fills most of the frame height. Wings stay inside the frame, so
they are a little shorter than a strict metre scale. Tail, stabilizers, and
the 3+3 cabin keep the narrow-body plan.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import skia

from style.gold import INK, NEON_RGB, OCEAN, PAPER, draw_pill, font, pop_scale


def render_seatmap(path: str | Path, w: int = 1080, h: int = 1920) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    surface = skia.Surface(w, h)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorSetARGB(255, OCEAN[0], OCEAN[1], OCEAN[2]))

    cx = w / 2
    nose = 0.07 * h
    tail = 0.92 * h
    length = tail - nose
    fuse_w = 210.0
    s = w / 1080.0

    def paint(r, g, b, a=255):
        p = skia.Paint(AntiAlias=True)
        p.setColor(skia.ColorSetARGB(a, r, g, b))
        return p

    body = paint(226, 230, 236)
    edge = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
    edge.setStrokeWidth(3 * s)
    edge.setColor(skia.ColorSetARGB(255, 30, 36, 48))
    shade = paint(186, 194, 206)

    # Wings, under the fuselage so the body reads on top.
    wing_y = nose + length * 0.46

    def wing(sign):
        path = skia.Path()
        path.moveTo(cx + sign * fuse_w * 0.42, wing_y - 20 * s)
        path.lineTo(cx + sign * 500 * s, wing_y + 70 * s)
        path.lineTo(cx + sign * 470 * s, wing_y + 150 * s)
        path.lineTo(cx + sign * fuse_w * 0.2, wing_y + 120 * s)
        path.close()
        canvas.drawPath(path, shade)

    wing(-1)
    wing(1)

    # Engines.
    for side in (-1, 1):
        ex = cx + side * 250 * s
        ey = wing_y + 40 * s
        canvas.drawOval(skia.Rect.MakeXYWH(ex - 28 * s, ey, 56 * s, 90 * s), paint(70, 78, 90))
        canvas.drawOval(skia.Rect.MakeXYWH(ex - 16 * s, ey + 8 * s, 32 * s, 70 * s), paint(40, 46, 56))

    # Horizontal stabilizers.
    stab_y = nose + length * 0.86

    def stab(sign):
        path = skia.Path()
        path.moveTo(cx + sign * fuse_w * 0.28, stab_y)
        path.lineTo(cx + sign * 210 * s, stab_y + 36 * s)
        path.lineTo(cx + sign * 180 * s, stab_y + 78 * s)
        path.lineTo(cx + sign * fuse_w * 0.1, stab_y + 48 * s)
        path.close()
        canvas.drawPath(path, shade)

    stab(-1)
    stab(1)

    # Fuselage: nose semicircle, straight cabin, tapered tail.
    fuse = skia.Path()
    fuse.moveTo(cx - fuse_w / 2, nose + 70 * s)
    fuse.arcTo(skia.Rect.MakeLTRB(cx - fuse_w / 2, nose, cx + fuse_w / 2, nose + 150 * s), 180, 180, False)
    fuse.lineTo(cx + fuse_w / 2, nose + length * 0.78)
    fuse.lineTo(cx + 18 * s, tail)
    fuse.lineTo(cx - 18 * s, tail)
    fuse.lineTo(cx - fuse_w / 2, nose + length * 0.78)
    fuse.close()
    canvas.drawPath(fuse, body)
    canvas.drawPath(fuse, edge)

    # Vertical stabilizer as the centerline fin you see from above.
    fin = skia.Path()
    fin.moveTo(cx - 8 * s, nose + length * 0.78)
    fin.lineTo(cx + 8 * s, nose + length * 0.78)
    fin.lineTo(cx + 5 * s, tail - 10 * s)
    fin.lineTo(cx - 5 * s, tail - 10 * s)
    fin.close()
    canvas.drawPath(fin, paint(90, 98, 112))

    # Cockpit glazing.
    canvas.drawOval(
        skia.Rect.MakeLTRB(cx - 36 * s, nose + 28 * s, cx + 36 * s, nose + 78 * s),
        paint(120, 168, 196),
    )

    # Cabin seats, nose at the top, so the backrest is the lower cap of each seat.
    cabin_top = nose + length * 0.16
    cabin_bot = nose + length * 0.76
    rows = 28
    row_h = (cabin_bot - cabin_top) / rows
    seat_w, seat_h = 26 * s, row_h * 0.72
    aisle = 22 * s
    gap = 4 * s
    block = 3 * seat_w + 2 * gap
    left0 = cx - aisle / 2 - block
    right0 = cx + aisle / 2
    exit_rows = {11, 12}
    front_rows = set(range(0, 5))

    def seat(x, y, hot):
        rect = skia.Rect.MakeXYWH(x, y, seat_w, seat_h)
        canvas.drawRRect(skia.RRect.MakeRectXY(rect, 5 * s, 5 * s), paint(*(NEON_RGB if hot else (64, 74, 92))))
        back = skia.Rect.MakeXYWH(x + 2 * s, y + seat_h * 0.62, seat_w - 4 * s, seat_h * 0.30)
        canvas.drawRRect(skia.RRect.MakeRectXY(back, 3 * s, 3 * s), paint(20, 24, 32))

    for r in range(rows):
        y = cabin_top + r * row_h + (row_h - seat_h) / 2
        hot = r in exit_rows or r in front_rows
        for side in (left0, right0):
            for k in range(3):
                seat(side + k * (seat_w + gap), y, hot)

    # Section brackets.
    def bracket(y0, y1, label, px):
        tick = paint(*NEON_RGB)
        canvas.drawRect(skia.Rect.MakeLTRB(cx + fuse_w / 2 + 16 * s, y0, cx + fuse_w / 2 + 22 * s, y1), tick)
        draw_pill(canvas, label, px, (y0 + y1) / 2, pop_scale(0.2), s)

    bracket(cabin_top, cabin_top + 5 * row_h, "FRONT", cx + 250 * s)
    bracket(cabin_top + 11 * row_h, cabin_top + 13 * row_h, "EXIT", cx - 250 * s)

    title = font(54 * s)
    canvas.drawString("Which seat?", 64 * s, 0.045 * h, title, paint(*PAPER))
    sub = font(28 * s)
    canvas.drawString("A320  ·  3 + 3", 64 * s, 0.045 * h + 40 * s, sub, paint(186, 198, 214))

    image = surface.makeImageSnapshot()
    image.save(str(path), skia.EncodedImageFormat.kPNG)
    # Confirm the aircraft really fills the frame.
    return {"nose": nose / h, "tail": tail / h, "height_frac": length / h}


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / "style" / "seatmap.png"
    info = render_seatmap(out)
    print(out, info)
