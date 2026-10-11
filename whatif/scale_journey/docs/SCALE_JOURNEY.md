# Scale-journey

A Short is one question, one zoom, and a counter that is the same math as the zoom.

```
hook (frame 0) → unbroken dolly → a reference every 3–5 s → reality-check card → dissolve to frame 0
```

Zoom **out** for growth (`direction: out`). Zoom **in** for shrinking (`direction: in`). The camera never sways, never pans, and never reverses. Pitch is constant. The ending dissolve is a crossfade back to the opening plate, not a camera move.

The bottom band y 1229–1382 is left empty for karaoke captions.

## Why the scenes swap

Blender’s meshes are float32. A camera that travels from a grain of rice to a galaxy in one coordinate system falls apart. Each layer is its own scene, built so the subject is a few Blender units tall:

```
true metres  →  layer.meters_per_bu  →  Blender coordinates near the origin
```

Neighbouring layers overlap in log(height). The host crossfades their plates. Python (float64) keeps the real size; Blender never sees it. `tests/test_scale_journey.py` checks that every layer’s camera stays in a float32-safe range, including orbit through the cosmic web and the micro stack down to a proton.

### Layers

Zoom out: `interior`, `city`, `aerial`, `orbit`, `cislunar`, `solar`, `galaxy`, `cosmic`.

Zoom in: `room`, `tabletop`, `fibers`, `cells`, `viruses`, `molecules`, `atoms`, `atom_void`, `nucleus`, `proton`.

An episode only renders the layers its size range actually enters. The rice episode stops in the aerial layer (the pile is about 4.7 km). The shrink episode runs the micro stack.

## Authoring an episode

Copy `episodes/rice_64.yaml` or `episodes/shrink_half.yaml`. The fields that matter:

```yaml
schema: scale_journey/1
id: my_episode
title: "What if …?"
status: final          # or stub
module: scale_journey  # so the parent engine can dispatch
fps: 30
width: 1080
height: 1920
direction: out         # or in
caption_band: [1229, 1382]

timing:
  hook_hold: 2.6       # camera stays on the opening
  journey_end: 35.4    # dolly arrives, reality-check begins
  ending_hold: 4.2
  dissolve: 0.7        # crossfade to frame 0

camera:
  lens_mm: 30
  sensor_height_mm: 24
  sensor_fit: VERTICAL
  pitch_deg: 26        # constant
  look_frac: 0.42      # look-at height as a fraction of the subject
  framing: 0.50        # subject height / frame, once the dolly is moving
  hold_distance_m: 0.105

counter:
  primary:   {label: DAYS, source: day}       # or source: second
  secondary: {label: HEIGHT, source: length}  # auto units

quantity:
  preset: rice_doubling   # or shrink_half
  # preset constants, all cited under sources:

milestones:
  - id: person
    t: 14.0                # seconds. Must increase. Aim for a 3–5 s gap.
    match_height_m: 1.70  # or day:, second:, match_volume_m3:
    proxy: person          # person | house | tower | spire | monument | peak | marker | grain
    proxy_height_m: 1.70
    label: "A PERSON"
    sub: "1.70 m"
    fact: "As tall as a person, 1.70 m."   # top line, during the journey
    say: "The pile is as tall as a person." # goes into timeline.json for the read
    word: person           # optional ElevenLabs lock
```

`{height}`, `{grains}`, `{years}`, `{day}`, `{mass}` in `fact`, `sub`, `label`, and the ending lines are filled from the preset. The ending card cannot drift from the math.

Templates in the ending:

```yaml
ending:
  highlight: "{years}"
  lines:
    - "Day 64 alone."
    - "About {years} years of Earth's rice harvest."
```

List every measurement under `sources`. The two shipped episodes already do. Fact-check those before publishing; kernel mass and the repose angle in particular are scenario choices inside published ranges, and the on-screen years follow from them.

### Quantity presets

`rice_doubling` — day 1 is 1 grain, day n is `2^(n-1)` grains (the pile that day, not the sum of every previous day). Height is a cone at `repose_deg`. A lone grain uses its real thickness instead of the cone.

`shrink_half` — height = `start_m × 2^(−seconds)`. The counter’s seconds are that clock.

### Retiming to a voiceover

`words.json` is an ElevenLabs word list:

```json
{"words": [{"word": "empire", "start": 27.4, "end": 27.9}]}
```

Pass `--words`. Each milestone with a `word` moves to that word’s start. Moves that would reverse the zoom, or land outside the journey, are refused and reported in `timeline.json` under `retime_warnings`. The camera stays monotonic.

### timeline.json

Written even with `--timeline-only`. Use it to write the read and to place karaoke inside the free band.

- `beats[]` — hook, each milestone, ending, with `start`, `end`, `narration`
- `milestones[]` — time, frame, label, sub, height, the parameter (day or second)
- `counters[]` — every frame: `t`, `param`, `height`, `height_m`, `grains`, active layers

## Render flags

| Flag | Effect |
| --- | --- |
| `--timeline-only` | JSON only |
| `--preview` | Schematic plates, no Blender, for timing and type |
| `--frames 0,420` | Only these frames |
| `--milestone-frames` | One frame per milestone |
| `--samples N` | Cycles samples. The shipped look is 1, direct light, analytic sky |
| `--scale 50` | Render percentage. UI is always composited at 1080×1920 |
| `--words FILE` | Retime milestones |
| `--blender PATH` | Blender binary |

The 1-sample look is a choice, not a default of laziness. On this CPU, Eevee Next was about 55 s/frame and a Nishita sky at 1 sample was noise. Direct suns, a diffuse wood photograph, and a colour-ramp sky are clean at 1 sample and about 2 s/frame. Turn `--samples` up if you want the roughness and normal maps in `assets/textures/` wired back on; they are licensed and present, and currently unused because JPEG normals speckle at 1 sample.

## Two episodes

**rice_64** — zoom out. One grain doubled every day for 64 days. Day 64 is `2^63` grains, a cone about 4.7 km tall (scenario kernel and 34° repose), on the order of 360 years of the FAO 2024/25 milled-rice harvest. References: tablespoon, bowl, person, house, Statue of Liberty, Empire State, Burj Khalifa, Mont Blanc.

**shrink_half** — zoom in. You start at 1.70 m and halve every second, down to a proton’s CODATA 2022 rms charge radius. The long empty stretch inside the atom is two narration beats, not invented objects.
