"""Render speedups. Each one is optional and must stay pixel-identical.

A layer cache stores a basemap or a border path only while its key is
unchanged. A new camera or a new lighting/animation parameter misses.
Frames are copied only when the caller says the whole scene state matches.
RGBA is piped to FFmpeg. Segments stay separate encodes.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np


def cpu_workers() -> int:
    """One worker per core. The old default was 3."""
    return max(1, os.cpu_count() or 1)


class RasterCache:
    """One raster. Any key change drops it."""

    def __init__(self):
        self.key = None
        self.image: np.ndarray | None = None
        self.hits = 0
        self.misses = 0

    def take(self, key, build):
        if self.key == key and self.image is not None:
            self.hits += 1
            return self.image
        self.misses += 1
        image = np.ascontiguousarray(build())
        self.image = image
        self.key = key
        return image

    def clear(self) -> None:
        self.key = None
        self.image = None


class SlotCache:
    """One built object, usually a border path. Invalidated when the key changes."""

    def __init__(self):
        self.key = None
        self.value = None
        self.hits = 0
        self.misses = 0

    def take(self, key, build):
        if self.key == key and self.value is not None:
            self.hits += 1
            return self.value
        self.misses += 1
        self.value = build()
        self.key = key
        return self.value


def same_state(a, b) -> bool:
    return a == b


def rgba_of(rgb: np.ndarray) -> np.ndarray:
    """Lossless RGB plus opaque alpha. No colour rounding."""
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("rgba_of expects uint8 RGB")
    alpha = np.full(rgb.shape[:2], 255, np.uint8)
    return np.ascontiguousarray(np.dstack([rgb, alpha]))


def encode_segment_rgba(frames_rgb, fps: int, dest: Path, crf: int = 16) -> None:
    """Pipe raw RGBA. The x264 settings are the show encode, unchanged."""
    if not frames_rgb:
        raise ValueError("empty segment")
    h, w = frames_rgb[0].shape[:2]
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
        "-r", str(fps), "-i", "-",
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", "veryfast",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for rgb in frames_rgb:
            proc.stdin.write(rgba_of(rgb).tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg failed {code}")


def pipe_rgba_roundtrip(frames_rgb) -> list[np.ndarray]:
    """Send RGBA through FFmpeg as raw video and read it back. No encoder."""
    if not frames_rgb:
        return []
    h, w = frames_rgb[0].shape[:2]
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
        "-r", "30", "-i", "-",
        "-an", "-f", "rawvideo", "-pix_fmt", "rgba", "-",
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    payload = b"".join(rgba_of(rgb).tobytes() for rgb in frames_rgb)
    out, _err = proc.communicate(payload)
    if proc.returncode != 0:
        raise RuntimeError("rgba pipe failed")
    frame_bytes = w * h * 4
    got = []
    for i in range(len(frames_rgb)):
        chunk = out[i * frame_bytes:(i + 1) * frame_bytes]
        if len(chunk) != frame_bytes:
            raise RuntimeError("short rgba pipe")
        got.append(np.frombuffer(chunk, np.uint8).reshape(h, w, 4).copy())
    return got
