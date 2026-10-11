# Penny / scale-journey handoff

Updated 2026-10-11, end of the Colab-bundle run. Branch `cursor/penny-lookdown-chase-d7c6`. The packed blend was baked at commit `657a956`. This handoff is the commit on top of that. PR https://github.com/dagadt675-oss/juicytea-media/pull/9 (draft).

**Standing instruction for every future agent:** at the end of your run, update this file in place and copy it to `/opt/cursor/artifacts/handoff/penny_scale_HANDOFF.md`. Do not let the chat be the only record.

This file plus the repo is enough to continue. Do not assume a fresh VM still has `/tmp` renders, the Blender 4.2 tarball, or the private asset cache.

---

## 1. Mission and current state

Juicy Tea makes vertical what-if Shorts. This checkout is the **scale-journey** module plus the **penny drop** episode, which is the only format-B episode that is a full 3D picture. The other format-B episodes resolve to timelines and an instancer. They are not rendered scenes.

### Penny drop (`penny_empire`) — active job

Question: could a penny dropped from the Empire State Building kill someone? Answer on screen: no. It flutters, locks at about 25 mph (40.3 km/h), taps a pedestrian, and he shrugs it off.

Picture spec that is locked:

- 1080×1920, 30 fps, **33.40 s, 1002 frames** (0 through 1001).
- Silent plates. Brian’s narration is the clock. Karaoke and the Anton counter are composited **after** the 3D plates, not inside Blender.
- Frame 1001 is the same pose as frame 0. When assembling, **copy `frames/0000.png` over `frames/1001.png`** so the seam has no motion smear.
- Physics, three-shot grammar, and the pedestrian reaction are in `whatif/scale_journey/engine/bformat.py` and `build_b.py`. See section 5.

**Where this run stopped.** The 1002-frame film is **not** rendered locally and **not** committed as an mp4. Kristóf moved final frames to a Google Colab GPU (Tesla T4, OptiX). This VM builds, tests, and hands over a packed blend.

The bundle is ready:

- `/opt/cursor/artifacts/colab_bundle/penny_empire/`
- Three parts, 95 MB, 95 MB, and 31 MB. Rejoin with `cat penny_empire_colab.zip.part* > penny_empire_colab.zip` (joined size 231,675,758 bytes).
- Inside: `scene.blend` (Blender 4.2.3, all images packed, 221 MB), `render.py`, `manifest.json`, `penny_words.json`, `penny_empire_sfx.json`.
- Private Empire State and Liberty scans are **inside the blend only**. They are not in git.
- Local check, unpacked into an empty directory with no asset cache: frame 0 matches the python-path preview exactly (SSIM 1.0). Frame 200 matches apart from denoiser grain on the facade (full-frame SSIM 0.9905, facade crop 0.9811, mean absolute difference 1.28 / 255).

Kristóf renders chunks on Colab with:

```bash
blender -b scene.blend -P render.py -- START END
```

`START` and `END` are inclusive frame indices, 0 through 1001. Output is `frames/0000.png` … next to the blend.

### Scale-journey module

Lives at `whatif/scale_journey/`. It does not import `whatif/engine/` (the humans-disappeared / decay engine). Shared UI is `whatif/ui/` (Anton counter, caption band, outlines, loop helper).

Two authoring styles share the folder:

1. **Format A / zoom** (`engine/spec.py`, `engine/build.py`, `engine/camera.py`). One log-scale dolly, layers swapped so Blender stays in float32. Episodes: `rice_64.yaml`, `shrink_half.yaml`. Pitch is constant. The camera does not sway, pan, or reverse. Ending is a dissolve back to frame 0.
2. **Format B / narrated explainer** (`engine/bformat.py`, `engine/build_b.py`, `engine/compose_b.py`, `engine/render_b.py`). Penny is the only full render. Rice-on-a-chessboard, hole-through-the-Earth, brick tower, and Rhode Island crowd load to a timeline (`--timeline-only` or automatic: non-penny presets do not launch Blender).

### Other episodes in this repo

| Spec | Preset | Status in code | What it actually is |
|---|---|---|---|
| `episodes/penny_empire.yaml` | `penny_fall` | The active picture | Full 3D, 33.40 s, Colab bundle handed off |
| `episodes/rice_chessboard.yaml` | `rice_chessboard` | Timeline only | 64 squares, heap instanced, camera (not the heap) reaches ~408 km. 56 s slate. |
| `episodes/rice_64.yaml` | zoom / format A | Older zoom path | “Double a grain every day.” Not the narrated penny pipeline. |
| `episodes/shrink_half.yaml` | zoom in | Older zoom path | Half-size stack down toward a proton. |
| `episodes/earth_hole.yaml` | `earth_hole` | Timeline only | Backyard to Indian Ocean antipode, ping-pong loop. 48 s slate. |
| `episodes/brick_tower.yaml` | `brick_tower` | Timeline only | Unbranded 2×2 bricks, ~375,000 courses. No logo on screen. 50 s slate. |
| `episodes/crowd_rhode_island.yaml` | `crowd_island` | Timeline only | 8.2 billion people on Rhode Island land. 48 s slate. |

