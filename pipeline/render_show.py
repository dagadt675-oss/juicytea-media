#!/usr/bin/env python3
"""Render the Greenland vs Africa silent picture.

    python render_show.py --stills
    python render_show.py --video
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from jt.show.greenland import (  # noqa: E402
    CLOCK,
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


def _encode(show: Greenland, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "18", "-preset", "veryfast",
        "-g", "60", "-bf", "2",
        "-force_key_frames", f"expr:eq(n,0)+eq(n,{N - 1})",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-color_range", "tv",
        "-movflags", "+faststart",
        str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frame0 = None
    prev = None
    diffs = []
    band_max = 0
    band_at = []
    try:
        for i in range(N):
            t = i / FPS
            img, hits = show.render(t)
            # Drag is authored at 60 fps and averaged down to the 30 fps file.
            if CLOCK.drag - 0.02 <= t <= CLOCK.drop + 0.5:
                earlier, _earlier_hits = show.render(max(0.0, t - (1.0 / 60.0)))
                img = ((img.astype(np.uint16) + earlier.astype(np.uint16)) // 2).astype(np.uint8)
            if hits:
                band_max = max(band_max, hits)
                if len(band_at) < 8:
                    band_at.append(round(t, 2))
            if i == 0:
                frame0 = img
            if i == N - 1 and frame0 is not None:
                loop = float(np.mean(np.abs(img.astype(np.int16) - frame0.astype(np.int16))))
            if prev is not None:
                diffs.append(float(np.mean(np.abs(img.astype(np.int16) - prev.astype(np.int16)))))
            prev = img
            proc.stdin.write(img.tobytes())
            if i % 30 == 0:
                print(f"frame {i}/{N}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg failed ({code})")
    return {
        "frames": N,
        "duration": DURATION,
        "loop_mean_abs": loop,
        "motion_mean": float(np.mean(diffs)) if diffs else 0.0,
        "motion_min": float(np.min(diffs)) if diffs else 0.0,
        "safe_or_band_hits": band_max,
        "safe_or_band_at": band_at,
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
    show = Greenland()
    cues = cue_payload()
    (OUT / "greenland_cues.json").write_text(json.dumps(cues, indent=2) + "\n", encoding="utf-8")
    words = WORDS if WORDS.exists() else None
    (OUT / "greenland_timeline.json").write_text(
        json.dumps(timeline_payload(words), indent=2) + "\n", encoding="utf-8"
    )
    if args.stills or not args.video:
        still_dir = OUT / "stills"
        still_dir.mkdir(exist_ok=True)
        for t in STILLS:
            img, hits = show.render(t)
            Image.fromarray(img).save(still_dir / f"t{t:05.2f}.png")
            print(f"still {t:.2f} band {hits}", flush=True)
    if args.video:
        stats = _encode(show, OUT / "greenland_africa.mp4")
        (OUT / "encode_stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(stats, indent=2))
        engine = {
            "scale": scale_report(),
            "fourteen": getattr(show, "qc_fourteen", None),
            "pack": getattr(show, "qc_pack", None),
        }
        engine["pass"] = bool(
            engine["scale"]["pass"]
            and (engine["fourteen"] or {}).get("pass")
            and (engine["pack"] or {}).get("pass")
        )
        (OUT / "engine_qc.json").write_text(json.dumps(engine, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(engine, indent=2))
        qa = report(OUT / "greenland_africa.mp4", cues["cues"])
        write_report(OUT / "qa.json", qa)
        motion = motion_per_second(OUT / "greenland_africa.mp4")
        write_report(OUT / "motion_per_second.json", motion)
        print(json.dumps(qa, indent=2))
        print(json.dumps({k: motion[k] for k in ("motion_mean", "seconds_under_1", "event_gap_max", "pass")}, indent=2))
    if args.contact:
        _contact(show, OUT / "contact.jpg")


if __name__ == "__main__":
    main()
