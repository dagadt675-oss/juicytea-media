"""River-city layout that does not need Blender.

The bridge is a straight line in s. s = 0 is where the deck finishes climbing
and runs level. Negative s is the approach street, which lands on the
foreground cross street. Blender's XYZ euler maps a mesh's local +Y to
(-sin(theta), cos(theta)), so the mesh yaw is the negation of the line's yaw.
Using the line yaw directly puts the deck on the mirror line and the towers
beside it.
"""

from __future__ import annotations

import math

# Yaw sets the deck's screen slope. 2.5° reads as about 58° from horizontal
# in the locked camera; zenith's centerline is 56.9°.
BRIDGE_YAW = math.radians(2.5)
DECK_ROT_Z = -BRIDGE_YAW
DECK_ORIGIN = (4.1, 79.0)
# Object-index measurement, not a guess: 15.2 m is 22.6% of the frame at the
# near bank and 30.4% on the lower deck. Zenith is 22.2% and 30.0%.
DECK_W = 15.2
DECK_HALF = DECK_W / 2.0
DECK_Z = 4.6
SOUTH_Z = 0.62
# Leg centers plus leg thickness. The near portal's outer width measures 18.0%
# of the frame where the legs meet the deck; zenith is 18.0%.
TOWER_W = 15.7
TOWER_LEG = 1.5
# Object-index ids for the opening metric. Cables and the pier stay at 0.
INDEX_DECK = 2
INDEX_CANOPY = 3
INDEX_PORTAL = 11
# Both portals are over the water, on the level deck.
TOWER_S = (32.0, 102.0)
# Foreground road the approach must join. The road plane is centered at y=14
# and is still asphalt here. y=22 sits in the lower part of the frame.
CROSS_Y = 22.0
CROSS_HALF_Y = 8.0
CROSS_X0 = -80.0
CROSS_X1 = 90.0
LEVEL_S1 = 150.0
FAR_S = 185.0
FAR_Z = 1.8

# Grey, white, light blue, and salmon. The back row is lifted toward blue in the scene.
SKYLINE_COLORS = (
    (0.68, 0.76, 0.84, 1),
    (0.96, 0.96, 0.95, 1),
    (0.50, 0.68, 0.88, 1),
    (0.74, 0.78, 0.82, 1),
    (0.84, 0.36, 0.32, 1),
    (0.78, 0.42, 0.36, 1),
    (0.62, 0.78, 0.90, 1),
    (0.90, 0.48, 0.40, 1),
    (0.86, 0.86, 0.88, 1),
    (0.58, 0.72, 0.84, 1),
)
# Front row base is the solved skyline line (world y=168). Back row is tall
# enough to leave the top of the frame.
SKYLINE_ROWS = (
    (172.0, 22.0, 58.0, -150.0, 190.0, (4.2, 7.2)),
    (198.0, 36.0, 82.0, -160.0, 200.0, (3.8, 6.4)),
    (228.0, 64.0, 118.0, -140.0, 190.0, (3.4, 5.8)),
)

# Park paths. Cars must not sit on these.
PATHS = (
    ("v1", -42.0, 58.0, 1.4, 18.0),
    ("v2", -26.0, 58.0, 1.4, 18.0),
    ("v3", -10.0, 58.0, 1.4, 16.0),
    ("h1", -26.0, 42.0, 20.0, 1.2),
    ("h2", -26.0, 56.0, 20.0, 1.2),
    ("h3", -26.0, 70.0, 20.0, 1.2),
    ("plaza", -38.0, 60.0, 4.5, 4.5),
)
FOUNTAIN = (-38.0, 60.0)
# One eastbound row on the near road, clear of the bridge slab and the park paths.
FOREGROUND_CARS = (
    (-46.0, 14.5),
    (-32.0, 14.8),
    (-22.0, 14.4),
    (16.0, 14.6),
    (28.0, 14.9),
)
DECK_LANES = (-4.8, -1.6, 1.6, 4.8)


