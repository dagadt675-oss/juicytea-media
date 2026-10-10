# What-if slate

This replaces the earlier eight-episode list.

Format A is a locked camera and a time-lapse. One YAML spec plus a scene. Format B, the scale journey, is another agent's module. Format C is a real-time disaster on the same city, at street level.

## Format A (this engine)

| Episode | Scene | What the spec drives |
| --- | --- | --- |
| What if all humans disappeared? | River city | vanish, power, flood, vegetation, collapse, rust, ice, geology |
| What if it never stopped snowing? | River city | snow, sag, collapse, ice |
| What if the oceans drained? | `mauna_kea` | water below zero, sand, dust, erosion |
| What if all the ice melted? | `ny_harbor` | water and flood, sea-level counter |
| What if it rained for a million years? | River city | rain, flood, mud, erosion, geology |
| What if a burger sat out for 15 years? | `kitchen` | sag, wilt, vegetation (mold) |

Shared format A pieces: global timeline, water plane (rise and drop), snow and sand buildup, vegetation, ice swap (canopy to bare branches), erosion, wet/dry, sag/crack/collapse, rain/snow/wind/fog, day/night/season.

## Format C

What if the Earth stopped spinning? Real seconds, not a time-lapse. Countdown, then loose props keep their speed when the ground stops, towers fracture, dust and wind, a wave wall, an underwater grade, and a status HUD. The spin returns and the count is five again, so the shot can loop.

The launch curve stands in for a rigid-body bake. Replacing it does not require a new city.

## Shared with format B

Word timings are written as `words.json` in the same `{w, t0, t1}` shape as `pipeline/examples/lax_tokyo/words.json`. Captions, label pills, and the scale-journey camera stay on that agent's branch. This engine does not copy them.
