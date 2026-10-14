# Plane-seat handoff

This file is the state of the silent Short “The back of the plane had the best odds” as of 13 Oct 2026. A new agent with this file and the repo can continue without the chat.

## 1. Mission and current state

Mission: a photoreal, shaded, silent 32.81 s YouTube Short, 1080×1920, 30 fps, 984 frames. No wireframe. One chase camera timed to the narrator take in `whatif/plane_seat/examples/words.json`. Karaoke captions, stat pills, a teal/orange grade, SFX, and the 32.81 s retime are applied after the Blender beauty pass.

What exists now:

- Kristóf rejected the Colab frames 493–984 (sideways horizon, black frames, fuselage close-ups, upside-down 32% card, the jet diving into the city, faceted snow). Those frames and the 1–492 chunk from that bundle are scrapped. Do not resume that render.
- The camera aim no longer uses a shortest-arc quaternion. The horizon stays level, and a steep top-down blends continuously toward nose-up so the fuselage runs up the 9:16 frame. The lens stays above the wing and off the fin. It never enters the cabin. The 44% and 28% beats stay on the rear 3/4 so the fuselage, seats, and the ground or sky stay in frame. Percent cards are billboarded after the camera matrix updates, at a size that is at least 5% of the frame height. The cutaway keeps the aircraft’s parent inverse so the opened mesh does not scale up and swallow the lens.
- Review v6 (no final render): distance haze starts much farther out, so the 1600 m chase is not an orange wash. The same city block is repeated out to about 140 km, street-scale nearby and larger copies at the horizon. Ocean stays blue water. Desert uses the aerial sand photo plus broad dune noise. Mountain snow is a soft low-frequency sheet plus the textured hub peak; the Gaea satellite albedo and the square-based peak prop are out of frame because both flickered black and white at phone size.
- Review v7 (no final render): Kristóf rejected the biome cuts, the single tail-chase, the missing hook, the unanchored cards, and the desert-to-city loop. v7 is one 12 km route. The camera eases from a top-down hook through a rear three-quarter, a side, a top-down seat map, and a front three-quarter, then back to the hook. Frame 984 matches frame 1, over a copy of the opening city. The crown slides off instead of popping. Cards are 38, 39, 32, 44, 28, and 17, each on a leader, and the first zone is on by 2 seconds. Stills and the animatic are in `plane_review_v7`. Do not start a final until Kristóf accepts them.
- Review v8 (no final render): the v7 orbit, hook, and loop stay. The ground is one mesh. Heights are the SRTM tile N45E007 for a short mountain leg and the broad forms of the Poly Haven `dirt_aerial_02` displacement for the dunes. Blend edges follow that same scan, so a border wanders instead of cutting straight. Snow is the `snow_02` scan. Water is a shore-following sheet plus one Ocean-modifier tile that does not repeat. City blocks thin out into the fields. Cards stay between the lens and the fuselage, copy the camera’s orientation, and ease in; the six read 38%, 39%, 32%, 44%, 28%, and 17%. The review set is `plane_review_v8`. Do not start a final until Kristóf accepts it.
- Check stills for v6 are 540×960 Cycles JPEGs, frames 1, 110, 230, 430, 530, 710, 830, 984, in `v/plane_tests/checks/` and the `plane_review_v6` artifact folder. Do not start the final 984-frame render until Kristóf confirms.
- The v6 animatic is `v/plane_seat_animatic.mp4`: 984 frames, 540×960, 30 fps, 32.80 s, H.264 CRF 30, about 1.6 MB. It is a 4-sample Cycles pass of this same scene. Finals are not packed. Wait for approval.
- Older approval stills remain in `v/plane_tests/` (`00_hook` through `07_forest`). They were shot with the old aim and are not the film path.
- Working branch: `cursor/plane-seat-review-v8-4316`. Final 984-frame render is still waiting on confirmation. The v7 review set stays in `plane_review_v7`. The v8 set is `plane_review_v8`.

