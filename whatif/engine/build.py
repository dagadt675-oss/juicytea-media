"""Build and render a what-if episode inside Blender.

    blender --background --python engine/build.py -- resolved.json --out dir --frames 1,10 --samples 8 --scale 1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.effects import apply  # noqa: E402
from engine.meshkit import set_linear_keys  # noqa: E402
from engine.pov import apply_pov, attach_pov  # noqa: E402
from engine.scenes import build_scene  # noqa: E402
from engine.spec import CHANNELS, DEFAULTS, channels_at  # noqa: E402

KIT = None
RESOLVED = None


def _args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = argv[1:]
    out = {}
    if not argv:
        raise SystemExit("missing resolved json")
    out["spec"] = argv[0]
    out["out"] = None
    out["frames"] = "1"
    out["samples"] = 8
    out["scale"] = 1.0
    i = 1
    while i < len(argv):
        key = argv[i]
        if key == "--out":
            out["out"] = argv[i + 1]
            i += 2
        elif key == "--frames":
            out["frames"] = argv[i + 1]
            i += 2
        elif key == "--samples":
            out["samples"] = int(argv[i + 1])
            i += 2
        elif key == "--scale":
            out["scale"] = float(argv[i + 1])
            i += 2
        else:
            raise SystemExit(f"unknown arg {key}")
    return out


def _parse_frames(text, count):
    frames = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if part == "all":
            return list(range(1, count + 1))
        if ":" in part and "-" in part:
            span, step = part.split(":")
            a, b = span.split("-")
            frames.extend(range(int(a), int(b) + 1, int(step)))
        elif "-" in part:
            a, b = part.split("-")
            frames.extend(range(int(a), int(b) + 1))
        else:
            frames.append(int(part))
    return frames


def _clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _init_props(scene, resolved):
    for name in CHANNELS:
        scene[name] = float(DEFAULTS[name])
    opening = resolved.get("opening") or {}
    for name, value in opening.items():
        scene[name] = float(value)


def _key_channels(scene, resolved):
    for name, keys in resolved["channels"].items():
        for frame, value in keys:
            scene[name] = float(value)
            scene.keyframe_insert(data_path=f'["{name}"]', frame=int(frame))
    if scene.animation_data and scene.animation_data.action:
        set_linear_keys(scene.animation_data.action)


def _look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _camera(scene, resolved):
    cam_spec = resolved.get("camera") or {}
    data = bpy.data.cameras.new("Camera")
    data.type = cam_spec.get("type", "PERSP")
    data.lens = float(cam_spec.get("lens", 40))
    data.sensor_fit = cam_spec.get("sensor_fit", "VERTICAL")
    data.sensor_height = float(cam_spec.get("sensor_height", 24))
    if cam_spec.get("sensor_width"):
        data.sensor_width = float(cam_spec["sensor_width"])
    data.clip_start = 0.5
    data.clip_end = float(cam_spec.get("clip_end", 4000.0))
    data.dof.use_dof = False
    obj = bpy.data.objects.new("Camera", data)
    scene.collection.objects.link(obj)
    loc = cam_spec.get("location") or [20.5, -30.5, 18.5]
    target = cam_spec.get("target") or [2.2, 1.4, 2.4]
    obj.location = loc
    _look_at(obj, target)
    locked = (cam_spec.get("mode") or "locked") != "pov"
    obj.lock_location = (locked, locked, locked)
    obj.lock_rotation = (locked, locked, locked)
    scene.camera = obj
    return obj


def _render_settings(scene, resolved, samples, scale):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(samples)
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception as exc:
        print("denoiser", exc)
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.08
    scene.cycles.adaptive_min_samples = max(1, min(4, int(samples)))
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 1
    scene.cycles.transmission_bounces = 2
    scene.cycles.volume_bounces = 0
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.sample_clamp_indirect = 3.0
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.cycles.use_light_tree = False
    try:
        scene.cycles.use_fast_gi = True
        scene.world.light_settings.ao_factor = 1.0
        scene.world.light_settings.distance = 1.6
    except Exception as exc:
        print("ao", exc)
    scene.render.use_motion_blur = False
    scene.render.use_persistent_data = True
    scene.render.resolution_x = int(resolved["width"])
    scene.render.resolution_y = int(resolved["height"])
    scene.render.resolution_percentage = int(round(scale * 100))
    scene.render.fps = int(resolved["fps"])
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.frame_start = 1
    scene.frame_end = int(resolved["frame_count"])


def _on_frame(scene, *args):
    if KIT is None or RESOLVED is None:
        return
    ch = channels_at(RESOLVED, scene.frame_current)
    apply(KIT, ch, scene.frame_current, RESOLVED["fps"])
    apply_pov(scene, KIT, RESOLVED, scene.frame_current)


def main():
    global KIT, RESOLVED
    opts = _args(sys.argv)
    with open(opts["spec"], "r", encoding="utf-8") as handle:
        RESOLVED = json.load(handle)
    out = Path(opts["out"] or "/tmp/whatif_frames")
    out.mkdir(parents=True, exist_ok=True)
    _clear()
    scene = bpy.context.scene
    _init_props(scene, RESOLVED)
    features = RESOLVED.get("features") or {}
    print("building", RESOLVED["id"], "features", {k: v for k, v in features.items() if v})
    KIT = build_scene(scene, RESOLVED, features)
    print("objects", len(KIT.items), "kind", KIT.kind)
    _key_channels(scene, RESOLVED)
    _camera(scene, RESOLVED)
    skin = KIT.mats.get("trim") or KIT.mats.get("car")
    if skin is not None:
        attach_pov(scene, KIT, RESOLVED, skin)
    _render_settings(scene, RESOLVED, opts["samples"], opts["scale"])
    bpy.app.handlers.frame_change_post.append(_on_frame)
    frames = _parse_frames(opts["frames"], RESOLVED["frame_count"])
    print("rendering", frames)
    for frame in frames:
        scene.frame_set(frame)
        _on_frame(scene)
        scene.render.filepath = str(out / f"f_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)


if __name__ == "__main__":
    main()
