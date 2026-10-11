#!/usr/bin/env python3
"""Segmented silent proof of the Märket opening plus the pencil redraw.

    python3 examples/market/render_proof.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.cues import lint_gaps  # noqa: E402
from jt.show.geoglobe import FPS, Episode, cue_list, load_episode, loop_step_ok  # noqa: E402
from jt.show.qa import motion_per_second, report, write_report  # noqa: E402

HERE = Path(__file__).resolve().parent
SPEC = HERE / "market.json"


def _encode_range(show: Episode, i0: int, i1: int, path: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
        "-movflags", "+faststart", str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(i0, i1):
            frame = show.render(i / FPS)
            proc.stdin.write(frame.tobytes())
            if i % 30 == 0:
                print(f"frame {i}/{show.frames}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code} on {path.name}")


def _concat(parts: list[Path], dest: Path) -> None:
    listing = dest.with_suffix(".txt")
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)],
        check=True,
    )


def _contact(show: Episode, path: Path) -> None:
    cols = 6
    thumb_w, thumb_h = 180, 320
    times = [i * (show.duration / 11) for i in range(12)]
    rows = 2
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (8, 10, 16))
    for i, t in enumerate(times):
        img = show.render(min(t, (show.frames - 1) / FPS))
        thumb = Image.fromarray(img).resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        sheet.paste(thumb, ((i % cols) * thumb_w, (i // cols) * thumb_h))
    sheet.save(path, quality=86)
    print("contact", path)


def main() -> None:
    spec = load_episode(SPEC)
    show = Episode(spec)
    cues = cue_list(spec)
    worst, bad = lint_gaps(cues, spec["duration"], 2.0)
    if bad:
        raise SystemExit(f"cue gaps {bad}")
    if not loop_step_ok(show):
        raise SystemExit("loop step does not match the opening")
    (HERE / "market_cues.json").write_text(json.dumps({"cues": cues, "duration": spec["duration"]}, indent=2) + "\n")
    ranges = [(0, 240), (240, 480), (480, show.frames)]
    parts = []
    for i0, i1 in ranges:
        part = HERE / f"_part_{i0}_{i1}.mp4"
        _encode_range(show, i0, i1, part)
        parts.append(part)
    dest = HERE / "market_proof.mp4"
    _concat(parts, dest)
    for part in parts:
        part.unlink(missing_ok=True)
    qa = report(dest, cues)
    write_report(HERE / "qa.json", qa)
    motion = motion_per_second(dest)
    write_report(HERE / "motion_per_second.json", motion)
    _contact(show, HERE / "contact.jpg")
    print(json.dumps({
        "structural_motion_mean": qa.get("structural_motion_mean"),
        "structural_event_gap_max": qa.get("structural_event_gap_max"),
        "structural_pass": qa.get("structural_pass"),
        "seconds_under_1": motion.get("seconds_under_1"),
        "cue_gap": worst,
        "loop": loop_step_ok(show),
    }, indent=2))


if __name__ == "__main__":
    main()
