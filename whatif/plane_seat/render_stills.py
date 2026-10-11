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
        "altitude": 540,
        "eye": [-76, -34, 16],
        "look": [20, 0, 7],
        "lens": 24,
        "bank": 6,
        "biome": "city",
        "xray": 0,
        "clouds": "off",
    },
    {
        "name": "01_city_flyover",
        "t": 2.0,
        "altitude": 260,
        "eye": [4, -58, 6],
        "look": [10, 0, 6],
        "lens": 20,
        "bank": 12,
        "biome": "city",
        "xray": 0,
        "clouds": "off",
    },
    {
        "name": "02_cloud_punch",
        "t": 4.08,
        "altitude": 1100,
        "eye": [-108, -32, 22],
        "look": [6, 0, 6],
        "lens": 22,
        "bank": 6,
        "biome": "forest",
        "xray": 0,
        "clouds": "punch",
    },
    {
        "name": "03_mountains",
        "t": 11.0,
        "altitude": 1500,
        "eye": [-96, -70, 28],
        "look": [20, -10, 0],
        "lens": 22,
        "bank": -8,
        "biome": "mountains",
        "xray": 0,
        "clouds": "off",
    },
    {
        "name": "04_xray_seats",
        "t": 12.6,
        "altitude": 900,
        "eye": [-8, -78, 26],
        "look": [2, 0, 9],
        "lens": 28,
        "bank": 0,
        "biome": "ocean",
        "xray": 1,
        "clouds": "off",
        "show": ["l38", "l39", "l32"],
    },
    {
        "name": "05_cabin_heatmap",
        "t": 22.9,
        "altitude": 640,
        "eye": [0, -46, 20],
        "look": [0, 0, 8],
        "lens": 32,
        "bank": 0,
        "biome": "ocean",
        "xray": 1,
        "clouds": "off",
        "show": ["l44"],
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
        composite(plate, float(shot["t"]), atmosphere=False, pills=False).save(shot["path"], quality=92)


if __name__ == "__main__":
    main()
