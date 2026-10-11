"""Blender scene for the penny / Empire State follow-fall.

    blender --background --python engine/build_b.py -- job.json

The tower is generic setback massing at the real heights. Floors are one
mesh instanced down the shaft. No logos.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import mathutils

ROOT = Path(__file__).resolve().parents[1]
WHATIF = ROOT.parent
for path in (str(ROOT), str(WHATIF)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _job() -> dict:
    argv = sys.argv
    return json.loads(Path(argv[argv.index("--") + 1]).read_text(encoding="utf-8"))


def _clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _mat(name, color, rough=0.7, emission=0.03):
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


def _shade(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)


def _box(name, w, d, h, location):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (w, d, h)
    bpy.ops.object.transform_apply(scale=True)
    return obj


def _world():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mapped = nt.nodes.new("ShaderNodeMapRange")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(geom.outputs["Incoming"], sep.inputs["Vector"])
    mapped.inputs["From Min"].default_value = -0.2
    mapped.inputs["From Max"].default_value = 0.8
    nt.links.new(sep.outputs["Z"], mapped.inputs["Value"])
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (0.98, 0.50, 0.38, 1)
    ramp.color_ramp.elements[1].position = 0.48
    ramp.color_ramp.elements[1].color = (0.96, 0.74, 0.62, 1)
    top = ramp.color_ramp.elements.new(0.82)
    top.color = (0.42, 0.58, 0.82, 1)
    nt.links.new(mapped.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    # Sky is camera-only so 1 sample stays clean.
    bg_off = nt.nodes.new("ShaderNodeBackground")
    bg_off.inputs["Strength"].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(bg_off.outputs["Background"], mix.inputs[1])
    nt.links.new(bg.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def _sun():
    light = bpy.data.lights.new("Sun", "SUN")
    light.energy = 6.0
    light.color = (1.0, 0.72, 0.48)
    light.angle = 0.0
    obj = _link(bpy.data.objects.new("Sun", light))
    direction = mathutils.Vector((0.55, 0.35, 0.76))
    obj.rotation_euler = mathutils.Vector((0, 0, -1)).rotation_difference(-direction).to_euler()
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 2.6
    fill.color = (0.75, 0.82, 1.0)
    fill.use_shadow = False
    fill_obj = _link(bpy.data.objects.new("Fill", fill))
    fill_obj.rotation_euler = (math.radians(70), 0, math.radians(160))
    bounce = bpy.data.lights.new("Bounce", "SUN")
    bounce.energy = 5.0
    bounce.color = (1.0, 0.82, 0.7)
    bounce.angle = 0.0
    bounce.use_shadow = False
    bounce_obj = _link(bpy.data.objects.new("Bounce", bounce))
    bounce_obj.rotation_euler = (math.radians(180), 0.0, 0.2)


def _facade(_path: str = ""):
    return _mat("Facade", (0.72, 0.66, 0.58), 1.0, 0.22)


def _window_mats():
    dark = _mat("Glass", (0.22, 0.26, 0.32), 1.0, 0.15)
    warm = _mat("Lit", (0.45, 0.16, 0.04), 1.0, 8.0)
    return dark, warm


def _boxes(name, pts, size, mat):
    """One mesh of boxes. Instancing was not showing up on the face."""
    if not pts:
        return
    hx, hy, hz = size
    verts = []
    faces = []
    corners = ((-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
               (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz))
    quads = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0))
    for x, y, z in pts:
        base = len(verts)
        verts.extend((x + dx, y + dy, z + dz) for dx, dy, dz in corners)
        faces.extend(tuple(base + i for i in quad) for quad in quads)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return _assign(_link(bpy.data.objects.new(name, mesh)), mat)


def _windows(name, face_x, z0, z1):
    """Two columns in the camera's view. The follow stays on this corner."""
    dark, warm = _window_mats()
    points = {dark: [], warm: []}
    for col, y in enumerate((14.35, 15.45)):
        z = z0 + 0.9
        row = 0
        while z < z1 - 0.5:
            mat = warm if (row + col) % 3 == 0 else dark
            points[mat].append((face_x + 0.02, y, z))
            z += 1.85
            row += 1
    _boxes(name + "Dark", points[dark], (0.012, 0.38, 0.55), dark)
    _boxes(name + "Warm", points[warm], (0.012, 0.38, 0.55), warm)


def _shaft(name, face_x, y0, y1, z0, z1, depth, mat):
    height = max(0.2, z1 - z0)
    width = max(0.2, y1 - y0)
    return _assign(_box(name, depth, width, height, (face_x - depth * 0.5, (y0 + y1) * 0.5, z0 + height * 0.5)), mat)


