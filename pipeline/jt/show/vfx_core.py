"""Reusable map VFX. Specs pass seconds, not frame numbers.

Three layers, in order:

1. Core. Spring arrivals, zoom-aware strokes, a pixel or two of line
   displacement. The camera does not sway.
2. Lens and atmosphere. Adaptive blur and glow-reactive dust. A dark
   single-accent focus mask is optional and only while a beat asks for it.
3. Optical output. Barrel distortion on the map, then edge chromatic
   aberration and dither on the finished frame.

The default plate is the colourful satellite globe. Word timestamps drive
the flashes. Impact shake, Perlin sway, and motion jolts stay off.
"""

from __future__ import annotations

import math

import numpy as np
import skia

# 5 frames of badge scale, text on frame 6, at the show frame rate.
BADGE_OPEN_S = 5.0 / 30.0
BADGE_TEXT_S = 6.0 / 30.0
SHAKE_MAX_S = 0.3
# SMOOTH. These stay off for every episode. Do not flip them to chase a
# motion number.
SPRING_CAMERA = False
IMPACT_SHAKE = False
PERLIN_SHAKE = False
MOTION_JOLTS = False


def _clamp(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def ease_in_out_cubic(t: float) -> float:
    t = _clamp(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def ease_in_out_quintic(t: float) -> float:
    t = _clamp(t)
    if t < 0.5:
        return 16.0 * t ** 5
    return 1.0 - ((-2.0 * t + 2.0) ** 5) / 2.0


def _spring(t: float) -> float:
    """Old spring curve. Kept so a test can see it. The default path does not call it."""
    t = _clamp(t)
    if t == 0.0 or t == 1.0:
        return t
    c4 = 2.0 * math.pi / 3.0
    return (2.0 ** (-10.0 * t)) * math.sin((t * 10.0 - 0.75) * c4) + 1.0


def overshoot(t: float) -> float:
    """Element entrance. Ease-in-out, and it never passes 1."""
    if not SPRING_CAMERA:
        return ease_in_out_cubic(t)
    return _spring(t)


# Snap integrator. One 1/60 s step uses the owner's update:
# force = k * (target - pos), vel = (vel + force / m) * damping, pos += vel * dt.
# Tuned to a small overshoot and a settle inside 0.7 s. Not a sway.
SPRING_STEP = 1.0 / 60.0
SPRING_MASS = 1.0
SPRING_STIFFNESS = 200.0
SPRING_DAMPING = 0.80


def spring_approach(start: float, target: float, elapsed: float, mass: float = SPRING_MASS,
                    stiffness: float = SPRING_STIFFNESS, damping: float = SPRING_DAMPING) -> float:
    """Deterministic spring from `start` toward `target` after `elapsed` seconds.

    Same elapsed always returns the same position. Velocity starts at rest,
    so a settled spring does not drift.
    """
    pos = float(start)
    vel = 0.0
    if elapsed <= 0.0:
        return pos
    step = SPRING_STEP
    n = int(round(elapsed / step))
    inv_m = 1.0 / max(1e-6, float(mass))
    k = float(stiffness)
    damp = float(damping)
    goal = float(target)
    for _ in range(n):
        force = k * (goal - pos)
        vel = (vel + force * inv_m * step) * damp
        pos += vel * step
    return pos


def exp_zoom(z0: float, z1: float, eased_t: float) -> float:
    """Constant-speed zoom in log space. z is a view span (larger is wider)."""
    u = _clamp(eased_t)
    z0 = max(1e-3, float(z0))
    z1 = max(1e-3, float(z1))
    return z0 * (z1 / z0) ** u


def impact_shake(t: float, t0: float, dur: float = 0.25, amp: float = 1.0) -> tuple[float, float]:
    """Camera offset in pixels. Off. A spec cannot turn this on."""
    if not IMPACT_SHAKE:
        return 0.0, 0.0
    dur = min(SHAKE_MAX_S, max(0.0, float(dur)))
    age = float(t) - float(t0)
    if dur <= 0.0 or age < 0.0 or age > dur:
        return 0.0, 0.0
    decay = (1.0 - age / dur) ** 2
    wave = math.sin(age * 46.0)
    return amp * wave * decay, amp * 0.35 * wave * decay


def perlin_shake(t: float, amp: float = 1.0) -> tuple[float, float]:
    """Idle sway. Off. The camera does not drift between events."""
    if PERLIN_SHAKE:
        return 0.0, 0.0
    return 0.0, 0.0


def motion_jolt(t: float, t0: float, amount: float = 1.0) -> float:
    """A punch or snap on the camera. Off."""
    if MOTION_JOLTS:
        return 0.0
    return 0.0


def accumulate(frames: list[np.ndarray]) -> np.ndarray:
    """True motion blur: average sub-frames rendered a fraction apart."""
    if not frames:
        raise ValueError("accumulate needs at least one frame")
    if len(frames) == 1:
        return frames[0]
    acc = np.zeros_like(frames[0], np.float32)
    for frame in frames:
        acc += frame.astype(np.float32)
    return np.clip(acc / len(frames), 0, 255).astype(np.uint8)


def shadow_offset(cx: float, cy: float, sun: tuple[float, float] = (1080.0, 0.0), zoom: float = 1.0) -> tuple[float, float]:
    """2.5D shadow. The sun sits at the top-right. zoom > 1 is closer."""
    z = max(0.15, float(zoom))
    return (cx - sun[0]) * 0.02 * z, (cy - sun[1]) * 0.02 * z


def neon_passes(core: float = 2.0) -> list[tuple[float, float]]:
    """Width, alpha. Wide dim halo, mid glow, solid core."""
    scale = max(0.4, core / 2.0)
    return [(15.0 * scale, 0.10), (7.0 * scale, 0.40), (2.0 * scale, 1.0)]


def stroke_for_zoom(base: float, zoom: float) -> float:
    """Thinner strokes when the camera is wider, so a border stays a border."""
    return float(base) / math.sqrt(max(0.25, float(zoom)))


def displace_line(pts: list[tuple[float, float]], t: float, amp: float = 1.2) -> list[tuple[float, float]]:
    """A slow, tiny offset along the normal. Enough to feel alive, not a shake."""
    if len(pts) < 2 or amp <= 0.0:
        return list(pts)
    out = []
    last = len(pts) - 1
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == last:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]
        length = math.hypot(dx, dy) or 1.0
        wobble = math.sin(t * 1.4 + i * 0.8) * float(amp)
        out.append((x - dy / length * wobble, y + dx / length * wobble))
    return out


def flash_envelope(t: float, words: list[dict], dur: float = 0.32) -> float:
    """0..1. Every peak sits on a word start from words.json."""
    hot = 0.0
    for word in words:
        t0 = float(word.get("t0", word.get("t", 0.0)))
        age = float(t) - t0
        if dur > 0.0 and 0.0 <= age <= dur:
            hot = max(hot, math.sin(math.pi * age / dur))
    return hot


def focus_amount(t: float, beats: list[dict]) -> float:
    """Dark single-accent mode. Zero unless a beat sets style to focus."""
    hot = 0.0
    for beat in beats:
        if beat.get("type") != "focus" and beat.get("style") != "focus":
            continue
        dur = float(beat.get("dur", 0.9))
        age = float(t) - float(beat["t"])
        if dur > 0.0 and 0.0 <= age <= dur:
            hot = max(hot, math.sin(math.pi * age / dur))
    return hot


def trim_polyline(pts: list[tuple[float, float]], u: float) -> list[tuple[float, float]]:
    """Laser reveal. u is 0..1 along the path length, in seconds of the caller."""
    if not pts:
        return []
    u = _clamp(u)
    if u <= 0.0:
        return [pts[0]]
    if u >= 1.0 or len(pts) == 1:
        return list(pts)
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(segs) or 1.0
    want = total * u
    out = [pts[0]]
    acc = 0.0
    for (a, b), dist in zip(zip(pts, pts[1:]), segs):
        if acc + dist >= want:
            v = 0.0 if dist == 0 else (want - acc) / dist
            out.append((a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v))
            return out
        out.append(b)
        acc += dist
    return out


def draw_neon_path(canvas, pts: list[tuple[float, float]], color: tuple[int, int, int], core: float = 2.0, dash: float = 0.0) -> None:
    if len(pts) < 2:
        return
    path = skia.Path()
    path.moveTo(pts[0][0], pts[0][1])
    for x, y in pts[1:]:
        path.lineTo(x, y)
    for width, alpha in neon_passes(core):
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
        pen.setStrokeCap(skia.Paint.kRound_Cap)
        pen.setStrokeJoin(skia.Paint.kRound_Join)
        pen.setColor(skia.ColorSetARGB(int(255 * alpha), color[0], color[1], color[2]))
        if dash > 1.0:
            pen.setPathEffect(skia.DashPathEffect.Make([dash, dash * 0.45], 0))
        canvas.drawPath(path, pen)


def badge_state(age: float) -> tuple[float, bool]:
    """Scale-x of the pill, and whether the glyphs are on yet.

    The pill opens across 5/30 s. The text appears at 6/30 s. Timing is
    seconds, so 24 fps and 30 fps hit the same moments.
    """
    if age <= 0.0:
        return 0.0, False
    scale = _clamp(age / BADGE_OPEN_S)
    scale = ease_in_out_cubic(scale)
    return scale, age >= BADGE_TEXT_S


def draw_badge(canvas, text: str, x: float, y: float, age: float, size: float = 48.0, fill=(16, 18, 22), ink=(255, 214, 48), background: np.ndarray | None = None) -> tuple[float, float, float, float] | None:
    font = skia.Font(None, size)
    # Prefer the project face when labels has loaded one.
    try:
        from jt.show.labels import faces
        font = skia.Font(faces()["bold"], size)
    except Exception:
        pass
    width = font.measureText(text)
    pad = 20.0
    scale, show = badge_state(age)
    if scale <= 0.01:
        return None
    rect_w = (width + pad * 2) * scale
    rect_h = size + pad
    text_ink = ink
    pill = fill
    backing = 0
    if background is not None:
        lum = box_luminance(background, x, y, max(rect_w, width + pad * 2), rect_h)
        text_ink, backing = label_style(lum)
        # Bright ground: dark glyphs on a light pill. Dark ground: the light ink stays.
        if lum > 0.70:
            pill = (244, 244, 246)
        else:
            text_ink = ink
            backing = 0
    rect = skia.Rect.MakeXYWH(x - rect_w / 2, y - rect_h / 2, rect_w, rect_h)
    if backing:
        shade = skia.Paint(AntiAlias=True)
        shade.setColor(skia.ColorSetARGB(backing, 8, 10, 16))
        shade.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8))
        canvas.drawRoundRect(rect.makeOutset(6, 6), 22, 22, shade)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(235, pill[0], pill[1], pill[2]))
    canvas.drawRoundRect(rect, 18, 18, paint)
    if show:
        glyph = skia.Paint(AntiAlias=True)
        glyph.setColor(skia.ColorSetARGB(255, text_ink[0], text_ink[1], text_ink[2]))
        canvas.drawString(text, x - width / 2, y + size * 0.32, font, glyph)
    return (rect.left(), rect.top(), rect.right(), rect.bottom())


