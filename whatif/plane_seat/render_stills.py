"""Six approval stills. Does not render the full Short."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLENDER = Path.home() / "apps/blender-4.5.9-linux-x64/blender"
OUT = Path("/workspace/v/plane_tests")

# Eye and look are metres in aircraft space: nose +X, fuselage center near z=7,
# wings out along Y, tail toward -X.
STILLS = [
    {
        "name": "00_hook",
        "t": 0.0,
        "altitude": 420,
        "eye": [-62, -40, 12],
        "look": [16, 0, 7],
        "lens": 26,
        "bank": 11,
        "biome": "city",
        "xray": 0,
        "clouds": "off",
        "sky": 0.38,
        "fstop": 6.3,
    },
    {
        "name": "01_city_flyover",
        "t": 2.0,
        "altitude": 240,
        "eye": [2, -52, 8],
        "look": [12, 0, 6],
        "lens": 20,
        "bank": 10,
        "biome": "city",
        "xray": 0,
        "clouds": "off",
        "sky": 0.42,
        "fstop": 7.1,
    },
    {
        "name": "02_cloud_punch",
        "t": 4.08,
        "altitude": 2400,
        "eye": [-96, -28, 16],
        "look": [8, 0, 7],
        "lens": 40,
        "bank": 5,
        "biome": "forest",
        "xray": 0,
        "clouds": "punch",
        "sky": 1.05,
        "fstop": 16.0,
    },
    {
        "name": "03_mountains",
        "t": 11.0,
        "altitude": 1100,
        "eye": [-70, -28, 16],
        "look": [16, -4, 2],
        "lens": 32,
        "bank": -4,
        "biome": "mountains",
        "xray": 0,
        "clouds": "off",
        "sky": 0.75,
        "fstop": 16.0,
    },
    {
        "name": "04_xray_seats",
        "t": 12.6,
        "altitude": 600,
        "eye": [-18, -36, 20],
        "look": [2, 0, 7],
        "lens": 32,
        "bank": 0,
        "biome": "ocean",
        "xray": 1,
        "clouds": "off",
        "sky": 0.6,
        "fstop": 16.0,
        "show": ["l38", "l39", "l32"],
    },
    {
        "name": "05_cabin_heatmap",
        "t": 22.9,
        "altitude": 480,
        "eye": [-2, -20, 14],
        "look": [2, 0, 6.5],
        "lens": 36,
        "bank": 0,
        "biome": "ocean",
        "xray": 1,
        "clouds": "off",
        "sky": 0.6,
        "fstop": 16.0,
        "show": ["l44"],
    },
    {
        "name": "06_ocean",
        "t": 19.2,
        "altitude": 150,
        "eye": [-68, -28, 9],
        "look": [18, 0, 4],
        "lens": 24,
        "bank": 7,
        "biome": "ocean",
        "xray": 0,
        "clouds": "off",
        "sky": 0.5,
        "fstop": 8.0,
    },
    {
        "name": "07_forest",
        "t": 7.4,
        "altitude": 170,
        "eye": [-64, -28, 14],
        "look": [16, 0, 3],
        "lens": 24,
        "bank": -6,
        "biome": "forest",
        "xray": 0,
        "clouds": "off",
        "sky": 0.48,
        "fstop": 8.0,
    },
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    shots = []
    for shot in STILLS:
        if only and shot["name"] not in only and not any(shot["name"].startswith(item) for item in only):
            continue
        item = dict(shot)
        item["path"] = str(OUT / f"{shot['name']}.jpg")
        shots.append(item)
    samples = 16
    scale = 100
    if "--draft" in sys.argv:
        samples = 8
        scale = 40
    job = {"stills": shots, "samples": samples, "scale": scale}
    path = Path("/tmp/plane_stills_job.json")
    path.write_text(json.dumps(job))
    subprocess.check_call(
        [str(BLENDER), "--background", "--python", str(ROOT / "engine" / "build.py"), "--", str(path)]
    )
    # Karaoke only. The 3D zone labels are the callouts; the cloud veil would hide the punch.
    sys.path.insert(0, str(ROOT.parent))
    from PIL import Image

    from plane_seat.engine.overlay import composite

    for shot in shots:
        plate = Image.open(shot["path"])
        graded = _grade(composite(plate, float(shot["t"]), atmosphere=False, pills=False))
        graded.save(shot["path"], quality=92)


def _grade(image):
    """Light teal-and-orange grade plus a fine film grain. Done on the still, not the VO."""
    import numpy as np
    from PIL import Image

    pixels = np.asarray(image).astype(np.float32)
    luma = pixels.mean(axis=2, keepdims=True) / 255.0
    teal = np.array([ -6.0, 8.0, 14.0 ], dtype=np.float32)
    orange = np.array([ 14.0, 6.0, -8.0 ], dtype=np.float32)
    pixels += (1.0 - luma) * teal + luma * orange
    rng = np.random.default_rng(11)
    pixels += rng.normal(0.0, 2.4, pixels.shape)
    np.clip(pixels, 0, 255, out=pixels)
    return Image.fromarray(pixels.astype(np.uint8))


if __name__ == "__main__":
    main()
