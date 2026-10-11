# City decay handoff

Date: 2026-10-11. Writer: the agent that stopped on branch `cursor/ready-city-f245`.

If you have only this file plus the repo, continue from here. Do not restart the handmade city, and do not delete either version. Update this file at the end of every future run that touches the city, the stills, the render path, or Kristóf's rules. After you commit it, copy the same bytes to `/opt/cursor/artifacts/handoff/city_decay_HANDOFF.md` so it can be uploaded to Google Drive.

Scene work that this document describes is commit `60c8318` on `cursor/ready-city-f245`. This handoff is the commit after that. `git log -1 -- docs/handoff/city_decay_HANDOFF.md` is the handoff SHA.

Blender for scene work on this machine: **4.5.9 LTS**, binary `/home/ubuntu/blender/blender`, built 2026-04-21. There is **no NVIDIA GPU**. `nvidia-smi` is absent. Cycles devices: CPU only (`compute_device_type` is `NONE`).

The Colab blend was saved with **Blender 4.2.3 LTS** at `/home/ubuntu/blender-4.2.3/blender` (build date 2024-10-14). Open and resave that blend only with 4.2. A 4.5 save will not open on Colab's 4.2.3.

---

## 1. Mission and current state

### Mission

Episode 1 of JuicyTea / whatif: **"What if every human vanished… right now?"**

Format A, vertical YouTube Short, **1080×1920**, **30 fps**, **1800 frames** (59.98 s). Silent picture. Sound effects only. On screen: title, then one counter (population, then the year). No narration, no music, no full encode until Kristóf approves stills.

The picture is a city that is alive on day 1, then ages: weeds, rust, a fallen bridge, heavy ruin at 100 years, a collapsed city swallowed by forest at 500 years, then a loop back to day 1. Benchmark is the zenith opening frame (`whatif/engine/opening_metrics.py`, reference image was `refs/zenith_opening.jpg` at 540×960).

Two city versions exist. **Keep both.**

### Version A — handmade river city (do not delete)

- Episode: `whatif/episodes/humans_disappeared.yaml` (`id: humans_disappeared`).
- Scene: `build_river_city` in `whatif/engine/scenes.py`. There is no `scene.name`. The default `else` branch builds it.
- Branch that owns the latest stills: `cursor/road-network-stills-f245` at `b33e88f`.
- Pull request: https://github.com/dagadt675-oss/juicytea-media/pull/11 (base `cursor/bridge-road-skyline-f245`).
- What it is: a constructed river, suspension bridge, avenue, park, far-bank street grid, hub building blocks, mountains, decay. It was iterated for many review rounds. Roads and the mountain *type* were accepted. The 100y/500y collapse was still not good enough for the owner when he asked for a different approach.
- Latest committed review images (handmade), commit `b33e88f`:
  - Four eras: https://github.com/dagadt675-oss/juicytea-media/raw/b33e88f/whatif/review/four_stills.jpg
  - Plan: https://github.com/dagadt675-oss/juicytea-media/raw/b33e88f/whatif/review/plan.jpg
- Earlier reviews the owner rejected, for history: `6977cc6` (roads ok, Quaternius boulder mountains, skyline "gone" at 500y), `3f60b18` (real snow peaks but small and washed out; 500y skyline standing again and tinted brown; 1y far bank neon green).
- Full 1800-frame encode: **not started**. Do not start it.

### Version B — downloaded city (where this agent stopped)

- Episode: `whatif/episodes/ready_city.yaml` (`id: ready_city`, `scene.name: ready_city`).
- Scene: `whatif/engine/ready_city.py`, hooked from `build_scene` when `name == "ready_city"`.
- Branch: `cursor/ready-city-f245` at `60c8318`, plus this handoff commit. Branched from `b33e88f`, so version A is still in the history.
- Pull request: https://github.com/dagadt675-oss/juicytea-media/pull/21 (base `cursor/road-network-stills-f245`).
- What it is: **Procedural City 6** dropped in whole as day 1 (about 248 × 196 × 113 m, 80 meshes, already has streets, crosswalks, trees, water towers). At collapse > 0.5 it is hidden and **Ruined City Free 5** is shown, scaled so its long side is 230 m and seated on z=0 at the same origin. Hub debris is scattered on that ground. A short Principled Volume fog sits on the streets. Two hub mountain meshes sit kilometres behind. The handmade river, bridge, and lot grid are not in this episode.
- Kristóf, 2026-10-11, in Hungarian: do not delete the previous city; make a completely separate one about the same vanish; pick an existing city from Drive; do not build a city; everything else stays; the camera may look from a slightly better place.
- Proof stills (half resolution, 8 samples, about 6 s/frame). Not owner-approved yet:
  - Strip: https://github.com/dagadt675-oss/juicytea-media/raw/60c8318/whatif/review/ready_city/three_stills.jpg
  - Day 1: https://github.com/dagadt675-oss/juicytea-media/raw/60c8318/whatif/review/ready_city/day.jpg
  - 100 years: https://github.com/dagadt675-oss/juicytea-media/raw/60c8318/whatif/review/ready_city/100.jpg
  - 500 years: https://github.com/dagadt675-oss/juicytea-media/raw/60c8318/whatif/review/ready_city/500.jpg
- What the agent was doing when stopped: the ready-city proof stills were committed. A lossless-speedup A/B (SSIM ≥ 0.99) was requested and then **paused before any test frame was rendered**. Do not resume that A/B unless Kristóf asks. Do not encode either episode.
- Colab final-render bundle for this version is built. See the dated note below and section 7. The blend is not in git.

### What "continue" means

Wait for Kristóf to say which version he wants next. If he says nothing, the open ask on version B is his review of those three stills. Likely follow-ups if he stays on B: closer camera so the grey ground does not fill the bottom half; god rays that read between the towers instead of one foreground bloom; 500y trees that read through the fog; the same living-city beats (people, traffic) only if a downloaded crowd already exists in the block. Do not go back to assembling towers from boxes.

