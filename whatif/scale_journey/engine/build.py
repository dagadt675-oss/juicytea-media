"""Headless Blender entry for one scale-journey layer.

    blender --background --python engine/build.py -- job.json

Coordinates in the job are already in this layer's Blender units. True metres
never enter the scene, so float32 stays comfortable from a desk to deep space.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

import bpy
import mathutils

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.quantity import (  # noqa: E402
    AU_M,
    EARTH_RADIUS_M,
    LY_M,
    MOON_DISTANCE_M,
    MOON_RADIUS_M,
    SUN_RADIUS_M,
    RiceParams,
    grain_layout,
)


def _argv_job() -> dict:
    argv = sys.argv
    if "--" not in argv:
        raise SystemExit("usage: blender --background --python build.py -- job.json")
    return json.loads(Path(argv[argv.index("--") + 1]).read_text(encoding="utf-8"))


def _clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _material(name, color, rough=0.55, emission=0.0, emission_color=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission
    if emission_color and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
    return mat


def _assign(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    return obj


def _box(name, w, d, h, z=0.0, location=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(location[0], location[1], location[2] + z + h * 0.5))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (w, d, h)
    bpy.ops.object.transform_apply(scale=True)
    return obj


def _uv_meters(obj, meters_per_bu, repeat_m):
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (
                co.x * meters_per_bu / repeat_m,
                co.z * meters_per_bu / repeat_m,
            )


def _finish(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj


def _image_tex(nt, path, non_color=False):
    node = nt.nodes.new("ShaderNodeTexImage")
    image = bpy.data.images.load(path, check_existing=True)
    if non_color:
        image.colorspace_settings.name = "Non-Color"
    node.image = image
    node.interpolation = "Smart"
    return node


def _wood(path_diff, path_rough, path_nor):
    # Diffuse photo only. A JPEG normal map plus glossy roughness at 1 sample
    # reads as static noise. The photograph already carries the grain.
    del path_rough, path_nor
    mat = bpy.data.materials.new("Wood")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.78
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.04
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.85, 0.65, 1.0)
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.12
    diff = _image_tex(nt, path_diff)
    nt.links.new(diff.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _rice_material():
    mat = bpy.data.materials.new("Rice")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.78, 0.62, 0.36, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.02
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.86, 0.55, 1.0)
    return mat


def _facade(path):
    mat = bpy.data.materials.new("Facade")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.62
    tex = _image_tex(nt, path)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    # Lit windows in the texture should glow a little.
    if "Emission Color" in bsdf.inputs and "Emission Strength" in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 0.06
    uv = nt.nodes.new("ShaderNodeUVMap")
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    return mat


def _sun(name, azimuth_deg, elevation_deg, energy, color, shadow=True):
    light = bpy.data.lights.new(name, "SUN")
    light.energy = energy
    light.color = color
    light.angle = 0.0
    if hasattr(light, "use_shadow"):
        light.use_shadow = shadow
    obj = _link(bpy.data.objects.new(name, light))
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    direction = mathutils.Vector((math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)))
    quat = mathutils.Vector((0.0, 0.0, -1.0)).rotation_difference(-direction)
    obj.rotation_euler = quat.to_euler()
    return obj


def _world_camera_background(color_socket_builder, strength=1.0):
    """Sky is visible to the camera and does not light the scene (keeps 1-sample clean)."""
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_cam.inputs["Strength"].default_value = strength
    bg_off = nt.nodes.new("ShaderNodeBackground")
    bg_off.inputs["Strength"].default_value = 0.0
    bg_off.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    color_socket_builder(nt, bg_cam)
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(bg_off.outputs["Background"], mix.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return world


def _world_gradient(top, horizon, ground):
    def build(nt, bg):
        coord = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[0].color = (*ground, 1)
        ramp.color_ramp.elements[1].position = 0.62
        ramp.color_ramp.elements[1].color = (*horizon, 1)
        extra = ramp.color_ramp.elements.new(0.92)
        extra.color = (*top, 1)
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])

    _world_camera_background(build, strength=1.0)


def _world_nishita(elevation_deg, rotation_deg, dust=3.0):
    """Analytic sky. Nishita at 1 sample is pure noise; a ramp is not."""
    del rotation_deg

    def build(nt, bg):
        geom = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geom.outputs["Incoming"], sep.inputs["Vector"])
        mapped = nt.nodes.new("ShaderNodeMapRange")
        mapped.inputs["From Min"].default_value = -0.15
        mapped.inputs["From Max"].default_value = 0.85
        nt.links.new(sep.outputs["Z"], mapped.inputs["Value"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        warm = dust > 3.0
        low = (1.0, 0.55, 0.28, 1) if warm else (0.55, 0.72, 0.88, 1)
        mid = (0.96, 0.62, 0.58, 1) if warm else (0.35, 0.55, 0.78, 1)
        high = (0.22, 0.18, 0.38, 1) if warm else (0.10, 0.18, 0.36, 1)
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[0].color = low
        ramp.color_ramp.elements[1].position = 0.62
        ramp.color_ramp.elements[1].color = mid
        top = ramp.color_ramp.elements.new(0.88)
        top.color = high
        nt.links.new(mapped.outputs["Result"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])

    _world_camera_background(build, strength=1.0)


def _world_stars(path):
    def build(nt, bg):
        tex = _image_tex(nt, path)
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = tex.image
        nt.nodes.remove(tex)
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])

    _world_camera_background(build, strength=1.0)


def _setup_render(job):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(job.get("samples", 1))
    scene.cycles.use_denoising = int(job.get("samples", 1)) >= 8
    bounces = int(job.get("bounces", 0))
    scene.cycles.max_bounces = bounces
    scene.cycles.diffuse_bounces = bounces
    scene.cycles.glossy_bounces = min(1, bounces)
    scene.cycles.transmission_bounces = 0
    scene.cycles.volume_bounces = 0
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.sample_clamp_direct = 0.0
    scene.cycles.sample_clamp_indirect = 2.5
    scene.cycles.use_adaptive_sampling = False
    try:
        scene.cycles.use_persistent_data = True
    except Exception:
        pass
    scene.render.resolution_x = int(job["width"])
    scene.render.resolution_y = int(job["height"])
    scene.render.resolution_percentage = int(job.get("scale", 100))
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.fps = int(job.get("fps", 30))
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = float(job.get("exposure", 0.2))
    scene.camera = None


def _camera(job):
    data = bpy.data.cameras.new("Cam")
    data.lens = float(job["frames"][0]["lens_mm"])
    data.sensor_height = float(job["frames"][0]["sensor_height_mm"])
    data.sensor_fit = "VERTICAL"
    data.clip_start = 0.01
    data.clip_end = 100000.0
    cam = _link(bpy.data.objects.new("Cam", data))
    target = _link(bpy.data.objects.new("Target", None))
    target.empty_display_size = 0.2
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam, target


def _lights(preset):
    if preset == "interior":
        _sun("Key", azimuth_deg=-58, elevation_deg=42, energy=4.2, color=(1.0, 0.78, 0.55))
        _sun("Fill", azimuth_deg=140, elevation_deg=28, energy=1.5, color=(0.75, 0.84, 1.0), shadow=False)
        _sun("Rim", azimuth_deg=20, elevation_deg=18, energy=2.4, color=(1.0, 0.72, 0.45), shadow=False)
    elif preset == "sunset":
        _sun("Key", azimuth_deg=-70, elevation_deg=14, energy=5.0, color=(1.0, 0.62, 0.38))
        _sun("Fill", azimuth_deg=120, elevation_deg=30, energy=1.3, color=(0.65, 0.75, 1.0), shadow=False)
        _sun("Rim", azimuth_deg=30, elevation_deg=8, energy=2.0, color=(1.0, 0.78, 0.5), shadow=False)
    elif preset == "day":
        _sun("Key", azimuth_deg=-40, elevation_deg=28, energy=4.6, color=(1.0, 0.93, 0.82))
        _sun("Fill", azimuth_deg=150, elevation_deg=20, energy=1.6, color=(0.7, 0.82, 1.0), shadow=False)
    else:
        _sun("Key", azimuth_deg=-30, elevation_deg=25, energy=3.5, color=(1.0, 0.95, 0.9))
        _sun("Fill", azimuth_deg=160, elevation_deg=15, energy=1.2, color=(0.7, 0.8, 1.0), shadow=False)


def _add_person(name, height_bu, xy=(0.0, 0.0)):
    """Stylised figure, feet at z=0. No face — silhouette and clothes carry it."""
    h = height_bu
    skin = _material(f"{name}Skin", (0.55, 0.36, 0.28), 0.55, 0.02, (0.6, 0.4, 0.3))
    cloth = _material(f"{name}Cloth", (0.08, 0.12, 0.22), 0.7, 0.01)
    pants = _material(f"{name}Pants", (0.12, 0.13, 0.16), 0.75)
    root = _link(bpy.data.objects.new(name, None))
    root.location = (xy[0], xy[1], 0.0)
    root.empty_display_size = h * 0.2

    def part(kind, scale, loc, mat):
        if kind == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=loc)
        else:
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.0, depth=1.0, location=loc)
        obj = bpy.context.object
        obj.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        obj.parent = root
        _assign(obj, mat)
        _finish(obj)
        return obj

    # Feet at 0, crown at h, so the leader on the crown meets the mesh.
    part("cyl", (0.07 * h, 0.07 * h, 0.46 * h), (0.08 * h, 0.0, 0.23 * h), pants)
    part("cyl", (0.07 * h, 0.07 * h, 0.46 * h), (-0.08 * h, 0.0, 0.23 * h), pants)
    part("cyl", (0.16 * h, 0.10 * h, 0.32 * h), (0.0, 0.0, 0.58 * h), cloth)
    part("sphere", (0.11 * h, 0.11 * h, 0.12 * h), (0.0, 0.0, 0.86 * h), skin)
    part("sphere", (0.12 * h, 0.11 * h, 0.06 * h), (0.0, 0.0, 0.96 * h), _material(f"{name}Hair", (0.08, 0.05, 0.03), 0.6))
    part("cyl", (0.045 * h, 0.045 * h, 0.30 * h), (0.20 * h, 0.0, 0.58 * h), cloth)
    part("cyl", (0.045 * h, 0.045 * h, 0.30 * h), (-0.20 * h, 0.0, 0.58 * h), cloth)
    return root


def _cone_mesh():
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=1.0, radius2=0.0, depth=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "Pile"
    for vert in obj.data.vertices:
        vert.co.z += 0.5
    _assign(obj, _rice_material())
    _finish(obj)
    return obj


def _grains(job, rice_mat):
    p = RiceParams(
        grain_length_m=job["grain"]["length_m"],
        grain_width_m=job["grain"]["width_m"],
        grain_thickness_m=job["grain"]["thickness_m"],
        grain_mass_kg=job["grain"]["mass_kg"],
        bulk_density_kg_m3=job["grain"]["density"],
        repose_deg=job["grain"]["repose_deg"],
    )
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
    proto = bpy.context.object
    mesh = proto.data
    proto.name = "GrainProto"
    m_per = job["meters_per_bu"]
    # Sphere radius 1, so scale is the semi-axis in BU.
    scale = (
        (p.grain_length_m / m_per) * 0.5,
        (p.grain_width_m / m_per) * 0.5,
        (p.grain_thickness_m / m_per) * 0.5,
    )
    objects = []
    for i in range(36):
        obj = _link(bpy.data.objects.new(f"Grain{i}", mesh))
        obj.scale = scale
        obj.hide_render = True
        _assign(obj, rice_mat)
        objects.append(obj)
    bpy.data.objects.remove(proto, do_unlink=True)
    return objects, p


def _proxies(job, mats):
    m_per = job["meters_per_bu"]
    made = []
    for proxy in job.get("proxies", []):
        h = proxy["height_m"] / m_per
        xy = (proxy["x_m"] / m_per, proxy["y_m"] / m_per)
        kind = proxy["kind"]
        if kind == "person":
            made.append(_add_person(proxy["id"], h, xy))
        elif kind == "house":
            made.append(_house(proxy["id"], h, xy, mats))
        elif kind == "tower":
            made.append(_tower(proxy["id"], h, xy, mats, taper=0.82))
        elif kind == "spire":
            made.append(_tower(proxy["id"], h, xy, mats, taper=0.62))
        elif kind == "monument":
            made.append(_monument(proxy["id"], h, xy, mats))
        elif kind == "peak":
            bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=h * 0.55, depth=h, location=(xy[0], xy[1], h * 0.5))
            obj = bpy.context.object
            obj.name = proxy["id"]
            _assign(obj, mats["stone"])
            _finish(obj)
            made.append(obj)
        elif kind == "marker":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=max(h * 0.08, 0.05), location=(xy[0], xy[1], h))
            obj = bpy.context.object
            obj.name = proxy["id"]
            _assign(obj, mats["marker"])
            made.append(obj)
    return made


def _house(name, h, xy, mats):
    root = _link(bpy.data.objects.new(name, None))
    root.location = (xy[0], xy[1], 0.0)
    w = h * 0.72
    d = h * 0.55
    walls = _box(f"{name}Walls", w, d, h * 0.72, location=(0, 0, 0))
    walls.parent = root
    _assign(walls, mats["facade"])
    _uv_meters(walls, 1.0, 3.2)
    roof = _box(f"{name}Roof", w * 1.08, d * 1.08, h * 0.28, location=(0, 0, h * 0.72))
    roof.parent = root
    _assign(roof, mats["roof"])
    return root


def _tower(name, h, xy, mats, taper):
    root = _link(bpy.data.objects.new(name, None))
    root.location = (xy[0], xy[1], 0.0)
    z = 0.0
    w = h * 0.09
    remaining = h
    i = 0
    while remaining > h * 0.04 and i < 8:
        seg = min(remaining * 0.34, h * 0.22)
        block = _box(f"{name}{i}", w, w * 0.82, seg, location=(0, 0, z))
        block.parent = root
        _assign(block, mats["facade"])
        _uv_meters(block, 1.0, 3.4)
        z += seg
        remaining -= seg
        w *= taper
        i += 1
    if remaining > 0:
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=w, depth=remaining, location=(0, 0, z + remaining * 0.5))
        tip = bpy.context.object
        tip.parent = root
        tip.location = (0, 0, z + remaining * 0.5)
        _assign(tip, mats["roof"])
    return root


def _monument(name, h, xy, mats):
    root = _link(bpy.data.objects.new(name, None))
    root.location = (xy[0], xy[1], 0.0)
    ped = _box(f"{name}Ped", h * 0.22, h * 0.22, h * 0.46)
    ped.parent = root
    _assign(ped, mats["stone"])
    body = _box(f"{name}Body", h * 0.08, h * 0.06, h * 0.38, location=(0, 0, h * 0.46))
    body.parent = root
    _assign(body, mats["stone"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=h * 0.035, location=(0, 0, h * 0.90))
    head = bpy.context.object
    head.parent = root
    head.location = (0, 0, h * 0.90)
    _assign(head, mats["stone"])
    torch = _box(f"{name}Arm", h * 0.035, h * 0.035, h * 0.16, location=(h * 0.08, 0, h * 0.78))
    torch.parent = root
    torch.rotation_euler = (0.0, math.radians(-38), 0.0)
    _assign(torch, mats["roof"])
    return root


def _city_blocks(job, mats):
    rng = random.Random(job.get("seed", 7))
    m_per = job["meters_per_bu"]
    # Keep a plaza clear around the origin, then a skyline.
    taken = [math.hypot(p["x_m"], p["y_m"]) for p in job.get("proxies", [])]
    for i in range(56):
        ang = rng.uniform(0, math.tau)
        # Proxies stand on the +X side, a little toward the camera. Leave that wedge empty.
        if -0.9 < ang < 0.9:
            ang = 1.2 if ang >= 0 else -1.2
        dist_m = rng.uniform(22.0, 900.0)
        if any(abs(dist_m - t) < 12 for t in taken):
            dist_m += 20.0
        x = math.cos(ang) * dist_m / m_per
        y = math.sin(ang) * dist_m / m_per
        height_m = rng.choice((12, 16, 22, 28, 36, 48, 64, 80, 110))
        if rng.random() > 0.86:
            height_m = rng.uniform(120, 220)
        w = rng.uniform(8.0, 16.0) / m_per
        d = rng.uniform(8.0, 16.0) / m_per
        h = height_m / m_per
        block = _box(f"Blk{i}", w, d, h * 0.94, location=(x, y, 0))
        _assign(block, mats["facade"])
        _uv_meters(block, m_per, 3.3)
        cap = _box(f"Cap{i}", w * 1.02, d * 1.02, h * 0.06, location=(x, y, h * 0.94))
        _assign(cap, mats["roof"])
        # Aerial perspective: push distant blocks toward the haze colour.
        fog = min(0.78, max(0.0, (dist_m - 60.0) / 700.0))
        if fog > 0.15:
            haze = (0.62 + 0.2 * fog, 0.55 + 0.15 * fog, 0.58 + 0.1 * fog)
            mat = _material(f"Haze{i}", haze, 0.7, 0.02, haze)
            _assign(block, mat)


def _terrain(job):
    m_per = job["meters_per_bu"]
    n = 70
    extent = 2500.0  # BU
    r_earth = EARTH_RADIUS_M / m_per
    mesh = bpy.data.meshes.new("Terrain")
    verts = []
    faces = []
    for j in range(n):
        for i in range(n):
            x = (i / (n - 1) - 0.5) * 2.0 * extent
            y = (j / (n - 1) - 0.5) * 2.0 * extent
            curve = -(x * x + y * y) / (2.0 * r_earth)
            hill = 0.0
            dist = math.hypot(x, y)
            if dist > 40.0:
                hill = 6.0 * math.sin(x * 0.02) * math.cos(y * 0.017) * min(1.0, dist / 200.0)
            verts.append((x, y, curve + hill))
    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i
            faces.append((a, a + 1, a + n + 1, a + n))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = _link(bpy.data.objects.new("Terrain", mesh))
    _finish(obj)
    land = _material("Land", (0.22, 0.38, 0.22), 0.9, 0.03, (0.25, 0.4, 0.24))
    _assign(obj, land)
    return obj


def _clouds(job):
    mat = _material("Cloud", (0.95, 0.95, 0.97), 1.0, 0.25, (1, 1, 1))
    rng = random.Random(4)
    m_per = job["meters_per_bu"]
    for i in range(8):
        ang = i / 8 * math.tau + 0.4
        dist = rng.uniform(420.0, 980.0)
        z = rng.uniform(90.0, 200.0)
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=24,
            ring_count=12,
            radius=1.0,
            location=(math.cos(ang) * dist, math.sin(ang) * dist, z),
        )
        obj = bpy.context.object
        obj.scale = (rng.uniform(40, 90), rng.uniform(22, 50), rng.uniform(6, 12))
        _assign(obj, mat)
        _finish(obj)
        obj.visible_shadow = False


def _sphere(name, radius_bu, location, mat, segments=64):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=segments // 2, radius=radius_bu, location=location)
    obj = bpy.context.object
    obj.name = name
    _assign(obj, mat)
    _finish(obj)
    return obj


def _earth(radius_bu, location, path):
    obj = _sphere("Earth", radius_bu, location, _material("EarthFallback", (0.1, 0.25, 0.55), 0.7), segments=72)
    if path and Path(path).exists():
        mat = bpy.data.materials.new("Earth")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Roughness"].default_value = 0.65
        tex = _image_tex(nt, path)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        _assign(obj, mat)
    # Atmosphere shell.
    shell = _sphere("Atmo", radius_bu * 1.025, location, _material("Atmo", (0.45, 0.7, 1.0), 0.2, 0.4, (0.45, 0.7, 1.0)), segments=48)
    shell.visible_shadow = False
    if hasattr(shell, "cycles"):
        pass
    return obj


def _bokeh_material(path, strength=2.2):
    mat = bpy.data.materials.new("WindowGlow")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    tex = _image_tex(mat.node_tree, path)
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def build_interior(job, mats):
    _world_nishita(elevation_deg=18.0, rotation_deg=-30.0, dust=6.0)
    _lights("interior")
    m = job["meters_per_bu"]
    wood = mats["wood"]
    table = _box("Table", 1.4 / m, 0.9 / m, 0.04 / m, z=-0.04 / m)
    _assign(table, wood)
    # Tight repeat so a macro crop of the 4k photo stays sharp, not blocky.
    _uv_meters(table, m, 0.14)
    for sx, sy in ((-0.58, -0.36), (0.58, -0.36), (-0.58, 0.36), (0.58, 0.36)):
        leg = _box(f"Leg{sx}{sy}", 0.045 / m, 0.045 / m, 0.74 / m, z=-0.78 / m, location=(sx / m, sy / m, 0))
        _assign(leg, wood)
    floor = _box("Floor", 8.0 / m, 8.0 / m, 0.04 / m, z=-0.82 / m)
    _assign(floor, wood)
    _uv_meters(floor, m, 0.55)
    # Warm side walls, open back so the bokeh card and sky read behind the grain.
    plaster = mats["plaster"]
    for name, loc, scale in (
        ("WallL", (-1.3 / m, 0.15 / m, 0.0), (0.06 / m, 1.6 / m, 1.4 / m)),
        ("WallR", (1.3 / m, 0.15 / m, 0.0), (0.06 / m, 1.6 / m, 1.4 / m)),
    ):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], scale[2] * 0.35))
        wall = bpy.context.object
        wall.name = name
        wall.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        _assign(wall, plaster)
    if job["textures"].get("bokeh"):
        win = _box("Window", 2.4 / m, 0.02 / m, 1.5 / m, z=0.05 / m, location=(0.0, 0.72 / m, 0))
        _assign(win, _bokeh_material(job["textures"]["bokeh"], 2.6))
        _uv_meters(win, m, 1.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.038 / m, depth=0.08 / m, location=(-0.22 / m, 0.08 / m, 0.04 / m))
    mug = bpy.context.object
    _assign(mug, _material("Mug", (0.92, 0.93, 0.94), 0.22, 0.03, (1, 1, 1)))


def build_city(job, mats):
    _world_nishita(elevation_deg=9.0, rotation_deg=-55.0, dust=4.5)
    _lights("sunset")
    m = job["meters_per_bu"]
    ground = _box("Plaza", 4000.0 / m, 4000.0 / m, 0.2 / m, z=-0.2 / m)
    _assign(ground, mats["asphalt"])
    _city_blocks(job, mats)
    _proxies(job, mats)


def build_aerial(job, mats):
    _world_nishita(elevation_deg=7.0, rotation_deg=-40.0, dust=2.2)
    _lights("day")
    _terrain(job)
    _clouds(job)
    _proxies(job, mats)


def build_orbit(job, mats):
    _world_stars(job["textures"]["stars"])
    _lights("day")
    m = job["meters_per_bu"]
    # Surface through the origin: centre sits one radius below.
    _earth(EARTH_RADIUS_M / m, (0.0, 0.0, -EARTH_RADIUS_M / m), job["textures"].get("earth"))


def build_cislunar(job, mats):
    _world_stars(job["textures"]["stars"])
    _lights("day")
    m = job["meters_per_bu"]
    _earth(EARTH_RADIUS_M / m, (0.0, 0.0, -EARTH_RADIUS_M / m), job["textures"].get("earth"))
    moon_mat = _material("MoonFallback", (0.55, 0.54, 0.52), 0.9)
    moon = _sphere("Moon", MOON_RADIUS_M / m, (MOON_DISTANCE_M / m, 0.0, 0.0), moon_mat, segments=48)
    if job["textures"].get("moon") and Path(job["textures"]["moon"]).exists():
        mat = bpy.data.materials.new("Moon")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Roughness"].default_value = 0.95
        tex = _image_tex(mat.node_tree, job["textures"]["moon"])
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        _assign(moon, mat)


def build_solar(job, mats):
    _world_stars(job["textures"]["stars"])
    m = job["meters_per_bu"]
    sun = _sphere("Sun", SUN_RADIUS_M / m, (AU_M / m, 0.0, 0.0), _material("Sun", (1.0, 0.85, 0.45), 0.4, 8.0, (1.0, 0.7, 0.3)), segments=48)
    sun.visible_shadow = False
    _earth(EARTH_RADIUS_M / m, (0.0, 0.0, 0.0), job["textures"].get("earth"))
    _sun("Key", 70, 15, 6.0, (1.0, 0.95, 0.85))


def build_galaxy(job, mats):
    _world_stars(job["textures"]["stars"])
    _lights("day")
    rng = random.Random(8)
    mat = _material("Star", (0.9, 0.92, 1.0), 0.4, 3.0, (0.85, 0.9, 1.0))
    bulge = _material("Bulge", (1.0, 0.82, 0.55), 0.5, 1.2, (1.0, 0.75, 0.4))
    _sphere("Core", 8.0, (0, 0, 0), bulge, segments=32)
    for i in range(280):
        arm = i % 4
        t = rng.uniform(0.2, 6.0)
        ang = t * 0.9 + arm * math.tau / 4 + rng.uniform(-0.3, 0.3)
        rad = t * 4.2
        z = rng.gauss(0, 0.35)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=rng.uniform(0.05, 0.16), location=(rad * math.cos(ang), rad * math.sin(ang), z))
        _assign(bpy.context.object, mat)


def build_cosmic(job, mats):
    _world_stars(job["textures"]["stars"])
    _lights("day")
    # Observable-universe proxy: a faint shell, plus a few galaxy smudges.
    shell = _sphere("Observable", 40.0, (0, 0, 0), _material("Shell", (0.85, 0.75, 0.65), 0.4, 0.35, (1.0, 0.8, 0.55)), segments=48)
    shell.visible_shadow = False
    rng = random.Random(2)
    mat = _material("Galaxy", (0.95, 0.85, 0.7), 0.5, 1.5, (1.0, 0.8, 0.55))
    for i in range(18):
        loc = (rng.uniform(-25, 25), rng.uniform(-25, 25), rng.uniform(-8, 8))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=rng.uniform(0.6, 1.8), location=loc)
        obj = bpy.context.object
        obj.scale = (1.0, 1.0, 0.28)
        _assign(obj, mat)


def build_room(job, mats):
    """Shrink-episode opening. Floor is z=0 so the person stands on it."""
    _world_gradient((0.93, 0.7, 0.48), (0.8, 0.5, 0.36), (0.28, 0.18, 0.14))
    _lights("interior")
    m = job["meters_per_bu"]
    floor = _box("Floor", 10.0 / m, 10.0 / m, 0.05 / m, z=-0.05 / m)
    _assign(floor, mats["wood"])
    _uv_meters(floor, m, 0.5)
    plaster = mats["plaster"]
    for name, loc, scale in (
        ("WallL", (-2.4 / m, 0.2 / m, 0.0), (0.08 / m, 4.0 / m, 2.8 / m)),
        ("WallR", (2.4 / m, 0.2 / m, 0.0), (0.08 / m, 4.0 / m, 2.8 / m)),
        ("WallB", (0.0, 2.2 / m, 0.0), (4.8 / m, 0.08 / m, 2.8 / m)),
    ):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], loc[2] + scale[2] * 0.5))
        wall = bpy.context.object
        wall.name = name
        wall.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        _assign(wall, plaster)
    if job["textures"].get("bokeh"):
        win = _box("Window", 1.6 / m, 0.02 / m, 1.3 / m, z=0.5 / m, location=(0.0, 2.12 / m, 0))
        mat = bpy.data.materials.new("WindowGlow")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex = _image_tex(mat.node_tree, job["textures"]["bokeh"])
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if "Emission Color" in bsdf.inputs:
            mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = 1.3
        _assign(win, mat)


def build_tabletop(job, mats):
    _world_gradient((0.55, 0.42, 0.32), (0.35, 0.24, 0.18), (0.12, 0.08, 0.06))
    _lights("interior")
    m = job["meters_per_bu"]
    table = _box("MacroDesk", 0.4 / m, 0.3 / m, 0.02 / m, z=-0.02 / m)
    _assign(table, mats["wood"])
    _uv_meters(table, m, 0.05)
    # A coin: US quarter diameter, lying flat, as the environment's scale anchor.
    coin_r = 0.01213 / m
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=coin_r, depth=0.00175 / m, location=(0.03 / m, 0.0, 0.0009 / m))
    _assign(bpy.context.object, _material("Coin", (0.72, 0.62, 0.38), 0.28, 0.05, (0.8, 0.7, 0.4)))


def build_fibers(job, mats):
    _world_gradient((0.05, 0.05, 0.07), (0.02, 0.02, 0.03), (0.0, 0.0, 0.0))
    _lights("day")
    m = job["meters_per_bu"]
    mat = _material("Hair", (0.18, 0.12, 0.08), 0.4, 0.05, (0.3, 0.2, 0.1))
    for i in range(5):
        x = (i - 2) * 80e-6 / m
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=35e-6 / m, depth=800e-6 / m, location=(x, 0, 0))
        obj = bpy.context.object
        obj.rotation_euler = (math.radians(80), 0.2 * i, 0.4)
        _assign(obj, mat)


def build_cells(job, mats):
    _world_gradient((0.35, 0.05, 0.08), (0.15, 0.02, 0.04), (0.05, 0.0, 0.02))
    _lights("interior")
    m = job["meters_per_bu"]
    mat = _material("RBC", (0.7, 0.08, 0.1), 0.35, 0.15, (0.8, 0.15, 0.12))
    rng = random.Random(1)
    for i in range(14):
        loc = (rng.uniform(-8, 8) * 4e-6 / m, rng.uniform(-5, 5) * 4e-6 / m, rng.uniform(-2, 2) * 4e-6 / m)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=3.8e-6 / m, location=loc)
        obj = bpy.context.object
        obj.scale = (1.0, 1.0, 0.32)
        _assign(obj, mat)
    bug = _material("Bug", (0.65, 0.75, 0.45), 0.4, 0.2, (0.7, 0.85, 0.4))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5e-6 / m, location=(6e-6 / m, 2e-6 / m, 0))
    obj = bpy.context.object
    obj.scale = (2.2, 0.7, 0.7)
    _assign(obj, bug)


def build_viruses(job, mats):
    _world_gradient((0.02, 0.06, 0.1), (0.0, 0.02, 0.05), (0, 0, 0))
    _lights("day")
    m = job["meters_per_bu"]
    body = _material("Virion", (0.85, 0.25, 0.35), 0.3, 0.45, (1.0, 0.35, 0.4))
    _sphere("Virion", 50e-9 / m, (0, 0, 0), body, segments=32)
    spike = _material("Spike", (0.95, 0.75, 0.7), 0.35, 0.3, (1, 0.8, 0.7))
    for i in range(18):
        ang = i / 18 * math.tau
        el = math.radians((i % 5) * 28 - 40)
        r = 50e-9 / m
        loc = (r * math.cos(el) * math.cos(ang), r * math.cos(el) * math.sin(ang), r * math.sin(el))
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=6e-9 / m, depth=18e-9 / m, location=loc)
        _assign(bpy.context.object, spike)


def build_molecules(job, mats):
    _world_gradient((0.03, 0.05, 0.12), (0.01, 0.02, 0.05), (0, 0, 0))
    _lights("day")
    m = job["meters_per_bu"]
    a = _material("AtomA", (0.3, 0.55, 1.0), 0.25, 0.6, (0.4, 0.6, 1))
    b = _material("AtomB", (1.0, 0.45, 0.35), 0.25, 0.6, (1, 0.5, 0.4))
    bond = _material("Bond", (0.8, 0.82, 0.9), 0.3, 0.2)
    rng = random.Random(5)
    centers = []
    for i in range(10):
        loc = (rng.uniform(-1, 1) * 1.2e-9 / m, rng.uniform(-1, 1) * 1.2e-9 / m, rng.uniform(-0.4, 0.4) * 1.2e-9 / m)
        centers.append(loc)
        _sphere(f"A{i}", 0.15e-9 / m, loc, a if i % 2 == 0 else b, segments=16)
    for i in range(len(centers) - 1):
        p = centers[i]
        q = centers[i + 1]
        mid = tuple((p[k] + q[k]) * 0.5 for k in range(3))
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.04e-9 / m, depth=0.4e-9 / m, location=mid)
        _assign(bpy.context.object, bond)


def build_atoms(job, mats):
    _world_stars(job["textures"]["stars"])
    _lights("day")
    core = _material("NucleusGlow", (1.0, 0.82, 0.45), 0.2, 2.5, (1, 0.7, 0.3))
    _sphere("Nucleus", 0.4, (0, 0, 0), core, segments=24)
    ring_mat = _material("Orbit", (0.6, 0.8, 1.0), 0.2, 1.2, (0.6, 0.85, 1))
    for tilt in (0.2, 1.1, 2.0):
        bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.03, location=(0, 0, 0))
        obj = bpy.context.object
        obj.rotation_euler = (tilt, tilt * 0.4, 0)
        _assign(obj, ring_mat)
        obj.visible_shadow = False


def build_atom_void(job, mats):
    _world_stars(job["textures"]["stars"])
    _lights("day")
    # Almost nothing. A far glow stands in for the electron cloud.
    glow = _sphere("Cloud", 12.0, (0, 0, 0), _material("Cloud", (0.25, 0.4, 0.8), 0.3, 0.15, (0.3, 0.5, 1)), segments=32)
    glow.visible_shadow = False


def build_nucleus(job, mats):
    _world_gradient((0.02, 0.0, 0.04), (0.0, 0.0, 0.0), (0, 0, 0))
    _lights("day")
    rng = random.Random(9)
    p = _material("ProtonM", (1.0, 0.35, 0.3), 0.25, 0.8, (1, 0.4, 0.3))
    n = _material("NeutronM", (0.75, 0.78, 0.85), 0.3, 0.25)
    for i in range(12):
        loc = (rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8))
        _sphere(f"N{i}", 0.45, loc, p if i % 2 == 0 else n, segments=16)


def build_proton(job, mats):
    _world_gradient((0.08, 0.0, 0.05), (0.0, 0.0, 0.0), (0, 0, 0))
    _lights("interior")
    _sphere("Proton", 1.0, (0, 0, 0), _material("ProtonBody", (0.95, 0.28, 0.38), 0.22, 0.7, (1, 0.45, 0.4)), segments=48)
    q = _material("Quark", (1.0, 0.85, 0.4), 0.2, 1.6, (1, 0.8, 0.3))
    for loc in ((0.25, 0.1, 0.05), (-0.2, 0.18, -0.08), (0.02, -0.22, 0.12)):
        _sphere("Quark", 0.22, loc, q, segments=16)


BUILDERS = {
    "interior": build_interior,
    "city": build_city,
    "aerial": build_aerial,
    "orbit": build_orbit,
    "cislunar": build_cislunar,
    "solar": build_solar,
    "galaxy": build_galaxy,
    "cosmic": build_cosmic,
    "room": build_room,
    "tabletop": build_tabletop,
    "fibers": build_fibers,
    "cells": build_cells,
    "viruses": build_viruses,
    "molecules": build_molecules,
    "atoms": build_atoms,
    "atom_void": build_atom_void,
    "nucleus": build_nucleus,
    "proton": build_proton,
}


def main():
    job = _argv_job()
    t0 = time.time()
    _clear()
    _setup_render(job)
    cam, target = _camera(job)
    tex = job["textures"]
    mats = {
        "wood": _wood(tex["wood_diff"], tex.get("wood_rough", ""), tex.get("wood_nor", "")),
        "facade": _facade(tex["facade"]) if tex.get("facade") else _material("Facade", (0.35, 0.38, 0.45), 0.6, 0.05),
        "roof": _material("Roof", (0.18, 0.16, 0.17), 0.7),
        "stone": _material("Stone", (0.62, 0.6, 0.55), 0.72, 0.02),
        "plaster": _material("Plaster", (0.78, 0.72, 0.64), 0.85, 0.03, (0.8, 0.7, 0.6)),
        "asphalt": _material("Asphalt", (0.28, 0.27, 0.25), 0.92, 0.02, (0.3, 0.28, 0.24)),
        "marker": _material("Marker", (1.0, 0.45, 0.2), 0.3, 1.2, (1, 0.5, 0.2)),
    }
    pile = _cone_mesh()
    grain_obs, rice_p = _grains(job, _rice_material())
    subject_root = None
    if job.get("subject") == "person":
        subject_root = _add_person("You", 1.0, (0.0, 0.0))
    builder = BUILDERS[job["layer"]]
    builder(job, mats)
    m_per = job["meters_per_bu"]
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    total = len(job["frames"])
    for index, fr in enumerate(job["frames"]):
        cam.location = fr["cam"]
        target.location = fr["target"]
        visual = fr["visual"]
        if job.get("subject") == "pile":
            if visual == "grains":
                pile.hide_render = True
                layout = grain_layout(max(1, int(round(min(fr["grains"], 36)))), rice_p)
                for i, obj in enumerate(grain_obs):
                    if i < len(layout):
                        x, y, z, yaw = layout[i]
                        obj.location = (x / m_per, y / m_per, z / m_per)
                        obj.rotation_euler = (0.0, 0.0, yaw)
                        obj.hide_render = False
                    else:
                        obj.hide_render = True
            else:
                for obj in grain_obs:
                    obj.hide_render = True
                pile.hide_render = False
                pile.scale = (fr["r_bu"], fr["r_bu"], max(fr["h_bu"], 1e-4))
                pile.location = (0.0, 0.0, 0.0)
        else:
            pile.hide_render = True
            for obj in grain_obs:
                obj.hide_render = True
            if subject_root is not None:
                # Unit person is 1 BU tall; scale to the subject's height.
                s = max(fr["h_bu"], 1e-6)
                subject_root.scale = (s, s, s)
                subject_root.hide_render = visual != "person"
                if visual == "orb":
                    subject_root.hide_render = True
        if visual == "orb":
            # A readable marker once "you" is smaller than the set dressing.
            if "Orb" not in bpy.data.objects:
                orb = _sphere("Orb", 0.12, (0, 0, 0.12), mats["marker"], segments=16)
            else:
                orb = bpy.data.objects["Orb"]
            orb.hide_render = False
            orb.scale = (fr["h_bu"] * 0.35 / 0.12, fr["h_bu"] * 0.35 / 0.12, fr["h_bu"] * 0.35 / 0.12)
        elif "Orb" in bpy.data.objects:
            bpy.data.objects["Orb"].hide_render = True
        bpy.context.view_layer.update()
        bpy.context.scene.render.filepath = str(out / f"f_{fr['frame']:04d}.png")
        bpy.ops.render.render(write_still=True)
        if index == 0 or index + 1 == total or index % 15 == 0:
            elapsed = time.time() - t0
            print(f"LAYER {job['layer']} {index + 1}/{total} frame {fr['frame']} elapsed {elapsed:.1f}s", flush=True)
    print(f"LAYER_DONE {job['layer']} frames {total} seconds {time.time() - t0:.1f}", flush=True)


if __name__ == "__main__":
    main()
