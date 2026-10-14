"""
Juicy Tea Map-Shorts Engine — Continuous C2 Camera, Globe Morph & Hermite Loop.
Supports close-up spans down to 3.2 degrees and orthographic globe morphs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

FPS: int = 60
WIDTH: int = 1080
HEIGHT: int = 1920
MIN_SPAN_DEG: float = 3.2
MAX_SPAN_DEG: float = 170.0
LOOP_TAIL_SEC: float = 0.5
LOOP_FRAMES: int = int(round(LOOP_TAIL_SEC * FPS))


def smoothstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * (3.0 - 2.0 * u_c)


def smootherstep(u: float | np.ndarray) -> float | np.ndarray:
    u_c = np.clip(u, 0.0, 1.0)
    return u_c * u_c * u_c * (u_c * (u_c * 6.0 - 15.0) + 10.0)


def smootherstep_deriv(u: float | np.ndarray, duration: float) -> float | np.ndarray:
    if duration <= 1e-9:
        return 0.0
    u_c = np.clip(u, 0.0, 1.0)
    return (30.0 * (u_c ** 2) * ((1.0 - u_c) ** 2)) / duration


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
        if n < 2:
            raise ValueError("At least 2 anchors are required for C2 spline.")
        if np.any(np.diff(self.t) <= 1e-6):
            raise ValueError("Anchor timestamps must be strictly increasing.")

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
    length = max(t1 - t0, 1e-9)
    u = float(np.clip((t - t0) / length, 0.0, 1.0))
    u2 = u * u
    u3 = u2 * u
    h00 = 2.0 * u3 - 3.0 * u2 + 1.0
    h10 = u3 - 2.0 * u2 + u
    h01 = -2.0 * u3 + 3.0 * u2
    h11 = u3 - u2
    pos = h00 * p0 + h10 * (length * v0) + h01 * p1 + h11 * (length * v1)
    dh00 = 6.0 * u2 - 6.0 * u
    dh10 = 3.0 * u2 - 4.0 * u + 1.0
    dh01 = -6.0 * u2 + 6.0 * u
    dh11 = 3.0 * u2 - 2.0 * u
    vel = (dh00 * p0 + dh10 * (length * v0) + dh01 * p1 + dh11 * (length * v1)) / length
    ddh00 = 12.0 * u - 6.0
    ddh10 = 6.0 * u - 4.0
    ddh01 = -12.0 * u + 6.0
    ddh11 = 6.0 * u - 2.0
    acc = (ddh00 * p0 + ddh10 * (length * v0) + ddh01 * p1 + ddh11 * (length * v1)) / (length * length)
    return float(pos), float(vel), float(acc)


class ContinuousCameraRig:
    def __init__(self, anchors: List[CameraAnchor], total_duration: float) -> None:
        if len(anchors) < 2:
            raise ValueError("At least 2 camera anchors are required.")
        self.total_duration = float(total_duration)
        self.loop_start_t = self.total_duration - LOOP_TAIL_SEC
        self.v0_w = 0.0
        self.v0_lon = 0.18
        self.v0_lat = 0.04
        self.v0_log_span = -0.015

        first = anchors[0]
        core_anchors = [a for a in anchors if a.t < self.loop_start_t - 0.8]
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
            lat, dlat, ddlat = hermite_segment(
                t_clamped, self.loop_start_t, self.total_duration, lat0, dlat0, lat1, dlat1
            )
            ls0, dls0, _ = self.spline_log_span.eval_with_derivs(self.loop_start_t)
            ls1, dls1, _ = self.spline_log_span.eval_with_derivs(0.0)
            lspan, dlspan, ddlspan = hermite_segment(
                t_clamped, self.loop_start_t, self.total_duration, ls0, dls0, ls1, dls1
            )
        return {
            "w": w, "dw": dw, "ddw": ddw,
            "lon": lon, "dlon": dlon, "ddlon": ddlon,
            "lat": lat, "dlat": dlat, "ddlat": ddlat,
            "log_span": lspan, "dlog_span": dlspan, "ddlog_span": ddlspan,
            "span": math.exp(lspan),
        }

    def camera_channels(self, t: float) -> Tuple[float, float, float, float]:
        state = self.evaluate_all(t)
        return state["w"], state["lon"], state["lat"], state["span"]


def project_point_merc_ortho_blend(
    lon_deg: float,
    lat_deg: float,
    cam_lon: float,
    cam_lat: float,
    span_deg: float,
    w: float,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> Tuple[float, float, bool]:
    blend = float(smootherstep(w))
    dlon = ((lon_deg - cam_lon + 180.0) % 360.0) - 180.0
    scale_merc = width / max(span_deg, 1e-3)
    lat_clamped = max(-84.0, min(84.0, lat_deg))
    cam_lat_clamped = max(-84.0, min(84.0, cam_lat))
    merc_y = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(lat_clamped) / 2.0)))
    cam_merc_y = math.degrees(math.log(math.tan(math.pi / 4.0 + math.radians(cam_lat_clamped) / 2.0)))
    cos_center = max(math.cos(math.radians(cam_lat_clamped)), 0.22)
    x_merc = width * 0.5 + dlon * scale_merc * cos_center
    y_merc = height * 0.5 - (merc_y - cam_merc_y) * scale_merc * cos_center

    lam = math.radians(dlon)
    phi = math.radians(lat_deg)
    phi0 = math.radians(cam_lat)
    cos_c = math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(lam)
    visible = (cos_c >= -0.05) or (blend < 0.25)
    globe_radius = (width * 0.44) * (68.0 / max(span_deg, 18.0))
    globe_radius = max(380.0, min(width * 0.95, globe_radius))
    x_ortho = width * 0.5 + globe_radius * (math.cos(phi) * math.sin(lam))
    y_ortho = height * 0.5 - globe_radius * (
        math.cos(phi0) * math.sin(phi) - math.sin(phi0) * math.cos(phi) * math.cos(lam)
    )
    x = (1.0 - blend) * x_merc + blend * x_ortho
    y = (1.0 - blend) * y_merc + blend * y_ortho
    return float(x), float(y), bool(visible)


def blend_xy_morph(merc_xy: np.ndarray, ortho_xy: np.ndarray, w: float) -> np.ndarray:
    blend = float(smootherstep(w))
    return (1.0 - blend) * merc_xy + blend * ortho_xy


def superellipse_silhouette(
    w: float, width: int = WIDTH, height: int = HEIGHT, globe_radius: float = 460.0, n_pts: int = 256
) -> Tuple[np.ndarray, float]:
    blend = float(smootherstep(w))
    rx = (1.0 - blend) * (width * 0.52) + blend * globe_radius
    ry = (1.0 - blend) * (height * 0.52) + blend * globe_radius
    exponent = (1.0 - blend) * 18.0 + blend * 2.0
    theta = np.linspace(0.0, 2.0 * math.pi, n_pts, endpoint=False)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    x = (width * 0.5) + rx * np.sign(cos_t) * (np.abs(cos_t) ** (2.0 / exponent))
    y = (height * 0.5) + ry * np.sign(sin_t) * (np.abs(sin_t) ** (2.0 / exponent))
    atmo_alpha = float(smoothstep((blend - 0.55) / (0.93 - 0.55)))
    return np.column_stack([x, y]), atmo_alpha


def globe_lod_mix(span: float) -> float:
    u = (span - 40.0) / (82.0 - 40.0)
    return float(smoothstep(u))