**The 60 m giant is not in this checkout.** No spec, scene, or branch here is that episode. Do not invent it. If Kristóf assigns it, it is a new format-B (or format-A) episode under the same asset and narration rules.

### What the last agent was doing, in order

1. Fixed the grey-plane hook (PeeJaa scan was off-axis; shaft median is now the origin, sprawling ground triangles are clipped).
2. Retimed the cut to Brian’s 33.40 s `penny_words.json`.
3. Applied the cinematic physics note: ~25 mph terminal velocity, deterministic flutter, three-shot grammar, shutter 0.6.
4. Replaced the handmade penny, deck cube, podium cube, and grey ground plane with hub assets (Kenney bronze coin; city packs carry the ground).
5. Measured render speedups. Kept only those that stayed at SSIM ≥ 0.99 against a 24-sample / 12-bounce reference.
6. Stopped the local 1002-frame render when Kristóf moved finals to Colab.
7. Baked every frame’s camera, coin, crowd, and visibility into one packed 4.2.3 blend and verified two frames.

Stale review JPEGs `whatif/review/penny/hook.jpg` and `contact_2_5s.jpg` are from an earlier local render. They are **not** the Colab plates. Do not treat them as the current picture.

---

## 2. Kristóf’s rules (numbered)

These are permanent. A later chat does not weaken them.

1. **Brian narrates explainer what-ifs.** The locked take is Brian, Eleven v4, single take, no splice, no stretch. File note in `penny_words.json`: `c30966de.mp3`. Do not re-record, retime, or swap the voice. The words file is wav2vec2 forced alignment with no global shift.
2. **Voice first, then the picture.** Picture duration is the voice duration: 33.40 s, 30 fps, 1002 frames. Beats, HUD numbers, and shots land on the word times in `penny_words.json`. Do not stretch the voice to the old picture.
3. **If a number is spoken, the picture shows that number.** Height: 1,250 ft until 15.44 s, then 500, 200, 100, 80, 40, 0. Speed: 0 until 5.34 s, then 10, 20, then 25 mph locked. The slot roll is centered on the word so the new digit is on screen when the word starts (`bformat.py`, roll window ±0.11 s). Do not show 65 mph. The title must not say “25”.
4. **Realistic penny physics.** Face-on disk, mass 2.5 g, diameter 19.05 mm, Cd 1.14, air 1.204 kg/m³. Terminal speed is **25.04 mph = 40.3 km/h** (inside the 40–45 km/h note). No vacuum fall and no straight line. The “NO AIR ~200 MPH” pill (11.26–12.90 s) is a ghost of the myth, not the trajectory.
5. **Flutter and tumble are deterministic.** `_wind()` in `bformat.py` (sum of sines). No rigid-body sim. Same seed every render.
6. **Three-shot grammar** (from the owner’s cinematic note, also `uploads` / Drive `JuicyTea_assets/VFX_TIPS`):
   - **Macro flick.** Observation-deck corner, 50 mm, camera holds and looks down while the coin leaves (flick at 0.573 s on the word “penny”) and shrinks. Holds through 2.40 s.
   - **Drone follow.** Beside the facade, 24 mm, Z lags the coin, XY ignores flutter, slight updraft buffet, shutter 0.6, motion-blur position END. Blend from the hook is 2.40–2.90 s.
   - **Static street impact.** Camera settles by 19.45 s and does not follow the coin through the bonk (21.073 s).
