"""The bridge is a road, and the portals straddle it.

Run from whatif/:  python3 -m unittest tests.test_bridge_geometry
"""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.city_layout import (
    PARK_LAND_Z,
    QUAY_Z,
    SKYLINE_COLORS,
    SKYLINE_ROWS,
    city_water_top,
    deck_z,
    land_top,
    layout_errors,
    river_contains,
)


class BridgeGeometryTest(unittest.TestCase):
    def test_deck_meets_the_road_and_towers_straddle_it(self):
        self.assertEqual(layout_errors(), [])

    def test_ramp_arrives_flat_on_the_level_deck(self):
        slope = (deck_z(0.0) - deck_z(-0.4)) / 0.4
        self.assertLess(slope, 0.04)

    def test_scene_uses_the_shared_layout(self):
        text = (Path(__file__).resolve().parents[1] / "engine" / "scenes.py").read_text(encoding="utf-8")
        self.assertIn("bridge_spans()", text)
        self.assertIn("DECK_ROT_Z", text)
        self.assertIn("SKYLINE_ROWS", text)
        self.assertNotIn("atan2(x1 - x0, y1 - y0)", text)

    def test_skyline_keeps_height_and_color(self):
        heights = [row[2] for row in SKYLINE_ROWS]
        self.assertGreaterEqual(max(heights), 70.0)
        self.assertGreaterEqual(len(SKYLINE_ROWS), 3)
        for _y, hmin, hmax, _x0, _x1, wr in SKYLINE_ROWS:
            self.assertGreaterEqual(wr[0], 24.0)
            self.assertLessEqual(wr[1], 48.0)
            self.assertGreaterEqual(hmin / wr[1], 3.0)
            self.assertLessEqual(hmax / wr[0], 6.5)
        blues = [color for color in SKYLINE_COLORS if color[2] > color[0] + 0.08]
        salmons = [color for color in SKYLINE_COLORS if color[0] > 0.7 and color[0] > color[2] + 0.25]
        self.assertGreaterEqual(len(blues), 1)
        self.assertGreaterEqual(len(salmons), 1)
        self.assertGreaterEqual(len({tuple(color[:3]) for color in SKYLINE_COLORS}), 6)

    def test_water_stays_below_the_land_outside_the_river(self):
        samples = ((0.0, 16.0), (-20.0, 40.0), (10.0, 70.0), (0.0, 90.0), (30.0, 400.0), (-40.0, 12.0))
        for flood in (0.0, 0.3, 0.72, 1.0):
            surface = city_water_top(flood)
            self.assertLess(surface, QUAY_Z)
            for x, y in samples:
                self.assertFalse(river_contains(x, y))
                self.assertLess(surface, land_top(x, y))
                self.assertLess(surface, PARK_LAND_Z)


if __name__ == "__main__":
    unittest.main()
