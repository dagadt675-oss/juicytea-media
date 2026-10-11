"""Render the silent plane-seat Short in cached segments."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WHATIF = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parent
for item in (str(WHATIF), str(ROOT)):
    if item not in sys.path:
        sys.path.insert(0, item)

from engine.segments import plan_segments  # noqa: E402
from plane_seat.engine.clock import (  # noqa: E402
    DURATION,
    FPS,
    FRAME_COUNT,
    HEIGHT,
    ITSSCALE,
    WIDTH,
    frame_time,
    resolved_spec,
    sfx_cues,
)
from plane_seat.engine.overlay import composite  # noqa: E402

BLENDER = Path.home() / "apps/blender-4.5.9-linux-x64/blender"
BUILD = ROOT / "engine" / "build.py"
CACHE = Path("/tmp/plane_seat_cache")
OUT = ROOT / "out"


def _render_beauty(frames, scale, force):
    segments = []
    pending = []
    for frame in frames:
        directory = CACHE / "beauty"
        directory.mkdir(parents=True, exist_ok=True)
        png = directory / f"f_{frame:04d}.png"
        if png.exists() and png.stat().st_size > 1000 and not force:
            continue
        pending.append(frame)
    if not pending:
        return CACHE / "beauty"
    job = {"scale": scale, "frames": pending, "out": str(CACHE / "beauty"), "force": force}
    # One Blender process. Segment folders below are the cache key for beats.
    path = CACHE / "job.json"
    path.write_text(json.dumps(job))
    subprocess.check_call([str(BLENDER), "--background", "--python", str(BUILD), "--", str(path)])
    return CACHE / "beauty"


def _segment_dirs(scale):
    spec = resolved_spec()
    segments = plan_segments(spec, min_seconds=2.0, max_seconds=5.0, handles=1)
    (OUT / "segments.json").write_text(json.dumps(segments, indent=2))
    return segments


def _composite(frames):
    from PIL import Image

    final = OUT / "frames"
    final.mkdir(parents=True, exist_ok=True)
    for frame in frames:
        src = CACHE / "beauty" / f"f_{frame:04d}.png"
        dest = final / f"f_{frame:04d}.png"
        if not src.exists():
            raise SystemExit(f"missing beauty {src}")
        image = composite(Image.open(src), frame_time(frame))
        if image.size != (WIDTH, HEIGHT):
            image = image.resize((WIDTH, HEIGHT))
        image.save(dest)
    return final


def _encode(final, dest):
    raw = dest.with_name(dest.stem + "_30fps.mp4")
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-start_number", "1",
            "-i", str(final / "f_%04d.png"), "-frames:v", str(FRAME_COUNT),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "medium", "-movflags", "+faststart", "-an", str(raw),
        ]
    )
    subprocess.check_call(
        ["ffmpeg", "-y", "-itsscale", f"{ITSSCALE:.12f}", "-i", str(raw), "-c", "copy", str(dest)]
    )


def _contact(final, dest):
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(str(WHATIF / "scale_journey/assets/fonts/Anton-Regular.ttf"), 28)
    times = [i * 2.5 for i in range(int(DURATION // 2.5) + 1)]
    thumbs = []
    for t in times:
        frame = max(1, min(FRAME_COUNT, int(round(t / DURATION * FRAME_COUNT)) + 1))
        im = Image.open(final / f"f_{frame:04d}.png").convert("RGB")
        im.thumbnail((270, 480))
        thumbs.append((t, im))
    cols = 7
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270, rows * 520), (12, 12, 14))
    draw = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(thumbs):
        c, r = i % cols, i // cols
        sheet.paste(im, (c * 270, r * 520))
        draw.text((c * 270 + 8, r * 520 + 486), f"{t:05.2f}s", fill=(255, 220, 160), font=font)
    sheet.save(dest, quality=90)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", default="")
    parser.add_argument("--scale", type=int, default=100)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--beauty-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sfx_cues.json").write_text(json.dumps(sfx_cues(), indent=2))
    if args.frames:
        frames = [int(x) for x in args.frames.split(",") if x]
    else:
        frames = list(range(1, FRAME_COUNT + 1))
        _segment_dirs(args.scale)
    _render_beauty(frames, args.scale, args.force)
    if args.beauty_only:
        return
    final = _composite(frames)
    if frames == list(range(1, FRAME_COUNT + 1)):
        video = Path("/workspace/v")
        video.mkdir(exist_ok=True)
        _encode(final, video / "plane_seat_silent.mp4")
        _contact(final, video / "plane_seat_contact.jpg")
        (video / "plane_seat_sfx_cues.json").write_text((OUT / "sfx_cues.json").read_text())


if __name__ == "__main__":
    main()
