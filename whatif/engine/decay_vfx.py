"""Owner decay toolkit. One value per channel, applied to the same buildings.

Erosion is a noise mask plus pointiness and ambient occlusion. Displace
crumbles those meshes. Ivy and moss grow by proximity to one animated sphere,
and Ivy Gen climbs the facades and the bridge pillars. Street grass follows a
crack mask that widens with the years. The river deck and the camera-facing
buildings are cell-fractured, held by breakable fixed constraints, and baked
once into a cache. Stills read that cache. They do not run the simulation.
Dust is a gas flow on the pieces plus a volume that only thickens while they
are moving. Year 500 swaps the avenue for an A.N.T. landscape and a forest of
instanced trees.
"""

from __future__ import annotations

import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

from engine import cc0_city
from engine import found_assets
from engine.city_layout import AVE_Y, FAR_Z, ROAD_Z

FRACTURE_CACHE = Path("/opt/cursor/asset-cache/private/fracture_cache/building_eras_v5.blend")


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
    hosts = []
    if host is not None:
        hosts.append(host)
    for item in kit.items:
        if item.role != "frontage" or item.obj == host or item.obj.type != "MESH":
            continue
        loc = item.obj.location
        if -90.0 < loc.x < 70.0 and -20.0 < loc.y < 20.0:
            hosts.append(item.obj)
    for obj in hosts[:4]:
        _ivy_on(kit, obj, 7.5)
    legs = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith("leg")]
    legs.sort(key=lambda obj: obj.matrix_world.translation.y)
    for leg in legs[:2]:
        _ivy_on(kit, leg, 9.0)


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


def _enable_vfx_addons():
    """Cell Fracture and A.N.T. Landscape. Blender 4.5 ships them as extensions."""
    import addon_utils

    for module in ("bl_ext.user_default.cell_fracture", "bl_ext.user_default.antlandscape"):
        try:
            addon_utils.enable(module, default_set=False, persistent=False)
        except Exception as exc:
            print("addon", module, exc)
    return hasattr(bpy.ops.object, "add_fracture_cell_objects"), hasattr(bpy.ops.mesh, "landscape_add")


def _ivy_on(kit, obj, length):
    if obj is None or obj.type != "MESH":
        return 0
    seed = obj.matrix_world.translation + Vector((0.4, -0.6, max(obj.dimensions.z, 1.0) * 0.35))
    grown = found_assets.grow_ivy(obj, (seed.x, seed.y, seed.z), length=length)
    for item in grown:
        kit.add(item, "weed", delay=0.26, sink=False, leaf=(0.16, 0.38, 0.12, 1))
    return len(grown)


def _world_copy(src, coll, name):
    """A world-space duplicate, light enough for a boolean fracture."""
    bpy.context.view_layer.update()
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.transform(src.matrix_world)
    if not bm.verts:
        bm.free()
        return None
    center = sum((vert.co for vert in bm.verts), Vector()) / len(bm.verts)
    for vert in bm.verts:
        vert.co -= center
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.location = center
    if src.data.materials:
        mesh.materials.append(src.data.materials[0])
    verts = len(mesh.vertices)
    if verts > 1600:
        ratio = min(0.4, 1400.0 / verts)
        mod = obj.modifiers.new("Lite", "DECIMATE")
        mod.ratio = ratio
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError as exc:
            print("decimate", name, exc)
    return obj


def _keep_band(obj, low_frac, high_frac):
    """Drop vertices outside a fraction of the mesh height. Roofs stay, bases go."""
    mesh = obj.data
    zs = [vert.co.z for vert in mesh.vertices]
    if not zs:
        return False
    lo, hi = min(zs), max(zs)
    span = max(hi - lo, 0.01)
    low = lo + span * low_frac
    high = lo + span * high_frac
    bm = bmesh.new()
    bm.from_mesh(mesh)
    kill = [vert for vert in bm.verts if vert.co.z < low - 0.02 or vert.co.z > high + 0.02]
    if len(kill) >= len(bm.verts):
        bm.free()
        return False
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    if not bm.faces:
        bm.free()
        return False
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return True


