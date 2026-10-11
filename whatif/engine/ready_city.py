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
from pathlib import Path

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


def _hide_old_peaks():
    """The low-poly cone and the puff of snow stay out of this shot."""
    tokens = {"snow_peak", "three_peaks", "gaea_range", "snow_peak_span", "three_peaks_span"}
    for obj in bpy.data.objects:
        if obj.name.split(".")[0] in tokens:
            obj.hide_render = True
            for child in obj.children_recursive:
                child.hide_render = True


def _import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


def _decimate(obj, ratio):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _photoreal_range(kit):
    """Poly Haven mountainside, repeated into one hazy range behind the skyline."""
    _hide_old_peaks()
    path = Path("/opt/cursor/asset-cache/private/found_plane/mountainside/mountainside_2k.gltf")
    if not path.exists():
        return 0
    fresh = _import_gltf(path)
    meshes = [obj for obj in fresh if obj.type == "MESH"]
    if not meshes:
        return 0
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    src = bpy.context.view_layer.objects.active
    coll = kit.collection("Horizon")
    for holder in list(src.users_collection):
        holder.objects.unlink(src)
    coll.objects.link(src)
    # The scan imports about 10 m across. Scale it into a kilometre-wide range.
    # About 10 m native. This scale makes a ridge a few hundred metres tall,
    # sitting just behind the far bank instead of a cliff in the sky.
    src.scale = (42.0, 70.0, 36.0)
    bpy.context.view_layer.update()
    width = _span_x(src) or 1.0
    placed = 0
    for index, x in enumerate((-1.3, -0.55, 0.15, 0.85, 1.55)):
        obj = src if index == 0 else src.copy()
        if obj is not src:
            obj.data = src.data
            obj.scale = src.scale
            coll.objects.link(obj)
        obj.name = "range_side"
        obj.location = (480.0 + x * width * 0.62, 860.0 + (index % 2) * 70.0, FAR_Z)
        obj.rotation_euler.z = 0.15 + index * 0.35
        _bury(obj, FAR_Z, 50.0)
        kit.add(obj, "mountain", sink=False)
        placed += 1
    return placed


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
    for i in range(40):
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


def _murky_river(kit):
    """Keep a dark river. The pale foreground slab was covering its near edge."""
    floor = bpy.data.objects.get("city_floor")
    if floor is not None:
        floor.location.y = -78.0
    if kit.water is None:
        return
    mat = bpy.data.materials.new("MurkyRiver")
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.015, 0.045, 0.038, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.22
    for name in ("Transmission Weight", "Transmission"):
        if name in bsdf.inputs:
            bsdf.inputs[name].default_value = 0.25
            break
    obj = kit.water.obj
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def _overgrowth(kit, mats):
    """Earthy cover on the land only. The river polygon stays open."""
    from engine.scenes import _ground_sheet, _plant

    grass = found_assets.pbr_material("AgeGrass", "grass_ground", uv=0.18) or mats.get("park")
    mud = found_assets.pbr_material("AgeMud", "leaves_forest_ground", uv=0.22) or mats.get("dirt")
    coll = kit.collection("Terrain")
    south = _ground_sheet("south_earth", coll, (-10.0, -76.0, ROAD_Z + 0.12), (460.0, 160.0), mud, tile=6.0)
    north = _ground_sheet("north_earth", coll, (20.0, 280.0, FAR_Z + 0.08), (520.0, 240.0), grass, tile=7.0)
    kit.add(south, "year_green", sink=False)
    kit.add(north, "year_green", sink=False)
    plants = kit.collection("Plants")
    rng = random.Random(41)
    for i in range(180):
        x = rng.uniform(-160.0, 180.0)
        y = rng.choice((
            rng.uniform(-90.0, 70.0),
            rng.uniform(160.0, 420.0),
        ))
        if river_contains(x, y):
            continue
        _plant(
            kit, plants,
            ("grass_medium_01", "shrub_01", "fern_02", "moss_01", "weed_plant_02")[i % 5],
            x, y, ROAD_Z if y < 80.0 else FAR_Z,
            rng.uniform(0.6, 1.4), delay=0.36, yaw=rng.random() * 6.0,
        )