7. **Pedestrian insert.** Overhead / from-above on “a guy RIGHT under it”, about 13.31–15.10 s, then back to the drone.
8. **Comedic reaction, four beats, on a rigged hub human.** Flinch 21.07–21.85 s, look around 21.85–22.55 s, scratch 22.55–23.27 s, shrug 23.27–23.85 s, then walk +X from 23.85 s until 27.60 s. Hero is the idle male GLB named `Star` at `MAN = (6.0, 66.6)`, yaw π. There is no scratch/shrug clip in the hub; the beats are keyed on that rig after muting the idle curves for neck, spine, arms, clavicles, and thighs. Do not use a static silhouette.
9. **Empire State environment is reused, not remodelled.** PeeJaa / hub scan `cache/private/empire_state.glb`, tip scaled to 443.2 m, shaft median XY shifted to the origin, base on z=0, low sprawl clipped. Footprint stays inside `ESB_LOT = (-28.5, 28.5, -64.5, 64.5)` plus 4.5 m sidewalks and must not meet the roads (`footprint_clears_roads`). Deck corner the coin leaves is about (3.35, 3.75, 381). One WTC is a separate hub mesh ~5.5 km south-southwest. Liberty is the hub scan, ~5 km southwest, 93 m to the torch.
10. **Ready-made assets only. Build nothing from scratch.** Hub first, then CC0 or public-domain with no attribution. If neither has a fit, leave the element out and name what you searched. No cubes, planes, cylinders, or other stand-ins in a deliverable. No CC-BY, NC, or ND. No game or brand IP. Sketchfab Free Standard and BlendKit are allowed only from the hub (renders OK, do not commit the raw file).
11. **People are rigged and animated from hub packs.** A statue, a card, or a silhouette is not a person.
12. **The airport pack’s Malaysia Airlines livery stays unused.** If that scene is ever placed, repaint those aircraft plain white first. Ruined-city and the airport are optional, not the default street.
13. **Every web download is logged.** Append a row to `assets/FOUND_ASSETS.md` (name, direct URL, source page, license, size, what it is for, file path). Under 50 MB and redistributable: also store the file in `assets/found/`. Kristóf mirrors the log into the Drive hub. Agents cannot write Drive. Hub packs are not listed again.
14. **Seamless loop.** Last frame’s pose equals frame 0 (already true in `bformat.py`). The assembled image of frame 1001 must be a copy of frame 0, because a shutter would otherwise smear the jump from the rise back to the deck.
15. **Native 1080×1920 plates.** Do not render small and upscale. A 345×614 render (32% scale) was rejected in spirit when Kristóf rejected another video for blur. 540×960 upscale was not used.
16. **Lossless speedups only.** A speedup is kept only when 2–3 frames, with and without it, stay at SSIM ≥ 0.99 and the crops look the same (coin edge, facade, type). See the table in section 7. Do not drop samples or bounces because a frame is slow.
17. **Final frames go to Colab, not this VM.** Local work is scene build, stills, and low-sample previews. The handoff artifact is the packed blend plus `render.py` plus `manifest.json`. See section 7.
18. **Silent deliverable.** No narration burned into the mp4. SFX are a cue list (`episodes/penny_empire_sfx.json`), not mixed audio.
19. **Caption band stays clear.** Karaoke sits in the safe band (about 68% down the 1920 frame; the shared UI band is y 1229–1382). Do not put the counter on top of the captions.
20. **Colour.** AgX, look `AgX - Medium High Contrast`, exposure 0.35, Cycles, OIDN. Format B shutter 0.6, position END.
21. **Do not commit private raw assets, blends, or zips.** `whatif/scale_journey/.gitignore` ignores `cache/`, `out/`, `*.blend`, `*.zip`.
22. **Update this handoff** at the end of every run, and copy it to `/opt/cursor/artifacts/handoff/`.

### Rejected attempts, and why

| Attempt | Why it was rejected |
|---|---|
| Hook rendered as a grey plane | The scan’s ground mesh was huge and the tower was ~90 m off the bounding-box center. Fixed by median-XY alignment and clipping spanning lid triangles. |
| Chase camera inside the shaft | Mid-altitude clearance box was too wide, then a raycast followed single flipped normals. Clearance bands were narrowed. The camera moves only when ≥ 3 inward hits agree. |
| Handmade penny (cylinder + torus) and a deck/podium cube | Breaks rule 10. Coin is now Kenney `item-coin-bronze.glb` from the hub CC0 library, scaled to 0.17 m so the macro reads. Drag still uses the real 19.05 mm diameter. |
| Generated grey ground plane | Same rule. City blocks and Kenney roads are the ground. The plane is gone. |
| Showing 1,250 or 40 while the line says 500 or 0 | The slot showed the old digit until the roll crossed halfway. The roll is now centered on the spoken time. |
| Rendering at 32% (345×614) and Lanczos-upscaling to 1080×1920 | Soft. Kristóf had just rejected another video for blur. |
| Adaptive sampling at 4, 8, 16, or 20 samples | Facade SSIM against the 24-sample reference was 0.899–0.946. Detail on windows broke. |
| Max bounces cut to 4 or 6 | 4 failed the facade crop (0.989). 6 changed trees and the roof edge and was not faster than 12. |
| Distant LOD (decimate to 7% past 320 m) | Facade SSIM 0.886. The far mesh is not instanced unless `dress_city(lod=True)`. |
| Light-tree off | Not in the approved list and not SSIM-tested. Left on. |
| GPU on this VM | Cycles device list is CPU only (Intel Xeon). No NVIDIA device. |
| Finishing all 1002 frames on this VM | Stopped on Kristóf’s Colab order. A partial native render had a 38 s median and two spikes (619 s, 1560 s). |
| Linear camera keys with shutter 0.6 in the baked file | Smeared the city (edge energy ~150 vs ~910 on the preview). The python preview’s shutter does not actually drag the camera. The blend now holds the camera pose across the 0.6 shutter. The coin’s keys stay linear. |
| A US Mint penny modelled in Blender | Rule 10. The hub coin is a low-poly bronze token, octagonal in close-up. That is the asset. Do not “fix” it with a generated relief. |
| 65 mph or a straight vacuum fall | Contradicts the narration and the physics note. |

---

## 3. Architecture, layout, setup, how to render

### Repo layout that matters