### 2026-10-11 — Colab bundle for version B

Kristóf: the final render runs on Google Colab (free Tesla T4, Blender 4.2.3, OptiX). This VM keeps doing stills and low-sample previews. The bundle is the ready-made city only. Version A is still the handmade episode and is not inside `scene.blend`.

The packed blend, `render.py`, and `manifest.json` are one zip of **296,657,654 bytes** (SHA-256 `8ef8dc15712f2cb2af15e8115fd42f271b62fb08cede1005a8cf1b21e7901fa7`). The artifact store returns `EINVAL` on a single file near 110 MB, so the zip is stored as four parts under `/opt/cursor/artifacts/colab_bundle/city_decay/` (90 MiB, 90 MiB, 90 MiB, 13 MiB). Rejoin with the `cat` line in section 7, then unzip. Proof PNGs from that unpack sit in `verify/`.

Clean unpack, Blender 4.2.3, `render.py`, frames 1 and 871: both PNGs are 1080×1920 RGB. Frame 1 shows Procedural City 6 with its facade textures. Frame 871 shows Ruined City Free 5, the two mountains, and the ground fog. Wall clock was 54 s and 72 s. Mean **63 s/frame** on this 4-thread CPU. `est_sec_per_frame_t4` is **16**, which is that mean divided by 4. No T4 was available, so 16 is a planning guess. 1800 frames at 63 s is about 31.5 hours on this CPU. At the guess, a free Colab session needs `START`/`END` chunks.

No 1800-frame encode was started. The speedup A/B stays paused.

---

## 2. Kristóf's rules (numbered)

These are standing. A later message does not cancel an earlier one unless he says so.

1. **Zenith is the opening benchmark** for the handmade episode. Portal outer width 0.180 of frame, portal height 0.375, deck width 0.222 at image y=0.58 and 0.300 at y=0.78, deck centerline 56.9° from horizontal, deck asphalt about sRGB (33, 44, 66), foreground tree canopies in the 5–6% band. Relative error tolerance **0.05**. Code: `whatif/engine/opening_metrics.py`. The ready-city episode does not have that bridge, so this metric does not apply to it.
2. **No narration and no music** on episode 1. `audio.narration: false`, `audio.music: false`. Beat `narration` strings time the picture. They are not spoken. `words.json` is empty.
3. **SFX and title/counter only.** `audio.sfx: true`. `ui.text` is `[title, counter]`. Counter is population (8.2 billion, UN WPP 2024) and then the year label. No other type on screen.
4. **The city is alive before the vanish.** Walking pedestrians, cyclists, buses, cars moving both ways. At `vanish` people disappear, cars coast or drift, bikes topple. Abandoned vehicles stay and age. On the handmade city this is `_alive` in `scenes.py`. On the ready city the block is used as shot; it was not repopulated. If you add life, use downloaded rigs, and they must vanish with the channel.
5. **Mountains behind the city.** Real meshes, kilometres back, larger than the skyline, ridgelines and snow, atmospheric haze, same geometry every era. Seasons and light may change. Not a Quaternius boulder row. Not a cliff wall in the camera. Not a photoscan stood on edge (`bk_peak.glb` faces the camera as a slab; leave it out). The glacier photoscan is a flat sheet; do not stand it up.
6. **No road ends in the river or in empty land.** Far-bank north-south streets meet a riverside drive. The bridge abutment meets an arterial. The near approach reads as a road over the park into the avenue. Verified in plan view for the handmade city as of `6977cc6` and still the layout in `b33e88f`.
7. **Filled far bank.** Real blocks on lots along streets, not scattered cubes. Handmade city uses `procedural_city_*.glb`, `one_wtc.glb`, Kenney towers. The plan must show filled lots.
8. **The bridge connects at both ends** to real roads. River span is down by 100 years. At 500 years the portals read as broken stumps, not a clean red gate.
9. **100 years = heavy ruin.** Broken roofs, dark shattered windows, rust, moss, ivy, at least one partial collapse, bridge span already in the river. Far towers must not look intact. As ruined as earlier 500-year attempts were supposed to be.
10. **500 years = a spectacular collapse** that reads from the locked wide camera: jagged stumps, one or two toppled towers, hollow facade shells, rubble mounds, forest through the ruins. Not "the skyline was deleted." Not "the skyline is still standing and tinted brown." Not trees on bare dirt with the city gone.
11. **Decay pipeline, in this order of intent:**
    - Era collections / roles, not a flat colour swap. Handmade roles include `building_base`, `frontage`, `shell`, `fallen`, `ruin`, `groundwear`, `fracture100`, `fracture500`, `hills`, `swallow`. Ready-city swap is `ready_city` vs `ready_ruin` inside `ready_city.drive`.
    - Smart materials: keep the asset's facade textures and add grime, moss, edge wear. No flat tan or brown override. `decay_vfx.arm_erosion`, `found_assets.stamp_object`.
    - Cell Fracture add-on plus rigid bodies with breakable fixed constraints. Bake **once**, cache the end pose, never simulate during stills. Handmade: `decay_vfx.fracture_buildings` and `fracture_deck`. Cache path used last: `/opt/cursor/asset-cache/private/fracture_cache/building_eras_v5.blend` (code constant is `building_eras_v5.blend` in `decay_vfx.py`). Ready city does not fracture.
    - Ivy Gen on facades and bridge pillars, visible at 100y and 500y. `found_assets.grow_ivy`. Addon file, not an extension.
    - A.N.T. Landscape for 500y uneven ground where asphalt was. `decay_vfx.ant_hills`. Handmade only.
    - Geometry Nodes proximity ivy/moss and crack-masked grass. Blender 4.5: connect scatter to the **`Density`** socket of `GeometryNodeDistributePointsOnFaces`, not `Density Factor` (that raises `KeyError`).
    - EXR beauty and Cryptomatte transitions: **not built.** `--format exr` writes a 16-bit ZIP EXR and refuses UI composite. Object indexes exist only for the opening metric (`INDEX_DECK=2`, `INDEX_CANOPY=3`, `INDEX_PORTAL=11`). Do not claim Cryptomatte works.