def _cell_fracture(obj, limit):
    before = set(bpy.data.objects)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.add_fracture_cell_objects(
            source={"VERT_OWN"},
            source_limit=int(limit),
            source_noise=0.18,
            recursion=0,
            use_smooth_faces=False,
            use_sharp_edges=False,
            use_sharp_edges_apply=False,
            use_data_match=True,
            use_island_split=False,
            margin=0.015,
            use_recenter=True,
            use_remove_original=False,
            collection_name="",
            use_debug_points=False,
            use_debug_redraw=False,
            use_debug_bool=False,
            mass_mode="UNIFORM",
            mass=18.0,
        )
    except RuntimeError as exc:
        print("cell fracture", obj.name, exc)
        return []
    return [item for item in bpy.data.objects if item not in before and item.type == "MESH"]


def _pin_shards(shards, coll, reach, threshold):
    centers = [shard.matrix_world.translation.copy() for shard in shards]
    joints = []
    for index, left in enumerate(shards):
        for follow, right in enumerate(shards[index + 1:], start=index + 1):
            if (centers[index] - centers[follow]).length > reach:
                continue
            empty = bpy.data.objects.new("era_fix", None)
            coll.objects.link(empty)
            empty.location = (centers[index] + centers[follow]) * 0.5
            bpy.ops.object.select_all(action="DESELECT")
            empty.select_set(True)
            bpy.context.view_layer.objects.active = empty
            try:
                bpy.ops.rigidbody.constraint_add()
            except RuntimeError:
                continue
            con = empty.rigid_body_constraint
            if con is None:
                continue
            con.type = "FIXED"
            con.object1 = left
            con.object2 = right
            con.use_breaking = True
            con.breaking_threshold = float(threshold)
            joints.append(empty)
            if len(joints) >= 16:
                return joints
    return joints


def _activate(obj, passive=False):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if obj.rigid_body is None:
        try:
            bpy.ops.rigidbody.object_add()
        except RuntimeError as exc:
            print("rigid body", obj.name, exc)
            return
    body = obj.rigid_body
    if body is None:
        return
    body.type = "PASSIVE" if passive else "ACTIVE"
    body.collision_shape = "BOX" if passive else "CONVEX_HULL"
    body.friction = 0.85
    body.mass = 80.0 if passive else 18.0
    body.use_margin = True
    body.collision_margin = 0.04


def _bake_pose(shards, helpers, frames):
    """Run the rigid-body cache once and freeze the last frame onto the meshes."""
    scene = bpy.context.scene
    if scene.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    world = scene.rigidbody_world
    world.enabled = True
    world.point_cache.frame_start = 1
    world.point_cache.frame_end = int(frames)
    world.substeps_per_frame = 2
    world.solver_iterations = 6
    scene.frame_start = 1
    scene.frame_end = int(frames)
    try:
        with bpy.context.temp_override(scene=scene, point_cache=world.point_cache):
            bpy.ops.ptcache.free_bake()
    except RuntimeError:
        pass
    scene.frame_set(1)
    starts = [shard.matrix_world.copy() for shard in shards]
    with bpy.context.temp_override(scene=scene, point_cache=world.point_cache):
        bpy.ops.ptcache.bake(bake=True)
    scene.frame_set(int(frames))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    poses = []
    for shard, start in zip(shards, starts):
        pose = shard.evaluated_get(depsgraph).matrix_world.copy()
        now = pose.to_translation()
        origin = start.to_translation()
        # A shard that flies into the lens fills the frame. Keep it on the lot.
        if (now - origin).length > 28.0 or now.y < -15.0 or now.z > origin.z + 6.0:
            pose = start.copy()
            pose.translation.z = max(0.3, origin.z - 5.0)
        poses.append(pose)
    for shard, pose in zip(shards, poses):
        bpy.ops.object.select_all(action="DESELECT")
        shard.select_set(True)
        bpy.context.view_layer.objects.active = shard
        if shard.rigid_body is not None:
            try:
                bpy.ops.rigidbody.object_remove()
            except RuntimeError:
                pass
        shard.matrix_world = pose
    world.enabled = False
    # Deleting constraint empties while the rigid-body world still points at
    # them segfaults Blender 4.5. Park them out of the shot instead.
    for helper in helpers:
        helper.hide_render = True
        helper.hide_viewport = True
        helper.location.z = -400.0
        con = helper.rigid_body_constraint
        if con is not None:
            con.enabled = False
        if helper.rigid_body is not None:
            helper.rigid_body.kinematic = True
            helper.rigid_body.type = "PASSIVE"
    return poses


