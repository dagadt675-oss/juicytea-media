#!/usr/bin/env python3
"""Render an inclusive-exclusive frame span of the current episode to an mp4."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.fast_render import rgba_of  # noqa: E402
from jt.show.greenland_v5 import FPS, H, W, Episode  # noqa: E402


def main() -> None:
    i0, i1 = int(sys.argv[1]), int(sys.argv[2])
    dest = Path(sys.argv[3])
    show = Episode()
    show.cache_layers = False
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-an",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1",
        "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-video_track_timescale", "15360",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(i0, i1):
            proc.stdin.write(rgba_of(show.render(i / FPS)).tobytes())
            if i % 40 == 0:
                print(f"span {i0}-{i1} frame {i}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    print("wrote", dest, dest.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
