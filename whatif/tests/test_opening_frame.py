"""Day-1 full frame: river, lawn, street, light, and the locked camera.

Run from whatif/:  python3 -m unittest tests.test_opening_frame
The render is low resolution. It fails if the river, lawn, or avenue
disappears from the locked frame again.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from PIL import Image

from engine.overlay import draw_state
from engine.spec import load_yaml, resolve
from render_episode import ROOT, blender_bin

REPORT = Path("/tmp/opening_frame/report.json")


class OpeningFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = ROOT / "episodes" / "humans_disappeared.yaml"
        out = Path("/tmp/opening_frame")
        out.mkdir(parents=True, exist_ok=True)
        resolved = resolve(load_yaml(spec))
        resolved_path = out / "resolved.json"
        resolved_path.write_text(json.dumps(resolved), encoding="utf-8")
        subprocess.check_call(
            [
                blender_bin(),
                "--background",
                "--python",
                str(ROOT / "tests" / "opening_frame.py"),
                "--",
                str(resolved_path),
            ]
        )
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_locked_camera_landmarks(self):
        camera = self.report["camera"]
        self.assertEqual([round(v, 1) for v in camera["location"]], [-56.0, -42.0, 66.0])
        self.assertAlmostEqual(camera["lens"], 57.2, places=1)
        for name in ("skyline_y", "bank_y", "promenade_y", "portal_x", "portal_y"):
            row = self.report["landmarks"][name]
            self.assertLess(row["error"], 0.03, msg=f"{name} {row}")

    def test_river_lawn_light_and_street(self):
        # Tuned on the restored day-1 frame. A grey sheet with no water,
        # no lawn, and no painted street fails each of these.
        self.assertGreater(self.report["river_blue"], 0.35)
        self.assertGreater(self.report["park_green"], 0.22)
        self.assertGreater(self.report["mean_luma"], 0.32)
        self.assertGreater(self.report["bottom_street"], 0.32)
        self.assertGreater(self.report["bottom_white"], 0.015)
        self.assertGreater(self.report["bottom_yellow"], 0.008)

    def test_title_is_large_and_clear_of_the_portal(self):
        image = Image.new("RGB", (1080, 1920), (150, 180, 205))
        state = {
            "title": "What if every human vanished… right now?",
            "title_alpha": 1.0,
            "label": "WORLD POPULATION",
            "number": "8,200,000,000",
            "unit": "",
            "hud": None,
        }
        drawn = draw_state(image, state, 1080, 1920)
        pixels = drawn.convert("RGB").load()
        xs = []
        ys = []
        for y in range(int(1920 * 0.16)):
            for x in range(1080):
                red, green, blue = pixels[x, y]
                if red > 220 and green > 220 and blue > 220:
                    xs.append(x / 1080.0)
                    ys.append(y / 1920.0)
        self.assertGreater(len(xs), 400)
        self.assertGreaterEqual(min(xs), 60.0 / 1080.0 - 0.004)
        self.assertLess(max(xs), 0.47)
        self.assertGreater(max(xs) - min(xs), 0.20)
        self.assertLess(sum(ys) / len(ys), 0.12)


if __name__ == "__main__":
    unittest.main()