```
whatif/scale_journey/
  render_episode.py          # host CLI
  colab/render.py            # copied into the Colab bundle; do not import the repo
  engine/bformat.py          # format-B timeline, physics, cameras, HUD values
  engine/build_b.py          # Blender scene for the penny (Cycles settings, coin, ESB)
  engine/bake_colab.py       # builds the packed 4.2 blend
  engine/manhattan.py        # city tiles, roads, cars, hero, culling, LOD flag
  engine/compose_b.py        # Anton counter, karaoke, guy ring, ghost pill
  engine/render_b.py         # segment plan, compose, encode
  engine/segments.py         # 2–5 s chunks, cache keys
  engine/landmarks.py        # ESB lot, sidewalk, MAN
  engine/spec.py             # format-A YAML
  engine/build.py            # format-A Blender scene (older zoom). Not the penny.
  engine/bench_speed.py      # SSIM bench of speedups (frames 0, 200, 690)
  engine/bench_samples.py    # follow-up sample search
  episodes/penny_empire.yaml
  episodes/penny_words.json
  episodes/penny_empire_sfx.json
  episodes/*.yaml            # other episodes, timelines
  tests/test_format_b.py
  tests/test_segments.py
  tests/test_scale_journey.py
  tools/fetch_library.py
  assets/library/cc0_manifest.json
  cache/                     # GITIGNORED
  docs/SCALE_JOURNEY.md      # module overview; asset rule matches the README
  docs/ADOPTION.md           # STALE on two points: it still says “build if both fail”,
                             # and it points format B at build.py. Penny uses build_b.py.
whatif/ui/                   # shared counter, outlines, loop, pills, words
assets/FOUND_ASSETS.md       # web-download log (empty; hub was enough)
assets/found/.gitkeep
docs/handoff/penny_scale_HANDOFF.md   # this file
whatif/review/penny/         # STALE early JPEGs, not the Colab plates
```

`ADOPTION.md` says the parent engine should dispatch `module: scale_journey` and not render a decay scene for these specs. That part is still right.

### Versions on the machine that produced the bundle

| Tool | Version | Where |
|---|---|---|
| Python | 3.12.3 | system `python3`. Needs PyYAML, Pillow, NumPy. No SciPy. |
| Blender for local stills / the python-path preview | 4.5.9 LTS | `/home/ubuntu/apps/blender-4.5.9-linux-x64/blender` |
| Blender for the Colab bundle | **4.2.3 LTS** (Colab’s version) | Downloaded to `/tmp/blender42/blender-4.2.3-linux-x64/`. A new VM must re-download. URL: `https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz` |
| Cycles | built into both Blenders | CPU here. OptiX then CUDA in `colab/render.py`. |
| Add-ons | none | Do not add one at render time. Geometry is already in the blend. |

A blend saved from 4.5.9 **will not open** in Colab’s 4.2.3. Always bake with 4.2.3.

### Setup from zero

```bash
cd /workspace
python3 -m pip install --user pyyaml pillow numpy

# CC0 packs the penny scene actually touches (zips stay in cache/, not git):
python3 whatif/scale_journey/tools/fetch_library.py hdri vehicles roads_props characters animations food

# Private hub files are NOT in git and NOT in cc0_manifest.json.
# They must already be in whatif/scale_journey/cache/private/ or the scene raises.
# Catalog to re-fetch: Drive file ASSET_HUB.json id 1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV
# Readable catalog: ASSET_HUB.md id 1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T
# Download URL pattern:
#   https://drive.usercontent.google.com/download?id=FILE_ID&export=download&confirm=t

# Tests (no Blender):
cd /workspace/whatif && python3 -m unittest scale_journey.tests.test_format_b scale_journey.tests.test_segments -q

# Blender 4.2.3, only if you must rebuild the bundle:
curl -L -o /tmp/blender-4.2.3-linux-x64.tar.xz \
  https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz
mkdir -p /tmp/blender42 && tar -C /tmp/blender42 -xf /tmp/blender-4.2.3-linux-x64.tar.xz
```

### How to render

Working directory: `whatif/scale_journey`. Blender is found by `render_b.py` (or pass `--blender`).

**Timeline only** (no picture). Use this for rice, hole, bricks, crowd, and to inspect penny beats:

```bash
python3 render_episode.py episodes/penny_empire.yaml --timeline-only --out /tmp/penny_timeline
```

**One still, python path** (needs the private cache and Blender). Native, approved samples, two frames:

```bash
python3 render_episode.py episodes/penny_empire.yaml \
  --frames 0,200 --samples 24 --scale 100 --no-video \
  --blender /home/ubuntu/apps/blender-4.5.9-linux-x64/blender \
  --out /tmp/penny_still
```

`--frames` forces a single Blender process (no segment cache). Plates land in `/tmp/penny_still/plates/`, composed frames in `frames/` if the compose step runs. For a lighting check, `--samples 4` is a preview only. Do not upscale it and do not call it final.

**Schematic preview** (no Blender, timing and UI only):

```bash
python3 render_episode.py episodes/penny_empire.yaml --preview --no-video --out /tmp/penny_schematic
```

**Final frames:** do not run all 1002 frames here. Use the Colab bundle in section 7. Rebuild the bundle only if the scene code changed:

```bash
# Host Python writes frame records (bpy’s Python has no PyYAML).
cd /workspace/whatif && python3 - << 'PY'
import json, sys
from pathlib import Path
sys.path[:0] = ["/workspace/whatif", "/workspace/whatif/scale_journey"]
from engine.bformat import resolve_b
from engine.render_b import _geom
ep = resolve_b(Path("scale_journey/episodes/penny_empire.yaml"))
Path("/tmp/penny_colab_frames.json").write_text(json.dumps([_geom(ep, fr) for fr in ep.frames]))
PY

/tmp/blender42/blender-4.2.3-linux-x64/blender --background \
  --python /workspace/whatif/scale_journey/engine/bake_colab.py
```

