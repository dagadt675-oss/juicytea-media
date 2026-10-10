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
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.95, 0.62, 0.42, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.55, 0.68, 0.82, 1)
    top = ramp.color_ramp.elements.new(0.9)
    top.color = (0.16, 0.28, 0.48, 1)
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
    light.energy = 4.5
    light.color = (1.0, 0.9, 0.75)
    light.angle = 0.0
    obj = _link(bpy.data.objects.new("Sun", light))
    direction = mathutils.Vector((0.45, -0.2, 0.85))
    obj.rotation_euler = mathutils.Vector((0, 0, -1)).rotation_difference(-direction).to_euler()
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 1.4
    fill.color = (0.7, 0.8, 1.0)
    fill.use_shadow = False
    fill_obj = _link(bpy.data.objects.new("Fill", fill))
    fill_obj.rotation_euler = (math.radians(70), 0, math.radians(160))


def _uv_facade(obj):
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (co.y / 3.4, co.z / 3.7)


def _facade(path: str):
    mat = _mat("Facade", (0.55, 0.57, 0.60), 0.72, 0.04)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.interpolation = "Cubic"
    uv = nt.nodes.new("ShaderNodeUVMap")
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _instance_floors(proto, zs):
    mesh = bpy.data.meshes.new("FloorPts")
    mesh.from_pydata([(0.0, 0.0, z) for z in zs], [], [])
    mesh.update()
    cloud = _link(bpy.data.objects.new("Floors", mesh))
    proto.parent = cloud
    proto.parent_type = "VERTEX"
    cloud.instance_type = "VERTS"
    cloud.show_instancer_for_render = False
    return cloud


def _tower(job, facade):
    stone = _mat("Stone", (0.62, 0.60, 0.56), 0.8, 0.03)
    deck = float(job["deck_m"])
    roof = float(job["roof_m"])
    tip = float(job["tip_m"])
    # Facade stops below the ledge so the follow camera is not inside the roof.
    wall_top = deck - 1.6
    wall = _box("Shaft", 0.9, 28.0, wall_top, (-0.45, 0.0, wall_top * 0.5))
    _assign(wall, facade)
    _uv_facade(wall)
    ledge = _box("Ledge", 0.5, 0.9, 0.18, (0.02, 0.0, deck - 0.09))
    _assign(ledge, stone)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3.2, depth=tip - roof, location=(-6.0, 0.0, roof + (tip - roof) * 0.5))
    spire = bpy.context.object
    spire.name = "Spire"
    _assign(spire, stone)
    # Instanced floor lips, one mesh, 86 copies.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    lip = bpy.context.object
    lip.name = "LipProto"
    lip.scale = (0.16, 8.0, 0.08)
    lip.location = (-0.22, 0.0, 0.0)
    bpy.ops.object.transform_apply(scale=True)
    _assign(lip, stone)
    step = deck / 86.0
    _instance_floors(lip, [step * (i + 0.5) for i in range(86)])


def _penny():
    mat = _mat("Penny", (0.72, 0.42, 0.22), 0.45, 0.08)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.009525, depth=0.00152, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = "Penny"
    _assign(obj, mat)
    _shade(obj)
    return obj


def _person():
    """5 ft 9 in outline standing on the sidewalk."""
    h = 1.7526
    cloth = _mat("Coat", (0.12, 0.16, 0.28), 0.7, 0.02)
    skin = _mat("Skin", (0.55, 0.38, 0.30), 0.6, 0.02)
    root = _link(bpy.data.objects.new("Person", None))
    root.location = (1.6, 1.4, 0.0)

    def part(scale, loc, mat):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc)
        obj = bpy.context.object
        obj.scale = scale
        bpy.ops.object.transform_apply(scale=True)
        obj.parent = root
        _assign(obj, mat)

    part((0.16 * h, 0.1 * h, 0.28 * h), (0, 0, 0.55 * h), cloth)
    part((0.11 * h, 0.11 * h, 0.12 * h), (0, 0, 0.88 * h), skin)
    return root


def _street():
    ground = _mat("Sidewalk", (0.35, 0.35, 0.36), 0.9, 0.02)
    road = _mat("Road", (0.12, 0.12, 0.13), 0.85, 0.01)
    _assign(_box("Walk", 30, 30, 0.2, (2, 0, -0.1)), ground)
    _assign(_box("Road", 16, 40, 0.05, (14, 0, 0.01)), road)
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
        penny.location = (px, py, pz + 0.012)
        penny.rotation_euler = (spin * fr["t"], 0.4, 0.0)
        bpy.context.view_layer.update()
        scene.render.filepath = str(out / f"f_{fr['frame']:04d}.png")
        bpy.ops.render.render(write_still=True)
        if index % 20 == 0 or index + 1 == len(job["frames"]):
            print(f"PENNY {index + 1}/{len(job['frames'])} frame {fr['frame']}", flush=True)
    print(f"PENNY_DONE {len(job['frames'])}", flush=True)


if __name__ == "__main__":
    main()
