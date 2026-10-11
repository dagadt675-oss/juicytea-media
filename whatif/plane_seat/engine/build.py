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
# Radians. 0 puts the Belfast sun on the chase camera's horizon.
SKY_TURN = {
    "city": 0.15,
    "forest": 0.4,
    "mountains": 0.35,
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
            if base in needed:
                (HDRI_DIR / base).write_bytes(zf.read(entry))


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
    bg.inputs["Strength"].default_value = 1.25
    env.image = bpy.data.images.load(str(HDRI_DIR / SKY_FILES["city"]), check_existing=True)
    mapping.inputs["Rotation"].default_value[2] = SKY_TURN["city"]
    return env, mapping


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


def _terrain(name, image, roughness=0.92, tint=(1, 1, 1), warmth=0.22):
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
    mapping.inputs["Scale"].default_value = (0.00085, 0.00085, 0.00085)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    warm = _mix_rgb(nt, None, tex.outputs["Color"], (*tint, 1))
    warm.inputs["Fac"].default_value = warmth
    # Keep the photo dark enough that a sunset sky and a city skyline read on top.
    dark = _mix_rgb(nt, None, warm.outputs["Color"], (0.02, 0.015, 0.012, 1))
    dark.inputs["Fac"].default_value = 0.62
    cam = nt.nodes.new("ShaderNodeCameraData")
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = 3500.0
    span.inputs["From Max"].default_value = 16000.0
    span.inputs["To Min"].default_value = 0.0
    span.inputs["To Max"].default_value = 0.55
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
    bsdf.inputs["Emission Strength"].default_value = 6.0
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


def _shade_airliner(body):
    by_name = {mat.name: mat for mat in body.data.materials if mat}
    main = by_name.get("Material.001")
    if main and main.node_tree:
        bsdf = next(n for n in main.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (0.93, 0.94, 0.96, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.12
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.55
        if "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.08
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.5
    paint = by_name.get("Matal solid paint white")
    if paint and paint.node_tree:
        bsdf = next(n for n in paint.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Roughness"].default_value = 0.18
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.4
    grey, _ = _principled("BellyGrey", (0.42, 0.44, 0.47), 0.45, 0.04)
    body.data.materials.append(grey)
    grey_i = len(body.data.materials) - 1
    # Tube skin gets its own material so the x-ray can fade it without melting the wings.
    tube_src = main if main is not None else paint
    tube = tube_src.copy() if tube_src is not None else grey.copy()
    tube.name = "FuselageSkin"
    body.data.materials.append(tube)
    tube_i = len(body.data.materials) - 1
    for poly in body.data.polygons:
        c = poly.center
        in_tube = abs(c.x) < 3.7 and -30.0 < c.y < 16.0 and 3.2 < c.z < 11.5
        if not in_tube or poly.material_index not in (0, 3, tube_i):
            continue
        if c.z < 6.15:
            poly.material_index = grey_i
        else:
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
            if "glass" in mat.name.lower() or "frost" in mat.name.lower():
                fac = _fade_glass(mat)
                if fac is not None:
                    glass_facs.append(fac)
        _add_fans(body)
        import bmesh
        opened = body.copy()
        opened.data = body.data.copy()
        opened.parent = empty
        _link(opened)
        bm = bmesh.new()
        bm.from_mesh(opened.data)
        kill = []
        for face in bm.faces:
            c = face.calc_center_median()
            # Open the crown of the tube only. The fin is farther aft (local +Y).
            if abs(c.x) < 3.15 and c.z > 6.85 and -28.0 < c.y < 16.0:
                kill.append(face)
        if kill:
            bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(opened.data)
        bm.free()
        opened.name = "BodyCutaway"
        opened.hide_render = True
        print("cutaway faces", len(kill))
    else:
        opened = None
    return empty, skin_nodes, body, opened, glass_facs


def _labels(root):
    """Big 3D callouts. Exterior zones sit beside the tube; 44/28 sit in the aisle."""
    font_path = WHATIF / "scale_journey/assets/fonts/Anton-Regular.ttf"
    font = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None
    # (text, color, location, em size)
    specs = {
        "l38": ("38%", AMBER, (8.5, -18.0, 16.0), 5.4),
        "l39": ("39%", AMBER, (0.2, -18.0, 16.0), 5.4),
        "l32": ("32%", GREEN, (-8.2, -18.0, 16.0), 5.4),
        "l44": ("44%", RED, (0.2, -16.0, 15.0), 7.0),
        "l28": ("28%", BRIGHT, (-12.0, -16.0, 15.0), 6.4),
    }
    out = {}
    for key, (text, color, loc, size) in specs.items():
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


def _peaks_object():
    verts = []
    faces = []
    nx = ny = 140
    span = 16000.0
    for j in range(ny):
        for i in range(nx):
            x = -span * 0.5 + span * i / (nx - 1)
            y = -span * 0.5 + span * j / (ny - 1)
            # Valley under the aircraft (origin), ridges off to the sides.
            # A valley under the jet, with summits a kilometre or two out.
            dist = math.hypot(x * 0.65, y)
            valley = min(1.0, max(0.0, (dist - 400.0) / 1100.0))
            ridge = max(0.0, math.sin(x * 0.00115 + 0.9) * math.sin(y * 0.00092 - 0.35))
            ridge += 0.65 * max(0.0, math.sin(x * 0.00062 - 1.4) * math.cos(y * 0.0007 + 0.8))
            h = 180.0 * abs(math.sin(x * 0.0016) * math.cos(y * 0.0013))
            h += 1050.0 * ridge * ridge
            h *= 0.15 + 0.85 * valley
            verts.append((x, y, h))
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + 1 + nx, a + nx))
    mesh = bpy.data.meshes.new("Peaks")
    mesh.from_pydata(verts, [], faces)
    mesh.shade_smooth()
    mat, bsdf = _principled("Snow", (0.90, 0.92, 0.95), 0.55)
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.04
    nt = mat.node_tree
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geom.outputs["Position"], sep.inputs["Vector"])
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = 180.0
    span.inputs["From Max"].default_value = 620.0
    span.clamp = True
    nt.links.new(sep.outputs["Z"], span.inputs["Value"])
    snow = _mix_rgb(nt, span.outputs["Result"], (0.34, 0.30, 0.28, 1), (0.92, 0.94, 0.96, 1))
    nt.links.new(snow.outputs["Color"], bsdf.inputs["Base Color"])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("Peaks", mesh)
    obj["ground"] = 1
    return obj


def _ocean_mat():
    mat = bpy.data.materials.new("Ocean")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.04
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.9
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.15
    cam = nt.nodes.new("ShaderNodeCameraData")
    span = nt.nodes.new("ShaderNodeMapRange")
    span.inputs["From Min"].default_value = 500.0
    span.inputs["From Max"].default_value = 10000.0
    span.clamp = True
    nt.links.new(cam.outputs["View Distance"], span.inputs["Value"])
    haze = _mix_rgb(nt, span.outputs["Result"], (0.02, 0.08, 0.12, 1), (*HAZE, 1))
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
    # The block is about 150 m. Scale 3.4 makes towers ~120 m, a real skyline.
    # Blocks run ahead of the nose (+X) and to both sides so a chase camera sees them.
    for ix in range(-1, 5):
        for iy in range(-3, 4):
            inst = bpy.data.objects.new(f"City_{ix}_{iy}", None)
            inst.instance_type = "COLLECTION"
            inst.instance_collection = col
            inst.parent = parent
            inst.location = (ix * 560.0 - 200.0, iy * 460.0, 0.0)
            inst.scale = (3.8, 3.8, 3.8)
            inst.rotation_euler[2] = (ix * 0.35 + iy * 0.55)
            _link(inst)


def _forest_trees(parent):
    if not TREES.exists():
        return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(TREES))
    fresh = [obj for obj in bpy.data.objects if obj not in before]
    picked = []
    for obj in fresh:
        if obj.type != "MESH":
            continue
        pts = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        size = (
            max(p.x for p in pts) - min(p.x for p in pts),
            max(p.y for p in pts) - min(p.y for p in pts),
            max(p.z for p in pts) - min(p.z for p in pts),
        )
        if 80.0 < size[2] < 210.0 and size[0] < 160.0 and size[2] > size[0]:
            picked.append((size[2], obj.data))
    meshes = []
    for _h, mesh in picked[:6]:
        copy = mesh.copy()
        copy.use_fake_user = True
        meshes.append(copy)
        if len(meshes) == 3:
            break
    for obj in fresh:
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except ReferenceError:
            continue
    if not meshes:
        print("no tree meshes kept")
        return
    rng = math.pi
    for i in range(48):
        mesh = meshes[i % len(meshes)]
        obj = bpy.data.objects.new(f"Tree_{i}", mesh)
        obj.parent = parent
        # ~40 m tall from a ~170 unit source mesh.
        scale = 0.20 + (i % 5) * 0.025
        obj.scale = (scale, scale, scale)
        obj.location = (
            ((i * 97) % 2400) - 1200,
            ((i * 173) % 2400) - 1200,
            0.0,
        )
        obj.rotation_euler[2] = rng * (i % 7)
        _link(obj)
    print("trees", len(meshes), "instances 48")