`bake_colab.py` reads `/tmp/penny_colab_frames.json`, writes preview plates for frames 0 and 200 to `/tmp/penny_colab_preview/`, then the packed blend to `/tmp/penny_colab_build/scene.blend`. `BAKE_LIMIT=2 SKIP_PREVIEW=1` is the smoke test. Zip and split as in section 7. The artifact store rejects a single file over 100 MB, so split at 95 MB even though Kristóf’s cap is 1.9 GB.

---

## 4. Assets

### Fetch order

1. Re-fetch `ASSET_HUB.json` (Drive id `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV`) before adding anything. Readable copy: `ASSET_HUB.md`, id `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T`. Folder name on Drive: `JuicyTea_assets`.
2. CC0 library via `tools/fetch_library.py` and `assets/library/cc0_manifest.json`. Zips extract under `whatif/scale_journey/cache/library/extracted/`.
3. Private Sketchfab Free Standard / BlendKit files live in `whatif/scale_journey/cache/private/`. Gitignored. A private overlay manifest, if present, is `cache/library/private_manifest.json` (also gitignored). The fetch script never prints private URLs.
4. Web only if the hub lacks it. Log it. `assets/FOUND_ASSETS.md` is empty because this episode did not need a new web file.

### Packs the penny scene actually loads

| What | Path |
|---|---|
| Empire State scan | `cache/private/empire_state.glb` (about 27 MB) |
| Statue of Liberty scan | `cache/private/statue_liberty.glb` (about 2.9 MB) |
| Procedural City blocks 6, 3, 4 | `cache/private/hub/procedural_city_{6,3,4}.glb` |
| One WTC | `cache/private/hub/one_wtc.glb` |
| Hero idle + walk clips | `cache/private/city_people/animations/sketchfab_free_standard/Idle_1_Male_…` and the three walk GLBs named in `manhattan.py` |
| Street props | `cache/private/city_people/.../city_props_vol1.glb` |
| Crosswalk | `cache/private/city_people/.../simple_crosswalk.glb` |
| Coin | `cache/library/extracted/assets_cc0_vehicles/vehicles/kenney_toy_car_kit/Models/GLB format/item-coin-bronze.glb` |
| Roads | `cache/library/extracted/assets_cc0_roads_props/.../kenney_city_kit_roads/` |
| Cars | `cache/library/extracted/assets_cc0_vehicles/.../kenney_car_kit/` |
| HDRI | `cache/library/extracted/assets_cc0_hdri/.../belfast_sunset_puresky_2k.hdr` (fallback in the job is `assets/hdri/sunset_jhbcentral_1k.hdr` if that file exists) |

CC0 zip names in the manifest (not all are used): animals, animations, characters, city_buildings, farm, food, hdri, interiors, materials, medieval_historical, nature, ocean_boats, roads_props, ruins_decay, space, sports, toys, vehicles, weather_fx, winter. Several are split on Drive; `fetch_library.py` reassembles them and checks sha256.

City tiling: cell 200 m, reach 1000 m, plaza around the scan is left empty (`PLAZA` in `manhattan.py`). Near vs far meshes exist in code, but **far meshes are not built** unless `dress_city(lod=True)`. LOD failed SSIM. Leave it off.

Checked and left out (comments in `manhattan.py`): ruined city, airport city (airline livery), armored vehicle mini-pack, curved highway pieces.

---

## 5. Episode spec, voice, beats, cameras

### Spec

`whatif/scale_journey/episodes/penny_empire.yaml`

- id `penny_empire`, preset `penny_fall`, 30 fps, 1080×1920, duration 33.4 s, hook hold 0.57 s.
- Quantity: mass 0.0025 kg, diameter 0.01905 m, thickness 0.00152 m, Cd 1.14, air 1.204. The yaml comment that says the mesh is “about 3×” is **stale**. `build_b._penny` scales the Kenney coin to **0.17 m** across so the macro shot reads. Drag uses `diameter_m`, not the mesh size.
- Sources in the yaml cite the US Mint, a face-on disk formula, ESB facts, Scientific American, the MythBusters-related 64.4 mph note (not spoken), NPS Liberty 305 ft, and the 2025 penny-production item (optional, not on frame 0).

### Voice and words

`episodes/penny_words.json`

- duration 33.403 s, sample rate 48000.
- Take: Brian, Eleven v4, `c30966de.mp3`, single take.
- Edit notes inside the JSON: lead room tone 0.098 s; a rush insert of 0.785 s placed at 19.68 s; gap from “hundred” to “Bonk” is 2.003 s; cut after the swear in the source at 32.52 s.
- Words have `w`, `t0`, `t1`. Some have `cap` (the digit string) and `cap_t1`. Empty `cap` means “merge into the previous digit”.
- Seam: speech onset 0.147 s, tail after “swear” 0.087 s, seam gap 0.234 s. Loop line: “…but people still swear” → “This penny could KILL someone.”

Spoken number anchors:

