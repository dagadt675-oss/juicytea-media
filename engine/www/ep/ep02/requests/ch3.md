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

## Round 2 (2026-11-09, after the ch3 review)

7. **Mixer re-sync requests (spot_notes section 10 allows it; ch3 events are keyed to markers, so these follow the words):**
   - x076 ice_wind: start it on the cut to Everest's summit, 240.42 s (= K.T('heard') + 0.64 + 1.25; the JUICE CHECK stamp keeps its 1.2 s hold on the comparison shot).
   - x078 whoosh_soft (whip out): now at the word "road", whip 243.79-244.03 s (K.word('s065','road').start - 0.1, 8 frames).
   - x079 jeep_climb: the road shot now holds 244.03-246.42 s (2.4 s); start it at 244.03 s and let it run about 2.2 s.
   - x080 whoosh_soft (whip back) unchanged at K.Te('road') - 0.05 = 246.42 s; x081 flag_droop unchanged (the pennant drops from 246.68 s, lands about 247.15 s).
   - x063 and x089 line_draw: they land when the lines START drawing (crest line 187.81-188.81 s, plate arrow 277.47-278.37 s). Shift x063 by about +1.0 s and x089 by about +0.9 s so each lands as its line finishes (the picture keeps the lines on {range} / {plate}, per the 2-4 frame lead rule).
   - x096 impact_short (311.78 s) now has a 6-frame camera settle on it (K.Te('bigbaby') + 0.05).
8. **A civilian public-domain 4WD paper cut-out.** The kit's only 4WD is the 1942 FSA/OWI jeep with four helmeted soldiers: it reads as a military convoy and pre-echoes ch5's war beat. Wanted: a plain 4WD (or pick-up) in profile, no people or one civilian driver, public domain (NPS, USGS, USFS, Library of Congress FSA civilian photos), cut like the others. s065 swaps it in by name.
9. **Legacy bigisland colour:** a grey smear on the Kona slopes (frames 9006/9115/9474 in ch3, today's sea level) reads as fog. Please check hero_color.jpg there (cloud or haze in the composite).
10. **ch6 / payoff owner, please confirm:** the hot-spot cut-away (s071-s072) uses the payoff's Section device on another plane (az 306 through Kīlauea) with the flexure sag on. Round 2 crops it to 36 km deep and frames the glow and the plate, but the crust under the island still shows its dent. If that pre-spends the dented-base reveal, ch3 can set `sag: 0.35` there (or frame the dent out).
