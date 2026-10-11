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
# A 20 m deck is four real lanes. Towers rise about 2.7 times that width
# above the roadway, so the portal reads as a bridge and not a gate.
DECK_W = 20.0
DECK_HALF = DECK_W / 2.0
DECK_Z = 4.6
TOWER_W = 22.0
TOWER_LEG = 1.6
# Height of each portal measured from the deck surface.
TOWER_CLEAR = (54.0, 46.0)
# Object-index ids for the opening metric. Cables and the pier stay at 0.
INDEX_DECK = 2
INDEX_CANOPY = 3
INDEX_PORTAL = 11
# Foreground road the approach must join. y=22 is the avenue center.
CROSS_Y = 22.0
CROSS_X0 = -80.0
CROSS_X1 = 90.0
# Far landing sits on the city ground.
FAR_Z = 1.4

# The river is a polygon between the near bank (y≈82) and the skyline (y≈168).
# Water stays inside it, and the surface stays below every walkable top.
RIVER_X0 = -520.0
RIVER_X1 = 520.0
RIVER_Y0 = 86.0
RIVER_Y1 = 150.0
QUAY_Z = 3.2
PARK_LAND_Z = 0.72
ROAD_Z = 0.58
WATER_BED_Z = -1.6
# Driving surface of the ramp is deck_z + RIBBON_TOP. A centimeter above the
# avenue keeps the joint from flickering where the two slabs overlap.
RIBBON_TOP = 0.06
SOUTH_Z = ROAD_Z - RIBBON_TOP + 0.012

# East-west avenue. Four lanes, the same width as the bridge, so the ramp
# lanes continue straight into the avenue lanes.
AVE_Y = 22.0
LANE_W = DECK_W / 4.0
AVE_HALF = DECK_W / 2.0
# Parking stalls sit outside the four travel lanes, on the avenue only.
PARKING_W = 2.5
AVENUE_HALF = AVE_HALF + PARKING_W
LANE_OFFSETS = (-1.5 * LANE_W, -0.5 * LANE_W, 0.5 * LANE_W, 1.5 * LANE_W)
DECK_LANES = LANE_OFFSETS
SIDEWALK_W = 3.0
ZEBRA_DEPTH = 3.0
STOP_SETBACK = 2.5
# US paint: 10 ft dashes, 30 ft gaps.
DASH_LEN = 3.05
DASH_GAP = 9.14
# Park reference only. The one cross street is the bridge ramp, not this x.
GRID_X = -22.0
GRID_HALF = 4.2
# Far-bank streets between tower blocks. Spaced so a chunky tower still fits
# between them. The park street uses the same x as the first one.
CITY_STREETS = (-22.0, 55.0)


def river_contains(x, y):
    return RIVER_X0 <= x <= RIVER_X1 and RIVER_Y0 <= y <= RIVER_Y1


def city_water_top(flood=0.0, water=0.0):
    """Visible river sheet. Still under the park, the road, and the quay."""
    # Day 1 sits near z=0.34, in the gap the locked camera sees as the river
    # band. Flood can rise a little. It never reaches a walkable surface.
    raw = 0.34 + float(flood) * 0.08 + float(water) * 0.03
    cap = min(PARK_LAND_Z, ROAD_Z) - 0.10
    return min(raw, cap)


def land_top(x, y):
    """Walkable surface. Inside the river this is the bed, not the bank."""
    if river_contains(x, y):
        return WATER_BED_Z
    if abs(y - AVE_Y) <= AVENUE_HALF + SIDEWALK_W + 2.0:
        return ROAD_Z
    if y > RIVER_Y1:
        return 1.4
    return PARK_LAND_Z


def on_block_street(x, pad=0.0):
    """True when a footprint would cover a street between tower blocks."""
    half = 4.5 + pad
    return any(abs(x - sx) <= half for sx in CITY_STREETS)


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
# (y, hmin, hmax, x0, x1, (wmin, wmax)). Footprints stay chunky, 26–42 m.
# The locked camera puts a roof above about 70 m off the top of the frame,
# which erases the sky the title sits in, so the band stops under that line.
# The front row is the solved skyline (world y≈168–172).
SKYLINE_ROWS = (
    (172.0, 32.0, 48.0, -220.0, 260.0, (26.0, 40.0)),
    (255.0, 34.0, 50.0, -250.0, 290.0, (28.0, 42.0)),
    (360.0, 32.0, 48.0, -270.0, 310.0, (26.0, 40.0)),
    (480.0, 30.0, 46.0, -290.0, 330.0, (26.0, 38.0)),
)