12. **Thin volumetric fog, thicker at the ground.** Ready city only, and only after the 2026-10-11 proof. Principled Volume, street density about **0.008** when ruined and about **0.0016** on day 1 (`0.008 * (0.2 + 0.8 * age)`), anisotropy **0.4**, height falloff from z=0 (full) to z=34 (zero). Domain is 260 × 230 × 36 m centered on the block so the camera sits above it. Mountains stay outside that box. Sun lowers only when `collapse > 0.4` (`rotation_euler` x from 0.85 toward 1.13, yaw 2.35, energy 8) so a shaft shows in front of the ruins. `volume_bounces` is set to **1** per frame in `ready_city.drive`. Global `build.py` still sets `volume_bounces = 0` before the frame loop; the drive overrides it for this episode. Half-res cost was about **6 seconds** a frame, so it was kept live. If a later full-res frame is dominated by volume time, bake a volume pass at fewer samples or fall back to world mist. Do not use density 0.01–0.02 across a kilometre domain: optical depth becomes a white wall. That was tried and washed out the ruins.
13. **Drone close-ups** stay on the 500-year picture, then the last shot eases back to the locked wide camera. Beats `drone_husk`, `drone_facade`, `drone_span`, `drone_orbit` in the handmade episode. The ready-city yaml still has those camera paths copied from the river city; they are **not** reframed for the downloaded block. Do not render them until the camera is retargeted.
14. **Ready-made assets only. Do not build the city, people, trees, cars, or ruins from primitives.** Order: asset hub, then CC0 with no attribution (Poly Haven, ambientCG, Kenney, Quaternius, Sketchfab CC0), then stop and say what you checked. Box primitives as buildings are not allowed. A ground sheet under a placed city, so the block is not floating in the sky, is the only local surface the ready episode adds.
15. **Realistic trees**, not neon lawn cards and not a flat green repaint. 1 year grass is cracks and verges only. The handmade `forest_floor` role is forced hidden because it painted the far bank neon green.
16. **Nothing floating, nothing sunk.** Seat meshes on the ground from the world-space bbox (`matrix_world` after parenting). Photoscan mountains and the Gaea range have awkward origins; measure them. Do not bury a city in a ground plane. Do not leave a ruin parent un-updated: call `view_layer.update()` before reading bounds.
17. **Lossless speedups only.** A speedup is kept only if 2–3 final-resolution frames (1080×1920, the sample count you will ship) match the unsped render with **SSIM ≥ 0.99** and the crops of windows, foliage, and any text look the same. This test was **not run**. Kristóf said to pause it ("pauzáld ezt a várost") before the first pair was rendered. Current `build.py` already turns on OIDN, adaptive sampling (threshold 0.08), 4 total bounces, and persistent data. Those were **not** passed through the SSIM gate. Do not lower samples or add culling/LOD until the table exists. GPU: skip on this machine.
18. **Never commit raw Free Standard, BlendKit, or Sketchfab files.** Render them. Log name, id, license, and size in `assets/FOUND_ASSETS.md`. Cache only.
19. **No Malaysia Airlines livery.** `airport_city_scene.glb` has that jet. Do not place it until the livery is plain.
20. **Do not encode the 1800-frame film** until Kristóf approves the stills he asked for.
21. **Segmented rendering stays.** 2–5 s chunks, 1–2 handle frames, cache key from code + assets + camera + per-frame channels. Do not replace it with one 1800-frame Blender job.
22. **Re-fetch the hub** at the start of an episode. Drive id for `ASSET_HUB.json` is `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV`. The copy on disk can be older than Kristóf's Drive.
23. **Memory cap is about 15 GB.** Exit 137 is the OOM killer. Exit 139 on Blender *quit* after `wrote ...png` has happened on this machine; the PNG is still valid. Do not treat 139-after-write as a bad frame.
24. **Update this handoff** at the end of every run that changes the city, stills, rules, or render path. Commit it on your branch and refresh `/opt/cursor/artifacts/handoff/city_decay_HANDOFF.md`.

### Rejected attempts (why)

- Quaternius boulder row as mountains. Read as low-poly rocks, not a range.
- `bk_peak.glb` toward camera. It is a floating photoscan slab.
- Glacier photoscan stood on edge. It is a flat sheet.
- Gaea range centered and upright close to the camera. The cliff is a wall. It must sit behind the snow peaks, buried slightly. Native size is about **2 × 2 × 0.23 m**. Scale from that, not from the snow meshes.
- `free_textured_mountain.glb` and `three_peaked.glb` scaled as if they were 2 m toys. They already import at **about 2000 × 2000 × 348 m** and **1024 × 1024 × 162 m**. Multiplying by hundreds puts the camera inside the mesh. That was the dark "cylinder" covering the 100y/500y handmade stills. Use scale about **1.15–1.8** and place the near edge past the skyline.
- Hiding the skyline at 500y and leaving dirt. Rejected as "the city disappeared."
- Putting the intact skyline back and tinting it brown (`3f60b18`). Rejected as a regression.
- Neon-green far-bank sheet at 1 year (`forest_floor` + park green). Grass only in cracks and verges.
- Flat tan/brown material override on near buildings. Keep the downloaded facade and add grime.
- Assembling the skyline from primitive boxes or tiny scattered cubes.
- Cell-fracturing a joined road mesh or any mesh whose world size is over about 45 m or whose vertex count is over 8000. Shards came out kilometres wide and the render OOM'd.
- A second rigid-body point-cache bake in the same process. Blender 4.5 segfaults. Fracture every building, then **one** bake.
- Deleting rigid-body constraint empties while the world still points at them. Segfault. Hide them and move them to z=−400.
- Ruined-city shells scaled with the **local** glTF scale after unparenting. Parent scale was lost and shells became kilometres tall. Use `matrix_world.to_scale()`.
- Fog density 0.012–0.016 through a domain the camera sits inside. The 100y/500y frame became a white wall. Shrink the domain, put the camera above it, cut density.
- License-filtering the debris search after Kristóf said every model in that search is free and needs no attribution. Use the hub copies. Still do not commit the raw files.
- Buildify. Optional and not used. Ruined City Free 5 is the ruin set.
- Full-city Geometry Nodes scatter of thousands of realized trees, plus Displace on every building. OOM (exit 137) around frame 871 or 1096 of the handmade scene. Instances only, foreground only, density well under 0.02 on a city-sized mesh.

