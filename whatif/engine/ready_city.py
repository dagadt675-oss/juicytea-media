"""A separate ready-made city, destroyed on the vanish clock.

Hub blocks (Procedural City 4 and 6) are tiled into two rows with a street
between them. The camera stands in that street, at eye height, and looks
along it. The handmade river city is not built and is not edited.
"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

from engine import cc0_city
from engine.meshkit import smoother

# Towers stay behind the shop row. The camera sits on x=0.
# Inside the downloaded intersection, along the south avenue.
# Past the bike rack, in the avenue, level so the facades stay upright.
CAM_LOC = (0.0, -66.0, 3.0)
CAM_TARGET = (0.0, -18.0, 5.8)
LENS = 28.0
SHIFT_Y = 0.06
BLOCKS = {
    "c6": "procedural_city_6.glb",
    "c4": "procedural_city_4.glb",
}
DEBRIS = (
    "lowpoly_concrete_debris.glb",
    "scan_pile_concrete.glb",
    "pbr_debris_2.glb",
    "wood_planks_debris.glb",
)


def _hide_tree(obj, hide):
    obj.hide_render = hide
    for child in obj.children_recursive:
        child.hide_render = hide


def _aim(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _world_xs(obj):
    xs = []
    for item in (obj, *obj.children_recursive):
        if getattr(item, "type", "") != "MESH":
            continue
        for corner in item.bound_box:
            xs.append((item.matrix_world @ Vector(corner)).x)
    return xs


def _push_off_street(obj, side):
    """Slide a block until its meshes clear the roadway."""
    bpy.context.view_layer.update()
    xs = _world_xs(obj)
    if not xs:
        return
    if side < 0 and max(xs) > -CORRIDOR:
        obj.location.x -= (max(xs) + CORRIDOR) + 0.4
    elif side > 0 and min(xs) < CORRIDOR:
        obj.location.x += (CORRIDOR - min(xs)) + 0.4
    bpy.context.view_layer.update()


def _footprint(filename, height):
    from engine import private_assets

    size = private_assets.block_size(filename, 2.0)
    if not size:
        return None
    scale = float(height) / max(size[2], 0.01)
    return size[0] * scale, size[1] * scale


def _place_blocks(kit):
    """Two staggered rows of hub blocks. The gap between them is the street."""
    from engine import private_assets

    coll = kit.collection("City")
    # (file, height) pairs. Left and right of one row, then the next row.
    rows = (
        (("c6", 38.0), ("c6", 46.0)),
        (("c4", 42.0), ("c6", 34.0)),
        (("c6", 52.0), ("c4", 44.0)),
        (("c6", 36.0), ("c6", 48.0)),
        (("c4", 40.0), ("c6", 33.0)),
    )
    y_cursor = -36.0
    gap = 14.0
    placed = []
    for index, pair in enumerate(rows):
        depths = []
        widths = []
        specs = []
        for file_key, height in pair:
            filename = BLOCKS[file_key]
            foot = _footprint(filename, height)
            if foot is None:
                continue
            widths.append(foot[0])
            depths.append(foot[1])
            specs.append((filename, height, foot[0], foot[1]))
        if not specs:
            continue
        depth = max(depths)
        center_y = y_cursor + depth * 0.5
        for side, (filename, height, width, _depth) in zip((-1, 1), specs):
            center_x = side * (CORRIDOR + width * 0.5 + 0.6)
            block = private_assets.place_city_block(
                coll, filename, center_x, center_y, 0.0,
                yaw=0.0, height=height, min_z=2.0, name="street_block",
            )
            if block is None:
                continue
            _push_off_street(block, side)
            item = kit.add(
                block, "building_base", sink=False, topple=(index % 2 == 0 and side > 0),
                rank="inner",
            )
            placed.append(item)
        # Outer block centered on the cross-street gap, so the side road ends at a building.
        gap_y = center_y + depth * 0.5 + gap * 0.5
        for side, (file_key, height) in zip((-1, 1), (("c4", 30.0), ("c6", 28.0))):
            filename = BLOCKS[file_key]
            foot = _footprint(filename, height)
            if foot is None:
                continue
            inner_width = widths[0] if side < 0 else widths[-1]
            center_x = side * (CORRIDOR + inner_width + 5.0 + foot[0] * 0.5)
            block = private_assets.place_city_block(
                coll, filename, center_x, gap_y, 0.0,
                yaw=0.0, height=height, min_z=2.0, name="side_block",
            )
            if block is None:
                continue
            _push_off_street(block, side)
            placed.append(kit.add(block, "building_base", sink=False, topple=False, rank="outer"))
        y_cursor = center_y + depth * 0.5 + gap
    print("street blocks", len(placed), "end y", round(y_cursor, 1), flush=True)
    return y_cursor


def _grey_concrete():
    """Flat grey concrete. The downtown curb atlas has a red trim; this replaces it."""
    path = Path(
        "/opt/cursor/asset-cache/cc0/extracted/city_buildings/"
        "quaternius_downtown_city_megakit/Textures/T_Concrete_BaseColor.png"
    )
    if not path.exists():
        return None
    mat = bpy.data.materials.new("GreyConcrete")
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = next(node for node in tree.nodes if node.type == "BSDF_PRINCIPLED")
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path), check_existing=True)
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.5, 2.5, 2.5)
    coord = tree.nodes.new("ShaderNodeTexCoord")
    tree.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
    tree.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.86
    return mat


def _visual_mesh(path):
    """Import a glTF and return one mesh. LOD copies and curves stay out."""
    key = str(path)
    cache = getattr(_visual_mesh, "cache", {})
    if key in cache:
        return cache[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in fresh if obj.type == "MESH" and "LOD" not in obj.name.upper()]
    for obj in fresh:
        if obj not in meshes:
            obj.hide_render = True
    if not meshes:
        cache[key] = None
        _visual_mesh.cache = cache
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    xs = [vert.co.x for vert in obj.data.vertices]
    ys = [vert.co.y for vert in obj.data.vertices]
    zs = [vert.co.z for vert in obj.data.vertices]
    dx = (min(xs) + max(xs)) * 0.5
    dy = (min(ys) + max(ys)) * 0.5
    dz = min(zs)
    for vert in obj.data.vertices:
        vert.co.x -= dx
        vert.co.y -= dy
        vert.co.z -= dz
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    cache[key] = mesh
    _visual_mesh.cache = cache
    return mesh


def _size(mesh):
    xs = [vert.co.x for vert in mesh.vertices]
    ys = [vert.co.y for vert in mesh.vertices]
    zs = [vert.co.z for vert in mesh.vertices]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def _spawn_mesh(coll, mesh, loc, yaw, scale, name):
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.location = loc
    obj.rotation_euler.z = yaw
    if isinstance(scale, (int, float)):
        obj.scale = (scale, scale, scale)
    else:
        obj.scale = scale
    return obj


def _tile(coll, mesh, x, y0, y1, z, along, name, mat=None):
    """Repeat a ground piece along Y. ``along`` is the native length of one piece."""
    made = []
    cursor = y0
    step = max(along * 0.98, 0.4)
    while cursor < y1:
        obj = _spawn_mesh(coll, mesh, (x, cursor + step * 0.5, z), 0.0, 1.0, name)
        if mat is not None:
            obj.data = obj.data.copy()
            obj.data.materials.clear()
            obj.data.materials.append(mat)
        made.append(obj)
        cursor += step
    return made


def _asphalt_strip(coll, mat, y0, y1, half):
    """One photographic asphalt surface, so the avenue has no tile seam."""
    mesh = bpy.data.meshes.new("avenue_asphalt")
    bm = bmesh.new()
    coords = ((-half, y0, 0.015), (half, y0, 0.015), (half, y1, 0.015), (-half, y1, 0.015))
    verts = [bm.verts.new(co) for co in coords]
    face = bm.faces.new(verts)
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for loop in face.loops:
        co = loop.vert.co
        loop[uv_layer].uv = ((co.x + half) / 3.2, (co.y - y0) / 3.2)
    bm.to_mesh(mesh)
    bm.free()
    if mat is not None:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new("asphalt", mesh)
    coll.objects.link(obj)
    return obj


def _roads(kit, end_y):
    """Grey concrete sidewalks and photographic asphalt. The red curb kit stays out."""
    from engine import found_assets

    roads = kit.collection("Terrain")
    kit_root = Path(
        "/opt/cursor/asset-cache/cc0/extracted/city_buildings/"
        "quaternius_downtown_city_megakit/Exports/glTF (Godot)"
    )
    asphalt = found_assets.pbr_material("AvenueAsphalt", "worn_asphalt", uv=0.55)
    ruined = found_assets.pbr_material("AvenueCracked", "road_damaged", uv=0.55)
    concrete = _grey_concrete()
    sidewalk_mesh = _visual_mesh(kit_root / "Sidewalk_Straight_3m.gltf")
    line_mesh = _visual_mesh(kit_root / "Decal_BrokenLine_Straight.gltf")
    cross_mesh = _visual_mesh(kit_root / "Decal_Crosswalk.gltf")
    hole_mesh = _visual_mesh(kit_root / "Prop_ManholeCover.gltf")
    y0, y1 = -6.0, min(end_y, 220.0)
    avenue = []
    strip = _asphalt_strip(roads, asphalt, y0, y1, 3.6)
    ruined_strip = _asphalt_strip(roads, ruined, y0, y1, 3.6)
    if ruined_strip is not None:
        ruined_strip.location.z = 0.008
    if strip is not None:
        kit.add(strip, "prop", sink=False)
    if ruined_strip is not None:
        kit.add(ruined_strip, "prop", sink=False)
    kit.road_clean = strip
    kit.road_ruined = ruined_strip
    if sidewalk_mesh is not None:
        size = _size(sidewalk_mesh)
        long_axis = 0 if size[0] >= size[1] else 1
        yaw = math.pi / 2.0 if long_axis == 0 else 0.0
        length = max(size[long_axis], 0.5)
        for side in (-1.0, 1.0):
            cursor = y0
            while cursor < y1:
                obj = _spawn_mesh(
                    roads, sidewalk_mesh, (side * 5.2, cursor + length * 0.5, 0.02),
                    yaw + (0.0 if side > 0 else math.pi), 1.0, "sidewalk",
                )
                if concrete is not None and obj.data.users > 1:
                    obj.data = obj.data.copy()
                if concrete is not None:
                    obj.data.materials.clear()
                    obj.data.materials.append(concrete)
                cursor += length * 0.98
                del obj
    if line_mesh is not None:
        size = _size(line_mesh)
        length = max(size[0], size[1], 0.4)
        yaw = math.pi / 2.0 if size[0] >= size[1] else 0.0
        for x in (-1.7, 1.7):
            cursor = 6.0
            while cursor < min(y1, 140.0):
                mark = _spawn_mesh(roads, line_mesh, (x, cursor, 0.045), yaw, 1.0, "lane")
                kit.add(mark, "road_mark", sink=False)
                cursor += length * 1.15
    if cross_mesh is not None:
        mark = _spawn_mesh(roads, cross_mesh, (0.0, 22.0, 0.05), math.pi / 2.0, 1.2, "crosswalk")
        kit.add(mark, "road_mark", sink=False)
    if hole_mesh is not None:
        for y in (14.0, 32.0, 54.0, 78.0, 104.0):
            cover = _spawn_mesh(roads, hole_mesh, (0.4, y, 0.04), 0.2, 1.0, "manhole")
            kit.add(cover, "prop", sink=False)
    kit.avenue = avenue
    kit.asphalt_clean = asphalt
    kit.asphalt_ruined = ruined
    print("avenue tiles", len(avenue), flush=True)


def _life(kit):
    """A busy avenue: walkers, cyclists, moving lanes, and cars parked at the curb."""
    from engine.scenes import _bike, _traffic, _walker

    life = kit.collection("Life")
    z = 0.08
    spots = []
    for side in (-1.0, 1.0):
        for step, y0 in enumerate((8.0, 14.0, 21.0, 29.0, 38.0, 48.0, 60.0, 74.0, 90.0)):
            spots.append((side * (4.4 if step % 2 == 0 else 4.9), y0, 1.0 if step % 2 == 0 else -1.0))
    for index, (x, y0, direction) in enumerate(spots):
        _walker(
            kit, life,
            [(x, y0, z), (x, y0 + 12.0 * direction, z)],
            1.3, index * 1.7, height=1.75,
        )
    for index, (x, y0) in enumerate(((-1.4, 26.0), (1.5, 38.0), (-0.6, 52.0), (2.0, 68.0), (-1.8, 84.0))):
        _bike(kit, life, [(x, y0, z), (x, y0 + 20.0, z)], index * 2.4)
    lanes = (
        ((-1.5, 12.0, z), (-1.5, 170.0, z), 6, 9.0),
        ((1.6, 18.0, z), (1.6, 180.0, z), 7, 11.0),
        ((-2.2, 40.0, z), (-2.2, 160.0, z), 8, 8.0),
        ((2.3, 150.0, z), (2.3, 10.0, z), 9, 10.0),
        ((1.2, 70.0, z), (1.2, 190.0, z), 10, 12.0),
        ((-1.8, 130.0, z), (-1.8, 8.0, z), 11, 7.5),
        ((2.0, 6.0, z), (2.0, 120.0, z), 4, 9.5),
        ((-2.4, 24.0, z), (-2.4, 140.0, z), 5, 8.5),
    )
    for index, (start, end, car_index, speed) in enumerate(lanes):
        item = _traffic(kit, life, [start, end], car_index, speed, index * 6.0, coast=6.0)
        if item is not None:
            item.extra["hero"] = True
    for index, (x, y) in enumerate(((-3.3, 16.0), (3.3, 20.0), (-3.3, 36.0), (3.3, 44.0), (-3.3, 62.0), (3.3, 70.0), (-3.3, 88.0), (3.3, 96.0))):
        loc = (x, y, z)
        built = cc0_city.place_fleet_car(life, loc, math.pi / 2.0 if x < 0 else -math.pi / 2.0, index=index + 3)
        if built is None:
            continue
        item = kit.add(built, "car", path_from=loc, path_to=loc, index=20 + index, paint=(0.9, 0.9, 0.9, 1), sink=False)
        item.extra["hero"] = True
        item.extra["parked"] = True


def _shops_and_lamps(kit):
    """Storefronts, awnings, and lamp posts along both sidewalks."""
    from engine import found_assets

    coll = kit.collection("City")
    godot = Path(
        "/opt/cursor/asset-cache/cc0/extracted/city_buildings/"
        "quaternius_downtown_city_megakit/Exports/glTF (Godot)"
    )
    kenney = Path(
        "/opt/cursor/asset-cache/cc0/extracted/city_buildings/"
        "kenney_city_kit_commercial/Models/GLB format"
    )
    names = ("Building_Small_1.gltf", "Building_Medium_2_001.gltf", "Building_Large_2.gltf")
    meshes = []
    for name in names:
        mesh = _visual_mesh(godot / name)
        if mesh is not None:
            meshes.append(mesh)
    awning = _visual_mesh(kenney / "detail-awning.glb")
    lamp = _visual_mesh(Path("/opt/cursor/asset-cache/cc0/polyhaven/street_lamp_01/street_lamp_01_1k.gltf"))
    hydrant = _visual_mesh(Path("/opt/cursor/asset-cache/cc0/polyhaven/fire_hydrant/fire_hydrant_1k.gltf"))
    if meshes:
        for index, y in enumerate(range(16, 140, 12)):
            for side in (-1.0, 1.0):
                mesh = meshes[(index + (0 if side < 0 else 1)) % len(meshes)]
                native = _size(mesh)
                # After a quarter turn the street-facing depth is the mesh's Y size.
                half = native[1] * 0.5
                yaw = math.pi / 2.0 if side > 0 else -math.pi / 2.0
                shop = _spawn_mesh(coll, mesh, (side * (6.4 + half), float(y), 0.0), yaw, 1.15, "shop")
                found_assets.stamp_object(shop, "moss")
                kit.add(shop, "building_base", sink=False, shop=True, topple=True)
                if awning is not None and index % 2 == 0:
                    face = side * (6.4 + 0.15)
                    _spawn_mesh(coll, awning, (face, float(y), 3.4), yaw, 1.4, "awning")
    if lamp is not None:
        native_h = max(_size(lamp)[2], 0.2)
        scale = 6.2 / native_h
        for y in range(10, 130, 16):
            for side in (-1.0, 1.0):
                obj = _spawn_mesh(coll, lamp, (side * 7.6, float(y), 0.0), 0.0, scale, "lamp")
                kit.add(obj, "prop", sink=False)
    if hydrant is not None:
        native_h = max(_size(hydrant)[2], 0.2)
        scale = 0.85 / native_h
        for y in (18.0, 46.0, 78.0):
            for side in (-1.0, 1.0):
                obj = _spawn_mesh(coll, hydrant, (side * 5.1, y, 0.0), 0.4, scale, "hydrant")
                kit.add(obj, "prop", sink=False)


def _forest_and_weeds(kit):
    """Photographed trees. Saplings at year 100, a forest through the street at year 500."""
    from engine.scenes import _plant

    plants = kit.collection("Plants")
    rng = random.Random(19)
    sources = (
        (Path("/opt/cursor/asset-cache/cc0/polyhaven/island_tree_02/island_tree_02_1k.gltf"), (9.0, 16.0)),
        (Path("/opt/cursor/asset-cache/cc0/polyhaven/tree_small_02/tree_small_02_1k.gltf"), (6.0, 10.0)),
        (Path("/workspace/assets/found/polyhaven/models/fir_sapling/fir_sapling_1k.gltf"), (4.0, 7.5)),
    )
    loaded = []
    for path, span in sources:
        if not path.exists():
            continue
        mesh = _visual_mesh(path)
        if mesh is not None:
            loaded.append((mesh, max(_size(mesh)[2], 0.2), span))
    for i, (mesh, native_h, span) in enumerate(loaded * 12):
        height = rng.uniform(*span)
        scale = height / native_h
        x = rng.choice((-2.4, -0.6, 0.8, 2.2, -4.6, 4.8))
        y = 12.0 + (i * 7.5) % 110.0
        tree = _spawn_mesh(plants, mesh, (x, y, 0.0), rng.random() * math.tau, scale, "real_tree")
        kit.add(tree, "swallow", sink=False)
    for i in range(10):
        mesh, native_h, _span = loaded[-1] if loaded else (None, 1.0, (1, 1))
        if mesh is None:
            break
        scale = rng.uniform(2.4, 4.2) / native_h
        tree = _spawn_mesh(plants, mesh, (rng.choice((-5.4, 5.6)), 14.0 + i * 8.0, 0.0), i, scale, "sapling")
        kit.add(tree, "tree_canopy", future=True, delay=0.5, sink=False, leaf=(0.15, 0.32, 0.1, 1), autumn=(0.2, 0.28, 0.08, 1))
    for i in range(70):
        _plant(
            kit, plants,
            ("grass_medium_01", "fern_02", "shrub_01", "weed_plant_02", "moss_01", "grass_medium_02")[i % 6],
            rng.uniform(-4.2, 4.2) if i % 3 else rng.choice((-6.2, 6.2)),
            rng.uniform(8.0, 110.0), 0.0,
            rng.uniform(0.35, 1.2), delay=0.22, yaw=rng.random() * 6.0,
        )
    for i, y in enumerate((12.0, 24.0, 36.0, 50.0, 66.0, 82.0)):
        for side in (-1.0, 1.0):
            _plant(
                kit, plants, "fern_02" if i % 2 == 0 else "moss_01",
                side * 10.4, y, 1.4 + (i % 3) * 1.1,
                1.1, delay=0.4, yaw=0.0, role="year_age",
            )


def _aabb(obj):
    xs, ys, zs = [], [], []
    for item in (obj, *obj.children_recursive):
        if getattr(item, "type", "") != "MESH":
            continue
        for corner in item.bound_box:
            point = item.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    if not zs:
        return None
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def _rubble_proto(path, coll):
    """One debris file, parented and scaled so its height is 1 m at the origin."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    fresh = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not fresh:
        return None
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for obj in fresh:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    if not zs:
        return None
    height = max(zs) - min(zs)
    width = max(max(xs) - min(xs), max(ys) - min(ys))
    # Scans sometimes import hundreds of metres across. Skip those.
    if height < 0.05 or height > 40.0 or width > 80.0:
        print("debris skip", path.name, round(width, 1), round(height, 1), flush=True)
        for obj in fresh:
            obj.hide_render = True
        return None
    holder = bpy.data.objects.new(path.stem + "_src", None)
    coll.objects.link(holder)
    holder.location = ((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, min(zs))
    bpy.context.view_layer.update()
    for obj in fresh:
        world = obj.matrix_world.copy()
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        coll.objects.link(obj)
        obj.parent = holder
        obj.matrix_world = world
    span = max(height, width, 0.01)
    holder.scale = (1.0 / span, 1.0 / span, 1.0 / span)
    holder.location = (0.0, 0.0, 0.0)
    _hide_tree(holder, True)
    return holder


def _spawn_rubble(src, coll, loc, yaw, height):
    copy = src.copy()
    coll.objects.link(copy)
    for child in src.children:
        child_copy = child.copy()
        coll.objects.link(child_copy)
        child_copy.parent = copy
        child_copy.matrix_parent_inverse = child.matrix_parent_inverse.copy()
        child_copy.hide_render = False
    copy.hide_render = False
    copy.location = Vector(loc)
    copy.rotation_euler = Euler((0.0, 0.0, yaw))
    copy.scale = tuple(axis * height for axis in src.scale)
    return copy


def _rubble(kit):
    """Hub debris piles, a few metres across. They must not become a mountain."""
    root = Path("/opt/cursor/asset-cache/private/debris")
    coll = kit.collection("City")
    rng = random.Random(23)
    protos = []
    for name in DEBRIS:
        path = root / name
        if not path.exists():
            continue
        proto = _rubble_proto(path, coll)
        if proto is not None:
            protos.append(proto)
    if not protos:
        return 0
    made = 0
    spots = []
    for i in range(14):
        spots.append((rng.uniform(-3.6, 3.6), 14.0 + i * 9.0, "rubble", rng.uniform(1.4, 2.6)))
    for i in range(6):
        spots.append((rng.choice((-1.6, 0.6, 2.0)), 22.0 + i * 16.0, "rubble_hill", rng.uniform(2.8, 4.2)))
    for x, y, role, height in spots:
        src = protos[made % len(protos)]
        copy = _spawn_rubble(src, coll, (x, y, 0.0), rng.random() * math.tau, height)
        kit.add(copy, role, sink=False)
        made += 1
    return made


def _shells(kit):
    """Ruined-city shells that replace the towers once they have fallen."""
    from engine.scenes import _ruin_piece

    coll = kit.collection("City")
    made = 0
    rng = random.Random(31)
    for i in range(14):
        side = -1.0 if i % 2 == 0 else 1.0
        shell = _ruin_piece(
            coll,
            (side * rng.uniform(0.4, 2.8), 24.0 + i * 8.0, 0.0),
            rng.random() * 0.4,
            rng.uniform(12.0, 20.0),
        )
        if shell is None:
            continue
        bpy.context.view_layer.update()
        box = _aabb(shell)
        if box is None or box[3] < 8.0 or abs((box[0] + box[1]) * 0.5) < 1.2 and box[2] < 6.0:
            bpy.data.objects.remove(shell, do_unlink=True)
            continue
        kit.add(shell, "shell", sink=False)
        made += 1
    return made


def _fog(coll):
    """A low sheet in the street. Density dies before the tower tops."""
    mesh = bpy.data.meshes.new("street_fog")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("street_fog", mesh)
    coll.objects.link(obj)
    obj.location = (0.0, 40.0, 6.0)
    obj.scale = (28.0, 90.0, 12.0)
    mat = bpy.data.materials.new("StreetFog")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    vol = tree.nodes.new("ShaderNodeVolumePrincipled")
    geom = tree.nodes.new("ShaderNodeNewGeometry")
    sep = tree.nodes.new("ShaderNodeSeparateXYZ")
    tree.links.new(geom.outputs["Position"], sep.inputs["Vector"])
    fall = tree.nodes.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value = 0.0
    fall.inputs["From Max"].default_value = 11.0
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    fall.clamp = True
    tree.links.new(sep.outputs["Z"], fall.inputs["Value"])
    density = tree.nodes.new("ShaderNodeValue")
    density.name = "Fog"
    density.outputs[0].default_value = 0.004
    mul = tree.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    tree.links.new(density.outputs[0], mul.inputs[0])
    tree.links.new(fall.outputs["Result"], mul.inputs[1])
    tree.links.new(mul.outputs[0], vol.inputs["Density"])
    vol.inputs["Color"].default_value = (0.92, 0.88, 0.78, 1.0)
    vol.inputs["Anisotropy"].default_value = 0.62
    tree.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    mesh.materials.append(mat)
    return obj, density


def _fracture_a_few(kit):
    """A few cell-fracture shards for the towers that come down at year 500."""
    if os.environ.get("WHATIF_FRACTURE", "1") == "0":
        print("fracture skipped", flush=True)
        return 0
    import addon_utils

    try:
        addon_utils.enable("bl_ext.user_default.cell_fracture", default_set=False, persistent=False)
    except Exception as exc:
        print("fracture addon", exc, flush=True)
        return 0
    if not hasattr(bpy.ops.object, "add_fracture_cell_objects"):
        print("fracture op missing", flush=True)
        return 0
    from engine.decay_vfx import _cell_fracture

    hosts = []
    for item in kit.items:
        if item.role != "building_base" or not item.extra.get("shop"):
            continue
        if not (20.0 < item.base_loc.y < 80.0):
            continue
        candidates = [item.obj] if item.obj.type == "MESH" else []
        candidates.extend(child for child in item.obj.children_recursive if child.type == "MESH")
        for child in candidates:
            if child.data is None:
                continue
            count = len(child.data.vertices)
            if 200 < count < 40000 and max(child.dimensions) < 40.0:
                hosts.append(child)
                break
        if len(hosts) >= 2:
            break
    made = 0
    coll = kit.collection("City")
    for host in hosts:
        shards = _cell_fracture(host, 8)
        for shard in shards:
            if shard.name not in coll.objects:
                coll.objects.link(shard)
            kit.add(shard, "fracture500", sink=False)
            made += 1
    print("fracture shards", made, flush=True)
    return made


def _darken_bike_lane():
    """The red bike-lane ribbon becomes dark grey asphalt. The paving stays."""
    image_path = Path("/workspace/assets/found/polyhaven/textures/worn_asphalt/worn_asphalt_diff_1k.jpg")
    image = bpy.data.images.load(str(image_path), check_existing=True) if image_path.exists() else None
    for name in ("Bike Lane", "Bike Lane Floor"):
        mat = bpy.data.materials.get(name)
        if mat is None or mat.node_tree is None:
            continue
        tree = mat.node_tree
        bsdf = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None or image is None:
            continue
        if bsdf.inputs["Base Color"].is_linked:
            tree.links.remove(bsdf.inputs["Base Color"].links[0])
        tex = tree.nodes.new("ShaderNodeTexImage")
        tex.image = image
        mapping = tree.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (0.12, 0.12, 0.12)
        coord = tree.nodes.new("ShaderNodeTexCoord")
        mix = tree.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        mix.inputs["Color2"].default_value = (0.62, 0.64, 0.66, 1)
        tree.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
        tree.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        tree.links.new(tex.outputs["Color"], mix.inputs["Color1"])
        tree.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.86


def _import_intersection(kit):
    """One complete CC0 intersection. Not a tiled block."""
    path = Path("/opt/cursor/asset-cache/cc0/source_city/Main_Intersection_v2.glb")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    bpy.context.view_layer.update()
    tall = []
    windows = []
    for obj in fresh:
        if obj.name == "Plane.016":
            obj.hide_render = True
            continue
        if obj.type != "MESH":
            continue
        if "Window Decal" in obj.name:
            zs = [(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]
            obj["floor_z"] = min(zs)
            windows.append(obj)
        elif obj.name.startswith("Block") and obj.dimensions.z > 18.0:
            zs = [(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]
            xs = [(obj.matrix_world @ Vector(corner)).x for corner in obj.bound_box]
            ys = [(obj.matrix_world @ Vector(corner)).y for corner in obj.bound_box]
            obj["floor_z"] = min(zs)
            obj["mid_x"] = (min(xs) + max(xs)) * 0.5
            obj["mid_y"] = (min(ys) + max(ys)) * 0.5
            tall.append(obj)
    kit.tall_blocks = tall
    kit.window_decals = windows
    # Right-hand row of this avenue (positive X, south of the crossing).
    kit.collapsed_block = next(
        (obj for obj in tall if obj.get("mid_x", 0.0) > 0.0 and obj.get("mid_y", 0.0) < 0.0),
        None,
    )
    dome = next((obj for obj in fresh if obj.type == "MESH" and obj.name.startswith("Store Circle")), None)
    kit.dome = dome
    _darken_bike_lane()
    from engine import found_assets
    for obj in tall + windows:
        found_assets.stamp_object(obj, "moss")
    _arm_ruin_stain(fresh)
    _cut_street_facades(kit, tall, windows, dome)
    print("intersection objects", len(fresh), "tall", len(tall), "windows", len(windows), flush=True)
    return fresh


def _rebar_material():
    mat = bpy.data.materials.get("RebarConcrete")
    if mat is not None:
        return mat
    mat = bpy.data.materials.new("RebarConcrete")
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = next(node for node in tree.nodes if node.type == "BSDF_PRINCIPLED")
    path = Path("/workspace/assets/found/polyhaven/textures/rebar_reinforced_concrete/rebar_reinforced_concrete_diff_1k.jpg")
    if path.exists():
        tex = tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        coord = tree.nodes.new("ShaderNodeTexCoord")
        mapping = tree.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (0.35, 0.35, 0.35)
        tree.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
        tree.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return mat


def _arm_ruin_stain(objects):
    """A Ruin factor of 0 leaves Day 1 untouched. Year 500 pushes it to 1."""
    seen = set()
    for obj in objects:
        if obj.type != "MESH" or obj.name.startswith("Ground") or obj.name.startswith("Bike"):
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or mat in seen or mat.node_tree is None or mat.get("ruin_stain"):
                continue
            seen.add(mat)
            bsdf = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
            if bsdf is None or "Base Color" not in bsdf.inputs:
                continue
            tree = mat.node_tree
            color_in = bsdf.inputs["Base Color"]
            if color_in.is_linked:
                source = color_in.links[0].from_socket
                tree.links.remove(color_in.links[0])
            else:
                rgb = tree.nodes.new("ShaderNodeRGB")
                rgb.outputs[0].default_value = tuple(color_in.default_value)
                source = rgb.outputs[0]
            ruin = tree.nodes.new("ShaderNodeValue")
            ruin.name = "Ruin"
            ruin.outputs[0].default_value = 0.0
            coord = tree.nodes.new("ShaderNodeTexCoord")
            mapping = tree.nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (0.18, 0.18, 3.2)
            tree.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
            streak = tree.nodes.new("ShaderNodeTexNoise")
            streak.inputs["Scale"].default_value = 5.0
            streak.inputs["Detail"].default_value = 8.0
            tree.links.new(mapping.outputs["Vector"], streak.inputs["Vector"])
            moss_path = Path("/workspace/assets/found/polyhaven/textures/concrete_moss/concrete_moss_diff_1k.jpg")
            dark = tree.nodes.new("ShaderNodeMixRGB")
            dark.blend_type = "MULTIPLY"
            dark.inputs["Fac"].default_value = 1.0
            dark.inputs["Color2"].default_value = (0.28, 0.32, 0.22, 1)
            tree.links.new(source, dark.inputs["Color1"])
            if moss_path.exists():
                moss = tree.nodes.new("ShaderNodeTexImage")
                moss.image = bpy.data.images.load(str(moss_path), check_existing=True)
                tree.links.new(mapping.outputs["Vector"], moss.inputs["Vector"])
                moss_mix = tree.nodes.new("ShaderNodeMixRGB")
                tree.links.new(streak.outputs["Fac"], moss_mix.inputs["Fac"])
                tree.links.new(dark.outputs["Color"], moss_mix.inputs["Color1"])
                tree.links.new(moss.outputs["Color"], moss_mix.inputs["Color2"])
                stained = moss_mix.outputs["Color"]
            else:
                stained = dark.outputs["Color"]
            ao = tree.nodes.new("ShaderNodeAmbientOcclusion")
            ao.inputs["Distance"].default_value = 1.6
            cavity = tree.nodes.new("ShaderNodeMath")
            cavity.operation = "SUBTRACT"
            cavity.inputs[0].default_value = 1.0
            tree.links.new(ao.outputs["AO"], cavity.inputs[1])
            grit = tree.nodes.new("ShaderNodeMath")
            grit.operation = "MULTIPLY_ADD"
            grit.inputs[1].default_value = 0.8
            grit.inputs[2].default_value = 0.0
            tree.links.new(cavity.outputs[0], grit.inputs[0])
            add_streak = tree.nodes.new("ShaderNodeMath")
            add_streak.operation = "MULTIPLY_ADD"
            add_streak.inputs[1].default_value = 0.55
            tree.links.new(streak.outputs["Fac"], add_streak.inputs[0])
            tree.links.new(grit.outputs[0], add_streak.inputs[2])
            capped = tree.nodes.new("ShaderNodeMath")
            capped.operation = "MINIMUM"
            capped.inputs[1].default_value = 0.72
            tree.links.new(add_streak.outputs[0], capped.inputs[0])
            fac = tree.nodes.new("ShaderNodeMath")
            fac.operation = "MULTIPLY"
            tree.links.new(ruin.outputs[0], fac.inputs[0])
            tree.links.new(capped.outputs[0], fac.inputs[1])
            final = tree.nodes.new("ShaderNodeMixRGB")
            final.name = "RuinMix"
            tree.links.new(fac.outputs[0], final.inputs["Fac"])
            tree.links.new(source, final.inputs["Color1"])
            tree.links.new(stained, final.inputs["Color2"])
            tree.links.new(final.outputs["Color"], color_in)
            mat["ruin_stain"] = True


def _bake_world(obj):
    baked = obj.data.copy()
    baked.transform(obj.matrix_world.copy())
    obj.data = baked
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.location = (0.0, 0.0, 0.0)


def _delete_where(obj, pred):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    doomed = [vert for vert in bm.verts if pred(vert.co)]
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _slab(coll, loc, size):
    mesh = bpy.data.meshes.new("floor_slab")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(_rebar_material())
    obj = bpy.data.objects.new("floor_slab", mesh)
    coll.objects.link(obj)
    obj.location = loc
    obj.scale = size
    return obj


def _fallen_corner(kit, src):
    """Break one top corner off the right tower and lay those shards across the avenue."""
    coll = kit.collection("City")
    chunk = src.copy()
    chunk.data = src.data.copy()
    coll.objects.link(chunk)
    _bake_world(chunk)
    _delete_where(
        chunk,
        lambda p: not (14.0 < p.x < 22.0 and -50.0 < p.y < -36.0 and 18.0 < p.z < 32.0),
    )
    if len(chunk.data.vertices) < 20:
        print("corner empty", flush=True)
        chunk.hide_render = True
        return
    # Keep the tower's own facade. Fracturing it replaced the windows with grey caps.
    members = [chunk]
    chunk.hide_render = False
    xs, ys, zs = [], [], []
    for shard in members:
        for vert in shard.data.vertices:
            xs.append(vert.co.x)
            ys.append(vert.co.y)
            zs.append(vert.co.z)
    if not xs:
        return
    center = Vector(((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, (min(zs) + max(zs)) * 0.5))
    tip = Matrix.Translation(center) @ Matrix.Rotation(math.pi / 2.0, 4, "Y") @ Matrix.Translation(-center)
    for shard in members:
        shard.data.transform(tip)
    xs, ys, zs = [], [], []
    for shard in members:
        for vert in shard.data.vertices:
            xs.append(vert.co.x)
            ys.append(vert.co.y)
            zs.append(vert.co.z)
    center = Vector(((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, (min(zs) + max(zs)) * 0.5))
    diagonal = Matrix.Translation(center) @ Matrix.Rotation(0.7, 4, "Z") @ Matrix.Translation(-center)
    for shard in members:
        shard.data.transform(diagonal)
    xs, ys, zs = [], [], []
    for shard in members:
        for vert in shard.data.vertices:
            xs.append(vert.co.x)
            ys.append(vert.co.y)
            zs.append(vert.co.z)
    height = max(zs) - min(zs)
    squash = min(1.0, 2.4 / max(height, 0.01))
    scale_z = Matrix.Identity(4)
    scale_z[2][2] = squash
    bottom = min(zs)
    squat = Matrix.Translation((0.0, 0.0, bottom)) @ scale_z @ Matrix.Translation((0.0, 0.0, -bottom))
    shift = Vector((-(min(xs) + max(xs)) * 0.5, -36.0 - (min(ys) + max(ys)) * 0.5, 1.35 - bottom))
    place = Matrix.Translation(shift) @ squat
    for shard in members:
        shard.data.transform(place)
    kit.corner_matrices = [tip, diagonal, place]
    kit.fallen_shards = list(members)
    print("tower corner shards", len(members), "z", round(height * squash, 1), flush=True)


def _cut_street_facades(kit, tall, windows, dome):
    """Full-height copies with a few missing panels. Only the right tower loses a top corner."""
    del dome
    coll = kit.collection("City")
    left = next((obj for obj in tall if obj.get("mid_x", 0.0) < 0.0 and obj.get("mid_y", 0.0) < 0.0), None)
    right = next((obj for obj in tall if obj.get("mid_x", 0.0) > 0.0 and obj.get("mid_y", 0.0) < 0.0), None)
    originals = []
    ruins = []
    panels = (
        (left, lambda p: (-18.0 < p.x < -14.2 and -47.0 < p.y < -42.0 and 15.0 < p.z < 22.0)
         or (-17.5 < p.x < -14.2 and -34.0 < p.y < -30.0 and 24.0 < p.z < 31.0)),
        (right, lambda p: 14.0 < p.x < 22.0 and -50.0 < p.y < -36.0 and 18.0 < p.z < 32.0),
    )
    for src, pred in panels:
        if src is None:
            continue
        copy = src.copy()
        copy.data = src.data.copy()
        coll.objects.link(copy)
        _bake_world(copy)
        _delete_where(copy, pred)
        copy.hide_render = True
        originals.append(src)
        ruins.append(copy)
    if right is not None:
        decal = next((obj for obj in windows if "Block2" in obj.name and "Window" in obj.name), None)
        _fallen_corner(kit, right)
        if decal is not None and getattr(kit, "fallen_shards", None):
            piece = decal.copy()
            piece.data = decal.data.copy()
            coll.objects.link(piece)
            _bake_world(piece)
            _delete_where(
                piece,
                lambda p: not (14.0 < p.x < 22.0 and -50.0 < p.y < -36.0 and 18.0 < p.z < 32.0),
            )
            for matrix in kit.corner_matrices:
                piece.data.transform(matrix)
            piece.hide_render = True
            kit.fallen_shards.append(piece)
            xs, ys, zs = [], [], []
            for shard in kit.fallen_shards:
                for vert in shard.data.vertices:
                    xs.append(vert.co.x)
                    ys.append(vert.co.y)
                    zs.append(vert.co.z)
            if xs:
                center = Vector(((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, 0.0))
                if (max(ys) - min(ys)) > (max(xs) - min(xs)):
                    turn = Matrix.Translation(center) @ Matrix.Rotation(math.pi / 2.0, 4, "Z") @ Matrix.Translation(-center)
                    for shard in kit.fallen_shards:
                        shard.data.transform(turn)
                widen = Matrix.Identity(4)
                widen[0][0] = 1.6
                widen[1][1] = 1.6
                for shard in kit.fallen_shards:
                    shard.data.transform(Matrix.Translation(center) @ widen @ Matrix.Translation(-center))
                zs = sorted(vert.co.z for shard in kit.fallen_shards for vert in shard.data.vertices)
                level = zs[max(len(zs) // 8, 0)]
                drop = Matrix.Translation((0.0, 0.0, 1.4 - level))
                for shard in kit.fallen_shards:
                    shard.data.transform(drop)
            # The standing decal loses that same corner, and stays on the tower.
            standing = decal.copy()
            standing.data = decal.data.copy()
            coll.objects.link(standing)
            _bake_world(standing)
            _delete_where(
                standing,
                lambda p: 14.0 < p.x < 22.0 and -50.0 < p.y < -36.0 and 18.0 < p.z < 32.0,
            )
            standing.hide_render = True
            originals.append(decal)
            ruins.append(standing)
    kit.facade_originals = originals
    kit.facade_ruins = ruins
    print("facade bites", len(ruins), flush=True)


def _ruin_sources():
    path = Path("/opt/cursor/asset-cache/private/sketchfab/city_blocks/ruined_city_free_5.glb")
    if not path.exists():
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    fresh = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    bpy.context.view_layer.update()
    kept = []
    for obj in fresh:
        obj.hide_render = True
        wide = min(obj.dimensions.x, obj.dimensions.y)
        if obj.name.startswith("Plane"):
            continue
        if obj.dimensions.z >= 4.0 and wide > 2.0:
            kept.append(obj)
    kept.sort(key=lambda obj: obj.dimensions.z, reverse=True)
    print("ruin sources", len(kept), flush=True)
    return kept


def _place_ruin(coll, src, loc, yaw, height, rot_y=0.0):
    copy = src.copy()
    copy.data = src.data
    coll.objects.link(copy)
    copy.parent = None
    copy.hide_render = False
    copy.rotation_mode = "XYZ"
    copy.rotation_euler = (0.0, rot_y, yaw)
    factor = float(height) / max(src.dimensions.z, 0.01)
    copy.scale = (factor, factor, factor)
    copy.location = Vector(loc)
    return copy


def _grow_vines(kit):
    """Ivy on the street face of the left block. Hidden until the years pass."""
    from engine import found_assets

    blocks = [
        obj for obj in getattr(kit, "tall_blocks", ())
        if obj.get("mid_y", 0.0) < 0.0
    ]
    if not blocks:
        return
    bpy.context.view_layer.update()
    plants = kit.collection("Plants")
    grown = []
    for block in blocks:
        xs = [(block.matrix_world @ Vector(corner)).x for corner in block.bound_box]
        face_x = (max(xs) - 0.3) if block.get("mid_x", 0.0) < 0.0 else (min(xs) + 0.3)
        for seed_y, seed_z in ((-48.0, 2.2), (-40.0, 8.0), (-34.0, 14.0), (-28.0, 20.0)):
            grown.extend(found_assets.grow_ivy(block, (face_x, seed_y, seed_z), length=9.0) or [])
    for obj in grown:
        try:
            plants.objects.link(obj)
        except RuntimeError:
            pass
        kit.add(obj, "year_age", sink=False)
    print("ivy", len(grown), flush=True)


def _crowd(kit):
    """Walkers on both sidewalks, and hub sedans plus the Miura in the avenue."""
    from engine import private_assets
    from engine.scenes import _bike, _traffic, _walker

    life = kit.collection("Life")
    z = 1.35
    spots = []
    sidewalks = ((-4.6, 3.5), (-6.4, 4.0), (3.8, 3.5), (5.6, 4.0))
    for x, step in sidewalks:
        direction = 1.0 if x < 0 else -1.0
        y0 = -58.0
        index = 0
        while y0 < -18.0:
            spots.append((x + (0.35 if index % 2 else 0.0), y0, direction))
            y0 += step
            index += 1
    for index, (x, y0, direction) in enumerate(spots):
        _walker(kit, life, [(x, y0, z), (x, y0 + 7.0 * direction, z)], 1.2, index * 1.1)
    for index, (x, y0) in enumerate(((-2.2, -50.0), (1.8, -42.0), (-1.2, -34.0), (2.2, -26.0), (0.4, -22.0))):
        _bike(kit, life, [(x, y0, z), (x, y0 + 10.0, z)], index * 2.0)
    # Hub sedans and the Miura. Nose yaw is from +X, so pi/2 drives away up the avenue.
    road_z = 1.28
    moving = (
        ((-1.0, -50.0, road_z), (-1.0, -22.0, road_z), 0, 7.0),
        ((1.4, -24.0, road_z), (1.4, -48.0, road_z), 1, 8.0),
        ((0.2, -44.0, road_z), (0.2, -20.0, road_z), 2, 6.5),
    )
    for index, (start, end, car_index, speed) in enumerate(moving):
        _traffic(kit, life, [start, end], car_index, speed, index * 6.0, coast=5.0)
    parked = ((-2.2, -42.0, math.pi / 2.0), (2.2, -36.0, -math.pi / 2.0), (-2.4, -30.0, math.pi / 2.0))
    for index, (x, y, yaw) in enumerate(parked):
        loc = (x, y, road_z)
        built = private_assets.place_avenue_car(life, loc, yaw, index=4 + index)
        if built is None:
            continue
        kit.add(built, "car", path_from=loc, path_to=loc, index=4 + index, sink=False)
    miura_loc = (-0.4, -54.0, road_z)
    miura = private_assets.place_hero_sports(life, miura_loc, -math.pi / 2.0)
    if miura is not None:
        kit.add(miura, "car", path_from=miura_loc, path_to=miura_loc, index=11, sink=False)


def _ground_patch(coll, mat, width, length):
    """A small cover whose origin is its centre, so a tilt stays on the street."""
    mesh = bpy.data.meshes.new("cover")
    bm = bmesh.new()
    hw, hl = width * 0.5, length * 0.5
    verts = [bm.verts.new(co) for co in ((-hw, -hl, 0.0), (hw, -hl, 0.0), (hw, hl, 0.0), (-hw, hl, 0.0))]
    face = bm.faces.new(verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for loop in face.loops:
        co = loop.vert.co
        loop[uv].uv = ((co.x + hw) / 2.0, (co.y + hl) / 2.0)
    bm.to_mesh(mesh)
    bm.free()
    if mat is not None:
        mesh.materials.append(mat)
    obj = bpy.data.objects.new("cover", mesh)
    coll.objects.link(obj)
    return obj


def _puddle(coll):
    mat = bpy.data.materials.get("StreetPuddle")
    if mat is None:
        mat = bpy.data.materials.new("StreetPuddle")
        mat.use_nodes = True
        bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (0.04, 0.05, 0.045, 1)
        bsdf.inputs["Roughness"].default_value = 0.06
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.8
    return _ground_patch(coll, mat, 1.0, 1.0)


def _heave(x, y):
    """Heaved soil the grid can actually resolve. Peaks stay under a third of a metre."""
    return (
        0.55 * math.sin(x * 0.85) * math.cos(y * 0.62)
        + 0.35 * math.sin(x * 1.9 + y * 1.4)
    )


def _soil_edge(y, side):
    """A wavy curb, not a straight rectangle."""
    wobble = 1.5 * math.sin(y * 0.27) + 0.7 * math.sin(y * 0.73 + side)
    return side * (4.6 + wobble)


def _bury_material():
    """Soil and grass, with cracked asphalt showing through in patches."""
    mat = bpy.data.materials.new("BuriedRoad")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    coord = tree.nodes.new("ShaderNodeTexCoord")
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    tree.links.new(coord.outputs["UV"], mapping.inputs["Vector"])

    root = Path("/opt/cursor/asset-cache/cc0/textures/ground4k")

    def image_node(filename, color=True):
        path = root / filename
        node = tree.nodes.new("ShaderNodeTexImage")
        if path.exists():
            node.image = bpy.data.images.load(str(path), check_existing=True)
            if not color:
                node.image.colorspace_settings.name = "Non-Color"
        tree.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    grass = image_node("aerial_grass_rock_diff_4k.jpg")
    leaves = image_node("leaves_forest_ground_diff_4k.jpg")
    mud = image_node("brown_mud_leaves_01_diff_4k.jpg")
    speckle = tree.nodes.new("ShaderNodeTexNoise")
    speckle.inputs["Scale"].default_value = 18.0
    speckle.inputs["Detail"].default_value = 10.0
    tree.links.new(coord.outputs["Object"], speckle.inputs["Vector"])
    floor = tree.nodes.new("ShaderNodeMixRGB")
    tree.links.new(speckle.outputs["Fac"], floor.inputs["Fac"])
    tree.links.new(grass.outputs["Color"], floor.inputs["Color1"])
    tree.links.new(leaves.outputs["Color"], floor.inputs["Color2"])
    rich = tree.nodes.new("ShaderNodeMixRGB")
    rich.blend_type = "MULTIPLY"
    rich.inputs["Fac"].default_value = 0.55
    rich.inputs["Color2"].default_value = (0.72, 0.95, 0.55, 1)
    tree.links.new(floor.outputs["Color"], rich.inputs["Color1"])
    mossy = tree.nodes.new("ShaderNodeMixRGB")
    mossy.inputs["Fac"].default_value = 0.28
    tree.links.new(rich.outputs["Color"], mossy.inputs["Color1"])
    tree.links.new(mud.outputs["Color"], mossy.inputs["Color2"])
    tree.links.new(mossy.outputs["Color"], bsdf.inputs["Base Color"])
    normal = image_node("leaves_forest_ground_nor_gl_4k.jpg", color=False)
    nmap = tree.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 1.4
    tree.links.new(normal.outputs["Color"], nmap.inputs["Color"])
    tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.86
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _uneven_ground(kit):
    """One heaved soil sheet. Its outline wobbles, so no tile edge shows."""
    coll = kit.collection("Terrain")
    mesh = bpy.data.meshes.new("buried_avenue")
    bm = bmesh.new()
    y0, y1 = -72.0, -16.0
    step_y, step_x = 0.22, 0.22
    rows = []
    y = y0
    while y <= y1:
        left, right = -7.2, 7.2
        row = []
        x = left
        while x <= right:
            heave = _heave(x, y)
            edge = min(x - left, right - x)
            fade = min(1.0, edge / 1.1)
            row.append(bm.verts.new((x, y, 1.22 + 0.12 * _heave(x, y))))
            x += step_x
        rows.append(row)
        y += step_y
    uv = bm.loops.layers.uv.new("UVMap")
    for row_i, row in enumerate(rows[:-1]):
        nxt = rows[row_i + 1]
        count = min(len(row), len(nxt)) - 1
        for i in range(max(count, 0)):
            face = bm.faces.new((row[i], row[i + 1], nxt[i + 1], nxt[i]))
            for loop in face.loops:
                co = loop.vert.co
                loop[uv].uv = (co.x * 0.5, co.y * 0.5)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(_bury_material())
    obj = bpy.data.objects.new("buried_avenue", mesh)
    coll.objects.link(obj)
    disp_path = Path("/opt/cursor/asset-cache/cc0/textures/ground4k/leaves_forest_ground_disp_4k.jpg")
    if disp_path.exists():
        tex = bpy.data.textures.new("SoilDisp", type="IMAGE")
        tex.image = bpy.data.images.load(str(disp_path), check_existing=True)
        tex.image.colorspace_settings.name = "Non-Color"
        mod = obj.modifiers.new("Heave", "DISPLACE")
        mod.texture = tex
        mod.texture_coords = "UV"
        mod.strength = 0.16
        mod.mid_level = 0.5
    kit.add(obj, "groundwear", sink=False)
    return obj


def _asphalt_slabs(kit):
    """Small cracked-asphalt pieces sitting in the soil, not one dark blob."""
    from engine import found_assets

    coll = kit.collection("Terrain")
    mat = found_assets.pbr_material("AsphaltSlab", "road_damaged", uv=1.6)
    if mat is None:
        return
    rng = random.Random(4)
    for i in range(11):
        slab = _ground_patch(coll, mat, rng.uniform(1.4, 2.8), rng.uniform(1.1, 2.4))
        x = rng.choice((-1.0, 1.0)) * rng.uniform(1.2, 4.8)
        y = rng.uniform(-46.0, -26.0)
        slab.location = (x, y, 1.22 + 0.25 * _heave(x, y))
        slab.rotation_euler = (rng.uniform(-0.12, 0.14), rng.uniform(-0.1, 0.1), rng.random() * 6.0)
        kit.add(slab, "groundwear", sink=False)


def _scatter_plants(kit):
    """Geometry Nodes scatter of real grass and ferns on the sidewalk lines."""
    from engine import found_assets

    plants = kit.collection("Plants")
    protos = bpy.data.collections.new("Year500Clumps")
    bpy.context.scene.collection.children.link(protos)
    for slug, height in (
        ("grass_medium_01", 1.2),
        ("grass_medium_02", 1.5),
        ("grass_bermuda_01", 0.9),
        ("fern_02", 1.3),
        ("shrub_01", 1.4),
    ):
        obj = found_assets.place(plants, slug, (0.0, 0.0, -80.0), 0.0, height, name=f"proto_{slug}")
        if obj is None:
            continue
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        protos.objects.link(obj)
        obj.hide_render = True
    if not protos.objects:
        print("scatter empty", flush=True)
        return
    mesh = bpy.data.meshes.new("edge_scatter")
    bm = bmesh.new()
    for x0, x1 in ((-9.0, -4.5), (4.5, 9.0)):
        y = -52.0
        row_a = []
        while y <= -20.0:
            row_b = [bm.verts.new((x0, y, 1.3)), bm.verts.new((x1, y, 1.3))]
            if row_a:
                bm.faces.new((row_a[0], row_a[1], row_b[1], row_b[0]))
            row_a = row_b
            y += 1.2
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("edge_scatter", mesh)
    plants.objects.link(obj)
    tree = bpy.data.node_groups.new("EdgeScatter", "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = tree.nodes
    links = tree.links
    group_in = nodes.new("NodeGroupInput")
    group_out = nodes.new("NodeGroupOutput")
    distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute.inputs["Density"].default_value = 2.4
    collect = nodes.new("GeometryNodeCollectionInfo")
    collect.inputs["Collection"].default_value = protos
    collect.inputs["Separate Children"].default_value = True
    collect.inputs["Reset Children"].default_value = True
    collect.transform_space = "RELATIVE"
    pick = nodes.new("FunctionNodeRandomValue")
    pick.data_type = "INT"
    pick.inputs["Min"].default_value = 0
    pick.inputs["Max"].default_value = max(len(protos.objects), 1)
    scale = nodes.new("FunctionNodeRandomValue")
    scale.data_type = "FLOAT_VECTOR"
    scale.inputs["Min"].default_value = (0.75, 0.75, 0.7)
    scale.inputs["Max"].default_value = (1.25, 1.25, 1.45)
    spin = nodes.new("FunctionNodeRandomValue")
    spin.data_type = "FLOAT_VECTOR"
    spin.inputs["Max"].default_value = (0.0, 0.0, 6.28)
    inst = nodes.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True
    links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
    links.new(distribute.outputs["Points"], inst.inputs["Points"])
    links.new(collect.outputs["Instances"], inst.inputs["Instance"])
    links.new(pick.outputs["Value"], inst.inputs["Instance Index"])
    links.new(spin.outputs["Value"], inst.inputs["Rotation"])
    links.new(scale.outputs["Value"], inst.inputs["Scale"])
    links.new(inst.outputs["Instances"], group_out.inputs["Geometry"])
    mod = obj.modifiers.new("Scatter", "NODES")
    mod.node_group = tree
    kit.plant_scatter = obj
    obj.hide_render = True
    print("scatter protos", len(protos.objects), flush=True)


def _ground_cover(kit):
    """Year 500 soil. Hidden on day 1, so the approved street is unchanged."""
    _uneven_ground(kit)
    _asphalt_slabs(kit)
    _scatter_plants(kit)


def _fracture_host(obj, limit):
    import addon_utils

    try:
        addon_utils.enable("bl_ext.user_default.cell_fracture", default_set=False, persistent=False)
    except Exception as exc:
        print("fracture addon", exc, flush=True)
        return []
    if not hasattr(bpy.ops.object, "add_fracture_cell_objects"):
        print("fracture op missing", flush=True)
        return []
    from engine.decay_vfx import _cell_fracture

    return _cell_fracture(obj, limit)


def _drop_group(empty, members, ground_z):
    bpy.context.view_layer.update()
    zs = []
    for obj in members:
        for corner in obj.bound_box:
            zs.append((obj.matrix_world @ Vector(corner)).z)
    if zs:
        empty.location.z += ground_z - min(zs)


def _lay_fractured_tower(kit, src):
    """Cell-fracture one ruined building and tip the pieces across the avenue."""
    coll = kit.collection("City")
    host = src.copy()
    host.data = src.data.copy()
    coll.objects.link(host)
    host.parent = None
    host.hide_render = False
    host.rotation_mode = "XYZ"
    host.rotation_euler = (0.0, 0.0, 0.4)
    factor = 18.0 / max(src.dimensions.z, 0.01)
    host.scale = (factor, factor, factor)
    host.location = (0.0, -35.0, 1.3)
    bpy.context.view_layer.update()
    shards = _fracture_host(host, 14) if len(host.data.vertices) < 80000 else []
    members = shards or [host]
    if shards:
        host.hide_render = True
    bpy.context.view_layer.update()
    # Bake the world transform, then tip the chunks onto their side in the mesh
    # itself so a later parent or rotation mode cannot stand them back up.
    for shard in members:
        shard.parent = None
        baked = shard.data.copy()
        baked.transform(shard.matrix_world.copy())
        shard.data = baked
        shard.matrix_world = Matrix.Identity(4)
        shard.hide_render = False
    xs, ys, zs = [], [], []
    for shard in members:
        for vert in shard.data.vertices:
            xs.append(vert.co.x)
            ys.append(vert.co.y)
            zs.append(vert.co.z)
    center = Vector(((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, (min(zs) + max(zs)) * 0.5))
    tip = Matrix.Translation(center) @ Matrix.Rotation(math.pi / 2.0, 4, "Y") @ Matrix.Translation(-center)
    for shard in members:
        shard.data.transform(tip)
    xs, ys, zs = [], [], []
    for shard in members:
        for vert in shard.data.vertices:
            xs.append(vert.co.x)
            ys.append(vert.co.y)
            zs.append(vert.co.z)
    center = Vector(((min(xs) + max(xs)) * 0.5, (min(ys) + max(ys)) * 0.5, (min(zs) + max(zs)) * 0.5))
    diagonal = Matrix.Translation(center) @ Matrix.Rotation(0.62, 4, "Z") @ Matrix.Translation(-center)
    for shard in members:
        shard.data.transform(diagonal)
    xs, ys, zs = [], [], []
    for shard in members:
        for vert in shard.data.vertices:
            xs.append(vert.co.x)
            ys.append(vert.co.y)
            zs.append(vert.co.z)
    height = max(zs) - min(zs)
    squash = min(1.0, 8.0 / max(height, 0.01))
    scale_z = Matrix.Identity(4)
    scale_z[2][2] = squash
    bottom = min(zs)
    squat = Matrix.Translation((0.0, 0.0, bottom)) @ scale_z @ Matrix.Translation((0.0, 0.0, -bottom))
    shift = Vector((-(min(xs) + max(xs)) * 0.5, -35.0 - (min(ys) + max(ys)) * 0.5, 1.32 - bottom))
    for shard in members:
        shard.data.transform(Matrix.Translation(shift) @ squat)
    bpy.context.view_layer.update()
    xs, zs2 = [], []
    for shard in members:
        for corner in shard.bound_box:
            point = shard.matrix_world @ Vector(corner)
            xs.append(point.x)
            zs2.append(point.z)
    if xs:
        print("fallen span x", round(max(xs) - min(xs), 1), "z", round(max(zs2) - min(zs2), 1), flush=True)
    kit.fallen_shards = list(members)
    for shard in members:
        kit.add(shard, "fracture500", sink=False)
    print("fallen shards", len(members), flush=True)
    return members[0]


def _year500_set(kit):
    """The same street, with one fractured building lying across it and a taller forest."""
    coll = kit.collection("City")
    plants = kit.collection("Plants")
    made = 0
    tree_paths = (
        Path("/opt/cursor/asset-cache/cc0/polyhaven/island_tree_02/island_tree_02_1k.gltf"),
        Path("/opt/cursor/asset-cache/cc0/polyhaven/tree_small_02/tree_small_02_1k.gltf"),
    )
    loaded = []
    for path in tree_paths:
        if path.exists():
            mesh = _visual_mesh(path)
            if mesh is not None:
                loaded.append((mesh, max(_size(mesh)[2], 0.2)))
    rng = random.Random(3)
    # Sidewalk lines, at least 15 m from the camera at y=-66, and off the axis.
    spots = []
    for x0 in (-7.0, 7.4):
        for y in range(-48, -22, 8):
            spots.append((x0 + rng.uniform(-0.3, 0.3), float(y)))
    for x, y in ((-6.8, -39.0), (7.2, -32.0)):
        spots.append((x, y))
    for i, (x, y) in enumerate(spots):
        if not loaded:
            break
        mesh, native = loaded[0]
        height = rng.uniform(11.0, 17.0)
        tree = _spawn_mesh(
            plants, mesh,
            (x, y, 1.25),
            rng.random() * 6.2, height / native, "broadleaf",
        )
        kit.add(tree, "swallow", sink=False)
    # Dark concrete and wood only. The white scan boulders stay out.
    for filename, size in (("lowpoly_concrete_debris.glb", 1.6), ("wood_planks_debris.glb", 1.3), ("asphalt_02.glb", 1.8)):
        path = Path("/opt/cursor/asset-cache/private/debris") / filename
        mesh = _visual_mesh(path) if path.exists() else None
        if mesh is None:
            continue
        native = max(_size(mesh))
        for i in range(4):
            side = -1.0 if i % 2 == 0 else 1.0
            pile = _spawn_mesh(
                coll, mesh,
                (side * rng.uniform(2.2, 6.5), rng.uniform(-46.0, -24.0), 1.25),
                rng.random() * 6.0, size / max(native, 0.2), "rubble_pile",
            )
            kit.add(pile, "rubble_hill", sink=False)
    print("year500 pieces", made, flush=True)


def build(kit, mats, rng):
    """One downloaded intersection. The handmade river city is not touched."""
    del mats, rng
    kit.kind = "ready_city"
    kit.water = None
    _import_intersection(kit)
    _grow_vines(kit)
    _crowd(kit)
    _ground_cover(kit)
    _year500_set(kit)
    fog, density = _fog(kit.collection("Weather"))
    fog.location = (0.0, -44.0, 6.0)
    fog.scale = (22.0, 48.0, 9.0)
    kit.street_fog = fog
    kit.fog_density = density
    _frame_camera(kit)
    print("intersection items", len(kit.items), flush=True)
    return kit


def _frame_camera(kit):
    """Eye height, in the street, looking along it. Same pose for every year."""
    del kit
    cam = bpy.context.scene.camera
    if cam is None:
        return
    cam.lock_location = (False, False, False)
    cam.lock_rotation = (False, False, False)
    cam.location = CAM_LOC
    _aim(cam, CAM_TARGET)
    cam.data.lens = LENS
    cam.data.shift_x = 0.0
    cam.data.shift_y = SHIFT_Y
    cam.data.clip_start = 0.08
    cam.data.clip_end = 800.0


def _sun_down_the_street(sun, collapse):
    """Low sun down the avenue. Year 500 looks back toward it so the fog throws shafts."""
    low = 1.0 if collapse > 0.5 else 0.0
    direction = Vector((0.15, -0.78, -0.28 - 0.22 * low))
    sun.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    sun.data.energy = 5.5 if low < 0.5 else 7.5
    sun.data.color = (1.0, 0.93, 0.82) if low < 0.5 else (1.0, 0.72, 0.42)
    sun.data.angle = 0.03


def _lay_in_street(item, sign):
    """Rotate a building about world Y so it lies across the avenue."""
    origin = Vector(item.base_loc)
    base = item.base_rot.to_matrix().to_4x4()
    base.translation = origin
    rot = Matrix.Rotation(1.52 * sign, 4, "Y")
    new = Matrix.Translation(origin) @ rot @ Matrix.Translation(-origin) @ base
    loc, quat, _scale = new.decompose()
    item.obj.location = loc
    item.obj.rotation_mode = "XYZ"
    item.obj.rotation_euler = quat.to_euler("XYZ")
    # The height falls across the street. Squash the other two axes so the tower is a slab, not a wall.
    item.obj.scale = (item.base_scale.x * 0.16, item.base_scale.y * 0.16, item.base_scale.z)


def _set_ruin(amount):
    for material in bpy.data.materials:
        tree = material.node_tree
        if tree is None:
            continue
        node = tree.nodes.get("Ruin")
        if node is not None and node.type == "VALUE":
            node.outputs[0].default_value = float(amount)


def _push_decay(amount, forest):
    for material in bpy.data.materials:
        tree = material.node_tree
        if tree is None:
            continue
        for name, value in (("Decay", amount), ("Forest", forest)):
            node = tree.nodes.get(name)
            if node is not None and node.type == "VALUE":
                node.outputs[0].default_value = float(value)


def _cloudy_sky(kit):
    """A 4K partly-cloudy sky, rotated so the cumulus sit in the frame."""
    hdr = Path("/opt/cursor/asset-cache/cc0/hdri/kloofendal_48d_partly_cloudy_puresky_4k.hdr")
    if not hdr.exists():
        return
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("Sky")
        bpy.context.scene.world = world
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputWorld")
    bg = tree.nodes.new("ShaderNodeBackground")
    env = tree.nodes.new("ShaderNodeTexEnvironment")
    coord = tree.nodes.new("ShaderNodeTexCoord")
    mapping = tree.nodes.new("ShaderNodeMapping")
    image = bpy.data.images.load(str(hdr), check_existing=True)
    try:
        image.colorspace_settings.name = "Linear Rec.709"
    except TypeError:
        image.colorspace_settings.name = "Linear"
    env.image = image
    env.projection = "EQUIRECTANGULAR"
    env.interpolation = "Linear"
    # Pitch brings the sharp cloud band down into the street view. The mirrored
    # lower half of a puresky HDR stays below the buildings.
    mapping.inputs["Rotation"].default_value = (0.2, 0.0, 0.2)
    bg.inputs[1].default_value = 1.0
    tree.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    tree.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    tree.links.new(env.outputs["Color"], bg.inputs[0])
    tree.links.new(bg.outputs["Background"], out.inputs["Surface"])
    kit.world_bg = bg
    kit.sky_mix = None
    kit.sky_zenith = None
    kit.sky_horizon = None


def _break_glass():
    for mat in bpy.data.materials:
        low = mat.name.lower()
        if not any(token in low for token in ("window", "glass", "blind")):
            continue
        if mat.node_tree is None:
            continue
        bsdf = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        color = bsdf.inputs.get("Base Color")
        if color is not None and color.is_linked:
            mat.node_tree.links.remove(color.links[0])
        if color is not None:
            color.default_value = (0.02, 0.025, 0.03, 1)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.72
        for name in ("Transmission Weight", "Transmission"):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = 0.05


def _shorten_block(obj, factor):
    """Drop the upper floors. The foot of the mesh stays where it was."""
    floor_z = float(obj.get("floor_z", 0.0))
    obj.scale.z = factor
    obj.location.z = floor_z * (1.0 - factor)


def drive(kit, ch):
    """The same facades age. A ruin shell appears only where one block has fallen."""
    collapse = float(ch.get("collapse", 0.0))
    fallen = collapse >= 0.85
    _frame_camera(kit)
    _cloudy_sky(kit)
    if kit.volume is not None:
        kit.volume.hide_render = True
    street = set(getattr(kit, "facade_originals", ()) or ())
    for obj in getattr(kit, "tall_blocks", ()) or ():
        obj.location.z = 0.0
        obj.scale.z = 1.0
        if obj in street:
            obj.hide_render = fallen
            continue
        obj.hide_render = False
    for decal in getattr(kit, "window_decals", ()) or ():
        decal.hide_render = False
        decal.location.z = 0.0
        decal.scale.z = 1.0
    for obj in getattr(kit, "facade_originals", ()) or ():
        obj.hide_render = fallen
    for obj in getattr(kit, "facade_ruins", ()) or ():
        obj.hide_render = not fallen
    scatter = getattr(kit, "plant_scatter", None)
    if scatter is not None:
        scatter.hide_render = not fallen
    if fallen:
        _break_glass()
        _push_decay(1.0, 1.0)
        _set_ruin(1.0)
    else:
        _push_decay(0.0, 0.0)
        _set_ruin(0.0)
    for item in kit.items:
        if item.role in {"shell", "swallow", "rubble_hill", "rubble"}:
            _hide_tree(item.obj, not fallen)
    for shard in getattr(kit, "fallen_shards", ()) or ():
        shard.hide_render = not fallen
    node = getattr(kit, "fog_density", None)
    if node is not None:
        node.outputs[0].default_value = 0.0035 if fallen else 0.0
    fog_mat = bpy.data.materials.get("StreetFog")
    if fog_mat is not None and fog_mat.node_tree is not None:
        vol = next((n for n in fog_mat.node_tree.nodes if n.type == "VOLUME_PRINCIPLED"), None)
        if vol is not None:
            if "Anisotropy" in vol.inputs:
                vol.inputs["Anisotropy"].default_value = 0.84 if fallen else 0.62
            vol.inputs["Color"].default_value = (0.93, 0.92, 0.9, 1)
    sun = getattr(kit, "sun", None)
    if sun is not None:
        _sun_down_the_street(sun, 1.0 if fallen else 0.0)
        if fallen:
            sun.data.energy = 6.0
            sun.data.angle = 0.02
            sun.data.color = (1.0, 0.9, 0.76)
    scene = bpy.context.scene
    scene.view_settings.exposure = 0.42
    try:
        scene.view_settings.look = "AgX - Base Contrast"
    except TypeError:
        pass
