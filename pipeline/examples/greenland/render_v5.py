#!/usr/bin/env python3
"""Stills, then the silent Greenland v5 picture.

    python3 examples/greenland/render_v5.py --stills
    python3 examples/greenland/render_v5.py --video
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.greenland_v5 import (  # noqa: E402
    FPS,
    H,
    T_LAST,
    W,
    CLOCK,
    Episode,
    beat_rows,
    cue_rows,
    element_rows,
)

HERE = Path(__file__).resolve().parent
STILLS = (
    ("00_lie", 0.00),
    ("01_excuse", 6.10),
    ("02_three_by_nine", 14.20),
    ("03_sixteen", 16.60),
    ("04_slide_hold", 23.40),
    ("05_fourteen", 30.50),
    ("06_hi_tiny", 36.10),
    ("07_still_bigger", 44.40),
)


def write_tables() -> None:
    payload = {
        "picture_duration": round(CLOCK.duration, 3),
        "frames": CLOCK.frames,
        "fps": FPS,
        "camera": beat_rows(),
        "elements": element_rows(),
    }
    (HERE / "beats_v5.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Greenland vs Africa v5",
        "",
        "A move starts on the word, eases in-out, then holds. Holds fill the voiceover.",
        "The counter rides the 4.40 s slide from 16× (spoken SIXTEEN) down to 1×.",
        "Fourteen is the tile count, not the slide counter.",
        "",
        "## Camera",
        "",
        "| Word | t | Move | Duration | Hold after |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for row in beat_rows():
        lines.append(
            f"| {row['word']} | {row['t']:.3f} | {row['move']} | {row['duration']:.2f} | {row['hold']:.2f} |"
        )
    lines += [
        "",
        "## Elements",
        "",
        "| Word | t | Move | Duration | Hold after |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for row in element_rows():
        lines.append(
            f"| {row['word']} | {row['t']:.3f} | {row['move']} | {row['duration']:.2f} | {row['hold']:.2f} |"
        )
    lines.append("")
    (HERE / "beats_v5.md").write_text("\n".join(lines), encoding="utf-8")
    cues = cue_rows()
    (HERE / "greenland_v5_cues.json").write_text(
        json.dumps({
            "id": "greenland_africa_v5",
            "picture_duration": round(T_LAST + 1.0 / FPS, 3),
            "fps": FPS,
            "frames": CLOCK.frames,
            "cues": cues,
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def render_stills() -> None:
    from PIL import Image

    show = Episode()
    out = HERE / "stills_v5"
    out.mkdir(parents=True, exist_ok=True)
    for name, t in STILLS:
        frame = show.render(t)
        path = out / f"{name}.png"
        Image.fromarray(frame).save(path)
        print(name, show.qc, flush=True)


def _segment(i0: int, i1: int, path: str) -> str:
    show = Episode()
    dest = Path(path)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(i0, i1):
            proc.stdin.write(show.render(i / FPS).tobytes())
            if i % 30 == 0:
                print(f"frame {i}/{CLOCK.frames}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    return path


def render_video() -> None:
    frames = CLOCK.frames
    workers = 4
    tmp = HERE / "_v5_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    edges = [round(i * frames / workers) for i in range(workers + 1)]
    jobs = [(edges[i], edges[i + 1], str(tmp / f"part_{i:02d}.mp4")) for i in range(workers)]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        parts = [Path(p) for p in pool.starmap(_segment, jobs)]
    listing = tmp / "list.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    dest = HERE / "greenland_africa_v5.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)],
        check=True,
    )
    print(dest, dest.stat().st_size, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args()
    write_tables()
    if args.stills:
        render_stills()
    if args.video:
        render_video()
    if not args.stills and not args.video:
        write_tables()
        print("wrote beat table and cues")


if __name__ == "__main__":
    main()
