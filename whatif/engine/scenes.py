"""Scene library: river city, coast city, forest/farm, suburbs.

Pieces are selected by the episode spec. Episode 1 uses the river city.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Matrix

from engine.meshkit import (
    Kit,
    add_box,
    aim_z,
    box_object,
    cylinder_mesh,
    empty,
    ico_object,
    lin,
    link_obj,
    make_emission,
    make_object_color_surface,
    make_surface,
    make_volume,
    make_water_material,
    make_window_material,
    mesh_from_bm,
    parent_keep,
)

# Layout, meters. Camera looks north (+Y) from the south.
RIVER_Y0 = -1.15
RIVER_Y1 = 7.35
PARK_Z = 0.92
LOW_Z = 0.46
FAR_Z = 1.08
DECK_Z = 2.62
DECK_X = 6.2
TOWER_H = 15.4
TOWER_W = 4.6


def _materials():
    wall = make_object_color_surface(
        "Tower",
        {"moss": 0.9, "rust": 0.25, "mud": 0.35, "scorch": 0.55, "snow": 0.85, "wet": 0.6},
    )
    window = make_window_material()
    trim = make_surface(
        "Trim",
        lin(0.32, 0.34, 0.38),
        {"moss": 0.4, "rust": 0.7, "mud": 0.3, "scorch": 0.4, "snow": 0.8, "wet": 0.5},
    )
    bridge = make_surface(
        "BridgeRed",
        lin(0.84, 0.10, 0.08),
        {"moss": 0.15, "rust": 1.0, "mud": 0.2, "scorch": 0.35, "snow": 0.7, "wet": 0.4},
    )
    cable = make_surface(
        "Cable",
        lin(0.12, 0.12, 0.13),
        {"moss": 0.05, "rust": 0.9, "mud": 0.1, "scorch": 0.2, "snow": 0.4, "wet": 0.3},
    )
    road = make_surface(
        "Road",
        lin(0.15, 0.16, 0.18),
        {"moss": 0.55, "rust": 0.05, "mud": 0.8, "scorch": 0.45, "snow": 1.0, "wet": 0.85},
    )
    park = make_surface(
        "Park",
        lin(0.30, 0.58, 0.24),
        {"moss": 0.2, "rust": 0.0, "mud": 0.45, "scorch": 0.65, "snow": 1.0, "wet": 0.35},
    )
    dirt = make_surface(
        "Dirt",
        lin(0.34, 0.26, 0.16),
        {"moss": 0.3, "rust": 0.0, "mud": 0.4, "scorch": 0.7, "snow": 1.0, "wet": 0.4},
    )
    sand = make_surface(
        "Sand",
        lin(0.76, 0.68, 0.46),
        {"moss": 0.05, "rust": 0.0, "mud": 0.25, "scorch": 0.15, "snow": 0.8, "wet": 0.3},
    )
    water = make_water_material()
    mark = make_surface("Mark", lin(0.92, 0.92, 0.88), {"snow": 1.0, "mud": 0.6, "wet": 0.4, "scorch": 0.3})
    yellow = make_surface("Yellow", lin(0.86, 0.72, 0.18), {"snow": 1.0, "mud": 0.5, "wet": 0.3})
    leaf = make_object_color_surface(
        "Leaf",
        {"moss": 0.1, "rust": 0.0, "mud": 0.15, "scorch": 0.8, "snow": 1.0, "wet": 0.25},
    )
    trunk = make_surface(
        "Trunk",
        lin(0.34, 0.22, 0.12),
        {"moss": 0.45, "rust": 0.0, "mud": 0.2, "scorch": 0.6, "snow": 0.7, "wet": 0.3},
    )
    wood = make_object_color_surface(
        "Wood",
        {"moss": 0.55, "rust": 0.1, "mud": 0.4, "scorch": 0.7, "snow": 0.9, "wet": 0.55},
    )
    roof = make_surface(
        "Roof",
        lin(0.48, 0.20, 0.16),
        {"moss": 0.7, "rust": 0.2, "mud": 0.3, "scorch": 0.6, "snow": 1.0, "wet": 0.4},
    )
    car = make_object_color_surface(
        "Car",
        {"moss": 0.25, "rust": 0.85, "mud": 0.55, "scorch": 0.4, "snow": 0.95, "wet": 0.6},
    )
    glass = make_surface("Glass", lin(0.18, 0.26, 0.34), {"snow": 0.3, "wet": 0.2, "scorch": 0.2})
    rubber = make_surface("Rubber", lin(0.05, 0.05, 0.055), {"snow": 0.8, "mud": 0.4})
    seam = make_emission("Seam", lin(0.92, 0.28, 0.06), 0.35)
    rock = make_surface(
        "Rock",
        lin(0.55, 0.50, 0.44),
        {"moss": 0.2, "snow": 0.9, "mud": 0.2, "scorch": 0.2},
    )
    snowmat = make_surface("SnowMat", lin(0.94, 0.96, 0.98), {"snow": 0.2})
    flame = make_emission("Flame", lin(1.0, 0.42, 0.08), 8.0)
    smoke = make_surface("Smoke", lin(0.75, 0.78, 0.82), {})
    dark = make_surface("Dark", lin(0.02, 0.02, 0.025), {})
    skin = make_surface("Skin", lin(0.72, 0.55, 0.42), {})
    cloth = make_object_color_surface("Cloth", {"snow": 0.4, "wet": 0.3, "mud": 0.3})
    return {
        "wall": wall,
        "window": window,
        "trim": trim,
        "bridge": bridge,
        "cable": cable,
        "road": road,
        "park": park,
        "dirt": dirt,
        "sand": sand,
        "water": water,
        "mark": mark,
        "yellow": yellow,
        "leaf": leaf,
        "trunk": trunk,
        "wood": wood,
        "roof": roof,
        "car": car,
        "glass": glass,
        "rubber": rubber,
        "seam": seam,
        "rock": rock,
        "snow": snowmat,
        "flame": flame,
        "smoke": smoke,
        "dark": dark,
        "skin": skin,
        "cloth": cloth,
    }


def _plane(name, coll, center, size, mat, z_thickness=0.08):
    return box_object(name, coll, center, (size[0], size[1], z_thickness), mat)


def _windows(bm, center, size, floors, cols):
    cx, cy, cz = center
    sx, sy, sz = size
    z0 = cz - sz / 2
    usable = sz * 0.86
    if floors < 1 or cols < 1:
        return
    wz = min(0.7, usable / floors * 0.62)
    wx = min(0.62, (sx * 0.8) / cols)
    for face_sign, axis in ((-1, "y"), (1, "x")):
        for floor in range(floors):
            for col in range(cols):
                tz = z0 + sz * 0.08 + (floor + 0.5) * (usable / floors)
                if axis == "y":
                    xx = cx - sx * 0.38 + (col + 0.5) * (sx * 0.76 / cols)
                    yy = cy + face_sign * (sy / 2 + 0.03)
                    add_box(bm, (xx, yy, tz), (wx, 0.06, wz), 1)
                else:
                    yy = cy - sy * 0.38 + (col + 0.5) * (sy * 0.76 / max(cols - 1, 1) if False else sy * 0.76 / cols)
                    xx = cx + face_sign * (sx / 2 + 0.03)
                    add_box(bm, (xx, yy, tz), (0.06, wx, wz), 1)


def _tower_mesh(name, w, d, h):
    bm = bmesh.new()
    add_box(bm, (0, 0, h / 2), (w, d, h), 0)
    floors = max(2, int(h / 1.65))
    cols = max(2, int(w / 1.2))
    _windows(bm, (0, 0, h / 2), (w, d, h), floors, cols)
    if h > 8:
        add_box(bm, (0, 0, h - 0.18), (w * 0.72, d * 0.72, 0.36), 0)
    return mesh_from_bm(name, bm)


def _tree(kit, coll, mats, x, y, z, scale, future=False, delay=0.0, rng=None):
    rng = rng or random
    greens = [
        (0.24, 0.55, 0.20, 1),
        (0.42, 0.68, 0.16, 1),
        (0.18, 0.42, 0.16, 1),
        (0.55, 0.66, 0.18, 1),
    ]
    autumns = [
        (0.72, 0.42, 0.12, 1),
        (0.80, 0.62, 0.16, 1),
        (0.55, 0.28, 0.12, 1),
    ]
    leaf = greens[rng.randrange(len(greens))]
    trunk_h = 0.9 * scale
    trunk = box_object(f"trunk", coll, (x, y, z + trunk_h / 2), (0.18 * scale, 0.18 * scale, trunk_h), mats["trunk"])
    canopy = ico_object(
        "canopy",
        coll,
        (x, y, z + trunk_h + 0.55 * scale),
        (1.15 * scale, 1.05 * scale, 0.85 * scale),
        mats["leaf"],
    )
    canopy.color = leaf
    bare_bm = bmesh.new()
    for ang in range(5):
        add_box(bare_bm, (0.15 * ang - 0.3, 0, 0.7), (0.05, 0.05, 1.1 * scale), 0)
    bare_me = mesh_from_bm("bare", bare_bm)
    bare = link_obj("bare", bare_me, coll, (mats["trunk"],))
    bare.location = (x, y, z)
    kit.add(trunk, "tree_trunk", future=future, delay=delay, sink=False)
    item = kit.add(canopy, "tree_canopy", future=future, delay=delay, sink=False, leaf=leaf, autumn=autumns[rng.randrange(3)])
    kit.add(bare, "tree_bare", future=future, delay=delay, sink=False)
    return item


def _car(kit, coll, mats, loc, yaw, color, parent=None, local=None, drive=0.0):
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.38), (0.86, 1.85, 0.42), 0)
    add_box(bm, (0, -0.05, 0.72), (0.78, 0.95, 0.38), 1)
    me = mesh_from_bm("car", bm)
    obj = link_obj("car", me, coll, (mats["car"], mats["glass"]))
    obj.color = color
    # wheels
    for wx, wy in ((-0.38, -0.55), (0.38, -0.55), (-0.38, 0.55), (0.38, 0.55)):
        wbm = bmesh.new()
        bmesh.ops.create_cone(wbm, cap_ends=True, segments=8, radius1=0.18, radius2=0.18, depth=0.12)
        for v in wbm.verts:
            v.co.x, v.co.z = v.co.z, v.co.x
        wme = mesh_from_bm("wheel", wbm)
        wheel = link_obj("wheel", wme, coll, (mats["rubber"],))
        wheel.parent = obj
        wheel.location = (wx, wy, 0.18)
        wheel.matrix_parent_inverse = Matrix.Identity(4)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = local
        obj.rotation_euler[2] = yaw
        stopped = local
        start = (local[0], local[1] + drive, local[2])
    else:
        obj.location = loc
        obj.rotation_euler[2] = yaw
        stopped = loc
        start = (loc[0] + drive, loc[1], loc[2])
    kit.add(
        obj,
        "car",
        path_from=start,
        path_to=stopped,
        parented=parent is not None,
        float=1.1,
        bob=0.18,
        sink=False,
    )


def _person(kit, coll, mats, x, y, z, rng):
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.55), (0.28, 0.18, 0.7), 0)
    add_box(bm, (0, 0, 1.05), (0.16, 0.16, 0.16), 1)
    me = mesh_from_bm("person", bm)
    obj = link_obj("person", me, coll, (mats["cloth"], mats["skin"]))
    obj.location = (x, y, z)
    obj.color = [(0.2, 0.35, 0.7, 1), (0.75, 0.2, 0.2, 1), (0.15, 0.15, 0.18, 1), (0.85, 0.75, 0.3, 1)][rng.randrange(4)]
    kit.add(obj, "person", float=1.6, bob=0.25, sink=False)


def _house(kit, coll, mats, x, y, z, w, d, h, index):
    body = box_object("house", coll, (x, y, z + h / 2), (w, d, h), mats["wood"])
    body.color = (0.72, 0.58, 0.40, 1) if index % 2 == 0 else (0.80, 0.72, 0.55, 1)
    bm = bmesh.new()
    hw, hd, rise = w * 0.55, d * 0.55, h * 0.45
    verts = [
        bm.verts.new((-hw, -hd, 0)),
        bm.verts.new((hw, -hd, 0)),
        bm.verts.new((hw, hd, 0)),
        bm.verts.new((-hw, hd, 0)),
        bm.verts.new((-hw, 0, rise)),
        bm.verts.new((hw, 0, rise)),
    ]
    for face in ((0, 1, 2, 3), (0, 1, 5, 4), (3, 2, 5, 4), (0, 3, 4), (1, 2, 5)):
        bm.faces.new([verts[i] for i in face])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    roof = link_obj("roof", mesh_from_bm("roof", bm), coll, (mats["roof"],))
    roof.location = (x, y, z + h)
    kit.add(body, "house", index=index, sink=False, float=0.4)
    kit.add(roof, "house_roof", index=index, sink=False, float=0.8)


def _markings(coll, mats, x0, x1, y, z, along="x"):
    step = 1.6
    if along == "x":
        x = x0
        while x < x1:
            box_object("dash", coll, (x, y, z), (0.7, 0.12, 0.02), mats["mark"])
            x += step
    else:
        yy = x0
        while yy < x1:
            box_object("dash", coll, (y, yy, z), (0.12, 0.7, 0.02), mats["mark"])
            yy += step


def build_river_city(kit, mats, rng, pieces):
    col_g = kit.collection("Terrain")
    col_c = kit.collection("City")
    col_b = kit.collection("Bridge")
    col_v = kit.collection("Life")
    col_p = kit.collection("Plants")
    # Catch-all ground so the frame never shows a void.
    _plane("bedrock", col_g, (0, -8, -0.55), (120, 120), mats["road"], 0.2)
    _plane("far", col_g, (0, 15.5, FAR_Z), (60, 22), mats["trim"])
    _plane("park", col_g, (-7.0, -10.2, PARK_Z), (32, 16), mats["park"])
    _plane("front", col_g, (0, -28, PARK_Z), (90, 36), mats["road"])
    low = _plane("lowroad", col_g, (0, -2.25, LOW_Z), (36, 2.5), mats["road"])
    # Quays.
    box_object("quay_n", col_g, (0, RIVER_Y0 - 0.15, 0.28), (40, 0.35, 0.56), mats["trim"])
    box_object("quay_f", col_g, (-4, RIVER_Y1 + 0.1, 0.45), (30, 0.4, 0.9), mats["trim"])
    # Lane markings. Foreground road and low road. Keep the caption meadow clear of clutter.
    _markings(col_g, mats, -20, 22, -16.6, PARK_Z + 0.06, "x")
    _markings(col_g, mats, -20, 22, -18.5, PARK_Z + 0.06, "x")
    for i, x in enumerate(range(-8, 10, 3)):
        box_object("cross", col_g, (x * 0.15 - 1 + i * 0.0, -15.2, PARK_Z + 0.06), (0.35, 1.4, 0.02), mats["mark"])
    # A few crosswalk bars across the near road.
    for i in range(6):
        box_object("bar", col_g, (-2.2 + i * 0.55, -15.15, PARK_Z + 0.065), (0.28, 2.4, 0.02), mats["mark"])

    # Cave-in slabs on the low road.
    for i, x in enumerate((-6.5, -3.2)):
        slab = box_object("slab", col_g, (x, -2.3, LOW_Z + 0.06), (2.4, 2.1, 0.08), mats["road"])
        box_object("hole", col_g, (x, -2.3, LOW_Z - 0.35), (2.2, 1.9, 0.4), mats["dark"])
        kit.add(slab, "road_slab", index=i, sink=False)

    if "subway" in pieces:
        box_object("stair", col_g, (-1.2, -2.5, LOW_Z - 0.15), (1.4, 1.1, 0.45), mats["dark"])
        box_object("rail_a", col_g, (-1.9, -2.5, LOW_Z + 0.35), (0.08, 1.2, 0.55), mats["trim"])
        box_object("rail_b", col_g, (-0.5, -2.5, LOW_Z + 0.35), (0.08, 1.2, 0.55), mats["trim"])

    # Skyline. Leave a gap where the bridge lands.
    colors = [
        (0.62, 0.78, 0.88, 1),
        (0.92, 0.93, 0.94, 1),
        (0.82, 0.76, 0.66, 1),
        (0.72, 0.45, 0.40, 1),
        (0.52, 0.62, 0.74, 1),
        (0.88, 0.80, 0.70, 1),
        (0.45, 0.52, 0.60, 1),
        (0.78, 0.55, 0.48, 1),
    ]
    fall_i = 0
    x = -18.0
    row = 0
    while x < 20.5:
        if 4.2 < x < 11.2:
            x += 1.2
            continue
        w = rng.uniform(2.3, 4.6)
        d = rng.uniform(2.3, 4.0)
        band = row % 3
        if band == 0:
            h = rng.uniform(6.0, 12.0)
            y = 9.2 + rng.uniform(-0.3, 0.4)
        elif band == 1:
            h = rng.uniform(12.0, 24.0)
            y = 12.6
        else:
            h = rng.uniform(16.0, 32.0)
            y = 16.0
        color = colors[rng.randrange(len(colors))]
        falling = h > 14 and fall_i < 6
        if h > 12 and falling:
            split = h * 0.56
            base = link_obj("tower", _tower_mesh("tower", w, d, split), col_c, (mats["wall"], mats["window"]))
            base.location = (x, y, FAR_Z)
            base.color = color
            top = link_obj("top", _tower_mesh("top", w * 0.96, d * 0.96, h - split), col_c, (mats["wall"], mats["window"]))
            top.location = (x, y, FAR_Z + split)
            top.color = color
            kit.add(base, "building_base", sink=True, fall_at=None)
            kit.add(top, "building_top", sink=True, fall_at=0.40 + fall_i * 0.045, index=fall_i, top_h=h - split)
            fall_i += 1
        else:
            obj = link_obj("tower", _tower_mesh("tower", w, d, h), col_c, (mats["wall"], mats["window"]))
            obj.location = (x, y, FAR_Z)
            obj.color = color
            kit.add(obj, "building_base", sink=True, fall_at=None)
        x += w + rng.uniform(0.35, 0.85)
        row += 1

    if "power" in pieces:
        _power_plant(kit, col_c, mats, -19.5, 10.5, FAR_Z)

    if "bridge" in pieces:
        _bridge(kit, col_b, col_v, mats, rng)

    if "suburbs" in pieces:
        for i in range(6):
            _house(kit, col_c, mats, -16.5 + (i % 3) * 3.3, -7.6 - (i // 3) * 3.4, PARK_Z, 2.2, 1.8, 1.7, i)

    # Park trees, kept off the open meadow in the lower middle.
    spots = [
        (-15, -6, 1.3),
        (-12.5, -11, 1.5),
        (-14, -13.5, 1.1),
        (-9, -5.5, 1.4),
        (-8, -12.5, 1.2),
        (-5.5, -6.2, 1.0),
        (2.5, -6.0, 1.15),
        (3.4, -8.5, 0.9),
        (-11, -8.5, 1.25),
        (0.5, -5.4, 1.05),
        (-17, -10, 1.4),
        (4.2, -5.2, 0.85),
    ]
    for x, y, s in spots:
        _tree(kit, col_p, mats, x, y, PARK_Z, s, future=False, rng=rng)

    if "forest" in pieces:
        # Future forest. Delays stagger the takeover.
        for i in range(28):
            x = rng.uniform(-16, 18)
            if 5.5 < x < 10.5 and rng.random() < 0.5:
                continue
            y = rng.choice([
                rng.uniform(-14, -4),
                rng.uniform(-3.2, -1.4),
                rng.uniform(8.2, 14),
            ])
            z = PARK_Z if y < -3.5 else (LOW_Z if y < 0 else FAR_Z)
            _tree(kit, col_p, mats, x, y, z, rng.uniform(0.8, 2.2), future=True, delay=rng.uniform(0.15, 0.85), rng=rng)
        for i in range(18):
            x = rng.uniform(-14, 12)
            y = rng.uniform(-13, -5)
            bush = ico_object("bush", col_p, (x, y, PARK_Z + 0.25), (0.45, 0.4, 0.28), mats["leaf"])
            bush.color = (0.30, 0.58, 0.18, 1)
            kit.add(bush, "weed", delay=rng.uniform(0.05, 0.45), sink=False, leaf=(0.30, 0.58, 0.18, 1), autumn=(0.62, 0.48, 0.16, 1))

    # People and cars.
    for i in range(8):
        _person(kit, col_v, mats, rng.uniform(-12, 2), rng.uniform(-13, -6), PARK_Z, rng)
    car_colors = [
        (0.92, 0.92, 0.94, 1),
        (0.08, 0.08, 0.09, 1),
        (0.75, 0.12, 0.12, 1),
        (0.15, 0.28, 0.62, 1),
        (0.85, 0.72, 0.18, 1),
    ]
    for i, x in enumerate((-12, -6, 0, 8, 14)):
        _car(kit, col_v, mats, (x, -17.4 if i % 2 == 0 else -16.5, PARK_Z + 0.02), 1.57 if i % 2 == 0 else -1.57, car_colors[i % 5], drive=rng.uniform(2.5, 5.0))
    for i, x in enumerate((-8, -2, 6)):
        _car(kit, col_v, mats, (x, -11.2, PARK_Z + 0.02), 0.15, car_colors[(i + 2) % 5], drive=0.0)
    for i, x in enumerate((-5.5, 1.5)):
        _car(kit, col_v, mats, (x, -2.3, LOW_Z + 0.02), 1.57, car_colors[i], drive=1.5)

    # Water last so it can be found.
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.12), (70, 28, 0.24), 0)
    water = link_obj("water", mesh_from_bm("water", bm), col_g, (mats["water"],))
    water.location = (2, 2.2, 0.18)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "city"


def _power_plant(kit, coll, mats, x, y, z):
    for i, dx in enumerate((-1.1, 1.1)):
        bm = bmesh.new()
        add_box(bm, (0, 0, 0.6), (1.5, 1.5, 1.2), 0)
        add_box(bm, (0, 0, 2.0), (1.15, 1.15, 1.8), 0)
        add_box(bm, (0, 0, 3.3), (0.85, 0.85, 1.0), 0)
        obj = link_obj("cool", mesh_from_bm("cool", bm), coll, (mats["trim"],))
        obj.location = (x + dx, y, z)
        kit.add(obj, "building_base", sink=True)
    stack = box_object("stack", coll, (x + 2.4, y + 0.4, z + 2.4), (0.55, 0.55, 4.8), mats["trim"])
    kit.add(stack, "building_base", sink=True)
    for i in range(3):
        puff = ico_object("puff", coll, (x + 2.4, y + 0.4, z + 5.2), (0.6, 0.6, 0.5), mats["smoke"])
        kit.add(puff, "smoke", index=i, sink=True, phase=i / 3.0)


def _bridge(kit, col, cars, mats, rng):
    # Flat deck segments along Y, plus a near ramp down to the foreground road.
    segments = []
    specs = [
        # i, y center, length, z, rot_x for ramp
        # Positive X rotation lifts the far end onto the tower deck and drops the near end onto the road.
        (0, -9.2, 15.0, 1.78, 0.115),
        (1, -0.4, 7.2, DECK_Z, 0.0),
        (2, 5.4, 6.4, DECK_Z, 0.0),
        (3, 10.2, 4.6, DECK_Z, 0.0),
    ]
    decks = []
    for i, y, length, z, rot in specs:
        obj = box_object("deck", col, (DECK_X, y, z), (3.15, length, 0.22), mats["road"])
        obj.rotation_euler[0] = rot
        # railings
        for side in (-1, 1):
            rail = box_object("rail", col, (0, 0, 0), (0.12, length * 0.96, 0.55), mats["bridge"])
            rail.parent = obj
            rail.matrix_parent_inverse = Matrix.Identity(4)
            rail.location = (side * 1.55, 0, 0.35)
        # lane dashes in local space
        dash_count = int(length / 1.5)
        for d in range(dash_count):
            mark = box_object("bdash", col, (0, 0, 0), (0.1, 0.55, 0.02), mats["yellow"] if side else mats["mark"])
            mark.parent = obj
            mark.matrix_parent_inverse = Matrix.Identity(4)
            mark.location = (0.15, -length / 2 + 0.8 + d * 1.5, 0.12)
        item = kit.add(obj, "bridge_deck", i=i, sink=True, length=length)
        decks.append(item)
        segments.append(obj)
    # Towers standing in the river.
    towers = []
    for i, y in enumerate((0.15, 6.35)):
        pivot = empty(f"tower_{i}", col, (DECK_X, y, 0.0))
        _tower_portal(col, mats, pivot, TOWER_H, TOWER_W)
        towers.append(kit.add(pivot, "bridge_tower", i=i, height=TOWER_H, width=TOWER_W, sink=True))
    # Cables and suspenders. Meshes are unit cylinders aimed every frame.
    cyl = cylinder_mesh("cable", radius=1.0, segments=6)
    cables = []
    for side in (-1, 1):
        for _ in range(36):
            obj = link_obj("cable", cyl, col, (mats["cable"],))
            cables.append(obj)
    suspenders = []
    for _ in range(42):
        obj = link_obj("sus", cyl, col, (mats["cable"],))
        suspenders.append(obj)
    # Cars on the two main spans.
    colors = [(0.92, 0.92, 0.94, 1), (0.1, 0.1, 0.12, 1), (0.7, 0.15, 0.14, 1), (0.2, 0.35, 0.7, 1)]
    for i, (seg, ly) in enumerate(((segments[1], -1.2), (segments[1], 0.8), (segments[2], -0.6), (segments[2], 1.1))):
        _car(
            kit,
            cars,
            mats,
            (0, 0, 0),
            0.0,
            colors[i],
            parent=seg,
            local=(0.55 if i % 2 == 0 else -0.55, ly, 0.16),
            drive=2.2,
        )
    kit.bridge = {
        "decks": decks,
        "towers": towers,
        "cables": cables,
        "suspenders": suspenders,
        "anchors": [
            (DECK_X - 1.55, -3.4, 3.15),
            (DECK_X + 1.55, -3.4, 3.15),
            (DECK_X - 1.55, 11.4, 3.05),
            (DECK_X + 1.55, 11.4, 3.05),
        ],
    }


def _tower_portal(coll, mats, pivot, height, width):
    def leg(side):
        obj = box_object("leg", coll, (0, 0, 0), (0.42, 0.55, height), mats["bridge"])
        obj.parent = pivot
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = (side * width / 2, 0, height / 2)
    leg(-1)
    leg(1)
    for z in (3.5, 7.1, 10.4):
        beam = box_object("beam", coll, (0, 0, 0), (width, 0.36, 0.32), mats["bridge"])
        beam.parent = pivot
        beam.matrix_parent_inverse = Matrix.Identity(4)
        beam.location = (0, 0, z)
    # X braces in the portal (XZ plane).
    for z0, z1 in ((3.7, 6.9), (7.3, 10.2)):
        for sign in (-1, 1):
            brace = box_object("brace", coll, (0, 0, 0), (0.12, 0.12, (z1 - z0) * 1.15), mats["bridge"])
            brace.parent = pivot
            brace.matrix_parent_inverse = Matrix.Identity(4)
            brace.location = (0, 0.18 * sign, (z0 + z1) / 2)
            brace.rotation_euler[1] = sign * 0.72
    cap = box_object("cap", coll, (0, 0, 0), (width + 0.6, 0.7, 0.28), mats["bridge"])
    cap.parent = pivot
    cap.matrix_parent_inverse = Matrix.Identity(4)
    cap.location = (0, 0, height + 0.1)


def build_coast(kit, mats, rng, with_city):
    col = kit.collection("Coast")
    col_c = kit.collection("City")
    _plane("seabed", col, (0, 8, -2.55), (70, 40), mats["sand"], 0.2)
    _plane("beach", col, (0, -8, 0.35), (56, 14), mats["sand"])
    _plane("back", col, (0, -16, 0.55), (56, 8), mats["park"])
    for i in range(8):
        rock = ico_object("rock", col, (rng.uniform(-18, 18), rng.uniform(-2, 16), -2.2), rng.uniform(0.4, 1.4), mats["rock"])
        kit.add(rock, "prop", sink=False, float=0.2)
    if with_city:
        colors = [(0.7, 0.78, 0.86, 1), (0.9, 0.9, 0.88, 1), (0.75, 0.5, 0.42, 1)]
        x = -16
        i = 0
        while x < 16:
            h = rng.uniform(6, 22)
            w = rng.uniform(2.4, 4.2)
            obj = link_obj("ctower", _tower_mesh("ct", w, w, h), col_c, (mats["wall"], mats["window"]))
            obj.location = (x, -12.5 - (i % 2), 0.55)
            obj.color = colors[i % 3]
            kit.add(obj, "building_base", sink=False, floodable=True)
            x += w + 0.6
            i += 1
        for i in range(4):
            _house(kit, col_c, mats, -12 + i * 3.2, -6.5, 0.35, 2.0, 1.6, 1.5, i)
    # Ships rest on the seabed; effects lift them with the water.
    for i, x in enumerate((-6, 8)):
        bm = bmesh.new()
        add_box(bm, (0, 0, 0.4), (1.6, 5.5, 0.7), 0)
        add_box(bm, (0, -0.4, 1.15), (1.3, 1.6, 0.8), 0)
        add_box(bm, (0, 1.6, 1.5), (0.35, 0.35, 1.3), 0)
        ship = link_obj("ship", mesh_from_bm("ship", bm), col, (mats["trim"],))
        ship.location = (x, 4 + i * 3, -2.3)
        ship.color = (0.3, 0.35, 0.4, 1)
        kit.add(ship, "ship", sink=False, draft=0.9)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (80, 50, 0.2), 0)
    water = link_obj("sea", mesh_from_bm("sea", bm), col, (mats["water"],))
    water.location = (0, 6, 0.05)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "coast"
    for i in range(6):
        _tree(kit, col, mats, rng.uniform(-14, 14), rng.uniform(-12, -5), 0.4, rng.uniform(0.8, 1.4), rng=rng)


def build_farm(kit, mats, rng):
    col = kit.collection("Farm")
    _plane("field", col, (0, 0, 0), (60, 50), mats["dirt"], 0.1)
    _plane("pasture", col, (-8, -6, 0.02), (24, 18), mats["park"])
    # Crop rows.
    for row in range(8):
        for col_i in range(10):
            x = -6 + col_i * 1.3
            y = 2 + row * 1.5
            crop = box_object("crop", col, (x, y, 0.35), (0.35, 0.35, 0.7), mats["leaf"])
            crop.color = (0.35, 0.62, 0.18, 1)
            kit.add(crop, "crop", delay=row / 20.0, sink=False, leaf=(0.35, 0.62, 0.18, 1), autumn=(0.55, 0.38, 0.12, 1))
    for i in range(10):
        flower = ico_object("flower", col, (rng.uniform(-16, -2), rng.uniform(-12, -2), 0.2), 0.18, mats["leaf"])
        flower.color = [(0.85, 0.3, 0.35, 1), (0.9, 0.8, 0.3, 1), (0.85, 0.55, 0.7, 1)][i % 3]
        kit.add(flower, "flower", sink=False, leaf=tuple(flower.color), autumn=(0.45, 0.32, 0.18, 1))
    for i in range(8):
        _tree(kit, col, mats, rng.uniform(-18, 16), rng.uniform(-16, 14), 0.0, rng.uniform(1.0, 2.0), rng=rng)
    _house(kit, col, mats, -14, 8, 0, 3.2, 2.4, 2.2, 0)
    # Birds and a couple of animals.
    for i in range(6):
        bird = ico_object("bird", col, (rng.uniform(-8, 8), rng.uniform(-4, 6), 2.5 + i * 0.2), (0.28, 0.1, 0.08), mats["trim"])
        kit.add(bird, "bird", phase=i, sink=False, float=2.2, bob=0.4)
    deer = box_object("deer", col, (4, -8, 0.55), (0.4, 0.9, 0.7), mats["wood"])
    deer.color = (0.45, 0.30, 0.16, 1)
    kit.add(deer, "animal", sink=False)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (30, 8, 0.2), 0)
    water = link_obj("pond", mesh_from_bm("pond", bm), col, (mats["water"],))
    water.location = (10, 6, 0.02)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "farm"


def build_strata(kit, mats):
    col = kit.collection("Geology")
    pivot = empty("strata", col, (0, 16.5, 0.0))
    layers = [
        (0.0, 1.4, lin(0.42, 0.30, 0.20), "rock"),
        (1.4, 1.3, lin(0.55, 0.52, 0.48), "rock"),
        (2.7, 1.2, lin(0.70, 0.60, 0.42), "rock"),
        (3.9, 0.16, lin(0.90, 0.24, 0.06), "seam"),
        (4.06, 1.3, lin(0.62, 0.58, 0.52), "rock"),
        (5.36, 1.15, lin(0.48, 0.42, 0.36), "rock"),
        (6.51, 0.7, lin(0.36, 0.30, 0.20), "dirt"),
    ]
    for i, (z0, h, _color, mat_name) in enumerate(layers):
        # Fixed materials already carry color; seam uses emission.
        mat = mats["seam"] if mat_name == "seam" else mats[mat_name]
        block = box_object("layer", col, (0, 0, 0), (58, 3.2, h), mat)
        block.parent = pivot
        block.matrix_parent_inverse = Matrix.Identity(4)
        block.location = (0, 0, z0 + h / 2)
    for i in range(11):
        tree = ico_object("stree", col, (0, 0, 0), (0.7, 0.6, 0.9), mats["leaf"])
        tree.parent = pivot
        tree.matrix_parent_inverse = Matrix.Identity(4)
        tree.location = (-20 + i * 4.0, -1.3, 7.5)
        tree.color = (0.30, 0.5, 0.18, 1)
    kit.add(pivot, "strata", sink=False)
    # Glacier in the river, hidden until the ice age.
    glacier = ico_object("glacier", kit.collection("Weather"), (4, 3.5, 0.6), (3.5, 2.2, 1.1), mats["snow"])
    kit.add(glacier, "glacier", sink=False)


def build_precip(kit, mats, features):
    col = kit.collection("Weather")
    if features.get("rain"):
        for i in range(80):
            drop = box_object("rain", col, (0, 0, 0), (0.03, 0.03, 0.55), mats["mark"])
            kit.precip.append(("rain", drop, i))
            drop.hide_render = True
    if features.get("snow") or features.get("ice"):
        for i in range(70):
            flake = ico_object("flake", col, (0, 0, 0), 0.08, mats["snow"])
            kit.precip.append(("snow", flake, i))
            flake.hide_render = True
    if features.get("dust") or features.get("heat"):
        for i in range(50):
            mote = ico_object("dust", col, (0, 0, 0), 0.07, mats["sand"])
            kit.precip.append(("dust", mote, i))
            mote.hide_render = True
    if features.get("ash") or features.get("fire"):
        for i in range(40):
            ash = ico_object("ash", col, (0, 0, 0), 0.06, mats["trim"])
            kit.precip.append(("ash", ash, i))
            ash.hide_render = True


def build_fx_meshes(kit, mats, features):
    col = kit.collection("Weather")
    if features.get("fire") or features.get("heat"):
        for i in range(5):
            flame = ico_object("flame", col, (-8 + i * 4, 10, FAR_Z + 1.2), (0.4, 0.4, 1.1), mats["flame"])
            kit.add(flame, "flame", index=i, sink=True)
            flame.hide_render = True
        for i in range(6):
            crack = box_object("crack", col, (-10 + i * 3.5, -8, PARK_Z + 0.03), (0.08, 2.4, 0.02), mats["dark"])
            kit.add(crack, "crack", index=i, sink=False)
            crack.hide_render = True
    # Snow mounds that bury cars. Always available; hidden until snow.
    for i in range(8):
        mound = ico_object("mound", col, (0, 0, 0), 1.0, mats["snow"])
        kit.add(mound, "mound", index=i, sink=False)
        mound.hide_render = True


def build_mauna_kea(kit, mats, rng):
    """Hawaii island and Mauna Kea. Ocean drains by lowering the water plane."""
    col = kit.collection("Coast")
    _plane("shelf", col, (0, 6, -3.2), (80, 50), mats["sand"], 0.2)
    _plane("shore", col, (0, -6, 0.15), (40, 10), mats["sand"])
    # Volcano as stacked rings, wide at the base.
    for i, (z, rad, h) in enumerate(((0.2, 16, 3.2), (3.2, 11, 3.0), (6.0, 7, 2.6), (8.4, 4.2, 2.2), (10.2, 2.2, 1.4))):
        obj = box_object("cone", col, (0, 2, z + h / 2), (rad * 2, rad * 1.4, h), mats["rock"])
        kit.add(obj, "building_base", sink=False, erode=True)
    for i, dx in enumerate((-1.2, 0.4, 1.5)):
        dome = ico_object("dome", col, (dx, 2.2, 11.8), 0.55, mats["trim"])
        kit.add(dome, "prop", sink=False)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (90, 60, 0.2), 0)
    water = link_obj("pacific", mesh_from_bm("pacific", bm), col, (mats["water"],))
    water.location = (0, 8, 0.02)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "coast"


def build_ny_harbor(kit, mats, rng):
    """Harbor water, a low skyline, and a simplified Statue of Liberty."""
    col = kit.collection("Harbor")
    col_c = kit.collection("City")
    _plane("island", col, (-6, -2, 0.35), (10, 8), mats["park"])
    _plane("manhattan", col, (8, 14, 0.4), (28, 10), mats["trim"])
    x = -2
    for i in range(7):
        h = 8 + (i * 3) % 14
        w = 2.4
        obj = link_obj("ny", _tower_mesh("ny", w, w, h), col_c, (mats["wall"], mats["window"]))
        obj.location = (x, 14, 0.4)
        obj.color = (0.75, 0.78, 0.82, 1)
        kit.add(obj, "building_base", sink=False)
        x += w + 0.7
    # Statue: pedestal, robe, head, crown, tablet. Copper green.
    green = (0.22, 0.55, 0.34, 1)
    ped = box_object("pedestal", col, (-6, -2, 1.6), (2.2, 2.2, 2.4), mats["trim"])
    robe = box_object("robe", col, (-6, -2, 4.3), (1.3, 1.1, 3.0), mats["car"])
    robe.color = green
    head = ico_object("head", col, (-6, -2.1, 6.2), 0.55, mats["car"])
    head.color = green
    for i in range(7):
        ang = i / 7 * 6.28
        spike = box_object("spike", col, (-6 + math.cos(ang) * 0.35, -2.1 + math.sin(ang) * 0.35, 6.9), (0.08, 0.08, 0.7), mats["car"])
        spike.color = green
    tablet = box_object("tablet", col, (-4.7, -2, 4.6), (0.7, 0.15, 1.1), mats["car"])
    tablet.color = green
    for obj in (ped, robe, head, tablet):
        kit.add(obj, "prop", sink=False)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (80, 40, 0.2), 0)
    water = link_obj("harbor", mesh_from_bm("harbor", bm), col, (mats["water"],))
    water.location = (2, 2, 0.05)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "coast"


def build_culdesac(kit, mats, rng):
    """US suburban loop. The snow episode's locked camera lives here."""
    col = kit.collection("Suburb")
    _plane("yards", col, (0, 0, 0.0), (46, 40), mats["park"])
    _plane("asphalt", col, (0, 0, 0.05), (18, 16), mats["road"])
    _plane("green", col, (0, 0, 0.08), (8, 6), mats["park"])
    spots = [(-8, -6), (-8, 0), (-8, 6), (8, -6), (8, 0), (8, 6), (-3, 8), (3, 8)]
    for i, (x, y) in enumerate(spots):
        _house(kit, col, mats, x, y, 0.08, 2.4, 2.0, 1.8, i)
        _tree(kit, col, mats, x + (1.6 if x < 0 else -1.6), y + 1.2, 0.08, 1.1, rng=rng)
    for i, x in enumerate((-2.2, 2.2)):
        _car(kit, col, mats, (x, -1.5, 0.1), 0.0, (0.9, 0.9, 0.92, 1) if i == 0 else (0.15, 0.2, 0.45, 1), drive=0.0)
    box_object("tower", col, (0, 0, 3.2), (0.8, 0.8, 6.2), mats["trim"])
    kit.kind = "suburb"
    kit.water = None


