# Myth Juice, long-form #1: "Why the Continents Point South (Not Just a Coincidence)"

The channel's first long-form video: 16:9, 1920×1080, 30 fps, 16:51, six chapters, English narration.

## Deliverables (`release/`)

| File | What it is |
|---|---|
| `metadata.md` | Title (+2 alternatives), description with chapter timestamps and credits, tags, pinned comment, upload settings |
| `thumb_A_cant_unsee_it.jpg`, `thumb_B_pointing_at_what.jpg`, `thumb_C_they_point_here.jpg` | Three thumbnails, 1280×720, for YouTube Test & Compare (B first) |
| `captions_en.srt` | English captions from the narration word timings (upload as a caption track; nothing is burned in) |

The rendered master video is delivered separately (see the session report); it is too large for a normal git file.

## How it is made

- `engine/`: programmatic film engine (headless Chromium + three.js + Canvas2D → ffmpeg). It draws a photoreal NASA Blue Marble globe with DEM relief,
  highlights, labels and arcs, a paleo-globe (GPlates/EarthByte reconstructions), animated CC0 3D characters (Quaternius/Kenney), a cut-away Earth,
  a tetrahedron morph and motion-graphics primitives. See `engine/ENGINE.md`.
  - `engine/www/ep/ep01/`: the episode, with chapter modules `ch1.js` to `ch6.js` (plus helpers), `timing.json` (word-level narration timing and
    markers), `edit.js` (orchestrator), `thumbs.js` (thumbnails) and the public-domain archival images in `img/`.
  - Large shared assets (8K textures, Natural Earth GeoJSON, paleo coastlines, fonts, 3D models) are not committed. They are rebuilt with the tools.
- `tools/`: the YouTube gap probe, NASA GIBS stitcher, DEM builder, ElevenLabs TTS with word timings, music and SFX mixer (BS.1770 loudness,
  true-peak limiter), QC, captions, and the restart-safe chunk renderer.
- `research/`: benchmark of 1M-view videos, retention checklist, creative brief, the fact ledger and the locked script.

## Render

```bash
# restart-safe: 450-frame chunks, skips finished ones; several runners can share the chunk dir (chunk locks)
python tools/render_chunks.py --ep ep01 --frames 30329 --chunk 450 --par 2 --out video_full.mp4
# grade + BT.709 master with the final mix (-14 LUFS, -1.5 dBTP)
tools/assemble.sh video_full.mp4 mix_full.wav final.mp4 18
python tools/qc_video.py final.mp4 qc/ --sheet 48
```