def _fracture_one(src, coll, limit, band, threshold):
    copy = _world_copy(src, coll, "fracture_src")
    if copy is None:
        return [], [], None
    if band is not None and not _keep_band(copy, band[0], band[1]):
        bpy.data.objects.remove(copy, do_unlink=True)
        return [], [], None
    shards = _cell_fracture(copy, limit)
    bpy.data.objects.remove(copy, do_unlink=True)
    sized = []
    for shard in shards:
        if max(shard.dimensions) > 40.0:
            bpy.data.objects.remove(shard, do_unlink=True)
            continue
        sized.append(shard)
    shards = sized
    if len(shards) < 2:
        for shard in shards:
            bpy.data.objects.remove(shard, do_unlink=True)
        return [], [], None
    for shard in shards:
        _activate(shard, passive=False)
    reach = 0.0
    centers = [shard.matrix_world.translation for shard in shards]
    for index, left in enumerate(centers):
        for right in centers[index + 1:]:
            reach = max(reach, (left - right).length)
    joints = _pin_shards(shards, coll, max(1.2, reach * 0.55), threshold)
    ground_z = min(center.z for center in centers) - 1.4
    ground = bpy.data.objects.new("era_ground", bpy.data.meshes.new("era_ground"))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(ground.data)
    bm.free()
    coll.objects.link(ground)
    ground.location = (sum(center.x for center in centers) / len(centers), sum(center.y for center in centers) / len(centers), ground_z)
    ground.scale = (40.0, 40.0, 0.4)
    _activate(ground, passive=True)
    return shards, joints, ground


def _link_cached(coll):
    if not FRACTURE_CACHE.exists():
        return []
    with bpy.data.libraries.load(str(FRACTURE_CACHE), link=False) as (src, dst):
        dst.objects = list(src.objects)
    loaded = []
    for obj in dst.objects:
        if obj is None or obj.type != "MESH":
            continue
        coll.objects.link(obj)
        loaded.append(obj)
    return loaded


def _store_cache(shards):
    FRACTURE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    blocks = set(shards)
    blocks.update(shard.data for shard in shards if shard.data is not None)
    bpy.data.libraries.write(str(FRACTURE_CACHE), blocks, fake_user=True)


def fracture_buildings(kit):
    """Roofs at year 100, tower tops at year 500. Bake once, then reuse the cache."""
    cell_ok, _ant_ok = _enable_vfx_addons()
    coll = kit.collection("City")
    cached = _link_cached(coll)
    if cached:
        for obj in cached:
            role = "fracture500" if int(obj.get("era", 500)) >= 500 else "fracture100"
            kit.add(obj, role, sink=False)
        print("fracture cache", len(cached))
        return len(cached)
    if not cell_ok:
        print("cell fracture addon missing")
        return 0
    roofs = []
    tops = []
    for item in kit.items:
        obj = item.obj
        host = obj if obj.type == "MESH" and obj.data is not None else None
        if host is None:
            best_n = 0
            for child in obj.children_recursive:
                if child.type != "MESH" or child.data is None:
                    continue
                n = len(child.data.vertices)
                if 12 < n < 30000 and n > best_n:
                    host = child
                    best_n = n
        if host is None:
            continue
        count = len(host.data.vertices)
        if count < 12 or count > 8000 or max(host.dimensions) > 45.0:
            continue
        loc = host.matrix_world.translation
        if item.role == "frontage" and -120.0 < loc.x < 80.0 and -40.0 < loc.y < 30.0:
            roofs.append(host)
        elif item.role == "building_base" and -140.0 < loc.x < 160.0 and 140.0 < loc.y < 320.0:
            tops.append(host)
    roofs.sort(key=lambda obj: abs(obj.location.x + 20.0) + abs(obj.location.y))
    tops.sort(key=lambda obj: abs(obj.location.x) + abs(obj.location.y - 180.0))
    print("fracture candidates", len(roofs), len(tops), flush=True)
    made = []
    helpers = []
    # One bake for every building. A second point-cache bake segfaults Blender 4.5.
    for obj, limit, band, threshold, era, role, name in (
        *[(obj, 8, (0.62, 1.0), 12.0, 100, "fracture100", "era100_roof") for obj in roofs[:2]],
        *[(obj, 10, (0.22, 1.0), 6.0, 500, "fracture500", "era500_top") for obj in tops[:2]],
    ):
        shards, joints, ground = _fracture_one(obj, coll, limit, band, threshold)
        helpers.extend(joints)
        if ground is not None:
            helpers.append(ground)
        for shard in shards:
            shard["era"] = era
            shard.name = name
            kit.add(shard, role, sink=False)
            made.append(shard)
    if made:
        _bake_pose(made, helpers, 24)
    if made:
        _store_cache(made)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 1800
    if scene.rigidbody_world is not None:
        scene.rigidbody_world.enabled = False
    print("fractured buildings", len(made))
    return len(made)


