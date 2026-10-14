#!/usr/bin/env python3
"""v16 loop fix. The v15 clock is unchanged. 4.63–4.98 s is left as v15.

The last 30 frames ease out onto the opening frame. The last frame is one
step before that frame, not a copy of it. The opening frame is encoded at
the same CRF so the seam is the ease, not a second generation of the picture.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

HERE = Path(__file__).resolve().parent
SRC = HERE / "greenland_africa_v15.mp4"
OUT = HERE / "greenland_africa_v16.mp4"
W, H, FPS = 1080, 1920, 60


def _encode(raw: Path, dest: Path, crf: str) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", str(raw),
        "-an",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-crf", crf, "-preset", "veryfast",
        "-g", "250", "-keyint_min", "250", "-sc_threshold", "0",
        "-video_track_timescale", "15360",
        str(dest),
    ], check=True)


def _decode(i0: int, i1: int, dest: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(SRC),
        "-vf", f"trim=start_frame={i0}:end_frame={i1},setpts=PTS-STARTPTS",
        "-f", "rawvideo", "-pix_fmt", "rgb24", str(dest),
    ], check=True)


def _assemble() -> None:
    tmp = HERE / "_v16_tail"
    tmp.mkdir(parents=True, exist_ok=True)
    _decode(0, 210, tmp / "a.rgb")
    _encode(tmp / "a.rgb", tmp / "a.mp4", "10")
    _decode(210, 250, tmp / "b.rgb")
    _encode(tmp / "b.rgb", tmp / "b.mp4", "16")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{250 / FPS:.6f}", "-i", str(SRC),
        "-frames:v", "2750", "-an", "-c", "copy", str(tmp / "c.mp4"),
    ], check=True)
    _decode(3000, 3146, tmp / "d.rgb")
    frame_bytes = W * H * 3
    tail = np.fromfile(tmp / "d.rgb", np.uint8).reshape((-1, H, W, 3)).astype(np.float32)
    if len(tail) != 146:
        raise SystemExit(f"tail has {len(tail)} frames")
    opening = np.fromfile(tmp / "a.rgb", np.uint8)[:frame_bytes].reshape((H, W, 3)).astype(np.float32)
    # 30 steps. u=0 on frame 3116 (unchanged), u=1 on the frame after the last.
    for n in range(3116, 3146):
        u = (n - 3116) / 30.0
        weight = 1.0 - (1.0 - u) ** 1.65
        tail[n - 3000] = (1.0 - weight) * tail[n - 3000] + weight * opening
    np.clip(tail, 0, 255).astype(np.uint8).tofile(tmp / "d.rgb")
    _encode(tmp / "d.rgb", tmp / "d.mp4", "10")
    listing = tmp / "list.txt"
    parts = [tmp / "a.mp4", tmp / "b.mp4", tmp / "c.mp4", tmp / "d.mp4"]
    listing.write_text("\n".join(f"file '{path.resolve()}'" for path in parts) + "\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(OUT)],
        check=True,
    )
    print("wrote", OUT, OUT.stat().st_size, flush=True)


if __name__ == "__main__":
    _assemble()
