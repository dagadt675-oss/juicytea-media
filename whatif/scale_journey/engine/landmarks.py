"""Where the Empire State sits on the Midtown grid.

Fifth Avenue runs north-south (+Y). 33rd and 34th Streets run east-west.
The building's long side faces Fifth Avenue, so the long axis is north-south.
The lot is the real footprint, about 57 m east-west by 129 m north-south.
Sidewalks wrap it. The roadways start outside those sidewalks.
"""

from __future__ import annotations

# xmin, xmax, ymin, ymax. East is +X, north is +Y.
ESB_LOT = (-28.5, 28.5, -64.5, 64.5)
SIDEWALK = 4.5
STREET_W = 18.0

# 5th Avenue and 34th Street corner, on the sidewalk, not in the roadway.
# The man the penny taps stands here, just north of the NanoRay base.
MAN = (8.0, 67.8)


def _street_centers():
    x0, x1, y0, y1 = ESB_LOT
    north = y1 + SIDEWALK + STREET_W * 0.5
    south = y0 - SIDEWALK - STREET_W * 0.5
    east = x1 + SIDEWALK + STREET_W * 0.5
    return north, south, east


def road_rects() -> list[tuple[float, float, float, float]]:
    """Axis-aligned road surfaces around the lot. xmin, xmax, ymin, ymax."""
    x0, x1, y0, y1 = ESB_LOT
    north, south, east = _street_centers()
    half = STREET_W * 0.5
    return [
        (x0 - 90.0, x1 + 90.0, north - half, north + half),
        (x0 - 90.0, x1 + 90.0, south - half, south + half),
        (east - half, east + half, y0 - 50.0, y1 + 50.0),
    ]


def boxes_overlap(a, b) -> bool:
    return a[0] < b[1] and a[1] > b[0] and a[2] < b[3] and a[3] > b[2]


def footprint_clears_roads(footprint=ESB_LOT) -> bool:
    """The building lot, grown by the sidewalk, must not meet a roadway."""
    x0, x1, y0, y1 = footprint
    pad = (x0 - SIDEWALK, x1 + SIDEWALK, y0 - SIDEWALK, y1 + SIDEWALK)
    return not any(boxes_overlap(pad, road) for road in road_rects())
