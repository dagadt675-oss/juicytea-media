#!/usr/bin/env python3
"""
Juicy Tea map-shorts engine for Countries Cut in Two.

1080x1920 at 60fps. The Earth is a circular sphere. Country fills come from
Natural Earth 10m, drawn with 16x sub-pixel edges. The Brian narration is
played once and the karaoke uses the measured word times.

Fills and double-stroke borders share one smootherstep alpha. Pills stay at
or left of x=895. The Alaska true-size card sits at y=1045 and draws the
real outline next to the Mercator sec(lat) enlargement.
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
MIN_SPAN_DEG = 3.2
MAX_SPAN_DEG = 170.0
TOTAL_DURATION = 79.00
SAFE_RIGHT = 895.0
SUBPIXEL_SHIFT = 4
SUBPIXEL_MULT = float(1 << SUBPIXEL_SHIFT)

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
UPLOAD_MP3 = Path(
    "/home/ubuntu/.cursor/projects/workspace/uploads/"
    "ElevenLabs_2026-10-14T10_39_49_Brian_-_Deep__Resonant_and_Comforting_pre_sp100_s50_sb75_v4_f582.mp3"
)
OUT_MP4 = WORKSPACE / "v" / "cut_in_two.mp4"
HIGHLIGHT_ISOS = {"USA", "CAN", "MYS", "BRN", "OMN", "ARE", "COD", "AGO", "AZE", "ARM"}


def smoothstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * (3.0 - 2.0 * u_c)


def smootherstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * u_c * (u_c * (u_c * 6.0 - 15.0) + 10.0)


def icon_pop_scale(elapsed_s: float, duration_s: float = 0.55, peak: float = 1.12) -> float:
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
    fade_in_s: float = 0.28,
    fade_out_s: float = 0.30,
    exit_drift_px: Tuple[float, float] = (12.0, -8.0),
) -> Tuple[float, float, float]:
    fade_in_s = max(fade_in_s, 0.25)
    fade_out_s = max(fade_out_s, 0.25)
    exit_move_s = max(fade_out_s, 0.40)
    if t <= enter_t or t >= exit_t + fade_out_s:
        return 0.0, 0.0, 0.0
    if t < enter_t + fade_in_s:
        alpha = float(smootherstep((t - enter_t) / fade_in_s))
        return alpha, 0.0, 0.0
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
        ddh0 = -60.0 * u + 180.0 * u2 - 120.0 * u3
        ddh1 = -36.0 * u + 96.0 * u2 - 60.0 * u3
        ddh2 = 60.0 * u - 180.0 * u2 + 120.0 * u3
        ddh3 = -24.0 * u + 84.0 * u2 - 60.0 * u3
        acc = (ddh0 * y0 + ddh1 * (h * v0) + ddh2 * y1 + ddh3 * (h * v1)) / (h * h)
        return float(pos), float(vel), float(acc)


def hermite_segment(t: float, t0: float, t1: float, p0: float, v0: float, p1: float, v1: float) -> Tuple[float, float, float]:
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
    ddh00 = 12.0 * u - 6.0
    ddh10 = 6.0 * u - 4.0
    ddh01 = -12.0 * u + 6.0
    ddh11 = 6.0 * u - 2.0
    acc = (ddh00 * p0 + ddh10 * (duration * v0) + ddh01 * p1 + ddh11 * (duration * v1)) / (duration * duration)
    return float(pos), float(vel), float(acc)


class ContinuousCameraRig:
    def __init__(self, anchors: List[CameraAnchor], total_duration: float) -> None:
        self.total_duration = float(total_duration)
        self.loop_start_t = self.total_duration - LOOP_TAIL_SEC
        self.v0_w = 0.0
        self.v0_lon = 0.16
        self.v0_lat = 0.03
        self.v0_log_span = -0.015
        first = anchors[0]
        core_anchors = [a for a in anchors if a.t < self.loop_start_t - 0.6]
        pre_loop_span = first.span / math.exp(self.v0_log_span * LOOP_TAIL_SEC)
        core_anchors.append(
            CameraAnchor(
                t=self.loop_start_t,
                w=first.w,
                lon=first.lon - self.v0_lon * LOOP_TAIL_SEC,
                lat=first.lat - self.v0_lat * LOOP_TAIL_SEC,
                span=pre_loop_span,
            )
        )
        self.anchors = core_anchors
        t_arr = np.array([a.t for a in core_anchors], dtype=np.float64)
        w_arr = np.array([a.w for a in core_anchors], dtype=np.float64)
        lon_arr = np.rad2deg(np.unwrap(np.deg2rad([a.lon for a in core_anchors])))
        lat_arr = np.array([a.lat for a in core_anchors], dtype=np.float64)
        log_span_arr = np.log(np.array([a.span for a in core_anchors], dtype=np.float64))
        self.spline_w = TimeParameterizedC2Spline(t_arr, w_arr, v_start=self.v0_w, v_end=self.v0_w)
        self.spline_lon = TimeParameterizedC2Spline(t_arr, lon_arr, v_start=self.v0_lon, v_end=self.v0_lon)
        self.spline_lat = TimeParameterizedC2Spline(t_arr, lat_arr, v_start=self.v0_lat, v_end=self.v0_lat)
        self.spline_log_span = TimeParameterizedC2Spline(t_arr, log_span_arr, v_start=self.v0_log_span, v_end=self.v0_log_span)

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
            lon1_wrapped = lon0 + ((lon1 - lon0 + 180.0) % 360.0 - 180.0)
            lon, dlon, ddlon = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lon0, dlon0, lon1_wrapped, dlon1)
            lat0, dlat0, _ = self.spline_lat.eval_with_derivs(self.loop_start_t)
            lat1, dlat1, _ = self.spline_lat.eval_with_derivs(0.0)
            lat, dlat, ddlat = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lat0, dlat0, lat1, dlat1)
            ls0, dls0, _ = self.spline_log_span.eval_with_derivs(self.loop_start_t)
            ls1, dls1, _ = self.spline_log_span.eval_with_derivs(0.0)
            lspan, dlspan, ddlspan = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, ls0, dls0, ls1, dls1)
        return {
            "w": float(np.clip(w, 0.0, 1.0)),
            "dw": dw,
            "ddw": ddw,
            "lon": lon,
            "dlon": dlon,
            "ddlon": ddlon,
            "lat": lat,
            "dlat": dlat,
            "ddlat": ddlat,
            "log_span": lspan,
            "dlog_span": dlspan,
            "ddlog_span": ddlspan,
            "span": math.exp(lspan),
        }


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
    map_has_yellow: bool = True

    def build_rig(self) -> ContinuousCameraRig:
        anchors: List[CameraAnchor] = []
        for i, mv in enumerate(self.moves):
            if i > 0:
                prev = anchors[-1]
                hold_dt = max(0.0, mv.start_t - prev.t)
                if hold_dt > 0.05:
                    drifted_span = float(np.clip(prev.span * math.exp(mv.drift_scale_rate * hold_dt), MIN_SPAN_DEG + 0.1, MAX_SPAN_DEG - 1.0))
                    drifted_lon = prev.lon + mv.drift_lon_rate * hold_dt * (prev.span / 50.0)
                    drifted_lat = prev.lat + mv.drift_lat_rate * hold_dt * (prev.span / 50.0)
                    anchors.append(CameraAnchor(t=mv.start_t, w=mv.w_start, lon=drifted_lon, lat=drifted_lat, span=drifted_span, is_snap=mv.is_snap))
            else:
                anchors.append(CameraAnchor(t=mv.start_t, w=mv.w_start, lon=mv.lon_start, lat=mv.lat_start, span=mv.span_start, is_snap=mv.is_snap))
            anchors.append(CameraAnchor(t=mv.start_t + mv.duration, w=mv.w_end, lon=mv.lon_end, lat=mv.lat_end, span=mv.span_end, is_snap=mv.is_snap))
        return ContinuousCameraRig(anchors, total_duration=self.total_duration)


def build_cut_in_two_episode() -> EpisodeSpec:
    total_dur = TOTAL_DURATION
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
        CountryHighlightCue(10, "USA", 0.00, 12.30, (245, 198, 45, 215), (255, 235, 120, 255), where="alaska"),
        CountryHighlightCue(10, "USA", 7.40, 12.30, (245, 198, 45, 215), (255, 235, 120, 255), where="usa_lower48"),
        CountryHighlightCue(15, "CAN", 6.00, 12.30, (225, 75, 70, 210), (255, 155, 150, 255), where="all"),
        CountryHighlightCue(10, "MYS", 16.60, 33.50, (220, 75, 70, 210), (255, 150, 145, 255), where="all"),
        CountryHighlightCue(20, "BRN", 22.40, 33.50, (250, 205, 25, 240), (255, 245, 150, 255), where="all"),
        CountryHighlightCue(15, "OMN", 34.10, 43.60, (225, 75, 70, 225), (255, 160, 155, 255), where="all"),
        CountryHighlightCue(10, "ARE", 36.40, 43.60, (245, 198, 45, 220), (255, 235, 120, 255), where="all"),
        CountryHighlightCue(10, "COD", 49.90, 59.80, (65, 155, 205, 215), (150, 220, 255, 255), where="all"),
        CountryHighlightCue(15, "AGO", 55.90, 59.80, (70, 175, 100, 215), (155, 245, 180, 255), where="angola_main"),
        CountryHighlightCue(20, "AGO", 51.10, 59.80, (250, 205, 25, 240), (255, 245, 150, 255), where="cabinda"),
        CountryHighlightCue(10, "AZE", 61.70, 75.10, (65, 155, 205, 220), (150, 220, 255, 255), where="azerbaijan_main"),
        CountryHighlightCue(15, "ARM", 64.20, 75.10, (238, 135, 55, 225), (255, 200, 140, 255), where="all"),
        CountryHighlightCue(20, "AZE", 65.00, 75.10, (250, 205, 25, 240), (255, 245, 150, 255), where="nakhchivan"),
        CountryHighlightCue(10, "USA", 76.70, 79.00, (245, 198, 45, 215), (255, 235, 120, 255), where="alaska"),
    ]
    arcs = [
        SplitArcCue(-148.0, 62.5, -120.5, 47.5, 7.70, 12.15, (0, 229, 255)),
        SplitArcCue(102.2, 4.0, 113.5, 3.2, 18.20, 22.70, (0, 229, 255)),
        SplitArcCue(114.65, 4.85, 115.12, 4.70, 25.70, 33.40, (0, 229, 255)),
        SplitArcCue(57.2, 23.6, 56.25, 26.05, 36.80, 43.40, (0, 229, 255)),
        SplitArcCue(17.2, -11.6, 12.30, -5.22, 52.10, 59.60, (0, 229, 255)),
        SplitArcCue(47.2, 40.1, 45.4, 39.2, 65.40, 74.95, (0, 229, 255)),
    ]
    labels = [
        MapLabelItem("ALASKA", -151.0, 64.5, 1.30, 6.00),
        MapLabelItem("BRITISH", -114.0, 56.5, 8.15, 9.85),
        MapLabelItem("CANADA", -108.0, 56.5, 9.85, 12.25),
        MapLabelItem("MALAYSIA", 102.2, 4.5, 17.05, 22.30),
        MapLabelItem("PENINSULA", 101.5, 2.2, 17.70, 22.30),
        MapLabelItem("BORNEO", 114.5, 1.5, 18.70, 22.50),
        MapLabelItem("BRUNEI", 114.60, 5.02, 23.20, 33.40),
        MapLabelItem("SARAWAK", 113.85, 3.70, 25.50, 33.40),
        MapLabelItem("LIMBANG", 114.98, 4.42, 26.30, 33.40),
        MapLabelItem("MUSANDAM", 56.10, 26.45, 36.50, 43.45, color_rgba=(255, 165, 165, 255)),
        MapLabelItem("UAE", 54.5, 24.3, 37.15, 43.45),
        MapLabelItem("OMAN", 57.5, 23.3, 38.90, 43.45, color_rgba=(255, 155, 155, 255)),
        MapLabelItem("CABINDA", 12.05, -4.85, 51.50, 59.70),
        MapLabelItem("DR CONGO", 17.6, -4.6, 53.20, 59.70),
        MapLabelItem("ANGOLA", 17.4, -12.4, 56.20, 59.70),
        MapLabelItem("NAKHCHIVAN", 45.05, 38.65, 65.20, 75.05),
        MapLabelItem("ARMENIA", 44.55, 40.35, 67.70, 75.05, color_rgba=(255, 190, 115, 255)),
        MapLabelItem("AZERBAIJAN", 47.55, 40.15, 66.10, 75.05, color_rgba=(140, 215, 255, 255)),
        MapLabelItem("IRAN", 46.15, 37.85, 69.20, 73.20),
        MapLabelItem("TURKEY", 44.15, 39.55, 71.70, 74.70),
    ]
    pills = [
        PillBannerItem("$7.2M · ≈2¢/ACRE · 1867", 540.0, 300.0, 1.05, 5.50, theme="red", counter_start=0.0, counter_end=7.2, counter_fmt="${val:.1f}M · ≈2¢/ACRE · 1867"),
        PillBannerItem("BORDER CHECK", 540.0, 390.0, 4.70, 6.05, theme="red"),
        PillBannerItem("1867", 540.0, 300.0, 6.15, 9.40, theme="dark"),
        PillBannerItem("STILL IN THE WAY", 540.0, 390.0, 10.85, 12.30, theme="red"),
        PillBannerItem("2 PIECES", 540.0, 300.0, 13.85, 15.30, theme="dark"),
        PillBannerItem("1963", 540.0, 300.0, 15.45, 16.90, theme="dark"),
        PillBannerItem("2-HOUR FLIGHT", 540.0, 300.0, 21.10, 22.85, theme="blue"),
        PillBannerItem("1890", 540.0, 300.0, 24.35, 25.70, theme="dark"),
        PillBannerItem("OUT OF THE MIDDLE", 540.0, 390.0, 27.20, 28.55, theme="dark"),
        PillBannerItem("19 MI", 540.0, 300.0, 31.15, 33.50, theme="blue", counter_start=0.0, counter_end=19.0, counter_fmt="{val:.0f} MI"),
        PillBannerItem("STRAIT OF HORMUZ", 540.0, 300.0, 35.55, 38.55, theme="blue"),
        PillBannerItem("UAE IN BETWEEN", 540.0, 390.0, 37.15, 38.60, theme="yellow"),
        PillBannerItem("EXIT OMAN", 540.0, 300.0, 41.55, 43.50, theme="red"),
        PillBannerItem("SAME TRICK", 540.0, 220.0, 43.95, 49.35, theme="dark"),
        PillBannerItem("ALASKA", 280.0, 330.0, 45.70, 49.30, theme="yellow"),
        PillBannerItem("MALAYSIA", 620.0, 330.0, 46.00, 49.30, theme="red"),
        PillBannerItem("BRUNEI", 280.0, 450.0, 46.30, 49.30, theme="yellow"),
        PillBannerItem("OMAN", 620.0, 450.0, 46.60, 49.30, theme="red"),
        PillBannerItem("A WHOLE SEA", 540.0, 570.0, 47.55, 49.40, theme="blue"),
        PillBannerItem("1885", 540.0, 300.0, 49.95, 51.30, theme="dark"),
        PillBannerItem("WRONG SIDE", 540.0, 300.0, 58.25, 59.75, theme="red"),
        PillBannerItem("1921", 540.0, 300.0, 61.55, 63.05, theme="dark"),
        PillBannerItem("TURKEY · 11 KM", 540.0, 300.0, 71.45, 74.20, theme="red", counter_start=0.0, counter_end=11.0, counter_fmt="TURKEY · {val:.0f} KM"),
        PillBannerItem("EXCEPT AZERBAIJAN", 540.0, 390.0, 73.45, 75.05, theme="dark"),
    ]
    events = sorted({round(t * 1.10, 2) for t in range(1, int(total_dur / 1.10) + 1) if t * 1.10 < total_dur})
    return EpisodeSpec(
        episode_id="cut_in_two",
        total_duration=total_dur,
        first_highlight_t=0.10,
        moves=moves,
        event_timestamps=events,
        highlights=highlights,
        arcs=arcs,
        labels=labels,
        pills=pills,
        map_has_yellow=True,
    )


FONT_PATH = "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"
if not Path(FONT_PATH).exists():
    for alt in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if Path(alt).exists():
            FONT_PATH = alt
            break

FONTS: dict[int, ImageFont.FreeTypeFont] = {}
PLATE: np.ndarray | None = None
STARS: np.ndarray | None = None
RINGS_BY_ISO: dict[str, list[dict]] = {}
ALASKA_SHAPE: np.ndarray | None = None

GRID_STEP = 6
GX_1D = np.linspace(0.0, float(W), W // GRID_STEP + 1, dtype=np.float64)
GY_1D = np.linspace(0.0, float(H), H // GRID_STEP + 1, dtype=np.float64)
GX, GY = np.meshgrid(GX_1D, GY_1D)
FULL_XS = np.arange(W, dtype=np.float32)[None, :]
FULL_YS = np.arange(H, dtype=np.float32)[:, None]
FULL_R_PX = np.hypot(FULL_XS - W * 0.5, FULL_YS - H * 0.5)


def get_font(size: float) -> ImageFont.FreeTypeFont:
    key = max(10, int(round(size)))
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(FONT_PATH, key)
    return FONTS[key]


def ensure_assets() -> Path:
    if not PLATE_PATH.exists() or PLATE_PATH.stat().st_size < 100_000:
        print("[ASSET] Downloading NASA Topo/Bathy Satellite Plate...", flush=True)
        urllib.request.urlretrieve(PLATE_URL, PLATE_PATH)
    if not GEOJSON_10M.exists() or GEOJSON_10M.stat().st_size < 500_000:
        print("[ASSET] Downloading Natural Earth 10m High-Res Borders...", flush=True)
        urllib.request.urlretrieve(GEOJSON_10M_URL, GEOJSON_10M)
    if (not BRIAN_MP3.exists() or BRIAN_MP3.stat().st_size < 100_000) and UPLOAD_MP3.exists():
        shutil.copyfile(UPLOAD_MP3, BRIAN_MP3)
    if not BRIAN_MP3.exists():
        raise FileNotFoundError(f"Approved narration is missing: {BRIAN_MP3}")
    if not BRIAN_WORDS.exists():
        raise FileNotFoundError(f"Measured word timings are missing: {BRIAN_WORDS}")
    return GEOJSON_10M


def load_enhanced_plate() -> np.ndarray:
    raw = np.asarray(Image.open(PLATE_PATH).convert("RGB"), dtype=np.uint8)
    denoised = cv2.bilateralFilter(raw, d=5, sigmaColor=18, sigmaSpace=18)
    blur = cv2.GaussianBlur(denoised, (0, 0), 1.6)
    return cv2.addWeighted(denoised, 1.38, blur, -0.38, 0)


def make_starfield() -> np.ndarray:
    rng = np.random.default_rng(11)
    img = np.zeros((H, W, 3), np.uint8)
    y = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    sky = (np.array([3, 6, 14]) * (1.0 - y) + np.array([10, 16, 28]) * y).astype(np.uint8)
    img[:] = sky[:, None, :]
    ys = rng.integers(0, H, 280)
    xs = rng.integers(0, W, 280)
    mag = rng.integers(140, 255, 280)
    img[ys, xs] = mag[:, None]
    return img


def lonlat_to_unit_xyz(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lam = np.radians(lon_deg)
    phi = np.radians(lat_deg)
    cos_phi = np.cos(phi)
    return np.column_stack([cos_phi * np.cos(lam), cos_phi * np.sin(lam), np.sin(phi)]).astype(np.float64)


def camera_rotation_matrix(cam_lon: float, cam_lat: float) -> Tuple[np.ndarray, np.ndarray]:
    lam0 = math.radians(cam_lon)
    phi0 = math.radians(cam_lat)
    cl, sl = math.cos(lam0), math.sin(lam0)
    cp, sp = math.cos(phi0), math.sin(phi0)
    rotation = np.array(
        [[-sl, cl, 0.0], [-sp * cl, -sp * sl, cp], [cp * cl, cp * sl, sp]],
        dtype=np.float64,
    )
    return rotation, rotation[2]


def camera_scale_and_disc_radius(span: float, w: float) -> Tuple[float, float, float]:
    mix = float(smootherstep(w))
    flat_scale = W / max(math.radians(span), 1e-4)
    globe_r = float(np.clip((W * 0.43) * (64.0 / max(span, 36.0)), 440.0, 1450.0))
    scale = (1.0 - mix) * flat_scale + mix * globe_r
    max_rho = (1.0 - mix) * (math.pi * 0.495) + mix * 1.0
    return mix, scale, scale * max_rho


def project_xyz(pts_xyz: np.ndarray, rotation: np.ndarray, mix: float, scale: float, clamp_to_horizon: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    cam_pts = pts_xyz @ rotation.T
    xc, yc = cam_pts[:, 0], cam_pts[:, 1]
    zc = np.clip(cam_pts[:, 2], -1.0, 1.0)
    c = np.arccos(zc)
    sin_c = np.maximum(np.hypot(xc, yc), 1e-9)
    max_c = (1.0 - mix) * 1.52 + mix * 1.54
    visible = c <= max_c
    c_eff = np.minimum(c, max_c) if clamp_to_horizon else c
    rho = (1.0 - mix) * c_eff + mix * np.sin(c_eff)
    factor = (scale * rho) / sin_c
    return W * 0.5 + xc * factor, H * 0.5 - yc * factor, visible


def project(lon: np.ndarray, lat: np.ndarray, cam_lon: float, cam_lat: float, span: float, w: float, clamp_to_horizon: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mix, scale, _ = camera_scale_and_disc_radius(span, w)
    rotation, _ = camera_rotation_matrix(cam_lon, cam_lat)
    return project_xyz(lonlat_to_unit_xyz(lon, lat), rotation, mix, scale, clamp_to_horizon=clamp_to_horizon)


def spherical_camera_warp(cam_lon: float, cam_lat: float, span: float, w: float, focus_dim: float = 0.0) -> np.ndarray:
    assert PLATE is not None and STARS is not None
    mix, scale, disc_r = camera_scale_and_disc_radius(span, w)
    p_h, p_w = PLATE.shape[:2]
    dx = GX - W * 0.5
    dy = -(GY - H * 0.5)
    r_px = np.hypot(dx, dy)
    rho = r_px / scale
    max_rho = (1.0 - mix) * (math.pi * 0.495) + mix * 1.0
    rho_clamped = np.minimum(rho, max_rho * 0.9995)
    c = np.where(mix > 0.5, np.arcsin(np.minimum(rho_clamped, 1.0)), rho_clamped)
    for _ in range(2):
        f_val = (1.0 - mix) * c + mix * np.sin(c) - rho_clamped
        f_der = np.maximum((1.0 - mix) + mix * np.cos(c), 1e-5)
        c = np.clip(c - f_val / f_der, 0.0, math.pi * 0.498)
    sin_c, cos_c = np.sin(c), np.cos(c)
    r_safe = np.maximum(r_px, 1e-7)
    xc = (dx / r_safe) * sin_c
    yc = (dy / r_safe) * sin_c
    zc = cos_c
    phi0, lam0 = math.radians(cam_lat), math.radians(cam_lon)
    cos_phi0, sin_phi0 = math.cos(phi0), math.sin(phi0)
    cos_lam0, sin_lam0 = math.cos(lam0), math.sin(lam0)
    x1 = xc
    y1 = -sin_phi0 * yc + cos_phi0 * zc
    vz = np.clip(cos_phi0 * yc + sin_phi0 * zc, -1.0, 1.0)
    vx = cos_lam0 * y1 - sin_lam0 * x1
    vy = sin_lam0 * y1 + cos_lam0 * x1
    vx_full = cv2.resize(vx.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vy_full = cv2.resize(vy.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vz_full = np.clip(cv2.resize(vz.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR), -1.0, 1.0)
    lon_rad = np.arctan2(vy_full, vx_full)
    lat_rad = np.arcsin(vz_full)
    map_x = ((lon_rad + math.pi) * (1.0 / (2.0 * math.pi)) * (p_w - 1)).astype(np.float32)
    map_y = ((math.pi * 0.5 - lat_rad) * (1.0 / math.pi) * (p_h - 1)).astype(np.float32)
    sampled = cv2.remap(PLATE, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
    if focus_dim > 0.01:
        sampled = cv2.convertScaleAbs(sampled, alpha=1.0 - 0.24 * focus_dim, beta=0.0)
    if disc_r >= SCREEN_DIAG_RADIUS + 18.0:
        return sampled
    norm_r = FULL_R_PX / max(disc_r, 1.0)
    inside = norm_r <= 1.0
    limb_dark = np.clip(1.0 - 0.34 * np.clip((norm_r - 0.72) / 0.28, 0.0, 1.0) ** 1.5, 0.62, 1.0)
    fresnel = np.clip((norm_r - 0.84) / 0.16, 0.0, 1.0) ** 2.2 * 0.38
    atmo_rgb = np.array([95.0, 175.0, 255.0], dtype=np.float32)
    earth_shaded = sampled.astype(np.float32) * limb_dark[:, :, None]
    earth_shaded = np.clip(earth_shaded * (1.0 - fresnel[:, :, None]) + atmo_rgb * fresnel[:, :, None], 0, 255).astype(np.uint8)
    frame = STARS.copy()
    frame[inside] = earth_shaded[inside]
    halo_mask = (norm_r > 0.992) & (norm_r < 1.045)
    if np.any(halo_mask):
        halo_u = np.clip((1.045 - norm_r[halo_mask]) / (1.045 - 0.992), 0.0, 1.0)
        halo_alpha = (halo_u ** 2.4) * 0.72
        frame[halo_mask] = np.clip(frame[halo_mask].astype(np.float32) * (1.0 - halo_alpha[:, None]) + atmo_rgb * halo_alpha[:, None], 0, 255).astype(np.uint8)
    return frame


PILL_RGB = {
    "red": ((212, 38, 42), (255, 255, 255)),
    "dark": ((16, 22, 34), (255, 255, 255)),
    "blue": ((14, 116, 218), (255, 255, 255)),
    "yellow": ((245, 197, 24), (14, 18, 26)),
    "white": ((248, 250, 252), (14, 18, 26)),
}


def chaikin_smooth_lonlat(lon: np.ndarray, lat: np.ndarray, passes: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    pts_lon, pts_lat = lon.copy(), lat.copy()
    for _ in range(passes):
        dlon = ((np.roll(pts_lon, -1) - pts_lon + 180.0) % 360.0) - 180.0
        dlat = np.roll(pts_lat, -1) - pts_lat
        new_lon = np.empty(len(pts_lon) * 2, dtype=np.float64)
        new_lat = np.empty(len(pts_lat) * 2, dtype=np.float64)
        new_lon[0::2] = pts_lon + 0.25 * dlon
        new_lon[1::2] = pts_lon + 0.75 * dlon
        new_lat[0::2] = pts_lat + 0.25 * dlat
        new_lat[1::2] = pts_lat + 0.75 * dlat
        pts_lon, pts_lat = new_lon, new_lat
    return pts_lon, pts_lat


def subdivide_ring_geodesic(lon: np.ndarray, lat: np.ndarray, max_deg: float = 0.20) -> Tuple[np.ndarray, np.ndarray]:
    dlon = np.diff(lon, append=lon[0])
    dlon_wrapped = ((dlon + 180.0) % 360.0) - 180.0
    dlat = np.diff(lat, append=lat[0])
    seg_len = np.hypot(dlon_wrapped, dlat)
    if len(lon) >= 12 and float(np.median(seg_len)) < 0.25:
        lon, lat = chaikin_smooth_lonlat(lon, lat, passes=1)
        dlon = np.diff(lon, append=lon[0])
        dlon_wrapped = ((dlon + 180.0) % 360.0) - 180.0
        dlat = np.diff(lat, append=lat[0])
        seg_len = np.hypot(dlon_wrapped, dlat)
    if float(np.max(seg_len)) <= max_deg:
        return lon, lat
    out_lon: List[float] = []
    out_lat: List[float] = []
    for i in range(len(lon)):
        steps = max(1, min(64, int(math.ceil(float(seg_len[i]) / max_deg))))
        for s in range(steps):
            u = s / steps
            out_lon.append(float(lon[i]) + u * float(dlon_wrapped[i]))
            out_lat.append(float(lat[i]) + u * float(dlat[i]))
    return np.asarray(out_lon, dtype=np.float64), np.asarray(out_lat, dtype=np.float64)


def _store_alaska_shape(xyz: np.ndarray) -> None:
    global ALASKA_SHAPE
    step = max(1, len(xyz) // 140)
    sample = xyz[::step]
    lon = np.degrees(np.arctan2(sample[:, 1], sample[:, 0]))
    lat = np.degrees(np.arcsin(np.clip(sample[:, 2], -1.0, 1.0)))
    lat0 = float(np.mean(lat))
    lon0 = float(np.mean(lon))
    x = np.radians(lon - lon0) * math.cos(math.radians(lat0))
    y = -np.radians(lat - lat0)
    span = max(float(np.ptp(x)), float(np.ptp(y)), 1e-6)
    ALASKA_SHAPE = np.column_stack([(x - np.mean(x)) / span, (y - np.mean(y)) / span])


def load_rings(geojson_path: Path) -> list[dict]:
    global RINGS_BY_ISO
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    rings = []
    best_alaska: dict | None = None
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
            clon, clat = float(np.mean(lon_raw)), float(np.mean(lat_raw))
            if iso in HIGHLIGHT_ISOS:
                lon_sub, lat_sub = subdivide_ring_geodesic(lon_raw, lat_raw, max_deg=0.18)
            else:
                lon_sub, lat_sub = lon_raw, lat_raw
            xyz = lonlat_to_unit_xyz(lon_sub, lat_sub)
            mean_vec = np.mean(xyz, axis=0)
            center_xyz = mean_vec / max(float(np.linalg.norm(mean_vec)), 1e-9)
            min_dot = float(np.min(xyz @ center_xyz))
            ring = {
                "iso": iso,
                "xyz": xyz,
                "center_xyz": center_xyz,
                "ang_radius": math.acos(max(-1.0, min(1.0, min_dot))),
                "clon": clon,
                "clat": clat,
                "n": int(lon_sub.shape[0]),
            }
            rings.append(ring)
            if iso == "USA" and clat > 51.0 and clon < -129.9 and (best_alaska is None or ring["n"] > best_alaska["n"]):
                best_alaska = ring
    RINGS_BY_ISO = {}
    for ring in rings:
        RINGS_BY_ISO.setdefault(ring["iso"], []).append(ring)
    if best_alaska is not None:
        _store_alaska_shape(best_alaska["xyz"])
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


def split_visible_polylines_subpixel(x: np.ndarray, y: np.ndarray, visible: np.ndarray, max_step: float) -> list[np.ndarray]:
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


def _roi_from_subpixel(subpixel_polys: list[np.ndarray], pad: int) -> Tuple[int, int, int, int] | None:
    all_pts = np.concatenate(subpixel_polys, axis=0)
    x0 = max(0, int(np.floor(np.min(all_pts[:, 0]) / SUBPIXEL_MULT)) - pad)
    y0 = max(0, int(np.floor(np.min(all_pts[:, 1]) / SUBPIXEL_MULT)) - pad)
    x1 = min(W, int(np.ceil(np.max(all_pts[:, 0]) / SUBPIXEL_MULT)) + pad)
    y1 = min(H, int(np.ceil(np.max(all_pts[:, 1]) / SUBPIXEL_MULT)) + pad)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def blend_polygon_roi_subpixel(frame: np.ndarray, subpixel_polys: list[np.ndarray], rgb_color: Tuple[int, int, int], weight: float, clip_disc: bool, disc_r: float) -> None:
    if not subpixel_polys or weight <= 0.005:
        return
    box = _roi_from_subpixel(subpixel_polys, 4)
    if box is None:
        return
    x0, y0, x1, y1 = box
    offset = np.array([[int(round(x0 * SUBPIXEL_MULT)), int(round(y0 * SUBPIXEL_MULT))]], dtype=np.int32)
    local_polys = [poly - offset for poly in subpixel_polys]
    roi = frame[y0:y1, x0:x1]
    overlay = roi.copy()
    cv2.fillPoly(overlay, local_polys, rgb_color, lineType=cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    if clip_disc:
        outside = FULL_R_PX[y0:y1, x0:x1] > disc_r * 0.995
        if np.any(outside):
            overlay[outside] = roi[outside]
    cv2.addWeighted(overlay, weight, roi, 1.0 - weight, 0.0, dst=roi)


def blend_polylines_roi_subpixel(
    frame: np.ndarray,
    subpixel_runs: list[np.ndarray],
    color: Tuple[int, int, int],
    thickness: int,
    alpha: float,
    glow: Tuple[int, int, int],
    glow_thickness: int,
) -> None:
    """Stroke the same fade as the fill, and only inside the stroke pixels."""
    if not subpixel_runs or alpha <= 0.005:
        return
    box = _roi_from_subpixel(subpixel_runs, glow_thickness + 6)
    if box is None:
        return
    x0, y0, x1, y1 = box
    offset = np.array([[int(round(x0 * SUBPIXEL_MULT)), int(round(y0 * SUBPIXEL_MULT))]], dtype=np.int32)
    local = [run - offset for run in subpixel_runs]
    roi = frame[y0:y1, x0:x1]
    overlay = np.zeros_like(roi)
    cv2.polylines(overlay, local, False, glow, glow_thickness, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    cv2.polylines(overlay, local, False, color, thickness, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    mask = np.any(overlay > 0, axis=2)
    if not np.any(mask):
        return
    base = roi.astype(np.float32)
    src = overlay.astype(np.float32)
    base[mask] = base[mask] * (1.0 - alpha) + src[mask] * alpha
    roi[:] = np.clip(base, 0, 255).astype(np.uint8)


def apply_vector_coast_refinement(frame: np.ndarray, visible_land_polys_subpixel: list[np.ndarray], span: float, w: float) -> None:
    if span >= 30.0 or w > 0.35 or not visible_land_polys_subpixel:
        return
    strength = float(smoothstep((30.0 - span) / 18.0)) * (1.0 - w)
    if strength <= 0.02:
        return
    land_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(land_mask, visible_land_polys_subpixel, 255, lineType=cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    shelf_blur = cv2.GaussianBlur(land_mask, (0, 0), 9.0)
    land_f = land_mask.astype(np.float32) / 255.0
    water_weight = (1.0 - land_f) * strength
    shelf_weight = (shelf_blur.astype(np.float32) / 255.0) * (1.0 - land_f) * strength
    deep_ocean = np.array([10.0, 34.0, 74.0], dtype=np.float32)
    shallow_shelf = np.array([24.0, 82.0, 142.0], dtype=np.float32)
    f32 = frame.astype(np.float32)
    ocean_target = f32 * 0.45 + deep_ocean * 0.55 + shallow_shelf * (shelf_weight[:, :, None] * 0.65)
    w_mask = (water_weight * 0.62)[:, :, None]
    frame[:] = np.clip(f32 * (1.0 - w_mask) + ocean_target * w_mask, 0, 255).astype(np.uint8)


def draw_vector_highlights_and_borders(frame: np.ndarray, rings: list[dict], spec: EpisodeSpec, lon0: float, lat0: float, span: float, w: float, t: float) -> None:
    mix, scale, disc_r = camera_scale_and_disc_radius(span, w)
    rotation, cam_fwd = camera_rotation_matrix(lon0, lat0)
    clip_disc = disc_r < SCREEN_DIAG_RADIUS + 10.0
    max_view_ang = math.radians(min(92.0, max(span * 1.15, 18.0))) if mix < 0.35 else 1.58
    active_cues = []
    for cue in spec.highlights:
        alpha = element_fade_and_exit_offset(t, cue.enter_t, cue.exit_t, 0.28, 0.30)[0]
        if alpha > 0.02:
            active_cues.append((cue, alpha))
    active_cues.sort(key=lambda item: item[0].z_order)
    active_isos = {cue.iso_a3 for cue, _ in active_cues}
    coasts_subpixel = []
    land_polys_subpixel = []
    need_coast_refinement = (span < 30.0) and (w <= 0.35)
    base_thick = 2 if span < 22.0 else 1
    for ring in rings:
        if span > 55.0 and ring["n"] < 32:
            continue
        if ring["iso"] not in active_isos:
            dot = float(ring["center_xyz"] @ cam_fwd)
            if dot < math.cos(min(math.pi, max_view_ang + ring["ang_radius"])):
                continue
        x, y, visible = project_xyz(ring["xyz"], rotation, mix, scale, clamp_to_horizon=False)
        if clip_disc:
            visible = visible & ((np.hypot(x - W * 0.5, y - H * 0.5)) <= disc_r * 0.994)
        if not np.any(visible):
            continue
        if not np.any((x > -120) & (x < W + 120) & (y > -120) & (y < H + 120)):
            continue
        runs = split_visible_polylines_subpixel(x, y, visible, 160.0)
        if runs:
            coasts_subpixel.extend(runs)
        if need_coast_refinement and bool(np.all(visible)):
            land_polys_subpixel.append(np.round(np.column_stack([x, y]) * SUBPIXEL_MULT).astype(np.int32))
    if need_coast_refinement and land_polys_subpixel:
        apply_vector_coast_refinement(frame, land_polys_subpixel, span, w)
    if coasts_subpixel:
        cv2.polylines(frame, coasts_subpixel, False, (175, 190, 208), base_thick, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
    for cue, alpha in active_cues:
        candidates = RINGS_BY_ISO.get(cue.iso_a3, rings)
        fill_polys_sub = []
        border_runs_sub = []
        for ring in candidates:
            if ring["iso"] != cue.iso_a3 or not where_ok(cue.where, ring["clon"], ring["clat"]):
                continue
            if span > 45.0 and ring["n"] < 20:
                continue
            x_f, y_f, vis_f = project_xyz(ring["xyz"], rotation, mix, scale, clamp_to_horizon=True)
            if not np.any(vis_f):
                continue
            if not np.any((x_f > -250) & (x_f < W + 250) & (y_f > -250) & (y_f < H + 250)):
                continue
            jumps = np.hypot(np.diff(x_f), np.diff(y_f))
            if len(jumps) > 0 and float(np.max(jumps)) < 450.0:
                fill_polys_sub.append(np.round(np.column_stack([x_f, y_f]) * SUBPIXEL_MULT).astype(np.int32))
            x_b, y_b, vis_b = project_xyz(ring["xyz"], rotation, mix, scale, clamp_to_horizon=False)
            if clip_disc:
                vis_b = vis_b & ((np.hypot(x_b - W * 0.5, y_b - H * 0.5)) <= disc_r * 0.994)
            runs = split_visible_polylines_subpixel(x_b, y_b, vis_b, 200.0)
            if runs:
                border_runs_sub.extend(runs)
        if fill_polys_sub:
            weight = float(alpha) * (cue.fill_rgba[3] / 255.0) * 0.78
            blend_polygon_roi_subpixel(frame, fill_polys_sub, cue.fill_rgba[:3], weight, clip_disc, disc_r)
        if border_runs_sub:
            stroke_thick = 4 if span < 12.0 else (3 if span < 32.0 else 2)
            glow = tuple(max(0, int(c * 0.22)) for c in cue.stroke_rgba[:3])
            blend_polylines_roi_subpixel(frame, border_runs_sub, cue.stroke_rgba[:3], stroke_thick, float(alpha), glow, stroke_thick + 5)


def draw_split_arcs(frame: np.ndarray, spec: EpisodeSpec, lon0: float, lat0: float, span: float, w: float, t: float) -> None:
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
        x_min = max(0, int(np.floor(np.min(x))) - 28)
        y_min = max(0, int(np.floor(np.min(y))) - 28)
        x_max = min(W, int(np.ceil(np.max(x))) + 28)
        y_max = min(H, int(np.ceil(np.max(y))) + 28)
        if x_max <= x_min or y_max <= y_min:
            continue
        roi = frame[y_min:y_max, x_min:x_max]
        overlay = roi.copy()
        pts_sub = np.round(np.column_stack([x - x_min, y - y_min]) * SUBPIXEL_MULT).astype(np.int32)
        for i in range(0, len(pts_sub) - 1, 2):
            p0 = tuple(pts_sub[i])
            p1 = tuple(pts_sub[min(i + 1, len(pts_sub) - 1)])
            cv2.line(overlay, p0, p1, (14, 18, 26), 7, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
            cv2.line(overlay, p0, p1, arc.color_rgb, 4, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
        pulse_r = int(round((10.0 + 4.0 * math.sin(t * 6.0)) * SUBPIXEL_MULT))
        dot_r = int(round(5.0 * SUBPIXEL_MULT))
        for ep_lon, ep_lat in ((arc.lon0, arc.lat0), (arc.lon1, arc.lat1)):
            ex, ey, ev = project(np.array([ep_lon]), np.array([ep_lat]), lon0, lat0, span, w)
            if bool(ev[0]):
                center = (int(round((float(ex[0]) - x_min) * SUBPIXEL_MULT)), int(round((float(ey[0]) - y_min) * SUBPIXEL_MULT)))
                cv2.circle(overlay, center, pulse_r, arc.color_rgb, 3, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
                cv2.circle(overlay, center, dot_r, (255, 255, 255), -1, cv2.LINE_AA, shift=SUBPIXEL_SHIFT)
        cv2.addWeighted(overlay, float(alpha), roi, 1.0 - float(alpha), 0.0, dst=roi)


def resolve_2d_label_collisions(boxes: List[Tuple[float, float, float, float]], min_gap_px: float = 22.0, iterations: int = 16) -> List[Tuple[float, float]]:
    centers = [[float(b[0]), float(b[1])] for b in boxes]
    sizes = [(float(b[2]), float(b[3])) for b in boxes]
    n = len(boxes)
    for _ in range(iterations):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = centers[j][0] - centers[i][0]
                dy = centers[j][1] - centers[i][1]
                overlap_x = (sizes[i][0] + sizes[j][0]) * 0.5 + min_gap_px - abs(dx)
                overlap_y = (sizes[i][1] + sizes[j][1]) * 0.5 + min_gap_px - abs(dy)
                if overlap_x > 0.0 and overlap_y > 0.0:
                    moved = True
                    if overlap_y <= overlap_x * 1.4:
                        sign_y = 1.0 if dy >= 0.0 else -1.0
                        shift = 0.52 * overlap_y * sign_y
                        centers[i][1] -= shift
                        centers[j][1] += shift
                    else:
                        sign_x = 1.0 if dx >= 0.0 else -1.0
                        shift = 0.52 * overlap_x * sign_x
                        centers[i][0] -= shift
                        centers[j][0] += shift
        if not moved:
            break
    return [(max(130.0, min(SAFE_RIGHT - 40.0, c[0])), max(260.0, min(1180.0, c[1]))) for c in centers]


def text_size(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0], box[3] - box[1]


def mercator_area_factor(lat_deg: float) -> float:
    cos_lat = max(math.cos(math.radians(float(np.clip(lat_deg, -78.0, 78.0)))), 0.08)
    return 1.0 / (cos_lat * cos_lat)


def draw_truesize_compare(draw: ImageDraw.ImageDraw, lat0: float, span: float, w: float, t: float) -> bool:
    if ALASKA_SHAPE is None or not (1.35 <= t <= 5.35 and span < 34.0 and lat0 > 55.0 and w < 0.25):
        return False
    alpha = element_fade_and_exit_offset(t, 1.35, 5.35, 0.28, 0.28)[0]
    if alpha <= 0.04:
        return False
    factor = mercator_area_factor(lat0)
    linear = min(math.sqrt(factor), 2.35)
    true_px = 118.0
    merc_px = true_px * linear
    card_y = 1045.0
    true_x, merc_x = 210.0, 210.0 + true_px * 0.55 + 36.0 + merc_px * 0.55
    right = merc_x + merc_px * 0.55 + 28.0
    if right > SAFE_RIGHT:
        shift = right - SAFE_RIGHT
        true_x -= shift
        merc_x -= shift
    top = card_y - merc_px * 0.55 - 28.0
    bottom = card_y + merc_px * 0.55 + 46.0
    a = int(235 * alpha)
    draw.rounded_rectangle([true_x - true_px * 0.62, top, merc_x + merc_px * 0.62, bottom], radius=16, fill=(8, 12, 20, int(190 * alpha)))
    true_pts = [(true_x + float(p[0]) * true_px, card_y + float(p[1]) * true_px) for p in ALASKA_SHAPE]
    merc_pts = [(merc_x + float(p[0]) * merc_px, card_y + float(p[1]) * merc_px) for p in ALASKA_SHAPE]
    draw.polygon(true_pts, fill=(245, 197, 24, int(230 * alpha)))
    draw.line(merc_pts + [merc_pts[0]], fill=(0, 229, 255, a), width=3)
    face = get_font(26)
    draw.text((true_x - 28, card_y + true_px * 0.55 + 6), "TRUE", font=face, fill=(255, 255, 255, a))
    label = f"MERCATOR {factor:.1f}×"
    tw, _th = text_size(draw, label, face)
    draw.text((merc_x - tw / 2, card_y + merc_px * 0.55 + 6), label, font=face, fill=(0, 229, 255, a))
    return True


def composite_rgba_roi(rgb_frame: np.ndarray, rgba_overlay: np.ndarray, y0: int, y1: int) -> None:
    y0_c, y1_c = max(0, min(H, y0)), max(0, min(H, y1))
    if y1_c <= y0_c:
        return
    sub_rgba = rgba_overlay[y0_c:y1_c]
    alpha = sub_rgba[:, :, 3:4].astype(np.float32) * (1.0 / 255.0)
    if not np.any(alpha > 0.002):
        return
    dst = rgb_frame[y0_c:y1_c].astype(np.float32)
    src = sub_rgba[:, :, :3].astype(np.float32)
    rgb_frame[y0_c:y1_c] = np.clip(dst * (1.0 - alpha) + src * alpha, 0, 255).astype(np.uint8)


def draw_overlay(rgb: np.ndarray, spec: EpisodeSpec, phrases: List[List[Dict]], lon0: float, lat0: float, span: float, w: float, t: float) -> np.ndarray:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    min_y, max_y = H, 0
    visible_labels = []
    for label in spec.labels:
        alpha, _dx, _dy = element_fade_and_exit_offset(t, label.enter_t, label.exit_t, 0.26, 0.28)
        if alpha <= 0.04:
            continue
        x, y, vis = project(np.array([label.lon]), np.array([label.lat]), lon0, lat0, span, w)
        if not bool(vis[0]):
            continue
        px, py = float(x[0]), float(y[0])
        if not (60 < px < W - 60 and 200 < py < H - 360):
            continue
        pop, _ = label_pop_state(t - label.enter_t, 0.28)
        face = get_font(label.font_size * max(pop, 0.5))
        tw, th = text_size(draw, label.text, face)
        visible_labels.append((label, alpha, px, py, tw + 16, th + 14, face))
    if visible_labels:
        boxes = [(px, py, tw, th) for _l, _a, px, py, tw, th, _f in visible_labels]
        centers = resolve_2d_label_collisions(boxes, min_gap_px=24.0)
        for (label, alpha, _px, _py, _tw, _th, face), (cx, cy) in zip(visible_labels, centers):
            ink = label.color_rgba[:3] + (int(255 * alpha),)
            stroke = (8, 12, 20, int(250 * alpha))
            tw, th = text_size(draw, label.text, face)
            ox, oy = cx - tw / 2.0, cy - th / 2.0
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                draw.text((ox + dx, oy + dy), label.text, font=face, fill=stroke)
            draw.text((ox, oy), label.text, font=face, fill=ink)
            min_y, max_y = min(min_y, int(oy) - 12), max(max_y, int(oy + th) + 12)
    if draw_truesize_compare(draw, lat0, span, w, t):
        min_y, max_y = min(min_y, 860), max(max_y, 1220)
    for pill in spec.pills:
        alpha, dx, dy = element_fade_and_exit_offset(t, pill.enter_t, pill.exit_t, 0.25, 0.28)
        if alpha <= 0.04:
            continue
        pop, _ = label_pop_state(t - pill.enter_t, 0.28)
        font_sz = 38.0 * max(pop, 0.85)
        face = get_font(font_sz)
        bg, fg = PILL_RGB.get(pill.theme, PILL_RGB["dark"])
        display_text = pill.text
        if pill.counter_start is not None and pill.counter_end is not None and pill.counter_fmt:
            roll_u = float(smootherstep(min(1.0, max(0.0, (t - pill.enter_t) / 0.65))))
            val = pill.counter_start + roll_u * (pill.counter_end - pill.counter_start)
            display_text = pill.counter_fmt.format(val=val)
        tw_fixed, th = text_size(draw, pill.text, face)
        tw_cur, _ = text_size(draw, display_text, face)
        tw = max(tw_fixed, tw_cur)
        pad_x, pad_y = 28, 16
        box_w = tw + pad_x * 2
        max_box = SAFE_RIGHT - 80.0
        if box_w > max_box:
            font_sz *= max_box / box_w
            face = get_font(font_sz)
            tw_fixed, th = text_size(draw, pill.text, face)
            tw_cur, _ = text_size(draw, display_text, face)
            tw = max(tw_fixed, tw_cur)
            box_w = tw + pad_x * 2
        box_h = th + pad_y * 2
        cx = max(80 + box_w / 2, min(SAFE_RIGHT - box_w / 2, pill.screen_x + dx))
        cy = max(210 + box_h / 2, min(1180 - box_h / 2, pill.screen_y + dy))
        rect = [cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2]
        shadow_rect = [rect[0] + 4, rect[1] + 6, rect[2] + 4, rect[3] + 6]
        a_solid = int(254 * (alpha ** 0.55))
        draw.rounded_rectangle(shadow_rect, radius=18, fill=(6, 10, 18, int(200 * alpha)))
        draw.rounded_rectangle(rect, radius=18, fill=bg + (a_solid,), outline=(255, 255, 255, int(105 * alpha)), width=2)
        draw.text((cx - tw_cur / 2, cy - th / 2 - 2), display_text, font=face, fill=fg + (a_solid,))
        min_y, max_y = min(min_y, int(rect[1]) - 10), max(max_y, int(shadow_rect[3]) + 10)
    active_phrase = None
    for phrase in phrases:
        if (float(phrase[0]["start"]) - 0.08) <= t <= (float(phrase[-1]["end"]) + 0.12):
            active_phrase = phrase
            break
    if active_phrase:
        t_lead = t + 0.04
        font_sz = 66.0
        face = get_font(font_sz)
        gap = 18
        widths = [text_size(draw, str(word["text"]), face)[0] for word in active_phrase]
        total_w = sum(widths) + gap * (len(active_phrase) - 1)
        if total_w > 880.0:
            font_sz = max(48.0, font_sz * (880.0 / total_w))
            face = get_font(font_sz)
            widths = [text_size(draw, str(word["text"]), face)[0] for word in active_phrase]
            total_w = sum(widths) + gap * (len(active_phrase) - 1)
        x_cur = (W - total_w) * 0.5
        y_cur = 1310.0
        for word, width in zip(active_phrase, widths):
            color = (0, 229, 255, 255) if float(word["start"]) <= t_lead <= float(word["end"]) else (255, 255, 255, 255)
            txt = str(word["text"])
            draw.text((x_cur + 4, y_cur + 5), txt, font=face, fill=(4, 8, 14, 210))
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3)):
                draw.text((x_cur + dx, y_cur + dy), txt, font=face, fill=(10, 14, 22, 252))
            draw.text((x_cur, y_cur), txt, font=face, fill=color)
            x_cur += width + gap
        min_y, max_y = min(min_y, 1285), max(max_y, 1410)
    if max_y > min_y:
        composite_rgba_roi(rgb, np.asarray(overlay, dtype=np.uint8), min_y, max_y)
    return rgb


WEAK_WORDS = {"A", "AN", "THE", "OF", "TO", "IN", "ON", "FOR", "AND", "OR", "WITH", "BY"}


def clean_caption_token(raw: str) -> str:
    return raw.strip().strip(",.;:?!\"'“”").upper()


def phrase_width(words: List[str]) -> int:
    return sum(len(word) for word in words) + max(0, len(words) - 1)


def group_spoken_phrases(spoken: List[dict]) -> List[List[Dict]]:
    phrases: List[List[Dict]] = []
    cur: List[Dict] = []

    def flush() -> None:
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
        if raw.endswith((".", "?", "!")):
            flush()
    flush()
    return phrases


def load_measured_words() -> List[dict]:
    payload = json.loads(BRIAN_WORDS.read_text(encoding="utf-8"))
    spoken = [word for word in payload["words"] if word.get("type", "word") == "word"]
    if not spoken:
        raise RuntimeError("brian_words.json has no spoken words")
    return spoken


def prepare_voiceover_and_karaoke_phrases(spec: EpisodeSpec) -> Tuple[np.ndarray, List[List[Dict]]]:
    sr = 48000
    total_samples = int(round(spec.total_duration * sr))
    wav_path = CACHE_DIR / "brian_cut_in_two.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(BRIAN_MP3), "-ar", str(sr), "-ac", "1", str(wav_path)],
        check=True,
    )
    with wave.open(str(wav_path), "rb") as wf:
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        if wf.getnchannels() == 2:
            pcm = pcm.reshape(-1, 2).mean(axis=1)
    print(f"[AUDIO] Brian narration {len(pcm) / sr:.2f}s from {BRIAN_MP3.name}, played once", flush=True)
    vo_track = np.zeros(total_samples, dtype=np.float64)
    n = min(len(pcm), total_samples)
    vo_track[:n] = pcm[:n]
    phrases = group_spoken_phrases(load_measured_words())
    master = np.column_stack([vo_track, vo_track])
    rng = np.random.default_rng(42)
    n_w = int(round(0.34 * sr))
    tw = np.linspace(0.0, 1.0, n_w, dtype=np.float64)
    env_w = 30.0 * (tw ** 2) * ((1.0 - tw) ** 2)
    noise = rng.normal(0.0, 1.0, n_w)
    smooth_noise = np.convolve(noise, np.ones(32) / 32, mode="same")
    air_whoosh = env_w * (smooth_noise - np.convolve(smooth_noise, np.ones(120) / 120, mode="same")) * 0.12
    for mv in spec.moves:
        peak_t = mv.start_t + 0.5 * mv.duration - 0.17
        idx = int(round(max(0.0, peak_t) * sr))
        end_idx = min(total_samples, idx + n_w)
        if end_idx > idx:
            master[idx:end_idx, 0] += air_whoosh[: end_idx - idx] * 0.45
            master[idx:end_idx, 1] += air_whoosh[: end_idx - idx] * 0.55
    n_p = int(round(0.045 * sr))
    tp = np.linspace(0.0, 0.045, n_p, dtype=np.float64)
    env_p = np.exp(-tp * 85.0) * np.sin(math.pi * tp / 0.045)
    thud_sig = env_p * np.sin(2.0 * math.pi * (150.0 * tp - 1100.0 * (tp ** 2))) * 0.06
    for pt in sorted({pill.enter_t for pill in spec.pills}):
        idx = int(round(max(0.0, pt + 0.02) * sr))
        end_idx = min(total_samples, idx + n_p)
        if end_idx > idx:
            master[idx:end_idx] += thud_sig[: end_idx - idx, None]
    peak = float(np.max(np.abs(master)))
    if peak > 0.89:
        master *= 0.89 / peak
    return master, phrases


def render_frame_at(rings: list[dict], spec: EpisodeSpec, phrases: List[List[Dict]], st: Dict[str, float], t: float) -> np.ndarray:
    focus_dim = float(smoothstep((35.0 - st["span"]) / 20.0)) * (1.0 - st["w"])
    frame = spherical_camera_warp(st["lon"], st["lat"], st["span"], st["w"], focus_dim=focus_dim)
    draw_vector_highlights_and_borders(frame, rings, spec, st["lon"], st["lat"], st["span"], st["w"], t)
    draw_split_arcs(frame, spec, st["lon"], st["lat"], st["span"], st["w"], t)
    return draw_overlay(frame, spec, phrases, st["lon"], st["lat"], st["span"], st["w"], t)


def main() -> None:
    global PLATE, STARS
    geojson_path = ensure_assets()
    PLATE = load_enhanced_plate()
    STARS = make_starfield()
    print(f"[ASSET] Loading {geojson_path.name}", flush=True)
    rings = load_rings(geojson_path)
    print(f"[ASSET] {len(rings)} rings indexed by ISO", flush=True)
    spec = build_cut_in_two_episode()
    rig = spec.build_rig()
    audio_f64, phrases = prepare_voiceover_and_karaoke_phrases(spec)
    print(f"[CAPTION] {sum(len(p) for p in phrases)} words in {len(phrases)} phrases", flush=True)
    for size in range(18, 72, 2):
        get_font(size)
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out_dir = Path("/tmp/cit_v6_stills")
        out_dir.mkdir(parents=True, exist_ok=True)
        test_times = [float(x) for x in sys.argv[2:]] or [2.4, 32.1, 73.2]
        for t in test_times:
            st = rig.evaluate_all(min(t, spec.total_duration))
            img = render_frame_at(rings, spec, phrases, st, t)
            path = out_dir / f"t_{t:05.1f}s.jpg"
            Image.fromarray(img).save(path, quality=92)
            print(f"[STILL] {path}", flush=True)
        return

    if len(sys.argv) < 2 or sys.argv[1] != "--render":
        print(f"[SKIP] {OUT_MP4.name} is already finished. Pass --render to encode again.", flush=True)
        return

    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    audio_i16 = (audio_f64 * 32767.0).astype(np.int16)
    wav_path = Path("/tmp/cit_v6_master.wav")
    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes(audio_i16.tobytes())
    n_frames = int(round(spec.total_duration * FPS))
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-i", str(wav_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "faster", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ]
    workers = max(2, min(8, (os.cpu_count() or 4)))
    print(f"[RENDER] {n_frames} frames, {workers} threads -> {OUT_MP4}", flush=True)

    def _worker(frame_idx: int) -> Tuple[int, bytes]:
        t = frame_idx / FPS
        st = rig.evaluate_all(t)
        return frame_idx, render_frame_at(rings, spec, phrases, st, t).tobytes()

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            batch_size = workers * 3
            for start_f in range(0, n_frames, batch_size):
                end_f = min(n_frames, start_f + batch_size)
                futures = [pool.submit(_worker, f) for f in range(start_f, end_f)]
                for fut in futures:
                    frame_idx, raw_bytes = fut.result()
                    proc.stdin.write(raw_bytes)
                    if frame_idx % (FPS * 5) == 0:
                        print(f"  frame {frame_idx:04d}/{n_frames}", flush=True)
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("FFmpeg failed")
    print(f"[DONE] {OUT_MP4}", flush=True)


if __name__ == "__main__":
    main()
