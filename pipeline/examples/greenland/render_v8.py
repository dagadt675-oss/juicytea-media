#!/usr/bin/env python3
"""Replace the globe-to-flat zoom in v7. Everything else stays the v7 picture.

The new frames are the outbound morph only (about 6.62 s to 8.05 s).
They are spliced between v7 keyframes so the rest of the file is copied.
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
V7 = HERE / "greenland_africa_v7.mp4"
V8 = HERE / "greenland_africa_v8.mp4"
# Keyframes in v7 that bracket the zoom: frame 250 (4.167 s) and frame 500 (8.333 s).
GOP0 = 250
GOP1 = 500


def _needs_new(frame: int) -> bool:
    t = frame / FPS
    w = camera_channels(t)[0]
    return t >= 6.5 and 0.004 < w < 0.996


def _decode(i0: int, i1: int, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(V7),
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
            if not _needs_new(frame):
                raise SystemExit(f"render range includes an unchanged frame {frame}")
            handle.write(show.render(frame / FPS).tobytes())
            if frame % 8 == 0:
                print(f"rendered {frame}", flush=True)
    print("wrote", path, path.stat().st_size, flush=True)
    return dest


def _assemble() -> None:
    tmp = HERE / "_v8_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    decoded = tmp / "gop.rgb"
    print("decoding v7 frames", GOP0, GOP1, flush=True)
    _decode(GOP0, GOP1, decoded)
    new_frames = [i for i in range(GOP0, GOP1) if _needs_new(i)]
    if not new_frames:
        raise SystemExit("no morph frames in the gop")
    i0, i1 = new_frames[0], new_frames[-1] + 1
    if new_frames != list(range(i0, i1)):
        raise SystemExit(f"morph frames are not one span: {new_frames[0]}..{new_frames[-1]}")
    workers = min(4, i1 - i0)
    edges = [i0 + (i1 - i0) * k // workers for k in range(workers + 1)]
    jobs = [(edges[k], edges[k + 1], str(tmp / f"morph_{k:02d}.rgb")) for k in range(workers)]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        parts = pool.starmap(_render_range, jobs)
    morph = np.concatenate([
        np.fromfile(part, dtype=np.uint8).reshape((-1, H, W, 3)) for part in parts
    ])
    if len(morph) != i1 - i0:
        raise SystemExit(f"rendered {len(morph)} frames, expected {i1 - i0}")
    gop = np.fromfile(decoded, dtype=np.uint8).reshape((GOP1 - GOP0, H, W, 3))
    gop[i0 - GOP0:i1 - GOP0] = morph
    raw = tmp / "middle.rgb"
    gop.tofile(raw)
    del gop, morph
    middle = tmp / "middle.mp4"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", str(raw),
        "-an",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-video_track_timescale", "15360",
        "-movflags", "+faststart", str(middle),
    ]
    subprocess.run(cmd, check=True)
    head = tmp / "head.mp4"
    tail = tmp / "tail.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(V7), "-frames:v", str(GOP0), "-an", "-c", "copy", str(head)],
        check=True,
    )
    # Frame 500 is a keyframe. -ss before -i keeps the copy on that frame.
    start = GOP1 / FPS
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.6f}", "-i", str(V7), "-an", "-c", "copy", str(tail)],
        check=True,
    )
    listing = tmp / "list.txt"
    listing.write_text(
        f"file '{head}'\nfile '{middle}'\nfile '{tail}'\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(V8)],
        check=True,
    )
    print("wrote", V8, V8.stat().st_size, "new frames", i0, i1, flush=True)


if __name__ == "__main__":
    _assemble()
