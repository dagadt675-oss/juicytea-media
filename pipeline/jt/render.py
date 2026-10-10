"""Frame renderer. Orthographic globe and flat Mercator / LAEA, with a whip
between projections.

The camera holds, pushes in once at the open, or eases once into the next
shot. It does not sway. A loop tail, when set, eases the ending into frame 0.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
import skia

from jt.captions import groups_for
from jt.data import resolve_ids
from jt.draw import Safe, clamp_nontext, overlay, text_pixel_mask
from jt.loop_tail import (
    blend_toward_open,
    ease_span_toward_open,
    last_frame_time,
    opening_span,
    split_shots,
    tail_progress,
    tail_start,
)
from jt.project import ease_in_out, ease_out, laea_inverse, lerp_camera, resolve
from jt.themes import get_theme

FPS = 30


class Studio:
    def __init__(self, earth, spec, timeline, w: int, h: int):
        self.earth = earth
        self.spec = spec
        self.timeline = timeline
        self.w = w
        self.h = h
        self.theme = get_theme(spec.theme)
        self.groups = groups_for(timeline["words"])
        self.words = timeline["words"]
        dur = float(timeline["duration"])
        lines = timeline["lines"]
        spans = []
        for i, ln in enumerate(lines):
            a = 0.0 if i == 0 else float(ln["start"])
            b = float(lines[i + 1]["start"]) if i + 1 < len(lines) else dur
            spans.append((a, max(b, a + 1e-3)))
        self.spans = spans
        self.vignette = _vignette(w, h)
        rng = np.random.default_rng(5)
        self.star_x = rng.uniform(0, w, 90)
        self.star_y = rng.uniform(0, h * 0.42, 90)
        self.star_p = rng.uniform(0, math.tau, 90)

    def camera_at(self, t: float, phase: float):
        idx = 0
        for i, (a, _b) in enumerate(self.spans):
            if t >= a:
                idx = i
        a, _b = self.spans[idx]
        local = t - a
        cur = self.spec.lines[idx].camera
        whip = 0.0
        if idx == 0:
            cam = cur.copy()
            # One push-in, then a hold. Span only falls, so the shot never reverses.
            if cur.push:
                # Linear across the first second. The default ease finishes early,
                # and the rest of that second barely moves.
                intro = 1.0
                start = float(cur.push)
                if t < intro:
                    u = t / intro
                    cam.span = cur.span * (start - (start - 1.0) * u)
            else:
                intro = 1.15
                if t < intro:
                    e = ease_out(t / intro)
                    cam.span = cur.span * (1.85 - 0.85 * e)
        elif cur.cut:
            cam = cur.copy()
        else:
            prev = self.spec.lines[idx - 1].camera
            beat_dur = self.spans[idx][1] - self.spans[idx][0]
            # fly is one ease into the shot. Span, lon, and lat each move one way.
            fly = float(cur.fly) if cur.fly else min(1.35, max(0.7, beat_dur * 0.45))
            if local < fly and (prev.proj != cur.proj or prev.lon != cur.lon or prev.lat != cur.lat or prev.span != cur.span):
                u = local / fly
                if prev.proj != cur.proj:
                    if u < 0.5:
                        cam = prev.copy()
                        whip = ease_in_out(u / 0.5)
                    else:
                        cam = cur.copy()
                        whip = 1.0 - ease_in_out((u - 0.5) / 0.5)
                else:
                    cam = lerp_camera(prev, cur, u)
            else:
                cam = cur.copy()
        # A slow tighten for the whole film. Span only falls, including across beats.
        creep = float(getattr(cur, "creep", 0.0) or 0.0)
        if creep > 0:
            dur = float(self.timeline.get("duration") or 1.0)
            u = min(1.0, max(0.0, t / dur))
            cam.span = cam.span * (1.0 - creep * u)
        # After the last word, span eases one way into the frame-0 framing.
        start = tail_start(self.spec)
        if start is not None and t > start:
            dur = float(self.timeline.get("duration") or 0.0)
            end = last_frame_time(dur, FPS)
            u = tail_progress(t, start, end)
            if u > 0:
                cam.span = ease_span_toward_open(cam.span, opening_span(self.spec.lines[0].camera), u)
        view = resolve(cam.proj, cam.lon, cam.lat, max(4.0, cam.span), self.w, self.h, whip)
        return view, idx, local


def _reversals(values, eps: float) -> int:
    arr = np.asarray(values, np.float64)
    if len(arr) < 3:
        return 0
    signs = []
    for delta in np.diff(arr):
        if abs(float(delta)) < eps:
            continue
        signs.append(1 if delta > 0 else -1)
    changes = 0
    for a, b in zip(signs, signs[1:]):
        if a != b:
            changes += 1
    return changes


def direction_changes(spec, timeline, w: int, h: int, fps: int = 30) -> int:
    """Most reversals of lon, lat, or span inside any one shot.

    A push-in and a single ease are monotonic. A sway reverses over and over.
    """
    studio = Studio(None, spec, timeline, w, h)
    worst = 0
    for a, b in split_shots(studio.spans, tail_start(spec)):
        n = max(3, int(round((b - a) * fps)))
        times = np.linspace(a, max(a, b - 1.0 / fps), n)
        cols = [[], [], []]
        for t in times:
            view, _idx, _local = studio.camera_at(float(t), 0.0)
            cols[0].append(view.lon)
            cols[1].append(view.lat)
            cols[2].append(view.span)
        # Unwrap longitude so a dateline crossing is not a fake reversal.
        lon = np.asarray(cols[0], np.float64)
        if len(lon):
            acc = np.empty_like(lon)
            acc[0] = lon[0]
            acc[1:] = (np.diff(lon) + 180.0) % 360.0 - 180.0
            cols[0] = lon[0] + np.cumsum(np.r_[0.0, acc[1:]])
        worst = max(worst, *(_reversals(col, 0.02) for col in cols))
    return worst


def _vignette(w, h):
    ny = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    nx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    r = np.sqrt(ny * ny * 0.55 + nx * nx)
    vig = np.clip(1.0 - 0.55 * np.clip(r - 0.35, 0, 1) ** 2, 0.45, 1.0)
    return vig.astype(np.float32)


def _shade_sample(earth, lon, lat, highlights, theme, pulse: float, t: float):
    """lon/lat in degrees, any shape. Returns float RGB in 0..255, same shape + 3."""
    shape = lon.shape
    lon = np.asarray(lon, np.float64).ravel()
    lat = np.asarray(lat, np.float64).ravel()
    th, tw = earth.ids.shape
    xf = np.mod((lon + 180.0) / 360.0 * tw, tw)
    yf = np.clip((90.0 - lat) / 180.0 * th, 0, th - 1.001)
    xi = np.floor(xf).astype(np.int32) % tw
    yi = np.floor(yf).astype(np.int32)
    xi1 = (xi + 1) % tw
    yi1 = np.minimum(yi + 1, th - 1)
    fx = (xf - np.floor(xf)).astype(np.float32)
    fy = (yf - np.floor(yf)).astype(np.float32)
    s00 = earth.shade[yi, xi].astype(np.float32)
    s10 = earth.shade[yi, xi1].astype(np.float32)
    s01 = earth.shade[yi1, xi].astype(np.float32)
    s11 = earth.shade[yi1, xi1].astype(np.float32)
    shade = (s00 * (1 - fx) * (1 - fy) + s10 * fx * (1 - fy)
             + s01 * (1 - fx) * fy + s11 * fx * fy) / 220.0
    ids = earth.ids[yi, xi]
    land = ids > 0
    lat_u = np.clip(np.cos(np.radians(lat)), 0, 1).astype(np.float32)
    ocean = (np.array(theme["ocean"], np.float32) * (1 - lat_u)[:, None]
             + np.array(theme["ocean2"], np.float32) * lat_u[:, None])
    # Slow geographic tint. The frame-to-frame motion lives in _living_light.
    w1 = np.sin(np.radians(lon) * 3.2 + t * 1.4)
    w2 = np.cos(np.radians(lat) * 2.2 - t * 0.9)
    wave = 0.72 * w1 + 0.28 * w2
    ocean = ocean * (0.90 + 0.10 * wave.astype(np.float32)[:, None])
    col = np.empty((lon.shape[0], 3), np.float32)
    col[:] = np.array(theme["land"], np.float32)
    col *= shade[:, None]
    for n, (cid, rgb) in enumerate(highlights.items()):
        if rgb[0] < 0:
            rgb = theme["hi"] if n % 2 == 0 else theme["hi2"]
        m = ids == cid
        if not np.any(m):
            continue
        boost = pulse if n % 2 == 0 else (2 - pulse)
        col[m] = np.array(rgb, np.float32) * (shade[m] * boost * 1.35)[:, None]
    col = np.where(land[:, None], col, ocean)
    return col.reshape(shape + (3,))


def _living_light(col, across, t):
    """A broad wedge of light that keeps sliding, including on a held camera.

    Added, not multiplied: the map fills are dark, so a percentage swing barely
    moves the pixels and the frozen-frame gate fires on a hold. A triangle wave
    has a steady slope, so the change does not die out at the top of a sine.
    Blue-weighted so the lift cannot read as white, yellow, or orange text.
    """
    x = np.asarray(across, np.float32)
    phase = np.mod(x * 0.40 + t * 1.15, 1.0)
    tri = 1.0 - np.abs(2.0 * phase - 1.0)
    add = tri * np.float32(50.0)
    lift = np.stack((add * 0.22, add * 0.48, add * 0.82), axis=-1)
    return col + lift


def _paint_ortho(frame, earth, view, highlights, theme, phase, t):
    if theme.get("flat"):
        return
    r = view.r
    cx, cy = view.cx, view.cy
    h, w = frame.shape[:2]
    x0 = max(0, int(math.floor(cx - r)))
    x1 = min(w, int(math.ceil(cx + r)) + 1)
    y0 = max(0, int(math.floor(cy - r)))
    y1 = min(h, int(math.ceil(cy + r)) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    nx = (xx - cx) / r
    ny = (cy - yy) / r
    rho2 = nx * nx + ny * ny
    m = rho2 <= 1.0
    if not np.any(m):
        return
    nz = np.zeros(nx.shape, np.float32)
    nz[m] = np.sqrt(np.maximum(0.0, 1.0 - rho2[m])).astype(np.float32)
    lat0 = math.radians(view.lat)
    lon0 = math.radians(view.lon)
    sl, cl = math.sin(lat0), math.cos(lat0)
    nxm = nx[m].astype(np.float32)
    nym = ny[m].astype(np.float32)
    nzm = nz[m]
    lat = np.degrees(np.arcsin(np.clip(nzm * sl + nym * cl, -1, 1)))
    lon = np.degrees(lon0 + np.arctan2(nxm, nzm * cl - nym * sl))
    pulse = 0.86 + 0.14 * math.sin(t * 4.6)
    col = _shade_sample(earth, lon, lat, highlights, theme, pulse, t)
    az = t * 3.1
    light = np.clip(nzm * 0.70 + nym * (0.22 * math.cos(az)) - nxm * (0.42 * math.sin(az)), 0, 1)
    col = col * (0.40 + 0.60 * light)[:, None]
    col = _living_light(col, nxm, t)
    rim = np.clip(1.0 - nzm, 0, 1)[:, None] ** 1.5
    rim_c = np.array(theme["rim"], np.float32)
    col = col * (1 - 0.38 * rim) + rim_c * (rim * 0.42)
    if view.whip_dark:
        col *= 1.0 - 0.62 * view.whip_dark
    sub = frame[y0:y1, x0:x1]
    sub[m] = np.clip(col, 0, 255).astype(np.uint8)


def _paint_flat(frame, earth, view, highlights, theme, phase, t):
    if theme.get("flat"):
        return
    x0, y0, x1, y1 = view.rect
    if x1 <= x0 or y1 <= y0:
        return
    xs = np.arange(x0, x1, dtype=np.float32)
    ys = np.arange(y0, y1, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)
    if view.proj == "merc":
        scale = (x1 - x0) / max(view.span, 1.0)
        lat0 = float(np.clip(view.lat, -78, 78))
        merc0 = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat0) / 2)))
        lon = view.lon + (xx - view.cx) / scale
        merc = merc0 - (yy - view.cy) / scale
        lat = np.degrees(np.arctan(np.sinh(np.radians(np.clip(merc, -150, 150)))))
    else:
        pr = (x1 - x0) / math.radians(max(view.span, 1.0))
        xr = (xx - view.cx) / pr
        yr = (view.cy - yy) / pr
        lon, lat = laea_inverse(xr, yr, view.lon, view.lat)
    pulse = 0.86 + 0.14 * math.sin(t * 4.6)
    col = _shade_sample(earth, lon, lat, highlights, theme, pulse, t)
    col = _living_light(col, (xx - view.cx) / max(x1 - x0, 1.0) * 2.0, t)
    if view.whip_dark:
        col *= 1.0 - 0.62 * view.whip_dark
    # Soft edge so the flat map doesn't stamp a hard rectangle.
    fade = np.minimum(np.minimum(xx - x0, x1 - 1 - xx), np.minimum(yy - y0, y1 - 1 - yy))
    fade = np.clip(fade / 14.0, 0, 1).astype(np.float32)
    patch = frame[y0:y1, x0:x1].astype(np.float32)
    col = np.clip(col, 0, 255)
    frame[y0:y1, x0:x1] = (patch * (1 - fade[..., None]) + col * fade[..., None]).astype(np.uint8)


def _background(studio: Studio, t: float, phase: float) -> np.ndarray:
    h, w = studio.h, studio.w
    theme = studio.theme
    if theme.get("flat"):
        frame = np.empty((h, w, 3), np.uint8)
        frame[:] = theme["bg0"]
        from style.gold import drift_field
        drift_field(frame, t, studio.star_x[::2], studio.star_y[::2])
        return frame
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top = np.array(theme["bg0"], np.float32)
    bot = np.array(theme["bg1"], np.float32)
    grad = top * (1 - ys) + bot * ys
    frame = np.empty((h, w, 3), np.uint8)
    frame[:] = grad[:, None, :].astype(np.uint8)
    shift = (t * 22.0) % w
    twinkle = 0.65 + 0.35 * np.sin(t * 2.2 + studio.star_p)
    for x, y, k in zip(studio.star_x, studio.star_y, twinkle):
        xi = int((x + shift) % w)
        yi = int(y)
        if 0 <= xi < w - 1 and 0 <= yi < h - 1:
            val = int(70 + 80 * k)
            frame[yi:yi + 2, xi:xi + 2] = (val // 3, val // 2, val)
    return frame


def render_frame(studio: Studio, t: float, phase: float, line_index: int | None = None,
                 clock: float | None = None) -> tuple[np.ndarray, dict]:
    view, idx, local = studio.camera_at(t, phase)
    draw_t = t
    if line_index is not None:
        idx = line_index
        local = 0.0 if clock is None else float(clock)
        draw_t = local
    line = studio.spec.lines[idx]
    highlights = resolve_ids(studio.earth, line.visuals)
    frame = _background(studio, t, phase)
    if view.proj == "ortho":
        _paint_ortho(frame, studio.earth, view, highlights, studio.theme, phase, t)
    else:
        _paint_flat(frame, studio.earth, view, highlights, studio.theme, phase, t)
    clamp_nontext(frame)
    if not studio.theme.get("flat"):
        frame = np.clip(frame.astype(np.float32) * studio.vignette[..., None], 0, 255).astype(np.uint8)
    rgba = np.dstack([frame, np.full((studio.h, studio.w), 255, np.uint8)])
    surface = skia.Surface(studio.w, studio.h)
    canvas = surface.getCanvas()
    canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
    safe = Safe(canvas, studio.w, studio.h)
    claim = "" if studio.spec.voice.get("draw_claims") is False else line.claim
    info = overlay(
        canvas, safe, studio.earth, view, line.visuals,
        claim, line.sub, studio.words, studio.groups,
        draw_t, local, studio.theme, highlights, punch=(line.kind == "p"),
    )
    bgra = surface.makeImageSnapshot().toarray()
    rgb = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
    info["spills"] = safe.spills
    return rgb, info


def _unsafe_count(rgb: np.ndarray) -> int:
    h, w = rgb.shape[:2]
    mask = text_pixel_mask(rgb)
    unsafe = np.zeros(mask.shape, bool)
    unsafe[:int(0.12 * h), :] = True
    unsafe[int(0.80 * h):, :] = True
    unsafe[:, int(round(900 * w / 1080)):] = True
    return int(np.count_nonzero(mask & unsafe))


def _down(frame: np.ndarray) -> np.ndarray:
    return frame[::5, ::5].astype(np.int16)


def render_video(studio: Studio, path: Path, crf: int = 20) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(float(studio.timeline["duration"]) * FPS))
    n = max(n, 2)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{studio.w}x{studio.h}",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", str(crf), "-preset", "veryfast",
        "-g", "60", "-bf", "2",
        # Commas stay bare: this is an argv option, not a filtergraph.
        "-force_key_frames", f"expr:eq(n,0)+eq(n,{n - 1})",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-color_range", "tv",
        "-movflags", "+faststart",
        str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    diffs = []
    prev = None
    spills = 0
    unsafe_max = 0
    cap_px = []
    cap_center = []
    frame0 = None
    contact = []
    contact_at = {int(round(i * (n - 1) / 11)) for i in range(12)}
    tail = tail_start(studio.spec)
    tail_end = last_frame_time(float(studio.timeline.get("duration") or 0.0), FPS)
    tail_diffs = []
    try:
        for i in range(n):
            t = i / FPS
            phase = i / (n - 1) if n > 1 else 0.0
            img, info = render_frame(studio, t, phase)
            spills += info["spills"]
            if info["caption"]:
                cap_px.append(info["caption"]["px"])
                cap_center.append(info["caption"]["center_frac"])
            if i % 4 == 0:
                unsafe_max = max(unsafe_max, _unsafe_count(img))
            if i == 0:
                frame0 = img.copy()
            elif tail is not None and t > tail and frame0 is not None:
                # Same camera on both layers, so the land does not ghost.
                # Only the pills, the arc, and the plane trade places.
                u = tail_progress(t, tail, tail_end)
                if u >= 1.0:
                    img = frame0.copy()
                else:
                    opened, _open_info = render_frame(studio, t, phase, line_index=0, clock=0.0)
                    img = blend_toward_open(img, opened, u)
            if prev is not None:
                step = float(np.mean(np.abs(_down(img) - prev)) / 255.0)
                diffs.append(step)
                if i >= n - 15:
                    tail_diffs.append(step)
            prev = _down(img)
            if i in contact_at:
                contact.append((i / FPS, img))
            try:
                proc.stdin.write(img.tobytes())
            except BrokenPipeError:
                break
            if i % 30 == 0:
                print(f"frame {i}/{n}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg video encode failed ({code})")
    hook = float(np.mean(diffs[:FPS])) if len(diffs) >= FPS else float(np.mean(diffs) if diffs else 0)
    return {
        "frames": n,
        "fps": FPS,
        "width": studio.w,
        "height": studio.h,
        "spills": spills,
        "unsafe_max": unsafe_max,
        "caption_px_min": min(cap_px) if cap_px else 0,
        "caption_center_min": min(cap_center) if cap_center else 0,
        "caption_center_max": max(cap_center) if cap_center else 0,
        "hook_motion": hook,
        "frame_diff_min": min(diffs) if diffs else 0,
        "frozen_raw": _frozen_spans(diffs, FPS),
        "loop_raw_max": 0,
        "tail_step_max": max(tail_diffs) if tail_diffs else 0.0,
        "tail_steps": tail_diffs,
        "contact": contact,
    }


def render_stills(studio: Studio, times: list[float], dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    spills = 0
    unsafe_max = 0
    cap_px = []
    cap_center = []
    for t in times:
        phase = 0.0 if t <= 0 else min(0.999, t / float(studio.timeline["duration"]))
        img, info = render_frame(studio, t, phase)
        spills += info["spills"]
        unsafe_max = max(unsafe_max, _unsafe_count(img))
        if info["caption"]:
            cap_px.append(info["caption"]["px"])
            cap_center.append(info["caption"]["center_frac"])
        Image.fromarray(img).save(dest / f"t{t:05.2f}.png")
        print("still", f"{t:.2f}", flush=True)
    return {
        "spills": spills,
        "unsafe_max": unsafe_max,
        "caption_px_min": min(cap_px) if cap_px else 0,
        "caption_center_min": min(cap_center) if cap_center else 0,
        "caption_center_max": max(cap_center) if cap_center else 0,
        "times": times,
    }


def _frozen_spans(diffs: list[float], fps: int, thresh: float = 0.004) -> list[list[float]]:
    spans = []
    run = 0
    start = 0
    for i, d in enumerate(diffs):
        if d < thresh:
            if run == 0:
                start = i
            run += 1
        elif run:
            if run / fps >= 0.4:
                spans.append([round(start / fps, 3), round((start + run) / fps, 3)])
            run = 0
    if run and run / fps >= 0.4:
        spans.append([round(start / fps, 3), round((start + run) / fps, 3)])
    return spans


def save_contact(frames: list[tuple[float, np.ndarray]], path: Path) -> None:
    from PIL import Image, ImageDraw
    if not frames:
        return
    thumb_w = 180
    src_h, src_w = frames[0][1].shape[:2]
    thumb_h = int(thumb_w * src_h / src_w)
    cols = 4
    rows = int(math.ceil(len(frames) / cols))
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 22)), (8, 10, 14))
    draw = ImageDraw.Draw(sheet)
    for i, (t, img) in enumerate(frames):
        im = Image.fromarray(img).resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        c, r = i % cols, i // cols
        sheet.paste(im, (c * thumb_w, r * (thumb_h + 22)))
        draw.text((c * thumb_w + 6, r * (thumb_h + 22) + thumb_h + 4), f"{t:.1f}s", fill=(230, 230, 230))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=86)
