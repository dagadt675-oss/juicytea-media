"""BlendKit meshes for the river city. Rendered videos only.

The files live in the gitignored cache. Branded models are never placed.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

from engine.cc0_city import _clone, _mesh_size, _sit_on_ground, _spawn

PRIVATE = Path(os.environ.get("PRIVATE_CACHE", "/opt/cursor/asset-cache/private"))
ROOT = PRIVATE / "blendkit"

# Real-world marques. Skip even if a caller asks for them by name.
BRAND_TOKENS = (
    "mustang",
    "beetle",
    "volkswagen",
    "audi",
    "bmw",
    "ramcharger",
    "escalade",
    "vaz_2107",
    "pinzgauer",
    "neoplan",
    "cessna",
    "yamaha",
    "fire_extinguisher",
    "lego",
)

_FILES = None
_MESHES = {}

TOWERS = (
    "Skyline_Vista_Tower_ff2c8a98",
    "Horizon_Glow_Tower_b9db0504",
    "Urban_Pulse_Tower_cf4883e9",
)


def ready() -> bool:
    return bool(_blends())


def is_brand(path: Path) -> bool:
    text = path.as_posix().lower()
    return any(token in text for token in BRAND_TOKENS)


def _blends():
    global _FILES
    if _FILES is None:
        _FILES = [] if not ROOT.is_dir() else [path for path in ROOT.rglob("*.blend") if not is_brand(path)]
    return _FILES


def find_blend(token: str):
    token_l = token.lower()
    hits = [path for path in _blends() if token_l in path.name.lower()]
    return hits[0] if hits else None


def _keep(name: str) -> bool:
    low = name.lower()
    if low.startswith("wgt-") or "wgt-" in low:
        return False
    if "lod1" in low or "lod2" in low or "lod3" in low:
        return False
    return True


def _mesh(token: str):
    if token in _MESHES:
        return _MESHES[token]
    path = find_blend(token)
    if path is None:
        _MESHES[token] = None
        return None
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = [name for name in src.objects if _keep(name)]
    objs = [obj for obj in dst.objects if obj is not None]
    col = bpy.data.collections.new("blend_src")
    bpy.context.scene.collection.children.link(col)
    for obj in objs:
        try:
            col.objects.link(obj)
        except RuntimeError:
            pass
    bpy.context.view_layer.update()
    meshes = [obj for obj in objs if obj.type == "MESH"]
    if not meshes:
        _MESHES[token] = None
        return None
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    _sit_on_ground(obj)
    mesh = obj.data
    mesh.name = "bk_" + path.stem[:40]
    for item in list(col.objects):
        try:
            bpy.data.objects.remove(item, do_unlink=True)
        except ReferenceError:
            pass
    bpy.data.collections.remove(col)
    _MESHES[token] = mesh
    return mesh


def place(coll, token, loc, yaw, height=None, longest=None, name="prop"):
    mesh = _mesh(token)
    if mesh is None:
        return None
    size = _mesh_size(mesh)
    if height is not None:
        scale = float(height) / max(size[2], 0.01)
    elif longest is not None:
        scale = float(longest) / max(max(size), 0.01)
    else:
        scale = 1.0
    return _spawn(coll, mesh, loc, yaw, scale, name)


def place_tower(coll, x, y, z, height):
    if not ready():
        return None
    token = TOWERS[int(abs(x * 3 + y)) % len(TOWERS)]
    return place(coll, token, (x, y, z), 0.0, height=height, name="tower")


def place_bench(coll, x, y, z, yaw):
    return place(coll, "Stylish_bench_7383c436", (x, y, z), yaw, height=0.85, name="bench")


def place_hydrant(coll, x, y, z, yaw=0.3):
    return place(coll, "Fire_Hydrant_b8013eb2", (x, y, z), yaw, height=0.85, name="hydrant")


def place_cat(coll, x, y, z, yaw=1.1):
    return place(coll, "Domestic_cat_rigged__731d9ed6", (x, y, z), yaw, height=0.32, name="cat")


# RMS Queen Mary, PeeJaa, Sketchfab Free Standard. Ocean episodes only.
# The file is a harbor tile. This length is the hull axis, not the tile.
QUEEN_MARY_LENGTH = 310.7
QUEEN_MARY_NATIVE = 260.7
# The hull runs along +Y. This swing lays that axis on +X.
QUEEN_MARY_ALIGN = -math.pi / 2


def queen_mary_scale() -> float:
    return QUEEN_MARY_LENGTH / QUEEN_MARY_NATIVE


def queen_mary_path(distant: bool = False):
    name = "RMS_Queen_Mary_distant.glb" if distant else "RMS_Queen_Mary.glb"
    path = PRIVATE / "ships" / name
    return path if path.exists() else None


def place_queen_mary(coll, loc, yaw=0.0, distant=False):
    """Place the liner at 310.7 m. Distant shots use the decimated mesh.

    Not used by the river-city episode.
    """
    path = queen_mary_path(distant=distant)
    if path is None:
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [obj for obj in bpy.data.objects if obj not in before]
    roots = [obj for obj in new if obj.parent not in new]
    empty = bpy.data.objects.new("queen_mary", None)
    coll.objects.link(empty)
    for obj in new:
        try:
            coll.objects.link(obj)
        except RuntimeError:
            pass
    bpy.context.view_layer.update()
    for root in roots:
        world = root.matrix_world.copy()
        root.parent = empty
        root.matrix_world = world
    scale = queen_mary_scale()
    empty.scale = (scale, scale, scale)
    empty.rotation_euler.z = float(yaw) + QUEEN_MARY_ALIGN
    empty.location = loc
    return empty


SKETCHFAB = PRIVATE / "sketchfab"
_PACKS = {}

# Generic cars only. The armored carrier in the same pack stays unused.
_CITY_CARS = (
    ("sedan_body_sedan_white_0", 4.6),
    ("sedan_body.001_sedan_blue_0", 4.6),
    ("sedan_body.002_sedan_red_0", 4.6),
    ("pickup_body_pickup_white_0", 4.9),
    ("pickup_body.001_pickup_blue_0", 4.9),
    ("pickup_body.002_pickup_red_0", 4.9),
    ("van_body_extra1_van_extra1_white_0", 5.2),
)


def _load_pack(filename):
    path = SKETCHFAB / filename
    if not path.exists():
        return None
    key = str(path)
    if key in _PACKS:
        return _PACKS[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [obj for obj in bpy.data.objects if obj not in before]
    for obj in new:
        obj.hide_render = True
        obj.hide_viewport = True
    _PACKS[key] = new
    return new


def _walk_meshes(root):
    found = []

    def walk(obj):
        if obj.type == "MESH":
            found.append(obj)
        for child in obj.children:
            walk(child)

    walk(root)
    return found


def _pack_root(mesh):
    obj = mesh
    while obj.parent is not None and obj.parent.name not in ("RootNode", "Sketchfab_model") and "fbx" not in obj.parent.name.lower():
        obj = obj.parent
    return obj


def _bounds_of(root):
    pts = []
    for mesh in _walk_meshes(root):
        for corner in mesh.bound_box:
            pts.append(mesh.matrix_world @ Vector(corner))
    if not pts:
        return None
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def _front_yaw(root):
    """Yaw that points the low end of the body (the hood) along +X."""
    body = next((mesh for mesh in _walk_meshes(root) if "wheel" not in mesh.name.lower()), None)
    if body is None:
        return 0.0
    coords = [body.matrix_world @ vert.co for vert in body.data.vertices]
    xs = [p.x for p in coords]
    ys = [p.y for p in coords]
    if max(ys) - min(ys) >= max(xs) - min(xs):
        axis = Vector((0.0, 1.0, 0.0))
        along = [p.y for p in coords]
    else:
        axis = Vector((1.0, 0.0, 0.0))
        along = [p.x for p in coords]
    lo, hi = min(along), max(along)
    span = max(hi - lo, 1e-4)
    front = [p for p, a in zip(coords, along) if a < lo + span * 0.25]
    back = [p for p, a in zip(coords, along) if a > hi - span * 0.25]
    if not front or not back:
        return 0.0
    # The cabin is taller than the hood, so the lower end is the front.
    front_z = sum(p.z for p in front) / len(front)
    back_z = sum(p.z for p in back) / len(back)
    sign = 1.0 if front_z <= back_z else -1.0
    forward = axis * sign
    # The lower end was landing on -X; the hood on these meshes is the taller end.
    return math.pi - math.atan2(forward.y, forward.x)


def _place_root(coll, root, loc, yaw, scale, name):
    clone = _clone(root, coll)
    bpy.context.view_layer.update()
    bounds = _bounds_of(clone)
    empty = bpy.data.objects.new(name, None)
    coll.objects.link(empty)
    if bounds is not None:
        center = Vector(((bounds[0] + bounds[1]) * 0.5, (bounds[2] + bounds[3]) * 0.5, bounds[4]))
        empty.location = center
    bpy.context.view_layer.update()
    world = clone.matrix_world.copy()
    clone.parent = empty
    clone.matrix_world = world
    empty.scale = (scale, scale, scale)
    empty.rotation_euler.z = yaw
    empty.location = loc
    return empty


def place_city_car(coll, loc, yaw, index=0):
    """A colored sedan, pickup, or van at car length. Nose points along yaw from +X."""
    pack = _load_pack("Low_Poly_Vehicle_Mini_Pack.glb")
    if not pack:
        return None
    token, length = _CITY_CARS[int(index) % len(_CITY_CARS)]
    mesh = next((obj for obj in pack if obj.type == "MESH" and obj.name == token), None)
    if mesh is None:
        return None
    root = _pack_root(mesh)
    bpy.context.view_layer.update()
    bounds = _bounds_of(root)
    if bounds is None:
        return None
    native = max(bounds[1] - bounds[0], bounds[3] - bounds[2])
    align = _front_yaw(root)
    return _place_root(coll, root, loc, float(yaw) + align, float(length) / max(native, 0.01), "car")


def place_city_prop(coll, token, loc, yaw=0.0, height=1.0, name="prop"):
    """One mesh from the city-props pack, scaled to a real height."""
    pack = _load_pack("City_Props_Collection_vol1.glb")
    if not pack:
        return None
    mesh = next((obj for obj in pack if obj.type == "MESH" and token in obj.name), None)
    if mesh is None:
        return None
    bpy.context.view_layer.update()
    bounds = _bounds_of(mesh)
    if bounds is None:
        return None
    native_h = max(bounds[5] - bounds[4], 0.01)
    return _place_root(coll, mesh, loc, float(yaw), float(height) / native_h, name)


_ROAD_MAT = None
_ZEBRA = None


def road_asphalt_material():
    """Asphalt from the US 4-lane road. The curved ribbon itself stays hidden."""
    global _ROAD_MAT
    if _ROAD_MAT is not None:
        return _ROAD_MAT
    path = PRIVATE / "roads" / "realistic_road" / "realistic_road.glb"
    if not path.exists():
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    for obj in bpy.data.objects:
        if obj not in before:
            obj.hide_render = True
            obj.hide_viewport = True
    _ROAD_MAT = bpy.data.materials.get("Road1")
    return _ROAD_MAT


def place_zebra(coll, x, y, z, yaw, across, depth):
    """One flat 5-stripe zebra.

    The mesh lies in local XZ (the row of bars along X, each bar along Z).
    A -90° pitch lays it on the ground; yaw then turns it in the street.
    """
    global _ZEBRA
    if _ZEBRA is None:
        path = PRIVATE / "roads" / "simple_crosswalk" / "simple_crosswalk.glb"
        if not path.exists():
            return None
        before = set(bpy.data.objects)
        mesh = None
        bpy.ops.import_scene.gltf(filepath=str(path))
        for obj in bpy.data.objects:
            if obj not in before:
                obj.hide_render = True
                obj.hide_viewport = True
            if obj.type == "MESH" and obj.name.startswith("Crosswalk_"):
                mesh = obj
                for slot in obj.material_slots:
                    material = slot.material
                    if material and material.use_nodes:
                        bsdf = material.node_tree.nodes.get("Principled BSDF")
                        if bsdf:
                            bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.93, 1.0)
                            bsdf.inputs["Roughness"].default_value = 0.45
        _ZEBRA = mesh
    if _ZEBRA is None:
        return None
    copy = _ZEBRA.copy()
    coll.objects.link(copy)
    copy.parent = None
    copy.hide_render = False
    copy.hide_viewport = False
    # Local X is the row (4.54 m). Local Z is the bar length (2.0 m).
    copy.scale = (float(depth) / 4.544, 1.0, float(across) / 2.0)
    copy.rotation_euler = (-math.pi / 2.0, 0.0, float(yaw))
    copy.location = (x, y, z)
    return copy
