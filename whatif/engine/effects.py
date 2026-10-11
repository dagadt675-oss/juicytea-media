"""Effect library. Every effect is driven by a 0..1 channel (water may be signed)."""

from __future__ import annotations

import math

from mathutils import Euler, Vector

from engine.city_layout import city_water_top
from engine.meshkit import aim_z, clamp, lin, smoother


def _euler(base, dx=0.0, dy=0.0, dz=0.0):
    return Euler((base.x + dx, base.y + dy, base.z + dz))


def _lerp(a, b, t):
    return a + (b - a) * t


def water_surface(ch, kind):
    if kind == "desert":
        return -2.2 + ch["flood"] * 2.6 + ch["water"] * 0.4
    if kind == "coast":
        return 0.05 + ch["flood"] * 1.35 + ch["water"] * 3.1
    if kind == "farm":
        return 0.02 + ch["flood"] * 0.9 + ch["water"] * 0.8
    # Capped under the quay. The mesh itself is only the river polygon.
    return city_water_top(ch["flood"], ch["water"])


def _sink(item, ch, loc):
    if item.extra.get("sink"):
        loc.z -= ch["geology"] * 180.0
    return loc


def _bury_scale(item, ch):
    if not item.extra.get("sink"):
        return 1.0
    return max(0.001, 1.0 - ch["geology"] * 1.08)


def _veg_scale(item, ch):
    wilt = ch["wilt"]
    heat = ch["heat"]
    if item.extra.get("future"):
        grow = smoother(item.extra.get("delay", 0.0), item.extra.get("delay", 0.0) + 0.22, ch["vegetation"])
    else:
        grow = 1.0 + 0.85 * ch["vegetation"]
    grow *= 1.0 - 0.88 * wilt
    grow *= 1.0 - 0.65 * heat
    grow *= 1.0 + 0.7 * ch["gravity"]
    return max(0.0, grow)


def _set_building_decay(amount):
    """Broken windows and grime. The value node is absent on day-1-only materials."""
    import bpy

    for material in bpy.data.materials:
        if not material.get("decay_hook") or material.node_tree is None:
            continue
        node = material.node_tree.nodes.get("Decay")
        if node is not None:
            node.outputs[0].default_value = float(amount)


def _drive_tint(mesh, color):
    """Write the rust color into the multiply node. Object Info does not update on these meshes."""
    for slot in mesh.material_slots:
        material = slot.material
        if material is None or not material.get("object_tint") or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type != "MIX_RGB" or node.blend_type != "MULTIPLY":
                continue
            sock = node.inputs["Color2"]
            while sock.is_linked:
                material.node_tree.links.remove(sock.links[0])
            sock.default_value = color


def _paint_descendants(obj, color, drive_nodes=False):
    if getattr(obj, "type", "") == "MESH":
        obj.color = color
        if drive_nodes:
            _drive_tint(obj, color)
    for child in obj.children:
        _paint_descendants(child, color, drive_nodes)


def _crumple_nose(empty):
    """Push the nose down and back. The mesh copy stays unique to this hero."""
    nose = empty.matrix_world.to_quaternion() @ Vector((1.0, 0.0, 0.0))
    for obj in empty.children_recursive:
        if obj.type != "MESH" or obj.data is None:
            continue
        if "vine" in obj.name or "moss" in obj.name or "sapling" in obj.name:
            continue
        world_pts = [obj.matrix_world @ vert.co for vert in obj.data.vertices]
        if not world_pts:
            continue
        projections = [(point - empty.matrix_world.translation).dot(nose) for point in world_pts]
        lo, hi = min(projections), max(projections)
        span = max(hi - lo, 1e-4)
        inverse = obj.matrix_world.inverted()
        for vert, proj, point in zip(obj.data.vertices, projections, world_pts):
            t = (proj - lo) / span
            if t < 0.8:
                continue
            dent = t - 0.8
            point = point - nose * dent * 0.7
            point.z -= dent * 0.45
            vert.co = inverse @ point


