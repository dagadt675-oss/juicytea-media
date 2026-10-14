"""Headless picture for the plane-seat Short.

Exterior: BlendKit 405-FLA, glossy white over a grey belly, solid the whole
flight. The fuselage skin fades to a glassy hologram only while the seat
zones are on screen. Interior: the approved cabin GLB, seat rows arrayed
to 36 at 0.80 m, 3-4-3. Boeing cockpit panel is removed.
"""

from __future__ import annotations

import json
import math
import sys
import time
import zipfile
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
HGT = Path("/workspace/assets/found/terrain/N45E007.hgt.gz")
HDRI_DIR = Path("/tmp/plane_hdri")
# Pure-sky HDRIs leave the lower frame for our landscapes. goegap / spruit
# bring a photographed horizon for desert and ocean.
SKY_FILES = {
    "city": "belfast_sunset_puresky_2k.hdr",
    "forest": "kloofendal_48d_partly_cloudy_puresky_2k.hdr",
    "mountains": "belfast_sunset_puresky_2k.hdr",
    "ocean": "belfast_sunset_puresky_2k.hdr",
    "desert": "goegap_2k.hdr",
    "cloudsea": "kloofendal_48d_partly_cloudy_puresky_2k.hdr",
}
ALPS_HDR = Path("/workspace/assets/found/hdri/alps_field_2k.hdr")
TERRAIN = Path("/workspace/assets/found/terrain/polyhaven")
# Radians. 0 puts the Belfast sun on the chase camera's horizon.
SKY_TURN = {
    "city": 0.15,
    "forest": 0.4,
    # Alps Field faces the massif toward the chase camera (nose is +X).
    "mountains": 1.15,
    "ocean": -0.2,
    "desert": 1.2,
    "cloudsea": 0.4,
}

ROWS = 36
PITCH = 0.80
# Nose is +X after the aircraft is turned. Front rows sit toward +X.
ROW0_X = 16.0
HAZE = (0.96, 0.48, 0.22)


def _link(obj, parent=None):
    linked = False
    for collection in obj.users_collection:
        linked = True
        break
    if not linked:
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


def _extract_skies():
    HDRI_DIR.mkdir(parents=True, exist_ok=True)
    needed = set(SKY_FILES.values())
    if all((HDRI_DIR / name).exists() and (HDRI_DIR / name).stat().st_size > 100000 for name in needed):
        return
    with zipfile.ZipFile(HDRI_ZIP) as zf:
        for entry in zf.namelist():
            base = Path(entry).name
            if base in needed and base != "alps_field_2k.hdr":
                (HDRI_DIR / base).write_bytes(zf.read(entry))
    if LAGO_HDR.exists():
        target = HDRI_DIR / LAGO_HDR.name
        if not target.exists() or target.stat().st_size < 100000:
            target.write_bytes(LAGO_HDR.read_bytes())


def _mist(scene):
    """Distance haze settings. Ground shaders fade on their own; a full-frame
    mist mix would paint the sky grey because the world sits at infinity."""
    mist = scene.world.mist_settings
    mist.start = 14000.0
    mist.depth = 50000.0
    mist.falloff = "QUADRATIC"
    scene.view_layers[0].use_pass_mist = True


def _world():
    """Sunset HDRI. The image is swapped per biome in apply_pose."""
    _extract_skies()
    world = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.name = "Env"
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.name = "SkyMap"
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.05
    env.image = bpy.data.images.load(str(HDRI_DIR / SKY_FILES["city"]), check_existing=True)
    mapping.inputs["Rotation"].default_value[2] = SKY_TURN["city"]
    return env, mapping, bg


def _mix_rgb(nt, fac_socket, color_a, color_b):
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Fac"].default_value = 1.0
    if fac_socket is not None:
        nt.links.new(fac_socket, mix.inputs["Fac"])
    if isinstance(color_a, tuple):
        mix.inputs["Color1"].default_value = color_a
    else:
        nt.links.new(color_a, mix.inputs["Color1"])
    if isinstance(color_b, tuple):
        mix.inputs["Color2"].default_value = color_b
    else:
        nt.links.new(color_b, mix.inputs["Color2"])
    return mix