---

## 3. Architecture, layout, setup, how to render

### Repo layout

Repo root is the git root (`/workspace` on this machine). The Blender project lives in `whatif/`.

| Path | Role |
|---|---|
| `whatif/episodes/*.yaml` | Episode specs. Channels, beats, camera, UI, audio flags. |
| `whatif/engine/spec.py` | YAML to frame curves. `CHANNELS`, `resolve`, `channels_at`, `beat_at`, `sfx_document`. |
| `whatif/engine/build.py` | Blender entry. Builds the scene, sets Cycles, renders frames. |
| `whatif/engine/scenes.py` | All handmade scenes, including `build_river_city`. Routes `scene.name == ready_city`. |
| `whatif/engine/ready_city.py` | Downloaded-city episode only. |
| `whatif/engine/effects.py` | Per-frame channel application. Calls `ready_city.drive` when `kit.kind == ready_city`. |
| `whatif/engine/decay_vfx.py` | Erosion, ivy, overgrowth GN, cell fracture, ANT hills, ruin-forest GN. Used by the handmade city. |
| `whatif/engine/city_layout.py` | Bridge and street numbers for the handmade city. Pure Python, no Blender. |
| `whatif/engine/segments.py` | 2–5 s chunk plan, cache key, overlap check, ffmpeg encode. |
| `whatif/engine/overlay.py` | Title and counter composited on PNG. |
| `whatif/engine/cc0_city.py` | CC0 cache placement. `CC0_CACHE`, default `/opt/cursor/asset-cache/cc0`. |
| `whatif/engine/private_assets.py` | Private cache placement. |
| `whatif/engine/found_assets.py` | CC0 models logged in `assets/FOUND_ASSETS.md`, plus Ivy Gen. |
| `whatif/engine/opening_metrics.py` | Zenith numbers and tolerances. |
| `whatif/render_episode.py` | CLI. Run from `whatif/` or pass a path. |
| `whatif/docs/whatif_engine.md` | Short engine note. Hub order. |
| `whatif/docs/whatif_humans.md` | Beat lines and sources. Not a voice track. |
| `assets/FOUND_ASSETS.md` | Download log. Do not put binaries here. |
| `whatif/review/` | Review JPEGs that are allowed in git. |
| `/opt/cursor/asset-cache/` | Gitignored downloads. |
| `/opt/cursor/artifacts/handoff/` | Copy of this file for Drive upload. |

### Setup from zero

```bash
# Blender 4.5.9 LTS is /home/ubuntu/blender/blender on this VM.
# System python3 has PyYAML and numpy. Blender's python does not have PyYAML.
# Resolve YAML with system python. Pass JSON into Blender.

python3 -m pip install --user pyyaml pillow numpy   # if missing

# Extensions (not bundled in 4.5). Already installed on this VM under
# ~/.config/blender/4.5/extensions/user_default/{cell_fracture,antlandscape}
# Enable names: bl_ext.user_default.cell_fracture , bl_ext.user_default.antlandscape
# Ivy Gen is a file, imported by found_assets.grow_ivy:
#   whatif/addons or assets/found/addons/add_curve_ivygen.py

# Hub
mkdir -p /opt/cursor/asset-cache/hub
curl -L 'https://drive.usercontent.google.com/download?id=1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV&export=download&confirm=t' \
  -o /opt/cursor/asset-cache/hub/ASSET_HUB.json
curl -L 'https://drive.usercontent.google.com/download?id=1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T&export=download&confirm=t' \
  -o /opt/cursor/asset-cache/hub/ASSET_HUB.md

# CC0 packs listed in the hub. Script:
cd /workspace/whatif && python3 assets/fetch_cc0.py
```

Private GLBs are downloaded with the same curl pattern into `/opt/cursor/asset-cache/private/...`. See section 4. Do not `git add` them.

### How to render

Work from `/workspace/whatif`. System python for the CLI. `BLENDER=/home/ubuntu/blender/blender` if `render_episode.py` cannot find it (`Path.home()/blender/blender` is the fallback).

**One still** (proof, half res, 8 samples). Example is the ready city, frames 1 (day 1), 871 (100y), 1096 (500y):

```bash
cd /workspace/whatif
python3 -c "
from engine.spec import load_resolved
import json
json.dump(load_resolved('episodes/ready_city.yaml'), open('/tmp/ready_resolved.json','w'))
"
/home/ubuntu/blender/blender --background --python engine/build.py -- \
  /tmp/ready_resolved.json --out /tmp/ready_frames --frames 1,871,1096 \
  --samples 8 --scale 0.5 --format png
```

`build.py` reads JSON only. Do not point it at YAML.

**Preview** (a few hero frames, UI on, no encode):

```bash
cd /workspace/whatif
python3 render_episode.py episodes/ready_city.yaml \
  --frames 1,871,1096 --samples 8 --scale 0.5 --composite --no-encode \
  --out /tmp/ready_preview
```

**Final** (only after stills are approved). Full frame, segmented, PNG, then one encode. Do not launch this on a guess.

