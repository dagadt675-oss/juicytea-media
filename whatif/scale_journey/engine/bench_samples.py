"""Follow-up sample search. Compares against the plates already in /tmp/penny_bench/ref."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHATIF = ROOT.parent
for path in (str(WHATIF), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from engine.bench_speed import FRAMES, GEOM_PATH, OUT, REF, _frames, _run
from engine.build_b import prepare_scene

def main():
    global FRAMES_GEOM
    import engine.bench_speed as bench
    bench.FRAMES_GEOM = _frames()
    job = {
        "width": 1080,
        "height": 1920,
        "scale": 100,
        "samples": 24,
        "hdri": str(ROOT / "assets" / "hdri" / "sunset_jhbcentral_1k.hdr"),
    }
    scene, cam, penny, arms = prepare_scene(job)
    variants = [
        ("adapt20", dict(REF, adaptive=True, samples=20, threshold=0.005)),
        ("adapt24", dict(REF, adaptive=True, samples=24, threshold=0.01)),
    ]
    report = {}
    for name, speed in variants:
        report[name] = _run(scene, cam, penny, arms, speed, name, FRAMES, job)
    prev = {}
    path = OUT / "times.json"
    if path.exists():
        prev = json.loads(path.read_text(encoding="utf-8"))
    prev.update(report)
    path.write_text(json.dumps(prev, indent=2), encoding="utf-8")
    print("BENCH_EXTRA_DONE", flush=True)


if __name__ == "__main__":
    main()