def _terrain(name, image, roughness=0.92, tint=(1, 1, 1), warmth=0.22, scale=0.00085, shade=0.62, dunes=False):
    """Large-scale photo ground. Mapping location scrolls the texture."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = roughness
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(image), check_existing=True)
    tex.extension = "REPEAT"
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    source = tex.outputs["Color"]
    if dunes:
        # The sand photo is a fine grain that disappears at 1600 m. Large
        # noise blotches read as dunes without a high-frequency shimmer.
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 0.0016
        noise.inputs["Detail"].default_value = 1.0
        noise.inputs["Roughness"].default_value = 0.45
        nt.links.new(coord.outputs["Generated"], noise.inputs["Vector"])
        noise.inputs["Scale"].default_value = 7.0
        dunes_col = _mix_rgb(nt, noise.outputs["Fac"], (0.45, 0.28, 0.16, 1), (0.93, 0.78, 0.55, 1))
        mixed = _mix_rgb(nt, None, tex.outputs["Color"], dunes_col.outputs["Color"])
        mixed.inputs["Fac"].default_value = 0.88
        source = mixed.outputs["Color"]
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.55
        bump.inputs["Distance"].default_value = 260.0
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    warm = _mix_rgb(nt, None, source, (*tint, 1))
    warm.inputs["Fac"].default_value = warmth
    # A light touch only. A heavy darken plus an early orange fade turned the
    # 1600 m chase into a flat haze with no landscape.
    dark = _mix_rgb(nt, None, warm.outputs["Color"], (0.15, 0.12, 0.1, 1))
    dark.inputs["Fac"].default_value = shade
    cam = nt.nodes.new("ShaderNodeCameraData")
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = 14000.0
    span.inputs["From Max"].default_value = 48000.0
    span.inputs["To Min"].default_value = 0.0
    span.inputs["To Max"].default_value = 0.18
    span.clamp = True
    nt.links.new(cam.outputs["View Distance"], span.inputs["Value"])
    haze = _mix_rgb(nt, span.outputs["Result"], dark.outputs["Color"], (*HAZE, 1))
    nt.links.new(haze.outputs["Color"], bsdf.inputs["Base Color"])
    return mat, mapping


def _ground_plane(name, y_half=1800.0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        [(0, -y_half, 0), (TILE, -y_half, 0), (TILE, y_half, 0), (0, y_half, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    return bpy.data.objects.new(name, mesh)


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


def _seat_material():
    """Zone color from the object color, with enough diffuse to read as a seat."""
    mat = bpy.data.materials.new("SeatGlow")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    dark = nt.nodes.new("ShaderNodeMixRGB")
    dark.inputs["Fac"].default_value = 0.72
    dark.inputs["Color2"].default_value = (0.02, 0.02, 0.025, 1)
    nt.links.new(info.outputs["Color"], dark.inputs["Color1"])
    nt.links.new(dark.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(info.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 2.2
    bsdf.inputs["Roughness"].default_value = 0.45
    return mat


def _array_seats(root):
    bpy.context.view_layer.update()
    templates = _seat_templates()
    proto = templates[len(templates) // 2]
    mesh = proto.data
    mesh.materials.clear()
    rot = proto.matrix_world.to_euler()
    rot.z += math.pi
    # 3-4-3. Outer seats are windows, the four aisle-side seats are worst,
    # and the inner pair of the center block are the back-cabin middle seats.
    ys = [-2.15, -1.72, -1.29, -0.62, -0.20, 0.20, 0.62, 1.29, 1.72, 2.15]
    roles = ["window", "middle", "aisle", "aisle", "middle", "middle", "aisle", "aisle", "middle", "window"]
    glow = _seat_material()
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
            obj.location = (x, y, 6.35)
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


def _principled(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.25
    return mat, bsdf


def _polish_paint(mat):
    """Keep the downloaded paint, normal, and roughness maps. Add a clearcoat."""
    if mat is None or mat.node_tree is None:
        return
    bsdf = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.78
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.06
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.55
    if "Base Color" not in bsdf.inputs or not bsdf.inputs["Base Color"].is_linked:
        return
    link = bsdf.inputs["Base Color"].links[0]
    nt = mat.node_tree
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    if "Distance" in ao.inputs:
        ao.inputs["Distance"].default_value = 0.55
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.28
    nt.links.new(link.from_socket, mix.inputs["Color1"])
    nt.links.new(ao.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    _panel_lines(nt, bsdf)


def _math(nt, op, a, b):
    node = nt.nodes.new("ShaderNodeMath")
    node.operation = op
    if isinstance(a, (int, float)):
        node.inputs[0].default_value = a
    else:
        nt.links.new(a, node.inputs[0])
    if isinstance(b, (int, float)):
        node.inputs[1].default_value = b
    else:
        nt.links.new(b, node.inputs[1])
    return node.outputs["Value"]


def _panel_lines(nt, bsdf):
    """Circumferential rings, a few long seams, and a generic cheatline.

    The fuselage axis on this mesh is local Y. No airline name, no tail mark.
    """
    if "Base Color" not in bsdf.inputs or not bsdf.inputs["Base Color"].is_linked:
        return
    src = bsdf.inputs["Base Color"].links[0].from_socket
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    # Sparse rings, and only on the tube. A full grid reads as a wireframe.
    rings = _math(nt, "LESS_THAN", _math(nt, "FRACT", _math(nt, "DIVIDE", sep.outputs["Y"], 3.4), 0.0), 0.018)
    abs_x = _math(nt, "ABSOLUTE", sep.outputs["X"], 0.0)
    on_tube = _math(
        nt, "MULTIPLY",
        _math(nt, "LESS_THAN", abs_x, 3.35),
        _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", sep.outputs["Z"], 4.2), _math(nt, "LESS_THAN", sep.outputs["Z"], 11.2)),
    )
    lines = _math(nt, "MULTIPLY", rings, on_tube)
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 9.0
    grain.inputs["Detail"].default_value = 6.0
    grain.inputs["Roughness"].default_value = 0.62
    nt.links.new(coord.outputs["Object"], grain.inputs["Vector"])
    grain_amt = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", grain.outputs["Fac"], 0.5), 0.05)
    shade = _math(nt, "SUBTRACT", 1.0, _math(nt, "MULTIPLY", lines, 0.42))
    shade = _math(nt, "ADD", shade, grain_amt)
    grey = nt.nodes.new("ShaderNodeCombineColor")
    nt.links.new(shade, grey.inputs["Red"])
    nt.links.new(shade, grey.inputs["Green"])
    nt.links.new(shade, grey.inputs["Blue"])
    broken = nt.nodes.new("ShaderNodeMixRGB")
    broken.blend_type = "MULTIPLY"
    broken.inputs["Fac"].default_value = 1.0
    nt.links.new(src, broken.inputs["Color1"])
    nt.links.new(grey.outputs["Color"], broken.inputs["Color2"])
    # Narrow navy cheatline. Generic, not a carrier livery.
    above = _math(nt, "GREATER_THAN", sep.outputs["Z"], 7.08)
    below = _math(nt, "LESS_THAN", sep.outputs["Z"], 7.38)
    stripe = _math(nt, "MULTIPLY", above, below)
    band = nt.nodes.new("ShaderNodeMixRGB")
    band.blend_type = "MIX"
    nt.links.new(stripe, band.inputs["Fac"])
    nt.links.new(broken.outputs["Color"], band.inputs["Color1"])
    band.inputs["Color2"].default_value = (0.07, 0.16, 0.34, 1.0)
    nt.links.remove(bsdf.inputs["Base Color"].links[0])
    nt.links.new(band.outputs["Color"], bsdf.inputs["Base Color"])
    if "Roughness" in bsdf.inputs and not bsdf.inputs["Roughness"].is_linked:
        rough = _math(nt, "ADD", bsdf.inputs["Roughness"].default_value, _math(nt, "MULTIPLY", lines, 0.18))
        nt.links.new(rough, bsdf.inputs["Roughness"])


def _shade_airliner(body):
    by_name = {mat.name: mat for mat in body.data.materials if mat}
    paint = by_name.get("Matal solid paint white")
    _polish_paint(paint)
    # Tube skin is a copy of the real paint so the x-ray fades the fuselage only.
    tube = paint.copy() if paint is not None else body.data.materials[0].copy()
    tube.name = "FuselageSkin"
    body.data.materials.append(tube)
    tube_i = len(body.data.materials) - 1
    for poly in body.data.polygons:
        if poly.material_index != 0:
            continue
        c = poly.center
        in_tube = abs(c.x) < 3.7 and -30.0 < c.y < 16.0 and 3.2 < c.z < 11.5
        if in_tube and c.z >= 6.15:
            poly.material_index = tube_i


def _fan_mesh():
    """Disc in the XZ plane so the intake faces body -Y (the nose)."""
    import bmesh

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.28, radius2=0.28, depth=0.08)
    for vert in bm.verts:
        vert.co = mathutils.Vector((vert.co.x, vert.co.z, vert.co.y))
    for i in range(16):
        ang = i * math.tau / 16.0
        ca, sa = math.cos(ang), math.sin(ang)
        verts = []
        for along, across in ((0.32, -0.045), (0.32, 0.045), (1.15, 0.02), (1.15, -0.02)):
            verts.append(bm.verts.new((ca * along - sa * across, 0.0, sa * along + ca * across)))
        bm.faces.new(verts)
    me = bpy.data.meshes.new("Fan")
    bm.to_mesh(me)
    bm.free()
    return me


def _engine_intakes(body):
    """Front lip of each under-wing nacelle. Nose of this mesh is -Y."""
    groups = {"ol": [], "or": [], "il": [], "ir": []}
    for poly in body.data.polygons:
        if poly.material_index != 1:
            continue
        c = poly.center
        if c.z > 6.2 or abs(c.x) < 6.0:
            continue
        side = "o" if abs(c.x) > 13.0 else "i"
        groups[side + ("l" if c.x < 0 else "r")].append(c.copy())
    intakes = []
    for pts in groups.values():
        if len(pts) < 30:
            continue
        front = min(p.y for p in pts)
        near = [p for p in pts if p.y < front + 0.7]
        n = float(len(near))
        intakes.append((
            sum(p.x for p in near) / n,
            sum(p.y for p in near) / n,
            sum(p.z for p in near) / n,
        ))
    return intakes


def _add_fans(body):
    mesh = _fan_mesh()
    mat, _ = _principled("FanMetal", (0.08, 0.09, 0.10), 0.32, 0.7)
    mesh.materials.append(mat)
    placed = []
    for center in _engine_intakes(body):
        obj = bpy.data.objects.new("Fan", mesh)
        obj.parent = body
        # Sit just inside the intake lip so the disc reads as fan blades.
        obj.location = (center[0], center[1] + 0.35, center[2])
        obj.scale = (0.72, 0.72, 0.72)
        _link(obj)
        placed.append(tuple(round(v, 2) for v in center))
    print("fans", placed)


def _fade_glass(mat):
    """Mix the window shader toward transparent. Fac 0 keeps the real glass."""
    nt = mat.node_tree
    if nt is None:
        return None
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if out is None or not out.inputs["Surface"].is_linked:
        return None
    link = out.inputs["Surface"].links[0]
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    src = link.from_socket
    nt.links.remove(link)
    nt.links.new(src, mix.inputs[1])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mix.inputs["Fac"].default_value = 0.0
    return mix.inputs["Fac"]


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
    body = None
    skin_nodes = []
    for obj in list(empty.children_recursive):
        low = obj.name.lower()
        if "gear" in low:
            obj.hide_render = True
            continue
        # Nav-light meshes are starbursts. Unlit, they read as a black glitch.
        if obj.type == "MESH" and any(key in low for key in ("light", "lamp", "beacon", "strobe", "bulb")):
            obj.hide_render = True
            continue
        if obj.type == "MESH" and obj.name == "Body":
            body = obj
    glass_facs = []
    if body is not None:
        _shade_airliner(body)
        for mat in body.data.materials:
            if mat is None or mat.node_tree is None:
                continue
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED" and "Alpha" in node.inputs:
                    # Wings and tail stay the white paint. Only the tube fades.
                    if mat.name in ("FuselageSkin", "BellyGrey"):
                        skin_nodes.append(node)
            low = mat.name.lower()
            if "glass" in low or "frost" in low or "window" in low:
                for node in mat.node_tree.nodes:
                    if node.type == "BSDF_PRINCIPLED" and "Emission Strength" in node.inputs:
                        if not node.inputs["Emission Strength"].is_linked:
                            node.inputs["Emission Strength"].default_value = 0.0
            if "glass" in low or "frost" in low:
                fac = _fade_glass(mat)
                if fac is not None:
                    glass_facs.append(fac)
        _add_fans(body)
        import bmesh
        opened = body.copy()
        opened.data = body.data.copy()
        # The copy already carries the parent's inverse scale. Assigning
        # parent again drops that inverse and blows the mesh up by ~15x,
        # which put the lens inside a black shell on the seat beats.
        parent_inverse = body.matrix_parent_inverse.copy()
        opened.parent = empty
        opened.matrix_parent_inverse = parent_inverse
        _link(opened)
        bm = bmesh.new()
        bm.from_mesh(opened.data)
        kill = []
        for face in bm.faces:
            c = face.calc_center_median()
            # Open the crown of the tube only. The fin is farther aft (local +Y).
            if abs(c.x) < 3.55 and c.z > 4.6 and -30.0 < c.y < 18.0:
                kill.append(face)
        lid = None
        if kill:
            lid_bm = bmesh.new()
            copied = {}
            for face in kill:
                verts = []
                for vert in face.verts:
                    if vert not in copied:
                        copied[vert] = lid_bm.verts.new(vert.co)
                    verts.append(copied[vert])
                try:
                    lid_bm.faces.new(verts)
                except ValueError:
                    pass
            lid_mesh = bpy.data.meshes.new("FuselageLid")
            lid_bm.to_mesh(lid_mesh)
            lid_bm.free()
            for mat in opened.data.materials:
                lid_mesh.materials.append(mat)
            lid = bpy.data.objects.new("FuselageLid", lid_mesh)
            lid.parent = empty
            lid.matrix_parent_inverse = parent_inverse
            lid.hide_render = True
            _link(lid)
            bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(opened.data)
        bm.free()
        opened.name = "BodyCutaway"
        opened.hide_render = True
        print("cutaway faces", len(kill))
    else:
        opened = None
        lid = None
    return empty, skin_nodes, body, opened, glass_facs, lid


def _labels(root):
    """Big 3D callouts. Exterior zones sit beside the tube; 44/28 sit in the aisle."""
    font_path = WHATIF / "scale_journey/assets/fonts/Anton-Regular.ttf"
    font = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None
    # (text, color, location, em size)
    # Inboard of the tube so a 3/4 view keeps every plate inside the portrait frame.
    specs = {
        # Beside the zone, not stacked in the sky. Em 3.6 is about 4 m of
        # plate, over 6% of the 9:16 frame from the orbit (about 40 m, 20 mm).
        # Anchor is where the leader meets the cabin.
        "l38": ("38%", AMBER, (4.0, -6.5, 6.5), 2.8, (11.0, -1.5, 3.2)),
        "l39": ("39%", AMBER, (1.5, -4.4, 4.8), 2.8, (1.5, -1.5, 3.2)),
        "l32": ("32%", GREEN, (-8.5, -4.4, 4.8), 2.8, (-8.5, -1.5, 3.2)),
        "l44": ("44%", RED, (1.5, -8.5, 8.0), 2.8, (1.5, -0.5, 3.0)),
        "l28": ("28%", BRIGHT, (-8.5, -4.6, 4.2), 2.8, (-8.5, 0.0, 3.0)),
        "l17": ("17", AMBER, (8.0, -6.0, 6.2), 2.6, (10.0, -1.6, 3.4)),
    }
    out = {}
    for key, (text, color, loc, size, anchor) in specs.items():
        holder = bpy.data.objects.new(key, None)
        holder.parent = root
        holder.location = loc
        _link(holder)
        curve = bpy.data.curves.new(key + "Text", "FONT")
        curve.body = text
        curve.align_x = "CENTER"
        curve.align_y = "CENTER"
        curve.size = size
        curve.extrude = size * 0.04
        if font:
            curve.font = font
        glyphs = bpy.data.objects.new(key + "Glyph", curve)
        glyphs.parent = holder
        glyphs.data.materials.append(_emission(key + "M", color, 4.5))
        _link(glyphs)
        card = bpy.data.meshes.new(key + "Card")
        w, h, z = size * 1.05, size * 0.58, -size * 0.15
        card.from_pydata(
            [(-w, -h, z), (w, -h, z), (w, h, z), (-w, h, z)],
            [],
            [(0, 1, 2, 3)],
        )
        plate = bpy.data.objects.new(key + "Plate", card)
        plate.parent = holder
        plate.data.materials.append(_emission(key + "Bg", (0.02, 0.015, 0.02), 1.2))
        _link(plate)
        lead = bpy.data.curves.new(key + "Lead", "CURVE")
        lead.dimensions = "3D"
        lead.bevel_depth = 0.07
        lead.resolution_u = 2
        spline = lead.splines.new("POLY")
        spline.points.add(1)
        spline.points[0].co = (0.0, 0.0, 0.0, 1.0)
        spline.points[1].co = (
            anchor[0] - loc[0],
            anchor[1] - loc[1],
            anchor[2] - loc[2],
            1.0,
        )
        wire = bpy.data.objects.new(key + "Wire", lead)
        wire.parent = holder
        wire.data.materials.append(_emission(key + "WireM", color, 3.0))
        _link(wire)
        out[key] = holder
    return out


def _big_plane(name, size=20000.0):
    mesh = bpy.data.meshes.new(name)
    s = size
    mesh.from_pydata(
        [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    obj = bpy.data.objects.new(name, mesh)
    obj["ground"] = 1
    obj.location.z = -2.0
    return obj


MOUNTAINS = Path("/opt/cursor/asset-cache/private/mountains")
LAGO_HDR = MOUNTAINS / "lago_disola_4k.hdr"


def _alpine_grade(mat):
    """Light snow on high upward faces, then aerial haze so distant ridges recede."""
    if mat is None or not mat.use_nodes or mat.get("alpine_grade"):
        return
    nt = mat.node_tree
    bsdf = next((node for node in nt.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None or "Base Color" not in bsdf.inputs:
        return
    link = next((item for item in nt.links if item.to_socket == bsdf.inputs["Base Color"]), None)
    if link is None:
        return
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    height_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geom.outputs["Position"], height_sep.inputs["Vector"])
    height = nt.nodes.new("ShaderNodeMapRange")
    height.inputs["From Min"].default_value = 280.0
    height.inputs["From Max"].default_value = 620.0
    height.clamp = True
    nt.links.new(height_sep.outputs["Z"], height.inputs["Value"])
    normal_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geom.outputs["Normal"], normal_sep.inputs["Vector"])
    upward = nt.nodes.new("ShaderNodeMapRange")
    upward.inputs["From Min"].default_value = 0.15
    upward.inputs["From Max"].default_value = 0.55
    upward.clamp = True
    nt.links.new(normal_sep.outputs["Z"], upward.inputs["Value"])
    snow_fac = nt.nodes.new("ShaderNodeMath")
    snow_fac.operation = "MULTIPLY"
    nt.links.new(height.outputs["Result"], snow_fac.inputs[0])
    nt.links.new(upward.outputs["Result"], snow_fac.inputs[1])
    snow_scale = nt.nodes.new("ShaderNodeMath")
    snow_scale.operation = "MULTIPLY"
    snow_scale.inputs[1].default_value = 0.45
    nt.links.new(snow_fac.outputs["Value"], snow_scale.inputs[0])
    # Keep the painted snow. This only thickens thin caps.
    snow = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(snow_scale.outputs["Value"], snow.inputs["Fac"])
    nt.links.new(link.from_socket, snow.inputs["Color1"])
    snow.inputs["Color2"].default_value = (0.93, 0.95, 0.97, 1.0)
    cam = nt.nodes.new("ShaderNodeCameraData")
    dist = nt.nodes.new("ShaderNodeMapRange")
    dist.inputs["From Min"].default_value = 4000.0
    dist.inputs["From Max"].default_value = 26000.0
    dist.inputs["To Min"].default_value = 0.0
    dist.inputs["To Max"].default_value = 0.22
    dist.clamp = True
    nt.links.new(cam.outputs["View Distance"], dist.inputs["Value"])
    haze = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(dist.outputs["Result"], haze.inputs["Fac"])
    nt.links.new(snow.outputs["Color"], haze.inputs["Color1"])
    haze.inputs["Color2"].default_value = (0.62, 0.70, 0.80, 1.0)
    nt.links.new(haze.outputs["Color"], bsdf.inputs["Base Color"])
    mat["alpine_grade"] = 1


def _hub_peak_material():
    """Baked terrain colour from the hub peak, stretched across the range.

    The Gaea albedo is a high-contrast satellite shade. At Shorts size it
    flickers. This keeps a downloaded hub texture and drops its normal map.
    """
    before_obj = set(bpy.data.objects)
    before_img = set(bpy.data.images)
    bpy.ops.import_scene.gltf(filepath=str(MOUNTAINS / "bk_peak.glb"))
    images = [im for im in bpy.data.images if im not in before_img]
    if len(images) < 2:
        raise RuntimeError("bk_peak base color")
    image = images[1]
    image.pack()
    for obj in list(bpy.data.objects):
        if obj not in before_obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    mat = bpy.data.materials.new("HubPeakTerrain")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(node for node in nt.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.92
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.25
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.12, 0.12, 0.12)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Smart"
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    # The hub photo is a high-contrast satellite shade. Crush that range,
    # then sit it on a light grey so a phone does not flicker between
    # black crevices and white ridges.
    flat = nt.nodes.new("ShaderNodeBrightContrast")
    flat.inputs["Bright"].default_value = 0.08
    flat.inputs["Contrast"].default_value = -0.75
    nt.links.new(tex.outputs["Color"], flat.inputs["Color"])
    soften = nt.nodes.new("ShaderNodeMixRGB")
    soften.inputs["Fac"].default_value = 0.72
    soften.inputs["Color2"].default_value = (0.84, 0.86, 0.88, 1.0)
    nt.links.new(flat.outputs["Color"], soften.inputs["Color1"])
    nt.links.new(soften.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    # Almost no shading normal. Fine ridge shadows are what shimmer.
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    scaled = nt.nodes.new("ShaderNodeVectorMath")
    scaled.operation = "SCALE"
    scaled.inputs["Scale"].default_value = 0.04
    nt.links.new(geom.outputs["Normal"], scaled.inputs[0])
    lifted = nt.nodes.new("ShaderNodeVectorMath")
    lifted.operation = "ADD"
    lifted.inputs[1].default_value = (0.0, 0.0, 1.0)
    nt.links.new(scaled.outputs["Vector"], lifted.inputs[0])
    nt.links.new(lifted.outputs["Vector"], bsdf.inputs["Normal"])
    return mat


def _refine_near_snow(obj):
    """Subdivide the heightfield under the chase. The far ridges stay coarse.

    A full subdivision of every Gaea chunk exhausted memory. The triangles
    that read on a phone are the ones below and just ahead of the jet.
    """
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    edges = set()
    for face in bm.faces:
        center = face.calc_center_median()
        if -0.95 <= center.x <= 0.45 and abs(center.y) <= 0.8:
            edges.update(face.edges)
    if len(edges) < 12:
        bm.free()
        return 0
    bmesh.ops.subdivide_edges(
        bm,
        edges=list(edges),
        cuts=1,
        use_grid_fill=True,
        smooth=0.55,
    )
    verts = [vert for vert in bm.verts if -1.0 <= vert.co.x <= 0.5 and abs(vert.co.y) <= 0.85]
    for _ in range(3):
        bmesh.ops.smooth_vert(
            bm,
            verts=verts,
            factor=0.55,
            use_axis_x=True,
            use_axis_y=True,
            use_axis_z=True,
        )
    bm.to_mesh(obj.data)
    obj.data.update()
    count = len(obj.data.vertices)
    bm.free()
    _drop_custom_normals(obj.data)
    return count


def _drop_custom_normals(mesh):
    """glTF split normals keep every face flat even after shade_smooth."""
    for name in ("custom_normal", "sharp_face", "sharp_edge"):
        attr = mesh.attributes.get(name)
        if attr is not None:
            mesh.attributes.remove(attr)
    try:
        mesh.shade_smooth()
    except (AttributeError, RuntimeError):
        for poly in mesh.polygons:
            poly.use_smooth = True


def _import_mountain(filename, name, grade=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(MOUNTAINS / filename))
    bpy.context.view_layer.update()
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in fresh if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(filename)
    xs, ys, zs = [], [], []
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(world.x)
            ys.append(world.y)
            zs.append(world.z)
        if grade:
            for mat in obj.data.materials:
                _alpine_grade(mat)
        # The heightfield is dense enough. Flat normals are what read as facets.
        mesh = obj.data
        if "sharp_face" in getattr(mesh, "attributes", {}):
            mesh.attributes.remove(mesh.attributes["sharp_face"])
        try:
            mesh.shade_smooth()
        except (AttributeError, RuntimeError):
            for poly in mesh.polygons:
                poly.use_smooth = True
        soften = obj.modifiers.new("Soften", "SMOOTH")
        soften.factor = 0.85
        soften.iterations = 24
    col = bpy.data.collections.new(name)
    for obj in fresh:
        for holder in list(obj.users_collection):
            holder.objects.unlink(obj)
        col.objects.link(obj)
    print(name, "size", round(max(xs) - min(xs), 2), round(max(zs) - min(zs), 2), "z0", round(min(zs), 3))
    return col, min(zs)


def _place_mountain(parent, col, z0, x, y, scale, yaw, mirror=False, z_scale=None):
    inst = bpy.data.objects.new(col.name + "_inst", None)
    inst.instance_type = "COLLECTION"
    inst.instance_collection = col
    inst.parent = parent
    zs = scale if z_scale is None else z_scale
    sx = -scale if mirror else scale
    inst.scale = (sx, scale, zs)
    inst.rotation_euler[2] = yaw
    # Seat the lowest vertex on z=0 so peaks stay a known height below the jet.
    inst.location = (x, y, -z0 * zs)
    inst["cull"] = 1
    inst["cull_radius"] = abs(scale) * (1.15 if abs(scale) > 40 else 520.0)
    _link(inst)
    return inst


def _soft_snow_material():
    """Broad snow colour. No satellite albedo, so the phone does not flicker."""
    mat = bpy.data.materials.new("SoftSnow")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(node for node in nt.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.04
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 1.0
    noise.inputs["Roughness"].default_value = 0.4
    nt.links.new(coord.outputs["Generated"], noise.inputs["Vector"])
    tint = _mix_rgb(nt, noise.outputs["Fac"], (0.76, 0.79, 0.83, 1), (0.90, 0.91, 0.93, 1))
    soft = _mix_rgb(nt, None, (0.84, 0.86, 0.88, 1), tint.outputs["Color"])
    soft.inputs["Fac"].default_value = 0.35
    nt.links.new(soft.outputs["Color"], bsdf.inputs["Base Color"])
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    scaled = nt.nodes.new("ShaderNodeVectorMath")
    scaled.operation = "SCALE"
    scaled.inputs["Scale"].default_value = 0.22
    nt.links.new(geom.outputs["Normal"], scaled.inputs[0])
    lifted = nt.nodes.new("ShaderNodeVectorMath")
    lifted.operation = "ADD"
    lifted.inputs[1].default_value = (0.0, 0.0, 0.85)
    nt.links.new(scaled.outputs["Vector"], lifted.inputs[0])
    nt.links.new(lifted.outputs["Vector"], bsdf.inputs["Normal"])
    return mat


def _snow_sheet(parent, mat):
    """Low-frequency hills. The downloaded heightfield's fine ridges shimmered."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=56, y_subdivisions=56, size=42000.0)
    obj = bpy.context.active_object
    obj.name = "SnowSheet"
    obj.parent = parent
    obj.location = (4000.0, 0.0, 120.0)
    sub = obj.modifiers.new("Sub", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    tex = bpy.data.textures.new("SnowHills", "CLOUDS")
    tex.noise_scale = 2400.0
    tex.noise_depth = 1
    tex.noise_type = "SOFT_NOISE"
    disp = obj.modifiers.new("Hills", "DISPLACE")
    disp.texture = tex
    disp.texture_coords = "OBJECT"
    disp.direction = "Z"
    disp.strength = 520.0
    disp.mid_level = 0.5
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj["ground"] = 1
    return obj


def _alps_range(parent):
    """Hub peaks on the mountain leg of the route. No white void sheet."""
    calm = _hub_peak_material()
    # The satellite shade flickers at phone size. Keep the hub mesh, drop the photo.
    bsdf = next(n for n in calm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for link in list(bsdf.inputs["Base Color"].links):
        calm.node_tree.links.remove(link)
    bsdf.inputs["Base Color"].default_value = (0.80, 0.83, 0.86, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    gaea, gaea_z = _import_mountain("gaea_range.glb", "GaeaRange", grade=False)
    textured, textured_z = _import_mountain("free_textured_mountain.glb", "TexturedPeak", grade=False)
    for col in (gaea, textured):
        for obj in col.objects:
            if obj.type != "MESH":
                continue
            obj.data.materials.clear()
            obj.data.materials.append(calm)
            _drop_custom_normals(obj.data)
            for mod in list(obj.modifiers):
                if mod.type == "SMOOTH":
                    mod.iterations = 4
                    mod.factor = 0.6
    _place_mountain(parent, gaea, gaea_z, 0.0, 200.0, 1400.0, 0.2, z_scale=1100.0)
    for x, y, scale, yaw, zs in (
        (-700.0, -800.0, 1.6, 0.4, 2.0),
        (800.0, 600.0, 2.0, -0.3, 2.4),
        (200.0, -1400.0, 1.3, 0.8, 1.6),
    ):
        _place_mountain(parent, textured, textured_z, x, y, scale, yaw, z_scale=zs)
    print("route peaks")


REAL_TREES = Path("/workspace/assets/found/trees/realistic")


def _forest_trees(parent):
    glbs = sorted(REAL_TREES.glob("*.glb"))
    if not glbs:
        print("no realistic trees")
        return
    templates = []
    for path in glbs:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(path))
        meshes = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
        if not meshes:
            continue
        src = meshes[0]
        zs = [vert.co.z for vert in src.data.vertices]
        height = (max(zs) - min(zs)) if zs else 8.0
        src.hide_render = True
        templates.append((src, height))
        print("realistic tree", path.name, "height", round(height, 2))
    if not templates:
        return
    # Photoscanned saplings are 6–9 m. Scale them into a 16–30 m canopy.
    # The strip sits ahead of the nose across the forest scroll (phase ~400–1,200 m).
    # A close stand under the chase camera at t≈7.4 (the tile has scrolled ~1 km).
    ground_z = -2.0
    # Wide enough that the chase at t≈7.4 (scroll ~1.08 km) sees canopy, not one clump.
    cols = 36
    rows = 14
    spacing = 42.0
    x0 = -500.0
    lods = {}

    def lod_for(mesh):
        if mesh.name in lods:
            return lods[mesh.name]
        tmp = bpy.data.objects.new("lodtmp", mesh.copy())
        _link(tmp)
        mod = tmp.modifiers.new("Dec", "DECIMATE")
        mod.ratio = 0.22
        bpy.context.view_layer.objects.active = tmp
        bpy.ops.object.modifier_apply(modifier="Dec")
        low = tmp.data
        low.name = mesh.name + "_far"
        bpy.data.objects.remove(tmp, do_unlink=True)
        lods[mesh.name] = low
        return low

    for i in range(cols * rows):
        src, height = templates[(i * 3) % len(templates)]
        obj = src.copy()
        obj.data = src.data
        obj.parent = parent
        obj.hide_render = False
        metres = 46.0 + (i % 7) * 6.0
        scale = metres / max(height, 0.1)
        base = min(vert.co.z for vert in src.data.vertices) if src.data.vertices else 0.0
        # Break the rows so the canopy is not a plantation grid.
        jitter_x = ((i * 17) % 9) - 4
        jitter_y = ((i * 13) % 9) - 4
        obj.scale = (scale, scale, scale * (0.85 + (i % 5) * 0.06))
        obj.location = (
            x0 + (i % cols) * spacing + jitter_x,
            (i // cols) * spacing - (rows * spacing) * 0.5 + jitter_y,
            ground_z - base * scale,
        )
        obj.rotation_euler[2] = (i % 11) * 0.57
        low = lod_for(src.data)
        obj["near_mesh"] = src.data.name
        obj["lod_mesh"] = low.name
        obj["cull"] = 1
        obj["cull_radius"] = metres * 0.55
        _link(obj)
    print("realistic trees", len(templates), "instances", cols * rows)


def _enable_easy_clouds():
    module = "bl_ext.user_default.easy_clouds"
    if module not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=module)
    print("easy clouds", module)


def _cumulus_mat(density):
    """White sunlit puff. Noise breaks the cube into a cumulus, anisotropy lights the rim."""
    mat = bpy.data.materials.new("Cumulus")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.2
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    length = nt.nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    nt.links.new(coord.outputs["Object"], length.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value = 0.05
    fall.inputs["From Max"].default_value = 0.62
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    fall.clamp = True
    nt.links.new(length.outputs["Value"], fall.inputs["Value"])
    carved = nt.nodes.new("ShaderNodeMapRange")
    carved.inputs["From Min"].default_value = 0.38
    carved.inputs["From Max"].default_value = 0.72
    carved.clamp = True
    nt.links.new(noise.outputs["Fac"], carved.inputs["Value"])
    shaped = _math(nt, "MULTIPLY", fall.outputs["Result"], carved.outputs["Result"])
    dense = _math(nt, "MULTIPLY", shaped, density)
    nt.links.new(dense, vol.inputs["Density"])
    vol.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    if "Absorption Color" in vol.inputs:
        vol.inputs["Absorption Color"].default_value = (0.97, 0.98, 1.0, 1.0)
    if "Anisotropy" in vol.inputs:
        vol.inputs["Anisotropy"].default_value = 0.62
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return mat


def _cumulus(parent, loc, scale, density, kind):
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    obj = bpy.context.active_object
    obj.parent = parent
    obj.location = loc
    obj.scale = scale
    obj["kind"] = kind
    obj.data.materials.append(_cumulus_mat(density))
    obj.visible_shadow = True
    return obj


def _easy_cloud(parent, loc, scale, density, kind):
    return _cumulus(parent, loc, scale, density, kind)


def _godrays():
    """A thin cabin volume so sun shafts read when the roof is open."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    obj = bpy.context.active_object
    obj.name = "CabinGodrays"
    obj.scale = (32.0, 8.0, 10.0)
    obj.location = (0.0, 0.0, 11.0)
    mat = bpy.data.materials.new("Godray")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.012
    vol.inputs["Color"].default_value = (1.0, 0.82, 0.62, 1.0)
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    obj.data.materials.append(mat)
    return obj


def _ocean_mat():
    mat = bpy.data.materials.new("Ocean")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(node for node in nt.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.04
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.9
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.15
    cam = nt.nodes.new("ShaderNodeCameraData")
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = 9000.0
    span.inputs["From Max"].default_value = 36000.0
    span.inputs["To Min"].default_value = 0.0
    span.inputs["To Max"].default_value = 0.28
    span.clamp = True
    nt.links.new(cam.outputs["View Distance"], span.inputs["Value"])
    haze = _mix_rgb(nt, span.outputs["Result"], (0.04, 0.16, 0.22, 1), (0.55, 0.62, 0.68, 1))
    nt.links.new(haze.outputs["Color"], bsdf.inputs["Base Color"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 2.4
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _move_to_collection(objs, col):
    for obj in objs:
        try:
            name = obj.name
        except ReferenceError:
            continue
        live = bpy.data.objects.get(name)
        if live is None:
            continue
        for holder in list(live.users_collection):
            holder.objects.unlink(live)
        col.objects.link(live)


def _city_instances(parent):
    if not CITY.exists():
        return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(CITY))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    col = bpy.data.collections.new("CityBlock")
    _move_to_collection(fresh, col)
    # The block is a few hundred metres across. From 1600 m the chase sees
    # many kilometres, so the same ready-made block is repeated out to the view.
    def spawn(prefix, x_center, scale, step_x, step_y, ix0, ix1, iy0, iy1, radius):
        made = 0
        for ix in range(ix0, ix1):
            for iy in range(iy0, iy1):
                inst = bpy.data.objects.new(f"{prefix}_{ix}_{iy}", None)
                inst.instance_type = "COLLECTION"
                inst.instance_collection = col
                inst.parent = parent
                inst.location = (x_center + ix * step_x, iy * step_y, 0.0)
                inst.scale = (scale, scale, scale)
                inst.rotation_euler[2] = ((ix * 3 + iy * 5) % 7) * 0.4
                inst["cull"] = 1
                inst["cull_radius"] = radius
                _link(inst)
                made += 1
        return made

    # Opening city and the identical copy one route-length ahead, so the
    # flight arrives back on the same streets.
    count = 0
    for center in (0.0, 12000.0):
        count += spawn("Near", center, 3.4, 520.0, 480.0, -4, 5, -5, 6, 700.0)
    print("city blocks", count)


def _ocean_object():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=4, y_subdivisions=4, size=2.0)
    obj = bpy.context.active_object
    obj.name = "OceanSurface"
    waves = obj.modifiers.new("Waves", "OCEAN")
    waves.geometry_mode = "GENERATE"
    waves.resolution = 12
    waves.spatial_size = 48
    waves.wave_scale = 1.8
    waves.choppiness = 1.05
    waves.wave_alignment = 0.2
    waves.wind_velocity = 16.0
    waves.repeat_x = 3
    waves.repeat_y = 3
    obj.scale = (14.0, 14.0, 2.2)
    obj.location.z = 4.0
    obj.data.materials.append(_ocean_mat())
    obj["ground"] = 1
    return obj


def _mesh_clouds(track):
    """Soft banks the camera flies through at the leg changes. Surface only."""
    mat = bpy.data.materials.new("RouteCloud")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.95, 0.96, 0.98, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.55
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 2.0
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    thin = nt.nodes.new("ShaderNodeMath")
    thin.operation = "MULTIPLY"
    thin.inputs[1].default_value = 0.22
    nt.links.new(noise.outputs["Fac"], thin.inputs[0])
    nt.links.new(thin.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    try:
        mat.blend_method = "BLEND"
    except (AttributeError, TypeError):
        pass
    for x, y, z, sx, sy, sz in (
        (1500.0, 80.0, 540.0, 260.0, 180.0, 40.0),
        (3400.0, -60.0, 500.0, 240.0, 160.0, 36.0),
        (5600.0, 40.0, 600.0, 280.0, 180.0, 32.0),
        (7800.0, -40.0, 520.0, 250.0, 170.0, 38.0),
        (10200.0, 0.0, 560.0, 270.0, 190.0, 40.0),
    ):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1.0)
        obj = bpy.context.active_object
        obj.name = "RouteCloud"
        obj.parent = track
        obj.location = (x, y, z)
        obj.scale = (sx, sy, sz)
        obj.data.materials.append(mat)
        obj.visible_shadow = False


def _horizon_sheet(track):
    """One ground under the whole route so a side view never looks off the edge."""
    mesh = bpy.data.meshes.new("Horizon")
    x0, x1, y = -6000.0, 18000.0, 14000.0
    z = -6.0
    mesh.from_pydata(
        [(x0, -y, z), (x1, -y, z), (x1, y, z), (x0, y, z)],
        [],
        [(0, 1, 2, 3)],
    )
    mat = bpy.data.materials.new("HorizonM")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = 0.0
    span.inputs["From Max"].default_value = 12000.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.45, 0.42, 0.38, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.45, 0.42, 0.38, 1.0)
    stops = (
        (0.16, (0.22, 0.38, 0.16, 1.0)),
        (0.36, (0.72, 0.75, 0.78, 1.0)),
        (0.55, (0.12, 0.32, 0.48, 1.0)),
        (0.74, (0.72, 0.55, 0.32, 1.0)),
        (0.90, (0.45, 0.42, 0.38, 1.0)),
    )
    for pos, color in stops:
        el = ramp.color_ramp.elements.new(pos)
        el.color = color
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.4
    noise.inputs["Detail"].default_value = 2.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.25
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["X"], span.inputs["Value"])
    nt.links.new(span.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(noise.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("Horizon", mesh)
    obj.parent = track
    _link(obj)


def _biome_tiles():
    photos = {
        "city": (TEX / "aerial_ground_rock_diff_1k.jpg", (0.55, 0.50, 0.45)),
        "forest": (TEX / "forest_ground_04_diff_1k.jpg", (0.25, 0.45, 0.18)),
        "desert": (TEX / "aerial_sand_diff_1k.jpg", (0.82, 0.55, 0.32)),
        "cloudsea": (TEX / "aerial_sand_diff_1k.jpg", (0.75, 0.78, 0.82)),
    }
    copies = {}
    for name in ("city", "forest", "mountains", "ocean", "desert", "cloudsea"):
        a = bpy.data.objects.new(name + "A", None)
        b = bpy.data.objects.new(name + "B", None)
        b.hide_render = True
        _link(a)
        _link(b)
        if name == "ocean":
            ground = _ocean_object()
        elif name == "mountains":
            ground = bpy.data.objects.new("MountainAnchor", None)
        else:
            image, tint = photos[name]
            span = {"city": 1500.0, "forest": 1200.0, "desert": 1100.0, "cloudsea": 400.0}[name]
            ground = _big_plane(name + "Ground", span)
            if name == "forest":
                mat, _mapping = _terrain(name + "M", image, tint=(0.2, 0.42, 0.12), warmth=0.42, scale=0.01, shade=0.12)
            elif name == "desert":
                mat, _mapping = _terrain(
                    name + "M", image, tint=tint, warmth=0.15, scale=0.0012, shade=0.0, dunes=True
                )
            else:
                mat, _mapping = _terrain(name + "M", image, tint=tint, warmth=0.08, scale=0.0035, shade=0.08)
            ground.data.materials.append(mat)
        _link(ground, a)
        copies[name] = (a, b)
    # One track. Sections sit on it in flight order and scroll together.
    # Nothing is swapped on. The closing city is a copy of the opening city.
    track = bpy.data.objects.new("WorldTrack", None)
    _link(track)
    centers = {
        "city": 0.0,
        "forest": 2200.0,
        "mountains": 4400.0,
        "ocean": 6600.0,
        "desert": 8800.0,
        "cloudsea": 10400.0,
    }
    for name, (a, _b) in copies.items():
        a.parent = track
        a.location.x = centers[name]
    city_ground = None
    for child in copies["city"][0].children:
        if child.type == "MESH":
            city_ground = child
            break
    if city_ground is not None:
        loop_ground = city_ground.copy()
        loop_ground.data = city_ground.data
        loop_ground.parent = copies["city"][0]
        loop_ground.location.x = 12000.0
        _link(loop_ground)
    snow_mat = bpy.data.materials.new("RangeM")
    snow_mat.use_nodes = True
    snow_bsdf = next(n for n in snow_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    snow_bsdf.inputs["Base Color"].default_value = (0.78, 0.81, 0.84, 1.0)
    snow_bsdf.inputs["Roughness"].default_value = 0.95
    snow = _big_plane("RangeGround", 1400.0)
    snow.data.materials.append(snow_mat)
    _link(snow, copies["mountains"][0])
    _alps_range(copies["mountains"][0])
    _city_instances(copies["city"][0])
    _forest_trees(copies["forest"][0])
    _horizon_sheet(track)
    _mesh_clouds(track)
    copies["cloudsea"][0].hide_render = True
    for child in copies["cloudsea"][0].children:
        child.hide_render = True
    cloud_root = bpy.data.objects.new("CloudField", None)
    cloud_root.parent = track
    cloud_root.hide_render = True
    _link(cloud_root)
    copies["_track"] = (track, track)
    shaft = _godrays()
    shaft.parent = cloud_root
    copies["_godrays"] = (shaft, shaft)
    copies["_clouds"] = (cloud_root, cloud_root)
    return copies


def _title_card(cam):
    """Opening and closing line. Parented to the camera so it stays in the upper third."""
    font_path = WHATIF / "scale_journey/assets/fonts/Anton-Regular.ttf"
    font = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None
    holder = bpy.data.objects.new("Title", None)
    holder.parent = cam
    # Camera looks down -Z, +Y is up. Sit above center, in front of the lens.
    holder.location = (0.0, 1.05, -3.1)
    holder.rotation_euler = (0.0, 0.0, 0.0)
    _link(holder)
    curve = bpy.data.curves.new("TitleText", "FONT")
    curve.body = "WHERE'S THE\nSAFEST SEAT?"
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 0.24
    curve.extrude = 0.004
    if font:
        curve.font = font
    glyphs = bpy.data.objects.new("TitleGlyph", curve)
    glyphs.parent = holder
    glyphs.data.materials.append(_emission("TitleM", (1.0, 0.96, 0.9), 6.0))
    _link(glyphs)
    return holder


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 28
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 4
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.volume_bounces = 2
    scene.cycles.volume_max_steps = 28
    scene.cycles.volume_step_rate = 1.6
    scene.cycles.light_sampling_threshold = 0.01
    scene.render.use_persistent_data = True
    scene.cycles.use_light_tree = False
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.35
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 3
    scene.view_settings.exposure = -0.15
    scene.render.use_motion_blur = False
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - High Contrast"
    except TypeError:
        pass
    env, sky_map, sky_bg = _world()
    _mist(scene)
    root = _link(bpy.data.objects.new("AircraftRoot", None))
    plane, skin_nodes, body, opened, glass_facs, lid = _load_plane(root)
    cabin, seats, shell = _load_cabin(root)
    biomes = _biome_tiles()
    labels = _labels(root)
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 4.2
    sun.angle = math.radians(1.2)
    sun.color = (1.0, 0.94, 0.84)
    sun_obj = bpy.data.objects.new("Sun", sun)
    # Low warm key from the front-right, so the white paint holds a shadow.
    sun_obj.rotation_euler = (math.radians(62), math.radians(-12), math.radians(-35))
    _link(sun_obj)
    rim = bpy.data.lights.new("Rim", "SUN")
    rim.energy = 9.0
    rim.angle = math.radians(3.5)
    rim.color = (1.0, 0.72, 0.42)
    rim_obj = bpy.data.objects.new("Rim", rim)
    rim_obj.rotation_euler = (math.radians(96), math.radians(18), math.radians(150))
    _link(rim_obj)
    cabin_light = bpy.data.lights.new("CabinFill", "AREA")
    cabin_light.energy = 0.0
    cabin_light.size = 8.0
    cabin_light.color = (1.0, 0.92, 0.82)
    cabin_obj = bpy.data.objects.new("CabinFill", cabin_light)
    cabin_obj.parent = root
    cabin_obj.location = (0.0, 0.0, 8.4)
    cabin_obj.rotation_euler = (math.pi, 0.0, 0.0)
    _link(cabin_obj)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = 24.0
    cam_data.clip_start = 0.25
    cam_data.clip_end = 50000.0
    cam = _link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
    title = _title_card(cam)
    print("scene ready", "plane", plane.name, "seats", len(seats))
    return {
        "root": root,
        "cabin": cabin,
        "seats": seats,
        "shell": shell,
        "plane_meshes": [obj for obj in plane.children_recursive if obj.type == "MESH" and "gear" not in obj.name.lower()],
        "skin_nodes": skin_nodes,
        "glass_facs": glass_facs,
        "body": body,
        "opened": opened,
        "lid": lid,
        "title": title,
        "track": biomes.get("_track", (None, None))[0],
        "labels": labels,
        "biomes": biomes,
        "cam": cam,
        "scene": scene,
        "env": env,
        "sky_map": sky_map,
        "sky_bg": sky_bg,
        "cabin_light": cabin_light,
        "sun": sun_obj,
    }


def _aim(cam, eye, target, roll_deg):
    """Point the lens at target with the horizon level.

    Blender's camera looks down local -Z and keeps local +Y up. A shortest-arc
    quaternion from (0, 0, -1) leaves that up-axis lying on its side whenever
    the view is horizontal, which rolled the Short onto its side. Build the
    basis so camera-up stays world-up, then apply only the small authored roll.
    """
    direction = mathutils.Vector(target) - mathutils.Vector(eye)
    if direction.length < 1e-5:
        return
    forward = direction.normalized()
    world_up = mathutils.Vector((0.0, 0.0, 1.0))
    # Chase shots level against the horizon. Only a steep top-down blends
    # toward nose-up, and the blend is continuous so the horizon never snaps.
    nose = mathutils.Vector((1.0, 0.0, 0.0))
    steep = (abs(forward.dot(world_up)) - 0.55) / 0.30
    steep = max(0.0, min(1.0, steep))
    steep = steep * steep * (3.0 - 2.0 * steep)
    up_hint = world_up * (1.0 - steep) + nose * steep
    if up_hint.length < 1e-4:
        up_hint = world_up
    up = up_hint - forward * forward.dot(up_hint)
    if up.length < 1e-4:
        up = nose - forward * forward.dot(nose)
    up.normalize()
    right = forward.cross(up).normalized()
    up = right.cross(forward).normalized()
    z_axis = -forward
    rot = mathutils.Matrix((
        (right.x, up.x, z_axis.x),
        (right.y, up.y, z_axis.y),
        (right.z, up.z, z_axis.z),
    )).to_quaternion()
    twist = mathutils.Quaternion(forward, math.radians(roll_deg))
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = twist @ rot


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


def _sky_image(sky_name):
    """Prefer an image already packed in the blend, then the extracted HDRI."""
    for image in bpy.data.images:
        if image.name == sky_name or Path(image.filepath).name == sky_name:
            return image
    return bpy.data.images.load(str(HDRI_DIR / sky_name), check_existing=True)


def apply_pose(state, pose):
    root = state["root"]
    root.location = (0.0, 0.0, pose["altitude"])
    root.rotation_euler = (
        math.radians(pose["roll"]),
        math.radians(pose["pitch"]),
        math.radians(pose["yaw"]),
    )
    track = state.get("track")
    if track is not None:
        # The whole route slides past the jet. No biome is hidden or swapped.
        track.location.x = -float(pose["distance"])
    if state.get("sky_bg") is not None:
        state["sky_bg"].inputs["Strength"].default_value = 1.05
    for name, (a, b) in state["biomes"].items():
        if name in ("_godrays", "_clouds", "_track"):
            a.hide_render = True
            continue
        if track is not None:
            b.hide_render = True
            continue
    xray = max(0.0, min(1.0, float(pose.get("xray", 0.0))))
    alpha = 1.0 - 0.96 * xray
    glassy = (0.62, 0.78, 0.88)
    for node in state.get("skin_nodes") or []:
        if "Alpha" in node.inputs:
            node.inputs["Alpha"].default_value = alpha
        base = node.get("solid_color")
        if base is None and "Base Color" in node.inputs:
            base = tuple(node.inputs["Base Color"].default_value[:3])
            node["solid_color"] = base
        if base is not None and "Base Color" in node.inputs:
            node.inputs["Base Color"].default_value = (
                *(base[i] * (1.0 - xray) + glassy[i] * xray for i in range(3)),
                1.0,
            )
    for fac in state.get("glass_facs") or []:
        fac.default_value = xray
    interior = bool(pose.get("interior"))
    lid_amt = max(0.0, min(1.0, float(pose.get("lid", 0.0))))
    cutaway = lid_amt > 0.04 and not interior
    body = state.get("body")
    opened = state.get("opened")
    lid_obj = state.get("lid")
    for obj in state.get("plane_meshes") or []:
        if "gear" in obj.name.lower():
            obj.hide_render = True
            continue
        if obj is body or obj is opened:
            continue
        if obj.name.startswith("Fan"):
            # The blade disc reads as a black starburst once the nacelle is out of frame.
            obj.hide_render = interior or cutaway or xray > 0.08
            continue
        obj.hide_render = interior
    if body is not None:
        body.hide_render = interior or cutaway
    if opened is not None:
        opened.hide_render = interior or not cutaway
    if lid_obj is not None:
        lid_obj.hide_render = interior or not cutaway
        # Local +Z is up on the fuselage. The crown lifts instead of vanishing.
        # Slide the crown off to the side. Lifting it straight up puts the
        # roof between a top-down lens and the seats, so the cabin stays hidden.
        lid_obj.location.x = lid_amt * 16.0
        lid_obj.location.z = lid_amt * 2.5
    for obj in state["shell"]:
        obj.hide_render = not interior
    light = state.get("cabin_light")
    if light is not None:
        light.energy = 1800.0 if interior else 0.0
    show_seats = interior or lid_amt > 0.15 or xray > 0.05
    for seat in state["seats"]:
        seat.hide_render = not show_seats
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
    # The billboard reads the camera matrix. Without this update it still
    # holds the previous frame, and the cards come out on their side.
    bpy.context.view_layer.update()
    cam.data.lens = pose["lens"]
    focus = (mathutils.Vector(pose["look"]) - mathutils.Vector(pose["eye"])).length
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = max(4.0, focus)
    cam.data.dof.aperture_fstop = float(pose.get("fstop", 8.0))
    show = {
        "l38": pose.get("show_38", 0) > 0.4,
        "l39": pose.get("show_39", 0) > 0.4,
        "l32": pose.get("show_32", 0) > 0.4,
        "l44": pose.get("show_44", 0) > 0.4,
        "l28": pose.get("show_28", 0) > 0.4,
        "l17": pose.get("show_17", 0) > 0.4,
    }
    title = state.get("title")
    if title is not None:
        show_title = pose.get("show_title", 0) > 0.35
        title.hide_render = not show_title
        for child in title.children:
            child.hide_render = not show_title
    parent_q = root.matrix_world.to_quaternion()
    for key, obj in (state.get("labels") or {}).items():
        visible = show.get(key, False)
        obj.hide_render = not visible
        for child in obj.children:
            child.hide_render = not visible
        if not visible:
            continue
        direction = cam.location - (root.matrix_world @ mathutils.Vector(obj.location))
        if direction.length < 0.1:
            continue
        # Face the camera and match its up, so the percent stays upright in frame.
        cam_q = cam.matrix_world.to_quaternion()
        cam_up = cam_q @ mathutils.Vector((0.0, 1.0, 0.0))
        cam_right = cam_q @ mathutils.Vector((1.0, 0.0, 0.0))
        z_axis = direction.normalized()
        y_axis = cam_up - z_axis * cam_up.dot(z_axis)
        if y_axis.length < 1e-4:
            y_axis = cam_right.cross(z_axis)
        y_axis.normalize()
        x_axis = y_axis.cross(z_axis).normalized()
        if x_axis.dot(cam_right) < 0.0:
            x_axis = -x_axis
            y_axis = -y_axis
        rot = mathutils.Matrix((
            (x_axis.x, y_axis.x, z_axis.x),
            (x_axis.y, y_axis.y, z_axis.y),
            (x_axis.z, y_axis.z, z_axis.z),
        )).to_quaternion()
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = parent_q.inverted() @ rot
    if state.get("cull") or state.get("lod"):
        _view_opt(state)


def _view_opt(state):
    """Drop off-screen scenery from the camera, and optionally swap far trees."""
    cam = state["cam"]
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    scene = state["scene"]
    lens = max(1.0, cam.data.lens)
    sensor_h = cam.data.sensor_height or 24.0
    aspect = scene.render.resolution_x / max(1, scene.render.resolution_y)
    tan_y = (sensor_h * 0.5 / lens) * 1.5
    tan_x = tan_y * aspect * 1.5
    cam_loc = cam.matrix_world.translation
    for obj in bpy.data.objects:
        if obj.get("lod_mesh") and state.get("lod") and obj.type == "MESH":
            dist = (obj.matrix_world.translation - cam_loc).length
            name = obj["lod_mesh"] if dist > 750.0 else obj["near_mesh"]
            if obj.data.name != name and name in bpy.data.meshes:
                obj.data = bpy.data.meshes[name]
        if not state.get("cull") or not obj.get("cull"):
            continue
        radius = float(obj.get("cull_radius", 40.0))
        loc = obj.matrix_world.translation
        dist = (loc - cam_loc).length
        obj.visible_shadow = True
        if dist < 300.0:
            obj.visible_camera = True
            continue
        p = inv @ loc
        depth = -p.z
        if depth < -radius:
            obj.visible_camera = False
            continue
        limit_x = tan_x * max(depth, 1.0) + radius
        limit_y = tan_y * max(depth, 1.0) + radius
        obj.visible_camera = abs(p.x) <= limit_x and abs(p.y) <= limit_y


def _configure_cycles(scene, job):
    scene.cycles.samples = int(job.get("samples", scene.cycles.samples))
    scene.cycles.use_denoising = bool(job.get("denoise", True))
    if job.get("denoiser"):
        scene.cycles.denoiser = job["denoiser"]
    scene.cycles.use_adaptive_sampling = bool(job.get("adaptive", False))
    if job.get("adaptive"):
        scene.cycles.adaptive_threshold = float(job.get("threshold", 0.01))
        scene.cycles.adaptive_min_samples = int(job.get("min_samples", 1))
    if "bounces" in job:
        bounces = int(job["bounces"])
        scene.cycles.max_bounces = bounces
        scene.cycles.diffuse_bounces = min(scene.cycles.diffuse_bounces, bounces)
        scene.cycles.glossy_bounces = min(scene.cycles.glossy_bounces, bounces)
        scene.cycles.transmission_bounces = min(scene.cycles.transmission_bounces, bounces)
        scene.cycles.volume_bounces = int(job.get("volume_bounces", 2))
        scene.cycles.transparent_max_bounces = int(job.get("transparent_bounces", 6))
    if "persistent" in job:
        scene.render.use_persistent_data = bool(job["persistent"])
    if "volume_step_rate" in job:
        scene.cycles.volume_step_rate = float(job["volume_step_rate"])
        scene.cycles.volume_max_steps = int(job.get("volume_steps", scene.cycles.volume_max_steps))
    print(
        "cycles",
        scene.cycles.samples,
        "adaptive", scene.cycles.use_adaptive_sampling,
        "denoise", scene.cycles.denoiser if scene.cycles.use_denoising else "off",
        "bounces", scene.cycles.max_bounces,
        "vol", scene.cycles.volume_bounces,
        "trans", scene.cycles.transparent_max_bounces,
        "persist", scene.render.use_persistent_data,
        flush=True,
    )


def _use_eevee(scene, samples):
    for name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = name
            break
        except TypeError:
            continue
    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        if hasattr(eevee, "taa_render_samples"):
            eevee.taa_render_samples = samples
        if hasattr(eevee, "use_raytracing"):
            eevee.use_raytracing = False
        if hasattr(eevee, "volumetric_samples"):
            eevee.volumetric_samples = 16
        if hasattr(eevee, "volumetric_tile_size"):
            try:
                eevee.volumetric_tile_size = "8"
            except TypeError:
                pass
    scene.render.use_motion_blur = False
    print("engine", scene.render.engine, "samples", samples, flush=True)


def _use_workbench(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    try:
        scene.display.render_aa = "FXAA"
    except TypeError:
        pass
    scene.render.use_motion_blur = False
    print("engine", scene.render.engine, flush=True)


def render_job(job):
    state = build_scene()
    state["cull"] = bool(job.get("cull"))
    state["lod"] = bool(job.get("lod"))
    scene = state["scene"]
    state["fast"] = bool(job.get("fast"))
    engine = str(job.get("engine", "")).upper()
    if engine == "EEVEE":
        _use_eevee(scene, int(job.get("samples", 8)))
    elif engine == "WORKBENCH":
        _use_workbench(scene)
    else:
        _configure_cycles(scene, job)
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
        tick = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        print(f"BENCH frame={frame} seconds={time.perf_counter() - tick:.3f}", flush=True)
        rendered[frame] = png
        done += 1
        if done == 1 or done % 20 == 0 or done == len(unique):
            print(f"frame {frame} {done}/{len(unique)} {time.time() - started:.1f}s", flush=True)


def render_stills(job):
    state = build_scene()
    scene = state["scene"]
    scene.cycles.samples = int(job.get("samples", 24))
    scene.render.use_motion_blur = False
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.render.resolution_percentage = int(job.get("scale", 100))
    only = set(job.get("only") or [])
    for shot in job["stills"]:
        if only and shot["name"] not in only:
            continue
        pose = pose_at(float(shot["t"]))
        pose["altitude"] = float(shot["altitude"])
        pose["eye"] = shot["eye"]
        pose["look"] = shot["look"]
        pose["lens"] = float(shot["lens"])
        pose["cam_roll"] = float(shot.get("roll", 0))
        pose["roll"] = float(shot.get("bank", 0))
        pose["pitch"] = 0.0
        pose["yaw"] = 0.0
        pose["biome"] = shot["biome"]
        pose["xray"] = float(shot.get("xray", 0))
        pose["cutaway"] = bool(shot.get("cutaway", False))
        pose["interior"] = bool(shot.get("interior", False))
        pose["inside"] = bool(shot.get("interior", False))
        if shot.get("clouds"):
            pose["clouds"] = shot["clouds"]
        if "sky" in shot:
            pose["sky"] = float(shot["sky"])
        if "fstop" in shot:
            pose["fstop"] = float(shot["fstop"])
        wanted = set(shot.get("show") or [])
        for key in ("show_38", "show_39", "show_32", "show_44", "show_28"):
            pose[key] = 1.0 if key.replace("show_", "l") in wanted else 0.0
        apply_pose(state, pose)
        scene.render.filepath = shot["path"]
        bpy.ops.render.render(write_still=True)
        print("still", shot["path"], flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    job = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    if job.get("stills"):
        render_stills(job)
    else:
        render_job(job)


if __name__ == "__main__":
    main()
