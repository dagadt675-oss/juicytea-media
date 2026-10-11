# Scale-journey (format B)

Format B from the approved slate. The full test picture is the penny dropped from the Empire State Building. The second spec is rice on a chessboard. Hole-through-the-Earth, the unbranded brick tower, and the Rhode Island crowd resolve to timelines and the instancer.

Shared with formats A and C: the caption band and the `words.json` clock from `whatif/engine`. The format B counter is the slate's Anton slot stack in `whatif/ui/` (height in feet big, metres small). The same folder holds label pills, the reference outlines (Statue of Liberty, Empire State, Burj Khalifa, a stadium, Titanic, a person), and the loop helper.

```bash
python3 whatif/scale_journey/render_episode.py whatif/scale_journey/episodes/penny_empire.yaml
python3 whatif/scale_journey/render_episode.py whatif/scale_journey/episodes/rice_chessboard.yaml --timeline-only
```

The older zoom path is still here: one dolly that only moves out or in, and an ending card that dissolves back to frame 0.

This package lives beside the headless what-if engine (`whatif/engine`, episode 1 “all humans disappeared”). It does not import or edit that code. When that engine is merged, a spec with `module: scale_journey` can be handed here. See `docs/ADOPTION.md`.

## Standing asset rule

Permanent. It applies to every episode, not only the penny fall. Use a ready-made model for animations, people, buildings, whole scenes and city blocks, vehicles, props, nature, and effects. Prefer a complete pre-built scene (the Procedural City blocks, a ruined city, an airport) over a set assembled from primitives.

Check sources in this order:

1. **The asset hub.** Re-fetch `ASSET_HUB.json` before building (Drive id `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV`; the readable catalog is `ASSET_HUB.md`, id `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T`). Hub packs already include the CC0 library and the private Sketchfab Free Standard / BlendKit files. Private raw files stay in the gitignored `cache/private/` and are never committed.
2. **A free ready-made file from the web, only if the hub does not have it.** It must be commercial-use with no attribution required: CC0 or public domain. Search Poly Haven, ambientCG, Kenney, Quaternius, Poly Pizza (CC0), OpenGameArt (CC0), or Sketchfab with the CC0 filter via the API. Download it, then log the license and source in `LICENSES.md` and, if it should be fetched again, in `assets/library/cc0_manifest.json`.
3. **Build it only if both of those fail.** Say which hub entries you checked and which web sources you searched, and why each one did not fit.

Never use CC-BY, NC, or ND, and never use game or brand IP. Sketchfab Free Standard and BlendKit are allowed only when they come from the hub (renders OK, no redistribution of the raw file). People are rigged and animated from the hub’s people and animation packs. A static placeholder or a silhouette is not a person.

The airport city scene in the hub includes a Malaysia Airlines livery. That livery stays unused. If that scene is ever placed, repaint the airline aircraft plain white first. The ruined-city pack and that airport are optional scenery, not a default set.

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
