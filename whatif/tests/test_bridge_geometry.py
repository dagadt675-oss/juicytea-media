"""The bridge is a road, and the portals straddle it.

Run from whatif/:  python3 -m unittest tests.test_bridge_geometry
"""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.city_layout import (
    SKYLINE_COLORS,
    SKYLINE_ROWS,
    layout_errors,
)


class BridgeGeometryTest(unittest.TestCase):
    def test_deck_meets_the_road_and_towers_straddle_it(self):
        self.assertEqual(layout_errors(), [])

    def test_scene_uses_the_shared_layout(self):
        text = (Path(__file__).resolve().parents[1] / "engine" / "scenes.py").read_text(encoding="utf-8")
        self.assertIn("bridge_spans()", text)
        self.assertIn("DECK_ROT_Z", text)
        self.assertIn("SKYLINE_ROWS", text)
        self.assertNotIn("atan2(x1 - x0, y1 - y0)", text)

    def test_skyline_keeps_height_and_color(self):
        heights = [row[2] for row in SKYLINE_ROWS]
        self.assertGreaterEqual(max(heights), 60.0)
        self.assertLessEqual(min(row[1] for row in SKYLINE_ROWS), 24.0)
        self.assertGreaterEqual(len(SKYLINE_ROWS), 3)
        blues = [color for color in SKYLINE_COLORS if color[2] > color[0] + 0.08]
        salmons = [color for color in SKYLINE_COLORS if color[0] > 0.7 and color[0] > color[2] + 0.25]
        self.assertGreaterEqual(len(blues), 1)
        self.assertGreaterEqual(len(salmons), 1)
        self.assertGreaterEqual(len({tuple(color[:3]) for color in SKYLINE_COLORS}), 6)


if __name__ == "__main__":
    unittest.main()
