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

# Same corners as engine.bformat.TOWER_TIERS. The coin clears the SE corner.
TOWER_TIERS = (
    (320.0, 381.0, 18.0, 14.0),
    (210.0, 320.0, 28.0, 22.0),
    (110.0, 210.0, 40.0, 30.0),
    (28.0, 110.0, 52.0, 38.0),
    (0.0, 28.0, 62.0, 46.0),
)


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
    bg.inputs["Strength"].default_value = 0.65
    dark = nt.nodes.new("ShaderNodeBackground")
    dark.inputs["Strength"].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    light = nt.nodes.new("ShaderNodeLightPath")
    nt.links.new(light.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(dark.outputs["Background"], mix.inputs[1])
    nt.links.new(bg.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])


def _sun():
    light = bpy.data.lights.new("Sun", "SUN")
    light.energy = 4.2
    light.color = (1.0, 0.72, 0.46)
    light.angle = 0.0
    obj = _link(bpy.data.objects.new("Sun", light))
    direction = mathutils.Vector((0.62, 0.48, 0.55))
    obj.rotation_euler = mathutils.Vector((0, 0, -1)).rotation_difference(-direction).to_euler()
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 1.6
    fill.color = (0.78, 0.84, 1.0)
    fill.use_shadow = False
    fill_obj = _link(bpy.data.objects.new("Fill", fill))
    fill_obj.rotation_euler = (math.radians(55), 0.2, math.radians(20))


def _tower(stone):
    for index, (z0, z1, hx, hy) in enumerate(TOWER_TIERS):
        height = z1 - z0
        body = _box(f"Tier{index}", hx, hy, height, (hx * 0.5, hy * 0.5, z0 + height * 0.5))
        _assign(body, stone)
        lip = _box(f"Lip{index}", hx + 1.4, hy + 1.4, 0.45, ((hx + 1.4) * 0.5, (hy + 1.4) * 0.5, z1 - 0.2))
        _assign(lip, stone)
        _piers(z0 + 0.6, z1 - 0.8, hx, hy, stone)
    crown = TOWER_TIERS[0]
    _spire(crown[2] * 0.34, crown[3] * 0.28, crown[1], stone)
    _railing(crown[2], crown[3], crown[1])


def _piers(z0, z1, hx, hy, stone):
    height = max(0.4, z1 - z0)
    z = z0 + height * 0.5
    step = 3.6
    x = 1.6
    while x < hx - 0.8:
        _assign(_box(f"PierY{x:.0f}{z0:.0f}", 0.42, 0.38, height, (x, hy + 0.16, z)), stone)
        x += step
    y = 1.6
    while y < hy - 0.8:
        _assign(_box(f"PierX{y:.0f}{z0:.0f}", 0.38, 0.42, height, (hx + 0.16, y, z)), stone)
        y += step


def _spire(x, y, z0, stone):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.6, depth=62.0, location=(x, y, z0 + 31.0))
    spire = bpy.context.object
    spire.name = "Spire"
    _assign(spire, stone)
    _assign(_box("Mast", 1.1, 1.1, 8.0, (x, y, z0 + 4.0)), stone)


def _railing(hx, hy, deck):
    metal = _mat("Rail", (0.35, 0.38, 0.42), 1.0, 0.0)
    z = deck + 0.55
    _assign(_box("RailY", hx + 1.2, 0.08, 0.08, (hx * 0.5, hy + 0.55, z)), metal)
    _assign(_box("RailX", 0.08, hy + 1.2, 0.08, (hx + 0.55, hy * 0.5, z)), metal)
    for i, x in enumerate((2.0, 6.0, 10.0, 14.0, hx)):
        _assign(_box(f"PostY{i}", 0.08, 0.08, 1.1, (x, hy + 0.55, deck + 0.55)), metal)
    for i, y in enumerate((2.0, 6.0, 10.0, hy)):
        _assign(_box(f"PostX{i}", 0.08, 0.08, 1.1, (hx + 0.55, y, deck + 0.55)), metal)


