"""Render one facade and refuse a blank wall.

    blender --background --python tests/skyline_windows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.meshkit import box_object, make_facade_material  # noqa: E402


def main():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 96
    scene.render.resolution_y = 160
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
        bg.inputs["Strength"].default_value = 1.0

    coll = scene.collection
    facade = make_facade_material()
    building = box_object("probe", coll, (0, 0, 24), (16, 12, 48), facade)
    building.color = (0.86, 0.87, 0.88, 1)

    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 4.0
    sun_obj = bpy.data.objects.new("sun", sun)
    coll.objects.link(sun_obj)
    sun_obj.rotation_euler = (0.9, 0.2, 0.4)

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("cam", cam_data)
    coll.objects.link(cam)
    cam.location = (0, -34, 24)
    direction = Vector((0, 0, 22)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    out = Path("/tmp/skyline_window.png")
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)

    image = bpy.data.images.load(str(out))
    pixels = list(image.pixels)
    width, height = image.size
    lums = []
    for i in range(0, len(pixels), 4):
        lums.append(0.2126 * pixels[i] + 0.7152 * pixels[i + 1] + 0.0722 * pixels[i + 2])
    ordered = sorted(lums)
    wall = ordered[int(len(ordered) * 0.85)]
    dark = sum(1 for value in lums if value < wall * 0.62)
    fraction = dark / len(lums)
    bands = 0
    row_h = height // 8
    for band in range(8):
        start = band * row_h * width
        end = (band + 1) * row_h * width
        if any(lums[i] < wall * 0.62 for i in range(start, min(end, len(lums)))):
            bands += 1
    report = {
        "wall": round(wall, 4),
        "dark_fraction": round(fraction, 4),
        "bands": bands,
        "path": str(out),
    }
    Path("/tmp/skyline_window.json").write_text(json.dumps(report), encoding="utf-8")
    print("SKYLINE", report)
    if wall < 0.35 or not (0.12 <= fraction <= 0.80) or bands < 4:
        raise SystemExit(f"facade lost its window grid: {report}")


if __name__ == "__main__":
    main()
