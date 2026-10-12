# Map Shorts handoff

Last updated: 2026-10-12.

This file is the only briefing a new agent gets, plus the git repo. Read it before editing. Update it at the end of every future run that changes the picture, the rules, the branches, or the next step, then commit it on the branch you are actually working on and copy it to `/opt/cursor/artifacts/handoff/map_HANDOFF.md`.

Picture this document describes: `greenland_africa_v14.mp4` on `cursor/greenland-africa-v14-7e9d`. v13 is the parent (`1363605` on `cursor/greenland-africa-v13-7e9d`, PR #29).

## Where the code actually is

Two checkouts exist on this machine. They are not the same branch.

| Path | Branch at the time of this handoff | What it is |
| --- | --- | --- |
| `/tmp/vfx-smooth` | `cursor/greenland-africa-v14-7e9d` | The live map engine. Greenland v5 through v14 live here. Edit this tree, or a fresh checkout of this branch. |
| `/workspace` | `cursor/greenland-vo-retime-7e9d` at `7ec07b0` | The rejected retime. Do not edit it thinking it is current. |

Before every edit, run `git -C <dir> branch --show-current`. If you are not on `cursor/greenland-africa-v14-7e9d` or a new branch cut from it, you are in the wrong tree.

Repo: `dagadt675-oss/juicytea-media`. New branches must match `cursor/<descriptive-name>-7e9d`, all lowercase. Open and update pull requests with the Cursor `ManagePullRequest` tool. Do not use `gh` to create or edit a PR. `gh` is read-only. `pipeline/.gitignore` ignores `*.mp4`; force-add a delivery with `git add -f`. GitHub rejects files over 100.00 MB (decimal). Warn above 50 MB. Do not commit `pipeline/examples/market/market_proof.txt`. Do not commit the hypso zip, the hypso tif, Blue Marble `.npy`, the Natural Earth shapefile, or anything under `pipeline/data/cache/`.

Do not start a new episode, a Märket rebuild, or another Greenland render until Kristóf reviews v14. v14 keeps v13's clock. It passed the no-cut gate, the 5× whole-frame spike rule, the loop-seam check, the local-pop gate, and the ghost-coast gate. He has not approved it.

---

## 1. Mission and current state

Juicy Tea map Shorts. Vertical 1080×1920 pictures of unbelievable geography, built from ready-made public-domain or CC0 imagery, timed to a recorded voice. The look Kristóf calls perfect is the GeoGlobeTales colourful satellite globe and flat maps. A dark single-accent focus mode is optional per beat. It is not the default.

The active job is **Greenland vs Africa**, silent picture, timed to Kristóf's Brian voiceover (52.428 s). The delivered file waiting on his review is `pipeline/examples/greenland/greenland_africa_v14.mp4`.

### Greenland versions

| Version | File | What it is | Status |
| --- | --- | --- | --- |
| Approved look, pre-VO-swap | `greenland_africa_polished.mp4` | 1080×1920, 30 fps, 45.233 s, 1357 frames, 51,812,755 bytes. Video commit `36d7650`. Camera code for the liked drag is `f87476c` (`polished_v2` is that camera; the v2 file is 47,389,410 bytes, same 45.233 s). | Do not overwrite. This is the picture he liked before the 52.43 s voice replaced the old clock. |
| First picture on the 52.43 s read | `greenland_africa.mp4` | 30 fps, 52.433 s, 1573 frames, 67,384,229 bytes. Commit `37b12c0`. | Superseded. |
| v4 retime | On branch `cursor/greenland-vo-retime-7e9d`, PR #15. The stretch lives in `/workspace/pipeline/jt/show/greenland.py` as `_glide_keys`. | Rejected twice. First: snaps, fidget, blur, stacked text from chasing a structural-motion score. Second, verbatim: "still not right, the whole thing feels unnatural." Cause: every move was stretched across 52 s, so the easing became a slow drift. A follow-up called retime2 was started and then cancelled. Do not implement retime2. Do not call `_glide_keys`. |
| v5 | `greenland_africa_v5.mp4` | Rebuilt from scratch in the current engine against `words.json`. 60 fps, 3146 frames, 52.433 s, 46,873,318 bytes. Commit `2721d6c` on `cursor/greenland-africa-v5-7e9d`, PR #17. | Rejected as lame. Discrete moves, projection cuts, and dead holds. Do not extend this camera. |
| v6 | `greenland_africa_v6.mp4` | One continuous Catmull-Rom camera. 60 fps, 3146 frames, 92,584,857 bytes after a veryslow CRF 16 encode (the first veryfast encode was 102,200,383 bytes and would be rejected by GitHub; a medium CRF 16 re-encode grew to about 105 MB). Commit `6130e7a`, PR #18. Gate passed: max diff 15.041, 0 spikes, 0 dead holds. | Blocked by Kristóf's frame review. Four visual bugs, listed in section 2. The v7 splice copies the untouched keyframe spans from this file, so keep the file. |
| v7 | `greenland_africa_v7.mp4` | Same moves and timing as v6. Only the broken stretches were re-rendered. 60 fps, 3146 frames, 97,747,960 bytes. Commit `0cc786a`, PR #19. Gate: frames 3146, max diff 8.671, spikes 0, dead 0, pass. | The four visual bugs are gone. He then blocked it on a double exposure at 6.8–7.7 s. Keep the file; v8 copies every span except that zoom. |
| v8 | `greenland_africa_v8.mp4` | v7 with frames 397–483 re-rendered as one projection. 60 fps, 3146 frames, 52.433 s, 95,523,515 bytes. No-cut gate: max diff 13.236, spikes 0, dead 0, pass. | He verified 5.2–7.7 s. The way into the globe (3.5–4.8 s) was still the old crossfade. Keep the file; v9 copies every span except that one. |
| v9 | `greenland_africa_v9.mp4` | v8 with frames 211–284 re-rendered as the same one-geometry morph. 60 fps, 3146 frames, 52.433 s, 91,923,357 bytes. No-cut gate: max diff 13.188, spikes 0, dead 0, pass. Ghost-coast gate: 223 samples, 0 fails. | He verified no cuts and no ghosts. The mid-morph outline was still an irregular blob. Keep the file; v10 copies every span except the two projection morphs. |
| v10 | `greenland_africa_v10.mp4` | v9 with frames 211–284 and 397–483 clipped to a convex outline. 60 fps, 3146 frames, 52.433 s, 89,788,561 bytes. No-cut gate: max diff 13.238, spikes 0, dead 0, pass. Ghost-coast gate: 223 samples, 0 fails. | He accepted the morph outline. The fourteen copies still vanished at about 31 s, and the loop popped. Keep the file; v11 copies every span except those fixes. |
| v11 | `greenland_africa_v11.mp4` | v10 with the fourteen copies shrinking out over 0.64 s and the last half-second joined to frame 0. 60 fps, 3146 frames, 52.433 s, 87,815,180 bytes. Whole-frame gate passed and hid the local pops below. | Superseded. Kristóf scored the smoothness 2/10. Keep the file; v12 copies every span except the fixes. |
| v12 | `greenland_africa_v12.mp4` | v11 with the eight review items fixed. 60 fps, 3146 frames, 52.433 s, 83,281,871 bytes. Gates passed, but frame 1680 snapped the framing and the shrink finished before the voice. | Superseded. Keep the file; v13 copies every span except the retimed ones. |
| v13 | `greenland_africa_v13.mp4` | Shrink timed to the three spoken words, 28 s splice closed, 40–44 s push. 60 fps, 3146 frames, 52.433 s, 82,359,454 bytes. Passed cuts and smoothness. | Superseded. Picture-only notes remained. Keep the file; v14 copies every span except those notes. |
| v14 | `greenland_africa_v14.mp4` | Same clock as v13. No ~9× AREA pill. Label entrances scale and fade over 7 frames. The flat-to-globe morph stays full-bleed until it is a globe. Excuse gag contrast is 12.5% higher from 5.6–6.6 s. 60 fps, 3146 frames, 52.433 s, 80,295,556 bytes. Whole-frame gate: max diff 9.824, spikes 0, dead 0, pass. Loop seam 2.328 against a neighbour median of 0.530, pass. Local pops 0. Ghost-coast gate: 294 samples, 0 fails. | **Current delivery. Waiting on Kristóf.** |

Raw v14:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v14-7e9d/pipeline/examples/greenland/greenland_africa_v14.mp4

Raw v10:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v10-7e9d/pipeline/examples/greenland/greenland_africa_v10.mp4

Raw v9:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v9-7e9d/pipeline/examples/greenland/greenland_africa_v9.mp4

Raw v8:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v8-7e9d/pipeline/examples/greenland/greenland_africa_v8.mp4

Raw v7:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v7-7e9d/pipeline/examples/greenland/greenland_africa_v7.mp4

Raw v6:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v6-7e9d/pipeline/examples/greenland/greenland_africa_v6.mp4

Raw v5:

https://raw.githubusercontent.com/dagadt675-oss/juicytea-media/cursor/greenland-africa-v5-7e9d/pipeline/examples/greenland/greenland_africa_v5.mp4

Eight v5 stills are in `pipeline/examples/greenland/stills_v5/` (`00_lie` through `07_still_bigger`). They were rendered before the v6 spline. v6 and v7 did not regenerate stills. Do not treat those PNGs as the v7 camera.

`pipeline/examples/greenland/beats_v5.md` and the `MOVES` list in `greenland_v5.py` describe the old discrete moves. The live camera is `_anchors()` plus the Catmull-Rom spline. The module docstring at the top of `greenland_v5.py` is also stale: it still says holds fill the voiceover and nothing drifts. That sentence is the v5 rule. v6/v7 replaced it with continuous drift.

### Other episodes

| Episode | Where | Status |
| --- | --- | --- |
| Märket proof | `pipeline/examples/market/` (`market.json`, `render_proof.py`, `geoglobe.py`). 22 s, 30 fps, id `market_proof`. | Not the current task. Close-up is Poly Haven `aerial_rocks_02` (CC0), not a real Märket orthophoto. The lighthouse is still a small icon. Swedish Lantmäteriet WMS is the intended ortho source (layer 401 was the one under discussion). Do not use Finnish NLS ortokuva (CC BY 4.0). `market_proof.txt` is untracked; do not commit it. |
| Countries cut in two | Nowhere in this repo. | No spec, no script, no branch. Do not invent one. |
| List / trivia format | Nowhere in this repo. | No spec. The old YAML pipeline is one sentence per beat, not a list show. |
| LA–Tokyo | `pipeline/examples/lax_tokyo/`, `pipeline/specs/lax_tokyo.yaml`, PR #4. | Silent 24.2 s, 30 fps, no burned karaoke. Sentence starts 0.03, 3.93, 7.24, 8.14, 10.81, 14.28, 20.25, 23.05. The spoken lines say the flight curves toward Alaska and that the shortest path is a great circle that bends north. They do not say the flight flies over Alaska. |
| Gold Canada / Rome | `pipeline/examples/canada_rome/`, `pipeline/style/gold_canada.md`, PR #3. | Silent. Scored 7.5/10 against the gold reference. Karaoke is absent on purpose. |
| Model-drop bridges | `pipeline/examples/model_drop/`, PR #13. | Temburong and Pelješac. Camera grammar in `moves.py`. Flight curve is the van Wijk port in `flyto.py` (d3-interpolate zoom.js, ISC). These shots use zoom blur. Greenland must not. |
| Neum zoom proof | `pipeline/examples/neum_zoom/`, PR #12. | 5 s proof that public-domain imagery can reach about 15–30 m. The proposal in that folder is stricter about Sentinel than the later Greenland log. See section 4. |
| Alaska | `pipeline/specs/alaska.yaml` | Renderer test only. Not a shippable episode. |
| Old seven topics | Hans Island, London, France, Diomede, Ceuta/Melilla, Congo | Explicitly not specs. `pipeline/README.md` and `pipeline/jt/review.py`. |
| Football Earth v5 | PR #2, branch `cursor/football-earth-v5-6cd0` | A different product line. Not this camera. |
| What-if humans, scale journey, plane seat, penny, skyline | PRs #5, #6, #8, #9, #10, #11, #14 | Other product lines. Not the map-Shorts camera. |

What was in progress when this handoff was written: v11 had just been spliced, the no-cut gate, the loop-seam check, and the ghost gate passed, and the file was committed. The next action is Kristóf's review of `greenland_africa_v11.mp4`. Do not start another episode.

---

## 2. Kristóf's rules

Numbered so a later run can cite them. When two rules conflict, the later Greenland rule wins for new map pictures, and the conflict is written here instead of being silently resolved.

1. **GeoGlobeTales is the benchmark.** Colourful satellite globe and colourful flat maps. Dark single-accent focus is optional per beat, not the house style.
2. **There is never a cut.** The whole video is one continuous camera move: zooms, pans, morphs, and elements animating in and out. No hard cuts, no instant plate swaps, no instant appear or disappear of a whole scene. This rule started with the v6 brief and applies to every map Short after v5.
3. **One continuous move, not a playlist of shots.** Moves are about 0.5–2 s and ease into each other with overlapping eases. v5's "move, then dead hold" rhythm was rejected.
4. **Smooth eased motion.** Long gentle ease-in-out. No snaps, no camera shake, no spring jolts, no idle fidget, no linear moves. Icon entrance overshoot (0 to about 110–120 percent, then back to 100 percent, over 15–20 frames at the 30 fps motion clock) is allowed for icons. It is not allowed for the camera.
5. **Holds are a slow drift.** About 1–3 percent of scale per second. A hold is not a freeze. The v5 rule "still holds fill the VO, never slow drift" is retired for new episodes.
6. **Something moves at least every 1.5 s.** A label, a ticking number, a border pulse, a blink, or a talk cycle. This is not camera shake.
7. **No blobs, no black circles, no shadow ovals.** No drop-shadow ellipses and no blob or texture layers on the map. `draw_clouds` in `vfx_core.py` still exists. Greenland must not call it. The hand SVG stays; the dark circle behind the hand was removed in v7.
8. **No camera shake.** Structural-motion score ≥ 3.7 was retired for Greenland. Do not add jolts to pass it.
9. **Do not stretch keyframes when re-timing.** Moves keep their approved durations. Extra voice used to be filled with still holds. For any new episode, rule 5 replaces the still hold: extra time is drift, not a stretched ease and not a freeze. The rejected v4 retime stretched every move across 52 s via `_glide_keys`. That is the failure mode to avoid.
10. **Seamless loop.** The last half-second lands on the opening camera. Renderer frame 0 equals the last frame before encode. yuv420 makes a small decoded difference (v6 thumbnail loop mean abs was about 1.54). `check_moves()` asserts the spline endpoints match.
11. **60 fps for Greenland v5 and later.** 1080×1920. Older pipeline default is 30 fps (`make_short.py`, LA–Tokyo, gold kit, Märket). Moves are timed in seconds. `MOTION_FPS = 30` so `icon_pop(age * 30, 18)` stays 0.6 s at 60 fps output. Hand parallax uses `camera_at(t - 1/30)`.
12. **Pixel-identical speedups only.** Max abs channel diff ≤ 1 (on the 0–255 scale) against the same frames without that speedup. A failure stays off. Report speedup, frames tested, max pixel diff, and time saved. The five switches are in section 7. v6 and v7 left duplicate-frame and layer-cache **off** even though the proof passed, because continuous motion must not be frozen by a stale hash.
13. **Ready-made assets, in this order.** (1) Asset hub or `asset_library/`. (2) Web search for CC0, public domain, or OFL fonts, commercial use, no attribution. Download into `asset_library/` and log license plus source. (3) Build it yourself only when neither exists, and say what you checked and why it failed. No hand-drawn props. No on-screen attribution. No OSM.
14. **License lines that already bit us.** Public-domain Landsat, NASA, and Natural Earth are fine. Copernicus Sentinel and EOX s2cloudless are CC BY 4.0: credit in `assets/FOUND_ASSETS.md` only, not burned on screen. The older Neum proposal (`pipeline/examples/neum_zoom/PROPOSAL.md`) says Sentinel must not be used in a public picture at all. Greenland logged the EOX mosaic and then stopped painting it, because the cached tile is a Scandinavia patch and caused dark pops. Prefer public domain for a new episode. Flaticon, Freepik, Noun Project free tiers, Twemoji, and OpenMoji need attribution: skip them. Finnish NLS ortokuva is CC BY 4.0: do not use it. Private Sketchfab and BlendKit files are for rendered video only and are never committed.
15. **Voice first, then the picture.** Brian (ElevenLabs v4) is the authority. Record the voice, then time the picture to `words.json`. Do not publish espeak. espeak-ng is a stand-in so the old YAML pipeline can be checked.
16. **Gag lines are separate takes.** `words.json` lists `excuse` `1b89c71e.mp3`, `waitwhat` `d600a861.mp3`, and `hitiny` `70eabdeb.mp3`, speakers `greenland` and `algeria`. Kristóf's rule is that these are pitched-up character voices, not Brian. The JSON does not say "pitched." The mp3 bytes are not in the git tree. Do not re-voice them with Brian.
17. **Karaoke colour is unresolved.** The gold kit and the YAML pipeline stress the spoken word in yellow: `pipeline/style/gold.py` uses `(254, 212, 10)` `#FED40A`; `pipeline/README.md` says `(255, 214, 10)`. A later note from Kristóf says the karaoke word is cyan. Greenland v5, v6, and v7 do not burn karaoke. Captions are composited later. Leave y about 0.64–0.72 (1150–1450) empty. Do not pick cyan or yellow until he says which applies to a burned line.
18. **Type and safe zone, when text is burned.** Glyphs at least 64 px. Nothing important in the top 12 percent, the bottom 20 percent, or past x = 900. Working safe zone used on Greenland labels: x about 80–1000, y between 12 percent and 80 percent of 1920, and out of the caption band. Labels are drawn last, above shapes. One label must not cover another. HI TINY sits to the right of Algeria and the face stays inside the frame. STILL BIGGER sits at the top, not on the USA chip.
19. **Sharp encode.** CRF 16 on Greenland deliveries (`libx264`, `yuv420p`, profile high, level 5.1). The old `make_short.py --preset final` is CRF 17. No `tmix`, no depth of field, no motion blur on Greenland. Kristóf rejected blurry renders. The grade is contrast, saturation, and vignette without dither (`_sharp_grade`), so holds and the loop are deterministic. Barrel distortion, if used elsewhere, scales x by half-width and y by half-height. Normalising both axes by half-width smeared 9:16 frames. Greenland sets barrel off.
20. **Story numbers are the spoken ones.** Counter is `16.0×` down to `1.0×` because the line is SIXTEEN. Format is always `f"{mult:.1f}×"` so it does not jump from `16×` to `16.0×` at the word "drag" (17.718 s). Fourteen is the tile count, not the counter. Areas: Africa 30.37e6 km², Greenland 2.166e6, Algeria 2.381741e6, DR Congo 2.344858e6, USA 9.833517e6, China 9.596960e6, India 3.287263e6, Europe (outside Russia) 6.2e6. Home pin: lat 74.319387, lon −39.335251. Sticker destination (lon 17, lat 6). Comparison chip (22, 21). `display_multiplier(..., home_label=16)`.
21. **Fills follow the real coastline.** Never close a chopped globe limb into a chord. Never clip a polygon to the frame and then close it. The v6 ruler-cut across northern Greenland and the vertical cut on West Africa came from that.
22. **Segment the render.** Do not keep every raw frame. One 1080×1920 frame is about 6.2 MB; 3146 of them are about 19 GB. Encode spans to mp4, then concat on keyframes.
23. **Git and review hygiene.** Draft PRs. Do not overwrite polished or v2. Do not commit caches, shapefiles, or private blends. Update this handoff before you finish.

### Rejected attempts, and why

- **v4 retime / `_glide_keys`.** Stretched the approved move durations to fill 52 s. Felt unnatural. retime2 was cancelled before it was committed.
- **Chasing structural motion ≥ 3.7** on the retime. Produced snaps, fidget, blur, and stacked text.
- **v5 discrete camera.** Projection cuts (flat to globe at 3.75 s, plate pops, a zoom step, a light-to-dark plate swap) and dead holds (about 22.1–25.5 s and 13.1–15.3 s). Kristóf: lame, and getting worse. Measured spikes he quoted: 3.75 s diff 53.7 vs neighbour 0.2; 4.65–5.43 s peak 23.8; 6.90 s zoom step 77.6; 7.25 s plate swap 90.8; 31.90 s scene swap 12.6; 46.65 s the four countries vanish 14.7; 17.73 s the `16×` to `16.0×` glyph jump.
- **Sentinel local plate on Greenland.** `sentinel_local.jpg` is southern Scandinavia (west 14.06, south 57.33, east 22.50, north 61.61). Compositing it on Greenland caused dark pops. `_graded()` crossfades regional hypso and Blue Marble only.
- **`paint_named` boolean-testing a numpy plate** (`plates.get(name) or plates["globe"]`). A numpy array cannot be used as a boolean. Check `None` explicitly.
- **Closing a partial orthographic ring.** Produced the white-ice-above-a-ruler-edge bug at about 7.0–8.2 s, and a straight vertical edge on the Africa fill.
- **Clipping Africa's bbox to the frame.** Tiles jumped when the south coast crossed y = 1920 (frame 1884, t = 31.40, thumbnail mean diff about 8.59, full-frame mean about 11.6).
- **`draw_clouds` on wide spans.** Dark translucent ovals over the Atlantic from about 46.6–51.3 s, worst near 49.5 s left of Africa and near Iceland.
- **Home Greenland turning red only after `HUGE` finished** (about 51.27 s). From 47–50 s the real island was a pure-white ice hole.
- **Full equator dashed line and a full-journey polyline.** Thin white guide lines at about 18.5 s and 22 s.
- **Dark circle behind the Kenney hand.** Banned shadow ellipse.
- **Upscaling `red_hand_point.png` (68×72).** Use the Kenney SVG.
- **`tmix`, DoF, motion blur, CRF above 16** on a Greenland delivery.
- **Frame duplication and basemap cache on the v6/v7 full render.** Pixel-identical on a short test with real holds, but they freeze a frame when the state hash misses a blink or a drift. Forced off for the continuous picture.
- **First v7 splice.** Gate failed at frame 250 (t = 4.167, diff 12.749, an old-v6 / new-render join), frame 285 (t = 4.75, diff 16.563), and frame 397 (t = 6.617, diff 72.416, a one-frame switch when globe blend crossed 0.996 and the fill flipped from ortho paths to mercator paths). Fixed by crossfading both coast-correct layers and re-rendering frames 0–500. That crossfade is what v8 then removed.
- **v7 projection crossfade (the double exposure).** From about 6.6 s to 8.1 s the renderer drew the Mercator plate and the orthographic plate at the same time, with complementary alpha, and did the same for every fill. Kristóf: a small Greenland and a big pink Greenland, two coastlines, two Africas, two Icelands. It reads as a dissolve, which is a disguised cut. Do not crossfade two framings. LoD may crossfade only textures that share one geometry.
- **Veryfast CRF 16 of the full v6 film** at 102.2 MB. GitHub's hard limit is 100.00 MB. Medium CRF 16 from that file got bigger. Veryslow CRF 16 from the mp4 landed at 92,584,857 bytes and still passed the gate.
- **Multiprocessing spawn from `python3 - <<'PY'`.** `FileNotFoundError` on `<stdin>`. Workers need a real `.py` file.
- **A false gate spike** from concatenating two non-contiguous frame ranges in one diff loop (diff 148 at t = 6.400 was t = 4.98 compared with t = 6.40). Reset the previous frame between runs.

---

## 3. Architecture, layout, setup, how to render

### Stack (versions on this machine, 2026-10-11)

- Python 3.12.3
- FFmpeg 6.1.1 (`ffmpeg version 6.1.1-3ubuntu5`)
- numpy 2.5.3
- Pillow 12.3.0
- skia-python 144.0.post2 (SVG DOM; alpha fades use `canvas.saveLayer(None, paint)`, not `canvas.saveLayer(paint)`)
- scipy 1.18.1 (`map_coordinates` for the projection curl)
- pyshp 3.1.6 (geopandas is not installed; do not block on it)
- PyYAML 6.0.1
- soundfile 0.14.0
- `nproc` on this VM is 4

`pipeline/requirements.txt` is unpinned: `numpy`, `scipy`, `PyYAML`, `soundfile`, `pyshp`, `pillow`, `skia-python`.

### Setup from zero

```bash
git clone <repo> juicytea-media
cd juicytea-media
git fetch origin cursor/greenland-africa-v7-7e9d
git checkout cursor/greenland-africa-v7-7e9d

python3 -m pip install --break-system-packages -r pipeline/requirements.txt
cd pipeline && python3 setup_data.py
```

`setup_data.py` calls `ensure_shapefile()` and `build_earth()`. The Natural Earth 50m admin-0 shapefile lands under `pipeline/data/ne/` and the baked cache under `pipeline/data/cache/`. Both are gitignored.

Then fetch the asset hub (section 4) and make sure the Blue Marble JPEG exists at one of the two paths in `basemap.py`, or that `pipeline/data/cache/bmng_jul_10800.npy` already exists (167 MB on this machine).

Old YAML pipeline, not used for Greenland v5+:

```bash
python3 pipeline/selftest.py
python3 pipeline/make_short.py pipeline/specs/alaska.yaml --preset preview --out pipeline/out/alaska
```

`--preset final` is 1080×1920 CRF 17. `--preset preview` is 540×960. That path burns nothing on `engine: silent` and leaves y 0.64–0.72 empty.

### Repo layout that matters

```
ASSET_HUB.md                  hub fetch commands and the standing asset rule
assets/FOUND_ASSETS.md        append-only web-asset log
assets/found/                 copies under 50 MB (hypso JPEG, sentinel preview, GIBS, Landsat windows, SRTM, code)
pipeline/requirements.txt
pipeline/setup_data.py
pipeline/make_short.py        old YAML renderer
pipeline/jt/show/greenland_v5.py   THE current episode (name is historical)
pipeline/jt/show/greenland.py      old episode and shared constants; do not extend its camera
pipeline/jt/show/fast_render.py    workers, raster cache, RGBA pipe
pipeline/jt/show/basemap.py        Blue Marble and plate paint
pipeline/jt/show/lod.py            globe / regional / local. Greenland does not use the hard swap
pipeline/jt/show/vfx_core.py       icon pop, atmosphere, clouds (do not call), neon
pipeline/jt/show/clock.py          words.json clock
pipeline/jt/show/labels.py         pills, safe zone, caption band
pipeline/jt/show/faces.py
pipeline/jt/show/truesize.py       sec(lat)^2 and the spoken 16× scale
pipeline/jt/show/pack.py           USA / China / India / Europe packing
pipeline/jt/show/polys.py
pipeline/jt/show/props.py          dust, dashed_path, contact ripple
pipeline/jt/show/flyto.py          van Wijk curve (bridges, not Greenland)
pipeline/jt/show/moves.py          bridge move grammar, includes zoom blur
pipeline/jt/show/segments.py       OLD 30 fps splicer with drag blur. Do not use it for v7
pipeline/jt/show/admin_index.py    SQLite RTree over NE admin-0
pipeline/examples/greenland/       words, stills, gates, the mp4s
pipeline/examples/market/          Märket proof
pipeline/examples/lax_tokyo/
pipeline/examples/canada_rome/
pipeline/examples/model_drop/
pipeline/examples/neum_zoom/
pipeline/style/gold_canada.md
pipeline/data/cache/               gitignored
```

### Clock

`load_clock(words.json)`. `_clean` strips punctuation and uppercases. `t(needle)` matches the token or a substring. `"IT"` matches inside `"IT'S"` and `"WITH"`; the first hit wins, so pass `after=` when a word repeats. `words.json` is the authority (127 words, duration 52.428). Audio duration 52.428 s. Frame count `N = ceil(52.428 * 60 - 1e-9) = 3146`. Picture duration `3146/60 = 52.433333` s. `T_LAST = 3145/60 = 52.416666…` s.

The old `greenland.py` clock uses `FPS = 30`, so its `frames` field is 1573. Do not import that `FPS` into the v5+ renderer. `segments.py` still does. That is a bug if you call it.

### Live camera

`camera_channels(t)` returns globe blend `w` (0 mercator, 1 ortho), unwrapped longitude, latitude, and span. Span is splined in log space and then exponentiated, then clamped to 28–170. `w` is clamped to 0–1. `camera_blend` returns `(merc Cam, ortho Cam, w)`. `camera_at` returns the ortho camera when `w >= 0.5`, otherwise mercator.

Endpoints `t = 0` and `t = T_LAST` are both mercator lon −6, lat 36, span 150, so the loop matches. `check_moves` fails if the span ratio in one frame (1/60 s) exceeds 1.04 or `|Δw|` exceeds 0.05.

Anchor rows are `(t, w, lon, lat, span)`:

| t | w | lon | lat | span |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0 | −6 | 36 | 150 |
| 1.40 | 0 | −9 | 40 | 132 |
| 2.70 | 0 | −12 | 44 | 118 |
| 3.50 | 0 | −13 | 45 | 112 |
| 4.75 | 1 | −22 | 42 | 92 |
| 5.90 | 1 | −40 | 72 | 38 |
| 6.60 | 1 | −41 | 73 | 35 |
| 8.05 | 0 | −28 | 58 | 78 |
| 9.55 | 0 | −32 | 62 | 66 |
| 11.20 | 0 | −36 | 66 | 56 |
| 12.95 | 0 | −40 | 70 | 49 |
| 14.55 | 0 | −41 | 71 | 45 |
| 16.40 | 0 | −42 | 72 | 40 |
| 18.50 | 0 | −8 | 46 | 62 |
| 20.50 | 0 | 8 | 18 | 76 |
| 22.40 | 0 | 17 | 5 | 90 |
| 24.50 | 0 | 17.6 | 3.4 | 86 |
| 26.70 | 0 | 17.3 | 2 | 83 |
| 28.80 | 0 | 17 | 1 | 81 |
| 30.70 | 0 | 17.4 | 5 | 72 |
| 32.80 | 0 | 18 | 12 | 62 |
| 35.50 | 0 | 20 | 8 | 66 |
| 37.30 | 0 | 18.4 | 4 | 74 |
| 39.70 | 0 | 17 | 0 | 84 |
| 42.50 | 0 | 16.4 | −0.8 | 80 |
| 45.30 | 0 | 17 | 0.5 | 86 |
| 47.40 | 0 | 2 | 18 | 108 |
| 49.30 | 0 | −4 | 30 | 130 |
| 51.00 | 0 | −6 | 38 | 148 |
| 52.4167 | 0 | −6 | 36 | 150 |

### Plates and fills

`_globe_mix(span)` is 0 at span ≤ 40, 1 at span ≥ 82, smoothstep between. Regional hypso and Blue Marble are pulled toward each other's mean colour by `pull = 1 - |2*mix - 1|` (strongest in the middle, zero at the ends), then crossfaded. The basemap `_curl` pinches the mercator image and crossfades to the ortho plate with `_smooth(w)`.

`_draw_fill`: if `w ≤ 0.004`, draw the mercator coast only. If `w ≥ 0.996`, draw the ortho coast only and skip a chopped limb (`len(piece) < max(8, int(len(arr) * 0.82))`). Otherwise there is one path. Each vertex is `_blend_xy`: `(1-s) * mercator + s * ortho`, with `s = _smooth(w)`. A point on the back of the globe is parked just outside the limb so it is not folded into a second copy. The basemap is the same blend. `_morph_plate` builds one geographic mesh, samples regional and Blue Marble at those lon/lats (one framing), and also draws a screen grid of the globe so the frame corners stay covered. Near the globe (`s > 0.80`) a gap in that mesh shows the ortho plate instead of stars.

During that blend the outer edge is not the raw mesh. `_silhouette` is a convex superellipse: the full frame at `s = 0`, the orthographic disk at `s = 1`. The plate is masked to it, country fills are clipped to the same path, and the atmosphere stroke follows that path. The stroke fades in only as the outline becomes round (`s` from about 0.55 to 0.93). On a pure globe frame the old circle ring is unchanged. `_path` still delegates to `_path_on(..., full_only=False)` for single-camera callers.

`_africa_box` on mercator keeps points past the frame so shapes parked on the box do not jump when a coast crosses y = 1920.

LoD constants in `lod.py`: `GLOBE_SPAN = 48`, `LOCAL_SPAN = 9`. `paint_lod`'s hard swap is not what Greenland uses.

### What is on screen, in time

Draw order: plate, atmosphere if `w > 0.04`, fills and neon, shapes, faces, hand, labels last.

- Africa gold fill breathes (`sin`). Tint eases from 96 toward 78 across the Algeria comparison.
- Tiles fade with `_window` around the Algeria line (31.900). Compare (Algeria, DR Congo, chip) fades in across that. Pack pieces exit staggered: `out0 = outro + index * 0.12`, fade 0.55 s.
- Home Greenland red is full before the drag and after `HUGE` plus `D_HUGE` (0.85 s). From `outro - 0.2` it eases in over 1.05 s, so 47–50 s is not a white hole.
- Drag trail is only the last 0.22 of journey progress, fade in 0.35 s, fade out 0.40 s after the slide ends. The equator dashed line is gone.
- Blink: `_blink_open`, phase `t * 0.72`, window 0.46–0.54, about every 1.4 s.
- Counter text is always one decimal.

Story beats the picture still has to hit, even though the camera no longer cuts between them: Mercator lie, EXCUSE ME, about 3× wider and about 9× area, true-size slide 16× to 1×, 14 Greenlands fill Africa, Algeria and DR Congo, HI TINY, USA + China + India + Europe (Europe outside Russia), return to the lie, THIS MAP IS LYING.

### Render a still

From `pipeline/` so `jt` imports:

```bash
cd pipeline
python3 -c "
from jt.show.greenland_v5 import Episode
from PIL import Image
ep = Episode()
Image.fromarray(ep.render(7.4)).save('/tmp/t74.png')
print(ep.qc)
"
```

`render(t)` takes seconds. First frame loads earth, plates, and SVG, so it is slow.

### Render a segment

```bash
cd pipeline
python3 examples/greenland/render_span.py 0 500 /tmp/open.mp4
```

`i0` inclusive, `i1` exclusive. RGBA piped to FFmpeg. CRF 16, preset veryfast, profile high, level 5.1, `-video_track_timescale 15360`, no audio. Forces `cache_layers = False`. One frame is often 0.8–1.9 s when both plates are graded. Four cores. Do not render all 3146 frames in one process if you can split on the keyframe list in section 7.

### Render a full picture

`python3 examples/greenland/render_v5.py --video` writes **`greenland_africa_v6.mp4`**, forces duplicate off, cache off, RGBA on, and workers = `cpu_count()`. It still requires `speedup_flags.json` because `_flags()` is read for the worker count. It will overwrite v6. It does not produce v9. `render_v8.py` re-renders only the outbound morph into v7. `render_v9.py` re-renders only the inbound morph into v8.

`python3 examples/greenland/render_v5.py --stills` rewrites `beats_v5.md`, `beats_v5.json`, and `greenland_v5_cues.json` from the stale `MOVES` table, then writes the eight PNGs. Do not run it unless you mean to refresh those v5 artifacts.

Camera-only test, no pixels:

```bash
cd pipeline
python3 -c "import jt.show.test_greenland_v5 as t; t.test_moves_hold_and_loop(); print('ok')"
```

That test requires the camera at 2.40 s and 2.70 s to differ. An old test that required frozen holds will fail on purpose.

---

## 4. Assets

### Hub

Re-fetch at the start of each new episode. Do not commit the JSON snapshot or any pack. `asset_library/` is gitignored.

- `ASSET_HUB.json` Drive id `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV`
- `ASSET_HUB.md` Drive id `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T`

```bash
mkdir -p asset_library/manifests
curl -L 'https://drive.usercontent.google.com/download?id=1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV&export=download&confirm=t' -o asset_library/manifests/ASSET_HUB.json
curl -L 'https://drive.usercontent.google.com/download?id=1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T&export=download&confirm=t' -o asset_library/manifests/ASSET_HUB.md
```

The Neum proof noted a fetch on 2026-10-11 with 56 hub entries, Blue Marble present, and no Landsat, SRTM, NAIP, or DEM pack. Re-count after you re-fetch. Do not trust 56 as permanent.

Private packs (Sketchfab Free Standard, BlendKit) are rendered into video only. Never commit the `.blend` files, never re-upload them.

### Basemaps and caches

| What | Path | Notes |
| --- | --- | --- |
| Blue Marble July, working cache | `pipeline/data/cache/bmng_jul_10800.npy` (167 MB) | Gitignored. Built from the JPEG below. |
| Blue Marble JPEG | `/workspace/asset_library/extra/blue_marble/world.topo.bathy.200407.3x21600x10800.jpg` or `.../map_assets/basemaps/basemaps/nasa_blue_marble/world.topo.bathy.200407.3x21600x10800.jpg` | Public domain. `basemap.py` tries those two paths. |
| Hypso regional cache | `pipeline/data/cache/hyp_50m_5400.npy` (42 MB) | Gitignored. |
| Hypso JPEG in repo | `assets/found/HYP_50M_SR_W.jpg` | The zip is 102,197,904 bytes. Do not commit the zip or the tif. |
| Hypso source | https://naciscdn.org/naturalearth/50m/raster/HYP_50M_SR_W.zip | Public domain, Natural Earth / Tom Patterson. |
| Sentinel local | `pipeline/data/cache/sentinel_local.jpg` and `.json` (also copied under `assets/found/`) | EOX s2cloudless 2020, tiles z=7, x=69–71, y=36–38. CC BY 4.0. Scandinavia only. Not painted on Greenland v7. |
| Admin RTree | `pipeline/data/cache/admin0_bbox.sqlite` | Gitignored. Built from NE 50m. |
| Earth bake | `earth_v3.json`, `ids_v3.npy`, `rings_v3.pkl`, `shade_v3.npy` | Gitignored, from `setup_data.py`. |
| Natural Earth vectors | `pipeline/data/ne/` via `ensure_shapefile()` | Gitignored. |

### Icons and code

- Kenney hand, CC0: `/workspace/asset_library/extra/kenney/input-prompts/Touch/Vector/touch_hand_open.svg`. Hard-coded as `HAND_SVG` in `greenland_v5.py`. Do not upscale `red_hand_point.png`.
- A crosshair SVG exists in the VFX proof. It is not the Greenland hero.
- d3-interpolate `zoom.js` v3.0.1, ISC, used by `flyto.py`. Copy under `assets/found/code/`.
- glfx.js `zoomblur.js`, MIT, used by `apply_zoom_blur` in `moves.py`. Not used by Greenland.

### SFX

Greenland v5, v6, and v7 deliveries are **silent pictures**. Cue sheet: `pipeline/examples/greenland/greenland_v5_cues.json` (older `greenland_cues.json` belongs to the pre-v5 episode). `make_short.py` synthesises whoosh, pop, tick, and ding. SFX peak stays 12 dB under the voice. Loudnorm target −14 LUFS, true peak ≤ −1.5 dBTP, AAC 320 kbps, keyword tails about +7 dB on the last 0.3 s. Do not call espeak for a shippable short. Captions are burned later, outside this picture.

### Voice files named in words.json

Not in git. Narrator: `7e0bd322.mp3` (Brian, Eleven v4), single take, no splice, no stretch. Gags: `1b89c71e.mp3`, `d600a861.mp3`, `70eabdeb.mp3`.

### Found-asset log

`assets/FOUND_ASSETS.md` is append-only. Entries already there: GIBS Blue Marble Brunei and southern Adriatic, Landsat 8 path 118 row 057 (Brunei window) and Landsat 9 path 188 row 030 (Dalmatia window), SRTM `N42E017` and `N43E017`, d3-interpolate zoom.js, glfx zoomblur, Poly Haven `aerial_rocks_02` (Märket stand-in), `HYP_50M_SR_W`, EOX `sentinel_local`. Full Landsat COGs are over 50 MB and are not in the repo; the windowed extracts are.

---

## 5. Greenland episode spec

### Script

Spoken text, in order, with the stressed words as written in `words.json`:

This map says Greenland is as big as AFRICA. It's not even as big as ALGERIA. Excuse me? Here's the trick. To flatten a round Earth, this map stretches land more and more toward the poles. Up where Greenland sits, that's about SIXTEEN times too big. So let's drag Greenland down to the equator, where the map tells the truth... Watch it shrink. And shrink. And SHRINK. Wait... what?! Now drop it on Africa. Africa is FOURTEEN times bigger. Even Algeria is bigger than Greenland. So is DR Congo. Hi, tiny. In fact, put the USA, China, India, and all of Europe outside Russia together... and Africa is STILL bigger. With room to spare. So next time someone shows you this map... remember: Greenland isn't huge. The map is LYING.

Gag speakers: "Excuse me?" and "Wait... what?!" are Greenland. "Hi, tiny." is Algeria. Everything else is Brian.

### Word timings

`pipeline/examples/greenland/words.json`. Duration 52.428 s, sample rate 48000, 127 words. Times are seconds.

| t0 | t1 | word | speaker |
| ---: | ---: | --- | --- |
| 0.150 | 0.538 | This | narrator |
| 0.538 | 0.818 | map | narrator |
| 0.818 | 1.098 | says | narrator |
| 1.098 | 1.738 | Greenland | narrator |
| 1.738 | 1.878 | is | narrator |
| 1.878 | 2.085 | as | narrator |
| 2.085 | 2.298 | big | narrator |
| 2.298 | 2.618 | as | narrator |
| 2.618 | 3.130 | AFRICA. | narrator |
| 3.345 | 3.738 | It's | narrator |
| 3.738 | 3.939 | not | narrator |
| 3.939 | 4.159 | even | narrator |
| 4.159 | 4.263 | as | narrator |
| 4.263 | 4.499 | big | narrator |
| 4.499 | 4.639 | as | narrator |
| 4.639 | 5.282 | ALGERIA. | narrator |
| 5.630 | 6.583 | Excuse me? | greenland |
| 6.897 | 7.232 | Here's | narrator |
| 7.232 | 7.392 | the | narrator |
| 7.392 | 7.768 | trick. | narrator |
| 8.232 | 8.452 | To | narrator |
| 8.452 | 8.852 | flatten | narrator |
| 8.852 | 8.932 | a | narrator |
| 8.932 | 9.272 | round | narrator |
| 9.272 | 9.582 | Earth, | narrator |
| 9.883 | 10.152 | this | narrator |
| 10.152 | 10.412 | map | narrator |
| 10.412 | 10.893 | stretches | narrator |
| 10.893 | 11.233 | land | narrator |
| 11.233 | 11.473 | more | narrator |
| 11.473 | 11.593 | and | narrator |
| 11.593 | 11.828 | more | narrator |
| 11.828 | 12.093 | toward | narrator |
| 12.093 | 12.188 | the | narrator |
| 12.188 | 12.645 | poles. | narrator |
| 13.162 | 13.333 | Up | narrator |
| 13.333 | 13.592 | where | narrator |
| 13.592 | 14.093 | Greenland | narrator |
| 14.093 | 14.520 | sits, | narrator |
| 14.725 | 14.954 | that's | narrator |
| 14.954 | 15.294 | about | narrator |
| 15.294 | 15.854 | SIXTEEN | narrator |
| 15.854 | 16.225 | times | narrator |
| 16.225 | 16.378 | too | narrator |
| 16.378 | 16.727 | big. | narrator |
| 17.198 | 17.394 | So | narrator |
| 17.394 | 17.718 | let's | narrator |
| 17.718 | 18.027 | drag | narrator |
| 18.027 | 18.490 | Greenland | narrator |
| 18.490 | 18.735 | down | narrator |
| 18.735 | 18.855 | to | narrator |
| 18.855 | 18.995 | the | narrator |
| 18.995 | 19.488 | equator, | narrator |
| 19.670 | 19.835 | where | narrator |
| 19.835 | 19.975 | the | narrator |
| 19.975 | 20.160 | map | narrator |
| 20.160 | 20.455 | tells | narrator |
| 20.455 | 20.595 | the | narrator |
| 20.595 | 20.970 | truth... | narrator |
| 21.460 | 21.895 | Watch | narrator |
| 21.895 | 22.095 | it | narrator |
| 22.095 | 22.598 | shrink. | narrator |
| 22.855 | 23.296 | And | narrator |
| 23.296 | 23.815 | shrink. | narrator |
| 24.148 | 24.556 | And | narrator |
| 24.556 | 25.168 | SHRINK. | narrator |
| 25.498 | 26.867 | Wait... what?! | greenland |
| 27.183 | 27.479 | Now | narrator |
| 27.479 | 27.779 | drop | narrator |
| 27.779 | 27.899 | it | narrator |
| 27.899 | 28.079 | on | narrator |
| 28.079 | 28.475 | Africa. | narrator |
| 28.977 | 29.600 | Africa | narrator |
| 29.600 | 29.840 | is | narrator |
| 29.840 | 30.420 | FOURTEEN | narrator |
| 30.420 | 30.777 | times | narrator |
| 30.777 | 31.095 | bigger. | narrator |
| 31.550 | 31.900 | Even | narrator |
| 31.900 | 32.560 | Algeria | narrator |
| 32.560 | 32.680 | is | narrator |
| 32.680 | 32.920 | bigger | narrator |
| 32.920 | 33.083 | than | narrator |
| 33.083 | 33.483 | Greenland. | narrator |
| 33.792 | 34.161 | So | narrator |
| 34.161 | 34.321 | is | narrator |
| 34.321 | 34.701 | DR | narrator |
| 34.701 | 35.188 | Congo. | narrator |
| 35.530 | 36.767 | Hi, tiny. | algeria |
| 37.083 | 37.296 | In | narrator |
| 37.296 | 37.700 | fact, | narrator |
| 37.820 | 38.016 | put | narrator |
| 38.016 | 38.256 | the | narrator |
| 38.256 | 39.057 | USA, | narrator |
| 39.057 | 39.697 | China, | narrator |
| 39.697 | 40.297 | India, | narrator |
| 40.297 | 40.577 | and | narrator |
| 40.577 | 40.757 | all | narrator |
| 40.757 | 40.917 | of | narrator |
| 40.917 | 41.257 | Europe | narrator |
| 41.257 | 41.677 | outside | narrator |
| 41.677 | 41.945 | Russia | narrator |
| 41.945 | 42.392 | together... | narrator |
| 42.763 | 43.118 | and | narrator |
| 43.118 | 43.598 | Africa | narrator |
| 43.598 | 43.778 | is | narrator |
| 43.778 | 44.118 | STILL | narrator |
| 44.118 | 44.443 | bigger. | narrator |
| 44.752 | 45.098 | With | narrator |
| 45.098 | 45.358 | room | narrator |
| 45.358 | 45.478 | to | narrator |
| 45.478 | 45.928 | spare. | narrator |
| 46.377 | 46.639 | So | narrator |
| 46.639 | 46.845 | next | narrator |
| 46.845 | 47.139 | time | narrator |
| 47.139 | 47.499 | someone | narrator |
| 47.499 | 47.739 | shows | narrator |
| 47.739 | 47.859 | you | narrator |
| 47.859 | 48.039 | this | narrator |
| 48.039 | 48.260 | map... | narrator |
| 48.645 | 49.195 | remember: | narrator |
| 49.453 | 50.100 | Greenland | narrator |
| 50.100 | 50.420 | isn't | narrator |
| 50.420 | 50.910 | huge. | narrator |
| 51.190 | 51.380 | The | narrator |
| 51.380 | 51.660 | map | narrator |
| 51.660 | 51.840 | is | narrator |
| 51.840 | 52.347 | LYING. | narrator |

Clock fields derived from those words (see `clock.py`): `sixteen` 15.294, `heres` 6.897 (`HERE` matches `Here's`), `excuse` 5.630–6.583, `wait` 25.498–26.867, `hi` 35.530–36.767, comparison `algeria` 31.900 (the second Algeria; the hook at 4.639 is `t("ALGERIA")` with no `after`), `congo` 34.701, `drag` 17.718, three `SHRINK` starts 22.095, 23.296, 24.556, `fourteen` 29.840, `drop` 27.479, `usa` 38.256, `china` 39.057, `india` 39.697, `europe` 40.917, `still` 43.778, `room` 45.098, `lying` 51.840, `africa14` is `AFRICA` after `drop + 0.8` so 28.977, `outro` is `NEXT` 46.639.

### Beat plan versus camera plan

`beats_v5.md` is the v5 staging table (a move starts on a word, eases, then holds). Useful as a story checklist. It is not the v6/v7 camera. The live camera is the anchor table in section 3. Element timing that still matters:

| Word | t | What the elements do |
| --- | ---: | --- |
| BIG | 2.085 | SAME SIZE pill |
| EXCUSE | 5.630 | EXCUSE ME pill and face |
| POLES | 12.188 | ~3× wider and ~9× area cards |
| SIXTEEN | 15.294 | counter reads 16.0× |
| DRAG | 17.718 | hand, sticker, counter ride a 4.40 s slide to 1.0× |
| SHRINK | 22.095, 23.296, 24.556 | counter is already descending; it is not a cut |
| WAIT | 25.498 | WAIT... WHAT?! |
| DROP | 27.479 | squash and dust, camera keeps drifting |
| FOURTEEN | 29.840 | 14th Greenland, then the set holds while the camera drifts |
| ALGERIA | 31.900 | tiles fade, Algeria and the true-size chip fade in |
| CONGO | 34.701 | DR Congo lights |
| HI | 35.530 | HI, TINY bubble, face inside the frame |
| USA / CHINA / INDIA / EUROPE | 38.256 / 39.057 / 39.697 / 40.917 | staggered pops |
| TOGETHER / STILL / ROOM | 41.945 / 43.778 / 45.098 | pills; STILL BIGGER stays off the USA chip |
| NEXT | 46.639 | return begins; home Greenland red eases in from about 46.44 s |
| HUGE | 50.420 | sticker travels home over 0.85 s |
| LYING | 51.840 | THIS MAP IS LYING; spline is already on the way to the opening frame |

Named durations still in the file, used by elements even though the camera ignores `MOVES`: slide 4.40 s, loop tail 0.50 s, huge 0.85 s. `HUGE_T = CLOCK.t("HUGE", after=outro)`, `LOOP_T = T_LAST - 0.50`.

### v7 splice map

v6 keyframes are every 250 frames (4.166667 s): 0, 4.166667, 8.333333, 12.5, 16.666667, 20.833333, 25, 29.166667, 33.333333, 37.5, 41.666667, 45.833333, 50.0. `-c copy` is frame-accurate when `-ss` is before `-i` on a keyframe.

| Piece | Frames | Source |
| --- | --- | --- |
| open.mp4 | 0–500 | New. Coast crossfade, no clouds, no mode-switch spike. |
| c.mp4 | 500–1000 | Bitstream copy of v6 from 8.333333 s, 500 frames. |
| d.mp4 | 1000–1750 | New. Short fading drag arc, no equator line. Rendered before the `_draw_fill` crossfade edit. `w = 0` for this whole span, so mercator-only fills match the later code. |
| e.mp4 | 1750–2750 | Bitstream copy of v6 from 29.166667 s, 1000 frames. |
| f.mp4 | 2750–3146 | New. No clouds. Home Greenland red eases in. Also rendered before `_draw_fill`. `w = 0`, so equivalent. |

Sum is 3146. New encodes used `libx264` high, level 5.1, yuv420p, CRF 16, veryfast, timescale 15360.

### v8 splice

v7 keyframes used here: frame 250 (4.167 s) and frame 500 (8.333 s). `render_v8.py` copies frames 0–250 and 500–3146, and re-encodes 250–500 with only frames 397–483 newly rendered. Those are the frames where `t >= 6.5` and `0.004 < w < 0.996`.

### v9 splice

The flat-to-globe morph is frames 211–284 (3.517–4.733 s), where `t < 6` and `0.004 < w < 0.996`. It crosses the keyframe at frame 250, so `render_v9.py` re-encodes frames 0–500 of v8 and copies frames 500–3146. Inside 0–500, only 211–284 are newly rendered. Frames 0–210 and 285–499 are the decoded v8 pictures. Same geometry as v8: vertices slide from Mercator to the globe, and the LoD textures share that mesh. The "THIS MAP IS LYING" and "SAME SIZE" pills are drawn once, in screen space, on top of that picture.

### v10 splice

`render_v10.py` decodes v9 frames 0–500, replaces both projection blends (211–284 and 397–483), and copies frames 500–3146. Those are the frames where the outline is the superellipse. The globe hold and the flat map are the v9 pictures.

### v12 splice

`render_v12.py` re-renders only the spans that changed and cuts the rest of v11 on keyframes. What changed:

1. 7.07 s. The close-up plate used to replace the mesh the instant the morph weight crossed 0.80. It now eases in with the morph, so the light map does not swap for the satellite on one frame.
2. 5.0–5.5 s. On the push into Greenland the colour follows the clock from 4.55 s to 6.35 s, one framing, instead of the steep middle of the zoom.
3. 31 s exit. Each of the fourteen copies scales to zero in place over 0.85 s. They are not clipped away by the moving Africa outline.
4. Loop. The title and the country pills are fully on for the last second, matching frame 0, which already has the borders and the labels.
5. ~30 s entrance. The fourteen copies arrive one after another across 0.90 s, each scaling in over 0.42 s.
6. ~37–38 s. Algeria, DR Congo, and the comparison Greenland fade out over 0.50 s while the packed countries fade in over 0.45 s. The background is not a plate cut.
7. ~46–47 s. The four countries scale out over 0.75 s. The travelling Greenland does not pop back on when they leave; it only returns for the inflate, and that return fades out into the map shape.
8. Faces, the crown, the hand, and the text boxes fade over at least 0.25 s.

### v13 splice

`render_v13.py` re-renders 14.5–31.2 s and 37.5–47.5 s from v12 and copies the other keyframe spans.

1. Frame 1679→1680 was a splice, not a spline kink. The engine step there was 0.15. v13 renders that stretch in one pass, so the framing no longer snaps. At 28.0 s the encoded diffs sit around 1.7, with the neighbours.
2. The counter is three stages from `words.json`: about 8× at 22.095 s ("shrink"), about 4× at 23.296 s ("shrink"), and 1.0× at 24.556 s ("SHRINK"). The drag counts down across 17.718–22.095 s. Each later leg eases across the gap to the next word, so the move is not stretched past the words and the holds keep drifting. The camera stays on the sticker.
3. 40–44 s pushes in and back out (span about 84→65→86) so the four countries keep moving. Encoded diffs around 42 s are about 1.3, not 0.24.

### v14 splice

`render_v14.py` keeps the v13 clock and replaces only the picture notes.

1. The ~9× AREA pill is gone. It sat on screen while the voice says 16× too big. ~3× WIDER stays.
2. `16.0×`, TOO BIG, EXCUSE ME?, the comparison labels, the sad face, and DR CONGO scale from 30% and fade across 7 frames. The word times did not move.
3. 3.8–4.2 s no longer cuts the map into a rounded card with black corners. Mesh holes show the flat map until the outline is a globe; space fills the corners only then.
4. 5.6–6.6 s raises contrast 12.5%, ramped over 0.12 s at each end so the grade does not pop. The excuse pill is white with near-black ink.

### Open feedback

Kristóf passed v13 on cuts and smoothness. The four picture notes above are what v14 answers. The clock is unchanged. It is waiting on him.

v6's four bugs, which v7 fixed and v8 kept:

1. About 7.0–8.2 s, red Greenland cut by a straight diagonal, white ice above a ruler edge, and the Africa fill cut by a straight vertical edge.
2. About 46.6–51.3 s, dark translucent ovals on the Atlantic.
3. About 47–50 s, real Greenland as a pure-white blank before it turned red.
4. About 18.5 s and 22 s, thin white dashed lines that looked like debug guides.

Residual, not a failed gate: on the flat map at t = 7–8 the longest Greenland outline step is about 99–185 px against a median near 8–26 px, because Mercator stretches the pole. A chord heuristic flags that. The red fill touches y = 0 across a wide span and almost no bright pixels sit above an interior edge. On the globe the longest Greenland step is about 27 px. Africa's longest step is about 23 px. If he still sees a ruler cut, the remaining cause is the frame cropping a shape that continues past y = 0, not a chord through the island.

---

## 6. QC gates

### Frame-diff gate (mandatory before any Greenland delivery)

Script: `pipeline/examples/greenland/gate_v6.py`.

```bash
cd pipeline
python3 examples/greenland/gate_v6.py examples/greenland/greenland_africa_v7.mp4
```

What it does: FFmpeg scales to 160×90 with `flags=area`, raw rgb24, mean absolute RGB between neighbouring frames. It also splits each frame into a 6×4 grid and flags a local pop.

Fail if any of these:

- any frame's whole-frame diff is **greater than 8** and **greater than 3×** the median of the other diffs in a ±6 frame window, or
- any frame's whole-frame diff is **greater than 1.5** and **greater than 5×** that same median (this is the rule that catches the v12 frame-1680 snap of 3.2 against a 0.3 median), or
- any run of diffs **≤ 1e-6** lasts longer than **1.5 × fps** (90 frames at 60 fps), or
- any grid cell's diff is **greater than 10** and **greater than 6×** the median of that same cell in a ±6 frame window, or
- the last frame versus frame 0 is a loop pop (greater than 8 and greater than 3× the neighbour median, or greater than 2.4 and greater than 2.5× that median).

The cell floor of 10 is there because splicing a fresh render onto an already-encoded coast moves that coast by under 10. An element appearing, which is what v11 missed, clears 10. v11's 7.07 s jump was a cell diff of 59.7 against a median of 8.5, and the whole-frame gate did not flag it.

Exit code 1 on failure. Default path if you omit the argument is `greenland_africa_v6.mp4`.

v14 result: frames 3146, max 9.824, spikes 0, dead 0, pass. Loop seam 2.328 against a neighbour median of 0.530, pass. Local pops 0, pass. Ghost-coast gate: 294 samples, 0 fails.

v13 result: frames 3146, max 9.824, spikes 0, dead 0, pass. Loop seam 1.605 against a neighbour median of 0.533, pass. Local pops 0, pass. Ghost-coast gate: 294 samples, 0 fails.

v12 result: frames 3146, max 6.52, spikes 0 under the old rule. The 5× rule fails v12 at frame 1680 (diff 3.25, neighbours about 0.3).

v11 result: frames 3146, max 13.238, spikes 0, dead 0, pass on the old whole-frame rule. The local rule, added for v12, fails v11 in ten places (3.52 s, 7.08 s, 8.05 s, 17.73 s, 29.63 s, 31.67 s, 38.37 s, 47.50 s, 51.28 s, 51.93 s).

v10 result: frames 3146, max 13.238, spikes 0, dead 0, pass.

v9 result: frames 3146, max 13.188, spikes 0, dead 0, pass.

v8 result: frames 3146, max 13.236, spikes 0, dead 0, pass.

v7 result: frames 3146, max 8.671, spikes 0, dead 0, pass.

v6 result after the veryslow encode: frames 3146, max 15.041, spikes 0, dead 0, pass.

The first v8 splice, before the globe-corner mesh, failed at frame 397 (t = 6.617, diff 31.627, median 2.186) because the new mesh did not cover the ortho frame. That file was not committed.

### Ghost-coast gate

```bash
cd pipeline
python3 examples/greenland/gate_ghost.py
```

Two overlapping fills become one connected region, so this strokes each coastline ring on a 0.28-scale canvas with a 100 px margin. A ring fails when it has two coastlines that are each at least 30% of the longest one and at least 80 px. The sampler walks the whole film every 0.1 s and keeps a time when the projection blend is between 0 and 1, or the plate LoD mix is between 0.02 and 0.98. v9 run: 223 samples, from 3.6 s through 38.2 s, Greenland plus every African country, 0 fails. Drawing the old Mercator path and the old ortho path together fails this test (two large coastlines).

`probe_gate.py` is a preflight on risky second-ranges via spawn workers. It must be a real file, not a stdin script. A probe before the fill crossfade passed except one spike near t = 31.40, which the unclipped Africa box fixed. A recheck of frames 1878–1905 then had no diff above 3.

### Clip-edge check

Not a committed script. It was an ad-hoc probe: build paths with `_ring_paths` at t = 7.0, 7.4, 7.8, 8.1, and flag a chord if the longest segment is greater than 90 px and greater than 8× the median. Use it when a fill changes. Interpret a long Mercator step at the pole with the fill-touches-y=0 test in section 5 before calling it a bug.

### Loop check

`check_moves()` in `greenland_v5.py` asserts the opening and closing cameras match and that both ends are the flat map (`w` near 0). Renderer frame 0 versus the frame at `T_LAST` had mean abs 0 before encode. After yuv420, expect a small decoded difference. Do not "fix" that by copying frame 0 onto the last encoded frame unless you are on the old YAML renderer, which does that on purpose.

### Speedup proof

```bash
cd pipeline
python3 examples/greenland/prove_speedups.py
```

Writes `speedup_flags.json` and `speedup_report.json`. Threshold: max abs diff ≤ 1 on the 0–255 scale, tested on a segment that includes a zoom, a pan, a hold, and a subtle animation. The run that is checked in used 20 frames.

| Speedup | Frames | Max pixel diff | Time saved | Left on? |
| --- | ---: | ---: | ---: | --- |
| All CPU cores (`os.cpu_count()`, here 4, versus 3) | 20 | 0 | −0.453 s (4.07 s vs 3.62 s) | Yes in the flags. The short test was slower because of process startup. Full renders still use 4 because the pixels matched. |
| Cache basemap and borders when camera and lighting match | 20 | 0 | 1.143 s (9 plate hits) | Yes in the flags. **Off for a v6/v7 full render.** |
| Duplicate a frame when the full scene-state hash matches | 20 | 0 | 0.629 s | Yes in the flags. **Off for a v6/v7 full render.** |
| Pipe raw RGBA to FFmpeg instead of writing PNGs | 20 | 0 | 8.086 s | Yes. Stays on. |
| Segmented rendering | — | — | — | Always on. Not a pixel switch. |

`speedup_flags.json` currently says all five true. The video driver overrides cache and duplicate to false. If you add a sixth switch, prove it the same way and write the row into this table.

### Encode identity

Final settings that must not change when a speedup is added: `libx264`, `yuv420p`, CRF 16, 1080×1920, 60 fps, no audio on the picture file. v7 pieces also set profile high, level 5.1, timescale 15360, so a concat with `-c copy` stays one timebase. v6 keyframe interval is 250 frames.

### Size gate

Stay under 100.00 MB decimal or GitHub rejects the push. 50 MB warns. v11 is 87,815,180 bytes. v10 is 89,788,561 bytes. v9 is 91,923,357 bytes. v8 is 95,523,515 bytes. v7 is 97,747,960 bytes. If a new encode crosses 100 MB, a veryslow CRF 16 re-encode of the mp4 is what shrank v6. A medium re-encode made v6 larger. Re-run the frame-diff gate after any re-encode.

---

## 7. Segmented rendering and caching

### Why

A graded morph frame costs about 0.8–1.9 s. A single plate is about 0.3–0.5 s. 3146 frames on 4 cores is a long job. Raw frames must not all sit on disk.

### Full-film driver

`render_v5.py` `render_video()` splits `N` into `cpu_workers()` spans, renders each with a spawn pool, concats with `-c copy`. Each worker forces `duplicate=False`, `cache=False`, RGBA true. Output name is `greenland_africa_v6.mp4`.

### Span driver

`render_span.py` is the tool for a repair. Same encode flags as the v7 pieces, including timescale 15360.

### v8 and v9 concat recipe

`render_v8.py` decodes v7 frames 250–500, replaces 397–483, encodes that GOP at CRF 16, timescale 15360, and concatenates with `-c copy` onto frames 0–250 and 500–3146. `render_v9.py` decodes v8 frames 0–500, replaces 211–284, and concatenates with `-c copy` onto frames 500–3146. After any splice, run `gate_v6.py` on the joined file and `gate_ghost.py` on the episode. The first v8 join failed at frame 397; the committed v8 file does not. The v9 joins at frames 211 and 285 were measured on fresh renders before the splice (mean diffs 1.891 and 3.604 on the 90×160 gate scale).

### Caches that are safe

- Disk caches of static rasters: Blue Marble npy, hypso npy, earth rings. They do not depend on the camera.
- `RasterCache` / `SlotCache` in `fast_render.py`: only when the camera and every animated input in the key are unchanged. On a drifting camera they never hit, and a key that forgets blink phase or cloud phase will duplicate a stale frame. That is why v6/v7 turned them off.
- `scene_state()` exists for the duplicate-frame path. Do not trust it for a delivery unless you have proved the hash covers camera, every element, glow, counters, and blink.

### Caches and code that are unsafe here

- `segments.py` decodes a master, re-renders ranges, and applies a two-frame average on the drag window. It imports `FPS` from the 30 fps `greenland.py`. Do not splice v7 with it.
- `paint_lod` hard-swaps plates. Greenland uses `_graded` instead.
- Do not boolean-test a numpy plate.

### Workers

`cpu_workers()` returns `os.cpu_count()`. Spawn context. The worker function must live in an importable module. A heredoc script has no file for the child to re-import.

---

## 8. Known bugs and next steps

### Known bugs and traps

1. v14 is not approved. Gates passing does not close the visual review.
2. v13 still has the ~9× AREA pill, the label pops, the black-corner card, and the washed-out excuse gag. Do not ship v13 as the current picture.
3. Mercator Greenland at the top edge can look like a clipped polygon because the island continues past y = 0. See section 5. Do not "fix" it by closing a shorter path.
4. `greenland_v5.py` docstring, `MOVES`, and `beats_v5.md` describe the retired discrete camera.
5. `render_v5.py --video` overwrites v6. It does not write v14. `render_v14.py` writes the v14 splice.
6. `segments.py` is the old 30 fps splicer and blurs the drag.
7. `speedup_flags.json` says cache and duplicate are on. The continuous-motion drivers turn them off in code. A future driver that trusts the JSON blindly will freeze frames.
8. Four workers were slower than three on the 20-frame proof. They stay available because pixels matched.
9. Decoded loop differs slightly from the renderer loop because of yuv420.
10. `HAND_SVG` is an absolute path under `/workspace/asset_library/...`. A machine without that checkout cannot draw the hand until the SVG is there.
11. Sentinel local is the wrong continent for Greenland.
12. `/workspace` is a different branch. Editing it does not change v14.
13. `pipeline/examples/market/market_proof.txt` is an untracked leftover. Do not commit it.
14. Karaoke yellow versus cyan is unresolved. Greenland does not burn it.
15. Module `greenland.py` still draws its own karaoke (`_draw_karaoke`) on the old episode. Leave that file's camera alone.

### Next steps, in order

1. Stop. Wait for Kristóf's review of `greenland_africa_v14.mp4`. Do not render v15, do not start Märket, do not start a new episode. The v13 clock stays put.
2. If he names a new visual bug, re-render only the keyframe-aligned span that contains it, splice with `-c copy`, re-run `gate_v6.py` and `gate_ghost.py`. Keep CRF 16 and the timescale. Every new element still needs at least 0.25 s of fade or scale. The shrink counter stays on the three spoken words.
3. If he approves v14, the next map Short is designed on this spline style from the first frame: one continuous camera, one geometry when the projection changes, a convex outline during that blend, exits that keep moving for at least 0.4 s, a loop whose last half-second is the lead-in to frame 0, drift on holds, an element at least every 1.5 s, voice timed from a new `words.json`, public-domain plates, no clouds, no shadow ellipses, no stretched keyframes.
4. Märket, when he asks: replace the Poly Haven rock texture with a real orthophoto. Lantmäteriet was the candidate. Do not use Finnish NLS. The lighthouse should become a real asset from the hub or a CC0 download, not a drawn icon. Re-fetch the hub first.
5. Countries-cut-in-two and a list/trivia format do not exist. Do not build them until he specifies the episode.
6. Update this file before you finish, including the commit hash, the gate numbers, and which branch is live.

---

## 9. Branches and pull requests

All of these were open drafts on 2026-10-11 unless noted. The map-Shorts camera stack is one chain. Review and edit the top. The lower links are history.

### Live

| PR | Head | Base | Title | Role |
| --- | --- | --- | --- | --- |
| (this branch) | `cursor/greenland-africa-v14-7e9d` | `cursor/greenland-africa-v13-7e9d` | Picture notes on the v13 clock | **Current.** v14 picture plus this handoff. |

https://github.com/dagadt675-oss/juicytea-media/pull/29

### Map stack under it (ancestors, still open, not the place to edit)

| PR | Head | Base | What it holds |
| --- | --- | --- | --- |
| #29 | `cursor/greenland-africa-v13-7e9d` | `cursor/greenland-africa-v12-7e9d` | Shrink lands on the three spoken words. Passed cuts and smoothness. Picture notes remained. |
| #28 | `cursor/greenland-africa-v12-7e9d` | `cursor/greenland-africa-v11-7e9d` | The eight v11 pops are eased. Frame 1680 still snaps, and the shrink finishes early. |
| #26 | `cursor/greenland-africa-v11-7e9d` | `cursor/greenland-africa-v10-7e9d` | Fourteen copies ease out, and the loop joins frame 0. The local pops Kristóf named are still in this file. |
| #24 | `cursor/greenland-africa-v10-7e9d` | `cursor/greenland-africa-v9-7e9d` | Convex morph outline. The fourteen copies still vanish, and the loop still pops. |
| #23 | `cursor/greenland-africa-v9-7e9d` | `cursor/greenland-africa-v8-7e9d` | Both projection blends are one geometry. The outline is still the raw mesh. |
| #22 | `cursor/greenland-africa-v8-7e9d` | `cursor/greenland-africa-v7-7e9d` | Outbound zoom is one geometry. The way into the globe is still the old crossfade in that file. |
| #19 | `cursor/greenland-africa-v7-7e9d` | `cursor/greenland-africa-v6-7e9d` | v7. Four visual bugs fixed. Both projection blends in that file are still the old crossfade. |
| #18 | `cursor/greenland-africa-v6-7e9d` | `cursor/greenland-africa-v5-7e9d` | Continuous camera. Gate passed. Visual bugs. Keep the mp4 because later versions copy spans from it. |
| #17 | `cursor/greenland-africa-v5-7e9d` | `cursor/geoglobe-engine-7e9d` | From-scratch episode, then 60 fps and the speedup proof. Rejected as lame. |
| #16 | `cursor/geoglobe-engine-7e9d` | `cursor/greenland-vo-retime-7e9d` | LoD plates, VFX layers, admin index, Märket asset swap. |
| #15 | `cursor/greenland-vo-retime-7e9d` | `cursor/model-drop-7e9d` | Rejected retime. `_glide_keys` lives on this branch (`/workspace`). |
| #13 | `cursor/model-drop-7e9d` | `cursor/map-shorts-pipeline-7e9d` | Temburong and Pelješac drop-ins. |
| #12 | `cursor/neum-zoom-proof-7e9d` | `cursor/greenland-true-size-7e9d` | Public-domain zoom proof. |
| #7 | `cursor/greenland-true-size-7e9d` | `cursor/lax-tokyo-scenes-7e9d` | First Greenland silent picture on the older clock. |
| #4 | `cursor/lax-tokyo-scenes-7e9d` | `cursor/gold-style-kit-7e9d` | LA–Tokyo silent picture. |
| #3 | `cursor/gold-style-kit-7e9d` | `cursor/map-shorts-pipeline-7e9d` | Gold style kit. Camera sway removed. |
| #1 | `cursor/map-shorts-pipeline-7e9d` | `cursor/post-dropbox-shorts-9137` | YAML map-Shorts pipeline. |

The handoff belongs on the v14 pull request. Do not open a second PR for the document alone.

### Other product lines (not this camera)

| PR | Head | Base | Note |
| --- | --- | --- | --- |
| #2 | `cursor/football-earth-v5-6cd0` | `cursor/map-shorts-pipeline-7e9d` | Football Earth. Draft. |
| #5 | `cursor/whatif-humans-engine-f245` | `main` | What-if engine. Draft. |
| #6 | `cursor/scale-journey-module-d7c6` | `main` | Scale journey. Not a draft. |
| #8 | `cursor/bridge-road-skyline-f245` | `cursor/whatif-humans-engine-f245` | River-city logic. |
| #9 | `cursor/penny-lookdown-chase-d7c6` | `cursor/scale-journey-module-d7c6` | NYC blocks around a penny. |
| #10 | `cursor/segmented-render-f245` | `cursor/whatif-humans-engine-f245` | 2–5 s render chunks for that line, not the Greenland splicer. |
| #11 | `cursor/road-network-stills-f245` | `cursor/bridge-road-skyline-f245` | Hub ruins and a skyline. |
| #14 | `cursor/plane-seat-silent-4316` | `cursor/scale-journey-module-d7c6` | Plane-seat stills. |

### Stale on purpose

- `cursor/greenland-vo-retime-7e9d` and anything that calls `_glide_keys`.
- `greenland.py` as an episode renderer. It remains imported for constants and the old shapes.
- `beats_v5.md` as a camera plan.
- The eight `stills_v5` PNGs as pictures of v7.
- A countries-cut-in-two episode or a trivia-list episode. They were named in the request for this handoff and they are not in the repo.

---

## How to keep this file true

At the end of a run that changed code, a picture, a rule, or a branch:

1. Edit the sections you touched. Put the new commit hash, gate numbers, file sizes, and Kristóf's words in the relevant section. Add a rejected attempt if something was thrown out.
2. If he stated a new preference, append it to section 2. Do not delete an old rule; mark it retired and say which rule replaced it.
3. Move the live row in section 9 if you opened a new branch. Leave the ancestor table.
4. Commit the markdown on the branch you actually edited. Copy the same bytes to `/opt/cursor/artifacts/handoff/map_HANDOFF.md`.
5. Push and update the existing PR. Do not open a parallel PR for the handoff alone.
