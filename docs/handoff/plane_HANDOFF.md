# Plane-seat Short — handoff

Silent portrait picture for “The back of the plane had the best odds.” One chase camera, 32.81 seconds, 984 frames at 30 fps, 1080×1920. No wireframe. The beauty pass is Blender Cycles. Karaoke captions, stat pills, the teal/orange grade, and the 32.81 s retime happen after the beauty PNGs.

This note matches the scene that was packed into the Colab preview bundle on 11 Oct 2026. That bundle is a look at the current picture, not a finished film.

## Preview bundle (current scene, as packed)

Path: `/opt/cursor/artifacts/colab_bundle/plane_seat_preview/`

| File | Bytes |
| --- | --- |
| `plane_seat_preview.zip.00` | 94,371,840 |
| `plane_seat_preview.zip.01` | 94,371,840 |
| `plane_seat_preview.zip.02` | 44,206,750 |
| Reassembled zip | 232,950,430 |
| `scene.blend` inside the zip | 268,144,841 |

The parts are 90 MiB, under the 1.9 GB ceiling. This artifact volume rejects a single file over 100 MiB (`EINVAL` on close), so the zip is split finer than 1.9 GB. `zip -s` multi-volume archives from Info-ZIP 3.0 did not round-trip; these parts are a GNU `split` of one ordinary zip. Reassemble in order:

```bash
cat plane_seat_preview.zip.* > plane_seat_preview_full.zip
unzip plane_seat_preview_full.zip
```

`scene.blend` is a gzip-compressed Blender file with images and the Anton label font packed (`bpy.ops.file.pack_all()`). Blender opens it without the asset cache. Confirmed by rendering with `/tmp/plane_hdri` moved aside.

Render a range (1-based, inclusive):

```bash
blender -b scene.blend -P render.py -- START END
```

`python3 render.py START END` relaunches that command when `blender` is on `PATH` or `BLENDER` is set. Frames land next to the blend as `frames/####.png` (Blender path `//frames/####.png`).

Preview settings inside `render.py`: Cycles, OptiX then CUDA then CPU, 1080×1920, 64 samples, adaptive threshold 0.01, minimum 8 samples, OpenImageDenoise, persistent data, camera culling, distant tree LOD. The full clock is frames 1–984. `manifest.json` in the zip repeats the fps, range, samples, and overlay notes.

Check render, from the unpacked zip, skies hidden: frame 61 (t = 2.00 s, city). CPU only (no OptiX/CUDA on this machine). 64/64 samples, 3 min 32.7 s, `frames/0061.png` is 6,233,287 bytes. The jet, sunset, and city blocks are in frame. A copy of that PNG is `verify_frame_0061.png` in the same artifact folder.

Do not commit the blend or the hub models inside it. They are packed so Colab can render, not so they can be redistributed.

## What the beauty frames do not include

`render.py` writes the beauty pass only.

- In the PNGs: jet, one biome at a time, Easy Clouds volumes when the flight clock asks for them, and the 3D percent labels (38 / 39 / 32 / 44 / 28) while their windows are open. View transform is AgX, look “AgX - High Contrast”, exposure −0.55.
- Not in the PNGs: karaoke (x 90–900, y 1120–1420) and stat pills (y 300–1050) from `whatif/plane_seat/engine/overlay.py`. After that, `render_episode.py` adds a teal shadow / orange highlight bias and fine grain, encodes silent H.264 at 30 fps, then `itsscale` 32.81 / (984/30) so the master is 32.81 s. Playback of the PNG sequence at 30 fps is 32.80 s.

The approval stills in `v/plane_tests/` are beauty plus karaoke (`composite(..., pills=False)`) plus that grade. They are not the Colab frames.

## Clock

Source of truth: `whatif/plane_seat/engine/clock.py` and `examples/words.json` (duration 32.81, single narrator take).

