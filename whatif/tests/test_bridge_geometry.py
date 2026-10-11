"""The bridge is a road, and the portals straddle it.

Run from whatif/:  python3 -m unittest tests.test_bridge_geometry
"""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.city_layout import (
    AVE_Y,
    PARK_LAND_Z,
    QUAY_Z,
    RIVER_Y0,
    RIVER_Y1,
    SKYLINE_COLORS,
    SKYLINE_ROWS,
    city_water_top,
    NEAR_BANK_S,
    deck_z,
    land_top,
    layout_errors,
    river_contains,
)


class BridgeGeometryTest(unittest.TestCase):
    def test_deck_meets_the_road_and_towers_straddle_it(self):
        self.assertEqual(layout_errors(), [])

    def test_ramp_arrives_flat_on_the_level_deck(self):
        slope = (deck_z(NEAR_BANK_S) - deck_z(NEAR_BANK_S - 0.4)) / 0.4
        self.assertLess(slope, 0.04)

    def test_ramp_meets_the_avenue_at_grade(self):
        from engine.city_layout import RAMP_JOIN_S, RIBBON_TOP, ROAD_Z

        surface = deck_z(RAMP_JOIN_S) + RIBBON_TOP
        self.assertAlmostEqual(surface, ROAD_Z + 0.012, delta=0.02)
        self.assertLess(deck_z(RAMP_JOIN_S), deck_z(NEAR_BANK_S))

    def test_scene_uses_the_shared_layout(self):
        text = (Path(__file__).resolve().parents[1] / "engine" / "scenes.py").read_text(encoding="utf-8")
        self.assertIn("bridge_spans()", text)
        self.assertIn("DECK_ROT_Z", text)
        self.assertIn("SKYLINE_ROWS", text)
        self.assertNotIn("atan2(x1 - x0, y1 - y0)", text)

    def test_skyline_keeps_height_and_color(self):
        heights = [row[2] for row in SKYLINE_ROWS]
        self.assertGreaterEqual(max(heights), 46.0)
        self.assertGreaterEqual(len(SKYLINE_ROWS), 3)
        for _y, hmin, hmax, _x0, _x1, wr in SKYLINE_ROWS:
            # Chunky footprints. A 3:1 roof on a 30 m lot is about 90 m, and
            # the locked camera puts that above the frame, so the band stops
            # under the sky instead.
            self.assertGreaterEqual(wr[0], 24.0)
            self.assertLessEqual(wr[1], 48.0)
            self.assertGreaterEqual(hmin, 28.0)
            self.assertLessEqual(hmax, 64.0)
            self.assertLessEqual(hmax / wr[0], 3.2)
        blues = [color for color in SKYLINE_COLORS if color[2] > color[0] + 0.08]
        salmons = [color for color in SKYLINE_COLORS if color[0] > 0.7 and color[0] > color[2] + 0.25]
        self.assertGreaterEqual(len(blues), 1)
        self.assertGreaterEqual(len(salmons), 1)
        self.assertGreaterEqual(len({tuple(color[:3]) for color in SKYLINE_COLORS}), 6)

    def test_water_stays_below_the_land_outside_the_river(self):
        samples = ((0.0, 16.0), (-20.0, 40.0), (10.0, 70.0), (0.0, 200.0), (30.0, 400.0), (-40.0, 18.0))
        self.assertGreater(city_water_top(0.0), 0.2)
        self.assertLess(RIVER_Y0, 90.0)
        self.assertGreater(RIVER_Y1, 140.0)
        self.assertLess(AVE_Y, 30.0)
        self.assertGreater(AVE_Y, 14.0)
        for flood in (0.0, 0.3, 0.72, 1.0):
            surface = city_water_top(flood)
            self.assertLess(surface, QUAY_Z)
            for x, y in samples:
                self.assertFalse(river_contains(x, y))
                self.assertLess(surface, land_top(x, y))
                self.assertLess(surface, PARK_LAND_Z)


if __name__ == "__main__":
    unittest.main()
