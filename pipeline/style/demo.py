"""Short clip of the kit components, plus a before/after still.

Before is the old static dark title card. After is the kit: bounce, drop,
a drawing line, one highlight pulse, a count-up, and a one-way drift.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import skia

from style.gold import (
    INK,
    LAND,
    NEON_RGB,
    OCEAN,
    PAPER,
    draw_counter,
    draw_motes,
    draw_pill,
    draw_sparkles,
    draw_stamp,
    draw_sweep,
    draw_tip,
    drift_field,
    face,
    grow,
    pin_pose,
    pop_scale,
    pulse_rgb,
    trim_polyline,
)


def _paint(r, g, b, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setColor(skia.ColorSetARGB(a, r, g, b))
    return p


def _frame(t: float, w: int, h: int, kit: bool) -> np.ndarray:
    s = w / 1080.0
    if kit:
        bg = np.empty((h, w, 3), np.uint8)
        bg[:] = OCEAN
        xs = np.linspace(40, w - 40, 18)
        ys = np.linspace(80, h * 0.3, 18)
        drift_field(bg, t, xs, ys)
    else:
        bg = np.empty((h, w, 3), np.uint8)
        bg[:] = (7, 16, 42)
    surface = skia.Surface(w, h)
    canvas = surface.getCanvas()
    canvas.drawImage(skia.Image.fromarray(np.dstack([bg, np.full((h, w), 255, np.uint8)])), 0, 0)

    local = t % 1.6
    # A fake country blob.
    blob = skia.Path()
    blob.moveTo(w * 0.22, h * 0.62)
    blob.quadTo(w * 0.40, h * 0.48, w * 0.62, h * 0.58)
    blob.quadTo(w * 0.78, h * 0.70, w * 0.55, h * 0.78)
    blob.quadTo(w * 0.30, h * 0.80, w * 0.22, h * 0.62)
    blob.close()
    if kit:
        rgb = pulse_rgb(NEON_RGB, local if t < 3.2 else 1.0)
        canvas.drawPath(blob, _paint(*rgb))
        draw_sweep(canvas, w, h, local if t < 4 else -1)
        draw_motes(canvas, w, h, t, s)
    else:
        canvas.drawPath(blob, _paint(*LAND))

    # Line.
    pts = [(w * 0.18, h * 0.70), (w * 0.40, h * 0.60), (w * 0.62, h * 0.66), (w * 0.84, h * 0.52)]
    if kit:
        part, tip = trim_polyline(pts, grow(min(t, 1.4), 1.1))
        path = skia.Path()
        path.moveTo(*part[0])
        for x, y in part[1:]:
            path.lineTo(x, y)
        stroke = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
        stroke.setStrokeWidth(8 * s)
        stroke.setColor(skia.ColorSetARGB(255, *NEON_RGB))
        canvas.drawPath(path, stroke)
        if tip and grow(min(t, 1.4), 1.1) < 0.99:
            draw_tip(canvas, tip[0], tip[1], s)
    else:
        path = skia.Path()
        path.moveTo(*pts[0])
        for x, y in pts[1:]:
            path.lineTo(x, y)
        stroke = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
        stroke.setStrokeWidth(6 * s)
        stroke.setColor(skia.ColorSetARGB(255, 228, 32, 72))
        canvas.drawPath(path, stroke)

    # Pin.
    px, py = w * 0.48, h * 0.64
    if kit:
        dy, sx, sy, ripples = pin_pose(min(t, 1.2), s)
        for frac, alpha in ripples:
            canvas.drawCircle(px, py, (14 + 54 * frac) * s, _stroke(NEON_RGB, 3 * s, int(170 * alpha)))
        canvas.save()
        canvas.translate(px, py + dy)
        canvas.scale(sx, sy)
        canvas.translate(-px, -py)
        canvas.drawCircle(px, py, 10 * s, _paint(*NEON_RGB))
        canvas.drawCircle(px, py, 4 * s, _paint(*PAPER))
        canvas.restore()
        draw_sparkles(canvas, px, py + dy, min(t, 1.0), s, seed=3)
        draw_pill(canvas, "MIDDLE ISLAND", px, py - 46 * s + dy, pop_scale(min(t, 0.8)), s)
    else:
        canvas.drawCircle(px, py, 8 * s, _paint(228, 32, 72))
        _dark_pill(canvas, "MIDDLE ISLAND", px, py - 40 * s, s)

    # Counter and stamp arrive later in the clip.
    if kit and t >= 2.4:
        draw_counter(canvas, w * 0.30, h * 0.30, 24, "km", t - 2.4, s)
    if kit and t >= 3.6:
        draw_stamp(canvas, w * 0.72, h * 0.30, t - 3.6, s, "X")

    # Title.
    if kit:
        _title(canvas, w, h, s, pop_scale(min(t, 0.5), punch=(t >= 4.4)))
    else:
        _dark_title(canvas, w, h, s)
    bgra = surface.makeImageSnapshot().toarray()
    return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])


def _stroke(color, width, alpha):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
    p.setStrokeWidth(width)
    p.setColor(skia.ColorSetARGB(alpha, *color))
    return p


def _dark_pill(canvas, text, x, y, s):
    f = skia.Font(face(), 36 * s)
    width = f.measureText(text)
    rect = skia.Rect.MakeLTRB(x - width / 2 - 16 * s, y - 28 * s, x + width / 2 + 16 * s, y + 18 * s)
    canvas.drawRRect(skia.RRect.MakeRectXY(rect, 18 * s, 18 * s), _paint(8, 10, 16, 220))
    canvas.drawString(text, x - width / 2, y, f, _paint(244, 247, 251))


def _dark_title(canvas, w, h, s):
    f = skia.Font(face(), 64 * s)
    text = "Further south"
    width = f.measureText(text)
    x, y = w / 2 - width / 2, 0.16 * h
    rect = skia.Rect.MakeLTRB(x - 24 * s, y - 70 * s, x + width + 24 * s, y + 24 * s)
    canvas.drawRRect(skia.RRect.MakeRectXY(rect, 16 * s, 16 * s), _paint(8, 10, 16, 220))
    canvas.drawString(text, x, y, f, _paint(244, 247, 251))


def _title(canvas, w, h, s, pop):
    f = skia.Font(face(), 72 * s * pop)
    a, b = "Further ", "south"
    wa = f.measureText(a)
    x = w / 2 - (wa + f.measureText(b)) / 2
    y = 0.18 * h
    shadow = _paint(0, 0, 0)
    canvas.drawString(a + b, x + 2 * s, y + 3 * s, f, shadow)
    canvas.drawString(a, x, y, f, _paint(248, 248, 248))
    canvas.drawString(b, x + wa, y, f, _paint(*NEON_RGB))


def render(out: Path, w: int = 1080, h: int = 1920) -> None:
    out.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.fromarray(_frame(1.1, w, h, kit=False)).save(out / "before.png")
    Image.fromarray(_frame(4.7, w, h, kit=True)).save(out / "after.png")
    n = 6 * 30
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
        "-r", "30", "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
        "-movflags", "+faststart",
        str(out / "components.mp4"),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(_frame(i / 30.0, w, h, kit=True).tobytes())
    proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"demo encode failed ({code})")
    print(out / "components.mp4")


if __name__ == "__main__":
    render(Path(__file__).resolve().parents[1] / "out" / "style")
