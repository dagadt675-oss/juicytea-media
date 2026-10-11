"""The vanish episode, built from downloaded city blocks.

The river, the suspension bridge, the park, the streets, and the locked
camera are the same shot as the handmade episode. The buildings are hub
blocks (Procedural City 3/4/6 and One WTC), tiled past every edge of that
frame. Year 100 keeps that skyline and breaks it. Year 500 collapses it
into shells, fracture shards, and forest. The handmade scene file is not
edited by this module.
"""

from __future__ import annotations

import random

import bmesh
import bpy
from mathutils import Euler, Vector

from engine import cc0_city, found_assets
from engine.city_layout import FAR_Z, RIVER_Y0, RIVER_Y1, ROAD_Z, river_contains
from engine.meshkit import smoother

PIECES = {"terrain", "city", "river", "bridge", "suburbs", "forest", "power", "subway"}
BLOCKS = ("procedural_city_6.glb", "procedural_city_3.glb", "procedural_city_4.glb")


def _hide_tree(obj, hide):
    obj.hide_render = hide
    for child in obj.children_recursive:
        child.hide_render = hide


def _bounds_z(obj):
    zs = []
    for item in (obj, *obj.children_recursive):
        if getattr(item, "type", "") != "MESH":
            continue
        for corner in item.bound_box:
            zs.append((item.matrix_world @ Vector(corner)).z)
    return zs


def _bury(obj, ground, bury):
    """Drop a mountain until its base is under the terrain."""
    bpy.context.view_layer.update()
    zs = _bounds_z(obj)
    if not zs:
        return
    obj.location.z += (float(ground) - float(bury)) - min(zs)


def _span_x(obj):
    xs = []
    for item in (obj, *obj.children_recursive):
        if getattr(item, "type", "") != "MESH":
            continue
        for corner in item.bound_box:
            xs.append((item.matrix_world @ Vector(corner)).x)
    if not xs:
        return 0.0
    return max(xs) - min(xs)


def _clone(src, name, dx):
    copy = src.copy()
    if src.data is not None:
        copy.data = src.data
    for holder in src.users_collection:
        holder.objects.link(copy)
    copy.name = name
    copy.location.x += dx
    return copy


def _continuous_range(kit):
    """Overlap the hub peaks into one range and sit every base in the plain."""
    peaks = [obj for obj in bpy.data.objects if obj.name.split(".")[0] in {"snow_peak", "three_peaks"}]
    clones = []
    for src in list(peaks):
        width = _span_x(src)
        if width < 50.0:
            continue
        step = width * 0.62
        for index, sign in enumerate((-1.0, 1.0)):
            clones.append(_clone(src, src.name.split(".")[0] + "_span", sign * step * (1.0 + 0.15 * index)))
    for obj in peaks + clones:
        _bury(obj, FAR_Z, 80.0)
    for obj in clones:
        kit.add(obj, "mountain", sink=False)
    for obj in bpy.data.objects:
        if obj.name.split(".")[0] == "gaea_range":
            _bury(obj, FAR_Z, 120.0)


def _retint_horizon(mats):
    """Grass and soil out to the range, so the far ground is not a flat void."""
    grass = found_assets.pbr_material("HorizonGrass", "grass_ground", uv=0.04) or mats.get("park")
    soil = found_assets.pbr_material("HorizonSoil", "leaves_forest_ground", uv=0.03) or mats.get("dirt")
    road = None
    try:
        from engine import private_assets

        road = private_assets.road_asphalt_material()
    except Exception:
        road = None
    road = road or mats.get("road")
    for name, mat in (
        ("city_ground", grass),
        ("range_plain", soil),
        ("bedrock", soil),
        ("city_floor", road),
        ("near_shoulder", road),
    ):
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH" or mat is None:
            continue
        obj.data.materials.clear()
        obj.data.materials.append(mat)


def _on_water_or_deck(x, y):
    if river_contains(x, y):
        return True
    if RIVER_Y0 - 8.0 < y < RIVER_Y1 + 8.0 and abs(x) < 28.0:
        return True
    return False


