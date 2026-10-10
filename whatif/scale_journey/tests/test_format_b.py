"""Format B slate: penny physics, shared UI, instancer, words clock."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WHATIF = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WHATIF))
sys.path.insert(0, str(WHATIF / "scale_journey"))

from engine.bformat import resolve_b  # noqa: E402
from engine.instancer import cone_points, ellipse_points  # noqa: E402
from ui.counter import CAPTION_Y0, draw_counter  # noqa: E402
from ui.loop import pingpong_index  # noqa: E402
from ui.outlines import OUTLINES  # noqa: E402
from PIL import Image  # noqa: E402

EP = WHATIF / "scale_journey" / "episodes"


class PennyTest(unittest.TestCase):
    def setUp(self):
        self.ep = resolve_b(EP / "penny_empire.yaml")

    def test_payoff_is_25_mph(self):
        self.assertEqual(round(self.ep.notes["terminal_mph"]), 25)

    def test_camera_only_descends(self):
        fall = [fr for fr in self.ep.frames if fr.phase == "fall"]
        for a, b in zip(fall, fall[1:]):
            self.assertLessEqual(b.cam[2], a.cam[2] + 1e-9)
            self.assertAlmostEqual(b.cam[0], a.cam[0])
            self.assertAlmostEqual(b.cam[1], a.cam[1])

    def test_reaches_the_sidewalk(self):
        last = [fr for fr in self.ep.frames if fr.phase == "payoff"][0]
        self.assertAlmostEqual(last.fallen_m, self.ep.notes["drop_m"], delta=0.05)
        self.assertEqual(last.primary, "25")

    def test_speed_holds(self):
        # Once the counter reads 25 it stays there at least 0.8 s, and in fact for the rest of the fall.
        seen = None
        for fr in self.ep.frames:
            if fr.primary == "25":
                seen = fr.t
                break
        self.assertIsNotNone(seen)
        tail = [fr for fr in self.ep.frames if fr.t >= seen and fr.phase != "dissolve"]
        self.assertTrue(all(fr.primary == "25" for fr in tail))
        self.assertGreater(tail[-1].t - tail[0].t, 0.8)

    def test_words_schema(self):
        words = self.ep.notes and __import__("engine.bformat", fromlist=["words_for"]).words_for(self.ep)
        self.assertIn("words", words)
        self.assertIn("w", words["words"][0])
        self.assertIn("t0", words["words"][0])
        self.assertIn("t1", words["words"][0])

    def test_loop_frame(self):
        self.assertEqual(self.ep.frames[-1].phase, "dissolve")
        self.assertGreater(self.ep.frames[-1].dissolve, 0.9)


class SlateTest(unittest.TestCase):
    def test_outlines(self):
        for name in ("person", "liberty", "empire", "burj", "stadium", "titanic"):
            self.assertIn(name, OUTLINES)
            self.assertGreater(OUTLINES[name]["height_m"], 0)

    def test_rice_heap_and_orbit_camera(self):
        ep = resolve_b(EP / "rice_chessboard.yaml")
        self.assertEqual(ep.notes["grains"], 2**64 - 1)
        self.assertLess(ep.notes["heap_height_m"], 20_000)  # kilometres, not orbit
        self.assertGreater(ep.notes["camera_altitude_m"], 300_000)
        self.assertLessEqual(ep.notes["instance_cap"], 8000)
        pts = cone_points(100, 2.0, 3.0, cap=50)
        self.assertEqual(len(pts), 50)
        self.assertTrue(all(0 <= p[2] <= 3.0 for p in pts))

    def test_crowd_fits_rhode_island(self):
        ep = resolve_b(EP / "crowd_rhode_island.yaml")
        self.assertTrue(ep.notes["fits"])
        self.assertLess(ep.notes["needed_sq_mi"], ep.notes["land_sq_mi"])
        self.assertEqual(len(ellipse_points(100, 1000.0, cap=40)), 40)

    def test_bricks_have_no_logo_and_a_finite_tower(self):
        ep = resolve_b(EP / "brick_tower.yaml")
        self.assertFalse(ep.notes["logo"])
        self.assertGreater(ep.notes["bricks"], 1000)
        self.assertGreater(ep.notes["height_m"], 100)

    def test_hole_exits_in_the_indian_ocean_and_pingpongs(self):
        ep = resolve_b(EP / "earth_hole.yaml")
        self.assertIn("Indian Ocean", ep.notes["exit"])
        self.assertEqual(ep.notes["loop"], "pingpong")
        self.assertEqual(pingpong_index(0, 10), (0, False))
        self.assertEqual(pingpong_index(10, 10), (8, True))
        # The frame after a full down-and-back is the opening picture again.
        self.assertEqual(pingpong_index(18, 10), (0, False))

    def test_counter_stays_above_the_caption_band(self):
        img = Image.new("RGB", (1080, 1920), (20, 20, 24))
        _img, box = draw_counter(img, "SPEED", "25", "mph")
        self.assertLess(box[3], int(CAPTION_Y0 * 1920))


if __name__ == "__main__":
    unittest.main()
