#!/usr/bin/env python3
"""Prove each render speedup on one segment: zoom, pan, hold, pulsing border.

A speedup that is not pixel-identical (max abs diff > 1) is left off.
"""

from __future__ import annotations

import json
import math
import multiprocessing
import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import skia
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.data import build_earth  # noqa: E402
from jt.draw import _ring_paths  # noqa: E402
from jt.show.basemap import build_plates, view_for  # noqa: E402
from jt.show.camera import Cam  # noqa: E402
from jt.show.fast_render import (  # noqa: E402
    RasterCache,
    SlotCache,
    cpu_workers,
    pipe_rgba_roundtrip,
)
from jt.show.greenland_v5 import Episode  # noqa: E402
from jt.show.lod import paint_lod  # noqa: E402
from jt.show.vfx_core import draw_clouds, exp_zoom  # noqa: E402

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920


def _smooth(u: float) -> float:
    u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
    return u * u * (3.0 - 2.0 * u)


def segment_times() -> list[float]:
    """Hold, pan, zoom, then a hold whose border and clouds keep moving."""
    return [round(i * 0.08, 5) for i in range(20)]


def classify(t: float) -> str:
    if t < 0.40:
        return "hold"
    if t < 0.80:
        return "pan"
    if t < 1.20:
        return "zoom"
    return "anim"


def cam_at(t: float) -> Cam:
    phase = classify(t)
    if phase == "hold":
        return Cam("merc", -6.0, 36.0, 150.0)
    if phase == "pan":
        u = _smooth((t - 0.40) / 0.40)
        return Cam("merc", -6.0 + (-18.0 - -6.0) * u, 36.0 + (48.0 - 36.0) * u, 150.0)
    if phase == "zoom":
        u = _smooth((t - 0.80) / 0.40)
        return Cam("merc", -40.0, 68.0, exp_zoom(70.0, 42.0, u))
    return Cam("merc", -40.0, 68.0, 42.0)


def scene_state(t: float) -> tuple:
    cam = cam_at(t)
    phase = classify(t)
    if phase == "anim":
        pulse = math.sin(t * 6.0)
        cloud_t = t
    elif phase == "hold":
        pulse = 0.0
        cloud_t = 0.0
    else:
        pulse = 0.0
        cloud_t = 0.0
    return (cam.proj, cam.lon, cam.lat, cam.span, phase, pulse, cloud_t)


class MapDrill:
    """Basemap, a real coast, drifting clouds, and a pulsing border."""

    def __init__(self):
        self.earth = build_earth()
        sat = build_plates(self.earth)["satellite"]
        self.plates = {"globe": sat, "regional": sat, "local": None}
        self.plate_cache = RasterCache()
        self.border_cache = SlotCache()

    def _border_path(self, cam: Cam):
        view = view_for(cam, W, H)
        path = skia.Path()
        for ring in (self.earth.rings.get("GRL") or [])[:4]:
            for piece in _ring_paths(np.asarray(ring, np.float64), view):
                if len(piece) < 3:
                    continue
                path.moveTo(piece[0][0], piece[0][1])
                for x, y in piece[1:]:
                    path.lineTo(x, y)
                path.close()
        return path

    def render(self, t: float, cache: bool) -> np.ndarray:
        cam = cam_at(t)
        phase = classify(t)
        key = (cam.proj, cam.lon, cam.lat, cam.span)

        def plate():
            return paint_lod(cam, W, H, self.plates, 1.0, cam.span, cam.span)

        img = self.plate_cache.take(key, plate) if cache else plate()
        rgba = np.dstack([img, np.full((H, W), 255, np.uint8)])
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        cloud_t = t if phase == "anim" else 0.0
        draw_clouds(canvas, cloud_t, 1.0, W, H, alpha=0.35)
        path = self.border_cache.take(key, lambda: self._border_path(cam)) if cache else self._border_path(cam)
        pulse = math.sin(t * 6.0) if phase == "anim" else 0.0
        alpha = int(180 + round(28 * pulse))
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4.0)
        pen.setColor(skia.ColorSetARGB(alpha, 255, 220, 80))
        canvas.drawPath(path, pen)
        bgra = surface.makeImageSnapshot().toarray()
        return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])


def max_diff(a: np.ndarray, b: np.ndarray) -> int:
    if a.shape != b.shape:
        return 255
    return int(np.max(np.abs(a.astype(np.int16) - b.astype(np.int16))))


def max_diff_list(got, ref) -> int:
    if len(got) != len(ref):
        return 255
    worst = 0
    for a, b in zip(got, ref):
        worst = max(worst, max_diff(a, b))
    return worst


def _render_chunk(times: list[float]) -> list[np.ndarray]:
    show = MapDrill()
    return [show.render(t, cache=False) for t in times]


