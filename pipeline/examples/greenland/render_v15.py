#!/usr/bin/env python3
"""v15 picture fixes. The v14 clock is unchanged."""

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
SRC = HERE / "greenland_africa_v15.mp4"
OUT = HERE / "greenland_africa_v15f.mp4"

# Slower 1.28× cover so no cell pops.
RANGES = (
    (232, 280),
)
GOPS = tuple((i, min(i + 250, 3146)) for i in range(0, 3146, 250))


def _decode(i0: int, i1: int, dest: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(SRC),
        "-vf", f"trim=start_frame={i0}:end_frame={i1},setpts=PTS-STARTPTS",
        "-f", "rawvideo", "-pix_fmt", "rgb24", str(dest),
    ], check=True)


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
        "ffmpeg", "-y", "-v", "error", "-ss", seek, "-i", str(SRC),
        "-frames:v", str(frames), "-an", "-c", "copy", str(dest),
    ], check=True)
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(dest),
    ], text=True).strip()
    if int(probe) != frames:
        raise SystemExit(f"{dest.name} has {probe} frames, expected {frames}")


def _assemble() -> None:
    tmp = HERE / "_v15_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    if not os.environ.get("SKIP_RENDER"):
        jobs = []
        for i0, i1 in RANGES:
            workers = min(4, max(1, (i1 - i0 + 19) // 40))
            edges = [i0 + (i1 - i0) * k // workers for k in range(workers + 1)]
            for k in range(workers):
                jobs.append((edges[k], edges[k + 1], str(tmp / f"new_{i0}_{k:02d}.rgb")))
        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(4) as pool:
            pool.starmap(_render_range, jobs)

    # The last frame is the decoded opening frame, so the loop seam is that encode.
    open_raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(SRC),
        "-vf", "select=eq(n\\,0)", "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    open_frame = np.frombuffer(open_raw, np.uint8).reshape((H, W, 3)).copy()

    parts = []
    frame_bytes = W * H * 3
    for g0, g1 in GOPS:
        touched = any(i1 > g0 and i0 < g1 for i0, i1 in RANGES)
        dest = tmp / f"gop_{g0}.mp4"
        if not touched:
            _copy(f"{g0 / FPS:.6f}", g1 - g0, dest)
            parts.append(dest)
            continue
        decoded = tmp / f"gop_{g0}.rgb"
        print("decoding", g0, g1, flush=True)
        _decode(g0, g1, decoded)
        gop = np.fromfile(decoded, dtype=np.uint8).reshape((g1 - g0, H, W, 3))
        decoded.unlink(missing_ok=True)
        for i0, i1 in RANGES:
            if i1 <= g0 or i0 >= g1:
                continue
            chunks = sorted(tmp.glob(f"new_{i0}_*.rgb"))
            offset = i0
            seen = 0
            for part in chunks:
                n = part.stat().st_size // frame_bytes
                c0, c1 = offset, offset + n
                offset = c1
                seen += n
                a, b = max(c0, g0), min(c1, g1)
                if a >= b:
                    continue
                with part.open("rb") as handle:
                    handle.seek((a - c0) * frame_bytes)
                    blob = handle.read((b - a) * frame_bytes)
                gop[a - g0:b - g0] = np.frombuffer(blob, np.uint8).reshape((b - a, H, W, 3))
            if seen != i1 - i0:
                raise SystemExit(f"patch {i0}:{i1} rendered {seen}")
        if g1 == 3146:
            gop[-1] = open_frame
        raw = tmp / f"gop_{g0}_out.rgb"
        gop.tofile(raw)
        del gop
        _encode(raw, dest)
        raw.unlink(missing_ok=True)
        parts.append(dest)

    listing = tmp / "list.txt"
    listing.write_text("\n".join(f"file '{path}'" for path in parts) + "\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(OUT)],
        check=True,
    )
    print("wrote", OUT, OUT.stat().st_size, flush=True)


if __name__ == "__main__":
    _assemble()
