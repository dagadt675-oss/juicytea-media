"""Math for the VFX core. No pixels of a full frame."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.vfx_core import (  # noqa: E402
    badge_state,
    cloud_alpha,
    ease_in_out_cubic,
    ease_in_out_quintic,
    exp_zoom,
    impact_shake,
    overshoot,
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
    assert overshoot(0.15) > 1.0
    # Shake is zero unless a caller opts in, and it is gone after 0.3 s.
    assert impact_shake(1.0, 1.0, dur=0.0) == (0.0, 0.0)
    assert impact_shake(0.0, 1.0, dur=0.25) == (0.0, 0.0)
    assert impact_shake(1.4, 1.0, dur=0.9) == (0.0, 0.0)
    dx, dy = impact_shake(1.05, 1.0, dur=0.25, amp=8)
    assert dx != 0.0 or dy != 0.0
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
