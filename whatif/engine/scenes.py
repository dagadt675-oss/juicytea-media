"""Scene library: river city, coast city, forest/farm, suburbs.

Pieces are selected by the episode spec. Episode 1 uses the river city.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

from engine import assets as assetlib
from engine import cc0_city
from engine import found_assets
from engine import private_assets
from engine.city_layout import (
    AVE_HALF,
    AVENUE_HALF,
    BRIDGE_YAW,
    AVE_Y,
    CROSS_X,
    DASH_GAP,
    DASH_LEN,
    CITY_STREETS,
    DECK_HALF,
    DECK_LANES,
    DECK_ROT_Z,
    DECK_W,
    FOREGROUND_CARS,
    HERO_SPORTS,
    FOUNTAIN,
    GRID_HALF,
    GRID_X,
    INDEX_CANOPY,
    INDEX_DECK,
    INDEX_PORTAL,
    LANE_OFFSETS,
    LANE_W,
    PARK_LAND_Z,
    PATHS,
    QUAY_Z,
    RIVER_X0,
    RIVER_X1,
    RIVER_Y0,
    RIVER_Y1,
    RAMP_FLAT_S,
    RIBBON_TOP,
    ROAD_Z,
    SIDEWALK_W,
    STOP_SETBACK,
    ZEBRA_DEPTH,
    SKYLINE_COLORS,
    SKYLINE_ROWS,
    TOWER_LEG,
    TOWER_S,
    TOWER_W,
    FAR_BANK_S,
    FAR_END_Y,
    FAR_LAND_Y,
    FAR_MID_Y,
    FAR_ROAD_S,
    NEAR_BANK_S,
    RIVER_DRIVE_Y,
    WATER_BED_Z,
    bridge_spans,
    city_water_top,
    on_block_street,
    deck_direction,
    deck_point,
    deck_s_at_y,
    deck_z,
    right_vector,
    south_s,
    tower_pose,
)
from engine import decay_vfx
from engine.meshkit import (
    Kit,
    add_box,
    aim_z,
    box_object,
    cylinder_mesh,
    empty,
    ico_object,
    lin,
    link_obj,
    make_emission,
    make_facade_material,
    make_block_material,
    make_canopy_material,
    make_object_color_surface,
    make_surface,
    make_volume,
    make_water_material,
    make_window_material,
    mesh_from_bm,
    parent_keep,
)

# Real-world meters. A drone looks north (+Y) and down. Near to far: road, park, river, skyline.
PARK_Z = PARK_LAND_Z
LOW_Z = 0.28
FAR_Z = 1.4
DECK_Z = 8.5


def _deck_x(y):
    return deck_point(deck_s_at_y(y))[0]


def _deck_z(y):
    return deck_z(deck_s_at_y(y))


def _tower_y(s):
    return deck_point(s)[1]


def _materials():
    wall = make_object_color_surface(
        "Tower",
        {"moss": 0.9, "rust": 0.25, "mud": 0.35, "scorch": 0.55, "snow": 0.85, "wet": 0.6},
    )
    facade = make_facade_material()
    window = make_window_material()
    trim = make_surface(
        "Trim",
        lin(0.32, 0.34, 0.38),
        {"moss": 0.4, "rust": 0.7, "mud": 0.3, "scorch": 0.4, "snow": 0.8, "wet": 0.5},
    )
    bridge = make_surface(
        "BridgeRed",
        lin(0.42, 0.13, 0.11),
        {"moss": 0.15, "rust": 1.0, "mud": 0.2, "scorch": 0.35, "snow": 0.7, "wet": 0.4},
        roughness=0.34,
    )
    cable = make_surface(
        "Cable",
        lin(0.22, 0.20, 0.19),
        {"moss": 0.05, "rust": 0.9, "mud": 0.1, "scorch": 0.2, "snow": 0.4, "wet": 0.3},
    )
    road = make_surface(
        "Road",
        lin(0.50, 0.52, 0.54),
        {"moss": 0.55, "rust": 0.05, "mud": 0.8, "scorch": 0.45, "snow": 1.0, "wet": 0.85},
    )
    # Dark blue-grey asphalt. The rendered pixels are what the metric checks
    # against zenith's deck sample, about sRGB (33, 44, 66).
    deck_asphalt = make_surface(
        "Deck",
        lin(0.22, 0.22, 0.23),
        {"moss": 0.15, "rust": 0.02, "mud": 0.25, "scorch": 0.15, "snow": 0.7, "wet": 0.45},
        roughness=0.92,
    )
    park = make_surface(
        "Park",
        lin(0.34, 0.72, 0.28),
        {"moss": 0.85, "rust": 0.0, "mud": 0.15, "scorch": 0.45, "snow": 1.0, "wet": 0.2},
    )
    dirt = make_surface(
        "Dirt",
        lin(0.34, 0.26, 0.16),
        {"moss": 0.3, "rust": 0.0, "mud": 0.4, "scorch": 0.7, "snow": 1.0, "wet": 0.4},
    )
    sand = make_surface(
        "Sand",
        lin(0.76, 0.68, 0.46),
        {"moss": 0.05, "rust": 0.0, "mud": 0.25, "scorch": 0.15, "snow": 0.8, "wet": 0.3},
    )
    water = make_water_material()
    mark = make_surface("Mark", lin(0.92, 0.92, 0.88), {"snow": 1.0, "mud": 0.6, "wet": 0.4, "scorch": 0.3})
    concrete = make_surface("Concrete", lin(0.78, 0.76, 0.70), {"snow": 0.9, "mud": 0.45, "wet": 0.35, "moss": 0.25})
    yellow = make_surface("Yellow", lin(0.86, 0.72, 0.18), {"snow": 1.0, "mud": 0.5, "wet": 0.3})
    leaf = make_object_color_surface(
        "Leaf",
        {"moss": 0.1, "rust": 0.0, "mud": 0.15, "scorch": 0.8, "snow": 1.0, "wet": 0.25},
    )
    canopy = make_canopy_material()
    block = make_block_material()
    trunk = make_surface(
        "Trunk",
        lin(0.34, 0.22, 0.12),
        {"moss": 0.45, "rust": 0.0, "mud": 0.2, "scorch": 0.6, "snow": 0.7, "wet": 0.3},
    )
    wood = make_object_color_surface(
        "Wood",
        {"moss": 0.55, "rust": 0.1, "mud": 0.4, "scorch": 0.7, "snow": 0.9, "wet": 0.55},
    )
    roof = make_surface(
        "Roof",
        lin(0.48, 0.20, 0.16),
        {"moss": 0.7, "rust": 0.2, "mud": 0.3, "scorch": 0.6, "snow": 1.0, "wet": 0.4},
    )
    car = make_object_color_surface(
        "Car",
        {"moss": 0.25, "rust": 0.85, "mud": 0.55, "scorch": 0.4, "snow": 0.95, "wet": 0.6},
    )
    glass = make_surface("Glass", lin(0.18, 0.26, 0.34), {"snow": 0.3, "wet": 0.2, "scorch": 0.2})
    rubber = make_surface("Rubber", lin(0.05, 0.05, 0.055), {"snow": 0.8, "mud": 0.4})
    seam = make_emission("Seam", lin(0.92, 0.28, 0.06), 0.35)
    rock = make_surface(
        "Rock",
        lin(0.55, 0.50, 0.44),
        {"moss": 0.2, "snow": 0.9, "mud": 0.2, "scorch": 0.2},
    )
    snowmat = make_surface("SnowMat", lin(0.94, 0.96, 0.98), {"snow": 0.2})
    flame = make_emission("Flame", lin(1.0, 0.42, 0.08), 8.0)
    smoke = make_surface("Smoke", lin(0.75, 0.78, 0.82), {})
    dark = make_surface("Dark", lin(0.02, 0.02, 0.025), {})
    skin = make_surface("Skin", lin(0.72, 0.55, 0.42), {})
    cloth = make_object_color_surface("Cloth", {"snow": 0.4, "wet": 0.3, "mud": 0.3})
    return {
        "wall": wall,
        "facade": facade,
        "window": window,
        "trim": trim,
        "bridge": bridge,
        "cable": cable,
        "road": road,
        "deck": deck_asphalt,
        "park": park,
        "dirt": dirt,
        "sand": sand,
        "water": water,
        "mark": mark,
        "concrete": concrete,
        "yellow": yellow,
        "leaf": leaf,
        "canopy": canopy,
        "block": block,
        "trunk": trunk,
        "wood": wood,
        "roof": roof,
        "car": car,
        "glass": glass,
        "rubber": rubber,
        "seam": seam,
        "rock": rock,
        "snow": snowmat,
        "flame": flame,
        "smoke": smoke,
        "dark": dark,
        "skin": skin,
        "cloth": cloth,
    }


def _plane(name, coll, center, size, mat, z_thickness=0.08):
    return box_object(name, coll, center, (size[0], size[1], z_thickness), mat)


def _ground_sheet(name, coll, center, size, mat, tile=2.8):
    """A flat sheet whose UVs repeat the texture every ``tile`` metres."""
    w, d = float(size[0]), float(size[1])
    bm = bmesh.new()
    verts = [bm.verts.new(co) for co in ((-w / 2, -d / 2, 0.0), (w / 2, -d / 2, 0.0), (w / 2, d / 2, 0.0), (-w / 2, d / 2, 0.0))]
    face = bm.faces.new(verts)
    layer = bm.loops.layers.uv.new("UVMap")
    for loop in face.loops:
        loop[layer].uv = ((loop.vert.co.x + w / 2) / tile, (loop.vert.co.y + d / 2) / tile)
    obj = link_obj(name, mesh_from_bm(name, bm), coll, (mat,))
    obj.location = center
    return obj


def _windows(bm, center, size, floors, cols):
    cx, cy, cz = center
    sx, sy, sz = size
    z0 = cz - sz / 2
    usable = sz * 0.86
    if floors < 1 or cols < 1:
        return
    wz = min(0.7, usable / floors * 0.62)
    wx = min(0.62, (sx * 0.8) / cols)
    for face_sign, axis in ((-1, "y"), (1, "x")):
        for floor in range(floors):
            for col in range(cols):
                tz = z0 + sz * 0.08 + (floor + 0.5) * (usable / floors)
                if axis == "y":
                    xx = cx - sx * 0.38 + (col + 0.5) * (sx * 0.76 / cols)
                    yy = cy + face_sign * (sy / 2 + 0.03)
                    add_box(bm, (xx, yy, tz), (wx, 0.06, wz), 1)
                else:
                    yy = cy - sy * 0.38 + (col + 0.5) * (sy * 0.76 / max(cols - 1, 1) if False else sy * 0.76 / cols)
                    xx = cx + face_sign * (sx / 2 + 0.03)
                    add_box(bm, (xx, yy, tz), (0.06, wx, wz), 1)


def _tower_mesh(name, w, d, h, windows=True):
    bm = bmesh.new()
    add_box(bm, (0, 0, h / 2), (w, d, h), 0)
    if windows:
        floors = max(2, int(h / 1.55))
        cols = max(2, int(w / 1.05))
        _windows(bm, (0, 0, h / 2), (w, d, h), floors, cols)
    pier = max(0.08, min(0.9, w * 0.045))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(bm, (sx * (w / 2), sy * (d / 2), h / 2), (pier, pier, h * 0.98), 0)
    if h > 12:
        add_box(bm, (0, 0, h + pier), (w * 0.62, d * 0.62, max(0.4, pier * 1.6)), 0)
    if h > 45:
        add_box(bm, (0, 0, h + 6.0), (0.4, 0.4, min(8.0, h * 0.05)), 0)
    return mesh_from_bm(name, bm)


_ASSET_MESHES = {}


def _kenney(relative):
    from pathlib import Path

    return Path(__file__).resolve().parents[1] / "assets" / "cc0" / "kenney" / relative


def _tint_with_object_color(mesh):
    """Let the time-lapse recolor a textured mesh through the object color."""
    for mat in mesh.materials:
        if mat is None or mat.get("object_tint"):
            continue
        nt = mat.node_tree
        if nt is None:
            continue
        bsdf = next((node for node in nt.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        color_in = bsdf.inputs["Base Color"]
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        if color_in.is_linked:
            source = color_in.links[0].from_socket
            nt.links.remove(color_in.links[0])
            nt.links.new(source, mix.inputs["Color1"])
        else:
            mix.inputs["Color1"].default_value = color_in.default_value
        info = nt.nodes.new("ShaderNodeObjectInfo")
        nt.links.new(info.outputs["Color"], mix.inputs["Color2"])
        nt.links.new(mix.outputs["Color"], color_in)
        mat["object_tint"] = True


def _load_glb(key, path, tint=False):
    """Import a CC0 glb and normalize it to 1 m tall, sitting on z = 0."""
    if key in _ASSET_MESHES:
        return _ASSET_MESHES[key]
    if path is None or not path.exists():
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not meshes:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    zs = [vert.co.z for vert in obj.data.vertices]
    span = max(zs) - min(zs)
    if span > 1e-4:
        factor = 1.0 / span
        for vert in obj.data.vertices:
            vert.co.x *= factor
            vert.co.y *= factor
            vert.co.z *= factor
        zs = [vert.co.z for vert in obj.data.vertices]
    drop = -min(zs)
    for vert in obj.data.vertices:
        vert.co.z += drop
    mesh = obj.data
    mesh.name = f"cc0_{key}"
    if tint:
        _tint_with_object_color(mesh)
    created = [item for item in bpy.data.objects if item not in before]
    for item in created:
        bpy.data.objects.remove(item, do_unlink=True)
    _ASSET_MESHES[key] = mesh
    return mesh


def _prop(kit, coll, name, path, loc, yaw, height, role, tint=False, **extra):
    mesh = _load_glb(name, path, tint=tint)
    if mesh is None:
        return None
    obj = link_obj(name, mesh, coll)
    obj.location = loc
    obj.rotation_euler[2] = yaw
    obj.scale = (height, height, height)
    kit.add(obj, role, sink=False, **extra)
    return obj


_PERSON_FILES = (
    "people/character-a.glb",
    "people/character-b.glb",
    "people/character-c.glb",
    "people/character-d.glb",
)


def _library_file(category, kind=None, rng=None):
    """Enabled file record, or None when the category is still procedural."""
    record = assetlib.choose(category, kind, rng)
    path = assetlib.existing_path(record)
    if path is None:
        return None
    return record, path


def _library_tower(kit, coll, x, y, z, height, color):
    """One imported tower, scaled to the lot height. False when no pack is enabled."""
    found = _library_file("building", "tower")
    if found is None:
        return False
    record, path = found
    mesh = _load_glb(record["id"], path)
    if mesh is None:
        return False
    obj = link_obj("tower", mesh, coll)
    # The loader leaves the mesh 1 m tall. Scale to this lot so the skyline
    # stays under the locked camera.
    obj.scale = (height, height, height)
    obj.location = (x, y, z)
    obj.color = color
    kit.add(obj, "building_base", sink=True)
    return True


def _plant(kit, coll, slug, x, y, z, height, delay=0.2, yaw=0.0, role="weed", only=None):
    """A downloaded plant. Hidden until vegetation passes ``delay``."""
    built = found_assets.place(coll, slug, (x, y, z), yaw, height, name=slug)
    if built is None:
        return None
    if only:
        return kit.add(built, "segment_prop", only=only, sink=False)
    return kit.add(
        built, role, delay=delay, sink=False, leaf=(0.2, 0.42, 0.16, 1),
        future=role == "tree_canopy",
    )


def _tree(kit, coll, mats, x, y, z, scale, future=False, delay=0.0, rng=None, kind="round", leaf=None):
    """A registry tree when a pack is enabled, otherwise the lobed crown."""
    rng = rng or random
    if cc0_city.ready():
        height = float(scale) * 2.9 * (1.15 if kind == "pine" else 1.0)
        tree_kind = "dead" if future and rng.random() < 0.28 else kind
        built = cc0_city.place_tree(coll, x, y, z, height, tree_kind)
        if built is not None:
            built.pass_index = INDEX_CANOPY
            return kit.add(
                built, "tree_canopy", future=future, delay=delay, sink=False,
                leaf=leaf or (0.16, 0.52, 0.18, 1), autumn=(0.55, 0.32, 0.12, 1),
            )
    found = _library_file("tree", kind, rng)
    if found is not None:
        record, path = found
        nominal = float(record.get("target_height") or 8.0)
        height = nominal * (float(scale) / 2.8)
        obj = _prop(
            kit, coll, record["id"], path, (x, y, z), rng.uniform(0.0, 6.28), height,
            "tree_canopy", future=future, delay=delay,
            leaf=leaf or (0.16, 0.52, 0.18, 1), autumn=(0.62, 0.42, 0.12, 1),
        )
        if obj is not None:
            obj.pass_index = INDEX_CANOPY
            return obj

    autumns = (
        (0.72, 0.42, 0.12, 1),
        (0.62, 0.48, 0.16, 1),
        (0.55, 0.28, 0.12, 1),
    )
    greens = (
        (0.12, 0.46, 0.16, 1),
        (0.16, 0.52, 0.18, 1),
        (0.20, 0.48, 0.15, 1),
    )
    if leaf is None:
        leaf = greens[rng.randrange(len(greens))]
    height = scale * 2.9 * rng.uniform(0.94, 1.06)
    if kind == "pine":
        height *= 1.15
    trunk_h = height * (0.38 if kind == "pine" else 0.28)
    trunk_r = height * 0.045
    trunk = link_obj("trunk", cylinder_mesh("trunk", radius=trunk_r, segments=7), coll, (mats["trunk"],))
    trunk.location = (x, y, z)
    trunk.scale = (1.0, 1.0, trunk_h)
    kit.add(trunk, "tree_trunk", future=future, delay=delay, sink=False)

    # A designed crown: overlapping low-poly lobes, not a sphere. The outer
    # radius stays near the measured 5–6% canopy so the metric still holds.
    bm = bmesh.new()
    crown = height * 0.40
    lobes = [(0.0, 0.0, trunk_h + crown * 0.85, crown * 1.05, crown * 0.82, crown * 0.78)]
    count = 5 if kind == "pine" else rng.randint(5, 8)
    for i in range(count - 1):
        ang = (i / max(1, count - 1)) * math.tau + rng.uniform(-0.2, 0.2)
        reach = crown * rng.uniform(0.28, 0.55)
        rad = crown * rng.uniform(0.42, 0.72)
        lobes.append(
            (
                math.cos(ang) * reach,
                math.sin(ang) * reach,
                trunk_h + crown * rng.uniform(0.35, 0.95),
                rad * rng.uniform(0.75, 1.15),
                rad * rng.uniform(0.6, 0.95),
                rad * rng.uniform(0.55, 0.9),
            )
        )
    for bx, by, bz, rx, ry, rz in lobes:
        nverts = len(bm.verts)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        bm.verts.ensure_lookup_table()
        for vert in bm.verts[nverts:]:
            vert.co.x = vert.co.x * rx + bx
            vert.co.y = vert.co.y * ry + by
            vert.co.z = vert.co.z * rz + bz
    try:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=crown * 0.045, segments=1, affect="EDGES", profile=0.4)
    except TypeError:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=crown * 0.045, segments=1, profile=0.4)
    zs = [vert.co.z for vert in bm.verts]
    z0, z1 = min(zs), max(zs)
    span = max(1e-4, z1 - z0)
    layer = bm.loops.layers.color.new("Col")
    for face in bm.faces:
        for loop in face.loops:
            t = (loop.vert.co.z - z0) / span
            shade = 0.42 + 0.72 * t
            loop[layer] = (shade, shade * 1.02, shade * 0.9, 1.0)
    me = mesh_from_bm("canopy", bm)
    canopy = link_obj("canopy", me, coll, (mats["canopy"],))
    canopy.location = (x, y, z)
    canopy.pass_index = INDEX_CANOPY
    canopy.color = leaf
    return kit.add(
        canopy,
        "tree_canopy",
        future=future,
        delay=delay,
        sink=False,
        leaf=leaf,
        autumn=autumns[rng.randrange(3)],
    )


_CAR_MESHES = {}


def _kenney_car_mesh(model):
    if model in _CAR_MESHES:
        return _CAR_MESHES[model]
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "assets" / "cc0" / "kenney" / "cars" / f"{model}.fbx"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not meshes:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.scale = (0.01, 0.01, 0.01)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    zs = [v.co.z for v in obj.data.vertices]
    dz = -min(zs)
    for vert in obj.data.vertices:
        vert.co.z += dz
    # Real sedan: about 4.6 m long, 1.8 m wide, 1.5 m tall. Nose stays on +X.
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    sx = 4.6 / max(0.01, max(xs) - min(xs))
    sy = 1.8 / max(0.01, max(ys) - min(ys))
    sz = 1.5 / max(0.01, max(zs) - min(zs))
    for vert in obj.data.vertices:
        vert.co.x *= sx
        vert.co.y *= sy
        vert.co.z *= sz
    mesh = obj.data
    mesh.name = f"kenney_{model}"
    bpy.data.objects.remove(obj)
    _CAR_MESHES[model] = mesh
    return mesh


def _car(kit, coll, mats, loc, yaw, color, parent=None, local=None, drive=0.0, model="sedan", scale=1.0, force_white=False, **extra):
    # Avenue and deck cars are the hub mini pack. Kenney stays out of this fleet.
    if parent is None:
        if extra.get("hero"):
            built = private_assets.place_hero_sports(coll, loc, yaw)
        else:
            built = private_assets.place_avenue_car(coll, loc, yaw, index=extra.get("index", 0))
        if built is not None:
            kit.add(
                built, "car", path_from=(loc[0] + drive, loc[1], loc[2]), path_to=loc,
                parented=False, float=1.1, bob=0.18, sink=False,
                **{"paint": color, **extra},
            )
            return
    elif parent is not None:
        built = private_assets.place_city_car(coll, (0.0, 0.0, 0.0), 0.0, index=extra.get("index", 0))
        if built is not None:
            built.parent = parent
            built.matrix_parent_inverse = Matrix.Identity(4)
            built.location = local
            built.rotation_euler[2] = yaw
            kit.add(
                built, "car",
                path_from=local, path_to=local,
                parented=True, float=0.0, bob=0.0, sink=False,
                **{"paint": color, **extra},
            )
            return
    found = _library_file("car", model)
    fitted = None
    if found is not None and not found[0]["id"].startswith("kenney_"):
        mesh = _load_glb(found[0]["id"], found[1])
        fitted = float(found[0].get("target_height") or 1.5)
    else:
        mesh = _kenney_car_mesh(model)
    if mesh is None:
        fitted = None
        bm = bmesh.new()
        add_box(bm, (0, 0, 0.4), (0.9, 2.0, 0.7), 0)
        mesh = mesh_from_bm("car", bm)
    if force_white:
        mesh = mesh.copy()
        mesh.materials.clear()
        mesh.materials.append(mats["mark"])
    obj = link_obj("car", mesh, coll)
    # Kenney cars are already 4.6 m long. A new pack comes in 1 m tall and is
    # scaled to the registry height, then by the same instance scale.
    obj.scale = (scale * fitted, scale * fitted, scale * fitted) if fitted else (scale, scale, scale)
    obj.color = (0.94, 0.94, 0.95, 1) if force_white else color
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = local
        obj.rotation_euler[2] = yaw
        stopped = local
        start = (local[0], local[1] + drive, local[2])
    else:
        obj.location = loc
        obj.rotation_euler[2] = yaw
        stopped = loc
        start = (loc[0] + drive, loc[1], loc[2])
    kit.add(
        obj,
        "car",
        path_from=start,
        path_to=stopped,
        parented=parent is not None,
        float=1.1,
        bob=0.18,
        sink=False,
        **{"paint": color, **extra},
    )


_PERSON_MESH = None


def _person_mesh():
    global _PERSON_MESH
    if _PERSON_MESH is None:
        bm = bmesh.new()
        add_box(bm, (0, 0, 0.85), (0.38, 0.24, 1.05), 0)
        add_box(bm, (0, 0, 1.55), (0.2, 0.2, 0.22), 1)
        _PERSON_MESH = mesh_from_bm("person", bm)
    return _PERSON_MESH


def _walker(kit, coll, path, speed, phase, height=1.75):
    """A rigged pedestrian. The walk cycle plays until the vanish cue."""
    if not path or not cc0_city.ready():
        return None
    x, y, z = path[0]
    dx = path[-1][0] - path[0][0]
    dy = path[-1][1] - path[0][1]
    yaw = math.atan2(dy, dx) - math.pi / 2.0
    built = cc0_city.place_person(coll, x, y, z, yaw, "Walk", offset=int(phase * 10) % 36)
    if built is None:
        return None
    item = kit.add(built, "person", path=path, speed=speed, phase=phase, sink=False, bob=0.0, float=0.0)
    if height != 1.75:
        factor = float(height) / 1.75
        item.obj.scale = tuple(axis * factor for axis in item.obj.scale)
        item.base_scale = item.obj.scale.copy()
    return item


def _bike(kit, coll, path, phase, drift=0.2, height=1.75):
    """A downloaded bicycle. It topples when the rider vanishes."""
    path_glb = Path("/opt/cursor/asset-cache/private/sketchfab_free_standard/Bicycle_Low-Poly_Minimalistic_5c70d53e/Bicycle_Low-Poly_Minimalistic_5c70d53e.glb")
    mesh = cc0_city.static_mesh(path_glb) if path_glb.exists() else None
    if mesh is None:
        return None
    size = cc0_city._mesh_size(mesh)
    scale = 1.75 / max(size[0], size[1], 0.01)
    x, y, z = path[0]
    obj = link_obj("bike", mesh, coll)
    obj.location = (x, y, z)
    factor = float(height) / 1.75
    obj.scale = (scale * factor, scale * factor, scale * factor)
    # The rider walks with the bike, a step to the side, and vanishes with everyone else.
    _walker(kit, coll, [(p[0], p[1] + 0.9, p[2]) for p in path], 4.2, phase, height=height)
    item = kit.add(obj, "bike", path=path, speed=4.2, phase=phase, sink=False)
    item.base_scale = obj.scale.copy()
    return item


def _traffic(kit, coll, cruise, index, speed, phase, stop_line=False, drift=0.0, coast=8.0):
    """A hub vehicle moving along ``cruise`` until people vanish, then it coasts."""
    loc = cruise[0]
    if index >= 6:
        built = cc0_city.place_fleet_car(coll, loc, 0.0, index=index)
    else:
        built = private_assets.place_avenue_car(coll, loc, 0.0, index=index)
        if built is None:
            built = cc0_city.place_fleet_car(coll, loc, 0.0, index=index)
    if built is None:
        return None
    return kit.add(
        built, "car",
        path_from=loc, path_to=cruise[-1],
        cruise=cruise, speed=speed, phase=phase,
        stop_line=stop_line, drift=drift, coast=coast,
        index=index, paint=(0.92, 0.92, 0.93, 1), sink=False,
    )


def _alive(kit, coll):
    """Sidewalks, the crosswalk, the park, bikes, and moving lanes. Day 1 only."""
    z = ROAD_Z + 0.02
    south = AVE_Y - AVENUE_HALF - SIDEWALK_W * 0.45
    north = AVE_Y + AVENUE_HALF + SIDEWALK_W * 0.45
    for i, x0 in enumerate((-78.0, -48.0, -12.0, 18.0, 48.0)):
        _walker(kit, coll, [(x0, south, z), (x0 + 22.0, south, z)], 1.25, i * 4.0)
        _walker(kit, coll, [(x0 + 16.0, north, z), (x0 - 6.0, north, z)], 1.15, i * 3.0)
    # Across the zebra, both ways.
    zx = CROSS_X
    for i, side in enumerate((-6.0, -2.0, 2.5, 6.5)):
        y0 = AVE_Y - AVENUE_HALF - 1.0
        y1 = AVE_Y + AVENUE_HALF + 1.0
        path = [(zx + side, y0, z), (zx + side, y1, z)] if i % 2 == 0 else [(zx + side, y1, z), (zx + side, y0, z)]
        _walker(kit, coll, path, 1.35, i * 1.2)
    fx, fy = FOUNTAIN
    for i, (x, y) in enumerate(((-6, -4), (5, 2), (-2, 8), (8, -6))):
        _walker(kit, coll, [(fx + x, fy + y, PARK_LAND_Z), (fx + x + 8.0, fy + y + 3.0, PARK_LAND_Z)], 1.05, i * 2.5)
    bike_y = AVE_Y - AVENUE_HALF - 1.15
    for i, x0 in enumerate((-70.0, -30.0, 8.0, 40.0)):
        _bike(kit, coll, [(x0, bike_y, z), (x0 + 28.0, bike_y, z)], i * 6.0)
    # The locked camera's nearest sidewalk. These are the people it can actually read.
    near_y = AVE_Y - AVENUE_HALF - SIDEWALK_W * 0.55
    for i, x in enumerate((-36.0, -24.0, -12.0, -2.0, 8.0, 18.0, 30.0)):
        _walker(kit, coll, [(x, near_y, z), (x + 10.0, near_y, z)], 1.15, i * 1.3, height=3.15)
    for i, y in enumerate((-16.0, -6.0, 2.0)):
        _walker(
            kit, coll,
            [(CROSS_X - DECK_HALF - 2.2, y, z), (CROSS_X - DECK_HALF - 2.2, y + 9.0, z)],
            1.2, i * 2.0, height=2.55,
        )
        _walker(
            kit, coll,
            [(CROSS_X + DECK_HALF + 2.2, y + 8.0, z), (CROSS_X + DECK_HALF + 2.2, y, z)],
            1.15, i * 1.6, height=2.55,
        )
    for i, x0 in enumerate((-20.0, -2.0, 14.0)):
        _bike(kit, coll, [(x0, near_y - 0.8, z), (x0 + 16.0, near_y - 0.8, z)], i * 3.0, height=3.05)
    # Closer to the camera than the avenue, so a person is readable in the wide shot.
    for i, (x, y) in enumerate(((-74.0, -46.0), (-60.0, -34.0), (-48.0, -54.0), (-36.0, -28.0), (-24.0, -42.0), (-12.0, -36.0))):
        _walker(kit, coll, [(x, y, z), (x + 7.0, y + 2.5, z)], 1.05, i * 1.1, height=3.5)
    _bike(kit, coll, [(-66.0, -40.0, z), (-50.0, -37.0, z)], 1.4, height=3.3)
    # Eastbound queue stops before the crosswalk. Through traffic keeps going.
    stop_x = zx - DECK_HALF - ZEBRA_DEPTH - STOP_SETBACK - 1.0
    east_y = AVE_Y + LANE_OFFSETS[0]
    east_y2 = AVE_Y + LANE_OFFSETS[1]
    west_y = AVE_Y + LANE_OFFSETS[3]
    _traffic(kit, coll, [(-70.0, east_y, z), (stop_x, east_y, z)], 0, 7.5, 8.0, stop_line=True, coast=3.0)
    _traffic(kit, coll, [(-55.0, east_y, z), (stop_x - 6.0, east_y, z)], 1, 7.5, 0.0, stop_line=True, coast=2.0)
    _traffic(kit, coll, [(-20.0, east_y2, z), (55.0, east_y2, z)], 2, 11.0, 15.0, drift=0.35, coast=9.0)
    _traffic(kit, coll, [(60.0, west_y, z), (-70.0, west_y, z)], 3, 10.0, 20.0, drift=-0.2, coast=8.0)
    _traffic(kit, coll, [(40.0, AVE_Y + LANE_OFFSETS[2], z), (stop_x + DECK_W + 8.0, AVE_Y + LANE_OFFSETS[2], z)], 4, 8.0, 4.0, stop_line=True, coast=4.0)
    # Two transit vehicles from the Kenney fleet. The hub's only coach wears a brand, so it stays out.
    _traffic(kit, coll, [(-78.0, east_y2, z), (70.0, east_y2, z)], 7, 8.5, 30.0, coast=10.0)
    _traffic(kit, coll, [(72.0, west_y, z), (-75.0, west_y, z)], 6, 8.0, 12.0, coast=9.0)
    # Across the bridge, one lane each way, same lane offsets as the deck.
    rx, ry = right_vector()
    for lane, index, phase in ((DECK_LANES[1], 2, 5.0), (DECK_LANES[2], 5, 18.0)):
        pts = []
        s = RAMP_FLAT_S
        while s < NEAR_BANK_S - 4.0:
            x, y = deck_point(s)
            pts.append((x + rx * lane, y + ry * lane, deck_z(s) + RIBBON_TOP + 0.05))
            s += 8.0
        if len(pts) >= 2:
            _traffic(kit, coll, pts, index, 9.0, phase, coast=6.0)


def _person(kit, coll, mats, x, y, z, rng, clip="Idle"):
    if cc0_city.ready():
        built = cc0_city.place_person(coll, x, y, z, rng.uniform(0, 6.28), clip, offset=int(abs(x + y)) % 36)
        if built is not None:
            return kit.add(built, "person", float=0.4, bob=0.08, sink=False)
    found = _library_file("person", "person", rng)
    if found is not None:
        record, path = found
        obj = _prop(
            kit, coll, record["id"], path, (x, y, z), rng.uniform(0, 6.28),
            float(record.get("target_height") or 1.75), "person", float=0.4, bob=0.08,
        )
    else:
        choice = _PERSON_FILES[rng.randrange(len(_PERSON_FILES))]
        obj = _prop(
            kit, coll, choice.rsplit("/", 1)[-1].split(".")[0], _kenney(choice),
            (x, y, z), rng.uniform(0, 6.28), 1.75, "person", float=0.4, bob=0.08,
        )
    if obj is not None:
        return obj
    obj = link_obj("person", _person_mesh(), coll, (mats["cloth"], mats["skin"]))
    obj.location = (x, y, z)
    obj.rotation_euler[2] = rng.uniform(0, 6.28)
    kit.add(obj, "person", float=1.6, bob=0.25, sink=False)
    return obj


def _house(kit, coll, mats, x, y, z, w, d, h, index):
    body = box_object("house", coll, (x, y, z + h / 2), (w, d, h), mats["wood"])
    body.color = (0.72, 0.58, 0.40, 1) if index % 2 == 0 else (0.80, 0.72, 0.55, 1)
    bm = bmesh.new()
    hw, hd, rise = w * 0.55, d * 0.55, h * 0.45
    verts = [
        bm.verts.new((-hw, -hd, 0)),
        bm.verts.new((hw, -hd, 0)),
        bm.verts.new((hw, hd, 0)),
        bm.verts.new((-hw, hd, 0)),
        bm.verts.new((-hw, 0, rise)),
        bm.verts.new((hw, 0, rise)),
    ]
    for face in ((0, 1, 2, 3), (0, 1, 5, 4), (3, 2, 5, 4), (0, 3, 4), (1, 2, 5)):
        bm.faces.new([verts[i] for i in face])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    roof = link_obj("roof", mesh_from_bm("roof", bm), coll, (mats["roof"],))
    roof.location = (x, y, z + h)
    kit.add(body, "house", index=index, sink=False, float=0.4)
    kit.add(roof, "house_roof", index=index, sink=False, float=0.8)


def _markings(coll, mats, x0, x1, y, z, along="x"):
    step = 7.0
    if along == "x":
        x = x0
        while x < x1:
            box_object("dash", coll, (x, y, z), (2.4, 0.45, 0.04), mats["mark"])
            x += step
    else:
        yy = x0
        while yy < x1:
            box_object("dash", coll, (y, yy, z), (0.45, 2.4, 0.04), mats["mark"])
            yy += step


def _lamp(kit, coll, mats, x, y, z):
    lamp = private_assets.place_city_prop(coll, "Light_Light", (x, y, z), 0.0, height=5.0, name="lamp")
    if lamp is not None:
        return kit.add(lamp, "prop", sink=False, float=0.1)
    found = _library_file("prop", "lamp")
    if found is not None:
        record, path = found
        obj = _prop(kit, coll, record["id"], path, (x, y, z), 0.0, float(record.get("target_height") or 5.0), "prop")
    else:
        obj = _prop(kit, coll, "lamp", _kenney("props/light-curved.glb"), (x, y, z), 0.0, 5.0, "prop")
    if obj is None:
        pole = box_object("lamp", coll, (x, y, z + 2.5), (0.16, 0.16, 5.0), mats["trim"])
        kit.add(pole, "prop", sink=False, float=0.1)


def _designed_tower(name, w, d, h, kind, podium=True, crown=True):
    """One of ten tower bodies: lobby, shaft, setback, mullion, window bands, roof kit."""
    bm = bmesh.new()
    kind = int(kind) % 10
    lobby_h = max(2.4, min(5.5, h * 0.08)) if podium else 0.0
    if podium:
        # Some archetypes step the lobby in, some give it a wider plinth.
        foot = 0.9 if kind in (1, 4, 7) else 1.06
        add_box(bm, (0, 0, lobby_h * 0.5), (w * foot, d * foot, lobby_h), 2)
    crown_h = max(2.2, h * (0.14 + (kind % 5) * 0.025)) if crown else 0.0
    shaft_h = max(3.0, h - lobby_h - crown_h)
    add_box(bm, (0, 0, lobby_h + shaft_h * 0.5), (w, d, shaft_h), 0)
    if crown:
        sw = w * (0.52 + (kind % 4) * 0.09)
        sd = d * (0.52 + (kind % 3) * 0.1)
        ox = w * 0.1 if kind in (2, 6) else 0.0
        add_box(bm, (ox, 0, lobby_h + shaft_h + crown_h * 0.5), (sw, sd, crown_h), 0)
    else:
        sw, sd, ox = w, d, 0.0
    # Camera looks from the south, so the mullion and the bands sit on -Y.
    mullion = max(0.22, w * (0.055 + (kind % 3) * 0.018))
    mx = -w * 0.3 if kind % 2 == 0 else w * 0.16
    add_box(bm, (mx, -d * 0.5 - 0.07, lobby_h + shaft_h * 0.5), (mullion, 0.16, shaft_h * 0.9), 2)
    if kind in (3, 5, 9):
        add_box(bm, (-mx * 0.4, -d * 0.5 - 0.06, lobby_h + shaft_h * 0.45), (mullion * 0.65, 0.14, shaft_h * 0.62), 2)
    step = (2.3, 2.9, 3.5, 2.5, 4.1, 2.6, 3.1, 2.4, 3.7, 2.8)[kind]
    band = 0.38 + (kind % 3) * 0.14
    z = lobby_h + step * 0.7
    limit = lobby_h + shaft_h - 0.6
    guard = 0
    while z < limit and guard < 36:
        add_box(bm, (0, -d * 0.5 - 0.04, z), (w * 0.7, 0.1, band), 1)
        if kind % 2 == 1:
            add_box(bm, (w * 0.5 + 0.04, 0, z), (0.1, d * 0.55, band * 0.8), 1)
        z += step
        guard += 1
    # A second color block, proud of the front face.
    add_box(
        bm,
        (-w * 0.2, -d * 0.5 - 0.05, lobby_h + shaft_h * 0.58),
        (w * 0.32, 0.14, shaft_h * 0.48),
        0,
    )
    if crown:
        roof = lobby_h + shaft_h + crown_h
        for i in range(1 + kind % 3):
            add_box(bm, (ox + sw * (-0.22 + 0.2 * i), sd * 0.12, roof + 0.32), (0.65, 0.5, 0.62), 2)
        mast = 1.6 + (kind % 5) * 1.15
        add_box(bm, (ox, 0, roof + mast * 0.5), (0.1, 0.1, mast), 2)
        if kind in (2, 6, 9):
            add_box(bm, (ox + 0.45, 0, roof + mast * 0.7), (1.05, 0.06, 0.06), 2)
    layer = bm.loops.layers.color.new("Col")
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert.co
            if vert.x < -w * 0.02:
                shade = (0.74, 0.82, 0.93, 1.0)
            elif vert.y < -d * 0.15:
                shade = (1.0, 0.96, 0.9, 1.0)
            else:
                shade = (0.88, 0.9, 0.94, 1.0)
            if crown and vert.z > lobby_h + shaft_h:
                shade = (shade[0] * 0.8, shade[1] * 0.8, shade[2] * 0.84, 1.0)
            loop[layer] = shade
    return mesh_from_bm(name, bm)


def _on_deck(x, y, pad=16.0):
    return abs(x - _deck_x(y)) < pad


def _mark(kit, coll, name, center, size, mat):
    """A painted marking. It fades once the forest has taken the street."""
    obj = box_object(name, coll, center, size, mat)
    kit.add(obj, "road_mark", sink=False)
    return obj


def _asphalt_plane(name, coll, center, size, fallback):
    """Asphalt. Wide planes are a grid so the cracked-asphalt displacement can show."""
    mat = private_assets.road_asphalt_material() or fallback
    w, d = size
    bm = bmesh.new()
    step = 1.1 if max(w, d) > 16.0 else 0.0
    uv = None
    tile = 4.0
    if step <= 0.0:
        verts = [
            bm.verts.new((-w / 2, -d / 2, 0)),
            bm.verts.new((w / 2, -d / 2, 0)),
            bm.verts.new((w / 2, d / 2, 0)),
            bm.verts.new((-w / 2, d / 2, 0)),
        ]
        face = bm.faces.new(verts)
        uv = bm.loops.layers.uv.new("UVMap")
        for loop in face.loops:
            loop[uv].uv = ((loop.vert.co.x + w / 2) / tile, (loop.vert.co.y + d / 2) / tile)
    else:
        nx = max(2, int(w / step))
        ny = max(2, int(d / step))
        grid = []
        for iy in range(ny + 1):
            row = []
            for ix in range(nx + 1):
                row.append(bm.verts.new((-w / 2 + w * ix / nx, -d / 2 + d * iy / ny, 0)))
            grid.append(row)
        uv = bm.loops.layers.uv.new("UVMap")
        for iy in range(ny):
            for ix in range(nx):
                face = bm.faces.new((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))
                for loop in face.loops:
                    loop[uv].uv = ((loop.vert.co.x + w / 2) / tile, (loop.vert.co.y + d / 2) / tile)
    me = mesh_from_bm(name, bm)
    obj = link_obj(name, me, coll, (mat,))
    obj.location = (center[0], center[1], center[2])
    return obj


def _rotated_mark(kit, coll, name, origin, offset, size, yaw, pitch, mat):
    """A paint box. Local +Y runs along the road after ``yaw``."""
    rx, ry = math.cos(yaw), math.sin(yaw)
    # right_vector() is local +X at DECK_ROT_Z; yaw here is that same angle.
    mark = box_object(name, coll, (0, 0, 0), size, mat)
    mark.location = (origin[0] + rx * offset, origin[1] + ry * offset, origin[2])
    mark.rotation_euler = (pitch, 0.0, yaw)
    kit.add(mark, "road_mark", sink=False)
    return mark


def _road_span(coll, name, a, b, width, z, mat):
    """Asphalt from ``a`` to ``b``. Local +Y runs along the segment, matching the deck."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 0.5:
        return None
    obj = box_object(name, coll, (0.0, 0.0, 0.0), (width, length, 0.08), mat)
    obj.location = ((ax + bx) * 0.5, (ay + by) * 0.5, z)
    obj.rotation_euler.z = -math.atan2(dx, dy)
    return obj