def deck_direction():
    return (math.sin(BRIDGE_YAW), math.cos(BRIDGE_YAW))


def right_vector():
    """World direction of a mesh's local +X at DECK_ROT_Z."""
    return (math.cos(DECK_ROT_Z), math.sin(DECK_ROT_Z))


def deck_point(s):
    dx, dy = deck_direction()
    return (DECK_ORIGIN[0] + s * dx, DECK_ORIGIN[1] + s * dy)


def deck_s_at_y(y):
    return (y - DECK_ORIGIN[1]) / math.cos(BRIDGE_YAW)


def south_s():
    return deck_s_at_y(CROSS_Y)


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def deck_z(s):
    """Smoothstep ramps so the slope is flat where it meets the level deck."""
    if s < 0.0:
        s0 = south_s()
        t = (s - s0) / (0.0 - s0)
        return SOUTH_Z + _smooth(t) * (DECK_Z - SOUTH_Z)
    if s > LEVEL_S1:
        t = (s - LEVEL_S1) / (FAR_S - LEVEL_S1)
        return DECK_Z + _smooth(t) * (FAR_Z - DECK_Z)
    return DECK_Z


def bridge_spans():
    """(index, s0, s1). 1 and 2 are the hidden wreckage copies.

    Spans meet at a shared s, where deck_z is continuous, so a vertical
    cross-section there is the same shape for both pieces.
    """
    return (
        (0, 0.0, LEVEL_S1),
        (1, 40.0, 72.0),
        (2, 70.0, 104.0),
        (3, LEVEL_S1, FAR_S),
        (4, south_s(), 0.0),
    )


def tower_pose(s):
    x, y = deck_point(s)
    return (x, y, 0.0), DECK_ROT_Z


def tower_legs(s):
    x, y = deck_point(s)
    rx, ry = right_vector()
    half = TOWER_W / 2.0
    return ((x - rx * half, y - ry * half), (x + rx * half, y + ry * half))


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def on_cross_street(x, y):
    return CROSS_X0 <= x <= CROSS_X1 and abs(y - CROSS_Y) <= CROSS_HALF_Y


def on_deck_road(x, y):
    s = deck_s_at_y(y)
    if s < south_s() - 0.4 or s > FAR_S + 0.4:
        return False
    cx, cy = deck_point(s)
    return abs(x - cx) <= DECK_HALF + 0.3 and abs(y - cy) < 0.6


def on_city_pad(x, y):
    """Far landing, where the deck comes down onto the far bank."""
    if y < 230.0:
        return False
    s = deck_s_at_y(y)
    cx, _cy = deck_point(s)
    return abs(x - cx) <= DECK_HALF + 6.0


def on_road(x, y):
    return on_cross_street(x, y) or on_deck_road(x, y) or on_city_pad(x, y)


def park_grass(x, y):
    in_park = 32.0 <= y <= 96.0 and -70.0 <= x <= 70.0
    return in_park and not on_road(x, y)


def _blender_rotate(local, pitch, yaw):
    x, y, z = local
    y1 = y * math.cos(pitch) - z * math.sin(pitch)
    z1 = y * math.sin(pitch) + z * math.cos(pitch)
    x2 = x * math.cos(yaw) - y1 * math.sin(yaw)
    y2 = x * math.sin(yaw) + y1 * math.cos(yaw)
    return (x2, y2, z1)


def span_mesh_error(s0, s1):
    """How far the rotated deck box ends from the centerline ends, in meters."""
    p0 = (*deck_point(s0), deck_z(s0))
    p1 = (*deck_point(s1), deck_z(s1))
    mid = tuple((a + b) / 2.0 for a, b in zip(p0, p1))
    horiz = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    length = math.hypot(horiz, p1[2] - p0[2])
    pitch = math.atan2(p1[2] - p0[2], max(horiz, 1e-6))
    err = 0.0
    for sign, target in ((1.0, p1), (-1.0, p0)):
        local = _blender_rotate((0.0, sign * length / 2.0, 0.0), pitch, DECK_ROT_Z)
        end = tuple(m + d for m, d in zip(mid, local))
        err = max(err, math.dist(end, target))
    return err