def build_desert(kit, mats, rng):
    """Red-rock basin. Rain fills the wash, then plants take the stone."""
    col = kit.collection("Desert")
    _plane("basin", col, (0, 2, 0.0), (55, 48), mats["sand"])
    for i, (x, y, w, h) in enumerate(((-8, 6, 4, 7), (6, 8, 3, 5), (0, 14, 6, 4), (10, 2, 2.5, 6))):
        butte = box_object("butte", col, (x, y, h / 2), (w, w * 0.7, h), mats["rock"])
        kit.add(butte, "building_base", sink=False)
    if "forest" in (kit.extra_pieces if hasattr(kit, "extra_pieces") else []):
        pass
    for i in range(16):
        fern = ico_object("fern", col, (rng.uniform(-12, 12), rng.uniform(-6, 12), 0.4), rng.uniform(0.4, 1.3), mats["leaf"])
        fern.color = (0.28, 0.5, 0.2, 1)
        kit.add(fern, "weed", delay=rng.uniform(0.2, 0.8), sink=False, leaf=(0.28, 0.5, 0.2, 1), autumn=(0.45, 0.32, 0.14, 1))
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.08), (30, 14, 0.16), 0)
    water = link_obj("wash", mesh_from_bm("wash", bm), col, (mats["water"],))
    water.location = (0, 2, -2.2)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "desert"


