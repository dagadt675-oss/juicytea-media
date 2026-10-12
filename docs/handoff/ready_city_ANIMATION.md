# Ready city animation plan

Kristóf approved the four stills and the street-level walk. The ending showcase does not rise. It stays at eye height and glides in on one hero: the Day 1 Miura, left where it stopped, rusted and overgrown. Then the camera eases back to the opening so the loop matches.

The proof stills stay on the higher frame in `ready_city.py` (`CAM_LOC` z = 3 m). The film uses `camera.path` in `whatif/episodes/ready_city.yaml`. While that path is set, a beat cannot take the camera anywhere else.

## Camera

One move, no cuts. Height is 1.70 m for the whole film. Lens stays 28 mm. Every leg eases in and out (smoothstep), so speed is zero at each key. Nothing snaps, and nothing climbs.

| Time | Move |
| --- | --- |
| 0–6 s | Hold at `(0, -66, 1.70)`, looking at `(0, -26, 2.40)`. Opening and the vanish. |
| 6–20 s | Slide to the right curb at `(4.2, -63.8, 1.70)`, still looking down the street. This line stays clear of the ferns in the roadway. |
| 20–33 s | A short drift along that curb. Year 100 passes here. The look eases onto the Miura at `(-0.40, -54, 1.35)`. |
| 33–44 s | The showcase. A slow glide along the curb to `(3.6, -56.6, 1.70)`, about 4.8 m off the car's front-right. Height stays 1.70 m. The ruined street is behind the car. |
| 44–55.5 s | Ease back along the same curb to the opening pose. Speed is zero at both ends. The pose at 55.5 s is the pose at 0 s. |
| 55.5–60 s | Hold the opening pose. The city returns underneath it at 55.8 s, so the last frame is the first frame. |

The hero is the Miura because it is the same car from Day 1 and it sits in the roadway. The glide uses the right curb so the lens is not inside the ferns. The dome and the fallen wall stay in the background of this shot.

### Why the loop does not pop

The opening pose and the pose from 55.5 s through 60 s are the same point, the same look, and the same lens. The way back is one eased leg, not a cut. The city reset is the existing return beat: it fires at 55.8 s, after the camera is already on the opening pose, and the picture then holds. The last frame and the first frame share that camera, and both show Day 1.

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
| Year 500 | frame 1096, then the push-in | The right-tower corner lies in the avenue. Ivy and the broadleaf trees fill the sidewalks. The dome is cracked. The Miura is the same car, rusted and half buried. The sun is lower and warmer, with a faint volume. The camera then glides in on that car at eye height. |

Spatial order inside each era: curb and wall base first, then the centre of the road, then up the facade. The near foreground and the far end of the avenue decay together. Nothing clean is left beside something already overgrown, except the upper floors, which stay cleaner than the bases until year 500.

## Check frames for the push-in

Frame 1 is t = 0. These are the showcase checks, not a full render. Height is 1.70 m in every one.

| Still | Frame | Time | What it is |
| --- | --- | --- | --- |
| start | 991 | 33.0 s | Year 500 is on. The look has found the Miura. The push begins. |
| mid | 1156 | 38.5 s | Halfway through the glide, still at eye height. |
| end | 1321 | 44.0 s | The close view, about 4.8 m off the car's front-right, on the curb, ruin behind it. |
| return | 1681 | 56.0 s | Back on the opening pose. The city has returned, so this matches frame 1. |