def _kill_emission(obj, amount):
    for mesh in [obj, *list(getattr(obj, "children_recursive", []))]:
        if getattr(mesh, "type", "") != "MESH":
            continue
        for slot in mesh.material_slots:
            material = slot.material
            if material is None or material.node_tree is None:
                continue
            bsdf = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
            if bsdf is None or "Emission Strength" not in bsdf.inputs:
                continue
            socket = bsdf.inputs["Emission Strength"]
            if "emit0" not in material:
                material["emit0"] = float(socket.default_value)
            socket.default_value = float(material["emit0"]) * (1.0 - amount)


def apply(kit, ch, frame, fps):
    kind = kit.kind
    collapse = ch["collapse"]
    ice = ch["ice"]
    snow = max(ch["snow"], ice * 0.95)
    veg = ch["vegetation"]
    # Year 1 (vegetation ~0.30) already breaks patches of windows. Later years go dark.
    _set_building_decay(smoother(0.08, 0.55, veg))
    # Water.
    if kit.water is not None:
        z = water_surface(ch, kind)
        seabed = -2.45 if kind == "coast" else (0.0 if kind == "desert" else -5.0)
        obj = kit.water.obj
        if z < seabed + 0.08:
            obj.hide_render = True
        else:
            obj.hide_render = False
            obj.location.z = z
    _structures(kit, ch, frame, fps)
    _life(kit, ch, frame, fps, snow)
    _bridge(kit, ch)
    _weather_fx(kit, ch, frame, fps, snow)
    _sky(kit, ch, frame, fps)
    if getattr(kit, "format", "A") == "C":
        from engine.format_c import apply_format_c

        apply_format_c(kit, ch, frame, fps)