def _river_debris(kit):
    """Logs and reeds in the water, from year 100 on."""
    plants = kit.collection("Plants")
    if not cc0_city.ready():
        return
    rng = random.Random(17)
    for i, (x, y) in enumerate(((-30, 100), (-8, 118), (18, 108), (36, 132), (-18, 140), (6, 96))):
        tree = cc0_city.place_tree(plants, x, y, 0.15, rng.uniform(6.0, 11.0), "dead" if i % 2 == 0 else "pine")
        if tree is None:
            continue
        tree.rotation_euler.x = 1.35
        kit.add(tree, "river_age", sink=False)
    from engine.scenes import _plant
    for i, (x, y) in enumerate(((-22, 104), (-4, 112), (14, 124), (28, 136), (2, 148), (-36, 128))):
        _plant(
            kit, plants, "grass_medium_02" if i % 2 == 0 else "fern_02",
            x, y, 0.2, 1.3, delay=0.0, yaw=i, role="river_age",
        )


def _place_suspension(kit):
    """Hub suspension bridge: towers, cables, hangers, deck. Replaces the red gate."""
    import math

    from engine.city_layout import BRIDGE_YAW, FAR_BANK_S, NEAR_BANK_S, deck_point, deck_z

    path = Path(
        "/opt/cursor/asset-cache/private/blendkit/blendkit_private/"
        "ep_humans_disappeared/Bridge_4cd69f5a/Bridge_4cd69f5a.blend"
    )
    if not path.exists():
        return
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = list(src.objects)
    fresh = [obj for obj in dst.objects if obj is not None]
    coll = kit.collection("Bridge")
    for obj in fresh:
        for holder in list(obj.users_collection):
            holder.objects.unlink(obj)
        coll.objects.link(obj)
    root = next((obj for obj in fresh if obj.name == "Bridge" and obj.type == "EMPTY"), None)
    deck = next((obj for obj in fresh if obj.type == "MESH" and obj.name.startswith("Plane")), None)
    towers = [obj for obj in fresh if obj.type == "MESH" and obj.name.startswith("Cube")]
    if root is None or deck is None:
        return
    holder = bpy.data.objects.new("suspension", None)
    coll.objects.link(holder)
    bpy.context.view_layer.update()
    world = root.matrix_world.copy()
    root.parent = holder
    root.matrix_world = world
    near = deck_point(NEAR_BANK_S - 4.0)
    far = deck_point(FAR_BANK_S + 8.0)
    span = math.hypot(far[0] - near[0], far[1] - near[1])
    holder.scale = (span / 38.6, 16.0 / 0.9, 36.0 / 6.45)
    holder.rotation_euler.z = math.pi / 2.0 - BRIDGE_YAW
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for corner in deck.bound_box:
        point = deck.matrix_world @ Vector(corner)
        xs.append(point.x)
        ys.append(point.y)
        zs.append(point.z)
    mid = ((near[0] + far[0]) * 0.5, (near[1] + far[1]) * 0.5)
    holder.location.x += mid[0] - (min(xs) + max(xs)) * 0.5
    holder.location.y += mid[1] - (min(ys) + max(ys)) * 0.5
    holder.location.z += deck_z((NEAR_BANK_S + FAR_BANK_S) * 0.5) - min(zs)
    bpy.context.view_layer.update()
    kit.suspension = {
        "holder": holder,
        "deck": deck,
        "towers": towers,
        "deck_loc": deck.location.copy(),
        "deck_rot": deck.rotation_euler.copy(),
        "holder_loc": holder.location.copy(),
        "holder_rot": holder.rotation_euler.copy(),
        "tower_rot": [obj.rotation_euler.copy() for obj in towers],
    }
    print("suspension span", round(span, 1), flush=True)