def place_labels(boxes: list[tuple[float, float, float, float]], gap: float = 12.0) -> list[tuple[float, float]]:
    """Nudge later labels down until their boxes no longer cross.

    Each box is (cx, cy, w, h). Returns the same count of (cx, cy).
    """
    placed: list[tuple[float, float, float, float]] = []
    out: list[tuple[float, float]] = []
    for cx, cy, w, h in boxes:
        x, y = cx, cy
        for _ in range(8):
            hit = False
            for px, py, pw, ph in placed:
                if abs(x - px) * 2 < (w + pw) + gap and abs(y - py) * 2 < (h + ph) + gap:
                    y = py + (h + ph) / 2 + gap
                    hit = True
                    break
            if not hit:
                break
        placed.append((x, y, w, h))
        out.append((x, y))
    return out


def cloud_alpha(zoom_ratio: float) -> float:
    """zoom_ratio is start_span / span. Clouds die once the camera is inside them."""
    if zoom_ratio >= 3.2:
        return 0.0
    if zoom_ratio <= 1.15:
        return 0.85
    return 0.85 * (1.0 - _clamp((zoom_ratio - 1.15) / 2.05))


def cloud_scale(zoom_ratio: float) -> float:
    """Clouds grow at twice the map's zoom rate."""
    return max(0.2, float(zoom_ratio)) ** 2


