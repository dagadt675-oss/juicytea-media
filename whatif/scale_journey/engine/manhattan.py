"""Midtown around the Empire State, tiled from hub scenes.

Hub entries used
- sketchfab_free_standard_procedural_city_6 / _3 / _4: the blocks themselves
- sketchfab_free_standard_one_world_trade_center: downtown skyline, 5.5 km SSW
- sketchfab_free_standard_city_commute_transport_pack: sidewalk bikes and scooters
- sketchfab_free_standard_city_props_vol1: hydrants, lamps, benches, trash, a bus stop
- simple_crosswalk: one zebra per corner of the tower streets
- CC0 Kenney roads, taxis, and sedans already in the hub library
- rigged walk cycles from the hub animation pack

Checked and left out
- sketchfab_free_standard_ruined_city_free_5: abandoned towers and wrecks, wrong for a lived-in Midtown afternoon
- sketchfab_free_standard_airport_city_scene: optional, and it carries a Malaysia Airlines livery
- sketchfab_free_standard_vehicle_mini_pack: armored cars and pickups, not yellow cabs
- realistic_road: curved highway pieces, not a straight Manhattan avenue

The only original surfaces are the crack-fill ground under the tiles and the
tower plaza streets. No hub scene is a horizon-sized ground, and dropping a
whole city block onto the scan would bury the Empire State mesh.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
import mathutils

from engine.landmarks import ESB_LOT, MAN, road_rects

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "library" / "extracted"
PRIVATE = ROOT / "cache" / "private"
HUB = PRIVATE / "hub"
PEOPLE = PRIVATE / "city_people"
PROPS = PEOPLE / "sketchfab_free_standard" / "city_props_vol1" / "city_props_vol1.glb"
CROSSWALK = PEOPLE / "sketchfab" / "simple_crosswalk" / "simple_crosswalk.glb"
IDLE = (
    PEOPLE
    / "animations"
    / "sketchfab_free_standard"
    / "Idle_1_Male_Free_Animation_200_frames_loop_4add87eb"
    / "Idle_1_Male_Free_Animation_200_frames_loop_4add87eb.glb"
)
WALKS = (
    PEOPLE / "animations" / "sketchfab_free_standard" / "Male_Basic_Walk_30_frames_loop_2e17b141" / "Male_Basic_Walk_30_frames_loop_2e17b141.glb",
    PEOPLE / "animations" / "sketchfab_free_standard" / "Basic_Walk_Free_Animation_30_frames_loop_7355f061" / "Basic_Walk_Free_Animation_30_frames_loop_7355f061.glb",
    PEOPLE / "animations" / "sketchfab_free_standard" / "Male_Phone_Walking_40_frames_loop_b2938151" / "Male_Phone_Walking_40_frames_loop_b2938151.glb",
)
ROADS = CACHE / "assets_cc0_roads_props" / "roads_props" / "kenney_city_kit_roads" / "Models" / "GLB format"
CARS = CACHE / "assets_cc0_vehicles" / "vehicles" / "kenney_car_kit" / "Models" / "GLB format"

CELL = 200.0
REACH = 1000.0
# Open plaza the scan occupies. City blocks tile outside it.
PLAZA = (-78.0, 64.0, -44.0, 50.0)
# One WTC is about 5.5 km south-southwest of the Empire State.
WTC_TIP_M = 541.3
WTC_AT = (-2105.0, -5081.0)

MOVERS: list[tuple] = []


def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _imported(path: Path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


def _drop_helpers(objs):
    kept = []
    for obj in objs:
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        kept.append(obj)
    return kept


def _bounds(objs):
    mn = mathutils.Vector((1e9, 1e9, 1e9))
    mx = mathutils.Vector((-1e9, -1e9, -1e9))
    for obj in objs:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            mn = mathutils.Vector((min(mn.x, world.x), min(mn.y, world.y), min(mn.z, world.z)))
            mx = mathutils.Vector((max(mx.x, world.x), max(mx.y, world.y), max(mx.z, world.z)))
    return mn, mx


def _pack(name, obj):
    col = bpy.data.collections.new(name)
    for holder in list(obj.users_collection):
        holder.objects.unlink(obj)
    col.objects.link(obj)
    return col


def _instance(col, location, yaw=0.0, mirror=1.0):
    empty = bpy.data.objects.new(col.name + "_i", None)
    empty.instance_type = "COLLECTION"
    empty.instance_collection = col
    empty.location = location
    empty.rotation_euler = (0.0, 0.0, yaw)
    empty.scale = (mirror, 1.0, 1.0)
    return _link(empty)


def _clear_parent(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if obj.parent is not None:
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def _join_meshes(meshes):
    # Clear parents first. _clear_parent deselects, so the join selection
    # has to happen after every mesh has been baked.
    for obj in meshes:
        _clear_parent(obj)
    bpy.ops.object.select_all(action="DESELECT")
    alive = [obj for obj in meshes if obj.name in bpy.data.objects]
    for obj in alive:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = alive[0]
    if len(alive) > 1:
        bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    print(f"JOIN {joined.name} faces {len(joined.data.polygons)}", flush=True)
    return joined


def _center_on_ground(obj):
    """Footprint centered on the origin, base on z=0. Returns the unscaled size."""
    bpy.context.view_layer.update()
    mn, mx = _bounds([obj])
    span = (max(0.01, mx.x - mn.x), max(0.01, mx.y - mn.y), max(0.01, mx.z - mn.z))
    obj.location = (-(mn.x + mx.x) * 0.5, -(mn.y + mx.y) * 0.5, -mn.z)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return span


def _apply_scale(obj, scale):
    obj.scale = scale
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def _decimate(obj, ratio, name):
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = name
    _link(copy)
    mod = copy.modifiers.new("Far", "DECIMATE")
    mod.ratio = ratio
    bpy.context.view_layer.objects.active = copy
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"LOD {name} faces {len(copy.data.polygons)}", flush=True)
    return copy


def _block(path: Path, name: str, hero: bool = False):
    if not path.exists():
        print(f"MISSING BLOCK {path}", flush=True)
        return None
    print(f"LOAD {path.name}", flush=True)
    objs = _drop_helpers(_imported(path))
    meshes = [obj for obj in objs if obj.type == "MESH" and len(obj.data.polygons) > 0]
    if not meshes:
        return None
    joined = _join_meshes(meshes)
    span = _center_on_ground(joined)
    hero_pack = None
    if hero:
        # Keep a true-proportion copy for the sidewalk the penny lands on.
        # Height about 28 m, an 8-story brick canyon, not stretched to the cell.
        hero_obj = joined.copy()
        hero_obj.data = joined.data.copy()
        hero_obj.name = name + "Hero"
        _link(hero_obj)
        uniform = min(28.0 / span[2], 110.0 / max(span[0], span[1]))
        _apply_scale(hero_obj, (uniform, uniform, uniform))
        bpy.context.view_layer.update()
        hmn, hmx = _bounds([hero_obj])
        hero_pack = (_pack(name + "Hero", hero_obj), (hmx.x - hmn.x, hmx.y - hmn.y, hmx.z - hmn.z))
        print(f"HERO {name} {hero_pack[1][0]:.0f}x{hero_pack[1][1]:.0f}x{hero_pack[1][2]:.0f}", flush=True)
    _apply_scale(joined, (CELL / span[0], CELL / span[1], ((CELL / span[0]) + (CELL / span[1])) * 0.5))
    print(f"BLOCK {joined.name} was {span[0]:.0f}x{span[1]:.0f}x{span[2]:.0f} m", flush=True)
    far = _decimate(joined, 0.07, name + "Far")
    return _pack(name, joined), _pack(name + "Far", far), hero_pack


# Brick canyon pulled up to the landing sidewalk. Filled when that block is placed.
HERO_KEEP: list[tuple[float, float, float, float]] = []


def _box_hits(x0, x1, y0, y1, box):
    return x0 < box[1] and x1 > box[0] and y0 < box[3] and y1 > box[2]


def _overlaps_plaza(cx, cy):
    x0, x1 = cx - CELL * 0.5, cx + CELL * 0.5
    y0, y1 = cy - CELL * 0.5, cy + CELL * 0.5
    if _box_hits(x0, x1, y0, y1, PLAZA):
        return True
    return any(_box_hits(x0, x1, y0, y1, box) for box in HERO_KEEP)


def _tile(blocks):
    n = int(REACH // CELL)
    placed = 0
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            cx, cy = i * CELL, j * CELL
            if _overlaps_plaza(cx, cy):
                continue
            near, far, _hero = blocks[(i * 3 + j * 5) % len(blocks)]
            dist = math.hypot(cx, cy)
            col = near if dist < 320.0 else far
            yaw = ((i * 2 + j) % 4) * (math.pi / 2.0)
            mirror = -1.0 if (i + j) % 2 == 0 else 1.0
            _instance(col, (cx, cy, 0.0), yaw, mirror)
            placed += 1
    print(f"CITY tiles {placed}", flush=True)


def _ground():
    mat = bpy.data.materials.new("Underlay")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.08, 0.08, 0.085, 1)
    bsdf.inputs["Roughness"].default_value = 0.95
    bpy.ops.mesh.primitive_plane_add(size=16000, location=(0.0, -400.0, -0.08))
    obj = bpy.context.object
    obj.name = "Underlay"
    obj.data.materials.append(mat)


def _fit_height(empty, meshes, height):
    bpy.context.view_layer.update()
    mn, mx = _bounds(meshes)
    span = max(0.01, mx.z - mn.z)
    empty.scale = (height / span,) * 3
    bpy.context.view_layer.update()
    mn, _mx = _bounds(meshes)
    empty.location.z -= mn.z


def _wtc():
    path = HUB / "one_wtc.glb"
    if not path.exists():
        print("WTC missing", flush=True)
        return
    objs = _drop_helpers(_imported(path))
    meshes = [obj for obj in objs if obj.type == "MESH" and len(obj.data.polygons) > 20]
    empty = _link(bpy.data.objects.new("OneWTC", None))
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    for obj in roots:
        if obj.type == "CAMERA":
            continue
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.matrix_world = world
    _fit_height(empty, meshes, WTC_TIP_M)
    empty.location.x = WTC_AT[0]
    empty.location.y = WTC_AT[1]
    bpy.context.view_layer.update()
    print(f"WTC at {tuple(round(v, 1) for v in empty.location)} tip {WTC_TIP_M}", flush=True)


def _clusters(meshes):
    """Split the commute pack into the separate vehicles sitting side by side."""
    groups = {0: [], 1: [], 2: [], 3: []}
    for obj in meshes:
        center = sum((obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box), mathutils.Vector()) / 8.0
        if center.x < -1.2:
            groups[0].append(obj)
        elif center.x < 0.0:
            groups[1].append(obj)
        elif center.x < 0.9:
            groups[2].append(obj)
        else:
            groups[3].append(obj)
    packed = []
    for index, members in groups.items():
        members = [obj for obj in members if len(obj.data.polygons) > 20]
        if len(members) < 2:
            continue
        for obj in members:
            _clear_parent(obj)
        bpy.context.view_layer.update()
        mn, mx = _bounds(members)
        shift = mathutils.Vector(((mn.x + mx.x) * 0.5, (mn.y + mx.y) * 0.5, mn.z))
        empty = _link(bpy.data.objects.new(f"Commute{index}", None))
        for obj in members:
            obj.matrix_world.translation -= shift
            world = obj.matrix_world.copy()
            obj.parent = empty
            obj.matrix_world = world
        packed.append(empty)
    return packed


def _commute():
    path = HUB / "city_commute_transport_pack.glb"
    if not path.exists():
        print("COMMUTE missing", flush=True)
        return
    objs = _drop_helpers(_imported(path))
    meshes = [obj for obj in objs if obj.type == "MESH"]
    protos = _clusters(meshes)
    if not protos:
        return
    spots = []
    for i, x in enumerate(range(-40, 220, 28)):
        spots.append((x, 43.5 if i % 2 == 0 else 47.2, 0.4 if i % 2 else -0.6))
        spots.append((x + 6.0, 36.2, 1.2))
    for index, (x, y, yaw) in enumerate(spots):
        proto = protos[index % len(protos)]
        bpy.ops.object.select_all(action="DESELECT")

        def select(obj):
            obj.select_set(True)
            for child in obj.children:
                select(child)

        select(proto)
        bpy.context.view_layer.objects.active = proto
        bpy.ops.object.duplicate(linked=True)
        copy = bpy.context.view_layer.objects.active
        copy.location = (x, y, 0.0)
        copy.rotation_euler = (0.0, 0.0, yaw)
    print(f"COMMUTE {len(spots)}", flush=True)


def _props():
    if not PROPS.exists():
        return
    objs = _drop_helpers(_imported(PROPS))
    want = ("FireHydrant", "TrashCanSmall", "ParkBenchShort", "Light_", "BusStop_Structure", "ParkingMeter")
    chosen = []
    for needle in want:
        for obj in objs:
            if obj.type == "MESH" and needle in obj.name and obj not in chosen:
                chosen.append(obj)
                break
    if not chosen:
        return
    for obj in chosen:
        mn, _mx = _bounds([obj])
        obj.location.z -= mn.z
    spots = []
    for i, x in enumerate(range(-60, 240, 34)):
        spots.append((x, 37.4, chosen[i % len(chosen)], 0.2))
        spots.append((x + 12.0, 57.5, chosen[(i + 1) % len(chosen)], 3.1))
    # Landing sidewalk: hydrant, lamps, and a bench in front of the storefronts.
    spots.extend(
        (
            (MAN[0] + 1.15, MAN[1] - 0.35, chosen[0], 0.4),
            (MAN[0] - 2.2, MAN[1] + 0.2, chosen[3] if len(chosen) > 3 else chosen[0], 0.1),
            (MAN[0] + 2.4, MAN[1] + 0.35, chosen[3] if len(chosen) > 3 else chosen[0], 3.1),
        )
    )
    for x, y, proto, yaw in spots:
        bpy.ops.object.select_all(action="DESELECT")
        proto.select_set(True)
        bpy.context.view_layer.objects.active = proto
        bpy.ops.object.duplicate(linked=True)
        copy = bpy.context.view_layer.objects.active
        copy.location = (x, y, proto.location.z)
        copy.rotation_euler = (0.0, 0.0, yaw)
        if "BusStop" in proto.name or "Light_" in proto.name:
            copy.scale = (1.0, 1.0, 1.0)


def _crosswalks():
    if not CROSSWALK.exists():
        return
    objs = _drop_helpers(_imported(CROSSWALK))
    meshes = [obj for obj in objs if obj.type == "MESH"]
    if not meshes:
        return
    empty = _link(bpy.data.objects.new("Zebra", None))
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.matrix_world = world
    bpy.context.view_layer.update()
    mn, mx = _bounds(meshes)
    span = max(0.01, mx.x - mn.x)
    empty.scale = (26.0 / span, 8.0 / span, 1.0)
    empty.location = (0.0, 0.0, -800.0)
    for x, y, yaw in ((-20.0, 46.0, 0.0), (40.0, 46.0, 0.0), (68.0, 10.0, 1.5708), (68.0, -20.0, 1.5708)):
        bpy.ops.object.select_all(action="DESELECT")
        empty.select_set(True)
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = empty
        bpy.ops.object.duplicate(linked=True)
        copy = bpy.context.view_layer.objects.active
        copy.location = (x, y, 0.05)
        copy.rotation_euler = (0.0, 0.0, yaw)


def _roads_and_cars():
    road = ROADS / "road-straight.glb"
    if road.exists():
        objs = _drop_helpers(_imported(road))
        meshes = [obj for obj in objs if obj.type == "MESH"]
        empty = _link(bpy.data.objects.new("RoadBit", None))
        for obj in meshes:
            world = obj.matrix_world.copy()
            obj.parent = empty
            obj.matrix_world = world
        bpy.context.view_layer.update()
        mn, mx = _bounds(meshes)
        length = max(0.01, mx.x - mn.x)
        empty.scale = (14.0 / length,) * 3
        empty.location = (0.0, 0.0, -800.0)
        # The tiled blocks start ~50 m out. Pave that gap so the chase
        # is not looking at the bare underlay.
        # Tile only the road rectangles. They sit outside the lot and its sidewalk.
        spots = []
        for x0, x1, y0, y1 in road_rects():
            cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
            long_x = (x1 - x0) >= (y1 - y0)
            if long_x:
                x = x0 + 7.0
                while x < x1:
                    spots.append((x, cy))
                    x += 14.0
            else:
                y = y0 + 7.0
                while y < y1:
                    spots.append((cx, y))
                    y += 14.0
        for x, y in spots:
            bpy.ops.object.select_all(action="DESELECT")
            empty.select_set(True)
            for obj in meshes:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = empty
            bpy.ops.object.duplicate(linked=True)
            copy = bpy.context.view_layer.objects.active
            copy.location = (x, y, 0.02)
            copy.rotation_euler = (0.0, 0.0, 0.0)
    # Kenney cars face +Y. Yaw 0 travels north. The tower street runs east-west,
    # so those cabs sit at ±90 degrees and slide along X.
    specs = (
        ("taxi.glb", -30.0, 48.0, 1.5708, 7.0, "x"),
        ("taxi.glb", 20.0, 56.0, -1.5708, -6.0, "x"),
        ("taxi.glb", 70.0, 48.0, 1.5708, 8.0, "x"),
        ("sedan.glb", 110.0, 56.0, -1.5708, -7.5, "x"),
        ("taxi.glb", 150.0, 48.0, 1.5708, 6.5, "x"),
        ("sedan.glb", 190.0, 56.0, -1.5708, -8.0, "x"),
        ("taxi.glb", 72.0, 8.0, 0.0, 6.0, "y"),
        ("sedan.glb", 76.0, -18.0, 3.1416, -6.0, "y"),
    )
    cache = {}
    for index, (name, x, y, yaw, speed, axis) in enumerate(specs):
        path = CARS / name
        if not path.exists():
            path = CARS / "taxi.glb"
        if not path.exists():
            return
        if name not in cache:
            objs = _drop_helpers(_imported(path))
            meshes = [obj for obj in objs if obj.type == "MESH"]
            proto = _link(bpy.data.objects.new(f"CabProto{name}", None))
            for obj in meshes:
                world = obj.matrix_world.copy()
                obj.parent = proto
                obj.matrix_world = world
            bpy.context.view_layer.update()
            mn, _mx = _bounds(meshes)
            proto.location = (0.0, 0.0, -800.0 - mn.z)
            proto.scale = (1.7, 1.7, 1.7)
            cache[name] = (proto, meshes, mn.z)
        proto, meshes, _base = cache[name]
        bpy.ops.object.select_all(action="DESELECT")
        proto.select_set(True)
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = proto
        bpy.ops.object.duplicate(linked=True)
        copy = bpy.context.view_layer.objects.active
        copy.location = (x, y, 0.05)
        copy.rotation_euler = (0.0, 0.0, yaw)
        copy.scale = (1.7, 1.7, 1.7)
        MOVERS.append((copy, axis, x if axis == "x" else y, speed, 280.0))


def _pose_proto(path: Path, name: str, frame: int):
    if not path.exists():
        return None, None
    objs = _drop_helpers(_imported(path))
    meshes = [obj for obj in objs if obj.type == "MESH"]
    arms = [obj for obj in objs if obj.type == "ARMATURE"]
    empty = _link(bpy.data.objects.new(name, None))
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    for obj in roots:
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.matrix_world = world
    bpy.context.view_layer.update()
    mn, mx = _bounds(meshes)
    height = max(0.01, mx.z - mn.z)
    empty.scale = (1.75 / height,) * 3
    bpy.context.view_layer.update()
    mn, _mx = _bounds(meshes)
    empty.location.z -= mn.z
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    if arms:
        arm = arms[0]
        if arm.animation_data and arm.animation_data.action:
            pass
        elif bpy.data.actions:
            arm.animation_data_create()
            arm.animation_data.action = bpy.data.actions[-1]
    return empty, (arms[0] if arms else None)


def _people():
    hero_arm = None
    protos = []
    hero_empty, hero_arm = _pose_proto(IDLE, "Star", 40)
    if hero_empty is not None:
        hero_empty.location = (MAN[0], MAN[1], hero_empty.location.z)
        hero_empty.rotation_euler = (0.0, 0.0, math.pi)
        if hero_arm is not None:
            hero_arm["punchline"] = 1
    for index, path in enumerate(WALKS):
        empty, arm = _pose_proto(path, f"Walker{index}", 8 + index * 6)
        if empty is None:
            continue
        protos.append(empty)
    if not protos:
        return []
    spots = [(x, 37.2, 1.4) for x in range(-40, 150, 22)]
    # The impact group, on the sidewalk, facing back toward the coin and the lens.
    # On the sidewalk the 32.5 s lens sees, and clustered at the landing.
    spots += [
        (MAN[0] - 1.8, MAN[1] + 0.15, 1.4),
        (MAN[0] + 1.7, MAN[1] - 0.1, 1.8),
        (MAN[0] + 0.4, MAN[1] + 0.7, 0.6),
    ]
    crowd = [proto for proto in protos if proto.location.x < 40.0] or protos
    for index, (x, y, yaw) in enumerate(spots):
        proto = crowd[index % len(crowd)]
        bpy.ops.object.select_all(action="DESELECT")

        def select(obj):
            obj.select_set(True)
            for child in obj.children:
                select(child)

        select(proto)
        bpy.context.view_layer.objects.active = proto
        bpy.ops.object.duplicate()
        copy = bpy.context.view_layer.objects.active
        copy.location = (x, y, proto.location.z)
        copy.rotation_euler = (0.0, 0.0, yaw)
    lamp_data = bpy.data.lights.new("Face", "AREA")
    lamp_data.energy = 250
    lamp_data.color = (1.0, 0.92, 0.82)
    lamp_data.size = 2.2
    lamp_data.use_shadow = False
    lamp = _link(bpy.data.objects.new("FaceLamp", lamp_data))
    lamp.location = (64.8, 43.2, 2.2)
    lamp.rotation_euler = mathutils.Vector((60.2 - 64.8, 45.6 - 43.2, 1.4 - 2.2)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    arms = [hero_arm] if hero_arm is not None else []
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE" and 54.0 < obj.matrix_world.translation.x < 72.0 and 42.0 < obj.matrix_world.translation.y < 49.0:
            if obj not in arms:
                arms.append(obj)
    print(f"PEOPLE arms {len(arms)}", flush=True)
    return arms


def tick_city(t: float):
    for empty, axis, origin, speed, span in MOVERS:
        coord = origin + speed * t
        coord = origin - span * 0.5 + (coord - (origin - span * 0.5)) % span
        if axis == "x":
            empty.location.x = coord
        else:
            empty.location.y = coord


def _place_canyon(hero_pack):
    if not hero_pack:
        return
    col, size = hero_pack
    south = ESB_LOT[3] + 4.5 + 18.0 + 2.0
    center = (72.0, south + size[1] * 0.5, 0.0)
    _instance(col, center, 0.0, 1.0)
    HERO_KEEP.append(
        (center[0] - size[0] * 0.5 - 2.0, center[0] + size[0] * 0.5 + 2.0, south - 1.0, south + size[1] + 2.0)
    )
    print(f"CANYON center {center} size {tuple(round(v, 1) for v in size)}", flush=True)


def dress_city():
    """Tile the NYC blocks, then the tower streets, sidewalk life, and One WTC."""
    MOVERS.clear()
    HERO_KEEP.clear()
    _ground()
    blocks = []
    canyon = None
    for name in ("procedural_city_6", "procedural_city_3", "procedural_city_4"):
        loaded = _block(HUB / f"{name}.glb", name, hero=(name == "procedural_city_3"))
        if loaded is None:
            continue
        blocks.append(loaded)
        if loaded[2] is not None:
            canyon = loaded[2]
    _place_canyon(canyon)
    if blocks:
        _tile(blocks)
    else:
        print("NO CITY BLOCKS", flush=True)
    _wtc()
    _roads_and_cars()
    _crosswalks()
    _props()
    _commute()
    return _people()
