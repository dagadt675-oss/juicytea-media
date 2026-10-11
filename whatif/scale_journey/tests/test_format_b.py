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
from ui.counter import CAPTION_Y0, draw_counter, draw_scale_counter  # noqa: E402
from ui.loop import pingpong_index  # noqa: E402
from ui.outlines import OUTLINES  # noqa: E402
from PIL import Image  # noqa: E402

EP = WHATIF / "scale_journey" / "episodes"


class PennyTest(unittest.TestCase):
    def setUp(self):
        self.ep = resolve_b(EP / "penny_empire.yaml")

    def _at(self, t):
        return min(self.ep.frames, key=lambda fr: abs(fr.t - t))

    def test_payoff_is_25_mph(self):
        self.assertEqual(round(self.ep.notes["terminal_mph"]), 25)
        self.assertAlmostEqual(self.ep.notes["drop_ft"], 1250, delta=0.2)

    def test_slate_beats(self):
        self.assertEqual(self._at(1.0).primary, "1,250")
        self.assertEqual(self._at(1.0).secondary, "0")
        self.assertLess(int(self._at(9.0).primary.replace(",", "")), int(self._at(4.5).primary.replace(",", "")))
        self.assertLess(int(self._at(16.0).primary.replace(",", "")), int(self._at(9.0).primary.replace(",", "")))
        self.assertLess(int(self._at(24.0).primary.replace(",", "")), 400)
        self.assertEqual(self._at(24.0).phase, "liberty")
        self.assertEqual(self._at(8.0).secondary, "25")
        self.assertEqual(self._at(30.0).secondary, "25")
        spoken = " ".join(beat["narration"] for beat in self.ep.beats)
        self.assertNotIn("65", spoken)
        self.assertNotIn("sixty-five", spoken.lower())
        self.assertNotIn("65", self._at(29.0).pill_sub)
        self.assertLess(int(self._at(33.0).primary.replace(",", "")), 40)
        self.assertNotIn("25", self.ep.raw["title"])

    def test_fall_descends_then_rises_to_the_ledge(self):
        rising = False
        for a, b in zip(self.ep.frames, self.ep.frames[1:]):
            if b.phase in ("rise", "hold"):
                rising = True
            elif b.phase != "hit" and not rising:
                self.assertLessEqual(b.penny[2], a.penny[2] + 1e-6)
        self.assertTrue(rising)
        first, last = self.ep.frames[0], self.ep.frames[-1]
        self.assertEqual(last.primary, "1,250")
        self.assertEqual(last.secondary, "0")
        self.assertAlmostEqual(last.penny[2], first.penny[2], delta=0.05)
        self.assertAlmostEqual(last.cam[2], first.cam[2], delta=0.05)

    def test_counter_holds_at_least_0_8s(self):
        # The opening height and the terminal speed hold. Height ticks during the fall.
        speed_runs = []
        current = None
        start = 0.0
        for fr in self.ep.frames:
            if fr.secondary != current:
                if current is not None:
                    speed_runs.append((current, start, fr.t))
                current = fr.secondary
                start = fr.t
        speed_runs.append((current, start, self.ep.duration))
        held = [run for run in speed_runs if run[0] == "25"]
        self.assertTrue(held)
        self.assertGreaterEqual(held[0][2] - held[0][1], 0.8)
        self.assertGreaterEqual(self._at(2.0).t, 0.0)
        self.assertEqual(self._at(2.0).primary, "1,250")

    def test_camera_stays_outside_the_shaft(self):
        from engine.bformat import clear_of_shaft

        pushed = clear_of_shaft((0.0, 0.0, 30.0), 1.0)
        self.assertGreater(pushed[0], 50.0)
        self.assertGreater(pushed[1], 30.0)
        for fr in self.ep.frames:
            again = clear_of_shaft(fr.cam, 0.8)
            self.assertAlmostEqual(again[0], fr.cam[0], delta=0.05)
            self.assertAlmostEqual(again[1], fr.cam[1], delta=0.05)
            coin = clear_of_shaft(fr.penny, 0.4)
            self.assertAlmostEqual(coin[0], fr.penny[0], delta=0.05)
            self.assertAlmostEqual(coin[1], fr.penny[1], delta=0.05)

    def test_hook_looks_out_over_the_city(self):
        hook = self._at(1.2)
        chase = self._at(14.0)
        self.assertLess(hook.target[2], hook.cam[2] - 20)
        self.assertGreater(hook.cam[2], hook.penny[2])
        self.assertLess(chase.target[2], chase.penny[2] - 0.5)
        self.assertGreater(chase.cam[2], chase.penny[2] + 0.4)

    def test_hook_does_not_spoil(self):
        hook = [fr for fr in self.ep.frames if fr.t < 2.5]
        self.assertTrue(all(fr.secondary == "0" for fr in hook))
        self.assertTrue(all("mph" not in fr.pill_sub for fr in hook))

    def test_words_schema(self):
        words = self.ep.notes and __import__("engine.bformat", fromlist=["words_for"]).words_for(self.ep)
        self.assertIn("words", words)
        self.assertIn("w", words["words"][0])
        self.assertIn("t0", words["words"][0])
        self.assertIn("t1", words["words"][0])

    def test_loop_frame(self):
        self.assertEqual(self.ep.frames[-1].phase, "hold")
        self.assertEqual(self.ep.frames[-1].primary, self.ep.frames[0].primary)


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
        self.assertGreater(ep.notes["years"], 500)
        self.assertLess(ep.notes["years"], 1000)
        self.assertGreater(ep.notes["square56_t"], ep.notes["world_harvest_t"])
        pts = cone_points(100, 2.0, 3.0, cap=50)
        self.assertEqual(len(pts), 50)
        self.assertTrue(all(0 <= p[2] <= 3.0 for p in pts))

    def test_crowd_fits_rhode_island(self):
        ep = resolve_b(EP / "crowd_rhode_island.yaml")
        self.assertEqual(ep.notes["people"], 8_200_000_000)
        self.assertTrue(ep.notes["fits"])
        self.assertAlmostEqual(ep.notes["per_m2"], 3.1, delta=0.15)
        self.assertEqual(len(ellipse_points(100, 1000.0, cap=40)), 40)

    def test_bricks_have_no_logo_and_a_finite_tower(self):
        ep = resolve_b(EP / "brick_tower.yaml")
        self.assertFalse(ep.notes["logo"])
        self.assertEqual(ep.notes["bricks"], 375_000)
        self.assertGreater(ep.notes["height_m"], 3000)

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
        _img, box = draw_scale_counter(
            img, "HEIGHT", "1,250", "ft", metric="381 m", second_label="SPEED", second_number="25", second_unit="mph"
        )
        self.assertLess(box[3], int(CAPTION_Y0 * 1920))


if __name__ == "__main__":
    unittest.main()