def _cloud_material():
    mat, bsdf = _principled("Cloud", (0.96, 0.94, 0.90), 0.88)
    bsdf.inputs["Base Color"].default_value = (0.97, 0.95, 0.91, 1)
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.0
    return mat


def _puff(mat, parent, loc, scale, kind):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1.0)
    obj = bpy.context.active_object
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.materials.append(mat)
    obj.parent = parent
    obj.location = loc
    obj.scale = scale
    obj["kind"] = kind
    obj.visible_shadow = False
    return obj


def _biome_tiles():
    photos = {
        "city": (TEX / "aerial_ground_rock_diff_1k.jpg", (0.55, 0.50, 0.45)),
        "forest": (TEX / "forest_ground_04_diff_1k.jpg", (0.25, 0.45, 0.18)),
        "desert": (TEX / "red_sand_diff_1k.jpg", (0.72, 0.42, 0.18)),
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
            ground = _big_plane(name + "Ground", 22000.0)
            ground.data.materials.append(_ocean_mat())
        elif name == "mountains":
            ground = _peaks_object()
        else:
            image, tint = photos[name]
            ground = _big_plane(name + "Ground", 22000.0)
            mat, _mapping = _terrain(name + "M", image, tint=tint)
            ground.data.materials.append(mat)
        _link(ground, a)
        copies[name] = (a, b)
    _city_instances(copies["city"][0])
    _forest_trees(copies["forest"][0])
    puff = _cloud_material()
    cloud_root = bpy.data.objects.new("CloudField", None)
    _link(cloud_root)
    # Deck sits beside and below the jet so a chase camera stays in clear air.
    deck = [
        ((-10, -60, -18), (30, 18, 11)),
        ((40, 48, -22), (34, 20, 12)),
        ((-36, 42, -16), (22, 16, 9)),
        ((70, -24, -40), (40, 24, 12)),
        ((-20, -24, -48), (36, 22, 12)),
        ((24, 18, -36), (26, 18, 10)),
    ]
    for loc, scale in deck:
        _puff(puff, cloud_root, loc, scale, "deck")
    # A bank the jet is flying out of. Kept off the chase camera, which sits near x=-90.
    for i in range(12):
        side = -1.0 if i % 2 == 0 else 1.0
        _puff(
            puff,
            cloud_root,
            (-28 + (i % 6) * 14, side * (20 + (i % 3) * 8), 4 + (i % 3) * 7),
            (24, 16, 8),
            "punch",
        )
    copies["_clouds"] = (cloud_root, cloud_root)
    return copies


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
    scene.cycles.use_light_tree = False
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 3
    scene.view_settings.exposure = -0.15
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    env, sky_map = _world()
    root = _link(bpy.data.objects.new("AircraftRoot", None))
    plane, skin_nodes, body, opened, glass_facs = _load_plane(root)
    cabin, seats, shell = _load_cabin(root)
    biomes = _biome_tiles()
    labels = _labels(root)
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 2.2
    sun.angle = math.radians(1.4)
    sun.color = (1.0, 0.78, 0.55)
    sun_obj = bpy.data.objects.new("Sun", sun)
    sun_obj.rotation_euler = (math.radians(68), math.radians(6), math.radians(32))
    _link(sun_obj)
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
    cam_data.clip_start = 0.05
    cam_data.clip_end = 50000.0
    cam = _link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
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
        "labels": labels,
        "biomes": biomes,
        "cam": cam,
        "scene": scene,
        "env": env,
        "sky_map": sky_map,
        "cabin_light": cabin_light,
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
    biome = pose["biome"]
    env = state.get("env")
    if env is not None:
        sky_name = SKY_FILES.get(biome, SKY_FILES["city"])
        image = bpy.data.images.load(str(HDRI_DIR / sky_name), check_existing=True)
        if env.image != image:
            env.image = image
        state["sky_map"].inputs["Rotation"].default_value[2] = SKY_TURN.get(biome, 0.0)
    cloud_mode = pose.get("clouds") or ("punch" if pose.get("cloud", 0.0) > 0.72 else "deck")
    if pose.get("inside") or pose.get("interior"):
        cloud_mode = "off"
    for name, (a, b) in state["biomes"].items():
        if name == "_clouds":
            # Stay with the jet (the jet itself does not translate). Deck vs punch.
            a.location = (0.0, 0.0, pose["altitude"])
            for child in a.children:
                kind = child.get("kind", "deck")
                child.hide_render = cloud_mode != "all" and kind != cloud_mode
            continue
        show = name == biome
        a.hide_render = not show
        b.hide_render = True
        for child in a.children_recursive:
            child.hide_render = not show
        a.location.x = -phase
        b.location.x = -phase + TILE
    xray = max(0.0, min(1.0, float(pose.get("xray", 0.0))))
    alpha = 1.0 - 0.9 * xray
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
    cutaway = bool(pose.get("cutaway")) and not interior
    body = state.get("body")
    opened = state.get("opened")
    for obj in state.get("plane_meshes") or []:
        if "gear" in obj.name.lower():
            obj.hide_render = True
            continue
        if obj is body or obj is opened:
            continue
        obj.hide_render = interior
    if body is not None:
        body.hide_render = interior or cutaway
    if opened is not None:
        opened.hide_render = interior or not cutaway
    for obj in state["shell"]:
        obj.hide_render = not interior
    light = state.get("cabin_light")
    if light is not None:
        light.energy = 1800.0 if interior else 0.0
    show_seats = interior or xray > 0.05
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
    cam.data.lens = pose["lens"]
    show = {
        "l38": pose.get("show_38", 0) > 0.4,
        "l39": pose.get("show_39", 0) > 0.4,
        "l32": pose.get("show_32", 0) > 0.4,
        "l44": pose.get("show_44", 0) > 0.4,
        "l28": pose.get("show_28", 0) > 0.4,
    }
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
        # Local +Z points at the camera, local +Y stays as upright as possible.
        z_axis = direction.normalized()
        up = mathutils.Vector((0.0, 0.0, 1.0))
        if abs(z_axis.dot(up)) > 0.92:
            up = mathutils.Vector((1.0, 0.0, 0.0))
        x_axis = up.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        rot = mathutils.Matrix((
            (x_axis.x, y_axis.x, z_axis.x),
            (x_axis.y, y_axis.y, z_axis.y),
            (x_axis.z, y_axis.z, z_axis.z),
        )).to_quaternion()
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = parent_q.inverted() @ rot


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


def render_stills(job):
    state = build_scene()
    scene = state["scene"]
    scene.cycles.samples = int(job.get("samples", 24))
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