def _paint_along(kit, coll, a, b, z, mats):
    """Double yellow and lane dashes, using the same offsets as the bridge deck."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 2.0:
        return
    ux, uy = dx / length, dy / length
    # Local +X at theta = -atan2(dx, dy) is the right-hand side of the road.
    theta = -math.atan2(dx, dy)
    rx, ry = math.cos(theta), math.sin(theta)
    cursor = 2.0
    while cursor < length - 2.0:
        px = ax + ux * cursor
        py = ay + uy * cursor
        for sign in (-1.0, 1.0):
            _rotated_mark(kit, coll, "net_yellow", (px, py, z + 0.03), sign * 0.12, (0.10, 4.0, 0.03), theta, 0.0, mats["yellow"])
        if int(cursor / 4.0) % 3 == 0:
            for offset in (-LANE_W, LANE_W):
                _rotated_mark(kit, coll, "net_dash", (px, py, z + 0.03), offset, (0.12, DASH_LEN, 0.03), theta, 0.0, mats["mark"])
        cursor += 4.0
    # Edge lines so the four lanes read as one roadway.
    for side in (-1.0, 1.0):
        mark = box_object("net_edge", coll, (0.0, 0.0, 0.0), (0.12, length - 1.0, 0.02), mats["mark"])
        mark.location = ((ax + bx) * 0.5 + rx * side * (DECK_HALF - 0.3), (ay + by) * 0.5 + ry * side * (DECK_HALF - 0.3), z + 0.03)
        mark.rotation_euler.z = theta
        kit.add(mark, "road_mark", sink=False)


def _east_west_road(kit, coll, mats, name, y, x0, x1, z, road):
    """One far-bank arterial. It crosses the bridge approach and both streets."""
    _asphalt_plane(name, coll, ((x0 + x1) * 0.5, y, z + 0.01), (x1 - x0, DECK_W), fallback=road)
    for sign in (-1.0, 1.0):
        _mark(kit, coll, name + "_yellow", ((x0 + x1) * 0.5, y + sign * 0.12, z + 0.04), (x1 - x0 - 8.0, 0.10, 0.03), mats["yellow"])
    crossings = [_deck_x(y), *CITY_STREETS]
    cursor = x0 + 2.0
    while cursor < x1 - 2.0:
        if any(abs(cursor - cx) < DECK_HALF + 2.0 for cx in crossings):
            cursor += 4.0
            continue
        for offset in (-LANE_W, LANE_W):
            _mark(kit, coll, name + "_dash", (cursor, y + offset, z + 0.04), (DASH_LEN, 0.12, 0.03), mats["mark"])
        cursor += DASH_LEN + DASH_GAP


def _far_bank_network(kit, coll, mats):
    """The bridge comes ashore into a grid that stays on land.

    A riverside drive stops the two north-south streets before the water.
    The approach crosses that drive, the landing arterial, a mid-town
    arterial, and ends on a northern arterial with blocks on every side.
    """
    road = private_assets.road_asphalt_material() or mats["road"]
    z = FAR_Z + 0.05
    x0, x1 = min(CITY_STREETS) - 150.0, max(CITY_STREETS) + 150.0
    _east_west_road(kit, coll, mats, "riverside", RIVER_DRIVE_Y, x0, x1, z, road)
    land = deck_point(FAR_ROAD_S)
    inland = deck_point(deck_s_at_y(FAR_END_Y))
    _road_span(coll, "far_approach", land, inland, DECK_W, z, road)
    _paint_along(kit, coll, land, inland, z, mats)
    fx, fy = land
    _east_west_road(kit, coll, mats, "far_arterial", fy, x0, x1, z + 0.004, road)
    _east_west_road(kit, coll, mats, "far_arterial_2", FAR_MID_Y, x0, x1, z + 0.004, road)
    _east_west_road(kit, coll, mats, "far_arterial_end", FAR_END_Y, x0, x1, z + 0.004, road)
    # On-ramps: leave the approach and meet the landing arterial beside the intersection.
    ramp_s = deck_s_at_y(fy + 28.0)
    rx, ry = right_vector()
    mouth = deck_point(ramp_s)
    for side in (-1.0, 1.0):
        start = (mouth[0] + rx * side * 6.0, mouth[1] + ry * side * 6.0)
        end = (fx + side * 42.0, fy)
        _road_span(coll, "far_ramp", start, end, 8.0, z + 0.012, road)


def _build_streets(kit, coll, mats):
    """One 4-lane avenue and one cross street, meeting at a single intersection.

    The north leg is the bridge ramp. Crosswalks exist only here, one per leg.
    """
    road_z = ROAD_Z
    y = AVE_Y
    paint_z = road_z + 0.045
    ix = CROSS_X
    depth = ZEBRA_DEPTH
    x_west = -88.0
    x_east = 72.0
    open_half = DECK_HALF
    _asphalt_plane("avenue", coll, ((x_west + x_east) / 2.0, y, road_z), (x_east - x_west, AVENUE_HALF * 2.0), fallback=mats["road"])
    # Shoulder south of the sidewalk, so the bottom of the frame is pavement.
    walk_s = y - AVENUE_HALF - SIDEWALK_W / 2.0
    walk_n = y + AVENUE_HALF + SIDEWALK_W / 2.0
    apron_far = walk_s - SIDEWALK_W / 2.0
    # Warm concrete under the south blocks. The old trim read as a navy lot.
    _plane("city_floor", coll, (0.0, -40.0, road_z - 0.08), (520.0, 280.0), mats["concrete"])
    _plane("near_shoulder", coll, ((x_west + x_east) / 2.0, apron_far / 2.0, road_z - 0.02), (x_east - x_west, max(apron_far, 1.0)), mats["concrete"])
    stub_end = -120.0
    stub_near = y - AVENUE_HALF
    _asphalt_plane(
        "south_leg",
        coll,
        (ix, (stub_end + stub_near) / 2.0, road_z + 0.008),
        (DECK_W, stub_near - stub_end),
        fallback=mats["road"],
    )
    for name, cx, width in (
        ("walk_sw", (x_west + ix - open_half) / 2.0, ix - open_half - x_west),
        ("walk_se", (ix + open_half + x_east) / 2.0, x_east - (ix + open_half)),
    ):
        _plane(name, coll, (cx, walk_s, road_z + 0.04), (width, SIDEWALK_W), mats["concrete"])
        _plane(name + "n", coll, (cx, walk_n, road_z + 0.04), (width, SIDEWALK_W), mats["concrete"])
    # Sidewalks beside the south leg, meeting the avenue sidewalk.
    side = DECK_HALF + 1.4
    _plane("stub_walk_w", coll, (ix - side, (stub_end + stub_near) / 2.0, road_z + 0.04), (2.2, stub_near - stub_end), mats["concrete"])
    _plane("stub_walk_e", coll, (ix + side, (stub_end + stub_near) / 2.0, road_z + 0.04), (2.2, stub_near - stub_end), mats["concrete"])
    for cy, span in (
        (y - AVENUE_HALF, (x_west, ix - open_half)),
        (y - AVENUE_HALF, (ix + open_half, x_east)),
        (y + AVENUE_HALF, (x_west, ix - open_half)),
        (y + AVENUE_HALF, (ix + open_half, x_east)),
    ):
        a, b = span
        box_object("curb", coll, ((a + b) / 2.0, cy, road_z + 0.12), (b - a, 0.18, 0.16), mats["concrete"])
    for x in range(-80, 64, 28):
        if abs(x - ix) < open_half + 6.0:
            continue
        _lamp(kit, coll, mats, x, walk_s, road_z + 0.05)
        _lamp(kit, coll, mats, x, walk_n, road_z + 0.05)

    # Paint runs continuously and stops on the outer edge of each crosswalk.
    paint_west = ix - open_half - depth - STOP_SETBACK
    paint_east = ix + open_half + depth + STOP_SETBACK
    for a, b in ((x_west, paint_west), (paint_east, x_east)):
        if b - a < 1.0:
            continue
        for sign in (-1.0, 1.0):
            _mark(kit, coll, "park_line", ((a + b) / 2.0, y + sign * AVE_HALF, paint_z), (b - a, 0.12, 0.03), mats["mark"])
        for line in (-0.11, 0.11):
            _mark(kit, coll, "yellow", ((a + b) / 2.0, y + line, paint_z + 0.004), (b - a, 0.10, 0.03), mats["yellow"])
    phase = x_west + 2.0
    cursor = phase
    while cursor < x_east:
        a = cursor
        b = cursor + DASH_LEN
        cursor += DASH_LEN + DASH_GAP
        for x0, x1 in ((x_west, paint_west), (paint_east, x_east)):
            if a >= x0 and b <= x1:
                for offset in (-LANE_W, LANE_W):
                    _mark(kit, coll, "lane", ((a + b) / 2.0, y + offset, paint_z), (DASH_LEN, 0.12, 0.03), mats["mark"])
    zebra_z = road_z + 0.002
    for zebra in (
        private_assets.place_zebra(coll, ix - open_half - depth / 2.0, y, zebra_z, 0.0, AVENUE_HALF * 2.0, depth),
        private_assets.place_zebra(coll, ix + open_half + depth / 2.0, y, zebra_z, 0.0, AVENUE_HALF * 2.0, depth),
        # The south leg slab sits 8 mm above the avenue. The zebra has to clear it.
        private_assets.place_zebra(coll, ix, y - AVENUE_HALF - depth / 2.0, road_z + 0.014, math.pi / 2.0, DECK_W, depth),
    ):
        if zebra is not None:
            kit.add(zebra, "road_mark", sink=False)
    s_zebra = deck_s_at_y(y + AVENUE_HALF) + depth / 2.0
    zx, zy = deck_point(s_zebra)
    ramp_zebra = private_assets.place_zebra(
        coll, zx, zy, deck_z(s_zebra) + RIBBON_TOP + 0.002,
        math.pi / 2.0 - BRIDGE_YAW, DECK_W, depth,
    )
    if ramp_zebra is not None:
        kit.add(ramp_zebra, "road_mark", sink=False)
    # Stop lines sit in front of the crosswalk, across the lanes that must stop.
    _mark(kit, coll, "stop_eb", (paint_west, y - AVE_HALF / 2.0, paint_z + 0.004), (0.28, AVE_HALF, 0.02), mats["mark"])
    _mark(kit, coll, "stop_wb", (paint_east, y + AVE_HALF / 2.0, paint_z + 0.004), (0.28, AVE_HALF, 0.02), mats["mark"])
    _mark(
        kit, coll, "stop_nb",
        (ix + DECK_HALF / 2.0, y - AVENUE_HALF - depth - STOP_SETBACK, paint_z + 0.01),
        (DECK_HALF, 0.28, 0.03),
        mats["mark"],
    )
    s_stop = deck_s_at_y(y + AVENUE_HALF) + depth + STOP_SETBACK
    px, py = deck_point(s_stop)
    rx, ry = right_vector()
    stop = box_object("stop_sb", coll, (0, 0, 0), (DECK_HALF, 0.28, 0.03), mats["mark"])
    stop.location = (px - rx * DECK_HALF / 2.0, py - ry * DECK_HALF / 2.0, deck_z(s_stop) + RIBBON_TOP + 0.02)
    stop.rotation_euler[2] = DECK_ROT_Z
    kit.add(stop, "road_mark", sink=False)
    # Short centerline on the south leg, south of its stop line.
    yellow_n = y - AVENUE_HALF - depth - STOP_SETBACK - 1.2
    if yellow_n - stub_end > 2.0:
        for line in (-0.11, 0.11):
            _mark(kit, coll, "stub_yellow", (ix + line, (yellow_n + stub_end) / 2.0, paint_z + 0.01), (0.10, yellow_n - stub_end, 0.03), mats["yellow"])
    corners = (
        (ix - open_half - 1.6, y + AVENUE_HALF + 1.3, -0.6),
        (ix + open_half + 1.6, y + AVENUE_HALF + 1.3, -2.4),
        (ix - open_half - 1.6, y - AVENUE_HALF - 1.3, 0.6),
        (ix + open_half + 1.6, y - AVENUE_HALF - 1.3, 2.4),
    )
    for sx, sy, yaw in corners:
        _prop(kit, coll, "signal", _kenney("props/traffic-light.glb"), (sx, sy, road_z + 0.05), yaw, 5.0, "prop")
    # Ramp paint starts north of the southbound stop line and climbs to the bank.
    s = s_stop + 2.6
    dash_at = DASH_GAP
    while s < NEAR_BANK_S - 1.5:
        px, py = deck_point(s)
        pz = deck_z(s) + RIBBON_TOP + 0.025
        ds = 0.4
        pitch = math.atan2(deck_z(s + ds) - deck_z(s - ds), 2.0 * ds)
        for sign in (-1.0, 1.0):
            _rotated_mark(kit, coll, "ramp_yellow", (px, py, pz), sign * 0.12, (0.10, 4.0, 0.03), DECK_ROT_Z, pitch, mats["yellow"])
        if dash_at >= DASH_GAP:
            for offset in (-LANE_W, LANE_W):
                _rotated_mark(kit, coll, "ramp_dash", (px, py, pz), offset, (0.12, DASH_LEN, 0.03), DECK_ROT_Z, pitch, mats["mark"])
            dash_at = 0.0
        else:
            dash_at += 4.0
        s += 4.0
    # Far bank. The deck comes ashore and becomes a street in the same grid
    # as the two north-south roads, with a cross street and a pair of ramps.
    _far_bank_network(kit, coll, mats)
    # South leg of the near intersection keeps the same four lanes as the deck.
    dash = stub_end + 4.0
    while dash < yellow_n - 4.0:
        for offset in (-LANE_W, LANE_W):
            _mark(kit, coll, "stub_lane", (ix + offset, dash, paint_z + 0.008), (0.12, DASH_LEN, 0.03), mats["mark"])
        dash += DASH_LEN + DASH_GAP


def _block_streets(kit, coll, mats):
    """North-south streets between the riverside drive and the last arterial.

    They meet those cross streets. They do not continue into the water or
    out into empty ground.
    """
    road_z = FAR_Z + 0.08
    y0 = RIVER_DRIVE_Y + DECK_HALF
    y1 = FAR_END_Y - DECK_HALF
    mid = (y0 + y1) / 2.0
    depth = y1 - y0
    for sx in CITY_STREETS:
        _plane("walk", coll, (sx, mid, road_z - 0.03), (13.0, depth), mats["concrete"])
        _plane("block_street", coll, (sx, mid, road_z), (8.5, depth), mats["road"])
        step = y0 + 6.0
        while step < y1:
            _mark(kit, coll, "block_dash", (sx, step, road_z + 0.05), (0.55, 3.2, 0.04), mats["mark"])
            step += 9.0


def _on_far_road(x, y, pad=8.0):
    """True when a footprint would sit on a far-bank road."""
    if on_block_street(x, pad):
        return True
    for road_y in (RIVER_DRIVE_Y, FAR_LAND_Y, FAR_MID_Y, FAR_END_Y):
        if abs(y - road_y) <= DECK_HALF + pad * 0.45:
            return True
    if y <= FAR_END_Y + 24.0 and abs(x - _deck_x(y)) <= DECK_HALF + pad:
        return True
    return False


def _fit_block(coll, filename, x, y, z, lot, height, yaw, name):
    """One hub block, shrunk until its footprint sits inside the lot."""
    block = private_assets.place_city_block(
        coll, filename, x, y, z, yaw=yaw, height=height, min_z=2.0, name=name,
    )
    if block is None:
        return None
    bpy.context.view_layer.update()
    xs, ys = [], []
    for obj in block.children_recursive:
        if getattr(obj, "type", "") != "MESH":
            continue
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
    if xs:
        wide = max(max(xs) - min(xs), max(ys) - min(ys), 0.01)
        if wide > lot:
            block.scale *= lot / wide
    return block


def _fill_far_bank(kit, coll):
    """Hub city blocks filling the lots. A few real towers are the ones that fall."""
    files = ("procedural_city_3.glb", "procedural_city_6.glb", "procedural_city_4.glb")
    spots = []
    for y in (210.0, 248.0, 345.0, 400.0):
        for x in (-130.0, -78.0, 98.0, 150.0):
            if not _on_far_road(x, y, 16.0):
                spots.append((x, y))
    placed = 0
    for i, (x, y) in enumerate(spots):
        block = _fit_block(
            coll, files[i % len(files)], x, y, FAR_Z, 108.0,
            58.0 if y < 300.0 else 74.0, 0.08 if i % 2 == 0 else math.pi, "far_block",
        )
        if block is None:
            continue
        kit.add(block, "building_base", sink=True, skeleton=False, near_bank=y < 300.0)
        found_assets.stamp_object(block, "plaster")
        placed += 1
    # Landmarks the wide camera can still read after the roofs fail.
    for i, (x, y, height, topple) in enumerate((
        (-88.0, 205.0, 52.0, False),
        (-36.0, 228.0, 64.0, True),
        (22.0, 198.0, 58.0, True),
        (78.0, 236.0, 46.0, False),
        (-96.0, 360.0, 72.0, False),
        (36.0, 372.0, 60.0, False),
        (128.0, 214.0, 44.0, False),
        (-48.0, 410.0, 68.0, False),
    )):
        if _on_far_road(x, y, 10.0):
            continue
        built = private_assets.place_tower(coll, x, y, FAR_Z, height)
        if built is None and cc0_city.ready():
            built = cc0_city.place_tower(coll, x, y, FAR_Z, height)
        if built is None:
            continue
        kit.add(
            built, "building_base", sink=True,
            skeleton=height > 66.0, topple=topple, near_bank=y < 300.0,
        )
        found_assets.stamp_object(built, "plaster")
        for k, slug in enumerate(("moss_01", "fern_02", "shrub_01", "fern_02")):
            _plant(
                kit, coll, slug, x + (k - 1.5) * 1.4, y - 5.5, FAR_Z + k * 2.2,
                0.7 + k * 0.25, delay=0.28, yaw=k,
            )
        placed += 1
    return placed


def _jagged_stump(coll, x, y):
    """Cut the top off a real tower on a noisy line, so the stump is not a flat box."""
    src = private_assets.place_tower(coll, x, y, FAR_Z, 36.0)
    if src is None or src.type != "MESH" or src.data is None:
        return src
    src.data = src.data.copy()
    me = src.data
    zs = [vert.co.z for vert in me.vertices]
    if not zs:
        return src
    lo, hi = min(zs), max(zs)
    span = max(hi - lo, 0.01)
    rng = random.Random(int(x * 13 + y))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    kill = []
    for vert in bm.verts:
        t = (vert.co.z - lo) / span
        wobble = 0.08 * math.sin(vert.co.x * 2.4 + vert.co.y * 1.7)
        if t > 0.36 + wobble + rng.uniform(-0.04, 0.05):
            kill.append(vert)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return src


def _ruin_city_path():
    """Hub copy of Ruined City Free 5. The Sketchfab download is the fallback."""
    hub = Path("/opt/cursor/asset-cache/private/debris/ruined_city_free_5.glb")
    if hub.exists():
        return hub
    return Path("/opt/cursor/asset-cache/private/sketchfab/city_blocks/ruined_city_free_5.glb")


def _ruin_shells():
    """Building shells from Ruined city FREE (5). Ground planes stay out."""
    if getattr(_ruin_shells, "protos", None) is not None:
        return _ruin_shells.protos
    path = _ruin_city_path()
    if not path.exists():
        _ruin_shells.protos = []
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    protos = []
    for obj in bpy.data.objects:
        if obj not in before:
            obj.hide_render = True
            obj.hide_viewport = True
        if obj not in before or obj.type != "MESH" or obj.data is None:
            continue
        pts = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        height = max(p.z for p in pts) - min(p.z for p in pts)
        width = max(max(p.x for p in pts) - min(p.x for p in pts), max(p.y for p in pts) - min(p.y for p in pts))
        # Keep ruined towers and broken blocks. Skip the city ground sheet.
        if 3.0 < height < 16.0 and width < 18.0:
            protos.append((obj, height))
    _ruin_shells.protos = protos
    return protos


def _spawn_shell(coll, src, native_h, x, y, z, target_h, yaw, name):
    copy = src.copy()
    coll.objects.link(copy)
    copy.parent = None
    copy.hide_render = False
    copy.hide_viewport = False
    factor = float(target_h) / max(native_h, 0.01)
    # Local scale sits under a glTF parent. Copying it bare makes a kilometre-tall shell.
    world_scale = src.matrix_world.to_scale()
    copy.scale = (abs(world_scale.x) * factor, abs(world_scale.y) * factor, abs(world_scale.z) * factor)
    world_rot = src.matrix_world.to_euler()
    copy.rotation_euler = (world_rot.x, world_rot.y, world_rot.z + float(yaw))
    copy.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    pts = [copy.matrix_world @ Vector(corner) for corner in copy.bound_box]
    copy.location = (
        float(x) - (min(p.x for p in pts) + max(p.x for p in pts)) * 0.5,
        float(y) - (min(p.y for p in pts) + max(p.y for p in pts)) * 0.5,
        float(z) - min(p.z for p in pts),
    )
    copy.name = name
    return copy


def _collapse_city(kit, coll):
    """Ruin shells and fallen towers that replace the skyline once it fails."""
    shells = ("Brick_Ruins_0b2b49b4", "Brick_Ruins_94d63184", "Scan_Rubble_ruins_01def269")
    mound = "Scan_Pile_of_rubble_8d90c8f1"
    placed = 0
    for y in (176.0, 214.0, 258.0, 312.0, 368.0, 424.0):
        for x in (-108.0, -52.0, 2.0, 52.0, 104.0, 154.0):
            if _on_far_road(x, y, 7.0):
                continue
            height = 16.0 + ((int(x) + int(y)) % 5) * 4.0
            obj = private_assets.place(
                coll, shells[placed % len(shells)], (x, y, FAR_Z), (placed % 6) * 0.5, height=height, name="shell",
            )
            if obj is not None:
                kit.add(obj, "shell", sink=False)
                placed += 1
            if placed % 2 == 0:
                pile = private_assets.place(
                    coll, mound, (x + 5.0, y - 4.0, FAR_Z), placed * 0.3, height=4.2, name="rubble_mound",
                )
                if pile is not None:
                    kit.add(pile, "shell", sink=False)
    shells_src = _ruin_shells()
    spots = []
    for y in (168.0, 198.0, 236.0, 286.0, 340.0, 400.0):
        for x in (-96.0, -40.0, 16.0, 72.0, 128.0):
            if not _on_far_road(x, y, 8.0):
                spots.append((x, y, FAR_Z, 22.0 + (abs(int(x + y)) % 4) * 5.0))
    for x, h in ((-28.0, 14.0), (-6.0, 16.0), (16.0, 13.0), (36.0, 15.0)):
        spots.append((x, 3.0, ROAD_Z, h))
    for i, (x, y, z, height) in enumerate(spots):
        if not shells_src:
            break
        src, native = shells_src[i % len(shells_src)]
        shell = _spawn_shell(coll, src, native, x, y, z, height, (i % 5) * 0.6, "ruin_shell")
        kit.add(shell, "shell", sink=False)
        placed += 1
    # Jagged stumps cut from real towers. They replace the standing meshes at year 500.
    for x, y in ((-60.0, 188.0), (10.0, 176.0), (70.0, 204.0), (-20.0, 260.0), (40.0, 330.0), (110.0, 250.0)):
        stump = _jagged_stump(coll, x, y)
        if stump is not None:
            kit.add(stump, "fallen", sink=False)
            placed += 1
    # Two real towers, already on their sides. They appear when the standing copies go.
    for x, y, yaw in ((-24.0, 198.0, 0.15), (46.0, 246.0, 0.9)):
        fallen = private_assets.place_tower(coll, x, y, FAR_Z, 46.0)
        if fallen is None and cc0_city.ready():
            fallen = cc0_city.place_tower(coll, x, y, FAR_Z, 46.0)
        if fallen is None:
            continue
        fallen.rotation_euler.x = 1.28
        fallen.rotation_euler.z = yaw
        kit.add(fallen, "fallen", sink=False)
        placed += 1
    placed += _scatter_hub_debris(kit, coll)
    return placed


def _fit_longest(coll, filename, loc, yaw, longest, name):
    """A hub debris mesh scaled so its longest side is ``longest`` metres."""
    path = Path("/opt/cursor/asset-cache/private/debris") / filename
    mesh = cc0_city.static_mesh(path) if path.exists() else None
    if mesh is None:
        return None
    size = cc0_city._mesh_size(mesh)
    scale = float(longest) / max(max(size), 0.01)
    return cc0_city._spawn(coll, mesh, loc, yaw, scale, name)


def _scatter_hub_debris(kit, coll):
    """Hub rubble, rebar, and cracked asphalt kitbashed into the ruined city."""
    z = ROAD_Z + 0.08
    fz = FAR_Z + 0.05
    # file, x, y, z, yaw, longest side, role
    spots = (
        ("concrete_rubble_steel.glb", -18.0, AVE_Y - 1.2, z, 0.4, 11.0, "ruin"),
        ("concrete_rubble_steel.glb", 22.0, AVE_Y + 2.2, z, 1.2, 9.0, "ruin"),
        ("pbr_debris.glb", -10.0, AVE_Y + 0.6, z, 0.2, 14.0, "ruin"),
        ("pbr_debris_3.glb", 6.0, AVE_Y - 2.4, z, 0.8, 10.0, "ruin"),
        ("pbr_debris_2.glb", -36.0, AVE_Y + 1.6, z, 1.6, 7.0, "ruin"),
        ("asphalt_02.glb", -6.0, AVE_Y, z, 0.05, 10.0, "groundwear"),
        ("asphalt_02.glb", 34.0, AVE_Y - 1.2, z, 0.15, 9.0, "groundwear"),
        ("asphalt_03.glb", 12.0, AVE_Y + 1.4, z, 0.0, 2.6, "groundwear"),
        ("wood_planks_debris.glb", -44.0, AVE_Y - 3.2, z, 0.6, 4.0, "ruin"),
        ("wood_planks_debris.glb", 46.0, AVE_Y + 3.0, z, 1.4, 3.4, "ruin"),
        ("trash_tarp.glb", -58.0, 8.0, ROAD_Z + 0.05, 0.3, 5.5, "ruin"),
        ("scan_pile_concrete.glb", -14.0, 176.0, fz, 0.5, 8.0, "ruin"),
        ("scan_pile_concrete.glb", 28.0, 168.0, fz, 1.1, 7.0, "ruin"),
        ("debris_kit.glb", -36.0, 192.0, fz, 0.4, 12.0, "ruin"),
        ("concrete_rubble_steel.glb", 4.0, 186.0, fz, 2.1, 14.0, "ruin"),
        ("pbr_debris_3.glb", 48.0, 178.0, fz, 0.7, 11.0, "ruin"),
        ("pbr_debris.glb", -62.0, 210.0, fz, 0.3, 16.0, "rubble_hill"),
        ("lowpoly_concrete_debris.glb", -90.0, 240.0, fz, 0.2, 18.0, "rubble_hill"),
        ("lowpoly_concrete_debris.glb", 70.0, 230.0, fz, 0.9, 16.0, "rubble_hill"),
        ("lowpoly_concrete_debris.glb", 18.0, 280.0, fz, 1.7, 22.0, "rubble_hill"),
        ("concrete_rubble_steel.glb", -8.0, 250.0, fz, 0.6, 18.0, "rubble_hill"),
        ("pbr_debris.glb", 36.0, 300.0, fz, 1.2, 20.0, "rubble_hill"),
    )
    placed = 0
    for filename, x, y, zz, yaw, longest, role in spots:
        obj = _fit_longest(coll, filename, (x, y, zz), yaw, longest, "debris")
        if obj is None:
            continue
        kit.add(obj, role, sink=False)
        placed += 1
    return placed


def _foothill_woods(kit, coll, mats):
    """Trees on the plain between the far bank and the range. Not a painted lawn."""
    rng = random.Random(23)
    placed = 0
    soil = found_assets.pbr_material("FoothillSoil", "leaves_forest_ground", uv=0.05) or mats["dirt"]
    sheet = _ground_sheet("foothill_land", coll, (400.0, 1300.0, FAR_Z - 0.04), (3200.0, 1700.0), soil, tile=22.0)
    kit.add(sheet, "mountain", sink=False)
    y = 560.0
    while y < 1750.0:
        x = -600.0
        while x < 1500.0:
            if abs(x - _deck_x(y)) < 36.0 and y < 800.0:
                x += 90.0
                continue
            _tree(
                kit, coll, mats, x + rng.uniform(-6.0, 6.0), y, FAR_Z,
                rng.uniform(12.0, 26.0), future=False, rng=rng,
                kind="pine" if (int(x + y) % 3 == 0) else "round",
            )
            placed += 1
            x += 95.0
        y += 110.0
    return placed


def _mesh_prop(coll, path, loc, yaw, height, name):
    """A downloaded mesh, bottom on loc, scaled to ``height`` metres."""
    mesh = cc0_city.static_mesh(Path(path))
    if mesh is None:
        return None
    size = cc0_city._mesh_size(mesh)
    scale = float(height) / max(size[2], 0.01)
    return cc0_city._spawn(coll, mesh, loc, yaw, scale, name)


def _park_approach(kit, coll):
    """Curbs and piers so the ramp reads as a road over the park, not a ribbon on grass."""
    roads = Path("/opt/cursor/asset-cache/cc0/extracted/roads_props/kenney_city_kit_roads/Models/GLB format")
    barrier = roads / "construction-barrier.glb"
    pillar = roads / "bridge-pillar.glb"
    if not barrier.exists():
        barrier = Path("/opt/cursor/asset-cache/cc0/extracted/ruins_decay/quaternius_post_apocalypse/glb/Traffic_Barrier_nugx3heueH.glb")
    rx, ry = right_vector()
    s = RAMP_FLAT_S + 2.0
    while s < NEAR_BANK_S - 1.0:
        x, y = deck_point(s)
        z = deck_z(s) + RIBBON_TOP
        for side in (-1.0, 1.0):
            edge = DECK_HALF + 0.7
            curb = _mesh_prop(
                coll, barrier,
                (x + rx * side * edge, y + ry * side * edge, z),
                DECK_ROT_Z, 1.7, "ramp_curb",
            )
            if curb is not None:
                kit.add(curb, "prop", sink=False)
            rise = z - PARK_Z
            if rise > 0.9 and pillar.exists():
                pier = _mesh_prop(
                    coll, pillar,
                    (x + rx * side * (DECK_HALF - 0.3), y + ry * side * (DECK_HALF - 0.3), PARK_Z),
                    DECK_ROT_Z, max(rise, 1.2), "ramp_pier",
                )
                if pier is not None:
                    kit.add(pier, "prop", sink=False)
        s += 8.0


def _seat_bottom(obj, z):
    """Drop a mesh so its lowest point sits on z."""
    bpy.context.view_layer.update()
    zs = [(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]
    if zs:
        obj.location.z += float(z) - min(zs)


def _heaved_avenue(kit, coll, mats):
    """Cracked, lifted asphalt on the near lanes. Hidden until the first weeds."""
    damaged = found_assets.pbr_material("HeavedAsphalt", "road_damaged", uv=0.35, displace=0.12) or mats["road"]
    road_z = ROAD_Z
    w, d, step = 86.0, 16.0, 0.7
    bm = bmesh.new()
    nx, ny = int(w / step), int(d / step)
    rng = random.Random(21)
    grid = []
    for iy in range(ny + 1):
        row = []
        for ix in range(nx + 1):
            lift = rng.uniform(-0.08, 0.38) if 0 < ix < nx and 0 < iy < ny else 0.0
            row.append(bm.verts.new((-w / 2 + w * ix / nx, -d / 2 + d * iy / ny, lift)))
        grid.append(row)
    uv = bm.loops.layers.uv.new("UVMap")
    for iy in range(ny):
        for ix in range(nx):
            face = bm.faces.new((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))
            for loop in face.loops:
                loop[uv].uv = ((loop.vert.co.x + w / 2) / 4.0, (loop.vert.co.y + d / 2) / 4.0)
    patch = link_obj("heaved_avenue", mesh_from_bm("heaved_avenue", bm), coll, (damaged,))
    patch.location = (-6.0, AVE_Y, road_z + 0.04)
    kit.add(patch, "groundwear", sink=False)
    for i in range(48):
        _plant(
            kit, coll,
            ("grass_medium_01", "grass_bermuda_01", "weed_plant_02", "fern_02")[i % 4],
            -48.0 + (i % 16) * 5.4, AVE_Y + (-4.2 if i % 2 == 0 else 3.6), road_z,
            rng.uniform(0.45, 0.95), delay=0.12, yaw=i * 0.4,
        )


def _seat_mass(obj, z, bury=40.0):
    """Sit the body of a mesh on z. A few low outliers do not hold it in the air."""
    if obj is None or obj.type != "MESH" or obj.data is None:
        return
    bpy.context.view_layer.update()
    verts = obj.data.vertices
    if not verts:
        return
    step = max(1, len(verts) // 5000)
    world = obj.matrix_world
    zs = [(world @ verts[i].co).z for i in range(0, len(verts), step)]
    zs.sort()
    base = zs[max(0, int(len(zs) * 0.12))]
    obj.location.z += (float(z) - float(bury)) - base


def _mountain_scaled(coll, path, loc, yaw, scale, name):
    """Place a mountain that is already modelled in metres. ``scale`` is uniform."""
    mesh = cc0_city.static_mesh(Path(path))
    if mesh is None:
        return None
    return cc0_city._spawn(coll, mesh, loc, yaw, scale, name)


def _mountains(kit, coll):
    """Hub ranges, several kilometres behind the far bank. They do not age."""
    cache = Path("/opt/cursor/asset-cache/private/mountains")
    # gaea_range imports about 2 m across. The snow peak and the three-peaked
    # ridge already import at kilometre scale, so they only get a modest scale.
    placed = 0
    # Buried and further back so the cliff is not a wall in front of the peaks.
    span = _mesh_prop(coll, cache / "gaea_range.glb", (1400.0, 4600.0, FAR_Z - 70.0), 1.15, 0.23 * 1500.0, "gaea_range")
    if span is not None:
        kit.add(span, "mountain", sink=False)
        placed += 1
    # 2000 m across and 348 m tall at scale 1. 1.35 keeps the near edge past the skyline.
    snow = _mountain_scaled(coll, cache / "free_textured_mountain.glb", (500.0, 2900.0, FAR_Z), -0.15, 1.35, "snow_peak")
    if snow is not None:
        kit.add(snow, "mountain", sink=False)
        placed += 1
    trio = _mountain_scaled(coll, cache / "three_peaked.glb", (1900.0, 3300.0, FAR_Z), 0.2, 1.8, "three_peaks")
    if trio is not None:
        kit.add(trio, "mountain", sink=False)
        placed += 1
    # The photoscan faces the camera as a slab, so it stays out of this view.
    # A thin haze only. The last pass washed the peaks out.
    mesh = bpy.data.meshes.new("distance_haze")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    haze = bpy.data.objects.new("distance_haze", mesh)
    coll.objects.link(haze)
    haze.location = (900.0, 1100.0, 180.0)
    haze.scale = (5000.0, 400.0, 280.0)
    mat = bpy.data.materials.new("DistanceHaze")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    vol = tree.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.64, 0.74, 0.86, 1.0)
    vol.inputs["Density"].default_value = 0.00005
    tree.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    haze.data.materials.append(mat)
    kit.add(haze, "mountain", sink=False)
    return placed


def _south_city_blocks(kit, coll, mats, ix, road_z, street_west, street_east, front_north):
    """Real blocks south of the avenue: sidewalk, street wall, alley, cross street.

    The ground inside a block is concrete. A 12 m east-west street sits about
    90 m south of the avenue. BlendKit towers stand on the sidewalk line.
    """
    walk = 3.2
    ew_y = -62.0
    ew_half = 6.0
    _asphalt_plane(
        "ew_street",
        coll,
        (0.0, ew_y, road_z + 0.006),
        (210.0, ew_half * 2.0),
        fallback=mats["road"],
    )
    _plane("ew_walk_n", coll, (0.0, ew_y + ew_half + walk / 2.0, road_z + 0.04), (210.0, walk), mats["concrete"])
    _plane("ew_walk_s", coll, (0.0, ew_y - ew_half - walk / 2.0, road_z + 0.04), (210.0, walk), mats["concrete"])
    # Alleys: one north-south service lane through each block, plus a short
    # east-west alley behind the avenue frontage.
    for ax in (ix - 52.0, ix + 48.0):
        _asphalt_plane("alley", coll, (ax, -28.0, road_z + 0.01), (4.0, 70.0), fallback=mats["road"])
        _asphalt_plane("alley_s", coll, (ax, -95.0, road_z + 0.01), (4.0, 40.0), fallback=mats["road"])
    _asphalt_plane("alley_ew", coll, (ix - 52.0, -18.0, road_z + 0.012), (70.0, 3.6), fallback=mats["road"])
    _asphalt_plane("alley_ew_e", coll, (ix + 48.0, -18.0, road_z + 0.012), (64.0, 3.6), fallback=mats["road"])

    def courtyard(x0, x1, y0, y1):
        _plane(
            "court",
            coll,
            ((x0 + x1) / 2.0, (y0 + y1) / 2.0, road_z - 0.01),
            (x1 - x0, y1 - y0),
            mats["concrete"],
        )

    # Block faces. y increases north. The avenue frontage is the north edge.
    north_build = front_north - 0.4
    south_of_ew = ew_y - ew_half - walk
    north_of_ew = ew_y + ew_half + walk
    blocks = (
        (-100.0, street_west - walk, north_of_ew, north_build),
        (street_east + walk, 110.0, north_of_ew, north_build),
        (-100.0, street_west - walk, -120.0, south_of_ew),
        (street_east + walk, 110.0, -120.0, south_of_ew),
    )
    for x0, x1, y0, y1 in blocks:
        courtyard(x0, x1, y0, y1)
        _plane("perim_n", coll, ((x0 + x1) / 2.0, y1 + walk / 2.0, road_z + 0.045), (x1 - x0, walk), mats["concrete"])
        _plane("perim_s", coll, ((x0 + x1) / 2.0, y0 - walk / 2.0, road_z + 0.045), (x1 - x0, walk), mats["concrete"])
        _plane("perim_w", coll, (x0 - walk / 2.0, (y0 + y1) / 2.0, road_z + 0.045), (walk, y1 - y0), mats["concrete"])
        _plane("perim_e", coll, (x1 + walk / 2.0, (y0 + y1) / 2.0, road_z + 0.045), (walk, y1 - y0), mats["concrete"])

    def row(x0, x1, y, height, index0, facing=0.0):
        cursor = x0 + 6.0
        i = 0
        while cursor < x1 - 4.0:
            # Avenue frontage stays near 11 m so the locked camera still sees the road.
            h = height if abs(y - north_build) > 8.0 else min(height, 11.0)
            h += (i % 3) * 0.8
            obj = private_assets.place_tower(coll, cursor, y, road_z, h)
            if obj is not None:
                obj.rotation_mode = "XYZ"
                obj.rotation_euler.z = facing
                idx = index0 + i
                kit.add(obj, "frontage", sink=False, index=idx)
                if idx % 17 == 0:
                    pile = ico_object("rubble", coll, (cursor, y, road_z + 0.4), (1.6, 1.2, 0.7), mats["concrete"])
                    kit.add(pile, "rubble", sink=False, index=idx)
            cursor += 8.6
            i += 1
        return i

    n = 0
    for x0, x1, y0, y1 in blocks:
        # Continuous wall on the avenue side of the near blocks. Side and
        # back edges are the same buildings, set on the sidewalk line.
        n += row(x0 + 1.0, x1 - 1.0, y1 - 5.5, 18.0, n, 0.0)
        n += row(x0 + 1.0, x1 - 1.0, y0 + 6.0, 22.0, n, math.pi)
    # Same buildings from day 1 through year 500. Rubble is added on a few lots;
    # the towers themselves are not replaced.
    _street_facade(kit, coll, mats, -32.8, 0.3, road_z)


def _ruin_piece(coll, loc, yaw, height):
    """One damaged high-rise from Ruined City 5, bottom on loc."""
    shells = _ruin_shells()
    if not shells:
        return None
    src, native = max(shells, key=lambda item: item[1])
    if src is None:
        return None
    copy = src.copy()
    coll.objects.link(copy)
    copy.parent = None
    copy.hide_render = False
    copy.location = Vector((0.0, 0.0, 0.0))
    copy.rotation_euler.z = float(yaw)
    # Keep the source scale. Replacing it ignores the transform that made the measured height.
    factor = float(height) / max(native, 0.01)
    world_scale = src.matrix_world.to_scale()
    copy.scale = (abs(world_scale.x) * factor, abs(world_scale.y) * factor, abs(world_scale.z) * factor)
    world_rot = src.matrix_world.to_euler()
    copy.rotation_euler = (world_rot.x, world_rot.y, world_rot.z + float(yaw))
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for corner in copy.bound_box:
        point = copy.matrix_world @ Vector(corner)
        xs.append(point.x)
        ys.append(point.y)
        zs.append(point.z)
    copy.location = Vector((float(loc[0]) - (min(xs) + max(xs)) * 0.5, float(loc[1]) - (min(ys) + max(ys)) * 0.5, float(loc[2]) - min(zs)))
    return copy


def _only_beat(kit, obj, beat):
    """Show this object only while that episode beat is on screen."""
    if obj is None:
        return None
    return kit.add(obj, "segment_prop", only=beat, sink=False)


def _street_facade(kit, coll, mats, x, y, z):
    """Hub plants at the avenue building. The shader, displace, and ivy gen age the mesh."""
    face_y = y - 4.15
    for i, (dx, dz, slug) in enumerate((
        (-2.0, 1.2, "fern_02"), (-0.4, 2.4, "moss_01"), (1.6, 1.6, "fern_02"),
        (-1.2, 3.8, "shrub_01"), (1.1, 4.4, "moss_01"), (0.2, 5.5, "fern_02"),
    )):
        _plant(kit, coll, slug, x + dx, face_y - 0.35, z + dz, 0.8 + (i % 3) * 0.3, delay=0.32, yaw=i * 0.4)
    rng = random.Random(8)
    for i in range(22):
        _plant(
            kit, coll,
            ("grass_medium_01", "grass_medium_02", "fern_02", "shrub_02", "moss_01")[i % 5],
            x + rng.uniform(-6.0, 6.0), y - rng.uniform(5.0, 12.0), z,
            rng.uniform(0.4, 1.3), delay=0.3, yaw=i,
        )


def _place_hub_blocks(kit, coll, mats):
    """Pre-built hub blocks for the empty frontage and the skyline.

    Procedural City 3 flanks the south street up to the sidewalk, short along
    the avenue and taller behind it. City 4 fills the east lawn without
    covering the ramp or the river. City 6 and One WTC vary the far bank.
    Ruined city FREE 5 stands on that bank once the collapse channel rises.
    The commute pack is abandoned bikes and scooters. The airport scene is
    not used: its jet wears a Malaysia Airlines livery.

    Weeds, cracks, and dirt patches are hand-built. The hub blocks are
    buildings, not lawn debris, and no CC0 pack is a flat year-1 stain.
    """
    ix = CROSS_X
    road_z = ROAD_Z
    street_west = ix - DECK_HALF - 3.6
    street_east = ix + DECK_HALF + 3.6
    front_north = AVE_Y - AVENUE_HALF - SIDEWALK_W - 0.3

    def sit(filename, cx, cy, z, height, yaw, name, min_z=1.2, role="building_base", skeleton=False):
        block = private_assets.place_city_block(
            coll, filename, cx, cy, z, yaw=yaw, height=height, min_z=min_z, name=name,
        )
        if block is not None:
            kit.add(block, role, sink=True, skeleton=skeleton)
        return block

    _south_city_blocks(kit, coll, mats, ix, road_z, street_west, street_east, front_north)
    # East of the ramp: mid-rise canyon, not the suburban houses in City 4.
    # Height ~22 m keeps the block between the sidewalk and the river.
    sit("procedural_city_6.glb", 46.0, 58.0, PARK_Z, 22.0, 0.1, "east_mid_a")
    sit("procedural_city_6.glb", 92.0, 60.0, PARK_Z, 26.0, math.pi, "east_mid_b")
    # Cover the lawn under those blocks so the gaps are a plaza, not grass.
    _plane("east_plaza", coll, (68.0, 60.0, PARK_Z + 0.02), (108.0, 40.0), mats["concrete"])
    _asphalt_plane("plaza_cross", coll, (62.0, 58.0, PARK_Z + 0.04), (3.2, 34.0), fallback=mats["road"])
    _asphalt_plane("plaza_long", coll, (78.0, 70.0, PARK_Z + 0.04), (28.0, 3.2), fallback=mats["road"])

    for name, x, y, h, yaw in (("nyc_w", -110.0, 188.0, 52.0, 0.15), ("nyc_e", 95.0, 192.0, 46.0, -0.25)):
        sit("procedural_city_6.glb", x, y, FAR_Z, h, yaw, name)
    sit("one_wtc.glb", -78.0, 218.0, FAR_Z, 90.0, 0.45, "wtc", min_z=1.0, skeleton=True)

    # The far bank keeps its day-1 towers. They age in place; a second city is not swapped in.

    walk = AVE_Y - AVENUE_HALF - SIDEWALK_W * 0.35
    for i, x in enumerate((-62.0, -36.0, 28.0, 52.0)):
        bikes = private_assets.place_city_block(
            coll, "city_commute_transport.glb", x, walk, road_z + 0.02, yaw=0.2 * i, height=1.35, min_z=0.0, name="commute",
        )
        if bikes is not None:
            kit.add(bikes, "prop", sink=False)
    for i, y in enumerate((-8.0, -28.0, -52.0)):
        bikes = private_assets.place_city_block(
            coll, "city_commute_transport.glb", ix - DECK_HALF - 1.7, y, road_z + 0.02, yaw=1.2, height=1.3, min_z=0.0, name="commute_s",
        )
        if bikes is not None:
            kit.add(bikes, "prop", sink=False)

    # Real plants, not icosphere gems. They stay hidden until vegetation rises.
    rng = random.Random(5)
    meadow = ("grass_medium_01", "grass_medium_02", "grass_bermuda_01", "weed_plant_02", "dandelion_01")
    for i in range(36):
        wx = rng.uniform(-78.0, 8.0)
        wy = rng.uniform(40.0, 80.0)
        if abs(wx - _deck_x(wy)) < DECK_HALF + 3.5:
            continue
        _plant(kit, coll, meadow[i % len(meadow)], wx, wy, PARK_Z, rng.uniform(0.35, 0.8), delay=0.12, yaw=rng.random() * math.tau)
    for i, x in enumerate((-78.0, -58.0, -40.0, -18.0, 22.0, 40.0, 58.0)):
        for sign in (-1.0, 1.0):
            _plant(
                kit, coll, "grass_medium_01" if sign < 0 else "weed_plant_02",
                x, AVE_Y + sign * (AVENUE_HALF - 0.4), road_z,
                rng.uniform(0.28, 0.55), delay=0.08, yaw=rng.random() * 3.0,
            )
    for i, y in enumerate((-6.0, -22.0, -40.0, -58.0, -78.0)):
        _plant(kit, coll, "fern_02", ix - DECK_HALF + 0.6, y, road_z, 0.7, delay=0.2, yaw=1.2)
    hx, hy, _hyaw = HERO_SPORTS
    for i, (dx, dy, slug, height, delay) in enumerate((
        (-1.6, 0.7, "grass_bermuda_01", 0.35, 0.35),
        (0.4, -0.8, "grass_medium_02", 0.45, 0.4),
        (1.8, 0.5, "weed_plant_02", 0.55, 0.42),
        (-0.3, 1.3, "moss_01", 0.22, 0.5),
        (2.2, -1.4, "fern_02", 0.6, 0.48),
        (-2.4, -0.4, "dandelion_01", 0.28, 0.18),
    )):
        _plant(kit, coll, slug, hx + dx, hy + dy, road_z, height, delay=delay, yaw=i * 0.7)
    for x, lane in ((-64.0, -4.0), (-40.0, 3.5), (-18.0, -2.0), (30.0, 4.0), (52.0, -3.2), (-50.0, 6.0), (-8.0, -5.5), (12.0, 3.0)):
        _tree(kit, coll, mats, x, AVE_Y + lane, road_z, 2.6, future=True, delay=0.55, rng=rng, kind="round")
        _plant(kit, coll, "fir_sapling", x + 1.4, AVE_Y + lane, road_z, 1.6, delay=0.5, yaw=0.4, role="tree_canopy")
    for x, y in ((-70.0, -8.0), (-48.0, -6.0), (-22.0, -10.0), (8.0, -8.0)):
        _plant(kit, coll, "pine_sapling_small", x, y, road_z + 11.0, 2.2, delay=0.62, yaw=0.5, role="tree_canopy")
    for x, lane in ((-55.0, 1.5), (18.0, -5.0), (42.0, 2.0)):
        _tree(kit, coll, mats, x, AVE_Y + lane, road_z, 3.1, future=True, delay=0.8, rng=rng, kind="pine")
    grass_mat = found_assets.pbr_material("AvenueGrass", "grass_ground", uv=0.2) or mats["dirt"]
    sheet = _plane("walk_blanket", coll, (0.0, AVE_Y - AVENUE_HALF - 1.6, road_z + 0.05), (180.0, 3.4), grass_mat)
    kit.add(sheet, "blanket", sink=False)
    sheet_n = _plane("walk_blanket_n", coll, (0.0, AVE_Y + AVENUE_HALF + 1.6, road_z + 0.05), (180.0, 3.4), grass_mat)
    kit.add(sheet_n, "blanket", sink=False)
    deer = cc0_city.place_deer(coll, -28.0, 156.0, FAR_Z)
    if deer is not None:
        kit.add(deer, "animal", sink=False)


def _close_forest(kit, coll, mats):
    """Year 100 greens the beige lots. Year 500 closes a canopy over them."""
    rng = random.Random(19)
    road_z = ROAD_Z
    grasses = ("grass_medium_01", "grass_medium_02", "grass_bermuda_01", "weed_plant_02", "dandelion_01")
    for i in range(90):
        _plant(
            kit, coll, grasses[i % len(grasses)],
            rng.uniform(-110.0, 70.0), rng.uniform(-120.0, 12.0), road_z,
            rng.uniform(0.4, 1.1), delay=0.4, yaw=rng.random() * math.tau,
        )
    for i in range(40):
        _plant(
            kit, coll, "shrub_01" if i % 2 == 0 else "shrub_02",
            rng.uniform(-100.0, 50.0), rng.uniform(-100.0, 8.0), road_z,
            rng.uniform(1.0, 2.0), delay=0.42, yaw=rng.random() * math.tau,
        )
    for i in range(28):
        _tree(
            kit, coll, mats,
            rng.uniform(-95.0, 40.0), rng.uniform(-90.0, 6.0),
            road_z, rng.uniform(2.8, 4.2), future=True, delay=0.4, rng=rng,
            kind="pine" if i % 3 == 0 else "round",
        )
    for i in range(22):
        _tree(
            kit, coll, mats,
            rng.uniform(-80.0, 30.0), rng.choice((-70.0, -40.0, -16.0, AVE_Y - 3.0, AVE_Y, AVE_Y + 4.0)),
            road_z, rng.uniform(3.4, 5.0), future=True, delay=0.74, rng=rng,
            kind="pine" if i % 2 == 0 else "round",
        )
    grass = decay_vfx.crack_material("LotGrass", "grass_ground") or mats["park"]
    soil = decay_vfx.crack_material("LotSoil", "leaves_forest_ground") or mats["dirt"]
    # Crack mask widens with the years. Day 1 is invisible; year 500 covers the lot.
    lot = _ground_sheet("lot_grass", coll, (-20.0, -80.0, road_z + 0.08), (420.0, 150.0), grass, tile=3.2)
    kit.add(lot, "crack_sheet", sink=False)
    for lx, ly in ((-40.0, -30.0), (-8.0, -55.0), (24.0, -16.0), (-70.0, -90.0), (-32.0, -12.0)):
        pad = _ground_sheet("litter_pad", coll, (lx, ly, road_z + 0.1), (16.0, 10.0), soil, tile=2.2)
        kit.add(pad, "crack_sheet", sink=False)
    meadow = decay_vfx.crack_material("ClosedGrass", "grass_ground") or grass
    sheet = _ground_sheet("avenue_meadow", coll, (-8.0, AVE_Y + 6.0, road_z + 0.05), (160.0, 12.0), meadow, tile=2.6)
    kit.add(sheet, "crack_sheet", sink=False)
    for i in range(20):
        _tree(
            kit, coll, mats,
            rng.uniform(-70.0, 55.0), rng.uniform(40.0, 78.0),
            road_z, rng.uniform(2.6, 4.8), future=True, delay=0.72, rng=rng,
            kind="pine" if i % 2 == 0 else "round",
        )
    # Erosion, displace, and the proximity ivy live in decay_vfx.install.


def _hero_broken_road(kit, coll, mats):
    """Cracked, displaced asphalt under the husk, hidden on day 1."""
    hx, hy, _yaw = HERO_SPORTS
    road_z = ROAD_Z
    cracked = decay_vfx.crack_material("HeroSoil", "grass_ground") or mats["park"]
    w, d, step = 20.0, 14.0, 0.45
    bm = bmesh.new()
    nx, ny = int(w / step), int(d / step)
    grid = []
    for iy in range(ny + 1):
        row = []
        for ix in range(nx + 1):
            row.append(bm.verts.new((-w / 2 + w * ix / nx, -d / 2 + d * iy / ny, 0.0)))
        grid.append(row)
    uv = bm.loops.layers.uv.new("UVMap")
    for iy in range(ny):
        for ix in range(nx):
            face = bm.faces.new((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))
            for loop in face.loops:
                loop[uv].uv = ((loop.vert.co.x + w / 2) / 3.0, (loop.vert.co.y + d / 2) / 3.0)
    me = mesh_from_bm("hero_cracks", bm)
    patch = link_obj("hero_cracks", me, coll, (cracked,))
    patch.location = (hx, hy, road_z + 0.03)
    kit.add(patch, "groundwear", sink=False)
    color = Path("/workspace/assets/found/ambientcg/AsphaltDamageSet001/AsphaltDamageSet001_1K-JPG_Color.jpg")
    opacity = Path("/workspace/assets/found/ambientcg/AsphaltDamageSet001/AsphaltDamageSet001_1K-JPG_Opacity.jpg")
    decal = None
    if color.exists() and opacity.exists():
        decal = bpy.data.materials.new("AsphaltDecal")
        decal.use_nodes = True
        tree = decal.node_tree
        tree.nodes.clear()
        out = tree.nodes.new("ShaderNodeOutputMaterial")
        bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
        diff = tree.nodes.new("ShaderNodeTexImage")
        diff.image = bpy.data.images.load(str(color), check_existing=True)
        mask = tree.nodes.new("ShaderNodeTexImage")
        mask.image = bpy.data.images.load(str(opacity), check_existing=True)
        mask.image.colorspace_settings.name = "Non-Color"
        tree.links.new(diff.outputs["Color"], bsdf.inputs["Base Color"])
        tree.links.new(mask.outputs["Color"], bsdf.inputs["Alpha"])
        bsdf.inputs["Roughness"].default_value = 0.9
        tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        decal.blend_method = "HASHED"
    rng = random.Random(4)
    for i in range(10):
        if decal is None:
            break
        mark = box_object(
            "crack_decal", coll,
            (hx + rng.uniform(-7.0, 7.0), hy + rng.uniform(-4.0, 4.0), road_z + 0.05),
            (rng.uniform(1.4, 3.2), rng.uniform(0.35, 0.8), 0.01),
            decal,
        )
        mark.rotation_euler.z = rng.uniform(0.0, math.pi)
        kit.add(mark, "groundwear", sink=False)
    for i in range(16):
        _plant(
            kit, coll, ("grass_medium_01", "grass_bermuda_01", "fern_02", "weed_plant_02")[i % 4],
            hx + rng.uniform(-6.0, 5.0), hy + rng.uniform(-5.5, 2.0), road_z,
            rng.uniform(0.35, 0.9), delay=0.4, yaw=i,
        )
    # Through the bonnet once the nose has swung toward the camera.
    _plant(kit, coll, "fir_sapling", hx + 0.85, hy - 0.7, road_z, 2.3, delay=0.45, yaw=0.4, role="tree_canopy")


def _break_river_span(obj, coll, kit, mats):
    """Jag the near end of the river deck and hang rebar, a bent rail, and debris off it."""
    me = obj.data
    if me is None or not me.vertices:
        return
    ys = [vert.co.y for vert in me.vertices]
    xs = [vert.co.x for vert in me.vertices]
    use_y = (max(ys) - min(ys)) >= (max(xs) - min(xs))
    lo = min(ys if use_y else xs)
    hi = max(ys if use_y else xs)
    span = max(hi - lo, 0.01)
    rng = random.Random(11)
    for vert in me.vertices:
        coord = vert.co.y if use_y else vert.co.x
        t = (hi - coord) / span
        if t < 0.86:
            continue
        jag = (t - 0.86) / 0.14
        vert.co.z += rng.uniform(-0.95, 0.2) * jag
        if use_y:
            vert.co.y -= rng.uniform(0.0, 0.7) * jag
        else:
            vert.co.x -= rng.uniform(0.0, 0.7) * jag
    me.update()
    rust = found_assets.pbr_material("SpanRust", "rusty_metal_02", uv=0.7) or mats["bridge"]
    rebar_mat = found_assets.pbr_material("SpanRebar", "rebar_reinforced_concrete", uv=1.4) or rust
    end = min(me.vertices, key=lambda vert: vert.co.y if use_y else vert.co.x)
    for i in range(9):
        bar = link_obj("rebar", cylinder_mesh("rebar", radius=0.04, segments=6), coll, (rebar_mat,))
        bar.parent = obj
        bar.matrix_parent_inverse = Matrix.Identity(4)
        bar.location = end.co + Vector((rng.uniform(-1.6, 1.6), rng.uniform(-0.2, 0.5), rng.uniform(-0.15, 0.25)))
        bar.rotation_euler = (rng.uniform(0.6, 1.5), rng.uniform(-0.5, 0.5), rng.uniform(0.0, 1.2))
        bar.scale = (1.0, 1.0, rng.uniform(0.7, 1.6))
    rail = box_object("rail", coll, (0.0, 0.0, 0.0), (0.1, 5.5, 0.1), rust)
    rail.parent = obj
    rail.matrix_parent_inverse = Matrix.Identity(4)
    rail.location = end.co + Vector((DECK_HALF * 0.55, 2.2, 0.85))
    rail.rotation_euler = (1.05, 0.55, 0.4)
    layer = box_object("asphalt_layer", coll, (0.0, 0.0, 0.0), (4.2, 0.22, 0.07), mats["road"])
    layer.parent = obj
    layer.matrix_parent_inverse = Matrix.Identity(4)
    layer.location = end.co + Vector((0.2, 0.4, 0.12))
    layer.rotation_euler = (0.35, 0.2, 0.15)
    for i in range(3):
        bit = found_assets.place(coll, "bark_debris_01" if i else "dry_branches_medium_01", (0, 0, 0), 0.2, 0.35, "span_debris")
        if bit is None:
            continue
        bit.name = "span_debris"
        bit.parent = obj
        bit.matrix_parent_inverse = Matrix.Identity(4)
        bit.location = end.co + Vector((rng.uniform(-1.0, 1.0), rng.uniform(0.2, 1.4), 0.2))
    # Thick broken end the span camera looks at. The face is jagged, not a flat top.
    concrete = found_assets.pbr_material("SpanConcrete", "cracked_concrete", uv=0.7, displace=0.05) or mats["concrete"]
    asphalt = found_assets.pbr_material("SpanAsphalt", "road_damaged_2", uv=0.8) or mats["road"]
    mossy = found_assets.pbr_material("SpanMoss", "concrete_moss", uv=0.9) or concrete
    face_y = 112.0
    origin_x = 16.0
    for ix in range(6):
        length = 3.4 + ((ix * 3) % 5) * 0.55
        for iz in range(5):
            slab = box_object(
                "deck_ply",
                coll,
                (origin_x + ix * 1.15, face_y + length * 0.5, 0.45 + iz * 0.24),
                (1.1, length, 0.22),
                mossy if iz == 4 else concrete,
            )
            kit.add(slab, "rubble", sink=False)
            if iz == 2:
                rod = link_obj("rebar", cylinder_mesh("span_rebar", radius=0.05, segments=5), coll, (rust,))
                rod.location = (origin_x + ix * 1.15, face_y - 0.2, 0.6 + iz * 0.24)
                rod.rotation_euler = (1.35, 0.15 * ix, 0.2)
                rod.scale = (1.0, 1.0, 1.6 + (ix % 3) * 0.35)
                kit.add(rod, "rubble", sink=False)
    cap = box_object("asphalt_cap", coll, (origin_x + 3.2, face_y + 2.6, 1.72), (6.4, 4.2, 0.12), asphalt)
    kit.add(cap, "rubble", sink=False)
    for post, py in enumerate((face_y + 1.0, face_y + 2.8, face_y + 4.6)):
        rail = box_object("rail", coll, (origin_x + 6.4, py, 2.2 if post < 2 else 1.15), (0.14, 0.14, 0.95 if post < 2 else 1.7), rust)
        if post == 2:
            rail.rotation_euler = (1.2, 0.15, 0.35)
        kit.add(rail, "rubble", sink=False)
    rail_top = box_object("rail", coll, (origin_x + 6.4, face_y + 2.4, 2.65), (0.1, 4.2, 0.1), rust)
    kit.add(rail_top, "rubble", sink=False)
    fallen = box_object("span_debris", coll, (origin_x + 1.5, face_y - 3.2, 0.2), (4.8, 2.4, 0.85), concrete)
    fallen.rotation_euler = (1.05, 0.4, 0.2)
    kit.add(fallen, "rubble", sink=False)
    for i in range(5):
        rod = link_obj("rebar", cylinder_mesh("fallen_rebar", radius=0.05, segments=5), coll, (rust,))
        rod.location = (origin_x + 0.4 + i * 0.7, face_y - 3.6, 0.35)
        rod.rotation_euler = (0.5, 1.2, i * 0.4)
        rod.scale = (1.0, 1.0, 1.5)
        kit.add(rod, "rubble", sink=False)
    for i, (px, py, slug) in enumerate((
        (origin_x + 1.2, face_y + 1.6, "moss_01"),
        (origin_x + 3.4, face_y + 2.4, "grass_bermuda_01"),
        (origin_x + 2.2, face_y + 3.2, "fern_02"),
        (origin_x + 4.6, face_y + 1.2, "weed_plant_02"),
    )):
        _plant(kit, coll, slug, px, py, 1.9, 0.4 + i * 0.06, delay=0.3, yaw=i)


def build_river_city(kit, mats, rng, pieces):
    col_g = kit.collection("Terrain")
    col_c = kit.collection("City")
    col_b = kit.collection("Bridge")
    col_v = kit.collection("Life")
    col_p = kit.collection("Plants")
    # Real scale. Park and the avenue stay above the river. The far bank is
    # city on day 1 so the horizon is not a green field; forest_floor covers
    # it only after the vegetation channel rises.
    _plane("bedrock", col_g, (0, 800, -6.0), (4000, 4000), mats["trim"], 0.4)
    _build_streets(kit, col_g, mats)
    # Lawn from the sidewalk to the quay. A gap leaves the ramp uncovered.
    park_y0 = 36.0
    park_y1 = RIVER_Y0 - 2.2
    ramp_x = CROSS_X
    gap = DECK_HALF + 2.2
    park_mid = (park_y0 + park_y1) / 2.0
    park_depth = park_y1 - park_y0
    _plane("park_w", col_g, ((-450 + ramp_x - gap) / 2.0, park_mid, PARK_Z), (ramp_x - gap - (-450), park_depth), mats["park"])
    _plane("park_e", col_g, ((ramp_x + gap + 450) / 2.0, park_mid, PARK_Z), (450 - (ramp_x + gap), park_depth), mats["park"])
    for name, px, py, hx, hy in PATHS:
        _plane(name, col_g, (px, py, PARK_Z + 0.04), (hx * 2, hy * 2), mats["concrete"])
    # Stone quay, about 2.5 m of face above the lawn, with a railing.
    # The wall stays on the bank. The water sheet starts at RIVER_Y0.
    wall_base = PARK_Z - 0.3
    wall_h = QUAY_Z - wall_base
    wall_y = (park_y1 + RIVER_Y0) / 2.0
    box_object(
        "quay_wall",
        col_g,
        (0, wall_y, wall_base + wall_h / 2),
        (980, RIVER_Y0 - park_y1, wall_h),
        mats["concrete"],
    )
    for x in range(-80, 90, 8):
        box_object("quay_post", col_g, (x, wall_y + 0.15, QUAY_Z + 0.45), (0.12, 0.12, 0.9), mats["trim"])
        if x < 82:
            box_object("quay_rail", col_g, (x + 4, wall_y + 0.15, QUAY_Z + 0.82), (8.0, 0.06, 0.06), mats["trim"])
    # Far bank only. A sheet from y=0 buried the river, the lawn, and the avenue.
    far_near = RIVER_Y1 + 1.0
    far_depth = 1100.0
    _plane("city_ground", col_g, (0, far_near + far_depth / 2.0, FAR_Z), (2400, far_depth), mats["trim"])
    # The range sits kilometres past the city. The plain under it is the same land.
    _plane("range_plain", col_g, (200.0, 4200.0, FAR_Z - 6.0), (12000, 7000), mats["trim"])
    floor = _plane(
        "forest_floor",
        col_g,
        (0, far_near + far_depth / 2.0, FAR_Z + 0.06),
        (2400, far_depth),
        mats["park"],
    )
    kit.add(floor, "forest_floor", sink=False)
    _block_streets(kit, col_g, mats)

    if "subway" in pieces:
        # A concrete entrance on the lawn. No black pit: that read as a hole in the grass.
        pad = box_object("stair", col_g, (-28.0, 70.0, PARK_Z + 0.16), (3.4, 2.2, 0.28), mats["concrete"])
        box_object("rail_a", col_g, (-29.4, 70.0, PARK_Z + 0.7), (0.12, 2.0, 1.1), mats["trim"])
        box_object("rail_b", col_g, (-26.6, 70.0, PARK_Z + 0.7), (0.12, 2.0, 1.1), mats["trim"])
        kit.add(pad, "road_slab", index=0, sink=False)

    # Three depths. Center towers stay shorter so the title has open sky.
    # Colors and heights live in city_layout so a pass cannot quietly drop them.
    colors = SKYLINE_COLORS
    # Only the far layer is lifted toward haze. Near and mid rows stay saturated.
    haze = ((0.0, 0.0, 0.0), (0.04, 0.05, 0.06), (0.12, 0.14, 0.16), (0.22, 0.24, 0.26))
    rows = SKYLINE_ROWS
    for row, (y, hmin, hmax, x0, x1, wr) in enumerate(rows):
        x = x0
        while x < x1:
            w = rng.uniform(*wr)
            # The bridge approach is a road. Towers stay off it on every row,
            # not only the first, and the gap is the road plus the building's own width.
            # The near far-bank is filled with hub blocks. Tiny towers here read as scattered boxes.
            if y < FAR_END_Y - 20.0:
                x += max(w, 48.0)
                continue
            corridor = abs(x - _deck_x(y)) < (w * 0.5 + DECK_HALF + 6.0) and y < FAR_END_Y + 30.0
            if corridor or on_block_street(x, w * 0.5 + 1.0):
                x += 6.0
                continue
            h = rng.uniform(hmin, hmax)
            # Neighbors jump between short and tall instead of clustering in the middle.
            if rng.random() < 0.4:
                h = hmin + (hmax - hmin) * (0.12 if rng.random() < 0.45 else 0.94)
            # Roofs left of the portal stay under the open sky the title uses.
            if x < 12.0:
                h = min(h, 38.0)
            # 30% salmon, 30% blue/teal, 25% grey, 15% white.
            roll = (row * 17 + int(x * 3)) % 20
            if roll < 6:
                base_col = ((0.78, 0.34, 0.30, 1), (0.84, 0.42, 0.36, 1), (0.70, 0.28, 0.26, 1))[roll % 3]
            elif roll < 12:
                base_col = ((0.45, 0.70, 0.86, 1), (0.38, 0.66, 0.78, 1), (0.55, 0.78, 0.88, 1))[roll % 3]
            elif roll < 17:
                base_col = ((0.62, 0.66, 0.70, 1), (0.72, 0.74, 0.76, 1))[roll % 2]
            else:
                base_col = (0.94, 0.94, 0.93, 1)
            hz = haze[row]
            color = (
                min(1.0, base_col[0] + hz[0]),
                min(1.0, base_col[1] + hz[1]),
                min(1.0, base_col[2] + hz[2]),
                1,
            )
            # A packed tower replaces the box when that record is enabled and on disk.
            built = private_assets.place_tower(col_c, x, y, FAR_Z, h)
            if built is None and cc0_city.ready():
                built = cc0_city.place_tower(col_c, x, y, FAR_Z, h)
            if built is not None:
                kit.add(built, "building_base", sink=True, skeleton=False, near_bank=True, topple=(int(x) % 110 < 22))
                x += w + rng.uniform(4.0, 8.0)
                continue
            if _library_tower(kit, col_c, x, y, FAR_Z, h, color):
                x += w + rng.uniform(4.0, 8.0)
                continue
            # No primitive stand-in. The lot stays open until a downloaded block fills it.
            x += 8.0

    _fill_far_bank(kit, col_c)
    _place_hub_blocks(kit, col_c, mats)
    _park_approach(kit, col_g)
    _mountains(kit, col_c)
    _foothill_woods(kit, kit.collection("Plants"), mats)
    _collapse_city(kit, col_c)
    _heaved_avenue(kit, col_g, mats)
    # Broken shells and rubble the wide camera can still read after the towers fail.
    for ruin_loc, ruin_h, ruin_yaw in (
        ((-18.0, 4.0, ROAD_Z), 14.0, 0.2),
        ((-42.0, 8.0, ROAD_Z), 11.0, 1.1),
        ((6.0, 178.0, FAR_Z), 24.0, 0.15),
        ((-28.0, 208.0, FAR_Z), 20.0, 0.8),
        ((38.0, 196.0, FAR_Z), 28.0, -0.35),
        ((-72.0, 242.0, FAR_Z), 18.0, 1.4),
        ((86.0, 228.0, FAR_Z), 22.0, 2.2),
        ((12.0, 268.0, FAR_Z), 26.0, 0.4),
        ((-8.0, 156.0, FAR_Z), 9.0, 0.6),
        ((30.0, 162.0, FAR_Z), 8.0, 1.7),
        ((-55.0, 188.0, FAR_Z), 10.0, -0.2),
        ((60.0, 250.0, FAR_Z), 16.0, 0.9),
    ):
        shell = _ruin_piece(col_c, ruin_loc, ruin_yaw, ruin_h)
        if shell is not None:
            kit.add(shell, "ruin", sink=False)

    if "power" in pieces:
        _power_plant(kit, col_c, mats, -70.0, 280.0, FAR_Z)

    if "bridge" in pieces:
        _bridge(kit, col_b, col_v, mats, rng)

    # Irregular clusters, not two ruler-straight rows. Kept off the deck.
    fx, fy = FOUNTAIN
    pad = link_obj("plaza", cylinder_mesh("plaza", radius=4.2, segments=24), col_g, (mats["concrete"],))
    pad.location = (fx, fy, PARK_Z + 0.02)
    pad.scale = (1.0, 1.0, 0.08)
    basin = link_obj("basin", cylinder_mesh("basin", radius=1.7, segments=20), col_g, (mats["water"],))
    basin.location = (fx, fy, PARK_Z + 0.1)
    basin.scale = (1.0, 1.0, 0.06)
    kit.add(pad, "prop", sink=False)
    kit.add(basin, "prop", sink=False)
    # Trees about 8 m tall, set beside the paths rather than on them.
    yellow = (0.78, 0.62, 0.16, 1)
    planted = 0
    for col, x in enumerate((-48.0, -34.0, -18.0)):
        for row, y in enumerate((40.0, 52.0, 66.0, 80.0)):
            px = x
            py = y
            if _on_deck(px, py, 10) or math.hypot(px - fx, py - fy) < 7.0:
                continue
            leaf = yellow if planted % 7 == 2 else None
            _tree(
                kit, col_p, mats, px, py, PARK_Z,
                rng.uniform(2.5, 3.1), future=False, rng=rng, kind="round", leaf=leaf,
            )
            planted += 1
    for x, y in ((-46, 44), (-30, 60), (-14, 76), (fx - 6.5, fy)):
        _lamp(kit, col_g, mats, x, y, PARK_Z)
    for i in range(4):
        ang = i / 4.0 * math.tau + 0.4
        bx = fx + math.cos(ang) * 6.4
        by = fy + math.sin(ang) * 6.4
        bench = private_assets.place_bench(col_g, bx, by, PARK_Z, ang + math.pi)
        if bench is not None:
            kit.add(bench, "prop", sink=False)
        else:
            bench = _prop(
                kit, col_g, "bench", _kenney("props/bench/bench.glb"),
                (bx, by, PARK_Z), ang + math.pi, 0.8, "prop",
            )
            if bench is None:
                box_object("bench", col_g, (bx, by, PARK_Z + 0.4), (1.6, 0.5, 0.8), mats["wood"])
    for i in range(8):
        bed_x = rng.uniform(-38, -2)
        bed_y = rng.uniform(42, 74)
        if _on_deck(bed_x, bed_y, 12):
            continue
        bed = box_object("bed", col_g, (bed_x, bed_y, PARK_Z + 0.12), (2.2, 1.3, 0.16), mats["dirt"])
        kit.add(bed, "prop", sink=False)
        for k in range(5):
            flower = ico_object("flower", col_p, (bed_x + rng.uniform(-0.8, 0.8), bed_y + rng.uniform(-0.4, 0.4), PARK_Z + 0.35), 0.22, mats["leaf"])
            flower.color = [(0.85, 0.35, 0.38, 1), (0.9, 0.78, 0.3, 1), (0.85, 0.55, 0.7, 1)][k % 3]
            kit.add(flower, "flower", sink=False, leaf=tuple(flower.color), autumn=(0.45, 0.32, 0.18, 1))

    if "forest" in pieces:
        kinds = ("round", "broad", "pine")
        for ix in range(-20, 24, 9):
            for iy in range(40, 76, 10):
                if _on_deck(ix, iy, 12):
                    continue
                _tree(
                    kit, col_p, mats, ix, iy, PARK_Z,
                    rng.uniform(3.5, 6.5), future=True, delay=rng.uniform(0.22, 0.5),
                    rng=rng, kind=rng.choice(kinds),
                )
        for ix in range(-80, 100, 12):
            for iy in (162, 180, 200):
                if _on_far_road(ix, iy, 7.0):
                    continue
                _tree(
                    kit, col_p, mats, ix, iy, FAR_Z,
                    rng.uniform(7.0, 12.0), future=True, delay=rng.uniform(0.28, 0.55),
                    rng=rng, kind=rng.choice(kinds),
                )
        for ix in range(-280, 300, 16):
            for iy in (230, 270, 320, 380):
                if _on_far_road(ix, iy, 6.0):
                    continue
                _tree(
                    kit, col_p, mats, ix, iy, FAR_Z,
                    rng.uniform(7.0, 12.0), future=True, delay=0.18 + (abs(ix) % 5) * 0.04,
                    rng=rng, kind=rng.choice(kinds),
                )
        for i in range(28):
            x = rng.uniform(-70, 20)
            y = rng.uniform(46, 76)
            if _on_deck(x, y, 9) or abs(y - AVE_Y) < AVENUE_HALF + 2.0:
                continue
            _plant(
                kit, col_p, "shrub_01" if i % 2 == 0 else "shrub_02",
                x, y, PARK_Z, rng.uniform(0.7, 1.3), delay=rng.uniform(0.2, 0.55), yaw=rng.random() * 6.0,
            )
        # These stay small at year 100 and close the canopy at year 500.
        for i in range(36):
            x = rng.uniform(-90.0, 70.0)
            y = rng.choice((AVE_Y - 2.0, AVE_Y + 3.0, 48.0, 64.0, 210.0, 250.0, 340.0))
            if _on_deck(x, y, 8) or _on_far_road(x, y, 6.0) or abs(y - AVE_Y) < 1.2:
                continue
            _tree(
                kit, col_p, mats, x, y, ROAD_Z if y < 40.0 else (PARK_Z if y < 90.0 else FAR_Z),
                rng.uniform(4.0, 7.5), future=True, delay=0.72, rng=rng,
                kind="pine" if i % 2 == 0 else "round",
            )

    # People stand on paths, the promenade, and around the fountain. A few on the grass.
    def _on_path(px, py):
        for _name, cx, cy, hx, hy in PATHS:
            if abs(px - cx) <= hx and abs(py - cy) <= hy:
                return True
        return False

    for _name, cx, cy, hx, hy in PATHS:
        if _name == "plaza":
            continue
        steps = 4 if hy > hx else 5
        for i in range(steps):
            t = (i + 0.5) / steps - 0.5
            px = cx + (0 if hy > hx else t * hx * 1.6)
            py = cy + (t * hy * 1.6 if hy > hx else 0)
            if _on_deck(px, py, 8) or py > RIVER_Y0 - 4 or py < AVE_Y + AVENUE_HALF + SIDEWALK_W:
                continue
            _person(kit, col_v, mats, px, py, PARK_Z, rng)
    for i in range(8):
        ang = i / 8.0 * math.tau
        _person(kit, col_v, mats, fx + math.cos(ang) * 5.2, fy + math.sin(ang) * 5.2, PARK_Z, rng)
    walk_y = AVE_Y + AVENUE_HALF + SIDEWALK_W * 0.5
    for x in (-40, -24, -8, 16, 32):
        _person(kit, col_v, mats, x, walk_y, ROAD_Z + 0.06, rng, clip="Walk")
    if cc0_city.ready():
        # Two quiet gags: someone flossing on the far bank, and a deer grazing.
        dancer = cc0_city.place_dancer(col_v, -30.0, 156.0, FAR_Z)
        if dancer is not None:
            kit.add(dancer, "person", float=0.2, bob=0.0, sink=False)
        phone = cc0_city.place_phone_walker(col_v, -34.0, walk_y, ROAD_Z + 0.06, yaw=0.2)
        if phone is not None:
            kit.add(phone, "person", float=0.2, bob=0.0, sink=False)
        deer = cc0_city.place_deer(col_v, -36.0, 70.0, PARK_Z)
        if deer is not None:
            kit.add(deer, "animal", sink=False)
        _blendkit_crowd(kit, col_v, col_g)
    for i in range(16):
        x = rng.uniform(-50, 10)
        y = rng.uniform(42, 76)
        if _on_deck(x, y, 8) or _on_path(x, y) or math.hypot(x - fx, y - fy) < 6:
            continue
        _person(kit, col_v, mats, x, y, PARK_Z, rng)
    white = (0.93, 0.93, 0.94, 1)
    hx, hy, hyaw = HERO_SPORTS
    _car(
        kit, col_v, mats, (hx, hy, ROAD_Z), hyaw, (1.0, 1.0, 1.0),
        drive=0.0, index=2, hero=True, paint=(1.0, 1.0, 1.0),
    )
    # A real sapling in the rear engine bay. Not parented: the Miura empty is scaled ~100x.
    if cc0_city.ready():
        sap = cc0_city.place_tree(
            col_v, hx - math.cos(hyaw) * 1.7, hy - math.sin(hyaw) * 1.7, ROAD_Z, 1.5, kind="round",
        )
        if sap is not None:
            kit.add(sap, "tree_canopy", future=True, delay=0.55, sink=False, leaf=(0.22, 0.45, 0.16, 1))
    # Debris stays off the car until the rust channel rises, so day 1 stays the showroom Miura.
    for slug, dx, dy, height, yaw in (
        ("moss_01", -0.2, 0.35, 0.18, 0.4),
        ("bark_debris_01", 0.6, -0.15, 0.22, 1.2),
        ("dry_branches_medium_01", -0.8, 0.1, 0.28, 0.6),
        ("old_tyre", 1.5, 0.9, 0.35, 0.2),
        ("rusted_wheel_rim_01", 0.35, -1.45, 0.72, 0.5),
        ("rusted_wheel_rim_01", -1.4, 0.05, 0.72, 1.2),
        ("moss_01", 0.1, 0.05, 0.28, 0.3),
        ("fern_02", -0.35, 0.15, 0.32, 1.1),
    ):
        z_lift = 1.02 if slug in ("moss_01", "fern_02") and abs(dx) < 0.5 else (0.55 if slug == "moss_01" else 0.0)
        _plant(kit, col_v, slug, hx + dx, hy + dy, ROAD_Z + z_lift, height, delay=0.0, yaw=yaw, role="wreckage")
    leaf = found_assets.pbr_material("HuskLeaves", "forest_leaves_02", uv=1.2) or mats["leaf"]
    for dx, dy, sx in ((0.2, 0.05, 1.1), (-0.45, 0.12, 0.8), (0.7, -0.05, 0.7)):
        pad = box_object("husk_leaf", col_v, (hx + dx, hy + dy, ROAD_Z + 1.05), (sx, 0.55, 0.03), leaf)
        kit.add(pad, "wreckage", sink=False)
    hero = next((item.obj for item in kit.items if item.extra.get("hero")), None)
    found_assets.arm_wreck(hero)
    _alive(kit, col_v)
    for i, (x, y, yaw) in enumerate(FOREGROUND_CARS):
        _car(
            kit,
            col_v,
            mats,
            (x, y, ROAD_Z),
            yaw,
            white,
            drive=0.0,
            model="sedan",
            scale=1.35,
            paint=(0.94, 0.94, 0.95, 1),
            index=i,
            force_white=True,
        )

    bm = bmesh.new()
    # Local top is z=0, so effects can set location.z to the river surface.
    add_box(
        bm,
        (0, 0, -0.25),
        (RIVER_X1 - RIVER_X0, RIVER_Y1 - RIVER_Y0, 0.5),
        0,
    )
    water = link_obj("water", mesh_from_bm("water", bm), col_g, (mats["water"],))
    water.location = ((RIVER_X0 + RIVER_X1) / 2, (RIVER_Y0 + RIVER_Y1) / 2, city_water_top())
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "city"
    for item in kit.items:
        if item.role == "frontage":
            found_assets.stamp_object(item.obj, "plaster")
        elif item.role in ("bridge_deck", "bridge_tower"):
            found_assets.stamp_object(item.obj, "metal" if item.role == "bridge_tower" else "road")
        elif item.role == "prop" and any(token in item.obj.name for token in ("east", "nyc", "wtc", "block", "tower", "pier")):
            found_assets.stamp_object(item.obj, "plaster")
    road_mat = private_assets.road_asphalt_material()
    found_assets.stamp_material(road_mat, "road")
    found_assets.stamp_material(mats.get("road"), "road")
    found_assets.stamp_material(mats.get("deck"), "road")
    found_assets.stamp_material(mats.get("facade"), "plaster")
    found_assets.stamp_material(mats.get("concrete"), "plaster")
    found_assets.stamp_material(mats.get("bridge"), "metal")
    found_assets.stamp_material(mats.get("wall"), "plaster")
    _close_forest(kit, kit.collection("Terrain"), mats)
    _hero_broken_road(kit, kit.collection("Terrain"), mats)
    decay_vfx.install(kit)
    for i, y in enumerate((112.0, 122.0, 132.0, 142.0)):
        _plant(kit, kit.collection("Bridge"), "fern_02" if i % 2 == 0 else "nettle_plant", 3.5 + i * 0.8, y, 0.15, 0.9, delay=0.45, yaw=i)
        _plant(kit, kit.collection("Bridge"), "moss_01", 8.0 - i * 0.4, y + 2.0, 0.1, 0.3, delay=0.4, yaw=0.5)


def _blendkit_crowd(kit, col_v, col_g):
    """Posed people, a cat, street props, and the ruins that show up later."""
    if not private_assets.ready():
        return
    fx, fy = FOUNTAIN
    walk_y = AVE_Y + AVENUE_HALF + SIDEWALK_W * 0.5

    def person(token, loc, yaw, height, name):
        obj = private_assets.place(col_v, token, loc, yaw, height=height, name=name)
        if obj is not None:
            kit.add(obj, "person", float=0.0, bob=0.0, sink=False)

    person("Young_guy_keeps_his_hands_in_pockets_ad9f69fc", (-28.0, walk_y, ROAD_Z + 0.06), 0.4, 1.75, "pockets")
    person("Lowpoly_Male_Standing_14ab4e7e", (-18.0, 50.0, PARK_Z), 1.2, 1.75, "standing")
    person("Lowpoly_Female_Talking_by_phone_87771976", (-32.0, 58.0, PARK_Z), 2.4, 1.75, "phone_talk")
    person("Lowpoly_Male_Sitting_db2280bf", (fx + 4.6, fy + 4.2, PARK_Z), 0.8, 1.25, "sitting")
    cat = private_assets.place_cat(col_v, -42.0, 64.0, PARK_Z, yaw=1.1)
    if cat is not None:
        kit.add(cat, "animal", sink=False)
    hydrant = private_assets.place_hydrant(col_g, -14.0, walk_y, ROAD_Z)
    if hydrant is not None:
        kit.add(hydrant, "prop", sink=False)
    for token, loc, yaw, height in (
        ("TrashCanSmall", (-20.0, walk_y, ROAD_Z), 0.4, 0.95),
        ("ParkingMeter", (-30.0, walk_y, ROAD_Z), 0.2, 1.35),
        ("Dumpster_Dumpster", (-16.0, 40.0, PARK_Z), 1.1, 1.45),
    ):
        prop = private_assets.place_city_prop(col_g, token, loc, yaw, height=height, name="prop")
        if prop is not None:
            kit.add(prop, "prop", sink=False)

    def ruin(token, loc, yaw, longest):
        obj = private_assets.place(col_g, token, loc, yaw, longest=longest, name="ruin")
        if obj is not None:
            kit.add(obj, "ruin", sink=False)

    ruin("Trash_Heap_62d00c11", (-22.0, 58.0, PARK_Z), 0.4, 4.5)
    ruin("Scan_Rubble_ruins_01def269", (8.0, 162.0, FAR_Z), 0.2, 9.0)
    ruin("Brick_Ruins_0b2b49b4", (-8.0, 48.0, PARK_Z), 0.6, 2.4)
    ruin("Brick_Ruins_0b2b49b4", (-44.0, 72.0, PARK_Z), 1.4, 2.4)
    ruin("Dead_Tree_Trunk_02_7723c39f", (-46.0, 62.0, PARK_Z), 0.7, 4.2)
    flame = private_assets.place(col_g, "Animated_Fire_Volume_73a03e3d", (-36.0, 168.0, 22.0), 0.0, height=2.4, name="outage")
    if flame is not None:
        kit.add(flame, "flame", index=0, outage=True, sink=False)


def _power_plant(kit, coll, mats, x, y, z):
    for i, dx in enumerate((-1.1, 1.1)):
        bm = bmesh.new()
        add_box(bm, (0, 0, 0.6), (1.5, 1.5, 1.2), 0)
        add_box(bm, (0, 0, 2.0), (1.15, 1.15, 1.8), 0)
        add_box(bm, (0, 0, 3.3), (0.85, 0.85, 1.0), 0)
        obj = link_obj("cool", mesh_from_bm("cool", bm), coll, (mats["trim"],))
        obj.location = (x + dx, y, z)
        kit.add(obj, "building_base", sink=True)
    stack = box_object("stack", coll, (x + 2.4, y + 0.4, z + 2.4), (0.55, 0.55, 4.8), mats["trim"])
    kit.add(stack, "building_base", sink=True)
    for i in range(3):
        puff = ico_object("puff", coll, (x + 2.4, y + 0.4, z + 5.2), (0.6, 0.6, 0.5), mats["smoke"])
        kit.add(puff, "smoke", index=i, sink=True, phase=i / 3.0)


def _deck_edge_s(s, side, half=DECK_HALF):
    x, y = deck_point(s)
    rx, ry = right_vector()
    return (x + rx * half * side, y + ry * half * side, deck_z(s) + 0.6)


def _deck_edge(y, side, half=DECK_HALF):
    s = deck_s_at_y(y)
    x, yy = deck_point(s)
    rx, ry = right_vector()
    return (x + rx * half * side, yy + ry * half * side, deck_z(s) + 2.2)


def _deck_ribbon(coll, mats, s0, s1, surface="deck"):
    """A slab whose cross-section is vertical, so two spans that share s meet flush."""
    from mathutils import Vector

    rx, ry = right_vector()
    half = DECK_HALF
    top = RIBBON_TOP
    thick = 0.55
    curb = 0.22
    samples = max(2, int(abs(s1 - s0) / 4.0) + 1)
    bm = bmesh.new()
    loops = []
    for i in range(samples):
        t = i / (samples - 1)
        s = s0 + (s1 - s0) * t
        x, y = deck_point(s)
        z = deck_z(s)
        left = bm.verts.new((x - rx * half, y - ry * half, z + top))
        right = bm.verts.new((x + rx * half, y + ry * half, z + top))
        left_b = bm.verts.new((x - rx * half, y - ry * half, z + top - thick))
        right_b = bm.verts.new((x + rx * half, y + ry * half, z + top - thick))
        # Curb sits on the same samples, so it arrives flat with the roadway.
        il = bm.verts.new((x - rx * (half - curb), y - ry * (half - curb), z + top))
        ir = bm.verts.new((x + rx * (half - curb), y + ry * (half - curb), z + top))
        il_t = bm.verts.new((x - rx * (half - curb), y - ry * (half - curb), z + top + 0.12))
        ir_t = bm.verts.new((x + rx * (half - curb), y + ry * (half - curb), z + top + 0.12))
        ol_t = bm.verts.new((x - rx * half, y - ry * half, z + top + 0.12))
        or_t = bm.verts.new((x + rx * half, y + ry * half, z + top + 0.12))
        loops.append((left, right, left_b, right_b, il, ir, il_t, ir_t, ol_t, or_t))
    for a, b in zip(loops, loops[1:]):
        bm.faces.new((a[0], b[0], b[1], a[1]))
        bm.faces.new((a[2], a[3], b[3], b[2]))
        bm.faces.new((a[2], b[2], b[0], a[0]))
        bm.faces.new((a[1], b[1], b[3], a[3]))
        for inner, outer, inner_t, outer_t in ((4, 0, 6, 8), (5, 1, 7, 9)):
            for face in (
                bm.faces.new((a[inner], b[inner], b[inner_t], a[inner_t])),
                bm.faces.new((a[inner_t], b[inner_t], b[outer_t], a[outer_t])),
                bm.faces.new((a[outer_t], b[outer_t], b[outer], a[outer])),
            ):
                face.material_index = 1
    cap0, cap1 = loops[0], loops[-1]
    bm.faces.new((cap0[0], cap0[2], cap0[3], cap0[1]))
    bm.faces.new((cap1[0], cap1[1], cap1[3], cap1[2]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    center = Vector((0.0, 0.0, 0.0))
    for vert in bm.verts:
        center += vert.co
    center /= len(bm.verts)
    for vert in bm.verts:
        vert.co -= center
    me = mesh_from_bm("deck", bm)
    obj = link_obj("deck", me, coll, (mats[surface], mats["concrete"]))
    obj.location = center
    obj.pass_index = INDEX_DECK
    return obj, center


def _bridge(kit, col, cars, mats, rng):
    # The approach (span 4) is the street from the foreground crossroad up to the
    # level deck. Spans 1 and 2 stay hidden until the river span falls.
    # Each span is a ribbon with a vertical cut, so the shared end is one edge.
    segments = {}
    decks = []
    for i, s0, s1 in bridge_spans():
        x0, y0 = deck_point(s0)
        x1, y1 = deck_point(s1)
        z0, z1 = deck_z(s0), deck_z(s1)
        horiz = math.hypot(x1 - x0, y1 - y0)
        pitch = math.atan2(z1 - z0, max(horiz, 0.1))
        length = math.hypot(horiz, z1 - z0)
        obj, center = _deck_ribbon(col, mats, s0, s1, "road" if i in (3, 4) else "deck")
        from mathutils import Vector

        center_v = Vector(center)
        if i in (0, 3):
            rx, ry = right_vector()
            direction = 1.0 if s1 >= s0 else -1.0
            s = s0 + direction * 2.0
            dash_at = 0.0
            while (s1 - s) * direction > 2.2:
                x, y = deck_point(s)
                z = deck_z(s) + RIBBON_TOP + 0.03
                marks = [(sign * 0.12, 0.10, 4.0, mats["yellow"]) for sign in (-1.0, 1.0)]
                if dash_at >= DASH_GAP:
                    for offset in (-LANE_W, LANE_W):
                        marks.append((offset, 0.12, DASH_LEN, mats["mark"]))
                    dash_at = 0.0
                else:
                    dash_at += 4.0
                for offset, width, length_m, mat in marks:
                    mark = box_object("bdash", col, (0, 0, 0), (width, length_m, 0.03), mat)
                    mark.parent = obj
                    mark.matrix_parent_inverse = Matrix.Identity(4)
                    mark.location = Vector((x + rx * offset, y + ry * offset, z)) - center_v
                    mark.rotation_euler = (pitch, 0.0, DECK_ROT_Z)
                    kit.add(mark, "road_mark", sink=False)
                s += direction * 4.0
        item = kit.add(obj, "bridge_deck", i=i, sink=True, length=length)
        cracks = obj.modifiers.new("deck_cracks", "SUBSURF")
        cracks.levels = 1
        cracks.render_levels = 1 if i == 0 else 3
        if i == 0:
            _break_river_span(obj, col, kit, mats)
        decks.append(item)
        segments[i] = obj
    towers = []
    for i, s in enumerate(TOWER_S):
        loc, rot = tower_pose(s)
        pivot = empty(f"tower_{i}", col, loc)
        pivot.rotation_euler[2] = rot
        # Near portal: leg top at z=62 is about 38% of the frame above the deck.
        # The far portal stays shorter so it does not fill the title.
        # 54 m and 46 m above the 4.6 m deck: about 2.7 and 2.3 deck-widths.
        height = 58.6 if i == 0 else 50.6
        _tower_portal(col, mats, pivot, height, TOWER_W, INDEX_PORTAL if i == 0 else 0)
        towers.append(kit.add(pivot, "bridge_tower", i=i, height=height, width=TOWER_W, sink=True))
        # Both portals stand on a pier that rises from the river bed to the deck.
        pier_h = max(2.0, deck_z(s) - WATER_BED_Z)
        pier = box_object(
            "pier",
            col,
            (loc[0], loc[1], WATER_BED_Z + pier_h / 2),
            (7.5, 5.5, pier_h),
            mats["concrete"],
        )
        pier.rotation_euler[2] = rot
        kit.add(pier, "prop", sink=False)
    cyl = cylinder_mesh("cable", radius=1.0, segments=8)
    cables = []
    for side in (-1, 1):
        for _ in range(36):
            obj = link_obj("cable", cyl, col, (mats["bridge"],))
            cables.append(obj)
    suspenders = []
    for _ in range(20):
        obj = link_obj("sus", cyl, col, (mats["cable"],))
        suspenders.append(obj)
    # No cars on the river span. A light body there read as a box on the deck.
    kit.bridge = {
        "decks": decks,
        "towers": towers,
        "cables": cables,
        "suspenders": suspenders,
        "half": DECK_HALF - 0.8,
        "anchors": [
            _deck_edge_s(NEAR_BANK_S - 1.0, -1),
            _deck_edge_s(NEAR_BANK_S - 1.0, 1),
            _deck_edge_s(FAR_BANK_S + 1.0, -1),
            _deck_edge_s(FAR_BANK_S + 1.0, 1),
        ],
    }


def _tower_portal(coll, mats, pivot, height, width, pass_index=0):
    leg_w = TOWER_LEG
    leg_d = leg_w * 1.25

    def tag(obj):
        obj.pass_index = pass_index
        return obj

    def leg(side):
        obj = box_object("leg", coll, (0, 0, 0), (leg_w, leg_d, height), mats["bridge"])
        obj.parent = pivot
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = (side * width / 2, 0, height / 2)
        tag(obj)

    leg(-1)
    leg(1)
    beam_h = max(0.55, height * 0.020)
    # Three cross-beams. The cap is the top of the portal.
    for frac in (0.42, 0.70):
        beam = box_object("beam", coll, (0, 0, 0), (width + leg_w, leg_d * 0.8, beam_h), mats["bridge"])
        beam.parent = pivot
        beam.matrix_parent_inverse = Matrix.Identity(4)
        beam.location = (0, 0, height * frac)
        tag(beam)
    cap = box_object("cap", coll, (0, 0, 0), (width + leg_w, leg_d * 1.15, beam_h * 1.25), mats["bridge"])
    cap.parent = pivot
    cap.matrix_parent_inverse = Matrix.Identity(4)
    cap.location = (0, 0, height + beam_h * 0.15)
    tag(cap)
    saddle = box_object("saddle", coll, (0, 0, 0), (width * 0.62, leg_d * 0.6, beam_h * 0.6), mats["bridge"])
    saddle.parent = pivot
    saddle.matrix_parent_inverse = Matrix.Identity(4)
    saddle.location = (0, 0, height + beam_h * 0.7)
    tag(saddle)


def build_coast(kit, mats, rng, with_city):
    col = kit.collection("Coast")
    col_c = kit.collection("City")
    _plane("seabed", col, (0, 8, -2.55), (70, 40), mats["sand"], 0.2)
    _plane("beach", col, (0, -8, 0.35), (56, 14), mats["sand"])
    _plane("back", col, (0, -16, 0.55), (56, 8), mats["park"])
    for i in range(8):
        rock = ico_object("rock", col, (rng.uniform(-18, 18), rng.uniform(-2, 16), -2.2), rng.uniform(0.4, 1.4), mats["rock"])
        kit.add(rock, "prop", sink=False, float=0.2)
    if with_city:
        colors = [(0.7, 0.78, 0.86, 1), (0.9, 0.9, 0.88, 1), (0.75, 0.5, 0.42, 1)]
        x = -16
        i = 0
        while x < 16:
            h = rng.uniform(6, 22)
            w = rng.uniform(2.4, 4.2)
            obj = link_obj("ctower", _tower_mesh("ct", w, w, h), col_c, (mats["wall"], mats["window"]))
            obj.location = (x, -12.5 - (i % 2), 0.55)
            obj.color = colors[i % 3]
            kit.add(obj, "building_base", sink=False, floodable=True)
            x += w + 0.6
            i += 1
        for i in range(4):
            _house(kit, col_c, mats, -12 + i * 3.2, -6.5, 0.35, 2.0, 1.6, 1.5, i)
    # Ships rest on the seabed; effects lift them with the water.
    for i, x in enumerate((-6, 8)):
        bm = bmesh.new()
        add_box(bm, (0, 0, 0.4), (1.6, 5.5, 0.7), 0)
        add_box(bm, (0, -0.4, 1.15), (1.3, 1.6, 0.8), 0)
        add_box(bm, (0, 1.6, 1.5), (0.35, 0.35, 1.3), 0)
        ship = link_obj("ship", mesh_from_bm("ship", bm), col, (mats["trim"],))
        ship.location = (x, 4 + i * 3, -2.3)
        ship.color = (0.3, 0.35, 0.4, 1)
        kit.add(ship, "ship", sink=False, draft=0.9)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (80, 50, 0.2), 0)
    water = link_obj("sea", mesh_from_bm("sea", bm), col, (mats["water"],))
    water.location = (0, 6, 0.05)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "coast"
    for i in range(6):
        _tree(kit, col, mats, rng.uniform(-14, 14), rng.uniform(-12, -5), 0.4, rng.uniform(0.8, 1.4), rng=rng)


def build_farm(kit, mats, rng):
    col = kit.collection("Farm")
    _plane("field", col, (0, 0, 0), (60, 50), mats["dirt"], 0.1)
    _plane("pasture", col, (-8, -6, 0.02), (24, 18), mats["park"])
    # Crop rows.
    for row in range(8):
        for col_i in range(10):
            x = -6 + col_i * 1.3
            y = 2 + row * 1.5
            crop = box_object("crop", col, (x, y, 0.35), (0.35, 0.35, 0.7), mats["leaf"])
            crop.color = (0.35, 0.62, 0.18, 1)
            kit.add(crop, "crop", delay=row / 20.0, sink=False, leaf=(0.35, 0.62, 0.18, 1), autumn=(0.55, 0.38, 0.12, 1))
    for i in range(10):
        flower = ico_object("flower", col, (rng.uniform(-16, -2), rng.uniform(-12, -2), 0.2), 0.18, mats["leaf"])
        flower.color = [(0.85, 0.3, 0.35, 1), (0.9, 0.8, 0.3, 1), (0.85, 0.55, 0.7, 1)][i % 3]
        kit.add(flower, "flower", sink=False, leaf=tuple(flower.color), autumn=(0.45, 0.32, 0.18, 1))
    for i in range(8):
        _tree(kit, col, mats, rng.uniform(-18, 16), rng.uniform(-16, 14), 0.0, rng.uniform(1.0, 2.0), rng=rng)
    _house(kit, col, mats, -14, 8, 0, 3.2, 2.4, 2.2, 0)
    # Birds and a couple of animals.
    for i in range(6):
        bird = ico_object("bird", col, (rng.uniform(-8, 8), rng.uniform(-4, 6), 2.5 + i * 0.2), (0.28, 0.1, 0.08), mats["trim"])
        kit.add(bird, "bird", phase=i, sink=False, float=2.2, bob=0.4)
    deer = box_object("deer", col, (4, -8, 0.55), (0.4, 0.9, 0.7), mats["wood"])
    deer.color = (0.45, 0.30, 0.16, 1)
    kit.add(deer, "animal", sink=False)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (30, 8, 0.2), 0)
    water = link_obj("pond", mesh_from_bm("pond", bm), col, (mats["water"],))
    water.location = (10, 6, 0.02)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "farm"


def build_strata(kit, mats):
    col = kit.collection("Geology")
    pivot = empty("strata", col, (10.0, 320.0, 0.0))
    layers = [
        (0.0, 1.4, lin(0.42, 0.30, 0.20), "rock"),
        (1.4, 1.3, lin(0.55, 0.52, 0.48), "rock"),
        (2.7, 1.2, lin(0.70, 0.60, 0.42), "rock"),
        (3.9, 0.16, lin(0.90, 0.24, 0.06), "seam"),
        (4.06, 1.3, lin(0.62, 0.58, 0.52), "rock"),
        (5.36, 1.15, lin(0.48, 0.42, 0.36), "rock"),
        (6.51, 0.7, lin(0.36, 0.30, 0.20), "dirt"),
    ]
    for i, (z0, h, _color, mat_name) in enumerate(layers):
        # Fixed materials already carry color; seam uses emission.
        mat = mats["seam"] if mat_name == "seam" else mats[mat_name]
        block = box_object("layer", col, (0, 0, 0), (58, 3.2, h), mat)
        block.parent = pivot
        block.matrix_parent_inverse = Matrix.Identity(4)
        block.location = (0, 0, z0 + h / 2)
    for i in range(11):
        tree = ico_object("stree", col, (0, 0, 0), (0.7, 0.6, 0.9), mats["leaf"])
        tree.parent = pivot
        tree.matrix_parent_inverse = Matrix.Identity(4)
        tree.location = (-20 + i * 4.0, -1.3, 7.5)
        tree.color = (0.30, 0.5, 0.18, 1)
    kit.add(pivot, "strata", sink=False)
    # Glacier in the river, hidden until the ice age.
    glacier = ico_object("glacier", kit.collection("Weather"), (20.0, 190.0, 1.0), (18.0, 10.0, 4.0), mats["snow"])
    kit.add(glacier, "glacier", sink=False)


def build_precip(kit, mats, features):
    col = kit.collection("Weather")
    if features.get("rain"):
        for i in range(80):
            drop = box_object("rain", col, (0, 0, 0), (0.03, 0.03, 0.55), mats["mark"])
            kit.precip.append(("rain", drop, i))
            drop.hide_render = True
    if features.get("snow") or features.get("ice"):
        for i in range(70):
            flake = ico_object("flake", col, (0, 0, 0), 0.08, mats["snow"])
            kit.precip.append(("snow", flake, i))
            flake.hide_render = True
    if features.get("dust") or features.get("heat"):
        for i in range(50):
            mote = ico_object("dust", col, (0, 0, 0), 0.07, mats["sand"])
            kit.precip.append(("dust", mote, i))
            mote.hide_render = True
    if features.get("ash") or features.get("fire"):
        for i in range(40):
            ash = ico_object("ash", col, (0, 0, 0), 0.06, mats["trim"])
            kit.precip.append(("ash", ash, i))
            ash.hide_render = True


def build_fx_meshes(kit, mats, features):
    col = kit.collection("Weather")
    if features.get("fire") or features.get("heat"):
        for i in range(5):
            flame = ico_object("flame", col, (-8 + i * 4, 10, FAR_Z + 1.2), (0.4, 0.4, 1.1), mats["flame"])
            kit.add(flame, "flame", index=i, sink=True)
            flame.hide_render = True
        for i in range(6):
            crack = box_object("crack", col, (-10 + i * 3.5, -8, PARK_Z + 0.03), (0.08, 2.4, 0.02), mats["dark"])
            kit.add(crack, "crack", index=i, sink=False)
            crack.hide_render = True
    # Snow mounds that bury cars. Always available; hidden until snow.
    for i in range(8):
        mound = ico_object("mound", col, (0, 0, 0), 1.0, mats["snow"])
        kit.add(mound, "mound", index=i, sink=False)
        mound.hide_render = True


def build_mauna_kea(kit, mats, rng):
    """Hawaii island and Mauna Kea. Ocean drains by lowering the water plane."""
    col = kit.collection("Coast")
    _plane("shelf", col, (0, 6, -3.2), (80, 50), mats["sand"], 0.2)
    _plane("shore", col, (0, -6, 0.15), (40, 10), mats["sand"])
    # Volcano as stacked rings, wide at the base.
    for i, (z, rad, h) in enumerate(((0.2, 16, 3.2), (3.2, 11, 3.0), (6.0, 7, 2.6), (8.4, 4.2, 2.2), (10.2, 2.2, 1.4))):
        obj = box_object("cone", col, (0, 2, z + h / 2), (rad * 2, rad * 1.4, h), mats["rock"])
        kit.add(obj, "building_base", sink=False, erode=True)
    for i, dx in enumerate((-1.2, 0.4, 1.5)):
        dome = ico_object("dome", col, (dx, 2.2, 11.8), 0.55, mats["trim"])
        kit.add(dome, "prop", sink=False)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (90, 60, 0.2), 0)
    water = link_obj("pacific", mesh_from_bm("pacific", bm), col, (mats["water"],))
    water.location = (0, 8, 0.02)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "coast"


def build_ny_harbor(kit, mats, rng):
    """Harbor water, a low skyline, and a simplified Statue of Liberty."""
    col = kit.collection("Harbor")
    col_c = kit.collection("City")
    _plane("island", col, (-6, -2, 0.35), (10, 8), mats["park"])
    _plane("manhattan", col, (8, 14, 0.4), (28, 10), mats["trim"])
    x = -2
    for i in range(7):
        h = 8 + (i * 3) % 14
        w = 2.4
        obj = link_obj("ny", _tower_mesh("ny", w, w, h), col_c, (mats["wall"], mats["window"]))
        obj.location = (x, 14, 0.4)
        obj.color = (0.75, 0.78, 0.82, 1)
        kit.add(obj, "building_base", sink=False)
        x += w + 0.7
    # Statue: pedestal, robe, head, crown, tablet. Copper green.
    green = (0.22, 0.55, 0.34, 1)
    ped = box_object("pedestal", col, (-6, -2, 1.6), (2.2, 2.2, 2.4), mats["trim"])
    robe = box_object("robe", col, (-6, -2, 4.3), (1.3, 1.1, 3.0), mats["car"])
    robe.color = green
    head = ico_object("head", col, (-6, -2.1, 6.2), 0.55, mats["car"])
    head.color = green
    for i in range(7):
        ang = i / 7 * 6.28
        spike = box_object("spike", col, (-6 + math.cos(ang) * 0.35, -2.1 + math.sin(ang) * 0.35, 6.9), (0.08, 0.08, 0.7), mats["car"])
        spike.color = green
    tablet = box_object("tablet", col, (-4.7, -2, 4.6), (0.7, 0.15, 1.1), mats["car"])
    tablet.color = green
    for obj in (ped, robe, head, tablet):
        kit.add(obj, "prop", sink=False)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (80, 40, 0.2), 0)
    water = link_obj("harbor", mesh_from_bm("harbor", bm), col, (mats["water"],))
    water.location = (2, 2, 0.05)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "coast"


def build_culdesac(kit, mats, rng):
    """US suburban loop. The snow episode's locked camera lives here."""
    col = kit.collection("Suburb")
    _plane("yards", col, (0, 0, 0.0), (46, 40), mats["park"])
    _plane("asphalt", col, (0, 0, 0.05), (18, 16), mats["road"])
    _plane("green", col, (0, 0, 0.08), (8, 6), mats["park"])
    spots = [(-8, -6), (-8, 0), (-8, 6), (8, -6), (8, 0), (8, 6), (-3, 8), (3, 8)]
    for i, (x, y) in enumerate(spots):
        _house(kit, col, mats, x, y, 0.08, 2.4, 2.0, 1.8, i)
        _tree(kit, col, mats, x + (1.6 if x < 0 else -1.6), y + 1.2, 0.08, 1.1, rng=rng)
    for i, x in enumerate((-2.2, 2.2)):
        _car(kit, col, mats, (x, -1.5, 0.1), 0.0, (0.9, 0.9, 0.92, 1) if i == 0 else (0.15, 0.2, 0.45, 1), drive=0.0)
    box_object("tower", col, (0, 0, 3.2), (0.8, 0.8, 6.2), mats["trim"])
    kit.kind = "suburb"
    kit.water = None


