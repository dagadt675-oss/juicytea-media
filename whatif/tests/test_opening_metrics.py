"""The opening metric reads a segmented frame the way it reads zenith.

Run from whatif/:  python3 -m unittest tests.test_opening_metrics
"""

from __future__ import annotations

import unittest

import numpy as np

from engine.opening_metrics import (
    IDX_CANOPY,
    IDX_DECK,
    IDX_PORTAL,
    ZENITH,
    measure_masks,
    rel_error,
)


class OpeningMetricTest(unittest.TestCase):
    def test_known_masks_match_the_zenith_targets(self):
        height, width = 400, 200
        index = np.zeros((height, width), dtype=np.int32)
        image = np.zeros((height, width, 3), dtype=np.uint8)
        # Portal legs. Outer span is 18% of the width. Top at 14%, contact near 51.5%.
        top = int(0.14 * height)
        contact = int(0.515 * height)
        left0 = int(0.60 * width)
        left1 = int(0.62 * width)
        right0 = int(0.76 * width)
        right1 = left0 + int(round(0.180 * width)) - 1
        # A deck whose center sits between the legs and widens toward the camera.
        # 22.2% at y=0.58, 30% at y=0.78. Slope is built to be near 57°.
        for y in range(int(0.50 * height), int(0.90 * height)):
            t = (y / height - 0.58) / (0.78 - 0.58)
            span = 0.222 + (0.300 - 0.222) * t
            center = 0.70 + 0.18 * (y / height - 0.50)
            half = span / 2.0
            x0 = int(round((center - half) * width))
            x1 = int(round((center + half) * width))
            x0 = max(0, min(width - 1, x0))
            x1 = max(x0 + 1, min(width, x1))
            index[y, x0:x1] = IDX_DECK
            image[y, x0:x1] = (33, 44, 66)
        # Legs are in front of the deck edges, so they win the index at the contact.
        index[top:contact, left0:left1] = IDX_PORTAL
        index[top:contact, right0:right1] = IDX_PORTAL
        # Two foreground canopies, each 5.5% of the frame.
        canopy = int(round(0.055 * width))
        for cx, cy in ((0.12, 0.70), (0.22, 0.76)):
            x = int(cx * width)
            y = int(cy * height)
            index[y : y + canopy, x : x + canopy] = IDX_CANOPY
        metrics = measure_masks(index, image)
        self.assertLess(rel_error(metrics["portal_outer_width"], ZENITH["portal_outer_width"]), 0.05)
        self.assertLess(rel_error(metrics["portal_height"], ZENITH["portal_height"]), 0.05)
        self.assertLess(rel_error(metrics["deck_width_bank"], ZENITH["deck_width_bank"]), 0.05)
        self.assertLess(rel_error(metrics["deck_width_bottom"], ZENITH["deck_width_bottom"]), 0.05)
        self.assertLess(color_ok(metrics), 0.02)
        self.assertGreaterEqual(metrics["tree_canopy"], 0.05)
        self.assertLessEqual(metrics["tree_canopy"], 0.06)

    def test_layout_still_lands(self):
        from engine.city_layout import layout_errors

        self.assertEqual(layout_errors(), [])


def color_ok(metrics):
    got = metrics["deck_rgb"]
    target = ZENITH["deck_rgb"]
    return sum(abs(a - b) for a, b in zip(got, target)) / (3.0 * 255.0)


if __name__ == "__main__":
    unittest.main()
