# Ready city animation plan

Kristóf, 2026-10-12: the camera is street-level and slow only. Eye height about 1.6–1.8 m. A gentle walking-speed dolly and pan, eased. No drone shots. No rising moves.

The proof stills stay on the higher frame in `ready_city.py` (`CAM_LOC` z = 3 m) so the buildings read in a single picture. The film does not use that height.

## Camera

One move, no cuts. The path is `camera.path` in `whatif/episodes/ready_city.yaml`. While that path is set, a beat cannot take the camera anywhere else. The four later beats that used to be inserts no longer have a camera.

Height is 1.70 m for the whole film. The look target stays at 2.40 m, so the tilt never climbs. The lens stays 28 mm. Nothing snaps. Each leg eases in and out.

| Time | Move |
| --- | --- |
| 0–6 s | Hold at `(0, -66, 1.70)`, looking at `(0, -26, 2.40)`. Opening and the vanish. |
| 6–26 s | Dolly 18 m up the avenue to `(0.30, -48, 1.70)`, looking at `(0.15, -10, 2.40)`. About 0.9 m/s on average, peak about 1.35 m/s. |
| 26–34 s | A short pan toward the left sidewalk, less than a metre of travel. Same height. |
| 34–54 s | Dolly back down the same line to the opening pose, same pace. |
| 54–60 s | Hold on the opening pose while the city returns, so the loop matches. |

The camera stays inside the roadway. It does not climb, crane, orbit, or leave the street.

## Ground-up, then outward

Decay starts on the ground and at the edges, then climbs. A later era only adds to the earlier one. The buildings keep the Day 1 silhouette until the year-500 collapse.

| Era | Still | What changes |
| --- | --- | --- |
| Day 1 | frame 1 | The living street. People walk. Feet meet the pavement. Cars and the Miura are where they drive. |
| Vanish | frame 88 | People are gone. Cars, including the Miura, are left where they stopped. The street is otherwise Day 1. |
| Months to 1 year | weeds beat | Cracks and the first weeds at the curbs only. Cars still shiny. Windows intact. |
| 20–50 years | streets, houses | Weeds reach the centre line. Cars dull and drop. Lower windows start to fail. Grime gathers at the base of walls, not the roofs. |
| Year 100 | frame 860 | Grass and weeds through cracked asphalt on both curbs and down the centre. Young trees, 3–6 m, on the sidewalks. Ivy on the lower two or three floors. Heavy grime and rain streaks. Many broken windows. The dome is stained. Cars are rust-brown, on flat tyres, with plants around them. No fallen tower yet. |
| 300 years | bridge beat | The same damage climbs. Upper floors stain. A few panels loosen. The street trees thicken. The tower is still standing. |
| Year 500 | frame 1096 | The right-tower corner lies in the avenue. Ivy and the broadleaf trees fill the sidewalks. The dome is cracked. The Miura is the same car, rusted and half buried. The sun is lower and warmer, with a faint volume. |

Spatial order inside each era: curb and wall base first, then the centre of the road, then up the facade. The near foreground and the far end of the avenue decay together. Nothing clean is left beside something already overgrown, except the upper floors, which stay cleaner than the bases until year 500.