def draw_clouds(canvas, t: float, zoom_ratio: float, w: int = 1080, h: int = 1920) -> None:
    alpha = cloud_alpha(zoom_ratio)
    if alpha <= 0.02:
        return
    scale = cloud_scale(zoom_ratio)
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(int(150 * alpha), 236, 242, 248))
    seeds = ((0.22, 0.30), (0.58, 0.22), (0.74, 0.48), (0.36, 0.62))
    for i, (fx, fy) in enumerate(seeds):
        drift = (t * (18 + i * 7) + i * 80) % (w + 400) - 200
        cx = fx * w + drift * 0.15
        cy = fy * h
        rx = (90 + i * 30) * scale
        ry = (36 + i * 10) * scale
        canvas.drawOval(skia.Rect.MakeXYWH(cx - rx, cy - ry, rx * 2, ry * 2), paint)


def draw_atmosphere(canvas, cx: float, cy: float, radius: float, strength: float = 1.0) -> None:
    """Rim on the outer 5% of the disk. strength is 1 zoomed out and 0 close."""
    if strength <= 0.03 or radius < 8:
        return
    for i, (grow, alpha, width) in enumerate(((0.015, 70, 10), (0.035, 40, 16), (0.05, 22, 22))):
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
        pen.setStrokeCap(skia.Paint.kRound_Cap)
        pen.setColor(skia.ColorSetARGB(int(alpha * strength), 150, 210, 255))
        canvas.drawCircle(cx, cy, radius * (1.0 + grow), pen)


