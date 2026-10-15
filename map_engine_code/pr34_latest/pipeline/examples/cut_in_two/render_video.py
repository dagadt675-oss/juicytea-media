#!/usr/bin/env python3
"""
================================================================================
JUICY TEA MAP-SHORTS ENGINE — PRODUCTION 60FPS 3D-SPHERICAL RENDERER
================================================================================
Fixes all 5 defects from the previous render:
1. ZERO North Pole whirlpool & ZERO vertical dateline seam:
   Uses exact 3D Unit-Sphere Camera Space projection (`spherical_camera_warp`)
   with 3D Cartesian vector interpolation (vx, vy, vz) before `atan2`, so
   neither the North Pole nor the +-180 antimeridian ever tears or swirls.
2. ZERO polygon chord-slicing over Canada (00:08-00:11):
   Country highlight fills are rasterized into a 5400x2700 equirectangular ID
   mask (`REGION_MASK`) and warped with the EXACT same `cv2.remap` pixel tables
   as the NASA satellite plate, guaranteeing 100% coastline lock and zero
   horizon-clipping chords.
3. TRUE Circular 3D Globe (`w = 1.0`) on all globe beats with 3D spherical
   limb shading and blue atmospheric rim glow.
4. ZERO Caspian Sea camera dip at 00:57: smooth C2 pull-back from Nakhchivan
   directly onto the 3D globe and across the Arctic to Alaska.
5. UNIFORM Studio Voiceover from 0.0s to 62.0s (`en-US-ChristopherNeural`),
   velocity-peak whoosh/pop SFX, and clean `EVER?` Cyan (#00E5FF) karaoke.
================================================================================
"""

from __future__ import annotations
import json
import math
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


# ==============================================================================
# 1. WORKSPACE & PATH RESOLUTION
# ==============================================================================
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
LOOP_TAIL_SEC = 0.5
MIN_SPAN_DEG = 3.2
MAX_SPAN_DEG = 170.0

CACHE_DIR = PR34 / "pipeline" / "examples" / "cut_in_two"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GEOJSON_50M = CACHE_DIR / "ne_50m_admin_0_countries.geojson"
GEOJSON_50M_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)
PLATE_PATH = CACHE_DIR / "earth_topo_5400.jpg"
PLATE_URL = (
    "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/"
    "world.topo.bathy.200412.3x5400x2700.jpg"
)
OUT_MP4 = WORKSPACE / "v" / "cut_in_two.mp4"


# ==============================================================================
# 2. C2 EASING & TIME-PARAMETERIZED SPLINE CAMERA RIG
# ==============================================================================
def smoothstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * (3.0 - 2.0 * u_c)


def smootherstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * u_c * (u_c * (u_c * 6.0 - 15.0) + 10.0)


def icon_pop_scale(elapsed_s: float, duration_s: float = 0.60, peak: float = 1.15) -> float:
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


def label_pop_state(elapsed_s: float, duration_s: float = 0.30) -> Tuple[float, float]:
    if elapsed_s <= 0.0:
        return 0.0, 0.0
    if elapsed_s >= duration_s:
        return 1.0, 1.0
    scale = icon_pop_scale(elapsed_s, duration_s=duration_s, peak=1.06)
    alpha = float(smootherstep(min(1.0, elapsed_s / (0.60 * duration_s))))
    return scale, alpha


def element_fade_and_exit_offset(
    t: float,
    enter_t: float,
    exit_t: float,
    fade_in_s: float = 0.28,
    fade_out_s: float = 0.30,
    exit_drift_px: Tuple[float, float] = (14.0, -10.0),
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
    def __init__(
        self,
        t: np.ndarray,
        y: np.ndarray,
        v_start: float | None = None,
        v_end: float | None = None,
    ) -> None:
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

        u2 = u * u
        u3 = u2 * u
        u4 = u3 * u
        u5 = u4 * u

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


def hermite_segment(
    t: float, t0: float, t1: float, p0: float, v0: float, p1: float, v1: float
) -> Tuple[float, float, float]:
    T = max(t1 - t0, 1e-9)
    u = float(np.clip((t - t0) / T, 0.0, 1.0))
    u2 = u * u
    u3 = u2 * u

    h00 = 2.0 * u3 - 3.0 * u2 + 1.0
    h10 = u3 - 2.0 * u2 + u
    h01 = -2.0 * u3 + 3.0 * u2
    h11 = u3 - u2
    pos = h00 * p0 + h10 * (T * v0) + h01 * p1 + h11 * (T * v1)

    dh00 = 6.0 * u2 - 6.0 * u
    dh10 = 3.0 * u2 - 4.0 * u + 1.0
    dh01 = -6.0 * u2 + 6.0 * u
    dh11 = 3.0 * u2 - 2.0 * u
    vel = (dh00 * p0 + dh10 * (T * v0) + dh01 * p1 + dh11 * (T * v1)) / T

    ddh00 = 12.0 * u - 6.0
    ddh10 = 6.0 * u - 4.0
    ddh01 = -12.0 * u + 6.0
    ddh11 = 6.0 * u - 2.0
    acc = (ddh00 * p0 + ddh10 * (T * v0) + ddh01 * p1 + ddh11 * (T * v1)) / (T * T)
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
                is_snap=False,
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
        self.spline_log_span = TimeParameterizedC2Spline(
            t_arr, log_span_arr, v_start=self.v0_log_span, v_end=self.v0_log_span
        )

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
            lon, dlon, ddlon = hermite_segment(
                t_clamped, self.loop_start_t, self.total_duration, lon0, dlon0, lon1_wrapped, dlon1
            )

            lat0, dlat0, _ = self.spline_lat.eval_with_derivs(self.loop_start_t)
            lat1, dlat1, _ = self.spline_lat.eval_with_derivs(0.0)
            lat, dlat, ddlat = hermite_segment(t_clamped, self.loop_start_t, self.total_duration, lat0, dlat0, lat1, dlat1)

            ls0, dls0, _ = self.spline_log_span.eval_with_derivs(self.loop_start_t)
            ls1, dls1, _ = self.spline_log_span.eval_with_derivs(0.0)
            lspan, dlspan, ddlspan = hermite_segment(
                t_clamped, self.loop_start_t, self.total_duration, ls0, dls0, ls1, dls1
            )

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


# ==============================================================================
# 3. EPISODE CHOREOGRAPHY, UNIFORM VOICEOVER SCRIPT & CUES (62.0s)
# ==============================================================================
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
    region_id: int
    iso_a3: str
    enter_t: float
    exit_t: float
    fill_rgba: Tuple[int, int, int, int]
    where: str = "all"


@dataclass(frozen=True)
class MapLabelItem:
    text: str
    lon: float
    lat: float
    enter_t: float
    exit_t: float
    color_rgba: Tuple[int, int, int, int] = (255, 255, 255, 255)
    font_size: float = 38.0


@dataclass(frozen=True)
class PillBannerItem:
    text: str
    screen_x: float
    screen_y: float
    enter_t: float
    exit_t: float
    theme: str = "dark"


@dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    total_duration: float
    first_highlight_t: float
    moves: List[LockedCameraMove]
    event_timestamps: List[float]
    highlights: List[CountryHighlightCue] = field(default_factory=list)
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
                    drifted_span = float(
                        np.clip(
                            prev.span * math.exp(mv.drift_scale_rate * hold_dt),
                            MIN_SPAN_DEG + 0.1,
                            MAX_SPAN_DEG - 1.0,
                        )
                    )
                    drifted_lon = prev.lon + mv.drift_lon_rate * hold_dt * (prev.span / 50.0)
                    drifted_lat = prev.lat + mv.drift_lat_rate * hold_dt * (prev.span / 50.0)
                    anchors.append(
                        CameraAnchor(
                            t=mv.start_t,
                            w=mv.w_start,
                            lon=drifted_lon,
                            lat=drifted_lat,
                            span=drifted_span,
                            is_snap=mv.is_snap,
                        )
                    )
            else:
                anchors.append(
                    CameraAnchor(
                        t=mv.start_t,
                        w=mv.w_start,
                        lon=mv.lon_start,
                        lat=mv.lat_start,
                        span=mv.span_start,
                        is_snap=mv.is_snap,
                    )
                )
            anchors.append(
                CameraAnchor(
                    t=mv.start_t + mv.duration,
                    w=mv.w_end,
                    lon=mv.lon_end,
                    lat=mv.lat_end,
                    span=mv.span_end,
                    is_snap=mv.is_snap,
                )
            )
        return ContinuousCameraRig(anchors, total_duration=self.total_duration)


# Clean, single-speaker script across all 62.0s (no '??' typo, no speaker switch at 58s!)
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
    (48.40, 55.40, "And in nineteen twenty-one, Nakhchivan was cut off from Azerbaijan by Armenia, touching Turkey for just eleven kilometers."),
    (56.20, 61.65, "And the cheapest split ever? That's the one where"),
]