## 2. Kristóf’s rules and rejected attempts

Rules, in the order they were given. Later rules override earlier ones when they conflict.

1. The picture is photoreal and shaded. No wireframe.
2. Use ready-made assets. Do not model the jet, cabin, city, mountains, or trees from scratch.
3. Approval stills come before the full film.
4. Duration is 32.81 s, 984 frames, 30 fps, 1080×1920 portrait. Frame 1 is t=0. The PNG sequence at 30 fps is 32.80 s; the master is retimed with `itsscale 32.81/(984/30)`.
5. The camera path is smooth and periodic. The pose at t=0 matches t=32.81. No cuts.
6. Trees must be realistic CC0 models (Poly Haven fir/pine), not the hub low-poly pack. Bases sit on the terrain. They are logged in `assets/FOUND_ASSETS.md`.
7. Mountains must be the downloaded hub models (Free Standard / BlendKit), not scaled rocks and not a heightmap. Composite a few instances into a range. Never commit the raw hub files.
8. Download hub files with `curl -L 'https://drive.usercontent.google.com/download?id=ID&export=download&confirm=t'`.
9. Cloud punch must be bright white sunlit cumulus, not dark smoke and not a flat fog veil.
10. X-ray must be a readable 3/4 of the whole jet. The 38% / 39% / 32% labels stay inside the frame.
11. The `44%` label stays fully inside the frame, not cropped at the top.
12. Forest must read as a canopy the jet flies over, not one clump and not trees sunk into the ground.
13. The jet must read as an airliner: windows, engines, a generic livery stripe, paint response. No airline name, no tail mark, no registration.
14. Flight altitude must be believable. The city beat is a flyover, not a rooftop scrape.
15. Speedups are allowed only when the picture does not visibly change. The bar used in the bench was SSIM about 0.99. Adaptive sampling at 2 samples failed that bar. 4 samples with adaptive sampling and OpenImageDenoise was kept.
16. Do not render the full 984-frame film on this VM. Final frames go to a Colab bundle. Kristóf renders them on a Tesla T4 with OptiX.
17. The Colab bundle is a packed `scene.blend` saved in Blender 4.2.3 (file header `BLENDER-v402`, not a 4.5 file), `render.py START END`, and `manifest.json` with the edit/overlay block. Cycles GPU, OptiX then CUDA, all non-CPU devices enabled, final samples, 1080×1920, PNG at `//frames/####`. Parts at most 1.9 GB, in `/opt/cursor/artifacts/colab_bundle/plane_seat_preview/`. Two test stills are rendered from that exact unpacked file in 4.2.3.
18. Licensed private assets (BlendKit, Sketchfab Free Standard, hub mountains) may be packed into that bundle and must never be committed to the public repo.
19. Karaoke, pills, grade, SFX, and the retime stay outside Blender. The 3D percent labels are inside the beauty pass.
20. Keep this handoff updated at the end of every future run. Copy it to `/opt/cursor/artifacts/handoff/`.

Rejected attempts, and why:

- Scaling Poly Haven cliff rocks by ~100×. They read as giant rocks, not a range.
- A DEM / heightmap mountain tile, and PTerrain. PTerrain needs a viewport draw handler and does not run headless here.
- The hub low-poly tree pack, Sapling Tree Gen, and Scatter Objects. Kristóf banned the low-poly pack. Scatter Objects is a mouse-stroke modal and cannot run headless. Sapling was not used.
- Easy Clouds density around 2–4. With few volume bounces the puffs went black. Density around 0.05 became a pale fog. The film now uses Principled Volume puffs with a spherical falloff, density about 0.2–0.3 per metre, white scatter, anisotropy about 0.6.
- A full panel-line grid on the fuselage and wings. It read as a wireframe. Rings are now sparse and only on the tube, plus a navy cheatline.
- Extreme Z-scale on `three_peaked` and viewing `bk_snow_cliff` edge-on. Both became floating slabs or paper-thin shards. The range is now `gaea_range.glb` as a continuous terrain, with two summit models seated on it. The terrain footprint covers the camera so the mesh rim is not a cliff in frame.
- Placing a scaled mountain so its bounding box contained the camera. The lens sat inside the mesh.
- `zip -s` multi-volume archives (Info-ZIP 3.0). Reassembly produced a corrupt zip. Use GNU `split` of one ordinary zip, then `cat` to restore.
- Saving the blend with Blender 4.5 for Colab. Colab is 4.2.3 and will not open a newer blend. The bundle is saved with 4.2.3.
- Unused HDRIs without `use_fake_user`. Blender dropped them on save, and the forest sky then tried to load `/tmp/plane_hdri/...` and failed.
- Rendering the 984-frame film on this 4-core CPU. Median about 18 s/frame. Kristóf moved that job to Colab.
- Adaptive sampling capped at 2 samples. It failed the SSIM bar in the earlier bench. Final samples are 4 with adaptive threshold 0.02 and OIDN.
- `bk_peak.glb` (Drive id `1sdNY81fyO7gxzg_pLLsVfItah3-JeXqm`). Downloaded and not placed.

## 3. Architecture, layout, setup, how to render

Repo root is the what-if engine plus episode modules. This episode lives in `whatif/plane_seat/`.

```
whatif/plane_seat/engine/build.py      scene build, pose apply, Cycles job
whatif/plane_seat/engine/flight.py     camera, altitude, biome, label windows
whatif/plane_seat/engine/clock.py      32.81 s clock, words, beats, SFX cues
whatif/plane_seat/engine/overlay.py    karaoke and pills (Pillow, after beauty)
whatif/plane_seat/engine/aircraft.py   colours, TILE=1200, TRAVEL=4800 (older 3-3 jet constants are unused)
whatif/plane_seat/examples/words.json  narrator take, 67 words, duration 32.81
whatif/plane_seat/render_stills.py     eight approval stills → v/plane_tests/
whatif/plane_seat/render_episode.py    beauty + overlay + grade + silent mp4
whatif/engine/segments.py              2–5 s segment planner (shared). Not what Colab runs.
assets/FOUND_ASSETS.md                 CC0 downloads and hub Drive ids
v/plane_tests/                         approval JPEGs
docs/handoff/plane_HANDOFF.md          this file
```

There is no `tests/` package for this episode. Clock checks are whatever you run by importing `plane_seat.engine.clock`.

Versions on this VM:

- Local stills and iteration: Blender 4.5.9 LTS at `/home/ubuntu/apps/blender-4.5.9-linux-x64/blender`
- Colab bundle authoring: Blender 4.2.3 LTS at `/home/ubuntu/apps/blender-4.2.3-linux-x64/blender` (download `https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz`)
- Colab runtime: Blender 4.2.3, Cycles, Tesla T4, OptiX
- Host Python for `render_stills.py` / `render_episode.py`: 3.12. Pillow and numpy are required for overlay and grade. Blender’s own Python is 3.11 and is what runs `build.py`.

From-zero, after the private cache is populated (section 4):

```bash
# stills (beauty + karaoke, no pills, then grade)
python3 whatif/plane_seat/render_stills.py
# one still
python3 whatif/plane_seat/render_stills.py 03_mountains

# a few beauty frames on this machine (not the master)
python3 whatif/plane_seat/render_episode.py --samples 4 --frames 1,61 --beauty-only

# final frames: do not do this for all 984 here
# blender -b scene.blend -P render.py -- START END
```

`render_stills.py` calls Blender 4.5. The Colab file must be saved by 4.2.3. Packing is the script `/tmp/colab_pack/pack_final.py` run as:

```bash
/home/ubuntu/apps/blender-4.2.3-linux-x64/blender --background --python /tmp/colab_pack/pack_final.py
```

That script imports `plane_seat.engine.build.build_scene`, packs images, sets fake users on the three sky HDRIs, saves `/tmp/plane_seat_final_scene.blend`, reopens it, makes paths relative, packs again, and refuses to save if a file-backed image is unpacked or a sky name is missing. It is not in git. If it is gone, follow section 7.

How the three render modes differ:

- Still: `render_stills.py` builds the scene and overrides eye, look, altitude, biome, and which labels show. Then Pillow draws karaoke and the grade. Output JPEG in `v/plane_tests/`.
- Preview on this VM: `render_episode.py --samples 4 --frames N --beauty-only`. Same pose as the film, no overlay.
- Final: Colab runs `render.py` on the packed blend. 4 samples, adaptive threshold 0.02, minimum 2, OIDN, 1080×1920, AgX, look `AgX - High Contrast`, exposure −0.55. Seed is `frame * 997 + 17`. Culling and distant tree LOD are on.

## 4. Assets

Private cache (do not commit):

| What | Path |
| --- | --- |
| BlendKit 405-FLA aircraft | `/opt/cursor/asset-cache/private/extracted/405-FLA/Long-range_passenger_aircraft_405-FLA_90155e42.blend` (blend version 2.93, gzip) |
| Cabin GLB | `/opt/cursor/asset-cache/private/cabin/airplane_cabin.glb` |
| City GLB | `/opt/cursor/asset-cache/private/glb/procedural_city_3.glb` |
| Hub mountains | `/opt/cursor/asset-cache/private/mountains/` |
| CC0 HDRI zip | `/opt/cursor/asset-cache/cc0/assets_cc0_hdri.zip` extracted to `/tmp/plane_hdri/` at build time |

Hub mountain Drive ids (also in `assets/FOUND_ASSETS.md`):

| File | Drive id | Used |
| --- | --- | --- |
| `gaea_range.glb` | `1uTqyJ7dNgY_XItgaJGfNo8Ag9qkPZpxp` | Yes. 2 m terrain, centered. The range. |
| `three_peaked.glb` | `1fe4xozIhUD7EnnDU_y208cvW2Tu0rfoi` | Yes. Corner origin, X 0..1024, Y −1024..0, height 162 m. Left summit. |
| `free_textured_mountain.glb` | `15lv0B3OxAyVi0TooPi_Tz6shbLwDOwch` | Yes. Centered ±1000 m, height 348 m. Right summit. |
| `bk_snow_cliff.glb` | `1OUVpoN_WuisazHEPhI2bpyCCEJawhsY9` | Not in the current range. Edge-on it looked like a shard. |
| `bk_peak.glb` | `1sdNY81fyO7gxzg_pLLsVfItah3-JeXqm` | Fetched, not placed. |
| `lago_disola_4k.hdr` | `1uh4W6lnFidmBcXbCMWMXY_z3u-MNal2k` | Extracted beside the skies. Not the world image. |

Skies actually on the world node, from the CC0 zip: `belfast_sunset_puresky_2k.hdr` (city, and the file’s default), `kloofendal_48d_partly_cloudy_puresky_2k.hdr` (forest, cloudsea), `goegap_2k.hdr` (desert). Mountains and ocean also use Belfast. All three are packed with fake users.

CC0 in git under `assets/found/`: Kenney SFX, OpenGameArt ticks and flares, Poly Haven ground textures, Poly Haven trees in `assets/found/trees/realistic/` (`fir_sapling_medium` and `pine_sapling_medium`, decimated). Font for labels and karaoke: `whatif/scale_journey/assets/fonts/Anton-Regular.ttf`.

Low-poly tree pack path still exists at `/opt/cursor/asset-cache/private/glb/low_poly_tree_pack.glb` and is not used.

## 5. Episode spec

