# What-if engine

A Blender episode is a YAML spec. The same city, coast, and farm scenes, and the same effect channels, render every short.

```bash
python3 whatif/render_episode.py whatif/episodes/humans_disappeared.yaml \
  --frames all --samples 8 --scale 1 --composite
```

That writes a silent PNG sequence, composites the UI, and (when you encode) an H.264 file plus `timeline.json`.

Timing is about 2.6 words per second of narration plus a 0.3 second pause, unless a beat sets `seconds`. Channels listed as a number are the value at the end of the beat. A list of `{u, v}` places keys inside the beat (`u` is 0..1). `reset: true` cuts every channel back to the opening on the next frame so the film can loop.

`format: A` is the time-lapse. `format: C` is the real-time street disaster (`engine/format_c.py`): inertia launch, fracture, wave wall, underwater grade, HUD. `camera.mode` is `locked` or `pov` (`engine/pov.py`). A POV path can name grab points for the cylinder arms. The park picnic and the cat rig are not in the build yet. Word clocks are `words.json` with `{w, t0, t1}`, the same shape as `pipeline/examples/lax_tokyo/words.json`. Format B's captions and scale camera are not copied here.

Preview stills of episode 1, 1080×1920, are in `/opt/cursor/artifacts/whatif_preview/`:

- `day1.png` — opening day
- `year1.png` — about 1 year
- `year100.png` — about 100 years
- `year500.png` — about 500 years

They are layout and decay tests, not the finished short.