def add_mascot(kit, mats, loc):
    """Small figure with a red sign. Off to the side, so the shot still reads."""
    col = kit.collection("Mascot")
    x, y, z = loc
    body = box_object("mascot", col, (x, y, z + 0.42), (0.26, 0.16, 0.5), mats["car"])
    body.color = (0.12, 0.28, 0.62, 1)
    head = ico_object("mascot_head", col, (x, y - 0.02, z + 0.78), 0.14, mats["car"])
    head.color = (0.93, 0.78, 0.62, 1)
    sign = box_object("mascot_sign", col, (x + 0.32, y, z + 0.62), (0.34, 0.04, 0.26), mats["bridge"])
    kit.add(body, "mascot", sink=False, throw=6.0, index=1)
    kit.add(head, "mascot", sink=False, throw=6.2, index=2)
    kit.add(sign, "mascot", sink=False, throw=7.0, index=3)


def build_nyc_avenue(kit, mats, rng):
    """Bright flat avenue. The reusable format-C street."""
    col = kit.collection("Avenue")
    _plane("street", col, (0, 8, 0.0), (14, 70), mats["road"])
    _plane("walk_l", col, (-8.2, 8, 0.08), (3.2, 70), mats["trim"])
    _plane("walk_r", col, (8.2, 8, 0.08), (3.2, 70), mats["trim"])
    colors = [(0.86, 0.88, 0.9, 1), (0.95, 0.78, 0.7, 1), (0.7, 0.78, 0.86, 1), (0.92, 0.9, 0.82, 1)]
    for side in (-1, 1):
        y = -4
        i = 0
        while y < 40:
            w = rng.uniform(3.2, 5.0)
            h = rng.uniform(10, 28)
            obj = link_obj("ave", _tower_mesh("ave", w, w * 0.8, h), col, (mats["wall"], mats["window"]))
            obj.location = (side * (9.5 + w * 0.3), y, 0.08)
            obj.color = colors[i % len(colors)]
            kit.add(obj, "building_base", sink=False)
            if h > 16:
                top = link_obj("avetop", _tower_mesh("avetop", w * 0.9, w * 0.7, h * 0.35), col, (mats["wall"], mats["window"]))
                top.location = (side * (9.5 + w * 0.3), y, 0.08 + h * 0.65)
                top.color = obj.color
                kit.add(top, "building_top", sink=False, fall_at=0.4, top_h=h * 0.35, index=i)
            y += w + 0.8
            i += 1
    for i, y in enumerate((-2, 4, 12, 22)):
        _car(kit, col, mats, (-1.6 if i % 2 == 0 else 1.6, y, 0.05), 0.0, (0.9, 0.9, 0.92, 1), drive=0.0)
    kit.kind = "nyc"
    kit.water = None


