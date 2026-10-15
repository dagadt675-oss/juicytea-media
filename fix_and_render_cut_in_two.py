#!/usr/bin/env python3
"""62s Countries Cut in Two renderer.

Single-geometry Mercator/globe warp, satellite longitude aligned to the
NASA plate (x = 0 is longitude -180), Natural Earth 10m borders, and the
uploaded Brian voice on the closing line. The earlier sentences are the
same Brian voice, placed on the script's beats.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 60
LOOP_TAIL_SEC = 0.5
SR = 48000

WORKSPACE = Path("/workspace")
PR34 = WORKSPACE / "map_engine_code" / "pr34_latest"
CACHE = PR34 / "pipeline" / "examples" / "cut_in_two"
OUT_MP4 = WORKSPACE / "v" / "cut_in_two.mp4"
PLATE_PATH = CACHE / "earth_topo.jpg"
GEOJSON_10M = CACHE / "ne_10m_admin_0_countries.geojson"
UPLOADED_MP3 = Path(
    "/home/ubuntu/.cursor/projects/workspace/uploads/"
    "ElevenLabs_2026-10-14T10_49_31_Brian_-_Deep__Resonant_and_Comforting_pre_sp100_s50_sb75_v4_2_f0b8.mp3"
)
FONT_PATH = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"

SCRIPT_TIMED_LINES: List[Tuple[float, float, str]] = [
    (0.08, 4.30, "Russia sold Alaska to the United States for just seven point two million dollars."),
    (4.45, 7.60, "That was two cents an acre, but nobody checked the map."),
    (7.80, 12.10, "Because British Canada was sitting right in the way, cutting America into two pieces."),
    (12.30, 17.80, "In nineteen sixty-three, Malaysia did it even bigger, split across the South China Sea."),
    (18.00, 22.80, "And right on Borneo, British Sarawak bit nineteen miles right out of the middle of Brunei."),
    (23.00, 26.80, "Today Brunei is still two separate pieces of land."),
    (27.10, 34.80, "Now cross the Indian Ocean to the Strait of Hormuz, where Oman's Musandam tip is completely surrounded by the U A E."),
    (35.00, 40.40, "Alaska, Malaysia, Brunei, and Oman all pulled the exact same trick across a whole sea."),
    (40.60, 48.20, "In eighteen eighty-five, Congo took a strip to the Atlantic, leaving Angola's Cabinda stuck on the wrong side."),
    (48.40, 56.80, "And in nineteen twenty-one, Nakhchivan was cut off from Azerbaijan by Armenia, touching Turkey for just eleven kilometers."),
    (58.10, 61.78, "And the cheapest split ever? That's the one where"),
]


def smoothstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * (3.0 - 2.0 * u_c)


def smootherstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * u_c * (u_c * (u_c * 6.0 - 15.0) + 10.0)


def icon_pop_scale(elapsed_s: float, duration_s: float = 0.30, peak: float = 1.06) -> float:
    if elapsed_s <= 0.0:
        return 0.0
    if elapsed_s >= duration_s:
        return 1.0
    peak_at = 0.62 * duration_s
    if elapsed_s <= peak_at:
        return float(peak * smootherstep(elapsed_s / peak_at))
    settle = (elapsed_s - peak_at) / (duration_s - peak_at)
    return float(peak + (1.0 - peak) * smootherstep(settle))


def element_fade(t: float, enter_t: float, exit_t: float, fade_in: float = 0.30, fade_out: float = 0.30) -> Tuple[float, float, float]:
    fade_in = max(fade_in, 0.25)
    fade_out = max(fade_out, 0.25)
    if t <= enter_t or t >= exit_t + fade_out:
        return 0.0, 0.0, 0.0
    if t < enter_t + fade_in:
        return float(smootherstep((t - enter_t) / fade_in)), 0.0, 0.0
    if t > exit_t:
        u = min(1.0, (t - exit_t) / fade_out)
        s = float(smootherstep(u))
        return 1.0 - s, 16.0 * s, -10.0 * s
    return 1.0, 0.0, 0.0


@dataclass(frozen=True)
class CameraAnchor:
    t: float
    w: float
    lon: float
    lat: float
    span: float


class TimeParameterizedC2Spline:
    def __init__(self, t: np.ndarray, y: np.ndarray, v_start: float, v_end: float) -> None:
        self.t = np.asarray(t, dtype=np.float64)
        self.y = np.asarray(y, dtype=np.float64)
        self.h = np.diff(self.t)
        secants = np.diff(self.y) / self.h
        d = np.zeros(len(self.t), dtype=np.float64)
        d[0] = v_start
        d[-1] = v_end
        for i in range(1, len(self.t) - 1):
            if secants[i - 1] * secants[i] <= 0.0:
                d[i] = 0.0
            else:
                w1 = 2.0 * self.h[i] + self.h[i - 1]
                w2 = self.h[i] + 2.0 * self.h[i - 1]
                d[i] = (w1 + w2) / (w1 / secants[i - 1] + w2 / secants[i])
        self.tangents = d

    def eval_with_derivs(self, t_query: float) -> Tuple[float, float, float]:
        tq = float(np.clip(t_query, self.t[0], self.t[-1]))
        idx = int(np.searchsorted(self.t, tq, side="right")) - 1
        idx = max(0, min(idx, len(self.t) - 2))
        h = self.h[idx]
        y0, y1 = self.y[idx], self.y[idx + 1]
        v0, v1 = self.tangents[idx], self.tangents[idx + 1]
        u = float(np.clip((tq - self.t[idx]) / h, 0.0, 1.0))
        u2, u3, u4, u5 = u * u, u * u * u, u * u * u * u, u * u * u * u * u
        h0 = 1.0 - 10.0 * u3 + 15.0 * u4 - 6.0 * u5
        h1 = u - 6.0 * u3 + 8.0 * u4 - 3.0 * u5
        h2 = 10.0 * u3 - 15.0 * u4 + 6.0 * u5
        h3 = -4.0 * u3 + 7.0 * u4 - 3.0 * u5
        pos = h0 * y0 + h1 * (h * v0) + h2 * y1 + h3 * (h * v1)
        dh0 = -30.0 * u2 + 60.0 * u3 - 30.0 * u4
        dh1 = 1.0 - 18.0 * u2 + 32.0 * u3 - 15.0 * u4
        dh2 = 30.0 * u2 - 60.0 * u3 + 30.0 * u4
        dh3 = -12.0 * u2 + 28.0 * u3 - 15.0 * u4
        vel = (dh0 * y0 + dh1 * (h * v0) + dh2 * y1 + dh3 * (h * v1)) / h
        return float(pos), float(vel), 0.0


def hermite_segment(t, t0, t1, p0, v0, p1, v1) -> Tuple[float, float, float]:
    duration = max(t1 - t0, 1e-9)
    u = float(np.clip((t - t0) / duration, 0.0, 1.0))
    u2, u3 = u * u, u * u * u
    h00 = 2.0 * u3 - 3.0 * u2 + 1.0
    h10 = u3 - 2.0 * u2 + u
    h01 = -2.0 * u3 + 3.0 * u2
    h11 = u3 - u2
    pos = h00 * p0 + h10 * (duration * v0) + h01 * p1 + h11 * (duration * v1)
    dh00 = 6.0 * u2 - 6.0 * u
    dh10 = 3.0 * u2 - 4.0 * u + 1.0
    dh01 = -6.0 * u2 + 6.0 * u
    dh11 = 3.0 * u2 - 2.0 * u
    vel = (dh00 * p0 + dh10 * (duration * v0) + dh01 * p1 + dh11 * (duration * v1)) / duration
    return float(pos), float(vel), 0.0


class ContinuousCameraRig:
    def __init__(self, anchors: List[CameraAnchor], total_duration: float) -> None:
        self.total_duration = float(total_duration)
        self.loop_start_t = self.total_duration - LOOP_TAIL_SEC
        first = anchors[0]
        core = [a for a in anchors if a.t < self.loop_start_t - 0.8]
        core.append(CameraAnchor(
            t=self.loop_start_t,
            w=first.w,
            lon=first.lon - 0.18 * LOOP_TAIL_SEC,
            lat=first.lat - 0.04 * LOOP_TAIL_SEC,
            span=first.span / math.exp(-0.015 * LOOP_TAIL_SEC),
        ))
        t_arr = np.array([a.t for a in core], dtype=np.float64)
        self.spline_w = TimeParameterizedC2Spline(t_arr, np.array([a.w for a in core]), 0.0, 0.0)
        lon = np.rad2deg(np.unwrap(np.deg2rad([a.lon for a in core])))
        self.spline_lon = TimeParameterizedC2Spline(t_arr, lon, 0.18, 0.18)
        self.spline_lat = TimeParameterizedC2Spline(t_arr, np.array([a.lat for a in core]), 0.04, 0.04)
        self.spline_log_span = TimeParameterizedC2Spline(t_arr, np.log([a.span for a in core]), -0.015, -0.015)

    def evaluate_all(self, t: float) -> Dict[str, float]:
        t_clamped = float(np.clip(t, 0.0, self.total_duration))
        if t_clamped <= self.loop_start_t:
            w, _, _ = self.spline_w.eval_with_derivs(t_clamped)
            lon, _, _ = self.spline_lon.eval_with_derivs(t_clamped)
            lat, _, _ = self.spline_lat.eval_with_derivs(t_clamped)
            lspan, _, _ = self.spline_log_span.eval_with_derivs(t_clamped)
        else:
            w0, dw0, _ = self.spline_w.eval_with_derivs(self.loop_start_t)
            w1, dw1, _ = self.spline_w.eval_with_derivs(0.0)
            w, _, _ = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, w0, dw0, w1, dw1)
            lon0, dlon0, _ = self.spline_lon.eval_with_derivs(self.loop_start_t)
            lon1, dlon1, _ = self.spline_lon.eval_with_derivs(0.0)
            lon1 = lon0 + ((lon1 - lon0 + 180.0) % 360.0 - 180.0)
            lon, _, _ = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lon0, dlon0, lon1, dlon1)
            lat0, dlat0, _ = self.spline_lat.eval_with_derivs(self.loop_start_t)
            lat1, dlat1, _ = self.spline_lat.eval_with_derivs(0.0)
            lat, _, _ = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lat0, dlat0, lat1, dlat1)
            ls0, dls0, _ = self.spline_log_span.eval_with_derivs(self.loop_start_t)
            ls1, dls1, _ = self.spline_log_span.eval_with_derivs(0.0)
            lspan, _, _ = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, ls0, dls0, ls1, dls1)
        return {"w": w, "lon": lon, "lat": lat, "span": math.exp(lspan)}


@dataclass(frozen=True)
class Move:
    start_t: float
    duration: float
    w0: float
    w1: float
    lon0: float
    lon1: float
    lat0: float
    lat1: float
    span0: float
    span1: float
    drift_scale: float = -0.014
    drift_lon: float = 0.06
    drift_lat: float = 0.015


@dataclass(frozen=True)
class Highlight:
    iso: str
    enter_t: float
    exit_t: float
    rgba: Tuple[int, int, int, int]
    where: str = "all"


@dataclass(frozen=True)
class Label:
    text: str
    lon: float
    lat: float
    enter_t: float
    exit_t: float
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    size: float = 38.0


@dataclass(frozen=True)
class Pill:
    text: str
    x: float
    y: float
    enter_t: float
    exit_t: float
    theme: str = "dark"


@dataclass
class Episode:
    total_duration: float
    moves: List[Move]
    highlights: List[Highlight]
    labels: List[Label]
    pills: List[Pill]

    def build_rig(self) -> ContinuousCameraRig:
        anchors: List[CameraAnchor] = []
        for i, mv in enumerate(self.moves):
            if i == 0:
                anchors.append(CameraAnchor(mv.start_t, mv.w0, mv.lon0, mv.lat0, mv.span0))
            else:
                prev = anchors[-1]
                hold = max(0.0, mv.start_t - prev.t)
                if hold > 0.05:
                    span = float(np.clip(prev.span * math.exp(mv.drift_scale * hold), 3.3, 169.0))
                    anchors.append(CameraAnchor(
                        mv.start_t,
                        mv.w0,
                        prev.lon + mv.drift_lon * hold * (prev.span / 45.0),
                        prev.lat + mv.drift_lat * hold * (prev.span / 45.0),
                        span,
                    ))
            anchors.append(CameraAnchor(mv.start_t + mv.duration, mv.w1, mv.lon1, mv.lat1, mv.span1))
        return ContinuousCameraRig(anchors, self.total_duration)


def build_episode() -> Episode:
    moves = [
        Move(0.0, 1.45, 0.85, 0.0, -146.0, -148.0, 61.0, 63.0, 62.0, 32.0),
        Move(4.2, 1.35, 0.0, 0.0, -147.5, -140.0, 63.0, 60.0, 31.0, 26.0),
        Move(7.6, 1.45, 0.0, 0.15, -139.5, -108.0, 60.0, 56.0, 25.5, 42.0),
        Move(12.2, 1.75, 0.15, 0.85, -107.5, 108.5, 56.0, 4.5, 41.0, 48.0),
        Move(14.5, 1.35, 0.85, 0.0, 108.5, 108.5, 4.5, 4.0, 46.0, 21.0),
        Move(18.0, 1.50, 0.0, 0.0, 108.7, 114.85, 4.0, 4.75, 20.5, 4.6),
        Move(22.8, 1.25, 0.0, 0.0, 114.9, 115.05, 4.75, 4.68, 4.5, 4.2),
        Move(27.0, 1.65, 0.0, 0.75, 115.1, 56.25, 4.68, 25.4, 4.2, 28.0),
        Move(29.2, 1.40, 0.75, 0.0, 56.25, 56.25, 25.4, 25.8, 27.0, 5.4),
        Move(35.0, 1.55, 0.0, 0.92, 56.3, 44.0, 25.8, 12.0, 5.3, 56.0),
        Move(40.5, 1.55, 0.92, 0.0, 44.0, 12.6, 12.0, -5.6, 54.0, 6.2),
        Move(44.8, 1.30, 0.0, 0.0, 12.7, 15.8, -5.6, -9.8, 6.1, 14.5),
        Move(48.4, 1.65, 0.0, 0.65, 15.9, 45.6, -9.7, 39.5, 14.2, 22.0),
        Move(50.6, 1.40, 0.65, 0.0, 45.6, 45.5, 39.5, 39.35, 21.0, 5.8),
        Move(57.2, 1.85, 0.0, 0.85, 45.6, -146.0, 39.35, 61.0, 5.7, 62.0),
    ]
    highlights = [
        Highlight("USA", 0.0, 7.6, (242, 198, 65, 220), "alaska"),
        Highlight("CAN", 7.4, 12.2, (219, 94, 86, 210)),
        Highlight("MYS", 14.0, 20.2, (219, 94, 86, 210)),
        Highlight("BRN", 18.2, 27.0, (245, 197, 24, 230)),
        Highlight("OMN", 28.8, 35.0, (219, 94, 86, 220)),
        Highlight("ARE", 29.4, 35.0, (242, 198, 65, 210)),
        Highlight("COD", 41.2, 48.2, (88, 154, 186, 210)),
        Highlight("AGO", 41.5, 48.2, (245, 197, 24, 230), "cabinda"),
        Highlight("AGO", 44.2, 48.2, (82, 168, 104, 210), "angola_main"),
        Highlight("AZE", 50.2, 57.2, (88, 154, 186, 200), "azerbaijan_main"),
        Highlight("AZE", 50.4, 57.2, (245, 197, 24, 230), "nakhchivan"),
        Highlight("ARM", 50.8, 57.2, (235, 142, 70, 220)),
        Highlight("USA", 58.0, 62.2, (242, 198, 65, 220), "alaska"),
    ]
    labels = [
        Label("ALASKA", -151.0, 64.5, 1.2, 7.3),
        Label("BRITISH", -114.0, 56.5, 8.0, 9.8, (255, 170, 170, 255), 32),
        Label("CANADA", -108.0, 56.5, 9.8, 12.0, (255, 130, 130, 255), 44),
        Label("MALAYSIA", 102.2, 4.5, 14.6, 18.2, (255, 125, 125, 255)),
        Label("PENINSULA", 101.5, 2.2, 15.2, 18.2, size=32),
        Label("BORNEO", 114.5, 1.5, 15.6, 18.5),
        Label("BRUNEI", 114.65, 5.05, 18.8, 26.6),
        Label("SARAWAK", 113.8, 3.6, 19.4, 26.6, (255, 130, 130, 255), 32),
        Label("MUSANDAM", 56.25, 26.2, 29.8, 34.8, (255, 145, 145, 255), 32),
        Label("UAE", 54.4, 24.2, 30.2, 34.8),
        Label("OMAN", 57.6, 23.2, 30.8, 34.8, (255, 145, 145, 255)),
        Label("CABINDA", 12.15, -5.25, 41.8, 47.8),
        Label("DR CONGO", 18.5, -4.2, 42.4, 47.8, (135, 205, 255, 255)),
        Label("ANGOLA", 17.5, -12.2, 45.0, 47.8, (140, 235, 165, 255)),
        Label("NAKHCHIVAN", 45.4, 39.1, 51.0, 56.8, size=32),
        Label("ARMENIA", 44.6, 40.3, 51.4, 56.8, (255, 180, 105, 255), 34),
        Label("AZERBAIJAN", 47.8, 40.4, 51.2, 56.8, (135, 205, 255, 255), 32),
        Label("IRAN", 46.2, 37.8, 52.0, 56.8, size=32),
    ]
    pills = [
        Pill("$7.2M · ≈2¢/ACRE · 1867", 540, 320, 0.6, 5.2, "red"),
        Pill("BORDER CHECK", 540, 410, 5.2, 7.3, "red"),
        Pill("STILL IN THE WAY", 540, 340, 8.4, 11.8, "red"),
        Pill("2 PIECES", 540, 310, 12.4, 14.4, "dark"),
        Pill("1963", 540, 310, 14.5, 17.8, "dark"),
        Pill("1890", 540, 310, 18.6, 21.8, "dark"),
        Pill("19 MI", 540, 310, 22.0, 26.6, "blue"),
        Pill("RIGHT OUT OF THE MIDDLE", 540, 400, 22.4, 26.6, "dark"),
        Pill("STRAIT OF HORMUZ", 540, 310, 27.6, 31.4, "blue"),
        Pill("EXIT OMAN", 540, 310, 31.6, 34.8, "red"),
        Pill("SAME TRICK", 540, 290, 35.4, 40.0, "dark"),
        Pill("A WHOLE SEA", 540, 380, 35.8, 40.0, "blue"),
        Pill("ALASKA", 310, 480, 36.0, 40.0, "yellow"),
        Pill("MALAYSIA", 770, 480, 36.3, 40.0, "red"),
        Pill("BRUNEI", 310, 575, 36.6, 40.0, "yellow"),
        Pill("OMAN", 770, 575, 36.9, 40.0, "red"),
        Pill("1885", 540, 310, 41.0, 44.2, "dark"),
        Pill("WRONG SIDE", 540, 310, 44.4, 47.8, "red"),
        Pill("1921", 540, 310, 48.8, 52.0, "dark"),
        Pill("TURKEY · 11 KM", 540, 310, 52.2, 56.8, "red"),
        Pill("EXCEPT AZERBAIJAN", 540, 400, 53.0, 56.8, "dark"),
    ]
    return Episode(62.0, moves, highlights, labels, pills)


PILL_RGB = {
    "red": ((212, 38, 42), (255, 255, 255)),
    "dark": ((16, 22, 34), (255, 255, 255)),
    "blue": ((14, 116, 218), (255, 255, 255)),
    "yellow": ((245, 197, 24), (14, 18, 26)),
    "white": ((248, 250, 252), (14, 18, 26)),
}

GRID_STEP = 8
GX_1D = np.linspace(0.0, float(W), W // GRID_STEP + 1)
GY_1D = np.linspace(0.0, float(H), H // GRID_STEP + 1)
GX, GY = np.meshgrid(GX_1D, GY_1D)
FULL_XS = np.arange(W, dtype=np.float32)[None, :]
FULL_YS = np.arange(H, dtype=np.float32)[:, None]
FONTS: Dict[int, ImageFont.FreeTypeFont] = {}
PLATE: np.ndarray | None = None
STARS: np.ndarray | None = None


def font(size: float) -> ImageFont.FreeTypeFont:
    key = max(10, int(round(size)))
    face = FONTS.get(key)
    if face is None:
        face = ImageFont.truetype(FONT_PATH, key)
        FONTS[key] = face
    return face


def globe_radius(span: float) -> float:
    radius = (W * 0.44) * (68.0 / max(span, 18.0))
    return float(max(390.0, min(W * 0.96, radius)))


def project(lon, lat, cam_lon, cam_lat, span, w):
    mix = float(smootherstep(w))
    dlon = (lon - cam_lon + 180.0) % 360.0 - 180.0
    scale = W / max(span, 1e-3)
    lat_c = np.clip(lat, -84.0, 84.0)
    cam_lat_c = max(-84.0, min(84.0, cam_lat))
    merc = np.degrees(np.log(np.tan(math.pi / 4.0 + np.radians(lat_c) / 2.0)))
    merc0 = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(cam_lat_c) / 2.0)))
    cos_c = max(math.cos(math.radians(cam_lat_c)), 0.22)
    x_m = W * 0.5 + dlon * scale * cos_c
    y_m = H * 0.5 - (merc - merc0) * scale * cos_c
    lam = np.radians(dlon)
    phi = np.radians(lat)
    phi0 = math.radians(cam_lat)
    cos_ang = math.sin(phi0) * np.sin(phi) + math.cos(phi0) * np.cos(phi) * np.cos(lam)
    visible = (cos_ang >= 0.02) | (mix < 0.15)
    radius = globe_radius(span)
    x_o = W * 0.5 + radius * (np.cos(phi) * np.sin(lam))
    y_o = H * 0.5 - radius * (math.cos(phi0) * np.sin(phi) - math.sin(phi0) * np.cos(phi) * np.cos(lam))
    return (1.0 - mix) * x_m + mix * x_o, (1.0 - mix) * y_m + mix * y_o, visible


def load_plate() -> np.ndarray:
    raw = np.asarray(Image.open(PLATE_PATH).convert("RGB"))
    soft = cv2.GaussianBlur(raw, (0, 0), 1.4)
    return cv2.addWeighted(raw, 1.18, soft, -0.18, 0)


def make_stars() -> np.ndarray:
    rng = np.random.default_rng(7)
    img = np.zeros((H, W, 3), np.uint8)
    y = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    sky = (np.array([4, 7, 15]) * (1.0 - y) + np.array([12, 19, 32]) * y).astype(np.uint8)
    img[:] = sky[:, None, :]
    ys = rng.integers(0, H, 260)
    xs = rng.integers(0, W, 260)
    img[ys, xs] = rng.integers(150, 255, 260)[:, None]
    return img


def render_plate(cam_lon: float, cam_lat: float, span: float, w: float) -> np.ndarray:
    assert PLATE is not None and STARS is not None
    mix = float(smootherstep(w))
    plate_h, plate_w = PLATE.shape[:2]
    scale = W / max(span, 1e-3)
    cam_lat_c = max(-84.0, min(84.0, cam_lat))
    cos_c = max(math.cos(math.radians(cam_lat_c)), 0.22)
    merc0 = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(cam_lat_c) / 2.0)))
    dlon_m = (GX - W * 0.5) / (scale * cos_c)
    merc_y = np.clip(merc0 - (GY - H * 0.5) / (scale * cos_c), -170.0, 170.0)
    lat_m = np.degrees(2.0 * np.arctan(np.exp(np.radians(merc_y))) - math.pi / 2.0)

    radius = globe_radius(span)
    nx = (GX - W * 0.5) / radius
    ny = -(GY - H * 0.5) / radius
    rho2 = np.minimum(nx * nx + ny * ny, 0.9995)
    z = np.sqrt(1.0 - rho2)
    phi0 = math.radians(cam_lat)
    sin_lat = np.clip(z * math.sin(phi0) + ny * math.cos(phi0), -1.0, 1.0)
    lat_o = np.degrees(np.arcsin(sin_lat))
    dlon_o = np.degrees(np.arctan2(nx, z * math.cos(phi0) - ny * math.sin(phi0)))

    dlon_est = (1.0 - mix) * dlon_m + mix * dlon_o
    lat_est = (1.0 - mix) * lat_m + mix * lat_o
    if 0.02 < mix < 0.98:
        for _ in range(2):
            x_cur, y_cur, _ = project(cam_lon + dlon_est, lat_est, cam_lon, cam_lat, span, w)
            eff_x = (1.0 - mix) * (scale * cos_c) + mix * (radius * math.pi / 180.0)
            eff_y = eff_x
            dlon_est = np.clip(dlon_est + (GX - x_cur) / np.maximum(eff_x, 1.0), -179.0, 179.0)
            lat_est = np.clip(lat_est - (GY - y_cur) / np.maximum(eff_y, 1.0), -85.0, 85.0)

    dlon_full = cv2.resize(dlon_est.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    lat_full = cv2.resize(lat_est.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    # NASA plate: column 0 is longitude -180, not Greenwich.
    map_x = (np.mod(cam_lon + dlon_full + 180.0, 360.0) / 360.0 * (plate_w - 1)).astype(np.float32)
    map_y = np.clip((90.0 - lat_full) / 180.0 * (plate_h - 1), 0, plate_h - 1).astype(np.float32)
    sampled = cv2.remap(PLATE, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
    if mix < 0.015:
        return sampled

    rx = (1.0 - mix) * (W * 0.52) + mix * radius
    ry = (1.0 - mix) * (H * 0.52) + mix * radius
    exponent = (1.0 - mix) * 12.0 + mix * 2.0
    dxn = np.abs(FULL_XS - W * 0.5) / rx
    dyn = np.abs(FULL_YS - H * 0.5) / ry
    dist = (np.power(dxn, exponent) + np.power(dyn, exponent)) ** (1.0 / exponent)
    inside = dist <= 1.0
    shade = np.clip(1.0 - 0.22 * mix * np.clip((dist - 0.84) / 0.16, 0.0, 1.0), 0.74, 1.0)
    shaded = (sampled.astype(np.float32) * shade[:, :, None]).astype(np.uint8)
    frame = STARS.copy()
    frame[inside] = shaded[inside]
    if mix > 0.25:
        rim = (dist >= 0.988) & (dist <= 1.015)
        alpha = float(smoothstep((mix - 0.25) / 0.6)) * 0.7
        glow = np.array([115, 185, 245], dtype=np.float32)
        frame[rim] = np.clip(frame[rim].astype(np.float32) * (1 - alpha) + glow * alpha, 0, 255).astype(np.uint8)
    return frame


def load_rings() -> list[dict]:
    data = json.loads(GEOJSON_10M.read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        props = feature.get("properties") or {}
        iso = props.get("ADM0_A3") or props.get("ISO_A3") or ""
        geometry = feature.get("geometry")
        if not geometry:
            continue
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            if not polygon or len(polygon[0]) < 4:
                continue
            arr = np.asarray(polygon[0], dtype=np.float64)
            lon, lat = arr[:, 0], arr[:, 1]
            rings.append({
                "iso": iso,
                "lon": lon,
                "lat": lat,
                "clon": float(lon.mean()),
                "clat": float(lat.mean()),
                "lat0": float(lat.min()),
                "lat1": float(lat.max()),
                "n": int(lon.shape[0]),
            })
    return rings


def where_ok(kind: str, lon: float, lat: float) -> bool:
    if kind == "alaska":
        return lat > 51.0 and (lon < -129.5 or lon > 170.0)
    if kind == "cabinda":
        return 11.5 <= lon <= 13.2 and -6.05 <= lat <= -4.2
    if kind == "angola_main":
        return lat < -6.05
    if kind == "nakhchivan":
        return 44.7 <= lon <= 46.2 and 38.75 <= lat <= 39.85
    if kind == "azerbaijan_main":
        return lon > 46.1 or lat > 39.85
    return True


def ring_in_view(ring, lon0, lat0, span, w) -> bool:
    if w < 0.45:
        half = span * (H / W) * 0.68 + 8.0
        if ring["lat1"] < lat0 - half or ring["lat0"] > lat0 + half:
            return False
        dlon = (ring["clon"] - lon0 + 180.0) % 360.0 - 180.0
        return abs(dlon) < span * 0.9 + 8.0
    dlon = math.radians((ring["clon"] - lon0 + 180.0) % 360.0 - 180.0)
    phi = math.radians(ring["clat"])
    phi0 = math.radians(lat0)
    return math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(dlon) > -0.05


def split_runs(x, y, visible, max_step: float) -> list[np.ndarray]:
    step = np.hypot(np.diff(x, prepend=x[:1]), np.diff(y, prepend=y[:1]))
    keep = visible & (step <= max_step)
    cuts = np.where(np.diff(keep.astype(np.int8)) != 0)[0] + 1
    bounds = [0, *cuts.tolist(), len(x)]
    runs = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a >= 2 and bool(keep[a]):
            runs.append(np.column_stack([x[a:b], y[a:b]]).astype(np.int32))
    return runs


def draw_map(frame, rings, spec: Episode, lon0, lat0, span, w, t) -> None:
    highlights = []
    for cue in spec.highlights:
        alpha = element_fade(t, cue.enter_t, cue.exit_t)[0]
        if alpha > 0.02:
            highlights.append((cue, alpha))
    coasts = []
    fills: dict = {}
    thick = 3 if span < 14 else (2 if span < 35 else 1)
    stride_cap = 80 if span > 40 else (160 if span > 15 else 500)
    for ring in rings:
        if not ring_in_view(ring, lon0, lat0, span, w):
            continue
        wanted = [
            (cue, alpha)
            for cue, alpha in highlights
            if ring["iso"] == cue.iso and where_ok(cue.where, ring["clon"], ring["clat"])
        ]
        if not wanted and span > 50 and ring["n"] < 40:
            continue
        step = max(1, ring["n"] // stride_cap)
        lon = ring["lon"][::step]
        lat = ring["lat"][::step]
        x, y, visible = project(lon, lat, lon0, lat0, span, w)
        if not np.any((x > -180) & (x < W + 180) & (y > -180) & (y < H + 180)):
            continue
        runs = split_runs(x, y, visible, 110.0 if w > 0.4 else 280.0)
        if runs and (wanted or span < 70 or ring["n"] >= 40):
            coasts.extend(runs)
        if wanted:
            for run in runs:
                if len(run) < 3:
                    continue
                jumps = np.hypot(np.diff(run[:, 0].astype(np.float32)), np.diff(run[:, 1].astype(np.float32)))
                if len(jumps) and float(jumps.max()) > 280:
                    continue
                for cue, alpha in wanted:
                    fills.setdefault((cue.rgba, round(alpha, 3)), []).append(run)
    for (rgba, alpha), polys in fills.items():
        overlay = frame.copy()
        cv2.fillPoly(overlay, polys, rgba[:3], lineType=cv2.LINE_AA)
        weight = float(alpha) * (rgba[3] / 255.0)
        cv2.addWeighted(overlay, weight, frame, 1.0 - weight, 0, frame)
    if coasts:
        color = (238, 242, 246) if span < 40 and w < 0.45 else (176, 190, 202)
        cv2.polylines(frame, coasts, False, color, thick, cv2.LINE_AA)


def collide(boxes, gap=18.0):
    centers = [[b[0], b[1]] for b in boxes]
    sizes = [(b[2], b[3]) for b in boxes]
    for _ in range(12):
        moved = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                dx = centers[j][0] - centers[i][0]
                dy = centers[j][1] - centers[i][1]
                ox = (sizes[i][0] + sizes[j][0]) * 0.5 + gap - abs(dx)
                oy = (sizes[i][1] + sizes[j][1]) * 0.5 + gap - abs(dy)
                if ox > 0 and oy > 0:
                    moved = True
                    if oy <= ox * 1.4:
                        shift = 0.52 * oy * (1 if dy >= 0 else -1)
                        centers[i][1] -= shift
                        centers[j][1] += shift
                    else:
                        shift = 0.52 * ox * (1 if dx >= 0 else -1)
                        centers[i][0] -= shift
                        centers[j][0] += shift
        if not moved:
            break
    return [(max(115, min(880, c[0])), max(255, min(1190, c[1]))) for c in centers]


def text_wh(draw, text, face):
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0], box[3] - box[1]


def draw_overlay(rgb, spec: Episode, words, lon0, lat0, span, w, t):
    image = Image.fromarray(rgb).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    visible = []
    for label in spec.labels:
        alpha, _, _ = element_fade(t, label.enter_t, label.exit_t, 0.28, 0.30)
        if alpha <= 0.04:
            continue
        x, y, vis = project(np.array([label.lon]), np.array([label.lat]), lon0, lat0, span, w)
        if not bool(vis[0]):
            continue
        px, py = float(x[0]), float(y[0])
        if not (40 < px < W - 40 and 160 < py < H - 340):
            continue
        pop = icon_pop_scale(t - label.enter_t, 0.30, 1.06)
        face = font(label.size * max(pop, 0.55))
        tw, th = text_wh(draw, label.text, face)
        visible.append((label, alpha, px, py, tw + 12, th + 8, face))
    if visible:
        centers = collide([(a[2], a[3], a[4], a[5]) for a in visible])
        for (label, alpha, _px, _py, _tw, _th, face), (cx, cy) in zip(visible, centers):
            tw, th = text_wh(draw, label.text, face)
            ox, oy = cx - tw / 2, cy - th / 2
            ink = label.color[:3] + (int(255 * alpha),)
            stroke = (10, 14, 22, int(235 * alpha))
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                draw.text((ox + dx, oy + dy), label.text, font=face, fill=stroke)
            draw.text((ox, oy), label.text, font=face, fill=ink)
    for pill in spec.pills:
        alpha, dx, dy = element_fade(t, pill.enter_t, pill.exit_t, 0.28, 0.30)
        if alpha <= 0.04:
            continue
        face = font(38 * max(icon_pop_scale(t - pill.enter_t, 0.30, 1.06), 0.85))
        bg, fg = PILL_RGB[pill.theme]
        tw, th = text_wh(draw, pill.text, face)
        bw, bh = tw + 52, th + 30
        cx = max(75 + bw / 2, min(W - 75 - bw / 2, pill.x + dx))
        cy = max(240 + bh / 2, min(1180 - bh / 2, pill.y + dy))
        rect = [cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2]
        draw.rounded_rectangle(rect, radius=18, fill=bg + (int(246 * alpha),), outline=(255, 255, 255, int(60 * alpha)), width=2)
        draw.text((cx - tw / 2, cy - th / 2 - 1), pill.text, font=face, fill=fg + (int(255 * alpha),))

    phrase = None
    chunks = []
    for group in words:
        for index in range(0, len(group), 4):
            chunks.append(group[index:index + 4])
    for group in chunks:
        if group and group[0]["start"] - 0.08 <= t <= group[-1]["end"] + 0.14:
            phrase = group
            break
    if phrase:
        face = font(64)
        gap = 16
        widths = [text_wh(draw, wds["text"], face)[0] for wds in phrase]
        total = sum(widths) + gap * (len(phrase) - 1)
        if total > 840:
            face = font(max(52, 64 * 840 / total))
            widths = [text_wh(draw, wds["text"], face)[0] for wds in phrase]
            total = sum(widths) + gap * (len(phrase) - 1)
        x = max(70, min(500 - total / 2, 900 - total))
        y = 1296
        lead = t + 0.04
        for wds, width in zip(phrase, widths):
            active = wds["start"] <= lead <= wds["end"]
            color = (0, 229, 255, 255) if active else (255, 255, 255, 255)
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                draw.text((x + dx, y + dy), wds["text"], font=face, fill=(10, 14, 22, 245))
            draw.text((x, y), wds["text"], font=face, fill=color)
            x += width + gap
    image.alpha_composite(overlay)
    return np.asarray(image.convert("RGB"))


def _duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        text=True,
    )
    return float(out.strip())


def _to_wav(src: Path, dst: Path, atempo: float = 1.0) -> None:
    filters = []
    rate = atempo
    while rate > 1.35:
        filters.append("atempo=1.35")
        rate /= 1.35
    if rate > 1.02:
        filters.append(f"atempo={rate:.4f}")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src)]
    if filters:
        cmd += ["-filter:a", ",".join(filters)]
    cmd += ["-ar", str(SR), "-ac", "1", str(dst)]
    subprocess.check_call(cmd)


def prepare_voice() -> Tuple[List[Tuple[float, np.ndarray]], List[List[dict]]]:
    """Fit each Brian line into its script window. The last line is the upload."""
    sources = [CACHE / f"vo_line_{i:02d}.mp3" for i in range(10)]
    sources.append(UPLOADED_MP3 if UPLOADED_MP3.exists() else CACHE / "vo_line_10_uploaded.mp3")
    placed = []
    phrases = []
    for (t0, t1, text), src in zip(SCRIPT_TIMED_LINES, sources):
        slot = max(0.4, t1 - t0 - 0.05)
        raw = _duration(src)
        tempo = max(1.0, raw / slot)
        wav = CACHE / f"fitted_{sources.index(src):02d}.wav"
        _to_wav(src, wav, tempo)
        with wave.open(str(wav), "rb") as handle:
            pcm = np.frombuffer(handle.readframes(handle.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        placed.append((t0, pcm))
        tokens = [tok.strip(".,?") for tok in text.replace("?", " ?").split() if tok.strip(".,?")]
        # Keep punctuation attached for the last question mark word.
        tokens = text.replace("?", " ?").split()
        weights = [max(2, len(tok.strip(".,?"))) for tok in tokens]
        total_w = sum(weights)
        dur = len(pcm) / SR
        cursor = t0
        group = []
        for tok, weight in zip(tokens, weights):
            word_dur = dur * weight / total_w
            group.append({"text": tok.strip(".,").upper() + ("?" if tok.endswith("?") else ""), "start": cursor, "end": cursor + word_dur * 0.92})
            cursor += word_dur
        phrases.append(group)
    return placed, phrases


def mix_audio(spec: Episode, voice: List[Tuple[float, np.ndarray]]) -> np.ndarray:
    total = int(round(spec.total_duration * SR))
    master = np.zeros((total, 2), dtype=np.float64)
    t = np.arange(total, dtype=np.float64) / SR
    bed = 0.012 * np.sin(2 * math.pi * 98 * t) + 0.008 * np.sin(2 * math.pi * 147 * t)
    master[:, 0] += bed
    master[:, 1] += bed
    for start_t, pcm in voice:
        i0 = int(round(start_t * SR))
        i1 = min(total, i0 + len(pcm))
        if i1 > i0:
            master[i0:i1, 0] += pcm[: i1 - i0] * 0.92
            master[i0:i1, 1] += pcm[: i1 - i0] * 0.92
    n_w = int(0.32 * SR)
    tw = np.linspace(0, 0.32, n_w)
    env = 30 * (tw / 0.32) ** 2 * (1 - tw / 0.32) ** 2
    whoosh = env * np.sin(2 * math.pi * (140 * tw + 220 * tw ** 2)) * 0.11
    for mv in spec.moves:
        i0 = int(round(max(0.0, mv.start_t + 0.45 * mv.duration - 0.16) * SR))
        i1 = min(total, i0 + n_w)
        if i1 > i0:
            master[i0:i1, 0] += whoosh[: i1 - i0]
            master[i0:i1, 1] += whoosh[: i1 - i0]
    n_p = int(0.07 * SR)
    tp = np.linspace(0, 0.07, n_p)
    pop = np.exp(-tp * 46) * np.sin(2 * math.pi * 420 * tp) * 0.16
    for stamp in [p.enter_t for p in spec.pills]:
        i0 = int(round((stamp + 0.02) * SR))
        i1 = min(total, i0 + n_p)
        if i1 > i0:
            master[i0:i1] += pop[: i1 - i0, None]
    peak = float(np.max(np.abs(master)))
    if peak > 0.92:
        master *= 0.92 / peak
    return master


def render_frame(rings, spec, words, state, t):
    plate = render_plate(state["lon"], state["lat"], state["span"], state["w"])
    draw_map(plate, rings, spec, state["lon"], state["lat"], state["span"], state["w"], t)
    return draw_overlay(plate, spec, words, state["lon"], state["lat"], state["span"], state["w"], t)


def main() -> None:
    global PLATE, STARS
    import sys

    target = CACHE / "render_video.py"
    here = Path(__file__).resolve()
    if here != target.resolve():
        shutil.copyfile(here, target)
    PLATE = load_plate()
    STARS = make_stars()
    rings = load_rings()
    spec = build_episode()
    rig = spec.build_rig()
    print(f"rings {len(rings)} plate {PLATE.shape}", flush=True)
    voice, phrases = prepare_voice()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out = Path("/tmp/cit_fixed_stills")
        out.mkdir(parents=True, exist_ok=True)
        times = [float(x) for x in sys.argv[2:]] or [1.2, 9.5, 16.0, 21.0, 31.5, 38.0, 43.5, 53.5, 60.0]
        for t in times:
            state = rig.evaluate_all(min(t, spec.total_duration))
            image = render_frame(rings, spec, phrases, state, t)
            path = out / f"t_{t:05.1f}.jpg"
            Image.fromarray(image).save(path, quality=88)
            print(f"still {path.name} w={state['w']:.2f} span={state['span']:.1f} lon={state['lon']:.1f} lat={state['lat']:.1f}", flush=True)
        return
    audio = (mix_audio(spec, voice) * 32767.0).astype(np.int16)
    wav_path = Path("/tmp/cit_fixed_master.wav")
    with wave.open(str(wav_path), "w") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(audio.tobytes())
    frames = int(round(spec.total_duration * FPS))
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(wav_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ]
    print(f"render {frames} frames -> {OUT_MP4}", flush=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for index in range(frames):
            t = index / FPS
            state = rig.evaluate_all(t)
            proc.stdin.write(render_frame(rings, spec, phrases, state, t).tobytes())
            if index % (FPS * 5) == 0:
                print(f"frame {index}/{frames} t={t:.1f} w={state['w']:.2f} span={state['span']:.1f}", flush=True)
    finally:
        proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited {code}")
    print("wrote", OUT_MP4, flush=True)


if __name__ == "__main__":
    main()
