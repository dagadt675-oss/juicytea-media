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
    "Brutalist_Apartment_Building_34c4860b",
    "Mediterranean_Apartment_Building_57cec170",
    "Modern_apartment_building_d5727bba",
    "Residential_Building_15133650",
    "Scan_Old_Brick_Building_9aa86602",
    "Block_of_flats_b5711e89",
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
        # A wide kitbash scaled to roof height would fill the locked camera.
        wide = max(size[0], size[1]) * scale
        if name == "tower" and wide > 14.0:
            scale *= 14.0 / wide
    elif longest is not None:
        scale = float(longest) / max(max(size), 0.01)
    else:
        scale = 1.0
    return _spawn(coll, mesh, loc, yaw, scale, name)


def place_tower(coll, x, y, z, height):
    if not ready():
        return None
    token = TOWERS[int(abs(x * 3 + y)) % len(TOWERS)]
    obj = place(coll, token, (x, y, z), 0.0, height=height, name="tower")
    if obj is None:
        return None
    bpy.context.view_layer.update()
    zs = [(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]
    built = max(zs) - min(zs) if zs else 0.0
    if built > float(height) * 1.25:
        obj.scale *= float(height) / built
    _hook_object_decay(obj)
    return obj


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
# The pack is sedans, pickups, and two van bodies. No separate taxi, SUV, or bus.
_CITY_CARS = (
    ("sedan_body_sedan_white_0", "sedan_white_0", 4.8),
    ("sedan_body.001_sedan_blue_0", "sedan_blue_0", 4.8),
    ("sedan_body.002_sedan_red_0", "sedan_red_0", 4.8),
    ("sedan_body.003_sedan_0", "sedan_0", 4.8),
    ("pickup_body_pickup_white_0", "pickup_white_0", 5.3),
    ("pickup_body.001_pickup_blue_0", "pickup_blue_0", 5.3),
    ("pickup_body.002_pickup_red_0", "pickup_red_0", 5.3),
    ("pickup_body.003_pickup_0", "pickup_0", 5.3),
    ("van_body_extra1_van_extra1_white_0", "van_extra1_white_0", 5.4),
    ("van_body_extra1.001_van_extra1_blue_0", "van_extra1_blue_0", 5.4),
    ("van_body_extra1.004_van_extra1_red_0", "van_extra1_red_0", 5.4),
    ("van_body_extra1.002_van_extra2_white_0", "van_extra2_white_0", 5.8),
    ("van_body_extra1.005_van_extra2_red_0", "van_extra2_red_0", 5.8),
)
# A '71 Miura SV is about this size. The nose is +X. The engine bay is behind
# the cabin, so a sapling belongs aft of center, not in the hood.
HERO_LENGTH = 4.39
HERO_WIDTH = 1.78
HERO_HEIGHT = 1.05
HERO_PAINT = (0.62, 0.075, 0.045)
_BADGE_TOKENS = ("logo", "badge", "emblem", "lambo", "lamborghini", "crest", "manufacturerplate", "brand")


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


def _wheels_for(pack, color_key):
    wheels = []
    for obj in pack:
        if obj.type != "MESH" or "wheel" not in obj.name.lower():
            continue
        # The plain sedan key "sedan_0" is also inside "sedan_white_0". Match the
        # plain cars only when the name does not carry another color.
        if color_key in ("sedan_0", "pickup_0"):
            if color_key not in obj.name:
                continue
            if any(color in obj.name for color in ("white", "blue", "red")):
                continue
            wheels.append(obj)
        elif color_key in obj.name:
            wheels.append(obj)
    return wheels


def _is_mark(obj):
    """Badges, crests, and plate text. Body panels named Textured stay."""
    low = obj.name.lower()
    if any(token in low for token in _BADGE_TOKENS):
        return True
    if obj.type != "MESH":
        return False
    for slot in obj.material_slots:
        material = slot.material
        if material and any(token in material.name.lower() for token in _BADGE_TOKENS):
            return True
    return False


def _strip_badges(root):
    """Hide marque badges and the plate. The hero stays unmarked."""
    stack = [root]
    while stack:
        obj = stack.pop()
        stack.extend(list(obj.children))
        if _is_mark(obj):
            obj.hide_render = True
            obj.hide_viewport = True


def _unique_mesh(obj):
    if obj.type == "MESH" and obj.data is not None and obj.data.users > 1:
        obj.data = obj.data.copy()
    for child in obj.children:
        _unique_mesh(child)


def hero_sports_path():
    """The Miura file, once it is in the private cache. None until that drop."""
    if not SKETCHFAB.is_dir():
        return None
    for name in ("hero_miura.glb", "miura_sv.glb", "miura.glb"):
        path = SKETCHFAB / name
        if path.exists():
            return path
    found = sorted(SKETCHFAB.glob("*miura*.glb"))
    return found[0] if found else None


def _place_pack_vehicle(coll, token, color_key, length, loc, yaw, name):
    pack = _load_pack("Low_Poly_Vehicle_Mini_Pack.glb")
    if not pack:
        return None
    mesh = next((obj for obj in pack if obj.type == "MESH" and obj.name == token), None)
    if mesh is None:
        return None
    parts = [mesh, *_wheels_for(pack, color_key)]
    bpy.context.view_layer.update()
    clones = []
    for src in parts:
        clone = _clone(src, coll)
        clones.append(clone)
    bpy.context.view_layer.update()
    bounds = _bounds_of(clones[0])
    if bounds is None:
        return None
    native = max(bounds[1] - bounds[0], bounds[3] - bounds[2])
    align = _front_yaw(mesh)
    center = Vector(((bounds[0] + bounds[1]) * 0.5, (bounds[2] + bounds[3]) * 0.5, bounds[4]))
    empty = bpy.data.objects.new(name, None)
    coll.objects.link(empty)
    empty.location = center
    bpy.context.view_layer.update()
    for clone in clones:
        world = clone.matrix_world.copy()
        clone.parent = empty
        clone.matrix_world = world
    scale = float(length) / max(native, 0.01)
    empty.scale = (scale, scale, scale)
    empty.rotation_euler.z = float(yaw) + align
    empty.location = loc
    _tint_mesh_colors(empty)
    return empty


def place_city_car(coll, loc, yaw, index=0):
    """A mini-pack sedan, pickup, or van at real length. Nose points along yaw from +X."""
    token, color_key, length = _CITY_CARS[int(index) % len(_CITY_CARS)]
    return _place_pack_vehicle(coll, token, color_key, length, loc, yaw, "car")


def _nose_correction(objects, front_token, rear_token):
    """Yaw that lays the nose (front_token) onto +X. 0 when the ends cannot be told apart."""
    def mean_y(token):
        samples = []
        for obj in objects:
            if obj.type != "MESH" or token not in obj.name:
                continue
            for corner in obj.bound_box:
                samples.append((obj.matrix_world @ Vector(corner)).y)
        if not samples:
            return None
        return sum(samples) / len(samples)

    front = mean_y(front_token)
    rear = mean_y(rear_token)
    if front is None or rear is None or abs(front - rear) < 1e-5:
        return 0.0
    # +Y nose needs -90 degrees. -Y nose needs +90 degrees.
    return -math.pi / 2.0 if front > rear else math.pi / 2.0


def _sit_group(coll, meshes, length, loc, yaw, name, nose=0.0):
    """Bottom-center the meshes on loc and scale the long axis to length."""
    bpy.context.view_layer.update()
    bounds = None
    xs, ys, zs = [], [], []
    for obj in meshes:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    if not xs:
        return None
    bounds = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    native = max(bounds[1] - bounds[0], bounds[3] - bounds[2], 0.01)
    center = Vector(((bounds[0] + bounds[1]) * 0.5, (bounds[2] + bounds[3]) * 0.5, bounds[4]))
    empty = bpy.data.objects.new(name, None)
    coll.objects.link(empty)
    empty.location = center
    bpy.context.view_layer.update()
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.matrix_world = world
        obj.hide_render = False
    empty.scale = (float(length) / native, float(length) / native, float(length) / native)
    empty.rotation_euler.z = float(yaw) + float(nose)
    empty.location = loc
    return empty


def place_hero_sports(coll, loc, yaw):
    """Luxury hero. The Miura file is used when it is in the cache; badges and the plate are hidden.

    Wheels sit on ``loc``. After placement the nose points along ``yaw`` from +X.
    The engine bay is aft of center, where the sapling is parented.
    """
    path = hero_sports_path()
    if path is None:
        placed = _place_pack_vehicle(
            coll, "sedan_body.002_sedan_red_0", "sedan_red_0", HERO_LENGTH, loc, yaw, "hero_sports",
        )
        if placed is not None:
            _unique_mesh(placed)
        return placed
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [obj for obj in bpy.data.objects if obj not in before]
    keep = []
    for obj in new:
        if obj.type != "MESH":
            continue
        if "icosphere" in obj.name.lower() or _is_mark(obj):
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        try:
            coll.objects.link(obj)
        except RuntimeError:
            pass
        keep.append(obj)
    nose = _nose_correction(keep, "Hood", "Trunk")
    empty = _sit_group(coll, keep, HERO_LENGTH, loc, yaw, "hero_sports", nose)
    if empty is None:
        return None
    _strip_badges(empty)
    _unique_mesh(empty)
    _tint_mesh_colors(empty)
    return empty


_SEDANS = None


def _load_sedans():
    global _SEDANS
    if _SEDANS is not None:
        return _SEDANS
    path = SKETCHFAB / "low_poly_sedans_11.glb"
    if not path.exists():
        _SEDANS = []
        return _SEDANS
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    groups = {}
    for obj in bpy.data.objects:
        if obj in before:
            continue
        obj.hide_render = True
        obj.hide_viewport = True
        if obj.type != "MESH":
            continue
        prefix = obj.name.split("_", 1)[0]
        groups.setdefault(prefix, []).append(obj)
    cars = []
    for prefix, meshes in sorted(groups.items()):
        body = next((mesh for mesh in meshes if "palette" in mesh.name.lower()), None)
        if body is None:
            continue
        bpy.context.view_layer.update()
        bounds = _bounds_of(body)
        if bounds is None or max(bounds[1] - bounds[0], bounds[3] - bounds[2]) < 2.0:
            continue
        cars.append(meshes)
    _SEDANS = cars
    return _SEDANS


def place_sedan_pack_car(coll, loc, yaw, index=0):
    """One of the 11 low-poly sedans, already near real size. Nose along yaw from +X."""
    cars = _load_sedans()
    if not cars:
        return None
    meshes = cars[int(index) % len(cars)]
    clones = [_clone(mesh, coll) for mesh in meshes]
    nose = _nose_correction(clones, "headLight", "stopLight")
    return _sit_group(coll, clones, 4.8, loc, yaw, "car", nose)


def place_avenue_car(coll, loc, yaw, index=0):
    """Mix the 11-sedan pack with the vehicle mini pack. No Kenney cars."""
    sedans = _load_sedans()
    span = len(sedans) + len(_CITY_CARS)
    slot = int(index) % max(span, 1)
    if slot < len(sedans):
        built = place_sedan_pack_car(coll, loc, yaw, slot)
        if built is not None:
            return built
    return place_city_car(coll, loc, yaw, slot)


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
    _hook_decay(_ROAD_MAT)
    return _ROAD_MAT


def _bake_flat_zebra(src):
    """A mesh that lies on XY. Local +X is each stripe (traffic). Local +Y is the row (across the road)."""
    bpy.context.view_layer.update()
    mesh = src.data.copy()
    world = src.matrix_world.copy()
    for vert in mesh.vertices:
        point = world @ vert.co
        vert.co = Vector((point.y, point.x, 0.0))
    xs = [vert.co.x for vert in mesh.vertices]
    ys = [vert.co.y for vert in mesh.vertices]
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    for vert in mesh.vertices:
        vert.co.x -= cx
        vert.co.y -= cy
    mesh.update()
    return mesh, max(xs) - min(xs), max(ys) - min(ys)


def _continental_bar(baked):
    """One hub crosswalk bar, resized to 3.0 m along traffic and 0.6 m across."""
    import bmesh

    source = bmesh.new()
    source.from_mesh(baked)
    source.faces.ensure_lookup_table()
    seen = set()
    islands = []
    for face in source.faces:
        if face.index in seen:
            continue
        stack = [face]
        seen.add(face.index)
        group = []
        while stack:
            current = stack.pop()
            group.append(current)
            for edge in current.edges:
                for link in edge.link_faces:
                    if link.index not in seen:
                        seen.add(link.index)
                        stack.append(link)
        islands.append(group)

    def bounds(group):
        xs, ys = [], []
        for face in group:
            for vert in face.verts:
                xs.append(vert.co.x)
                ys.append(vert.co.y)
        return min(xs), max(xs), min(ys), max(ys)

    if islands:
        islands.sort(key=lambda group: (bounds(group)[1] - bounds(group)[0]) * max(bounds(group)[3] - bounds(group)[2], 1e-4))
        chosen = islands[len(islands) // 2]
        x0, x1, y0, y1 = bounds(chosen)
        bm = bmesh.new()
        mapping = {}
        for face in chosen:
            verts = []
            for vert in face.verts:
                if vert.index not in mapping:
                    mapping[vert.index] = bm.verts.new(vert.co)
                verts.append(mapping[vert.index])
            try:
                bm.faces.new(verts)
            except ValueError:
                pass
    else:
        x0, x1, y0, y1 = -1.0, 1.0, -0.3, 0.3
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for vert in bm.verts:
            vert.co.x *= 2.0
            vert.co.y *= 0.6
            vert.co.z = 0.0
    # Local +X is the bar (with traffic). Local +Y is its width.
    if (y1 - y0) > (x1 - x0):
        for vert in bm.verts:
            vert.co.x, vert.co.y = vert.co.y, vert.co.x
        x0, x1, y0, y1 = y0, y1, x0, x1
    sx = 3.0 / max(x1 - x0, 0.01)
    sy = 0.6 / max(y1 - y0, 0.01)
    cx = (x0 + x1) * 0.5
    cy = (y0 + y1) * 0.5
    for vert in bm.verts:
        vert.co.x = (vert.co.x - cx) * sx
        vert.co.y = (vert.co.y - cy) * sy
        vert.co.z = 0.004
    me = bpy.data.meshes.new("continental_bar")
    bm.to_mesh(me)
    bm.free()
    source.free()
    if baked.materials:
        me.materials.append(baked.materials[0])
    return me


def place_zebra(coll, x, y, z, yaw, across, along):
    """US continental bars: 0.6 m wide, 0.6 m gaps, 3 m with the traffic.

    Every leg uses that same bar. ``along`` is accepted so older calls still
    line up, and the bar length stays 3 m.
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
                            bsdf.inputs["Roughness"].default_value = 0.4
        if mesh is None:
            return None
        baked, _native_along, _native_across = _bake_flat_zebra(mesh)
        _ZEBRA = _continental_bar(baked)
    bar = _ZEBRA
    pitch = 1.2
    count = max(1, int((float(across) - 0.6) / pitch) + 1)
    while count > 1 and (count - 1) * pitch + 0.6 > float(across) + 0.05:
        count -= 1
    empty = bpy.data.objects.new("zebra", None)
    coll.objects.link(empty)
    empty.empty_display_size = 0.2
    empty.rotation_mode = "XYZ"
    empty.rotation_euler = (0.0, 0.0, float(yaw))
    empty.location = (float(x), float(y), float(z))
    empty.scale = (1.0, 1.0, 1.0)
    empty.visible_shadow = False
    mid = (count - 1) * 0.5
    for i in range(count):
        copy = bpy.data.objects.new("zebra_bar", bar)
        coll.objects.link(copy)
        copy.parent = empty
        copy.location = (0.0, (i - mid) * pitch, 0.0)
        copy.rotation_mode = "XYZ"
        copy.rotation_euler = (0.0, 0.0, 0.0)
        copy.scale = (1.0, 1.0, 1.0)
        copy.visible_shadow = False
        copy.hide_render = False
    return empty


def _hook_decay(material):
    """Dark patches driven by a value node named Decay. Day 1 leaves it at 0."""
    if material is None or material.get("decay_hook"):
        return
    tree = material.node_tree
    if tree is None:
        return
    bsdf = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None or "Base Color" not in bsdf.inputs:
        return
    color_in = bsdf.inputs["Base Color"]
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7.0
    noise.inputs["Detail"].default_value = 2.0
    spread = tree.nodes.new("ShaderNodeMath")
    spread.operation = "MULTIPLY_ADD"
    spread.inputs[1].default_value = 0.82
    spread.inputs[2].default_value = 0.12
    tree.links.new(noise.outputs["Fac"], spread.inputs[0])
    decay = tree.nodes.new("ShaderNodeValue")
    decay.name = "Decay"
    decay.label = "Decay"
    decay.outputs[0].default_value = 0.0
    fac = tree.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    tree.links.new(decay.outputs[0], fac.inputs[0])
    tree.links.new(spread.outputs[0], fac.inputs[1])
    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Color2"].default_value = (0.015, 0.016, 0.018, 1.0)
    if color_in.is_linked:
        source = color_in.links[0].from_socket
        tree.links.remove(color_in.links[0])
        tree.links.new(source, mix.inputs["Color1"])
    else:
        mix.inputs["Color1"].default_value = tuple(color_in.default_value)
    tree.links.new(fac.outputs["Value"], mix.inputs["Fac"])
    tree.links.new(mix.outputs["Color"], color_in)
    material["decay_hook"] = True


def _hook_object_decay(obj):
    if obj is None:
        return
    meshes = _walk_meshes(obj) if obj.type != "MESH" else [obj]
    for mesh in meshes:
        for slot in mesh.material_slots:
            _hook_decay(slot.material)


def _tint_mesh_colors(obj):
    """Multiply a textured car by its object color so grime can dull the paint."""
    for mesh in _walk_meshes(obj):
        for slot in mesh.material_slots:
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
        mesh.color = (1.0, 1.0, 1.0, 1.0)


_BLOCK_PROTOS = {}


def _block_protos(filename, min_z):
    key = (filename, float(min_z))
    if key in _BLOCK_PROTOS:
        return _BLOCK_PROTOS[key]
    path = PRIVATE / "sketchfab" / "city_blocks" / filename
    if not path.exists():
        _BLOCK_PROTOS[key] = []
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    kept = []
    for obj in bpy.data.objects:
        if obj not in before:
            obj.hide_render = True
            obj.hide_viewport = True
        if obj in before or obj.type != "MESH":
            continue
        pts = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        height = max(point.z for point in pts) - min(point.z for point in pts)
        if height < min_z:
            continue
        for slot in obj.material_slots:
            _hook_decay(slot.material)
        kept.append(obj)
    _BLOCK_PROTOS[key] = kept
    return kept


def block_size(filename, min_z=1.2):
    """(width, depth, height) of the tall meshes, in the file's units."""
    protos = _block_protos(filename, min_z)
    if not protos:
        return None
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for src in protos:
        for corner in src.bound_box:
            point = src.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def place_city_block(coll, filename, x, y, z, yaw=0.0, height=30.0, min_z=1.2, name="block"):
    """One hub city block, bottom on z, footprint centered on x, y. Flat road decals are skipped."""
    protos = _block_protos(filename, min_z)
    if not protos:
        return None
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for src in protos:
        for corner in src.bound_box:
            point = src.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    native_h = max(zs) - min(zs)
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    cz = min(zs)
    empty = bpy.data.objects.new(name, None)
    coll.objects.link(empty)
    for src in protos:
        copy = src.copy()
        coll.objects.link(copy)
        world = copy.matrix_world.copy()
        copy.parent = empty
        copy.matrix_world = world
        copy["ruin_with"] = empty.name
        copy.hide_render = False
        copy.hide_viewport = False
    scale = float(height) / max(native_h, 0.01)
    empty.scale = (scale, scale, scale)
    empty.rotation_mode = "XYZ"
    empty.rotation_euler = (0.0, 0.0, float(yaw))
    from mathutils import Euler

    lifted = Vector((scale * cx, scale * cy, scale * cz))
    empty.location = Vector((float(x), float(y), float(z))) - Euler((0.0, 0.0, float(yaw)), "XYZ").to_matrix() @ lifted
    return empty
