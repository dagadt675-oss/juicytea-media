# Myth Juice, long-form #1: "Why the Continents Point South (Not Just a Coincidence)"

The channel's first long-form video: 16:9, 1920×1080, 30 fps, 15:34 (v3), six chapters, English narration.

## Deliverables (`release/`)

| File | What it is |
|---|---|
| `metadata.md` | Title (+2 alternatives), description with chapter timestamps and credits, tags, pinned comment, upload settings |
| `thumb_B_pointing_at_what.jpg`, `thumb_A_cant_unsee_it.jpg`, `thumb_S_theyre_scars.jpg` | Three thumbnails, 1280×720: one image, three texts, for YouTube Test & Compare (B is the default) |
| `captions_en.srt` | English captions on the v3 timeline |
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

## v3 (2026-11-06): review round 6

The owner saw animation problems in the 16:51 preview. Round 6 added motion-aware checks (`tools/temporal_scan.py`, `audio_scan.py`,
`asr_check.py`) and a per-segment review by agents (97 findings, `research/review6/`), then one fix agent per chapter module with
test renders. 93 defects were fixed, 61 of 68 chunks re-rendered. A retention panel (four viewer lenses + a voice check) then
produced a ranked plan; the picture-only and audio parts were applied, and the film was tightened in post without new narration
(`tools/edl.py`, `research/review6/edl_v3.json`): 77 s cut (Forster's flood, the re-read list, two restated statistics, the Nevada tangent),
the recap moved to replace the stacked closer, 8-frame dissolves at the three same-subject joins, seven stray take fragments silenced,
one mispronounced name replaced from another take, the record scratch moved, music dips before two punchlines, and the opening theme
returning under the end screen. Chapters: 0:00, 2:15, 3:13, 5:06, 7:10, 9:13, 10:43, 11:46, 13:10.

Render on a Colab L4 GPU (`tools/colab/`): the whole film in 14 minutes (32 s per 450-frame chunk) against 6-8 hours on the 4-CPU box;
`GPU=1` switches `engine/render.cjs` to ANGLE on the NVIDIA EGL driver. The v3 delivery is assembled from the SwiftShader render that the
fix agents verified; the GPU render matches it to within 1/255 on 61 chunks (up to 5/255 on flat-map and photo scenes, GPU image scaling)
and is the pipeline for the next rounds.
