# Myth Juice film engine (shared by all episodes)

The canonical engine. Clone the repo and it runs: code, vendor libraries and all shared data assets are committed.
`longform/ep01-continental-drip/engine` is the frozen ep01 snapshot; build new episodes here.

Headless Chromium + three.js r170 + Canvas2D, a pure function of the frame number, encoded with ffmpeg. 1920x1080 or 1080x1920, 30 fps.

## Quick start
```bash
cd engine && npm ci                      # three, d3, commander (Playwright + Chromium come from the machine)
node still.cjs --page film.html --q '{"ep":"test"}' --frames 0,60 --outdir /tmp/stills    # a few frames as JPEG
node still.cjs --page lab_globe.html --q '{"mode":"after","shot":"froward"}' --frames 0 --outdir /tmp/stills
node render.cjs --page film.html --q '{"ep":"EP"}' --start 0 --frames 900 --jobs 3 --out out.mp4
```
- Local rendering is software WebGL (slow but exact). Final renders: Colab NVIDIA GPU with `GPU=1` (see `tools/colab/README.md`; a 16-minute film renders in about 14 minutes on an L4).
- Long films render in restart-safe 450-frame chunks: `python tools/render_chunks.py --ep EP --frames N --chunk 450 --par 2 --out video.mp4`.

## Layout
| Path | What |
|---|---|
| `ENGINE.md` | API reference for building scenes (edit.js contract, globe camera, fx primitives, 3D actors, paleo-geography, data overlays, sound cues) |
| `www/film.html` | Runtime: loads `www/ep/<EP>/edit.js` + `timing.json` (narration word timings and markers) |
| `www/lib/` | Production modules: `globe.js` (photoreal globe), `fx.js` (2D primitives), `geo.js` (Natural Earth helpers), `shots.js`, `actors.js` (animated 3D characters), `cutaway.js`, `morph.js`, `beats.js`, `equalearth.js` |
| `www/lab/`, `www/lab_*.html` | ep02 prototypes, not yet production: `globe/cineglobe.js` (cinematic globe: clouds, sun glint, grade, depth of field), `drain/terrain.js` (DEM terrain and seafloor with a draining water plane), `type/type.js` (phone-first type system), `story/story.js` (paper cut-outs of real photos on the map). Review verdicts and open issues: `longform/ep02-hawaii/research/visual/visual_plan.md` |
| `www/ep/<EP>/` | One folder per episode (`test`, `test2` are small examples). Episode folders of finished films live under `longform/<ep>/` |
| `www/tex`, `www/geo`, `www/paleo`, `www/models`, `www/fonts`, `www/jsm` | Shared data and vendor assets, see `ASSETS.md` |
| `tools/` | Production tools: chunk renderer, EDL assembly with dissolves, music/SFX mixer (-14 LUFS, -1.5 dBTP), ElevenLabs TTS with word timings, captions, QC (video, temporal, audio, ASR), NASA GIBS and DEM builders, paleo fetchers, YouTube supply probe, Colab GPU scripts |

Rules for working on the engine and the films: `PLAYBOOK.md` at the repo root.