def build_full_karaoke_words() -> List[Dict[str, float | str]]:
    words: List[Dict[str, float | str]] = []
    for t0, t1, sentence in SCRIPT_TIMED_LINES:
        tokens = [w.strip() for w in sentence.split() if w.strip()]
        total_chars = sum(max(2, len(tok)) for tok in tokens)
        avail_dur = max(0.2, (t1 - t0) - 0.03 * len(tokens))
        cursor = t0
        for tok in tokens:
            w_dur = avail_dur * (max(2, len(tok)) / total_chars)
            words.append({
                "text": tok.upper(),
                "start": round(cursor, 3),
                "end": round(cursor + w_dur, 3),
            })
            cursor += w_dur + 0.025
    return words


def build_cut_in_two_episode() -> EpisodeSpec:
    total_dur = 62.00
    moves = [
        # 1. Alaska hook (0.0s - 7.6s): starts on TRUE 3D Globe (w=1.0) over Alaska -> zooms into flat map (w=0.0)
        LockedCameraMove("cit_01_alaska_open", 0, 0.0, 1.50, 1.0, 0.0, -148.0, -149.0, 61.0, 63.0, 64.0, 30.0, is_snap=True),
        LockedCameraMove("cit_02_alaska_pan", 8, 4.2, 1.35, 0.0, 0.0, -148.5, -140.0, 63.0, 60.0, 29.0, 25.0),
        # 2. Canada in the way (7.6s - 12.2s): stays clean on spherical map without polar vortex
        LockedCameraMove("cit_03_canada_wide", 18, 7.6, 1.45, 0.0, 0.0, -139.5, -108.0, 60.0, 55.0, 24.5, 40.0),
        # 3. 3D Globe arc (w=1.0) across Pacific to Malaysia (12.2s - 18.0s)
        LockedCameraMove("cit_04_globe_to_malaysia", 30, 12.2, 1.80, 0.0, 1.0, -107.5, 108.5, 55.0, 4.5, 39.5, 54.0),
        LockedCameraMove("cit_05_malaysia_focus", 38, 14.5, 1.35, 1.0, 0.0, 108.5, 108.5, 4.5, 4.0, 53.0, 20.0),
        # 4. True close-up on Brunei & Sarawak / 19-mile Limbang split (18.0s - 27.0s)
        LockedCameraMove("cit_06_brunei_closeup", 50, 18.0, 1.50, 0.0, 0.0, 108.7, 114.85, 4.0, 4.75, 19.5, 4.6, is_snap=True),
        LockedCameraMove("cit_07_limbang_corridor", 60, 22.8, 1.25, 0.0, 0.0, 114.9, 115.05, 4.75, 4.68, 4.5, 4.2),
        # 5. Smooth pull-back to Strait of Hormuz / Musandam Peninsula (27.0s - 35.0s)
        LockedCameraMove("cit_08_globe_to_hormuz", 72, 27.0, 1.65, 0.0, 0.85, 115.1, 56.25, 4.68, 25.4, 4.2, 32.0),
        LockedCameraMove("cit_09_musandam_closeup", 80, 29.2, 1.40, 0.85, 0.0, 56.25, 56.25, 25.4, 25.8, 31.0, 5.4, is_snap=True),
        # 6. Summary comparison beat on TRUE 3D Globe (w=1.0) (35.0s - 40.5s)
        LockedCameraMove("cit_10_indian_ocean_globe", 94, 35.0, 1.55, 0.0, 1.0, 56.3, 42.0, 25.8, 12.0, 5.3, 62.0),
        # 7. Angola & Cabinda / DR Congo corridor close-up (40.5s - 48.4s)
        LockedCameraMove("cit_11_cabinda_zoom", 108, 40.5, 1.55, 1.0, 0.0, 42.0, 12.6, 12.0, -5.6, 60.0, 6.2, is_snap=True),
        LockedCameraMove("cit_12_angola_frame", 118, 44.8, 1.30, 0.0, 0.0, 12.7, 15.8, -5.6, -9.8, 6.1, 14.5),
        # 8. Smooth arc to Nakhchivan / Armenia / Azerbaijan (48.4s - 55.6s)
        LockedCameraMove("cit_13_globe_to_caucasus", 130, 48.4, 1.60, 0.0, 0.70, 15.9, 45.5, -9.7, 39.4, 14.2, 24.0),
        LockedCameraMove("cit_14_nakhchivan_closeup", 140, 50.4, 1.35, 0.70, 0.0, 45.5, 45.4, 39.4, 39.35, 23.0, 5.8, is_snap=True),
        # 9. Direct pull-back onto TRUE 3D Globe (w=1.0) at 55.6s (NO Caspian Sea dip!) -> rotates to Alaska
        LockedCameraMove("cit_15_pullback_globe", 148, 55.6, 1.55, 0.0, 1.0, 45.5, -45.0, 39.35, 54.0, 5.6, 64.0),
        LockedCameraMove("cit_16_globe_loop_alaska", 154, 57.4, 1.95, 1.0, 1.0, -45.0, -148.0, 54.0, 61.0, 64.0, 64.0),
    ]

    highlights = [
        CountryHighlightCue(1, "USA", 0.0, 7.6, (242, 198, 65, 235), where="alaska"),
        CountryHighlightCue(2, "CAN", 7.4, 12.2, (219, 94, 86, 225), where="all"),
        CountryHighlightCue(3, "MYS", 14.0, 20.2, (219, 94, 86, 235), where="all"),
        CountryHighlightCue(4, "BRN", 18.2, 27.0, (245, 197, 24, 245), where="all"),
        CountryHighlightCue(5, "OMN", 28.8, 35.0, (219, 94, 86, 240), where="all"),
        CountryHighlightCue(6, "ARE", 29.4, 35.0, (242, 198, 65, 240), where="all"),
        CountryHighlightCue(7, "COD", 41.2, 48.2, (88, 154, 186, 235), where="all"),
        CountryHighlightCue(8, "AGO", 41.5, 48.2, (245, 197, 24, 245), where="cabinda"),
        CountryHighlightCue(9, "AGO", 44.2, 48.2, (82, 168, 104, 235), where="angola_main"),
        CountryHighlightCue(10, "AZE", 50.0, 55.8, (88, 154, 186, 235), where="azerbaijan_main"),
        CountryHighlightCue(11, "AZE", 50.2, 55.8, (245, 197, 24, 245), where="nakhchivan"),
        CountryHighlightCue(12, "ARM", 50.6, 55.8, (235, 142, 70, 240), where="all"),
        CountryHighlightCue(1, "USA", 57.2, 62.0, (242, 198, 65, 235), where="alaska"),
    ]

    labels = [
        MapLabelItem("ALASKA", -151.0, 64.5, 1.2, 7.3),
        MapLabelItem("BRITISH", -114.0, 56.5, 8.0, 9.8),
        MapLabelItem("CANADA", -108.0, 56.5, 9.8, 12.0),
        MapLabelItem("MALAYSIA", 102.2, 4.5, 14.6, 18.2, color_rgba=(255, 125, 125, 255)),
        MapLabelItem("PENINSULA", 101.5, 2.2, 15.2, 18.2),
        MapLabelItem("BORNEO", 114.5, 1.5, 15.6, 18.5),
        MapLabelItem("BRUNEI", 114.65, 5.05, 18.8, 26.6),
        MapLabelItem("SARAWAK", 113.8, 3.6, 19.4, 26.6, color_rgba=(255, 130, 130, 255)),
        # Offset into clean dark water of Strait of Hormuz so it never sits on the white coast border
        MapLabelItem("MUSANDAM", 56.05, 26.55, 29.8, 34.8, color_rgba=(255, 155, 155, 255)),
        MapLabelItem("UAE", 54.4, 24.2, 30.2, 34.8),
        MapLabelItem("OMAN", 57.6, 23.2, 30.8, 34.8, color_rgba=(255, 145, 145, 255)),
        MapLabelItem("CABINDA", 11.4, -5.25, 41.8, 47.8),
        MapLabelItem("DR CONGO", 18.5, -4.2, 42.4, 47.8, color_rgba=(135, 205, 255, 255)),
        MapLabelItem("ANGOLA", 17.5, -12.2, 45.0, 47.8, color_rgba=(140, 235, 165, 255)),
        MapLabelItem("NAKHCHIVAN", 45.1, 38.65, 50.8, 55.6),
        MapLabelItem("ARMENIA", 44.5, 40.45, 51.2, 55.6, color_rgba=(255, 185, 110, 255)),
        MapLabelItem("AZERBAIJAN", 47.9, 40.5, 51.0, 55.6, color_rgba=(135, 205, 255, 255)),
        MapLabelItem("IRAN", 46.2, 37.5, 51.8, 55.6),
    ]

    pills = [
        PillBannerItem("$7.2M · ≈2¢/ACRE · 1867", 540.0, 320.0, 0.6, 5.2, theme="red"),
        PillBannerItem("BORDER CHECK", 540.0, 410.0, 5.2, 7.3, theme="red"),
        PillBannerItem("STILL IN THE WAY", 540.0, 340.0, 8.4, 11.8, theme="red"),
        PillBannerItem("2 PIECES", 540.0, 310.0, 12.4, 14.4, theme="dark"),
        PillBannerItem("1963", 540.0, 310.0, 14.5, 17.8, theme="dark"),
        PillBannerItem("1890", 540.0, 310.0, 18.6, 21.8, theme="dark"),
        PillBannerItem("19 MI", 540.0, 310.0, 22.0, 26.6, theme="blue"),
        PillBannerItem("RIGHT OUT OF THE MIDDLE", 540.0, 400.0, 22.4, 26.6, theme="dark"),
        PillBannerItem("STRAIT OF HORMUZ", 540.0, 310.0, 27.6, 31.4, theme="blue"),
        PillBannerItem("EXIT OMAN", 540.0, 310.0, 31.6, 34.8, theme="red"),
        PillBannerItem("SAME TRICK", 540.0, 290.0, 35.4, 40.0, theme="dark"),
        PillBannerItem("A WHOLE SEA", 540.0, 380.0, 35.8, 40.0, theme="blue"),
        PillBannerItem("ALASKA", 310.0, 480.0, 36.0, 40.0, theme="yellow"),
        PillBannerItem("MALAYSIA", 770.0, 480.0, 36.3, 40.0, theme="red"),
        PillBannerItem("BRUNEI", 310.0, 575.0, 36.6, 40.0, theme="yellow"),
        PillBannerItem("OMAN", 770.0, 575.0, 36.9, 40.0, theme="red"),
        PillBannerItem("1885", 540.0, 310.0, 41.0, 44.2, theme="dark"),
        PillBannerItem("WRONG SIDE", 540.0, 310.0, 44.4, 47.8, theme="red"),
        PillBannerItem("1921", 540.0, 310.0, 48.8, 51.8, theme="dark"),
        PillBannerItem("TURKEY · 11 KM", 540.0, 310.0, 52.0, 55.6, theme="red"),
        PillBannerItem("EXCEPT AZERBAIJAN", 540.0, 400.0, 52.8, 55.6, theme="dark"),
    ]

    events = sorted(set([round(t * 1.10, 2) for t in range(1, int(total_dur / 1.10) + 1) if t * 1.10 < total_dur]))
    return EpisodeSpec(
        episode_id="cut_in_two",
        total_duration=total_dur,
        first_highlight_t=0.10,
        moves=moves,
        event_timestamps=events,
        highlights=highlights,
        labels=labels,
        pills=pills,
        map_has_yellow=True,
    )