| Time | Word | HUD |
|---|---|---|
| 0.147–2.158 | This penny could KILL someone. | 1,250 ft, 0 mph. Title on screen until ~2.35 s. |
| 5.340 | Ten | 10 mph |
| 6.700 | twenty… | 20 mph |
| 7.675 | TWENTY-FIVE. | 25 mph, then locked |
| 11.26–12.90 | no air / two hundred (myth) | ghost pill `NO AIR ~200 MPH` |
| 13.31–14.55 | a guy RIGHT under it | overhead insert, red ring in compose |
| 15.440 | Five hundred | 500 ft |
| 16.91 | two hundred | 200 ft |
| 18.25 | ONE hundred | 100 ft |
| 19.07–21.07 | silent rush | HUD ticks 80, then 40, then 0. Those three numbers are **not** separate words in the JSON. |
| 21.073 | Bonk. | 0 ft, 25 mph. Coin at head height. |
| 22.03–23.83 | It STINGS. That's it. | reaction |
| 24.16–27.28 | tumbles like a LEAF… twenty-five | still 25 mph |
| 27.71–33.32 | real Empire State… people still swear | camera rises |
| 33.15–33.40 | hold | back to opening pose, 1,250 ft, 0 mph |

### Camera plan (already keyed in the blend)

From `bformat._penny`:

| Time | Shot | Lens |
|---|---|---|
| 0–2.40 s and ≥ 33.15 s | Hook on the deck corner, looking down | 50 mm |
| 2.40–2.90 s | Blend hook → drone | 50 → 24 |
| 2.90–13.31 s | Drone, Z lags, buffet | 24 mm |
| 13.31–14.55 s | Blend to the guy insert | 24 mm |
| 14.55–15.10 s | Blend back to the drone | 24 mm |
| 15.10–19.07 s | Drone | 24 mm |
| 19.07–19.45 s | Blend to the street camera | 24 → 32 |
| 19.45–27.71 s | Static street shot (code uses 48 mm on `up_cam`) | 48 mm |
| 27.71–33.05 s | Rise toward the opening, with a lateral sine so it can meet frame 0 | 32 → 50 |
| frame 1001 | Forced to the opening pose | 50 mm |

Coin path: ledge until 0.57 s, then a dragged fall with `_wind` flutter, then a blend onto the pedestrian at the end of the fall, a small hop at the bonk, then rest. `clear_of_shaft` pushes the coin and the chase camera outside the shaft bands. Do not put the camera back inside the building.

Pedestrian pose is **not** a clip. `_punchline` in `build_b.py` keys it. The bake copies the evaluated bone matrices into the blend, so Colab does not need `build_b.py`.

### Output URLs

- PR: https://github.com/dagadt675-oss/juicytea-media/pull/9
- Branch: `cursor/penny-lookdown-chase-d7c6`
- There is **no** finished silent mp4 on the branch from this run. Do not look for a raw GitHub URL of `penny_empire.mp4`. The plates Kristóf will render are the Colab bundle under `/opt/cursor/artifacts/colab_bundle/penny_empire/`.
- SFX cue list (in repo and inside the zip): `whatif/scale_journey/episodes/penny_empire_sfx.json`. Cues at 0.0 deck wind, 0.573 flick, 2.4 rush, 11.26 ghost whoosh, 19.07 rush close, 21.073 bonk, 21.35 bounce, 22.4 scratch, 23.28 shrug, 27.71 deck wind again.

### Open feedback

- Kristóf has not yet rendered the Colab chunks or approved a finished mp4 of this cut.
- The coin reads as a low-poly bronze token, not a Lincoln cent. That was accepted under the asset rule. Do not remodel it.
- Drone frames are dominated by the scan’s roof and facade (a large pale surface) with the city in the upper part of the frame. That is the current camera, not a bug to “fix” with a ground plane.
- `episodes/penny_empire.yaml` still contains older `say:` lines (“about fifty feet down”, Liberty at three hundred feet) that are **not** the Brian track. The picture follows `penny_words.json`, not those lines.
- `docs/ADOPTION.md` is stale on the asset rule and on which Blender entry point the penny uses.
- Review JPEGs in `whatif/review/penny/` are stale.

---

## 6. QC

Run from `/workspace/whatif` so `engine` and `ui` import:

```bash
python3 -m unittest scale_journey.tests.test_format_b scale_journey.tests.test_segments -q
```

`PennyTest` thresholds that must stay green:

- Duration 33.4 ± 0.05 s. Terminal speed rounds to 25 mph. Drop 1250 ± 0.2 ft.
- HUD at t = 0.3, 5.5, 6.9, 8.0, 15.6, 17.1, 18.5, 21.07 matches section 5. Pill `NO AIR` at t = 11.5.
- Spoken beats contain neither “65” nor “sixty-five”. Title does not contain “25”.
- Penny height at the bonk (t = 21.07) is 1.7 ± 0.25 m.
- Fall descends, then the rise returns the coin and the camera to the ledge (0.05 m).
- 25 mph holds at least 0.8 s.
- `ESB_LOT` clears the three road rectangles.
- `clear_of_shaft` pushes (0, 0, 30) outside x = 28.5 and y = 64.5, and no frame’s camera or coin needs a second push.
- Hook looks down (target z < camera z − 0.4) and sits above the coin. Chase does the same at t = 8.
- Hook frames before 0.5 s show speed 0 and no mph pill.
- Last frame phase is `hold` and its primary matches frame 0.