def build_desert(kit, mats, rng):
    """Red-rock basin. Rain fills the wash, then plants take the stone."""
    col = kit.collection("Desert")
    _plane("basin", col, (0, 2, 0.0), (55, 48), mats["sand"])
    for i, (x, y, w, h) in enumerate(((-8, 6, 4, 7), (6, 8, 3, 5), (0, 14, 6, 4), (10, 2, 2.5, 6))):
        butte = box_object("butte", col, (x, y, h / 2), (w, w * 0.7, h), mats["rock"])
        kit.add(butte, "building_base", sink=False)
    if "forest" in (kit.extra_pieces if hasattr(kit, "extra_pieces") else []):
        pass
    for i in range(16):
        fern = ico_object("fern", col, (rng.uniform(-12, 12), rng.uniform(-6, 12), 0.4), rng.uniform(0.4, 1.3), mats["leaf"])
        fern.color = (0.28, 0.5, 0.2, 1)
        kit.add(fern, "weed", delay=rng.uniform(0.2, 0.8), sink=False, leaf=(0.28, 0.5, 0.2, 1), autumn=(0.45, 0.32, 0.14, 1))
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.08), (30, 14, 0.16), 0)
    water = link_obj("wash", mesh_from_bm("wash", bm), col, (mats["water"],))
    water.location = (0, 2, -2.2)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "desert"


