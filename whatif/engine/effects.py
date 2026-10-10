"""Effect library. Every effect is driven by a 0..1 channel (water may be signed)."""

from __future__ import annotations

import math

from mathutils import Euler, Vector

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
    # The park and cross street stay dry. Only the quay and subway flood.
    return 0.18 + ch["flood"] * 0.42 + ch["water"] * 1.15


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


def apply(kit, ch, frame, fps):
    kind = kit.kind
    collapse = ch["collapse"]
    ice = ch["ice"]
    snow = max(ch["snow"], ice * 0.95)
    veg = ch["vegetation"]
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
            # Late collapse removes the shaft. Squashing the mesh turns the windows into a cage.
            ruin = smoother(0.62, 0.92, collapse)
            bury = _bury_scale(item, ch)
            obj.location = loc
            obj.scale = item.base_scale * bury
            obj.hide_render = ruin > 0.9 or bury < 0.05
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
            u = smoother(0.0, 1.0, clamp(ch["vanish"] / 0.55))
            a = Vector(item.extra["path_from"])
            b = Vector(item.extra["path_to"])
            pos = a.lerp(b, u)
            fade = 1.0 - smoother(0.78, 1.0, ch["vanish"])
            pos.z -= snow * 0.32
            pos.z += ch["gravity"] * item.extra.get("float", 0.0)
            pos.z += math.sin(frame * 0.16 + pos.x) * ch["gravity"] * item.extra.get("bob", 0.0)
            obj.location = pos
            obj.scale = item.base_scale * max(fade, 0.001)
            obj.hide_render = fade < 0.03
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
        elif role == "prop":
            loc = item.base_loc.copy()
            loc.z += ch["gravity"] * item.extra.get("float", 0.2)
            obj.location = loc
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
        droop = (ch["sag"] * 0.55 + ch["gravity"] * 0.15) * (0.55 if i in (1, 2) else 0.12)
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
            u = smoother(0.9, 1.0, ch["collapse"])
            rot.x += u * 0.06
            loc.z -= u * 0.4
            item.obj.hide_render = False
        else:
            item.obj.hide_render = False
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
    sag = span / 10.0
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
            aim_z(seg, a, b, 0.28)
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
        aim_z(sus, top, deck, 0.11)


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
        elev = _lerp(1.15, 1.28, u)
        energy = _lerp(5.2, 2.6, u)
        color = Vector(lin(1.0, 0.86, 0.68)[:3]).lerp(Vector(lin(1.0, 0.55, 0.28)[:3]), u)
        sky = Vector(lin(0.58, 0.74, 0.90)[:3]).lerp(Vector(lin(0.98, 0.62, 0.38)[:3]), u * 0.75)
        sky_e = _lerp(0.85, 0.7, u)
        fill = 0.16
    elif dn < 0.68:
        u = clamp((dn - 0.42) / 0.26)
        elev = _lerp(1.15, 1.72, u)
        energy = _lerp(2.1, 0.12, u)
        color = Vector(lin(1.0, 0.62, 0.32)[:3]).lerp(Vector(lin(0.55, 0.68, 1.0)[:3]), u)
        sky = Vector(lin(0.95, 0.55, 0.35)[:3]).lerp(Vector((0.015, 0.02, 0.045)), u)
        sky_e = _lerp(0.7, 0.28, u)
        fill = _lerp(0.4, 0.32, u)
    else:
        u = clamp((dn - 0.68) / 0.2)
        elev = _lerp(1.72, 0.8, u)
        energy = _lerp(0.12, 3.3, u)
        color = Vector(lin(0.55, 0.68, 1.0)[:3]).lerp(Vector(lin(1.0, 0.97, 0.92)[:3]), u)
        sky = Vector((0.015, 0.02, 0.045)).lerp(Vector(lin(0.64, 0.76, 0.88)[:3]), u)
        sky_e = _lerp(0.28, 0.95, u)
        fill = _lerp(0.32, 0.45, u)
    # Heat haze warms the sky. Dust desaturates it.
    if ch["heat"] > 0.01:
        sky = sky.lerp(Vector(lin(0.95, 0.72, 0.45)[:3]), ch["heat"] * 0.65)
        sky_e *= 1.0 + ch["heat"] * 0.15
    if ch["dust"] > 0.01:
        sky = sky.lerp(Vector(lin(0.72, 0.62, 0.48)[:3]), ch["dust"] * 0.5)
    kit.sun.rotation_euler = Euler((elev, 0.08, -0.85))
    kit.sun.data.energy = energy
    kit.sun.data.angle = 0.08 if dn > 0.68 else 0.5
    kit.sun.data.color = (color.x, color.y, color.z)
    kit.fill.data.energy = fill * (1.0 - 0.3 * ch["ice"])
    if kit.world_bg:
        kit.world_bg.inputs[0].default_value = (sky.x, sky.y, sky.z, 1)
        kit.world_bg.inputs[1].default_value = sky_e
