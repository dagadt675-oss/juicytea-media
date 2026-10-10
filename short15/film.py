"""Ray-cast football Earth.

The ball is an ellipsoid. Geographic albedo comes from a Natural Earth raster;
leather, laces and stripes are procedural and stuck to the same surface.
Santa, the cabin and the person who sits down are shaded ellipsoids in the
same light, so they sit in the shot instead of reading as flat clipart.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from short15.tex import textures

W, H = 1080, 1920
# Karaoke is composited later. This strip stays a clean plate.
BAND0 = int(round(0.64 * H))
BAND1 = int(round(0.72 * H))
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SAFE_TOP = 236
SAFE_BOT = 1524
SAFE_RIGHT = 900
SAFE_LEFT = 40

WHITE = (255, 255, 255)
GOLD = (255, 186, 38)
RED = (255, 48, 58)
CYAN = (130, 214, 255)
GREEN = (198, 255, 90)


@dataclass
class Cam:
    origin: np.ndarray
    forward: np.ndarray
    right: np.ndarray
    up: np.ndarray
    tan_y: float
    aspect: float


def make_camera() -> Cam:
    origin = np.array([0.0, 0.42, 5.55], np.float32)
    target = np.array([0.0, -0.08, 0.0], np.float32)
    forward = target - origin
    forward /= np.linalg.norm(forward)
    world_up = np.array([0.0, 1.0, 0.0], np.float32)
    right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    up /= np.linalg.norm(up)
    return Cam(origin, forward.astype(np.float32), right.astype(np.float32),
               up.astype(np.float32), tan_y=math.tan(math.radians(15.2)), aspect=W / H)


def ray_dirs(cam: Cam) -> np.ndarray:
    ys, xs = np.mgrid[0:H, 0:W]
    ndc_x = ((xs + 0.5) / W * 2 - 1) * cam.tan_y * cam.aspect
    ndc_y = (1 - (ys + 0.5) / H * 2) * cam.tan_y
    dirs = (cam.forward + ndc_x[..., None] * cam.right + ndc_y[..., None] * cam.up).astype(np.float32)
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True) + 1e-8
    return dirs


def _rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)


def _rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)


def project(cam: Cam, p: np.ndarray) -> tuple[float, float, float]:
    d = p - cam.origin
    z = float(np.dot(d, cam.forward))
    x = float(np.dot(d, cam.right)) / max(z, 1e-4)
    y = float(np.dot(d, cam.up)) / max(z, 1e-4)
    sx = (x / (cam.tan_y * cam.aspect) + 1) * 0.5 * W
    sy = (1 - (y / cam.tan_y + 1) * 0.5) * H
    return sx, sy, z


def trace(origin, dirs, center, radii, R):
    """Ray/ellipsoid. dirs is (..., 3). Returns t, n_world, p_obj, hit."""
    rt = R.T
    o = (rt @ (origin - center).astype(np.float32)) / radii
    d = np.einsum("...i,ij->...j", dirs, R) / radii
    a = np.sum(d * d, axis=-1)
    b = 2.0 * np.sum(d * o, axis=-1)
    c = float(np.dot(o, o) - 1.0)
    disc = b * b - 4.0 * a * c
    hit = disc > 1e-6
    sqrt = np.sqrt(np.maximum(disc, 0.0))
    inv = 1.0 / (2.0 * a + 1e-8)
    t = (-b - sqrt) * inv
    t2 = (-b + sqrt) * inv
    t = np.where(t > 1e-3, t, t2)
    hit = hit & (t > 1e-3)
    p_obj = (o + d * t[..., None]) * radii
    n_obj = p_obj / (radii ** 2)
    n_w = np.einsum("...i,ij->...j", n_obj, rt)
    n_w /= np.linalg.norm(n_w, axis=-1, keepdims=True) + 1e-8
    return t.astype(np.float32), n_w.astype(np.float32), p_obj.astype(np.float32), hit


def _bilinear(tex: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    h, w = tex.shape[:2]
    x = np.mod(u, 1.0) * (w - 1)
    y = np.clip(v, 0.0, 1.0) * (h - 1)
    x0 = np.floor(x).astype(np.int32) % w
    y0 = np.floor(y).astype(np.int32)
    x1 = (x0 + 1) % w
    y1 = np.minimum(y0 + 1, h - 1)
    fx = (x - np.floor(x)).astype(np.float32)[..., None]
    fy = (y - np.floor(y)).astype(np.float32)[..., None]
    c00 = tex[y0, x0]
    c10 = tex[y0, x1]
    c01 = tex[y1, x0]
    c11 = tex[y1, x1]
    return c00 * (1 - fx) * (1 - fy) + c10 * fx * (1 - fy) + c01 * (1 - fx) * fy + c11 * fx * fy


def _sample_mask(mask: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    x = (np.mod(u, 1.0) * (w - 1)).astype(np.int32)
    y = (np.clip(v, 0.0, 1.0) * (h - 1)).astype(np.int32)
    return mask[y, x]


class Scene:
    def __init__(self):
        self.cam = make_camera()
        self.dirs = ray_dirs(self.cam)
        self.tex = textures()
        self.font_cache: dict[int, ImageFont.FreeTypeFont] = {}
        rng = np.random.default_rng(4)
        self.star_x = rng.integers(0, W - 2, 220)
        self.star_y = rng.integers(0, H - 2, 220)
        self.star_p = rng.random(220).astype(np.float32)
        self.star_s = (0.35 + 0.65 * rng.random(220)).astype(np.float32)
        ys = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        top = np.array([6, 10, 22], np.float32)
        bot = np.array([3, 5, 12], np.float32)
        self.bg = (top * (1 - ys) + bot * ys).astype(np.float32)
        nx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
        ny = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
        r = np.sqrt(nx ** 2 * 0.55 + ny ** 2 * 0.85)
        self.vig = np.clip(1 - 0.45 * np.clip(r - 0.45, 0, 1) ** 2, 0.55, 1).astype(np.float32)

    def font(self, px: int) -> ImageFont.FreeTypeFont:
        px = int(px)
        if px not in self.font_cache:
            self.font_cache[px] = ImageFont.truetype(FONT_PATH, px)
        return self.font_cache[px]


def _norm_tok(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalpha())


def find_word(words: list[dict], text: str, nth: int = 0) -> dict:
    key = _norm_tok(text)
    n = 0
    for w in words:
        if _norm_tok(w["text"]) == key:
            if n == nth:
                return w
            n += 1
    raise KeyError(text)


def marks_from(words: list[dict], duration: float) -> dict:
    def s(token, nth=0):
        return float(find_word(words, token, nth)["start"])

    def e(token, nth=0):
        return float(find_word(words, token, nth)["end"])

    on_end = e("on.")
    hold_end = max(on_end + 0.65, s("sat") + 0.85)
    # Leave a real return to the opening pose so the loop is the football, not the sit.
    hold_end = min(hold_end, duration - 0.85)
    if hold_end - s("sat") < 0.60:
        hold_end = s("sat") + 0.60
    return {
        "snap": 0.97,
        "football_end": e("football."),
        "the": s("The"),
        "sorry": s("Sorry,"),
        "santa_end": e("Santa."),
        "your": s("Your"),
        "workshop_end": e("space.", 1),
        "oceans": s("Oceans?"),
        "slide_end": e("slide."),
        "plot": s("Plot"),
        "already_end": e("already"),
        "forty": s("forty-three"),
        "tall_end": e("tall."),
        "its": s("It's"),
        "someone": s("someone"),
        "sat": s("sat"),
        "on_end": on_end,
        "hold_end": hold_end,
        "duration": duration,
    }


def _smooth(a: float, b: float, u: float) -> float:
    u = max(0.0, min(1.0, u))
    u = u * u * (3 - 2 * u)
    return a + (b - a) * u


def _lerp_dict(a: dict, b: dict, u: float) -> dict:
    return {k: _smooth(a[k], b[k], u) for k in a}


def _pose_at(t: float, m: dict) -> dict:
    """Numeric pose. Caption mode is chosen separately so it can cut."""
    T = m["duration"]
    # (time, elong, leather, tilt_deg, cy, scale, slide, squash, santa, sitter)
    keys = [
        (0.00, 1.50, 0.18, 18, -0.55, 1.08, 0.0, 0.0, 0.0, 0.0),
        (m["snap"] - 0.06, 1.50, 0.18, 18, -0.55, 1.08, 0.0, 0.0, 0.0, 0.0),
        (m["snap"] + 0.08, 1.52, 1.00, 20, -0.48, 1.12, 0.0, 0.0, 0.0, 0.0),
        (m["the"] - 0.05, 1.50, 0.95, 24, -0.42, 1.06, 0.0, 0.0, 0.0, 0.0),
        (m["sorry"] - 0.15, 1.55, 0.72, 50, -0.15, 1.18, 0.0, 0.0, 1.0, 0.0),
        (m["workshop_end"], 1.52, 0.55, 48, -0.10, 1.16, 0.0, 0.0, 1.0, 0.0),
        (m["oceans"] - 0.08, 1.42, 0.12, 16, -0.48, 1.12, 0.05, 0.0, 0.0, 0.0),
        (m["oceans"] + 0.25, 1.36, 0.05, 14, -0.50, 1.14, 0.45, 0.0, 0.0, 0.0),
        (m["slide_end"], 1.28, 0.0, 12, -0.50, 1.12, 1.0, 0.0, 0.0, 0.0),
        (m["plot"], 1.08, 0.0, 10, -0.52, 1.08, 0.25, 0.0, 0.0, 0.0),
        (m["forty"] - 0.05, 0.72, 0.0, 8, -0.50, 1.10, 0.0, 0.0, 0.0, 0.0),
        (m["tall_end"], 0.62, 0.0, 8, -0.50, 1.12, 0.0, 0.0, 0.0, 0.0),
        (m["its"], 1.05, 0.15, 12, -0.48, 1.08, 0.0, 0.0, 0.0, 0.0),
        (m["someone"] - 0.05, 1.20, 0.35, 14, -0.35, 1.02, 0.0, 0.0, 0.0, 0.15),
        (m["sat"], 1.05, 0.45, 14, -0.32, 1.02, 0.0, 0.15, 0.0, 0.72),
        (m["on_end"], 0.92, 0.5, 14, -0.30, 1.00, 0.0, 0.85, 0.0, 1.0),
        (m["hold_end"], 0.90, 0.48, 14, -0.30, 1.00, 0.0, 0.70, 0.0, 1.0),
        (T - 0.35, 1.50, 0.18, 18, -0.55, 1.08, 0.0, 0.0, 0.0, 0.0),
        (T, 1.50, 0.18, 18, -0.55, 1.08, 0.0, 0.0, 0.0, 0.0),
    ]
    keys.sort(key=lambda k: k[0])
    names = ["elong", "leather", "tilt", "cy", "scale", "slide", "squash", "santa", "sitter"]
    if t <= keys[0][0]:
        vals = keys[0][1:]
    elif t >= keys[-1][0]:
        vals = keys[-1][1:]
    else:
        for (t0, *v0), (t1, *v1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / max(1e-4, t1 - t0)
                vals = [_smooth(a, b, u) for a, b in zip(v0, v1)]
                break
        else:
            vals = keys[-1][1:]
    pose = dict(zip(names, vals))
    # Sit bounce keeps the hold alive.
    if m["sat"] <= t <= m["hold_end"]:
        age = t - m["sat"]
        pose["squash"] = float(np.clip(pose["squash"] + 0.07 * math.sin(age * 8.5) * math.exp(-age * 1.2), 0, 1.2))
        pose["cy"] = pose["cy"] + 0.015 * math.sin(age * 6.0)
    return pose


def caption_mode(t: float, m: dict) -> str:
    T = m["duration"]
    if t < m["football_end"] + 0.12 or t >= m["hold_end"]:
        return "hook"
    if m["sorry"] - 0.08 <= t < m["your"] - 0.04:
        return "santa"
    if m["oceans"] - 0.06 <= t < m["slide_end"] + 0.08:
        return "oceans"
    if m["plot"] - 0.05 <= t < m["forty"] - 0.06:
        return "twist"
    if m["forty"] - 0.06 <= t < m["tall_end"] + 0.1:
        return "fatter"
    if m["sat"] - 0.08 <= t < m["hold_end"]:
        return "sat"
    return "karaoke"


def _groups(words: list[dict]) -> list[list[int]]:
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        tok = w["text"]
        if tok.endswith((".", "?", "!", ",", ";", ":")) or len(cur) >= 3:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _active(words: list[dict], t: float) -> int | None:
    idx = None
    for i, w in enumerate(words):
        if t + 0.04 >= w["start"]:
            idx = i
        else:
            break
    if idx is None:
        return None
    end = words[idx]["end"]
    nxt = words[idx + 1]["start"] if idx + 1 < len(words) else 1e9
    if t > end + 0.28 and t + 0.04 < nxt:
        return None
    return idx


def _draw_lines(scene: Scene, img: np.ndarray, lines: list[list[tuple[str, tuple]]], px: int, top: int) -> tuple[int, int, int, int]:
    """Centered block. Returns x0,y0,x1,y1 of the ink, clipped into the safe rect."""
    # Shrink until every line fits the safe width.
    while px >= 48:
        font = scene.font(px)
        widths = []
        for line in lines:
            text = " ".join(tok for tok, _ in line)
            widths.append(font.getlength(text))
        stroke_try = max(4, px // 9)
        if max(widths) + 2 * stroke_try <= (SAFE_RIGHT - SAFE_LEFT - 16):
            break
        px -= 2
    font = scene.font(px)
    stroke = max(4, px // 9)
    gap = int(px * 0.18)
    heights = []
    for line in lines:
        text = " ".join(tok for tok, _ in line)
        bbox = font.getbbox(text, stroke_width=stroke)
        heights.append(bbox[3] - bbox[1])
    # Width from the glyphs we actually draw, not a second measurement that
    # includes a trailing space.
    widths = []
    space_w = font.getlength(" ")
    for line in lines:
        widths.append(sum(font.getlength(tok) for tok, _ in line) + space_w * (len(line) - 1))
    block_w = max(widths)
    block_h = sum(heights) + gap * (len(lines) - 1)
    # Prefer frame center, then shove left so the stroke stays inside x <= 900.
    left = W / 2 - block_w / 2
    if left + block_w + stroke > SAFE_RIGHT:
        left = SAFE_RIGHT - stroke - block_w
    if left < SAFE_LEFT + stroke:
        left = SAFE_LEFT + stroke
    top = int(np.clip(top, SAFE_TOP + stroke + 2, SAFE_BOT - block_h - stroke - 2))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    y = top
    ink = []
    for line, h_line in zip(lines, heights):
        widths_tok = [font.getlength(tok) for tok, _ in line]
        space = font.getlength(" ")
        line_w = sum(widths_tok) + space * (len(line) - 1)
        x = left + (block_w - line_w) / 2
        for (tok, col), tw in zip(line, widths_tok):
            draw.text((x, y), tok, font=font, fill=col + (255,),
                      stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
            ink.append((x - stroke, y - stroke, x + tw + stroke, y + h_line + stroke))
            x += tw + space
        y += h_line + gap
    rgba = np.asarray(overlay, np.float32)
    a = rgba[:, :, 3:4] / 255.0
    base = img.astype(np.float32)
    comp = base * (1 - a) + rgba[:, :, :3] * a
    img[:] = np.clip(comp, 0, 255).astype(np.uint8)
    xs0 = min(r[0] for r in ink)
    ys0 = min(r[1] for r in ink)
    xs1 = max(r[2] for r in ink)
    ys1 = max(r[3] for r in ink)
    return int(xs0), int(ys0), int(xs1), int(ys1), rgba[:, :, 3] > 20


def _hook_lines(words, active) -> list[list[tuple[str, tuple]]]:
    """Three-line claim. AMERICAN and FOOTBALL stay gold; the spoken word burns hotter."""
    idxs = [[0, 1, 2], [3, 4, 5], [6]]
    always_gold = {"american", "football"}
    lines = []
    for group in idxs:
        line = []
        for i in group:
            tok = words[i]["text"].upper().rstrip(".")
            if i == 6:
                tok = "FOOTBALL"
            key = _norm_tok(words[i]["text"])
            if i == active:
                col = (255, 214, 80)
            elif key in always_gold:
                col = GOLD
            else:
                col = WHITE
            line.append((tok, col))
        lines.append(line)
    return lines


def _karaoke_lines(words, idxs, active, palette=None) -> list[list[tuple[str, tuple]]]:
    line = []
    for i in idxs:
        tok = words[i]["text"].upper()
        if palette and i in palette:
            col = palette[i]
        else:
            col = (255, 214, 80) if i == active else WHITE
        if i == active and palette and i in palette:
            col = tuple(min(255, c + 30) for c in palette[i])
        line.append((tok, col))
    return [line]


def paint_captions(scene: Scene, img: np.ndarray, words, groups, t: float, m: dict, globe_top: int) -> dict:
    mode = caption_mode(t, m)
    # Closing frames show the identical claim as t = 0, including the "I" highlight,
    # so the loop seam is the opening card.
    if t >= m["hold_end"]:
        t_cap = 0.0
        mode = "hook"
    else:
        t_cap = t
    active = _active(words, t_cap)
    top = SAFE_TOP + 8
    # Keep the block above the ball when the ball is high, but never in the unsafe top.
    ceiling = max(SAFE_TOP + 8, min(globe_top - 24, 760))
    info = {"mode": mode, "box": None}
    if mode == "hook":
        lines = _hook_lines(words, active if active is not None and active <= 6 else 0)
        box = _draw_lines(scene, img, lines, 86, top)
    elif mode == "santa":
        lines = [
            [("SORRY,", WHITE)],
            [("SANTA.", RED)],
        ]
        box = _draw_lines(scene, img, lines, 118, top)
    elif mode == "oceans":
        # Two beats, one at a time: the question, then the verb.
        if t < find_word(words, "They")["start"] - 0.04:
            lines = [[("OCEANS?", CYAN)]]
            px = 120
        else:
            lines = _karaoke_lines(words, [words.index(find_word(words, "They")),
                                           words.index(find_word(words, "slide."))], active)
            px = 100
        box = _draw_lines(scene, img, lines, px, top)
    elif mode == "twist":
        if t < find_word(words, "Earth", 1)["start"] - 0.04:
            lines = [[("PLOT", WHITE), ("TWIST:", GOLD)]]
        else:
            lines = [[("EARTH", WHITE), ("IS", WHITE), ("ALREADY", GOLD)]]
        box = _draw_lines(scene, img, lines, 84, top)
    elif mode == "fatter":
        if t < find_word(words, "fatter")["start"] - 0.04:
            lines = [
                [("FORTY-THREE", GOLD)],
                [("KILOMETERS", WHITE)],
            ]
            px = 92
        else:
            lines = [
                [("FATTER", CYAN)],
                [("THAN IT IS TALL.", GREEN)],
            ]
            px = 100
        box = _draw_lines(scene, img, lines, px, min(top, ceiling))
    elif mode == "sat":
        lines = [[("SAT", RED), ("ON.", RED)]]
        box = _draw_lines(scene, img, lines, 168, top)
    else:
        if active is None:
            # Hold the most recent group briefly; _active already does. If nothing, skip.
            return info
        group = next(g for g in groups if active in g)
        lines = _karaoke_lines(words, group, active)
        box = _draw_lines(scene, img, lines, 78, top)
    _x0, _y0, _x1, _y1, mask = box
    ys, xs = np.where(mask)
    if len(xs) == 0:
        info["box"] = None
        return info
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    info["box"] = (x0, y0, x1, y1)
    info["mask"] = mask
    info["px_note"] = y1 - y0
    return info


def _shade(albedo, n, view, light):
    ndotl = np.clip(np.sum(n * light, axis=-1), 0, 1)
    wrap = np.clip(ndotl * 0.94 + 0.06, 0, 1)
    half = light + view
    half = half / (np.linalg.norm(half, axis=-1, keepdims=True) + 1e-8)
    spec = np.clip(np.sum(n * half, axis=-1), 0, 1) ** 40
    fres = np.clip(1 - np.sum(n * view, axis=-1), 0, 1) ** 2.1
    col = albedo * wrap[..., None]
    col = col + spec[..., None] * np.array([255, 236, 200], np.float32) * 0.42
    col = col + fres[..., None] * np.array([120, 180, 255], np.float32) * 0.38
    return col, fres


def _project_many(cam, pts: np.ndarray):
    d = pts - cam.origin
    z = d @ cam.forward
    inv = 1.0 / np.maximum(z, 1e-4)
    x = (d @ cam.right) * inv
    y = (d @ cam.up) * inv
    sx = (x / (cam.tan_y * cam.aspect) + 1) * 0.5 * W
    sy = (1.0 - (y / cam.tan_y + 1) * 0.5) * H
    return sx, sy


def _ellipsoid_bounds(cam, center, radii, R, extra_up: float = 0.0):
    """Screen AABB of the ellipsoid. Yaw-invariant when rx == rz.

    extra_up reserves room above the pole for Santa or the sitter.
    """
    lats = np.linspace(-math.pi / 2, math.pi / 2, 17)
    lons = np.linspace(0, 2 * math.pi, 28, endpoint=False)
    lat = lats[:, None]
    lon = lons[None, :]
    p = np.stack(
        [
            radii[0] * np.cos(lat) * np.sin(lon),
            radii[1] * np.sin(lat) * np.ones_like(lon),
            radii[2] * np.cos(lat) * np.cos(lon),
        ],
        axis=-1,
    ).reshape(-1, 3).astype(np.float32)
    world = (R @ p.T).T + center
    pole = center + R @ np.array([0.0, float(radii[1]) + extra_up, 0.0], np.float32)
    crown = np.stack([
        pole,
        pole + cam.right * np.float32(0.14),
        pole - cam.right * np.float32(0.14),
    ])
    world = np.concatenate([world, crown], axis=0)
    sx, sy = _project_many(cam, world)
    return float(sx.min()), float(sy.min()), float(sx.max()), float(sy.max())


def _fit_above_caption(cam, radii, center, R, extra_up: float = 0.0):
    """Keep the silhouette, plus anyone on the pole, out of the caption strip.

    World +Y is up (smaller screen Y). The old sphere bbox filled the frame
    and the fitter gave up with the ball still crossing y 0.64.
    """
    radii = np.array(radii, np.float32, copy=True)
    center = np.array(center, np.float32, copy=True)
    # Insets leave room for the opening bob and the 18px limb glow
    # without the fitter cancelling that bob frame by frame.
    bottom_limit = float(BAND0 - 64)
    top_limit = 68.0
    for _ in range(10):
        x0, y0, x1, y1 = _ellipsoid_bounds(cam, center, radii, R, extra_up)
        left_limit, right_limit = 48.0, float(W - 48)
        if y1 <= bottom_limit + 0.5 and y0 >= top_limit - 0.5 and x0 >= left_limit and x1 <= right_limit:
            return radii, center
        room = bottom_limit - top_limit
        width_room = right_limit - left_limit
        factor = 1.0
        if (y1 - y0) > room * 0.995:
            factor = min(factor, (room / (y1 - y0)) * 0.985)
        if (x1 - x0) > width_room * 0.995:
            factor = min(factor, (width_room / (x1 - x0)) * 0.985)
        if factor < 0.999:
            radii *= np.float32(factor)
            continue
        trial = center.copy()
        trial[1] = center[1] + np.float32(0.05)
        _, y0b, _, y1b = _ellipsoid_bounds(cam, trial, radii, R, extra_up)
        if y1 > bottom_limit:
            dpy = (y1b - y1) / 0.05
            delta = 0.0 if abs(dpy) < 1.0 else (bottom_limit - y1) / dpy
        else:
            dpy = (y0b - y0) / 0.05
            delta = 0.0 if abs(dpy) < 1.0 else (top_limit - y0) / dpy
        center[1] = center[1] + np.float32(np.clip(delta, -0.8, 0.8))
    return radii, center


def _ray_window(cam, center, radii, R) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = _ellipsoid_bounds(cam, center, radii, R, 0.0)
    pad = 22
    return (
        max(0, int(math.floor(x0)) - pad),
        max(0, int(math.floor(y0)) - pad),
        min(W, int(math.ceil(x1)) + pad + 1),
        min(H, int(math.ceil(y1)) + pad + 1),
    )


def render_frame(scene: Scene, words, groups, m: dict, t: float) -> tuple[np.ndarray, dict]:
    pose = _pose_at(t, m)
    T = m["duration"]
    yaw = 2 * math.pi * 3.0 * (t / T)          # three full turns, periodic
    tilt = math.radians(pose["tilt"])
    R = _rot_x(tilt) @ _rot_y(yaw)
    scale = pose["scale"]
    squash = pose["squash"]
    rx = 1.05 * scale * (1 + 0.20 * squash)
    ry = 1.05 * scale * pose["elong"] * (1 - 0.24 * squash)
    rz = rx
    radii = np.array([rx, ry, rz], np.float32)
    center = np.array([0.0, pose["cy"], 0.0], np.float32)

    img = np.empty((H, W, 3), np.float32)
    img[:] = scene.bg[:, None, :]
    # Stars. Phase is periodic in T so a looped timeline matches, and the
    # last frame (a copy of t=0) matches exactly. The caption strip stays bare.
    tw = 0.55 + 0.45 * np.sin(2 * math.pi * (t / T) * 3 + scene.star_p * 6.28)
    for x, y, s, k in zip(scene.star_x, scene.star_y, scene.star_s, tw):
        if BAND0 - 2 <= y <= BAND1:
            continue
        v = 140 + 100 * s * k
        img[y:y + 2, x:x + 2] = (v * 0.75, v * 0.85, v)

    extra_up = 0.0
    if pose["santa"] > 0.15:
        extra_up = 0.62 * min(1.0, float(pose["santa"]))
    if pose["sitter"] > 0.08:
        sit = min(1.0, float(pose["sitter"]))
        # Headroom for the fall and the seated figure. Scales with the pose
        # so the ball does not pop when the person appears.
        extra_up = max(extra_up, 0.62 + (1.0 - sit) * 0.42)
    radii, center = _fit_above_caption(scene.cam, radii, center, R, extra_up)
    if 0.0 < t < 1.0:
        # Whole-ball drift. Zero at both ends, inside the fitter's inset.
        center = center.copy()
        center[1] += np.float32(0.055 * math.sin(2 * math.pi * t))
    rx, ry, rz = float(radii[0]), float(radii[1]), float(radii[2])

    depth = np.full((H, W), np.inf, np.float32)
    x0, y0, x1, y1 = _ray_window(scene.cam, center, radii, R)
    dirs = scene.dirs[y0:y1, x0:x1]
    t_hit, n_w, p_obj, hit = trace(scene.cam.origin, dirs, center, radii, R)

    # Geographic direction (not the stretched parametric angle).
    pn = np.linalg.norm(p_obj, axis=-1) + 1e-8
    lon = np.arctan2(p_obj[..., 0], p_obj[..., 2])
    lat = np.arcsin(np.clip(p_obj[..., 1] / pn, -1, 1))
    u = (lon + math.pi) / (2 * math.pi)
    v = (math.pi / 2 - lat) / math.pi
    land = _sample_mask(scene.tex["land"], u, v)
    earth = _bilinear(scene.tex["earth"], u, v)
    leather = _bilinear(scene.tex["leather"], u, v)

    slide = float(pose["slide"])
    if slide > 0.02:
        # Sample water from a higher latitude so the pattern has moved toward the equator.
        lat2 = np.clip(lat * (1 + 0.62 * slide), -1.45, 1.45)
        u2 = u
        v2 = (math.pi / 2 - lat2) / math.pi
        shifted = _bilinear(scene.tex["earth"], u2, v2)
        land2 = _sample_mask(scene.tex["land"], u2, v2)
        deep = np.array([10, 70, 130], np.float32)
        water = np.where(land2[..., None] > 0.5, deep, shifted)
        # Meridional streaks. Phase falls toward lat=0, so the eye reads a slide
        # to the equator. Noise in longitude keeps them from becoming bars.
        # Soft meridional flow. Latitude-only so it cannot break into cells.
        phase = np.abs(lat) * 6.5 - t * 2.6 * slide
        streak = np.clip(np.sin(phase), 0, 1) ** 2
        streak = streak * (land < 0.5)
        water = water * (0.88 + 0.18 * streak)[..., None]
        water = water + streak[..., None] * np.array([50, 140, 180], np.float32) * (0.22 * slide)
        # Soft pile-up at the equator, gaussian, not a rectangle.
        band = np.exp(-0.5 * (lat / (0.34 + 0.02)) ** 2) * slide * (land < 0.5)
        water = water + band[..., None] * np.array([40, 110, 140], np.float32)
        ocean_m = (land < 0.5)[..., None]
        earth = np.where(ocean_m, water, earth)

    leather_amt = float(np.clip(pose["leather"], 0, 1))
    albedo = earth * (1 - leather_amt) + leather * leather_amt

    # Laces and stripes in object space, stuck to the leather.
    if leather_amt > 0.08:
        nx_ = p_obj[..., 0] / rx
        ny_ = p_obj[..., 1] / ry
        nz_ = p_obj[..., 2] / rz
        ay = np.abs(ny_)
        stripe = ((ay > 0.58) & (ay < 0.66)) | ((ay > 0.72) & (ay < 0.80))
        # Laces on the screen-left limb at yaw 0 (negative X, front-facing +Z).
        lace_bar = (nx_ < -0.62) & (nx_ > -0.90) & (nz_ > 0.05) & (np.abs(ny_) < 0.34)
        bars = np.abs(np.mod(ny_ * 11.0 + 0.5, 1.0) - 0.5) < 0.16
        spine = (np.abs(nx_ + 0.76) < 0.025) & (np.abs(ny_) < 0.36) & (nz_ > 0.05)
        lace = lace_bar & bars | spine
        seam = (np.abs(nx_) < 0.012) & (nz_ > 0) & (ay < 0.9)
        white = np.array([236, 236, 232], np.float32)
        dark = albedo * 0.35
        wgt = leather_amt
        albedo = np.where(stripe[..., None], albedo * (1 - wgt) + white * wgt, albedo)
        albedo = np.where(lace[..., None], albedo * (1 - wgt) + white * wgt, albedo)
        albedo = np.where(seam[..., None], albedo * (1 - 0.45 * wgt) + dark * (0.45 * wgt), albedo)

    # Contact shadow under whoever is standing on the tip.
    up = R @ np.array([0, 1, 0], np.float32)
    pole = center + R @ np.array([0, ry, 0], np.float32)
    p_world = np.einsum("...i,ij->...j", p_obj, R.T) + center
    if pose["santa"] > 0.05:
        d = np.linalg.norm(p_world - pole, axis=-1)
        shadow = np.exp(-(d / 0.22) ** 2) * pose["santa"]
        albedo = albedo * (1 - 0.5 * shadow)[..., None]
    if pose["sitter"] > 0.4:
        seat = pole + up * 0.02
        d = np.linalg.norm(p_world - seat, axis=-1)
        shadow = np.exp(-(d / 0.28) ** 2) * min(1.0, pose["sitter"])
        albedo = albedo * (1 - 0.55 * shadow)[..., None]

    view = -dirs
    # Slow orbit for the whole film (periodic), plus a fast sweep in the
    # opening second so the hook is obviously alive. The sweep is zero at
    # t = 0 and t = 1, so it does not pop and the loop still matches frame 0.
    az = 2 * math.pi * (t / T) * 4.0
    if 0.0 < t < 1.0:
        az += 4.4 * math.sin(2 * math.pi * 2.0 * t)
    light = np.array([-0.62 * math.sin(az) - 0.05, 0.55, 0.70 * math.cos(az)], np.float32)
    light /= np.linalg.norm(light)
    col, fres = _shade(albedo, n_w, view, light)
    xs = np.linspace(0, 1, col.shape[1], dtype=np.float32)
    sweep = 0.85 * (1 - math.cos(2 * math.pi * t)) if t < 1.0 else 0.0
    pos = ((t / T) * 4.0 + sweep) % 1.0
    band = np.exp(-0.5 * ((xs - pos) / 0.10) ** 2).astype(np.float32)
    col += band[None, :, None] * np.array([160, 128, 64], np.float32)
    patch = img[y0:y1, x0:x1]
    patch[hit] = np.clip(col[hit], 0, 255)
    depth[y0:y1, x0:x1][hit] = t_hit[hit]
    globe_hit = np.zeros((H, W), bool)
    globe_hit[y0:y1, x0:x1] = hit

    # Atmosphere just outside the limb.
    glow = np.zeros((H, W), np.float32)
    sub = globe_hit.astype(np.float32)
    for dpx in (5, 11, 18):
        g = np.zeros_like(sub)
        g[dpx:] = np.maximum(g[dpx:], sub[:-dpx])
        g[:-dpx] = np.maximum(g[:-dpx], sub[dpx:])
        g[:, dpx:] = np.maximum(g[:, dpx:], sub[:, :-dpx])
        g[:, :-dpx] = np.maximum(g[:, :-dpx], sub[:, dpx:])
        glow = np.maximum(glow, g * (0.55 if dpx == 5 else 0.28 if dpx == 11 else 0.12))
    glow *= 1 - sub
    img += glow[..., None] * np.array([40, 90, 160], np.float32)

    _paint_props(scene, img, depth, pose, R, radii, center, light, t)

    ys = np.where(globe_hit.any(axis=1))[0]
    xs = np.where(globe_hit.any(axis=0))[0]
    globe_top = int(ys.min()) if len(ys) else H // 2
    # Dashed silhouette during the "fatter" card. Ticks stay on the limb,
    # and any dash that would enter the caption band is dropped.
    dashes = None
    if caption_mode(t, m) == "fatter":
        dashes = _draw_dashes(img, globe_hit, BAND0, BAND1)
    img *= scene.vig[..., None]
    # Caption plate. No type, no stars, no globe. The bot draws karaoke here.
    plate = scene.bg[BAND0:BAND1, None, :] * scene.vig[BAND0:BAND1, :, None]
    img[BAND0:BAND1] = plate

    out = np.clip(img, 0, 255).astype(np.uint8)
    band = out[BAND0:BAND1]
    meta = {
        "mode": caption_mode(t, m),
        "globe_top": globe_top,
        "globe_bottom": int(ys.max()) if len(ys) else 0,
        "globe_left": int(xs.min()) if len(xs) else 0,
        "globe_right": int(xs.max()) if len(xs) else 0,
        "band_max": int(band.max()) if band.size else 0,
        "pose": {k: round(float(v), 4) for k, v in pose.items()},
        "safe": True,
        "dashes": dashes,
    }
    return out, meta


def _draw_dashes(img: np.ndarray, hit: np.ndarray, y_avoid0: int, y_avoid1: int) -> dict:
    ys, xs = np.where(hit)
    if len(xs) == 0:
        return {"n": 0}
    cx = float(xs.mean())
    cy = float(ys.mean())
    # Silhouette radii from the hit mask, a little outside the limb.
    rx = (xs.max() - xs.min()) * 0.5 + 16
    ry = (ys.max() - ys.min()) * 0.5 + 16
    n = 56
    drawn = 0
    for i in range(n):
        if i % 2:
            continue
        a = 2 * math.pi * i / n
        x = int(cx + math.cos(a) * rx)
        y = int(cy + math.sin(a) * ry)
        if y_avoid0 <= y <= y_avoid1 and SAFE_LEFT - 10 <= x <= SAFE_RIGHT:
            # This dash lives in the caption band. Skip it so it cannot cross type.
            continue
        if 4 <= x < W - 4 and 4 <= y < H - 4:
            img[y - 2:y + 3, x - 2:x + 3] = (244, 246, 248)
            drawn += 1
    # Short side ticks only, low on the ball, never a long arrow into the type.
    for x, y in ((int(cx - rx), int(cy)), (int(cx + rx), int(cy))):
        if 8 < x < W - 8 and SAFE_BOT > y > y_avoid1:
            img[y - 2:y + 3, x - 10:x + 10] = (235, 240, 245)
    return {"n": drawn, "cx": cx, "cy": cy}


def _paint_ell(scene, img, depth, center, radii, rot, color, light, emit=0.0):
    radii = np.asarray(radii, np.float32)
    center = np.asarray(center, np.float32)
    if rot is None:
        rot = np.eye(3, dtype=np.float32)
    sx, sy, z = project(scene.cam, center)
    if z < 0.3:
        return
    pix = (float(np.max(radii)) / z) / scene.cam.tan_y * (H * 0.5) * 1.35
    x0 = max(0, int(sx - pix))
    x1 = min(W, int(sx + pix) + 2)
    y0 = max(0, int(sy - pix))
    y1 = min(H, int(sy + pix) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    dirs = scene.dirs[y0:y1, x0:x1]
    t_hit, n_w, _p, hit = trace(scene.cam.origin, dirs, center, radii, rot)
    if not np.any(hit):
        return
    view = -dirs
    albedo = np.broadcast_to(np.array(color, np.float32), n_w.shape).copy()
    col, _fres = _shade(albedo, n_w, view, light)
    if emit:
        col = col + np.array(color, np.float32) * emit
    closer = hit & (t_hit < depth[y0:y1, x0:x1])
    patch = img[y0:y1, x0:x1]
    patch[closer] = np.clip(col[closer], 0, 255)
    depth[y0:y1, x0:x1][closer] = t_hit[closer]


def _paint_props(scene, img, depth, pose, R, radii, center, light, t):
    rx, ry, rz = map(float, radii)
    up = R @ np.array([0, 1, 0], np.float32)
    pole = center + R @ np.array([0, ry * 0.985, 0], np.float32)
    side = scene.cam.right - up * float(np.dot(scene.cam.right, up))
    sl = float(np.linalg.norm(side))
    if sl < 1e-4:
        side = scene.cam.right
    else:
        side = side / sl
    fwd = scene.cam.forward

    if pose["santa"] > 0.15:
        vis = float(np.clip(pose["santa"], 0, 1))
        bob = 0.012 * math.sin(t * 3.1)
        foot = pole + up * (0.01 + bob)
        s = 0.20 * vis
        # Body stack. Same leather-warm light as the ball.
        red = (196, 36, 44)
        white = (236, 236, 234)
        skin = (236, 198, 166)
        _paint_ell(scene, img, depth, foot + up * (0.05 * s / 0.2), (0.045, 0.03, 0.05), R, (30, 28, 32), light)
        _paint_ell(scene, img, depth, foot + side * 0.05 * s / 0.16 + up * 0.02, (0.035, 0.025, 0.04), R, (24, 22, 26), light)
        _paint_ell(scene, img, depth, foot - side * 0.05 + up * 0.02, (0.035, 0.025, 0.04), R, (24, 22, 26), light)
        body = foot + up * 0.16
        _paint_ell(scene, img, depth, body, (0.09, 0.12, 0.07), R, red, light)
        _paint_ell(scene, img, depth, body + up * 0.02, (0.095, 0.025, 0.075), R, (32, 30, 34), light)
        _paint_ell(scene, img, depth, body + up * 0.02 + fwd * -0.04, (0.02, 0.02, 0.015), R, (230, 190, 70), light)
        _paint_ell(scene, img, depth, body + side * 0.11 + up * 0.02, (0.03, 0.07, 0.03), R, red, light)
        _paint_ell(scene, img, depth, body - side * 0.11 + up * 0.02, (0.03, 0.07, 0.03), R, red, light)
        head = body + up * 0.16
        _paint_ell(scene, img, depth, head, (0.055, 0.055, 0.05), R, skin, light)
        _paint_ell(scene, img, depth, head + fwd * -0.03 + up * -0.01, (0.05, 0.045, 0.03), R, white, light)
        _paint_ell(scene, img, depth, head + up * 0.045, (0.058, 0.02, 0.055), R, white, light)
        _paint_ell(scene, img, depth, head + up * 0.10, (0.04, 0.055, 0.04), R, red, light)
        _paint_ell(scene, img, depth, head + up * 0.16, (0.022, 0.022, 0.022), R, white, light)
        # Eyes, small and high-contrast so the face reads at phone size.
        for sgn in (1, -1):
            eye = head + side * (0.02 * sgn) + fwd * -0.048 + up * 0.01
            _paint_ell(scene, img, depth, eye, (0.008, 0.008, 0.006), R, (20, 18, 22), light)

        # Cabin, same clay shading, offset to the side of the tip.
        base = pole + side * 0.28 + up * 0.02
        wood = (132, 78, 44)
        _paint_ell(scene, img, depth, base + up * 0.08, (0.11, 0.08, 0.09), R, wood, light)
        _paint_ell(scene, img, depth, base + up * 0.15, (0.13, 0.045, 0.11), R, (92, 48, 36), light)
        _paint_ell(scene, img, depth, base + up * 0.175, (0.10, 0.03, 0.09), R, (230, 236, 240), light)
        _paint_ell(scene, img, depth, base + up * 0.06 + fwd * -0.07, (0.025, 0.04, 0.01), R, (255, 196, 80), light, emit=0.65)
        _paint_ell(scene, img, depth, base + up * 0.05 + fwd * -0.075, (0.03, 0.055, 0.012), R, (64, 38, 26), light)
        chim = base + side * 0.06 + up * 0.20
        _paint_ell(scene, img, depth, chim, (0.025, 0.05, 0.025), R, (70, 70, 74), light)
        for i in range(3):
            ph = (t * 0.45 + i * 0.33) % 1.0
            c = chim + up * (0.06 + ph * 0.22) + side * math.sin(t * 2 + i) * 0.02
            rad = 0.03 * (1.15 - ph)
            gray = int(170 + 40 * (1 - ph))
            _paint_ell(scene, img, depth, c, (rad, rad * 0.8, rad), R, (gray, gray, gray + 4), light)

    if pose["sitter"] > 0.08:
        sit = float(np.clip(pose["sitter"], 0, 1))
        # Drop from above the tip onto the leather.
        hip = pole + up * (0.06 + (1 - sit) * 0.38) - fwd * 0.06
        denim = (32, 74, 148)
        denim_d = (22, 52, 112)
        skin = (214, 170, 138)
        hair = (36, 26, 22)
        _paint_ell(scene, img, depth, hip + up * 0.16, (0.16, 0.15, 0.11), R, denim, light)
        # Back seam: a darker sliver on the camera side so the torso reads as clothing.
        _paint_ell(scene, img, depth, hip + up * 0.16 - fwd * 0.10, (0.02, 0.12, 0.02), R, denim_d, light)
        _paint_ell(scene, img, depth, hip + up * 0.34, (0.075, 0.08, 0.07), R, skin, light)
        _paint_ell(scene, img, depth, hip + up * 0.40, (0.078, 0.045, 0.075), R, hair, light)
        _paint_ell(scene, img, depth, hip + up * 0.18 + side * 0.18, (0.045, 0.11, 0.045), R, denim, light)
        _paint_ell(scene, img, depth, hip + up * 0.18 - side * 0.18, (0.045, 0.11, 0.045), R, denim, light)
        # Thighs fold forward as he sits. Bend increases with sit.
        bend = _rot_x(math.radians(-55 * sit))
        leg_r = R @ bend
        for sgn in (1.0, -1.0):
            thigh = hip + side * (0.07 * sgn) + up * -0.02 + leg_r @ np.array([0, -0.10, -0.06], np.float32)
            _paint_ell(scene, img, depth, thigh, (0.055, 0.11, 0.05), leg_r, denim_d, light)
            shin_r = R @ _rot_x(math.radians(40 * sit))
            shin = thigh + shin_r @ np.array([0, -0.12, 0.02], np.float32)
            _paint_ell(scene, img, depth, shin, (0.04, 0.10, 0.04), shin_r, (24, 24, 28), light)