Id `plane_seat`. Title “The back of the plane had the best odds.” Status: beauty bundle ready for Colab. No graded master video yet.

Clock: `FPS=30`, `DURATION=32.81`, `FRAME_COUNT=984`, `WIDTH=1080`, `HEIGHT=1920`. `frame_time(n) = (n-1) * 32.81 / 984`.

Narrator: `examples/words.json`, take note says Brian, Eleven v4, single take, cut after “data,”. 67 words. Duration field is 32.81.

Beats (`clock._shot_beats`):

| Id | Start (s) | Line |
| --- | --- | --- |
| s1_city | 0 | The back of the plane had the best odds. |
| s2_front | word 9, t=2.84 | Not the front. |
| s3_forest | 4.08 | Time dug through FAA records… |
| s4_mountains | 10.02 | Front third 38, middle 39, back 32. |
| s5_ocean | 18.05 | Aisle seats mid-cabin, 44%. |
| s6_desert | 24.38 | Middle seats in the back, 28%. |
| s7_loop | 28.55 | Small sample… Time's data. |
| end | 32.81 | |

Biome under the jet (`flight.biome_at`): city to 4.08, forest to 10.02, mountains to 18.05, ocean to 24.38, desert to 28.55, cloudsea to 31.85, city again. Swaps sit on cloud peaks.

Altitude (metres) in `flight.ALT_KEYS`: city and the loop about 1600–1680, cloud punch about 1900, forest about 700–760, mountains about 2600–2700 (above the range), ocean and desert about 1620–1700. City roofs are about 200 m, so this is a high approach, not a rooftop pass. Nothing descends into the city. The camera is a periodic centripetal spline. Nose is +X. Eyes stay on the rear 3/4, above the wing. The 44% and 28% beats look down the open roof. `pose["interior"]` is false for the whole film. The snow under the chase is subdivided once; the far Gaea chunks are not.

X-ray is on from about 10.9 s to 18.0 s (the 38 / 39 / 32 line), not the whole flight. The roof opens from about 19.2 s to 28.5 s for the 44% and 28% beats. `44%` shows around word 44 (t=22.81). `28%` around word 54 (t=27.27). Cards billboard to the camera’s up axis.

Seat map in the picture (not the unused constants in `aircraft.py`): 36 rows, pitch 0.80 m, 3-4-3, 360 seats, instanced from one cabin seat. Front 12 amber, mid 12 amber, back 12 green. Aisle seats in the middle third go red on the 44% line. Middle seats in the back go bright green on the 28% line.

3D labels, parented to the aircraft, billboarded at the camera: `l38` / `l39` / `l32` at size 3.6 beside the tube; `l44` size 0.62 and `l28` size 0.78 in the aisle.

Preview stills from the film clock, in the bundle (beauty only, no karaoke):

| File | Frame | t |
| --- | --- | --- |
| `stills/start.png` | 1 | 0 |
| `stills/city.png` | 61 | 2.00 s |
| `stills/mountains.png` | 316 | 10.50 s (range is up, 38% x-ray has not peaked) |
| `stills/end.png` | 984 | 32.78 s |

Output URL for the master does not exist yet. After Colab, the intended local path is `v/plane_seat_silent.mp4` via `render_episode.py` once beauty PNGs are present. Raw GitHub link: none, because the mp4 was not encoded.

Open feedback that this pass answered: photoreal-enough airliner (cheatline, windows, engines, clearcoat), bright cumulus, a downloaded range instead of floating cliffs, trees on the terrain, higher city altitude, city flyover, large zone labels, cinematic chase. Still soft: the jet paint is smooth at a distance; the gaea mesh is coarse if the lens gets close to a ridge; the city ground outside the instanced blocks is a flat photo plane.

## 6. QC

