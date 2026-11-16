# Short 6 (P2-08-coming-soon + S11-next-island-under-construction): "Hawaiʻi's Most Optimistic Sign"

| | |
|---|---|
| Release | **D+7**, same clock hour as the long-form (slot 5 of 7; moved from D+8/9, see below) |
| Length | 25.0 s = 750 frames at 30 fps = 10 bars at 96 bpm = 10 sway cycles of 2.5 s |
| The one big number | 3,200 FEET |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps, VE 1.0 throughout; one continuous camera path, no hard cuts |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

## Integrator changes (2026-11-08)

1. **Release D+7** (was D+8 or D+9): it swaps with Short 5, so the two Midway Shorts (4 and 5) sit 4 days apart.
2. **Captions follow the house spec** (shorts_plan.md section 4): Anton cap 80, centred x 460 / y 1515 (the writer's centre y 1496.5 at cap 77 and its flag are replaced by the one house position for all 7). The widest card, OF GENERATIONS., is about 577 px at cap 80 (x 172-748).
3. **Pinned comment added** (owner's OK): see section 8.
4. **Engine safety:** the near-surface ocean pass and periodic water proven in this Short's fork are ported to `engine/www/lab/hawaii/hterrain.js` only as default-off options, after the long-form's chapter builds that use that file are locked or with a pixel regression check (shorts_plan.md section 9). They also serve Shorts 1 and 2.
5. "Plug-hole gurgle" renamed "drain gurgle" in the sound notes (the plug belongs to Short 1).

## 1. Narration and TTS

**Voice:** "Rodney - Clear Educator" (`eY2VJs4Gi8QKG2RV01sS`), model `eleven_v4`, the long-form's settings (longform/ep02-hawaii/script/tts_spec.json, default voice settings). Pass the voice explicitly (tts.py still defaults to Brian). TTS text uses plain ASCII "Hawaii" (lexicon entry "hawaii"); screen text keeps the ʻokina. No bracket or break tags; the number spelled as spoken.

**Segments file** (tts.py, per-segment takes; previous/next text sent automatically). Planned start, then the pause after the segment:

| Seg | Start | Text | Pause / note |
|---|---|---|---|
| s01 | 0.03 | This is the most optimistic sign in Hawaii. | 0.20 |
| s02 | 3.00 | Drain the ocean. | 0.20 |
| s03 | 3.95 | Follow the pole. | 0.40 |
| s04 | 5.10 | Keep going. | 0.50; deadpan, flat |
| s05 | 6.20 | Three thousand two hundred feet down, | 0.40 (THUNK in the gap); speed 0.95 |
| s06 | 8.70 | A volcano. | 0.30; deadpan |
| s07 | 9.65 | The youngest in the whole Hawaiian chain. | 0.55 |
| s08 | 12.45 | Not even born, and already renamed. | 0.70 (the laugh gap) |
| s09 | 15.30 | Back up. | 0.55; deadpan |
| s10 | 16.40 | Grand opening? | 0.50 (the guess beat); bright, mock-cheerful |
| s11 | 17.60 | In thousands of generations. | 1.10 (covers the surge and splash) |
| s12 | 20.60 | Maybe. | about 2.7 (covers the sticker and gust); deadpan, falling |
| s13 | about 23.80 | Which means... | open and rising; see SEAM |

Totals: 48 words, 74 syllables, about 17 s of speech in 25.0 s. The silences are the comic beats and the spectacle.

**Seam take.** Generate this one text, 3 takes (`"take": 1, 2, 3`): "Which means... this is the most optimistic sign in Hawaii."
1. Measure the real silent gap G between "means" and "this" (alignment end/start times plus silencedetect at -45 dB).
2. Cut at a zero crossing in the middle of the gap, with 5-8 ms fades.
3. Place "Which means..." so that it ends at 25.00 - (G - 0.03); the tail silence plus the 0.03 s head offset then equals the take's own gap. Example: if G = 0.53, s13 runs 23.80-24.50.
4. Opener check (a person decides, never an agent): compare the second half of this take with the stand-alone s01. Use the seam take's half as s01 only if it starts clean, with full energy and no trailing afterthought contour; otherwise keep the stand-alone s01 and still use the measured G as the seam gap.
5. Fallback if no take has an open, rising "means": a 3-segment seam file [s12 "Maybe.", s13 "Which means...", s01b "This is the most optimistic sign in Hawaii."]; tts.py then sends s01b as next_text for s13, which keeps "means" open. No code change needed.

**Playback order (25.0 s loop):** "This is the most optimistic sign in Hawaiʻi. / Drain the ocean. / Follow the pole. / Keep going. / Three thousand two hundred feet down, / [THUNK] A volcano. / The youngest in the whole Hawaiian chain. / Not even born, and already renamed. / Back up. / Grand opening? / In thousands of generations. / Maybe. / Which means..." (then the loop returns to the first line)

**Pronunciation** (consistent with longform/ep02-hawaii/script/lexicon.json)
- Hawaiʻi (spoken in s01 and the seam take): TTS text "Hawaii" (U+02BB never goes into TTS text). Target /həˈwaɪ.ʔi/: three syllables, a light glottal catch before the final "ee". Lexicon respelling "hah-WHY-ee" only if a test take collapses to two syllables. Accept the plain English three-syllable huh-WHY-ee; reject huh-WAH-yuh and huh-WAH-ee.
- Hawaiian (spoken in s07): the English adjective, no ʻokina, no respelling; /həˈwaɪ.ən/ "huh-WHY-un"; reject huh-WAH-yun.
- Kamaʻehuakanaloa (tag only, never spoken): lexicon "kah-mah-EH-hoo-ah-kah-nah-LOH-ah", /ˌkɑː.məˌʔɛ.huː.əˌkɑː.nəˈloʊ.ə/; glottal break before EH; main stress on LOH.
- Lōʻihi (tag only, never spoken): "loh-EE-hee", /loʊˈʔiː.hi/, stress on EE.
- Description only: Kīlauea "kee-lao-WAY-ah" (avoid KILL-uh-WAY-uh); Kanaloa "kah-nah-LOH-ah" (a major Hawaiian god: no joke touches this word).
- The lexicon is still DRAFT (not yet checked on wehewehe.org or by a Hawaiian speaker); that gate applies before rendering.

**QC:** ASR-check every take (small.en and medium.en); "renamed", "generations" and "Hawaii" must come back as scripted. Listen on a phone speaker. A person signs off the voice.

## 2. Second-by-second table

**Key cameras** (scene origin: the pole, at the hero-grid summit 18.922N 155.263W)
- K0 (frame 0, and 16.35-25.0): eye 5 m from the pole on bearing 157.13° (SSE), 0.6 m above old sea level; heading 343°, pitch -3°, vfov 30°; pole at x 155-191, waterline y ≈ 1203 (test out/loop25b/f000000.jpg).
- K_ride: same horizontal spot; eye locked 1.6 m above the falling waterline; pitch -12° (test desc2).
- K_foot: 4 m from the pole; eye 1.6 m above the rock; heading 337°, pitch -25°.
- K_wide: eye 18.740N 155.255W, 7.0 km above old sea level; target the summit at the hold level; vfov 50°, lensShiftY 0.35 (test wide2).
- K_low: eye 18.898N 155.2595W, 620 m below old sea level; target 18.935N 155.266W at -700 m; vfov 40° (test klow2: the foot sits visibly on the islet rock).
- K_top: the K0 position with pitch -20° (the rocket's arrival).

**Text safety:** all text inside x 132-849 and y 236-1535 (captions per house spec: Anton cap 80, white, navy edge 0.13 x cap, no box, active word cyan #00E5FF, centred x 460 / y 1515).

**0.00-0.90 · K0, already moving**
- Picture: board sway ±1.5° (2.5 s period), the 12-component wave field, a broken foam collar at the pole. A cream postcard-paper board (#F6F1E4, 3-4 px warm edge, two nails, soft shadow) at x 190-872, y 200-646, nailed to the right side of a yellow #FFD23F / navy #0B1D28 striped pole (0.2 m bands). Deep-blue open ocean fills the lower half; the Big Island a long low silhouette at y ≈ 595-775; clear sky. Rebuilt from: the Ch6 COMING SOON gag (new board, new 3D pole), the HawaiiStage horizon from 30 km, and the new near-surface ocean pass.
- Text: sign (in-world, navy Anton): NEW ISLAND (cap 116, x 232-828, y 236-352) / COMING (cap 96, x 232-559, y 386-482) / SOON (cap 96, x 232-448, y 512-608). Captions THIS IS THE (0.03) / MOST (0.70) / OPTIMISTIC (0.95).
- VO: 0.03 "This is the most optimistic sign in Hawaiʻi."
- Sound: the decay of the seam slap+creak (attack at 24.92; one event straddles the cut). Wave bed, a seamless 25.0 s loop. Music bar 1 (sparse pizzicato and marimba).

**0.90-1.80**
- Picture: a swell slaps the pole; spray bursts to the board's lower edge (the first visual event).
- Sound: spray splash at 0.90.

**1.80-3.00**
- Picture: motion inside the hook: the sea starts sliding away beneath the sign (0 to -6 m, ease-in). The foam collar slides down and out of frame by 2.1. The wet striped pole lengthens below the board and foam streaks start to curl. The camera holds K0.
- Text: captions SIGN IN (1.80) / HAWAIʻI. (2.20-3.00).
- VO: (hook ends 2.80)
- Sound: a soft drain gurgle at 1.80, kept under 300 Hz and 12 dB below the voice.

**3.00-3.95**
- Picture: the drain kicks in: the water accelerates (-6 to -40 m) and the striped pole streams out below the board.
- Text: captions DRAIN THE / OCEAN.
- VO: 3.00 "Drain the ocean."
- Sound: a big comic gurgle, then a falling whirr.

**3.95-5.10**
- Picture: tilt -3° to -12° and drop into K_ride; the board exits the top by 4.3. At 4.30 the odometer (T.slot) appears and rolls with the true waterline depth, rounded to 10 ft. Spiral foam streaks converge on the pole (a drain swirl, so it cannot read as the pole being pulled up). The Big Island band at the top grows a dark basalt apron (test desc2).
- Text: counter: Anton cap 240, yellow #FFD23F with a navy edge, right-aligned x 232-849, y 600-840; FEET: Barlow Condensed 800, cap 96, white, x 581-843, y 876-972. Captions FOLLOW THE / POLE.
- VO: 3.95 "Follow the pole."
- Sound: a clunk at every joint collar (every 160 ft), a soft tick under each.

**5.10-6.20**
- Picture: the ride peaks: stripes motion-blur, the pole creaks and flexes, the swirl tightens.
- Text: captions KEEP / GOING.
- VO: 5.10 "Keep going." (deadpan)
- Sound: clunks speed up into a rattle.

**6.20-8.35**
- Picture: deceleration. A dark rock shadow rises under the water from 7.0. The counter crawls 3,180... 3,190 and lands 3,200 on "down" (8.10).
- Text: 3,200 FEET (the only big number; the counter carries the number words, so captions show only DOWN, 7.80-8.35).
- VO: 6.20 "Three thousand two hundred feet down,"
- Sound: clunks slow; the last tick on "down".

**8.35 · THUNK**
- Picture: the water reaches the summit (-975 m after the summit correction; see renders) and the ride stops 1.6 m above black pillow lava. Counter punch (scale 1.08 to 1.0); 4-frame camera shake.
- Text: 3,200 FEET holds.
- Sound: thunk_heavy (energy under 300 Hz). The music stops dead for 0.35 s.

**8.70-9.65**
- Picture: tilt to K_foot: the pole's foot planted in glossy black pillow lava, water sheeting off the rock. The counter slides up and out (8.9-9.2).
- Text: caption A VOLCANO.
- VO: 8.70 "A volcano." (deadpan)
- Sound: run-off hiss.

**9.10-11.70**
- Picture: one eased crane and pull-back to K_wide while the water falls the last 75 m (-975 to -1,050 m, eased out by 10.2). The summit becomes a small dark crescent islet in turquoise shallows. The Big Island massif fills the top third, green above its old shoreline and dark basalt below (test wide2). Rebuilt from: the long-form drain stage plus the Ch6 cone.
- Text: captions THE YOUNGEST / IN THE WHOLE / HAWAIIAN / CHAIN.
- VO: 9.65 "The youngest in the whole Hawaiian chain."
- Sound: music re-enters softly and lifts at the reveal; soft whoosh.

**11.70-12.50**
- Picture: an eased swoop to K_low: the islet in the foreground, the pole standing on its rock and rising to near the top of frame, the Big Island across the water (test klow2). At 12.25 a cream paper tag on a string swings in on the pole, front side up.
- Text: tag front LŌʻIHI (Anton cap 96, 231 px, centred; Ō from the latin-ext subset). Caption NOT EVEN (12.45).
- VO: 12.45 "Not even born,"
- Sound: paper-flap motif as the tag swings in.

**12.50-14.60**
- Picture: at 13.50-13.80 the tag flips over (a paper turn about its vertical axis) to the new name. The tag is cream paper at x 112-880, y 560-742, tilted 2°. The string runs from an eyelet at (850, 592), outside the text, up to the pole, never across the letters.
- Text: tag back KAMAʻEHUAKANALOA (Anton cap 78, x 138-829, y 622-700; the ʻokina side gaps tightened by -0.03/-0.035 em so it reads as one word). Captions BORN, / AND ALREADY / RENAMED.
- VO: "...and already renamed." (ends 14.60)
- Sound: a soft paper flip, with no comic sting on the name.

**14.60-15.30**
- Picture: the laugh gap: a slow 2% push; the tag sways. The tag is on screen 12.25-15.75 (3.5 s), its new-name side 1.95 s.
- Text: RENAMED. holds.
- Sound: the music lifts one bar.

**15.30-16.35**
- Picture: 15.30 "Back up." At 15.75 the rocket-up: one eased arc from K_low up the pole to K_top at old sea level, with 6-8 sub-frames of motion blur. The islet drops away below; the tag streaks out of frame.
- Text: caption BACK UP.
- VO: 15.30 "Back up." (deadpan)
- Sound: a rising whoosh and a pole twang.

**16.35-17.60**
- Picture: the longest smooth move: a tilt from K_top (-20°, looking down the empty pole into the drop) up to K0 pitch -3° over the lowered sea (test vert2). No foam collar; the pole runs out of the bottom of frame; the Big Island's dark exposed apron shows below the board. The board wobbles ±4° from the stop. The pause 17.10-17.60 is the guess beat under the tilt.
- Text: sign NEW ISLAND / COMING / SOON. Captions GRAND / OPENING?
- VO: 16.40 "Grand opening?"
- Sound: board creak; the music holds one note through the pause.

**17.60-19.80**
- Picture: a time-lapse gag: clouds race across the sky (clear to clear, light constant, no flashing). The board's sway speeds up by exactly 4 extra cycles. At 18.10 the sea surges back up from 3,400 ft below: the apron floods along the horizon (18.1-19.2), then the near surface rushes up the frame, arriving at the frame-0 waterline at 19.80 with spray on the board's lower edge (19.80-20.20).
- Text: captions IN THOUSANDS / OF GENERATIONS.
- VO: 17.60 "In thousands of generations."
- Sound: time-lapse wind whoosh (-14 dB under the voice); a surge roar from 18.10 (a reversed gurgle into a rush); a splash at 19.80.

**20.20-21.15**
- Picture: a deadpan beat: spray falls back, the sway returns to normal. Visually back to frame 0: still just a sign in the sea.
- Text: caption MAYBE. (20.60-21.90).
- VO: 20.60 "Maybe."
- Sound: waves only.

**21.15-23.35 · PAYOFF**
- Picture: a yellow paper sticker slaps on right after SOON, so the sign reads COMING SOON-ISH, with a small bounce. A 1% push in and back out returns to K0 exactly by 23.3. The sticker is on screen 21.15-23.35 (2.2 s).
- Text: sticker -ISH: Anton cap 96, navy on yellow #FFD23F paper, tilted 6°, text at about x 490-658, y 506-602.
- Sound: a sticker smack plus a 2-note music button (in the gap after the line).

**23.35-23.70**
- Picture: a gust peels the sticker off; it flutters out of the top of frame by 23.70. The gust's board shake decays to 0 by 24.4.
- Sound: paper-flap motif plus a gust, both ducked -10 dB from 23.80.

**23.80-24.50**
- Picture: hold at K0.
- Text: caption WHICH MEANS... (23.80-25.00).
- VO: 23.80 "Which means..." (open, rising; its exact start = 25.00 - (G - 0.03) - its duration)
- Sound: splash and gust tails ducked under the voice.

**24.50-25.00**
- Picture: settle. From 24.50 the picture is the exact frame-0 state: camera K0, water at 0, no sticker or spray, sway phase 0, wave field periodic. Cut after frame 749.
- Text: the sign only, then THIS IS THE at the wrap.
- Sound: bar 10 resolves into bar 1. The single seam slap+creak attack at 24.92, decaying across the cut.

**Water level** (grid metres, after the summit correction)

| Time | Level |
|---|---|
| 0-1.80 | 0 |
| 1.80-3.00 | 0 to -6 (ease-in) |
| 3.00-3.90 | -6 to -40 |
| 3.90-8.35 | -40 to -975 (fast mid-ride, crawling at the end) |
| 8.35-10.20 | -975 to -1,050 (ease-out) |
| 10.20-18.10 | hold -1,050 |
| 18.10-19.80 | -1,050 to 0 (ease-in surge) |
| 19.80-25.00 | 0 |

**Deviations flagged for the owner:** length 25.0 s, not the panel's 22.5 (the task sets a 25 s floor; the extra time goes to the ride and the deadpan timing, not to holds). K0 over the lowered sea holds at pitch -3°, not -18° (at -18° the far sea read as a flat blue wall, test vert); the -20° look-down plays only as the rocket's arrival, and the tilt-up covers the guess pause.

## 3. Hook

- 0.03 s VO: "This is the most optimistic sign in Hawaiʻi." (8 words, 13 syllables, ends 2.80). A flat statement about an absurd prop: no question and no menu.
- **Frame 0 is the thumbnail, already moving:** a cream postcard-paper board reading NEW ISLAND / COMING / SOON (navy Anton, caps 116/96/96, upper third, x 232-828, y 236-608), nailed to a yellow/navy striped survey pole rising out of open, deep-blue ocean about 19 miles off Kīlauea's coast, with a broken foam collar at the waterline; the Big Island's long low silhouette on the horizon; nothing else in frame. The hook phrase is the biggest line. Sound off, the 4-word sign asks the question itself: what new island, out here?
- **Measured on the real engine frame** (near-surface ocean pass, board composited at final size): mean luma 146; lower half 98.7% blue-dominant; pale-grey pixels 1.8% (against 33% in the old previz that read as a beach); tan 0.5%; near-black 0.4%.
- **Motion inside the hook:** 0.90 a swell slaps the pole and spray hits the board; 1.80, under SIGN IN HAWAIʻI., the sea starts sliding away beneath the sign, the foam collar drops out of frame and the wet striped pole streams out of the water; 3.00 "Drain the ocean." with the gurgle; 3.95 the camera dives after the waterline. The thumb sees the spectacle begin before 2 s.

## 4. Payoff

Three stacked payoffs, each new information, the last closest to the loop.
1. **Depth** (the strongest stretch). The camera rides the falling waterline down the striped pole, through a converging drain swirl and joint clunks speeding into a rattle, with Rodney's deadpan "Keep going." The odometer crawls 3,180... 3,190 and lands 3,200 FEET on "down". THUNK, the music cuts dead: black pillow lava at the pole's foot. "A volcano." One crane and pull-back shows the summit as a tiny dark crescent islet in turquoise shallows under the giant Big Island massif: "The youngest in the whole Hawaiian chain."
2. **New twist** (true, unspent). Low beside the islet a paper tag swings in on the pole reading LŌʻIHI and flips over to KAMAʻEHUAKANALOA: "Not even born, and already renamed." Then "Back up." completes the narrator's command motif (Drain the ocean / Follow the pole / Keep going / Back up), and the camera rockets 3,400 ft up the pole to the sign, now hanging over the lowered sea.
3. **Time answer and sticker button.** "Grand opening?" (a 0.55 s guess beat under the tilt-up) "In thousands of generations." (the USGS's own phrase; new wording against the long-form's "thousands of years from now") over a time-lapse: clouds race, the sea surges back and splashes the board; generations pass and it is still just a sign in the sea. Deadpan "Maybe." A yellow -ISH sticker slaps on: COMING SOON-ISH. A gust peels it off (a second micro-gag that also resets the frame), and "Which means..." hands back to the opening claim.

## 5. Loop check

**Last line into first line:** "...Grand opening? In thousands of generations. Maybe. Which means... this is the most optimistic sign in Hawaiʻi. Drain the ocean. Follow the pole..." One natural sentence: "Which means..." (open, rising) completes into the opening statement; a first-time viewer hears a clean claim.

**The seam gap is a real gap, not a guess:** generate "Which means... this is the most optimistic sign in Hawaii.", measure G, place s13 so that tail silence + 0.03 s head offset = G (s13 ends at 25.00 - (G - 0.03)), cut at a zero crossing with 5-8 ms fades; the opener check is done by a person.

**Last frame against first frame**
- Same camera at both ends: K0 (5 m from the pole on bearing 157.13°, eye 0.6 m, heading 343°, pitch -3°, vfov 30°), static from 23.3 (the sticker push returns exactly).
- State by 24.50: water at 0 since 19.80; spray gone by 20.20; no wet shading (the pole shader has no wetness term and the splash is particles only); sticker out of frame by 23.70; gust shake at 0 by 24.4; sway 2.5 s period with 10 whole cycles (the rocket wobble decays to 0 by 19.5; the time-lapse adds exactly 4 extra cycles); clear sky at both ends.
- Captions switch hard by design (WHICH MEANS... until 25.00, THIS IS THE from 0.03); seam metrics are measured on the picture layer before captions.
- **Measured on real engine frames**, after making every time-driven water term periodic (waves at periods 25/n s; micro chop, foam collar, swirl and large-scale slicks driven by cos/sin(2πt/25)), grain off: frames 0 vs 749 (first vs last) MAE 1.91/255; 749 vs 750 (an ordinary frame step) 1.91; 0 vs 750 (one full period) 0.002. The seam step equals an ordinary step: an invisible join. With grain on it was 2.66 against a 2.34 ordinary step. Gate ≤ 5.
- Found and fixed: the stock HawaiiStage water drifts linearly in time (fbm offsets time*0.004 and time*0.03), which breaks any loop (1.43-1.88 MAE over one period before the fix). This fix is shared with every looping Short (shorts_plan.md section 5B).

**Sound:** the wave bed is one seamless 25.0 s loop, crossfaded tail into head. Music 10 bars at 96 bpm; bar 10 resolves into bar 1. One slap+creak straddles the cut (attack at 24.92, decay through 0.35); no second slap, so no stutter. Splash and gust tails ducked -10 dB under "Which means".

**QC gate on the final render:** first/last MAE ≤ about 5/255 on the full composite with the board; concatenate the Short with itself and run temporal_scan.py (no "cut" or "flash"); audio_scan.py: no click at the seam.

## 6. Facts

1. **"Three thousand two hundred feet down"** and the counter 3,200 FEET. Spine #16 (summit 975 m / 3,200 ft below sea level). USGS HVO Volcano Watch, 27 Jan 2022 (the spine #16 URL), re-fetched 2026-11-08: "rising to 3,189 ft (975 m) below sea level". Brief unit table: -975 m = 3,200 ft. With the summit correction the counter shows the true waterline depth in feet, rounded to 10, at every frame, and lands 3,200 at -975 m (3,199 ft). The ETOPO grid smooths the summit to -1,023/-1,026 m.
2. **"A volcano."** Spine #16.
3. **"The youngest in the whole Hawaiian chain."** Spine #16. USGS, same page: "the youngest volcano in the long line of the Hawaiian-Emperor chain".
4. **"Not even born, and already renamed."** Spine #16 (renamed 2021). USGS, same page: "in July 2021, Lōʻihi Seamount was renamed Kamaʻehuakanaloa by the Hawaii Board on Geographic Names"; the name Lōʻihi dates from 1955. "Not even born" is a metaphor for not yet emerged as an island (spine #16: "it will be millennia before" it emerges). "already renamed" does not claim how many times.
5. **"Grand opening? In thousands of generations. Maybe."** VERIFY closed by the writer on 2026-11-08 on the spine #16 URL: "In thousands of generations, perhaps our descendants will witness Kamaʻehuakanaloa ... finally emerging and forming a new island." (from a fetched page summary; recheck the exact wording on the page before quoting it anywhere). "Maybe" = USGS's "perhaps"; "generations" is USGS's own word; consistent with spine #16 "millennia" and the brief's "thousands of years at least". Add it to the ep02 ledger before lock.
6. **Sign NEW ISLAND / COMING SOON.** A joke prop, hedged in the narration ("Maybe.") and on the sign itself (the -ISH sticker). Spine #16: say it "could" become the next island; the description says "could one day rise above the sea as a new Hawaiian island".
7. **Tag LŌʻIHI to KAMAʻEHUAKANALOA.** Spine #16 (formerly Lōʻihi, renamed 2021). Screen only, never spoken.
8. **"This is the most optimistic sign in Hawaiʻi."** A joke about our own prop; no factual claim.
9. **"Drain the ocean." / "Back up."** Imperatives that frame the drain as a thought experiment; no claim. The description says "lowering the sea is a thought experiment".
10. **Visuals.** At about -1,050 m (corrected grid) the summit shows as a small crescent islet; nothing is said or shown about its shape as a future island (never "this is what the island will look like"). The same DEM has a bench about 24 km north at about -1,000 m that also surfaces: re-run sill.py and the flood-fill on the production grid. VE 1.0 in every shot.
11. **Description lines.** "About 19 miles off Kīlauea's coast", "youngest volcano in the Hawaiian-Emperor chain", "millennia", renamed July 2021 and "the reddish child of Kanaloa" are all from the same USGS page; the description writes "perhaps thousands of generations" as a paraphrase, not a quote.

Never said: erupting, active, 1996, earthquake, Everest, 56,000 ft, dent. One big number (3,200). No on-screen sources. Open VERIFY items: none in narration or on screen once item 5 is in the ledger.

## 7. Renders: new for this Short vs reused

**Proven in the writer's fork** (scratchpad; the repo engine is untouched): /tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/short06v2/ with www/s06/hterrain_s06.js (a fork of engine/www/lab/hawaii/hterrain.js; patch.py plus inline edits), www/s06.html (the proof page; render with `node engine/still.cjs --www <that www> --page s06.html --w 1080 --h 1920`), out/*/f*.jpg (frames), mock_v2.py (compositor), m_phone390.jpg (6 key frames at phone width), m_sheet_guides.jpg (safe-zone guides), m_f0.jpg, m_desc.jpg, m_wide.jpg, m_tag.jpg, m_grand.jpg, m_payoff.jpg.
1. **Near-surface ocean pass** (built and measured). Root cause of the beach-like frame 0: HawaiiStage's camera near plane is 0.5 km, so all water within 500 m was clipped and the seabed 1 km down showed through; the skirt water grid's 4.4 km cells also mis-place the curvature drop by up to 0.38 m (matters at a 0.6 m eye). Fix A, split-depth render: a far pass (near plane 1.2 km), clear depth, then a near pass (0.2 m to 1.2 km), sky off. Fix B: a 3x3 km near water patch at 2.5 m cells, re-centred under the camera each frame (the water vertex shader takes lon/lat from the world position, so both water meshes share one material). Fix C: metre-scale waves, 12 directional deep-water components with periods 25/n s (n = 5-58, wavelengths about 0.25-39 m), faded by pixel footprint, plus periodic micro chop and turquoise crests. Fix D: a broken foam collar at the pole and log-spiral drain-swirl foam streaks. Fix E: every time-driven water term on a circle (cos/sin 2πt/L). Fix F: the scene origin at the pole for float precision. Results: frame 0 lower half 98.7% blue, 1.8% pale grey (was about 33%), mean luma 146; descent (desc2) and K0 over the lowered sea (vert2) show no exposed seabed.
2. **The 3D pole:** 975 m plus 1.45 m above sea level, 2.5 cm radius, 0.2 m yellow/navy bands, joint collars every 48.77 m below water only; 4096 height segments (one segment made the band edges jagged).
3. **Dark-basalt grade on all exposed rock:** basalt 0.017/0.017/0.020, sediment 0.027/0.025/0.024 (linear); key frames measure pale grey 1.0-1.8% and tan 0.4-1.2%.

**Still to build**
1. Port 1-2 into engine/www/lab/hawaii/hterrain.js as default-off options (split, nearPlane, the near patch, the near-wave uniforms, the pole, periodic drift), with the long-form safeguards in shorts_plan.md section 9.
2. Pillow-lava patch at the pole's foot for the THUNK and K_foot (the 100 m DEM alone gives a flat dark plane, test thunk2): about 40 m radius of instanced lumpy ellipsoids 0.5-1.5 m across, dark basalt with glassy rinds, wet sheen, run-off sheets; built in the engine, no generators.
3. Summit correction: a smooth bump (Gaussian sigma about 1.5 km, peak +48 m) on the summit so the grid maximum equals the USGS 975 m; then pick the islet hold level (about -1,050 m) and gate it with sill.py and the flood-fill. If the owner prefers raw data, key the counter to the grid summit instead.
4. Props: the board (series postcard paper #F6F1E4, text baked as a 4K texture, nailed to the pole, sway driven by a phase function); the -ISH sticker (yellow paper, slap and peel); the two-sided name tag (LŌʻIHI / KAMAʻEHUAKANALOA, flip, outside eyelet, string); spray particles (gone 0.4 s after each splash); time-lapse sky clouds (clear to clear); in wide shots the pole drawn at least 8 px wide in screen space (the proof cheated with 40 m and 4.5 m radii in wide2 and klow2).
5. One continuous camera spline: K0 → K_ride → THUNK → K_foot → crane/pull-back to K_wide → swoop to K_low → rocket to K_top (6-8 sub-frames of blur) → tilt to K0; cyclic at the ends; eased on the destination keys.
6. UI layer: counter (T.slot, Anton cap 240); captions (house spec); load both latin and latin-ext subsets (ʻ U+02BB in latin, Ō U+014C only in latin-ext; checked with fontTools).
7. Render: render_chunks.py --w 1080 --h 1920 into the Short's own chunk directory; then the loop-seam QC.

**Reused as-is:** HawaiiStage and its baked data (ETOPO 2022 15", Terrain Tiles, MODIS colour, AO); the 'day' look and the 'turq' water; the long-form's live drain mechanic; the Ch6 young-cone location and the COMING SOON idea; the Anton/Barlow type system and the T.slot odometer; library cues thunk_heavy, tick_counter, whoosh, the paper-flap motif, gurgle, riser.

**Clone-look check:** no caption box, no curved arrows, no dashed sea-level line (the sign marks sea level); dark basalt and turquoise/deep blue, never a tan basin; no "taller than Everest".

**Probe** (ytsearch, 2026-11-08): "hawaii most optimistic sign" returns zodiac Shorts only; "loihi renamed kamaehuakanaloa": best Short 9 views; "next Hawaiian island" Shorts sit at 1.5-2.3K. The premise is unclaimed but not proven to pull views.

## 8. Title, description, link

**Title:** Hawaiʻi's Most Optimistic Sign (30 characters; the proper noun first; the clone-word regex finds no match; whole-word AI check over title, description, narration, captions and on-screen strings: 0 hits).

**Description (paste-ready):**

> This sign hangs on a pole about 3,200 feet long. At its foot is the summit of Kamaʻehuakanaloa, the youngest volcano in the Hawaiian-Emperor chain, about 19 miles off Kīlauea's coast on Hawaiʻi Island.
>
> It could one day rise above the sea as a new Hawaiian island, but not soon: USGS scientists say it will take millennia, perhaps thousands of generations.
>
> Until July 2021 it was called Lōʻihi Seamount. The Hawaiʻi Board on Geographic Names renamed it Kamaʻehuakanaloa, "the reddish child of Kanaloa."
>
> How much of the Big Island is under the waves? The full film: Why Can't You See Most of Hawaii? (Look Down)
>
> The sign is a joke, and lowering the sea is a thought experiment. The depth is real: the summit lies about 3,200 feet (975 m) below sea level.
> Source: USGS Hawaiian Volcano Observatory, Volcano Watch (January 27, 2022). Seafloor and terrain: NOAA NCEI ETOPO 2022; Terrain Tiles (Mapzen and its data sources). Imagery: NASA GIBS (MODIS).
>
> #Hawaii #volcano #geography

**Link:** in YouTube Studio the owner sets the Short's Related video to "Why Can't You See Most of Hawaii? (Look Down)" (only with his OK; nothing is uploaded or changed by an agent). This Short feeds the film's Ch6 newborn-volcano beat without spending the film's payoff (no 56,000 ft, no dent, no Everest); its time line ("In thousands of generations. Maybe.") differs from the film's ("thousands of years from now").

**Pinned comment** (integrator addition; owner's OK): "Should the sign say COMING SOON, or COMING SOON-ISH? Be honest."

**Before upload:** re-run the whole-word check (AI|A.I.|artificial|synthetic|generated|generative|TTS|ElevenLabs...) and the clone-title regex on the final strings; confirm the related video is live; never credit or name the voice or music tool.

**For the 7-Shorts table:** hook type: absurd prop plus a superlative statement; opening shot: a sea-level close-up of a paper sign on a striped pole in open ocean; payoff device: rename-tag flip, then a time answer, then the -ISH sticker; loop line: "Which means... / this is the most optimistic sign in Hawaiʻi."

**Playbook lessons for the parent to record:** stock HawaiiStage cannot render water within 500 m of the camera (near plane 0.5 km), so near-surface shots need the split pass; every time-driven shader term in a looping Short must be periodic (cos/sin 2πt/L): measured one-period MAE dropped from 1.43-1.88 to 0.002.

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 70. All 8 must-fixes are in: the near-surface ocean pass built and measured (frame 0 now open deep-blue sea); the TTS seam (ellipsis take, measured gap, opener check, fallback); the 15.30-18.10 dead zone removed ("Grand opening?" now at 16.40); the name tag's string from an outside eyelet and the ʻokina spacing tightened; the pole on exposed rock in K_wide and K_low (re-check after sill.py); one slap+creak straddling the seam and the splash and gust ducked; NEW ISLAND the biggest sign line and the drain starting at 1.80; dark basalt on all exposed rock.
