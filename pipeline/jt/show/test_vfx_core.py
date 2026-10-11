"""Math for the VFX core. No pixels of a full frame."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.vfx_core import (  # noqa: E402
    badge_state,
    cloud_alpha,
    _spring,
    ease_in_out_cubic,
    ease_in_out_quintic,
    exp_zoom,
    impact_shake,
    motion_jolt,
    overshoot,
    perlin_shake,
    place_labels,
    shadow_offset,
    stress_glow,
)


def main() -> None:
    assert ease_in_out_cubic(0) == 0 and ease_in_out_cubic(1) == 1
    assert ease_in_out_quintic(0) == 0 and abs(ease_in_out_quintic(1) - 1) < 1e-9
    assert ease_in_out_cubic(0.5) == 0.5
    assert abs(exp_zoom(80, 20, 0.5) - (80 * 20) ** 0.5) < 1e-6
    assert overshoot(0) == 0 and overshoot(1) == 1
    assert overshoot(0.15) <= 1.0
    assert _spring(0.15) > 1.0
    # Shake, sway, and jolts stay at zero. They are not a QC tool.
    assert impact_shake(1.05, 1.0, dur=0.25, amp=8) == (0.0, 0.0)
    assert perlin_shake(1.2, amp=12) == (0.0, 0.0)
    assert motion_jolt(1.0, 1.0, amount=4) == 0.0
    assert shadow_offset(540, 400, zoom=2)[1] > 0
    assert badge_state(0.0) == (0.0, False)
    assert badge_state(5 / 30)[1] is False
    assert badge_state(6 / 30)[1] is True
    assert cloud_alpha(1.0) > 0.5 and cloud_alpha(4.0) == 0.0
    assert stress_glow(1.2, [(1.0, 0.4)]) > 0.5
    assert stress_glow(3.0, [(1.0, 0.4)]) == 0.0
    nudged = place_labels([(100, 100, 80, 40), (100, 100, 80, 40)])
    assert nudged[1][1] > nudged[0][1]
    print("vfx_core tests ok")


if __name__ == "__main__":
    main()
