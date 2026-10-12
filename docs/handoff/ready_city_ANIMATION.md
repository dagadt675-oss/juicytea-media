# Ready city animation plan

Kristóf approved the four stills and the street-level walk. One addition: at the end, in the Year 500 era, the camera rises once to show the ruined city, then eases back to the opening so the loop matches.

The proof stills stay on the higher frame in `ready_city.py` (`CAM_LOC` z = 3 m). The film uses `camera.path` in `whatif/episodes/ready_city.yaml`. While that path is set, a beat cannot take the camera anywhere else.

## Camera

One move, no cuts. Lens stays 28 mm. Every leg eases in and out (smoothstep), so speed is zero at each key. Nothing snaps.

Until Year 500 the camera stays at eye height, 1.70 m, inside the roadway.

| Time | Move |
| --- | --- |
| 0–6 s | Hold at `(0, -66, 1.70)`, looking at `(0, -26, 2.40)`. Opening and the vanish. |
| 6–14 s | Dolly 7 m up the avenue to `(0.10, -59, 1.70)`, looking at `(0.05, -18, 2.40)`. About 0.9 m/s, peak about 1.3 m/s. This stops short of the Miura at y = -54. |
| 14–33 s | Drift back to `(0, -63, 1.70)`, still at 1.70 m. Year 100 passes during this. The ruin settles in. |
| 33–44 s | The only rise. From that eye-height view up to `(0, -66, 14)`, looking at `(0.05, -20, 5.50)`. Still in the avenue, above the street mist, looking along the overgrown street. |
| 44–47 s | Hold that view. This is the Year 500 showcase. |
| 47–55.5 s | Ease straight down to the opening pose. Speed is zero at both ends, and the pose at 55.5 s is the pose at 0 s. |
| 55.5–60 s | Hold the opening pose. The city returns underneath it at 55.8 s, so the last frame is the first frame. |

The rise starts only after the collapse channel has reached the Year 500 ruin (about 33 s). It does not climb during Day 1, the vanish, or Year 100.

### Why the loop does not pop

The opening pose and the pose from 55.5 s through 60 s are the same point, the same look, and the same lens. The way down is one eased leg, not a cut. The city reset is the existing return beat: it fires at 55.8 s, after the camera is already on the opening pose, and the picture then holds. The last frame and the first frame share that camera, and both show Day 1.

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
| Year 500 | frame 1096, then the rise | The right-tower corner lies in the avenue. Ivy and the broadleaf trees fill the sidewalks. The dome is cracked. The Miura is the same car, rusted and half buried. The sun is lower and warmer, with a faint volume. The camera then rises to show that same street from above the mist. |

Spatial order inside each era: curb and wall base first, then the centre of the road, then up the facade. The near foreground and the far end of the avenue decay together. Nothing clean is left beside something already overgrown, except the upper floors, which stay cleaner than the bases until year 500.

## Check frames for the rise

Frame 1 is t = 0. These are the drone-move checks, not a full render.

| Still | Frame | Time | What it is |
| --- | --- | --- | --- |
| start | 991 | 33.0 s | Eye height, Year 500 already on the street. The rise begins. |
| mid | 1156 | 38.5 s | Halfway up, eased. |
| end | 1321 | 44.0 s | The hold at 14 m, looking along the ruined avenue. |
| return | 1681 | 56.0 s | Back on the opening pose. The city has returned, so this matches frame 1. |