def _extend_blocks(kit):
    """Hub blocks past the left, right, and near edges of the locked frame."""
    from engine import private_assets

    coll = kit.collection("City")
    spots = []
    # The locked camera's bottom edge lands just south of the avenue.
    # Blocks here cover the ground slab so the frame is streets and roofs.
    for x in (-150.0, -95.0, -40.0, 15.0, 70.0, 125.0, 180.0):
        for y, height in ((-8.0, 12.0), (-24.0, 16.0)):
            spots.append((x, y, ROAD_Z, height))
    for x in (-250.0, -180.0, 180.0, 250.0, 330.0):
        for y, height in ((-20.0, 16.0), (-55.0, 20.0)):
            spots.append((x, y, ROAD_Z, height))
    for x in (-280.0, -210.0, 200.0, 280.0, 360.0):
        for y, height in ((190.0, 42.0), (270.0, 56.0), (360.0, 48.0), (450.0, 40.0)):
            spots.append((x, y, FAR_Z, height))
    placed = 0
    for index, (x, y, z, height) in enumerate(spots):
        if _on_water_or_deck(x, y):
            continue
        block = private_assets.place_city_block(
            coll,
            BLOCKS[index % len(BLOCKS)],
            x,
            y,
            z,
            yaw=0.12 if index % 2 == 0 else 3.0,
            height=height,
            min_z=2.0,
            name="wing",
        )
        if block is None:
            continue
        kit.add(block, "building_base", sink=True, near_bank=y < 140.0, topple=(index % 7 == 0))
        found_assets.stamp_object(block, "plaster")
        placed += 1
    return placed


def _ruin_skyline(kit):
    """Ruin shells large enough to fill the locked frame once the towers fail."""
    from engine.scenes import _ruin_piece

    coll = kit.collection("City")
    placed = 0
    spots = []
    for y in (176.0, 214.0, 268.0, 330.0):
        for x in (-120.0, -40.0, 40.0, 120.0):
            spots.append((x, y, FAR_Z, 26.0 + (abs(int(x + y)) % 4) * 6.0))
    for x, h in ((-48.0, 16.0), (-16.0, 18.0), (18.0, 15.0), (44.0, 17.0)):
        spots.append((x, 6.0, ROAD_Z, h))
    for index, (x, y, z, height) in enumerate(spots):
        if _on_water_or_deck(x, y):
            continue
        shell = _ruin_piece(coll, (x, y, z), (index % 6) * 0.45, height)
        if shell is None:
            continue
        kit.add(shell, "shell", sink=False)
        placed += 1
    return placed


def _forest(kit):
    """Street trees by year 100, and a dense swallow canopy at year 500."""
    plants = kit.collection("Plants")
    if not cc0_city.ready():
        return 0
    rng = random.Random(29)
    placed = 0
    for i in range(160):
        x = rng.uniform(-160.0, 180.0)
        y = rng.uniform(-110.0, 80.0)
        if _on_water_or_deck(x, y):
            continue
        if abs(y - 22.0) < 12.0 and abs(x) < 90.0:
            continue
        tree = cc0_city.place_tree(plants, x, y, ROAD_Z, rng.uniform(7.0, 14.0), "pine" if i % 3 == 0 else "round")
        if tree is None:
            continue
        kit.add(tree, "tree_canopy", future=True, delay=0.42, sink=False)
        placed += 1
    for i in range(320):
        x = rng.uniform(-220.0, 260.0)
        y = rng.uniform(155.0, 520.0)
        if _on_water_or_deck(x, y):
            continue
        kind = "pine" if i % 2 == 0 else "round"
        tree = cc0_city.place_tree(plants, x, y, FAR_Z, rng.uniform(8.0, 18.0), kind)
        if tree is None:
            continue
        kit.add(tree, "swallow", sink=False)
        placed += 1
    return placed


