#!/usr/bin/env python3
"""Render a what-if episode from a YAML spec.

    python3 render_episode.py episodes/humans_disappeared.yaml --frames 1 --scale 0.5 --samples 8
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--out", default=None)
    parser.add_argument("--frames", default="1")
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--composite", action="store_true")
    args = parser.parse_args()
    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = ROOT / spec_path
    resolved = resolve(load_yaml(spec_path))
    out = Path(args.out) if args.out else ROOT / "out" / resolved["id"]
    out.mkdir(parents=True, exist_ok=True)
    resolved_path = out / "resolved.json"
    resolved_path.write_text(json.dumps(resolved), encoding="utf-8")
    (out / "timeline.json").write_text(json.dumps(timeline_document(resolved), indent=2), encoding="utf-8")
    (out / "words.json").write_text(json.dumps(words_document(resolved), indent=2), encoding="utf-8")
    (out / "sfx.json").write_text(json.dumps(sfx_document(resolved), indent=2), encoding="utf-8")
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
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd)
    if args.composite:
        from engine.overlay import composite_file

        comp = out / "comp"
        comp.mkdir(parents=True, exist_ok=True)
        for frame_path in sorted(frames.glob("f_*.png")):
            frame = int(frame_path.stem.split("_")[1])
            composite_file(resolved, frame_path, comp / frame_path.name, frame)
            print("ui", frame_path.name)


if __name__ == "__main__":
    main()
