"""Owner decay toolkit. One value per channel, applied to the same buildings.

Erosion is a noise mask plus pointiness and ambient occlusion. Displace
crumbles those meshes. Ivy and moss grow by proximity to one animated sphere.
Street grass follows a crack mask that widens with the years. The river deck
is cell-fractured, held by breakable fixed constraints, and dropped by the
collapse trigger. Dust is a gas flow on the pieces plus a volume that only
thickens while they are moving.
"""

from __future__ import annotations

import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from engine import found_assets


def _value(tree, name):
    node = tree.nodes.get(name)
    if node is None or node.type != "VALUE":
        node = tree.nodes.new("ShaderNodeValue")
        node.name = name
        node.label = name
    return node


def arm_erosion(material):
    """Noise eats the wall. Grime collects in creases. Both stay at 0 on day 1."""
    if material is None or material.get("erode_arm") or material.node_tree is None:
        return
    low = material.name.lower()
    if any(token in low for token in ("water", "leaf", "canopy", "flame", "skin", "mark", "grass", "soil")):
        return
    tree = material.node_tree
    bsdf = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None or "Base Color" not in bsdf.inputs:
        return
    color_in = bsdf.inputs["Base Color"]
    erode = _value(tree, "Erode")
    grime = _value(tree, "Grime")
    erode.outputs[0].default_value = 0.0
    grime.outputs[0].default_value = 0.0
    geom = tree.nodes.new("ShaderNodeNewGeometry")
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.55
    tree.links.new(geom.outputs["Position"], noise.inputs["Vector"])
    # The mask crosses zero only after Erode has risen, so day 1 stays clean.
    eat = tree.nodes.new("ShaderNodeMath")
    eat.operation = "MULTIPLY_ADD"
    eat.inputs[1].default_value = 1.35
    tree.links.new(erode.outputs[0], eat.inputs[2])
    tree.links.new(noise.outputs["Fac"], eat.inputs[0])
    eat.inputs[2].default_value = -0.72
    # Rebuild: fac = noise * 1.4 + (erode - 1) so erode 0 => negative, erode 1 => noise-ish.
    sub = tree.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[0].default_value = 0.15
    tree.links.new(erode.outputs[0], sub.inputs[1])
    # fac = noise + erode - 0.85
    add = tree.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    tree.links.new(noise.outputs["Fac"], add.inputs[0])
    tree.links.new(erode.outputs[0], add.inputs[1])
    bias = tree.nodes.new("ShaderNodeMath")
    bias.operation = "SUBTRACT"
    bias.inputs[1].default_value = 0.92
    tree.links.new(add.outputs[0], bias.inputs[0])
    eroded = tree.nodes.new("ShaderNodeMixRGB")
    if color_in.is_linked:
        source = color_in.links[0].from_socket
        tree.links.remove(color_in.links[0])
        tree.links.new(source, eroded.inputs["Color1"])
    else:
        eroded.inputs["Color1"].default_value = tuple(color_in.default_value)
    eroded.inputs["Color2"].default_value = (0.22, 0.16, 0.12, 1.0)
    tree.links.new(bias.outputs[0], eroded.inputs["Fac"])
    point = tree.nodes.new("ShaderNodeMath")
    point.operation = "SUBTRACT"
    point.inputs[0].default_value = 1.0
    tree.links.new(geom.outputs["Pointiness"], point.inputs[1])
    ao = tree.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.8
    crease = tree.nodes.new("ShaderNodeMath")
    crease.operation = "MULTIPLY"
    tree.links.new(point.outputs[0], crease.inputs[0])
    ao_inv = tree.nodes.new("ShaderNodeMath")
    ao_inv.operation = "SUBTRACT"
    ao_inv.inputs[0].default_value = 1.0
    tree.links.new(ao.outputs["AO"], ao_inv.inputs[1])
    tree.links.new(ao_inv.outputs[0], crease.inputs[1])
    dirt_fac = tree.nodes.new("ShaderNodeMath")
    dirt_fac.operation = "MULTIPLY"
    tree.links.new(grime.outputs[0], dirt_fac.inputs[0])
    tree.links.new(crease.outputs[0], dirt_fac.inputs[1])
    dirty = tree.nodes.new("ShaderNodeMixRGB")
    tree.links.new(eroded.outputs["Color"], dirty.inputs["Color1"])
    dirty.inputs["Color2"].default_value = (0.10, 0.08, 0.06, 1.0)
    tree.links.new(dirt_fac.outputs[0], dirty.inputs["Fac"])
    tree.links.new(dirty.outputs["Color"], color_in)
    material["erode_arm"] = True


