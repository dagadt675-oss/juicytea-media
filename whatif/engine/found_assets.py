"""CC0 models and PBR textures recorded in assets/FOUND_ASSETS.md.

Day 1 leaves every mix at zero. Vegetation and rust raise grime, moss,
cracked asphalt, and the plant instances.
"""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2] / "assets" / "found"
TEX = ROOT / "polyhaven" / "textures"
MOD = ROOT / "polyhaven" / "models"

_PROTOS: dict[str, tuple] = {}
_IMAGES: dict[tuple, bpy.types.Image] = {}


def available(slug: str) -> bool:
    return (MOD / slug / f"{slug}_1k.gltf").exists()


def _image(path: Path, color: bool):
    key = (str(path), color)
    image = _IMAGES.get(key)
    if image is not None:
        return image
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = "sRGB" if color else "Non-Color"
    _IMAGES[key] = image
    return image


def _map(slug: str, kind: str) -> Path | None:
    path = TEX / slug / f"{slug}_{kind}_1k.jpg"
    return path if path.exists() else None


def pbr_material(name: str, slug: str, uv=2.5, displace=0.0):
    """A principled material from a Poly Haven 1k set. Missing maps are skipped."""
    diff = _map(slug, "diff")
    if diff is None:
        return None
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (uv, uv, uv)
    tree.links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])

    def tex_node(path, color):
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = _image(path, color)
        tree.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    color_node = tex_node(diff, True)
    tree.links.new(color_node.outputs["Color"], bsdf.inputs["Base Color"])
    rough = _map(slug, "rough")
    if rough is not None:
        tree.links.new(tex_node(rough, False).outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = 0.8
    normal = _map(slug, "nor_gl")
    if normal is not None:
        nmap = tree.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = 1.0
        tree.links.new(tex_node(normal, False).outputs["Color"], nmap.inputs["Color"])
        tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    disp = _map(slug, "disp")
    if disp is not None and displace > 0:
        height = tex_node(disp, False)
        bump = tree.nodes.new("ShaderNodeDisplacement")
        bump.inputs["Scale"].default_value = displace
        bump.inputs["Midlevel"].default_value = 0.5
        tree.links.new(height.outputs["Color"], bump.inputs["Height"])
        tree.links.new(bump.outputs["Displacement"], out.inputs["Displacement"])
        mat.displacement_method = "BOTH"
    return mat


def _principled(material):
    tree = material.node_tree
    if tree is None:
        return None
    return next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def _value(tree, name):
    node = tree.nodes.get(name)
    if node is None:
        node = tree.nodes.new("ShaderNodeValue")
        node.name = name
        node.label = name
        node.outputs[0].default_value = 0.0
    return node


def stamp_material(material, kind="plaster"):
    """Mix a downloaded weathering texture over a material. Factor stays 0 on day 1."""
    if material is None or material.get("age_stamp") or material.node_tree is None:
        return
    low = material.name.lower()
    if any(token in low for token in ("water", "miura", "leaf", "canopy", "flame", "skin", "mark")):
        return
    if material.get("object_tint"):
        return
    bsdf = _principled(material)
    if bsdf is None or "Base Color" not in bsdf.inputs:
        return
    slug = {
        "road": "road_damaged",
        "metal": "rusty_metal_02",
        "moss": "worn_mossy_plasterwall",
    }.get(kind, "worn_cracked_plaster")
    diff = _map(slug, "diff")
    if diff is None:
        return
    tree = material.node_tree
    decay = _value(tree, "Decay")
    forest = _value(tree, "Forest")
    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.12, 0.12, 0.12) if kind == "road" else (0.22, 0.22, 0.22)
    tree.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    image = tree.nodes.new("ShaderNodeTexImage")
    image.image = _image(diff, True)
    tree.links.new(mapping.outputs["Vector"], image.inputs["Vector"])
    # Vertical rain streaks, stronger as the years pass.
    streak_noise = tree.nodes.new("ShaderNodeTexNoise")
    streak_noise.inputs["Scale"].default_value = 3.5
    streak_noise.inputs["Detail"].default_value = 2.0
    tree.links.new(texcoord.outputs["Object"], streak_noise.inputs["Vector"])
    streak = tree.nodes.new("ShaderNodeMath")
    streak.operation = "MULTIPLY_ADD"
    streak.inputs[1].default_value = 0.65
    streak.inputs[2].default_value = 0.35
    tree.links.new(streak_noise.outputs["Fac"], streak.inputs[0])
    fac = tree.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    amount = 0.82 if kind == "road" else 0.72
    scale = tree.nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = amount
    tree.links.new(decay.outputs[0], scale.inputs[0])
    tree.links.new(scale.outputs[0], fac.inputs[0])
    tree.links.new(streak.outputs[0], fac.inputs[1])
    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    color_in = bsdf.inputs["Base Color"]
    if color_in.is_linked:
        source = color_in.links[0].from_socket
        tree.links.remove(color_in.links[0])
        tree.links.new(source, mix.inputs["Color1"])
    else:
        mix.inputs["Color1"].default_value = tuple(color_in.default_value)
    tree.links.new(image.outputs["Color"], mix.inputs["Color2"])
    tree.links.new(fac.outputs[0], mix.inputs["Fac"])
    # Moss and grass keep increasing after the grime has already saturated.
    moss_path = _map("concrete_moss" if kind != "road" else "grass_ground", "diff")
    if moss_path is not None:
        moss = tree.nodes.new("ShaderNodeTexImage")
        moss.image = _image(moss_path, True)
        tree.links.new(mapping.outputs["Vector"], moss.inputs["Vector"])
        moss_mix = tree.nodes.new("ShaderNodeMixRGB")
        moss_fac = tree.nodes.new("ShaderNodeMath")
        moss_fac.operation = "MULTIPLY"
        moss_fac.inputs[1].default_value = 0.55 if kind != "road" else 0.7
        tree.links.new(forest.outputs[0], moss_fac.inputs[0])
        tree.links.new(mix.outputs["Color"], moss_mix.inputs["Color1"])
        tree.links.new(moss.outputs["Color"], moss_mix.inputs["Color2"])
        tree.links.new(moss_fac.outputs[0], moss_mix.inputs["Fac"])
        tree.links.new(moss_mix.outputs["Color"], color_in)
    else:
        tree.links.new(mix.outputs["Color"], color_in)
    if "Roughness" in bsdf.inputs and not bsdf.inputs["Roughness"].is_linked:
        rough = tree.nodes.new("ShaderNodeMath")
        rough.operation = "MULTIPLY_ADD"
        rough.inputs[1].default_value = 0.45
        tree.links.new(decay.outputs[0], rough.inputs[0])
        rough.inputs[2].default_value = float(bsdf.inputs["Roughness"].default_value)
        tree.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    disp = _map("road_damaged" if kind == "road" else "cracked_concrete", "disp")
    if disp is not None and kind in ("road", "plaster"):
        out = next((node for node in tree.nodes if node.type == "OUTPUT_MATERIAL"), None)
        if out is not None:
            height = tree.nodes.new("ShaderNodeTexImage")
            height.image = _image(disp, False)
            tree.links.new(mapping.outputs["Vector"], height.inputs["Vector"])
            bump = tree.nodes.new("ShaderNodeDisplacement")
            bump.inputs["Midlevel"].default_value = 0.5
            strength = tree.nodes.new("ShaderNodeMath")
            strength.operation = "MULTIPLY"
            strength.inputs[1].default_value = 0.12 if kind == "road" else 0.04
            tree.links.new(decay.outputs[0], strength.inputs[0])
            tree.links.new(strength.outputs[0], bump.inputs["Scale"])
            tree.links.new(height.outputs["Color"], bump.inputs["Height"])
            tree.links.new(bump.outputs["Displacement"], out.inputs["Displacement"])
            material.displacement_method = "BOTH"
    material["age_stamp"] = True
    material["decay_hook"] = True