def _fog(coll):
    """Street-level volume. The locked camera sits above it."""
    mesh = bpy.data.meshes.new("street_fog")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("street_fog", mesh)
    coll.objects.link(obj)
    # Cube is 1 m, centered. Top is z = 14 so the towers stay above the mist.
    # A taller box at density 0.02 hid the city: the locked camera looks along the streets.
    obj.location = (10.0, 70.0, 7.0)
    obj.scale = (480.0, 360.0, 14.0)
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
    fall.inputs["From Max"].default_value = 12.0
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    fall.clamp = True
    tree.links.new(sep.outputs["Z"], fall.inputs["Value"])
    density = tree.nodes.new("ShaderNodeValue")
    density.name = "Fog"
    density.outputs[0].default_value = 0.003
    mul = tree.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    tree.links.new(density.outputs[0], mul.inputs[0])
    tree.links.new(fall.outputs["Result"], mul.inputs[1])
    tree.links.new(mul.outputs[0], vol.inputs["Density"])
    vol.inputs["Color"].default_value = (0.78, 0.80, 0.84, 1.0)
    vol.inputs["Anisotropy"].default_value = 0.45
    tree.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    mesh.materials.append(mat)
    return obj, density


def _prune(kit):
    """Drop off-camera fracture shards. The cache is large enough to OOM a still."""
    removed = 0
    for obj in list(bpy.data.objects):
        if getattr(obj, "type", "") != "MESH":
            continue
        era = obj.get("era")
        if era is None and not obj.name.startswith("era"):
            continue
        loc = obj.matrix_world.translation
        huge = max(obj.dimensions) > 90.0
        far = not (-200.0 <= loc.x <= 260.0 and -40.0 <= loc.y <= 460.0)
        if not huge and not far:
            continue
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        removed += 1
    alive = set(bpy.data.objects)
    kit.items[:] = [item for item in kit.items if getattr(item, "obj", None) in alive]
    print("pruned", removed, "items", len(kit.items), flush=True)
    return removed


def build(kit, mats, rng):
    """Full locked-camera city. Buildings come from the hub, not from boxes."""
    del rng
    from engine.scenes import build_river_city

    build_river_city(kit, mats, random.Random(11), PIECES)
    kit.kind = "ready_city"
    wings = _extend_blocks(kit)
    ruins = _ruin_skyline(kit)
    trees = _forest(kit)
    _continuous_range(kit)
    _retint_horizon(mats)
    fog, density = _fog(kit.collection("Weather"))
    kit.street_fog = fog
    kit.fog_density = density
    print("ready city wings", wings, "ruin shells", ruins, "trees", trees, flush=True)
    _prune(kit)
    return kit


def drive(kit, ch):
    """Keep a ruined skyline in frame, and hold a thin street fog with a low sun."""
    collapse = float(ch.get("collapse", 0.0))
    if 0.45 <= collapse < 0.85:
        # The front skyline stays up as a broken city. Deeper blocks stay
        # hidden so the ruin shells read, and so the still fits in memory.
        for item in kit.items:
            if item.role != "building_base":
                continue
            if item.base_loc.y > 230.0:
                continue
            _hide_tree(item.obj, False)
    elif collapse >= 0.85:
        for item in kit.items:
            if item.role != "building_base":
                continue
            near = item.base_loc.y < 120.0
            topple = bool(item.extra.get("topple"))
            if not near and not topple:
                continue
            _hide_tree(item.obj, False)
            if near and not topple:
                item.obj.scale = (
                    item.base_scale.x,
                    item.base_scale.y,
                    item.base_scale.z * 0.32,
                )
    node = getattr(kit, "fog_density", None)
    if node is not None:
        # Street coefficient. 0.02 through the long view along the avenue was an
        # opaque wall. 0.012 over this 14 m mist is enough for shafts and still
        # leaves the towers readable.
        amount = 0.2 + 0.8 * smoother(0.30, 0.70, collapse)
        node.outputs[0].default_value = 0.012 * amount
    scene = bpy.context.scene
    scene.cycles.volume_bounces = 1
    scene.cycles.volume_max_steps = 64
    scene.cycles.volume_step_rate = 1.6
    sun = getattr(kit, "sun", None)
    if sun is None or collapse < 0.4:
        return
    drop = smoother(0.4, 0.8, collapse)
    sun.rotation_euler = Euler((1.05 + drop * 0.22, 0.05, 2.15))
    sun.data.energy = 7.0
    sun.data.color = (1.0, 0.84, 0.64)
    sun.data.angle = 0.02
