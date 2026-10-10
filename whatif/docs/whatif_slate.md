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

Street-level, real seconds, bright flat low-poly. The reusable place is `nyc_avenue`. `rio_beach` is the next one, for an ocean that pulls back. The anomaly in a 45–60 s short starts by about 2 seconds.

Presets and channels, meant for surreal rules rather than explosions:

- `gravity_off` lifts loose props, holds them, then crashes them back down
- `scatter` and `inertia` throw them (the stand-in for a rigid-body bake)
- `fracture` shifts tower tops
- `wind` and `dust`
- `wave` brings a wall in; `ocean_pull` draws the water plane away

The HUD shows gravity in m/s², speed, a 180 lb person's weight, time left, and failure. Critical turns red. A faint countdown sits on the right.

A small figure with a red sign is placed off to the side of each scene unless the spec sets `mascot: false`. It is an Easter egg, not a character in the story.

A spec chooses the camera with `camera.mode`. `locked` is the wide shot used by episode 1 and the avenue. `pov` is one unbroken first-person path: keys of time, location, look target, and a `grab` name. Cylinder arms on the camera reach toward those grab points. That aim is the stand-in for IK. Second-person lines ("Grab something.") stay in the beat narration until a POV episode is actually cut. They are not burned into episode 1.

Not built yet, on purpose: a city-park picnic set (blanket, bench, trash can, flagpole) and a cartoon cat rig with idle, float, and held poses. Those are self-built or CC0 when a POV short is scheduled. `episodes/gravity_cat_pov.yaml` only records the path. Do not treat it as a renderable film.

Earth stopped spinning uses the avenue, not the slate's orbital globe. The count returns and the street is intact, so the shot can loop. Gravity switched off is the same avenue and the `gravity_off` preset.

## What a spec can already draw

A single low-sample frame renders for every format A spec above, and for the format C street spec. Only the humans episode is being finished to the reference reel. The others are scenes plus counters, not finished films.
