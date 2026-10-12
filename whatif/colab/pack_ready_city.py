"""Build the ready-city episode and write a Colab bundle.

Run with Blender 4.2.3 only. The saved blend must open on Colab's 4.2.3.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, "/workspace/whatif")

from engine import build as build_mod  # noqa: E402
from engine.effects import apply  # noqa: E402
from engine.spec import beat_at, channels_at  # noqa: E402

RESOLVED = json.loads(Path("/tmp/ready_city_resolved.json").read_text(encoding="utf-8"))
OUT = Path("/tmp/city_decay_bundle")
OUT.mkdir(parents=True, exist_ok=True)
SAMPLES = 64


def _key_hide(obj, frame):
    try:
        obj.keyframe_insert(data_path="hide_render", frame=frame)
    except RuntimeError as exc:
        print("hide key", obj.name, exc)


def _key_xform(obj, frame):
    for path in ("location", "rotation_euler", "scale", "hide_render"):
        try:
            obj.keyframe_insert(data_path=path, frame=frame)
        except RuntimeError:
            pass


def _key_node_value(node, frame, output=True):
    sock = node.outputs[0] if output else node.inputs[1]
    try:
        sock.keyframe_insert(data_path="default_value", frame=frame)
    except RuntimeError as exc:
        print("node key", getattr(node, "name", "?"), exc)


def main():
    build_mod.RESOLVED = RESOLVED
    build_mod._clear()
    scene = bpy.context.scene
    build_mod._init_props(scene, RESOLVED)
    features = RESOLVED.get("features") or {}
    print("building", RESOLVED["id"], flush=True)
    t0 = time.perf_counter()
    kit = build_mod.build_scene(scene, RESOLVED, features)
    build_mod._key_channels(scene, RESOLVED)
    build_mod._camera(scene, RESOLVED)
    print("built", round(time.perf_counter() - t0, 1), "s", "items", len(kit.items), flush=True)

    precip = [obj for _kind, obj, _i in kit.precip]
    rig = getattr(kit, "suspension", None)
    rig_objs = []
    if rig:
        rig_objs = [rig["holder"], rig["deck"], *rig["towers"]]
    last = int(RESOLVED["frame_count"])
    fps = int(RESOLVED["fps"])
    prev = {}

    keyframes = {1, last}
    for keys in RESOLVED["channels"].values():
        for fr, _value in keys:
            keyframes.add(int(fr))
    # People and traffic move through the opening. After that, poses hold.
    keyframes.update(range(1, 96))
    frames = sorted(frame for frame in keyframes if 1 <= frame <= last)
    print("baking", len(frames), "poses of", last, flush=True)
    t1 = time.perf_counter()
    for frame in frames:
        ch = channels_at(RESOLVED, frame)
        kit.beat_id = beat_at(RESOLVED, frame)["id"]
        apply(kit, ch, frame, fps)
        _key_xform(kit.sun, frame)
        kit.sun.data.keyframe_insert(data_path="energy", frame=frame)
        kit.sun.data.keyframe_insert(data_path="color", frame=frame)
        kit.sun.data.keyframe_insert(data_path="angle", frame=frame)
        _key_xform(kit.fill, frame)
        kit.fill.data.keyframe_insert(data_path="energy", frame=frame)
        if kit.world_bg is not None:
            kit.world_bg.inputs[1].keyframe_insert(data_path="default_value", frame=frame)
        if getattr(kit, "sky_zenith", None) is not None:
            _key_node_value(kit.sky_zenith, frame, output=True)
        if getattr(kit, "sky_horizon", None) is not None:
            _key_node_value(kit.sky_horizon, frame, output=True)
        if getattr(kit, "sky_mix", None) is not None:
            kit.sky_mix.inputs["Fac"].keyframe_insert(data_path="default_value", frame=frame)
        if getattr(kit, "fog_density", None) is not None:
            _key_node_value(kit.fog_density, frame, output=True)
        for obj in precip:
            obj.keyframe_insert(data_path="location", frame=frame)
            _key_hide(obj, frame)
        if kit.water is not None:
            _key_xform(kit.water.obj, frame)
        for obj in rig_objs:
            _key_xform(obj, frame)
        cam = scene.camera
        if cam is not None:
            _key_xform(cam, frame)
            cam.data.keyframe_insert(data_path="lens", frame=frame)
        for item in kit.items:
            obj = item.obj
            # Coarse on purpose. Tree sway is not baked; era hides and collapses are.
            state = (
                obj.hide_render,
                round(obj.location.x, 1),
                round(obj.location.z, 2),
                round(obj.rotation_euler.x, 1),
                round(obj.scale.z, 2),
            )
            token = obj.name
            if frame in (1, last) or prev.get(token) != state:
                _key_xform(obj, frame)
                for child in obj.children_recursive:
                    child.hide_render = obj.hide_render
                    _key_hide(child, frame)
                prev[token] = state
        if frame % 30 == 0 or frame == frames[-1]:
            print("baked", frame, flush=True)
    print("bake", round(time.perf_counter() - t1, 1), "s", flush=True)

    scene.frame_start = 1
    scene.frame_end = last
    scene.frame_set(1)
    kit.beat_id = beat_at(RESOLVED, 1)["id"]
    apply(kit, channels_at(RESOLVED, 1), 1, fps)

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.adaptive_min_samples = 8
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 4
    scene.cycles.volume_bounces = 1
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.volume_max_steps = 64
    scene.cycles.volume_step_rate = 1.6
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.filepath = "//frames/"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.use_file_extension = True
    scene.render.use_persistent_data = True
    scene.render.use_motion_blur = False

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_post.clear()
    # Packed images. No addon is required at render time: fog is a shader,
    # the cities are meshes, and the era motion is keyframed.
    bpy.ops.file.pack_all()
    blend = OUT / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    print("saved", blend, blend.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
