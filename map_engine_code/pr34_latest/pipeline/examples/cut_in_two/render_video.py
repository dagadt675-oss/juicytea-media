#!/usr/bin/env python3
"""Render the Countries Cut in Two v3 short: 1080x1920, 60 fps, Mercator.

Country shapes are Natural Earth 50m (public domain). The uploaded voice line
is mixed once, aligned so "cheapest" hits the home move. The rest of the
narration was not in that file, so the picture carries those beats.
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

ROOT = Path(__file__).resolve().parents[2]  # pipeline/
PR34 = ROOT.parent
WORKSPACE = PR34.parents[1]
sys.path.insert(0, str(ROOT))

from jt.show.cut_in_two import build_cut_in_two_episode, word_time  # noqa: E402

W, H, FPS = 1080, 1920, 60
OCEAN = (18, 52, 78)
LAND = (168, 156, 124)
COAST = (86, 78, 62)
GRAT = (40, 78, 104)
FONT = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
GEOJSON = Path(__file__).resolve().parent / "ne_50m_admin_0_countries.geojson"
GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)
VO = PR34 / "assets/vo/cut_in_two_vo_once.wav"
OUT = WORKSPACE / "v/cut_in_two.mp4"


def ensure_geojson() -> None:
    if GEOJSON.exists() and GEOJSON.stat().st_size > 100_000:
        return
    print("downloading Natural Earth 50m", flush=True)
    urllib.request.urlretrieve(GEOJSON_URL, GEOJSON)


def load_rings() -> list[dict]:
    data = json.loads(GEOJSON.read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        iso = feature["properties"].get("ADM0_A3") or ""
        geometry = feature["geometry"]
        if geometry is None:
            continue
        polygons = (
            geometry["coordinates"]
            if geometry["type"] == "MultiPolygon"
            else [geometry["coordinates"]]
        )
        for polygon in polygons:
            if not polygon:
                continue
            outer = polygon[0]
            if len(outer) < 4:
                continue
            arr = np.asarray(outer, dtype=np.float64)
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
                }
            )
    return rings


def project(dlon: np.ndarray, lat: np.ndarray, lat0: float, span: float) -> np.ndarray:
    scale = W / max(span, 1.0)
    lat_c = np.clip(lat, -85.0, 85.0)
    merc = np.degrees(np.log(np.tan(np.pi / 4.0 + np.radians(lat_c) / 2.0)))
    merc0 = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(lat0) / 2.0)))
    x = W * 0.5 + dlon * scale
    y = H * 0.5 - (merc - merc0) * scale
    return np.column_stack([x, y]).astype(np.int32)


def pieces(lon: np.ndarray, lat: np.ndarray, lon0: float) -> list[tuple[np.ndarray, np.ndarray]]:
    dlon = (lon - lon0 + 180.0) % 360.0 - 180.0
    jump = np.where(np.abs(np.diff(dlon)) > 60.0)[0]
    cuts = [0, *(int(i) + 1 for i in jump), len(dlon)]
    out = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a >= 3:
            out.append((dlon[a:b], lat[a:b]))
    return out


def on_screen(pts: np.ndarray, margin: int = 80) -> bool:
    return bool(
        np.any(
            (pts[:, 0] > -margin)
            & (pts[:, 0] < W + margin)
            & (pts[:, 1] > -margin)
            & (pts[:, 1] < H + margin)
        )
    )


YELLOW = (255, 196, 48)
RED = (214, 40, 60)
INK = (20, 24, 32)
BLUE = (0, 120, 200)
GREEN = (0, 140, 70)


def _box(west, south, east, north):
    def inside(lon: float, lat: float) -> bool:
        return west <= lon <= east and south <= lat <= north

    return inside


def _alaska(lon: float, lat: float) -> bool:
    return lat > 50.0 and (lon < -129.0 or lon > 170.0)


HIGHLIGHTS = [
    (0.0, word_time(20), "USA", YELLOW, 150, _alaska),
    (word_time(22), word_time(34), "CAN", RED, 130, None),
    (word_time(36), word_time(37.2), "USA", YELLOW, 160, _alaska),
    (word_time(38), word_time(39.2), "MYS", YELLOW, 160, None),
    (word_time(45), word_time(61), "MYS", RED, 140, None),
    (word_time(61), word_time(86), "BRN", YELLOW, 170, None),
    (word_time(86), word_time(113), "OMN", RED, 140, None),
    (word_time(95), word_time(113), "ARE", YELLOW, 150, None),
    (word_time(135), word_time(155), "AGO", YELLOW, 170, _box(11.0, -6.2, 13.6, -4.2)),
    (word_time(137), word_time(155), "COD", BLUE, 120, None),
    (word_time(145), word_time(155), "AGO", GREEN, 120, _box(11.0, -18.0, 24.0, -6.3)),
    (word_time(167), word_time(80), "AZE", YELLOW, 170, _box(44.5, 38.7, 46.3, 39.8)),
    (word_time(169), word_time(80), "AZE", BLUE, 120, _box(46.3, 38.2, 51.0, 42.0)),
    (word_time(170), word_time(176), "ARM", (240, 130, 30), 130, None),
    (word_time(174), word_time(175), "IRN", (255, 255, 255), 90, None),
    (word_time(175), word_time(176), "ARM", (255, 255, 255), 90, None),
    (word_time(178), word_time(179), "TUR", (255, 255, 255), 90, None),
    (word_time(189), 80.0, "USA", YELLOW, 160, _alaska),
]


def active_highlights(t: float) -> list[tuple[str, tuple, int, object]]:
    found = []
    for t0, t1, iso, color, alpha, where in HIGHLIGHTS:
        if t0 <= t <= t1:
            found.append((iso, color, alpha, where))
    return found


LABELS = [
    (word_time(8), word_time(19), "ALASKA", -152, 64, None, INK, 42),
    (word_time(26), word_time(30), "BRITISH", -112, 58, None, (150, 20, 36), 36),
    (word_time(29), word_time(34), "CANADA", -108, 56, None, RED, 48),
    (word_time(45), word_time(50), "MALAYSIA", 102, 6, None, RED, 42),
    (word_time(48), word_time(53), "PENINSULA", 101.5, 3.5, None, INK, 32),
    (word_time(51), word_time(56), "BORNEO", 114, 1, None, INK, 40),
    (word_time(61), word_time(66), "BRUNEI", 114.7, 4.6, None, INK, 36),
    (word_time(64), word_time(69), "SARAWAK", 112.5, 2.5, None, RED, 32),
    (word_time(87), word_time(92), "MUSANDAM", 56.3, 26.2, None, RED, 36),
    (word_time(88), word_time(96), "STRAIT OF HORMUZ", 56.6, 26.6, None, (0, 90, 160), 28),
    (word_time(95), word_time(100), "UAE", 54.3, 23.8, None, INK, 36),
    (word_time(107), word_time(110), "OMAN", 57.5, 21.5, None, RED, 40),
    (word_time(135), word_time(142), "CABINDA", 12.3, -5.0, None, INK, 36),
    (word_time(141), word_time(145), "DR CONGO", 18.0, -2.5, None, BLUE, 36),
    (word_time(148), word_time(152), "ANGOLA", 17.5, -12.0, None, GREEN, 40),
    (word_time(167), word_time(172), "NAKHCHIVAN", 45.4, 39.2, None, INK, 32),
    (word_time(169), word_time(173), "AZERBAIJAN", 48.5, 40.4, None, BLUE, 32),
    (word_time(171), word_time(175), "ARMENIA", 44.5, 40.2, None, (240, 130, 30), 32),
    (word_time(174), word_time(176), "IRAN", 46.5, 38.2, None, INK, 32),
]

STAMPS = [
    (word_time(3), word_time(19), "$7.2M  ·  ≈2¢/ACRE  ·  1867", (450, 430), 40, RED),
    (word_time(17), word_time(21), "BORDER CHECK", (450, 520), 46, RED),
    (word_time(33), word_time(36), "STILL IN THE WAY", (450, 470), 44, RED),
    (word_time(41), word_time(44), "2 PIECES", (450, 470), 56, INK),
    (word_time(44), word_time(52), "1963", (450, 330), 60, INK),
    (word_time(63), word_time(71), "1890", (450, 330), 60, INK),
    (word_time(71), word_time(74), "RIGHT OUT OF THE MIDDLE", (450, 470), 36, INK),
    (word_time(81), word_time(86), "19 MI", (450, 470), 56, BLUE),
    (word_time(110), word_time(113), "EXIT OMAN", (450, 470), 48, RED),
    (word_time(117), word_time(121), "SAME TRICK", (450, 400), 48, INK),
    (word_time(124), word_time(129), "A WHOLE SEA", (450, 400), 48, (0, 90, 160)),
    (word_time(130), word_time(135), "1885", (450, 330), 60, INK),
    (word_time(151), word_time(155), "WRONG SIDE", (450, 470), 50, RED),
    (word_time(159), word_time(167), "1921", (450, 330), 60, INK),
    (word_time(180), word_time(183), "TURKEY  ·  11 KM", (450, 470), 42, RED),
    (word_time(182), word_time(185), "EXCEPT AZERBAIJAN", (450, 560), 40, INK),
    (word_time(184), word_time(80), "CHEAPEST SPLIT?", (450, 430), 46, INK),
]

CHIPS = [
    (word_time(114), word_time(130), "ALASKA", (250, 980), YELLOW, INK),
    (word_time(116), word_time(130), "MALAYSIA", (700, 980), RED, (255, 255, 255)),
    (word_time(119), word_time(130), "BRUNEI", (250, 1080), YELLOW, INK),
    (word_time(121), word_time(130), "OMAN", (700, 1080), RED, (255, 255, 255)),
]


def smoother(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def fade(t: float, t0: float, t1: float) -> float:
    if t < t0 or t > t1:
        return 0.0
    if t < t0 + 0.28:
        return smoother((t - t0) / 0.28)
    if t > t1 - 0.28:
        return smoother((t1 - t) / 0.28)
    return 1.0


def draw_map(frame: np.ndarray, rings, lon0: float, lat0: float, span: float, t: float) -> None:
    half_lat = span * (H / W) * 0.55 + 12.0
    highlights = active_highlights(t)
    land_parts = []
    hi_parts: dict[tuple, list] = {}
    for ring in rings:
        if ring["lat1"] < lat0 - half_lat or ring["lat0"] > lat0 + half_lat:
            continue
        for dlon, lat in pieces(ring["lon"], ring["lat"], lon0):
            if float(np.min(np.abs(dlon))) > span * 0.85 and float(np.max(dlon) - np.min(dlon)) < span:
                if float(np.min(dlon)) > span * 0.65 or float(np.max(dlon)) < -span * 0.65:
                    continue
            pts = project(dlon, lat, lat0, span)
            if not on_screen(pts):
                continue
            land_parts.append(pts)
            for iso, color, alpha, where in highlights:
                if ring["iso"] != iso:
                    continue
                if where is not None and not where(ring["clon"], ring["clat"]):
                    continue
                hi_parts.setdefault((color, alpha), []).append(pts)
    if land_parts:
        cv2.fillPoly(frame, land_parts, LAND[::-1])
        cv2.polylines(frame, land_parts, True, COAST[::-1], 1, cv2.LINE_AA)
    for (color, alpha), parts in hi_parts.items():
        overlay = frame.copy()
        cv2.fillPoly(overlay, parts, color[::-1])
        cv2.addWeighted(overlay, alpha / 255.0, frame, 1.0 - alpha / 255.0, 0, frame)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def pill(draw, xy, text, font, fill, ink) -> None:
    tw, th = text_size(draw, text, font)
    x, y = xy
    pad_x, pad_y = 22, 12
    rect = [x - tw / 2 - pad_x, y - th / 2 - pad_y, x + tw / 2 + pad_x, y + th / 2 + pad_y]
    draw.rounded_rectangle(rect, radius=18, fill=fill)
    draw.text((x - tw / 2, y - th / 2 - 4), text, font=font, fill=ink)


def draw_overlay(rgb: np.ndarray, lon0: float, lat0: float, span: float, t: float) -> np.ndarray:
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    for t0, t1, text, lon, lat, _xy, color, size in LABELS:
        alpha = fade(t, t0, t1)
        if alpha <= 0.02:
            continue
        dlon = (lon - lon0 + 180.0) % 360.0 - 180.0
        pts = project(np.array([dlon]), np.array([lat]), lat0, span)
        x, y = int(pts[0, 0]), int(pts[0, 1])
        if not (40 < x < W - 40 and 80 < y < H - 80):
            continue
        font = ImageFont.truetype(FONT, size)
        ink = tuple(int(c * alpha + 255 * (1 - alpha) * 0) for c in color)
        # Stroke so the name stays readable on yellow land.
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((x + dx, y + dy), text, font=font, fill=(255, 255, 255))
        draw.text((x, y), text, font=font, fill=ink)
    for t0, t1, text, xy, size, color in STAMPS:
        alpha = fade(t, t0, t1)
        if alpha <= 0.02:
            continue
        font = ImageFont.truetype(FONT, size)
        fill = tuple(int(255 * (1 - alpha) + c * alpha) for c in color)
        pill(draw, xy, text, font, fill, (255, 255, 255))
    for t0, t1, text, xy, fill, ink in CHIPS:
        alpha = fade(t, t0, t1)
        if alpha <= 0.02:
            continue
        font = ImageFont.truetype(FONT, 36)
        pill(draw, xy, text, font, fill, ink)
    draw_caption(draw, t)
    return np.asarray(image)


CAPTION_WORDS = [
    ("AND", 74.45, 74.57),
    ("THE", 74.61, 74.73),
    ("CHEAPEST", 74.83, 75.21),
    ("SPLIT", 75.33, 75.55),
    ("EVER?", 75.73, 75.99),
    ("THAT'S", 76.57, 76.83),
    ("THE", 76.87, 76.97),
    ("ONE", 77.03, 77.23),
    ("WHERE", 77.29, 77.55),
]


def draw_caption(draw: ImageDraw.ImageDraw, t: float) -> None:
    # Sentence groups, in the 64–72% band. Active word is cyan 0.04 s early.
    groups = [CAPTION_WORDS[0:3], CAPTION_WORDS[3:5], CAPTION_WORDS[5:]]
    shown = None
    for group in groups:
        if group[0][1] - 0.15 <= t <= group[-1][2] + 0.28:
            shown = group
    if shown is None:
        return
    font = ImageFont.truetype(FONT, 64)
    parts = []
    for text, start, end in shown:
        color = (0, 229, 255) if start - 0.04 <= t <= end else (255, 255, 255)
        parts.append((text, color))
    gap = 18
    widths = [text_size(draw, text, font)[0] for text, _ in parts]
    total = sum(widths) + gap * (len(parts) - 1)
    x = max(80, min(540 - total / 2, 900 - total))
    y = 1288
    for (text, color), width in zip(parts, widths):
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)):
            draw.text((x + dx, y + dy), text, font=font, fill=(14, 18, 26))
        draw.text((x, y), text, font=font, fill=color)
        x += width + gap


def render_frame(rings, lon: float, lat: float, span: float, t: float) -> np.ndarray:
    frame = np.empty((H, W, 3), dtype=np.uint8)
    frame[:] = OCEAN[::-1]
    draw_map(frame, rings, lon, lat, span, t)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return draw_overlay(rgb, lon, lat, span, t)


def encode(rings) -> None:
    spec = build_cut_in_two_episode()
    rig = spec.build_rig()
    frames = int(round(spec.total_duration * FPS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    delay = 74230
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-f", "lavfi", "-t", f"{spec.total_duration:.3f}",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-i", str(VO),
        "-filter_complex",
        f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay}[vo];"
        "[1:a][vo]amix=inputs=2:duration=first:normalize=0[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
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
            image = render_frame(rings, state["lon"], state["lat"], state["span"], t)
            proc.stdin.write(image.tobytes())
            if frame_index % (FPS * 5) == 0:
                print(f"frame {frame_index}/{frames} t={t:.1f}s", flush=True)
    finally:
        proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited {code}")
    print("wrote", OUT, flush=True)


def main() -> None:
    ensure_geojson()
    rings = load_rings()
    print("rings", len(rings), flush=True)
    encode(rings)


if __name__ == "__main__":
    main()
