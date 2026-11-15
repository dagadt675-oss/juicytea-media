# Chapter 2 requests (toolkit owner; one cross-chapter note at the end)

Each item: what, why (segment, still), and the workaround ch2 uses until it is merged. Stills are in the scratchpad (`research/ep02/ch2/`), never in git.

## 1. Gauge: a faint leading zero and a wide plate for 5-digit values (shared.js `ui.gauge` / `ui.number`)

- What: between about 9,200 and 10,000 ft a leading `0` fades in front of the value (`ui.number` fades a hidden digit in from 0.92 to 1.0 of its base, but the digit it fades in is still `0`): in ch2 that is f3712 to f3761 (s034 `{first}` to 1.6 s after it): a faint ghost `0` beside the minus at f3714-f3716 (`-9,266`, `-9,322`), `09,421` at f3720 and a two-thirds-bright `-09,71x` with the minus touching the zero at f3738 (round 8 `final_r8`), until the roll to `-10,00x` at f3762. The plate is about 1,050 px wide when `to` has 5 digits (16,404 ft for a 5,000 m drain), so it covers a lot of the subject.
- Ask: hide leading zeros completely while `lead0: false` (a hidden digit should appear only as its `1` rolls in, with the minus sliding left at the same moment), and a narrower value window for 5-digit ranges (for example only as many digit slots as the current value needs, growing as it rolls).
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
- Two things to copy from ch2.js `monotone` when it moves to shared.js (round 8):
  - The inner-key slope is the Fritsch-Carlson / Brodlie weighted harmonic mean `m = 3(h0 + h1) / ((2 h1 + h0) / d0 + (h1 + 2 h0) / d1)`, with `h0` the segment before the key and `h1` the one after. Round 7 had the second weight as `h1 - h0`. That made the slope too steep or of the wrong sign whenever the two segments differ in length: 7 camera reversals away from any key in ch2 (lon 131.03 s, lat 108.53 and 181.47 s, d 130.80 s, tilt 129.70 and 144.60 s, fov 110.73 s) and a drain level that overshot to -3,109 m and then rose back 86 m (124.5-125.3 s), so the water came back up while the gauge counted. With the weights fixed there are 0 reversals away from keys in any channel, and the drain level never reverses (largest step 76 m a frame). `{"ch2oldmono":1}` still renders the old curve for comparison.
  - An optional `peak` list of inner keys. For a 3-key flight that should be one speed hump, the harmonic mean sits between the two secants, so the camera slows at the middle key (a 14-26 % speed dip in the swing back, `{outhere}`, the `{spare}` rise and the flight SE). The peak option raises that key's slope to max(1.5 x the smaller secant, 1.25 x the larger), capped at 3 x the smaller. That stays inside the Fritsch-Carlson monotone box, so the curve is still monotone, and each of those flights is now one hump. `{"ch2nopeak":1}` turns it off.
- Workaround: ch2.js has a local `chainPath`, used for the dive, the drain flight, the swing back, the `{outhere}` flight, the `{spare}` rise into the 100 MILES pull-back, the flight SE and the last move.

## 6. Sub-frame motion blur

- What: after round 8, ch2's fastest move is the drain flight down to the first block at 7.5 % of the camera distance per frame (123.2 s). The swing back peaks at 6.1 % (138.8 s), `{outhere}` at 5.7 % (143.7 s), the dive at 4.9 % (106.6 s), the `{spare}` rise at 4.4 % and the flight SE at 3.9 %. Round 7 had 6.5-7.5 % on the dive, the drain flight, the swing back and `{outhere}`. Turns stay at 2.8 deg per frame or less. Without motion blur these moves still need a phone motion test.
- Ask: optional sub-frame motion blur for terrain shots (n sub-frames of the camera, averaged before the grade).

## 7. Cross-chapter note for the orchestrator and the ch3 builder (not a toolkit change)

- ch2 now ends (t1x) on region `bigisland`, looking SW at the Hāmākua flank from the NE, the same side and subject as ch3's opening low camera: orbit camera `{ lon: -155.33, lat: 19.83, h: 0, d: 95, tilt: 75, heading: 210, fov: 40 }` (ch2.js `CH3_IN`), water falling (`bigDrain`, about -110 m at t1x).
- ch3 opens 1.2 km above the water about 41 km from the flank (heading about 208). The 0.3 s dissolve under the card is now the same subject from the same direction, about half the distance. To make it seamless, ch3 could start its first camera from `CH3_IN` and descend to its low camera over its first 1-1.5 s (or ch2 can end on any camera ch3 names).
