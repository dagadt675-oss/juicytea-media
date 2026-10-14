#!/usr/bin/env python3
"""Re-render both projection morphs with the convex silhouette. The rest is v9.

The outline is clipped on every blended frame, so the whole morph is
replaced: frames 211-284 on the way in, and frames 397-483 on the way out.
"""

from __future__ import annotations

import multiprocessing
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.greenland_v5 import FPS, H, W, Episode, camera_channels  # noqa: E402

HERE = Path(__file__).resolve().parent
V9 = HERE / "greenland_africa_v9.mp4"
V10 = HERE / "greenland_africa_v10.mp4"
GOP0 = 0
GOP1 = 500


def _needs_new(frame: int) -> bool:
    w = camera_channels(frame / FPS)[0]
    return 0.004 < w < 0.996


def _decode(i0: int, i1: int, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(V9),
        "-vf", f"trim=start_frame={i0}:end_frame={i1},setpts=PTS-STARTPTS",
        "-f", "rawvideo", "-pix_fmt", "rgb24", str(dest),
    ]
    subprocess.run(cmd, check=True)
    expected = (i1 - i0) * W * H * 3
    if dest.stat().st_size != expected:
        raise SystemExit(f"{dest} has {dest.stat().st_size} bytes, expected {expected}")


def _render_range(i0: int, i1: int, dest: str) -> str:
    show = Episode()
    show.cache_layers = False
    path = Path(dest)
    with path.open("wb") as handle:
        for frame in range(i0, i1):
            handle.write(show.render(frame / FPS).tobytes())
            if frame % 6 == 0:
                print(f"rendered {frame}", flush=True)
    print("wrote", path, path.stat().st_size, flush=True)
    return dest


def _runs(frames: list[int]) -> list[tuple[int, int]]:
    runs = []
    start = prev = frames[0]
    for frame in frames[1:]:
        if frame != prev + 1:
            runs.append((start, prev + 1))
            start = frame
        prev = frame
    runs.append((start, prev + 1))
    return runs


def _assemble() -> None:
    tmp = HERE / "_v10_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    decoded = tmp / "gop.rgb"
    print("decoding v9 frames", GOP0, GOP1, flush=True)
    _decode(GOP0, GOP1, decoded)
    new_frames = [i for i in range(GOP0, GOP1) if _needs_new(i)]
    runs = _runs(new_frames)
    print("runs", runs, flush=True)
    jobs = []
    for run_i, (i0, i1) in enumerate(runs):
        workers = min(4, i1 - i0)
        edges = [i0 + (i1 - i0) * k // workers for k in range(workers + 1)]
        for k in range(workers):
            jobs.append((edges[k], edges[k + 1], str(tmp / f"morph_{run_i}_{k:02d}.rgb")))
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(4) as pool:
        pool.starmap(_render_range, jobs)
    gop = np.fromfile(decoded, dtype=np.uint8).reshape((GOP1 - GOP0, H, W, 3))
    for run_i, (i0, i1) in enumerate(runs):
        chunks = sorted((tmp).glob(f"morph_{run_i}_*.rgb"))
        morph = np.concatenate([
            np.fromfile(part, dtype=np.uint8).reshape((-1, H, W, 3)) for part in chunks
        ])
        if len(morph) != i1 - i0:
            raise SystemExit(f"run {run_i} has {len(morph)} frames, expected {i1 - i0}")
        gop[i0:i1] = morph
    raw = tmp / "middle.rgb"
    gop.tofile(raw)
    del gop
    middle = tmp / "middle.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", str(raw),
        "-an",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-video_track_timescale", "15360",
        "-movflags", "+faststart", str(middle),
    ], check=True)
    tail = tmp / "tail.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{GOP1 / FPS:.6f}", "-i", str(V9), "-an", "-c", "copy", str(tail)],
        check=True,
    )
    listing = tmp / "list.txt"
    listing.write_text(f"file '{middle}'\nfile '{tail}'\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(V10)],
        check=True,
    )
    print("wrote", V10, V10.stat().st_size, "runs", runs, flush=True)


if __name__ == "__main__":
    _assemble()