def ant_hills(kit):
    """Uneven ground where the asphalt was. Hidden until year 500."""
    _cell_ok, ant_ok = _enable_vfx_addons()
    if not ant_ok:
        print("ant landscape addon missing")
        return 0
    coll = kit.collection("Terrain")
    soil = found_assets.pbr_material("HillSoil", "leaves_forest_ground", uv=0.35) or kit.mats.get("dirt")
    placed = 0
    for name, size_x, size_y, loc, height, seed in (
        ("AvenueHills", 150.0, 24.0, (-6.0, AVE_Y, ROAD_Z + 0.12), 2.6, 11),
        ("FarHills", 220.0, 70.0, (10.0, 200.0, FAR_Z + 0.2), 4.2, 19),
    ):
        before = set(bpy.data.objects)
        try:
            bpy.ops.mesh.landscape_add(
                refresh=True,
                ant_terrain_name=name,
                subdivision_x=36,
                subdivision_y=22,
                mesh_size_x=size_x,
                mesh_size_y=size_y,
                random_seed=seed,
                noise_type="hetero_terrain",
                basis_type="PERLIN_NEW",
                noise_size=0.5,
                noise_depth=4,
                amplitude=0.42,
                frequency=1.15,
                dimension=0.9,
                lacunarity=2.05,
                height=height,
                height_offset=-0.35,
                at_cursor=False,
                smooth_mesh=True,
                tri_face=False,
                water_plane=False,
            )
        except RuntimeError as exc:
            print("ant", name, exc)
            continue
        created = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
        if not created:
            print("ant made nothing", name)
            continue
        land = created[0]
        for extra in created[1:]:
            bpy.data.objects.remove(extra, do_unlink=True)
        if land.name not in coll.objects:
            for holder in list(land.users_collection):
                holder.objects.unlink(land)
            coll.objects.link(land)
        land.location = loc
        if soil is not None:
            land.data.materials.clear()
            land.data.materials.append(soil)
        kit.add(land, "hills", sink=False)
        placed += 1
    return placed