def prove() -> dict:
    times = segment_times()
    phases = {classify(t) for t in times}
    if phases != {"hold", "pan", "zoom", "anim"}:
        raise SystemExit(f"segment is missing a beat: {phases}")

    show = MapDrill()
    t0 = time.perf_counter()
    ref = [show.render(t, cache=False) for t in times]
    ref_s = time.perf_counter() - t0

    fresh = MapDrill()
    t1 = time.perf_counter()
    cached = [fresh.render(t, cache=True) for t in times]
    cache_s = time.perf_counter() - t1
    cache_diff = max_diff_list(cached, ref)

    t2 = time.perf_counter()
    duped = []
    prev = None
    for t in times:
        state = scene_state(t)
        if prev is not None and state == prev[0]:
            duped.append(prev[1].copy())
            continue
        frame = show.render(t, cache=False)
        duped.append(frame)
        prev = (state, frame)
    dup_s = time.perf_counter() - t2
    dup_diff = max_diff_list(duped, ref)
    # The animated hold must not be treated as frozen.
    anim_states = [scene_state(t) for t in times if classify(t) == "anim"]
    if len(anim_states) >= 2 and anim_states[0] == anim_states[1]:
        dup_diff = 255

    workers = cpu_workers()
    chunks = [times[i::workers] for i in range(workers)]
    t3 = time.perf_counter()
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        parts = pool.map(_render_chunk, chunks)
    par_s = time.perf_counter() - t3
    by_t = {}
    for chunk, frames in zip(chunks, parts):
        for t, frame in zip(chunk, frames):
            by_t[t] = frame
    parallel = [by_t[t] for t in times]
    # Three-worker baseline, same frames.
    three = min(3, workers)
    chunks3 = [times[i::three] for i in range(three)]
    t4 = time.perf_counter()
    with ctx.Pool(three) as pool:
        parts3 = pool.map(_render_chunk, chunks3)
    three_s = time.perf_counter() - t4
    core_diff = max_diff_list(parallel, ref)

    t5 = time.perf_counter()
    pngs = []
    for frame in ref:
        buf = BytesIO()
        Image.fromarray(frame).save(buf, format="PNG")
        buf.seek(0)
        pngs.append(np.asarray(Image.open(buf).convert("RGB")))
    png_s = time.perf_counter() - t5
    t6 = time.perf_counter()
    piped = pipe_rgba_roundtrip(ref)
    pipe_s = time.perf_counter() - t6
    png_diff = max_diff_list(pngs, ref)
    pipe_rgb = [frame[:, :, :3] for frame in piped]
    pipe_diff = max_diff_list(pipe_rgb, ref)

    rows = [
        {
            "speedup": "all CPU cores",
            "frames": len(times),
            "max_pixel_diff": core_diff,
            "time_saved_s": round(three_s - par_s, 3),
            "on": core_diff <= 1,
            "note": f"{workers} workers vs 3, wall {par_s:.2f}s vs {three_s:.2f}s",
        },
        {
            "speedup": "cache basemap and borders",
            "frames": len(times),
            "max_pixel_diff": cache_diff,
            "time_saved_s": round(ref_s - cache_s, 3),
            "on": cache_diff <= 1,
            "note": f"cache {cache_s:.2f}s vs redraw {ref_s:.2f}s, plate hits {fresh.plate_cache.hits}",
        },
        {
            "speedup": "duplicate identical frames",
            "frames": len(times),
            "max_pixel_diff": dup_diff,
            "time_saved_s": round(ref_s - dup_s, 3),
            "on": dup_diff <= 1,
            "note": f"state copy {dup_s:.2f}s vs redraw {ref_s:.2f}s",
        },
        {
            "speedup": "pipe raw RGBA, not PNG",
            "frames": len(times),
            "max_pixel_diff": max(png_diff, pipe_diff),
            "time_saved_s": round(png_s - pipe_s, 3),
            "on": png_diff <= 1 and pipe_diff <= 1,
            "note": f"rgba pipe {pipe_s:.2f}s vs png readback {png_s:.2f}s",
        },
    ]

    # The episode has to pass the same cache and duplicate checks.
    g_times = (
        [2.50, 2.55, 2.60, 2.65]
        + [1.15, 1.35, 1.55, 1.75]
        + [15.40, 15.60, 15.80, 16.05]
        + [5.80, 5.95, 6.10, 6.25]
    )
    off = Episode()
    off.cache_layers = False
    g_ref = [off.render(t) for t in g_times]
    on = Episode()
    on.cache_layers = True
    g_cached = [on.render(t) for t in g_times]
    g_cache = max_diff_list(g_cached, g_ref)
    prev = None
    g_duped = []
    for t, frame in zip(g_times, g_ref):
        state = off.scene_state(t)
        if prev is not None and state == prev[0]:
            g_duped.append(prev[1].copy())
        else:
            g_duped.append(frame)
            prev = (state, frame)
    g_dup = max_diff_list(g_duped, g_ref)
    if g_cache > 1:
        for row in rows:
            if row["speedup"].startswith("cache"):
                row["on"] = False
                row["max_pixel_diff"] = max(row["max_pixel_diff"], g_cache)
                row["note"] += f"; greenland cache diff {g_cache}"
    if g_dup > 1:
        for row in rows:
            if row["speedup"].startswith("duplicate"):
                row["on"] = False
                row["max_pixel_diff"] = max(row["max_pixel_diff"], g_dup)
                row["note"] += f"; greenland dup diff {g_dup}"

    flags = {
        "cores": rows[0]["on"],
        "cache": rows[1]["on"],
        "duplicate": rows[2]["on"],
        "rgba": rows[3]["on"],
        "segmented": True,
    }
    (HERE / "speedup_flags.json").write_text(json.dumps(flags, indent=2) + "\n", encoding="utf-8")
    (HERE / "speedup_report.json").write_text(json.dumps({"rows": rows, "flags": flags}, indent=2) + "\n", encoding="utf-8")
    print(f"{'speedup':<32} {'frames':>6} {'max_diff':>8} {'saved_s':>8} {'on':>4}")
    for row in rows:
        print(
            f"{row['speedup']:<32} {row['frames']:>6} {row['max_pixel_diff']:>8} "
            f"{row['time_saved_s']:>8} {str(row['on']):>4}  {row['note']}"
        )
    if not all(row["on"] for row in rows):
        raise SystemExit("a speedup failed the pixel check and stays off")
    return {"rows": rows, "flags": flags}


if __name__ == "__main__":
    prove()
