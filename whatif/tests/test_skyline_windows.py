"""Visual lock: a tower facade must keep a window grid.

Run from whatif/:  python3 -m unittest tests.test_skyline_windows
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from render_episode import blender_bin


class SkylineWindowTest(unittest.TestCase):
    def test_facade_is_not_a_blank_wall(self):
        probe = Path(__file__).resolve().parent / "skyline_windows.py"
        subprocess.check_call([blender_bin(), "--background", "--python", str(probe)])
        report = json.loads(Path("/tmp/skyline_window.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(report["wall"], 0.35)
        self.assertGreaterEqual(report["dark_fraction"], 0.12)
        self.assertLessEqual(report["dark_fraction"], 0.80)
        self.assertGreaterEqual(report["bands"], 4)


if __name__ == "__main__":
    unittest.main()
