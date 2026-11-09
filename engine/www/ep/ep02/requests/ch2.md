# Chapter 2 requests (toolkit owner; one cross-chapter note at the end)

Each item: what, why (segment, still), and the workaround ch2 uses until it is merged. Stills are in the scratchpad (`research/ep02/ch2/`), never in git.

## 1. Gauge: a faint leading zero and a wide plate for 5-digit values (shared.js `ui.gauge` / `ui.number`)

- What: between about 9,200 and 10,000 ft a faint leading `0` shows in front of the value (`-09,31x FT`, s034 `{first}` + 0 to 0.8 s, f3714). The plate is about 1,050 px wide when `to` has 5 digits (16,404 ft for a 5,000 m drain), so it covers a lot of the subject.
- Ask: hide leading zeros completely while `lead0: false` (no fade-in ghost), and a narrower value window for 5-digit ranges (for example only as many digit slots as the current value needs, growing as it rolls).
- Workaround: none in ch2 (the counter is the toolkit's); the camera keeps Oʻahu below the plate (y 360 or lower).

## 2. Drained shallow flats read as turquoise lakes (lab/hawaii/hterrain.js)

- What: the terrain shader takes the satellite colour for every texel above -6 m (`alb = mix(seabed, land, smoothstep(-6, 4, h))`). Below sea level that colour is the picture of the water, so once drained, Kāneʻohe and Kailua bays, the fringing reef flats and the inland fishponds show turquoise-green "lakes" 5 km above the new sea (s036-s037 swing back, f4239 x 520-1100, y 560-780 in round 6).
- Ask: a uniform (for example `flatSea` 0..1) that uses the depth-coded seabed (`seaMat`) for texels below 0 m once they are exposed (level below h), so every drained flat matches the rest of the seabed.
- Workaround in ch2: the S2 mask's G channel covers the texels from -14 to +0.3 m around Oʻahu and dims them as soon as the level falls past them (`dim` 0 to 1 from -1 to -11 m): they read as grey sediment, not water. The gate now passes on the swing back (f4239: tan 7 %, drain-clone 11.50).

## 3. Nested region colour stops with a hard edge (kilauea_sf; region_bake / loadRegion)

- What: `kilauea_sf` (31 m) draws its own satellite colour up to its bbox and the parent `bigisland` colour beyond, with no blend: a straight-edged orange-brown "pyramid" on Mauna Loa's SE flank and a soft green trapezoid over Puna and Hilo whenever lon -155.6 or lat 19.5 is in frame (round 6 f4947, f5010-f5258, f5355-f5457). Its bbox also ends at -154.85 / 19.5, inside Kīlauea's south flank (Cape Kumukahi is at -154.81, 19.52), so a seam-free view of the whole flank is impossible.
- Ask: feather the nested colour (and heights) into the parent over 3-5 km at the bbox edge, and extend `kilauea_sf` east and north by about 0.1 deg.
- Workaround in ch2: S4 renders on `bigisland` throughout (115 m grid; it reads well at 40-240 km); the hand-off from `main_chain` happens high in the flight SE (d about 260 km), so the coasts do not double.

## 4. Pali colour: never-clear texels on the Koʻolau crest (region `pali`)

- What: pale, blocky, translucent patches on the crest within about 1 km of (-157.80, 21.37): most likely the 3-4 % of HLS texels that were never cloud-free, filled with a flat value (round 6 f3190, f3204, f3228; review crop_3204.jpg).
- Ask: inpaint those texels from the clear neighbours (or from `oahu_nuuanu`'s colour) in the `pali` bake.
- Workaround in ch2: the dive now rises out over the drop and looks down from 1.1 km NE of the lookout, so the crest west of the lookout stays behind the camera; S1 hands off to `oahu_nuuanu` 2.5 s into the dive.

## 5. A multi-key camera spline in shared.js

- What: `orbitPath` eases every segment to rest, so a flight through several keys stops at each one.
- Ask: a shared `chainPath(keys)` (a per-channel monotone cubic through orbit keys: lon, lat, log d, tilt, unwrapped heading, fov, h), easing in at the first key and out at the last only.
- Workaround: ch2.js has a local `chainPath`, used for the dive, the drain flight, the swing back, the `{outhere}` flight, the `{spare}` rise into the 100 MILES pull-back, the flight SE and the last move.

## 6. Sub-frame motion blur

- What: ch2's fastest moves now peak at 6.5-7.4 % of the camera distance per frame (the dive's level-out 109.3 s, the drain flight to the first block 123.7 s, the swing back 138.3 s, `{outhere}` 143.8 s); turns stay at 3.0 deg per frame or less. Without motion blur they still need a phone motion test.
- Ask: optional sub-frame motion blur for terrain shots (n sub-frames of the camera, averaged before the grade).

## 7. Cross-chapter note for the orchestrator and the ch3 builder (not a toolkit change)

- ch2 now ends (t1x) on region `bigisland`, looking SW at the Hāmākua flank from the NE, the same side and subject as ch3's opening low camera: orbit camera `{ lon: -155.33, lat: 19.83, h: 0, d: 95, tilt: 75, heading: 210, fov: 40 }` (ch2.js `CH3_IN`), water falling (`bigDrain`, about -110 m at t1x).
- ch3 opens 1.2 km above the water about 41 km from the flank (heading about 208). The 0.3 s dissolve under the card is now the same subject from the same direction, about half the distance. To make it seamless, ch3 could start its first camera from `CH3_IN` and descend to its low camera over its first 1-1.5 s (or ch2 can end on any camera ch3 names).
