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
from engine.segments import (  # noqa: E402
    cache_dir,
    code_hash,
    encode_sequence,
    hash_key,
    is_ready,
    plan_segments,
    scene_hash,
    store_ready,
)
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
    step = max(1, int(round(fps * 2.5)))
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

    def into(phase, seconds):
        frames = [fr for fr in ep.frames if fr.phase == phase]
        return frames[min(len(frames) - 1, int(seconds * ep.fps))].frame

    picks = [
        ("00_hook", into("hook", 1.0)),
        ("setback", into("floors", 2.0)),
        ("mid", into("drag", 3.0)),
        ("street", into("edge", 2.0)),
        ("impact", into("hit", 4.0)),
        ("loop", ep.frames[-1].frame),
    ]
    written = []
    for name, frame in picks:
        src = final_dir / f"f_{frame:04d}.png"
        if src.exists():
            target = dest / f"key_{name}.png"
            shutil.copyfile(src, target)
            written.append(str(target))
    return written


def _round_vec(values):
    return [round(float(v), 5) for v in values]


def _geom(ep, fr) -> dict:
    prev = ep.frames[max(0, fr.frame - 1)]
    return {
        "frame": fr.frame,
        "t": round(fr.t, 5),
        "cam": _round_vec(fr.cam),
        "target": _round_vec(fr.target),
        "penny": _round_vec(fr.penny),
        "rot": _round_vec(fr.rot),
        "lens": round(float(fr.lens), 4),
        "prev_cam": _round_vec(prev.cam),
        "prev_penny": _round_vec(prev.penny),
    }


def _ui(fr) -> dict:
    return {
        "frame": fr.frame,
        "phase": fr.phase,
        "primary": fr.primary,
        "secondary": fr.secondary,
        "primary_prev": fr.primary_prev,
        "secondary_prev": fr.secondary_prev,
        "roll": round(fr.roll, 5),
        "secondary_roll": round(fr.secondary_roll, 5),
        "title_alpha": round(fr.title_alpha, 5),
        "ending_alpha": round(fr.ending_alpha, 5),
        "pill_title": fr.pill_title,
        "pill_sub": fr.pill_sub,
        "pill_alpha": round(fr.pill_alpha, 5),
        "metric": fr.metric,
    }


def _scene_key(ep, args) -> str:
    private = ROOT / "cache" / "private"
    library = ROOT / "cache" / "library" / "extracted"
    assets = [path for path in (private, library) if path.exists()]
    assets.append(ROOT / "assets" / "hdri" / "sunset_jhbcentral_1k.hdr")
    assets.append(ROOT / "assets" / "characters" / "characterMedium.fbx")
    return scene_hash(
        [ROOT / "engine" / "build_b.py", ROOT / "engine" / "manhattan.py", ROOT / "engine" / "gen_textures.py"],
        assets,
        {
            "samples": max(16, int(args.samples)),
            "scale": int(args.scale),
            "width": ep.width,
            "height": ep.height,
            "seed": ep.raw.get("seed"),
            "plate_format": getattr(args, "plate_format", "png"),
        },
    )


def _compose_key() -> str:
    return code_hash(
        [
            ROOT / "engine" / "compose_b.py",
            ROOT.parent / "ui" / "counter.py",
            ROOT / "assets" / "fonts" / "Anton-Regular.ttf",
        ]
    )


def _spec_key(spec: Path) -> str:
    return hashlib_file(spec)


def hashlib_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def _job(ep, frames, plates: Path, args) -> dict:
    textures = write_all(plates.parent / "gen")
    empire = outline("empire")
    return {
        "width": ep.width,
        "height": ep.height,
        "samples": int(args.samples),
        "scale": int(args.scale),
        "lens_mm": float(ep.raw["camera"]["lens_mm"]),
        "deck_m": empire["deck_m"],
        "roof_m": empire["roof_m"],
        "tip_m": empire["height_m"],
        "liberty_m": outline("liberty")["height_m"],
        "facade": textures["facade"],
        "street": textures["street"],
        "hdri": str(ROOT / "assets" / "hdri" / "sunset_jhbcentral_1k.hdr"),
        "character": str(ROOT / "assets" / "characters" / "characterMedium.fbx"),
        "skin": str(ROOT / "assets" / "characters" / "skaterMaleA.png"),
        "plate_format": getattr(args, "plate_format", "png"),
        "out": str(plates),
        "frames": [_geom(ep, fr) for fr in frames],
    }


def _run_blender(ep, frames, plates: Path, args):
    plates.mkdir(parents=True, exist_ok=True)
    job = _job(ep, frames, plates, args)
    job_path = plates.parent / "job_penny.json"
    job_path.write_text(json.dumps(job), encoding="utf-8")
    blender = args.blender or _blender()
    subprocess.check_call([blender, "--background", "--python", str(ROOT / "engine" / "build_b.py"), "--", str(job_path)])


