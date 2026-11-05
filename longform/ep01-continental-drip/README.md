# Myth Juice — long-form #1: "Why the Continents All Point South"

Production project for the channel's first long-form video (16:9, ~16 min).

- `engine/` — programmatic film engine (headless Chromium + three.js + Canvas2D → ffmpeg):
  photoreal NASA Blue Marble globe, DEM relief, highlights/labels/arcs, paleo-globe (GPlates/EarthByte reconstructions),
  animated CC0 3D characters (Quaternius/Kenney), cut-away Earth, tetrahedron morph, motion-graphics primitives.
  See `engine/ENGINE.md`. Large assets (textures, Natural Earth GeoJSON, paleo coastlines, fonts, models) are fetched by the tools, not committed.
- `tools/` — YouTube gap probe, NASA GIBS stitcher, DEM builder, ElevenLabs TTS with word timings, music + mixer, QC.
- `research/` — benchmark of 1M-view videos, retention checklist, creative brief, script workflow and drafts.

Rendering: `node engine/render.cjs --page film.html --q '{"ep":"ep01"}' --frames N --jobs 3 --out out.mp4`
