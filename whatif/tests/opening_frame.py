"""Low-res day-1 render. Checks the river, lawn, street, light, and camera.

    blender --background --python tests/opening_frame.py -- resolved.json

Writes /tmp/opening_frame/beauty.png and /tmp/opening_frame/report.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import build as build_mod  # noqa: E402
from engine.city_layout import tower_pose  # noqa: E402

OUT = Path("/tmp/opening_frame")

# Image y is 0 at the top. These are the registered landmarks.
BANDS = {
    "skyline_y": ((0.0, 168.0, 1.4), 0.38),
    "bank_y": ((0.0, 82.0, 0.35), 0.55),
    "promenade_y": ((-8.0, 36.0, 0.7), 0.77),
}


def _load_display(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    flat = np.array(image.pixels[:], dtype=np.float64)
    array = flat.reshape((height, width, image.channels))
    array = np.flipud(array[:, :, :3])
    return np.clip(np.rint(array * 255.0), 0, 255).astype(np.uint8)


def _fractions(rgb):
    red = rgb[:, :, 0].astype(np.float64)
    green = rgb[:, :, 1].astype(np.float64)
    blue = rgb[:, :, 2].astype(np.float64)
    peak = np.maximum(np.maximum(red, green), blue)
    floor = np.minimum(np.minimum(red, green), blue)
    sat = np.where(peak > 1.0, (peak - floor) / np.maximum(peak, 1.0), 0.0)
    luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    blue_px = (blue > red + 12.0) & (blue + 8.0 > green) & (blue > 50.0) & (sat > 0.15)
    green_px = (green > red + 10.0) & (green > blue + 8.0) & (green > 45.0) & (sat > 0.12)
    yellow_px = (red > 150.0) & (green > 120.0) & (blue < 110.0) & (red > blue + 40.0) & (green > blue + 25.0)
    white_px = (floor > 175.0) & (sat < 0.16)
    grey_px = (sat < 0.14) & (luma > 75.0) & (luma < 200.0) & ~white_px
    street = grey_px | white_px | yellow_px
    return {
        "blue": blue_px,
        "green": green_px,
        "yellow": yellow_px,
        "white": white_px,
        "street": street,
        "luma": luma / 255.0,
    }


def _band(mask, y0, y1):
    height = mask.shape[0]
    a = int(round(y0 * height))
    b = int(round(y1 * height))
    part = mask[a:b]
    if part.size == 0:
        return 0.0
    return float(part.mean())


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    spec = argv[0] if argv else str(OUT / "resolved.json")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(spec, "r", encoding="utf-8") as handle:
        resolved = json.load(handle)
    build_mod.RESOLVED = resolved
    build_mod._clear()
    scene = bpy.context.scene
    build_mod._init_props(scene, resolved)
    kit = build_mod.build_scene(scene, resolved, resolved.get("features") or {})
    build_mod.KIT = kit
    build_mod._key_channels(scene, resolved)
    build_mod._camera(scene, resolved)
    build_mod._render_settings(scene, resolved, 6, 0.25)
    scene.cycles.samples = 6
    scene.cycles.use_denoising = True
    bpy.app.handlers.frame_change_post.append(build_mod._on_frame)
    scene.frame_set(1)
    build_mod._on_frame(scene)
    cam = scene.camera
    bpy.context.view_layer.update()

    def project(point):
        co = world_to_camera_view(scene, cam, Vector(point))
        return float(co.x), float(1.0 - co.y)

    landmarks = {}
    for name, point, target in ((key, BANDS[key][0], BANDS[key][1]) for key in BANDS):
        sx, sy = project(point)
        landmarks[name] = {"x": sx, "y": sy, "target": target, "error": abs(sy - target)}
    (px, py, _pz), _rot = tower_pose(32.0)
    # The near portal leg runs from z=0 to z=64.5 on the pivot.
    top = (px, py, 64.5)
    sx, sy = project(top)
    landmarks["portal_x"] = {"x": sx, "y": sy, "target": 0.584, "error": abs(sx - 0.584)}
    landmarks["portal_y"] = {"x": sx, "y": sy, "target": 0.057, "error": abs(sy - 0.057)}

    scene.render.filepath = str(OUT / "beauty.png")
    bpy.ops.render.render(write_still=True)
    rgb = _load_display(OUT / "beauty.png")
    masks = _fractions(rgb)
    report = {
        "camera": {
            "location": [float(v) for v in cam.location],
            "lens": float(cam.data.lens),
        },
        "landmarks": landmarks,
        "river_blue": _band(masks["blue"], 0.40, 0.54),
        "park_green": _band(masks["green"], 0.56, 0.74),
        "mean_luma": float(masks["luma"].mean()),
        "bottom_street": _band(masks["street"], 0.75, 1.0),
        "bottom_white": _band(masks["white"], 0.75, 1.0),
        "bottom_yellow": _band(masks["yellow"], 0.75, 1.0),
        "width": int(rgb.shape[1]),
        "height": int(rgb.shape[0]),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
