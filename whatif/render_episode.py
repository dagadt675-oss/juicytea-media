#!/usr/bin/env python3
"""Render a what-if episode from a YAML spec.

    python3 render_episode.py episodes/humans_disappeared.yaml --frames 1 --scale 0.5 --samples 8

Segmented render (PNG or EXR sequences, then one encode). Cached chunks
are skipped unless the spec, code, or assets that affect them changed:

    python3 render_episode.py episodes/humans_disappeared.yaml --segments --scale 0.5 --samples 8
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.segments import (  # noqa: E402
    asset_digest,
    default_asset_roots,
    encode_sequence,
    project_code_digest,
    run_segments,
)
from engine.spec import load_yaml, resolve, sfx_document, timeline_document, words_document  # noqa: E402


def blender_bin():
    env = os.environ.get("BLENDER")
    if env and Path(env).exists():
        return env
    home = Path.home() / "blender" / "blender"
    if home.exists():
        return str(home)
    found = shutil.which("blender")
    if found:
        return found
    raise SystemExit("Blender not found")


def _write_documents(resolved, out):
    out.mkdir(parents=True, exist_ok=True)
    resolved_path = out / "resolved.json"
    resolved_path.write_text(json.dumps(resolved), encoding="utf-8")
    (out / "timeline.json").write_text(json.dumps(timeline_document(resolved), indent=2), encoding="utf-8")
    (out / "words.json").write_text(json.dumps(words_document(resolved), indent=2), encoding="utf-8")
    (out / "sfx.json").write_text(json.dumps(sfx_document(resolved), indent=2), encoding="utf-8")
    return resolved_path


def _blender_segment(resolved_path, samples, scale, image_format, motion_blur):
    def render(segment, dest):
        dest.mkdir(parents=True, exist_ok=True)
        cmd = [
            blender_bin(),
            "--background",
            "--python",
            str(ROOT / "engine" / "build.py"),
            "--",
            str(resolved_path),
            "--out",
            str(dest),
            "--frames",
            f"{segment['render_start']}-{segment['render_end']}",
            "--samples",
            str(samples),
            "--scale",
            str(scale),
            "--format",
            image_format,
        ]
        if motion_blur:
            cmd.append("--motion-blur")
        print("segment", segment["id"], " ".join(cmd))
        subprocess.check_call(cmd)

    return render


def _run_segmented(args, resolved, out, resolved_path):
    if args.composite and args.format == "exr":
        raise SystemExit("composite the PNG sequence; EXR stays a linear beauty pass")
    cache = Path(args.cache) if args.cache else out / "segment_cache"
    assemble_dir = out / "frames"
    code = project_code_digest(ROOT)
    assets = asset_digest(default_asset_roots(ROOT), cache_file=cache / "_asset_digest.json")
    manifest = run_segments(
        resolved,
        cache_dir=cache,
        assemble_dir=assemble_dir,
        render_fn=_blender_segment(resolved_path, args.samples, args.scale, args.format, args.motion_blur),
        code=code,
        assets=assets,
        samples=args.samples,
        scale=args.scale,
        image_format=args.format,
        handles=args.handles,
        min_seconds=args.segment_min,
        max_seconds=args.segment_max,
        force=args.force,
        full_reference=args.verify_full,
        render=not args.plan_only,
    )
    public = {key: value for key, value in manifest.items() if key != "entries"}
    for segment in public["segments"]:
        state = "cached" if segment["cached"] else ("needed" if args.plan_only else "render")
        print(
            f"{segment['id']}  {segment['start_frame']}-{segment['end_frame']}"
            f"  handles {segment['render_start']}-{segment['render_end']}  {state}"
        )
    encode_dir = assemble_dir
    if args.composite and not args.plan_only:
        from engine.overlay import composite_directory

        encode_dir = out / "comp"
        composite_directory(resolved, assemble_dir, encode_dir)
        print("ui", encode_dir)
    movie = None
    if not args.plan_only and not args.no_encode:
        movie = Path(args.encode) if args.encode else out / f"{resolved['id']}.mp4"
        encode_sequence(
            encode_dir,
            movie,
            fps=resolved["fps"],
            frame_count=resolved["frame_count"],
            ext=manifest["format"] if encode_dir == assemble_dir else "png",
        )
        print("encode", movie)
    public["assembled"] = str(assemble_dir)
    public["encoded"] = str(movie) if movie else None
    (out / "segments.json").write_text(json.dumps(public, indent=2), encoding="utf-8")
    return public


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--out", default=None)
    parser.add_argument("--frames", default="1")
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--composite", action="store_true")
    parser.add_argument("--segments", action="store_true", help="render 2–5 s chunks with a per-segment cache")
    parser.add_argument("--plan-only", action="store_true", help="write the segment plan and cache keys, do not render")
    parser.add_argument("--segment-min", type=float, default=2.0)
    parser.add_argument("--segment-max", type=float, default=5.0)
    parser.add_argument("--handles", type=int, default=2, help="extra frames on each side of a chunk (1 or 2)")
    parser.add_argument("--format", choices=("png", "exr"), default="png")
    parser.add_argument("--cache", default=None)
    parser.add_argument("--encode", default=None, help="mp4 path for the single final encode")
    parser.add_argument("--no-encode", action="store_true")
    parser.add_argument("--force", action="store_true", help="ignore the segment cache")
    parser.add_argument("--motion-blur", action="store_true")
    parser.add_argument("--verify-full", default=None, help="directory of a full render; boundary frames must match")
    args = parser.parse_args()
    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = ROOT / spec_path
    resolved = resolve(load_yaml(spec_path))
    out = Path(args.out) if args.out else ROOT / "out" / resolved["id"]
    resolved_path = _write_documents(resolved, out)
    if args.segments or args.plan_only:
        _run_segmented(args, resolved, out, resolved_path)
        return
    frames = out / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    cmd = [
        blender_bin(),
        "--background",
        "--python",
        str(ROOT / "engine" / "build.py"),
        "--",
        str(resolved_path),
        "--out",
        str(frames),
        "--frames",
        args.frames,
        "--samples",
        str(args.samples),
        "--scale",
        str(args.scale),
        "--format",
        args.format,
    ]
    if args.motion_blur:
        cmd.append("--motion-blur")
    print(" ".join(cmd))
    subprocess.check_call(cmd)
    if args.composite:
        from engine.overlay import composite_file

        comp = out / "comp"
        comp.mkdir(parents=True, exist_ok=True)
        suffix = "exr" if args.format == "exr" else "png"
        if suffix != "png":
            raise SystemExit("composite the PNG sequence; EXR stays a linear beauty pass")
        for frame_path in sorted(frames.glob("f_*.png")):
            frame = int(frame_path.stem.split("_")[1])
            composite_file(resolved, frame_path, comp / frame_path.name, frame)
            print("ui", frame_path.name)


if __name__ == "__main__":
    main()
