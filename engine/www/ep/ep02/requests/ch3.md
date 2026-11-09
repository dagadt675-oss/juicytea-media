# ch3 requests (2026-11-09)

1. **Bug in ch2.js's `monotone()` (and so in its `chainPath`), copied into ch3 and fixed there.** The Fritsch-Butland tangent's second
   weight is written `(x[i+1] - 2*x[i] + x[i-1]) / d[i]` (that is h1 - h0); it must be `(x[i+1] + x[i] - 2*x[i-1]) / d[i]` (h1 + 2 h0).
   With unequal key spacing the curve overshoots and even runs backwards: ch3's Everest look curve went to -1.07 between keys 0 and 1
   (a SCENE-ERROR until fixed). Any ch2 camera key or water level whose neighbour intervals differ is affected. Please fix it in ch2.js
   (not my file) and, better, put one tested `monotone` / `chainPath` in shared.js for every chapter.
2. **A shared multi-key flight without stops** (`chainPath` in ch2 and ch3, `spline` in ch1): three local copies now.
3. **A shared JUICE CHECK stamp.** ch3 draws its own (`stamp()` in ch3.js: rotated plate, cyan border and TRUE for a true verdict,
   5-frame slam, 1.2 s hold, registered as the frame's one text block). The brand device should look the same in every chapter.
4. **A prop slot on terrain stages.** ch3 adds a mesh (Everest's real terrain on a plinth, forced perspective) to the shared bigisland
   stage and registers it in `S._sections` so every other terrainShot hides it each frame, then shows it from its `cam()` callback (the
   only callback that runs after the hide loop and before the render). A documented `spec.props(lt, S)` hook would make this clean.
5. **Shared paper props for a candle and a sheet of paper** (s072-s073 metaphor): ch3 draws both locally (`candleCard`, `paperCanvas`).
6. **API.md section 6** still says everest_wide has the baked dark blob and the Pali cloud specks (fixed in round 3); also mention that
   region `everest`'s `meta` (hmin, hrange, files) is usable directly for a prop mesh.
