#!/usr/bin/env python3
"""Render Countries Cut in Two at 1080x1920, 60 fps.

The picture is the NASA topo/bathymetry plate, morphed between Mercator and a
3D orthographic globe with the same projection as jt.show.camera. Country
shapes are Natural Earth 50m. Highlights fade in and out over at least 0.30s.
Pills keep their theme colors on one alpha (never white text fading in on a
white box). Labels that overlap are pushed apart.

The uploaded voice is one 3.68s sentence. It is mixed once, under the return
to Alaska, so "cheapest" lands on the closing pose. There is no second copy
and no 75s narration in that file.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PR34 = ROOT.parent
WORKSPACE = PR34.parents[1]
sys.path.insert(0, str(ROOT))

from jt.loop_tail import apply_seamless_audio_loop_tail  # noqa: E402
from jt.show.camera import smootherstep  # noqa: E402
from jt.show.captions import (  # noqa: E402
    active_karaoke_style,
    get_active_phrase_words,
    load_karaoke_words,
)
from jt.show.episodes import build_cut_in_two_episode  # noqa: E402
from jt.show.labels import resolve_2d_label_collisions  # noqa: E402
from jt.show.vfx_core import element_fade_and_exit_offset, label_pop_state  # noqa: E402

W, H, FPS = 1080, 1920, 60
FONT = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
GEOJSON = Path(__file__).resolve().parent / "ne_50m_admin_0_countries.geojson"
GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)
PLATE_PATH = Path(__file__).resolve().parent / "earth_topo.jpg"
PLATE_URL = "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg"
VO = PR34 / "assets/vo/cut_in_two_vo_once.wav"
VO_JSON = Path(__file__).resolve().parent / "vo_once.json"
OUT = WORKSPACE / "v/cut_in_two.mp4"
# "cheapest" (0.60s into the file) lands as the camera settles on Alaska.
VO_START = 87.40

PILL_RGB = {
    "red": ((212, 38, 42), (255, 255, 255)),
    "dark": ((16, 22, 34), (255, 255, 255)),
    "blue": ((14, 116, 218), (255, 255, 255)),
    "yellow": ((245, 197, 24), (14, 18, 26)),
    "white": ((248, 250, 252), (14, 18, 26)),
}

XS = np.arange(W, dtype=np.float64)[None, :]
YS = np.arange(H, dtype=np.float64)[:, None]
PLATE: np.ndarray | None = None
STARS: np.ndarray | None = None
WORDS = []
FONTS: dict[int, ImageFont.FreeTypeFont] = {}


def font(size: float) -> ImageFont.FreeTypeFont:
    key = max(8, int(round(size)))
    cached = FONTS.get(key)
    if cached is None:
        cached = ImageFont.truetype(FONT, key)
        FONTS[key] = cached
    return cached


def ensure_geojson() -> None:
    if GEOJSON.exists() and GEOJSON.stat().st_size > 100_000:
        return
    print("downloading Natural Earth 50m", flush=True)
    urllib.request.urlretrieve(GEOJSON_URL, GEOJSON)


def ensure_plate() -> np.ndarray:
    if not PLATE_PATH.exists() or PLATE_PATH.stat().st_size < 100_000:
        print("downloading satellite plate", flush=True)
        urllib.request.urlretrieve(PLATE_URL, PLATE_PATH)
    return np.asarray(Image.open(PLATE_PATH).convert("RGB"))


def make_stars() -> np.ndarray:
    rng = np.random.default_rng(3)
    img = np.zeros((H, W, 3), np.uint8)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    sky = (np.array([5, 8, 16]) * (1 - y) + np.array([14, 22, 36]) * y).astype(np.uint8)
    img[:] = sky[:, None, :]
    ys = rng.integers(0, H, 220)
    xs = rng.integers(0, W, 220)
    mag = rng.integers(160, 255, 220)
    img[ys, xs] = mag[:, None]
    return img


def load_rings() -> list[dict]:
    data = json.loads(GEOJSON.read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        iso = feature["properties"].get("ADM0_A3") or ""
        geometry = feature["geometry"]
        if geometry is None:
            continue
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            if not polygon or len(polygon[0]) < 4:
                continue
            arr = np.asarray(polygon[0], dtype=np.float64)
            lon, lat = arr[:, 0], arr[:, 1]
            rings.append(
                {
                    "iso": iso,
                    "lon": lon,
                    "lat": lat,
                    "clon": float(np.mean(lon)),
                    "clat": float(np.mean(lat)),
                    "lat0": float(np.min(lat)),
                    "lat1": float(np.max(lat)),
                    "n": int(lon.shape[0]),
                }
            )
    return rings


def load_words() -> list:
    raw = json.loads(VO_JSON.read_text(encoding="utf-8"))["words"]
    shifted = []
    for item in raw:
        shifted.append(
            {
                "text": item["text"],
                "start": round(float(item["start"]) + VO_START, 3),
                "end": round(float(item["end"]) + VO_START, 3),
            }
        )
    return load_karaoke_words(shifted)


def globe_radius(span: float) -> float:
    radius = (W * 0.44) * (68.0 / max(span, 18.0))
    return float(max(380.0, min(W * 0.95, radius)))


def _lookup(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    assert PLATE is not None
    height, width = PLATE.shape[:2]
    yi = np.clip(((90.0 - lat) / 180.0 * (height - 1)).astype(np.int32), 0, height - 1)
    xi = np.clip((np.mod(lon, 360.0) / 360.0 * (width - 1)).astype(np.int32), 0, width - 1)
    return PLATE[yi, xi]


def sample_mercator(lon0: float, lat0: float, span: float) -> np.ndarray:
    scale = W / max(span, 1e-3)
    lat_c = max(-84.0, min(84.0, lat0))
    cos_c = max(math.cos(math.radians(lat_c)), 0.22)
    merc0 = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(lat_c) / 2.0)))
    dlon = (XS - W * 0.5) / (scale * cos_c)
    merc = np.clip(merc0 - (YS - H * 0.5) / (scale * cos_c), -170.0, 170.0)
    lat = np.degrees(2.0 * np.arctan(np.exp(np.radians(merc))) - math.pi / 2.0)
    image = _lookup(lon0 + dlon, lat)
    if span < 30.0:
        texels = (W / max(span, 1.0)) / (PLATE.shape[1] / 360.0)
        kernel = min(41, int(texels * 2.0) | 1)
        if kernel >= 3:
            image = cv2.GaussianBlur(image, (kernel, kernel), 0)
    return image


def sample_ortho(lon0: float, lat0: float, span: float) -> tuple[np.ndarray, np.ndarray, float]:
    radius = globe_radius(span)
    x = (XS - W * 0.5) / radius
    y = -(YS - H * 0.5) / radius
    rho2 = x * x + y * y
    inside = rho2 <= 1.0
    z = np.sqrt(np.clip(1.0 - rho2, 0.0, 1.0))
    lat0_r = math.radians(lat0)
    sin_lat = np.clip(z * math.sin(lat0_r) + y * math.cos(lat0_r), -1.0, 1.0)
    lat = np.degrees(np.arcsin(sin_lat))
    lon = np.degrees(math.radians(lon0) + np.arctan2(x, z * math.cos(lat0_r) - y * math.sin(lat0_r)))
    sampled = _lookup(lon, lat)
    assert STARS is not None
    image = STARS.copy()
    image[inside] = sampled[inside]
    edge = inside & (rho2 > 0.90)
    image[edge] = (image[edge].astype(np.float32) * 0.78).astype(np.uint8)
    return image, inside, radius


def render_plate(lon: float, lat: float, span: float, w: float) -> np.ndarray:
    mix = float(smootherstep(w))
    if mix < 0.04:
        return sample_mercator(lon, lat, span)
    ortho, _inside, radius = sample_ortho(lon, lat, span)
    if mix > 0.96:
        image = ortho
    else:
        merc = sample_mercator(lon, lat, span).astype(np.float32)
        image = np.clip(merc * (1.0 - mix) + ortho.astype(np.float32) * mix, 0, 255).astype(np.uint8)
    if mix > 0.45:
        glow = int(90 * min(1.0, (mix - 0.45) / 0.4))
        cv2.circle(image, (W // 2, H // 2), int(radius) + 2, (40 + glow, 80 + glow, 110 + glow), 4, cv2.LINE_AA)
    return image


def project(lon: np.ndarray, lat: np.ndarray, cam_lon: float, cam_lat: float, span: float, w: float):
    mix = float(smootherstep(w))
    dlon = (lon - cam_lon + 180.0) % 360.0 - 180.0
    scale = W / max(span, 1e-3)
    lat_c = np.clip(lat, -84.0, 84.0)
    cam_lat_c = max(-84.0, min(84.0, cam_lat))
    merc = np.degrees(np.log(np.tan(np.pi / 4.0 + np.radians(lat_c) / 2.0)))
    merc0 = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(cam_lat_c) / 2.0)))
    cos_c = max(math.cos(math.radians(cam_lat_c)), 0.22)
    x_m = W * 0.5 + dlon * scale * cos_c
    y_m = H * 0.5 - (merc - merc0) * scale * cos_c

    lam = np.radians(dlon)
    phi = np.radians(lat)
    phi0 = math.radians(cam_lat)
    cos_ang = np.sin(phi0) * np.sin(phi) + np.cos(phi0) * np.cos(phi) * np.cos(lam)
    # Keep the front of the globe. A negative threshold lets the back
    # hemisphere fold into long chords across the disk.
    visible = (cos_ang >= 0.05) | (mix < 0.2)
    radius = globe_radius(span)
    x_o = W * 0.5 + radius * (np.cos(phi) * np.sin(lam))
    y_o = H * 0.5 - radius * (math.cos(phi0) * np.sin(phi) - math.sin(phi0) * np.cos(phi) * np.cos(lam))
    x = (1.0 - mix) * x_m + mix * x_o
    y = (1.0 - mix) * y_m + mix * y_o
    return x, y, visible


def polygon_runs(
    x: np.ndarray, y: np.ndarray, visible: np.ndarray, max_step: float
) -> list[np.ndarray]:
    """Split a ring where it crosses the limb or jumps across the screen."""
    step = np.hypot(np.diff(x, prepend=x[:1]), np.diff(y, prepend=y[:1]))
    keep = visible & (step <= max_step)
    cuts = np.where(np.diff(keep.astype(np.int8)) != 0)[0] + 1
    bounds = [0, *cuts.tolist(), len(x)]
    runs = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a >= 3 and bool(keep[a]):
            runs.append(np.column_stack([x[a:b], y[a:b]]).astype(np.int32))
    return runs


def ring_in_view(ring, lon0, lat0, span, w) -> bool:
    if w < 0.45:
        half = span * (H / W) * 0.62 + 6.0
        if ring["lat1"] < lat0 - half or ring["lat0"] > lat0 + half:
            return False
        dlon = (ring["clon"] - lon0 + 180.0) % 360.0 - 180.0
        return abs(dlon) < span * 0.75 + 6.0
    dlon = math.radians((ring["clon"] - lon0 + 180.0) % 360.0 - 180.0)
    phi = math.radians(ring["clat"])
    phi0 = math.radians(lat0)
    cos_c = math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(dlon)
    return cos_c > -0.08


def where_ok(kind: str, lon: float, lat: float) -> bool:
    if kind == "alaska":
        return lat > 50.0 and (lon < -129.0 or lon > 170.0)
    if kind == "cabinda":
        return 10.6 <= lon <= 14.0 and -6.5 <= lat <= -4.0
    if kind == "angola_main":
        return lat < -6.4
    if kind == "nakhchivan":
        return 44.7 <= lon <= 46.5 and 38.75 <= lat <= 39.95
    if kind == "azerbaijan_main":
        return lon > 46.4 and lat > 38.4
    return True


def active_highlights(spec, t: float):
    found = []
    for cue in spec.highlights:
        alpha = element_fade_and_exit_offset(t, cue.enter_t, cue.exit_t, 0.32, 0.32)[0]
        if alpha <= 0.02:
            continue
        found.append((cue, alpha))
    return found


def on_screen(x, y, margin=120) -> bool:
    return bool(np.any((x > -margin) & (x < W + margin) & (y > -margin) & (y < H + margin)))


def draw_map(frame: np.ndarray, rings, spec, lon0, lat0, span, w, t) -> None:
    highlights = active_highlights(spec, t)
    coasts = []
    fills: dict[tuple, list] = {}
    thick = 3 if span < 18 else 1
    for ring in rings:
        if not ring_in_view(ring, lon0, lat0, span, w):
            continue
        if (span > 80 or w > 0.55) and ring["n"] < 36:
            continue
        wanted = []
        for cue, alpha in highlights:
            if ring["iso"] != cue.iso_a3:
                continue
            if not where_ok(cue.where, ring["clon"], ring["clat"]):
                continue
            wanted.append((cue, alpha))
        if not wanted and span > 70 and ring["n"] < 24:
            continue
        x, y, visible = project(ring["lon"], ring["lat"], lon0, lat0, span, w)
        if w > 0.45:
            radius = globe_radius(span)
            visible = visible & (((x - W * 0.5) ** 2 + (y - H * 0.5) ** 2) <= (radius * 1.01) ** 2)
        if not on_screen(x, y):
            continue
        max_step = 64.0 if w > 0.4 else 220.0
        parts = polygon_runs(x, y, visible, max_step)
        if not parts:
            continue
        if thick == 1 or span < 40:
            coasts.extend(parts)
        for cue, alpha in wanted:
            key = (cue.fill_rgba, round(alpha, 3))
            fills.setdefault(key, []).extend(parts)
    for (rgba, alpha), parts in fills.items():
        overlay = frame.copy()
        cv2.fillPoly(overlay, parts, rgba[:3])
        weight = float(alpha) * (rgba[3] / 255.0)
        cv2.addWeighted(overlay, weight, frame, 1.0 - weight, 0, frame)
    if coasts:
        color = (236, 240, 244) if span < 40 and w < 0.45 else (176, 188, 198)
        cv2.polylines(frame, coasts, w < 0.4, color, thick, cv2.LINE_AA)


def text_size(draw: ImageDraw.ImageDraw, text: str, face) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0], box[3] - box[1]


def draw_overlay(rgb: np.ndarray, spec, lon0, lat0, span, w, t) -> np.ndarray:
    image = Image.fromarray(rgb).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    visible = []
    for label in spec.labels:
        alpha, _dx, _dy = element_fade_and_exit_offset(t, label.enter_t, label.exit_t, 0.30, 0.32)
        if alpha <= 0.04:
            continue
        x, y, vis = project(np.array([label.lon]), np.array([label.lat]), lon0, lat0, span, w)
        if not bool(vis[0]):
            continue
        px, py = float(x[0]), float(y[0])
        if not (-40 < px < W + 40 and 40 < py < H - 40):
            continue
        pop, _ = label_pop_state(t - label.enter_t, 0.30)
        face = font(label.font_size * max(pop, 0.4))
        tw, th = text_size(draw, label.text, face)
        visible.append((label, alpha, px, py, tw + 8, th + 6, face))
    if visible:
        boxes = [(px, py, tw, th) for _label, _a, px, py, tw, th, _f in visible]
        centers = resolve_2d_label_collisions(boxes, min_gap_px=18.0)
        for (label, alpha, _px, _py, _tw, _th, face), (cx, cy) in zip(visible, centers):
            ink = label.color_rgba[:3] + (int(255 * alpha),)
            stroke = (14, 18, 26, int(230 * alpha))
            tw, th = text_size(draw, label.text, face)
            origin = (cx - tw / 2, cy - th / 2)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                draw.text((origin[0] + dx, origin[1] + dy), label.text, font=face, fill=stroke)
            draw.text(origin, label.text, font=face, fill=ink)

    for pill in spec.pills:
        alpha, dx, dy = element_fade_and_exit_offset(t, pill.enter_t, pill.exit_t, 0.30, 0.32)
        if alpha <= 0.04:
            continue
        pop, _ = label_pop_state(t - pill.enter_t, 0.30)
        face = font(40 * max(pop, 0.85))
        bg, fg = PILL_RGB.get(pill.theme, PILL_RGB["dark"])
        tw, th = text_size(draw, pill.text, face)
        pad_x, pad_y = 28, 16
        box_w = tw + pad_x * 2
        box_h = th + pad_y * 2
        cx = max(70 + box_w / 2, min(W - 70 - box_w / 2, pill.screen_x + dx))
        cy = max(240 + box_h / 2, min(1180 - box_h / 2, pill.screen_y + dy))
        rect = [cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2]
        a = int(248 * alpha)
        draw.rounded_rectangle(rect, radius=18, fill=bg + (a,))
        draw.text((cx - tw / 2, cy - th / 2 - 2), pill.text, font=face, fill=fg + (int(255 * alpha),))

    phrase = get_active_phrase_words(WORDS, t)
    if phrase:
        styled = active_karaoke_style(phrase, t, map_has_yellow=True)
        face = font(66)
        gap = 16
        widths = [text_size(draw, text, face)[0] for text, _ in styled]
        total = sum(widths) + gap * (len(styled) - 1)
        x = max(70, min(540 - total / 2, 900 - total))
        y = 1288
        for (text, rgba), width in zip(styled, widths):
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                draw.text((x + dx, y + dy), text, font=face, fill=(14, 18, 26, 245))
            draw.text((x, y), text, font=face, fill=rgba[:3] + (255,))
            x += width + gap

    image.alpha_composite(overlay)
    return np.asarray(image.convert("RGB"))


def render_frame(rings, spec, state, t: float) -> np.ndarray:
    lon = ((state["lon"] + 180.0) % 360.0) - 180.0
    # Keep the unwrapped camera longitude for the globe arc direction.
    # Projection uses shortest-arc deltas, so the raw spline longitude is correct.
    lon = state["lon"]
    lat = state["lat"]
    span = state["span"]
    w = state["w"]
    plate = render_plate(lon, lat, span, w)
    draw_map(plate, rings, spec, lon, lat, span, w, t)
    return draw_overlay(plate, spec, lon, lat, span, w, t)


def stills(rings, spec, rig, times: list[float]) -> None:
    out_dir = Path("/tmp/cit_fix")
    out_dir.mkdir(parents=True, exist_ok=True)
    for t in times:
        state = rig.evaluate_all(min(t, spec.total_duration))
        image = render_frame(rings, spec, state, t)
        path = out_dir / f"t{t:05.1f}.jpg"
        Image.fromarray(image).save(path, quality=85)
        print(
            f"still {path} w={state['w']:.2f} span={state['span']:.1f} "
            f"lon={state['lon']:.1f} lat={state['lat']:.1f}",
            flush=True,
        )


def mix_audio(spec) -> np.ndarray:
    """Full-length stereo bed. The 3.68s line is placed once. Nothing is trimmed."""
    import wave

    with wave.open(str(VO)) as handle:
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
        voice = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if rate != 48000:
        raise RuntimeError(f"expected 48 kHz voice, got {rate}")
    total = int(round(spec.total_duration * 48000))
    start = int(round(VO_START * 48000))
    bed = np.zeros((total, 2), dtype=np.float32)
    end = min(total, start + voice.shape[0])
    bed[start:end, 0] = voice[: end - start] * 1.45
    bed[start:end, 1] = bed[start:end, 0]
    np.clip(bed, -1.0, 1.0, out=bed)
    return apply_seamless_audio_loop_tail(bed, tail_overlap_s=0.25)


def encode(rings, spec, rig) -> None:
    frames = int(round(spec.total_duration * FPS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    audio = (mix_audio(spec) * 32767.0).astype(np.int16)
    _encode_with_wav(rings, spec, rig, frames, audio)


def _encode_with_wav(rings, spec, rig, frames: int, audio_i16: np.ndarray) -> None:
    import wave

    wav_path = Path("/tmp/cit_bed.wav")
    with wave.open(str(wav_path), "w") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(48000)
        handle.writeframes(audio_i16.tobytes())
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(wav_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for frame_index in range(frames):
            t = frame_index / FPS
            state = rig.evaluate_all(min(t, spec.total_duration))
            image = render_frame(rings, spec, state, t)
            proc.stdin.write(image.tobytes())
            if frame_index % (FPS * 5) == 0:
                print(
                    f"frame {frame_index}/{frames} t={t:.1f}s "
                    f"w={state['w']:.2f} span={state['span']:.1f}",
                    flush=True,
                )
    finally:
        proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited {code}")
    print("wrote", OUT, flush=True)


def main() -> None:
    global PLATE, STARS, WORDS
    ensure_geojson()
    PLATE = ensure_plate()
    STARS = make_stars()
    WORDS = load_words()
    rings = load_rings()
    spec = build_cut_in_two_episode()
    rig = spec.build_rig()
    print("rings", len(rings), "plate", PLATE.shape, "dur", spec.total_duration, flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        times = [float(x) for x in sys.argv[2:]] or [0.4, 24.5, 41.5, 58.0, 74.8, 88.6]
        stills(rings, spec, rig, times)
        return
    encode(rings, spec, rig)


if __name__ == "__main__":
    main()