FOUNTAIN = (-38.0, 60.0)


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


def _s_at_y(y):
    return (y - DECK_ORIGIN[1]) / math.cos(BRIDGE_YAW)


# Level deck is the river span. The ramp meets it at the near bank and the
# far road leaves it at the far bank. Towers stand just in the water.
NEAR_BANK_S = _s_at_y(RIVER_Y0)
FAR_BANK_S = _s_at_y(RIVER_Y1)
FAR_ROAD_S = _s_at_y(RIVER_Y1 + 40.0)
TOWER_S = (_s_at_y(RIVER_Y0 + 12.0), _s_at_y(RIVER_Y1 - 12.0))
CROSS_HALF_Y = AVENUE_HALF + 1.0
# The ramp meets the north curb and stays at avenue grade through the crosswalk.
# Three metres into the avenue so the ramp asphalt overlaps the cross street.
RAMP_JOIN_S = _s_at_y(AVE_Y + AVENUE_HALF - 3.5)
RAMP_FLAT_S = _s_at_y(AVE_Y + AVENUE_HALF + ZEBRA_DEPTH + STOP_SETBACK + 1.2)


def deck_z(s):
    """Flat through the intersection, then a smoothstep up to the river deck."""
    if s <= RAMP_FLAT_S:
        return SOUTH_Z
    if s < NEAR_BANK_S:
        span = NEAR_BANK_S - RAMP_FLAT_S
        t = 0.0 if span == 0 else (s - RAMP_FLAT_S) / span
        return SOUTH_Z + _smooth(t) * (DECK_Z - SOUTH_Z)
    if s > FAR_BANK_S:
        span = FAR_ROAD_S - FAR_BANK_S
        t = 0.0 if span == 0 else (s - FAR_BANK_S) / span
        t = max(0.0, min(1.0, t))
        return DECK_Z + _smooth(t) * (FAR_Z - DECK_Z)
    return DECK_Z


