#!/usr/bin/env python3
"""
Juicy Tea map-shorts engine.

Renders a 1080x1920 60fps globe from Natural Earth 10m with 16x sub-pixel edges.
The newest narration in latest_vo.mp3 is played once. Word times come from
latest_vo_words.json when that file matches the audio, otherwise from the
waveform envelope. The episode is chosen from the spoken words.
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def locate_paths() -> Tuple[Path, Path, Path]:
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "map_engine_code" / "pr34_latest" / "pipeline").exists():
            pr34 = candidate / "map_engine_code" / "pr34_latest"
            return candidate, pr34, pr34 / "pipeline"
        if (candidate / "pr34_latest" / "pipeline").exists():
            pr34 = candidate / "pr34_latest"
            return candidate, pr34, pr34 / "pipeline"
        if (candidate / "pipeline" / "jt").exists():
            return candidate.parent, candidate, candidate / "pipeline"
    return cwd, cwd, cwd / "pipeline"


WORKSPACE, PR34, ROOT = locate_paths()
sys.path.insert(0, str(ROOT))

W, H, FPS = 1080, 1920, 60
SCREEN_DIAG_RADIUS = math.hypot(W * 0.5, H * 0.5)
LOOP_TAIL_SEC = 0.5
MIN_SPAN_DEG = 2.8
MAX_SPAN_DEG = 170.0
SUBPIXEL_SHIFT = 4
SUBPIXEL_MULT = float(1 << SUBPIXEL_SHIFT)
SAFE_RIGHT = 895.0

CACHE_DIR = PR34 / "pipeline" / "examples" / "cut_in_two"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GEOJSON_10M = CACHE_DIR / "ne_10m_admin_0_countries.geojson"
GEOJSON_10M_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_10m_admin_0_countries.geojson"
)
PLATE_PATH = CACHE_DIR / "earth_topo_5400.jpg"
PLATE_URL = (
    "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/"
    "world.topo.bathy.200412.3x5400x2700.jpg"
)
BRIAN_MP3 = CACHE_DIR / "brian_cut_in_two.mp3"
BRIAN_WORDS = CACHE_DIR / "brian_words.json"
LATEST_VO = CACHE_DIR / "latest_vo.mp3"
LATEST_WORDS = CACHE_DIR / "latest_vo_words.json"
UPLOAD_DIR = Path("/home/ubuntu/.cursor/projects/workspace/uploads")
OUT_DIR = WORKSPACE / "v"

HIGHLIGHT_ISOS = {
    "USA", "CAN", "MYS", "BRN", "OMN", "ARE", "COD", "AGO", "AZE", "ARM", "TUR", "IRN",
    "FRA", "BRA", "DNK", "GRL", "ESP", "GBR", "MAR", "BWA", "ZMB", "NAM", "ZWE", "NOR", "RUS", "PRK",
}


def smoothstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * (3.0 - 2.0 * u_c)


def smootherstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * u_c * (u_c * (u_c * 6.0 - 15.0) + 10.0)


def icon_pop_scale(elapsed_s: float, duration_s: float = 0.52, peak: float = 1.14) -> float:
    if elapsed_s <= 0.0:
        return 0.0
    if elapsed_s >= duration_s:
        return 1.0
    u = elapsed_s / duration_s
    c = (peak - 1.0) * 15.6
    one_minus_u = 1.0 - u
    base = 1.0 - (one_minus_u ** 3) * (1.0 + 3.0 * u)
    overshoot = c * (u ** 2) * (one_minus_u ** 3) * 4.0
    return float(base + overshoot)


def label_pop_state(elapsed_s: float, duration_s: float = 0.28) -> Tuple[float, float]:
    if elapsed_s <= 0.0:
        return 0.0, 0.0
    if elapsed_s >= duration_s:
        return 1.0, 1.0
    scale = icon_pop_scale(elapsed_s, duration_s=duration_s, peak=1.06)
    alpha = float(smootherstep(min(1.0, elapsed_s / (0.55 * duration_s))))
    return scale, alpha


def element_fade_and_exit_offset(
    t: float,
    enter_t: float,
    exit_t: float,
    fade_in_s: float = 0.26,
    fade_out_s: float = 0.28,
    exit_drift_px: Tuple[float, float] = (12.0, -8.0),
) -> Tuple[float, float, float]:
    fade_in_s = max(fade_in_s, 0.25)
    fade_out_s = max(fade_out_s, 0.25)
    exit_move_s = max(fade_out_s, 0.40)
    if t <= enter_t or t >= exit_t + fade_out_s:
        return 0.0, 0.0, 0.0
    if t < enter_t + fade_in_s:
        return float(smootherstep((t - enter_t) / fade_in_s)), 0.0, 0.0
    if t > exit_t:
        u_fade = min(1.0, (t - exit_t) / fade_out_s)
        u_move = min(1.0, (t - exit_t) / exit_move_s)
        alpha = float(1.0 - smootherstep(u_fade))
        s_move = float(smootherstep(u_move))
        return alpha, exit_drift_px[0] * s_move, exit_drift_px[1] * s_move
    return 1.0, 0.0, 0.0


@dataclass(frozen=True)
class CameraAnchor:
    t: float
    w: float
    lon: float
    lat: float
    span: float
    is_snap: bool = False


class TimeParameterizedC2Spline:
    def __init__(self, t: np.ndarray, y: np.ndarray, v_start: float | None = None, v_end: float | None = None) -> None:
        self.t = np.asarray(t, dtype=np.float64)
        self.y = np.asarray(y, dtype=np.float64)
        n = len(self.t)
        self.h = np.diff(self.t)
        secants = np.diff(self.y) / self.h
        d = np.zeros(n, dtype=np.float64)
        d[0] = v_start if v_start is not None else secants[0] * 0.5
        d[-1] = v_end if v_end is not None else secants[-1] * 0.5
        for i in range(1, n - 1):
            if secants[i - 1] * secants[i] <= 0.0:
                d[i] = 0.0
            else:
                w1 = 2.0 * self.h[i] + self.h[i - 1]
                w2 = self.h[i] + 2.0 * self.h[i - 1]
                d[i] = (w1 + w2) / (w1 / secants[i - 1] + w2 / secants[i])
        self.tangents = d

    def eval_with_derivs(self, t_query: float) -> Tuple[float, float, float]:
        tq = float(np.clip(t_query, self.t[0], self.t[-1]))
        idx = max(0, min(int(np.searchsorted(self.t, tq, side="right")) - 1, len(self.t) - 2))
        h = self.h[idx]
        y0, y1 = self.y[idx], self.y[idx + 1]
        v0, v1 = self.tangents[idx], self.tangents[idx + 1]
        u = float(np.clip((tq - self.t[idx]) / h, 0.0, 1.0))
        u2, u3, u4, u5 = u * u, u * u * u, u * u * u * u, u * u * u * u * u
        pos = (1.0 - 10.0 * u3 + 15.0 * u4 - 6.0 * u5) * y0 + (u - 6.0 * u3 + 8.0 * u4 - 3.0 * u5) * (h * v0) + (10.0 * u3 - 15.0 * u4 + 6.0 * u5) * y1 + (-4.0 * u3 + 7.0 * u4 - 3.0 * u5) * (h * v1)
        vel = ((-30.0 * u2 + 60.0 * u3 - 30.0 * u4) * y0 + (1.0 - 18.0 * u2 + 32.0 * u3 - 15.0 * u4) * (h * v0) + (30.0 * u2 - 60.0 * u3 + 30.0 * u4) * y1 + (-12.0 * u2 + 28.0 * u3 - 15.0 * u4) * (h * v1)) / h
        acc = ((-60.0 * u + 180.0 * u2 - 120.0 * u3) * y0 + (-36.0 * u + 96.0 * u2 - 60.0 * u3) * (h * v0) + (60.0 * u - 180.0 * u2 + 120.0 * u3) * y1 + (-24.0 * u + 84.0 * u2 - 60.0 * u3) * (h * v1)) / (h * h)
        return float(pos), float(vel), float(acc)


def hermite_segment(t: float, t0: float, t1: float, p0: float, v0: float, p1: float, v1: float) -> Tuple[float, float, float]:
    duration = max(t1 - t0, 1e-9)
    u = float(np.clip((t - t0) / duration, 0.0, 1.0))
    u2, u3 = u * u, u * u * u
    pos = (2.0 * u3 - 3.0 * u2 + 1.0) * p0 + (u3 - 2.0 * u2 + u) * (duration * v0) + (-2.0 * u3 + 3.0 * u2) * p1 + (u3 - u2) * (duration * v1)
    vel = ((6.0 * u2 - 6.0 * u) * p0 + (3.0 * u2 - 4.0 * u + 1.0) * (duration * v0) + (-6.0 * u2 + 6.0 * u) * p1 + (3.0 * u2 - 2.0 * u) * (duration * v1)) / duration
    acc = ((12.0 * u - 6.0) * p0 + (6.0 * u - 4.0) * (duration * v0) + (-12.0 * u + 6.0) * p1 + (6.0 * u - 2.0) * (duration * v1)) / (duration * duration)
    return float(pos), float(vel), float(acc)


class ContinuousCameraRig:
    def __init__(self, anchors: List[CameraAnchor], total_duration: float) -> None:
        self.total_duration = float(total_duration)
        self.loop_start_t = self.total_duration - LOOP_TAIL_SEC
        self.v0_w, self.v0_lon, self.v0_lat, self.v0_log_span = 0.0, 0.16, 0.03, -0.015
        first = anchors[0]
        core = [a for a in anchors if a.t < self.loop_start_t - 0.6]
        core.append(CameraAnchor(self.loop_start_t, first.w, first.lon - self.v0_lon * LOOP_TAIL_SEC, first.lat - self.v0_lat * LOOP_TAIL_SEC, first.span / math.exp(self.v0_log_span * LOOP_TAIL_SEC)))
        t_arr = np.array([a.t for a in core], dtype=np.float64)
        self.spline_w = TimeParameterizedC2Spline(t_arr, np.array([a.w for a in core]), self.v0_w, self.v0_w)
        self.spline_lon = TimeParameterizedC2Spline(t_arr, np.rad2deg(np.unwrap(np.deg2rad([a.lon for a in core]))), self.v0_lon, self.v0_lon)
        self.spline_lat = TimeParameterizedC2Spline(t_arr, np.array([a.lat for a in core]), self.v0_lat, self.v0_lat)
        self.spline_log_span = TimeParameterizedC2Spline(t_arr, np.log(np.array([a.span for a in core])), self.v0_log_span, self.v0_log_span)

    def evaluate_all(self, t: float) -> Dict[str, float]:
        t_clamped = float(np.clip(t, 0.0, self.total_duration))
        if t_clamped <= self.loop_start_t:
            w, dw, ddw = self.spline_w.eval_with_derivs(t_clamped)
            lon, dlon, ddlon = self.spline_lon.eval_with_derivs(t_clamped)
            lat, dlat, ddlat = self.spline_lat.eval_with_derivs(t_clamped)
            lspan, dlspan, ddlspan = self.spline_log_span.eval_with_derivs(t_clamped)
        else:
            w0, dw0, _ = self.spline_w.eval_with_derivs(self.loop_start_t)
            w1, dw1, _ = self.spline_w.eval_with_derivs(0.0)
            w, dw, ddw = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, w0, dw0, w1, dw1)
            lon0, dlon0, _ = self.spline_lon.eval_with_derivs(self.loop_start_t)
            lon1, dlon1, _ = self.spline_lon.eval_with_derivs(0.0)
            lon, dlon, ddlon = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lon0, dlon0, lon0 + ((lon1 - lon0 + 180.0) % 360.0 - 180.0), dlon1)
            lat0, dlat0, _ = self.spline_lat.eval_with_derivs(self.loop_start_t)
            lat1, dlat1, _ = self.spline_lat.eval_with_derivs(0.0)
            lat, dlat, ddlat = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lat0, dlat0, lat1, dlat1)
            ls0, dls0, _ = self.spline_log_span.eval_with_derivs(self.loop_start_t)
            ls1, dls1, _ = self.spline_log_span.eval_with_derivs(0.0)
            lspan, dlspan, ddlspan = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, ls0, dls0, ls1, dls1)
        return {"w": float(np.clip(w, 0.0, 1.0)), "dw": dw, "ddw": ddw, "lon": lon, "dlon": dlon, "ddlon": ddlon, "lat": lat, "dlat": dlat, "ddlat": ddlat, "log_span": lspan, "dlog_span": dlspan, "ddlog_span": ddlspan, "span": math.exp(lspan)}


@dataclass(frozen=True)
class LockedCameraMove:
    move_id: str
    cue_word_index: int
    start_t: float
    duration: float
    w_start: float
    w_end: float
    lon_start: float
    lon_end: float
    lat_start: float
    lat_end: float
    span_start: float
    span_end: float
    drift_scale_rate: float = -0.012
    drift_lon_rate: float = 0.04
    drift_lat_rate: float = 0.01
    is_snap: bool = False


@dataclass(frozen=True)
class CountryHighlightCue:
    z_order: int
    iso_a3: str
    enter_t: float
    exit_t: float
    fill_rgba: Tuple[int, int, int, int]
    stroke_rgba: Tuple[int, int, int, int]
    where: str = "all"


@dataclass(frozen=True)
class SplitArcCue:
    lon0: float
    lat0: float
    lon1: float
    lat1: float
    enter_t: float
    exit_t: float
    color_rgb: Tuple[int, int, int] = (0, 229, 255)


@dataclass(frozen=True)
class MapLabelItem:
    text: str
    lon: float
    lat: float
    enter_t: float
    exit_t: float
    color_rgba: Tuple[int, int, int, int] = (255, 255, 255, 255)
    font_size: float = 40.0


@dataclass(frozen=True)
class PillBannerItem:
    text: str
    screen_x: float
    screen_y: float
    enter_t: float
    exit_t: float
    theme: str = "dark"
    counter_start: float | None = None
    counter_end: float | None = None
    counter_fmt: str = ""


@dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    total_duration: float
    first_highlight_t: float
    moves: List[LockedCameraMove]
    event_timestamps: List[float]
    highlights: List[CountryHighlightCue] = field(default_factory=list)
    arcs: List[SplitArcCue] = field(default_factory=list)
    labels: List[MapLabelItem] = field(default_factory=list)
    pills: List[PillBannerItem] = field(default_factory=list)
    script_lines: List[Tuple[float, float, str]] = field(default_factory=list)
    map_has_yellow: bool = True

    def build_rig(self) -> ContinuousCameraRig:
        anchors: List[CameraAnchor] = []
        for i, mv in enumerate(self.moves):
            if i > 0:
                prev = anchors[-1]
                hold_dt = max(0.0, mv.start_t - prev.t)
                if hold_dt > 0.05:
                    drifted_span = float(np.clip(prev.span * math.exp(mv.drift_scale_rate * hold_dt), MIN_SPAN_DEG + 0.1, MAX_SPAN_DEG - 1.0))
                    anchors.append(CameraAnchor(mv.start_t, mv.w_start, prev.lon + mv.drift_lon_rate * hold_dt * (prev.span / 50.0), prev.lat + mv.drift_lat_rate * hold_dt * (prev.span / 50.0), drifted_span, mv.is_snap))
            else:
                anchors.append(CameraAnchor(mv.start_t, mv.w_start, mv.lon_start, mv.lat_start, mv.span_start, mv.is_snap))
            anchors.append(CameraAnchor(mv.start_t + mv.duration, mv.w_end, mv.lon_end, mv.lat_end, mv.span_end, mv.is_snap))
        return ContinuousCameraRig(anchors, self.total_duration)


def scale_episode_timing(spec: EpisodeSpec, target_duration: float) -> EpisodeSpec:
    s = float(target_duration) / spec.total_duration
    if abs(s - 1.0) < 0.015:
        return spec
    moves = [LockedCameraMove(m.move_id, m.cue_word_index, round(m.start_t * s, 3), round(max(0.75, min(2.1, m.duration * s)), 3), m.w_start, m.w_end, m.lon_start, m.lon_end, m.lat_start, m.lat_end, m.span_start, m.span_end, m.drift_scale_rate, m.drift_lon_rate, m.drift_lat_rate, m.is_snap) for m in spec.moves]
    highlights = [CountryHighlightCue(h.z_order, h.iso_a3, h.enter_t * s, h.exit_t * s, h.fill_rgba, h.stroke_rgba, h.where) for h in spec.highlights]
    arcs = [SplitArcCue(a.lon0, a.lat0, a.lon1, a.lat1, a.enter_t * s, a.exit_t * s, a.color_rgb) for a in spec.arcs]
    labels = [MapLabelItem(l.text, l.lon, l.lat, l.enter_t * s, l.exit_t * s, l.color_rgba, l.font_size) for l in spec.labels]
    pills = [PillBannerItem(p.text, p.screen_x, p.screen_y, p.enter_t * s, p.exit_t * s, p.theme, p.counter_start, p.counter_end, p.counter_fmt) for p in spec.pills]
    lines = [(t0 * s, t1 * s, txt) for t0, t1, txt in spec.script_lines]
    events = sorted({round(t * 1.10, 2) for t in range(1, int(target_duration / 1.10) + 1) if t * 1.10 < target_duration})
    return EpisodeSpec(spec.episode_id, round(target_duration, 2), spec.first_highlight_t, moves, events, highlights, arcs, labels, pills, lines, spec.map_has_yellow)


def build_cut_in_two_episode() -> EpisodeSpec:
    total_dur = 79.00
    moves = [
        LockedCameraMove("cit_01_alaska_open", 0, 0.00, 1.70, 1.0, 0.0, -148.0, -149.0, 61.0, 63.0, 64.0, 28.0, is_snap=True),
        LockedCameraMove("cit_02_alaska_pan", 13, 3.05, 1.45, 0.0, 0.0, -148.5, -140.0, 63.0, 60.0, 27.5, 24.0),
        LockedCameraMove("cit_03_canada_wide", 21, 6.05, 1.55, 0.0, 0.0, -139.5, -112.0, 60.0, 54.0, 23.5, 38.0),
        LockedCameraMove("cit_04_globe_to_malaysia", 34, 12.35, 2.10, 0.0, 1.0, -111.5, 108.5, 54.0, 4.5, 37.5, 56.0),
        LockedCameraMove("cit_05_malaysia_focus", 45, 16.55, 1.45, 1.0, 0.0, 108.5, 108.5, 4.5, 4.0, 55.0, 19.5),
        LockedCameraMove("cit_06_brunei_closeup", 61, 22.35, 1.55, 0.0, 0.0, 108.7, 114.80, 4.0, 4.78, 19.0, 4.2, is_snap=True),
        LockedCameraMove("cit_07_limbang_corridor", 67, 27.15, 1.25, 0.0, 0.0, 114.85, 114.95, 4.78, 4.72, 4.1, 3.8),
        LockedCameraMove("cit_08_globe_to_hormuz", 83, 33.55, 1.70, 0.0, 0.85, 115.0, 56.25, 4.72, 25.4, 3.8, 32.0),
        LockedCameraMove("cit_09_musandam_closeup", 87, 36.35, 1.40, 0.85, 0.0, 56.25, 56.25, 25.4, 25.75, 31.0, 5.0, is_snap=True),
        LockedCameraMove("cit_10_indian_ocean_globe", 110, 43.70, 1.60, 0.0, 1.0, 56.3, 42.0, 25.75, 12.0, 4.9, 64.0),
        LockedCameraMove("cit_11_cabinda_zoom", 128, 49.75, 1.65, 1.0, 0.0, 42.0, 12.6, 12.0, -5.6, 62.0, 5.8, is_snap=True),
        LockedCameraMove("cit_12_angola_frame", 142, 55.85, 1.30, 0.0, 0.0, 12.7, 15.8, -5.6, -9.8, 5.7, 14.0),
        LockedCameraMove("cit_13_globe_to_caucasus", 152, 59.95, 1.80, 0.0, 0.70, 15.9, 45.5, -9.7, 39.4, 13.8, 24.0),
        LockedCameraMove("cit_14_nakhchivan_closeup", 164, 64.15, 1.40, 0.70, 0.0, 45.5, 45.4, 39.4, 39.35, 23.0, 5.4, is_snap=True),
        LockedCameraMove("cit_15_pullback_globe", 183, 75.15, 1.35, 0.0, 1.0, 45.5, -45.0, 39.35, 54.0, 5.3, 64.0),
        LockedCameraMove("cit_16_globe_loop_alaska", 186, 76.55, 1.15, 1.0, 1.0, -45.0, -148.0, 54.0, 61.0, 64.0, 64.0),
    ]
    highlights = [
        CountryHighlightCue(10, "USA", 0.00, 12.30, (245, 198, 45, 215), (255, 235, 120, 255), "alaska"),
        CountryHighlightCue(10, "USA", 7.40, 12.30, (245, 198, 45, 215), (255, 235, 120, 255), "usa_lower48"),
        CountryHighlightCue(15, "CAN", 6.00, 12.30, (225, 75, 70, 210), (255, 155, 150, 255)),
        CountryHighlightCue(10, "MYS", 16.60, 33.50, (220, 75, 70, 210), (255, 150, 145, 255)),
        CountryHighlightCue(20, "BRN", 22.40, 33.50, (250, 205, 25, 240), (255, 245, 150, 255)),
        CountryHighlightCue(15, "OMN", 34.10, 43.60, (225, 75, 70, 225), (255, 160, 155, 255)),
        CountryHighlightCue(10, "ARE", 36.40, 43.60, (245, 198, 45, 220), (255, 235, 120, 255)),
        CountryHighlightCue(10, "COD", 49.90, 59.80, (65, 155, 205, 215), (150, 220, 255, 255)),
        CountryHighlightCue(15, "AGO", 55.90, 59.80, (70, 175, 100, 215), (155, 245, 180, 255), "angola_main"),
        CountryHighlightCue(20, "AGO", 51.10, 59.80, (250, 205, 25, 240), (255, 245, 150, 255), "cabinda"),
        CountryHighlightCue(10, "AZE", 61.70, 75.10, (65, 155, 205, 220), (150, 220, 255, 255), "azerbaijan_main"),
        CountryHighlightCue(15, "ARM", 64.20, 75.10, (238, 135, 55, 225), (255, 200, 140, 255)),
        CountryHighlightCue(20, "AZE", 65.00, 75.10, (250, 205, 25, 240), (255, 245, 150, 255), "nakhchivan"),
        CountryHighlightCue(10, "USA", 76.70, 79.00, (245, 198, 45, 215), (255, 235, 120, 255), "alaska"),
    ]
    arcs = [
        SplitArcCue(-148.0, 62.5, -120.5, 47.5, 7.70, 12.15),
        SplitArcCue(102.2, 4.0, 113.5, 3.2, 18.20, 22.70),
        SplitArcCue(114.65, 4.85, 115.12, 4.70, 25.70, 33.40),
        SplitArcCue(57.2, 23.6, 56.25, 26.05, 36.80, 43.40),
        SplitArcCue(17.2, -11.6, 12.30, -5.22, 52.10, 59.60),
        SplitArcCue(47.2, 40.1, 45.4, 39.2, 65.40, 74.95),
    ]
    labels = [
        MapLabelItem("ALASKA", -151.0, 64.5, 1.30, 6.00),
        MapLabelItem("CANADA", -108.0, 56.5, 9.85, 12.25),
        MapLabelItem("MALAYSIA", 102.2, 4.5, 17.05, 22.30),
        MapLabelItem("BORNEO", 114.5, 1.5, 18.70, 22.50),
        MapLabelItem("BRUNEI", 114.60, 5.02, 23.20, 33.40),
        MapLabelItem("MUSANDAM", 56.10, 26.45, 36.50, 43.45),
        MapLabelItem("CABINDA", 12.05, -4.85, 51.50, 59.70),
        MapLabelItem("ANGOLA", 17.4, -12.4, 56.20, 59.70),
        MapLabelItem("NAKHCHIVAN", 45.05, 38.65, 65.20, 75.05),
        MapLabelItem("ARMENIA", 44.55, 40.35, 67.70, 75.05, (255, 190, 115, 255)),
    ]
    pills = [
        PillBannerItem("$7.2M · ≈2¢/ACRE · 1867", 540.0, 300.0, 1.05, 5.50, "red", 0.0, 7.2, "${val:.1f}M · ≈2¢/ACRE · 1867"),
        PillBannerItem("19 MI", 540.0, 300.0, 31.15, 33.50, "blue", 0.0, 19.0, "{val:.0f} MI"),
        PillBannerItem("TURKEY · 11 KM", 540.0, 300.0, 71.45, 74.20, "red", 0.0, 11.0, "TURKEY · {val:.0f} KM"),
    ]
    lines = [(0.08, 78.12, "Alaska Malaysia Brunei Oman Cabinda Nakhchivan")]
    events = sorted({round(t * 1.10, 2) for t in range(1, int(total_dur / 1.10) + 1) if t * 1.10 < total_dur})
    return EpisodeSpec("cut_in_two", total_dur, 0.10, moves, events, highlights, arcs, labels, pills, lines, True)


def build_impossible_neighbors_episode() -> EpisodeSpec:
    """France–Brazil, Hans Island, Gibraltar, the 85 m rock, Kazungula, Norway–Korea."""
    total_dur = 76.50
    moves = [
        LockedCameraMove("in_01_france_hook", 0, 0.00, 1.40, 1.0, 0.0, 2.5, 2.5, 46.5, 46.5, 52.0, 22.0, is_snap=True),
        LockedCameraMove("in_02_globe_to_brazil", 9, 4.35, 1.70, 0.0, 0.85, 2.5, -53.0, 46.5, 4.0, 22.0, 48.0),
        LockedCameraMove("in_03_guiana_zoom", 18, 8.50, 1.45, 0.85, 0.0, -53.0, -53.2, 4.0, 3.8, 46.0, 11.5, is_snap=True),
        LockedCameraMove("in_04_globe_to_arctic", 42, 19.70, 1.80, 0.0, 0.90, -53.2, -68.0, 3.8, 76.5, 11.5, 44.0),
        LockedCameraMove("in_05_hans_island_zoom", 69, 29.40, 1.50, 0.90, 0.0, -68.0, -66.45, 76.5, 80.82, 42.0, 8.5, is_snap=True),
        LockedCameraMove("in_06_globe_to_spain", 75, 34.45, 1.70, 0.0, 0.75, -66.45, -5.0, 80.82, 36.2, 8.5, 28.0),
        LockedCameraMove("in_07_gibraltar_zoom", 88, 38.70, 1.40, 0.75, 0.0, -5.0, -4.65, 36.2, 35.65, 27.0, 4.5, is_snap=True),
        LockedCameraMove("in_08_globe_to_zambezi", 116, 50.90, 1.70, 0.0, 0.85, -4.65, 25.26, 35.65, -17.79, 4.5, 36.0),
        LockedCameraMove("in_09_kazungula_zoom", 128, 55.40, 1.45, 0.85, 0.0, 25.26, 25.26, -17.79, -17.79, 34.0, 6.2, is_snap=True),
        LockedCameraMove("in_10_globe_norway_korea", 156, 65.70, 1.80, 0.0, 1.0, 25.26, 85.0, -17.79, 62.0, 6.2, 68.0),
        LockedCameraMove("in_11_loop_back_france", 172, 73.70, 1.45, 1.0, 1.0, 85.0, 2.5, 62.0, 46.5, 68.0, 52.0),
    ]
    highlights = [
        CountryHighlightCue(20, "FRA", -0.40, 19.60, (65, 155, 235, 225), (160, 225, 255, 255)),
        CountryHighlightCue(15, "BRA", 4.30, 19.60, (70, 185, 95, 220), (160, 250, 180, 255)),
        CountryHighlightCue(15, "CAN", 19.60, 34.40, (225, 75, 70, 215), (255, 155, 150, 255)),
        CountryHighlightCue(20, "GRL", 21.20, 34.40, (245, 198, 45, 225), (255, 240, 135, 255)),
        CountryHighlightCue(20, "ESP", 34.40, 50.80, (245, 198, 45, 225), (255, 240, 135, 255)),
        CountryHighlightCue(15, "GBR", 36.40, 50.80, (225, 75, 70, 220), (255, 155, 150, 255)),
        CountryHighlightCue(15, "MAR", 40.30, 50.80, (70, 185, 95, 220), (160, 250, 180, 255)),
        CountryHighlightCue(20, "BWA", 50.90, 65.60, (65, 155, 235, 225), (160, 225, 255, 255)),
        CountryHighlightCue(20, "ZMB", 50.90, 65.60, (70, 185, 95, 225), (160, 250, 180, 255)),
        CountryHighlightCue(12, "NAM", 55.20, 65.60, (245, 198, 45, 210), (255, 235, 120, 255)),
        CountryHighlightCue(12, "ZWE", 55.20, 65.60, (225, 75, 70, 210), (255, 155, 150, 255)),
        CountryHighlightCue(20, "NOR", 65.60, 73.60, (65, 155, 235, 230), (160, 225, 255, 255)),
        CountryHighlightCue(12, "RUS", 65.60, 73.60, (225, 75, 70, 215), (255, 155, 150, 255)),
        CountryHighlightCue(20, "PRK", 67.40, 73.60, (245, 198, 45, 235), (255, 240, 135, 255)),
        CountryHighlightCue(20, "FRA", 73.60, 77.20, (65, 155, 235, 225), (160, 225, 255, 255)),
    ]
    arcs = [
        SplitArcCue(2.4, 46.6, -53.1, 3.9, 4.50, 19.40),
        SplitArcCue(-75.0, 78.5, -52.0, 72.0, 21.40, 34.20),
        SplitArcCue(-5.35, 36.14, -4.30, 35.17, 39.00, 50.60),
        SplitArcCue(24.5, -19.5, 28.0, -15.0, 56.00, 65.40),
        SplitArcCue(29.0, 69.5, 130.6, 42.4, 67.20, 73.40),
    ]
    labels = [
        MapLabelItem("FRANCE", 2.4, 46.8, 0.40, 4.20),
        MapLabelItem("FRENCH GUIANA", -53.2, 4.2, 8.60, 19.40, (140, 215, 255, 255)),
        MapLabelItem("BRAZIL", -51.2, 1.2, 9.20, 19.40, (145, 245, 175, 255)),
        MapLabelItem("CANADA", -78.0, 77.5, 21.40, 34.20, (255, 150, 150, 255)),
        MapLabelItem("GREENLAND", -48.0, 74.5, 22.00, 34.20, (255, 235, 130, 255)),
        MapLabelItem("HANS ISLAND", -66.45, 80.95, 30.80, 34.20),
        MapLabelItem("SPAIN", -4.2, 36.6, 36.20, 50.60, (255, 235, 130, 255)),
        MapLabelItem("GIBRALTAR", -5.35, 36.22, 39.20, 50.60, (255, 150, 150, 255)),
        MapLabelItem("MOROCCO", -4.4, 35.15, 42.20, 50.60, (145, 245, 175, 255)),
        MapLabelItem("BOTSWANA", 23.6, -21.2, 56.00, 65.40, (140, 215, 255, 255)),
        MapLabelItem("ZAMBIA", 27.4, -15.6, 56.40, 65.40, (145, 245, 175, 255)),
        MapLabelItem("NAMIBIA", 22.4, -18.6, 60.80, 65.40, (255, 235, 130, 255)),
        MapLabelItem("ZIMBABWE", 28.2, -19.4, 61.20, 65.40, (255, 150, 150, 255)),
        MapLabelItem("NORWAY", 18.0, 68.5, 66.40, 73.40, (140, 215, 255, 255)),
        MapLabelItem("RUSSIA", 90.0, 62.0, 68.40, 73.40, (255, 150, 150, 255)),
        MapLabelItem("NORTH KOREA", 127.5, 40.0, 69.20, 73.40, (255, 235, 130, 255)),
    ]
    pills = [
        PillBannerItem("LONGEST BORDER", 540.0, 280.0, 0.70, 4.30, "blue"),
        PillBannerItem("730 KM JUNGLE BORDER", 540.0, 280.0, 12.80, 19.30, "yellow", 0.0, 730.0, "{val:.0f} KM JUNGLE BORDER"),
        PillBannerItem("EU BORDERS SOUTH AMERICA", 540.0, 390.0, 16.80, 19.30, "dark"),
        PillBannerItem("CANADA · DENMARK", 540.0, 280.0, 25.00, 28.10, "red"),
        PillBannerItem("2022 · HANS ISLAND", 540.0, 280.0, 28.70, 34.20, "dark"),
        PillBannerItem("GIBRALTAR · 1.2 KM", 540.0, 280.0, 36.50, 40.20, "red"),
        PillBannerItem("SHORTEST BORDER · 85 M", 540.0, 280.0, 46.60, 50.70, "yellow", 0.0, 85.0, "SHORTEST BORDER · {val:.0f} M"),
        PillBannerItem("BOTSWANA · ZAMBIA · 150 M", 540.0, 280.0, 56.00, 60.20, "blue", 0.0, 150.0, "BOTSWANA · ZAMBIA · {val:.0f} M"),
        PillBannerItem("CURVED BRIDGE", 540.0, 390.0, 61.40, 65.40, "dark"),
        PillBannerItem("1 COUNTRY APART", 540.0, 280.0, 68.20, 73.40, "red"),
    ]
    lines = [(0.12, 75.60, "France Brazil Hans Island Gibraltar Botswana Zambia Norway North Korea")]
    events = sorted({round(t * 1.10, 2) for t in range(1, int(total_dur / 1.10) + 1) if t * 1.10 < total_dur})
    return EpisodeSpec("impossible_neighbors", total_dur, 0.10, moves, events, highlights, arcs, labels, pills, lines, True)


FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
for alt in ["/usr/share/fonts/truetype/macos/Inter-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
    if Path(alt).exists():
        FONT_PATH = alt
        break
FONTS: dict[int, ImageFont.FreeTypeFont] = {}
PLATE: np.ndarray | None = None
STARS: np.ndarray | None = None
RINGS_BY_ISO: dict[str, list[dict]] = {}
GRID_STEP = 6
GX, GY = np.meshgrid(np.linspace(0.0, float(W), W // GRID_STEP + 1), np.linspace(0.0, float(H), H // GRID_STEP + 1))
FULL_R_PX = np.hypot(np.arange(W, dtype=np.float32)[None, :] - W * 0.5, np.arange(H, dtype=np.float32)[:, None] - H * 0.5)


def get_font(size: float) -> ImageFont.FreeTypeFont:
    key = max(10, int(round(size)))
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(FONT_PATH, key)
    return FONTS[key]


def find_newest_uploaded_mp3() -> Path | None:
    candidates: List[Path] = []
    for search_dir in [UPLOAD_DIR, CACHE_DIR, WORKSPACE]:
        if not search_dir.exists():
            continue
        for path in search_dir.glob("*.mp3"):
            if path.is_file() and path.stat().st_size > 40_000 and "vo_uniform" not in path.name and "vo_line" not in path.name:
                candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def ensure_assets() -> Path:
    if not PLATE_PATH.exists() or PLATE_PATH.stat().st_size < 100_000:
        urllib.request.urlretrieve(PLATE_URL, PLATE_PATH)
    if not GEOJSON_10M.exists() or GEOJSON_10M.stat().st_size < 500_000:
        urllib.request.urlretrieve(GEOJSON_10M_URL, GEOJSON_10M)
    newest = find_newest_uploaded_mp3()
    if newest is not None and newest.resolve() != LATEST_VO.resolve():
        if (not LATEST_VO.exists()) or newest.stat().st_mtime >= LATEST_VO.stat().st_mtime:
            shutil.copyfile(newest, LATEST_VO)
    if not LATEST_VO.exists():
        raise FileNotFoundError("latest_vo.mp3 is missing")
    return GEOJSON_10M


def load_enhanced_plate() -> np.ndarray:
    raw = np.asarray(Image.open(PLATE_PATH).convert("RGB"), dtype=np.uint8)
    blur = cv2.GaussianBlur(raw, (0, 0), 1.6)
    return cv2.addWeighted(raw, 1.38, blur, -0.38, 0)


def make_starfield() -> np.ndarray:
    rng = np.random.default_rng(11)
    img = np.zeros((H, W, 3), np.uint8)
    y = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    img[:] = (np.array([3, 6, 14]) * (1.0 - y) + np.array([10, 16, 28]) * y).astype(np.uint8)[:, None, :]
    ys, xs = rng.integers(0, H, 280), rng.integers(0, W, 280)
    img[ys, xs] = rng.integers(140, 255, 280)[:, None]
    return img


def lonlat_to_unit_xyz(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lam, phi = np.radians(lon_deg), np.radians(lat_deg)
    cos_phi = np.cos(phi)
    return np.column_stack([cos_phi * np.cos(lam), cos_phi * np.sin(lam), np.sin(phi)]).astype(np.float64)


def camera_rotation_matrix(cam_lon: float, cam_lat: float) -> Tuple[np.ndarray, np.ndarray]:
    lam0, phi0 = math.radians(cam_lon), math.radians(cam_lat)
    cl, sl, cp, sp = math.cos(lam0), math.sin(lam0), math.cos(phi0), math.sin(phi0)
    rotation = np.array([[-sl, cl, 0.0], [-sp * cl, -sp * sl, cp], [cp * cl, cp * sl, sp]], dtype=np.float64)
    return rotation, rotation[2]


def camera_scale_and_disc_radius(span: float, w: float) -> Tuple[float, float, float]:
    mix = float(smootherstep(w))
    flat_scale = W / max(math.radians(span), 1e-4)
    globe_r = float(np.clip((W * 0.43) * (64.0 / max(span, 36.0)), 440.0, 1450.0))
    scale = (1.0 - mix) * flat_scale + mix * globe_r
    return mix, scale, scale * ((1.0 - mix) * (math.pi * 0.495) + mix * 1.0)


def project_xyz(pts_xyz: np.ndarray, rotation: np.ndarray, mix: float, scale: float, clamp_to_horizon: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    cam = pts_xyz @ rotation.T
    xc, yc, zc = cam[:, 0], cam[:, 1], np.clip(cam[:, 2], -1.0, 1.0)
    c = np.arccos(zc)
    sin_c = np.maximum(np.hypot(xc, yc), 1e-9)
    max_c = (1.0 - mix) * 1.52 + mix * 1.54
    c_eff = np.minimum(c, max_c) if clamp_to_horizon else c
    factor = (scale * ((1.0 - mix) * c_eff + mix * np.sin(c_eff))) / sin_c
    return W * 0.5 + xc * factor, H * 0.5 - yc * factor, c <= max_c


def project(lon, lat, cam_lon, cam_lat, span, w, clamp_to_horizon=False):
    mix, scale, _ = camera_scale_and_disc_radius(span, w)
    rotation, _ = camera_rotation_matrix(cam_lon, cam_lat)
    return project_xyz(lonlat_to_unit_xyz(lon, lat), rotation, mix, scale, clamp_to_horizon)


def spherical_camera_warp(cam_lon, cam_lat, span, w, focus_dim=0.0):
    assert PLATE is not None and STARS is not None
    mix, scale, disc_r = camera_scale_and_disc_radius(span, w)
    p_h, p_w = PLATE.shape[:2]
    dx, dy = GX - W * 0.5, -(GY - H * 0.5)
    r_px = np.hypot(dx, dy)
    rho_clamped = np.minimum(r_px / scale, ((1.0 - mix) * (math.pi * 0.495) + mix) * 0.9995)
    c = np.where(mix > 0.5, np.arcsin(np.minimum(rho_clamped, 1.0)), rho_clamped)
    for _ in range(2):
        f_val = (1.0 - mix) * c + mix * np.sin(c) - rho_clamped
        c = np.clip(c - f_val / np.maximum((1.0 - mix) + mix * np.cos(c), 1e-5), 0.0, math.pi * 0.498)
    sin_c, cos_c = np.sin(c), np.cos(c)
    r_safe = np.maximum(r_px, 1e-7)
    xc, yc, zc = (dx / r_safe) * sin_c, (dy / r_safe) * sin_c, cos_c
    phi0, lam0 = math.radians(cam_lat), math.radians(cam_lon)
    cp, sp, cl, sl = math.cos(phi0), math.sin(phi0), math.cos(lam0), math.sin(lam0)
    y1 = -sp * yc + cp * zc
    vz = np.clip(cp * yc + sp * zc, -1.0, 1.0)
    vx, vy = cl * y1 - sl * xc, sl * y1 + cl * xc
    vx_full = cv2.resize(vx.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vy_full = cv2.resize(vy.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vz_full = np.clip(cv2.resize(vz.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR), -1.0, 1.0)
    lon_rad, lat_rad = np.arctan2(vy_full, vx_full), np.arcsin(vz_full)
    sampled = cv2.remap(PLATE, ((lon_rad + math.pi) / (2 * math.pi) * (p_w - 1)).astype(np.float32), ((math.pi * 0.5 - lat_rad) / math.pi * (p_h - 1)).astype(np.float32), interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
    if focus_dim > 0.01:
        sampled = cv2.convertScaleAbs(sampled, alpha=1.0 - 0.24 * focus_dim)
    if disc_r >= SCREEN_DIAG_RADIUS + 18.0:
        return sampled
    norm_r = FULL_R_PX / max(disc_r, 1.0)
    inside = norm_r <= 1.0
    limb = np.clip(1.0 - 0.34 * np.clip((norm_r - 0.72) / 0.28, 0.0, 1.0) ** 1.5, 0.62, 1.0)
    fresnel = np.clip((norm_r - 0.84) / 0.16, 0.0, 1.0) ** 2.2 * 0.38
    atmo = np.array([95.0, 175.0, 255.0], dtype=np.float32)
    earth = np.clip(sampled.astype(np.float32) * limb[:, :, None] * (1.0 - fresnel[:, :, None]) + atmo * fresnel[:, :, None], 0, 255).astype(np.uint8)
    frame = STARS.copy()
    frame[inside] = earth[inside]
    halo = (norm_r > 0.992) & (norm_r < 1.045)
    if np.any(halo):
        hu = np.clip((1.045 - norm_r[halo]) / (1.045 - 0.992), 0.0, 1.0)
        ha = (hu ** 2.4) * 0.72
        frame[halo] = np.clip(frame[halo].astype(np.float32) * (1 - ha[:, None]) + atmo * ha[:, None], 0, 255).astype(np.uint8)
    return frame


PILL_RGB = {"red": ((212, 38, 42), (255, 255, 255)), "dark": ((16, 22, 34), (255, 255, 255)), "blue": ((14, 116, 218), (255, 255, 255)), "yellow": ((245, 197, 24), (14, 18, 26))}


def chaikin_smooth_lonlat(lon, lat, passes=1):
    pts_lon, pts_lat = lon.copy(), lat.copy()
    for _ in range(passes):
        dlon = ((np.roll(pts_lon, -1) - pts_lon + 180.0) % 360.0) - 180.0
        dlat = np.roll(pts_lat, -1) - pts_lat
        new_lon, new_lat = np.empty(len(pts_lon) * 2), np.empty(len(pts_lat) * 2)
        new_lon[0::2], new_lon[1::2] = pts_lon + 0.25 * dlon, pts_lon + 0.75 * dlon
        new_lat[0::2], new_lat[1::2] = pts_lat + 0.25 * dlat, pts_lat + 0.75 * dlat
        pts_lon, pts_lat = new_lon, new_lat
    return pts_lon, pts_lat


def subdivide_ring_geodesic(lon, lat, max_deg=0.18):
    dlon_wrapped = ((np.diff(lon, append=lon[0]) + 180.0) % 360.0) - 180.0
    dlat = np.diff(lat, append=lat[0])
    seg_len = np.hypot(dlon_wrapped, dlat)
    if len(lon) >= 10 and float(np.median(seg_len)) < 0.28:
        lon, lat = chaikin_smooth_lonlat(lon, lat, 1)
        dlon_wrapped = ((np.diff(lon, append=lon[0]) + 180.0) % 360.0) - 180.0
        dlat = np.diff(lat, append=lat[0])
        seg_len = np.hypot(dlon_wrapped, dlat)
    if float(np.max(seg_len)) <= max_deg:
        return lon, lat
    out_lon, out_lat = [], []
    for i in range(len(lon)):
        steps = max(1, min(48, int(math.ceil(float(seg_len[i]) / max_deg))))
        for s in range(steps):
            u = s / steps
            out_lon.append(float(lon[i]) + u * float(dlon_wrapped[i]))
            out_lat.append(float(lat[i]) + u * float(dlat[i]))
    return np.asarray(out_lon), np.asarray(out_lat)


def load_rings(geojson_path: Path) -> list[dict]:
    global RINGS_BY_ISO
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
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
            lon_raw, lat_raw = arr[:, 0], arr[:, 1]
            if iso in HIGHLIGHT_ISOS:
                lon_sub, lat_sub = subdivide_ring_geodesic(lon_raw, lat_raw, 0.22)
            else:
                lon_sub, lat_sub = lon_raw, lat_raw
            xyz = lonlat_to_unit_xyz(lon_sub, lat_sub)
            center = np.mean(xyz, axis=0)
            center = center / max(float(np.linalg.norm(center)), 1e-9)
            min_dot = float(np.min(xyz @ center))
            rings.append({"iso": iso, "xyz": xyz, "center_xyz": center, "ang_radius": math.acos(max(-1.0, min(1.0, min_dot))), "clon": float(np.mean(lon_raw)), "clat": float(np.mean(lat_raw)), "n": int(len(lon_sub))})
    RINGS_BY_ISO = {}
    for ring in rings:
        RINGS_BY_ISO.setdefault(ring["iso"], []).append(ring)
    return rings


def where_ok(kind: str, lon: float, lat: float) -> bool:
    if kind == "alaska":
        return lat > 51.0 and (lon < -129.9 or lon > 170.0)
    if kind == "usa_lower48":
        return 24.0 <= lat <= 50.0 and -126.0 <= lon <= -66.0
    if kind == "cabinda":
        return 11.5 <= lon <= 13.2 and -6.02 <= lat <= -4.2
    if kind == "angola_main":
        return lat < -6.02
    if kind == "nakhchivan":
        return 44.7 <= lon <= 46.15 and 38.75 <= lat <= 39.85
    if kind == "azerbaijan_main":
        return lon > 46.15 or lat > 39.85
    return True


def split_visible_polylines_subpixel(x, y, visible, max_step):
    step = np.hypot(np.diff(x, prepend=x[:1]), np.diff(y, prepend=y[:1]))
    keep = visible & (step <= max_step)
    if not np.any(keep):
        return []
    cuts = np.where(np.diff(keep.astype(np.int8)) != 0)[0] + 1
    bounds = [0, *cuts.tolist(), len(x)]
    runs = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a >= 2 and bool(keep[a]):
            runs.append(np.round(np.column_stack([x[a:b], y[a:b]]) * SUBPIXEL_MULT).astype(np.int32))
    return runs


def _roi_from_subpixel(polys, pad):
    pts = np.concatenate(polys, axis=0)
    x0 = max(0, int(np.floor(np.min(pts[:, 0]) / SUBPIXEL_MULT)) - pad)
    y0 = max(0, int(np.floor(np.min(pts[:, 1]) / SUBPIXEL_MULT)) - pad)
    x1 = min(W, int(np.ceil(np.max(pts[:, 0]) / SUBPIXEL_MULT)) + pad)
    y1 = min(H, int(np.ceil(np.max(pts[:, 1]) / SUBPIXEL_MULT)) + pad)
    return None if x1 <= x0 or y1 <= y0 else (x0, y0, x1, y1)


def blend_polygon_roi_subpixel(frame, polys, color, weight, clip_disc, disc_r):
    if not polys or weight <= 0.005:
        return
    box = _roi_from_subpixel(polys, 4)
    if box is None:
        return
    x0, y0, x1, y1 = box
    offset = np.array([[int(round(x0 * SUBPIXEL_MULT)), int(round(y0 * SUBPIXEL_MULT))]], dtype=np.int32)
    roi = frame[y0:y1, x0:x1]
    overlay = roi.copy()
    cv2.fillPoly(overlay, [p - offset for p in polys], color, lineType=cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    if clip_disc:
        outside = FULL_R_PX[y0:y1, x0:x1] > disc_r * 0.995
        overlay[outside] = roi[outside]
    cv2.addWeighted(overlay, weight, roi, 1.0 - weight, 0.0, dst=roi)


def blend_polylines_roi_subpixel(frame, runs, color, thickness, alpha, glow, glow_thickness):
    if not runs or alpha <= 0.005:
        return
    box = _roi_from_subpixel(runs, glow_thickness + 6)
    if box is None:
        return
    x0, y0, x1, y1 = box
    offset = np.array([[int(round(x0 * SUBPIXEL_MULT)), int(round(y0 * SUBPIXEL_MULT))]], dtype=np.int32)
    local = [run - offset for run in runs]
    roi = frame[y0:y1, x0:x1]
    overlay = np.zeros_like(roi)
    cv2.polylines(overlay, local, False, glow, glow_thickness, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    cv2.polylines(overlay, local, False, color, thickness, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    mask = np.any(overlay > 0, axis=2)
    if np.any(mask):
        base = roi.astype(np.float32)
        base[mask] = base[mask] * (1.0 - alpha) + overlay.astype(np.float32)[mask] * alpha
        roi[:] = np.clip(base, 0, 255).astype(np.uint8)


def apply_vector_coast_refinement(frame, land_polys, span, w):
    if span >= 30.0 or w > 0.35 or not land_polys:
        return
    strength = float(smoothstep((30.0 - span) / 18.0)) * (1.0 - w)
    if strength <= 0.02:
        return
    land = np.zeros((H, W), np.uint8)
    cv2.fillPoly(land, land_polys, 255, lineType=cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    land_f = land.astype(np.float32) / 255.0
    shelf = (cv2.GaussianBlur(land, (0, 0), 9.0).astype(np.float32) / 255.0) * (1.0 - land_f) * strength
    water = ((1.0 - land_f) * strength * 0.62)[:, :, None]
    f32 = frame.astype(np.float32)
    ocean = f32 * 0.45 + np.array([10.0, 34.0, 74.0]) * 0.55 + np.array([24.0, 82.0, 142.0]) * shelf[:, :, None] * 0.65
    frame[:] = np.clip(f32 * (1.0 - water) + ocean * water, 0, 255).astype(np.uint8)


def draw_vector_highlights_and_borders(frame, rings, spec, lon0, lat0, span, w, t):
    mix, scale, disc_r = camera_scale_and_disc_radius(span, w)
    rotation, cam_fwd = camera_rotation_matrix(lon0, lat0)
    clip_disc = disc_r < SCREEN_DIAG_RADIUS + 10.0
    max_view = math.radians(min(92.0, max(span * 1.15, 18.0))) if mix < 0.35 else 1.58
    active = []
    for cue in spec.highlights:
        alpha = element_fade_and_exit_offset(t, cue.enter_t, cue.exit_t, 0.28, 0.30)[0]
        if alpha > 0.02:
            active.append((cue, alpha))
    active.sort(key=lambda item: item[0].z_order)
    active_isos = {cue.iso_a3 for cue, _ in active}
    coasts, land = [], []
    refine = span < 30.0 and w <= 0.35
    for ring in rings:
        if span > 55.0 and ring["n"] < 32:
            continue
        if ring["iso"] not in active_isos and float(ring["center_xyz"] @ cam_fwd) < math.cos(min(math.pi, max_view + ring["ang_radius"])):
            continue
        x, y, visible = project_xyz(ring["xyz"], rotation, mix, scale, False)
        if clip_disc:
            visible = visible & (np.hypot(x - W * 0.5, y - H * 0.5) <= disc_r * 0.994)
        if not np.any(visible) or not np.any((x > -120) & (x < W + 120) & (y > -120) & (y < H + 120)):
            continue
        coasts.extend(split_visible_polylines_subpixel(x, y, visible, 160.0))
        if refine and bool(np.all(visible)):
            land.append(np.round(np.column_stack([x, y]) * SUBPIXEL_MULT).astype(np.int32))
    if refine and land:
        apply_vector_coast_refinement(frame, land, span, w)
    if coasts:
        cv2.polylines(frame, coasts, False, (175, 190, 208), 2 if span < 22 else 1, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    for cue, alpha in active:
        fills, borders = [], []
        for ring in RINGS_BY_ISO.get(cue.iso_a3, []):
            if not where_ok(cue.where, ring["clon"], ring["clat"]) or (span > 45 and ring["n"] < 20):
                continue
            x_f, y_f, vis_f = project_xyz(ring["xyz"], rotation, mix, scale, True)
            if not np.any(vis_f) or not np.any((x_f > -250) & (x_f < W + 250) & (y_f > -250) & (y_f < H + 250)):
                continue
            jumps = np.hypot(np.diff(x_f), np.diff(y_f))
            if len(jumps) and float(np.max(jumps)) < 450:
                fills.append(np.round(np.column_stack([x_f, y_f]) * SUBPIXEL_MULT).astype(np.int32))
            x_b, y_b, vis_b = project_xyz(ring["xyz"], rotation, mix, scale, False)
            if clip_disc:
                vis_b = vis_b & (np.hypot(x_b - W * 0.5, y_b - H * 0.5) <= disc_r * 0.994)
            borders.extend(split_visible_polylines_subpixel(x_b, y_b, vis_b, 200.0))
        if fills:
            blend_polygon_roi_subpixel(frame, fills, cue.fill_rgba[:3], float(alpha) * (cue.fill_rgba[3] / 255.0) * 0.78, clip_disc, disc_r)
        if borders:
            thick = 4 if span < 12 else (3 if span < 32 else 2)
            glow = tuple(max(0, int(c * 0.22)) for c in cue.stroke_rgba[:3])
            blend_polylines_roi_subpixel(frame, borders, cue.stroke_rgba[:3], thick, float(alpha), glow, thick + 5)


def draw_split_arcs(frame, spec, lon0, lat0, span, w, t):
    for arc in spec.arcs:
        alpha = element_fade_and_exit_offset(t, arc.enter_t, arc.exit_t, 0.25, 0.28)[0]
        if alpha <= 0.04:
            continue
        progress = float(smootherstep(min(1.0, (t - arc.enter_t) / 0.85)))
        u = np.linspace(0.0, progress, 48)
        lons = arc.lon0 + u * (((arc.lon1 - arc.lon0 + 180.0) % 360.0) - 180.0)
        lats = arc.lat0 + u * (arc.lat1 - arc.lat0) + np.sin(u * math.pi) * min(3.5, span * 0.08)
        x, y, vis = project(lons, lats, lon0, lat0, span, w)
        if not np.all(vis):
            continue
        if float(np.min(x)) < 20 or float(np.max(x)) > W - 20 or float(np.min(y)) < 20 or float(np.max(y)) > H - 20:
            continue
        x0, y0 = max(0, int(np.floor(np.min(x))) - 28), max(0, int(np.floor(np.min(y))) - 28)
        x1, y1 = min(W, int(np.ceil(np.max(x))) + 28), min(H, int(np.ceil(np.max(y))) + 28)
        if x1 <= x0 or y1 <= y0:
            continue
        roi = frame[y0:y1, x0:x1]
        overlay = roi.copy()
        pts = np.round(np.column_stack([x - x0, y - y0]) * SUBPIXEL_MULT).astype(np.int32)
        for i in range(0, len(pts) - 1, 2):
            p0, p1 = tuple(pts[i]), tuple(pts[min(i + 1, len(pts) - 1)])
            cv2.line(overlay, p0, p1, (14, 18, 26), 7, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
            cv2.line(overlay, p0, p1, arc.color_rgb, 4, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
        pulse = int(round((10 + 4 * math.sin(t * 6)) * SUBPIXEL_MULT))
        for elon, elat in ((arc.lon0, arc.lat0), (arc.lon1, arc.lat1)):
            ex, ey, ev = project(np.array([elon]), np.array([elat]), lon0, lat0, span, w)
            if bool(ev[0]):
                c = (int(round((float(ex[0]) - x0) * SUBPIXEL_MULT)), int(round((float(ey[0]) - y0) * SUBPIXEL_MULT)))
                cv2.circle(overlay, c, pulse, arc.color_rgb, 3, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
                cv2.circle(overlay, c, int(5 * SUBPIXEL_MULT), (255, 255, 255), -1, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
        cv2.addWeighted(overlay, float(alpha), roi, 1 - float(alpha), 0, dst=roi)


def resolve_2d_label_collisions(boxes, min_gap_px=22.0, iterations=16):
    centers = [[float(b[0]), float(b[1])] for b in boxes]
    sizes = [(float(b[2]), float(b[3])) for b in boxes]
    for _ in range(iterations):
        moved = False
        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                dx, dy = centers[j][0] - centers[i][0], centers[j][1] - centers[i][1]
                ox = (sizes[i][0] + sizes[j][0]) * 0.5 + min_gap_px - abs(dx)
                oy = (sizes[i][1] + sizes[j][1]) * 0.5 + min_gap_px - abs(dy)
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
    return [(max(80.0, min(SAFE_RIGHT - 40.0, c[0])), max(220.0, min(1240.0, c[1]))) for c in centers]


def text_size(draw, text, face):
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0], box[3] - box[1]


def mercator_area_factor(lat_deg: float) -> float:
    return 1.0 / max(math.cos(math.radians(float(np.clip(lat_deg, -78.0, 78.0)))), 0.08) ** 2


def draw_truesize_compare(draw, lat0, span, w, t) -> bool:
    if not (span < 34.0 and 56.0 < lat0 < 70.0 and w < 0.25):
        return False
    alpha = 1.0
    factor = mercator_area_factor(lat0)
    linear = min(math.sqrt(factor), 2.4)
    true_r, merc_r = 28, int(round(28 * linear))
    true_c, merc_c = (220, 1045), (220 + 28 + merc_r + 40, 1045)
    if merc_c[0] + merc_r > SAFE_RIGHT:
        shift = merc_c[0] + merc_r - SAFE_RIGHT
        true_c = (true_c[0] - shift, true_c[1])
        merc_c = (merc_c[0] - shift, merc_c[1])
    a = int(230 * alpha)
    draw.ellipse([true_c[0] - true_r, true_c[1] - true_r, true_c[0] + true_r, true_c[1] + true_r], fill=(245, 197, 24, a))
    draw.ellipse([merc_c[0] - merc_r, merc_c[1] - merc_r, merc_c[0] + merc_r, merc_c[1] + merc_r], outline=(0, 229, 255, a), width=4)
    face = get_font(26)
    draw.text((true_c[0] - 24, true_c[1] + true_r + 6), "TRUE", font=face, fill=(255, 255, 255, a))
    label = f"MERCATOR {factor:.1f}×"
    tw, _ = text_size(draw, label, face)
    draw.text((merc_c[0] - tw / 2, merc_c[1] + merc_r + 6), label, font=face, fill=(0, 229, 255, a))
    return True


def composite_rgba_roi(rgb_frame, rgba_overlay, y0, y1):
    y0, y1 = max(0, min(H, y0)), max(0, min(H, y1))
    if y1 <= y0:
        return
    sub = rgba_overlay[y0:y1]
    alpha = sub[:, :, 3:4].astype(np.float32) / 255.0
    if np.any(alpha > 0.002):
        dst = rgb_frame[y0:y1].astype(np.float32)
        rgb_frame[y0:y1] = np.clip(dst * (1 - alpha) + sub[:, :, :3].astype(np.float32) * alpha, 0, 255).astype(np.uint8)


def draw_overlay(rgb, spec, phrases, lon0, lat0, span, w, t):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    min_y, max_y = H, 0
    visible = []
    for label in spec.labels:
        alpha = element_fade_and_exit_offset(t, label.enter_t, label.exit_t, 0.26, 0.28)[0]
        if alpha <= 0.04:
            continue
        x, y, vis = project(np.array([label.lon]), np.array([label.lat]), lon0, lat0, span, w)
        if not bool(vis[0]):
            continue
        px, py = float(x[0]), float(y[0])
        if not (40 < px < W - 40 and 180 < py < H - 280):
            continue
        pop, _ = label_pop_state(t - label.enter_t, 0.28)
        face = get_font(min(label.font_size, 34) * max(pop, 0.5))
        tw, th = text_size(draw, label.text, face)
        visible.append((label, alpha, px, py, tw + 16, th + 14, face))
    if visible:
        centers = resolve_2d_label_collisions([(px, py, tw, th) for _l, _a, px, py, tw, th, _f in visible])
        for (label, alpha, _px, _py, _tw, _th, face), (cx, cy) in zip(visible, centers):
            tw, th = text_size(draw, label.text, face)
            ox, oy = cx - tw / 2, cy - th / 2
            ink = label.color_rgba[:3] + (int(255 * alpha),)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                draw.text((ox + dx, oy + dy), label.text, font=face, fill=(8, 12, 20, int(230 * alpha)))
            draw.text((ox, oy), label.text, font=face, fill=ink)
            min_y, max_y = min(min_y, int(oy) - 8), max(max_y, int(oy + th) + 8)
    if draw_truesize_compare(draw, lat0, span, w, t):
        min_y, max_y = min(min_y, 960), max(max_y, 1180)
    for pill in spec.pills:
        alpha, dx, dy = element_fade_and_exit_offset(t, pill.enter_t, pill.exit_t, 0.25, 0.28)
        if alpha <= 0.04:
            continue
        pop, _ = label_pop_state(t - pill.enter_t, 0.28)
        font_sz = 34.0 * max(pop, 0.85)
        face = get_font(font_sz)
        bg, fg = PILL_RGB.get(pill.theme, PILL_RGB["dark"])
        display = pill.text
        if pill.counter_fmt:
            roll = float(smootherstep(min(1.0, max(0.0, (t - pill.enter_t) / 0.65))))
            display = pill.counter_fmt.format(val=pill.counter_start + roll * (pill.counter_end - pill.counter_start))
        tw_fixed, th = text_size(draw, pill.text, face)
        tw_cur, _ = text_size(draw, display, face)
        tw = max(tw_fixed, tw_cur)
        box_w, box_h = tw + 48, th + 28
        if box_w > SAFE_RIGHT - 80:
            font_sz *= (SAFE_RIGHT - 80) / box_w
            face = get_font(font_sz)
            tw_fixed, th = text_size(draw, pill.text, face)
            tw_cur, _ = text_size(draw, display, face)
            tw = max(tw_fixed, tw_cur)
            box_w, box_h = tw + 48, th + 28
        cx = max(80 + box_w / 2, min(SAFE_RIGHT - box_w / 2, pill.screen_x + dx))
        cy = max(210 + box_h / 2, min(1100 - box_h / 2, pill.screen_y + dy))
        rect = [cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2]
        a_solid = int(250 * (alpha ** 0.55))
        draw.rounded_rectangle([rect[0] + 3, rect[1] + 5, rect[2] + 3, rect[3] + 5], radius=16, fill=(6, 10, 18, int(180 * alpha)))
        draw.rounded_rectangle(rect, radius=16, fill=bg + (a_solid,))
        draw.text((cx - tw_cur / 2, cy - th / 2 - 1), display, font=face, fill=fg + (a_solid,))
        min_y, max_y = min(min_y, int(rect[1]) - 8), max(max_y, int(rect[3]) + 12)
    active = None
    for phrase in phrases:
        if phrase[0]["start"] - 0.08 <= t <= phrase[-1]["end"] + 0.12:
            active = phrase
            break
    if active:
        face = get_font(62)
        gap = 16
        widths = [text_size(draw, w["text"], face)[0] for w in active]
        total = sum(widths) + gap * (len(active) - 1)
        if total > 880:
            face = get_font(max(46, 62 * 880 / total))
            widths = [text_size(draw, w["text"], face)[0] for w in active]
            total = sum(widths) + gap * (len(active) - 1)
        x_cur, y_cur, lead = (W - total) * 0.5, 1310.0, t + 0.04
        for word, width in zip(active, widths):
            color = (0, 229, 255, 255) if word["start"] <= lead <= word["end"] else (255, 255, 255, 255)
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                draw.text((x_cur + dx, y_cur + dy), word["text"], font=face, fill=(8, 12, 20, 250))
            draw.text((x_cur, y_cur), word["text"], font=face, fill=color)
            x_cur += width + gap
        min_y, max_y = min(min_y, 1280), max(max_y, 1420)
    if max_y > min_y:
        composite_rgba_roi(rgb, np.asarray(overlay, dtype=np.uint8), min_y, max_y)
    return rgb


WEAK_WORDS = {"A", "AN", "THE", "OF", "TO", "IN", "ON", "FOR", "AND", "OR", "WITH", "BY", "IS", "IT'S"}


def clean_caption_token(raw: str) -> str:
    return raw.strip().strip(",.;:?!\"'“”—-").upper().replace("730-KILOMETER", "730 KM").replace("1.2-KILOMETER", "1.2 KM")


def phrase_width(words: List[str]) -> int:
    return sum(len(word) for word in words) + max(0, len(words) - 1)


def group_spoken_phrases(spoken: List[dict]) -> List[List[Dict]]:
    phrases, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            phrases.append(cur)
            cur = []

    for item in spoken:
        token = clean_caption_token(str(item["text"]))
        if not token:
            continue
        raw = str(item["text"]).strip()
        if cur and token in WEAK_WORDS and len(cur) >= 2:
            flush()
        trial = [str(word["text"]) for word in cur] + [token]
        if cur and (len(trial) > 3 or phrase_width(trial) > 18):
            flush()
        cur.append({"text": token, "start": float(item["start"]), "end": float(item["end"])})
        if raw.endswith((".", "?", "!", ",")) and len(cur) >= 2:
            flush()
    flush()
    return phrases


def align_words_from_audio_envelope(pcm, sr, script_lines):
    audio_dur = len(pcm) / sr
    planned_end = max(script_lines[-1][1], 1.0)
    scale = audio_dur / planned_end
    hop = int(round(0.02 * sr))
    n_wins = max(1, len(pcm) // hop)
    rms = np.array([float(np.sqrt(np.mean(pcm[i * hop:(i + 1) * hop] ** 2))) for i in range(n_wins)])
    thresh = max(0.012, float(np.percentile(rms, 22)))
    spoken = []
    for t0_p, t1_p, line in script_lines:
        t0, t1 = t0_p * scale, min(audio_dur, t1_p * scale)
        w0, w1 = max(0, int(t0 / 0.02)), max(1, min(n_wins, int(t1 / 0.02)))
        active = np.where(rms[w0:w1] > thresh)[0]
        if len(active) >= 2:
            t0, t1 = (w0 + int(active[0])) * 0.02, min(audio_dur, (w0 + int(active[-1]) + 1) * 0.02)
        tokens = [tok for tok in line.split() if clean_caption_token(tok)]
        weights = [max(2.0, len(clean_caption_token(tok))) for tok in tokens]
        total = sum(weights) or 1
        cursor, seg = t0, max(0.15, t1 - t0)
        for tok, wt in zip(tokens, weights):
            dur = seg * wt / total
            spoken.append({"text": tok, "start": round(cursor, 3), "end": round(cursor + dur * 0.94, 3), "type": "word"})
            cursor += dur
    return spoken


def detect_episode_id(text: str) -> str:
    low = text.lower()
    if any(token in low for token in ("brazil", "hans", "botswana", "gibraltar", "north korea")):
        return "impossible_neighbors"
    return "cut_in_two"


def load_measured_words() -> List[dict] | None:
    if not LATEST_WORDS.exists():
        return None
    payload = json.loads(LATEST_WORDS.read_text(encoding="utf-8"))
    words = [word for word in payload.get("words", []) if word.get("type", "word") == "word"]
    return words or None


def prepare_voiceover_and_karaoke_phrases(base_spec: EpisodeSpec):
    sr = 48000
    wav_path = CACHE_DIR / "latest_vo.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(LATEST_VO), "-ar", str(sr), "-ac", "1", str(wav_path)], check=True)
    with wave.open(str(wav_path), "rb") as wf:
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    audio_seconds = len(pcm) / sr
    print(f"[AUDIO] {audio_seconds:.2f}s from {LATEST_VO.name}", flush=True)
    spoken = load_measured_words()
    if spoken is None:
        spoken = align_words_from_audio_envelope(pcm, sr, base_spec.script_lines)
        print(f"[AUDIO] envelope aligned {len(spoken)} words", flush=True)
    else:
        print(f"[AUDIO] measured {len(spoken)} word times", flush=True)
    spec = scale_episode_timing(base_spec, max(audio_seconds + 0.45, base_spec.total_duration))
    total = int(round(spec.total_duration * sr))
    track = np.zeros(total, dtype=np.float64)
    n = min(len(pcm), total)
    track[:n] = pcm[:n]
    phrases = group_spoken_phrases(spoken)
    master = np.column_stack([track, track])
    rng = np.random.default_rng(42)
    n_w = int(round(0.34 * sr))
    tw = np.linspace(0, 1, n_w)
    env = 30 * tw ** 2 * (1 - tw) ** 2
    noise = rng.normal(0, 1, n_w)
    smooth = np.convolve(noise, np.ones(32) / 32, mode="same")
    whoosh = env * (smooth - np.convolve(smooth, np.ones(120) / 120, mode="same")) * 0.10
    for mv in spec.moves:
        idx = int(round(max(0.0, mv.start_t + 0.5 * mv.duration - 0.17) * sr))
        end = min(total, idx + n_w)
        if end > idx:
            master[idx:end] += whoosh[: end - idx, None] * 0.4
    n_p = int(round(0.045 * sr))
    tp = np.linspace(0, 0.045, n_p)
    thud = np.exp(-tp * 85) * np.sin(math.pi * tp / 0.045) * np.sin(2 * math.pi * (150 * tp - 1100 * tp ** 2)) * 0.05
    for pt in {p.enter_t for p in spec.pills}:
        idx = int(round(max(0.0, pt + 0.02) * sr))
        end = min(total, idx + n_p)
        if end > idx:
            master[idx:end] += thud[: end - idx, None]
    peak = float(np.max(np.abs(master)))
    if peak > 0.89:
        master *= 0.89 / peak
    return spec, master, phrases


def render_frame_at(rings, spec, phrases, st, t):
    focus = float(smoothstep((35.0 - st["span"]) / 20.0)) * (1.0 - st["w"])
    frame = spherical_camera_warp(st["lon"], st["lat"], st["span"], st["w"], focus)
    draw_vector_highlights_and_borders(frame, rings, spec, st["lon"], st["lat"], st["span"], st["w"], t)
    draw_split_arcs(frame, spec, st["lon"], st["lat"], st["span"], st["w"], t)
    return draw_overlay(frame, spec, phrases, st["lon"], st["lat"], st["span"], st["w"], t)


def main() -> None:
    global PLATE, STARS
    ensure_assets()
    words = load_measured_words() or []
    text = " ".join(word["text"] for word in words)
    episode_id = detect_episode_id(text)
    if "--impossible" in sys.argv:
        episode_id = "impossible_neighbors"
    if "--cut-in-two" in sys.argv:
        episode_id = "cut_in_two"
    print(f"[EPISODE] detected {episode_id}", flush=True)
    PLATE = load_enhanced_plate()
    STARS = make_starfield()
    rings = load_rings(GEOJSON_10M)
    print(f"[ASSET] {len(rings)} rings", flush=True)
    base = build_impossible_neighbors_episode() if episode_id == "impossible_neighbors" else build_cut_in_two_episode()
    spec, audio, phrases = prepare_voiceover_and_karaoke_phrases(base)
    rig = spec.build_rig()
    for size in range(18, 72, 2):
        get_font(size)
    out_mp4 = OUT_DIR / f"{spec.episode_id}.mp4"
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out = Path("/tmp/neighbors_stills")
        out.mkdir(parents=True, exist_ok=True)
        times = [float(x) for x in sys.argv[2:] if not x.startswith("--")] or [2.5, 9.2, 14.0, 32.0, 39.6, 49.4, 58.5, 62.2, 70.0]
        for t in times:
            st = rig.evaluate_all(min(t, spec.total_duration - 0.01))
            Image.fromarray(render_frame_at(rings, spec, phrases, st, t)).save(out / f"t_{t:05.1f}.jpg", quality=90)
            print(f"[STILL] t={t:.1f} span={st['span']:.1f} lon={st['lon']:.1f} lat={st['lat']:.1f}", flush=True)
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = Path("/tmp/neighbors_master.wav")
    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes((audio * 32767.0).astype(np.int16).tobytes())
    n_frames = int(round(spec.total_duration * FPS))
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-i", str(wav_path), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out_mp4)]
    print(f"[RENDER] {n_frames} frames -> {out_mp4}", flush=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for frame_idx in range(n_frames):
            t = spec.total_duration if frame_idx == n_frames - 1 else frame_idx / FPS
            proc.stdin.write(render_frame_at(rings, spec, phrases, rig.evaluate_all(t), t).tobytes())
            if frame_idx % (FPS * 5) == 0:
                print(f"  frame {frame_idx:04d}/{n_frames} t={t:.1f}", flush=True)
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("FFmpeg failed")
    print(f"[DONE] {out_mp4}", flush=True)


if __name__ == "__main__":
    main()