def _hide_gate(kit):
    bridge = getattr(kit, "bridge", None)
    if not bridge:
        return
    for key in ("decks", "towers", "cables", "suspenders"):
        for item in bridge.get(key) or []:
            obj = item.obj if hasattr(item, "obj") else item
            obj.hide_render = True
            for child in getattr(obj, "children_recursive", []):
                child.hide_render = True
    for obj in bpy.data.objects:
        if obj.name.split(".")[0] == "pier":
            obj.hide_render = True


def _vanish_traffic(kit):
    """Cars in the travel lanes, and bikes that fall when the riders vanish."""
    from engine.city_layout import AVE_Y, LANE_OFFSETS, ROAD_Z
    from engine.scenes import _bike, _traffic

    life = kit.collection("Life")
    z = ROAD_Z + 0.02
    lanes = (LANE_OFFSETS[1], LANE_OFFSETS[2])
    for index, (x0, x1, lane) in enumerate((
        (-55.0, 28.0, lanes[0]),
        (40.0, -36.0, lanes[1]),
        (-20.0, 48.0, LANE_OFFSETS[0]),
    )):
        _traffic(kit, life, [(x0, AVE_Y + lane, z), (x1, AVE_Y + lane, z)], index + 2, 7.0, index * 4.0)
    for index, x in enumerate((-18.0, 4.0, 22.0)):
        _bike(kit, life, [(x, AVE_Y - 6.5, z), (x + 12.0, AVE_Y - 6.5, z)], index * 2.0)


def _fir_mesh():
    path = Path("/opt/cursor/asset-cache/private/found_plane/fir_sapling_medium/fir_sapling_medium_1k.gltf")
    if not path.exists():
        return None
    fresh = _import_gltf(path)
    meshes = [obj for obj in fresh if obj.type == "MESH"]
    if not meshes:
        return None
    src = meshes[0]
    for extra in meshes[1:]:
        bpy.data.objects.remove(extra, do_unlink=True)
    count = len(src.data.vertices)
    if count > 40000:
        _decimate(src, 40000 / count)
    src.hide_render = True
    return src.data


def _forest_patches(kit):
    """Irregular green firs. The straight autumn row behind the skyline goes away."""
    for item in kit.items:
        if item.role == "tree_canopy" and item.base_loc.y > 420.0:
            item.extra["backdrop"] = True
            item.obj.hide_render = True
    mesh = _fir_mesh()
    if mesh is None:
        return 0
    coll = kit.collection("Plants")
    rng = random.Random(53)
    placed = 0
    # Native firs are already about 8 m. A small clump at the foot of the range.
    clumps = ((-220, 980), (80, 1120), (420, 1040), (-40, 860))
    for cx, cy in clumps:
        for i in range(7):
            obj = bpy.data.objects.new("fir_patch", mesh)
            coll.objects.link(obj)
            obj.location = (cx + rng.uniform(-55.0, 55.0), cy + rng.uniform(-40.0, 40.0), FAR_Z)
            obj.rotation_euler.z = rng.random() * 6.2
            height = rng.uniform(1.1, 2.2)
            obj.scale = (height, height, height)
            kit.add(obj, "tree_canopy", future=False, sink=False, leaf=(0.08, 0.32, 0.12, 1), autumn=(0.1, 0.32, 0.12, 1))
            placed += 1
    if cc0_city.ready():
        for i in range(220):
            x = rng.uniform(-200.0, 240.0)
            y = rng.uniform(170.0, 480.0)
            if river_contains(x, y) or abs(x - (y * 0.02)) < 8.0 and y < 220.0:
                continue
            tree = cc0_city.place_tree(coll, x, y, FAR_Z, rng.uniform(8.0, 16.0), "pine" if i % 4 else "round")
            if tree is None:
                continue
            kit.add(tree, "swallow", sink=False, leaf=(0.1, 0.36, 0.14, 1), autumn=(0.2, 0.38, 0.12, 1))
            placed += 1
    return placed


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
    _photoreal_range(kit)
    _retint_horizon(mats)
    _murky_river(kit)
    _overgrowth(kit, mats)
    _river_debris(kit)
    _place_suspension(kit)
    _vanish_traffic(kit)
    patches = _forest_patches(kit)
    print("fir patches", patches, flush=True)
    fog, density = _fog(kit.collection("Weather"))
    kit.street_fog = fog
    kit.fog_density = density
    print("ready city wings", wings, "ruin shells", ruins, "trees", trees, flush=True)
    _prune(kit)
    return kit


