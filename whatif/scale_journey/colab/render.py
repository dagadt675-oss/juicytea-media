"""Render a frame range from the packed penny blend on a Colab GPU.

    blender -b scene.blend -P render.py -- START END

Frames land in frames/0000.png next to this script. OPTIX is used when the
GPU offers it, otherwise CUDA. Every non-CPU device is enabled. Samples,
resolution and colour management match the approved full-resolution picture.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy


def _enable_gpu(scene):
    prefs = bpy.context.preferences.addons["cycles"].preferences
    chosen = None
    for device_type in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = device_type
        except Exception as exc:
            print(f"GPU {device_type} unavailable: {exc}", flush=True)
            continue
        try:
            prefs.get_devices()
        except Exception as exc:
            print(f"GPU {device_type} devices failed: {exc}", flush=True)
            continue
        gpus = [device for device in prefs.devices if device.type != "CPU"]
        if not gpus:
            print(f"GPU {device_type} has no devices", flush=True)
            continue
        for device in prefs.devices:
            device.use = device.type != "CPU"
        chosen = device_type
        print(f"GPU {device_type} " + ", ".join(device.name for device in gpus), flush=True)
        break
    if chosen is None:
        print("GPU fallback CPU", flush=True)
        scene.cycles.device = "CPU"
        return
    scene.cycles.device = "GPU"


def _apply_picture(scene):
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.cycles.samples = 24
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.adaptive_min_samples = 1
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    for name in ("max_bounces", "diffuse_bounces", "glossy_bounces", "transmission_bounces", "transparent_max_bounces"):
        setattr(scene.cycles, name, 12)
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.6
    scene.cycles.motion_blur_position = "END"
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = 0.55
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    start, end = int(argv[0]), int(argv[1])
    if end < start:
        raise SystemExit(f"bad range {start} {end}")
    scene = bpy.context.scene
    _apply_picture(scene)
    _enable_gpu(scene)
    out = Path(bpy.data.filepath).resolve().parent / "frames"
    out.mkdir(parents=True, exist_ok=True)
    scene.frame_start = start
    scene.frame_end = end
    for frame in range(start, end + 1):
        scene.frame_set(frame)
        scene.cycles.seed = frame
        # A still render does not expand ####, so the frame number is written out.
        scene.render.filepath = f"//frames/{frame:04d}.png"
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {frame}", flush=True)
    print(f"RENDER_DONE {start} {end}", flush=True)


if __name__ == "__main__":
    main()