Picture checks (not unit tests):

- Plates are exactly 1080×1920. Reject anything else.
- Frame 0 vs the python-path preview: SSIM 1.0 on the current bundle.
- Any other still vs that preview: full-frame SSIM ≥ 0.99, and a facade crop that is only denoiser grain. The measured frame 200 was 0.9905 full, 0.981 facade. If a new change drops the facade crop, look at it before calling it noise.
- Speedup A/B: SSIM ≥ 0.99 on frames 0, 200, and 690, plus the coin, facade, and type crops. Bench entry points: `engine/bench_speed.py`, `engine/bench_samples.py`. Reference was CPU, 24 samples, OIDN, 12 bounces, no adaptive, no persistent data, no culling, no LOD.
- Loop: assembled frame 1001 equals file bytes of frame 0 (copy the PNG; do not re-render the jump).
- No primitive named `Podium`, `Deck`, `Underlay`, or `Earth` in a deliverable. Those functions still exist in `build_b.py` and are **not called**.
- `git status` must not show `cache/private`, `*.blend`, or `*.zip`.

SSIM in the last run was a NumPy Gaussian implementation (no scikit-image). Reuse that method or an equivalent 11×11 σ=1.5 SSIM. Do not compare an upscaled plate to a native plate.

---

## 7. Segmented rendering and the Colab bundle

### Local segments

`engine/segments.py` cuts the episode at beat edges into chunks of about 2–5 s (`TARGET_SEC = 4`, `MAX_SEC = 5`, `MIN_SEC = 2`) plus 2 handle frames for motion blur. Cache: `whatif/scale_journey/cache/segments/penny_empire/`. The key hashes scene code, assets, samples, and scale. A code change misses the cache. Handles are deleted before the chunk is marked ready.

Default `render_episode.py` **uses segments** unless you pass `--frames` or `--no-segments`. Encode is silent H.264, yuv420p, bt709, CRF 16, in `segments.encode_sequence`. That CRF made a ~50 MB file when an earlier low-res pass was re-encoded at CRF 22. A native CRF 16 mp4 may exceed 50 MB; re-encode under 50 MB only after Kristóf has plates he wants cut. Do not upscale to get there.

Segmented rendering matched the continuous reference (SSIM 1.0 on frame 200) and was slightly slower per frame (52.6 s vs 49.6 s) because each chunk reloads Blender. It is for local resume, not for the Colab final.

### Colab workflow (current final path)

Kristóf’s benchmark: 95 s on a Tesla T4 (OptiX) vs 655 s on an 8-core CPU for one frame, about 7×, and about 14× versus this VM. This VM’s own median at 24 samples was 38 s, with rare multi-minute spikes. Use his Colab number for scheduling, and the manifest’s 38 s as the CPU figure from **this** machine.

Bundle contents:

| File | Role |
|---|---|
| `scene.blend` | Blender 4.2.3. Meshes, HDRI, and textures packed (`bpy.ops.file.pack_all()`, paths relative). No external cache. No add-on. |
| `render.py` | `blender -b scene.blend -P render.py -- START END`. Sets Cycles GPU, OptiX then CUDA, all non-CPU devices on, CPU if neither exists. Re-asserts 1080×1920, 24 samples, adaptive 0.01, OIDN, 12 bounces, shutter 0.6 END, AgX Medium High Contrast, exposure 0.35, seed = frame index. Writes `frames/NNNN.png`. |
| `manifest.json` | `blender_version`, `frame_start` 0, `frame_end` 1001, `fps` 30, `resolution` [1080, 1920], `samples` 24, `est_seconds_per_frame_on_your_cpu` 38, plus the edit notes. |
| `penny_words.json`, `penny_empire_sfx.json` | Assembly. Not read by `render.py`. |

What is baked into the blend so Colab does not need this repo:

- Camera location, rotation, and lens, held constant across each frame’s shutter.
- Coin location, rotation, and scale, linear so the tumble can blur.
- Hero and other armatures’ bone poses per frame (the punchline is already evaluated).
- Mover empties (cars).
- `hide_render` keys for culled blocks and props (margin 0.22 in NDC, 80 m shadow keep, 120 m near keep).

Rebuild with `engine/bake_colab.py` (section 3) if any of those change. Then:

```bash
cd /tmp/penny_colab_build
zip -0 -r /tmp/penny_empire_colab.zip \
  scene.blend render.py manifest.json penny_words.json penny_empire_sfx.json
split -b 95M -d -a 2 /tmp/penny_empire_colab.zip \
  /opt/cursor/artifacts/colab_bundle/penny_empire/penny_empire_colab.zip.part
```

Verify before telling Kristóf it is ready:

