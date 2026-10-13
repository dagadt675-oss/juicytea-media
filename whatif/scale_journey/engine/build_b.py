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

from engine.landmarks import ESB_LOT

CACHE = ROOT / "cache" / "library" / "extracted"
PRIVATE = ROOT / "cache" / "private"
# Hub files. Not redistributed; the fetch/cache holds them.
# Empire State Building by NanoRay (CC-BY). Shrugging by Rida.Sidi.Ben.Ali (CC-BY).
ESB_GLB = PRIVATE / "empire_nanoray.glb"
SHRUG_GLB = PRIVATE / "shrug.glb"
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
    bg.inputs["Strength"].default_value = 1.35
    dark = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(env.outputs["Color"], dark.inputs["Color"])
    dark.inputs["Strength"].default_value = 0.85
    mix = nt.nodes.new("ShaderNodeMixShader")
    light = nt.nodes.new("ShaderNodeLightPath")
    nt.links.new(light.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(dark.outputs["Background"], mix.inputs[1])
    nt.links.new(bg.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    # No world volume. It was turning the clear sky grey.


def _sun():
    # Clear daytime, sun about 40 degrees up, small disc so shadows stay crisp.
    light = bpy.data.lights.new("Sun", "SUN")
    light.energy = 4.4
    light.color = (1.0, 0.97, 0.90)
    light.angle = 0.009
    obj = _link(bpy.data.objects.new("Sun", light))
    elev = math.radians(40.0)
    azim = math.radians(-35.0)
    direction = mathutils.Vector((math.cos(elev) * math.cos(azim), math.cos(elev) * math.sin(azim), math.sin(elev)))
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 2.2
    fill.color = (0.92, 0.90, 0.84)
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
HDRI = CACHE / "assets_cc0_hdri" / "hdri" / "polyhaven_hdris_2k" / "kloofendal_43d_clear_puresky" / "kloofendal_43d_clear_puresky_2k.hdr"


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


def _envelope(z: float) -> tuple[float, float]:
    """Half-width and half-depth of the real shaft, measured after it is centered.

    Below 90 m the keep is the lot, so the base cannot spill into Fifth Avenue.
    """
    if z >= 408.0:
        return 5.0, 5.0
    if z >= 372.0:
        return 8.5, 8.5
    if z >= 350.0:
        return 12.0, 12.0
    if z >= 325.0:
        return 18.0, 26.0
    if z >= 295.0:
        return 22.0, 32.0
    if z >= 90.0:
        return 32.0, 42.0
    _x0, x1, _y0, y1 = ESB_LOT
    return x1, y1


def _clip_low(meshes, zcut):
    """Keep the vertical shaft. The grey plane was the scan's ground, left at the origin while the tower sat 90 m away."""
    import bmesh

    kept_min = mathutils.Vector((1e9, 1e9, 1e9))
    kept_max = mathutils.Vector((-1e9, -1e9, -1e9))
    kept_n = 0
    deck_x = deck_y = -1e9
    for obj in meshes:
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        mw = obj.matrix_world
        nmat = mw.to_3x3()
        dead = []
        for face in bm.faces:
            verts = [mw @ vert.co for vert in face.verts]
            center = sum(verts, mathutils.Vector()) / len(verts)
            hx, hy = _envelope(center.z)
            outside = abs(center.x) > hx or abs(center.y) > hy
            stray = any(abs(v.x) > hx + 3.0 or abs(v.y) > hy + 3.0 for v in verts)
            edge = 0.0
            for a, b in zip(verts, verts[1:] + verts[:1]):
                edge = max(edge, (a - b).length)
            area = (verts[1] - verts[0]).cross(verts[2] - verts[0]).length * 0.5 if len(verts) >= 3 else 0.0
            normal = (nmat @ face.normal).normalized()
            # Long edges are the ribbon. Low flat lids are the scan's ground sheet.
            # The setback roofs stay so the deck is still there.
            flat_lid = abs(normal.z) > 0.84 and area > 14.0 and center.z < 80.0
            # Loose triangles around the mast, and the broken white setback slabs.
            crown_junk = center.z > 408.0 and (edge > 5.0 or area > 3.0)
            white_slab = abs(normal.z) > 0.55 and center.z > 40.0
            # Ribbons span hundreds of metres. A real facade triangle is shorter than that.
            if outside or stray or edge > 48.0 or flat_lid or crown_junk or white_slab or center.z < zcut:
                dead.append(face)
            else:
                kept_n += 1
                if 330.0 < center.z < 348.0:
                    deck_x = max(deck_x, center.x)
                    deck_y = max(deck_y, center.y)
                for v in verts:
                    kept_min = mathutils.Vector((min(kept_min.x, v.x), min(kept_min.y, v.y), min(kept_min.z, v.z)))
                    kept_max = mathutils.Vector((max(kept_max.x, v.x), max(kept_max.y, v.y), max(kept_max.z, v.z)))
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bm.to_mesh(obj.data)
            obj.data.update()
        print(f"CLIP {obj.name} removed {len(dead)}", flush=True)
        bm.free()
    if kept_n:
        print(
            f"SHAFT faces {kept_n} bbox x[{kept_min.x:.1f},{kept_max.x:.1f}] y[{kept_min.y:.1f},{kept_max.y:.1f}] z[{kept_min.z:.1f},{kept_max.z:.1f}] deckNE ({deck_x:.1f},{deck_y:.1f})",
            flush=True,
        )


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
    # The scan is a shell at the bottom. This plug stays inside the walls,
    # so it does not become a roof the hook camera looks down on.
    stone = _mat("Podium", (0.70, 0.66, 0.60), 0.7, 0.04)
    _assign(_box("Podium", 44.0, 56.0, 32.0, (0.0, 0.0, 16.0)), stone)


def _triplanar_facade():
    """CC0 window strips on vertical walls, plaster on the setback roofs."""
    found = WHATIF.parent / "assets" / "found"
    color_path = found / "Facade014_2K-JPG_Color.jpg"
    rough_path = found / "Facade014_2K-JPG_Roughness.jpg"
    stone_path = found / "Plaster001_1K-JPG_Color.jpg"
    stone_rough = found / "Plaster001_1K-JPG_Roughness.jpg"
    for path in (color_path, rough_path, stone_path, stone_rough):
        if not path.exists():
            raise RuntimeError(f"missing facade texture {path}")
    mat = bpy.data.materials.new("ESBFacade")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep_p = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep_p.inputs["Vector"])
    nt.links.new(geo.outputs["Normal"], sep_n.inputs["Vector"])

    def axis_abs(socket):
        return _math(nt, "ABSOLUTE", socket)

    abs_x = axis_abs(sep_n.outputs["X"])
    abs_y = axis_abs(sep_n.outputs["Y"])
    abs_z = axis_abs(sep_n.outputs["Z"])
    face_x = _math(nt, "GREATER_THAN", abs_x, abs_y)

    def scaled(socket, scale):
        return _math(nt, "MULTIPLY", socket, scale)

    # About 2.2 m per window bay and 3.7 m per floor (31 rows in the tile).
    u_ns = scaled(sep_p.outputs["X"], 0.014)
    u_ew = scaled(sep_p.outputs["Y"], 0.014)
    v = scaled(sep_p.outputs["Z"], 0.0087)
    u = nt.nodes.new("ShaderNodeMix")
    u.data_type = "FLOAT"
    nt.links.new(face_x, u.inputs[0])
    nt.links.new(u_ns, u.inputs[2])
    nt.links.new(u_ew, u.inputs[3])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u.outputs[0], comb.inputs["X"])
    nt.links.new(v, comb.inputs["Y"])

    def tex(path, colorspace):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(path))
        node.image.colorspace_settings.name = colorspace
        node.interpolation = "Smart"
        node.extension = "REPEAT"
        nt.links.new(comb.outputs["Vector"], node.inputs["Vector"])
        return node

    facade = tex(color_path, "sRGB")
    facade_r = tex(rough_path, "Non-Color")
    # Plaster repeats on the horizontal setbacks, not up the shaft.
    stone_uv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(scaled(sep_p.outputs["X"], 0.35), stone_uv.inputs["X"])
    nt.links.new(scaled(sep_p.outputs["Y"], 0.35), stone_uv.inputs["Y"])
    stone = nt.nodes.new("ShaderNodeTexImage")
    stone.image = bpy.data.images.load(str(stone_path))
    stone.image.colorspace_settings.name = "sRGB"
    stone.interpolation = "Smart"
    stone.extension = "REPEAT"
    nt.links.new(stone_uv.outputs["Vector"], stone.inputs["Vector"])
    stone_r = nt.nodes.new("ShaderNodeTexImage")
    stone_r.image = bpy.data.images.load(str(stone_rough))
    stone_r.image.colorspace_settings.name = "Non-Color"
    stone_r.interpolation = "Smart"
    stone_r.extension = "REPEAT"
    nt.links.new(stone_uv.outputs["Vector"], stone_r.inputs["Vector"])

    roof = _math(nt, "GREATER_THAN", abs_z, 0.72)
    color = nt.nodes.new("ShaderNodeMix")
    color.data_type = "RGBA"
    nt.links.new(roof, color.inputs[0])
    nt.links.new(facade.outputs["Color"], color.inputs[6])
    nt.links.new(stone.outputs["Color"], color.inputs[7])
    rough = nt.nodes.new("ShaderNodeMix")
    rough.data_type = "FLOAT"
    nt.links.new(roof, rough.inputs[0])
    nt.links.new(facade_r.outputs["Color"], rough.inputs[2])
    nt.links.new(stone_r.outputs["Color"], rough.inputs[3])
    nt.links.new(color.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.0
    # Warm the piers toward Indiana limestone without replacing the window strips.
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 1.0
    nt.links.new(color.outputs[2], tint.inputs[6])
    tint.inputs[7].default_value = (1.42, 1.24, 1.06, 1.0)
    nt.links.new(tint.outputs[2], bsdf.inputs["Base Color"])
    return mat


def _dress_facade(meshes):
    mat = _triplanar_facade()
    dressed = 0
    for obj in meshes:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        dressed += 1
    print(f"FACADE {dressed} meshes", flush=True)


def _found_image(name, colorspace):
    path = WHATIF.parent / "assets" / "found" / name
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = colorspace
    return image


def _principled(name, color, rough, metallic):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def _limestone_mat():
    mat = _principled("Limestone", (0.62, 0.56, 0.46), 0.72, 0.0)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.2, 2.2, 2.2)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    color = nt.nodes.new("ShaderNodeTexImage")
    color.image = _found_image("Plaster001_1K-JPG_Color.jpg", "sRGB")
    color.interpolation = "Smart"
    color.extension = "REPEAT"
    nt.links.new(mapping.outputs["Vector"], color.inputs["Vector"])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 1.0
    nt.links.new(color.outputs["Color"], tint.inputs[6])
    tint.inputs[7].default_value = (1.15, 1.02, 0.86, 1.0)
    nt.links.new(tint.outputs[2], bsdf.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeTexImage")
    rough.image = _found_image("Plaster001_1K-JPG_Roughness.jpg", "Non-Color")
    rough.interpolation = "Smart"
    rough.extension = "REPEAT"
    nt.links.new(mapping.outputs["Vector"], rough.inputs["Vector"])
    nt.links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
    normal = nt.nodes.new("ShaderNodeTexImage")
    normal.image = _found_image("Plaster001_1K-JPG_NormalGL.jpg", "Non-Color")
    normal.interpolation = "Smart"
    normal.extension = "REPEAT"
    nt.links.new(mapping.outputs["Vector"], normal.inputs["Vector"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.35
    nt.links.new(normal.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _metal_mat(name, color, rough):
    mat = _principled(name, color, rough, 1.0)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.4, 1.4, 1.4)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    rough_tex = nt.nodes.new("ShaderNodeTexImage")
    rough_tex.image = _found_image("Concrete034_1K-JPG_Roughness.jpg", "Non-Color")
    rough_tex.interpolation = "Smart"
    rough_tex.extension = "REPEAT"
    nt.links.new(mapping.outputs["Vector"], rough_tex.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs[0].default_value = 0.35
    mix.inputs[2].default_value = rough
    nt.links.new(rough_tex.outputs["Color"], mix.inputs[3])
    nt.links.new(mix.outputs[0], bsdf.inputs["Roughness"])
    return mat


def _glass_mat():
    mat = _principled("WindowGlass", (0.045, 0.062, 0.078), 0.18, 0.04)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.55
    return mat


def _nanoray_role(color):
    """Flat Sketchfab colours are material ids, not the finished look."""
    palette = (
        ((0.683, 0.535, 0.376), "limestone"),
        ((0.846, 0.846, 0.846), "frame"),
        ((0.636, 0.210, 0.173), "spandrel"),
        ((0.084, 0.155, 0.218), "glass"),
        ((0.069, 0.011, 0.011), "glass"),
        ((0.015, 0.026, 0.042), "glass"),
        ((0.003, 0.003, 0.003), "granite"),
        ((0.183, 0.352, 0.499), "frame"),
    )
    best, role = 1e9, "trim"
    for src, name in palette:
        dist = sum((color[i] - src[i]) ** 2 for i in range(3))
        if dist < best:
            best, role = dist, name
    return role if best <= 0.02 else "trim"


def _dress_nanoray(meshes):
    """Limestone piers, aluminium mullions and spandrels, dark glass bays."""
    mats = {
        "limestone": _triplanar_facade(),
        "frame": _metal_mat("AluminiumFrame", (0.74, 0.73, 0.70), 0.38),
        "spandrel": _metal_mat("AluminiumSpandrel", (0.58, 0.59, 0.57), 0.30),
        "glass": _glass_mat(),
        "granite": _principled("GraniteBase", (0.22, 0.21, 0.20), 0.84, 0.0),
    }
    counts = {}
    for obj in meshes:
        if obj.type != "MESH" or not obj.material_slots:
            continue
        color = (0.5, 0.5, 0.5)
        slot = obj.material_slots[0].material
        if slot and slot.use_nodes:
            bsdf = slot.node_tree.nodes.get("Principled BSDF")
            if bsdf is not None:
                color = tuple(bsdf.inputs["Base Color"].default_value[:3])
        role = _nanoray_role(color)
        if role == "trim":
            key = "trim_%d_%d_%d" % tuple(int(channel * 255) for channel in color)
            if key not in mats:
                mats[key] = _principled(key, color, 0.58, 0.0)
            role = key
        obj.data.materials.clear()
        obj.data.materials.append(mats[role])
        counts[role.split("_")[0]] = counts.get(role.split("_")[0], 0) + 1
    print("NANORAY " + " ".join(f"{name} {count}" for name, count in sorted(counts.items())), flush=True)


def _empire():
    """NanoRay Empire State. Re-centred, long side north, tip at 443.2 m."""
    if not ESB_GLB.exists():
        raise RuntimeError(f"missing hero model {ESB_GLB}")
    objs = _imported(ESB_GLB)
    meshes = [obj for obj in objs if obj.type == "MESH"]
    _dress_nanoray(meshes)
    mn, mx = _bounds(meshes)
    anchor = mathutils.Vector(((mn.x + mx.x) * 0.5, (mn.y + mx.y) * 0.5, mn.z))
    empty = _link(bpy.data.objects.new("EmpireState", None))
    empty.location = anchor
    bpy.context.view_layer.update()
    roots = [obj for obj in objs if obj.parent is None or obj.parent not in objs]
    _parent_keep(roots, empty)
    empty.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    scale = 443.2 / max(0.01, mx.z - mn.z)
    empty.rotation_euler = (0.0, 0.0, math.pi * 0.5)
    empty.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    mn2, mx2 = _bounds(meshes)
    empty.location.x -= (mn2.x + mx2.x) * 0.5
    empty.location.y += 64.5 - mx2.y
    empty.location.z -= mn2.z
    bpy.context.view_layer.update()
    mn3, mx3 = _bounds(meshes)
    print(
        f"ESB tip {mx3.z:.1f} m base {mn3.z:.1f} m footprint {mx3.x - mn3.x:.0f} x {mx3.y - mn3.y:.0f} scale {scale:.4f}",
        flush=True,
    )
    return empty


def _median_xy(meshes, zmin, zmax, rmax=None):
    xs, ys = [], []
    for obj in meshes:
        if obj.type != "MESH":
            continue
        mw = obj.matrix_world
        for poly in obj.data.polygons:
            center = mw @ mathutils.Vector(poly.center)
            if center.z < zmin or center.z > zmax:
                continue
            if rmax is not None and math.hypot(center.x, center.y) > rmax:
                continue
            xs.append(center.x)
            ys.append(center.y)
    if len(xs) < 40:
        return None
    xs.sort()
    ys.sort()
    mid = len(xs) // 2
    return xs[mid], ys[mid]


def _shift_xy(empty, meshes, zmin, zmax, rmax=None):
    center = _median_xy(meshes, zmin, zmax, rmax)
    if center is None:
        return
    empty.location.x -= center[0]
    empty.location.y -= center[1]
    bpy.context.view_layer.update()
    print(f"ESB center shift ({center[0]:.1f}, {center[1]:.1f})", flush=True)


def _align_to_lot(empty, meshes):
    """Put the mast on the lot center, long side north, base on z = 0.

    The scan includes a few hundred metres of ground. Centering that bbox
    parked the real tower at about (-46, 75) and left the ground under the camera.
    """
    _shift_xy(empty, meshes, 370.0, 435.0)
    pts = []
    for obj in meshes:
        if obj.type != "MESH":
            continue
        mw = obj.matrix_world
        polys = obj.data.polygons
        step = max(1, len(polys) // 6000)
        for index in range(0, len(polys), step):
            center = mw @ mathutils.Vector(polys[index].center)
            if 110.0 < center.z < 280.0 and math.hypot(center.x, center.y) < 45.0:
                pts.append((center.x, center.y))
    if len(pts) > 30:
        mean_x = sum(p[0] for p in pts) / len(pts)
        mean_y = sum(p[1] for p in pts) / len(pts)
        sxx = sum((p[0] - mean_x) ** 2 for p in pts)
        syy = sum((p[1] - mean_y) ** 2 for p in pts)
        sxy = sum((p[0] - mean_x) * (p[1] - mean_y) for p in pts)
        angle = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
        empty.rotation_euler.z += math.pi * 0.5 - angle
        bpy.context.view_layer.update()
    _shift_xy(empty, meshes, 370.0, 435.0, 25.0)
    lowest = 1e9
    for obj in meshes:
        if obj.type != "MESH":
            continue
        mw = obj.matrix_world
        verts = obj.data.vertices
        for index in range(0, len(verts), 4):
            world = mw @ verts[index].co
            if math.hypot(world.x, world.y) < 50.0 and world.z < lowest:
                lowest = world.z
    if lowest < 1e8:
        empty.location.z -= lowest
        bpy.context.view_layer.update()


def _crown():
    """North-east observation ledge. The scan already has the mast and the spire."""
    stone = _mat("CrownStone", (0.62, 0.58, 0.52), 0.55, 0.02)
    # A pad just bigger than the coin, on the scan's north-east corner.
    # A flat spot under the coin, sunk into the scan roof so it does not read as a slab.
    _assign(_box("Deck", 0.55, 0.5, 0.16, (3.28, 3.68, 381.0)), stone)


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


def _copper(name, roughness):
    mat = _mat(name, (0.86, 0.46, 0.26), roughness, 0.0)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 1.0
    nt = mat.node_tree
    coord = nt.nodes.new("ShaderNodeTexCoord")
    rings = nt.nodes.new("ShaderNodeTexWave")
    rings.wave_type = "RINGS"
    rings.inputs["Scale"].default_value = 18.0
    rings.inputs["Distortion"].default_value = 1.4
    nt.links.new(coord.outputs["Object"], rings.inputs["Vector"])
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 42.0
    grain.inputs["Detail"].default_value = 6.0
    nt.links.new(coord.outputs["Object"], grain.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs[0].default_value = 0.45
    nt.links.new(rings.outputs["Fac"], mix.inputs[2])
    nt.links.new(grain.outputs["Fac"], mix.inputs[3])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.42
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(mix.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _penny():
    """Round Lincoln cent. 64-side disc, bevelled rim, both faces from the packed map.

    The map is johndh's CC-BY-SA penny (public-domain Mint photos). Local +Z is Lincoln.
    Real cent: 19.05 mm across, 1.52 mm thick. The close camera, not the scale, makes it fill the frame.
    """
    found = WHATIF.parent / "assets" / "found"
    tex_path = found / "penny_tex.png"
    if not tex_path.exists():
        raise RuntimeError(f"missing penny texture {tex_path}")
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.5, depth=0.08, location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = "PennyDisc"
    bevel = obj.modifiers.new("Rim", "BEVEL")
    bevel.width = 0.016
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(35.0)
    bpy.ops.object.modifier_apply(modifier=bevel.name)

    import bmesh

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        normal = face.normal
        if normal.z > 0.45:
            center = (0.50, 0.75)
        elif normal.z < -0.45:
            center = (0.50, 0.25)
        else:
            center = None
        for loop in face.loops:
            if center is None:
                loop[layer].uv = (0.02, 0.50)
                continue
            co = loop.vert.co
            # The photo is twice as tall as it is wide, and each face sits in one half.
            loop[layer].uv = (center[0] + co.x * 0.86, center[1] + co.y * 0.43)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.clear()

    def copper(name, image):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.38
        bsdf.inputs["Base Color"].default_value = (0.78, 0.38, 0.20, 1.0)
        if image is None:
            return mat
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Smart"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.18
        bump.inputs["Distance"].default_value = 0.0015
        nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        return mat

    image = bpy.data.images.load(str(tex_path))
    image.colorspace_settings.name = "sRGB"
    obj.data.materials.append(copper("PennyFace", image))
    obj.data.materials.append(copper("PennyRim", None))
    for poly in obj.data.polygons:
        poly.material_index = 0 if abs(poly.normal.z) > 0.45 else 1

    empty = _link(bpy.data.objects.new("Penny", None))
    world = obj.matrix_world.copy()
    obj.parent = empty
    obj.matrix_world = world
    empty.scale = (0.01905, 0.01905, 0.01905)
    bpy.context.view_layer.update()
    print("COIN lincoln disc 64 sides -> 19.05 mm", flush=True)
    return empty


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
            if any(token in curve.data_path for token in ("Head", "Neck", "Spine", "Chest")):
                curve.mute = True
    for suffix, scale in (("Head", 1.0), ("Neck", 0.45)):
        pose = _bone(arm, suffix)
        if pose is None:
            continue
        pose.rotation_mode = "XYZ"
        pose.rotation_euler = (down * scale, 0.15, 0.0)
    for suffix, scale in (("Spine", 1.0), ("Spine1", 0.65), ("Chest", 0.45)):
        pose = _bone(arm, suffix)
        if pose is None:
            continue
        pose.rotation_mode = "XYZ"
        pose.rotation_euler = (-0.55 * min(1.0, down), 0.0, 0.0)


_IDLE_BASIS: dict = {}


def _shrug_frame(t):
    """Mixamo shrug, imported as 0..48 at 24 fps. Shoulders peak at frame 16.

    The bonk still holds an early flinch (frame 8). The reaction still holds
    the peak. Outside that window the pose is the standing first frame.
    """
    if t < 21.07 or t > 25.4:
        return 0.0
    if t < 22.15:
        return 8.0
    u = min(1.0, (t - 22.15) / (23.33 - 22.15))
    u = u * u * (3.0 - 2.0 * u)
    frame = 8.0 + (16.0 - 8.0) * u
    if t > 23.33:
        release = min(1.0, (t - 23.33) / 1.4)
        frame = 16.0 + (48.0 - 16.0) * release
    return frame


def _play_clip(arm, frame):
    name = arm.get("clip")
    action = bpy.data.actions.get(str(name)) if name else None
    arm.animation_data_clear()
    for bone in arm.pose.bones:
        bone.rotation_mode = "QUATERNION"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)
    if action is None:
        return
    touched = {}
    for curve in action.fcurves:
        path = curve.data_path
        if not path.startswith('pose.bones["'):
            continue
        bone_name = path.split('"')[1]
        attr = path.rsplit(".", 1)[-1]
        if arm.pose.bones.get(bone_name) is None:
            continue
        slot = touched.setdefault((bone_name, attr), {})
        slot[curve.array_index] = curve.evaluate(frame)
    for (bone_name, attr), slot in touched.items():
        bone = arm.pose.bones[bone_name]
        if attr == "rotation_quaternion":
            values = [bone.rotation_quaternion[i] for i in range(4)]
            for index, value in slot.items():
                values[index] = value
            bone.rotation_quaternion = values
        elif attr == "location":
            values = [bone.location[i] for i in range(3)]
            for index, value in slot.items():
                if index < 3:
                    values[index] = value
            bone.location = values
        elif attr == "scale":
            values = [bone.scale[i] for i in range(3)]
            for index, value in slot.items():
                if index < 3:
                    values[index] = value
            bone.scale = values
        elif attr == "rotation_euler":
            bone.rotation_mode = "XYZ"
            values = [bone.rotation_euler[i] for i in range(3)]
            for index, value in slot.items():
                if index < 3:
                    values[index] = value
            bone.rotation_euler = values


def _key_pose(arm, frame):
    for bone in arm.pose.bones:
        bone.keyframe_insert("location", frame=frame)
        bone.keyframe_insert("scale", frame=frame)
        if bone.rotation_mode == "QUATERNION":
            bone.keyframe_insert("rotation_quaternion", frame=frame)
        else:
            bone.keyframe_insert("rotation_euler", frame=frame)


def _slide_host(arm, t):
    host = arm.parent or arm
    if "home_x" not in host:
        host["home_x"] = host.location.x
        host["home_y"] = host.location.y
    if 23.9 < t < 27.6:
        host.location.x = float(host["home_x"]) + (t - 23.9) * 0.9
    else:
        host.location.x = float(host["home_x"])
        host.location.y = float(host["home_y"])


def _punchline(arm, t):
    """Four beats after the coin taps his head. Offsets are applied on top of the idle pose.

    Euler 0 on this rig is a T, so the idle matrices are captured before the curves are muted.
    The Mixamo shrug clip replaces that procedural pose when the hero carries it.
    """
    if arm is None:
        return
    if arm.get("clip"):
        _play_clip(arm, _shrug_frame(t))
        _slide_host(arm, t)
        return
    if t < 21.0 or t >= 27.6:
        return
    if arm.name not in _IDLE_BASIS:
        _IDLE_BASIS[arm.name] = {bone.name: bone.matrix.copy() for bone in arm.pose.bones}
        action = arm.animation_data.action if arm.animation_data else None
        if action is not None:
            for curve in action.fcurves:
                if any(token in curve.data_path for token in ("Neck", "Head", "Spine", "Clavicle", "UpperArm", "Forearm", "Hand", "Thigh")):
                    curve.mute = True
    bases = _IDLE_BASIS[arm.name]
    for bone in arm.pose.bones:
        saved = bases.get(bone.name)
        if saved is not None:
            bone.matrix = saved

    def put(suffix, rot):
        pose = _bone(arm, suffix)
        if pose is None:
            return
        pose.rotation_mode = "XYZ"
        extra = mathutils.Euler(rot, "XYZ").to_matrix().to_4x4()
        pose.matrix = pose.matrix @ extra

    neck = (0.0, 0.0, 0.0)
    spine = (0.0, 0.0, 0.0)
    uarm = (0.0, 0.0, 0.0)
    fore = (0.0, 0.0, 0.0)
    clav_l = (0.0, 0.0, 0.0)
    clav_r = (0.0, 0.0, 0.0)
    thigh_l = (0.0, 0.0, 0.0)
    thigh_r = (0.0, 0.0, 0.0)
    hand_l = (0.0, 0.0, 0.0)
    hand_r = (0.0, 0.0, 0.0)
    uarm_r = (0.0, 0.0, 0.0)
    fore_r = (0.0, 0.0, 0.0)
    if t < 21.70:
        u = _fade_u(t, 21.07, 21.16)
        neck = (0.65 * u, 0.0, 0.15 * u)
        spine = (0.45 * u, 0.0, 0.0)
        uarm = (0.35 * u, 0.15 * u, -0.2 * u)
        uarm_r = (0.35 * u, -0.15 * u, 0.2 * u)
        fore = (-0.45 * u, 0.0, 0.0)
        fore_r = (-0.45 * u, 0.0, 0.0)
    elif t < 22.45:
        u = (t - 21.70) / 0.75
        yaw = math.sin(u * math.pi * 2.0) * 0.9
        neck = (-0.15, yaw, -0.35)
        spine = (0.0, yaw * 0.35, 0.0)
    elif t < 23.05:
        u = min(1.0, (t - 22.45) / 0.18)
        uarm = (-0.4 * u, 0.2 * u, -1.6 * u)
        fore = (-1.3 * u, 0.0, -0.8 * u)
        hand_l = (0.6 * u, 0.4 * u, 0.2 * u)
        neck = (-0.25 * u, 0.2 * u, 0.15 * u)
    else:
        u = min(1.0, (t - 23.05) / 0.2)
        down = 1.0
        if t > 24.05:
            down = max(0.0, 1.0 - (t - 24.05) / 0.35)
            swing = math.sin((t - 24.05) * 7.0) * 0.7
            thigh_l = (swing, 0.0, 0.0)
            thigh_r = (-swing, 0.0, 0.0)
        clav_l = (0.0, 0.35 * u * down, 1.1 * u * down)
        clav_r = (0.0, -0.35 * u * down, -1.1 * u * down)
        uarm = (0.25 * u * down, 0.0, -0.55 * u * down)
        uarm_r = (0.25 * u * down, 0.0, 0.55 * u * down)
        fore = (-0.2 * u * down, 0.0, -0.35 * u * down)
        fore_r = (-0.2 * u * down, 0.0, 0.35 * u * down)
        hand_l = (0.2 * u * down, 1.1 * u * down, 0.0)
        hand_r = (0.2 * u * down, -1.1 * u * down, 0.0)
        neck = (-0.2 * u * down, 0.45 * u * down, 0.35 * u * down)
        spine = (-0.15 * u * down, 0.0, 0.0)
    put("Neck_05", neck)
    put("Head_06", (neck[0] * 0.6, neck[1] * 0.5, neck[2] * 0.4))
    put("Spine_03", spine)
    put("L UpperArm_08", uarm)
    put("R UpperArm_016", uarm_r)
    put("L Forearm_09", fore)
    put("R Forearm_017", fore_r)
    put("L Hand_010", hand_l)
    put("R Hand_018", hand_r)
    put("L Clavicle_07", clav_l)
    put("R Clavicle_015", clav_r)
    if t >= 23.85:
        put("L Thigh_023", thigh_l)
        put("R Thigh_027", thigh_r)
    host = arm.parent or arm
    if "home_x" not in host:
        host["home_x"] = host.location.x
        host["home_y"] = host.location.y
    if t > 23.9:
        host.location.x = float(host["home_x"]) + (t - 23.9) * 0.9
    elif "home_x" in host:
        host.location.x = float(host["home_x"])
        host.location.y = float(host["home_y"])


def _fade_u(t, t0, t1):
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    u = (t - t0) / (t1 - t0)
    return u * u * (3.0 - 2.0 * u)


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
    prev_rot = fr.get("prev_rot") or fr.get("rot") or (0.2, 0.4, 0.0)
    curr_rot = fr.get("rot") or (0.2, 0.4, 0.0)
    penny.rotation_euler = prev_rot
    penny.keyframe_insert("rotation_euler", frame=frame)
    penny.rotation_euler = curr_rot
    penny.keyframe_insert("rotation_euler", frame=frame + 1)
    scene.frame_set(frame + 1)


# Kept only where a 1080x1920 A/B against 24 samples, 12 bounces, OIDN,
# no culling and no LOD stayed at SSIM >= 0.99 on frames 0, 200 and 690.
# Adaptive sampling below 24 samples broke the facade. 4 and 6 bounces did
# not, and did not get faster. Distant LOD rewrote that same facade.
# There is no GPU on this machine.
SPEED = {
    "adaptive": True,
    "threshold": 0.01,
    "min_samples": 1,
    "bounces": 12,
    "persistent": True,
    "cull": False,
    "lod": False,
}


def configure_cycles(scene, job, speed=None):
    speed = SPEED if speed is None else speed
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = max(1, int(job.get("samples", 24)))
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    scene.cycles.use_adaptive_sampling = bool(speed["adaptive"])
    scene.cycles.adaptive_threshold = float(speed["threshold"])
    scene.cycles.adaptive_min_samples = int(speed["min_samples"])
    scene.cycles.max_bounces = int(speed["bounces"])
    scene.cycles.diffuse_bounces = int(speed["bounces"])
    scene.cycles.glossy_bounces = int(speed["bounces"])
    scene.cycles.transmission_bounces = int(speed["bounces"])
    scene.cycles.transparent_max_bounces = int(speed["bounces"])
    scene.cycles.sample_clamp_indirect = 0.0
    try:
        scene.cycles.use_light_tree = True
    except Exception:
        pass
    scene.render.use_persistent_data = bool(speed["persistent"])
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.6
    scene.cycles.motion_blur_position = "END"
    scene.render.resolution_x = int(job["width"])
    scene.render.resolution_y = int(job["height"])
    scene.render.resolution_percentage = int(job.get("scale", 100))
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.compression = 15
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = 0.55
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.get_devices()
        for device in prefs.devices:
            print(f"DEVICE {device.type} {device.name}", flush=True)
    except Exception as exc:
        print(f"DEVICE none {exc}", flush=True)


def prepare_scene(job, lod=False):
    _clear()
    scene = bpy.context.scene
    _sun()
    hdr = str(HDRI if HDRI.exists() else job["hdri"])
    _world(hdr)
    _empire()
    _liberty()
    from engine.manhattan import dress_city

    arms = dress_city(lod=lod) or []
    _deck_rail()
    penny = _penny()
    cam = _camera()
    return scene, cam, penny, arms


def _gltf_proto(path: Path, name: str):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not meshes:
        print(f"KIT missing {path.name}", flush=True)
        return None, (0.0, 0.0, 0.0)
    empty = _link(bpy.data.objects.new(name, None))
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.matrix_world = world
    bpy.context.view_layer.update()
    mn, mx = _bounds(meshes)
    empty.location.z -= mn.z
    bpy.context.view_layer.update()
    mn, mx = _bounds(meshes)
    empty["cull"] = "prop"
    empty["lod_hidden"] = 0
    return empty, (mx.x - mn.x, mx.y - mn.y, mx.z - mn.z)


def _stamp(proto, location, yaw=0.0, scale=1.0):
    bpy.ops.object.select_all(action="DESELECT")
    proto.select_set(True)
    for child in proto.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = proto
    bpy.ops.object.duplicate(linked=True)
    copy = bpy.context.view_layer.objects.active
    copy.location = location
    copy.rotation_euler = (0.0, 0.0, yaw)
    copy.scale = (scale, scale, scale)
    copy["cull"] = "prop"
    copy["lod_hidden"] = 0
    return copy


def _stone_cap(name, w, d, h, location):
    """Concrete parapet piece. The scan's setback roofs were the white slabs."""
    found = WHATIF.parent / "assets" / "found"
    mat = bpy.data.materials.get("ParapetStone")
    if mat is None:
        mat = bpy.data.materials.new("ParapetStone")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(found / "Concrete034_1K-JPG_Color.jpg"))
        tex.image.colorspace_settings.name = "sRGB"
        coord = mat.node_tree.nodes.new("ShaderNodeTexCoord")
        mapping = mat.node_tree.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (0.55, 0.55, 0.55)
        mat.node_tree.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
        mat.node_tree.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.72
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (w, d, h)
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(mat)
    return obj


def _deck_parapet():
    """L-shaped stone lip the coin rests on, at the 86th-floor corner."""
    z = 338.67
    _stone_cap("ParapetN", 4.6, 0.42, 0.36, (8.4, 15.55, z))
    _stone_cap("ParapetE", 0.42, 3.8, 0.36, (10.45, 13.8, z))
    print("PARAPET stone lip", flush=True)


def _deck_rail():
    """Curved run of the downtown metal rail around the 86th-floor parapet."""
    path = (
        CACHE
        / "assets_cc0_city_buildings"
        / "city_buildings"
        / "quaternius_downtown_city_megakit"
        / "Exports"
        / "glTF (Godot)"
        / "Stairs_Rails_Metal_Straight_1.gltf"
    )
    if not path.exists():
        print("RAIL missing", flush=True)
        return
    proto, span = _gltf_proto(path, "RailProto")
    if proto is None:
        return
    height = max(span[2], 0.2)
    scale = 1.85 / height
    # Curved safety rail on the 86th-floor parapet, just outside the coin.
    cx, cy, z = 10.7, 3.85, 317.25
    count = 0
    for index in range(7):
        ang = 0.35 + index * 0.22
        x = cx + math.cos(ang) * 0.85
        y = cy + math.sin(ang) * 0.85
        _stamp(proto, (x, y, z), ang + math.pi * 0.5, scale)
        count += 1
    proto.location.z = -400.0
    print(f"RAIL {count} curved span {span}", flush=True)


def _window_corner():
    """Quaternius brick windows down the corner the drone looks at.

    The scan albedo is one aerial photo, so a close wall reads as a grey slab.
    These pieces are the limestone courses with actual window openings.
    """
    path = (
        CACHE
        / "assets_cc0_city_buildings"
        / "city_buildings"
        / "quaternius_downtown_city_megakit"
        / "Exports"
        / "glTF (Godot)"
        / "Brick_Inset_Window.gltf"
    )
    if not path.exists():
        print("WINDOW missing", flush=True)
        return
    proto, span = _gltf_proto(path, "WinProto")
    if proto is None:
        return
    height = max(span[2], 0.2)
    width = max(span[0], span[1], 0.2)
    scale = 3.4 / height
    step_z = height * scale * 0.98
    step_x = width * scale * 0.98
    count = 0
    z = 2.0
    while z < 372.0:
        _stamp(proto, (21.6, 27.5, z), 1.5708, scale)
        _stamp(proto, (21.6 + step_x, 27.5, z), 1.5708, scale)
        z += step_z
        count += 2
    proto.location.z = -400.0
    print(f"WINDOWS {count} piece {span}", flush=True)


def pose_frame(scene, cam, penny, arms, fr, speed=None):
    from engine.manhattan import cull_to_camera, restore_cull, set_distant_lod, tick_city

    speed = SPEED if speed is None else speed
    t = float(fr["t"])
    gx, gy = _air_gap(t)
    pgx, pgy = _air_gap(max(0.0, t - 1.0 / 30.0))
    prev_cam = list(fr.get("prev_cam") or fr["cam"])
    prev_penny = list(fr.get("prev_penny") or fr["penny"])
    prev_cam[0] += pgx
    prev_cam[1] += pgy
    prev_penny[0] += pgx
    prev_penny[1] += pgy
    prev_penny[2] += 0.0015
    curr_cam = (fr["cam"][0] + gx, fr["cam"][1] + gy, fr["cam"][2])
    curr_penny = (fr["penny"][0] + gx, fr["penny"][1] + gy, fr["penny"][2] + 0.0015)
    target = (fr["target"][0] + gx, fr["target"][1] + gy, fr["target"][2])
    walk_frame = 12 + int(t * 24.0) % 40
    if int(fr["frame"]) in (0, 1001):
        prev_cam = [curr_cam[0], curr_cam[1], curr_cam[2]]
        prev_penny = [curr_penny[0], curr_penny[1], curr_penny[2]]
        walk_frame = 12
    # Frame 0 and the last frame share a seed so the loop diff is the picture, not the noise.
    scene.cycles.seed = 7 if int(fr["frame"]) in (0, 1001) else int(fr["frame"])
    _blur(
        scene,
        cam,
        penny,
        {"cam": curr_cam, "penny": curr_penny, "prev_cam": prev_cam, "prev_penny": prev_penny, "rot": fr.get("rot"), "prev_rot": fr.get("prev_rot")},
        walk_frame,
    )
    cam.data.lens = float(fr.get("lens") or 14)
    hook = float(fr.get("t") or 0.0) < 2.4 or float(fr.get("t") or 0.0) >= 33.15
    cam.data.dof.use_dof = False
    if hook:
        cam.data.dof.focus_distance = max(0.2, (mathutils.Vector(curr_penny) - mathutils.Vector(curr_cam)).length)
        cam.data.dof.aperture_fstop = 8.0
    _look(cam, target)
    rot = tuple(fr.get("rot") or (0.2, 0.4, 0.0))
    # Local +Z is Lincoln. Point that face at the lens. The way down adds a tumble.
    aim = mathutils.Vector(curr_cam) - mathutils.Vector(curr_penny)
    if aim.length > 0.02:
        face = aim.to_track_quat("Z", "Y").to_euler()
        # Macro, the bonk, and the loop stay face-on. The chase flutters.
        if t < 2.4 or t >= 32.8 or (20.9 <= t < 21.7):
            rot = (face.x, face.y, face.z)
        else:
            def _flutter(seed, scale):
                x = t * scale + seed
                return (
                    math.sin(x)
                    + 0.62 * math.sin(x * 2.37 + 1.3)
                    + 0.28 * math.sin(x * 5.05 + seed)
                ) / 1.9

            rot = (
                face.x + 0.85 * _flutter(0.6, 3.4),
                face.y + 0.45 * _flutter(2.1, 4.2),
                face.z + t * 7.2 + 1.3 * _flutter(1.4, 2.6),
            )
    penny.rotation_euler = rot
    penny.keyframe_insert("rotation_euler", frame=walk_frame)
    penny.keyframe_insert("rotation_euler", frame=walk_frame + 1)
    scene.frame_set(walk_frame + 1)
    for arm in arms:
        if arm.get("punchline"):
            _punchline(arm, t)
            if arm.get("clip"):
                _key_pose(arm, walk_frame)
                _key_pose(arm, walk_frame + 1)
        else:
            _head(arm, t)
    # Overhead insert faces north, matching the approved plate. The street
    # shot turns him toward the lens so both shrug palms read.
    star = bpy.data.objects.get("Star")
    if star is not None:
        star.rotation_euler = (0.0, 0.0, math.pi if t < 19.07 else 0.35)
    tick_city(t)
    bpy.context.view_layer.update()
    _clear_camera(cam, {penny, bpy.data.objects.get("Rim") or penny})
    _look(cam, target)
    set_distant_lod(bool(speed["lod"]))
    if speed["cull"]:
        cull_to_camera(cam)
    else:
        restore_cull()
    bpy.context.view_layer.update()


def render_frame(scene, cam, penny, arms, fr, dest: Path, speed=None):
    pose_frame(scene, cam, penny, arms, fr, speed)
    dest.parent.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(dest)
    bpy.ops.render.render(write_still=True)


def main():
    job = _job()
    scene, cam, penny, arms = prepare_scene(job, lod=bool(SPEED["lod"]))
    configure_cycles(scene, job, SPEED)
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    frames = job["frames"]
    for index, fr in enumerate(frames):
        render_frame(scene, cam, penny, arms, fr, out / f"f_{fr['frame']:04d}.png", SPEED)
        if index % 10 == 0 or index + 1 == len(frames):
            print(f"PENNY {index + 1}/{len(frames)} frame {fr['frame']}", flush=True)
    print(f"PENNY_DONE {len(frames)}", flush=True)


if __name__ == "__main__":
    main()