def add_mascot(kit, mats, loc):
    """Small figure with a red sign. Off to the side, so the shot still reads."""
    col = kit.collection("Mascot")
    x, y, z = loc
    body = box_object("mascot", col, (x, y, z + 0.42), (0.26, 0.16, 0.5), mats["car"])
    body.color = (0.12, 0.28, 0.62, 1)
    head = ico_object("mascot_head", col, (x, y - 0.02, z + 0.78), 0.14, mats["car"])
    head.color = (0.93, 0.78, 0.62, 1)
    sign = box_object("mascot_sign", col, (x + 0.32, y, z + 0.62), (0.34, 0.04, 0.26), mats["bridge"])
    kit.add(body, "mascot", sink=False, throw=6.0, index=1)
    kit.add(head, "mascot", sink=False, throw=6.2, index=2)
    kit.add(sign, "mascot", sink=False, throw=7.0, index=3)


def build_nyc_avenue(kit, mats, rng):
    """Bright flat avenue. The reusable format-C street."""
    col = kit.collection("Avenue")
    _plane("street", col, (0, 8, 0.0), (14, 70), mats["road"])
    _plane("walk_l", col, (-8.2, 8, 0.08), (3.2, 70), mats["trim"])
    _plane("walk_r", col, (8.2, 8, 0.08), (3.2, 70), mats["trim"])
    colors = [(0.86, 0.88, 0.9, 1), (0.95, 0.78, 0.7, 1), (0.7, 0.78, 0.86, 1), (0.92, 0.9, 0.82, 1)]
    for side in (-1, 1):
        y = -4
        i = 0
        while y < 40:
            w = rng.uniform(3.2, 5.0)
            h = rng.uniform(10, 28)
            obj = link_obj("ave", _tower_mesh("ave", w, w * 0.8, h), col, (mats["wall"], mats["window"]))
            obj.location = (side * (9.5 + w * 0.3), y, 0.08)
            obj.color = colors[i % len(colors)]
            kit.add(obj, "building_base", sink=False)
            if h > 16:
                top = link_obj("avetop", _tower_mesh("avetop", w * 0.9, w * 0.7, h * 0.35), col, (mats["wall"], mats["window"]))
                top.location = (side * (9.5 + w * 0.3), y, 0.08 + h * 0.65)
                top.color = obj.color
                kit.add(top, "building_top", sink=False, fall_at=0.4, top_h=h * 0.35, index=i)
            y += w + 0.8
            i += 1
    for i, y in enumerate((-2, 4, 12, 22)):
        _car(kit, col, mats, (-1.6 if i % 2 == 0 else 1.6, y, 0.05), 0.0, (0.9, 0.9, 0.92, 1), drive=0.0)
    kit.kind = "nyc"
    kit.water = None


