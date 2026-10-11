"""Splice a few rendered stretches into an existing silent master.

Unchanged frames are decoded from the master. Changed frames are rendered
here, including the 60 fps sample the drag motion-blur needs. The result
is one H.264, same length as the master.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from jt.show.greenland import CLOCK, FPS

W, H = 1080, 1920


def _blur_window(t: float) -> bool:
    return CLOCK.drag - 0.02 <= t <= CLOCK.drop + 0.5


def render_range(show, i0: int, i1: int) -> np.ndarray:
    """Frames [i0, i1). Motion blur matches the full-show encoder."""
    n = i1 - i0
    out = np.empty((n, H, W, 3), np.uint8)
    for k, i in enumerate(range(i0, i1)):
        t = i / FPS
        img, _hits = show.render(t)
        if _blur_window(t):
            earlier, _ = show.render(max(0.0, t - (1.0 / 60.0)))
            img = ((img.astype(np.uint16) + earlier.astype(np.uint16)) // 2).astype(np.uint8)
        out[k] = img
        if k % 15 == 0:
            print(f"segment frame {i}", flush=True)
    return out


def _extract_raw(master: Path, i0: int, i1: int, dest: Path) -> None:
    if i1 <= i0:
        dest.write_bytes(b"")
        return
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(master),
        "-vf", f"trim=start_frame={i0}:end_frame={i1},setpts=PTS-STARTPTS",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        str(dest),
    ]
    subprocess.run(cmd, check=True)
    expected = (i1 - i0) * W * H * 3
    got = dest.stat().st_size
    if got != expected:
        raise RuntimeError(f"{dest.name} has {got} bytes, expected {expected}")


def _write_raw(frames: np.ndarray, dest: Path) -> None:
    dest.write_bytes(frames.tobytes())


def splice(master: Path, pieces: list[tuple[int, int, np.ndarray | None]], dest: Path, n: int) -> None:
    """pieces cover [0, n) in order. A None payload means 'decode from master'."""
    cursor = 0
    raws = []
    tmp = dest.parent / "_seg_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for i, (i0, i1, frames) in enumerate(pieces):
        if i0 != cursor or i1 < i0:
            raise RuntimeError(f"splice gap or overlap at {i0}, cursor {cursor}")
        raw = tmp / f"part_{i:02d}.rgb"
        if frames is None:
            _extract_raw(master, i0, i1, raw)
        else:
            if len(frames) != i1 - i0:
                raise RuntimeError(f"piece {i} has {len(frames)} frames, expected {i1 - i0}")
            _write_raw(frames, raw)
        raws.append(raw)
        cursor = i1
    if cursor != n:
        raise RuntimeError(f"splice ended at {cursor}, expected {n}")
    combined = tmp / "combined.rgb"
    with combined.open("wb") as out:
        for raw in raws:
            with raw.open("rb") as fh:
                while True:
                    chunk = fh.read(8 * 1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
    expected = n * W * H * 3
    if combined.stat().st_size != expected:
        raise RuntimeError(f"combined size {combined.stat().st_size} != {expected}")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", str(combined),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "18", "-preset", "veryfast",
        "-g", "60", "-bf", "2",
        "-force_key_frames", f"expr:eq(n,0)+eq(n,{n - 1})",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-color_range", "tv",
        "-movflags", "+faststart",
        str(dest),
    ]
    subprocess.run(cmd, check=True)
    for raw in raws:
        raw.unlink(missing_ok=True)
    combined.unlink(missing_ok=True)
