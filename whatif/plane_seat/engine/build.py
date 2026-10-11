"""Headless picture for the plane-seat Short.

Exterior: BlendKit 405-FLA, generic white livery, gear up, x-ray fuselage.
Interior: the approved cabin GLB, seat rows arrayed to 36 at 0.80 m,
3-4-3, bins and windows kept. Boeing cockpit panel is removed.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import bpy
import mathutils

WHATIF = Path(__file__).resolve().parents[2]
if str(WHATIF) not in sys.path:
    sys.path.insert(0, str(WHATIF))

from plane_seat.engine.aircraft import AMBER, BRIGHT, GREEN, RED, TILE  # noqa: E402
from plane_seat.engine.clock import frame_time  # noqa: E402
from plane_seat.engine.flight import pose_at  # noqa: E402

PLANE = Path("/opt/cursor/asset-cache/private/extracted/405-FLA/Long-range_passenger_aircraft_405-FLA_90155e42.blend")
CABIN = Path("/opt/cursor/asset-cache/private/cabin/airplane_cabin.glb")
HDRI_ZIP = Path("/opt/cursor/asset-cache/cc0/assets_cc0_hdri.zip")
CITY = Path("/opt/cursor/asset-cache/private/glb/procedural_city_3.glb")
TREES = Path("/opt/cursor/asset-cache/private/glb/low_poly_tree_pack.glb")
TEX = Path("/workspace/assets/found/textures")
SKY = Path("/tmp/plane_sky.hdr")

ROWS = 36
PITCH = 0.80
# Nose is +X after the aircraft is turned. Front rows sit toward +X.
ROW0_X = 10.0


def _link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def _emission(name, color, strength=1.2):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def _image_mat(name, path, strength=1.15):
    mat = _emission(name, (1, 1, 1), strength)
    nt = mat.node_tree
    em = nt.nodes["Emission"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path), check_existing=True)
    tex.projection = "BOX"
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    return mat


def _xray(mat):
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    nt = mat.node_tree
    if nt is None:
        return
    for node in nt.nodes:
        if node.type == "BSDF_PRINCIPLED" and "Alpha" in node.inputs:
            node.inputs["Alpha"].default_value = 0.22


def _extract_sky():
    if SKY.exists() and SKY.stat().st_size > 100000:
        return
    import zipfile
    with zipfile.ZipFile(HDRI_ZIP) as zf:
        name = next(n for n in zf.namelist() if n.endswith("belfast_sunset_puresky_2k.hdr"))
        SKY.write_bytes(zf.read(name))


def _world():
    _extract_sky()
    world = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(SKY))
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.05


def _ground(name, image, y_half=1600.0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        [(0, -y_half, 0), (TILE, -y_half, 0), (TILE, y_half, 0), (0, y_half, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(_image_mat(name + "M", image))
    obj.visible_shadow = False
    return obj


def _hide_branding(objs):
    banned = ("boeing", "logo", "airline", "livery", "registration", "overhead panel")
    names = []
    for obj in objs:
        try:
            names.append(obj.name)
        except ReferenceError:
            continue
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        if not any(word in name.lower() for word in banned):
            continue
        for child in list(obj.children_recursive):
            if bpy.data.objects.get(child.name) is not None:
                bpy.data.objects.remove(child, do_unlink=True)
        if bpy.data.objects.get(name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def _seat_templates():
    seats = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        n = len(obj.data.polygons)
        if n < 8000:
            continue
        pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        size = (
            max(p.x for p in pts) - min(p.x for p in pts),
            max(p.y for p in pts) - min(p.y for p in pts),
            max(p.z for p in pts) - min(p.z for p in pts),
        )
        center = sum(pts, mathutils.Vector()) / 8.0
        if size[0] < 1.4 and size[1] < 1.4 and 0.8 < size[2] < 1.4 and center.x > -30:
            seats.append((center.x, center.y, obj))
    if not seats:
        raise RuntimeError("cabin seat meshes were not found")
    # One existing row: the X cluster with the most seats.
    xs = {}
    for x, y, obj in seats:
        xs.setdefault(round(x, 1), []).append((y, obj))
    row = max(xs.values(), key=len)
    row.sort(key=lambda item: item[0])
    return [obj for _y, obj in row]


def _array_seats(root):
    templates = _seat_templates()
    proto = templates[len(templates) // 2]
    bpy.context.view_layer.objects.active = proto
    proto.select_set(True)
    mod = proto.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = 0.18
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mesh = proto.data
    mesh.materials.clear()
    rot = proto.matrix_world.to_euler()
    rot.z += math.pi
    # 3-4-3. Outer seats are windows, the four aisle-side seats are worst,
    # and the inner pair of the center block are the back-cabin middle seats.
    ys = [-2.85, -2.25, -1.65, -0.85, -0.28, 0.28, 0.85, 1.65, 2.25, 2.85]
    roles = ["window", "middle", "aisle", "aisle", "middle", "middle", "aisle", "aisle", "middle", "window"]
    glow = _emission("SeatGlow", (1, 1, 1), 3.4)
    nt = glow.node_tree
    info = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(info.outputs["Color"], nt.nodes["Emission"].inputs["Color"])
    mesh.materials.append(glow)
    for poly in mesh.polygons:
        poly.material_index = 0
    made = []
    for row in range(ROWS):
        third = "front" if row < 12 else ("mid" if row < 24 else "back")
        x = ROW0_X - row * PITCH
        for y, role in zip(ys, roles):
            obj = proto.copy()
            obj.data = mesh
            obj.parent = root
            obj.location = (x, y, 5.55)
            obj.rotation_euler = rot
            obj.scale = (0.82, 0.82, 0.82)
            obj["role"] = role
            obj["third"] = third
            obj["row"] = row
            made.append(obj)
            _link(obj)
    drop = []
    for old in templates:
        try:
            drop.append(old.name)
        except ReferenceError:
            continue
    for obj in list(bpy.data.objects):
        try:
            if obj.type == "MESH" and obj.get("role") is None and len(obj.data.polygons) < 500:
                center = obj.matrix_world.translation
                if abs(center.x) < 3 and abs(center.y) < 1:
                    drop.append(obj.name)
        except ReferenceError:
            continue
    for name in drop:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    print(f"seats {len(made)} rows {ROWS} pitch {PITCH} m abreast {len(ys)} layout 3-4-3")
    return made


def _load_cabin(root):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(CABIN))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    _hide_branding(fresh)
    # Drop the cockpit cluster (nose of this file is -X) so the button forest is gone.
    cockpit = []
    for obj in fresh:
        try:
            if obj.matrix_world.translation.x < -30.5:
                cockpit.append(obj.name)
        except ReferenceError:
            continue
    for name in cockpit:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        for child in list(obj.children_recursive):
            if bpy.data.objects.get(child.name) is not None:
                bpy.data.objects.remove(child, do_unlink=True)
        if bpy.data.objects.get(name) is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
    holder = bpy.data.objects.new("Cabin", None)
    _link(holder, root)
    # Nose of the cabin file is -X. Turn it to +X and stretch it to the 66.5 m fuselage.
    holder.rotation_euler[2] = math.pi
    holder.scale = (66.5 / 55.54, 0.90, 0.90)
    holder.location = (2.0, 0.0, 0.35)
    for obj in list(bpy.data.objects):
        if obj.parent is None and obj is not holder and obj is not root and obj.type != "CAMERA":
            if obj.name.startswith("Sketchfab") or obj.name.startswith("GLTF") or "cabin" in obj.name.lower():
                obj.parent = holder
    # Reparent loose imported roots.
    for obj in fresh:
        try:
            name = obj.name
        except ReferenceError:
            continue
        live = bpy.data.objects.get(name)
        if live is not None and live.parent is None and live is not holder:
            live.parent = holder
    seats = _array_seats(root)

    def _under(obj):
        found = []
        for child in obj.children:
            found.append(child)
            found.extend(_under(child))
        return found

    shell = _under(holder)
    holder.hide_render = True
    return holder, seats, shell


def _load_plane(root):
    with bpy.data.libraries.load(str(PLANE), link=False) as (src, dst):
        dst.objects = [name for name in src.objects]
    empty = None
    for obj in dst.objects:
        if obj is None:
            continue
        _link(obj)
        if obj.name.startswith("Long-range"):
            empty = obj
    if empty is None:
        empty = dst.objects[0]
    empty.parent = root
    # Fuselage runs along Y, nose toward -Y. Turn the nose to +X.
    empty.rotation_euler[2] = math.pi / 2.0
    empty.location = (0.0, 0.0, 0.0)
    for obj in list(empty.children_recursive):
        low = obj.name.lower()
        if "gear" in low:
            obj.hide_render = True
            continue
        if obj.type != "MESH" or obj.name != "Body":
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        dec = obj.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = 0.08
        bpy.ops.object.modifier_apply(modifier=dec.name)
        wire = obj.modifiers.new("Wire", "WIREFRAME")
        wire.thickness = 0.045
        wire.use_replace = True
        bpy.ops.object.modifier_apply(modifier=wire.name)
        obj.data.materials.clear()
        obj.data.materials.append(_emission("HullWire", (0.78, 0.86, 0.95), 1.6))
        print("wire fuselage faces", len(obj.data.polygons))
    return empty


def _biome_tiles():
    specs = {
        "city": TEX / "aerial_ground_rock_diff_1k.jpg",
        "forest": TEX / "forest_ground_04_diff_1k.jpg",
        "mountains": TEX / "aerial_rocks_01_diff_1k.jpg",
        "ocean": TEX / "aerial_beach_01_diff_1k.jpg",
        "desert": TEX / "red_sand_diff_1k.jpg",
        "cloudsea": TEX / "aerial_sand_diff_1k.jpg",
    }
    copies = {}
    for name, image in specs.items():
        a = bpy.data.objects.new(name + "A", None)
        b = bpy.data.objects.new(name + "B", None)
        _link(a)
        _link(b)
        ground = _ground(name + "Ground", image)
        _link(ground, a)
        dup = ground.copy()
        dup.data = ground.data
        _link(dup, b)
        copies[name] = (a, b)
    if CITY.exists():
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(CITY))
        city_root = next(obj for obj in bpy.data.objects if obj not in before and obj.parent is None)
        city_root.parent = copies["city"][0]
        city_root.scale = (2.2, 2.2, 2.2)
        city_root.location = (TILE * 0.5, 0, 0)
    if TREES.exists():
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(TREES))
        tree = next((obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"), None)
        if tree is not None:
            tree.parent = copies["forest"][0]
            for i in range(24):
                inst = tree.copy()
                inst.data = tree.data
                inst.parent = copies["forest"][0]
                inst.location = (40 + (i % 8) * 140, -600 + (i // 8) * 400, 0)
                inst.scale = (8, 8, 8)
                _link(inst)
    puff = _emission("Cloud", (1.0, 0.93, 0.82), 1.6)
    clouds = []
    for i in range(18):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0)
        obj = bpy.context.active_object
        obj.data.materials.append(puff)
        obj.visible_shadow = False
        obj.location = ((i % 6) * 90, -180 + (i // 6) * 120, 150 + (i % 4) * 12)
        obj.scale = (22, 14, 8)
        clouds.append(obj)
    cloud_root = bpy.data.objects.new("CloudField", None)
    _link(cloud_root)
    for obj in clouds:
        obj.parent = cloud_root
    copies["_clouds"] = (cloud_root, cloud_root)
    return copies


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.max_bounces = 2
    scene.cycles.transparent_max_bounces = 2
    scene.cycles.use_light_tree = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 3
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    _world()
    root = _link(bpy.data.objects.new("AircraftRoot", None))
    plane = _load_plane(root)
    cabin, seats, shell = _load_cabin(root)
    biomes = _biome_tiles()
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = 24.0
    cam_data.clip_start = 0.08
    cam_data.clip_end = 8000.0
    cam = _link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
    print("scene ready", "plane", plane.name, "seats", len(seats))
    return {
        "root": root,
        "cabin": cabin,
        "seats": seats,
        "shell": shell,
        "plane_meshes": [obj for obj in plane.children_recursive if obj.type == "MESH" and "gear" not in obj.name.lower()],
        "biomes": biomes,
        "cam": cam,
        "scene": scene,
    }


def _aim(cam, eye, target, roll_deg):
    direction = mathutils.Vector(target) - mathutils.Vector(eye)
    if direction.length < 1e-5:
        return
    direction.normalize()
    quat = mathutils.Vector((0.0, 0.0, -1.0)).rotation_difference(direction)
    roll = mathutils.Quaternion(direction, math.radians(roll_deg))
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = roll @ quat


def _paint(seats, pose):
    colors = pose["colors"]
    for seat in seats:
        role = seat.get("role")
        third = seat.get("third")
        if role == "aisle" and third == "mid":
            color = colors["worst"]
        elif role == "middle" and third == "back":
            color = colors["best"]
        else:
            color = colors[third]
        if pose["scatter"] > 0.2:
            jitter = ((hash(seat.name) % 100) / 100.0, (hash(seat.name[::-1]) % 100) / 100.0, 0.4)
            u = pose["scatter"]
            color = tuple(color[i] * (1 - u) + jitter[i] * u for i in range(3))
        seat.color = (*color, 1.0)
        gap = pose["explode"]
        shift = gap if third == "front" else (-gap if third == "back" else 0.0)
        seat.location.x = ROW0_X - int(seat.get("row", 0)) * PITCH + shift


def apply_pose(state, pose):
    root = state["root"]
    root.location = (0.0, 0.0, pose["altitude"])
    root.rotation_euler = (
        math.radians(pose["roll"]),
        math.radians(pose["pitch"]),
        math.radians(pose["yaw"]),
    )
    phase = pose["scroll"]
    for name, (a, b) in state["biomes"].items():
        if name == "_clouds":
            a.location.x = -phase
            hidden = pose["inside"]
            a.hide_render = hidden
            for child in a.children_recursive:
                child.hide_render = hidden
            continue
        show = name == pose["biome"]
        a.hide_render = not show
        b.hide_render = not show
        for child in a.children_recursive:
            child.hide_render = not show
        for child in b.children_recursive:
            child.hide_render = not show
        a.location.x = -phase
        b.location.x = -phase + TILE
    inside = pose["inside"]
    for mesh in state["plane_meshes"]:
        mesh.hide_render = inside
    for obj in state["shell"]:
        if obj.get("role"):
            continue
        obj.hide_render = True
    # Seat X is rebuilt from the row index each frame.
    for seat in state["seats"]:
        if "row" not in seat:
            # row stored once
            seat["row"] = int(round((ROW0_X - seat.location.x) / PITCH))
    _paint(state["seats"], pose)
    bpy.context.view_layer.update()
    mw = root.matrix_world
    cam = state["cam"]
    eye = mw @ mathutils.Vector(pose["eye"])
    look = mw @ mathutils.Vector(pose["look"])
    cam.location = eye
    _aim(cam, eye, look, pose["cam_roll"])
    cam.data.lens = pose["lens"]


def render_job(job):
    state = build_scene()
    scene = state["scene"]
    scene.render.resolution_percentage = int(job.get("scale", 100))
    tasks = []
    for segment in job.get("segments", []):
        directory = Path(segment["dir"])
        directory.mkdir(parents=True, exist_ok=True)
        for frame in range(int(segment["start"]), int(segment["end"]) + 1):
            tasks.append((frame, directory / f"f_{frame:04d}"))
    for frame in job.get("frames", []):
        directory = Path(job["out"])
        directory.mkdir(parents=True, exist_ok=True)
        tasks.append((int(frame), directory / f"f_{int(frame):04d}"))
    seen = set()
    ordered = []
    for frame, path in tasks:
        ordered.append((frame, path, frame in seen))
        seen.add(frame)
    rendered = {}
    started = time.time()
    done = 0
    unique = [item for item in ordered if not item[2]]
    for frame, path, duplicate in ordered:
        png = path.with_suffix(".png")
        if duplicate:
            src = rendered.get(frame)
            if src and src.resolve() != png.resolve():
                png.write_bytes(src.read_bytes())
            continue
        if png.exists() and png.stat().st_size > 1000 and not job.get("force"):
            rendered[frame] = png
            done += 1
            continue
        apply_pose(state, pose_at(frame_time(frame)))
        scene.cycles.seed = int(frame) * 997 + 17
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered[frame] = png
        done += 1
        if done == 1 or done % 20 == 0 or done == len(unique):
            print(f"frame {frame} {done}/{len(unique)} {time.time() - started:.1f}s", flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    job = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    render_job(job)


if __name__ == "__main__":
    main()