def build_rio_beach(kit, mats, rng):
    """Beach, a low skyline, and an ocean that can pull back."""
    col = kit.collection("Beach")
    _plane("sand", col, (0, -2, 0.05), (40, 18), mats["sand"])
    _plane("cityground", col, (0, 12, 0.2), (36, 14), mats["trim"])
    for i, x in enumerate(range(-12, 14, 4)):
        h = 6 + (i % 4) * 3
        obj = link_obj("rio", _tower_mesh("rio", 3.2, 3.0, h), col, (mats["wall"], mats["window"]))
        obj.location = (x, 12, 0.2)
        obj.color = (0.95, 0.9, 0.8, 1)
        kit.add(obj, "building_base", sink=False)
        _tree(kit, col, mats, x + 1.4, 4, 0.05, 1.0, rng=rng)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (50, 24, 0.2), 0)
    water = link_obj("atlantic", mesh_from_bm("atlantic", bm), col, (mats["water"],))
    water.location = (0, -12, 0.02)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "rio"


def build_kitchen(kit, mats, rng):
    """A counter and a burger. Mold is vegetation; drying is wilt and heat."""
    col = kit.collection("Kitchen")
    _plane("counter", col, (0, 0, 0.9), (8, 5), mats["trim"], 0.12)
    _plane("back", col, (0, 2.2, 1.8), (8, 0.2), mats["wall"] if False else mats["trim"], 1.6)
    # Burger stack, each layer its own object so it can sag.
    layers = [
        ("bun_bottom", 0.08, (0.72, 0.55, 0.28)),
        ("patty", 0.07, (0.28, 0.14, 0.08)),
        ("cheese", 0.025, (0.9, 0.72, 0.15)),
        ("lettuce", 0.04, (0.3, 0.62, 0.18)),
        ("bun_top", 0.09, (0.82, 0.6, 0.32)),
    ]
    for side, x0 in (("fast", -0.95), ("home", 0.95)):
        z = 0.98
        for i, (name, h, color) in enumerate(layers):
            obj = box_object(f"{side}_{name}", col, (x0, 0, z + h / 2), (1.15 - i * 0.04, 1.15 - i * 0.04, h), mats["car"])
            obj.color = (*color, 1)
            kit.add(obj, "food", index=i, sink=False)
            z += h
    for i in range(8):
        mold = ico_object("mold", col, (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1.35), 0.12, mats["leaf"])
        mold.color = (0.25, 0.45, 0.18, 1)
        kit.add(mold, "weed", delay=0.15 + i * 0.08, sink=False, leaf=(0.25, 0.45, 0.18, 1), autumn=(0.35, 0.28, 0.12, 1))
    kit.kind = "kitchen"
    kit.water = None


