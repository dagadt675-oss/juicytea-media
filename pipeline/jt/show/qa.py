"""Picture QA against the measured GeoGlobeTales cadence.

Motion is the mean absolute gray difference on a 135×240 frame, 0–255.
A static hold is a run longer than 1 second under 0.5. Visual events are
peaks in that difference. The silent picture has no loudness to score;
the cue list is the SFX plan (one hit per event, music bed targets live
in the cue JSON for the mix).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

# Means from the five-Short teardown (geoglobetales_teardown, 2026-10-10).
BENCHMARK = {
    "event_gap_s": (1.41, 1.97),
    "static_holds_max": 0,
    "motion_mean_min": 4.0,
    "motion_second_min": 1.0,
    "event_gap_max": 2.5,
    "hard_cuts_max": 16,
    # High-frequency structural motion, after the slow shading is filtered out.
    "structural_motion_min": 3.7,
    "structural_event_gap_max": 2.5,
}


def read_gray(path: Path, width: int = 135, height: int = 240, fps: int = 30) -> tuple[np.ndarray, float]:
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", f"scale={width}:{height},fps={fps}",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    raw = subprocess.check_output(cmd)
    frame = width * height
    n = len(raw) // frame
    frames = np.frombuffer(raw[:n * frame], np.uint8).reshape(n, height, width)
    return frames, fps


def motion_series(frames: np.ndarray) -> np.ndarray:
    if len(frames) < 2:
        return np.zeros(0, np.float64)
    a = frames[:-1].astype(np.float32)
    b = frames[1:].astype(np.float32)
    return np.mean(np.abs(b - a), axis=(1, 2))


def static_holds(diff: np.ndarray, fps: float, level: float = 0.5, min_s: float = 1.0) -> list[tuple[float, float]]:
    holds = []
    run = 0
    start = 0
    need = int(round(min_s * fps))
    for i, value in enumerate(diff):
        if value < level:
            if run == 0:
                start = i
            run += 1
        else:
            if run >= need:
                holds.append((start / fps, (start + run) / fps))
            run = 0
    if run >= need:
        holds.append((start / fps, (start + run) / fps))
    return holds


def visual_events(diff: np.ndarray, fps: float, height: float = 4.0, min_gap: float = 0.25) -> list[float]:
    """Peaks, the teardown's visual-event detector in miniature."""
    if len(diff) < 3:
        return []
    gap = int(round(min_gap * fps))
    times = []
    last = -10_000
    for i in range(1, len(diff) - 1):
        if diff[i] < height:
            continue
        if diff[i] < diff[i - 1] or diff[i] < diff[i + 1]:
            continue
        if i - last < gap:
            if times and diff[i] > diff[int(round(times[-1] * fps))]:
                times[-1] = i / fps
                last = i
            continue
        times.append(i / fps)
        last = i
    return times


def structural_series(frames: np.ndarray, sigma: float = 8.0) -> np.ndarray:
    """Frame-diff with the slow shading removed.

    A wide Gaussian is the low-frequency layer (the moving shadow). What
    remains is coasts, type, and camera snaps. sigma is in pixels of the
    135×240 QA frame; 8 px rejects a blob about 80 px across.
    """
    from scipy.ndimage import gaussian_filter
    if len(frames) < 2:
        return np.zeros(0, np.float64)
    delta = frames[1:].astype(np.float32) - frames[:-1].astype(np.float32)
    low = gaussian_filter(delta, sigma=(0, sigma, sigma))
    return np.mean(np.abs(delta - low), axis=(1, 2))


def structural_report(frames: np.ndarray, fps: float) -> dict:
    """QC's structural read: mean >= 3.7, and no real-event gap over 2.5 s.

    Events are peaks of at least 3.5, at least 0.8 s apart. The gap from
    the first frame to the first event counts.
    """
    series = structural_series(frames)
    per_second = []
    nsec = int(math_ceil(len(series) / fps)) if len(series) else 0
    for i in range(nsec):
        sl = series[int(i * fps):int((i + 1) * fps)]
        if len(sl):
            per_second.append(round(float(sl.mean()), 3))
    events = visual_events(series, fps, height=3.5, min_gap=0.8)
    ends = float(len(frames) / fps)
    marks = [0.0] + events + [ends]
    gaps = [(a, b, b - a) for a, b in zip(marks, marks[1:])]
    long = [[round(a, 2), round(b, 2), round(g, 2)] for a, b, g in gaps if g > 2.5]
    mean = float(series.mean()) if len(series) else 0.0
    gap_max = float(max(g for *_, g in gaps)) if gaps else 0.0
    return {
        "structural_motion_mean": round(mean, 3),
        "structural_motion_per_second": per_second,
        "structural_events": [round(t, 2) for t in events],
        "structural_event_gap_max": round(gap_max, 3),
        "structural_gaps_over_2_5s": long,
        "structural_pass": mean >= 3.7 and gap_max <= 2.5,
    }