def _structures(kit, ch, frame, fps):
    collapse = ch["collapse"]
    for item in kit.items:
        role = item.role
        obj = item.obj
        if role == "building_base":
            loc = _sink(item, ch, item.base_loc.copy())
            # Shrink to a concrete stump. A few marked skeletons stay standing.
            ruin = smoother(0.40, 0.92, collapse)
            stump = 1.0 - ruin * (0.55 if item.extra.get("skeleton") else 0.78)
            bury = _bury_scale(item, ch)
            obj.location = loc
            obj.scale = (
                item.base_scale.x * bury,
                item.base_scale.y * bury,
                item.base_scale.z * max(0.18, stump) * bury,
            )
            obj.hide_render = bury < 0.05
        elif role == "building_top":
            loc = item.base_loc.copy()
            fall = item.extra.get("fall_at")
            u = smoother(fall, fall + 0.2, collapse) if fall is not None else 0.0
            top_h = float(item.extra.get("top_h") or 8.0)
            rot = _euler(item.base_rot, dx=u * 1.7)
            # The hinge drops to the ground so the piece lands instead of hanging in the air.
            loc.z = item.base_loc.z * (1.0 - u) + (loc.z * 0 + 1.15) * u
            loc.y -= u * top_h * 0.42
            loc = _sink(item, ch, loc)
            obj.location = loc
            obj.rotation_euler = rot
            bury = _bury_scale(item, ch)
            obj.scale = item.base_scale * bury
            obj.hide_render = bury < 0.04
        elif role == "house":
            u = smoother(0.18 + item.extra["index"] * 0.03, 0.34 + item.extra["index"] * 0.03, collapse)
            # Snow load helps roofs and walls fail.
            u = max(u, smoother(0.45, 0.85, ch["snow"]) * 0.65)
            loc = item.base_loc.copy()
            loc.z -= u * 0.55
            loc = _sink(item, ch, loc)
            obj.location = loc
            obj.rotation_euler = _euler(item.base_rot, dx=u * 0.9, dz=u * 0.25)
        elif role == "house_roof":
            u = smoother(0.16 + item.extra["index"] * 0.03, 0.32 + item.extra["index"] * 0.03, collapse)
            u = max(u, smoother(0.35, 0.8, ch["snow"]))
            loc = item.base_loc.copy()
            loc.z -= u * 1.1
            loc.y += u * 0.9
            obj.location = loc
            obj.rotation_euler = _euler(item.base_rot, dx=u * 1.7)
        elif role == "food":
            u = max(ch["sag"], ch["wilt"] * 0.5)
            loc = item.base_loc.copy()
            loc.z -= u * (0.04 + 0.03 * item.extra.get("index", 0))
            obj.location = loc
            obj.rotation_euler.z = u * 0.15 * (1 if item.extra.get("index", 0) % 2 == 0 else -1)
        elif role == "road_slab":
            u = smoother(0.05 + item.extra["index"] * 0.04, 0.16 + item.extra["index"] * 0.04, collapse)
            loc = item.base_loc.copy()
            loc.z -= u * 0.7
            obj.location = loc
            obj.rotation_euler = _euler(item.base_rot, dx=u * 0.9)
        elif role == "strata":
            g = ch["geology"]
            obj.hide_render = g < 0.04
            loc = item.base_loc.copy()
            loc.z -= (1.0 - g) * 9.0
            obj.location = loc
        elif role == "glacier":
            u = ch["ice"]
            obj.hide_render = u < 0.05
            loc = item.base_loc.copy()
            loc.x -= (1.0 - u) * 12.0
            obj.location = loc
            s = max(0.001, u)
            obj.scale = (item.base_scale.x * s, item.base_scale.y * s, item.base_scale.z * s)
        elif role == "ship":
            z = water_surface(ch, kit.kind)
            draft = item.extra.get("draft", 0.8)
            loc = item.base_loc.copy()
            loc.z = max(-2.35, z - draft)
            # Low gravity lets hulls ride higher and bob.
            loc.z += ch["gravity"] * 0.45
            loc.z += math.sin(frame * 0.08 + loc.x) * ch["gravity"] * 0.15
            obj.location = loc
        elif role == "smoke":
            grid = ch["power_grid"]
            phase = (frame / max(fps, 1) * 0.28 + item.extra.get("phase", 0.0)) % 1.0
            loc = item.base_loc.copy()
            loc.z += phase * 6.5
            loc = _sink(item, ch, loc)
            puff = max(0.0, (1.0 - phase) * grid)
            obj.hide_render = puff < 0.04
            obj.location = loc
            obj.scale = (puff, puff, puff * 1.3)
        elif role == "flame":
            if item.extra.get("outage"):
                s = ch["power"] * (1.0 - smoother(0.15, 0.55, ch["vegetation"]))
                obj.hide_render = s < 0.04
                flicker = 0.85 + 0.15 * math.sin(frame * 0.9)
                obj.scale = item.base_scale * max(s * flicker, 0.001)
            else:
                s = max(ch["fire"], ch["heat"] * 0.55)
                obj.hide_render = s < 0.04
                flicker = 0.75 + 0.25 * math.sin(frame * 0.7 + item.extra["index"])
                obj.scale = (s * flicker, s * flicker, s * 1.4 * flicker)
        elif role == "crack":
            s = max(ch["heat"], ch["scorch"], ch["dry"] if "dry" in ch else 0.0)
            obj.hide_render = s < 0.08
            obj.scale = (1 + s * 2.0, 0.4 + s * 2.5, 1)