def build_scene(scene, spec, features):
    rng = random.Random(int((spec.get("scene") or {}).get("seed") or 1))
    pieces = set((spec.get("scene") or {}).get("pieces") or ["city", "river", "bridge"])
    kit = Kit(scene)
    mats = _materials()
    kit.mats = mats
    kit.format = spec.get("format") or "A"
    name = (spec.get("scene") or {}).get("name") or ""
    if name == "mauna_kea":
        build_mauna_kea(kit, mats, rng)
    elif name == "ny_harbor":
        build_ny_harbor(kit, mats, rng)
    elif name == "kitchen":
        build_kitchen(kit, mats, rng)
    elif name == "culdesac":
        build_culdesac(kit, mats, rng)
    elif name == "desert":
        build_desert(kit, mats, rng)
    elif name == "nyc_avenue":
        build_nyc_avenue(kit, mats, rng)
    elif name == "rio_beach":
        build_rio_beach(kit, mats, rng)
    elif name == "city_park":
        raise RuntimeError("city_park is on the roadmap (picnic set and cat rig) and is not built")
    elif name == "ready_city":
        from engine.ready_city import build as build_ready_city

        build_ready_city(kit, mats, rng)
    elif "coast" in pieces:
        build_coast(kit, mats, rng, with_city="city" in pieces)
        if "suburbs" in pieces and "city" not in pieces:
            for i in range(5):
                _house(kit, kit.collection("City"), mats, -8 + i * 3, -6, 0.35, 2.1, 1.7, 1.6, i)
    elif "farm" in pieces or ("forest" in pieces and "city" not in pieces):
        build_farm(kit, mats, rng)
    else:
        build_river_city(kit, mats, rng, pieces)
    if not name and ("city" in pieces or "coast" in pieces or kit.kind == "city"):
        build_strata(kit, mats)
    build_precip(kit, mats, features)
    build_fx_meshes(kit, mats, features)
    # Volume for ice fog, dust, ash, rain haze.
    vol_me_bm = bmesh.new()
    add_box(vol_me_bm, (0, 0, 0), (420, 560, 120), 0)
    vol = link_obj("fog", mesh_from_bm("fog", vol_me_bm), kit.collection("Weather"), (make_volume(),))
    vol.location = (10, 160, 40)
    vol.hide_render = True
    kit.volume = vol
    if kit.format == "C":
        from engine.format_c import build_wave

        build_wave(kit, mats)
    if spec.get("mascot", True):
        corners = {
            "city": (-48.0, 42.0, 0.7),
            "suburb": (13.0, 8.5, 0.1),
            "desert": (14.0, -3.0, 0.05),
            "coast": (12.0, -7.0, 0.3),
            "kitchen": (2.3, 0.6, 0.96),
            "nyc": (4.2, -8.0, 0.02),
            "rio": (-10.0, 1.5, 0.08),
        }
        add_mascot(kit, mats, corners.get(kit.kind, (6.0, -6.0, 0.1)))
    _lights(kit)
    return kit


