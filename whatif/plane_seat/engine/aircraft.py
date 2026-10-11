"""A321LR-class single-aisle jet, metres. 3-3 cabin, 30 rows.

Procedural geometry only: generic white/charcoal/gold livery, no airline
name, no tail mark, no registration. Front and middle thirds share one amber.
"""

from __future__ import annotations

LENGTH = 44.51
NOSE_X = 22.25
TAIL_X = -22.26
RADIUS = 1.97
WINGSPAN = 35.80

ROWS = 30
SEATS_PER_ROW = 6
ROW_PITCH = 0.78
ROW0_X = 8.60

# Cuts fall in the gaps between row thirds (0-9, 10-19, 20-29).
CUT_FRONT = 1.19
CUT_BACK = -6.61

# Seat centres, left (+Y) then mirrored. Window, middle, aisle.
SEAT_Y = (1.28, 0.78, 0.30)

AMBER = (1.0, 0.56, 0.08)
GREEN = (0.10, 0.92, 0.38)
BRIGHT = (0.55, 1.0, 0.28)
RED = (1.0, 0.14, 0.10)
WHITE = (0.92, 0.90, 0.86)
GOLD = (0.95, 0.72, 0.28)
CHARCOAL = (0.16, 0.17, 0.19)

# Ground tiles. Travel is an integer number of tiles so the seam repeats.
TILE = 1200.0
TRAVEL = 4800.0


def row_x(index: int) -> float:
    return ROW0_X - index * ROW_PITCH


def third_of_row(index: int) -> str:
    if index < 10:
        return "front"
    if index < 20:
        return "mid"
    return "back"


def seat_role(row: int, seat: int) -> str:
    """seat 0 window, 1 middle, 2 aisle, on either side."""
    third = third_of_row(row)
    if third == "mid" and seat == 2:
        return "worst"
    if third == "back" and seat == 1:
        return "best"
    return third
