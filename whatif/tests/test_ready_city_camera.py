"""Street-level walk, one Year 500 rise, then a matched return to the opening."""

import math
import unittest
from pathlib import Path

from engine.spec import load_resolved, sample_camera_path

ROOT = Path(__file__).resolve().parents[1]
EYE = 1.70


class ReadyCityCameraTest(unittest.TestCase):
    def setUp(self):
        self.resolved = load_resolved(ROOT / "episodes" / "ready_city.yaml")
        self.path = self.resolved["camera"]["path"]
        self.frames = self.resolved["frame_count"]
        self.fps = self.resolved["fps"]
        self.poses = [
            sample_camera_path(self.path, (frame - 1) / (self.frames - 1))
            for frame in range(1, self.frames + 1)
        ]

    def test_no_beat_takes_the_camera(self):
        self.assertTrue(self.path)
        for beat in self.resolved["beats"]:
            self.assertIsNone(beat.get("camera"), beat["id"])

    def test_street_stays_low_until_year_500(self):
        # Year 100 is frame 860. The rise starts after the ruin is on, about 33 s.
        for frame in range(1, int(32.5 * self.fps) + 2):
            self.assertAlmostEqual(self.poses[frame - 1]["location"][2], EYE, places=2)
        top = max(pose["location"][2] for pose in self.poses)
        self.assertGreater(top, 12.0)
        self.assertLess(top, 18.0)

    def test_rise_then_ease_home(self):
        heights = [pose["location"][2] for pose in self.poses]
        peak_at = heights.index(max(heights))
        self.assertGreater(peak_at, int(33 * self.fps))
        self.assertLess(peak_at, int(48 * self.fps))
        # One rise, one descent. No second climb.
        rising = True
        for earlier, later in zip(heights[: peak_at + 1], heights[1 : peak_at + 1]):
            self.assertGreaterEqual(later + 1e-6, earlier)
        for earlier, later in zip(heights[peak_at:], heights[peak_at + 1 :]):
            self.assertLessEqual(later, earlier + 1e-6)
            rising = False
        self.assertFalse(rising)
        return_at = next(beat["start"] for beat in self.resolved["beats"] if beat["id"] == "return")
        landed = int(return_at * self.fps)
        self.assertAlmostEqual(heights[landed], EYE, places=2)
        self.assertAlmostEqual(heights[-1], EYE, places=2)

    def test_loop_matches_the_opening_pose(self):
        self.assertLess(math.dist(self.poses[0]["location"], self.poses[-1]["location"]), 0.01)
        self.assertLess(math.dist(self.poses[0]["target"], self.poses[-1]["target"]), 0.01)
        self.assertAlmostEqual(self.poses[0]["lens"], self.poses[-1]["lens"])
        # The hold after landing is long enough that the city reset happens on this pose.
        return_at = next(beat["start"] for beat in self.resolved["beats"] if beat["id"] == "return")
        landed = int((return_at - 0.4) * self.fps)
        self.assertLess(math.dist(self.poses[0]["location"], self.poses[landed]["location"]), 0.05)

    def test_the_move_stays_slow(self):
        peak = 0.0
        street_peak = 0.0
        street_until = int(33 * self.fps)
        for index, (left, right) in enumerate(zip(self.poses, self.poses[1:])):
            speed = math.dist(left["location"], right["location"]) * self.fps
            peak = max(peak, speed)
            if index < street_until:
                street_peak = max(street_peak, speed)
        self.assertGreater(street_peak, 1.0)
        self.assertLess(street_peak, 1.6)
        self.assertLess(peak, 2.6)


if __name__ == "__main__":
    unittest.main()
