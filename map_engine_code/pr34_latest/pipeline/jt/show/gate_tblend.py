"""
Juicy Tea Map-Shorts Engine — Mandatory 7-Point Pre-Delivery QC Gate (Rule 11 & Section 10).
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import json
import re
import subprocess
import tempfile
import numpy as np
from .camera import FPS


def run_ffmpeg_tblend_yavg(mp4_path: str | Path) -> List[float]:
    """
    Executes Section 10 mandatory pipeline:
    ffmpeg -i final.mp4 -vf "tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=yavg.txt" -f null -
    """
    mp4_path = Path(mp4_path)
    if not mp4_path.exists():
        raise FileNotFoundError(f"Encoded MP4 not found: {mp4_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        yavg_file = Path(tmpdir) / "yavg.txt"
        vf_expr = (
            f"tblend=all_mode=difference,signalstats,"
            f"metadata=print:key=lavfi.signalstats.YAVG:file='{yavg_file.as_posix()}'"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(mp4_path), "-vf", vf_expr, "-f", "null", "-",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        raw = yavg_file.read_text(encoding="utf-8")
        vals = [
            float(m.group(1))
            for m in re.finditer(r"lavfi\.signalstats\.YAVG=([0-9.]+)", raw)
        ]
    if len(vals) < 2:
        raise RuntimeError("Failed to extract YAVG series from ffmpeg tblend output.")
    return vals


def compute_loop_seam_yavg(mp4_path: str | Path) -> float:
    """Measures exact tblend YAVG difference between the LAST frame and Frame 0 (must be <= 1.0)."""
    mp4_path = Path(mp4_path)
    with tempfile.TemporaryDirectory() as tmpdir:
        first_png = Path(tmpdir) / "frame_0000.png"
        last_png = Path(tmpdir) / "frame_last.png"
        yavg_file = Path(tmpdir) / "loop_yavg.txt"

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp4_path), "-frames:v", "1", str(first_png)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-sseof", "-0.05", "-i", str(mp4_path), "-update", "1", str(last_png)],
            check=True, capture_output=True,
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(last_png), "-i", str(first_png),
            "-filter_complex",
            f"[0:v][1:v]concat=n=2:v=1:a=0,tblend=all_mode=difference,signalstats,"
            f"metadata=print:key=lavfi.signalstats.YAVG:file='{yavg_file.as_posix()}'",
            "-f", "null", "-",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        raw = yavg_file.read_text(encoding="utf-8")
        vals = [float(m.group(1)) for m in re.finditer(r"lavfi\.signalstats\.YAVG=([0-9.]+)", raw)]
        return float(vals[-1]) if vals else 999.0


def evaluate_delivery_gate(
    mp4_path: str | Path,
    motion_lint_report: Dict,
    event_lint_report: Dict,
    local_grid_pops: int = 0,
    ghost_coast_errors: int = 0,
    spike_noise_floor: float = 1.5,
    dead_window_floor: float = 0.05,
) -> Dict:
    """Enforces all 7 pre-delivery gates from Section 10."""
    d = np.asarray(run_ffmpeg_tblend_yavg(mp4_path), dtype=np.float64)
    n = len(d)

    spikes = []
    for i in range(n):
        lo = max(0, i - 6)
        hi = min(n, i + 7)
        neighbors = np.concatenate([d[lo:i], d[i + 1:hi]])
        local_med = float(np.median(neighbors)) if len(neighbors) > 0 else 0.0
        if d[i] > spike_noise_floor and d[i] > 5.0 * max(local_med, 1e-6):
            spikes.append({
                "frame": i + 1,
                "t_s": round((i + 1) / FPS, 3),
                "yavg": round(float(d[i]), 3),
                "local_median": round(local_med, 3),
            })

    loop_step_yavg = compute_loop_seam_yavg(mp4_path)

    win = int(round(0.5 * FPS))
    dead_windows = []
    for start in range(0, max(1, n - win + 1)):
        mean_diff = float(np.mean(d[start:start + win]))
        if mean_diff < dead_window_floor:
            dead_windows.append({
                "start_frame": start,
                "t_s": round(start / FPS, 3),
                "mean_yavg": round(mean_diff, 5),
            })

    passed = (
        len(spikes) == 0
        and loop_step_yavg <= 1.0
        and len(dead_windows) == 0
        and local_grid_pops == 0
        and ghost_coast_errors == 0
        and bool(motion_lint_report.get("ok", False))
        and bool(event_lint_report.get("ok", False))
    )

    report = {
        "passed": passed,
        "frame_count": n + 1,
        "max_yavg_diff": round(float(np.max(d)), 3),
        "spike_count": len(spikes),
        "spikes": spikes,
        "last_frame_loop_step_yavg": round(loop_step_yavg, 3),
        "dead_05s_windows": len(dead_windows),
        "local_grid_pops": local_grid_pops,
        "ghost_coast_errors": ghost_coast_errors,
        "motion_lint": motion_lint_report,
        "event_lint": event_lint_report,
    }
    if not passed:
        raise RuntimeError(f"Delivery QC Gate FAILED:\n{json.dumps(report, indent=2)}")
    return report
