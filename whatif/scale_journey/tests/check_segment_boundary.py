"""Compare one segment boundary against a single continuous Blender pass.

Renders six frames in one job, and the same frames as a later segment that
keeps two handle frames for motion blur and then drops them. Frame 3 must match.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

from engine.bformat import resolve_b  # noqa: E402
from engine.render_b import _compose_body, _run_blender  # noqa: E402

EP = ROOT / "episodes" / "penny_empire.yaml"


class Args:
    samples = 16
    scale = 100
    preview = False
    plate_format = "png"
    blender = ""
    spec = EP


def main():
    ep = resolve_b(EP)
    work = ROOT / "cache" / "segment_boundary"
    shutil.rmtree(work, ignore_errors=True)
    full = work / "full"
    split = work / "split"
    body = [3, 4, 5]
    handles = [1, 2]
    _run_blender(ep, [ep.frames[i] for i in range(6)], full, Args)
    _run_blender(ep, [ep.frames[i] for i in handles + body], split, Args)
    for frame in handles:
        for path in (split / f"f_{frame:04d}.png", split / f"f_{frame:04d}.exr"):
            if path.exists():
                path.unlink()
    _compose_body(ep, full, work / "full_frames", [3], None)
    _compose_body(ep, split, work / "split_frames", [3], None)
    a = Image.open(work / "full_frames" / "f_0003.png")
    b = Image.open(work / "split_frames" / "f_0003.png")
    diff = ImageChops.difference(a, b)
    if diff.getbbox() is not None:
        raise SystemExit("boundary frame 3 does not match the continuous render")
    print("BOUNDARY_MATCH frame 3")


if __name__ == "__main__":
    main()