def _ruin_forest_group():
    ng = bpy.data.node_groups.get("RuinForest")
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new("RuinForest", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    density = ng.interface.new_socket(name="Density", in_out="INPUT", socket_type="NodeSocketFloat")
    density.default_value = 0.012
    ng.interface.new_socket(name="Trees", in_out="INPUT", socket_type="NodeSocketCollection")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = ng.nodes
    links = ng.links
    gin = nodes.new("NodeGroupInput")
    gout = nodes.new("NodeGroupOutput")
    dist = nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = "RANDOM"
    links.new(gin.outputs["Geometry"], dist.inputs["Mesh"])
    links.new(gin.outputs["Density"], dist.inputs["Density"])
    plants = nodes.new("GeometryNodeCollectionInfo")
    plants.inputs["Separate Children"].default_value = True
    plants.inputs["Reset Children"].default_value = False
    links.new(gin.outputs["Trees"], plants.inputs["Collection"])
    inst = nodes.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True
    links.new(dist.outputs["Points"], inst.inputs["Points"])
    links.new(plants.outputs["Instances"], inst.inputs["Instance"])
    yaw = nodes.new("FunctionNodeRandomValue")
    yaw.data_type = "FLOAT"
    yaw.inputs[2].default_value = 0.0
    yaw.inputs[3].default_value = 6.28318
    spin = nodes.new("ShaderNodeCombineXYZ")
    links.new(yaw.outputs[1], spin.inputs["Z"])
    links.new(spin.outputs["Vector"], inst.inputs["Rotation"])
    scale_rng = nodes.new("FunctionNodeRandomValue")
    scale_rng.data_type = "FLOAT"
    scale_rng.inputs[2].default_value = 0.65
    scale_rng.inputs[3].default_value = 1.85
    scale = nodes.new("ShaderNodeCombineXYZ")
    for axis in ("X", "Y", "Z"):
        links.new(scale_rng.outputs[1], scale.inputs[axis])
    links.new(scale.outputs["Vector"], inst.inputs["Scale"])
    links.new(inst.outputs["Instances"], gout.inputs["Geometry"])
    return ng


def scatter_ruin_forest(kit):
    """Thousands of instanced trees over the year-500 ruins. The meshes are not copied."""
    sources = []
    for item in kit.items:
        obj = item.obj
        if item.role != "tree_canopy" or obj.type != "MESH" or obj.data is None:
            continue
        if len(obj.data.vertices) > 20000:
            continue
        sources.append(obj)
        if len(sources) >= 4:
            break
    if len(sources) < 2 and cc0_city.ready():
        for kind, height in (("round", 9.0), ("pine", 12.0)):
            built = cc0_city.place_tree(kit.collection("Plants"), 0.0, 0.0, -80.0, height, kind)
            if built is not None:
                sources.append(built)
    if not sources:
        print("ruin forest has no tree")
        return 0
    protos = bpy.data.collections.new("RuinTreeProtos")
    for index, src in enumerate(sources):
        proto = bpy.data.objects.new(f"ruin_tree_{index}", src.data)
        proto.scale = src.scale.copy()
        proto.rotation_euler = src.rotation_euler.copy()
        protos.objects.link(proto)
    group = _ruin_forest_group()
    coll = kit.collection("Plants")
    placed = 0
    for name, loc, size, density in (
        ("ruin_canopy", (16.0, 240.0, FAR_Z + 0.15), (380.0, 240.0), 0.009),
        ("street_canopy", (-8.0, AVE_Y, ROAD_Z + 0.2), (140.0, 18.0), 0.045),
    ):
        bm = bmesh.new()
        w, d = size
        verts = [bm.verts.new(co) for co in ((-w / 2, -d / 2, 0.0), (w / 2, -d / 2, 0.0), (w / 2, d / 2, 0.0), (-w / 2, d / 2, 0.0))]
        bm.faces.new(verts)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        coll.objects.link(obj)
        obj.location = loc
        mod = obj.modifiers.new("RuinForest", "NODES")
        mod.node_group = group
        mod.show_viewport = False
        trees = _socket(mod, "Trees")
        thick = _socket(mod, "Density")
        if trees:
            mod[trees] = protos
        if thick:
            mod[thick] = density
        kit.add(obj, "swallow", sink=False)
        placed += 1
    print("ruin forest patches", placed, "protos", len(sources))
    return placed


def install(kit):
    arm_buildings(kit)
    fracture_buildings(kit)
    ant_hills(kit)
    scatter_ruin_forest(kit)
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
    # Year 1 is only stained. Year 100 is fully eaten. Year 500 stays there.
    erode = max(0.0, min(1.0, (max(veg, collapse) - 0.16) / 0.5))
    grime = max(0.0, min(1.0, (veg - 0.1) / 0.52))
    crack = max(0.0, min(1.0, (veg - 0.16) / 0.5))
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
    """Sweep the sun during a time jump. The last frames of a beat stay at noon.

    A still is the last frame of the beat. Leaving the spin running there
    dropped the sun behind the range and the city read as a night shot.
    """
    if beat_id not in {"weeds", "houses", "towers", "bridge", "forest"}:
        return 0.0
    ends = {"weeds": 498, "houses": 746, "towers": 871, "bridge": 984, "forest": 1096}
    end = ends.get(beat_id)
    if end is not None and frame >= end - 3:
        return 0.0
    return (frame / max(fps, 1.0)) * 6.28318 * 2.0