Frame 1 is t = 0. Frame N is t = (N − 1) × 32.81 / 984. `pose_at` wraps with modulo so t = 0 and t = 32.81 match.

Biome under the jet (`flight.biome_at`), swaps sitting on cloud peaks:

| Until (s) | Biome |
| --- | --- |
| 4.08 | city |
| 10.02 | forest |
| 18.05 | mountains |
| 24.38 | ocean |
| 28.55 | desert |
| 31.85 | cloudsea |
| 32.81 | city |

Narration beats in `clock._shot_beats`: city hook at 0, “Not the front.” at word 9, forest line at 4.08, the 38/39/32 line at 10.02, the 44% line at 18.05, the 28% line at 24.38, the caveat at 28.55.

Camera, altitude, pitch, and roll are centripetal samples of the keys in `flight.py`, plus a small periodic drift. The path is periodic. Chase eyes sit behind the tail (nose is +X). Interior eyes sit in the aisle around 22.5–27.8 s. X-ray is a short gaussian on each third, not the whole flight. Seat colors: front and middle amber, back green; aisle-mid goes red on the 44% line; back-middle goes bright green on the 28% line.

Ground tiles are 1200 m (`aircraft.TILE`). Travel over the film is 4800 m, an integer number of tiles, so the scroll seam repeats.

## How the scene is built

`whatif/plane_seat/engine/build.py` `build_scene()` is the picture. `apply_pose` moves the aircraft root, swaps the world HDRI, hides the other biomes, fades the fuselage for x-ray, cuts the crown open when `cutaway` is set, paints seat object-color, and aims the camera. There are no baked keyframes. The Colab `render.py` loads the packed blend and calls the same `apply_pose`. `_sky_image` uses an image already in the file (packed skies are named by filename) before it tries `/tmp/plane_hdri`.

Aircraft: BlendKit 405-FLA from the private cache, nose turned to +X. White paint keeps its maps, plus clearcoat and a little ambient occlusion. A fuselage-only material copy (`FuselageSkin`) is what the x-ray fades. `BodyCutaway` is the same mesh with the crown faces deleted. Fan discs sit in the intakes. Gear is hidden.

Cabin: the owner cabin GLB, nose turned, scaled to the 66.5 m tube. Cockpit cluster in front of x = −30.5 is removed. Seats are one cabin seat, instanced as 36 rows at 0.80 m, 3-4-3 (360 seats). `aircraft.py` still describes an older 30-row 3-3 procedural jet; the picture does not use that mesh.

Biomes, parented so they scroll in x:

- City: `procedural_city_3.glb` collection instances.
- Forest: Poly Haven `fir_sapling_medium` and `pine_sapling_medium`, decimated, scaled to about 28–46 m, bases on z = −2. A 26×16 stand sits ahead of the nose. Far copies swap to a decimated mesh past 750 m when LOD is on.
- Mountains: hub `gaea_range.glb`, `three_peaked.glb`, `free_textured_mountain.glb`, `bk_snow_cliff.glb`. Snow grade on upward high faces. Raw GLBs stay in `/opt/cursor/asset-cache/private/mountains/` and out of git. `bk_peak.glb` was fetched and not placed.
- Ocean: Blender Ocean modifier.
- Desert and cloudsea: photo ground planes.

Clouds: Easy Clouds 2.2 sphere volumes on `CloudField`, low density (about 0.04–0.08), white. A cabin god-ray volume shows when the roof is open. The addon’s node groups are stored in the packed blend, so Colab does not need the addon enabled.

Skies: Belfast sunset pure sky (city, mountains, ocean), Kloofendal partly cloudy (forest, cloudsea), Goegap (desert). `lago_disola_4k.hdr` is extracted beside them and is not the world image in this build.

Labels: Anton text, parented to the aircraft, turned toward the camera each frame. 38/39/32 sit beside the tube. 44 and 28 sit nearer the aisle. Sizes were reduced so they sit inside the portrait frame; the stills still need a check that 44% is fully inside the safe area.