def _city(stone_a, stone_b):
    rng = random.Random(7)
    spots = []
    for gx in range(0, 5):
        for gy in range(0, 5):
            cx = 88 + gx * 28 + rng.uniform(-4, 4)
            cy = 70 + gy * 26 + rng.uniform(-4, 4)
            spots.append((cx, cy))
    spots += [(36, 78), (48, 96), (70, 88), (24, 60), (100, 36)]
    for i, (cx, cy) in enumerate(spots):
        w = rng.uniform(12, 22)
        d = rng.uniform(12, 20)
        h = rng.choice((28, 40, 55, 70, 96, 120, 150))
        mat = stone_a if i % 3 else stone_b
        _assign(_box(f"Block{i}", w, d, h, (cx, cy, h * 0.5)), mat)


def _street(image_path: str):
    mat = _mat("Grid", (0.7, 0.66, 0.6), 1.0, 0.04)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path)
    tex.interpolation = "Closest"
    coord = nt.nodes.new("ShaderNodeTexCoord")
    scale = nt.nodes.new("ShaderNodeMapping")
    scale.inputs["Scale"].default_value = (1800 / 240, 1800 / 240, 1)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], scale.inputs["Vector"])
    nt.links.new(scale.outputs["Vector"], sep.inputs["Vector"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    nt.links.new(comb.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    tex.extension = "REPEAT"
    _assign(_box("Ground", 1800, 1800, 0.3, (80, 80, -0.15)), mat)


def _traffic():
    taxi = _mat("Taxi", (0.95, 0.72, 0.12), 1.0, 0.15)
    dark = _mat("Car", (0.15, 0.16, 0.18), 1.0, 0.0)
    glass = _mat("Cab", (0.2, 0.24, 0.28), 1.0, 0.0)
    rng = random.Random(3)
    roads_x = (8, 78, 140)
    roads_y = (8, 78, 140)
    made = 0
    for road in roads_y:
        for i in range(6):
            x = 20 + i * 22 + rng.uniform(-3, 3)
            if 58 < x < 74 and 40 < road < 56:
                continue
            color = taxi if (i + int(road)) % 3 == 0 else dark
            _car(f"H{made}", (x, road + rng.choice((-2.2, 2.2)), 0.7), color, glass, along_x=True)
            made += 1
    for road in roads_x:
        for i in range(4):
            y = 24 + i * 24
            color = taxi if i % 2 == 0 else dark
            _car(f"V{made}", (road + 2.4, y, 0.7), color, glass, along_x=False)
            made += 1


def _car(name, loc, body, glass, along_x):
    sx, sy = (4.4, 1.8) if along_x else (1.8, 4.4)
    _assign(_box(name, sx, sy, 1.1, loc), body)
    _assign(_box(name + "Win", sx * 0.4, sy * 0.62, 0.45, (loc[0], loc[1], loc[2] + 0.75)), glass)


def _crowd():
    cloth = _mat("Dot", (0.25, 0.28, 0.34), 1.0, 0.0)
    rng = random.Random(11)
    for i in range(28):
        x = rng.uniform(30, 150)
        y = rng.uniform(24, 140)
        if 58 < x < 76 and 40 < y < 58:
            continue
        _assign(_box(f"Dot{i}", 0.45, 0.35, rng.uniform(1.4, 1.8), (x, y, 0.8)), cloth)


def _cart():
    steel = _mat("Cart", (0.72, 0.74, 0.76), 1.0, 0.0)
    umbrella = _mat("Umbrella", (0.75, 0.18, 0.16), 1.0, 0.1)
    _assign(_box("CartBody", 1.6, 0.9, 0.9, (69.2, 47.4, 0.7)), steel)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.55, depth=0.16, location=(69.2, 47.4, 1.7))
    top = bpy.context.object
    top.name = "Umbrella"
    _assign(top, umbrella)
    _assign(_box("UmbrellaPole", 0.08, 0.08, 1.3, (69.2, 47.4, 1.4)), steel)


def _tourist(fbx_path: str, skin_path: str):
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    for name in ("Camera", "Light", "Cube"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    arm = bpy.data.objects.get("Root")
    mesh = bpy.data.objects.get("characterMedium")
    if arm is None or mesh is None:
        raise RuntimeError("Kenney character did not import")
    arm.scale = (0.46, 0.46, 0.46)
    arm.location = (65.7, 49.1, 0.0)
    arm.rotation_euler = (0.0, 0.0, math.radians(230))
    mat = _mat("Skater", (1, 1, 1), 1.0, 0.0)
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(skin_path)
    nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    mesh.data.materials.clear()
    _assign(mesh, mat)
    return arm


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
    show = 18.0
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
    data.clip_end = 6000.0
    cam = _link(bpy.data.objects.new("Cam", data))
    bpy.context.scene.camera = cam
    return cam


def _pose_bone(arm, name, rot):
    pose = arm.pose.bones.get(name)
    if pose is None:
        return
    pose.rotation_mode = "XYZ"
    pose.rotation_euler = rot


def _head(arm, t):
    if arm is None:
        return
    down = 0.15
    if t > 34.15:
        down = 0.15 + 1.05 * min(1.0, (t - 34.15) / 0.5)
    _pose_bone(arm, "Head", (down, 0.0, 0.0))
    _pose_bone(arm, "Neck", (down * 0.45, 0.0, 0.0))
    _pose_bone(arm, "LeftArm", (0.0, 0.0, -1.2))
    _pose_bone(arm, "RightArm", (0.0, 0.0, 1.2))
    _pose_bone(arm, "LeftForeArm", (0.0, 0.35, 0.0))
    _pose_bone(arm, "RightForeArm", (0.0, -0.35, 0.0))


def _air_gap(t):
    """Keep the coin in open air beside the facade during the chase."""
    if t < 3.4 or t > 33.0:
        return 0.0, 0.0
    u = 1.0
    if t < 5.0:
        u = (t - 3.4) / 1.6
    elif t > 31.2:
        u = max(0.0, (33.0 - t) / 1.8)
    return 4.8 * u, 3.6 * u


def _blur(scene, cam, penny, fr):
    scene.frame_set(1)
    for obj, prev, curr in (
        (cam, fr["prev_cam"], fr["cam"]),
        (penny, fr["prev_penny"], fr["penny"]),
    ):
        obj.animation_data_clear()
        obj.location = prev
        obj.keyframe_insert("location", frame=1)
        obj.location = curr
        obj.keyframe_insert("location", frame=2)
    scene.frame_set(2)


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
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 0
    scene.cycles.sample_clamp_indirect = 0.0
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.2
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
    scene.view_settings.exposure = -0.25
    _world(job["hdri"])
    _sun()
    stone = _facade_mat((0.78, 0.73, 0.64), "Limestone")
    stone_b = _facade_mat((0.62, 0.58, 0.54), "BrickCity")
    _tower(stone)
    _city(stone, stone_b)
    _street(job["street"])
    _traffic()
    _crowd()
    _cart()
    arm = _tourist(job["character"], job["skin"])
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
        _blur(scene, cam, penny, {"cam": curr_cam, "penny": curr_penny, "prev_cam": prev_cam, "prev_penny": prev_penny})
        cam.data.lens = float(fr.get("lens") or job.get("lens_mm") or 14)
        _look(cam, target)
        penny.rotation_euler = tuple(fr.get("rot") or (0.2, 0.4, 0.0))
        _head(arm, float(fr["t"]))
        bpy.context.view_layer.update()
        scene.render.filepath = str(out / f"f_{fr['frame']:04d}.png")
        bpy.ops.render.render(write_still=True)
        if index % 10 == 0 or index + 1 == len(job["frames"]):
            print(f"PENNY {index + 1}/{len(job['frames'])} frame {fr['frame']}", flush=True)
    print(f"PENNY_DONE {len(job['frames'])}", flush=True)


if __name__ == "__main__":
    main()