def build_rio_beach(kit, mats, rng):
    """Beach, a low skyline, and an ocean that can pull back."""
    col = kit.collection("Beach")
    _plane("sand", col, (0, -2, 0.05), (40, 18), mats["sand"])
    _plane("cityground", col, (0, 12, 0.2), (36, 14), mats["trim"])
    for i, x in enumerate(range(-12, 14, 4)):
        h = 6 + (i % 4) * 3
        obj = link_obj("rio", _tower_mesh("rio", 3.2, 3.0, h), col, (mats["wall"], mats["window"]))
        obj.location = (x, 12, 0.2)
        obj.color = (0.95, 0.9, 0.8, 1)
        kit.add(obj, "building_base", sink=False)
        _tree(kit, col, mats, x + 1.4, 4, 0.05, 1.0, rng=rng)
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.1), (50, 24, 0.2), 0)
    water = link_obj("atlantic", mesh_from_bm("atlantic", bm), col, (mats["water"],))
    water.location = (0, -12, 0.02)
    kit.water = kit.add(water, "water", sink=False)
    kit.kind = "rio"


def build_kitchen(kit, mats, rng):
    """A counter and a burger. Mold is vegetation; drying is wilt and heat."""
    col = kit.collection("Kitchen")
    _plane("counter", col, (0, 0, 0.9), (8, 5), mats["trim"], 0.12)
    _plane("back", col, (0, 2.2, 1.8), (8, 0.2), mats["wall"] if False else mats["trim"], 1.6)
    # Burger stack, each layer its own object so it can sag.
    layers = [
        ("bun_bottom", 0.08, (0.72, 0.55, 0.28)),
        ("patty", 0.07, (0.28, 0.14, 0.08)),
        ("cheese", 0.025, (0.9, 0.72, 0.15)),
        ("lettuce", 0.04, (0.3, 0.62, 0.18)),
        ("bun_top", 0.09, (0.82, 0.6, 0.32)),
    ]
    for side, x0 in (("fast", -0.95), ("home", 0.95)):
        z = 0.98
        for i, (name, h, color) in enumerate(layers):
            obj = box_object(f"{side}_{name}", col, (x0, 0, z + h / 2), (1.15 - i * 0.04, 1.15 - i * 0.04, h), mats["car"])
            obj.color = (*color, 1)
            kit.add(obj, "food", index=i, sink=False)
            z += h
    for i in range(8):
        mold = ico_object("mold", col, (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1.35), 0.12, mats["leaf"])
        mold.color = (0.25, 0.45, 0.18, 1)
        kit.add(mold, "weed", delay=0.15 + i * 0.08, sink=False, leaf=(0.25, 0.45, 0.18, 1), autumn=(0.35, 0.28, 0.12, 1))
    kit.kind = "kitchen"
    kit.water = None