## Render entry points

- Stills: `python whatif/plane_seat/render_stills.py` writes `v/plane_tests/00_hook.jpg` through `07_forest.jpg`. Optional name filter. Samples default to 8. Each still overrides eye, look, altitude, and biome, then composites karaoke.
- Film: `python whatif/plane_seat/render_episode.py` builds beauty through `build.py`, composites, grades, and encodes `v/plane_seat_silent.mp4`. Default samples in that script are 4, which is the old draft count, not the Colab preview’s 64.
- Colab: the packed blend and `render.py` above. Do not point Colab at the repo paths under `/opt/cursor/asset-cache` or `/workspace/assets`.

Cycles in `build_scene`: 4 max bounces, 2 diffuse, 2 glossy, 4 transmission, 8 transparent, 2 volume, volume step rate 1.8, persistent data, motion blur shutter 0.35. The builder also pins threads to 4 for this machine; `render.py` sets threads back to AUTO.

## Speed bench already measured (CPU, this scene family)

Same three frames: 61 (city), 123 (cloud), 685. Wall seconds from `/tmp/bench/*.log`:

| Run | f61 | f123 | f685 |
| --- | --- | --- | --- |
| base (persistent on) | 19.0 | 553.6 | 11.3 |
| persistent off | 37.6 | 718.8 | 12.4 |
| bounces capped (4 / vol 2) | 20.9 | 519.6 | 12.7 |
| adaptive + OIDN, 4 samples | 20.0 | 568.6 | 11.3 |
| adaptive + OIDN, 2 samples | 12.8 | 282.2 | 9.1 |
| camera cull | 18.5 | 555.7 | 11.1 |
| distant tree LOD | 19.0 | 573.8 | 12.5 |

Cloud frames dominate. The 2-sample cap was the one the earlier review rejected on SSIM. The preview bundle uses 64 with adaptive sampling so a Colab GPU pass stays in a preview budget without dropping to that 2-sample cap. Frame 61 at 64 samples was 212.7 s on this CPU.

## Assets and licenses

Inventory: `assets/FOUND_ASSETS.md`.

CC0 (Poly Haven trees and ground/HDRIs, Kenney and OpenGameArt SFX) can live under `assets/found/`. Sketchfab Free Standard and BlendKit files (405-FLA, cabin, city, hub mountains, lago HDR) stay in the private cache. Render them. Do not commit the raw files or the packed blend.

## Last still pass

Judged at full 1080×1920 in `v/plane_tests/` after the fixes below.

- `02_cloud_punch`: white cumulus against blue sky, jet tail and wing in frame. Volumes are Principled Volume puffs (the Easy Clouds density was either fog or black). The punch camera looks up so the ground plane stays out of frame.
- `03_mountains`: oblique pass of two snow-capped rock ridges (`bk_snow_cliff`), jet beside them. `three_peaked` and the huge gaea instances were dropped from the valley because their ground faces became floating slabs.
- `04_xray_seats`: whole jet in a front 3/4, fuselage transparent, 32% / 39% / 38% plates readable and inside the frame.
- `05_cabin_heatmap`: `44%` sits in the aisle, fully inside the frame, not on the top edge.
- `07_forest`: photoscanned fir and pine fill the view under the wing. Bases are seated on the ground.
- Jet: navy cheatline, window rows, engine nacelles, clearcoat and a light circumferential ring on the tube only. A full panel grid read as a wireframe and was removed.

`00_hook`, `01_city_flyover`, and `06_ocean` were re-rendered with the same jet.

Film beauty is Cycles, 4 samples, adaptive threshold 0.02, OIDN, culling, distant tree LOD. `python whatif/plane_seat/render_episode.py --samples 4 --force` writes `v/plane_seat_silent.mp4`. On this 4-core CPU a frame is about 22 s, so the 984-frame pass is several hours. Do not reuse an old `/tmp/plane_seat_cache/beauty` from a previous scene.