def multiply_rgb(img: np.ndarray, tint: tuple[int, int, int], amount: float) -> np.ndarray:
    """Paper or hillshade multiply. amount 0 leaves the plate alone."""
    amount = _clamp(amount)
    if amount <= 0.0:
        return img
    tint_v = np.array(tint, np.float32) / 255.0
    base = img.astype(np.float32)
    mixed = base * ((1.0 - amount) + amount * tint_v)
    return np.clip(mixed, 0, 255).astype(np.uint8)


def stress_glow(t: float, marks: list[tuple[float, float]]) -> float:
    """0..1 from stress-word windows (t0, dur). Modulates glow, not the camera."""
    hot = 0.0
    for t0, dur in marks:
        age = t - t0
        if 0.0 <= age <= dur and dur > 0:
            u = age / dur
            hot = max(hot, math.sin(math.pi * u))
    return hot


def camera_micro_offset(t: float) -> tuple[float, float]:
    """Constant sub-pixel sway. Banned. A hold stays still."""
    return 0.0, 0.0


def travel_blur_sigma(speed: float, zoom: float = 1.0, max_sigma: float = 2.0) -> float:
    """Background blur from camera speed. Zero at rest, softer when zoomed in.

    speed is a per-second mix of zoom rate and pan. max_sigma stays small so
    a phone frame does not turn to mush.
    """
    if speed <= 0.02:
        return 0.0
    amount = _clamp(float(speed) / 0.85)
    zoom_cut = 1.0 / math.sqrt(max(1.0, float(zoom)))
    return max_sigma * amount * zoom_cut


def adaptive_blur(img: np.ndarray, sigma: float, protect: np.ndarray | None = None) -> np.ndarray:
    """Blur the map. Pixels marked in `protect` (the focus country) stay sharp."""
    if sigma < 0.35:
        return img
    from scipy.ndimage import gaussian_filter
    small = img[::2, ::2].astype(np.float32)
    blurred = gaussian_filter(small, sigma=(max(0.4, sigma * 0.5), max(0.4, sigma * 0.5), 0))
    up = np.repeat(np.repeat(blurred, 2, axis=0), 2, axis=1)
    up = up[:img.shape[0], :img.shape[1]]
    out = np.clip(up, 0, 255).astype(np.uint8)
    if protect is not None and protect.any():
        mask = protect[:out.shape[0], :out.shape[1]]
        out[mask] = img[:out.shape[0], :out.shape[1]][mask]
    return out


def apply_focus_mask(img: np.ndarray, cx: float, cy: float, travel: float, arrive: float) -> np.ndarray:
    """Radial darkening that opens while the camera travels, then a small centre lift on arrival."""
    h, w = img.shape[:2]
    ys = np.linspace(0.0, h - 1, h, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, w - 1, w, dtype=np.float32)[None, :]
    radius = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    hole = 160.0 + 460.0 * _clamp(travel)
    edge = np.clip((radius - hole) / 320.0, 0.0, 1.0)
    dark = 1.0 - 0.22 * edge * (0.25 + 0.75 * _clamp(travel))
    out = img.astype(np.float32) * dark[..., None]
    lift = np.clip(1.0 - radius / 240.0, 0.0, 1.0) ** 2
    out += float(arrive) * lift[..., None] * 16.0
    return np.clip(out, 0, 255).astype(np.uint8)


