"""Place CC0 city kits when the fetch cache is present.

Procedural meshes stay the fallback. People keep their armature so idle,
walk, and the background dance actually play.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

from engine.meshkit import link_obj

CACHE = Path(os.environ.get("CC0_CACHE", "/opt/cursor/asset-cache/cc0")) / "extracted"

_MESHES = {}
_ACTORS = {}
_CAR_YAW = {}


def ready() -> bool:
    return (CACHE / "city_buildings").is_dir() and (CACHE / "nature").is_dir()


def sunny_hdri() -> Path | None:
    path = CACHE / "hdri" / "polyhaven_hdris_2k" / "kloofendal_48d_partly_cloudy_puresky" / "kloofendal_48d_partly_cloudy_puresky_2k.hdr"
    return path if path.exists() else None


def _glb(root: Path, name: str) -> Path:
    return root / name


def _import_objects(path: Path):
    before = set(bpy.data.objects)
    suffix = path.suffix.lower()
    if suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


def _bounds(objs):
    xs, ys, zs = [], [], []
    for obj in objs:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            xs.append(world.x)
            ys.append(world.y)
            zs.append(world.z)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def _mesh_size(mesh):
    xs = [vert.co.x for vert in mesh.vertices]
    ys = [vert.co.y for vert in mesh.vertices]
    zs = [vert.co.z for vert in mesh.vertices]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def _sit_on_ground(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mesh = obj.data
    xs = [vert.co.x for vert in mesh.vertices]
    ys = [vert.co.y for vert in mesh.vertices]
    zs = [vert.co.z for vert in mesh.vertices]
    dx = (min(xs) + max(xs)) * 0.5
    dy = (min(ys) + max(ys)) * 0.5
    dz = min(zs)
    for vert in mesh.vertices:
        vert.co.x -= dx
        vert.co.y -= dy
        vert.co.z -= dz


def static_mesh(path: Path, rotate_z=0.0):
    key = (str(path), round(rotate_z, 4))
    if key in _MESHES:
        return _MESHES[key]
    new = _import_objects(path)
    meshes = [obj for obj in new if obj.type == "MESH"]
    if not meshes:
        _MESHES[key] = None
        return None
    if abs(rotate_z) > 1e-4:
        for obj in meshes:
            obj.rotation_euler.z += rotate_z
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    _sit_on_ground(obj)
    mesh = obj.data
    mesh.name = "cc0_" + path.stem
    for item in new:
        if item == obj:
            continue
        try:
            bpy.data.objects.remove(item, do_unlink=True)
        except ReferenceError:
            pass
    bpy.data.objects.remove(obj, do_unlink=True)
    _MESHES[key] = mesh
    return mesh


def _spawn(coll, mesh, loc, yaw, scale, name):
    obj = link_obj(name, mesh, coll)
    obj.location = loc
    obj.rotation_euler.z = yaw
    if isinstance(scale, (int, float)):
        obj.scale = (scale, scale, scale)
    else:
        obj.scale = scale
    return obj


def place_tower(coll, x, y, z, height):
    root = CACHE / "city_buildings" / "kenney_city_kit_commercial" / "Models" / "GLB format"
    names = (
        "building-skyscraper-a.glb",
        "building-skyscraper-b.glb",
        "building-skyscraper-c.glb",
        "building-skyscraper-d.glb",
        "building-skyscraper-e.glb",
    )
    path = root / names[int(abs(x) * 3 + y) % len(names)]
    mesh = static_mesh(path)
    if mesh is None:
        return None
    native_h = _mesh_size(mesh)[2]
    scale = float(height) / max(native_h, 0.01)
    return _spawn(coll, mesh, (x, y, z), 0.0, scale, "tower")


def place_tree(coll, x, y, z, height, kind="round"):
    folder = CACHE / "nature" / "quaternius_stylized_nature_megakit" / "glTF"
    if kind == "pine":
        names = ("Pine_1.gltf", "Pine_2.gltf", "Pine_3.gltf", "Pine_4.gltf", "Pine_5.gltf")
    elif kind == "dead":
        names = ("DeadTree_1.gltf", "DeadTree_2.gltf", "DeadTree_3.gltf")
    else:
        names = ("CommonTree_1.gltf", "CommonTree_2.gltf", "CommonTree_3.gltf", "CommonTree_4.gltf", "CommonTree_5.gltf", "TwistedTree_1.gltf", "TwistedTree_2.gltf")
    path = folder / names[int(abs(x * 7 + y)) % len(names)]
    mesh = static_mesh(path)
    if mesh is None:
        return None
    native_h = _mesh_size(mesh)[2]
    scale = float(height) / max(native_h, 0.01)
    return _spawn(coll, mesh, (x, y, z), (x * 0.17) % math.tau, scale, "tree")


def _car_yaw_fix(path: Path) -> float:
    """Rotate so the nose points along +X. Kenney cars are longer on Y."""
    if path in _CAR_YAW:
        return _CAR_YAW[path]
    new = _import_objects(path)
    fronts = [obj for obj in new if obj.type == "MESH" and "front" in obj.name.lower()]
    backs = [obj for obj in new for _ in (0,) if obj.type == "MESH" and "back" in obj.name.lower()]
    yaw = 0.0
    if fronts and backs:
        fy = sum(obj.location.y for obj in fronts) / len(fronts)
        by = sum(obj.location.y for obj in backs) / len(backs)
        fx = sum(obj.location.x for obj in fronts) / len(fronts)
        bx = sum(obj.location.x for obj in backs) / len(backs)
        # Angle of the nose from +X. Rotate the mesh by the opposite amount.
        yaw = -math.atan2(fy - by, fx - bx)
    for obj in new:
        bpy.data.objects.remove(obj, do_unlink=True)
    _CAR_YAW[path] = yaw
    return yaw


def place_car(coll, x, y, z, yaw):
    root = CACHE / "vehicles" / "kenney_car_kit" / "Models" / "GLB format"
    names = ("sedan.glb", "taxi.glb", "suv.glb", "hatchback-sports.glb", "van.glb")
    path = root / names[int(abs(x)) % len(names)]
    fix = _car_yaw_fix(path)
    mesh = static_mesh(path, rotate_z=fix)
    if mesh is None:
        return None
    size = _mesh_size(mesh)
    length = max(size[0], size[1])
    scale = 4.6 / max(length, 0.01)
    return _spawn(coll, mesh, (x, y, z), yaw, scale, "car")


def _road_mesh(filename: str):
    path = CACHE / "city_buildings" / "quaternius_downtown_city_megakit" / "Exports" / "glTF (Godot)" / filename
    mesh = static_mesh(path)
    if mesh is None:
        return None, 1.0, 1.0
    size = _mesh_size(mesh)
    # Length runs along local X after we rotate a Y-long tile.
    if size[1] > size[0]:
        mesh = static_mesh(path, rotate_z=math.pi / 2.0)
        size = _mesh_size(mesh)
    return mesh, size[0], size[1]


def _tile(coll, mesh, span, along, center, z, scale, step, yaw):
    start, stop = span
    cursor = start
    while cursor < stop:
        if along == "x":
            loc = (cursor + step * 0.5, center, z)
        else:
            loc = (center, cursor + step * 0.5, z)
        _spawn(coll, mesh, loc, yaw, scale, "street")
        cursor += step
    return True


def place_avenue(coll, y, z, x0=-120.0, x1=80.0, width=16.0):
    mesh, length, native_w = _road_mesh("Street_4Lane.gltf")
    if mesh is None:
        return False
    scale = float(width) / max(native_w, 0.01)
    step = max(2.0, length * scale * 0.98)
    return _tile(coll, mesh, (x0, x1), "x", y, z, scale, step, 0.0)


def place_side_street(coll, x, y0, y1, z, width=9.0):
    mesh, length, native_w = _road_mesh("Street_2Lane.gltf")
    if mesh is None:
        return False
    scale = float(width) / max(native_w, 0.01)
    step = max(2.0, length * scale * 0.98)
    return _tile(coll, mesh, (y0, y1), "y", x, z, scale, step, math.pi / 2.0)


def _hide(obj):
    obj.hide_render = True
    obj.hide_viewport = True
    for child in obj.children:
        _hide(child)


def _clone(root, coll):
    originals = []

    def walk(obj):
        originals.append(obj)
        for child in obj.children:
            walk(child)

    walk(root)
    mapping = {}
    for obj in originals:
        copy = obj.copy()
        coll.objects.link(copy)
        copy.hide_render = False
        copy.hide_viewport = False
        mapping[obj] = copy
    for obj, copy in mapping.items():
        if obj.parent in mapping:
            copy.parent = mapping[obj.parent]
            copy.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
        if obj.type == "MESH":
            for mod, copied in zip(obj.modifiers, copy.modifiers):
                target = getattr(mod, "object", None)
                if mod.type == "ARMATURE" and target in mapping:
                    copied.object = mapping[target]
    return mapping[root]


def _actor(path: Path):
    key = str(path)
    if key in _ACTORS:
        return _ACTORS[key]
    new = _import_objects(path)
    arm = next((obj for obj in new if obj.type == "ARMATURE"), None)
    if arm is None:
        _ACTORS[key] = None
        return None
    bounds = _bounds(new)
    height = 1.0 if bounds is None else max(0.2, bounds[5] - bounds[4])
    actions = {action.name.split("|")[-1]: action for action in bpy.data.actions}
    _hide(arm)
    _ACTORS[key] = {"arm": arm, "height": height, "actions": actions}
    return _ACTORS[key]


def _play(arm, action, offset):
    data = arm.animation_data_create()
    data.action = None
    track = data.nla_tracks.new()
    strip = track.strips.new(action.name[-24:], 1, action)
    strip.frame_start = 1 - int(offset) % 40
    strip.repeat = 40
    try:
        strip.extrapolation = "HOLD_FORWARD"
    except TypeError:
        pass


def place_actor(coll, path: Path, loc, yaw, target_height, clip, offset=0):
    proto = _actor(path)
    if proto is None or clip not in proto["actions"]:
        # Fall back to any idle-like clip.
        if proto is None:
            return None
        clip = next((name for name in ("Idle", "Idle_Loop", "Idle_Neutral", "Eating") if name in proto["actions"]), None)
        if clip is None:
            return None
    root = _clone(proto["arm"], coll)
    # Scale an empty parent. Scaling the armature alone stretches the skin
    # into spikes because the mesh is bound to the bones.
    empty = bpy.data.objects.new("actor", None)
    coll.objects.link(empty)
    root.parent = empty
    root.matrix_parent_inverse.identity()
    scale = float(target_height) / proto["height"]
    empty.scale = (scale, scale, scale)
    empty.location = loc
    empty.rotation_euler.z = yaw
    action = proto["actions"].get(clip) or next(iter(proto["actions"].values()))
    _play(root, action, offset)
    return empty


_PEOPLE = None


def _people():
    global _PEOPLE
    if _PEOPLE is None:
        men = CACHE / "characters" / "quaternius_ultimate_modular_men" / "glb"
        women = CACHE / "characters" / "quaternius_ultimate_modular_women" / "glb"
        names = (
            "Casual_Character_kZ3DmIoGip.glb",
            "Hoodie_Character_gKLBoRsyKe.glb",
            "Worker_Yg2bQZO6Hj.glb",
            "Beach_Character_DojKLcO34E.glb",
            "Business_Man_JFrLIKqvCH.glb",
            "Punk_BTALZymknF.glb",
        )
        paths = [men / name for name in names if (men / name).exists()]
        for path in sorted(women.glob("*.glb")):
            if "Astronaut" in path.name or "Hooded" in path.name:
                continue
            paths.append(path)
        _PEOPLE = paths
    return _PEOPLE


def place_person(coll, x, y, z, yaw, clip="Idle", offset=0):
    paths = _people()
    if not paths:
        return None
    path = paths[int(abs(x * 3 + y * 5)) % len(paths)]
    return place_actor(coll, path, (x, y, z), yaw, 1.75, clip, offset)


def place_dancer(coll, x, y, z):
    path = CACHE / "animations" / "quaternius_universal_animation_library" / "Universal Animation Library[Standard]" / "Unreal-Godot" / "UAL1_Standard.glb"
    if not path.exists():
        return None
    return place_actor(coll, path, (x, y, z), 0.4, 1.75, "Dance_Loop", offset=3)


def place_deer(coll, x, y, z):
    path = CACHE / "animals" / "quaternius_ultimate_animated_animals" / "glb" / "Deer_T6Cs7tmMHJ.glb"
    if not path.exists():
        return None
    return place_actor(coll, path, (x, y, z), 1.2, 1.55, "Eating", offset=8)
