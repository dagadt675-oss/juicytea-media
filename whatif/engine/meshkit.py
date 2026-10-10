"""Low-level mesh, material, and object helpers for the what-if engine."""

from __future__ import annotations

import math
from mathutils import Euler, Matrix, Vector

import bpy
import bmesh


def lin(r, g, b, a=1.0):
    """sRGB 0..1 to linear."""

    def c(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

    return (c(r), c(g), c(b), a)


def smoother(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    t = (x - a) / (b - a)
    return t * t * (3.0 - 2.0 * t)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class Item:
    def __init__(self, obj, role, **extra):
        self.obj = obj
        self.role = role
        self.extra = extra
        self.base_loc = obj.location.copy()
        self.base_rot = obj.rotation_euler.copy()
        self.base_scale = obj.scale.copy()


class Kit:
    def __init__(self, scene):
        self.scene = scene
        self.items: list[Item] = []
        self.colls = {}
        self.mats = {}
        self.bridge = None
        self.kind = "city"
        self.water = None
        self.volume = None
        self.sun = None
        self.fill = None
        self.world_bg = None
        self.precip = []

    def collection(self, name):
        if name in self.colls:
            return self.colls[name]
        col = bpy.data.collections.new(name)
        self.scene.collection.children.link(col)
        self.colls[name] = col
        return col

    def add(self, obj, role, **extra):
        item = Item(obj, role, **extra)
        self.items.append(item)
        obj["role"] = role
        return item


def mesh_from_bm(name, bm):
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = False
    return me


def link_obj(name, me, coll, mats=()):
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    for mat in mats:
        if mat and mat.name not in [slot.name for slot in obj.data.materials]:
            obj.data.materials.append(mat)
    return obj


def empty(name, coll, loc):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.3
    obj.location = loc
    coll.objects.link(obj)
    return obj


def parent_keep(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)


def add_box(bm, center, size, mat_index=0):
    # Index by count. Face object ids are not stable across bmesh.ops.
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    nverts = len(bm.verts)
    nfaces = len(bm.faces)
    bmesh.ops.create_cube(bm, size=1.0)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    new_verts = list(bm.verts[nverts:])
    new_faces = list(bm.faces[nfaces:])
    for face in new_faces:
        face.material_index = mat_index
    cx, cy, cz = center
    sx, sy, sz = size
    for vert in new_verts:
        vert.co.x = vert.co.x * sx + cx
        vert.co.y = vert.co.y * sy + cy
        vert.co.z = vert.co.z * sz + cz
    return new_faces


def box_object(name, coll, center, size, mat, mats=None):
    bm = bmesh.new()
    add_box(bm, (0, 0, 0), size, 0)
    me = mesh_from_bm(name, bm)
    obj = link_obj(name, me, coll, mats or (mat,))
    obj.location = center
    return obj


def cylinder_mesh(name, radius=1.0, segments=6):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=1.0,
    )
    for vert in bm.verts:
        vert.co.z += 0.5
    return mesh_from_bm(name, bm)


def ico_object(name, coll, loc, scale, mat, subdivisions=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    me = mesh_from_bm(name, bm)
    obj = link_obj(name, me, coll, (mat,))
    obj.location = loc
    obj.scale = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    return obj


def aim_z(obj, p0, p1, radius):
    p0 = Vector(p0)
    p1 = Vector(p1)
    delta = p1 - p0
    dist = delta.length
    if dist < 1e-4:
        obj.scale = (0.0001, 0.0001, 0.0001)
        obj.hide_render = True
        return
    obj.hide_render = False
    obj.location = p0
    obj.scale = (radius, radius, dist)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()


def drive(target, data_path, index, expression, variables):
    fcurve = target.driver_add(data_path, index) if index is not None else target.driver_add(data_path)
    driver = fcurve.driver
    driver.type = "SCRIPTED"
    driver.expression = expression
    for name in variables:
        var = driver.variables.new()
        var.name = name
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "SCENE"
        var.targets[0].id = bpy.context.scene
        var.targets[0].data_path = f'["{name}"]'
    return fcurve


def _math(nt, op, a, b=None):
    node = nt.nodes.new("ShaderNodeMath")
    node.operation = op
    if isinstance(a, (int, float)):
        node.inputs[0].default_value = a
    else:
        nt.links.new(a, node.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            node.inputs[1].default_value = b
        else:
            nt.links.new(b, node.inputs[1])
    return node.outputs[0]


def _mix(nt, fac, c1, c2):
    node = nt.nodes.new("ShaderNodeMixRGB")
    node.blend_type = "MIX"
    if isinstance(fac, (int, float)):
        node.inputs["Fac"].default_value = fac
    else:
        nt.links.new(fac, node.inputs["Fac"])
    if isinstance(c1, (tuple, list)):
        node.inputs["Color1"].default_value = c1
    else:
        nt.links.new(c1, node.inputs["Color1"])
    if isinstance(c2, (tuple, list)):
        node.inputs["Color2"].default_value = c2
    else:
        nt.links.new(c2, node.inputs["Color2"])
    return node.outputs["Color"]


def channel_value(nt, names, expression):
    node = nt.nodes.new("ShaderNodeValue")
    drive(node.outputs[0], "default_value", None, expression, names)
    return node.outputs[0]


def weather_color(nt, base, weights):
    """Stack moss, rust, mud, scorch, snow, and wetness on a base color socket."""
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep_p = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geom.outputs["Position"], sep_p.inputs["Vector"])
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geom.outputs["Normal"], sep_n.inputs["Vector"])
    up = _math(nt, "MAXIMUM", _math(nt, "MINIMUM", sep_n.outputs["Z"], 1.0), 0.0)
    # Low faces pick up more moss and mud.
    low = nt.nodes.new("ShaderNodeMapRange")
    low.inputs["From Min"].default_value = 0.2
    low.inputs["From Max"].default_value = 12.0
    low.inputs["To Min"].default_value = 1.0
    low.inputs["To Max"].default_value = 0.25
    nt.links.new(sep_p.outputs["Z"], low.inputs["Value"])

    moss = channel_value(nt, ("moss", "vegetation"), "max(moss, vegetation * 0.8)")
    rust = channel_value(nt, ("rust",), "rust")
    mud = channel_value(nt, ("mud", "rain", "flood"), "max(mud, rain * 0.65 + flood * 0.15)")
    scorch = channel_value(nt, ("scorch", "heat", "fire"), "max(scorch, heat * 0.85, fire * 0.7)")
    snow = channel_value(nt, ("snow", "ice"), "max(snow, ice * 0.95)")
    wet = channel_value(nt, ("wet", "rain"), "max(wet, rain * 0.9)")

    color = base
    color = _mix(nt, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", moss, weights.get("moss", 0.0)), low.outputs["Result"]), color, lin(0.28, 0.40, 0.16))
    color = _mix(nt, _math(nt, "MULTIPLY", rust, weights.get("rust", 0.0)), color, lin(0.38, 0.16, 0.08))
    color = _mix(nt, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", mud, weights.get("mud", 0.0)), low.outputs["Result"]), color, lin(0.28, 0.20, 0.12))
    color = _mix(nt, _math(nt, "MULTIPLY", scorch, weights.get("scorch", 0.0)), color, lin(0.10, 0.07, 0.05))
    color = _mix(nt, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", snow, weights.get("snow", 0.0)), up), color, lin(0.93, 0.95, 0.97))
    darken = _math(nt, "MULTIPLY", wet, weights.get("wet", 0.7))
    # Mix toward a darker version of itself by blending with black.
    color = _mix(nt, _math(nt, "MULTIPLY", darken, 0.45), color, lin(0.02, 0.02, 0.025))
    rough = 0.55
    rough = _math(nt, "ADD", rough, _math(nt, "MULTIPLY", snow, 0.2))
    rough = _math(nt, "SUBTRACT", rough, _math(nt, "MULTIPLY", wet, 0.28))
    return color, rough


def principled(nt, color, rough, emission=None, emission_strength=0.0):
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if isinstance(color, (tuple, list)):
        bsdf.inputs["Base Color"].default_value = color
    else:
        nt.links.new(color, bsdf.inputs["Base Color"])
    if isinstance(rough, (int, float)):
        bsdf.inputs["Roughness"].default_value = rough
    else:
        nt.links.new(rough, bsdf.inputs["Roughness"])
    if emission is not None:
        if isinstance(emission, (tuple, list)):
            bsdf.inputs["Emission Color"].default_value = emission
        else:
            nt.links.new(emission, bsdf.inputs["Emission Color"])
        if isinstance(emission_strength, (int, float)):
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        else:
            nt.links.new(emission_strength, bsdf.inputs["Emission Strength"])
    return bsdf


def finish(nt, bsdf):
    out = nt.nodes["Material Output"]
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.location = (400, 0)
    out.location = (700, 0)


def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    nt.nodes.new("ShaderNodeOutputMaterial")
    return mat, nt


def make_surface(name, base, weights, roughness=0.55):
    mat, nt = new_material(name)
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = base
    color, rough = weather_color(nt, rgb.outputs[0], weights)
    # roughness returned is a socket already offset from 0.55. Blend toward the requested roughness
    # by just using the socket; the constant inside weather_color is a decent default.
    bsdf = principled(nt, color, rough if roughness == 0.55 else roughness)
    finish(nt, bsdf)
    return mat


def make_object_color_surface(name, weights):
    mat, nt = new_material(name)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    color, rough = weather_color(nt, info.outputs["Color"], weights)
    bsdf = principled(nt, color, rough)
    finish(nt, bsdf)
    return mat


def make_window_material():
    mat, nt = new_material("Window")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 0.0
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    nt.links.new(geom.outputs["Position"], noise.inputs["Vector"])
    lit = _math(nt, "GREATER_THAN", noise.outputs["Fac"], _math(nt, "ADD", 0.48, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", info.outputs["Random"], 0.5), 0.2)))
    night = channel_value(nt, ("day_night",), "clamp((day_night - 0.48) / 0.2, 0, 1)")
    power = channel_value(nt, ("power",), "power")
    strength = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", lit, night), _math(nt, "MULTIPLY", power, 14.0))
    glass = lin(0.16, 0.24, 0.32)
    warm = lin(1.0, 0.78, 0.42)
    color, _rough = weather_color(
        nt,
        _const_rgb(nt, glass),
        {"moss": 0.35, "snow": 0.45, "rust": 0.05, "mud": 0.15, "scorch": 0.4, "wet": 0.3},
    )
    emit_color = _mix(nt, lit, glass, warm)
    bsdf = principled(nt, color, 0.18, emission=emit_color, emission_strength=strength)
    finish(nt, bsdf)
    return mat


def _const_rgb(nt, color):
    node = nt.nodes.new("ShaderNodeRGB")
    node.outputs[0].default_value = color
    return node.outputs[0]


def make_water_material():
    mat, nt = new_material("Water")
    wave = nt.nodes.new("ShaderNodeMapping")
    wave.name = "Wave"
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
    fcurve = wave.inputs["Location"].driver_add("default_value", 0)
    fcurve.driver.type = "SCRIPTED"
    fcurve.driver.expression = "f * 0.02"
    var = fcurve.driver.variables.new()
    var.name = "f"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "SCENE"
    var.targets[0].id = bpy.context.scene
    var.targets[0].data_path = "frame_current"
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 2.0
    nt.links.new(wave.outputs["Vector"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.35
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    drive(bump.inputs["Strength"], "default_value", None, "0.12 + gravity * 0.55", ("gravity",))
    water_shift = channel_value(nt, ("water", "dust", "heat"), "clamp(-water, 0, 1) * 0.0 + dust * 0.35 + heat * 0.15")
    deep = lin(0.10, 0.32, 0.52)
    shallow = lin(0.22, 0.48, 0.62)
    muddy = lin(0.30, 0.26, 0.16)
    color = _mix(nt, water_shift, deep, muddy)
    bsdf = principled(nt, color, 0.08)
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    finish(nt, bsdf)
    mat["is_water"] = True
    return mat


def make_emission(name, color, strength=4.0):
    mat, nt = new_material(name)
    bsdf = principled(nt, color, 0.4, emission=color, emission_strength=strength)
    finish(nt, bsdf)
    return mat


def make_volume():
    mat, nt = new_material("Fog")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.name = "Fog"
    # density driven by ice, dust, ash, rain
    drive(
        vol.inputs["Density"],
        "default_value",
        None,
        "ice * 0.012 + dust * 0.01 + ash * 0.008 + rain * 0.004",
        ("ice", "dust", "ash", "rain"),
    )
    vol.inputs["Color"].default_value = (0.75, 0.82, 0.9, 1.0)
    out = nt.nodes["Material Output"]
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return mat


def set_linear_keys(action):
    if action is None:
        return
    curves = list(action.fcurves) if hasattr(action, "fcurves") else []
    for fcurve in curves:
        for key in fcurve.keyframe_points:
            key.interpolation = "LINEAR"
    if hasattr(action, "layers") and bpy.context.scene.animation_data:
        slot = bpy.context.scene.animation_data.action_slot
        for layer in action.layers:
            for strip in layer.strips:
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if not bag:
                    continue
                for fcurve in bag.fcurves:
                    for key in fcurve.keyframe_points:
                        key.interpolation = "LINEAR"
