# Contributing to juicytea-media

We welcome contributions to the `juicytea-media` programmatic rendering engine, scene pattern library, and automated QC suite.

## Core Engineering Rules for Contributors

1. **Deterministic Frame Output:** Every scene or camera move must be strictly a function of frame index `f` and `fps` (`nf = Math.ceil(sec * fps)`). Never use `Date.now()` or unseeded `Math.random()` inside render loops.
2. **QC Gates Are Never Loosened:** Pull requests that modify `lib/engine.js` or `src_assets/motion3d.html` must pass all bounding-box collision, margin safe-zone, and local contrast (>= 3.0:1) checks in `qc/visual_qc.py`.
3. **Asset Licensing:** Any 3D model, HDRI, PBR texture, or icon added to the pattern library must be strictly `CC0` or `MIT` licensed and logged with its primary source URL.

## Submitting a Pull Request
1. Fork the repository and create a feature branch.
2. Run a 12-frame contact sheet verification (`--sheet 12`) on your test specification.
3. Ensure both `npm run qc:visual` and `npm run qc:audio` exit with code `0`.