```bash
cd /workspace/whatif
python3 render_episode.py episodes/humans_disappeared.yaml \
  --segments --samples 8 --scale 1 --composite \
  --segment-min 2 --segment-max 5 --handles 2
```

Swap the yaml for `episodes/ready_city.yaml` if version B is the one that was approved. Output defaults to `whatif/out/<episode id>/` with `frames/`, `comp/`, `segment_cache/`, `segments.json`, and `<id>.mp4`.

EXR beauty, no UI: `--format exr`. Do not pass `--composite` with EXR.

Plan / top-down: not a flag. Clear `bpy.app.handlers.frame_change_post` or the locked camera handler overwrites the ortho camera. Then set `cam.data.type = 'ORTHO'`. The handmade plan used ortho scale about 1020 from `(0, 280, 980)` looking at `(0, 280, 0)`, 1200×1200. The ready city has no plan yet.

### Cycles settings actually in `build.py` today

These are what a render uses unless a frame handler overrides them. They are **not** SSIM-approved.

- Engine Cycles, device CPU.
- Samples from CLI, default 8.
- OIDN on, adaptive on, threshold 0.08, min samples `min(4, samples)`.
- `max_bounces` 4, diffuse 2, glossy 1, transmission 2, volume 0, transparent 4.
- Persistent data on.
- AgX, exposure 0.42, a glare/bloom composite node.
- No camera culling. No distant LOD.
- Ready city sets `volume_bounces = 1`, `volume_max_steps = 64`, `volume_step_rate = 1.6` inside `drive()` every frame.

---

## 4. Assets

### Fetch

```bash
curl -L 'https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t' -o <name>
```

No login. Confirm the file is a real GLB (`file` says `glTF binary`), not an HTML warning page.

### Hub documents

| File | Drive id |
|---|---|
| `ASSET_HUB.json` | `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV` |
| `ASSET_HUB.md` | `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T` |

Public folder: `1Sd1dFKDDifLNr4cSUZXLxwMJhYwedIDl`. Private folder: `1Wo8pbim5geqfTgl_G-8Re_FnDBlgXePF`.

### Cache paths

| What | Where |
|---|---|
| Hub docs | `/opt/cursor/asset-cache/hub/` |
| CC0 extracted | `/opt/cursor/asset-cache/cc0/extracted/` |
| CC0 zips | `/opt/cursor/asset-cache/cc0/zips/` |
| City blocks (procedural 3, 4, 6, one WTC, ruined city, commute) | `/opt/cursor/asset-cache/private/sketchfab/city_blocks/` |
| Other Sketchfab | `/opt/cursor/asset-cache/private/sketchfab/` |
| Hub debris + ruined city copy | `/opt/cursor/asset-cache/private/debris/` |
| Mountains + Alps HDRI | `/opt/cursor/asset-cache/private/mountains/` |
| BlendKit | `/opt/cursor/asset-cache/private/blendkit/` |
| Fracture pose cache | `/opt/cursor/asset-cache/private/fracture_cache/` |
| Ivy Gen source | `assets/found/addons/add_curve_ivygen.py` |

Env overrides: `CC0_CACHE`, `PRIVATE_CACHE` (see `cc0_city.py`).

### Packs and ids the city work actually uses

Living block (version B): `procedural_city_6.glb`, uid `d681c1a2d89e47acb03934d0a79107fd`, Drive `1_nD2dk2_2nmdBvIPsu3590qjf8Y-G0Q3`, about 60 MB, 313k faces. Author abhayexe. Free Standard. Cache: `city_blocks/procedural_city_6.glb`.

Ruin (both versions): `ruined_city_free_5.glb`, uid `4b0b0021d91442079a91b075576efe4e`, Drive `1viIoFfLy71G97yIXOt4K9s_GJ-5uElGO`, 77,330,052 bytes. Also at `city_blocks/ruined_city_free_5.glb` and `debris/ruined_city_free_5.glb`. Native bounds about x 20 m, y 50 m, z 12 m. Scale as a whole; do not scale one shell by its local glTF scale.

Debris (Drive ids, files in `private/debris/`):

| File | Drive id | Use |
|---|---|---|
| `concrete_rubble_steel.glb` | `1lSyTM9_FIWsITCj4sd1sd6BNErFxLxci` | Best rubble, steel bars |
| `pbr_debris.glb` | `1MK12j95AzBVcUK_7JIR0GRF_4r4WdyqY` | Large slabs |
| `pbr_debris_3.glb` | `1OIPRVnjAXgNffPp7e3z6zFBUwxUMXZej` | Shards and rebar |
| `pbr_debris_2.glb` | `1jvEeyuDU6N_8WBR1hbDXAsrQbB3GO2MN` | Sheet metal. Native about 100 m. Scale by longest side. |
| `scan_pile_concrete.glb` | `1gK-41dRKshvapWK1PdqlXffpsf6TDm9x` | Small scanned pile |
| `lowpoly_concrete_debris.glb` | `1Ffhb4eAY-IENKbXjNVgr-iC8aAUOIN2B` | Distant piles. Has LODs. |
| `debris_kit.glb` | `1q4tW4Wmu-HpT55OT2k4wJyLS0PahhTXU` | 494 tiny pieces. Joining them is one kit, not 494 hero props. |
| `asphalt_02.glb` | `1jcCbD5lZQdQ8gOvXpB-EMS1bFqTn6rSp` | Cracked slab |
| `asphalt_03.glb` | `1XoXSTcQ32Dh1clQeiPXxwxMD3ZlIkES6` | Manhole |
| `wood_planks_debris.glb` | `1EDdc7NHKqIWXgCWbejxj85d5x12P8sPl` | Planks. Native millimetres. Scale up. |
| `trash_tarp.glb` | `100TtFFQafSrJDj-RHhl0q4DUEDmxLQdb` | Tarp pile. Native about 2800 m. Scale by longest side or it fills the frame. |

Mountains:

| File | Drive id | Native size | Placement note |
|---|---|---|---|
| `gaea_range.glb` | `1uTqyJ7dNgY_XItgaJGfNo8Ag9qkPZpxp` | ~2 × 2 × 0.23 m | Scale ~1500 in height units. Behind the snow peaks. Bury the base a little. |
| `free_textured_mountain.glb` | `15lv0B3OxAyVi0TooPi_Tz6shbLwDOwch` | ~2000 × 2000 × 348 m | Scale ~1.15. Do not multiply by 1000. |
| `three_peaked.glb` | `1fe4xozIhUD7EnnDU_y208cvW2Tu0rfoi` | ~1024 × 1024 × 162 m | Scale ~1.6–1.8. |
| `bk_peak.glb` | `1sdNY81fyO7gxzg_pLLsVfItah3-JeXqm` | photoscan slab | Do not face it at the camera. |
| `alps_field_4k.hdr` | `1hlRHJKGiO4kd35HLTbJxgI7bWnJQcVD3` | HDRI | Lights. Not committed. |

Other private ids that matter:

| Asset | Drive id | Note |
|---|---|---|
| `procedural_city_3.glb` | `1f87GpiMUYnbH_BW2PmC7NUwwCYS-txPl` | Brick canyon. Handmade far bank / south blocks. Not the ready-city hero. |
| `procedural_city_4.glb` | `14KXRMRzP-lneWAxpm9xbdPxOcsVXnuSq` | 8-building block plus park. |
| `one_world_trade_center.glb` | `102_LwdYwZClJuww8h8QJKXBMnPxKMkKY` | Landmark. Handmade far bank. |
| `airport_city_scene.glb` | `11lGuGZgMCF6SR7rWR-gilTYD5YygQvyZ` | Do not use the Malaysia Airlines jet. |
| `city_commute_transport` | `18V05cyxam7BvcKDpLXYxOf85vlzQsoxs` | Bikes and scooters. The coach in that pack is branded; the handmade scene skips it. |

CC0: Kenney city / roads / cars, Quaternius nature and downtown, Poly Haven textures (`road_damaged`, `cracked_concrete`, moss, rust, forest ground), ambientCG asphalt damage. Fetched by `whatif/assets/fetch_cc0.py`. Logged in `assets/FOUND_ASSETS.md` and `whatif/assets/fetch/CATALOG.md`.

External pages Kristóf sent, already mirrored or rejected:

- Sketchfab ruined city uid `4b0b0021d91442079a91b075576efe4e` (hub copy above).
- Sketchfab debris search. He later said every model there is free with no attribution, then put the chosen files in the hub. Use the hub ids, not a fresh API crawl, unless the hub is missing one.

---

## 5. Episode specs, timeline, cameras, outputs, open feedback

Both yamls share the beat list and the 1800-frame clock. `ready_city.yaml` is a copy with `scene.name: ready_city`, `mascot: false`, and a different locked camera. Drone paths inside it are still the river-city coordinates. Do not trust them.

### Clock (both episodes)

| Frames | Beat | On-screen label | Collapse at end | Vegetation at end |
|---|---|---|---|---|
| 1–90 | vanish | title, population | 0 | 0 |
| 91–237 | power | +1 HOUR | 0 | 0 |
| 238–362 | flood | +2 DAYS | 0 | 0 |
| 363–498 | weeds | 1 YEAR | ~0.14 (held from previous, weeds does not set it) | 0.30 |
| 499–633 | streets | 20 YEARS | 0.18 | 0.46 |
| 634–746 | houses | 50 YEARS | 0.40 | 0.62 |
| 747–871 | towers | 100 YEARS | 0.68 | 0.78 |
| 872–984 | bridge | 300 YEARS | 1.0 | 0.90 |
| 985–1096 | forest | 500 YEARS | 1.0 | 1.0 |
| 1097–1174 | drone_husk | 500 YEARS | 1.0 | 1.0 |
| 1175–1252 | drone_facade | 500 YEARS | 1.0 | 1.0 |
| 1253–1330 | drone_span | 500 YEARS | 1.0 | 1.0 |
| 1331–1426 | drone_orbit | 500 YEARS | 1.0 | 1.0 |
| 1427–1528 | relics | 10,000 YEARS | held | 1.0 |
| 1529–1675 | seam | 10 MILLION YEARS | held | falls during ice |
| 1676–1800 | return | loop | snaps back | snaps back |

Proof frames used in practice: **1** (day 1, people still present), **498** (end of 1 year), **871** (end of 100 years), **1096** (end of 500 years). `spin_sun` in `decay_vfx.py` holds a daytime sun on the last 3 frames of weeds, houses, towers, bridge, and forest so a still is not a night shot. Mid-beat frames still spin. The ready-city drive then overrides the sun when collapse > 0.4.

### Cameras

Handmade locked camera (`humans_disappeared.yaml`): location `[-85, -90, 80]`, target `[12, 130, 4]`, lens 57.2 mm, sensor horizontal 36 mm, clip end 14000. Looks up the bridge from the near avenue.

Ready locked camera (`ready_city.yaml`): location `[-145, -150, 52]`, target `[8, 10, 36]`, lens 28 mm, clip end 8000. Outside the southwest corner of the block, slightly above the street fog. This was the "slightly better place" pass. The grey ground still fills the lower third. A later pass can come in closer only after measuring the block corner (about ±125 m).

Drone paths: see the yaml. They assume the handmade avenue at y≈22 and the river span. Wrong for the ready city.

### Versions and URLs

| Version | Commit | Status | URLs |
|---|---|---|---|
| Handmade stills, owner rejected mountains and 500y | `3f60b18` | historical | `.../raw/3f60b18/whatif/review/four_stills.jpg` and `plan.jpg` |
| Handmade stills, latest | `b33e88f` | open, PR 11, not approved for encode | https://github.com/dagadt675-oss/juicytea-media/raw/b33e88f/whatif/review/four_stills.jpg and `plan.jpg` |
| Ready city proof | `60c8318` | open, PR 21, not approved | https://github.com/dagadt675-oss/juicytea-media/raw/60c8318/whatif/review/ready_city/three_stills.jpg plus `day.jpg`, `100.jpg`, `500.jpg` |