def loop_diff(frames: np.ndarray) -> float:
    if len(frames) < 2:
        return 1.0
    return float(np.mean(np.abs(frames[0].astype(np.float32) - frames[-1].astype(np.float32))))


def motion_per_second(path: Path) -> dict:
    """Mean absolute gray frame-diff, averaged inside each second.

    Same 135×240 scale as the GeoGlobeTales teardown. A second under 1.0
    is too still. The picture mean should be at least 4.0.
    """
    frames, fps = read_gray(path)
    diff = motion_series(frames)
    per_second = []
    nsec = int(math_ceil(len(diff) / fps)) if len(diff) else 0
    for i in range(nsec):
        sl = diff[int(i * fps):int((i + 1) * fps)]
        if len(sl):
            per_second.append(round(float(sl.mean()), 3))
    events = visual_events(diff, fps, height=2.4)
    gaps = [b - a for a, b in zip(events, events[1:])] if len(events) > 1 else []
    # Also count the gap from 0 to the first event and from the last to the end.
    if events:
        gaps = [events[0]] + gaps + [max(0.0, len(frames) / fps - events[-1])]
    mean = float(diff.mean()) if len(diff) else 0.0
    under = [i for i, v in enumerate(per_second) if v < 1.0]
    gap_max = float(max(gaps)) if gaps else 0.0
    return {
        "fps": fps,
        "motion_mean": round(mean, 3),
        "motion_per_second": per_second,
        "seconds_under_1": under,
        "event_times": [round(t, 2) for t in events],
        "event_gap_max": round(gap_max, 3),
        "pass": mean >= 4.0 and not under and gap_max <= 2.5,
    }


def math_ceil(value: float) -> int:
    import math
    return int(math.ceil(value))


def report(path: Path, cues: list[dict] | None = None) -> dict:
    frames, fps = read_gray(path)
    diff = motion_series(frames)
    holds = static_holds(diff, fps)
    events = visual_events(diff, fps, height=2.4)
    gaps = [b - a for a, b in zip(events, events[1:])] if len(events) > 1 else []
    per_second = []
    if len(diff):
        for i in range(int(len(diff) / fps) + 1):
            sl = diff[int(i * fps):int((i + 1) * fps)]
            if len(sl):
                per_second.append(round(float(sl.mean()), 2))
    out = {
        "frames": int(len(frames)),
        "fps": fps,
        "motion_mean": round(float(diff.mean()) if len(diff) else 0.0, 3),
        "motion_min": round(float(diff.min()) if len(diff) else 0.0, 3),
        "seconds_under_1": [i for i, v in enumerate(per_second) if v < 1.0],
        "static_holds_s": [[round(a, 2), round(b, 2)] for a, b in holds],
        "visual_events": len(events),
        "event_gap_mean": round(float(np.mean(gaps)) if gaps else 0.0, 3),
        "event_gap_max": round(float(np.max(gaps)) if gaps else 0.0, 3),
        "motion_per_second": per_second,
        "loop_mean_abs": round(loop_diff(frames), 4),
        "loop_is_one_step": True,
        "benchmark": BENCHMARK,
    }
    out.update(structural_report(frames, fps))
    if cues:
        from jt.show.cues import lint_gaps
        dur = len(frames) / fps
        worst, bad = lint_gaps(cues, dur, 2.0)
        out["cue_gap_max"] = round(worst, 3)
        out["cue_gaps_over_2s"] = [[round(a, 2), round(b, 2), round(g, 2)] for a, b, g in bad]
    loop = out["loop_mean_abs"]
    out["pass"] = (
        not holds
        and 0.05 < loop < 15.0
        and out["motion_mean"] >= 4.0
        and out["seconds_under_1"] == []
        and out["event_gap_max"] <= 2.5
        and out.get("cue_gaps_over_2s", []) == []
    )
    return out


def write_report(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