Clock:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "whatif")
from plane_seat.engine.clock import DURATION, FRAME_COUNT, FPS, frame_time, load_words
assert abs(DURATION - 32.81) < 1e-9
assert FRAME_COUNT == 984 and FPS == 30
assert abs(frame_time(1)) < 1e-12
assert abs(frame_time(984) - 32.81 * 983 / 984) < 1e-9
words = load_words()
assert abs(words[-1]["t1"] - 32.81) < 0.05 or words[-1]["t1"] <= 32.81
print("clock ok", len(words))
PY
```

Pose seam: `pose_at(0)` and `pose_at(32.81)` must match eye, altitude, biome. `hidden_swap` is true on the cloud peaks so a ground change is covered.

Bundle:

```bash
cd /opt/cursor/artifacts/colab_bundle/plane_seat
cat plane_seat.zip.* > /tmp/plane_seat_full.zip
rm -rf /tmp/colab_verify && mkdir /tmp/colab_verify
unzip -q /tmp/plane_seat_full.zip -d /tmp/colab_verify
# hide extracted skies so a missing pack fails loudly
mv /tmp/plane_hdri /tmp/plane_hdri_aside 2>/dev/null || true
cd /tmp/colab_verify
/home/ubuntu/apps/blender-4.2.3-linux-x64/blender -b scene.blend -P render.py -- 1 1
/home/ubuntu/apps/blender-4.2.3-linux-x64/blender -b scene.blend -P render.py -- 316 316
mv /tmp/plane_hdri_aside /tmp/plane_hdri 2>/dev/null || true
```

Pass: both PNGs exist, 1080×1920, no `Cannot read` for an HDRI, `bound seats 360`, and the shots are city (frame 1) and snow (frame 316). This run’s frames are the files in `stills/`. Mean absolute pixel difference between those four frames is tens of levels, so they are not copies of one image.

SSIM, when comparing a speedup to a baseline, used a Gaussian-window RGB mean. Threshold that was treated as pass: about 0.99. 2-sample adaptive failed it. Do not drop below 4 samples to chase speed.

Artifact volume: a single file over 100 MiB fails on close with `Errno 22`. Parts must stay ≤ 100 MiB here even though Kristóf’s cap is 1.9 GB. 90 MiB (`94371840` bytes) is the split size that worked.

## 7. Render workflow

Segmented rendering (`whatif/engine/segments.py`) cuts a film into 2–5 s chunks with 1–2 handle frames. `render_episode.py` can write `segments.json`. That planner is for a local cache. Colab does not use it. Kristóf renders contiguous ranges with `render.py`.

Colab bundle contents after `cat` and `unzip`:

- `scene.blend` — zstd-compressed file, header `BLENDER-v402`, 250,231,977 bytes, in `/opt/cursor/artifacts/colab_bundle/plane_seat_preview/`. Written by Blender 4.2.3, not 4.5. Opening it in 4.2.3 keeps the camera: lens 28 mm, vertical sensor 24 mm, clip 0.05–50000, depth of field on, 1080×1920, AgX high contrast, exposure −0.55, samples 4. A 4.5 save was rejected on the penny bundle because 4.2.3 dropped data such as lens. All file images are packed. Sky HDRIs have fake users so they survive save. Paths were remade relative. No Alembic. The ocean is a live Ocean modifier. Clouds are Principled Volume cubes, not an add-on. Easy Clouds is not required. `stills/frame_0001.png` and `stills/frame_0061.png` were rendered from this exact unpacked blend with Blender 4.2.3.
- `render.py` — `blender -b scene.blend -P render.py -- START END`. OptiX, then CUDA, every non-CPU device enabled, else CPU. Writes `//frames/####.png`. Vendored pose code is `py/plane_seat/` inside the zip. Nothing outside the bundle is required.
- `manifest.json` — fps 30, frames 1–984, samples 4, adaptive 0.02, min samples 2, OIDN, resolution 1080×1920, `est_seconds_per_frame_on_your_cpu` 18 (median 17.5 s, mean 18.2 s, range 14.8–24.7 s on 530 frames of the previous altitude on this 4-core VM). Overlay notes: karaoke x 90–900 y 1120–1420, pills y 300–1050, then teal/orange grade and grain, silent H.264, then itsscale. 3D labels are already in the beauty frames. SFX are outside Blender.