def _pose_suspension(kit, collapse):
    rig = getattr(kit, "suspension", None)
    if not rig:
        return
    holder = rig["holder"]
    deck = rig["deck"]
    holder.location = rig["holder_loc"].copy()
    holder.rotation_euler = rig["holder_rot"].copy()
    deck.location = rig["deck_loc"].copy()
    deck.rotation_euler = rig["deck_rot"].copy()
    for obj, rot in zip(rig["towers"], rig["tower_rot"]):
        obj.rotation_euler = rot.copy()
    if collapse < 0.45:
        return
    if collapse < 0.85:
        # Deck sags. Towers stay up.
        deck.location.z = rig["deck_loc"].z - 0.35
        deck.rotation_euler.y = rig["deck_rot"].y + 0.08
        return
    # Centre span drops into the river. Towers lean.
    deck.location.z = rig["deck_loc"].z - 1.1
    deck.rotation_euler.y = rig["deck_rot"].y + 1.15
    for obj, rot in zip(rig["towers"], rig["tower_rot"]):
        obj.rotation_euler = Euler((rot.x + 0.55, rot.y, rot.z + 0.25))


def drive(kit, ch):
    """100 years keeps a broken skyline. 500 years knocks it down."""
    collapse = float(ch.get("collapse", 0.0))
    heavy = 0.45 <= collapse < 0.85
    fallen = collapse >= 0.85
    _hide_gate(kit)
    _hide_old_peaks()
    _pose_suspension(kit, collapse)
    if kit.water is not None:
        kit.water.obj.hide_render = False
    for item in kit.items:
        if item.extra.get("backdrop"):
            item.obj.hide_render = True
        if item.role == "river_age":
            _hide_tree(item.obj, collapse < 0.4)
        elif item.role == "building_base" and heavy and item.base_loc.y < 420.0:
            _hide_tree(item.obj, False)
        elif item.role == "building_base" and fallen:
            topple = bool(item.extra.get("topple"))
            stump = item.base_loc.y < 80.0 and (int(item.base_loc.x) // 17) % 3 == 0
            if topple:
                _hide_tree(item.obj, False)
                item.obj.rotation_euler = Euler((1.25, 0.1, item.base_rot.z))
            elif stump:
                _hide_tree(item.obj, False)
                item.obj.scale = (item.base_scale.x, item.base_scale.y, item.base_scale.z * 0.22)
            else:
                _hide_tree(item.obj, True)
        elif item.role in {"shell", "fallen", "rubble_hill"} and heavy:
            _hide_tree(item.obj, True)
        elif item.role == "shell" and fallen:
            # The ruin meshes are full towers. At 500 years they are stumps or they lie down.
            if (int(item.base_loc.x) // 19) % 4 == 0:
                item.obj.rotation_euler = Euler((1.2, 0.15, item.base_rot.z))
                item.obj.location.z = max(0.2, item.base_loc.z)
            else:
                item.obj.scale = (item.base_scale.x, item.base_scale.y, item.base_scale.z * 0.26)
        elif item.role == "swallow" and heavy:
            item.obj.hide_render = True
    node = getattr(kit, "fog_density", None)
    if node is not None:
        amount = 0.15 + 0.85 * smoother(0.30, 0.70, collapse)
        node.outputs[0].default_value = 0.005 * amount
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
