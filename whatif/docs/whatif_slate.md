# What-if episode slate

Episode 1 is the one we finish first. The scene and effect libraries are shaped so the rest of the slate is a new spec, not a new film.

| # | Title | Scene | Effects the spec drives |
| --- | --- | --- | --- |
| 1 | What if all humans disappeared? | River city, bridge, park, suburbs | vanish, power failure, flood, vegetation, collapse, sag, rust, ice, geology |
| 2 | What if it never stopped snowing? | Same city | snow, sag, collapse, ice |
| 3 | What if the oceans disappeared? | Coast, ships, seabed | water (negative), dust |
| 4 | What if it rained nonstop for a year? | River city | rain, flood, wet, mud, vegetation |
| 5 | What if Earth's gravity halved? | River city | gravity (float, taller plants, choppier water) |
| 6 | What if every insect vanished? | Forest and farm | wilt, fauna, vegetation |
| 7 | What if all ice melted? | Coast city | water / flood in steps, sealevel counter |
| 8 | What if a heatwave never ended? | City or farm | heat, scorch, dust, fire, cracks |

## Libraries

Scenes, selected by `scene.pieces`:

- `city`, `river`, `bridge` — the episode 1 diorama
- `suburbs` — wooden houses that can collapse
- `forest` — overgrowth inside a city, or a standalone forest
- `farm` — crops, flowers, birds, animals
- `coast` — beach, seabed, ships; with `city`, a coast city
- `power`, `subway` — episode 1 story beats

Effects are 0..1 channels ( `water` is signed: negative drops a water body):

- Water level: `flood` rises, `water` rises further or drops to a dry seabed
- Weather particles: `rain`, `snow`, `dust`, `ash`
- Plants: `vegetation` grows, `wilt` kills crops and flowers
- Materials: `rust`, `moss`, `snow`, `mud`, `scorch`, `wet`, `heat`, `ice`
- Structure: `collapse`, `sag`
- `gravity` lifts and bobs loose objects, stretches plants, roughens water
- `vanish` removes people, then cars; `fauna` removes birds and animals
- `geology` swaps the skyline for a stratigraphic wall with a thin red seam

The on-screen counter modes are `population`, `time`, `sealevel`, and `temperature`. The beat's `time_label` is the step (`1 YEAR`, `+12%`, `49°C`).

Specs live in `whatif/episodes/`. Only `humans_disappeared.yaml` is a finished episode. The others are stubs.
