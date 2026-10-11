"""Math for the VFX core. No pixels of a full frame."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.show.vfx_core import (  # noqa: E402
    GRAIN_OPACITY,
    badge_state,
    barrel_shift,
    box_luminance,
    cloud_alpha,
    _spring,
    adaptive_blur,
    anamorphic_alpha,
    apply_focus_mask,
    apply_glitch,
    border_strands,
    camera_micro_offset,
    displace_line,
    flash_envelope,
    focus_amount,
    dust_opacity,
    glitch_active,
    ink_color,
    ink_widths,
    travel_blur_sigma,
    apply_light_spill,
    ease_in_out_cubic,
    ease_in_out_expo,
    icon_pop,
    cloud_alpha_for_span,
    ease_in_out_quintic,
    exp_zoom,
    impact_shake,
    label_style,
    motion_jolt,
    overlay_grain,
    overshoot,
    perlin_shake,
    place_labels,
    shadow_offset,
    spill_falloff,
    spring_approach,
    stress_glow,
)


def main() -> None:
    assert ease_in_out_cubic(0) == 0 and ease_in_out_cubic(1) == 1
    assert ease_in_out_expo(0) == 0 and ease_in_out_expo(1) == 1
    assert abs(ease_in_out_expo(0.5) - 0.5) < 1e-9
    assert icon_pop(0, 18) == 0.0 and abs(icon_pop(18, 18) - 1.0) < 1e-6
    assert 1.10 <= icon_pop(11, 18) <= 1.20
    assert cloud_alpha_for_span(90) > 0.8 and cloud_alpha_for_span(20) == 0.0
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
    # Spring snap: rest at 0, a small overshoot, then a settle. No leftover velocity.
    assert spring_approach(0.0, 1.0, 0.0) == 0.0
    assert spring_approach(0.0, 1.0, 0.25) > 1.05
    assert abs(spring_approach(0.0, 1.0, 0.70) - 1.0) < 0.02
    assert spring_approach(2.0, 5.0, 0.40) == spring_approach(2.0, 5.0, 0.40)
    # Long dives are not this integrator. exp_zoom stays the dive.
    assert abs(exp_zoom(100, 20, 1.0) - 20) < 1e-6
    assert abs(spill_falloff(0, 80, 1) - 1.0) < 1e-6
    assert abs(spill_falloff(160, 80, 1) - 0.2) < 1e-6
    assert spill_falloff(40, 80, 1) > spill_falloff(120, 80, 1)
    cx, cy = barrel_shift(539.5, 959.5, 1080, 1920)
    assert abs(cx - 539.5) < 1e-3 and abs(cy - 959.5) < 1e-3
    edge = barrel_shift(1070, 960, 1080, 1920)
    assert abs(edge[0] - 1070) > 0.2
    assert abs(edge[0] - 1070) < 12
    assert label_style(0.85)[0][0] < 40
    assert label_style(0.20)[1] == 0
    import numpy as np
    white = np.full((40, 40, 3), 250, np.uint8)
    black = np.zeros((40, 40, 3), np.uint8)
    assert box_luminance(white, 20, 20, 20, 20) > 0.70
    assert box_luminance(black, 20, 20, 20, 20) < 0.10
    assert 0.01 <= GRAIN_OPACITY <= 0.02
    base = np.full((64, 64, 3), 128, np.uint8)
    g0 = overlay_grain(base, 0.0, 30)
    g1 = overlay_grain(base, 1.0 / 30.0, 30)
    assert np.array_equal(g0, overlay_grain(base, 0.0, 30))
    assert not np.array_equal(g0, g1)
    assert float(np.mean(np.abs(g0.astype(np.int16) - base.astype(np.int16)))) < 8
    dist = np.zeros((24, 24), np.float32)
    dist[:] = 400
    dist[8:16, 8:16] = 0
    lit = apply_light_spill(black[:24, :24], dist, (0, 180, 255), radius=8, gain=0.8)
    assert lit[12, 12, 2] > lit[0, 0, 2]
    # Part 6 and 7. No constant sway. Effects stay small.
    assert camera_micro_offset(1.5) == (0.0, 0.0)
    moved = displace_line([(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)], 0.4, amp=1.2)
    assert max(abs(p[1]) for p in moved) <= 1.21
    assert displace_line([(0.0, 0.0), (10.0, 0.0)], 0.4, 1.2) == displace_line([(0.0, 0.0), (10.0, 0.0)], 0.4, 1.2)
    words = [{"w": "HUGE", "t0": 1.0, "t1": 1.4}]
    assert flash_envelope(0.5, words) == 0.0
    assert flash_envelope(1.16, words) > 0.9
    assert focus_amount(1.0, [{"t": 1.0, "type": "stress"}]) == 0.0
    assert focus_amount(1.2, [{"t": 1.0, "type": "stress", "style": "focus", "dur": 0.8}]) > 0.5
    assert travel_blur_sigma(0.0) == 0.0
    assert travel_blur_sigma(2.0, zoom=1.0) > travel_blur_sigma(2.0, zoom=6.0) > 0.0
    assert travel_blur_sigma(2.0) <= 2.0
    assert anamorphic_alpha(0.2) == 0.0
    assert abs(anamorphic_alpha(1.0) - 0.05) < 1e-6
    assert dust_opacity(0.0) == 0.0 and dust_opacity(1.0) <= 0.04
    assert glitch_active(1.0, 1.0, 30, 3) and not glitch_active(1.2, 1.0, 30, 3)
    torn = apply_glitch(np.full((40, 40, 3), 80, np.uint8))
    assert not np.array_equal(torn[:6], np.full((6, 40, 3), 80, np.uint8))
    line = [(float(i * 10), 0.0) for i in range(13)]
    early = border_strands(line, origins=4, progress=0.15)
    done = border_strands(line, origins=4, progress=1.0)
    assert len(early) >= 2 and len(done) >= 1
    widths = ink_widths(8, base=5.0, salt=3)
    assert widths.std() > 0.2
    soaked = ink_color((0, 0, 255))
    assert soaked[2] < 255 and soaked[0] > 0
    gray = np.full((360, 360, 3), 140, np.uint8)
    focused = apply_focus_mask(gray, 180, 180, travel=0.0, arrive=1.0)
    assert focused[180, 180, 0] > gray[180, 180, 0]
    assert focused[0, 0, 0] < gray[0, 0, 0]
    sharp = np.arange(16 * 16 * 3, dtype=np.uint8).reshape(16, 16, 3)
    mask = np.zeros((16, 16), np.bool_)
    mask[4:8, 4:8] = True
    blurred = adaptive_blur(sharp, 1.6, mask)
    assert np.array_equal(blurred[4:8, 4:8], sharp[4:8, 4:8])
    from jt.show.lod import lod_swap, level_for
    assert lod_swap(0.1) == 0.0 and lod_swap(0.9) == 1.0
    assert abs(lod_swap(0.5) - 0.5) < 1e-6
    assert level_for(80) == "globe" and level_for(20) == "regional" and level_for(4) == "local"
    from jt.show.admin_index import countries_in_bbox
    sweden = countries_in_bbox(10, 55, 25, 70)
    assert "SWE" in sweden and "BRA" not in sweden
    assert len(sweden) < 40
    print("vfx_core tests ok")


if __name__ == "__main__":
    main()
