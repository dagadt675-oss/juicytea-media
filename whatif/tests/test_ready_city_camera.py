"""Street walk, then the first episode's three low glides, then the opening pose."""

import math
import unittest
from pathlib import Path

from engine.spec import load_resolved, sample_camera_path

ROOT = Path(__file__).resolve().parents[1]
EYE = 1.70
MIURA = (-0.4, -54.0)
FALLEN = (1.4, -40.0)


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

    def _pose_at(self, seconds):
        return self.poses[min(self.frames - 1, int(round(seconds * self.fps)))]

    def test_no_beat_takes_the_camera(self):
        self.assertTrue(self.path)
        for beat in self.resolved["beats"]:
            self.assertIsNone(beat.get("camera"), beat["id"])

    def test_the_glides_stay_low(self):
        for pose in self.poses:
            self.assertLess(pose["location"][2], 2.8)
            self.assertGreater(pose["location"][2], 1.1)
        for frame in range(1, int(24 * self.fps)):
            self.assertAlmostEqual(self.poses[frame - 1]["location"][2], EYE, places=2)

    def test_three_low_passes_then_home(self):
        husk = self._pose_at(37.5)
        facade = self._pose_at(41.8)
        span = self._pose_at(44.3)

        def tilt(pose):
            loc = pose["location"]
            aim = pose["target"]
            dz = aim[2] - loc[2]
            horiz = math.hypot(aim[0] - loc[0], aim[1] - loc[1]) or 1.0
            return abs(math.degrees(math.atan2(dz, horiz)))

        for pose in (husk, facade, span):
            self.assertLess(tilt(pose), 10.5)
        self.assertLess(math.dist((husk["location"][0], husk["location"][1]), MIURA), 8.0)
        self.assertLess(math.dist((husk["target"][0], husk["target"][1]), MIURA), 2.0)
        self.assertGreater(facade["target"][0], 6.0)
        self.assertLess(math.dist((span["target"][0], span["target"][1]), FALLEN), 3.0)
        self.assertLess(span["location"][2], 2.4)
        self.assertGreater(husk["lens"], 32.0)

    def test_loop_matches_the_opening_pose(self):
        self.assertLess(math.dist(self.poses[0]["location"], self.poses[-1]["location"]), 0.01)
        self.assertLess(math.dist(self.poses[0]["target"], self.poses[-1]["target"]), 0.01)
        self.assertAlmostEqual(self.poses[0]["lens"], 28.0, places=1)
        self.assertAlmostEqual(self.poses[-1]["lens"], 28.0, places=1)
        return_at = next(beat["start"] for beat in self.resolved["beats"] if beat["id"] == "return")
        landed = int((return_at - 0.4) * self.fps)
        self.assertLess(math.dist(self.poses[0]["location"], self.poses[landed]["location"]), 0.05)
        self.assertLess(math.dist(self.poses[0]["target"], self.poses[landed]["target"]), 0.05)

    def test_the_move_stays_slow(self):
        peak = 0.0
        for left, right in zip(self.poses, self.poses[1:]):
            step = math.dist(left["location"], right["location"]) * self.fps
            peak = max(peak, step)
        self.assertGreater(peak, 0.5)
        self.assertLess(peak, 9.0)


if __name__ == "__main__":
    unittest.main()
