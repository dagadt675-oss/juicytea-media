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
from engine.segments import MOTION_BLUR_SHUTTER, frame_seed  # noqa: E402
from engine.spec import CHANNELS, DEFAULTS, beat_at, channels_at, sample_camera_path  # noqa: E402

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
    out["format"] = "png"
    out["motion_blur"] = False
    out["denoise"] = True
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
        elif key == "--format":
            out["format"] = argv[i + 1]
            i += 2
        elif key == "--motion-blur":
            out["motion_blur"] = True
            i += 1
        elif key == "--no-denoise":
            out["denoise"] = False
            i += 1
        else:
            raise SystemExit(f"unknown arg {key}")
    if out["format"] not in ("png", "exr"):
        raise SystemExit(f"unsupported format {out['format']}")
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


def _frame_float(scene):
    return float(scene.frame_current) + float(getattr(scene, "frame_subframe", 0.0))


def _render_settings(scene, resolved, samples, scale, image_format="png", motion_blur=False, denoise=True):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(samples)
    scene.cycles.use_denoising = bool(denoise)
    denoiser = "OPENIMAGEDENOISE"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.get_devices()
        if any(device.type == "OPTIX" and device.use for device in prefs.devices):
            denoiser = "OPTIX"
    except Exception as exc:
        print("denoiser probe", exc)
    try:
        scene.cycles.denoiser = denoiser
    except Exception as exc:
        print("denoiser", exc)
        try:
            scene.cycles.denoiser = "OPENIMAGEDENOISE"
        except Exception as fallback:
            print("denoiser", fallback)
    scene.cycles.use_adaptive_sampling = True
    if int(samples) >= 64:
        scene.cycles.adaptive_threshold = 0.01
        scene.cycles.adaptive_min_samples = min(16, int(samples))
        scene.cycles.max_bounces = 6
        scene.cycles.diffuse_bounces = 4
        scene.cycles.glossy_bounces = 4
        scene.cycles.transmission_bounces = 4
        scene.cycles.volume_bounces = 1
        scene.cycles.volume_max_steps = 64
        scene.cycles.volume_step_rate = 1.6
    else:
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
        scene.world.light_settings.ao_factor = 0.65
        scene.world.light_settings.distance = 3.2
    except Exception as exc:
        print("ao", exc)
    # Shutter is centered and one frame wide, which the segment handles cover.
    # The seed stays on the integer frame so a segment matches a full render.
    scene.render.use_motion_blur = bool(motion_blur)
    if motion_blur:
        scene.render.motion_blur_shutter = MOTION_BLUR_SHUTTER
        try:
            scene.render.motion_blur_position = "CENTER"
        except TypeError as exc:
            print("motion blur", exc)
    try:
        scene.cycles.use_animated_seed = False
    except Exception as exc:
        print("seed", exc)
    scene.render.use_persistent_data = True
    scene.render.resolution_x = int(resolved["width"])
    scene.render.resolution_y = int(resolved["height"])
    scene.render.resolution_percentage = int(round(scale * 100))
    scene.render.fps = int(resolved["fps"])
    if image_format == "exr":
        scene.render.image_settings.file_format = "OPEN_EXR"
        scene.render.image_settings.color_mode = "RGB"
        scene.render.image_settings.color_depth = "16"
        try:
            scene.render.image_settings.exr_codec = "ZIP"
        except TypeError as exc:
            print("exr", exc)
    else:
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"
        scene.render.image_settings.color_depth = "8"
        scene.render.image_settings.compression = 15
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Base Contrast"
    except TypeError:
        scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.42
    scene.view_settings.gamma = 1.0
    try:
        scene.use_nodes = True
        nt = scene.node_tree
        if nt and "Bloom" not in nt.nodes:
            glare = nt.nodes.new("CompositorNodeGlare")
            glare.name = "Bloom"
            glare.glare_type = "FOG_GLOW"
            glare.quality = "MEDIUM"
            glare.mix = -0.65
            glare.threshold = 0.6
            layers = nt.nodes.get("Render Layers")
            composite = nt.nodes.get("Composite")
            if layers and composite:
                for link in list(nt.links):
                    if link.to_node == composite and link.to_socket == composite.inputs.get("Image"):
                        nt.links.remove(link)
                nt.links.new(layers.outputs["Image"], glare.inputs["Image"])
                nt.links.new(glare.outputs["Image"], composite.inputs["Image"])
    except Exception as exc:
        print("bloom", exc)
    scene.frame_start = 1
    scene.frame_end = int(resolved["frame_count"])


def _pose_camera(cam, pose):
    cam.data.type = "PERSP"
    cam.location = pose["location"]
    _look_at(cam, pose["target"])
    cam.data.lens = float(pose["lens"])
    fstop = float(pose.get("fstop") or 0.0)
    cam.data.dof.use_dof = fstop > 0.05
    if fstop > 0.05:
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = (Vector(pose["target"]) - Vector(pose["location"])).length


def _apply_shot_camera(scene, resolved):
    """A film path stays on the street. Without one, a beat may still carry its own camera."""
    frame = _frame_float(scene)
    cam = scene.camera
    if cam is None:
        return
    spec = resolved.get("camera") or {}
    path = spec.get("path")
    if path:
        span = max(1, int(resolved.get("frame_count") or 1) - 1)
        _pose_camera(cam, sample_camera_path(path, (frame - 1.0) / span))
        return
    for beat in resolved.get("beats") or []:
        path = beat.get("camera")
        if not path:
            continue
        start = float(beat["start_frame"])
        end = float(beat["end_frame"])
        if frame < start or frame > end + 0.01:
            continue
        span = max(1.0, end - start)
        _pose_camera(cam, sample_camera_path(path, (frame - start) / span))
        return
    spec = resolved.get("camera") or {}
    if spec.get("location") and spec.get("target"):
        cam.data.type = "PERSP"
        cam.location = spec["location"]
        _look_at(cam, spec["target"])
        cam.data.lens = float(spec.get("lens", 57.2))
        cam.data.dof.use_dof = False


def _on_frame(scene, *args):
    if KIT is None or RESOLVED is None:
        return
    # Subframe time keeps motion blur on the same curve a full render samples.
    frame = _frame_float(scene)
    ch = channels_at(RESOLVED, frame)
    KIT.beat_id = beat_at(RESOLVED, int(frame))["id"]
    apply(KIT, ch, frame, RESOLVED["fps"])
    apply_pov(scene, KIT, RESOLVED, frame)
    _apply_shot_camera(scene, RESOLVED)


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
    image_format = opts["format"]
    _render_settings(
        scene, RESOLVED, opts["samples"], opts["scale"], image_format, opts["motion_blur"], opts["denoise"],
    )
    bpy.app.handlers.frame_change_post.append(_on_frame)
    frames = _parse_frames(opts["frames"], RESOLVED["frame_count"])
    suffix = "exr" if image_format == "exr" else "png"
    print("rendering", frames)
    for frame in frames:
        scene.cycles.seed = frame_seed(frame)
        scene.frame_set(frame)
        _on_frame(scene)
        scene.render.filepath = str(out / f"f_{frame:04d}.{suffix}")
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)


if __name__ == "__main__":
    main()