def _tower(job, facade):
    stone = _mat("Stone", (0.74, 0.68, 0.60), 1.0, 0.22)
    deck = float(job["deck_m"])
    roof = float(job["roof_m"])
    tip = float(job["tip_m"])
    corner = 16.0
    seam = deck * 0.55
    # The corner the penny follows stays put. The wall steps out lower down.
    _shaft("Crown", -1.15, corner - 10.0, corner, seam, deck - 0.02, 12.0, facade)
    _shaft("Base", -0.05, corner - 26.0, corner, 0.0, seam, 16.0, facade)
    _windows("Crown", -1.15, seam + 1.0, deck - 1.5)
    _windows("Base", -0.05, 1.5, seam - 0.8)
    _assign(_box("Setback", 1.35, 10.2, 0.18, (-0.55, corner - 5.0, seam)), stone)
    _assign(_box("Ledge", 0.7, 1.1, 0.14, (0.12, 15.15, deck - 0.07)), stone)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.4, depth=max(1.0, tip - roof), location=(-8.0, corner - 6.0, roof + (tip - roof) * 0.5))
    spire = bpy.context.object
    spire.name = "Spire"
    _assign(spire, stone)
    _skyline(facade, stone)


def _skyline(facade, stone):
    """Neighboring blocks, on the open side of the corner so the fall has a city."""
    blocks = (
        ("Near", (-2.0, 26.0, 0.0), (8.0, 8.0, 210.0), facade),
        ("Mid", (3.0, 36.0, 0.0), (10.0, 10.0, 140.0), stone),
        ("Far", (-8.0, 48.0, 0.0), (12.0, 12.0, 90.0), facade),
    )
    for name, (x, y, _z), (w, d, h), mat in blocks:
        _assign(_box(name, w, d, h, (x, y, h * 0.5)), mat)


def _penny():
    # Picture scale. A real 19 mm coin is a speck beside the tower. Drag uses the spec diameter.
    mat = _mat("Penny", (0.86, 0.45, 0.22), 1.0, 0.06)
    rim = _mat("Rim", (0.62, 0.34, 0.16), 1.0, 0.02)
    show = 5.5
    radius = 0.009525 * show
    depth = 0.00152 * show
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "Penny"
    _assign(obj, mat)
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=depth * 0.55, major_segments=48, minor_segments=8, location=(0, 0, 0))
    ring = bpy.context.object
    ring.name = "Rim"
    ring.parent = obj
    _assign(ring, rim)
    return obj


def _person():
    """5 ft 9 in outline with a cap, standing where the penny lands."""
    h = 1.7526
    cloth = _mat("Coat", (0.12, 0.16, 0.28), 0.7, 0.02)
    skin = _mat("Skin", (0.55, 0.38, 0.30), 0.6, 0.02)
    cap = _mat("Cap", (0.15, 0.22, 0.55), 0.55, 0.04)
    root = _link(bpy.data.objects.new("Person", None))
    root.location = (0.62, 15.45, 0.0)

    def part(scale, loc, mat, kind="sphere"):
        if kind == "sphere":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc)
        else:
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.0, depth=1.0, location=loc)
        obj = bpy.context.object
        obj.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        obj.parent = root
        _assign(obj, mat)

    part((0.22, 0.16, 0.42), (0, 0, 0.55 * h), cloth)
    part((0.11, 0.11, 0.12), (0, 0, 1.48), skin)
    part((0.095, 0.095, 0.018), (0, 0.0, 1.58), cap, kind="cyl")
    return root


def _street():
    ground = _mat("Sidewalk", (0.55, 0.53, 0.50), 1.0, 0.02)
    road = _mat("Road", (0.16, 0.16, 0.17), 1.0, 0.0)
    _assign(_box("Walk", 40, 50, 0.2, (8, 16, -0.1)), ground)
    _assign(_box("Road", 18, 60, 0.05, (20, 16, 0.01)), road)
    _person()


def _camera(job):
    data = bpy.data.cameras.new("Cam")
    data.lens = float(job["lens_mm"])
    data.sensor_height = 24.0
    data.sensor_fit = "VERTICAL"
    data.clip_start = 0.02
    data.clip_end = 5000.0
    cam = _link(bpy.data.objects.new("Cam", data))
    target = _link(bpy.data.objects.new("Target", None))
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam, target


def main():
    job = _job()
    _clear()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(job.get("samples", 1))
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
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
    _world()
    _sun()
    facade = _facade(job["facade"])
    _tower(job, facade)
    _street()
    penny = _penny()
    cam, target = _camera(job)
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    spin = float(job.get("spin_rad_s", 2.2))
    for index, fr in enumerate(job["frames"]):
        cam.location = fr["cam"]
        target.location = fr["target"]
        px, py, pz = fr["penny"]
        penny.location = (px, py, pz + 0.11)
        rot = fr.get("rot")
        if rot:
            penny.rotation_euler = tuple(rot)
        else:
            penny.rotation_euler = (spin * fr["t"], 1.05, 0.05)
        bpy.context.view_layer.update()
        scene.render.filepath = str(out / f"f_{fr['frame']:04d}.png")
        bpy.ops.render.render(write_still=True)
        if index % 20 == 0 or index + 1 == len(job["frames"]):
            print(f"PENNY {index + 1}/{len(job['frames'])} frame {fr['frame']}", flush=True)
    print(f"PENNY_DONE {len(job['frames'])}", flush=True)


if __name__ == "__main__":
    main()
