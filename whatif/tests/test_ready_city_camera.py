"""The ready-city film camera stays at eye height and walking pace."""

import math
import unittest
from pathlib import Path

from engine.spec import load_resolved, sample_camera_path

ROOT = Path(__file__).resolve().parents[1]


class ReadyCityCameraTest(unittest.TestCase):
    def setUp(self):
        self.resolved = load_resolved(ROOT / "episodes" / "ready_city.yaml")
        self.path = self.resolved["camera"]["path"]

    def test_no_beat_takes_the_camera(self):
        self.assertTrue(self.path)
        for beat in self.resolved["beats"]:
            self.assertIsNone(beat.get("camera"), beat["id"])

    def test_eye_height_and_no_rise(self):
        height = None
        look = None
        for key in self.path:
            z = key["location"][2]
            self.assertGreaterEqual(z, 1.6)
            self.assertLessEqual(z, 1.8)
            if height is None:
                height = z
                look = key["target"][2]
            self.assertEqual(z, height)
            self.assertEqual(key["target"][2], look)
        frames = self.resolved["frame_count"]
        for frame in range(1, frames + 1):
            pose = sample_camera_path(self.path, (frame - 1) / (frames - 1))
            self.assertAlmostEqual(pose["location"][2], height)
            self.assertAlmostEqual(pose["target"][2], look)

    def test_walking_pace_and_a_closed_loop(self):
        frames = self.resolved["frame_count"]
        fps = self.resolved["fps"]
        poses = [
            sample_camera_path(self.path, (frame - 1) / (frames - 1))
            for frame in range(1, frames + 1)
        ]
        peak = 0.0
        for left, right in zip(poses, poses[1:]):
            step = math.dist(left["location"], right["location"])
            peak = max(peak, step * fps)
        self.assertLess(peak, 1.5)
        self.assertGreater(peak, 1.0)
        self.assertLess(math.dist(poses[0]["location"], poses[-1]["location"]), 0.01)
        self.assertLess(math.dist(poses[0]["target"], poses[-1]["target"]), 0.01)


if __name__ == "__main__":
    unittest.main()
