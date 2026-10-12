"""Colab final render. No external files besides this blend.

    blender -b scene.blend -P render.py -- START END

Cycles on OptiX, then CUDA, then CPU. Writes frames/0001.png next to the blend.
"""

from __future__ import annotations

import sys

import bpy

SAMPLES = 64
WIDTH = 1080
HEIGHT = 1920


def _argv():
    raw = sys.argv
    if "--" not in raw:
        raise SystemExit("usage: blender -b scene.blend -P render.py -- START END")
    args = raw[raw.index("--") + 1 :]
    if len(args) < 2:
        raise SystemExit("usage: blender -b scene.blend -P render.py -- START END")
    return int(args[0]), int(args[1])


def _gpu():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            chosen = [device for device in prefs.devices if device.type == kind]
            if not chosen:
                continue
            for device in prefs.devices:
                device.use = device.type == kind
            scene.cycles.device = "GPU"
            print("cycles device", kind, [device.name for device in chosen], flush=True)
            return kind
        except Exception as exc:
            print("cycles device skip", kind, exc, flush=True)
    scene.cycles.device = "CPU"
    print("cycles device CPU", flush=True)
    return "CPU"


def main():
    start, end = _argv()
    _gpu()
    scene = bpy.context.scene
    scene.cycles.samples = SAMPLES
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.adaptive_min_samples = min(8, SAMPLES)
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError as exc:
        print("denoiser", exc, flush=True)
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 4
    scene.cycles.volume_bounces = 1
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.volume_max_steps = 64
    scene.cycles.volume_step_rate = 1.6
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.use_file_extension = True
    scene.render.use_persistent_data = True
    scene.render.use_motion_blur = False
    scene.frame_start = start
    scene.frame_end = end
    for frame in range(start, end + 1):
        scene.cycles.seed = frame * 997 + 17
        scene.frame_set(frame)
        scene.render.filepath = "//frames/{:04d}".format(frame)
        bpy.ops.render.render(write_still=True)
        # frame_path() appends the frame again when the path has no # marks.
        # write_still uses the path above and adds the extension: frames/0001.png.
        written = bpy.path.abspath(scene.render.filepath) + scene.render.file_extension
        print("wrote", written, flush=True)


if __name__ == "__main__":
    main()
