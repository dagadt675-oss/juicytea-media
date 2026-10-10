"""Format C camera choice: locked wide, or one unbroken POV path.

Episode 1 uses the default locked camera and never builds arms.
A POV spec lists path keys in seconds. `grab` names a prop the hands reach for.
The arms are two cylinders aimed at that point. A later IK rig can replace
`aim_arms` without changing the spec.

The picnic park and the cartoon cat (idle, float, held) are not built yet.
They should be self-made or CC0. See docs/whatif_slate.md.
"""

from __future__ import annotations

import bpy
from mathutils import Vector

from engine.meshkit import cylinder_mesh, link_obj


def _look_at(obj, target):
    direction = Vector(target) - obj.location
    if direction.length < 1e-5:
        return
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def sample_path(path, t):
    """Linear blend between path keys. Returns location, target, grab name."""
    if not path:
        return Vector((0, 0, 1.6)), Vector((0, 1, 1.4)), None
    keys = sorted(path, key=lambda item: float(item.get("t", 0)))
    if t <= float(keys[0].get("t", 0)):
        key = keys[0]
        return Vector(key["location"]), Vector(key.get("target") or key["location"]), key.get("grab")
    for a, b in zip(keys, keys[1:]):
        t0, t1 = float(a.get("t", 0)), float(b.get("t", 0))
        if t <= t1:
            span = max(1e-4, t1 - t0)
            u = (t - t0) / span
            loc = Vector(a["location"]).lerp(Vector(b["location"]), u)
            ta = Vector(a.get("target") or a["location"])
            tb = Vector(b.get("target") or b["location"])
            grab = b.get("grab") if u > 0.5 else a.get("grab")
            return loc, ta.lerp(tb, u), grab
    last = keys[-1]
    return Vector(last["location"]), Vector(last.get("target") or last["location"]), last.get("grab")


def _arm(name, coll, mat):
    mesh = cylinder_mesh(name, radius=1.0, segments=8)
    upper = link_obj(name + "_upper", mesh, coll, (mat,))
    fore = link_obj(name + "_fore", mesh, coll, (mat,))
    upper.scale = (0.06, 0.06, 0.34)
    fore.scale = (0.05, 0.05, 0.32)
    return upper, fore


def attach_pov(scene, kit, resolved, skin):
    """Parent cylinder arms to the camera. No-op unless camera.mode is pov."""
    spec = resolved.get("camera") or {}
    if spec.get("mode", "locked") != "pov":
        return
    coll = kit.collection("POV")
    left = _arm("arm_l", coll, skin)
    right = _arm("arm_r", coll, skin)
    for piece in left + right:
        piece.parent = scene.camera
        piece.matrix_parent_inverse.identity()
    kit.arms = {"left": left, "right": right}
    kit.grab_points = {}
    for name, loc in (spec.get("grabs") or {}).items():
        empty = bpy.data.objects.new(f"grab_{name}", None)
        empty.empty_display_type = "SPHERE"
        empty.empty_display_size = 0.08
        empty.location = loc
        coll.objects.link(empty)
        kit.grab_points[name] = empty


def _rest(arms):
    # Local to the camera: forearms hang in the lower third of the view.
    poses = {
        "left": ((-0.22, -0.35, -0.25), (-0.28, -0.55, -0.45)),
        "right": ((0.22, -0.35, -0.25), (0.28, -0.55, -0.45)),
    }
    for side, (upper_loc, fore_loc) in poses.items():
        upper, fore = arms[side]
        upper.location = upper_loc
        fore.location = fore_loc
        upper.rotation_euler = (0.6, 0, 0)
        fore.rotation_euler = (0.4, 0, 0)


def aim_arms(cam, arms, grab_world):
    """Point both forearms toward a world point, in camera space.

    This is the stand-in for an IK chain. Replace this function when the
    arm rig exists. The spec's grab names stay the same.
    """
    if grab_world is None:
        _rest(arms)
        return
    local = cam.matrix_world.inverted() @ Vector(grab_world)
    for side, sign in (("left", -1), ("right", 1)):
        upper, fore = arms[side]
        upper.location = (0.2 * sign, -0.22, -0.18)
        upper.rotation_euler = (0.5, 0.0, 0.0)
        fore.location = (0.22 * sign, min(-0.2, local.y * 0.45), min(-0.1, local.z))
        direction = local - Vector(fore.location)
        if direction.length > 1e-4:
            fore.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


def apply_pov(scene, kit, resolved, frame):
    spec = resolved.get("camera") or {}
    if spec.get("mode", "locked") != "pov":
        return
    path = spec.get("path") or []
    if not path or scene.camera is None:
        return
    t = (frame - 1) / float(resolved.get("fps") or 30)
    loc, target, grab = sample_path(path, t)
    scene.camera.location = loc
    _look_at(scene.camera, target)
    if getattr(kit, "arms", None):
        point = None
        if grab and grab in getattr(kit, "grab_points", {}):
            point = kit.grab_points[grab].matrix_world.translation
        aim_arms(scene.camera, kit.arms, point)