def glow_hillshade(img: np.ndarray, glow: float) -> np.ndarray:
    """Directional relief from the plate, visible only while something is glowing."""
    if glow < 0.12:
        return img
    luma = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]
    small = luma[::4, ::4].astype(np.float32)
    from scipy.ndimage import gaussian_filter
    relief = gaussian_filter(small, 1.1)
    gy, gx = np.gradient(relief)
    shade = gx * 0.72 + gy * 0.48
    scale = float(np.percentile(np.abs(shade), 96)) + 1e-3
    shade = np.clip(shade / scale, -1.0, 1.0)
    up = np.repeat(np.repeat(shade, 4, axis=0), 4, axis=1)
    up = up[:img.shape[0], :img.shape[1]]
    factor = 1.0 + up * (0.14 * float(glow))
    return np.clip(img.astype(np.float32) * factor[..., None], 0, 255).astype(np.uint8)


def anamorphic_alpha(glow: float) -> float:
    """About 5% at full glow. Nothing until the glow is actually strong."""
    if glow < 0.55:
        return 0.0
    return 0.05 * min(1.0, (float(glow) - 0.40) / 0.60)


def draw_anamorphic(canvas, cx: float, cy: float, glow: float, drift: float = 0.0, width: int = 1080) -> None:
    alpha = anamorphic_alpha(glow)
    if alpha <= 0.0:
        return
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(int(255 * alpha), 90, 170, 255))
    paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7))
    y = cy - drift
    canvas.drawRect(skia.Rect.MakeXYWH(0, y - 5, width, 10), paint)


def glitch_active(t: float, t0: float, fps: float = 30.0, frames: int = 3) -> bool:
    """True for 2–3 frames after a dramatic beat. Not a hold and not a sway."""
    frames = 2 if frames < 2 else 3 if frames > 3 else int(frames)
    age = (float(t) - float(t0)) * float(fps)
    return 0.0 <= age < frames


def apply_glitch(img: np.ndarray, salt: int = 0) -> np.ndarray:
    """RGB shift on the top band, plus a few scanlines. The rest of the frame stays."""
    out = img.copy()
    band = max(8, int(out.shape[0] * 0.16))
    shift = 5 + (salt % 3)
    out[:band, :, 0] = np.roll(out[:band, :, 0], shift, axis=1)
    out[:band, :, 2] = np.roll(out[:band, :, 2], -shift, axis=1)
    faded = (out[:band:3].astype(np.float32) * 0.88).astype(np.uint8)
    out[:band:3] = faded
    return out


def dust_opacity(glow: float) -> float:
    """Invisible in the dark. A few percent on a big flash."""
    if glow < 0.35:
        return 0.0
    return min(0.04, (float(glow) - 0.35) * 0.05)


_DUST = None


