# Myth Juice, long-form #1: "Why the Continents Point South (Not Just a Coincidence)"

The channel's first long-form video: 16:9, 1920×1080, 30 fps, 16:51, six chapters, English narration.

## Deliverables (`release/`)

| File | What it is |
|---|---|
| `metadata.md` | Title (+2 alternatives), description with chapter timestamps and credits, tags, pinned comment, upload settings |
| `thumb_B_pointing_at_what.jpg`, `thumb_A_cant_unsee_it.jpg`, `thumb_S_theyre_scars.jpg` | Three thumbnails, 1280×720: one image, three texts, for YouTube Test & Compare (B is the default) |
| `captions_en.srt` | English captions from the narration word timings (upload as a caption track; nothing is burned in) |

The rendered video is delivered separately; it is too large for git. There are two encodes of the same picture and mix:

- master: CRF 18, ~6.9 Mbps, ~870 MB;
- upload copy: 2-pass ~3.7 Mbps video + AAC 256k, under 500 MiB (`tools/deliver_encode.sh`).

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
# size-capped upload copy (same grade chain, 2-pass)
tools/deliver_encode.sh video_full.mp4 mix_full.wav upload.mp4 3700
```

## Final QC (`research/qc_final.json`)

- Loudness: -14.0 LUFS integrated, LRA 2.3 LU, true peak -1.4 dBTP.
- Length: 1010.97 s. 93 hard cuts, 10.75 s apart on average. Between cuts the picture keeps moving with camera moves, morphs and overlays.
- The automatic verdict is "FAIL", but every flag was checked by eye:
  - The two black stretches are intended: the hard cut to black on "Eventually" (53.1–54.6 s) and the war-smoke beat (506.3–507.2 s).
  - The 25 "static" stretches are slow drifts and overlays that build up gradually. The detector's threshold (scene score < 0.0008 for more than 3.5 s) is stricter than what a viewer would see as a still frame.
  - The only silence is the final 1.4 s after the last line.
- The whole film was reviewed end to end on sampled frame sheets in five waves. All blockers and major findings were fixed, and the affected chunks were re-rendered.

