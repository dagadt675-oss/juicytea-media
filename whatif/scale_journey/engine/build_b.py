"""Blender scene for the penny / Empire State fall.

    blender --background --python engine/build_b.py -- job.json

The hook looks off the deck at the city. The chase sits above the coin and
looks down the streets. The tower is original Art Deco massing: setbacks,
piers, a spire. No logos.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bpy
import mathutils

ROOT = Path(__file__).resolve().parents[1]
WHATIF = ROOT.parent
for path in (str(WHATIF), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

CACHE = ROOT / "cache" / "library" / "extracted"
PRIVATE = ROOT / "cache" / "private"
# Sketchfab Free Standard. Not redistributed; the fetch/cache holds the files.
ESB_GLB = PRIVATE / "empire_state.glb"
LIBERTY_GLB = PRIVATE / "statue_liberty.glb"


def _job() -> dict:
    argv = sys.argv
    return json.loads(Path(argv[argv.index("--") + 1]).read_text(encoding="utf-8"))


def _clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _mat(name, color, rough=1.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*color, 1)
    return mat


def _assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def _box(name, w, d, h, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (max(w, 0.02), max(d, 0.02), max(h, 0.02))
    bpy.ops.object.transform_apply(scale=True)
    return obj


def _math(nt, op, a, b=None):
    node = nt.nodes.new("ShaderNodeMath")
    node.operation = op
    if isinstance(a, float):
        node.inputs[0].default_value = a
    else:
        nt.links.new(a, node.inputs[0])
    if b is not None:
        if isinstance(b, float):
            node.inputs[1].default_value = b
        else:
            nt.links.new(b, node.inputs[1])
    return node.outputs[0]


def _facade_mat(stone, name="Limestone"):
    """Limestone piers and dark window bays. Flat colors, so 1 sample stays clean."""
    mat = _mat(name, stone, 1.0, 0.05)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], nsep.inputs["Vector"])
    abs_z = _math(nt, "ABSOLUTE", nsep.outputs["Z"])
    wall = _math(nt, "LESS_THAN", abs_z, 0.55)

    def band(socket, scale, lo, hi):
        scaled = _math(nt, "MULTIPLY", socket, scale)
        frac = _math(nt, "FRACT", scaled)
        inside = _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", frac, lo), _math(nt, "LESS_THAN", frac, hi))
        return inside

    windows = _math(nt, "MULTIPLY", band(sep.outputs["X"], 0.38, 0.16, 0.78), band(sep.outputs["Z"], 0.32, 0.18, 0.74))
    windows = _math(nt, "MULTIPLY", windows, wall)
    lit_hash = _math(nt, "FRACT", _math(nt, "ADD", _math(nt, "MULTIPLY", sep.outputs["X"], 0.37), _math(nt, "MULTIPLY", sep.outputs["Z"], 0.19)))
    lit = _math(nt, "MULTIPLY", windows, _math(nt, "LESS_THAN", lit_hash, 0.28))
    glass = nt.nodes.new("ShaderNodeMix")
    glass.data_type = "RGBA"
    glass.inputs[6].default_value = (*stone, 1)
    glass.inputs[7].default_value = (0.10, 0.12, 0.15, 1)
    nt.links.new(windows, glass.inputs[0])
    warm = nt.nodes.new("ShaderNodeMix")
    warm.data_type = "RGBA"
    nt.links.new(glass.outputs[2], warm.inputs[6])
    warm.inputs[7].default_value = (1.0, 0.62, 0.28, 1)
    nt.links.new(lit, warm.inputs[0])
    nt.links.new(warm.outputs[2], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.55, 0.22, 1)
        emit = _math(nt, "MULTIPLY", lit, 5.5)
        nt.links.new(emit, bsdf.inputs["Emission Strength"])
    return mat


def _world(hdr_path: str):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdr_path)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, 0.9)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.85
    dark = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(env.outputs["Color"], dark.inputs["Color"])
    dark.inputs["Strength"].default_value = 0.45
    mix = nt.nodes.new("ShaderNodeMixShader")
    light = nt.nodes.new("ShaderNodeLightPath")
    nt.links.new(light.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(dark.outputs["Background"], mix.inputs[1])
    nt.links.new(bg.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def _sun():
    # Late afternoon, high enough that shadows stay short and soft.
    light = bpy.data.lights.new("Sun", "SUN")
    light.energy = 5.0
    light.color = (1.0, 0.78, 0.55)
    light.angle = 0.045
    obj = _link(bpy.data.objects.new("Sun", light))
    direction = mathutils.Vector((0.45, -0.25, 0.86))
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 2.2
    fill.color = (0.75, 0.82, 1.0)
    fill.use_shadow = False
    fill.angle = 0.4
    fill_obj = _link(bpy.data.objects.new("Fill", fill))
    fill_obj.rotation_euler = mathutils.Vector((-0.2, 0.55, 0.35)).to_track_quat("Z", "Y").to_euler()


KIT = CACHE / "assets_cc0_city_buildings" / "city_buildings"
ROADS = CACHE / "assets_cc0_roads_props" / "roads_props" / "kenney_city_kit_roads" / "Models" / "GLB format"
CARS = CACHE / "assets_cc0_vehicles" / "vehicles" / "kenney_car_kit" / "Models" / "GLB format"
FOOD = CACHE / "assets_cc0_food" / "food" / "kenney_food_kit" / "Models" / "GLB format"
MEN = CACHE / "assets_cc0_characters" / "characters" / "quaternius_animated_men" / "glb"
DANCE = CACHE / "assets_cc0_animations" / "animations" / "quaternius_universal_animation_library" / "Universal Animation Library[Standard]" / "Unreal-Godot" / "UAL1_Standard.glb"
HDRI = CACHE / "assets_cc0_hdri" / "hdri" / "polyhaven_hdris_2k" / "belfast_sunset_puresky" / "belfast_sunset_puresky_2k.hdr"


def _imported(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


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


def _parent_keep(children, empty):
    for obj in children:
        if obj.parent is not None:
            continue
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.matrix_world = world


def _place_model(path, name, location, scale, rotation_z=0.0):
    objs = _imported(path)
    empty = _link(bpy.data.objects.new(name, None))
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    _parent_keep(roots, empty)
    empty.location = location
    empty.scale = (scale, scale, scale)
    empty.rotation_euler = (0.0, 0.0, rotation_z)
    bpy.context.view_layer.update()
    return empty, objs


def _ground(empty, objs):
    bpy.context.view_layer.update()
    mn, _mx = _bounds(objs)
    empty.location.z -= mn.z
    bpy.context.view_layer.update()


def _clip_low(meshes, zcut):
    """Drop scan holes, giant spanning triangles, and faces outside the shaft."""
    import bmesh

    for obj in meshes:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        mw = obj.matrix_world
        dead = []
        for face in bm.faces:
            center = mw @ face.calc_center_median()
            verts = [mw @ vert.co for vert in face.verts]
            edge = 0.0
            for a, b in zip(verts, verts[1:] + verts[:1]):
                edge = max(edge, (a - b).length)
            outside = center.z < 180.0 and (center.x < -80.0 or center.x > 60.0 or center.y < -42.0 or center.y > 40.0)
            if edge > 16.0 or center.z < zcut or outside:
                dead.append(face)
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bm.to_mesh(obj.data)
            obj.data.update()
        print(f"CLIP {obj.name} removed {len(dead)}", flush=True)
        bm.free()


def _sharpen_textures():
    import subprocess

    for img in list(bpy.data.images):
        width, height = img.size
        if width < 128 or height < 128:
            continue
        source = PRIVATE / "esb_src.png"
        sharp_path = PRIVATE / "esb_sharp.png"
        img.filepath_raw = str(source)
        img.file_format = "PNG"
        img.save()
        subprocess.check_call(
            [
                "python3",
                "-c",
                (
                    "from PIL import Image, ImageFilter;"
                    f"im=Image.open({str(source)!r}).convert('RGB');"
                    "im=im.resize((im.width*2, im.height*2), Image.Resampling.LANCZOS);"
                    "im=im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=190, threshold=1));"
                    f"im.save({str(sharp_path)!r})"
                ),
            ]
        )
        sharp = bpy.data.images.load(str(sharp_path))
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image == img:
                    node.image = sharp
                    node.interpolation = "Smart"
        print(f"ESB texture sharpened {width}x{height}", flush=True)
        return


def _podium():
    # The Free Standard scan is open below ~46 m. No hub asset is a cap for
    # this mesh (the city blocks are whole streets and would bury the tower).
    stone = _mat("Podium", (0.73, 0.67, 0.58), 0.72, 0.04)
    glass = _mat("Storefront", (0.12, 0.14, 0.16), 0.15, 0.35)
    _assign(_box("Podium", 130, 72, 46.0, (-11.0, 0.0, 23.0)), stone)
    for index, x in enumerate(range(-60, 50, 9)):
        _assign(_box(f"ShopN{index}", 6.2, 0.35, 3.4, (x, 36.2, 2.2)), glass)
    for index, y in enumerate(range(-28, 30, 9)):
        _assign(_box(f"ShopE{index}", 0.35, 6.2, 3.4, (54.2, y, 2.2)), glass)


def _empire():
    if not ESB_GLB.exists():
        raise RuntimeError(f"missing hero model {ESB_GLB}")
    objs = _imported(ESB_GLB)
    meshes = [obj for obj in objs if obj.type == "MESH"]
    mn, mx = _bounds(meshes)
    height = mx.z - mn.z
    scale = 443.2 / height
    empty = _link(bpy.data.objects.new("EmpireState", None))
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    _parent_keep(roots, empty)
    empty.scale = (scale, scale, scale)
    empty.location = (0.0, 0.0, -mn.z * scale)
    bpy.context.view_layer.update()
    mn2, mx2 = _bounds(meshes)
    print(f"ESB tip {mx2.z:.1f} m base {mn2.z:.1f} m footprint {mx2.x - mn2.x:.0f} x {mx2.y - mn2.y:.0f}", flush=True)
    _clip_low(meshes, 44.0)
    _sharpen_textures()
    _podium()
    return empty


def _liberty():
    """Liberty Island is about 5 km south-west of the tower. 93 m to the torch."""
    if not LIBERTY_GLB.exists():
        print("LIBERTY missing", flush=True)
        return None
    objs = _imported(LIBERTY_GLB)
    meshes = [obj for obj in objs if obj.type == "MESH"]
    mn, mx = _bounds(meshes)
    scale = 93.0 / max(0.01, mx.z - mn.z)
    empty = _link(bpy.data.objects.new("Liberty", None))
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    _parent_keep(roots, empty)
    empty.scale = (scale, scale, scale)
    # South is -Y, west is -X. About 5.0 km from the tower.
    empty.location = (-1600.0, -4750.0, -mn.z * scale)
    bpy.context.view_layer.update()
    return empty


def _quads(name, quads, mat, z=0.02):
    verts = []
    faces = []
    for x0, y0, x1, y1 in quads:
        i = len(verts)
        verts.extend(((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)))
        faces.append((i, i + 1, i + 2, i + 3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = _link(bpy.data.objects.new(name, mesh))
    return _assign(obj, mat)


def _dup(root, location, scale, yaw):
    bpy.ops.object.select_all(action="DESELECT")

    def select(obj):
        obj.select_set(True)
        for child in obj.children:
            select(child)

    select(root)
    bpy.context.view_layer.objects.active = root
    bpy.ops.object.duplicate(linked=True)
    copy = bpy.context.view_layer.objects.active
    copy.location = location
    copy.scale = scale
    copy.rotation_euler = (0.0, 0.0, yaw)
    return copy


def _manhattan():
    """Avenues run north-south, streets east-west. Blocks are about 280 x 80 m."""
    pitch_x = 280.0 + 30.0
    pitch_y = 80.0 + 18.0
    ave_w, st_w = 30.0, 18.0
    reach = 2500.0
    asphalt = _mat("Asphalt", (0.045, 0.046, 0.05), 0.92, 0.0)
    walk = _mat("Concrete", (0.55, 0.53, 0.50), 0.9, 0.02)
    paint = _mat("Lane", (0.85, 0.75, 0.28), 0.6, 0.0)
    zebra = _mat("Crosswalk", (0.82, 0.82, 0.80), 0.7, 0.0)
    _assign(_box("Earth", reach * 4, reach * 4, 0.3, (0.0, 0.0, -0.45)), asphalt)
    roads, walks, lanes, crosses = [], [], [], []
    avenues = [i * pitch_x + pitch_x * 0.5 for i in range(-9, 9)]
    streets = [j * pitch_y + pitch_y * 0.5 for j in range(-28, 28)]
    for x in avenues:
        roads.append((x - ave_w * 0.5, -reach, x + ave_w * 0.5, reach))
        walks.append((x - ave_w * 0.5 - 4.5, -reach, x - ave_w * 0.5, reach))
        walks.append((x + ave_w * 0.5, -reach, x + ave_w * 0.5 + 4.5, reach))
    for y in streets:
        roads.append((-reach, y - st_w * 0.5, reach, y + st_w * 0.5))
        walks.append((-reach, y - st_w * 0.5 - 4.5, reach, y - st_w * 0.5))
        walks.append((-reach, y + st_w * 0.5, reach, y + st_w * 0.5 + 4.5))
    for x in avenues:
        y = -reach
        while y < reach:
            if not any(abs(y - sy) < st_w for sy in streets):
                lanes.append((x - 0.12, y, x + 0.12, y + 4.0))
            y += 10.0
    for y in streets:
        x = -reach
        while x < reach:
            if not any(abs(x - ax) < ave_w for ax in avenues):
                lanes.append((x, y - 0.12, x + 4.0, y + 0.12))
            x += 10.0
    for x in avenues:
        for y in streets:
            # One zebra per leg, just outside the intersection box.
            for k in range(6):
                yy = y + st_w * 0.5 + 0.6 + k * 0.55
                crosses.append((x - ave_w * 0.42, yy, x + ave_w * 0.42, yy + 0.28))
                yy = y - st_w * 0.5 - 0.6 - k * 0.55
                crosses.append((x - ave_w * 0.42, yy - 0.28, x + ave_w * 0.42, yy))
            for k in range(6):
                xx = x + ave_w * 0.5 + 0.6 + k * 0.55
                crosses.append((xx, y - st_w * 0.42, xx + 0.28, y + st_w * 0.42))
                xx = x - ave_w * 0.5 - 0.6 - k * 0.55
                crosses.append((xx - 0.28, y - st_w * 0.42, xx, y + st_w * 0.42))
    _quads("Roads", roads, asphalt, 0.02)
    _quads("Sidewalks", walks, walk, 0.06)
    _quads("Lanes", lanes, paint, 0.07)
    _quads("Crosswalks", crosses, zebra, 0.075)
    folder = KIT / "kenney_city_kit_commercial" / "Models" / "GLB format"
    names = [
        "building-skyscraper-a.glb",
        "building-skyscraper-b.glb",
        "building-skyscraper-c.glb",
        "building-skyscraper-d.glb",
        "building-skyscraper-e.glb",
        "building-a.glb",
        "building-b.glb",
    ]
    protos = []
    for name in names:
        empty, objs = _place_model(folder / name, "Proto" + name, (0.0, 0.0, 0.0), 1.0, 0.0)
        bpy.context.view_layer.update()
        mn, mx = _bounds(objs)
        shift = mathutils.Vector(((mn.x + mx.x) * 0.5, (mn.y + mx.y) * 0.5, mn.z))
        for obj in objs:
            if obj.parent == empty:
                obj.matrix_world.translation -= shift
        empty.location = (0.0, 0.0, -800.0)
        protos.append(empty)
    rng = __import__("random").Random(11)
    placed = 0
    for i in range(-8, 9):
        for j in range(-26, 27):
            if i == 0 and j == 0:
                continue
            cx, cy = i * pitch_x, j * pitch_y
            if cx * cx + cy * cy > reach * reach:
                continue
            proto = protos[(i * 3 + j * 5) % len(protos)]
            height = rng.choice((28, 40, 55, 18, 70, 46, 34))
            _dup(proto, (cx - 50, cy, 0.0), (42, 28, height), rng.random() * 0.2)
            other = protos[(i + j * 2) % len(protos)]
            _dup(other, (cx + 55, cy, 0.0), (32, 24, height * rng.uniform(0.45, 0.9)), 0.1)
            placed += 1
    print(f"CITY blocks {placed}", flush=True)
    taxi = CARS / "taxi.glb"
    for n, (x, y, yaw) in enumerate(
        (
            (110, 96, 1.57),
            (150, 108, -1.57),
            (80, 112, 1.57),
            (40, 68, 1.57),
            (95, 64, 1.57),
            (150, 70, -1.57),
            (210, 66, 1.57),
            (55, 74, -1.57),
            (155, 20, 0.0),
            (155, -40, 3.14),
            (155, 120, 0.0),
            (-155, 30, 3.14),
            (70, -37, 1.57),
            (220, -37, -1.57),
            (340, 61, 1.57),
        )
    ):
        empty, objs = _place_model(taxi, f"Taxi{n}", (x, y, 0.0), 1.8, yaw)
        _ground(empty, objs)


def _blocks():
    folder = KIT / "kenney_city_kit_commercial" / "Models" / "GLB format"
    names = [
        "building-skyscraper-a.glb",
        "building-skyscraper-b.glb",
        "building-skyscraper-c.glb",
        "building-skyscraper-d.glb",
        "building-skyscraper-e.glb",
        "building-a.glb",
        "building-b.glb",
    ]
    # Outside the hero footprint (about x -270..100, y -145..155).
    spots = [
        (170, 30, 48, 0.4),
        (230, 90, 36, 1.2),
        (150, 210, 42, 0.2),
        (240, 190, 30, 2.0),
        (90, 230, 38, 0.8),
        (-340, 20, 44, 1.5),
        (-310, -90, 34, 0.6),
        (20, -220, 40, 2.2),
        (200, -40, 46, 1.0),
        (-60, 240, 32, 0.3),
        (300, 40, 28, 1.7),
        (-360, 120, 36, 2.4),
    ]
    for index, (x, y, scale, yaw) in enumerate(spots):
        path = folder / names[index % len(names)]
        empty, objs = _place_model(path, f"Block{index}", (x, y, 0.0), scale, yaw)
        _ground(empty, objs)


def _roads_and_taxis():
    road = ROADS / "road-straight.glb"
    taxi = CARS / "taxi.glb"
    # A street just south of the tower base, in the fall's view.
    for i, x in enumerate(range(110, 290, 16)):
        empty, objs = _place_model(road, f"Road{i}", (x, 168.0, 0.02), 16.0, 0.0)
        _ground(empty, objs)
    for i, x in enumerate((130, 168, 206, 244, 150, 220)):
        yaw = 1.57 if i % 2 == 0 else -1.57
        empty, objs = _place_model(taxi, f"Taxi{i}", (x, 166.5 if i % 2 == 0 else 171.0, 0.0), 1.7, yaw)
        _ground(empty, objs)
    lamp = ROADS / "light-curved.glb"
    if lamp.exists():
        for i, x in enumerate((140, 200, 260)):
            empty, objs = _place_model(lamp, f"Lamp{i}", (x, 160.0, 0.0), 8.0, 0.0)
            _ground(empty, objs)


def _hotdog():
    path = FOOD / "hot-dog.glb"
    if not path.exists():
        return
    empty, objs = _place_model(path, "HotDog", (108.0, 156.0, 0.9), 2.2, 0.4)
    _ground(empty, objs)


def _action(arm, needle):
    for action in bpy.data.actions:
        if needle in action.name:
            if arm.animation_data is None:
                arm.animation_data_create()
            arm.animation_data.action = action
            return action
    return None


def _people():
    path = MEN / "Man_in_Suit_mQnGoME1ez.glb"
    if not path.exists():
        return None
    empty, objs = _place_model(path, "Walker0", (125.4, 103.6, 0.0), 0.34, 2.5)
    for obj in objs:
        if obj.type != "MESH":
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.use_nodes:
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    color = bsdf.inputs["Base Color"].default_value
                    if color[0] + color[1] + color[2] < 0.45:
                        bsdf.inputs["Base Color"].default_value = (0.62, 0.48, 0.40, 1.0)
    face = bpy.data.lights.new("Face", "AREA")
    face.energy = 180
    face.color = (1.0, 0.9, 0.78)
    face.size = 1.6
    face.use_shadow = False
    lamp = _link(bpy.data.objects.new("FaceLamp", face))
    lamp.location = (128.8, 106.6, 2.3)
    lamp.rotation_euler = mathutils.Vector((-1.7, -1.9, -0.8)).to_track_quat("-Z", "Y").to_euler()
    _ground(empty, objs)
    arms = [obj for obj in objs if obj.type == "ARMATURE"]
    for arm in arms:
        _action(arm, "Man_Walk")
    spots = [(70, 58, 1.5), (110, 62, 1.6), (140, 59, 4.7), (40, 60, 1.4), (175, 63, 1.2), (20, 57, 1.8)]
    for index, (x, y, yaw) in enumerate(spots, start=1):
        bpy.ops.object.select_all(action="DESELECT")
        empty.select_set(True)
        for obj in objs:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = empty
        bpy.ops.object.duplicate()
        copy = bpy.context.view_layer.objects.active
        copy.location = (x, y, empty.location.z)
        copy.rotation_euler = (0.0, 0.0, yaw)
    return arms[0] if arms else None


def _dancer():
    """Tiny gag: a mannequin dancing on a far roof. Not in the hero frame."""
    if not DANCE.exists():
        return
    empty, objs = _place_model(DANCE, "Dancer", (230.0, 90.0, 104.0), 0.62, 0.8)
    for arm in objs:
        if arm.type == "ARMATURE":
            _action(arm, "Dance_Loop")


def _street(image_path: str):
    mat = _mat("Grid", (0.45, 0.44, 0.42), 1.0, 0.03)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path)
    tex.interpolation = "Closest"
    tex.extension = "REPEAT"
    coord = nt.nodes.new("ShaderNodeTexCoord")
    scale = nt.nodes.new("ShaderNodeMapping")
    scale.inputs["Scale"].default_value = (8.0, 8.0, 1.0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], scale.inputs["Vector"])
    nt.links.new(scale.outputs["Vector"], sep.inputs["Vector"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    nt.links.new(comb.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    _assign(_box("Ground", 12000, 12000, 0.4, (-400, -800, -0.35)), mat)


def _look(cam, target):
    forward = mathutils.Vector(target) - cam.location
    if forward.length < 1e-5:
        return
    forward.normalize()
    up = mathutils.Vector((0.0, 0.0, 1.0))
    if abs(forward.dot(up)) > 0.96:
        up = mathutils.Vector((0.0, 1.0, 0.0))
    right = forward.cross(up).normalized()
    up = right.cross(forward).normalized()
    z_axis = -forward
    x_axis = up.cross(z_axis).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    cam.rotation_euler = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed().to_euler()


def _penny():
    mat = _mat("Penny", (0.86, 0.42, 0.2), 1.0, 0.08)
    rim = _mat("Rim", (0.55, 0.28, 0.12), 1.0, 0.02)
    show = 9.0
    radius = 0.009525 * show
    depth = 0.0018 * show
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "Penny"
    _assign(obj, mat)
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=depth * 0.7, major_segments=40, minor_segments=8)
    ring = bpy.context.object
    ring.name = "Rim"
    ring.parent = obj
    _assign(ring, rim)
    return obj


def _camera():
    data = bpy.data.cameras.new("Cam")
    data.lens = 14.0
    data.sensor_height = 24.0
    data.sensor_fit = "VERTICAL"
    data.clip_start = 0.04
    data.clip_end = 8000.0
    cam = _link(bpy.data.objects.new("Cam", data))
    bpy.context.scene.camera = cam
    return cam


def _pose_bone(arm, name, rot):
    pose = arm.pose.bones.get(name)
    if pose is None:
        return
    pose.rotation_mode = "XYZ"
    pose.rotation_euler = rot


def _bone(arm, suffix):
    for pose in arm.pose.bones:
        if pose.name == suffix or pose.name.endswith(suffix):
            return pose
    return None


def _head(arm, t):
    if arm is None or t < 33.4:
        return
    _action(arm, "Man_Idle")
    down = 0.35 + 0.85 * min(1.0, (t - 33.4) / 0.6)
    action = arm.animation_data.action if arm.animation_data else None
    if action is not None:
        for curve in action.fcurves:
            if "Head" in curve.data_path or "Neck" in curve.data_path:
                curve.mute = True
    for suffix, scale in (("Head", 1.0), ("Neck", 0.45)):
        pose = _bone(arm, suffix)
        if pose is None:
            continue
        pose.rotation_mode = "XYZ"
        pose.rotation_euler = (down * scale, 0.0, 0.0)


def _clear_camera(cam, protect):
    """Step the camera out only when several rays hit a solid from inside.

    One backface is not enough: the scan has flipped normals, and following
    a single one walks the camera into the tower.
    """
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    origin = cam.location.copy()
    axes = [mathutils.Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    for _ in range(5):
        inward = []
        for direction in axes:
            hit, loc, normal, _idx, obj, _mat = scene.ray_cast(deps, origin, direction, distance=12.0)
            if not hit or obj in protect:
                continue
            if direction.dot(normal) > 0.25 and (loc - origin).length < 6.0:
                inward.append(normal.normalized())
        if len(inward) < 3:
            break
        push = sum(inward, mathutils.Vector())
        if push.length < 1e-4:
            break
        origin = origin + push.normalized() * 1.4
    if (origin - cam.location).length > 0.05:
        print(f"CAM CLEAR {tuple(round(v, 2) for v in cam.location)} -> {tuple(round(v, 2) for v in origin)}", flush=True)
    cam.location = origin


def _air_gap(t):
    """The shaft test in bformat owns clearance. This offset stays zero."""
    return 0.0, 0.0


def _blur(scene, cam, penny, fr, frame):
    scene.frame_set(frame)
    for obj, prev, curr in (
        (cam, fr["prev_cam"], fr["cam"]),
        (penny, fr["prev_penny"], fr["penny"]),
    ):
        obj.animation_data_clear()
        obj.location = prev
        obj.keyframe_insert("location", frame=frame)
        obj.location = curr
        obj.keyframe_insert("location", frame=frame + 1)
    scene.frame_set(frame + 1)


def main():
    job = _job()
    _clear()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = max(16, int(job.get("samples", 16)))
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 1
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 0
    scene.cycles.sample_clamp_indirect = 0.0
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5
    scene.cycles.motion_blur_position = "END"
    scene.render.resolution_x = int(job["width"])
    scene.render.resolution_y = int(job["height"])
    scene.render.resolution_percentage = int(job.get("scale", 100))
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = 0.35
    _sun()
    hdr = str(HDRI if HDRI.exists() else job["hdri"])
    _world(hdr)
    from engine.manhattan import dress_city, tick_city

    _empire()
    _liberty()
    arm = dress_city()
    penny = _penny()
    cam = _camera()
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    for index, fr in enumerate(job["frames"]):
        prev = {
            "cam": fr.get("prev_cam") or fr["cam"],
            "penny": fr.get("prev_penny") or fr["penny"],
            "prev_cam": fr.get("prev_cam") or fr["cam"],
            "prev_penny": fr.get("prev_penny") or fr["penny"],
        }
        t = float(fr["t"])
        gx, gy = _air_gap(t)
        pgx, pgy = _air_gap(max(0.0, t - 1.0 / 30.0))
        prev_cam = list(fr.get("prev_cam") or fr["cam"])
        prev_penny = list(fr.get("prev_penny") or fr["penny"])
        prev_cam[0] += pgx
        prev_cam[1] += pgy
        prev_penny[0] += pgx
        prev_penny[1] += pgy
        prev_penny[2] += 0.02
        curr_cam = (fr["cam"][0] + gx, fr["cam"][1] + gy, fr["cam"][2])
        curr_penny = (fr["penny"][0] + gx, fr["penny"][1] + gy, fr["penny"][2] + 0.02)
        target = (fr["target"][0] + gx, fr["target"][1] + gy, fr["target"][2])
        walk_frame = 12 + int(t * 24.0) % 40
        _blur(scene, cam, penny, {"cam": curr_cam, "penny": curr_penny, "prev_cam": prev_cam, "prev_penny": prev_penny}, walk_frame)
        cam.data.lens = float(fr.get("lens") or job.get("lens_mm") or 14)
        _look(cam, target)
        penny.rotation_euler = tuple(fr.get("rot") or (0.2, 0.4, 0.0))
        _head(arm, float(fr["t"]))
        tick_city(t)
        bpy.context.view_layer.update()
        _clear_camera(cam, {penny, bpy.data.objects.get("Rim") or penny})
        _look(cam, target)
        png_path = out / f"f_{fr['frame']:04d}.png"
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(png_path)
        bpy.ops.render.render(write_still=True)
        if job.get("plate_format") == "exr":
            scene.render.image_settings.file_format = "OPEN_EXR"
            scene.render.image_settings.color_depth = "16"
            exr_path = out / f"f_{fr['frame']:04d}.exr"
            image = bpy.data.images.get("Render Result")
            if image is not None:
                image.save_render(str(exr_path))
            scene.render.image_settings.file_format = "PNG"
        if index % 10 == 0 or index + 1 == len(job["frames"]):
            print(f"PENNY {index + 1}/{len(job['frames'])} frame {fr['frame']}", flush=True)
    print(f"PENNY_DONE {len(job['frames'])}", flush=True)


if __name__ == "__main__":
    main()
