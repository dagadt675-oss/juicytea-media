"""A/B the approved Cycles speedups on three frames.

    blender --background --python engine/bench_speed.py

Writes /tmp/penny_bench/<variant>/f_XXXX.png and times.json.
The reference is CPU, 24 samples, OpenImageDenoise, 12 bounces, no adaptive
sampling, no persistent data, no culling, no distant LOD.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
WHATIF = ROOT.parent
for path in (str(WHATIF), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from engine.build_b import configure_cycles, prepare_scene, render_frame

OUT = Path("/tmp/penny_bench")
FRAMES = (0, 200, 690)
GEOM_PATH = Path("/tmp/penny_bench_frames.json")
REF = {
    "adaptive": False,
    "threshold": 0.01,
    "min_samples": 1,
    "bounces": 12,
    "persistent": False,
    "cull": False,
    "lod": False,
    "samples": 24,
}


def _frames():
    rows = json.loads(GEOM_PATH.read_text(encoding="utf-8"))
    return {int(row["frame"]): row for row in rows}


def _variant(name, **overrides):
    speed = dict(REF)
    speed.update(overrides)
    return name, speed


def _run(scene, cam, penny, arms, speed, name, frame_ids, job):
    job = dict(job)
    job["samples"] = int(speed["samples"])
    configure_cycles(scene, job, speed)
    rows = []
    for frame_id in frame_ids:
        dest = OUT / name / f"f_{frame_id:04d}.png"
        t0 = time.perf_counter()
        render_frame(scene, cam, penny, arms, FRAMES_GEOM[frame_id], dest, speed)
        sec = time.perf_counter() - t0
        rows.append({"frame": frame_id, "sec": round(sec, 3)})
        print(f"BENCH {name} frame {frame_id} {sec:.2f}s", flush=True)
    return rows


def main():
    global FRAMES_GEOM
    FRAMES_GEOM = _frames()
    job = {
        "width": 1080,
        "height": 1920,
        "scale": 100,
        "samples": 24,
        "hdri": str(ROOT / "assets" / "hdri" / "sunset_jhbcentral_1k.hdr"),
    }
    scene, cam, penny, arms = prepare_scene(job)
    variants = [
        _variant("ref"),
        _variant("samples4", adaptive=True, samples=4),
        _variant("samples8", adaptive=True, samples=8),
        _variant("samples16", adaptive=True, samples=16),
        _variant("bounce4", bounces=4),
        _variant("bounce6", bounces=6),
        _variant("persistent", persistent=True),
        _variant("cull", cull=True),
        _variant("lod", lod=True),
    ]
    report = {}
    for name, speed in variants:
        report[name] = _run(scene, cam, penny, arms, speed, name, FRAMES, job)
    # Same settings as the reference, but frame 200 is rendered after its
    # two handle frames, the way a segment is.
    report["segment"] = _run(scene, cam, penny, arms, dict(REF), "segment", (198, 199, 200), job)
    (OUT / "times.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BENCH_DONE", flush=True)


if __name__ == "__main__":
    main()