def build_scene(scene, spec, features):
    rng = random.Random(int((spec.get("scene") or {}).get("seed") or 1))
    pieces = set((spec.get("scene") or {}).get("pieces") or ["city", "river", "bridge"])
    kit = Kit(scene)
    mats = _materials()
    kit.mats = mats
    kit.format = spec.get("format") or "A"
    name = (spec.get("scene") or {}).get("name") or ""
    if name == "mauna_kea":
        build_mauna_kea(kit, mats, rng)
    elif name == "ny_harbor":
        build_ny_harbor(kit, mats, rng)
    elif name == "kitchen":
        build_kitchen(kit, mats, rng)
    elif name == "culdesac":
        build_culdesac(kit, mats, rng)
    elif name == "desert":
        build_desert(kit, mats, rng)
    elif name == "nyc_avenue":
        build_nyc_avenue(kit, mats, rng)
    elif name == "rio_beach":
        build_rio_beach(kit, mats, rng)
    elif "coast" in pieces:
        build_coast(kit, mats, rng, with_city="city" in pieces)
        if "suburbs" in pieces and "city" not in pieces:
            for i in range(5):
                _house(kit, kit.collection("City"), mats, -8 + i * 3, -6, 0.35, 2.1, 1.7, 1.6, i)
    elif "farm" in pieces or ("forest" in pieces and "city" not in pieces):
        build_farm(kit, mats, rng)
    else:
        build_river_city(kit, mats, rng, pieces)
    if not name and ("city" in pieces or "coast" in pieces or kit.kind == "city"):
        build_strata(kit, mats)
    build_precip(kit, mats, features)
    build_fx_meshes(kit, mats, features)
    # Volume for ice fog, dust, ash, rain haze.
    vol_me_bm = bmesh.new()
    add_box(vol_me_bm, (0, 0, 0), (80, 70, 30), 0)
    vol = link_obj("fog", mesh_from_bm("fog", vol_me_bm), kit.collection("Weather"), (make_volume(),))
    vol.location = (0, 0, 8)
    vol.hide_render = True
    kit.volume = vol
    if kit.format == "C":
        from engine.format_c import build_wave

        build_wave(kit, mats)
    if spec.get("mascot", True):
        corners = {
            "city": (-16.8, -13.2, 0.92),
            "suburb": (13.0, 8.5, 0.1),
            "desert": (14.0, -3.0, 0.05),
            "coast": (12.0, -7.0, 0.3),
            "kitchen": (2.3, 0.6, 0.96),
            "nyc": (4.2, -8.0, 0.02),
            "rio": (-10.0, 1.5, 0.08),
        }
        add_mascot(kit, mats, corners.get(kit.kind, (6.0, -6.0, 0.1)))
    _lights(kit)
    return kit


def _lights(kit):
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.2
    sun_data.angle = 0.09
    sun_data.color = (1.0, 0.97, 0.92)
    sun = bpy.data.objects.new("Sun", sun_data)
    kit.collection("Lights").objects.link(sun)
    sun.rotation_euler = (0.92, 0.05, -0.55)
    kit.sun = sun
    fill_data = bpy.data.lights.new("Fill", "SUN")
    fill_data.energy = 0.55
    fill_data.angle = 0.6
    fill_data.color = (0.75, 0.84, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    kit.collection("Lights").objects.link(fill)
    fill.rotation_euler = (1.1, 0.2, 2.4)
    kit.fill = fill
    world = bpy.data.worlds.new("Sky")
    kit.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = lin(0.64, 0.76, 0.88)
    bg.inputs[1].default_value = 0.9
    kit.world_bg = bg
