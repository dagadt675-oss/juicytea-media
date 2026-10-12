#!/usr/bin/env python3
"""Re-render the fourteen-Greenland exit and the loop tail. The rest is v10."""

from __future__ import annotations

import multiprocessing
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.greenland_v5 import FPS, H, W, Episode  # noqa: E402

HERE = Path(__file__).resolve().parent
V10 = HERE / "greenland_africa_v10.mp4"
V11 = HERE / "greenland_africa_v11.mp4"

# Keyframe-aligned spans. Heads and the middle stay copied.
GOPS = (
    (1750, 2000),
    (3000, 3146),
)
# Frames whose pictures changed.
PATCHES = (
    (1876, 1932),
    (3116, 3146),
)


def _decode(i0: int, i1: int, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(V10),
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


def _encode(raw: Path, dest: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", str(raw),
        "-an",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-g", "250", "-keyint_min", "250",
        "-video_track_timescale", "15360",
        "-movflags", "+faststart", str(dest),
    ], check=True)


def _copy(args: list[str], dest: Path, frames: int) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args, "-an", "-c", "copy", str(dest)], check=True)
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(dest),
    ], text=True).strip()
    if int(probe) != frames:
        raise SystemExit(f"{dest.name} has {probe} frames, expected {frames}")


def _assemble() -> None:
    tmp = HERE / "_v11_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    jobs = []
    for i0, i1 in PATCHES:
        workers = min(4, i1 - i0)
        edges = [i0 + (i1 - i0) * k // workers for k in range(workers + 1)]
        for k in range(workers):
            jobs.append((edges[k], edges[k + 1], str(tmp / f"new_{i0}_{k:02d}.rgb")))
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(4) as pool:
        pool.starmap(_render_range, jobs)

    encoded = []
    for g0, g1 in GOPS:
        decoded = tmp / f"gop_{g0}.rgb"
        print("decoding", g0, g1, flush=True)
        _decode(g0, g1, decoded)
        gop = np.fromfile(decoded, dtype=np.uint8).reshape((g1 - g0, H, W, 3))
        for i0, i1 in PATCHES:
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
        encoded.append(dest)

    head = tmp / "head.mp4"
    mid = tmp / "mid.mp4"
    _copy(["-i", str(V10), "-frames:v", "1750"], head, 1750)
    _copy(["-ss", "33.333333", "-i", str(V10), "-frames:v", "1000"], mid, 1000)
    listing = tmp / "list.txt"
    listing.write_text(
        "\n".join(f"file '{path}'" for path in (head, encoded[0], mid, encoded[1])) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(V11)],
        check=True,
    )
    print("wrote", V11, V11.stat().st_size, flush=True)


if __name__ == "__main__":
    _assemble()