Prefix every raw URL with `https://github.com/dagadt675-oss/juicytea-media`.

### Open feedback (unanswered)

- Which city continues: handmade river (`PR 11`) or downloaded block (`PR 21`)?
- Ready-city 100y/500y: ruins read, mountains read, one foreground light shaft reads. Shafts do not yet cut between towers. Fog must not get thicker.
- Ready-city day 1: the block reads. The lower frame is still empty ground. People and moving traffic were not re-staged on this block.
- Handmade 500y was never signed off. Do not treat `b33e88f` as approved.
- Speedup SSIM table: paused, not delivered.
- Full encode: not approved.

---

## 6. QC and verification

Run from `/workspace/whatif` with system python.

| Check | Command | Pass |
|---|---|---|
| Episode clock | `python3 -c "from engine.spec import load_resolved; r=load_resolved('episodes/humans_disappeared.yaml'); assert r['frame_count']==1800"` | 1800 frames, 30 fps, 1080×1920 |
| Segment plan | `python3 -m unittest tests.test_segments` | Chunks cover every frame once, 2–5 s, handles match, cache key changes only for touched beats, ffmpeg command is one encode |
| Zenith masks (no Blender) | `python3 -m unittest tests.test_opening_metrics` | Synthetic masks within the zenith targets |
| Zenith opening render | `python3 -m unittest tests.test_opening_frame` | Low-res day-1 frame still contains river, lawn, avenue. Slow. Handmade episode only. |
| Bridge geometry | `python3 -m unittest tests.test_bridge_geometry` | Deck does not use the mirrored yaw. Numbers live in `city_layout.py`. |
| Skyline windows | `python3 -m unittest tests.test_skyline_windows tests.test_library` | Window material and asset library tests |
| Speedup gate (not run) | 2–3 frames at 1080×1920, same seed (`frame * 997 + 17`), SSIM on luma, crops of windows / foliage / text | SSIM ≥ 0.99 and crops match. Otherwise revert that setting. |
| Private files not in git | `git status` and `git ls-files '*.glb' '*.blend'` | No Free Standard or BlendKit binaries |
| GLB is a GLB | `file <path>` | `glTF binary`, not HTML |
| Roads vs water | Handmade `plan.jpg` | No street centerline enters the river polygon (`RIVER_Y0=86` to `RIVER_Y1=150` in `city_layout.py`) |
| OOM | watch Blender RSS | Stay under ~15 GB. If you see `Mem:13xxx.M` and then exit 137, you are at the wall. |

SSIM recipe when you do run the gate: same frames, one knob changed, luma, 11×11 Gaussian window, K1=0.01, K2=0.03, L=255. Compare crops, not only the full frame. A high SSIM with mushy windows is a fail.

---

## 7. Segmented rendering and Colab

### What exists

`whatif/engine/segments.py` and `render_episode.py --segments`.

- Beats are packed into 2–5 second chunks (`--segment-min`, `--segment-max`).
- Each chunk renders `handles` extra frames on each side (default 2, clamp 1–2) so motion blur matches a full render. Handles are dropped at assembly.
- Cache key is SHA-256 of code digest, asset digest, samples, scale, format, resolution, fps, camera, scene, features, and per-frame channel samples on the rendered range including handles.
- A beat edit re-renders that chunk and the neighbour that uses its frames as handles. A camera, code, or asset edit re-renders every chunk.
- Cycles seed is `frame_seed(frame) = frame * 997 + 17`, not the segment index.
- Overlaps can be checked against each other and against `--verify-full <dir>`.
- Assembly hardlinks `f_####.png` into `frames/` for frames 1..N only.
- Encode is one ffmpeg call: libx264, yuv420p, crf 18, `+faststart`, `-frames:v` equal to the film length. PNG composite first if you want the title. EXR is not composited and is not what ffmpeg is set up for in the tests (the command still builds an input pattern; do not encode EXR with that command without checking).

Local stills and previews still use the segment tools above. There is no Colab notebook and no `render_bundle.ipynb`. The final for version B is a packed blend, not a segment-cache upload.

### Colab bundle (version B, ready city)

Built 2026-10-11 with Blender 4.2.3. The blend is packed (`bpy.ops.file.pack_all()`, 131 images, 0 unpacked external files, 0 libraries). Era hides, sun, fog density, and weather cards are keyframed for frames 1–1800. Frame-change handlers are cleared. No add-on, no RBD cache, no fluid cache. Fog is a Principled Volume shader.

Repo copies of the text files (the blend is not committed):

- `whatif/colab/city_decay/render.py`
- `whatif/colab/city_decay/manifest.json`
- Rebuild, 4.2.3 only: `whatif/colab/pack_ready_city.py` (reads `/tmp/ready_city_resolved.json`, writes `/tmp/city_decay_bundle/scene.blend`)

Artifact parts, each under the store's ~100 MB ceiling and under the 1.9 GB cap:

| File | Bytes |
|---|---|
| `/opt/cursor/artifacts/colab_bundle/city_decay/city_decay.zip.00` | 94371840 |
| `/opt/cursor/artifacts/colab_bundle/city_decay/city_decay.zip.01` | 94371840 |
| `/opt/cursor/artifacts/colab_bundle/city_decay/city_decay.zip.02` | 94371840 |
| `/opt/cursor/artifacts/colab_bundle/city_decay/city_decay.zip.03` | 13542134 |
| `JOIN.txt` in that same directory | rejoin instructions |
| `verify/0001.png`, `verify/0871.png` | proof frames from the clean unpack |

Rejoin and run:

