"""Pure-Python checks. No Blender required."""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.camera import (  # noqa: E402
    float32_ok,
    layer_weights,
    layers_for,
    pose_for,
    project,
    to_bu,
)
from engine.overlay import compose  # noqa: E402
from engine.preview import plate  # noqa: E402
from engine.quantity import (  # noqa: E402
    RiceParams,
    choose_unit,
    format_length,
    harvest_years,
    rice_metrics,
)
from engine.spec import load_raw, resolve, retime_milestones, timeline_document  # noqa: E402

EPISODES = ROOT / "episodes"
RICE = EPISODES / "rice_64.yaml"
SHRINK = EPISODES / "shrink_half.yaml"


class QuantityTest(unittest.TestCase):
    def test_day64_is_two_to_the_63(self):
        p = RiceParams()
        m = rice_metrics(64, p)
        self.assertAlmostEqual(m.grains, 2**63, delta=1.0)

    def test_height_grows(self):
        p = RiceParams()
        prev = 0.0
        for day in (1, 8, 16, 32, 48, 64):
            h = rice_metrics(day, p).height_m
            self.assertGreater(h, prev)
            prev = h

    def test_units(self):
        self.assertEqual(choose_unit(0.004)[0], "mm")
        self.assertEqual(choose_unit(0.42)[0], "cm")
        self.assertEqual(choose_unit(12.0)[0], "m")
        self.assertEqual(choose_unit(4800)[0], "km")
        self.assertEqual(choose_unit(1.5e11)[0], "AU")
        self.assertEqual(choose_unit(1.0e16)[0], "ly")
        self.assertEqual(choose_unit(2e-6)[0], "um")
        self.assertIn("km", format_length(4840))

    def test_harvest_years_are_centuries_not_a_slogan(self):
        p = RiceParams()
        years = harvest_years(2**63, p)
        # With the spec's own constants this lands near a few centuries.
        self.assertGreater(years, 200)
        self.assertLess(years, 800)


