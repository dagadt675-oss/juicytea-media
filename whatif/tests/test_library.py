"""Asset swap and the sound-effects-only plan.

Run from whatif/:  python3 -m unittest tests.test_library
"""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.assets import choose, existing_path, fit_scale, height_scale
from engine.overlay import ui_state
from engine.spec import load_yaml, resolve, sfx_document, words_document

SPEC = Path(__file__).resolve().parents[1] / "episodes" / "humans_disappeared.yaml"


class AssetRegistryTest(unittest.TestCase):
    def test_people_and_cars_normalize_to_real_sizes(self):
        person = choose("person", "person")
        self.assertEqual(person["source"], "file")
        self.assertEqual(person["target_height"], 1.75)
        self.assertIsNotNone(existing_path(person))
        car = choose("car", "sedan")
        self.assertEqual(car["target_length"], 4.6)
        self.assertAlmostEqual(height_scale(1.0, 8.0), 8.0)
        self.assertEqual(fit_scale((2.0, 4.0, 1.0), (4.6, 1.8, 1.5)), (2.3, 0.45, 1.5))

    def test_trees_and_towers_stay_procedural_until_a_pack_is_enabled(self):
        tree = choose("tree", "round")
        self.assertEqual(tree["source"], "procedural")
        self.assertIsNone(existing_path(tree))
        tower = choose("building", "tower")
        self.assertEqual(tower["id"], "facade_tower")
        parked = choose("tree", "pine")
        self.assertEqual(parked["source"], "procedural")


class SoundPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolved = resolve(load_yaml(SPEC))

    def test_no_narration_and_no_music(self):
        audio = self.resolved["audio"]
        self.assertFalse(audio["narration"])
        self.assertFalse(audio["music"])
        self.assertTrue(audio["sfx"])
        self.assertEqual(self.resolved["ui"]["text"], ["title", "counter"])
        words = words_document(self.resolved)
        self.assertEqual(words["words"], [])
        self.assertFalse(words["narration"])

    def test_sfx_covers_the_decay(self):
        sheet = sfx_document(self.resolved)
        self.assertFalse(sheet["policy"]["narration"])
        self.assertFalse(sheet["policy"]["music"])
        beds = {bed["kind"] for bed in sheet["beds"]}
        self.assertTrue({"city", "wind", "birds", "water"} <= beds)
        kinds = {cue["kind"] for cue in sheet["cues"]}
        self.assertTrue({"creak", "rust", "glass", "collapse"} <= kinds)
        city = next(bed for bed in sheet["beds"] if bed["kind"] == "city")
        wind = next(bed for bed in sheet["beds"] if bed["kind"] == "wind")
        self.assertEqual(city["start"], 0.0)
        self.assertGreaterEqual(wind["start"], city["gain"][-1]["t"])
        collapse = [cue for cue in sheet["cues"] if cue["kind"] == "collapse"]
        self.assertGreaterEqual(len(collapse), 2)
        for cue in sheet["cues"]:
            self.assertIsNone(cue["file"])

    def test_onscreen_text_is_the_title_and_the_counter(self):
        opening = ui_state(self.resolved, 1)
        self.assertTrue(opening["title"])
        self.assertEqual(opening["label"], "WORLD POPULATION")
        self.assertEqual(opening["ticker"], "")
        year = ui_state(self.resolved, 490)
        self.assertEqual(year["title"], "")
        self.assertEqual(year["number"], "1")
        self.assertEqual(year["unit"], "YEAR")
        self.assertEqual(year["ticker"], "")


if __name__ == "__main__":
    unittest.main()