def _lights(kit):
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 1.8
    sun_data.angle = 0.36
    sun_data.color = (0.92, 0.95, 1.0)
    sun = bpy.data.objects.new("Sun", sun_data)
    kit.collection("Lights").objects.link(sun)
    sun.rotation_euler = (1.05, 0.08, -0.85)
    kit.sun = sun
    fill_data = bpy.data.lights.new("Fill", "SUN")
    fill_data.energy = 0.12
    fill_data.angle = 1.1
    fill_data.color = (0.75, 0.84, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    kit.collection("Lights").objects.link(fill)
    fill.rotation_euler = (1.2, -0.4, 2.2)
    kit.fill = fill
    world = bpy.data.worlds.new("Sky")
    kit.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    gradient = nt.nodes.new("ShaderNodeMixRGB")
    gradient.name = "SkyGradient"
    zenith = nt.nodes.new("ShaderNodeRGB")
    horizon = nt.nodes.new("ShaderNodeRGB")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeMapRange")
    # Warm horizon under a clear blue zenith. The camera sees this gradient.
    zenith.outputs[0].default_value = lin(0.22, 0.42, 0.78)
    horizon.outputs[0].default_value = lin(0.98, 0.72, 0.46)
    ramp.inputs["From Min"].default_value = -0.05
    ramp.inputs["From Max"].default_value = 0.45
    ramp.inputs["To Min"].default_value = 1.0
    ramp.inputs["To Max"].default_value = 0.0
    ramp.clamp = True
    nt.links.new(geo.outputs["Incoming"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], gradient.inputs["Fac"])
    nt.links.new(horizon.outputs["Color"], gradient.inputs["Color1"])
    nt.links.new(zenith.outputs["Color"], gradient.inputs["Color2"])
    sky_mix = nt.nodes.new("ShaderNodeMixRGB")
    sky_mix.name = "SkyMix"
    # 0 keeps the HDRI for lighting. 1 is the night gradient.
    sky_mix.inputs["Fac"].default_value = 0.0
    alps = Path("/opt/cursor/asset-cache/private/mountains/alps_field_4k.hdr")
    hdri_path = alps if alps.exists() else (
        found_assets.clear_sky() or cc0_city.sunny_hdri() or (
            Path(__file__).resolve().parents[1] / "assets" / "cc0" / "hdri" / "kloofendal_48d_partly_cloudy_1k.hdr"
        )
    )
    if hdri_path.exists():
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(hdri_path), check_existing=True)
        env.image.colorspace_settings.name = "Linear Rec.709"
        mapping = nt.nodes.new("ShaderNodeMapping")
        texcoord = nt.nodes.new("ShaderNodeTexCoord")
        mapping.inputs["Rotation"].default_value = (0.0, 0.0, 1.15)
        nt.links.new(texcoord.outputs["Reflection"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], sky_mix.inputs["Color1"])
    else:
        flat = nt.nodes.new("ShaderNodeRGB")
        flat.outputs[0].default_value = lin(0.48, 0.58, 0.68)
        nt.links.new(flat.outputs["Color"], sky_mix.inputs["Color1"])
    nt.links.new(gradient.outputs["Color"], sky_mix.inputs["Color2"])
    # The camera sees the flat zenith blue. Reflections and diffuse rays see the HDRI.
    camera = nt.nodes.new("ShaderNodeLightPath")
    shown = nt.nodes.new("ShaderNodeMixRGB")
    shown.name = "SkyShown"
    # Daytime the camera sees the HDRI (sky_mix fac 0). Night raises the fac
    # and both rays see the gradient. A flat dim gradient here made the
    # opening gloomy even when the HDRI was lighting the ground.
    # Bounces keep the HDRI so the sun still lights the street. The camera sees the gradient.
    nt.links.new(camera.outputs["Is Camera Ray"], shown.inputs["Fac"])
    nt.links.new(sky_mix.outputs["Color"], shown.inputs["Color1"])
    nt.links.new(gradient.outputs["Color"], shown.inputs["Color2"])
    nt.links.new(shown.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs[1].default_value = 0.85
    kit.world_bg = bg
    kit.sky_zenith = zenith
    kit.sky_horizon = horizon
    kit.sky_mix = sky_mix
