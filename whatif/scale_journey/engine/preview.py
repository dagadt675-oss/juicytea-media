"""Fast schematic plates so the UI and the zoom can be checked without Blender."""

from __future__ import annotations

from PIL import Image, ImageDraw

from .camera import Pose, project
from .spec import Episode, Frame


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def plate(ep: Episode, fr: Frame) -> Image.Image:
    w, h = ep.width, ep.height
    dom = max(fr.weights, key=fr.weights.get)
    skies = {
        "interior": ((92, 64, 48), (210, 164, 120)),
        "city": ((244, 156, 98), (88, 64, 120)),
        "aerial": ((186, 206, 214), (64, 104, 148)),
        "orbit": ((6, 8, 16), (16, 22, 40)),
        "room": ((120, 96, 80), (196, 168, 140)),
    }
    top, bot = skies.get(dom, ((20, 22, 36), (8, 8, 14)))
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        # Horizon sits a little below centre.
        u = min(1.0, max(0.0, (t - 0.35) / 0.65))
        c = _lerp(top, bot, u)
        for x in range(0, w, 2):
            px[x, y] = c
            if x + 1 < w:
                px[x + 1, y] = c
    draw = ImageDraw.Draw(img, "RGBA")
    cam = ep.raw["camera"]
    pose = Pose(fr.pose_cam, fr.pose_target, fr.distance_m, fr.pitch_deg)

    def P(pt):
        return project(pose, pt, w, h, float(cam["lens_mm"]), float(cam["sensor_height_mm"]))

    # Ground disc.
    ground = []
    rad = max(fr.metrics.radius_m * 6.0, fr.distance_m * 2.0)
    for i in range(24):
        import math
        a = i / 24 * math.tau
        pt = P((rad * math.cos(a), rad * math.sin(a), 0.0))
        if pt:
            ground.append(pt)
    if len(ground) >= 3:
        draw.polygon(ground, fill=(70, 62, 56, 255))
    # Subject.
    hh = fr.metrics.height_m
    rr = fr.metrics.radius_m
    tip = P((0.0, 0.0, hh))
    left = P((-rr, 0.0, 0.0))
    right = P((rr, 0.0, 0.0))
    if tip and left and right:
        draw.polygon([left, tip, right], fill=(232, 206, 150, 255))
    for item in fr.labels:
        top = item["anchor_m"]
        base = (top[0], top[1], 0.0)
        a = P(base)
        b = P(top)
        if a and b:
            draw.line((a, b), fill=(236, 232, 228, 255), width=3)
            draw.ellipse((b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4), fill=(255, 120, 60, 255))
    return img
