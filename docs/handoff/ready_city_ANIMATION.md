# Ready city animation plan

Kristóf approved the four stills and the street-level walk. The ending is the same camera language as the first episode (`humans_disappeared.yaml`): after Year 500, three slow low glides through the ruins, then a smooth return to the opening frame.

The old shots are `drone_husk`, `drone_facade`, and `drone_span`. Each one moves only a few metres, drops slightly, and tightens the lens. `drone_orbit` in that episode climbed to the aerial camera at z = 80. This film does not. The return lands on `(0, -66, 1.70)`.

The proof stills stay on the higher frame in `ready_city.py` (`CAM_LOC` z = 3 m). The film uses `camera.path` in `whatif/episodes/ready_city.yaml`. While that path is set, a beat cannot take the camera anywhere else.

## Camera

One eased move, no cuts. The street portion stays at 1.70 m. The three glides stay low, between about 1.25 m and 1.90 m. Nothing climbs over the street.

| Time | Move | Same language as |
| --- | --- | --- |
| 0–6 s | Hold at `(0, -66, 1.70)`, looking at `(0, -26, 2.40)`, 28 mm. Opening and the vanish. | |
| 6–24 s | Creep to `(0.4, -63, 1.70)`, still looking down the street. | |
| 24–36.5 s | Drift to the right curb as the ruin finishes. Year 100 is still on this low walk. | |
| 36.5–39.2 s | Pass over the rusted Miura at 1.90 m. Look stays within 10° of level. Leaves inside 1.2 m of the lens are removed. | `drone_husk` |
| 39.2–41.8 s | Level look at the sunlit window wall beside the cracked dome. The camera sits off the tree trunks. | `drone_facade` |
| 41.8–44.4 s | The windowed hub ruin lying across the avenue, seated on the ground. | `drone_span` |
| 44.4–55.5 s | Fly back to the opening pose. Speed is zero at both ends. | the old orbit's return, without the climb |
| 55.5–60 s | Hold the opening pose. The city returns underneath it at 55.8 s, so the last frame is the first frame. | |

### Why the loop does not pop

The opening pose and the pose from 55.5 s through 60 s are the same point, the same look, and the same lens. The way back is one eased leg. The city reset fires at 55.8 s, after the camera is already on the opening pose. The last frame and the first frame share that camera, and both show Day 1.

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
| Year 500 | frame 1096, then the three low glides | One Ruined City chunk lies across the avenue, windowed face toward the street, bottom on the ground. Ivy and the broadleaf trees fill the sidewalks. The dome is cracked. The Miura keeps its orange paint in flakes over downloaded rust and moss maps. The near tyre is hidden so it does not read as a loose copper tube. The camera then glides over that car, along the sunlit window wall, and past the fallen chunk. |

Spatial order inside each era: curb and wall base first, then the centre of the road, then up the facade. The near foreground and the far end of the avenue decay together. Nothing clean is left beside something already overgrown, except the upper floors, which stay cleaner than the bases until year 500.

## Check frames for the ending glides

Frame 1 is t = 0. These are the ending checks, not a full render.

| Still | Frame | Time | What it is |
| --- | --- | --- | --- |
| start | 1097 | 36.6 s | The rusted Miura. Downloaded rust and moss textures, with the original paint left in flakes. The near tyre that read as a copper tube is hidden. |
| mid | 1253 | 41.8 s | The sunlit window wall and the cracked dome. The tree trunk is at the left edge, not the middle of the frame. |
| end | 1331 | 44.4 s | The hub ruin chunk lying across the avenue. |
| return | 1681 | 56.0 s | Back on the opening pose. The city has returned, so this matches frame 1. |
