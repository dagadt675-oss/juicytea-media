#!/usr/bin/env python3
"""Render the Greenland vs Africa silent picture.

    python render_show.py --stills
    python render_show.py --video

The video is 1080×1920, CRF 16, with no blur and no frame blend.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from jt.show.greenland import (  # noqa: E402
    DURATION,
    FPS,
    N,
    TAIL1,
    Greenland,
    cue_payload,
    scale_report,
    timeline_payload,
)
from jt.show.qa import motion_per_second, report, write_report  # noqa: E402

OUT = ROOT / "examples" / "greenland"
WORDS = ROOT / "examples" / "greenland" / "words.json"

STILLS = (
    0.00, 1.70, 3.20, 3.90, 4.70, 8.80, 12.90, 16.40,
    18.60, 20.50, 21.40, 23.00, 24.90, 27.20, 29.50,
    32.20, 34.90, 36.30, 40.20, 41.80, TAIL1,
)


def _ffmpeg_cmd(path: Path, frames: int) -> list[str]:
    return [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "16", "-preset", "medium",
        "-g", "60", "-bf", "2",
        "-force_key_frames", f"expr:eq(n,0)+eq(n,{frames - 1})",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-color_range", "tv",
        "-movflags", "+faststart",
        str(path),
    ]


def _encode_range(spec: tuple[int, int, str]) -> tuple[str, dict | None, dict | None]:
    """Render [start, end) to an mp4. Sharp frames, no blend."""
    start, end, path = spec
    show = Greenland()
    cmd = _ffmpeg_cmd(Path(path), end - start)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(start, end):
            img, _hits = show.render(i / FPS)
            proc.stdin.write(img.tobytes())
            if (i - start) % 30 == 0:
                print(f"frame {i}/{N}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg failed ({code}) on {path}")
    return path, getattr(show, "qc_fourteen", None), getattr(show, "qc_pack", None)


def _read_frame(path: Path, index: int) -> np.ndarray:
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", f"select=eq(n\\,{index})", "-vframes", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    frame = 1080 * 1920 * 3
    if len(raw) < frame:
        raise RuntimeError(f"short read of frame {index} from {path}")
    return np.frombuffer(raw[:frame], np.uint8).reshape((1920, 1080, 3))


def _encode(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    workers = min(4, multiprocessing.cpu_count())
    edges = [int(round(i * N / workers)) for i in range(workers + 1)]
    tmp = path.parent / "_v4_seg"
    tmp.mkdir(parents=True, exist_ok=True)
    specs = [(edges[i], edges[i + 1], str(tmp / f"part_{i:02d}.mp4")) for i in range(workers) if edges[i] < edges[i + 1]]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        packed = pool.map(_encode_range, specs)
    parts = [row[0] for row in packed]
    listing = tmp / "list.txt"
    listing.write_text(
        "".join(f"file '{Path(part).resolve()}'\n" for part in parts),
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", "-movflags", "+faststart", str(path)],
        check=True,
    )
    frame0 = _read_frame(path, 0)
    last = _read_frame(path, N - 1)
    loop = float(np.mean(np.abs(last.astype(np.int16) - frame0.astype(np.int16))))
    fourteen = next((row[1] for row in packed if row[1]), None)
    pack = next((row[2] for row in packed if row[2]), None)
    return {
        "frames": N,
        "duration": DURATION,
        "width": int(frame0.shape[1]),
        "height": int(frame0.shape[0]),
        "crf": 16,
        "blur": False,
        "loop_mean_abs": loop,
        "fourteen": fourteen,
        "pack": pack,
    }


def _contact(show: Greenland, path: Path):
    cols = 8
    thumb_w, thumb_h = 135, 240
    times = [i * 3 for i in range(int(DURATION // 3) + 1)]
    rows = math.ceil(len(times) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (8, 10, 16))
    for i, t in enumerate(times):
        img, _ = show.render(min(t, TAIL1))
        thumb = Image.fromarray(img).resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        sheet.paste(thumb, ((i % cols) * thumb_w, (i // cols) * thumb_h))
    sheet.save(path)
    print("contact", path, len(times))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--contact", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    show = None
    cues = cue_payload()
    (OUT / "greenland_cues.json").write_text(json.dumps(cues, indent=2) + "\n", encoding="utf-8")
    words = WORDS if WORDS.exists() else None
    (OUT / "greenland_timeline.json").write_text(
        json.dumps(timeline_payload(words), indent=2) + "\n", encoding="utf-8"
    )
    if args.stills or not args.video:
        show = Greenland()
        still_dir = OUT / "stills"
        still_dir.mkdir(exist_ok=True)
        for t in STILLS:
            img, hits = show.render(t)
            Image.fromarray(img).save(still_dir / f"t{t:05.2f}.png")
            print(f"still {t:.2f} band {hits}", flush=True)
    if args.video:
        stats = _encode(OUT / "greenland_africa_v4_retime.mp4")
        (OUT / "encode_stats_v4.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(stats, indent=2))
        engine = {
            "scale": scale_report(),
            "fourteen": stats.get("fourteen"),
            "pack": stats.get("pack"),
        }
        engine["pass"] = bool(
            engine["scale"]["pass"]
            and (engine["fourteen"] or {}).get("pass")
            and (engine["pack"] or {}).get("pass")
        )
        (OUT / "engine_qc_v4.json").write_text(json.dumps(engine, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(engine, indent=2))
        video = OUT / "greenland_africa_v4_retime.mp4"
        qa = report(video, cues["cues"])
        write_report(OUT / "qa_v4.json", qa)
        motion = motion_per_second(video)
        write_report(OUT / "motion_v4.json", motion)
        print(json.dumps(qa, indent=2))
        print(json.dumps({k: motion[k] for k in ("motion_mean", "seconds_under_1", "event_gap_max", "pass")}, indent=2))
    if args.contact:
        if show is None:
            show = Greenland()
        _contact(show, OUT / "contact.jpg")


if __name__ == "__main__":
    main()