def _dust_field(h: int, w: int) -> np.ndarray:
    global _DUST
    if _DUST is not None and _DUST.shape == (h, w):
        return _DUST
    rng = np.random.default_rng(1998)
    field = np.zeros((h // 4, w // 4), np.float32)
    ys = rng.integers(0, field.shape[0], 18)
    xs = rng.integers(0, field.shape[1], 18)
    field[ys, xs] = rng.uniform(0.4, 1.0, len(xs))
    from scipy.ndimage import gaussian_filter
    field = gaussian_filter(field, 1.4)
    field /= max(1e-6, float(field.max()))
    _DUST = np.repeat(np.repeat(field, 4, axis=0), 4, axis=1)[:h, :w]
    return _DUST


def apply_lens_dust(img: np.ndarray, glow: float) -> np.ndarray:
    opacity = dust_opacity(glow)
    if opacity <= 0.0:
        return img
    dust = _dust_field(img.shape[0], img.shape[1]).astype(np.float32)
    out = img.astype(np.float32) + dust[..., None] * (255.0 * opacity)
    return np.clip(out, 0, 255).astype(np.uint8)


def lens_atmosphere(img: np.ndarray, sigma: float, glow: float, protect: np.ndarray | None = None,
                    focus: float = 0.0, cx: float = 540.0, cy: float = 960.0,
                    travel: float = 0.0, arrive: float = 1.0) -> np.ndarray:
    """Layer 2. Blur and dust. The dark focus mask runs only while `focus` is up."""
    out = img
    if focus > 0.04:
        out = apply_focus_mask(out, cx, cy, travel=max(travel, 0.2), arrive=max(arrive, focus))
    out = adaptive_blur(out, sigma, protect)
    return apply_lens_dust(out, glow)


def edge_chromatic(img: np.ndarray) -> np.ndarray:
    """One pixel of red shift, and only in the rim."""
    h, w = img.shape[:2]
    ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    radius = np.sqrt(xs * xs * 0.85 + ys * ys)
    edge = np.clip((radius - 0.72) / 0.28, 0.0, 1.0)
    out = img.astype(np.float32)
    red = out[:, :, 0]
    shifted = np.roll(red, 1, axis=1)
    out[:, :, 0] = red * (1.0 - edge * 0.45) + shifted * (edge * 0.45)
    return out


def dither_frame(img: np.ndarray, t: float) -> np.ndarray:
    """One least-significant-bit of deterministic noise, against banding."""
    rng = np.random.default_rng(int(float(t) * 1000.0) & 0xFFFFFFFF)
    noise = rng.integers(-1, 2, size=img.shape, dtype=np.int16)
    base = img if img.dtype != np.float32 else img
    return np.clip(base.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def optical_output(img: np.ndarray, t: float, barrel: bool = False) -> np.ndarray:
    """Layer 3. Barrel is opt-in because captions must not bend with the map."""
    out = barrel_distort(img) if barrel else img
    return dither_frame(edge_chromatic(out), t)


def ink_color(color: tuple[int, int, int], paper: tuple[int, int, int] = (214, 186, 140), mix: float = 0.22) -> tuple[int, int, int]:
    """Pull the ink a little toward the paper so it looks soaked, not neon-pure."""
    mix = _clamp(mix)
    return tuple(int(round(color[i] * (1.0 - mix) + paper[i] * mix)) for i in range(3))


def ink_widths(count: int, base: float = 5.0, salt: int = 1) -> np.ndarray:
    """Noise-modulated stroke widths. Deterministic for a given salt."""
    if count <= 0:
        return np.zeros(0, np.float32)
    noise = np.random.default_rng(20261011 + int(salt)).random(count)
    return (base * (0.55 + 0.9 * noise)).astype(np.float32)


def _cumlen(pts: list[tuple[float, float]]) -> list[float]:
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return cum


def _slice_by_length(pts, cum, start: float, end: float) -> list[tuple[float, float]]:
    if end <= start or len(pts) < 2:
        return []
    out = []
    for i in range(len(pts) - 1):
        a0, a1 = cum[i], cum[i + 1]
        if a1 <= start or a0 >= end:
            continue
        span = max(1e-6, a1 - a0)
        u0 = max(0.0, (start - a0) / span)
        u1 = min(1.0, (end - a0) / span)
        p0 = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u0, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u0)
        p1 = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u1, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u1)
        if not out:
            out.append(p0)
        out.append(p1)
    return out


def border_strands(pts: list[tuple[float, float]], origins: int = 4, progress: float = 1.0) -> list[list[tuple[float, float]]]:
    """Grow a border from several seeds at once until the strands meet."""
    if len(pts) < 2 or progress <= 0.0:
        return []
    origins = max(2, min(int(origins), len(pts)))
    seeds = sorted({int(round(i * (len(pts) - 1) / (origins - 1))) for i in range(origins)})
    if len(seeds) < 2:
        return [list(pts)] if progress >= 1 else []
    cum = _cumlen(pts)
    strands = []
    speeds = [0.75 + 0.45 * ((i * 3) % 5) / 5.0 for i in range(len(seeds))]
    for i in range(len(seeds) - 1):
        a, b = seeds[i], seeds[i + 1]
        span = cum[b] - cum[a]
        if span <= 1e-6:
            continue
        grow_a = speeds[i] * progress * span * 1.2
        grow_b = speeds[i + 1] * progress * span * 1.2
        if grow_a + grow_b >= span:
            strands.append(pts[a:b + 1])
            continue
        left = _slice_by_length(pts, cum, cum[a], cum[a] + grow_a)
        right = _slice_by_length(pts, cum, cum[b] - grow_b, cum[b])
        if len(left) >= 2:
            strands.append(left)
        if len(right) >= 2:
            strands.append(right)
    return strands


def draw_ink_bleed(canvas, strands: list[list[tuple[float, float]]], color: tuple[int, int, int], salt: int = 1) -> None:
    """Variable-width ink, plus a wider faint pass that soaks into the paper."""
    ink = ink_color(color)
    for index, strand in enumerate(strands):
        if len(strand) < 2:
            continue
        widths = ink_widths(len(strand) - 1, base=4.5, salt=salt + index * 17)
        soak = round_pen(9.0, ink, 36)
        core_color = ink
        for i, (a, b) in enumerate(zip(strand, strand[1:])):
            canvas.drawLine(a[0], a[1], b[0], b[1], soak)
            pen = round_pen(float(widths[i]), core_color, 230)
            canvas.drawLine(a[0], a[1], b[0], b[1], pen)


def grade(img: np.ndarray, t: float) -> np.ndarray:
    """Subtle vignette, a touch more contrast, edge-only chroma, 1-LSB dither.

    The centre stays put. This is the still version of
    vignette=PI/4, eq=saturation=1.1:contrast=1.05:brightness=-0.02
    and a 0.005 chroma ramp, kept lighter so captions remain readable.
    """
    h, w = img.shape[:2]
    ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    r = np.sqrt(xs * xs * 0.85 + ys * ys)
    vig = np.clip(1.0 - 0.14 * np.clip(r - 0.55, 0, 1) ** 1.4, 0.82, 1.0)
    out = img.astype(np.float32)
    out *= vig[..., None]
    out = (out - 8.0) * 1.04 + 8.0
    # Saturation falls off with the vignette. The centre stays vivid.
    luma = 0.2126 * out[:, :, 0] + 0.7152 * out[:, :, 1] + 0.0722 * out[:, :, 2]
    fade = (np.clip((r - 0.62) / 0.55, 0.0, 1.0) ** 1.3) * 0.34
    out = out * (1.0 - fade[..., None]) + luma[..., None] * fade[..., None]
    # Optical output, without a second barrel pass. Captions are already in frame
    # and the shift is one pixel at the rim only.
    return optical_output(np.clip(out, 0, 255).astype(np.uint8), t, barrel=False)


def spill_falloff(dist: float, radius: float = 80.0, gain: float = 1.0) -> float:
    """1/d^2 light around a glow. dist and radius are pixels."""
    r = max(1.0, float(radius))
    d = max(0.0, float(dist))
    return float(gain) / (1.0 + (d * d) / (r * r))


_SPILL_EFFECT = None


def _spill_effect():
    global _SPILL_EFFECT
    if _SPILL_EFFECT is None:
        _SPILL_EFFECT = skia.RuntimeEffect.MakeForShader("""
            uniform shader distmap;
            uniform float gain;
            uniform float radius;
            uniform float maxd;
            half4 main(float2 coord) {
                float d = distmap.eval(coord).r * maxd;
                float s = gain / (1.0 + (d * d) / (radius * radius));
                return half4(s, s, s, 1.0);
            }
        """)
    return _SPILL_EFFECT


def apply_light_spill(img: np.ndarray, dist: np.ndarray, color: tuple[int, int, int],
                      radius: float = 90.0, gain: float = 0.55, maxd: float = 420.0) -> np.ndarray:
    """Add a camera-space glow. `dist` is pixels to the glowing shape.

    The falloff is evaluated in a SkSL RuntimeEffect from a distance field.
    """
    if img.size == 0:
        return img
    h, w = img.shape[:2]
    field = np.clip(dist, 0.0, maxd) / maxd
    encoded = (field * 255.0).astype(np.uint8)
    rgba = np.dstack([encoded, np.zeros((h, w), np.uint8), np.zeros((h, w), np.uint8),
                      np.full((h, w), 255, np.uint8)])
    child = skia.Image.fromarray(rgba).makeShader()
    data = np.array([float(gain), float(radius), float(maxd)], np.float32)
    shader = _spill_effect().makeShader(skia.Data.MakeWithCopy(data.tobytes()), child, 1)
    surface = skia.Surface(w, h)
    paint = skia.Paint(AntiAlias=False)
    paint.setShader(shader)
    surface.getCanvas().drawPaint(paint)
    got = surface.makeImageSnapshot().toarray()
    # toarray is BGRA. The shader wrote the same value in RGB, so any channel works.
    amount = got[:, :, 0].astype(np.float32) / 255.0
    glow = np.array(color, np.float32)
    out = img.astype(np.float32) + amount[..., None] * glow
    return np.clip(out, 0, 255).astype(np.uint8)


_BARREL_MAPS: dict = {}


def barrel_distort(img: np.ndarray, k1: float = 0.005, k2: float = 0.003) -> np.ndarray:
    """Subtle lens barrel on one image. Call this on the map, never on captions.

    Matches ffmpeg lenscorrection: r_src = r * (1 + k1 r^2 + k2 r^4), with r
    normalised by half the frame width and the lens centred.
    """
    h, w = img.shape[:2]
    key = (h, w, round(k1, 6), round(k2, 6))
    coords = _BARREL_MAPS.get(key)
    if coords is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx = (w - 1) * 0.5
        cy = (h - 1) * 0.5
        # Each axis is -1..1, so k1=0.005 stays a few pixels even on a tall frame.
        nx = (xx - cx) / max(cx, 1.0)
        ny = (yy - cy) / max(cy, 1.0)
        r2 = nx * nx + ny * ny
        factor = 1.0 + k1 * r2 + k2 * r2 * r2
        coords = np.stack([(yy - cy) * factor + cy, (xx - cx) * factor + cx])
        _BARREL_MAPS[key] = coords
    from scipy.ndimage import map_coordinates
    out = np.empty_like(img)
    for channel in range(img.shape[2]):
        out[:, :, channel] = map_coordinates(img[:, :, channel], coords, order=1, mode="nearest")
    return out


def barrel_shift(x: float, y: float, w: int, h: int, k1: float = 0.005, k2: float = 0.003) -> tuple[float, float]:
    """Source pixel a destination pixel reads. The centre does not move."""
    cx = (w - 1) * 0.5
    cy = (h - 1) * 0.5
    nx = (x - cx) / max(cx, 1.0)
    ny = (y - cy) / max(cy, 1.0)
    r2 = nx * nx + ny * ny
    factor = 1.0 + k1 * r2 + k2 * r2 * r2
    return cx + (x - cx) * factor, cy + (y - cy) * factor


_GRAIN = None
GRAIN_OPACITY = 0.015


def _grain_texture() -> np.ndarray:
    global _GRAIN
    if _GRAIN is None:
        _GRAIN = np.random.default_rng(20261011).integers(0, 256, size=(192, 192), dtype=np.uint8)
    return _GRAIN


def overlay_grain(img: np.ndarray, t: float, fps: float = 30.0, opacity: float = GRAIN_OPACITY) -> np.ndarray:
    """Fixed fine grain, rotated 90/180/270/0 by frame, Overlay at 0.01–0.02.

    The rotation is a function of the frame index, so a re-render matches.
    """
    opacity = float(opacity)
    if opacity <= 0.0:
        return img
    h, w = img.shape[:2]
    frame = int(math.floor(float(t) * float(fps) + 1e-6))
    turns = (1, 2, 3, 0)[frame % 4]
    tile = np.rot90(_grain_texture(), turns)
    reps = (math.ceil(h / tile.shape[0]), math.ceil(w / tile.shape[1]))
    grain = np.tile(tile, reps)[:h, :w].astype(np.float32) / 255.0
    base = img.astype(np.float32) / 255.0
    layer = grain[..., None]
    over = np.where(base < 0.5, 2.0 * base * layer, 1.0 - 2.0 * (1.0 - base) * (1.0 - layer))
    mixed = base * (1.0 - opacity) + over * opacity
    return np.clip(mixed * 255.0, 0, 255).astype(np.uint8)


def box_luminance(img: np.ndarray, cx: float, cy: float, width: float, height: float) -> float:
    """Mean Rec.709 luminance of the pixels under a label, 0..1."""
    h, w = img.shape[:2]
    x0 = int(max(0, math.floor(cx - width * 0.5)))
    x1 = int(min(w, math.ceil(cx + width * 0.5)))
    y0 = int(max(0, math.floor(cy - height * 0.5)))
    y1 = int(min(h, math.ceil(cy + height * 0.5)))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    patch = img[y0:y1, x0:x1].astype(np.float32)
    y = 0.2126 * patch[:, :, 0] + 0.7152 * patch[:, :, 1] + 0.0722 * patch[:, :, 2]
    return float(y.mean() / 255.0)


def label_style(luminance: float) -> tuple[tuple[int, int, int], int]:
    """Ink RGB and soft-backing alpha. Above 70% luminance the ink goes dark."""
    if float(luminance) > 0.70:
        return (18, 20, 26), 150
    return (255, 248, 236), 0


def round_pen(width: float, color: tuple[int, int, int], alpha: int = 255) -> skia.Paint:
    pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    pen.setStrokeCap(skia.Paint.kRound_Cap)
    pen.setStrokeJoin(skia.Paint.kRound_Join)
    pen.setColor(skia.ColorSetARGB(alpha, color[0], color[1], color[2]))
    return pen
