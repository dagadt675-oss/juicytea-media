# What-if slate

Production copy of the approved slate (`whatif_slate_v1`). Format B (penny, hole through the Earth, rice, bricks, crowd) is the other agent's module. This engine owns format A, plus the street-level format C version of "Earth stopped spinning."

Frame-0 titles do not spoil the payoff. Counters hold at least 0.8 s. US units are the big number. Claims in a finished voiceover need a source. Loops return to frame 0.

## Format A

| Episode | Scene | Counter | Loop |
| --- | --- | --- | --- |
| What if every human vanished… right now? | River city | Population 8.2B to 0, then time | Cut back to the opening city |
| What if it started snowing… and never stopped? | `culdesac` | Day / snow depth (inches, then feet) | Thaw back to the first flake |
| What if we pulled the plug on the ocean? | `mauna_kea` | Sea level in feet, down to the average ocean depth | Water pours back |
| What if every glacier on Earth melted? | `ny_harbor` | Sea level in feet, up the Statue of Liberty | Water drains back |
| What if it rained… for a million years? | `desert` | Years of rain | The basin dries to the opening desert |
| Leave a burger on the counter for 15 years. | `kitchen` | Days, then years. Two burgers, no logos | Both are fresh again |

Shared format A pieces: one global 0..1 timeline, water plane (rise or drain), snow and sand buildup, vegetation, ice swap, erosion, wet/dry, sag, crack, collapse, rain, snow, wind, fog, day/night and season.

Later decay years in episode 1 are labeled in the script doc. The slate marks bridge, forest, and deep-time stamps as timings that have to follow that script.

## Format C

The slate's orbital "Earth stopped spinning" film is last and not this build. The street-level reel (a countdown, loose objects keeping their speed, a wave over the camera) is format C. Our version loops: the count returns to five and the street is intact. The reference ending is a "simulation complete" card and does not loop. We do not copy that card.

HUD: STATUS, rotation, structural failure, red when critical, a large faint countdown. Word timings are `words.json` with `{w, t0, t1}`, the same shape as the map pipeline. Format B's captions, pills, and scale camera stay on that branch.

## What a spec can already draw

A single low-sample frame renders for every format A spec above, and for the format C street spec. Only the humans episode is being finished to the reference reel. The others are scenes plus counters, not finished films.
