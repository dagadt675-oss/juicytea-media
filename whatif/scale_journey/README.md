# Scale-journey

One unbroken zoom for a YouTube Short. The picture is driven by a YAML episode: an everyday object, a single dolly that only moves out (growth) or in (shrinking), a left-side Anton counter, a scale reference every few seconds, and an ending card that dissolves back to frame 0 so the file loops.

This package lives beside the headless what-if engine (`whatif/engine`, episode 1 “all humans disappeared”). It does not import or edit that code. When that engine is merged, a spec with `module: scale_journey` can be handed here. See `docs/ADOPTION.md`.

```
whatif/scale_journey/
  render_episode.py      # host CLI
  engine/spec.py         # YAML → timeline, no Blender
  engine/camera.py       # log-scale layer swap, float32-safe
  engine/build.py        # blender --background --python
  engine/overlay.py      # Anton UI, caption band kept clear
  episodes/*.yaml
  docs/SCALE_JOURNEY.md
```

## Render

```bash
# Timing only. Writes timeline.json. No Blender.
python3 whatif/scale_journey/render_episode.py \
  whatif/scale_journey/episodes/rice_64.yaml --timeline-only

# Full silent Short (1080×1920, 30 fps, H.264, no audio).
python3 whatif/scale_journey/render_episode.py \
  whatif/scale_journey/episodes/rice_64.yaml

# Fit the picture to an ElevenLabs words.json (monotonic; never rewinds the zoom).
python3 whatif/scale_journey/render_episode.py \
  whatif/scale_journey/episodes/rice_64.yaml \
  --words whatif/scale_journey/examples/words_rice.json
```

Blender 4.5.9 LTS is expected at `~/apps/blender-4.5.9-linux-x64/blender`, or pass `--blender`.

Outputs in `whatif/scale_journey/out/<id>/`:

| File | What it is |
| --- | --- |
| `<id>.mp4` | Silent master |
| `timeline.json` | Milestone times, per-frame counter values, label texts, for voiceover and karaoke |
| `contact_sheet.jpg` | 2 fps sheet |
| `keys/key_*.png` | Six stills |
| `frames/` | Composited PNG sequence |

Tests (no Blender): `python3 whatif/scale_journey/tests/test_scale_journey.py`

The spec format, the layer swap, and how to author a third episode are in `docs/SCALE_JOURNEY.md`.