def bridge_spans():
    """(index, s0, s1). 1 and 2 are the hidden wreckage copies.

    0 is the river deck between the banks. 4 is the ramp down to the avenue.
    3 is the far-bank road. They meet at a shared s.
    """
    a = NEAR_BANK_S
    b = FAR_BANK_S
    wreck_a = a + (b - a) * 0.30
    wreck_b = a + (b - a) * 0.70
    mid = (wreck_a + wreck_b) * 0.5
    return (
        (0, a, b),
        (1, wreck_a, mid),
        (2, mid - 1.0, wreck_b),
        (3, b, FAR_ROAD_S),
        (4, RAMP_JOIN_S, a),
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
    if s < RAMP_JOIN_S - 0.4 or s > FAR_ROAD_S + 0.4:
        return False
    cx, cy = deck_point(s)
    return abs(x - cx) <= DECK_HALF + 0.3 and abs(y - cy) < 0.6


def on_city_pad(x, y):
    """Far landing, where the deck comes down onto the far bank."""
    if y < RIVER_Y1 - 1.0 or y > RIVER_Y1 + 48.0:
        return False
    s = deck_s_at_y(y)
    cx, _cy = deck_point(s)
    return abs(x - cx) <= DECK_HALF + 6.0


def on_road(x, y):
    return on_cross_street(x, y) or on_deck_road(x, y) or on_city_pad(x, y)


def park_grass(x, y):
    in_park = 40.0 <= y <= 82.0 and -70.0 <= x <= 40.0
    return in_park and not on_road(x, y) and not river_contains(x, y)


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
    for x, y, yaw in FOREGROUND_CARS:
        for rect in PATHS:
            if _on_rect(x, y, rect):
                errors.append(f"car at {(x, y)} sits on park path {rect[0]}")
        if park_grass(x, y):
            errors.append(f"car at {(x, y)} sits on grass")
        if on_deck_road(x, y):
            errors.append(f"car at {(x, y)} sits on the bridge deck")
        if abs(x - CROSS_X) < DECK_HALF + ZEBRA_DEPTH and abs(y - AVE_Y) < AVENUE_HALF + ZEBRA_DEPTH:
            errors.append(f"car at {(x, y)} sits in the intersection")
        if y < AVE_Y and abs(yaw) > 0.2:
            errors.append(f"car at {(x, y)} faces against the eastbound lanes")
        if y > AVE_Y and abs(abs(yaw) - math.pi) > 0.2:
            errors.append(f"car at {(x, y)} faces against the westbound lanes")
    for lane in DECK_LANES:
        if abs(lane) > DECK_HALF - 1.0:
            errors.append(f"deck lane {lane} is off the roadway")
    fx, fy = FOUNTAIN
    if on_deck_road(fx, fy) or on_cross_street(fx, fy):
        errors.append("fountain is on a road")
    return errors


# The ramp meets the avenue on the bridge centerline. One intersection.
CROSS_X = deck_point(south_s())[0]
# Paths are paths: they meet the north sidewalk west of that intersection.
PATHS = (
    ("quay_walk", -30.0, 78.0, 18.0, 1.15),
    ("to_fountain", -30.0, 66.0, 1.15, 12.0),
    ("to_sidewalk", -12.0, 40.0, 1.15, 8.0),
)
# Eastbound (nose +X) in the south lanes, westbound in the north lanes.
# None of them sit in the intersection box.
_EAST_Y = AVE_Y + LANE_OFFSETS[0]
_EAST_Y2 = AVE_Y + LANE_OFFSETS[1]
_WEST_Y = AVE_Y + LANE_OFFSETS[3]
_WEST_Y2 = AVE_Y + LANE_OFFSETS[2]
_PARK_S = AVE_Y - AVE_HALF - PARKING_W * 0.5
_PARK_N = AVE_Y + AVE_HALF + PARKING_W * 0.5
# The drone hero sits in the southbound-side eastbound lane. Nose +X.
# A Miura mesh can replace the stand-in without moving this point.
HERO_SPORTS = (-36.0, _EAST_Y, 0.0)
# Stopped traffic sits about 7.5 m center to center (a car length plus a
# short gap). Cars farther from the light are spaced wider. Parked cars
# face the same way as the lane beside them.
FOREGROUND_CARS = (
    (-20.0, _EAST_Y, 0.0),
    (-28.0, _EAST_Y, 0.0),
    (-44.0, _EAST_Y, 0.0),
    (-56.0, _EAST_Y, 0.0),
    (-72.0, _EAST_Y, 0.0),
    (-24.0, _EAST_Y2, 0.0),
    (-33.0, _EAST_Y2, 0.0),
    (-48.0, _EAST_Y2, 0.0),
    (-66.0, _EAST_Y2, 0.0),
    (22.0, _WEST_Y, math.pi),
    (30.0, _WEST_Y, math.pi),
    (38.0, _WEST_Y, math.pi),
    (50.0, _WEST_Y, math.pi),
    (66.0, _WEST_Y, math.pi),
    (26.0, _WEST_Y2, math.pi),
    (35.0, _WEST_Y2, math.pi),
    (52.0, _WEST_Y2, math.pi),
    (-70.0, _PARK_S, 0.0),
    (-62.0, _PARK_S, 0.0),
    (-54.0, _PARK_S, 0.0),
    (-46.0, _PARK_S, 0.0),
    (28.0, _PARK_S, 0.0),
    (36.0, _PARK_S, 0.0),
    (44.0, _PARK_S, 0.0),
    (52.0, _PARK_S, 0.0),
    (60.0, _PARK_S, 0.0),
    (-68.0, _PARK_N, math.pi),
    (-60.0, _PARK_N, math.pi),
    (-44.0, _PARK_N, math.pi),
    (32.0, _PARK_N, math.pi),
    (40.0, _PARK_N, math.pi),
    (56.0, _PARK_N, math.pi),
)