Zip on disk:

| File | Bytes |
| --- | --- |
| `plane_seat_preview.zip.00` | 94,371,840 |
| `plane_seat_preview.zip.01` | 94,371,840 |
| `plane_seat_preview.zip.02` | 58,591,646 |
| Reassembled zip | 247,335,326 |

```bash
cat plane_seat_preview.zip.* > plane_seat_preview_full.zip
unzip plane_seat_preview_full.zip
blender -b scene.blend -P render.py -- 1 120
```

Suggested Colab chunks are about 2 minutes of frames (120 frames) so a failed chunk is small. A T4 OptiX benchmark on an earlier frame was about 95 s versus 655 s on an 8-core CPU (about 7×, and about 14× versus this VM’s ~18 s if you scale cores the way Kristóf did). Re-time the first chunk; the mountain and cloud frames cost more.

Rebuild the zip after any scene edit:

1. Edit `build.py` / `flight.py` on this branch.
2. Copy those files into `/tmp/plane_bundle_final/py/plane_seat/engine/`.
3. Run `pack_final.py` under Blender 4.2.3.
4. `zip` then `split -b 94371840`.
5. Copy parts to `/opt/cursor/artifacts/colab_bundle/plane_seat/`.
6. Unpack elsewhere, hide `/tmp/plane_hdri`, render two frames.

Do not commit `scene.blend` or the zip.

## 8. Known bugs and next steps

Priority order:

1. Frames 1–492 are already rendered from the 4.2.3 bundle and zipped in `/opt/cursor/artifacts/plane_frames_1_492/`. Reassemble a split chunk with `cat frames_AAAA_BBBB.zip.* > frames_AAAA_BBBB.zip`. Kristóf renders 493–984. Do not mix in `/tmp/plane_seat_cache/beauty/` from the older 4.5 CPU run.
2. Bring the PNGs back and run overlay, grade, silent encode, and itsscale. Target file `v/plane_seat_silent.mp4`. Then a raw link if it is committed. GitHub rejects files over 100 MB; check the mp4 size first.
3. The gaea mesh is coarse up close. If a Colab contact sheet shows faceted ridges, swap in a denser source or ease the camera off the slope. Do not go back to scaled cliff rocks.
4. City blocks do not cover the whole ground tile. The photo plane shows at the edge of the flyover. More city instances, or a tighter lens, if Kristóf flags it.
5. Jet paint is still smooth in a wide shot. Do not put a dense panel grid back on the wings.
6. `bk_snow_cliff` and `bk_peak` are unused. Only add them if a still shows a face, not an edge.
7. Update this handoff at the end of the next run, including the Colab frame time and the mp4 path.

## 9. Branches and PRs

Current, use this:

- Branch `cursor/plane-seat-final-film-4316` at the commit that contains this file. Draft PR 25 against `cursor/plane-seat-silent-4316`: https://github.com/dagadt675-oss/juicytea-media/pull/25

Stale for this episode, do not continue them:

- `cursor/plane-seat-preview-bundle-4316`, PR 20. Earlier packed preview (64 samples, Blender 4.5 scene, floating-rock mountains). Superseded by PR 25 and the 4.2.3 bundle.
- `cursor/plane-seat-silent-4316`, PR 14. First shaded stills. Missing the later cloud, forest, label, altitude, and range fixes.

Other open PRs in the repo (Greenland, penny, globe, roads) are different episodes. Do not mix them into this branch. `main` is behind this work. Base for this episode’s PR is `cursor/plane-seat-silent-4316`, whose base is `cursor/scale-journey-module-d7c6`.
