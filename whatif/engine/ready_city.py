"""A downloaded city, used whole. The old river city is not touched.

Procedural City 6 is the living block. Ruined City Free 5 replaces it
once the years have taken the roofs. Mountains, debris, and a ground fog
sit around that pair. Nothing here is built as a stand-in building.
"""

from __future__ import annotations

from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Vector

from engine import cc0_city
from engine.meshkit import smoother

CITY = Path("/opt/cursor/asset-cache/private/sketchfab/city_blocks/procedural_city_6.glb")
RUIN = Path("/opt/cursor/asset-cache/private/debris/ruined_city_free_5.glb")
DEBRIS = Path("/opt/cursor/asset-cache/private/debris")
MOUNTAINS = Path("/opt/cursor/asset-cache/private/mountains")


def _import(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


def _bounds(objects):
    xs, ys, zs = [], [], []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def _adopt(objects, coll, name):
    """Parent without moving the meshes. matrix_world is restored after the link."""
    empty = bpy.data.objects.new(name, None)
    coll.objects.link(empty)
    bpy.context.view_layer.update()
    for obj in objects:
        world = obj.matrix_world.copy()
        for holder in list(obj.users_collection):
            holder.objects.unlink(obj)
        coll.objects.link(obj)
        obj.parent = empty
        obj.matrix_world = world
    return empty


def _seat(empty, objects, span=None):
    """Center on XY, sit the base on z=0, optionally match a horizontal span."""
    bpy.context.view_layer.update()
    box = _bounds(objects)
    if box is None:
        return
    minx, maxx, miny, maxy, minz, _maxz = box
    if span:
        current = max(maxx - minx, maxy - miny, 0.01)
        empty.scale = (span / current, span / current, span / current)
        bpy.context.view_layer.update()
        box = _bounds(objects)
        minx, maxx, miny, maxy, minz, _maxz = box
    empty.location.x -= (minx + maxx) * 0.5
    empty.location.y -= (miny + maxy) * 0.5
    empty.location.z -= minz


def _hide(root, hide):
    root.hide_render = hide
    for child in root.children_recursive:
        child.hide_render = hide


def _fog(coll):
    """Ground fog. Thick at street level, gone before the mountain peaks."""
    mesh = bpy.data.meshes.new("street_fog")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("street_fog", mesh)
    coll.objects.link(obj)
    # Cube is 1 m. This covers the block and the near streets, not the peaks.
    # Short enough that the camera sits above it. Peaks and the far range stay clear.
    obj.location = (0.0, 0.0, 18.0)
    obj.scale = (260.0, 230.0, 36.0)
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
    fall.inputs["From Max"].default_value = 34.0
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
    vol.inputs["Color"].default_value = (0.78, 0.80, 0.84, 1.0)
    vol.inputs["Anisotropy"].default_value = 0.4
    tree.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    mesh.materials.append(mat)
    return obj, density


def _mountain(coll, filename, loc, yaw, scale, name):
    mesh = cc0_city.static_mesh(MOUNTAINS / filename)
    if mesh is None:
        return None
    return cc0_city._spawn(coll, mesh, loc, yaw, scale, name)


def _debris(coll, filename, loc, yaw, longest):
    path = DEBRIS / filename
    mesh = cc0_city.static_mesh(path) if path.exists() else None
    if mesh is None:
        return None
    size = max(cc0_city._mesh_size(mesh))
    scale = float(longest) / max(size, 0.01)
    return cc0_city._spawn(coll, mesh, loc, yaw, scale, "debris")


def _ground(coll, mats):
    """Land under the block so the fog is not a hole in the sky."""
    mesh = bpy.data.meshes.new("ready_ground")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("ready_ground", mesh)
    coll.objects.link(obj)
    obj.location = (0.0, 40.0, -0.4)
    obj.scale = (700.0, 560.0, 0.4)
    mat = mats.get("trim") or mats.get("concrete")
    if mat is not None:
        mesh.materials.append(mat)
    return obj


def build(kit, mats, rng):
    """Drop the downloaded block in. Do not assemble a second city."""
    del rng
    coll = kit.collection("City")
    _ground(coll, mats)
    kit.kind = "ready_city"
    kit.water = None
    city = _import(CITY)
    root = _adopt(city, coll, "ready_city")
    _seat(root, city)
    kit.ready_city = root

    ruins = _import(RUIN)
    ruin_root = _adopt(ruins, coll, "ready_ruin")
    _seat(ruin_root, ruins, span=230.0)
    kit.ready_ruin = ruin_root

    far = kit.collection("Horizon")
    # These two already import at kilometre scale. A small factor keeps the
    # near edge behind the block instead of inside the camera.
    for filename, loc, yaw, scale, name in (
        ("free_textured_mountain.glb", (80.0, 2200.0, 0.0), -0.2, 1.15, "snow_peak"),
        ("three_peaked.glb", (1400.0, 2500.0, 0.0), 0.3, 1.6, "three_peaks"),
    ):
        obj = _mountain(far, filename, loc, yaw, scale, name)
        if obj is not None:
            kit.add(obj, "ready_mountain", sink=False)

    plants = kit.collection("Plants")
    if cc0_city.ready():
        for i, (x, y) in enumerate((
            (-70, -40), (-20, -55), (30, -20), (55, 15), (-40, 25), (10, 40),
            (-90, 5), (70, -45), (-15, -10), (40, 35), (-55, 40), (15, -40),
        )):
            tree = cc0_city.place_tree(plants, x, y, 0.0, 11.0 + (i % 3) * 2.0, "pine" if i % 2 else "round")
            if tree is not None:
                kit.add(tree, "swallow", sink=False)

    for filename, loc, yaw, longest in (
        ("concrete_rubble_steel.glb", (-18.0, -8.0, 0.2), 0.4, 14.0),
        ("pbr_debris.glb", (12.0, 6.0, 0.2), 0.2, 16.0),
        ("pbr_debris_3.glb", (24.0, -16.0, 0.15), 1.1, 11.0),
        ("pbr_debris_2.glb", (-30.0, 12.0, 0.2), 0.6, 8.0),
        ("scan_pile_concrete.glb", (6.0, -22.0, 0.1), 0.3, 7.0),
        ("asphalt_02.glb", (-6.0, 2.0, 0.15), 0.1, 12.0),
        ("wood_planks_debris.glb", (36.0, 8.0, 0.1), 0.8, 4.0),
        ("lowpoly_concrete_debris.glb", (-48.0, 28.0, 0.1), 0.5, 18.0),
    ):
        obj = _debris(coll, filename, loc, yaw, longest)
        if obj is not None:
            kit.add(obj, "ruin", sink=False)

    fog, density = _fog(kit.collection("Weather"))
    kit.street_fog = fog
    kit.fog_density = density
    return kit


def drive(kit, ch):
    """Era swap, a lower sun once the ruins are up, and ground fog."""
    collapse = float(ch.get("collapse", 0.0))
    ruined = collapse > 0.5
    _hide(kit.ready_city, ruined)
    _hide(kit.ready_ruin, not ruined)
    node = getattr(kit, "fog_density", None)
    if node is not None:
        # Day 1 stays a thin veil. Year 100 and 500 hold the street fog.
        amount = 0.2 + 0.8 * smoother(0.32, 0.62, collapse)
        node.outputs[0].default_value = 0.008 * amount
    scene = bpy.context.scene
    scene.cycles.volume_bounces = 1
    scene.cycles.volume_max_steps = 64
    scene.cycles.volume_step_rate = 1.6
    sun = getattr(kit, "sun", None)
    if sun is None or collapse < 0.4:
        return
    # Their daytime sun sits near x=0.72. Pushing that toward 1.15 lowers it
    # enough for shafts between the towers without turning the shot into night.
    drop = smoother(0.4, 0.75, collapse)
    # Low, and on the far side of the block, so the camera looks into the light.
    sun.rotation_euler = Euler((0.85 + drop * 0.28, 0.04, 2.35))
    sun.data.energy = 8.0
    sun.data.color = (1.0, 0.86, 0.68)
    sun.data.angle = 0.015
