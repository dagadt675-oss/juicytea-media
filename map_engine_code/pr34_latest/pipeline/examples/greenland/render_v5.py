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

from jt.show.fast_render import cpu_workers, rgba_of  # noqa: E402
from jt.show.greenland_v5 import (  # noqa: E402
    FPS,
    H,
    N,
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
        "picture_duration": round(N / FPS, 3),
        "frames": N,
        "fps": FPS,
        "camera": beat_rows(),
        "elements": element_rows(),
    }
    (HERE / "beats_v5.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Greenland vs Africa v5",
        "",
        "The picture is 60 fps. A move starts on the word, eases in-out, then holds. Times below are seconds, so the motion matches the 30 fps staging and is only sampled finer. Holds fill the voiceover.",
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
            "picture_duration": round(N / FPS, 3),
            "fps": FPS,
            "frames": N,
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


def _flags() -> dict:
    path = HERE / "speedup_flags.json"
    if not path.exists():
        raise SystemExit("run prove_speedups.py before the full render")
    return json.loads(path.read_text(encoding="utf-8"))


def _segment(i0: int, i1: int, path: str, duplicate: bool, cache: bool, rgba: bool) -> str:
    show = Episode()
    show.cache_layers = cache
    dest = Path(path)
    pix = "rgba" if rgba else "rgb24"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", pix, "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev = None
    try:
        for i in range(i0, i1):
            t = i / FPS
            if duplicate:
                state = show.scene_state(t)
                if prev is not None and state == prev[0]:
                    proc.stdin.write(prev[1])
                    continue
            rgb = show.render(t)
            raw = rgba_of(rgb).tobytes() if rgba else rgb.tobytes()
            proc.stdin.write(raw)
            if duplicate:
                prev = (state, raw)
            if i % 60 == 0:
                print(f"frame {i}/{N}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    return path


def render_video() -> None:
    flags = _flags()
    frames = N
    workers = cpu_workers() if flags.get("cores") else 3
    tmp = HERE / "_v6_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    edges = [round(i * frames / workers) for i in range(workers + 1)]
    jobs = [
        (edges[i], edges[i + 1], str(tmp / f"part_{i:02d}.mp4"),
         False, False, True)
        for i in range(workers)
    ]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        parts = [Path(p) for p in pool.starmap(_segment, jobs)]
    listing = tmp / "list.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    dest = HERE / "greenland_africa_v6.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)],
        check=True,
    )
    for part in parts:
        part.unlink(missing_ok=True)
    listing.unlink(missing_ok=True)
    print(dest, dest.stat().st_size, "workers", workers, flags, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--video", action="store_true")
    args = parser.parse_args()
    if args.stills:
        write_tables()
        render_stills()
    if args.video:
        render_video()
    if not args.stills and not args.video:
        write_tables()
        print("wrote beat table and cues")


if __name__ == "__main__":
    main()