def _compose_body(ep, plates: Path, dest: Path, frame_ids: list[int], opening: Image.Image | None):
    dest.mkdir(parents=True, exist_ok=True)
    by_id = {fr.frame: fr for fr in ep.frames}
    for frame in frame_ids:
        fr = by_id[frame]
        if plates.joinpath("preview").exists():
            base = _preview_plate(ep, fr)
        else:
            base = Image.open(plates / f"f_{frame:04d}.png").convert("RGB")
        img = compose_b(base, ep, fr)
        if fr.frame == ep.frames[-1].frame and opening is not None:
            img = opening.copy()
        img.save(dest / f"f_{frame:04d}.png")
        if frame == 0:
            opening = img.copy()
    return opening


def _segmented(args, ep, out: Path) -> list[dict]:
    """Render beat-sized chunks. Reuse a chunk when its key is unchanged."""
    segments = plan_segments(len(ep.frames), ep.fps, ep.beats)
    scene = _scene_key(ep, args)
    compose = _compose_key()
    spec = _spec_key(Path(args.spec))
    report = []
    final_dir = out / "frames"
    if final_dir.exists() and not getattr(args, "keep_frames", False):
        shutil.rmtree(final_dir)
    final_dir.mkdir(parents=True, exist_ok=True)
    opening = None
    for segment in segments:
        rendered = [ep.frames[i] for i in segment.render_frames]
        body = list(segment.body)
        plate_key = hash_key(scene, bool(args.preview), [_geom(ep, fr) for fr in rendered])
        frame_key = hash_key(plate_key, compose, spec, [_ui(fr) for fr in (ep.frames[i] for i in body)])
        plate_dir = cache_dir(ep.id, "plates", plate_key)
        frame_dir = cache_dir(ep.id, "frames", frame_key)
        cached = is_ready(frame_dir)
        if not cached:
            if not is_ready(plate_dir):
                partial = plate_dir.with_name(plate_key + ".partial")
                if partial.exists():
                    shutil.rmtree(partial)
                if args.preview:
                    partial.mkdir(parents=True, exist_ok=True)
                    (partial / "preview").write_text("1", encoding="utf-8")
                else:
                    _run_blender(ep, rendered, partial, args)
                for frame in segment.handles:
                    for suffix in (".png", ".exr"):
                        leftover = partial / f"f_{frame:04d}{suffix}"
                        if leftover.exists():
                            leftover.unlink()
                if plate_dir.exists():
                    shutil.rmtree(plate_dir)
                partial.rename(plate_dir)
                store_ready(plate_dir, {"key": plate_key, "start": segment.start, "end": segment.end, "handles": list(segment.handles)})
            partial_frames = frame_dir.with_name(frame_key + ".partial")
            if partial_frames.exists():
                shutil.rmtree(partial_frames)
            opening = _compose_body(ep, plate_dir, partial_frames, body, opening)
            if frame_dir.exists():
                shutil.rmtree(frame_dir)
            partial_frames.rename(frame_dir)
            store_ready(frame_dir, {"key": frame_key, "plate": plate_key, "start": segment.start, "end": segment.end})
        else:
            first = frame_dir / "f_0000.png"
            if segment.start == 0 and first.exists():
                opening = Image.open(first).convert("RGB")
        for frame in body:
            source = frame_dir / f"f_{frame:04d}.png"
            target = final_dir / source.name
            if target.exists():
                target.unlink()
            try:
                os_link(source, target)
            except OSError:
                shutil.copyfile(source, target)
        report.append(
            {
                "index": segment.index,
                "start": segment.start,
                "end": segment.end,
                "handles": list(segment.handles),
                "cached": cached,
                "key": frame_key[:16],
            }
        )
        print(f"SEGMENT {segment.index} {segment.start}-{segment.end} cached={cached}", flush=True)
    if opening is not None and ep.frames:
        last = final_dir / f"f_{ep.frames[-1].frame:04d}.png"
        first = final_dir / "f_0000.png"
        if first.exists():
            shutil.copyfile(first, last)
    return report


def os_link(source, target):
    import os

    os.link(source, target)


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
    segmented = not args.frames and not getattr(args, "no_segments", False)
    segment_report = []
    if segmented:
        segment_report = _segmented(args, ep, out)
        final_dir = out / "frames"
        frames = ep.frames
    else:
        final_dir = out / "frames"
        if final_dir.exists() and not args.keep_frames:
            shutil.rmtree(final_dir)
        final_dir.mkdir(parents=True, exist_ok=True)
        if not args.preview:
            _run_blender(ep, frames, out / "plates", args)
        opening = None
        for fr in frames:
            if args.preview:
                base = _preview_plate(ep, fr)
            else:
                base = Image.open(out / "plates" / f"f_{fr.frame:04d}.png").convert("RGB")
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
        encode_sequence(final_dir, ep.fps, mp4)
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
        "segments": segment_report,
    }
    (out / "render_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    return ep
