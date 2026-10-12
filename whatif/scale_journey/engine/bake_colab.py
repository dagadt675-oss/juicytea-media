"""Bake the penny scene into one packed Blender 4.2 file.

    blender -b --python engine/bake_colab.py

Reads /tmp/penny_colab_frames.json. Writes the blend, a copy of render.py
and manifest.json under /tmp/penny_colab_build/. Preview plates for frames
0 and 200 go to /tmp/penny_colab_preview/ before the keys replace the
live pose, so they are the python-path picture.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
WHATIF = ROOT.parent
for path in (str(WHATIF), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from engine.build_b import SPEED, configure_cycles, pose_frame, prepare_scene, render_frame

GEOM = Path("/tmp/penny_colab_frames.json")
BUILD = Path("/tmp/penny_colab_build")
PREVIEW = Path("/tmp/penny_colab_preview")


def _bone_rec(bone):
    return (
        bone.rotation_mode,
        tuple(bone.location),
        tuple(bone.rotation_euler),
        tuple(bone.rotation_quaternion),
        tuple(bone.scale),
    )


def _apply_bone(bone, rec):
    mode, loc, eul, quat, scale = rec
    bone.rotation_mode = mode
    bone.location = loc
    bone.scale = scale
    if mode == "QUATERNION":
        bone.rotation_quaternion = quat
    else:
        bone.rotation_euler = eul


def _xf(obj):
    return (tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale))


def _put_xf(obj, rec):
    obj.location, obj.rotation_euler, obj.scale = rec


def _linear(anim):
    if anim is None or anim.action is None:
        return
    for curve in anim.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"


def _snapshot(cam, penny, hosts):
    arms = {}
    for obj in bpy.data.objects:
        if obj.type != "ARMATURE":
            continue
        arms[obj.name] = {bone.name: _bone_rec(bone) for bone in obj.pose.bones}
    hidden = [obj.name for obj in bpy.data.objects if obj.hide_render]
    return {
        "cam": _xf(cam),
        "lens": float(cam.data.lens),
        "penny": _xf(penny),
        "hosts": {name: _xf(bpy.data.objects[name]) for name in hosts if name in bpy.data.objects},
        "arms": arms,
        "hidden": hidden,
    }


def _write_keys(cam, penny, snaps, hosts):
    for obj in list(bpy.data.objects):
        obj.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()
    togglers = set()
    for snap in snaps:
        togglers.update(snap["hidden"])
    for obj in bpy.data.objects:
        if "cull" in obj.keys():
            togglers.add(obj.name)
    for snap in snaps:
        frame = snap["frame"]
        _put_xf(cam, snap["cam"])
        cam.data.lens = snap["lens"]
        # Hold the camera still across the shutter. A linear key smears the
        # city; the python preview exposes the settled camera.
        for sample in (frame - 0.6, float(frame)):
            cam.keyframe_insert("location", frame=sample)
            cam.keyframe_insert("rotation_euler", frame=sample)
            cam.data.keyframe_insert("lens", frame=sample)
        # Same hold as the camera. A linear key across the shutter smears the
        # penny out of the close 24 mm frame; the preview exposes the settled coin.
        _put_xf(penny, snap["penny"])
        for sample in (frame - 0.6, float(frame)):
            penny.keyframe_insert("location", frame=sample)
            penny.keyframe_insert("rotation_euler", frame=sample)
            penny.keyframe_insert("scale", frame=sample)
        for name, rec in snap["hosts"].items():
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            _put_xf(obj, rec)
            obj.keyframe_insert("location", frame=frame)
            obj.keyframe_insert("rotation_euler", frame=frame)
            obj.keyframe_insert("scale", frame=frame)
        hidden = set(snap["hidden"])
        for name in togglers:
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            obj.hide_render = name in hidden
            obj.keyframe_insert("hide_render", frame=frame)
        for arm_name, bones in snap["arms"].items():
            arm = bpy.data.objects.get(arm_name)
            if arm is None or arm.pose is None:
                continue
            for bone_name, rec in bones.items():
                bone = arm.pose.bones.get(bone_name)
                if bone is None:
                    continue
                _apply_bone(bone, rec)
                bone.keyframe_insert("location", frame=frame)
                bone.keyframe_insert("scale", frame=frame)
                if rec[0] == "QUATERNION":
                    bone.keyframe_insert("rotation_quaternion", frame=frame)
                else:
                    bone.keyframe_insert("rotation_euler", frame=frame)
        if frame % 50 == 0:
            print(f"KEYS {frame}", flush=True)
    for anim in (cam.animation_data, cam.data.animation_data):
        if anim is None or anim.action is None:
            continue
        for curve in anim.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"
    _linear(penny.animation_data)
    for name in hosts:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            _linear(obj.animation_data)
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE" or "cull" in obj.keys():
            _linear(obj.animation_data)


def main():
    rows = json.loads(GEOM.read_text(encoding="utf-8"))
    limit = int(os.environ.get("BAKE_LIMIT", "0"))
    if limit:
        rows = rows[:limit]
    job = {
        "width": 1080,
        "height": 1920,
        "scale": 100,
        "samples": 24,
        "hdri": str(ROOT / "assets" / "hdri" / "sunset_jhbcentral_1k.hdr"),
    }
    scene, cam, penny, arms = prepare_scene(job, lod=False)
    configure_cycles(scene, job, SPEED)
    scene.render.fps = 30
    scene.frame_start = 0
    scene.frame_end = 1001
    PREVIEW.mkdir(parents=True, exist_ok=True)
    by_frame = {int(row["frame"]): row for row in rows}
    for frame in (0, 200):
        if frame not in by_frame:
            continue
        if os.environ.get("SKIP_PREVIEW") == "1":
            break
        render_frame(scene, cam, penny, arms, by_frame[frame], PREVIEW / f"f_{frame:04d}.png", SPEED)
        print(f"PREVIEW {frame}", flush=True)
    from engine.manhattan import MOVERS

    hosts = set()
    for empty, *_rest in MOVERS:
        hosts.add(empty.name)
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            hosts.add((obj.parent or obj).name)
    snaps = []
    for index, fr in enumerate(rows):
        pose_frame(scene, cam, penny, arms, fr, SPEED)
        snap = _snapshot(cam, penny, hosts)
        snap["frame"] = int(fr["frame"])
        snaps.append(snap)
        if index % 25 == 0:
            print(f"SNAP {fr['frame']}", flush=True)
    print(f"SNAP_DONE {len(snaps)}", flush=True)
    _write_keys(cam, penny, snaps, hosts)
    for image in bpy.data.images:
        if image.packed_file is None and image.filepath:
            try:
                image.pack()
            except Exception as exc:
                print(f"PACK FAIL {image.name} {exc}", flush=True)
    try:
        bpy.ops.file.pack_all()
    except Exception as exc:
        print(f"PACK_ALL {exc}", flush=True)
    for image in bpy.data.images:
        if image.packed_file is not None:
            image.filepath = "//" + image.name.replace(" ", "_")
            image.filepath_raw = image.filepath
    BUILD.mkdir(parents=True, exist_ok=True)
    blend = BUILD / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, relative_remap=False)
    unpacked = [
        f"{image.name} {image.filepath}"
        for image in bpy.data.images
        if image.packed_file is None and image.filepath and image.source == "FILE"
    ]
    print("UNPACKED", unpacked, flush=True)
    shutil.copyfile(ROOT / "colab" / "render.py", BUILD / "render.py")
    print(f"BLEND {blend} bytes {blend.stat().st_size}", flush=True)
    manifest = {
        "episode": "penny_empire",
        "blender_version": "4.2.3",
        "frame_start": 0,
        "frame_end": 1001,
        "fps": 30,
        "resolution": [1080, 1920],
        "samples": 24,
        "est_seconds_per_frame_on_your_cpu": 38,
        "cpu_note": "4-core VM, Cycles CPU, same settings as this file. Median 38 s, p90 40 s, over 82 measured frames. Two frames spiked (619 s and 1560 s).",
        "engine": "CYCLES",
        "device": "OPTIX, else CUDA. render.py enables every non-CPU device.",
        "adaptive_threshold": 0.01,
        "adaptive_min_samples": 1,
        "denoiser": "OPENIMAGEDENOISE",
        "bounces": 12,
        "motion_blur_shutter": 0.6,
        "motion_blur_position": "END",
        "view_transform": "AgX",
        "look": "AgX - Medium High Contrast",
        "exposure": 0.55,
        "duration_sec": 33.4,
        "output": "frames/####.png beside scene.blend (frames/0000.png through frames/1001.png)",
        "command": "blender -b scene.blend -P render.py -- START END",
        "description": (
            "Empire State Building by NanoRay (CC-BY, Sketchfab). "
            "Shrugging by Rida.Sidi.Ben.Ali (CC-BY, Sketchfab)."
        ),
        "audio": {
            "narration": "Brian, Eleven v4, single take. Align penny_words.json. Duration 33.400 s.",
            "words": "penny_words.json",
            "sfx": "penny_empire_sfx.json",
            "music": False,
        },
        "edit": {
            "plates": "Silent 3D only. The counter, word-by-word karaoke, the red ring on the pedestrian, and the NO AIR ~200 MPH pill are composited after these plates.",
            "loop": "Frame 1001 is the opening pose. Copy frames/0000.png over frames/1001.png so the seam has no motion smear.",
            "hud": "Height stays 1,250 ft until 15.44 s, then 500, 200, 100, 80, 40, and 0 ft on those words. Speed stays 0 until 5.34 s, then 10, 20, and 25 mph. The 25 mph lock is the 40.3 km/h terminal velocity.",
            "shots": "0-2.40 s macro on the deck, 32 mm, camera holds. 2.40-2.90 s blend to the 24 mm drone. Drone follows down the facade until 19.07 s, with the overhead pedestrian insert at 13.31-15.10 s. 19.07-19.45 s blend to the static street shot. That shot holds through the bonk at 21.073 s and the reaction until 27.71 s, then the camera rises back to the opening.",
            "reaction": "Flinch at 21.07 s, look around at 21.85 s, scratch at 22.55 s, shrug at 23.27 s, walk from 23.85 s.",
            "captions": "Karaoke from penny_words.json, in the safe band around 68% down the frame.",
        },
        "camera_motion": "Camera keys hold still across the 0.6 shutter so the city stays as sharp as the preview. The coin is held across that same shutter so the close 24 mm frame keeps it. Between frames the coin still advances.",
    }
    (BUILD / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("MANIFEST description credits NanoRay and Rida.Sidi.Ben.Ali", flush=True)
    print("BAKE_DONE", flush=True)


if __name__ == "__main__":
    main()