def _life(kit, ch, frame, fps, snow):
    cars = [item for item in kit.items if item.role == "car"]
    mounds = [item for item in kit.items if item.role == "mound"]
    for item in kit.items:
        role = item.role
        obj = item.obj
        if role == "tree_canopy":
            grow = _veg_scale(item, ch)
            ice = ch["ice"]
            s = grow * (1.0 - 0.94 * ice)
            obj.hide_render = s < 0.03
            obj.scale = item.base_scale * s
            leaf = Vector(item.extra.get("leaf", (0.3, 0.55, 0.2, 1))[:3])
            autumn = Vector(item.extra.get("autumn", (0.7, 0.4, 0.12, 1))[:3])
            mix = clamp(ch["geology"] * 1.1 + ch["wilt"] * 0.8 + ch["heat"] * 0.7 + max(0.0, ch.get("season", 0.35) - 0.55))
            col = leaf.lerp(autumn, mix)
            if ice > 0.2:
                col = col.lerp(Vector((0.55, 0.5, 0.46)), ice)
            obj.color = (col.x, col.y, col.z, 1)
            sway = math.sin(frame * 0.11 + obj.location.x) * (0.015 + 0.14 * ch.get("wind", 0.0)) * (1 + ch["gravity"])
            obj.rotation_euler = _euler(item.base_rot, dz=sway)
        elif role == "tree_bare":
            grow = _veg_scale(item, ch) if item.extra.get("future") else 1.0
            s = grow * ch["ice"]
            obj.hide_render = s < 0.04
            obj.scale = (s, s, s)
        elif role == "tree_trunk":
            grow = _veg_scale(item, ch) if item.extra.get("future") else 1.0
            obj.hide_render = grow < 0.04
            obj.scale = item.base_scale * max(grow, 0.001)
        elif role in ("weed", "crop", "flower"):
            if role == "weed":
                s = smoother(item.extra.get("delay", 0.0), item.extra.get("delay", 0.0) + 0.2, ch["vegetation"])
                s *= 1.0 - 0.9 * ch["wilt"]
            else:
                s = (1.0 - 0.94 * ch["wilt"]) * (1.0 - 0.8 * ch["heat"])
                s *= 1.0 + 0.45 * ch["vegetation"] * (0 if role == "flower" else 0.2)
            obj.hide_render = s < 0.03
            obj.scale = item.base_scale * max(s, 0.001)
            if "leaf" in item.extra:
                leaf = Vector(item.extra["leaf"][:3])
                dead = Vector((0.4, 0.28, 0.14))
                col = leaf.lerp(dead, clamp(ch["wilt"] * 0.9 + ch["heat"] * 0.6))
                obj.color = (col.x, col.y, col.z, 1)
        elif role == "person":
            s = 1.0 - smoother(0.0, 0.2, ch["vanish"])
            obj.hide_render = s < 0.03
            lift = ch["gravity"] * item.extra.get("float", 0.0)
            bob = math.sin(frame * 0.18 + obj.location.x) * ch["gravity"] * item.extra.get("bob", 0.0)
            loc = item.base_loc.copy()
            loc.z += lift + bob
            obj.location = loc
            obj.scale = item.base_scale * max(s, 0.001)
        elif role == "car":
            # People vanish. Cars roll to a stop and stay, then rust where they stopped.
            u = smoother(0.0, 1.0, clamp(ch["vanish"] / 0.55))
            a = Vector(item.extra["path_from"])
            b = Vector(item.extra["path_to"])
            pos = a.lerp(b, u)
            rust = ch["rust"]
            veg = ch["vegetation"]
            hero = bool(item.extra.get("hero"))
            grime_u = max(rust, smoother(0.05, 0.4, veg) * 0.7)
            flat = 1.0 - (0.22 if hero else 0.62) * smoother(0.28, 0.92, rust)
            bury = 0.7 * smoother(0.5, 1.0, max(rust, veg if veg > 0.85 else 0.0))
            if hero:
                bury = 0.06 * rust
                if rust > 0.72 and not obj.get("nose_crumpled"):
                    _crumple_nose(obj)
                    obj["nose_crumpled"] = True
            gone = (not hero) and rust > 0.9
            pos.z -= snow * 0.32 + bury
            pos.z += ch["gravity"] * item.extra.get("float", 0.0)
            obj.location = pos
            obj.scale = (item.base_scale.x, item.base_scale.y, item.base_scale.z * max(flat, 0.2))
            obj.hide_render = gone
            for child in obj.children:
                if child.get("role") not in ("weed", "tree_canopy"):
                    child.hide_render = gone
            paint = Vector(item.extra.get("paint", (1.0, 1.0, 1.0))[:3])
            if hero:
                # Darken the factory paint. A red or gold Miura still reads through the rust.
                husk = Vector((1.0, 1.0, 1.0)).lerp(Vector((0.32, 0.18, 0.11)), min(1.0, grime_u * 0.85))
            else:
                husk = Vector((1.0, 1.0, 1.0)).lerp(Vector((0.18, 0.11, 0.07)), grime_u)
            _paint_descendants(obj, (husk.x, husk.y, husk.z, 1.0), drive_nodes=hero)
            askew = 0.35 if veg > 0.15 and not hero else 0.08
            yaw = item.base_rot.z + grime_u * (askew if item.extra.get("index", 0) % 2 == 0 else -askew)
            obj.rotation_euler = _euler(item.base_rot, dz=yaw - item.base_rot.z)
        elif role == "bird":
            gone = max(ch["fauna"], smoother(0.15, 0.45, ch["vanish"]))
            s = 1.0 - gone
            loc = item.base_loc.copy()
            loc.z += gone * 6.0 + math.sin(frame * 0.2 + item.extra.get("phase", 0)) * 0.2
            loc.z += ch["gravity"] * item.extra.get("float", 0.0)
            obj.location = loc
            obj.hide_render = s < 0.03
            obj.scale = item.base_scale * max(s, 0.001)
        elif role == "animal":
            s = 1.0 - smoother(0.1, 0.55, ch["fauna"])
            obj.hide_render = s < 0.03
            obj.scale = item.base_scale * max(s, 0.001)
        elif role == "mascot":
            obj.hide_render = ch["vegetation"] > 0.65 or ch["ice"] > 0.2 or ch["geology"] > 0.15
        elif role == "road_mark":
            # Year 100 fragments the paint. Year 500 removes it.
            veg = ch["vegetation"]
            frag = smoother(0.5, 0.88, veg)
            bucket = abs(hash(obj.name)) % 100
            obj.hide_render = veg > 0.9 or bucket < frag * 62.0
            for child in obj.children:
                child.hide_render = obj.hide_render
        elif role == "blanket":
            obj.hide_render = ch["vegetation"] < 0.7
        elif role == "frontage":
            # The same building stays. A few lean as the top gives way.
            lean = 0.0
            if int(item.extra.get("index", 0)) % 17 == 0:
                lean = smoother(0.55, 0.95, ch["collapse"]) * 0.22
            obj.rotation_euler = _euler(item.base_rot, dx=lean)
            obj.hide_render = False
        elif role == "rubble":
            s = smoother(0.48, 0.82, ch["collapse"])
            obj.hide_render = s < 0.08
            obj.scale = item.base_scale * max(s, 0.001)
        elif role == "prop" and "signal" in obj.name:
            u = smoother(0.35, 0.8, ch["vegetation"])
            obj.rotation_euler = _euler(item.base_rot, dx=u * 1.35)
            obj.location = item.base_loc
            _kill_emission(obj, u)
        elif role == "forest_floor":
            # Day 1 stays city-grey on the far bank. Meadow, then forest floor.
            obj.hide_render = ch["vegetation"] < 0.22
        elif role == "ruin":
            # Full size once the collapse is underway. Scaling it up reads as a toy.
            s = smoother(0.35, 0.72, ch["collapse"])
            obj.hide_render = s < 0.08
            obj.scale = item.base_scale
            for child in obj.children:
                child.hide_render = obj.hide_render
        elif role == "wear":
            s = smoother(0.06, 0.28, ch["vegetation"])
            obj.hide_render = s < 0.04
            obj.scale = item.base_scale * max(s, 0.001)
        elif role == "prop":
            loc = item.base_loc.copy()
            loc.z += ch["gravity"] * item.extra.get("float", 0.0)
            tilt = smoother(0.45, 0.9, ch["collapse"])
            obj.location = loc
            fallen = 1.25 if "lamp" in obj.name else 0.0
            obj.rotation_euler = _euler(item.base_rot, dx=tilt * fallen)
            obj.hide_render = False
    for mound, car in zip(mounds, cars):
        if snow < 0.18:
            mound.obj.hide_render = True
            continue
        mound.obj.hide_render = False
        mound.obj.location = car.obj.matrix_world.translation + Vector((0, 0, 0.45 * snow))
        mound.obj.scale = (0.7 * snow, 1.1 * snow, 0.45 * snow)


