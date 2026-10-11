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
# Sketchfab Free Standard lives here. Rendered videos only. Never commit it.
PRIVATE = Path(os.environ.get("PRIVATE_CACHE", "/opt/cursor/asset-cache/private"))

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
    return place_fleet_car(coll, (x, y, z), yaw, index=int(abs(x)))


# Real-world size. Length runs along +X after the mesh is baked. Kenney's
# car kit (sedan, yellow taxi, SUV, van) is the CC0 fleet in the hub. The
# low-poly mini pack reads as a toy at this camera, so it is not used here.
_FLEET = (
    ("sedan.glb", 4.8, 1.80, 1.45),
    ("taxi.glb", 4.8, 1.80, 1.55),
    ("suv.glb", 4.9, 1.95, 1.75),
    ("hatchback-sports.glb", 4.4, 1.78, 1.40),
    ("sedan-sports.glb", 4.7, 1.85, 1.38),
    ("suv-luxury.glb", 5.1, 2.00, 1.72),
    ("van.glb", 5.3, 2.00, 2.05),
    ("delivery.glb", 6.5, 2.15, 2.55),
    ("truck.glb", 8.2, 2.45, 3.10),
)
_FLEET_MESH = {}
_CONTACT = None


def _contact_mesh():
    global _CONTACT
    if _CONTACT is not None:
        return _CONTACT
    import bmesh

    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=1.0)
    me = bpy.data.meshes.new("contact")
    bm.to_mesh(me)
    bm.free()
    _CONTACT = me
    return me


def _fleet_mesh(filename, length, width, height):
    key = filename
    if key in _FLEET_MESH:
        return _FLEET_MESH[key]
    path = CACHE / "vehicles" / "kenney_car_kit" / "Models" / "GLB format" / filename
    if not path.exists():
        _FLEET_MESH[key] = None
        return None
    new = _import_objects(path)
    meshes = [obj for obj in new if obj.type == "MESH"]
    if not meshes:
        _FLEET_MESH[key] = None
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    # The long axis is the car. Point the lower end (the hood) along +X.
    if max(ys) - min(ys) >= max(xs) - min(xs):
        obj.rotation_euler.z += math.pi / 2.0
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
    lo, hi = min(xs), max(xs)
    span = max(hi - lo, 1e-4)
    front = [v.co for v in obj.data.vertices if v.co.x < lo + span * 0.22]
    back = [v.co for v in obj.data.vertices if v.co.x > hi - span * 0.22]
    if front and back:
        if sum(p.z for p in front) / len(front) > sum(p.z for p in back) / len(back):
            obj.rotation_euler.z += math.pi
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    sx = float(length) / max(max(xs) - min(xs), 0.01)
    sy = float(width) / max(max(ys) - min(ys), 0.01)
    sz = float(height) / max(max(zs) - min(zs), 0.01)
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    cz = min(zs)
    for vert in obj.data.vertices:
        vert.co.x = (vert.co.x - cx) * sx
        vert.co.y = (vert.co.y - cy) * sy
        vert.co.z = (vert.co.z - cz) * sz
    mesh = obj.data
    mesh.name = "fleet_" + path.stem
    for item in new:
        if item == obj:
            continue
        try:
            bpy.data.objects.remove(item, do_unlink=True)
        except ReferenceError:
            pass
    bpy.data.objects.remove(obj, do_unlink=True)
    _FLEET_MESH[key] = mesh
    return mesh


def _tint_fleet(obj):
    """Object color multiplies the paint so rust can dull it later."""
    for slot in obj.material_slots:
        material = slot.material
        if material is None or material.get("object_tint") or material.node_tree is None:
            continue
        tree = material.node_tree
        bsdf = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None or "Base Color" not in bsdf.inputs:
            continue
        color_in = bsdf.inputs["Base Color"]
        mix = tree.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        if color_in.is_linked:
            source = color_in.links[0].from_socket
            tree.links.remove(color_in.links[0])
            tree.links.new(source, mix.inputs["Color1"])
        else:
            mix.inputs["Color1"].default_value = tuple(color_in.default_value)
        info = tree.nodes.new("ShaderNodeObjectInfo")
        tree.links.new(info.outputs["Color"], mix.inputs["Color2"])
        tree.links.new(mix.outputs["Color"], color_in)
        material["object_tint"] = True
    obj.color = (1.0, 1.0, 1.0, 1.0)


