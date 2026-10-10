"""Format C: a locked street camera, running in real seconds.

Episode 1 does not use this. The hooks are here so a disaster spec can drive
the same city without a second scene graph.

`inertia` is the eastward launch of loose props. It is the curve a rigid-body
bake would draw; swapping in a baked simulation means replacing this function,
not the city. `fracture` shears building tops. `wave` lifts a displaced wall.
`critical` is the HUD failure fraction.
"""

from __future__ import annotations

import math

import bmesh
from mathutils import Vector

from engine.meshkit import add_box, link_obj, mesh_from_bm

LOOSE = {"car", "person", "tree_canopy", "tree_trunk", "tree_bare", "lamp", "bird", "animal"}


def build_wave(kit, mats):
    col = kit.collection("Weather")
    bm = bmesh.new()
    # A wide wall with a lumpy crest. Displaced mesh, not a fluid sim.
    segments = 24
    width = 46.0
    for i in range(segments):
        x = -width / 2 + width * i / (segments - 1)
        crest = 0.35 * math.sin(i * 0.7)
        add_box(bm, (x, 0, 2.2 + crest), (width / segments * 1.05, 1.4, 4.4 + crest), 0)
    obj = link_obj("wave", mesh_from_bm("wave", bm), col, (mats["water"],))
    obj.location = (8, 18, -6)
    obj.hide_render = True
    kit.wave = obj


def apply_format_c(kit, ch, frame, fps):
    inertia = ch.get("inertia", 0.0)
    fracture = ch.get("fracture", 0.0)
    wave = ch.get("wave", 0.0)
    # Loose props keep going east after the ground stops. A small arc, then they drop.
    for item in kit.items:
        if item.role not in LOOSE:
            continue
        throw = float(item.extra.get("throw", 14.0 + (item.extra.get("index") or 0)))
        loc = Vector(item.obj.location)
        base = item.base_loc
        loc.x = base.x + inertia * throw
        loc.z = base.z + math.sin(min(inertia, 1.0) * math.pi) * (2.2 + 0.15 * throw)
        item.obj.location = loc
        item.obj.rotation_euler.y = inertia * 1.4
        item.obj.rotation_euler.z = inertia * 0.4
    if fracture > 0.02:
        for item in kit.items:
            if item.role != "building_top":
                continue
            item.obj.location.x += fracture * 6.0
            item.obj.rotation_euler.y += fracture * 0.8
            item.obj.rotation_euler.z += fracture * 0.35
    wall = getattr(kit, "wave", None)
    if wall is not None:
        wall.hide_render = wave < 0.04
        wall.location.y = 18.0 - wave * 28.0
        wall.location.z = -6.0 + wave * 7.5
        if wave > 0.72 and kit.world_bg is not None:
            # Underwater grade once the wall passes the camera.
            kit.world_bg.inputs[0].default_value = (0.02, 0.08, 0.16, 1)
            kit.world_bg.inputs[1].default_value = 0.35
    # Dust already rides the precip system when `dust` is keyed.
    _ = frame, fps
