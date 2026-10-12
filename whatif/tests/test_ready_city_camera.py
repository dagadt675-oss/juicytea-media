"""Eye-height walk, a Year 500 push-in on the Miura, then the opening pose."""

import math
import unittest
from pathlib import Path

from engine.spec import load_resolved, sample_camera_path

ROOT = Path(__file__).resolve().parents[1]
EYE = 1.70
# The hero car, placed in ready_city._crowd.
MIURA = (-0.4, -54.0)


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

    def test_the_camera_never_rises(self):
        for pose in self.poses:
            self.assertAlmostEqual(pose["location"][2], EYE, places=2)
            self.assertAlmostEqual(pose["lens"], 28.0, places=2)

    def test_year_500_pushes_in_on_the_car(self):
        def gap(pose):
            loc = pose["location"]
            return math.dist((loc[0], loc[1]), MIURA)

        start = self.poses[int(33 * self.fps)]
        close = min(self.poses[int(40 * self.fps) : int(49 * self.fps)], key=gap)
        self.assertGreater(gap(start), 6.0)
        self.assertLess(gap(close), 5.0)
        self.assertGreater(gap(close), 3.0)
        # The close look stays on the car, not up the facade.
        aim = close["target"]
        self.assertLess(math.dist((aim[0], aim[1]), MIURA), 1.5)
        self.assertLess(aim[2], EYE)

    def test_loop_matches_the_opening_pose(self):
        self.assertLess(math.dist(self.poses[0]["location"], self.poses[-1]["location"]), 0.01)
        self.assertLess(math.dist(self.poses[0]["target"], self.poses[-1]["target"]), 0.01)
        self.assertAlmostEqual(self.poses[0]["lens"], self.poses[-1]["lens"])
        return_at = next(beat["start"] for beat in self.resolved["beats"] if beat["id"] == "return")
        landed = int((return_at - 0.4) * self.fps)
        self.assertLess(math.dist(self.poses[0]["location"], self.poses[landed]["location"]), 0.05)
        self.assertLess(math.dist(self.poses[0]["target"], self.poses[landed]["target"]), 0.05)

    def test_the_move_stays_slow(self):
        peak = 0.0
        for left, right in zip(self.poses, self.poses[1:]):
            step = math.dist(left["location"], right["location"]) * self.fps
            peak = max(peak, step)
        self.assertGreater(peak, 0.8)
        self.assertLess(peak, 1.8)


if __name__ == "__main__":
    unittest.main()
