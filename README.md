# juicytea-media

**Deterministic 3D/2D Programmatic Video Engine & Automated Visual QC Pipeline**

`juicytea-media` is an open-source programmatic rendering and verification framework designed for data journalism, financial dissection documentaries, and automated educational studios. It bridges headless **Three.js (WebGL) PBR 3D scenes**, frame-exact **HTML5 Canvas2D typographic overlays**, word-level audio-sync anchoring, and strict **multi-stage quality control (QC) gates**.

---

## Why `juicytea-media`?

Existing programmatic video frameworks (such as Remotion or Manim) excel at flat 2D vector animations but lack native pipelines for:
1. **Continuous PBR 3D Camera Choreography:** Zero-cut diorama transitions, HDRI lighting, and 3D-to-2D screen-space coordinate projection (`anchors`).
2. **Primary-Source Fact Ledger Binding:** Every rendered counter, split-flap roll, and label is strictly bound to a verified data ledger (`facts.js`)—preventing hallucinated or unsynchronized figures on screen.
3. **Automated Visual & Audio QC Gates:** Built-in frame inspection that blocks renders on bounding-box text collisions, WCAG local contrast failures (< 3.0:1), empty canvas dead-zones, or EBU R128 loudness violations.

---

## System Architecture

```text
juicytea-media/
├── lib/
│   ├── engine.js          # Deterministic Canvas2D overlay, split-flap counters (E.roll), tokens
│   └── compositor.js      # 3D sequence + 2D typography + word-synced caption compositor
├── src_assets/
│   ├── motion3d.html      # Three.js PBR 3D scene graph & camera rig definitions
│   └── gen_seq.mjs        # Headless WebGL sequence generator & 3D-to-2D anchor exporter
├── render/
│   └── render.mjs         # Frame-accurate seek renderer & FFmpeg H.264/AAC muxer
├── qc/
│   ├── visual_qc.py       # BBox overlap, safe-zone margin, edge-density & contrast verifier
│   └── voice_qc.py        # Zero-crossing splice check, LUFS (-14) & True Peak (-1.5 dBTP) gate
└── tools/
    └── gates/             # Multi-stage CI/CD production gates (G1 Timing -> G2 Stills -> G3 Animatic)
