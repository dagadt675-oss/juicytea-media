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

# Building meshes stay outside this half-width. The camera sits on x=0.
CORRIDOR = 7.6
CAM_LOC = (0.0, 1.4, 1.58)
CAM_TARGET = (0.1, 34.0, 5.2)
LENS = 28.0
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


def _roads(kit, end_y):
    """Downloaded asphalt. The avenue runs under the camera and does not stop in empty ground."""
    roads = kit.collection("Terrain")
    if not cc0_city.ready():
        return
    cc0_city.place_side_street(roads, 0.0, -48.0, end_y + 24.0, 0.02, width=12.0)
    # Side streets leave the avenue and run into the next row of blocks.
    y = -8.0
    while y < end_y:
        cc0_city.place_avenue(roads, y, 0.03, x0=-78.0, x1=-7.2, width=10.0)
        cc0_city.place_avenue(roads, y, 0.03, x0=7.2, x1=78.0, width=10.0)
        y += 52.0


def _life(kit):
    """People, bikes, and cars in the street. They leave with the vanish channel."""
    from engine.scenes import _bike, _traffic, _walker

    life = kit.collection("Life")
    z = 0.05
    # Near sidewalks first, so the opening frame has people at a readable size.
    for index, (x, y0, direction) in enumerate((
        (-5.2, 9.0, 1.0),
        (5.2, 11.0, 1.0),
        (-4.6, 18.0, -1.0),
        (4.8, 16.0, 1.0),
        (-5.4, 28.0, 1.0),
        (5.5, 32.0, -1.0),
        (-4.8, 48.0, 1.0),
        (4.6, 55.0, 1.0),
        (-5.1, 72.0, -1.0),
        (5.3, 80.0, 1.0),
    )):
        _walker(
            kit, life,
            [(x, y0, z), (x, y0 + 14.0 * direction, z)],
            1.25, index * 2.5, height=1.75,
        )
    for index, (x, y0) in enumerate(((-1.2, 34.0), (1.8, 52.0), (-2.0, 74.0))):
        _bike(kit, life, [(x, y0, z), (x, y0 + 24.0, z)], index * 3.0)
    lanes = (
        ((-1.7, 15.0, z), (-1.7, 160.0, z), 6, 9.0),
        ((2.0, 22.0, z), (2.0, 170.0, z), 7, 11.0),
        ((1.6, 120.0, z), (1.6, 8.0, z), 8, 8.0),
        ((-2.4, 90.0, z), (-2.4, 6.0, z), 9, 7.5),
        ((2.5, 48.0, z), (2.5, 150.0, z), 10, 10.0),
        ((-2.2, 140.0, z), (-2.2, 30.0, z), 11, 8.5),
    )
    for index, (start, end, car_index, speed) in enumerate(lanes):
        item = _traffic(kit, life, [start, end], car_index, speed, index * 5.0, coast=6.0)
        if item is not None:
            item.extra["hero"] = True