```bash
cat city_decay.zip.00 city_decay.zip.01 city_decay.zip.02 city_decay.zip.03 > city_decay.zip
unzip city_decay.zip
blender -b scene.blend -P render.py -- START END
```

Joined zip: 296657654 bytes, SHA-256 `8ef8dc15712f2cb2af15e8115fd42f271b62fb08cede1005a8cf1b21e7901fa7`. `unzip -t` passed after copying the parts back off the artifact store.

`render.py` sets Cycles to OptiX, then CUDA, then CPU. Samples 32, adaptive threshold 0.01, minimum 8, OIDN, max bounces 6, volume bounces 1, 1080×1920, 30 fps. It writes `frames/0001.png` beside the blend (`//frames/####.png`). Seed is `frame * 997 + 17`. It does not import `whatif`.

`manifest.json`: blender 4.2.3, frames 1–1800, fps 30, 1080×1920, samples 32, `est_sec_per_frame_cpu` 63, `est_sec_per_frame_t4` 16 (guess: CPU mean / 4). Overlay notes: beauty only; title `What if every human vanished… right now?`; counter is population 8.2 billion then the year, composited later by `whatif/engine/overlay.py`. No narration, no music. SFX stays in `sfx.json`.

Do not upload loose Free Standard GLBs. They are already packed inside the blend. Do not start the 1800-frame encode on this VM.

---

## 8. Known bugs and next steps

Priority order. Stop when Kristóf picks a version. Do not encode.

1. **Get a yes or no on PR 21 vs PR 11.** Do not merge them into one picture.
2. **Ready city, if he stays on it.** Move the camera so the grey ground is not half the frame, without clipping the block. Keep fog thin. Make the 100y/500y shaft read between ruins, not as a blob in front of the lens. Show 500y trees through that fog. Retarget or delete the copied drone paths before any drone frame. People and traffic only from assets already in the block or the hub, and they must vanish.
3. **Handmade city, if he stays on it.** 500y must read as collapsed ruins from `[-85,-90,80]`, not a brown intact skyline and not an empty lot. 100y far towers still need to read as broken. 1y must not repaint the far bank green. People on day 1 are still small in the wide frame (a 1.75 m figure at ~100 m is ~30 px). Near-camera scale-up was tried (`height` about 3.2–3.5 m on the south sidewalk) and is still easy to miss. Do not grow them into giants. Place downloaded people closer to the lens.
4. **Do not re-run the fracture bake casually.** One bake per process. Skip meshes over 45 m or 8000 verts. After a bad bake, bump `FRACTURE_CACHE` so the next run does not load kilometre shards. Second bake segfaults. Deleting constraint empties segfaults.
5. **Mountain scale.** Re-measure before any new placement. Snow and three-peaked are already kilometres. Gaea is 2 m.
6. **Speedup SSIM table.** Paused. Not a next step until he asks. If he asks: full 1080×1920, 2–3 frames (1, 871, and 498 or 1096 if memory allows), one knob at a time, SSIM ≥ 0.99, crop check, table of setting / SSIM / seconds per frame before and after. GPU row is "skipped, no device." Keep segmented rendering either way.
7. **Cryptomatte / EXR era transitions.** Not implemented. Object index passes for deck, canopy, and portal exist for the metric only. Do not wire a transition until the stills are approved.
8. **500y OOM on the handmade scene** if you turn on ruin-forest GN plus foothill trees plus fracture shards plus ANT. The ready city at half res did not OOM.
9. **Blender exit 139 after a successful `wrote` line.** Keep the PNG.
10. **`ready_city.yaml` drones** still point at the river. Rendering frame 1175 today flies through the wrong coordinates.

---

## 9. Branches and pull requests

Stack that matters for this city, from older base to newer tip:

| PR | Head | Base | Tip commit (this VM) | Role |
|---|---|---|---|---|
| 5 | `cursor/whatif-humans-engine-f245` | `main` | `d7e9755` | Engine and first river city. Open. |
| 8 | `cursor/bridge-road-skyline-f245` | `cursor/whatif-humans-engine-f245` | `5224be4` | Bridge, roads, skyline logic. Open. |
| 10 | `cursor/segmented-render-f245` | `cursor/whatif-humans-engine-f245` | `6ac3651` | Segment cache. **Stale relative to the city tip.** It does not contain the road, mountain, or ready-city commits. Do not rebase the city onto it blindly. The segment code is already on the city branches. |
| 11 | `cursor/road-network-stills-f245` | `cursor/bridge-road-skyline-f245` | `b33e88f` | Latest handmade stills. Open. Not approved. |
| 21 | `cursor/ready-city-f245` | `cursor/road-network-stills-f245` | `60c8318`, handoff `7032728`, plus the Colab-bundle commit on this branch | Downloaded city. Open. Not approved. Colab zip is an artifact, not a git blob. |

`main` on this VM was `1ea85e4` and `git status` at last check said it was **behind origin/main by 2**. Fetch before you branch from main. Other open PRs (1–4, 6–7, 9, 12–20) are map, Greenland, plane-seat, and scale-journey work. They are not this city. Do not edit them.

Local branches match those tips. The handmade review JPEGs in `whatif/review/four_stills.jpg` and `plan.jpg` on `ready-city-f245` are the `b33e88f` files, because this branch contains that commit. The new stills are only under `whatif/review/ready_city/`.

### Last actions before this handoff

- Version A stills committed and pushed (`b33e88f`, PR 11).
- Version B built, proof-rendered, committed, pushed (`60c8318`, PR 21).
- Speedup A/B not started. Kristóf paused it in the same hour.
- No full encode. No Cryptomatte.
- 2026-10-11: version B Colab bundle packed with Blender 4.2.3, two frames verified from a clean unpack (1 and 871), zip split into four parts under `/opt/cursor/artifacts/colab_bundle/city_decay/`.

When you finish a run, append a dated paragraph under section 1 and fix any row in sections 5 and 9 that you changed. Commit the markdown and refresh the artifacts copy.