```bash
rm -rf /tmp/penny_colab_empty && mkdir /tmp/penny_colab_empty
cat /opt/cursor/artifacts/colab_bundle/penny_empire/penny_empire_colab.zip.part* > /tmp/rejoin.zip
unzip /tmp/rejoin.zip -d /tmp/penny_colab_empty
cd /tmp/penny_colab_empty
blender -b scene.blend -P render.py -- 0 0
blender -b scene.blend -P render.py -- 200 200
# compare to /tmp/penny_colab_preview/f_0000.png and f_0200.png
```

The empty directory must not be the repo, and the blend must not contain `/workspace` or `cache/private` path strings. The last check found none.

Speedups inside the blend (all passed SSIM, or they would not be there):

- Samples stay at 24. Adaptive sampling is on with threshold 0.01 because at 24 it matched the fixed-24 reference (SSIM 1.0) and lower caps failed.
- Persistent data on.
- Camera culling on (baked visibility).
- Bounces 12. LOD off. No GPU flag inside the blend; `render.py` switches the device.

---

## 8. Known bugs and next steps

Priority order. Do not start the bottom of the list while the top is open.

1. **Kristóf renders the Colab chunks and assembles the film.** This agent does not render the 1002 frames. If a plate comes back wrong, diff it against a python-path still of that frame before changing the scene.
2. **Assemble, don’t re-invent.** Composite `compose_b.py` (counter, karaoke from `penny_words.json`, red ellipse on the guy, ghost pill) onto the Colab plates. Copy frame 0 over frame 1001. Encode silent H.264 under 50 MB if a file is requested. Keep the SFX as a cue list.
3. **Facade SSIM 0.981 on frame 200** is the residual gap versus the python preview (denoiser grain, not a missing building). If Kristóf calls the Colab frame soft or different, render that frame with motion blur off and seed = frame index before chasing geometry.
4. **The Kenney coin is not a Lincoln cent.** Only replace it if the hub or a CC0 scan of a US cent appears. Log any download. Do not model one.
5. **Drone framing is mostly the scan surface.** Changing it is a camera change in `bformat.py`, then a rebake. Do not put a plane under it.
6. **`penny_empire.yaml` `say:` block and `ADOPTION.md` are stale.** Fix the comments when you next touch those files so the next agent does not voice the old lines.
7. **Dead primitive helpers** `_podium`, `_crown`, and `_box` remain in `build_b.py` and are not called. Deleting them is safe cleanup. Do not call them.
8. **Other episodes are timelines.** Rice, hole, bricks, and the Rhode Island crowd do not have a Blender scene that satisfies rule 10. Building them means the same hub-first pass, not `engine/build.py`’s primitive zoom sets.
9. **60 m giant** is not in this repo. Wait for a spec.
10. **Local segment cache** under `cache/segments/` may hold a partial native render from the stopped job (key prefix `e95378ea…`). It is gitignored. Delete it if disk matters. Do not resume it as the final.

---

## 9. Branches and PRs

This agent’s branch is the penny branch. `main` on the VM was **2 commits behind `origin/main`** at handoff time. Fetch before trusting it.

| Branch | Tip (this VM) | PR | State | Use |
|---|---|---|---|---|
| `cursor/penny-lookdown-chase-d7c6` | `657a956` | [#9](https://github.com/dagadt675-oss/juicytea-media/pull/9) draft, base `cursor/scale-journey-module-d7c6` | **Current.** Penny picture, Colab baker, asset rule. | Continue here. |
| `cursor/scale-journey-module-d7c6` | `8cfad6c` | [#6](https://github.com/dagadt675-oss/juicytea-media/pull/6) open, base `main` | Parent of the penny branch. Older ledge lighting. | Do not reset the penny branch onto this tip. |
| `main` | `1ea85e4` locally, behind origin | — | “Host the seat survival Short.” | Not the penny scene. |

Other open draft PRs on the same GitHub repo are **different shows** (Greenland, plane seat, globe, gold kit, football, LA–Tokyo, humans-disappeared). They are not this episode. Do not merge penny work into them. Numbers seen on 2026-10-11: #21 city vanish, #20 plane-seat bundle, #19–#15 and #13–#12 and #7 Greenland/globe, #14 and the seat work, #11 ruins, #10 segmented render, #8 river city, #5 what-if engine, #4 LA–Tokyo, #3 gold kit, #2 football Earth.

Latest penny commits on the branch, newest first:

- `657a956` Bake the penny scene into a packed Blender 4.2 Colab bundle.
- `90bde9d` Keep only the full-resolution speedups that match the clean plate.
- `7bd1bf2` Lock the counter to the spoken word and render plates at full resolution.
- `cfcfb76` Use the hub bronze coin and drop generated stand-ins.
- `4a23ecc` Fit the penny drop to a flick, a lagging facade follow, and a static landing.
- `74922f3` Recut the penny fall to the 33.40 s narration and stand the tower up.

---

## Continue-from-here checklist

1. Read this file. Read `episodes/penny_words.json` and `engine/bformat.py` before changing a time.
2. Run `python3 -m unittest scale_journey.tests.test_format_b -q` from `whatif/`.
3. Do not render the full film on the VM. If the blend is stale, rebuild with Blender 4.2.3 and re-verify frames 0 and 200.
4. If Kristóf returns Colab plates, composite, copy frame 0 onto frame 1001, and only then encode.
5. Update this handoff before you finish.