def _forest_and_weeds(kit):
    """Saplings by year 100. A forest stands in the street at year 500."""
    from engine.scenes import _plant

    plants = kit.collection("Plants")
    rng = random.Random(19)
    if cc0_city.ready():
        for i in range(28):
            x = rng.choice((-5.8, -4.2, 4.3, 5.9, rng.uniform(-2.2, 2.2)))
            y = rng.uniform(22.0, 150.0)
            kind = "pine" if i % 2 == 0 else "round"
            tree = cc0_city.place_tree(plants, x, y, 0.0, rng.uniform(5.5, 11.0), kind)
            if tree is None:
                continue
            kit.add(
                tree, "swallow", sink=False,
                leaf=(0.08, 0.32, 0.1, 1), autumn=(0.12, 0.3, 0.08, 1),
            )
        for i in range(14):
            x = rng.choice((-6.2, 6.3))
            y = 12.0 + i * 8.5
            tree = cc0_city.place_tree(plants, x, y, 0.0, rng.uniform(3.5, 6.5), "round")
            if tree is None:
                continue
            kit.add(
                tree, "tree_canopy", future=True, delay=0.62, sink=False,
                leaf=(0.1, 0.34, 0.12, 1), autumn=(0.16, 0.32, 0.1, 1),
            )
    for i in range(36):
        _plant(
            kit, plants,
            ("grass_medium_01", "fern_02", "shrub_01", "weed_plant_02", "moss_01")[i % 5],
            rng.uniform(-6.4, 6.4), rng.uniform(8.0, 120.0), 0.0,
            rng.uniform(0.45, 1.15), delay=0.34, yaw=rng.random() * 6.0,
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
    for i in range(10):
        side = -1.0 if i % 2 == 0 else 1.0
        shell = _ruin_piece(
            coll,
            (side * rng.uniform(3.2, 6.4), 12.0 + i * 11.0, 0.0),
            rng.random() * math.tau,
            rng.uniform(8.0, 14.0),
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
        if item.role != "building_base" or item.extra.get("rank") != "inner":
            continue
        if not (8.0 < item.base_loc.y < 90.0):
            continue
        for child in item.obj.children_recursive:
            if child.type != "MESH" or child.data is None:
                continue
            count = len(child.data.vertices)
            if 200 < count < 6000 and max(child.dimensions) < 40.0:
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


def build(kit, mats, rng):
    """Street canyon from hub blocks. No river, no bridge, no overview."""
    del mats, rng
    kit.kind = "ready_city"
    kit.water = None
    end_y = _place_blocks(kit)
    _roads(kit, end_y)
    _life(kit)
    _forest_and_weeds(kit)
    piles = _rubble(kit)
    shells = _shells(kit)
    fog, density = _fog(kit.collection("Weather"))
    kit.street_fog = fog
    kit.fog_density = density
    _fracture_a_few(kit)
    _frame_camera(kit)
    print("ready street rubble", piles, "shells", shells, "items", len(kit.items), flush=True)
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
    cam.data.clip_start = 0.08
    cam.data.clip_end = 800.0


def _sun_down_the_street(sun, collapse):
    """Low sun along the avenue so the street fog throws shafts."""
    drop = smoother(0.4, 0.85, collapse)
    direction = Vector((0.22, 0.86, -0.42 - 0.12 * drop))
    sun.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    sun.data.energy = 8.0
    sun.data.color = (1.0, 0.86, 0.68)
    sun.data.angle = 0.025


def drive(kit, ch):
    """Year 100 is still this street, broken. Year 500 is the same street fallen in."""
    collapse = float(ch.get("collapse", 0.0))
    heavy = 0.45 <= collapse < 0.85
    fallen = collapse >= 0.85
    _frame_camera(kit)
    if kit.volume is not None:
        kit.volume.hide_render = True
    for item in kit.items:
        if item.role == "building_base" and heavy:
            _hide_tree(item.obj, False)
            sign = 1.0 if item.base_loc.x < 0.0 else -1.0
            item.obj.location = item.base_loc.copy()
            item.obj.rotation_euler = Euler((0.04, 0.14 * sign, item.base_rot.z))
            item.obj.scale = (item.base_scale.x, item.base_scale.y, item.base_scale.z * 0.82)
        elif item.role == "building_base" and fallen:
            sign = 1.0 if item.base_loc.x < 0.0 else -1.0
            near = item.base_loc.y < 90.0
            bucket = int(abs(item.base_loc.y) + (0.0 if item.base_loc.x < 0.0 else 11.0)) % 4
            item.obj.location = item.base_loc.copy()
            # The two walls beside the camera stay, as broken stumps. Further blocks can fall away.
            if near or bucket != 0:
                _hide_tree(item.obj, False)
                lean = 0.55 if bucket == 1 else 0.22
                stump = 0.46 if near else 0.32
                item.obj.rotation_euler = Euler((0.05, lean * sign, item.base_rot.z))
                item.obj.scale = (item.base_scale.x, item.base_scale.y, item.base_scale.z * stump)
            else:
                _hide_tree(item.obj, True)
        elif item.role == "shell":
            _hide_tree(item.obj, not fallen)
        elif item.role == "rubble":
            _hide_tree(item.obj, collapse < 0.32)
        elif item.role == "rubble_hill":
            _hide_tree(item.obj, not fallen)
        elif item.role == "swallow" and heavy:
            item.obj.hide_render = True
    node = getattr(kit, "fog_density", None)
    if node is not None:
        amount = 0.35 + 0.65 * smoother(0.35, 0.9, collapse)
        node.outputs[0].default_value = 0.007 * amount
    scene = bpy.context.scene
    scene.cycles.volume_bounces = 1
    scene.cycles.volume_max_steps = 64
    scene.cycles.volume_step_rate = 1.6
    sun = getattr(kit, "sun", None)
    if sun is not None:
        _sun_down_the_street(sun, collapse)