def _on_rect(x, y, rect):
    _name, cx, cy, hx, hy = rect
    return abs(x - cx) <= hx and abs(y - cy) <= hy


def layout_errors():
    """Empty when the bridge is a road and the portals straddle its centerline."""
    errors = []
    spans = bridge_spans()
    ends = []
    for index, s0, s1 in spans:
        err = span_mesh_error(s0, s1)
        if err > 0.5:
            errors.append(f"span {index} deck mesh is {err:.2f} m off the centerline")
        for s in (s0, s1):
            point = deck_point(s)
            ends.append((index, s, point))
            if park_grass(*point):
                errors.append(f"span {index} ends on grass at s={s:.1f}")
            if not on_road(*point):
                errors.append(f"span {index} end s={s:.1f} is not on a road")
    approach = next(span for span in spans if span[0] == 4)
    south = deck_point(approach[1])
    if not on_cross_street(*south):
        errors.append("approach deck does not land on the cross street")
    # The street is spans 0, 3, and 4. Spans 1 and 2 are copies of the level deck.
    street = [span for span in spans if span[0] in (0, 3, 4)]

    def on_other_span(index, point):
        py = point[1]
        s = deck_s_at_y(py)
        center = deck_point(s)
        if _dist(point, center) > 1.0:
            return False
        for other_i, a, b in street:
            if other_i == index:
                continue
            if min(a, b) - 0.2 <= s <= max(a, b) + 0.2:
                return True
        return False

    for index, s, point in ends:
        if index in (1, 2):
            if not any(min(a, b) <= s <= max(a, b) for _i, a, b in street):
                errors.append(f"wreckage span {index} is not on the deck")
            continue
        if on_cross_street(*point) or on_city_pad(*point):
            continue
        if not on_other_span(index, point):
            errors.append(f"span {index} end s={s:.1f} does not connect to a road")
    for s in TOWER_S:
        (x, y, _z), _rot = tower_pose(s)
        center = deck_point(s)
        if _dist((x, y), center) > 0.5:
            errors.append(f"tower at s={s} is off the centerline")
        legs = tower_legs(s)
        mid = ((legs[0][0] + legs[1][0]) / 2.0, (legs[0][1] + legs[1][1]) / 2.0)
        if _dist(mid, center) > 0.5:
            errors.append(f"tower legs at s={s} are not centered on the deck")
        rx, ry = right_vector()
        offsets = []
        for leg in legs:
            offsets.append((leg[0] - center[0]) * rx + (leg[1] - center[1]) * ry)
        if offsets[0] * offsets[1] >= 0:
            errors.append(f"tower legs at s={s} are on the same side of the deck")
        for offset in offsets:
            if abs(offset) < DECK_HALF - 0.5:
                errors.append(f"tower leg at s={s} stands on the deck instead of straddling it")
            if abs(offset) > DECK_HALF + TOWER_LEG + 1.0:
                errors.append(f"tower leg at s={s} stands beside the deck")
    for x, y in FOREGROUND_CARS:
        for rect in PATHS:
            if _on_rect(x, y, rect):
                errors.append(f"car at {(x, y)} sits on park path {rect[0]}")
        if park_grass(x, y):
            errors.append(f"car at {(x, y)} sits on grass")
        if on_deck_road(x, y):
            errors.append(f"car at {(x, y)} sits on the bridge deck")
    for lane in DECK_LANES:
        if abs(lane) > DECK_HALF - 1.0:
            errors.append(f"deck lane {lane} is off the roadway")
    fx, fy = FOUNTAIN
    if on_deck_road(fx, fy) or on_cross_street(fx, fy):
        errors.append("fountain is on a road")
    return errors