class EpisodeTest(unittest.TestCase):
    def setUp(self):
        self.rice = resolve(load_raw(RICE))
        self.shrink = resolve(load_raw(SHRINK))

    def test_duration_band(self):
        self.assertGreater(self.rice.duration, 30)
        self.assertLess(self.rice.duration, 46)
        self.assertGreater(len(self.rice.frames), 900)

    def test_zoom_out_never_reverses(self):
        dists = [fr.distance_m for fr in self.rice.frames if fr.phase != "dissolve"]
        for a, b in zip(dists, dists[1:]):
            self.assertGreaterEqual(b + 1e-9, a)
        for fr in self.rice.frames:
            self.assertEqual(fr.pose_cam[0], 0.0)
            self.assertEqual(fr.pitch_deg, self.rice.frames[0].pitch_deg)

    def test_zoom_in_never_reverses(self):
        dists = [fr.distance_m for fr in self.shrink.frames if fr.phase != "dissolve"]
        for a, b in zip(dists, dists[1:]):
            self.assertLessEqual(b - 1e-9, a)

    def test_milestone_cadence(self):
        times = [m.t for m in self.rice.milestones]
        gaps = [b - a for a, b in zip(times, times[1:])]
        for gap in gaps:
            self.assertGreaterEqual(gap, 3.0)
            self.assertLessEqual(gap, 5.0)
        # Shrink follows the halving clock, so a few famous sizes sit closer
        # than 3 s. Nothing should be under 2.4 s or over 6.2 s.
        st = [m.t for m in self.shrink.milestones]
        for gap in [b - a for a, b in zip(st, st[1:])]:
            self.assertGreaterEqual(gap, 2.4, msg=f"shrink gap {gap}")
            self.assertLessEqual(gap, 6.2, msg=f"shrink gap {gap}")

    def test_hook_title_is_on(self):
        self.assertEqual(self.rice.frames[0].phase, "hook")
        self.assertGreater(self.rice.frames[0].title_opacity, 0.9)
        # Title is gone once the zoom is underway.
        later = self.rice.frames[int(4 * self.rice.fps)]
        self.assertLess(later.title_opacity, 0.05)

    def test_loop_matches_open(self):
        first, last = self.rice.frames[0], self.rice.frames[-1]
        self.assertEqual(last.phase, "dissolve")
        self.assertGreater(last.dissolve, 0.9)
        self.assertEqual(first.param, self.rice.frames[1].param)

    def test_caption_band_clear(self):
        band = (1229, 1382)
        for ep in (self.rice, self.shrink):
            sample = ep.frames[:: max(1, len(ep.frames) // 12)]
            for fr in sample:
                _img, boxes = compose(plate(ep, fr), ep, fr)
                for box in boxes:
                    self.assertFalse(box[3] > band[0] and box[1] < band[1], msg=box)

    def test_every_height_has_a_layer(self):
        for direction, ep in (("out", self.rice), ("in", self.shrink)):
            for fr in ep.frames[::10]:
                weights = layer_weights(fr.metrics.height_m, direction)
                self.assertGreater(sum(weights.values()), 0.99)
                self.assertLessEqual(len(weights), 2)

    def test_float32_across_the_catalogue(self):
        # Every layer, at its short edge, its middle, and its tall edge.
        from engine.camera import LAYERS, layer_by_id

        for layer in LAYERS:
            direction = "out" if layer.family in ("macro", "space") else "in"
            for height in (layer.h_min * 1.05, math.sqrt(layer.h_min * layer.h_max), layer.h_max * 0.95):
                weights = layer_weights(height, direction)
                self.assertIn(layer.id, weights, msg=f"{layer.id} missing at {height}")
                pose = pose_for(
                    height,
                    direction,
                    height * 8 if direction == "in" else height * 0.01,
                    0.45,
                    20,
                    0.4,
                    32,
                    24,
                )
                layer = layer_by_id(layer.id)
                cam = to_bu(pose.cam, layer.meters_per_bu)
                target = to_bu(pose.target, layer.meters_per_bu)
                span = math.dist(cam, target)
                self.assertTrue(
                    float32_ok([cam, target, (0.0, 0.0, height / layer.meters_per_bu)], span),
                    msg=f"{direction} {layer.id} h={height:.3e} cam={cam}",
                )

    def test_timeline_shape(self):
        doc = timeline_document(self.rice)
        for key in ("id", "title", "fps", "width", "height", "duration_sec", "frame_count", "beats", "milestones", "counters"):
            self.assertIn(key, doc)
        self.assertEqual(doc["fps"], 30)
        self.assertEqual(doc["width"], 1080)
        self.assertEqual(doc["caption_band"], {"y0": 1229, "y1": 1382})
        self.assertEqual(len(doc["counters"]), doc["frame_count"])
        self.assertIn("years", " ".join(doc["ending"]))

    def test_retime_is_monotone(self):
        raw = load_raw(RICE)
        words = {
            "words": [
                {"word": "tablespoon", "start": 6.4, "end": 6.9},
                {"word": "bowl", "start": 10.5, "end": 10.8},
                {"word": "person", "start": 15.0, "end": 15.4},
                {"word": "empire", "start": 27.2, "end": 27.6},
                {"word": "blanc", "start": 34.8, "end": 35.2},
            ]
        }
        path = ROOT / "out" / "_words.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(words), encoding="utf-8")
        shifted = retime_milestones(raw, path)
        ep = resolve(shifted)
        times = [m.t for m in ep.milestones]
        self.assertEqual(times, sorted(times))
        by_id = {m.id: m.t for m in ep.milestones}
        self.assertAlmostEqual(by_id["spoon"], 6.4)
        dists = [fr.distance_m for fr in ep.frames if fr.phase != "dissolve"]
        for a, b in zip(dists, dists[1:]):
            self.assertGreaterEqual(b + 1e-6, a)

    def test_hook_grain_is_readable(self):
        fr = self.rice.frames[0]
        cam = self.rice.raw["camera"]
        from engine.camera import Pose

        pose = Pose(fr.pose_cam, fr.pose_target, fr.distance_m, fr.pitch_deg)
        a = project(pose, (0.0, 0.0, 0.001), 1080, 1920, cam["lens_mm"], cam["sensor_height_mm"])
        b = project(pose, (0.0066, 0.0, 0.001), 1080, 1920, cam["lens_mm"], cam["sensor_height_mm"])
        pixels = math.dist(a, b)
        self.assertGreater(pixels, 70, msg=f"grain only {pixels:.0f}px")
        self.assertLess(pixels, 280, msg=f"grain {pixels:.0f}px fills the frame")


class LayerFamilyTest(unittest.TestCase):
    def test_directions_do_not_share_layers(self):
        out_ids = {layer.id for layer in layers_for("out")}
        in_ids = {layer.id for layer in layers_for("in")}
        self.assertFalse(out_ids & in_ids)
        self.assertIn("orbit", out_ids)
        self.assertIn("proton", in_ids)
        self.assertIn("interior", out_ids)


if __name__ == "__main__":
    unittest.main()
