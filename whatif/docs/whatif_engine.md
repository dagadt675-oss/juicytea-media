# What-if engine

A Blender episode is a YAML spec. The same city, coast, and farm scenes, and the same effect channels, render every short.

```bash
python3 whatif/render_episode.py whatif/episodes/humans_disappeared.yaml \
  --frames all --samples 8 --scale 1 --composite
```

That writes a silent PNG sequence, composites the UI, and (when you encode) an H.264 file plus `timeline.json`, `words.json`, and `sfx.json`.

Episode 1 sets `audio.narration: false` and `audio.music: false`. `sfx.json` is the cue sheet (city bed, wind, birds, water, creaks, rust, glass, collapse). `words.json` is empty for that episode. `ui.text` is `title` and `counter` only.

Timing is about 2.6 words per second of the beat line plus a 0.3 second pause, unless a beat sets `seconds`. Channels listed as a number are the value at the end of the beat. A list of `{u, v}` places keys inside the beat (`u` is 0..1). `reset: true` cuts every channel back to the opening on the next frame so the film can loop.

`engine/assets.py` is the swap point for trees, people, cars, buildings, props, and the HDRI. An enabled file that exists replaces the procedural mesh for that kind. Imported meshes are normalized to the record's target height (cars: length, width, and height). Packs that are not on disk stay off, and the scene keeps the procedural fallback.

`python3 whatif/assets/fetch_cc0.py` downloads the public CC0 zips from the Drive manifest into `/opt/cursor/asset-cache/cc0` (or `CC0_CACHE`). The zips stay out of git. When that cache is present, the river city uses Kenney skyscrapers, Quaternius street pieces, Kenney cars, Quaternius trees, and rigged people with idle and walk clips. When the private Sketchfab cache is present, a man flossing on the far bank and a woman walking with a phone on the promenade replace the mannequin dance. Both vanish with everyone else. A deer still grazes in the park and stays. The BlendKit cache, when present, supplies the skyline towers, the fountain benches, a few posed people, a cat, a hydrant, and the rubble that appears as the city collapses. Park trees stay the Quaternius set. Branded models are skipped. The files stay out of git and are rendered only.

`format: A` is the time-lapse. `format: C` is the real-time street disaster (`engine/format_c.py`): inertia launch, fracture, wave wall, underwater grade, HUD. `camera.mode` is `locked` or `pov` (`engine/pov.py`). A POV path can name grab points for the cylinder arms. The park picnic and the cat rig are not in the build yet. Word clocks are `words.json` with `{w, t0, t1}`, the same shape as `pipeline/examples/lax_tokyo/words.json`. Format B's captions and scale camera are not copied here.

Preview stills of episode 1, 1080×1920, are in `/opt/cursor/artifacts/whatif_preview/`:

- `day1.png` — opening day
- `year1.png` — about 1 year
- `year100.png` — about 100 years
- `year500.png` — about 500 years

They are layout and decay tests, not the finished short.
