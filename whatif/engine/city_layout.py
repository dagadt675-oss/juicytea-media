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

# Positive yaw brings the near end down into the camera, onto the foreground road.
BRIDGE_YAW = math.radians(11.0)
DECK_ROT_Z = -BRIDGE_YAW
DECK_ORIGIN = (8.0, 79.0)
DECK_W = 16.0
DECK_HALF = DECK_W / 2.0
DECK_Z = 8.5
SOUTH_Z = 0.62
TOWER_W = 18.0
TOWER_LEG = 1.6
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

# Grey, white, and light blue, with a few salmon towers. Locked by a test.
SKYLINE_COLORS = (
    (0.78, 0.80, 0.83, 1),
    (0.92, 0.93, 0.94, 1),
    (0.62, 0.74, 0.86, 1),
    (0.70, 0.76, 0.82, 1),
    (0.86, 0.87, 0.88, 1),
    (0.84, 0.48, 0.42, 1),
    (0.55, 0.66, 0.80, 1),
    (0.76, 0.42, 0.40, 1),
    (0.90, 0.88, 0.84, 1),
)
# y, hmin, hmax, x0, x1, (wmin, wmax). Back row is the tall one.
SKYLINE_ROWS = (
    (208.0, 22.0, 42.0, -100.0, 140.0, (10.0, 18.0)),
    (242.0, 30.0, 54.0, -110.0, 150.0, (8.0, 15.0)),
    (278.0, 40.0, 68.0, -90.0, 130.0, (7.0, 13.0)),
)

# Park paths. Cars must not sit on these.
PATHS = (
    ("promenade", -22.0, 55.0, 3.4, 44.0),
    ("path_a", -8.0, 48.0, 36.0, 2.2),
    ("path_b", -30.0, 64.0, 2.2, 28.0),
    ("path_c", -4.0, 68.0, 28.0, 2.0),
    ("plaza", -20.0, 58.0, 9.0, 9.0),
)
FOUNTAIN = (-20.0, 58.0)
# East-west traffic on the foreground road, clear of the park paths.
# West of the bridge landing (center x about -3). Kept off the deck slab.
FOREGROUND_CARS = (
    (-32.0, 21.0),
    (-28.0, 27.0),
    (-16.0, 19.0),
    (-14.0, 26.0),
    (-17.5, 23.0),
    (-30.0, 16.5),
)
DECK_LANES = (-5.0, -2.2, 2.2, 5.0)


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


def deck_z(s):
    if s < 0.0:
        s0 = south_s()
        t = (s - s0) / (0.0 - s0)
        t = max(0.0, min(1.0, t))
        return SOUTH_Z + t * (DECK_Z - SOUTH_Z)
    if s > LEVEL_S1:
        t = min(1.0, (s - LEVEL_S1) / (FAR_S - LEVEL_S1))
        return DECK_Z + t * (FAR_Z - DECK_Z)
    return DECK_Z


def bridge_spans():
    """(index, s0, s1). 1 and 2 are the hidden wreckage copies.

    The approach runs a few meters under the level deck, and the far ramp
    starts a few meters back under it, so the square ends cannot leave a gap.
    """
    return (
        (0, 0.0, LEVEL_S1),
        (1, 40.0, 72.0),
        (2, 70.0, 104.0),
        (3, LEVEL_S1 - 6.0, FAR_S),
        (4, south_s(), 8.0),
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