def stamp_object(obj, kind="plaster"):
    if obj is None:
        return
    stack = [obj]
    while stack:
        item = stack.pop()
        stack.extend(list(item.children))
        if getattr(item, "type", "") != "MESH":
            continue
        for slot in item.material_slots:
            stamp_material(slot.material, kind)


def arm_wreck(root):
    """A rust-texture mix on the hero. The Wreck value stays 0 until the years pile up."""
    if root is None:
        return
    stack = [root]
    while stack:
        obj = stack.pop()
        stack.extend(list(obj.children))
        if getattr(obj, "type", "") != "MESH":
            continue
        for slot in obj.material_slots:
            material = slot.material
            if material is None or material.get("wreck_mix") or material.node_tree is None:
                continue
            bsdf = _principled(material)
            diff = _map("rust_coarse_01", "diff")
            if bsdf is None or diff is None:
                continue
            tree = material.node_tree
            wreck = _value(tree, "Wreck")
            image = tree.nodes.new("ShaderNodeTexImage")
            image.image = _image(diff, True)
            coord = tree.nodes.new("ShaderNodeTexCoord")
            tree.links.new(coord.outputs["Object"], image.inputs["Vector"])
            mix = tree.nodes.new("ShaderNodeMixRGB")
            color_in = bsdf.inputs["Base Color"]
            if color_in.is_linked:
                source = color_in.links[0].from_socket
                tree.links.remove(color_in.links[0])
                tree.links.new(source, mix.inputs["Color1"])
            else:
                mix.inputs["Color1"].default_value = tuple(color_in.default_value)
            tree.links.new(image.outputs["Color"], mix.inputs["Color2"])
            faded = tree.nodes.new("ShaderNodeMath")
            faded.operation = "MULTIPLY"
            faded.inputs[1].default_value = 0.92
            tree.links.new(wreck.outputs[0], faded.inputs[0])
            tree.links.new(faded.outputs[0], mix.inputs["Fac"])
            tree.links.new(mix.outputs["Color"], color_in)
            if "Roughness" in bsdf.inputs:
                rough = tree.nodes.new("ShaderNodeMath")
                rough.operation = "MULTIPLY_ADD"
                rough.inputs[1].default_value = 0.75
                tree.links.new(wreck.outputs[0], rough.inputs[0])
                base = bsdf.inputs["Roughness"].default_value if not bsdf.inputs["Roughness"].is_linked else 0.35
                rough.inputs[2].default_value = float(base) if isinstance(base, (int, float)) else 0.35
                if not bsdf.inputs["Roughness"].is_linked:
                    tree.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
            material["wreck_mix"] = True


