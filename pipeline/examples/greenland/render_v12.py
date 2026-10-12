#!/usr/bin/env python3
"""Re-render the spans v12 changes. The rest is v11, cut on keyframes."""

from __future__ import annotations

import multiprocessing
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.greenland_v5 import FPS, H, W, Episode  # noqa: E402

HERE = Path(__file__).resolve().parent
V11 = HERE / "greenland_africa_v12.mp4"
V12 = HERE / "greenland_africa_v12b.mp4"

# Second pass. Joins, the copy entrance, and the sticker that was popping back on.
RANGES = (
    (200, 250),
    (1680, 1750),
)
# Keyframe-aligned decode/encode windows that contain those ranges.
GOPS = (
    (0, 250),
    (250, 500),
    (1000, 1250),
    (1500, 1750),
    (1750, 2000),
    (2000, 2250),
    (2250, 2500),
    (2750, 3000),
    (3000, 3146),
)
# Untouched keyframe spans, copied. (start_frame, end_frame, seek_seconds)
COPIES = (
    (500, 1000, "8.333333"),
    (1250, 1500, "20.833333"),
    (2500, 2750, "41.666667"),
)


def _decode(i0: int, i1: int, dest: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(V11),
        "-vf", f"trim=start_frame={i0}:end_frame={i1},setpts=PTS-STARTPTS",
        "-f", "rawvideo", "-pix_fmt", "rgb24", str(dest),
    ], check=True)
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
            if frame % 8 == 0:
                print(f"rendered {frame}", flush=True)
    print("wrote", path, path.stat().st_size, flush=True)
    return dest


def _encode(raw: Path, dest: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", str(raw),
        "-an",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-g", "250", "-keyint_min", "250", "-sc_threshold", "0",
        "-video_track_timescale", "15360",
        "-movflags", "+faststart", str(dest),
    ], check=True)


def _copy(seek: str, frames: int, dest: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", seek, "-i", str(V11),
        "-frames:v", str(frames), "-an", "-c", "copy", str(dest),
    ], check=True)
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(dest),
    ], text=True).strip()
    if int(probe) != frames:
        raise SystemExit(f"{dest.name} has {probe} frames, expected {frames}")


def _assemble() -> None:
    tmp = HERE / "_v12_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    if not os.environ.get("SKIP_RENDER"):
        jobs = []
        for i0, i1 in RANGES:
            workers = min(4, max(1, (i1 - i0) // 12))
            edges = [i0 + (i1 - i0) * k // workers for k in range(workers + 1)]
            for k in range(workers):
                jobs.append((edges[k], edges[k + 1], str(tmp / f"new_{i0}_{k:02d}.rgb")))
        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(4) as pool:
            pool.starmap(_render_range, jobs)

    encoded = {}
    touched = []
    for g0, g1 in GOPS:
        if any(i1 > g0 and i0 < g1 for i0, i1 in RANGES):
            touched.append((g0, g1))
            continue
        # An untouched span is copied, so it is not compressed again.
        seek = f"{g0 / FPS:.6f}"
        dest = tmp / f"gop_{g0}.mp4"
        _copy(seek, g1 - g0, dest)
        encoded[g0] = dest
    for g0, g1 in touched:
        decoded = tmp / f"gop_{g0}.rgb"
        print("decoding", g0, g1, flush=True)
        _decode(g0, g1, decoded)
        gop = np.fromfile(decoded, dtype=np.uint8).reshape((g1 - g0, H, W, 3))
        for i0, i1 in RANGES:
            if i1 <= g0 or i0 >= g1:
                continue
            a, b = max(i0, g0), min(i1, g1)
            chunks = sorted(tmp.glob(f"new_{i0}_*.rgb"))
            rendered = np.concatenate([
                np.fromfile(part, dtype=np.uint8).reshape((-1, H, W, 3)) for part in chunks
            ])
            if len(rendered) != i1 - i0:
                raise SystemExit(f"patch {i0}:{i1} rendered {len(rendered)}")
            gop[a - g0:b - g0] = rendered[a - i0:b - i0]
        raw = tmp / f"gop_{g0}_out.rgb"
        gop.tofile(raw)
        del gop
        dest = tmp / f"gop_{g0}.mp4"
        _encode(raw, dest)
        encoded[g0] = dest

    copied = {}
    for start, end, seek in COPIES:
        dest = tmp / f"copy_{start}.mp4"
        _copy(seek, end - start, dest)
        copied[start] = dest

    order = [
        encoded[0], encoded[250], copied[500], encoded[1000], copied[1250],
        encoded[1500], encoded[1750], encoded[2000], encoded[2250], copied[2500],
        encoded[2750], encoded[3000],
    ]
    listing = tmp / "list.txt"
    listing.write_text("\n".join(f"file '{path}'" for path in order) + "\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(V12)],
        check=True,
    )
    print("wrote", V12, V12.stat().st_size, flush=True)


if __name__ == "__main__":
    _assemble()
