#!/usr/bin/env python3
"""Render a scale-journey episode.

    python3 whatif/scale_journey/render_episode.py EPISODE.yaml --out DIR

Writes a silent 1080x1920 H.264, timeline.json (for ElevenLabs / karaoke),
a 2 fps contact sheet, and key frames. ``--timeline-only`` skips Blender.
``--preview`` draws schematic plates so timing and UI can be checked quickly.

Blender is invoked the same way the sibling what-if engine does:

    blender --background --python engine/build.py -- job.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.camera import layer_by_id  # noqa: E402
from engine.gen_textures import write_all  # noqa: E402
from engine.overlay import FONT_PATH, compose  # noqa: E402
from engine.preview import plate  # noqa: E402
from engine.spec import (  # noqa: E402
    blender_frames,
    load_raw,
    resolve,
    retime_milestones,
    timeline_document,
)

ASSETS = ROOT / "assets"


def _blender_bin() -> str:
    env = Path(str(shutil.which("blender") or ""))
    candidates = [
        Path.home() / "apps/blender-4.5.9-linux-x64/blender",
        Path("/usr/bin/blender"),
        env,
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return str(candidate)
    raise SystemExit("Blender 4.5.9 not found. Install it or pass --blender.")


def _select_frames(ep, frames_arg, milestone_only, step):
    if frames_arg:
        wanted = {int(x) for x in frames_arg.split(",") if x != ""}
        return [fr for fr in ep.frames if fr.frame in wanted]
    if milestone_only:
        fps = ep.fps
        wanted = {0, len(ep.frames) - 1}
        for m in ep.milestones:
            wanted.add(min(len(ep.frames) - 1, int(round(m.t * fps))))
        return [fr for fr in ep.frames if fr.frame in wanted]
    if step > 1:
        return [fr for fr in ep.frames if fr.frame % step == 0 or fr.frame == len(ep.frames) - 1]
    return list(ep.frames)


def _job_for_layer(ep, layer_id, frames, args, textures):
    layer = layer_by_id(layer_id)
    q = ep.raw["quantity"]
    proxies = []
    for m in ep.milestones:
        if m.proxy in ("", "grain", "marker"):
            continue
        height = m.anchor[2]
        if layer.h_min * 0.2 <= height <= layer.h_max * 1.4:
            proxies.append(
                {
                    "id": m.id,
                    "kind": m.proxy,
                    "height_m": height,
                    "x_m": m.anchor[0],
                    "y_m": m.anchor[1],
                }
            )
    payload_frames = []
    for fr in frames:
        weight = fr.weights.get(layer_id, 0.0)
        if weight < 0.04:
            continue
        from engine.camera import to_bu

        payload_frames.append(
            {
                "frame": fr.frame,
                "weight": weight,
                "cam": list(to_bu(fr.pose_cam, layer.meters_per_bu)),
                "target": list(to_bu(fr.pose_target, layer.meters_per_bu)),
                "h_bu": fr.metrics.height_m / layer.meters_per_bu,
                "r_bu": max(fr.metrics.radius_m, 1e-9) / layer.meters_per_bu,
                "grains": fr.metrics.grains,
                "visual": fr.metrics.visual,
                "param": fr.param,
                "lens_mm": float(ep.raw["camera"]["lens_mm"]),
                "sensor_height_mm": float(ep.raw["camera"]["sensor_height_mm"]),
            }
        )
    subject = "pile" if ep.raw["quantity"]["preset"] == "rice_doubling" else "person"
    return {
        "layer": layer_id,
        "subject": subject,
        "width": ep.width,
        "height": ep.height,
        "fps": ep.fps,
        "scale": int(args.scale),
        "samples": int(args.samples),
        "bounces": int(args.bounces),
        "exposure": 0.25 if layer_id == "interior" else 0.15,
        "meters_per_bu": layer.meters_per_bu,
        "seed": int(ep.raw.get("seed", 7)),
        "out": str(Path(args.out) / "plates" / layer_id),
        "textures": textures,
        "proxies": proxies,
        "grain": {
            "length_m": float(q.get("grain_length_m", 0.0066)),
            "width_m": float(q.get("grain_width_m", 0.0021)),
            "thickness_m": float(q.get("grain_thickness_m", 0.0017)),
            "mass_kg": float(q.get("grain_mass_kg", 2.1e-5)),
            "density": float(q.get("bulk_density_kg_m3", 800)),
            "repose_deg": float(q.get("repose_deg", 34)),
        },
        "frames": payload_frames,
    }


def _load_plate(path: Path, width: int, height: int) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if im.size != (width, height):
        im = im.resize((width, height), Image.Resampling.LANCZOS)
    return np.asarray(im, dtype=np.float32)


def _composite(ep, fr, args):
    acc = None
    wsum = 0.0
    for layer_id, weight in fr.weights.items():
        if weight < 0.04:
            continue
        path = Path(args.out) / "plates" / layer_id / f"f_{fr.frame:04d}.png"
        if not path.exists():
            continue
        im = _load_plate(path, ep.width, ep.height)
        acc = im * weight if acc is None else acc + im * weight
        wsum += weight
    if acc is None:
        acc = np.zeros((ep.height, ep.width, 3), dtype=np.float32)
        wsum = 1.0
    acc = np.clip(acc / wsum, 0, 255).astype(np.uint8)
    return Image.fromarray(acc, "RGB")


def _encode(frame_dir: Path, fps: int, mp4: Path):
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-start_number", "0",
            "-i", str(frame_dir / "f_%04d.png"),
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


def _contact(frame_dir: Path, fps: int, dest: Path):
    frames = sorted(frame_dir.glob("f_*.png"))
    step = max(1, fps // 2)
    picked = frames[::step]
    if not picked:
        return
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
        t = frame / fps
        draw.text((c * thumb_w + 4, r * (thumb_h + 18) + thumb_h + 1), f"{t:05.2f}s", fill=(255, 220, 190), font=font)
    sheet.save(dest, quality=90)


def _keys(ep, final_dir: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    fps = ep.fps
    wanted = [("00_hook", 0)]
    journey = [m for m in ep.milestones if m.t >= float(ep.raw["timing"]["hook_hold"]) - 0.01]
    if journey:
        picks = [journey[0], journey[len(journey) // 3], journey[len(journey) // 2], journey[(2 * len(journey)) // 3], journey[-1]]
        seen = {0}
        for m in picks:
            f = min(len(ep.frames) - 1, int(round(m.t * fps)))
            if f in seen:
                continue
            seen.add(f)
            wanted.append((m.id, f))
    # Always include the frame just before the dissolve (the reality-check beat).
    end_hold = float(ep.raw["timing"]["journey_end"]) + float(ep.raw["timing"]["ending_hold"]) * 0.5
    f_end = min(len(ep.frames) - 1, int(round(end_hold * fps)))
    wanted.append(("ending", f_end))
    written = []
    for name, frame in wanted[:6]:
        src = final_dir / f"f_{frame:04d}.png"
        if not src.exists():
            continue
        target = dest / f"key_{name}.png"
        shutil.copyfile(src, target)
        written.append(target)
    return written


def render(args):
    t0 = time.time()
    import yaml
    with open(args.spec, "r", encoding="utf-8") as handle:
        peek = yaml.safe_load(handle)
    if peek.get("format") == "B":
        from engine.render_b import render_format_b
        return render_format_b(args, peek)
    raw = load_raw(args.spec)
    if args.words:
        raw = retime_milestones(raw, args.words)
    ep = resolve(raw)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = timeline_document(ep)
    (out / "timeline.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"timeline {doc['duration_sec']:.2f}s {doc['frame_count']} frames -> {out / 'timeline.json'}")
    if args.timeline_only:
        return ep
    frames = _select_frames(ep, args.frames, args.milestone_frames, args.step)
    final_dir = out / "frames"
    if final_dir.exists() and not args.keep_frames:
        shutil.rmtree(final_dir)
    final_dir.mkdir(parents=True, exist_ok=True)
    if not args.preview:
        from PIL import ImageFilter

        gen = out / "gen"
        gen.mkdir(parents=True, exist_ok=True)
        soft_wood = gen / "wood_diff_soft.jpg"
        if not soft_wood.exists():
            Image.open(ASSETS / "textures" / "wood_diff_4k.jpg").convert("RGB").filter(
                ImageFilter.GaussianBlur(radius=0.8)
            ).save(soft_wood, quality=90)
        textures = {
            "wood_diff": str(soft_wood),
            "wood_rough": str(ASSETS / "textures" / "wood_rough_2k.jpg"),
            "wood_nor": str(ASSETS / "textures" / "wood_nor_2k.jpg"),
            "earth": str(ASSETS / "textures" / "earth_2k.jpg"),
            "moon": str(ASSETS / "textures" / "moon_1k.jpg"),
        }
        textures.update(write_all(gen))
        needed = blender_frames(ep, frames)
        blender = args.blender or _blender_bin()
        build = ROOT / "engine" / "build.py"
        for layer_id, _payload in needed.items():
            job = _job_for_layer(ep, layer_id, frames, args, textures)
            if not job["frames"]:
                continue
            job_path = out / f"job_{layer_id}.json"
            job_path.write_text(json.dumps(job), encoding="utf-8")
            print(f"blender layer {layer_id} frames {len(job['frames'])}", flush=True)
            subprocess.check_call([blender, "--background", "--python", str(build), "--", str(job_path)])
    frame0 = None
    ordered = sorted(frames, key=lambda fr: fr.frame)
    for fr in ordered:
        if args.preview:
            base = plate(ep, fr)
        else:
            base = _composite(ep, fr, args)
        img, _boxes = compose(base, ep, fr)
        if fr.frame == 0:
            frame0 = img.copy()
        if fr.dissolve > 0.0 and frame0 is not None:
            img = Image.blend(img, frame0, min(1.0, fr.dissolve))
        if frame0 is not None and fr.frame == ep.frames[-1].frame and fr.phase == "dissolve":
            img = frame0.copy()
        img.save(final_dir / f"f_{fr.frame:04d}.png")
    mp4 = out / f"{ep.id}.mp4"
    full = args.step == 1 and not args.frames and not args.milestone_frames
    if not args.no_video and full and len(frames) > 1:
        _encode(final_dir, ep.fps, mp4)
        print("mp4", mp4)
    _contact(final_dir, ep.fps, out / "contact_sheet.jpg")
    keys = _keys(ep, final_dir, out / "keys")
    stats = {
        "id": ep.id,
        "seconds": round(time.time() - t0, 2),
        "frames": len(frames),
        "preview": bool(args.preview),
        "samples": args.samples,
        "mp4": str(mp4) if mp4.exists() else None,
        "keys": [str(k) for k in keys],
    }
    (out / "render_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return ep


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Render a scale-journey episode")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--words", type=Path, default=None, help="ElevenLabs words.json; retimes milestones")
    parser.add_argument("--timeline-only", action="store_true")
    parser.add_argument("--preview", action="store_true", help="schematic plates, no Blender")
    parser.add_argument("--milestone-frames", action="store_true")
    parser.add_argument("--frames", default="", help="comma-separated frame indices")
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--bounces", type=int, default=0)
    parser.add_argument("--scale", type=int, default=100, help="render percentage")
    parser.add_argument("--blender", default="")
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument("--keep-frames", action="store_true")
    args = parser.parse_args(argv)
    if args.out is None:
        import yaml
        with open(args.spec, "r", encoding="utf-8") as handle:
            spec = yaml.safe_load(handle)
        args.out = ROOT / "out" / spec["id"]
    return args


if __name__ == "__main__":
    render(parse_args())