def place_fleet_car(coll, loc, yaw, index=0):
    """A Kenney sedan, taxi, SUV, van, or truck at a real size. Wheels sit on z."""
    filename, length, width, height = _FLEET[int(index) % len(_FLEET)]
    mesh = _fleet_mesh(filename, length, width, height)
    if mesh is None:
        return None
    obj = _spawn(coll, mesh, loc, yaw, 1.0, "car")
    obj.visible_shadow = True
    _tint_fleet(obj)
    disc = _spawn(coll, _contact_mesh(), (0.0, 0.0, 0.015), 0.0, 1.0, "contact")
    disc.parent = obj
    disc.location = (0.0, 0.0, 0.012)
    disc.scale = (length * 0.42, width * 0.46, 1.0)
    disc.visible_shadow = False
    mat = bpy.data.materials.get("CarContact")
    if mat is None:
        mat = bpy.data.materials.new("CarContact")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1.0)
            bsdf.inputs["Roughness"].default_value = 1.0
            if "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = 0.45
        mat.blend_method = "BLEND"
    if mat.name not in [slot.name for slot in disc.data.materials]:
        disc.data.materials.append(mat)
    return obj


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


def _skinned_meshes(arm, objs):
    found = []

    def walk(obj):
        if obj.type == "MESH":
            found.append(obj)
        for child in obj.children:
            walk(child)

    walk(arm)
    for obj in objs:
        if obj.type != "MESH" or obj in found:
            continue
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and getattr(mod, "object", None) == arm:
                found.append(obj)
                break
    return found


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
    before_actions = set(bpy.data.actions)
    new = _import_objects(path)
    arm = next((obj for obj in new if obj.type == "ARMATURE"), None)
    if arm is None:
        _ACTORS[key] = None
        return None
    # Only pull in meshes that are actually skinned to this armature.
    # Sketchfab files also ship a loose preview sphere that must stay out.
    skinned = _skinned_meshes(arm, new)
    for mesh in skinned:
        if mesh.parent is None:
            mesh.parent = arm
    bounds = _bounds(skinned)
    height = 1.0 if bounds is None else max(0.2, bounds[5] - bounds[4])
    actions = {}
    for action in bpy.data.actions:
        if action in before_actions:
            continue
        actions[action.name] = action
        actions[action.name.split("|")[-1]] = action
        stem = action.name.rsplit(".", 1)[0] if action.name.rsplit(".", 1)[-1].isdigit() else action.name
        actions.setdefault(stem, action)
    for obj in new:
        _hide(obj)
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
    if proto is None or not proto["actions"]:
        return None
    if clip not in proto["actions"]:
        clip = next((name for name in ("Idle", "Idle_Loop", "Idle_Neutral", "Eating", "Take 001") if name in proto["actions"]), None)
        if clip is None:
            clip = next(iter(proto["actions"]))
    root = _clone(proto["arm"], coll)
    # Scale an empty parent. Scaling the armature alone stretches the skin
    # into spikes because the mesh is bound to the bones.
    # Keep the imported world matrix. Sketchfab clips store the centimeter
    # scale on an ancestor empty; dropping it inflates the mesh ~100x.
    empty = bpy.data.objects.new("actor", None)
    coll.objects.link(empty)
    bpy.context.view_layer.update()
    world = root.matrix_world.copy()
    root.parent = empty
    root.matrix_world = world
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


def _private_glb(token: str):
    if not PRIVATE.is_dir():
        return None
    hits = [path for path in PRIVATE.rglob("*.glb") if token.lower() in path.name.lower()]
    return hits[0] if hits else None


def place_dancer(coll, x, y, z):
    """Far-bank gag. The floss clip replaces the mannequin when the private cache is present."""
    path = _private_glb("Dance_Male_Flossing")
    clip = "Take 001"
    if path is None:
        path = CACHE / "animations" / "quaternius_universal_animation_library" / "Universal Animation Library[Standard]" / "Unreal-Godot" / "UAL1_Standard.glb"
        clip = "Dance_Loop"
    if path is None or not path.exists():
        return None
    return place_actor(coll, path, (x, y, z), 0.6, 1.75, clip, offset=3)


def place_phone_walker(coll, x, y, z, yaw=0.0):
    """One promenade pedestrian looking at a phone. Vanishes with the crowd."""
    path = _private_glb("Female_Phone-Walking")
    if path is None:
        return None
    return place_actor(coll, path, (x, y, z), yaw, 1.75, "Take 001", offset=11)


def place_deer(coll, x, y, z):
    path = CACHE / "animals" / "quaternius_ultimate_animated_animals" / "glb" / "Deer_T6Cs7tmMHJ.glb"
    if not path.exists():
        return None
    return place_actor(coll, path, (x, y, z), 1.2, 1.55, "Eating", offset=8)