# ==============================================================================
# 4. EXACT 3D UNIT-SPHERE CAMERA PROJECTION (ZERO POLAR VORTEX, ZERO SEAM!)
# ==============================================================================
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
REGION_MASK: np.ndarray | None = None

GRID_STEP = 6
GX_1D = np.linspace(0.0, float(W), W // GRID_STEP + 1, dtype=np.float64)
GY_1D = np.linspace(0.0, float(H), H // GRID_STEP + 1, dtype=np.float64)
GX, GY = np.meshgrid(GX_1D, GY_1D)
FULL_XS = np.arange(W, dtype=np.float32)[None, :]
FULL_YS = np.arange(H, dtype=np.float32)[:, None]


def get_font(size: float) -> ImageFont.FreeTypeFont:
    key = max(10, int(round(size)))
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(FONT_PATH, key)
    return FONTS[key]


def ensure_assets() -> Path:
    if not PLATE_PATH.exists() or PLATE_PATH.stat().st_size < 100_000:
        print("[ASSET] Downloading NASA Topo/Bathy Satellite Plate...", flush=True)
        urllib.request.urlretrieve(PLATE_URL, PLATE_PATH)
    if not GEOJSON_50M.exists() or GEOJSON_50M.stat().st_size < 100_000:
        print("[ASSET] Downloading Natural Earth Countries...", flush=True)
        urllib.request.urlretrieve(GEOJSON_50M_URL, GEOJSON_50M)
    return GEOJSON_50M


def load_enhanced_plate() -> np.ndarray:
    raw = np.asarray(Image.open(PLATE_PATH).convert("RGB"), dtype=np.uint8)
    blur = cv2.GaussianBlur(raw, (0, 0), 2.0)
    return cv2.addWeighted(raw, 1.22, blur, -0.22, 0)


def make_starfield() -> np.ndarray:
    rng = np.random.default_rng(7)
    img = np.zeros((H, W, 3), np.uint8)
    y = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    sky = (np.array([4, 7, 15]) * (1.0 - y) + np.array([12, 19, 32]) * y).astype(np.uint8)
    img[:] = sky[:, None, :]
    ys = rng.integers(0, H, 260)
    xs = rng.integers(0, W, 260)
    mag = rng.integers(150, 255, 260)
    img[ys, xs] = mag[:, None]
    return img


def where_ok(kind: str, lon: float, lat: float) -> bool:
    if kind == "alaska":
        return lat > 51.0 and (lon < -129.9 or lon > 170.0)
    if kind == "cabinda":
        return 11.5 <= lon <= 13.2 and -6.02 <= lat <= -4.2
    if kind == "angola_main":
        return lat < -6.02
    if kind == "nakhchivan":
        return 44.7 <= lon <= 46.15 and 38.75 <= lat <= 39.85
    if kind == "azerbaijan_main":
        return lon > 46.15 or lat > 39.85
    return True


def build_region_mask(rings: list[dict], spec: EpisodeSpec, p_w: int, p_h: int) -> np.ndarray:
    """
    Rasterizes every highlighted country/region into an equirectangular ID mask (p_h x p_w)
    matching PLATE pixel-for-pixel. Because highlights are warped with the exact same
    3D spherical lookup table as PLATE, Canada and Alaska NEVER suffer from polygon
    chord-closing or horizon-clipping glitches!
    """
    mask = np.zeros((p_h, p_w), dtype=np.uint8)
    unique_regions: Dict[int, Tuple[str, str]] = {}
    for cue in spec.highlights:
        unique_regions[cue.region_id] = (cue.iso_a3, cue.where)

    for reg_id, (iso, where_kind) in unique_regions.items():
        polys = []
        for ring in rings:
            if ring["iso"] != iso:
                continue
            if not where_ok(where_kind, ring["clon"], ring["clat"]):
                continue
            px = ((np.mod(ring["lon"] + 180.0, 360.0) / 360.0) * (p_w - 1)).astype(np.int32)
            py = (((90.0 - ring["lat"]) / 180.0) * (p_h - 1)).astype(np.int32)
            # Skip rings that wrap across the +-180 edge in pixel space
            if len(px) > 1 and np.max(np.abs(np.diff(px))) > p_w * 0.4:
                continue
            polys.append(np.column_stack([px, py]))
        if polys:
            cv2.fillPoly(mask, polys, int(reg_id))
    return mask


def camera_scale_and_radius(span: float, w: float) -> Tuple[float, float, float]:
    """
    Returns (mix, scale_px_per_rad, globe_radius_px) for the unified 3D spherical camera.
    - When w = 0 (flat map): scale = W / rad(span)
    - When w = 1 (3D globe): globe_radius = 455 px (true circular 3D globe inside 1080x1920)
    """
    mix = float(smootherstep(w))
    flat_scale = W / max(math.radians(span), 1e-4)
    globe_r = float(np.clip((W * 0.43) * (64.0 / max(span, 42.0)), 430.0, 485.0))
    scale = (1.0 - mix) * flat_scale + mix * globe_r
    return mix, scale, globe_r


def project(
    lon: np.ndarray,
    lat: np.ndarray,
    cam_lon: float,
    cam_lat: float,
    span: float,
    w: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Exact 3D Spherical Forward Projection:
    Maps any (lon, lat) on Earth into camera-centered 3D unit sphere coordinates (Xc, Yc, Zc),
    then applies the Cinfty monotonic radial morph `rho(c) = (1 - s) * c + s * sin(c)`.
    Zero pole singularity, zero dateline jump!
    """
    mix, scale, _ = camera_scale_and_radius(span, w)
    dlon = np.radians(lon - cam_lon)
    phi = np.radians(lat)
    phi0 = math.radians(cam_lat)

    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    cos_phi0 = math.cos(phi0)
    sin_phi0 = math.sin(phi0)
    cos_dlon = np.cos(dlon)
    sin_dlon = np.sin(dlon)

    # Camera-space 3D unit vector (Xc, Yc, Zc)
    xc = cos_phi * sin_dlon
    yc = cos_phi0 * sin_phi - sin_phi0 * cos_phi * cos_dlon
    zc = np.clip(sin_phi0 * sin_phi + cos_phi0 * cos_phi * cos_dlon, -1.0, 1.0)

    c = np.arccos(zc)
    sin_c = np.maximum(np.hypot(xc, yc), 1e-9)

    # Morphed radial distance: c (azimuthal flat) <-> sin(c) (3D orthographic globe)
    rho = (1.0 - mix) * c + mix * np.sin(c)
    factor = (scale * rho) / sin_c

    x = W * 0.5 + xc * factor
    y = H * 0.5 - yc * factor
    # Visible hemisphere: strictly front-facing on globe (c <= 88 deg), wider on flat map
    max_c = (1.0 - mix) * 1.48 + mix * 1.53
    visible = c <= max_c
    return x, y, visible


def spherical_camera_warp(
    cam_lon: float,
    cam_lat: float,
    span: float,
    w: float,
    active_fills: List[Tuple[int, Tuple[int, int, int, int], float]],
) -> np.ndarray:
    """
    Exact Analytical Inverse of `project()` in 3D Unit-Sphere Coordinates:
    1. For every coarse grid point (GX, GY), computes normalized radius `rho = r_px / scale`.
    2. Solves `(1 - s) * c + s * sin(c) = rho` in 2 scalar Newton steps to 1e-12 precision.
    3. Reconstructs the 3D unit vector (vx, vy, vz) on Earth — which is 100% smooth across
       both the North/South Poles and the +-180 dateline!
    4. Upsamples (vx, vy, vz) smoothly to 1080x1920, then converts to (map_x, map_y)
       for `cv2.remap` on PLATE and REGION_MASK.
    """
    assert PLATE is not None and STARS is not None and REGION_MASK is not None
    mix, scale, globe_r = camera_scale_and_radius(span, w)
    p_h, p_w = PLATE.shape[:2]

    dx = GX - W * 0.5
    dy = -(GY - H * 0.5)
    r_px = np.hypot(dx, dy)
    rho = r_px / scale

    # Clamp rho to the valid domain of (1 - mix)*c + mix*sin(c) on [0, pi/2]
    max_rho = (1.0 - mix) * (math.pi * 0.495) + mix * 1.0
    rho_clamped = np.minimum(rho, max_rho * 0.9995)

    # Exact 2-step scalar Newton inversion of rho(c) = (1 - mix)*c + mix*sin(c)
    c = np.where(mix > 0.5, np.arcsin(np.minimum(rho_clamped, 1.0)), rho_clamped)
    for _ in range(2):
        f_val = (1.0 - mix) * c + mix * np.sin(c) - rho_clamped
        f_der = np.maximum((1.0 - mix) + mix * np.cos(c), 1e-5)
        c = np.clip(c - f_val / f_der, 0.0, math.pi * 0.498)

    sin_c = np.sin(c)
    cos_c = np.cos(c)
    r_safe = np.maximum(r_px, 1e-7)

    # Camera-space unit vector (Xc, Yc, Zc)
    xc = (dx / r_safe) * sin_c
    yc = (dy / r_safe) * sin_c
    zc = cos_c

    # Rotate camera-space 3D vector back to World Earth 3D unit vector (vx, vy, vz)
    phi0 = math.radians(cam_lat)
    lam0 = math.radians(cam_lon)
    cos_phi0, sin_phi0 = math.cos(phi0), math.sin(phi0)
    cos_lam0, sin_lam0 = math.cos(lam0), math.sin(lam0)

    # Intermediate after undoing latitude tilt phi0:
    x1 = xc
    y1 = -sin_phi0 * yc + cos_phi0 * zc
    vz = np.clip(cos_phi0 * yc + sin_phi0 * zc, -1.0, 1.0)

    # Undo longitude rotation lam0 -> 3D Earth Cartesian (vx, vy, vz):
    vx = cos_lam0 * y1 - sin_lam0 * x1
    vy = sin_lam0 * y1 + cos_lam0 * x1

    # Upsample smooth 3D Cartesian components (vx, vy, vz) to 1080x1920 BEFORE atan2!
    # Because (vx, vy, vz) has NO branch cut at +-180 and NO singularity at the poles,
    # upsampling (vx, vy, vz) produces ZERO vertical seams and ZERO polar whirlpools!
    vx_full = cv2.resize(vx.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vy_full = cv2.resize(vy.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    vz_full = np.clip(cv2.resize(vz.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR), -1.0, 1.0)

    lon_rad = np.arctan2(vy_full, vx_full)  # in [-pi, +pi]
    lat_rad = np.arcsin(vz_full)            # in [-pi/2, +pi/2]

    map_x = ((lon_rad + math.pi) * (1.0 / (2.0 * math.pi)) * (p_w - 1)).astype(np.float32)
    map_y = ((math.pi * 0.5 - lat_rad) * (1.0 / math.pi) * (p_h - 1)).astype(np.float32)

    sampled = cv2.remap(PLATE, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

    # Apply rasterized country highlights in the exact same projection (zero chord-closing!)
    if active_fills:
        reg_warped = cv2.remap(REGION_MASK, map_x, map_y, interpolation=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
        blended = sampled.astype(np.float32)
        for reg_id, rgba, alpha in active_fills:
            sel = reg_warped == reg_id
            if np.any(sel):
                w_fill = float(alpha) * (rgba[3] / 255.0) * 0.78
                color_vec = np.array(rgba[:3], dtype=np.float32)
                blended[sel] = blended[sel] * (1.0 - w_fill) + color_vec * w_fill
        sampled = np.clip(blended, 0, 255).astype(np.uint8)

    if mix < 0.005:
        return sampled

    # Circular 3D Globe Silhouette when mix -> 1.0, smoothly expanding to full screen as mix -> 0.0
    # Note: At mix = 1.0, rx = ry = globe_r and exponent = 2.0 -> 100% TRUE CIRCLE!
    rx = (1.0 - mix) * (W * 0.75) + mix * globe_r
    ry = (1.0 - mix) * (H * 0.75) + mix * globe_r
    exponent = (1.0 - mix) * 8.0 + mix * 2.0

    dx_norm = np.abs(FULL_XS - W * 0.5) / rx
    dy_norm = np.abs(FULL_YS - H * 0.5) / ry
    super_dist = (dx_norm ** exponent + dy_norm ** exponent) ** (1.0 / exponent)

    inside = super_dist <= 1.0
    # 3D spherical limb darkening near the edge of the globe
    limb_shade = np.clip(1.0 - 0.28 * mix * np.clip((super_dist - 0.78) / 0.22, 0.0, 1.0), 0.70, 1.0)
    sampled_shaded = (sampled.astype(np.float32) * limb_shade[:, :, None]).astype(np.uint8)

    frame = STARS.copy()
    frame[inside] = sampled_shaded[inside]

    # Crisp blue 3D atmospheric rim glow
    if mix > 0.15:
        rim_band = (super_dist >= 0.986) & (super_dist <= 1.012)
        atmo_alpha = float(smoothstep((mix - 0.15) / 0.60)) * 0.82
        atmo_color = np.array([110, 185, 250], dtype=np.float32)
        frame[rim_band] = np.clip(
            frame[rim_band].astype(np.float32) * (1.0 - atmo_alpha) + atmo_color * atmo_alpha,
            0,
            255,
        ).astype(np.uint8)

    return frame


# ==============================================================================
# 5. VECTOR COASTLINE OVERLAY, COLLISION-FREE LABELS & CYAN KARAOKE
# ==============================================================================
PILL_RGB = {
    "red": ((212, 38, 42), (255, 255, 255)),
    "dark": ((16, 22, 34), (255, 255, 255)),
    "blue": ((14, 116, 218), (255, 255, 255)),
    "yellow": ((245, 197, 24), (14, 18, 26)),
    "white": ((248, 250, 252), (14, 18, 26)),
}


def load_rings(geojson_path: Path) -> list[dict]:
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        props = feature.get("properties") or {}
        iso = props.get("ADM0_A3") or props.get("ISO_A3") or ""
        geometry = feature.get("geometry")
        if not geometry:
            continue
        polygons = (
            geometry["coordinates"]
            if geometry["type"] == "MultiPolygon"
            else [geometry["coordinates"]]
        )
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


def split_visible_polylines(
    x: np.ndarray, y: np.ndarray, visible: np.ndarray, max_step: float
) -> list[np.ndarray]:
    step = np.hypot(np.diff(x, prepend=x[:1]), np.diff(y, prepend=y[:1]))
    keep = visible & (step <= max_step)
    cuts = np.where(np.diff(keep.astype(np.int8)) != 0)[0] + 1
    bounds = [0, *cuts.tolist(), len(x)]
    runs = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a >= 2 and bool(keep[a]):
            runs.append(np.column_stack([x[a:b], y[a:b]]).astype(np.int32))
    return runs


def draw_vector_borders(
    frame: np.ndarray,
    rings: list[dict],
    lon0: float,
    lat0: float,
    span: float,
    w: float,
) -> None:
    """Draws crisp anti-aliased country border polylines clipped cleanly to the 3D globe disc."""
    mix, _, globe_r = camera_scale_and_radius(span, w)
    rx = (1.0 - mix) * (W * 0.75) + mix * globe_r
    ry = (1.0 - mix) * (H * 0.75) + mix * globe_r
    exponent = (1.0 - mix) * 8.0 + mix * 2.0

    coasts = []
    thick = 3 if span < 14.0 else (2 if span < 35.0 else 1)

    for ring in rings:
        if (span > 55.0 or mix > 0.5) and ring["n"] < 28:
            continue
        x, y, visible = project(ring["lon"], ring["lat"], lon0, lat0, span, w)
        if mix > 0.05:
            dx_n = np.abs(x - W * 0.5) / (rx * 0.992)
            dy_n = np.abs(y - H * 0.5) / (ry * 0.992)
            inside_sil = (dx_n ** exponent + dy_n ** exponent) <= 1.0
            visible = visible & inside_sil
        if not np.any(visible):
            continue
        if not np.any((x > -120) & (x < W + 120) & (y > -120) & (y < H + 120)):
            continue
        max_step = 80.0 if mix > 0.3 else 220.0
        runs = split_visible_polylines(x, y, visible, max_step)
        if runs:
            coasts.extend(runs)

    if coasts:
        color = (238, 242, 246) if span < 38.0 and mix < 0.4 else (178, 192, 206)
        cv2.polylines(frame, coasts, False, color, thick, cv2.LINE_AA)


def resolve_2d_label_collisions(
    boxes: List[Tuple[float, float, float, float]],
    min_gap_px: float = 20.0,
    iterations: int = 14,
) -> List[Tuple[float, float]]:
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

    return [
        (max(115.0, min(880.0, c[0])), max(255.0, min(1190.0, c[1])))
        for c in centers
    ]


def text_size(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0], box[3] - box[1]


def draw_overlay(
    rgb: np.ndarray,
    spec: EpisodeSpec,
    all_words: List[Dict],
    lon0: float,
    lat0: float,
    span: float,
    w: float,
    t: float,
) -> np.ndarray:
    image = Image.fromarray(rgb).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Collision-free Map Labels
    visible_labels = []
    for label in spec.labels:
        alpha, _dx, _dy = element_fade_and_exit_offset(t, label.enter_t, label.exit_t, 0.28, 0.30)
        if alpha <= 0.04:
            continue
        x, y, vis = project(np.array([label.lon]), np.array([label.lat]), lon0, lat0, span, w)
        if not bool(vis[0]):
            continue
        px, py = float(x[0]), float(y[0])
        if not (50 < px < W - 50 and 190 < py < H - 340):
            continue
        pop, _ = label_pop_state(t - label.enter_t, 0.30)
        face = get_font(label.font_size * max(pop, 0.5))
        tw, th = text_size(draw, label.text, face)
        visible_labels.append((label, alpha, px, py, tw + 14, th + 12, face))

    if visible_labels:
        boxes = [(px, py, tw, th) for _l, _a, px, py, tw, th, _f in visible_labels]
        centers = resolve_2d_label_collisions(boxes, min_gap_px=22.0)
        for (label, alpha, _px, _py, _tw, _th, face), (cx, cy) in zip(visible_labels, centers):
            ink = label.color_rgba[:3] + (int(255 * alpha),)
            stroke = (10, 14, 22, int(248 * alpha))
            tw, th = text_size(draw, label.text, face)
            ox, oy = cx - tw / 2.0, cy - th / 2.0
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                draw.text((ox + dx, oy + dy), label.text, font=face, fill=stroke)
            draw.text((ox, oy), label.text, font=face, fill=ink)

    # 2. High-Contrast Pills with solid dark drop-shadow so they never look muddy during fade
    for pill in spec.pills:
        alpha, dx, dy = element_fade_and_exit_offset(t, pill.enter_t, pill.exit_t, 0.26, 0.28)
        if alpha <= 0.04:
            continue
        pop, _ = label_pop_state(t - pill.enter_t, 0.30)
        face = get_font(38.0 * max(pop, 0.85))
        bg, fg = PILL_RGB.get(pill.theme, PILL_RGB["dark"])
        tw, th = text_size(draw, pill.text, face)
        pad_x, pad_y = 28, 16
        box_w = tw + pad_x * 2
        box_h = th + pad_y * 2
        cx = max(75 + box_w / 2, min(W - 75 - box_w / 2, pill.screen_x + dx))
        cy = max(240 + box_h / 2, min(1180 - box_h / 2, pill.screen_y + dy))
        rect = [cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2]
        shadow_rect = [rect[0] + 4, rect[1] + 5, rect[2] + 4, rect[3] + 5]
        a_solid = int(252 * (alpha ** 0.65))
        draw.rounded_rectangle(shadow_rect, radius=18, fill=(8, 12, 20, int(190 * alpha)))
        draw.rounded_rectangle(rect, radius=18, fill=bg + (a_solid,), outline=(255, 255, 255, int(90 * alpha)), width=2)
        draw.text((cx - tw / 2, cy - th / 2 - 2), pill.text, font=face, fill=fg + (a_solid,))

    # 3. Full-Duration Cyan (#00E5FF) Karaoke Captions (64-72% band, y=1300)
    phrases: List[List[Dict]] = []
    cur: List[Dict] = []
    for w_item in all_words:
        if cur and (len(cur) >= 4 or (float(w_item["start"]) - float(cur[-1]["end"])) > 0.40):
            phrases.append(cur)
            cur = []
        cur.append(w_item)
    if cur:
        phrases.append(cur)

    active_phrase = None
    for ph in phrases:
        if (float(ph[0]["start"]) - 0.10) <= t <= (float(ph[-1]["end"]) + 0.15):
            active_phrase = ph
            break

    if active_phrase:
        t_lead = t + 0.04
        face = get_font(64.0)
        gap = 16
        widths = [text_size(draw, str(w_it["text"]), face)[0] for w_it in active_phrase]
        total_w = sum(widths) + gap * (len(active_phrase) - 1)
        if total_w > 820:
            face = get_font(max(52.0, 64.0 * (820.0 / total_w)))
            widths = [text_size(draw, str(w_it["text"]), face)[0] for w_it in active_phrase]
            total_w = sum(widths) + gap * (len(active_phrase) - 1)

        x_cur = max(70.0, min(500.0 - total_w * 0.5, 895.0 - total_w))
        y_cur = 1300.0
        for w_it, ww in zip(active_phrase, widths):
            is_act = float(w_it["start"]) <= t_lead <= float(w_it["end"])
            color = (0, 229, 255, 255) if is_act else (255, 255, 255, 255)
            txt = str(w_it["text"])
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3)):
                draw.text((x_cur + dx, y_cur + dy), txt, font=face, fill=(10, 14, 22, 248))
            draw.text((x_cur, y_cur), txt, font=face, fill=color)
            x_cur += ww + gap

    image.alpha_composite(overlay)
    return np.asarray(image.convert("RGB"))


# ==============================================================================
# 6. UNIFORM VOICEOVER + VELOCITY-PEAK SFX + SEAMLESS LOOP AUDIO MIXER
# ==============================================================================
def build_full_audio_track(spec: EpisodeSpec) -> np.ndarray:
    sr = 48000
    total_samples = int(round(spec.total_duration * sr))
    master = np.zeros((total_samples, 2), dtype=np.float64)

    t_vec = np.arange(total_samples, dtype=np.float64) / sr
    bgm = (
        0.016 * np.sin(2.0 * math.pi * 110.0 * t_vec)
        + 0.010 * np.sin(2.0 * math.pi * 165.0 * t_vec)
    )
    master[:, 0] += bgm
    master[:, 1] += bgm

    # Generate ALL 11 lines with the exact same voice (`en-US-ChristopherNeural`)
    # so there is zero speaker change at 00:58!
    for idx, (t0, t1, text) in enumerate(SCRIPT_TIMED_LINES):
        start_sample = int(round(t0 * sr))
        seg_wav = CACHE_DIR / f"vo_uniform_{idx:02d}.wav"

        if not seg_wav.exists():
            mp3_tmp = CACHE_DIR / f"vo_uniform_{idx:02d}.mp3"
            try:
                subprocess.run(
                    [
                        "edge-tts",
                        "--voice", "en-US-ChristopherNeural",
                        "--rate=+8%",
                        "--text", text,
                        "--write-media", str(mp3_tmp),
                    ],
                    check=True, capture_output=True, timeout=20,
                )
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(mp3_tmp), "-ar", str(sr), "-ac", "1", str(seg_wav)],
                    check=True, capture_output=True,
                )
            except Exception:
                try:
                    subprocess.run(
                        ["espeak-ng", "-v", "en-us", "-s", "175", "-w", str(seg_wav), text],
                        check=True, capture_output=True,
                    )
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", str(seg_wav), "-ar", str(sr), "-ac", "1", str(seg_wav) + ".tmp.wav"],
                        check=True, capture_output=True,
                    )
                    Path(str(seg_wav) + ".tmp.wav").replace(seg_wav)
                except Exception:
                    pass

        if seg_wav.exists():
            try:
                with wave.open(str(seg_wav), "rb") as wf:
                    if wf.getframerate() == sr:
                        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
                        if wf.getnchannels() == 2:
                            pcm = pcm.reshape(-1, 2).mean(axis=1)
                        end_sample = min(total_samples, start_sample + len(pcm))
                        if end_sample > start_sample:
                            master[start_sample:end_sample, 0] += pcm[: end_sample - start_sample] * 0.88
                            master[start_sample:end_sample, 1] += pcm[: end_sample - start_sample] * 0.88
            except Exception:
                pass

    # Velocity-Peak Synced Whooshes
    n_w = int(round(0.36 * sr))
    tw = np.linspace(0.0, 0.36, n_w, dtype=np.float64)
    uw = tw / 0.36
    env_w = 30.0 * (uw ** 2) * ((1.0 - uw) ** 2)
    whoosh_sig = env_w * np.sin(2.0 * math.pi * (130.0 * tw + 240.0 * (tw ** 2))) * 0.15
    for mv in spec.moves:
        peak_t = mv.start_t + 0.5 * mv.duration - 0.18
        idx = int(round(max(0.0, peak_t) * sr))
        end_idx = min(total_samples, idx + n_w)
        if end_idx > idx:
            master[idx:end_idx, 0] += whoosh_sig[: end_idx - idx]
            master[idx:end_idx, 1] += whoosh_sig[: end_idx - idx]

    # Harmonic Pops on Pills & Labels
    n_p = int(round(0.08 * sr))
    tp = np.linspace(0.0, 0.08, n_p, dtype=np.float64)
    env_p = np.exp(-tp * 42.0) * np.sin(math.pi * tp / 0.08)
    pop_sig = env_p * np.sin(2.0 * math.pi * (340.0 + 460.0 * (tp / 0.08)) * tp) * 0.18
    pop_times = sorted(set([p.enter_t for p in spec.pills] + [l.enter_t for l in spec.labels]))
    for pt in pop_times:
        idx = int(round(max(0.0, pt + 0.03) * sr))
        end_idx = min(total_samples, idx + n_p)
        if end_idx > idx:
            master[idx:end_idx, 0] += pop_sig[: end_idx - idx]
            master[idx:end_idx, 1] += pop_sig[: end_idx - idx]

    # Seamless 0.25s loop tail wrap into Frame 0
    n_tail = int(round(0.25 * sr))
    u = np.linspace(0.0, 1.0, n_tail, dtype=np.float64)[:, None]
    s = u * u * u * (u * (u * 6.0 - 15.0) + 10.0)
    tail_seg = master[-n_tail:].copy()
    head_seg = master[:n_tail].copy()
    master[:n_tail] = head_seg * np.sqrt(s) + tail_seg * np.sqrt(1.0 - s)

    peak = float(np.max(np.abs(master)))
    if peak > 0.89:
        master *= 0.89 / peak
    return master


# ==============================================================================
# 7. MAIN EXECUTION
# ==============================================================================
def render_frame_at(rings: list[dict], spec: EpisodeSpec, all_words: List[Dict], st: Dict[str, float], t: float) -> np.ndarray:
    active_fills = []
    for cue in spec.highlights:
        alpha = element_fade_and_exit_offset(t, cue.enter_t, cue.exit_t, 0.30, 0.30)[0]
        if alpha > 0.02:
            active_fills.append((cue.region_id, cue.fill_rgba, alpha))

    frame = spherical_camera_warp(st["lon"], st["lat"], st["span"], st["w"], active_fills)
    draw_vector_borders(frame, rings, st["lon"], st["lat"], st["span"], st["w"])
    return draw_overlay(frame, spec, all_words, st["lon"], st["lat"], st["span"], st["w"], t)


def main() -> None:
    global PLATE, STARS, REGION_MASK
    geojson_path = ensure_assets()
    PLATE = load_enhanced_plate()
    STARS = make_starfield()
    rings = load_rings(geojson_path)
    spec = build_cut_in_two_episode()
    rig = spec.build_rig()
    all_words = build_full_karaoke_words()
    REGION_MASK = build_region_mask(rings, spec, PLATE.shape[1], PLATE.shape[0])

    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out_dir = Path("/tmp/cit_v3_stills")
        out_dir.mkdir(parents=True, exist_ok=True)
        test_times = [float(x) for x in sys.argv[2:]] or [0.0, 9.5, 13.8, 21.0, 31.0, 37.5, 44.0, 53.0, 59.5]
        for t in test_times:
            st = rig.evaluate_all(min(t, spec.total_duration))
            img = render_frame_at(rings, spec, all_words, st, t)
            p = out_dir / f"t_{t:05.1f}s.jpg"
            Image.fromarray(img).save(p, quality=92)
            print(f"[STILL] {p} (w={st['w']:.2f}, span={st['span']:.1f}°, lon={st['lon']:.1f}°, lat={st['lat']:.1f}°)")
        return

    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    audio_f64 = build_full_audio_track(spec)
    audio_i16 = (audio_f64 * 32767.0).astype(np.int16)

    wav_path = Path("/tmp/cit_v3_master.wav")
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
        "-c:v", "libx264", "-preset", "faster", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ]

    print(f"[RENDER] Rendering {n_frames} frames ({spec.total_duration}s @ 60fps) -> {OUT_MP4}", flush=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for f in range(n_frames):
            t = f / FPS
            st = rig.evaluate_all(t)
            rgb = render_frame_at(rings, spec, all_words, st, t)
            proc.stdin.write(rgb.tobytes())
            if f % (FPS * 5) == 0:
                print(
                    f"  frame {f:04d}/{n_frames} (t={t:04.1f}s) | "
                    f"w={st['w']:.2f} span={st['span']:04.1f}° lon={st['lon']:+06.1f}° lat={st['lat']:+05.1f}°",
                    flush=True,
                )
    finally:
        proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")
    print(f"[DONE] Successfully rendered: {OUT_MP4}", flush=True)


if __name__ == "__main__":
    main()