def set_named_value(name: str, amount: float):
    for material in bpy.data.materials:
        tree = material.node_tree
        if tree is None:
            continue
        node = tree.nodes.get(name)
        if node is not None and node.type == "VALUE":
            node.outputs[0].default_value = float(amount)


def _proto(slug: str):
    """Join the glTF into one mesh sitting on z=0. The import is removed from the scene."""
    cached = _PROTOS.get(slug)
    if cached is not None:
        return cached
    path = MOD / slug / f"{slug}_1k.gltf"
    if not path.exists():
        _PROTOS[slug] = None
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in fresh if obj.type == "MESH"]
    if not meshes:
        for obj in fresh:
            bpy.data.objects.remove(obj, do_unlink=True)
        _PROTOS[slug] = None
        return None
    bpy.context.view_layer.update()
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
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
    if not xs:
        bpy.data.objects.remove(obj, do_unlink=True)
        _PROTOS[slug] = None
        return None
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    z0 = min(zs)
    height = max(max(zs) - z0, 0.05)
    for vert in obj.data.vertices:
        vert.co.x -= cx
        vert.co.y -= cy
        vert.co.z -= z0
    mesh = obj.data
    mesh.name = f"found_{slug}"
    bpy.data.objects.remove(obj, do_unlink=True)
    for extra in fresh:
        if extra == obj:
            continue
        try:
            bpy.data.objects.remove(extra, do_unlink=True)
        except ReferenceError:
            pass
    _PROTOS[slug] = (mesh, height)
    return _PROTOS[slug]


def place(coll, slug: str, loc, yaw=0.0, height=1.0, name="plant"):
    """One cached plant, bottom on loc, scaled to height. None when the file is absent."""
    proto = _proto(slug)
    if proto is None:
        return None
    mesh, native = proto
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    scale = min(float(height) / native, 6.0)
    obj.scale = (scale, scale, scale)
    obj.rotation_euler.z = float(yaw)
    obj.location = Vector(loc)
    return obj


def clear_sky() -> Path | None:
    folder = ROOT / "polyhaven" / "hdri"
    if not folder.exists():
        return None
    found = sorted(folder.glob("kloofendal_43d_clear_puresky_*.hdr"))
    return found[0] if found else None


def grow_ivy(obj, seed, length=5.0, leaf_size=0.22, ivy_size=0.15, leaf_probability=0.72, float_length=0.35):
    """Blender's Ivy Gen, grown on obj from seed. Returns the new objects, or none."""
    addon = ROOT / "addons" / "add_curve_ivygen.py"
    if obj is None or not addon.exists():
        return []
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("add_curve_ivygen", addon)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(bpy.types.WindowManager, "ivy_gen_props"):
            module.register()
        props = bpy.context.window_manager.ivy_gen_props
        props.maxIvyLength = float(length)
        props.ivySize = float(ivy_size)
        props.ivyLeafSize = float(leaf_size)
        props.ivyBranchSize = 0.02
        props.leafProbability = float(leaf_probability)
        props.branchingProbability = 0.18
        props.gravityWeight = 0.55
        props.adhesionWeight = 0.95
        props.maxAdhesionDistance = 2.2
        props.maxFloatLength = float(float_length)
        bpy.context.scene.cursor.location = Vector(seed)
        for selected in bpy.context.view_layer.objects:
            selected.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        before = set(bpy.data.objects)
        bpy.ops.curve.ivy_gen(updateIvy=True, defaultIvy=False)
    except Exception:
        return []
    grown = [item for item in bpy.data.objects if item not in before]
    leaf = pbr_material("IvyLeaf", "forest_leaves_02", uv=1.2)
    for item in grown:
        if item.type == "MESH" and leaf is not None and item.material_slots:
            item.material_slots[0].material = leaf
        elif item.type == "MESH" and leaf is not None:
            item.data.materials.append(leaf)
    return grown