def crack_material(name, slug):
    """Grass photo that only appears inside a widening crack mask."""
    mat = found_assets.pbr_material(name, slug, uv=1.0)
    if mat is None or mat.node_tree is None:
        return None
    tree = mat.node_tree
    bsdf = next((node for node in tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    out = next((node for node in tree.nodes if node.type == "OUTPUT_MATERIAL"), None)
    if bsdf is None or out is None:
        return mat
    crack = _value(tree, "Crack")
    crack.outputs[0].default_value = 0.0
    noise = tree.nodes.new("ShaderNodeTexVoronoi")
    noise.inputs["Scale"].default_value = 3.5
    geom = tree.nodes.new("ShaderNodeNewGeometry")
    tree.links.new(geom.outputs["Position"], noise.inputs["Vector"])
    opened = tree.nodes.new("ShaderNodeMath")
    opened.operation = "SUBTRACT"
    tree.links.new(crack.outputs[0], opened.inputs[0])
    tree.links.new(noise.outputs["Distance"], opened.inputs[1])
    wide = tree.nodes.new("ShaderNodeMath")
    wide.operation = "MULTIPLY"
    wide.inputs[1].default_value = 2.4
    tree.links.new(opened.outputs[0], wide.inputs[0])
    trans = tree.nodes.new("ShaderNodeBsdfTransparent")
    mix = tree.nodes.new("ShaderNodeMixShader")
    tree.links.new(wide.outputs[0], mix.inputs["Fac"])
    tree.links.new(trans.outputs["BSDF"], mix.inputs[1])
    if out.inputs["Surface"].is_linked:
        src = out.inputs["Surface"].links[0].from_socket
        tree.links.remove(out.inputs["Surface"].links[0])
        tree.links.new(src, mix.inputs[2])
    tree.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat["crack_mask"] = True
    return mat


def _displace(obj):
    if obj is None or obj.type != "MESH":
        return
    if obj.modifiers.get("Erode"):
        return
    tex = bpy.data.textures.get("ErodeVoronoi")
    if tex is None:
        tex = bpy.data.textures.new("ErodeVoronoi", "VORONOI")
        tex.noise_scale = 1.4
        tex.distance_metric = "DISTANCE"
    mod = obj.modifiers.new("Erode", "DISPLACE")
    mod.texture = tex
    mod.texture_coords = "OBJECT"
    mod.strength = 0.0
    mod.mid_level = 0.62
    mod.direction = "NORMAL"


def _overgrowth_group():
    ng = bpy.data.node_groups.get("Overgrowth")
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new("Overgrowth", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    spread = ng.interface.new_socket(name="Spread", in_out="INPUT", socket_type="NodeSocketFloat")
    spread.default_value = 0.0
    ng.interface.new_socket(name="Sphere", in_out="INPUT", socket_type="NodeSocketObject")
    ng.interface.new_socket(name="Plants", in_out="INPUT", socket_type="NodeSocketCollection")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = ng.nodes
    links = ng.links
    gin = nodes.new("NodeGroupInput")
    gout = nodes.new("NodeGroupOutput")
    gin.location = (-900, 0)
    gout.location = (700, 0)
    dist = nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = "RANDOM"
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.22
    links.new(gin.outputs["Spread"], mul.inputs[0])
    links.new(gin.outputs["Geometry"], dist.inputs["Mesh"])
    links.new(mul.outputs[0], dist.inputs["Density"])
    info = nodes.new("GeometryNodeObjectInfo")
    links.new(gin.outputs["Sphere"], info.inputs["Object"])
    pos = nodes.new("GeometryNodeInputPosition")
    delta = nodes.new("ShaderNodeVectorMath")
    delta.operation = "SUBTRACT"
    links.new(pos.outputs["Position"], delta.inputs[0])
    links.new(info.outputs["Location"], delta.inputs[1])
    length = nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    links.new(delta.outputs["Vector"], length.inputs[0])
    cmp = nodes.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "GREATER_THAN"
    links.new(length.outputs["Value"], cmp.inputs[0])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(info.outputs["Scale"], sep.inputs["Vector"])
    links.new(sep.outputs["X"], cmp.inputs[1])
    delete = nodes.new("GeometryNodeDeleteGeometry")
    links.new(dist.outputs["Points"], delete.inputs["Geometry"])
    links.new(cmp.outputs["Result"], delete.inputs["Selection"])
    plants = nodes.new("GeometryNodeCollectionInfo")
    plants.inputs["Separate Children"].default_value = True
    plants.inputs["Reset Children"].default_value = True
    links.new(gin.outputs["Plants"], plants.inputs["Collection"])
    inst = nodes.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True
    links.new(delete.outputs["Geometry"], inst.inputs["Points"])
    links.new(plants.outputs["Instances"], inst.inputs["Instance"])
    links.new(dist.outputs["Rotation"], inst.inputs["Rotation"])
    scale = nodes.new("ShaderNodeCombineXYZ")
    for axis in ("X", "Y", "Z"):
        scale.inputs[axis].default_value = 0.85
    links.new(scale.outputs["Vector"], inst.inputs["Scale"])
    join = nodes.new("GeometryNodeJoinGeometry")
    links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
    links.new(inst.outputs["Instances"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], gout.inputs["Geometry"])
    return ng


def _socket(mod, name):
    group = mod.node_group
    if group is None:
        return None
    for item in group.interface.items_tree:
        if item.name == name and item.in_out == "INPUT":
            return item.identifier
    return None


def _plant_collection():
    coll = bpy.data.collections.get("GrowPlants")
    if coll is None:
        coll = bpy.data.collections.new("GrowPlants")
        bpy.context.scene.collection.children.link(coll)
    if coll.objects:
        return coll
    for slug, height in (
        ("moss_01", 0.35),
        ("fern_02", 0.7),
        ("grass_medium_01", 0.55),
        ("grass_bermuda_01", 0.4),
    ):
        obj = found_assets.place(coll, slug, (0.0, 0.0, -40.0), 0.0, height, slug)
        if obj is not None:
            obj.hide_render = True
            obj.hide_viewport = True
    return coll


def _grow_sphere(coll):
    mesh = bpy.data.meshes.get("GrowSphereMesh")
    if mesh is None:
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        mesh = bpy.data.meshes.new("GrowSphereMesh")
        bm.to_mesh(mesh)
        bm.free()
    obj = bpy.data.objects.new("GrowSphere", mesh)
    coll.objects.link(obj)
    obj.location = (-30.0, 0.5, 4.0)
    obj.scale = (0.05, 0.05, 0.05)
    obj.hide_render = True
    obj.display_type = "WIRE"
    return obj


def arm_buildings(kit):
    """Displace and a proximity ivy/moss scatter on the same frontage meshes."""
    group = _overgrowth_group()
    plants = _plant_collection()
    sphere = _grow_sphere(kit.collection("City"))
    kit.grow_sphere = sphere
    seen = set()
    # Only the foreground blocks. Doing every tower blows the render memory.
    chosen = []
    for item in kit.items:
        if item.role != "frontage" or item.obj.type != "MESH":
            continue
        loc = item.obj.location
        if -80.0 < loc.x < 30.0 and -15.0 < loc.y < 12.0:
            chosen.append(item)
    chosen.sort(key=lambda item: abs(item.obj.location.x + 32.8) + abs(item.obj.location.y - 0.3))
    for item in chosen[:10]:
        obj = item.obj
        for slot in obj.material_slots:
            if slot.material is not None and slot.material.name not in seen:
                seen.add(slot.material.name)
                arm_erosion(slot.material)
        _displace(obj)
        if obj.modifiers.get("Overgrowth"):
            continue
        mod = obj.modifiers.new("Overgrowth", "NODES")
        mod.node_group = group
        spread = _socket(mod, "Spread")
        ball = _socket(mod, "Sphere")
        planted = _socket(mod, "Plants")
        if spread:
            mod[spread] = 0.0
        if ball:
            mod[ball] = sphere
        if planted:
            mod[planted] = plants
        obj["over_spread"] = spread or ""
    # Ivy Generator on the avenue building the facade drone looks at.
    host = None
    best = 1e9
    for item in kit.items:
        if item.role != "frontage":
            continue
        loc = item.obj.location
        score = abs(loc.x + 32.8) + abs(loc.y - 0.3)
        if score < best:
            best = score
            host = item.obj
    if host is not None:
        for grown in found_assets.grow_ivy(host, (host.location.x, host.location.y - 4.2, host.location.z + 3.2), length=6.5):
            kit.add(grown, "weed", delay=0.32, sink=False, leaf=(0.16, 0.38, 0.12, 1))


def fracture_deck(obj, coll):
    """Split the river deck into cells and pin them with breakable fixed joints."""
    if obj is None or obj.type != "MESH" or obj.data is None or obj.get("fractured"):
        return []
    src = bmesh.new()
    src.from_mesh(obj.data)
    src.faces.ensure_lookup_table()
    if not src.faces:
        src.free()
        return []
    centers = [face.calc_center_median() for face in src.faces]
    lo = Vector((min(c.x for c in centers), min(c.y for c in centers), min(c.z for c in centers)))
    hi = Vector((max(c.x for c in centers), max(c.y for c in centers), max(c.z for c in centers)))
    span = hi - lo
    axis = 1 if span.y >= span.x else 0
    rng = random.Random(7)
    count = 22
    sites = []
    for _ in range(count):
        sites.append(Vector((
            rng.uniform(lo.x, hi.x),
            rng.uniform(lo.y, hi.y),
            rng.uniform(lo.z, hi.z),
        )))
    groups = {i: [] for i in range(count)}
    for face, center in zip(src.faces, centers):
        owner = min(range(count), key=lambda i: (center - sites[i]).length_squared)
        groups[owner].append(face)
    pieces = []
    scene = bpy.context.scene
    if scene.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    if scene.rigidbody_world is not None:
        scene.rigidbody_world.enabled = False
    along_span = max(span[axis], 0.01)
    for index, faces in groups.items():
        if len(faces) < 2:
            continue
        bm = bmesh.new()
        verts = {}
        for face in faces:
            copied = []
            for vert in face.verts:
                key = vert.index
                if key not in verts:
                    verts[key] = bm.verts.new(vert.co)
                copied.append(verts[key])
            try:
                bm.faces.new(copied)
            except ValueError:
                continue
        if not bm.faces:
            bm.free()
            continue
        me = bpy.data.meshes.new(f"span_cell_{index}")
        bm.to_mesh(me)
        bm.free()
        piece = bpy.data.objects.new(f"span_cell_{index}", me)
        coll.objects.link(piece)
        piece.parent = obj
        piece.matrix_parent_inverse = Matrix.Identity(4)
        piece.location = (0.0, 0.0, 0.0)
        mid = sum((face.calc_center_median() for face in faces), Vector()) / len(faces)
        piece["span_t"] = (mid[axis] - lo[axis]) / along_span
        piece["rest_loc"] = [0.0, 0.0, 0.0]
        piece.hide_render = True
        bpy.context.view_layer.objects.active = piece
        try:
            bpy.ops.rigidbody.object_add()
        except RuntimeError:
            pass
        if piece.rigid_body is not None:
            piece.rigid_body.type = "ACTIVE"
            piece.rigid_body.kinematic = True
            piece.rigid_body.collision_shape = "CONVEX_HULL"
            piece.rigid_body.mass = 40.0
            piece.rigid_body.use_deactivation = True
            piece.rigid_body.use_start_deactivated = True
        if piece.material_slots:
            piece.data.materials.append(obj.data.materials[0] if obj.data.materials else None)
        elif obj.data.materials:
            piece.data.materials.append(obj.data.materials[0])
        pieces.append(piece)
    src.free()
    # Breakable fixed joints between cells that sit next to each other along the span.
    ordered = sorted(pieces, key=lambda item: float(item["span_t"]))
    for left, right in zip(ordered, ordered[1:]):
        joint = bpy.data.objects.new("span_fix", None)
        coll.objects.link(joint)
        joint.empty_display_size = 0.2
        joint.location = (left.matrix_world.translation + right.matrix_world.translation) * 0.5
        bpy.context.view_layer.objects.active = joint
        try:
            bpy.ops.rigidbody.constraint_add()
        except RuntimeError:
            continue
        con = joint.rigid_body_constraint
        if con is None:
            continue
        con.type = "FIXED"
        con.object1 = left
        con.object2 = right
        con.use_breaking = True
        con.breaking_threshold = 35.0
    # Rebar hanging off the two cells that border the future gap.
    rust = found_assets.pbr_material("BreakRebar", "rusty_metal_02", uv=0.8)
    for piece in ordered:
        t = float(piece["span_t"])
        if abs(t - 0.34) > 0.06 and abs(t - 0.66) > 0.06:
            continue
        for side in (-0.4, 0.4):
            bar = found_assets.place(coll, "dry_branches_medium_01", (0, 0, 0), 0.2, 0.45, "rebar")
            if bar is None or rust is None:
                # A thin cylinder stands in when the plant proxy is the wrong shape.
                bm = bmesh.new()
                bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=0.04, radius2=0.04, depth=1.6)
                me = bpy.data.meshes.new("rebar_rod")
                bm.to_mesh(me)
                bm.free()
                bar = bpy.data.objects.new("rebar", me)
                coll.objects.link(bar)
                if rust is not None:
                    bar.data.materials.append(rust)
            bar.parent = piece
            bar.location = Vector((side, 0.0, -0.15))
            bar.rotation_euler = (1.2, side, 0.4)
            bar.name = "rebar"
    # Kinematic trigger. apply() drives it through the span as collapse rises.
    trigger = bpy.data.objects.new("CollapseTrigger", bpy.data.meshes.new("trigger"))
    coll.objects.link(trigger)
    trigger.empty_display_type = "CUBE"
    trigger.empty_display_size = 1.2
    trigger.location = obj.location + Vector((0.0, 0.0, 8.0))
    bpy.context.view_layer.objects.active = trigger
    try:
        bpy.ops.rigidbody.object_add()
    except RuntimeError:
        pass
    if trigger.rigid_body is not None:
        trigger.rigid_body.type = "PASSIVE"
        trigger.rigid_body.kinematic = True
    # Gas domain and a flow on the middle cell. The volume below is what a still sees
    # after the sim has settled; the flow is velocity-driven for the encode.
    domain = bpy.data.objects.new("CollapseDust", bpy.data.meshes.new("dust_domain"))
    coll.objects.link(domain)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(domain.data)
    bm.free()
    domain.location = obj.location
    domain.scale = (18.0, 28.0, 12.0)
    domain.hide_render = True
    try:
        mod = domain.modifiers.new("Fluid", "FLUID")
        mod.fluid_type = "DOMAIN"
        mod.domain_settings.domain_type = "GAS"
        mod.domain_settings.resolution_max = 24
        mod.domain_settings.use_adaptive_domain = True
        if ordered:
            flow_host = ordered[len(ordered) // 2]
            flow = flow_host.modifiers.new("Fluid", "FLUID")
            flow.fluid_type = "FLOW"
            flow.flow_settings.flow_type = "SMOKE"
            flow.flow_settings.flow_behavior = "INFLOW"
            flow.flow_settings.use_initial_velocity = True
            flow.flow_settings.velocity_factor = 1.0
    except (AttributeError, TypeError, RuntimeError):
        pass
    dust = bpy.data.objects.new("SettledDust", domain.data)
    # Separate mesh so the domain scale does not stretch the still volume.
    dust_mesh = bpy.data.meshes.new("settled_dust")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(dust_mesh)
    bm.free()
    dust = bpy.data.objects.new("SettledDust", dust_mesh)
    coll.objects.link(dust)
    dust.location = obj.location + Vector((0.0, 4.0, 2.0))
    dust.scale = (16.0, 22.0, 8.0)
    vol = bpy.data.materials.new("CollapseHaze")
    vol.use_nodes = True
    tree = vol.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    principled = tree.nodes.new("ShaderNodeVolumePrincipled")
    amount = _value(tree, "Dust")
    tree.links.new(amount.outputs[0], principled.inputs["Density"])
    principled.inputs["Color"].default_value = (0.55, 0.5, 0.45, 1.0)
    tree.links.new(principled.outputs["Volume"], out.inputs["Volume"])
    dust.data.materials.append(vol)
    dust.hide_render = True
    obj["fractured"] = True
    return pieces, trigger, dust


def install(kit):
    arm_buildings(kit)
    deck = next((item.obj for item in kit.items if item.role == "bridge_deck" and item.extra.get("i") == 0), None)
    fractured = fracture_deck(deck, kit.collection("Bridge")) if deck is not None else []
    if fractured:
        pieces, trigger, dust = fractured
        kit.span_pieces = pieces
        kit.collapse_trigger = trigger
        kit.collapse_dust = dust
    else:
        kit.span_pieces = []
        kit.collapse_trigger = None
        kit.collapse_dust = None


def drive(kit, ch, frame, fps):
    """Push the global values. Day 1 stays at zero."""
    import bpy

    veg = float(ch.get("vegetation", 0.0))
    collapse = float(ch.get("collapse", 0.0))
    erode = max(0.0, min(1.0, (max(veg, collapse) - 0.18) / 0.72))
    grime = max(0.0, min(1.0, (veg - 0.12) / 0.7))
    crack = max(0.0, min(1.0, (veg - 0.22) / 0.7))
    for material in bpy.data.materials:
        tree = material.node_tree
        if tree is None:
            continue
        for name, value in (("Erode", erode), ("Grime", grime), ("Crack", crack)):
            node = tree.nodes.get(name)
            if node is not None and node.type == "VALUE":
                node.outputs[0].default_value = value
    for obj in bpy.data.objects:
        mod = obj.modifiers.get("Erode") if obj.type == "MESH" else None
        if mod is not None and mod.type == "DISPLACE":
            mod.strength = erode * 0.55
        spread_id = obj.get("over_spread")
        grow = obj.modifiers.get("Overgrowth") if hasattr(obj, "modifiers") else None
        if grow is not None and spread_id:
            grow[spread_id] = veg
    sphere = getattr(kit, "grow_sphere", None)
    if sphere is not None:
        radius = 0.2 + veg * 78.0
        sphere.scale = (radius, radius, radius)
    _drive_span(kit, collapse)
    dust = getattr(kit, "collapse_dust", None)
    if dust is not None and dust.data.materials:
        # Dust only while the pieces are actually moving, then it settles out.
        moving = max(0.0, 1.0 - abs(collapse - 0.72) / 0.18)
        tree = dust.data.materials[0].node_tree
        node = tree.nodes.get("Dust") if tree else None
        if node is not None:
            node.outputs[0].default_value = moving * 0.08
        dust.hide_render = moving < 0.04
    trigger = getattr(kit, "collapse_trigger", None)
    deck = next((item.obj for item in kit.items if item.role == "bridge_deck" and item.extra.get("i") == 0), None)
    if trigger is not None and deck is not None:
        trigger.location = deck.matrix_world.translation + Vector((0.0, (collapse - 0.45) * 40.0, 6.0 - collapse * 8.0))


def _drive_span(kit, collapse):
    pieces = getattr(kit, "span_pieces", None) or []
    dropping = max(0.0, min(1.0, (collapse - 0.58) / 0.28))
    show = collapse > 0.8
    for piece in pieces:
        piece.hide_render = not show
        t = float(piece.get("span_t", 0.5))
        gap = 1.0 - min(1.0, abs(t - 0.5) / 0.22)
        piece.location = Vector((0.0, 0.0, -9.5 * dropping * gap))
        piece.rotation_euler.x = dropping * gap * (0.9 if t < 0.5 else -0.7)
        for child in piece.children:
            child.hide_render = not show


def spin_sun(kit, frame, fps, beat_id):
    """Sweep the sun during a time jump. Review frames at the end of a beat stay put."""
    if beat_id not in {"weeds", "houses", "towers", "bridge", "forest"}:
        return 0.0
    # Two revolutions a second while the years are skipping.
    return (frame / max(fps, 1.0)) * 6.28318 * 2.0
