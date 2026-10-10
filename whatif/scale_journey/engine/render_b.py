"""Render a format B episode. Penny is the full Blender path."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WHATIF = ROOT.parent
for path in (str(ROOT), str(WHATIF)):
    if path not in sys.path:
        sys.path.insert(0, path)

from engine.bformat import resolve_b, timeline_for  # noqa: E402
from engine.compose_b import compose_b  # noqa: E402
from engine.gen_textures import write_all  # noqa: E402
from ui._load import sibling_overlay  # noqa: E402

FONT_PATH = sibling_overlay().SANS
from ui.loop import dissolve_to_frame  # noqa: E402
from ui.outlines import outline  # noqa: E402


def _blender() -> str:
    candidates = [
        Path.home() / "apps/blender-4.5.9-linux-x64/blender",
        Path("/usr/bin/blender"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("blender")
    if found:
        return found
    raise SystemExit("Blender 4.5.9 not found")


def _preview_plate(ep, fr) -> Image.Image:
    w, h = ep.width, ep.height
    img = Image.new("RGB", (w, h), (120, 150, 180))
    draw = ImageDraw.Draw(img)
    # Schematic shaft on the left, penny as a dot that descends.
    draw.rectangle((80, 200, 420, h - 80), fill=(70, 74, 82))
    if ep.raw["preset"] == "penny_fall":
        deck = outline("empire")["deck_m"]
        u = 1.0 - (fr.penny[2] / deck)
        y = int(220 + u * (h - 400))
        draw.ellipse((500, y, 540, y + 24), fill=(190, 120, 70))
    return img


def _contact(frame_dir: Path, fps: int, dest: Path):
    frames = sorted(frame_dir.glob("f_*.png"))
    step = max(1, fps // 2)
    picked = frames[::step]
    thumb_w, thumb_h = 135, 240
    cols = 8
    rows = (len(picked) + cols - 1) // cols
    font = ImageFont.truetype(str(FONT_PATH), 14)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 18)), (12, 12, 14))
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(picked):
        im = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        c, r = i % cols, i // cols
        sheet.paste(im, (c * thumb_w, r * (thumb_h + 18)))
        frame = int(path.stem.split("_")[1])
        draw.text((c * thumb_w + 4, r * (thumb_h + 18) + thumb_h + 1), f"{frame / fps:05.2f}s", fill=(255, 230, 210), font=font)
    sheet.save(dest, quality=90)


def _keys(ep, final_dir: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    fps = ep.fps
    names = {
        0: "00_hook",
    }
    # Payoff frame: first frame of the payoff phase, plus a mid-fall and the street.
    payoff = next(fr.frame for fr in ep.frames if fr.phase == "payoff")
    mid = next(fr.frame for fr in ep.frames if fr.phase == "fall" and fr.speed_mps > ep.notes["terminal_mps"] * 0.5)
    fast = next(fr.frame for fr in ep.frames if fr.phase == "fall" and fr.speed_mps > ep.notes["terminal_mps"] * 0.97)
    names[mid] = "fall_mid"
    names[fast] = "terminal"
    names[payoff] = "payoff"
    names[len(ep.frames) // 5] = "leaving"
    written = []
    for frame, name in list(names.items())[:6]:
        src = final_dir / f"f_{frame:04d}.png"
        if src.exists():
            target = dest / f"key_{name}.png"
            shutil.copyfile(src, target)
            written.append(str(target))
    return written


def render_format_b(args, raw):
    t0 = time.time()
    ep = resolve_b(args.spec)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = timeline_for(ep)
    (out / "timeline.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    (out / "words.json").write_text(json.dumps(doc["words"], indent=2), encoding="utf-8")
    print(f"format B {ep.id} {ep.duration:.2f}s {len(ep.frames)} frames terminal {ep.notes.get('terminal_mph', 0):.2f} mph" if ep.raw["preset"] == "penny_fall" else f"format B {ep.id} {ep.duration:.2f}s")
    if args.timeline_only or ep.raw["preset"] != "penny_fall":
        if ep.raw["preset"] != "penny_fall":
            print("timeline only for this preset (penny is the full render)")
        stats = {"id": ep.id, "seconds": round(time.time() - t0, 2), "frames": len(ep.frames), "rendered": False}
        (out / "render_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        return ep
    frames = ep.frames
    if args.frames:
        wanted = {int(x) for x in args.frames.split(",") if x != ""}
        frames = [fr for fr in ep.frames if fr.frame in wanted]
    final_dir = out / "frames"
    if final_dir.exists() and not args.keep_frames:
        shutil.rmtree(final_dir)
    final_dir.mkdir(parents=True, exist_ok=True)
    if not args.preview:
        textures = write_all(out / "gen")
        empire = outline("empire")
        job = {
            "width": ep.width,
            "height": ep.height,
            "samples": int(args.samples),
            "scale": int(args.scale),
            "lens_mm": float(ep.raw["camera"]["lens_mm"]),
            "deck_m": empire["deck_m"],
            "roof_m": empire["roof_m"],
            "tip_m": empire["height_m"],
            "facade": textures["facade"],
            "out": str(out / "plates"),
            "frames": [
                {"frame": fr.frame, "t": fr.t, "cam": list(fr.cam), "target": list(fr.target), "penny": list(fr.penny)}
                for fr in frames
            ],
        }
        job_path = out / "job_penny.json"
        job_path.write_text(json.dumps(job))
        blender = args.blender or _blender()
        subprocess.check_call([blender, "--background", "--python", str(ROOT / "engine" / "build_b.py"), "--", str(job_path)])
    opening = None
    for fr in frames:
        if args.preview:
            base = _preview_plate(ep, fr)
        else:
            plate = out / "plates" / f"f_{fr.frame:04d}.png"
            base = Image.open(plate).convert("RGB")
            if base.size != (ep.width, ep.height):
                base = base.resize((ep.width, ep.height), Image.Resampling.LANCZOS)
        img = compose_b(base, ep, fr)
        if fr.frame == 0:
            opening = img.copy()
        if fr.dissolve > 0 and opening is not None:
            img = dissolve_to_frame(img, opening, fr.dissolve)
        if fr.frame == ep.frames[-1].frame and opening is not None:
            img = opening.copy()
        img.save(final_dir / f"f_{fr.frame:04d}.png")
    mp4 = out / f"{ep.id}.mp4"
    full = not args.preview and not args.frames and not args.no_video
    if full:
        subprocess.check_call(
            [
                "ffmpeg", "-y",
                "-framerate", str(ep.fps),
                "-start_number", "0",
                "-i", str(final_dir / "f_%04d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709",
                "-color_trc", "bt709",
                "-colorspace", "bt709",
                "-crf", "16",
                "-movflags", "+faststart",
                "-an",
                str(mp4),
            ]
        )
    _contact(final_dir, ep.fps, out / "contact_sheet.jpg")
    keys = _keys(ep, final_dir, out / "keys") if ep.raw["preset"] == "penny_fall" else []
    stats = {
        "id": ep.id,
        "seconds": round(time.time() - t0, 2),
        "frames": len(frames),
        "preview": bool(args.preview),
        "samples": args.samples,
        "mp4": str(mp4) if mp4.exists() else None,
        "terminal_mph": ep.notes.get("terminal_mph"),
        "fall_sec": ep.notes.get("fall_sec"),
        "keys": keys,
    }
    (out / "render_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return ep