def _bridge(kit, ch):
    bridge = kit.bridge
    if not bridge:
        return
    poses = []
    for item in bridge["decks"]:
        i = item.extra["i"]
        loc = item.base_loc.copy()
        droop = ch["sag"] * (4.5 if i == 0 else 1.2) + ch["gravity"] * 0.15
        loc.z -= droop
        rot = _euler(item.base_rot)
        if i in (1, 2):
            # Hidden while the continuous deck is whole. Later they are the wreckage in the river.
            u = smoother(0.62 + (i - 1) * 0.04, 0.86 + (i - 1) * 0.03, ch["collapse"])
            rot.x += u * (0.9 if i == 1 else -1.05)
            loc.z -= u * 9.2
            hidden = u < 0.08
            item.obj.hide_render = hidden
            for child in item.obj.children:
                child.hide_render = hidden
        elif i == 0:
            # The river span settles into the water. It does not slide onto the far bank.
            u = smoother(0.55, 0.92, ch["collapse"])
            rot.x += u * 0.62
            loc.z = item.base_loc.z * (1.0 - u) + 0.15 * u
            item.obj.hide_render = False
            for child in item.obj.children:
                child.hide_render = "car" not in child.name and u > 0.45
        elif i == 4:
            u = smoother(0.75, 1.0, ch["collapse"])
            loc.z -= u * 0.12
            item.obj.hide_render = False
            for child in item.obj.children:
                child.hide_render = "car" not in child.name and ch["vegetation"] > 0.92
        else:
            item.obj.hide_render = False
            for child in item.obj.children:
                child.hide_render = ch["vegetation"] > 0.5 or ch["collapse"] > 0.7
        if item.extra.get("sink"):
            loc.z -= ch["geology"] * 180.0
        item.obj.location = loc
        item.obj.rotation_euler = rot
        bury = _bury_scale(item, ch)
        item.obj.scale = item.base_scale * bury
        poses.append((item, loc, rot))
    tower_pts = []
    for item in bridge["towers"]:
        i = item.extra["i"]
        loc = item.base_loc.copy()
        rot = _euler(item.base_rot)
        rot.z += ch["sag"] * (0.04 if i == 0 else -0.05)
        if i == 1:
            u = smoother(0.75, 0.98, ch["collapse"])
            rot.x += u * 0.25
            loc.z -= u * 6.0
        else:
            u = smoother(0.9, 1.0, ch["collapse"])
            rot.z += u * 0.05
        if item.extra.get("sink"):
            loc.z -= ch["geology"] * 180.0
        item.obj.location = loc
        item.obj.rotation_euler = rot
        item.obj.scale = item.base_scale * _bury_scale(item, ch)
        q = rot.to_quaternion()
        h = item.extra["height"]
        w = item.extra["width"] / 2
        left = Vector(loc) + q @ Vector((-w, 0, h))
        right = Vector(loc) + q @ Vector((w, 0, h))
        tower_pts.append((left, right))
    # Anchors sag and sink with the bridge.
    geology = ch["geology"]
    sag = ch["sag"] + ch["collapse"] * 0.4
    anchors = []
    for ax, ay, az in bridge["anchors"]:
        anchors.append(Vector((ax, ay, az - sag * 1.2 - geology * 180.0)))
    if len(tower_pts) < 2:
        return
    ya = bridge["towers"][0].base_loc.y
    yb = bridge["towers"][1].base_loc.y
    span = max(1.0, abs(yb - ya))
    sag = span / 8.5
    snap = smoother(0.66, 0.9, ch["collapse"])
    half = float(bridge.get("half", 7.6))
    sides = []
    for sidx in (0, 1):
        near_a = anchors[sidx]
        far_a = anchors[2 + sidx]
        top_a = tower_pts[0][sidx]
        top_b = tower_pts[1][sidx]
        back_n = _catenary(near_a, top_a, 1.4, 6)
        main = _catenary(top_a, top_b, sag, 14)
        # One side snaps: the main cable leaves the near tower and hangs into the river.
        if sidx == 0 and snap > 0.04:
            hung = []
            for i, p in enumerate(main):
                t = i / max(1, len(main) - 1)
                if t > 0.55:
                    hung.append(Vector((p.x, p.y, -80.0)))
                else:
                    drop = top_a.lerp(Vector((top_a.x, (ya + yb) * 0.5, 1.2)), t / 0.55)
                    hung.append(Vector((p.x, p.y, (1.0 - snap) * p.z + snap * drop.z)))
            main = hung
        back_f = _catenary(top_b, far_a, 1.2, 5)
        curve = back_n + main[1:] + back_f[1:]
        sides.append(curve)
        cables = bridge["cables"][sidx * 36 : (sidx + 1) * 36]
        pairs = list(zip(curve, curve[1:]))
        for seg, pair in zip(cables, pairs):
            a, b = pair
            if a.z < -20 or b.z < -20:
                seg.hide_render = True
                continue
            aim_z(seg, a, b, 0.16)
        for seg in cables[len(pairs) :]:
            seg.hide_render = True
    count = len(bridge["suspenders"])
    per = max(1, count // 2)
    for n, sus in enumerate(bridge["suspenders"]):
        side = 0 if n < per else 1
        k = n if side == 0 else n - per
        t = k / max(1, per - 1)
        y = _lerp(ya + 3.0, yb - 3.0, t)
        curve = sides[side]
        top = _sample_curve_y(curve, y)
        deck = _deck_edge(poses, y, -half if side == 0 else half)
        if top is None or deck is None or top.z < -20 or (side == 0 and snap > 0.75):
            sus.hide_render = True
            continue
        sus.hide_render = False
        aim_z(sus, top, deck, 0.07)


def _catenary(a, b, sag, n):
    pts = []
    a = Vector(a)
    b = Vector(b)
    for i in range(n + 1):
        t = i / max(1, n)
        p = a.lerp(b, t)
        p.z -= sag * 4.0 * t * (1.0 - t)
        pts.append(p)
    return pts


def _span_points(pts, sags, count):
    # pts: 4 points, 3 spans.
    out = []
    spans = list(zip(pts, pts[1:], sags))
    per = max(2, count // len(spans))
    for a, b, sag in spans:
        for i in range(per):
            t = i / per
            p = Vector(a).lerp(Vector(b), t)
            p.z -= sag * 4 * t * (1 - t)
            out.append(p)
    out.append(Vector(pts[-1]))
    return out


def _sample_curve_y(curve, y):
    best = None
    best_d = 1e9
    for p in curve:
        d = abs(p.y - y)
        if d < best_d:
            best_d = d
            best = p
    return best


def _deck_edge(poses, y, x_local):
    for item, loc, rot in poses:
        half = item.extra.get("length", 4) / 2
        if abs(y - item.base_loc.y) <= half + 0.3:
            q = rot.to_quaternion()
            local_y = y - item.base_loc.y
            return Vector(loc) + q @ Vector((x_local, local_y, 0.2))
    return None


def _weather_fx(kit, ch, frame, fps, snow):
    if kit.volume is not None:
        density = ch["ice"] * 0.012 + ch["dust"] * 0.01 + ch["ash"] * 0.008 + ch["rain"] * 0.004 + ch.get("fog", 0.0) * 0.01
        kit.volume.hide_render = density < 0.0008
        fog = kit.volume.data.materials[0].node_tree.nodes.get("Fog")
        if fog:
            if ch["dust"] + ch["heat"] > ch["ice"]:
                fog.inputs["Color"].default_value = lin(0.72, 0.58, 0.40)
            elif ch["ash"] > 0.2:
                fog.inputs["Color"].default_value = lin(0.35, 0.35, 0.36)
            else:
                fog.inputs["Color"].default_value = lin(0.78, 0.84, 0.9)
    t = frame / max(fps, 1)
    for kind, obj, index in kit.precip:
        if kind == "rain":
            amount = ch["rain"]
        elif kind == "snow":
            amount = snow
        elif kind == "dust":
            amount = max(ch["dust"], ch["heat"] * 0.45)
        else:
            amount = max(ch["ash"], ch["fire"] * 0.6)
        if amount < 0.04:
            obj.hide_render = True
            continue
        obj.hide_render = False
        column = index % 10
        row = (index // 10) % 8
        x = -20 + column * 4.4 + (index % 3) * 0.4 + ch.get("wind", 0.0) * (6.0 if kind == "rain" else 2.5)
        y = -16 + row * 5.5
        speed = 9.0 if kind == "rain" else 1.6 if kind == "snow" else 0.8
        phase = (t * speed + index * 0.17) % 1.0
        z = 14.0 * (1.0 - phase)
        if kind == "dust":
            x += math.sin(t + index) * 1.5
            z = 1.0 + phase * 6.0
        obj.location = (x, y, z)
        if kind == "rain":
            obj.scale = (1, 1, 0.6 + amount)
        else:
            s = 0.6 + amount
            obj.scale = (s, s, s)


def _sky(kit, ch, frame, fps):
    dn = ch["day_night"]
    # 0.16 noon-ish, ~0.5 sunset, ~0.78 night.
    if dn < 0.42:
        u = clamp((dn - 0.12) / 0.3)
        elev = _lerp(1.05, 1.22, u)
        # The HDRI is the fill. The sun is a cooler, weaker key with a wide angle.
        energy = _lerp(5.2, 2.4, u)
        color = Vector(lin(1.0, 0.96, 0.88)[:3]).lerp(Vector(lin(1.0, 0.72, 0.48)[:3]), u)
        sky = Vector(lin(0.42, 0.64, 0.95)[:3]).lerp(Vector(lin(0.98, 0.62, 0.38)[:3]), u * 0.75)
        horizon = Vector(lin(0.96, 0.90, 0.78)[:3]).lerp(Vector(lin(0.98, 0.55, 0.32)[:3]), u)
        sky_e = _lerp(1.15, 0.85, u)
        fill = 0.22
        # Mostly the clear HDRI, with a warm horizon so the sky is not a grey slab.
        sky_mix = _lerp(0.18, 0.45, u)
    elif dn < 0.68:
        u = clamp((dn - 0.42) / 0.26)
        elev = _lerp(1.15, 1.72, u)
        energy = _lerp(2.1, 0.12, u)
        color = Vector(lin(1.0, 0.62, 0.32)[:3]).lerp(Vector(lin(0.55, 0.68, 1.0)[:3]), u)
        sky = Vector(lin(0.95, 0.55, 0.35)[:3]).lerp(Vector((0.015, 0.02, 0.045)), u)
        sky_e = _lerp(0.7, 0.28, u)
        horizon = sky
        fill = _lerp(0.18, 0.12, u)
        sky_mix = _lerp(0.55, 1.0, u)
    else:
        u = clamp((dn - 0.68) / 0.2)
        elev = _lerp(1.72, 0.8, u)
        energy = _lerp(0.12, 3.3, u)
        color = Vector(lin(0.55, 0.68, 1.0)[:3]).lerp(Vector(lin(1.0, 0.97, 0.92)[:3]), u)
        sky = Vector((0.015, 0.02, 0.045)).lerp(Vector(lin(0.64, 0.76, 0.88)[:3]), u)
        sky_e = _lerp(0.28, 0.95, u)
        horizon = sky
        fill = _lerp(0.12, 0.2, u)
        sky_mix = 1.0
    # Heat haze warms the sky. Dust desaturates it.
    if ch["heat"] > 0.01:
        sky = sky.lerp(Vector(lin(0.95, 0.72, 0.45)[:3]), ch["heat"] * 0.65)
        sky_e *= 1.0 + ch["heat"] * 0.15
    if ch["dust"] > 0.01:
        sky = sky.lerp(Vector(lin(0.72, 0.62, 0.48)[:3]), ch["dust"] * 0.5)
    kit.sun.rotation_euler = Euler((elev, 0.08, -0.85))
    kit.sun.data.energy = energy
    kit.sun.data.angle = 0.06 if dn < 0.42 else (0.1 if dn > 0.68 else 0.2)
    kit.sun.data.color = (color.x, color.y, color.z)
    kit.fill.data.energy = fill * (1.0 - 0.3 * ch["ice"])
    if kit.world_bg:
        kit.world_bg.inputs[1].default_value = sky_e
    if getattr(kit, "sky_zenith", None) is not None:
        kit.sky_zenith.outputs[0].default_value = (sky.x, sky.y, sky.z, 1)
        kit.sky_horizon.outputs[0].default_value = (horizon.x, horizon.y, horizon.z, 1)
    if getattr(kit, "sky_mix", None) is not None:
        kit.sky_mix.inputs["Fac"].default_value = sky_mix
