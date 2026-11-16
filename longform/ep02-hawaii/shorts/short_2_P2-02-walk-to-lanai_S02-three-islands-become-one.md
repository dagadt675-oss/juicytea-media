# Short 2 (P2-02-walk-to-lanai + S02-three-islands-become-one): "You Can't Walk From Maui to Lānaʻi (Unless...)"

| | |
|---|---|
| Release | **D+1**, same clock hour as the long-form (slot 2 of 7) |
| Length | 25.000 s (750 frames); 11 bars / 27.5 s if the real take does not fit |
| The one big number | none (zero numbers on screen or spoken) |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps; music 96 BPM, 10 bars, built to loop |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

Times are estimates calibrated on Rodney's measured take (audio/rodney_test/timing.json). Every picture event is tied to the quoted word and moves with it once the real take is aligned.

## Integrator changes (2026-11-08)

1. **The bath plug and chain became a chest freezer.** "Unless you pull the plug." became **"Unless you put some ocean in the freezer."**, and "The Ice Age pulled this plug for real." became **"The Ice Age did this for real."** Reasons:
   - Short 1, released the day before, is built on a bathtub plug and chain at a shoreline with a paper figure. Two plug Shorts on consecutive days break the playbook's distinctness rule (no shared opening shot or device) and would look templated.
   - "Pull the plug on the ocean" is the farmed clone premise (23M, 10M, 214K and at least 8 copies). Speaking it in the hook put us inside that family.
   - The freezer is the honest cartoon of the real mechanism: in an ice age, water leaves the ocean and is stored as ice on land, and the sea falls (C12-04). "The Ice Age did this for real" is now literal, VERIFY (g) on the figurative plug wording is closed, and the loop rhymes ("the ice melted" into "the freezer").
   - Every beat, gag, camera and loop mechanic of the writer's version is kept; only the prop, two lines and the SFX change. Times from 3.4 s to 20.5 s moved by +0.15 to +0.55 s and three VO holes shrank so the seam stays at 25.0 s.
   - If the owner prefers the plug version, it can be restored by swapping these lines and props back, and Short 1 would then need a different device.
2. **TTS text uses the lexicon respellings** (lah-NAH-ee, moh-loh-KAH-ee) instead of an alias dictionary, the series method (lexicon.json: no U+02BB or kahakō in TTS text until a test render passes). Maui is sent plain; never "MOW-ee" (lexicon).
3. **All text at x ≤ 849** (channel rule): the LĀNAʻI slip moved to x 430-840, the Shot B MAUI slip to x 560-840, the IT HAPPENED stamp to x 110-845.
4. **Burned-in captions added** in the house style (shorts_plan.md section 4), suppressed while the NOBODY / WALKED IT slip shows the same words. Our own SRT with native spellings is also uploaded.
5. **ʻOkina glyph:** the LĀNAʻI and MOLOKAʻI slips are Barlow Condensed 800, whose U+02BB draws as a backtick. type.js draws Barlow's U+2018 glyph for U+02BB (house rule); the text stays U+02BB.
6. Lānaʻi is spoken 3 times per loop (the draft said 4).

## 1. Narration and TTS

**Text sent to TTS** (one request, rotated so the loop seam is one natural take). Voice "Rodney - Clear Educator" (`eY2VJs4Gi8QKG2RV01sS`), model `eleven_v4`, the locked long-form settings (`"settings": {}`). Generate 3 takes (`"take": 1, 2, 3`) and pick one by the listen test below.

> Then the ice melted, the sea crept back, and ever since, you can't walk to lah-NAH-ee. Unless you put some ocean in the freezer. Lah-NAH-ee snaps onto Maui. Moh-loh-KAH-ee snaps onto lah-NAH-ee. Sorry, ferry. You're grounded. The Ice Age did this for real. The catch? Nobody ever walked it. People hadn't made it here yet.

As heard and captioned (caption_map spellings): "You can't walk to Lānaʻi. Unless you put some ocean in the freezer. Lānaʻi snaps onto Maui. Molokaʻi snaps onto Lānaʻi. Sorry, ferry. You're grounded. The Ice Age did this for real. The catch? Nobody ever walked it. People hadn't made it here yet. Then the ice melted, the sea crept back, and ever since,"

55 words, all written new for this Short. It reuses none of the long-form's lines ("Drop the sea four hundred feet", "They become one island", "That's not a what-if", "No ferry needed"). Estimated speech about 20.3 s (about 0.19 s per syllable mid-sentence, 0.5-0.85 s on sentence-final words, comma pauses 0.08-0.15 s).

**How the take is placed (build to the real take)**
1. Align the chosen take for word timings. Cut it at sentence ends, and inside the comma pause after "since,".
2. Seam: "you can't walk to Lānaʻi." starts at 0.05. "...ever since," ends so that the take's own comma pause spans the seam, plus at most 0.1 s of room tone: about 0.16 s at the end and 0.05 s at the start.
3. Lines are placed only by adding or trimming silence between sentences. No time-stretching.
4. Planned placement (estimates; every picture event is anchored to a word):

| Line | Planned time |
|---|---|
| VO1 "You can't walk to Lānaʻi." | 0.05-1.66 |
| VO2 "Unless you put some ocean in the freezer." ("Unless" before 2.2 s) | 1.86-4.05 |
| VO3 "Lānaʻi snaps onto Maui." | 4.95-6.79 |
| VO4 "Molokaʻi snaps onto Lānaʻi." | 6.99-9.17 |
| VO5 "Sorry, ferry." then "You're grounded." | 10.07-11.50, 12.05-13.03 |
| VO6 "The Ice Age did this for real." | 13.33-15.26 |
| VO7 "The catch? Nobody ever walked it." | 15.61-18.24 |
| VO8 "People hadn't made it here yet." | 18.54-20.47 |
| VO9 "Then the ice melted, the sea crept back, and ever since," | 21.28-24.84 |

   Holes between lines: 0.20, 0.90 (the ocean pours into the freezer), 0.20, 0.90 (rim and crash zoom), 0.55 (sad toot), 0.30, 0.35, 0.30, 0.81 (the comic awkward beat). None is over 1.2 s.
5. If the real take runs long: shrink the 0.90, 0.90 and 0.81 holes to 0.8, 0.8 and 0.6. If speech plus the minimum holes still exceeds about 24.8 s, go to 11 bars (27.5 s) and give the extra time to those three holes (at most 1.2 s each) and to G1 (+0.5 s). If the take runs short, grow those three holes up to 1.2 s.
6. Choosing the take (phone speaker): every Hawaiian name right; "since," keeps a continuing comma tone; played cold from 0.00, "You can't walk to Lānaʻi." sounds like an opening line, not half a sentence.

**Pronunciation** (lexicon.json; check every entry on wehewehe.org, and with a Hawaiian speaker if possible, before the render)
- Spoken by Rodney:
  - Lānaʻi (3 times) → TTS "lah-NAH-ee" (lexicon alt "laah-NAH-ee"). Hawaiian [laːˈnɐʔi]: long first "ah", stress on NAH, a light glottal catch before the final "ee". Never "luh-NYE".
  - Molokaʻi → TTS "moh-loh-KAH-ee" ([ˌmoloˈkɐʔi]). Four syllables; never "MOLLY-kai" or "moh-loh-KYE".
  - Maui → plain "Maui" (English voices say it right), target /ˈmaʊ.i/; fall back to "MAO-ee" only if the listen test fails. Never "MOW".
- On screen only: LĀNAʻI, MAUI, MOLOKAʻI (as above).
- Description, pinned comment and tags only: Hawaiʻi "hah-WHY-ee" ([həˈwɐiʔi]); Kahoʻolawe "kah-hoh-oh-LAH-veh"; Maui Nui "MAO-ee NOO-ee" ("Big Maui"); ʻAuʻau "ao-AO" ([ʔɐuˈʔɐu]; the Grigg paper title prints "Au'au").
- Production place names, never spoken (rule-derived; add to the lexicon and check on wehewehe.org): Launiupoko "lao-nee-oo-POH-koh"; Lahaina "lah-HIGH-nah"; Olowalu "oh-loh-WAH-loo"; Lānaʻihale "lah-NAH-ee-HAH-leh"; Kalohi "kah-LOH-hee"; Pailolo "pie-LOH-loh".
- ASR-check the take (small.en, medium.en) through caption_map: "Lānaʻi", "Molokaʻi", "Maui" and "freezer" must come back as scripted.

## 2. Second-by-second table

Shared rules for every shot: one sun (azimuth ~110°, elevation ~20°, warm low light); turquoise water with depth gradient and foam rims; exposed seabed in real tones (dark wet basalt near the old coasts, slate-olive carbonate on the shelves, dark reef pinnacles); turquoise pools only in the real enclosed basins; tan ≤ 10% of the frame (gate.py); no gull sounds (gulls are rare visitors in Hawaiʻi). Text: everything inside x 72-849, y 200-1500, except captions (house spec). Paper slips: dark ink #14202A on off-white #F6F1E4, tilted 2-4°, soft shadow. No black boxes, arrows, dashed lines, odometer or number anywhere.

**0.0-1.0 · SHOT A = FRAME 0**
- Picture:
  - NEW shore-level vertical camera. ONE continuous render from t = -2.2 to 5.05; its first 2.2 s become 22.80-25.00.
  - Location: Launiupoko, West Maui, about 20.842N 156.650W, chosen over Olowalu (site of the 1790 massacre). VERIFY it is outside the 2023 burn area. No structures in frame.
  - Camera 2.2 m up, 9 m behind the tourist, heading 258.5° (Lānaʻihale at bearing 261°, 23 km), pitch -7°, vFOV 32°, pushing in 2% per 2.7 s.
  - Horizon at about y 550. Lānaʻi's ridge across the whole horizon, peak near x 700, y 405. Lahaina (bearing 323°), Molokaʻi and Kahoʻolawe out of frame.
  - The paper tourist (the long-form 0:23.6 cut-out, red aloha shirt) at the waterline: feet at x 470, y 1350, head at y 700 (34% of frame height), three-quarter view facing frame-left, suitcase in his left hand.
  - THE FREEZER: a white chest freezer (paper cut-out of a real photo) stands in the swash just left of him, x 120-420, y 1080-1340. Its lid card is hinged at the back and propped 25° open by his right hand; a curl of frost spills over the lip (loop-clock sprite). He leans in 12°, peering into it. At 390 px it reads as a man with a suitcase holding open a freezer in the surf.
  - A swash covers his front foot and the freezer's base (peak 0.15).
  - A paper ferry bobs 400 m out (x 560-760, y 515-600; 2.5 s bob).
- Text: LĀNAʻI paper slip (Barlow Condensed 800 cap 90, small Myth Juice stamp in the corner, tilted -3°) pinned above the peak at x 430-840, y 230-360. MAUI slip (cap 90) at x 520-780, y 1330-1450 beside his feet. Captions from 0.05: YOU CAN'T / WALK TO / LĀNAʻI.
- VO: "You can't walk to Lānaʻi." (0.05-1.66; "Lānaʻi" at 0.81)
- Sound: surf bed (loop). Bar 1: a caper theme of pizzicato strings, upright bass and a brushed tick (not a ukulele travel bed). Swash hiss peaks at 0.15.

**1.0-2.0**
- Picture: 1.00 the compressor kicks on: the cabinet shudders, its lid light flicks on, a frost puff rolls out. 1.20 THE ANOMALY: the backwash keeps going, too far and too fast, and a thin rope of seawater peels off the swash, curls up the freezer's side and pours over the lip into it. 1.86 he plants his feet and braces the lid wider.
- Text: LĀNAʻI + MAUI; caption UNLESS from 1.86.
- VO: "...Lānaʻi." ends at 1.66; "Unless..." starts at 1.86.
- Sound: compressor THUNK and hum (1.00) with a bass "boing". A slurp enters low at 1.20, clearly audible by 1.30. One sour bass note at 1.25.

**2.0-3.0**
- Picture: 2.40 on "put": he flings the lid fully open; it bangs against its hinge stop with a frost blast. 2.95 on "ocean": the rope swells into a thick twisting arc of seawater from the receding sea up into the freezer. The sea starts falling fast.
- Text: LĀNAʻI + MAUI; captions YOU PUT / SOME OCEAN.
- VO: "...you put some ocean..." ("put" at 2.40, "ocean" at 2.95)
- Sound: bar 2 at 2.5. Lid bang at 2.40; a big rushing slurp from 2.95 (a drain glug run backwards, not surf). The music low-pass sweep starts.

**3.0-4.05**
- Picture: 3.55 on "freezer": the arc becomes a torrent; the freezer frosts white and its compressor roars. 3.60-4.20 the LĀNAʻI slip unpins and is sucked along the arc into the freezer. 4.00 the waterline races out across the reef flat, exposing wet black basalt boulders, dark sand, slate-olive flats and turquoise tide pools.
- Text: MAUI holds (LĀNAʻI gone by 4.20); captions IN THE / FREEZER.
- VO: "...in the freezer." (to 4.05)
- Sound: paper-flap MOTIF #1 (3.60-4.20), the series sound mark. Rushing water. Riser starts.

**4.05-5.05**
- Picture: 4.15 paper double-take (a 0.15 s squash): he looks at the freezer, then at the camera. 4.40 the ferry grounds 400 m out and tilts; at 4.50 it flops onto its side. 4.55-5.05 an eased log-altitude lift (0.5 s, sub-frame motion blur): the beach, the freezer and the MAUI slip drop away. 5.05 a hidden cut inside the blur to SHOT B.
- Text: MAUI gone by 4.85; no caption (VO hole 4.05-4.95).
- Sound: wooden clonk and creak at 4.50. Whoosh up at 4.55. The riser climbs.

**5.05-6.0 · SHOT B**
- Picture: rebuilt from long-form Ch1 0:12.9-0:18 (the same Maui Nui terrain, water plane, -122 m rim polygon, Penguin Bank lobe and Kahoʻolawe dim mask), seen through a NEW vertical camera: the w345 previz regional oblique (about 190 km, heading 345°, pitch -58°, vFOV 45°, about 1° lower), framed about 10% tighter. Layout: Molokaʻi across the upper middle, Lānaʻi centre-left, West Maui centre-right, East Maui off the right edge, Kahoʻolawe low centre. The sea at -38 m and still falling; the West Maui-Lānaʻi gap a thin turquoise strip. 5.17 the LĀNAʻI slip lands on Lānaʻi. 5.52-5.59 on "snaps": the sea passes -53 m and the West Maui-Lānaʻi gap closes.
- Text: LĀNAʻI paper slip (cap 90) on Lānaʻi at x 150-500, y 1040-1170, lands 5.17. Captions LĀNAʻI SNAPS / ONTO MAUI.
- VO: "Lānaʻi snaps..." (from 4.95)
- Sound: soft paper tap at 5.17. Puzzle-piece CLICK #1 on "snaps" (~5.55, snapped to the beat at 5.625 if within 0.1 s).

**6.0-7.0**
- Picture: 6.15 a slip lands on West Maui. About 6.55 Penguin Bank meets Molokaʻi (at -60 m) at the left edge, with no sound. The sea falls from -60 to -75 m and the Lānaʻi-Molokaʻi gap (Kalohi side) narrows. The Pailolo, between Molokaʻi and West Maui, stays a deep turquoise inlet (its direct saddle is about -240 m).
- Text: LĀNAʻI + MAUI (slip, cap 90, on West Maui at x 560-840, y 1040-1170; lands 6.15).
- VO: "...onto Maui." (to 6.79); "Molokaʻi..." from 6.99.
- Sound: paper tap at 6.15. Riser.

**7.0-8.0**
- Picture: 7.03 a slip lands on Molokaʻi. 7.75-7.85 on "snaps": the sea passes -78 m and the Lānaʻi-Molokaʻi gap closes.
- Text: LĀNAʻI + MAUI + MOLOKAʻI (slip, cap 90, at x 160-600, y 650-780; lands 7.03). Captions MOLOKAʻI / SNAPS.
- VO: "Molokaʻi snaps..."
- Sound: paper tap at 7.03. CLICK #2 on "snaps" (~7.80). Bar 4 at 7.50.

**8.0-9.3**
- Picture: 8.40 the LĀNAʻI slip bounces as it is named. 9.17-9.34 the three slips flick off.
- Text: captions ONTO / LĀNAʻI.
- VO: "...onto Lānaʻi." (to 9.17)

**9.3-10.07**
- Picture: 9.30 the sea lands at -122 m. The yellow rim (#FFD23F, 10 px, glow) sweeps around the merged land in 0.35 s, off the left edge along Penguin Bank and off the right edge along East Maui. Kahoʻolawe stays outside the rim, dimmed 45% and desaturated. Shelves slate-olive and basalt, never pale tan. The merged island holds until 9.85. 9.85-10.07 a crash zoom (log altitude, 0.22 s, motion blur) down to SHOT C.
- Text: none (VO hole 9.17-10.07).
- Sound: impact_deep at 9.30 (beat at 9.375). Rim shimmer. Theme B (bouncy) begins. Crash-zoom whoosh at 9.85.

**10.07-11.0 · SHOT C**
- Picture: a NEW ground camera on the dry shelf 400 m off the frame-0 beach: 3 m up, heading 275°, vFOV 40°, low golden light. Lānaʻi across the horizon; Lahaina (bearing 333°) out of frame. The paper ferry lies on its side mid-frame in a turquoise puddle (x 300-720, y 1050-1250). 10.10 hop 1: the tourist lands from frame right, with squash and stretch and a dust puff. 10.65 hop 2 takes off and arcs over the ferry's hull (peak y 700 at 10.97).
- Text: captions SORRY, / FERRY.
- VO: "Sorry," (10.07-10.67), "ferry." (10.75-11.50)
- Sound: hop whoosh and thunk at 10.10. Bar 5 at 10.0: hop plucks. Whoosh at 10.65.

**11.0-12.05**
- Picture: 11.30 he lands to the left of the ferry. 11.55-11.95 the stranded ferry lets out one weak, deflating toot. 11.75 he looks back at it.
- Sound: thunk at 11.30. Sad toot at 11.55, in the VO gap (the gag).

**12.05-13.05**
- Picture: 12.25 he wags a split-pin paper finger at the ferry; the wag ends at 12.85.
- Text: captions YOU'RE / GROUNDED.
- VO: "You're grounded." (12.05-13.03)
- Sound: a pizzicato "tsk" figure under the wag. Bar 6 at 12.50: warm pad and theme B.

**13.05-14.4 · SHOT D**
- Picture: 13.05-13.32 a whip-pan left (8 frames, motion blur) into SHOT D: the long-form's 0:18-0:23 golden-hour land-bridge pass, re-flown for 9:16. Camera 6 m up and 12 m behind him, heading 275°, tracking as he skips west along the ʻAuʻau crest (about 20.885N 156.74W) toward Lānaʻi. Lānaʻi fills the top half with its whole flank exposed; reef pinnacles cast long shadows. On "Ice Age" (13.45-13.85) the camera rises 2 m and tilts up 6°: Lānaʻi's modern shoreline (where the land colours meet the dark wet seabed) reads as a bathtub ring high on its flank.
- Text: captions THE ICE AGE / DID THIS.
- VO: "The Ice Age did this..." (from 13.33)
- Sound: whip whoosh at 13.05. Theme B.

**14.4-15.61**
- Picture: 14.60 on "real", the Juice Check verdict stamp slams over the moving shot: the land and Lānaʻi's ring, the tourist small in the lower third.
- Text: IT HAPPENED (verdict stamp, Anton cap 110, 589 px wide, tilted -6°, stamp box x 110-845, y 300-560), on screen 14.60-15.61. Caption FOR REAL.
- VO: "...for real." (to 15.26)
- Sound: stamp cue at 14.60.

**15.61-16.6 · SHOT E**
- Picture: 15.61 a hard cut to SHOT E (NEW): a front-on medium shot on the crest. Camera 5 m south of him, 1.6 m up, heading 5°, vFOV 36°; he fills about 55% of the frame height. Behind him the empty dry floor runs north to Molokaʻi on the horizon. Lānaʻi off-frame left; Lahaina (bearing 99°) far off-frame right. He is mid-skip; on "catch?" he skids to a stop in a puff of dust (15.95).
- Text: IT HAPPENED exits at 15.61. Caption THE CATCH?
- VO: "The catch?" (15.61-16.40)
- Sound: the music stops dead on "catch?" (16.10): a comic full-band stop, then one pizzicato plink.

**16.6-17.55**
- Picture: he stands still. 16.60 a paper slip slaps down above him.
- Text: NOBODY / WALKED IT (paper slip, Anton cap 110, dark ink, two lines, x 120-760, y 230-560), on screen 16.60-18.30. Captions suppressed while it shows.
- VO: "Nobody ever..." (16.60-17.55)
- Sound: paper slap at 16.60. Sparse "tiptoe" plucks (bar 7).

**17.55-18.54**
- Picture: on "walked it" he slowly turns his head and stares into the camera, deadpan.
- VO: "...walked it." (17.55-18.24)
- Sound: plucks. Bar 8 at 17.50.

**18.54-19.5**
- Picture: 18.75 he looks down at his own red aloha shirt. 19.25 he looks at his suitcase.
- Text: the slip exits at 18.30; captions PEOPLE / HADN'T.
- VO: "People hadn't..." (18.54-19.30)
- Sound: plucks.

**19.5-20.47**
- Picture: 19.90-20.20 a comic push-in on his face (+8%, ease-out).
- Text: captions MADE IT / HERE YET.
- VO: "...made it here yet." (19.30-20.47; "yet" at ~19.95)
- Sound: a tiny sting on the push-in. Bar 9 at 20.0.

**20.47-21.28 · the awkward beat**
- Picture: 20.60 one cricket chirp. 20.75 the refill begins as the drain in reverse. 20.80 cloud shadows start to streak across the floor: the refill is a time-lapse, because the real rise took thousands of years. 21.00 he glances toward the sound. 21.05 a Paper-Mario flip (0.15 s) to face Maui. 21.25 he hops out of frame right.
- VO: none (hole 20.47-21.28).
- Sound: cricket at 20.60 (a sound gag). A faint reversed slurp (meltwater, the refill motif) from 20.75. No rumble, no roar.

**21.28-22.0 · SHOT G1**
- Picture: 21.28 a cut on the hop to SHOT G1 (NEW race shot): a low side-tracking camera 2.5 m up, 15 m south of the crest, heading 5°. Molokaʻi on the horizon; Lahaina out of frame. He hops left to right (east, toward Maui) in double time along the crest. The sea rises from -110 to -85 m. Gentle foam tongues creep in from the top (north) and bottom (south) of the frame as the dry strip narrows. Cloud shadows streak.
- Text: captions THEN THE ICE.
- VO: "Then the ice..." (21.28-21.85)
- Sound: the chase cue enters on bar 9, beat 3 (21.25): double-time plucks, a hop whoosh every 0.3125 s, soft foam lapping, the reversed slurp underneath.

**22.0-23.0**
- Picture: 22.30 the two foam fronts meet right behind his heels: the real last dry link between Lānaʻi and Maui, the -53 m crest at 20.885N 156.758W, going under. A foam tongue licks his heel (splash at 22.32) and he does a startled extra-high hop. 22.55-22.80 a whip-pan into SHOT A's pre-roll (the same render as frame 0, at t = -2.2); the camera lands on the frame-0 push path, already moving at the push speed. The sea (-36 m) creeps up the Launiupoko shelf toward the camera. He hops toward the camera ahead of it, on eighth notes. The freezer stands on the dry beach ahead, lid open, frosted white.
- Text: captions MELTED, / THE SEA.
- VO: "...melted, the sea..." (21.85-22.95)
- Sound: small splash at 22.32. Whip whoosh at 22.55. Bar 10 at 22.50.

**23.0-24.0**
- Picture: 23.00-23.45 the LĀNAʻI slip flutters back out of the freezer and up onto its pin above the peak. 23.50 the ferry, 400 m out, floats as the water reaches it, rights itself and bobs. 23.60 meltwater dribbles out over the freezer's lip into the rising swash (the 1.20 rope, reversed and gentle). 23.75 the MAUI slip pops in on his mark, ahead of him. His hops land at 23.125, 23.44 and 23.75, always on ground at least 1 m above the water at that moment (GMRT shelf profile).
- Text: LĀNAʻI returns to its frame-0 position (23.00-23.45). MAUI pops in at its frame-0 position (23.75). Captions CREPT BACK, / AND.
- VO: "...crept back, and..." (22.95-23.91)
- Sound: paper-flap MOTIF #2 (23.00-23.45). Ferry creak and bloop at 23.50, then one happy toot at 23.66, in the comma pause. The chase continues.

**24.0-25.0 · the frames that run straight into frame 0 in Shot A's one render**
- Picture: 24.06 his last hop lands him on his mark, with a thunk and a sand puff. 24.20 he grabs the freezer lid. 24.375 he swings it down to its frame-0 prop angle (25°) with a soft clunk; the frost curl returns to its frame-0 size; the compressor is off (it kicks on again at 1.00). 24.45-24.80 he settles into the frame-0 pose: leaning in 12°, right hand on the lid, suitcase in his left hand. Cloud shadows are back to normal speed by 24.60. 24.85-25.00 a swash runs up the sand and touches his front foot and the freezer's base exactly at 25.00, which is frame 0.
- Text: LĀNAʻI + MAUI at their frame-0 positions. Captions EVER / SINCE, (gone at 24.84).
- VO: "...ever since," (23.91-24.84), then the take's own comma pause (24.84-25.00, continuing at 0.00-0.05).
- Sound: landing thunk at 24.06, under the VO. A soft lid clunk at 24.375, 8 dB under the VO; the reversed slurp stops with it. The chase resolves on 24.375 into the caper theme's pickup, leading into bar 1. From 24.45 there is only surf, swash and the pickup: the same sound as frame 0.

## 3. Hook

- 0.0 s VO: "You can't walk to Lānaʻi." (5 words, about 1.6 s). The turn, "Unless you put some ocean in the freezer.", starts at 1.86 s, and the sea starts pouring into the freezer on "ocean" (2.95 s).
- FRAME 0 (and the last frame) shows one absurd thing that reads at phone size: a paper tourist with a suitcase at a Maui waterline, holding open a white chest freezer that stands in the surf, frost curling out. Lānaʻi lies right across the water, labelled.
- It does not read as a travel Short: there is a freezer in the sea; the LĀNAʻI label is the series' plain paper name slip; bar 1 is a sneaky pizzicato caper theme, not a ukulele.
- The anomaly escalates inside the swipe window: 1.0 s the compressor kicks on (THUNK, frost puff); 1.2 s the backwash runs too far and a rope of seawater climbs into the freezer (slurp); 1.86 s "Unless"; 2.40 s the lid flies open; 2.95 s the arc becomes a torrent and the sea starts falling.
- A freezer pulling water uphill, plus the slurp, makes the drain read as cartoon magic, never as a tsunami drawback.
- Probe (ytsearch, 2026-11-08): "walk to lanai": best Short 33K, off-topic. "maui lanai molokai one island ice age": best 9.3K, off-topic. "maui lanai land bridge": no on-topic Short. "ocean in the freezer" and "freeze the ocean sea level drop": only frozen-sea novelty Shorts and global sea-level maps, no land-bridge premise. The ferry crowd exists: "Why Hawaii's Islands Aren't Connected by Boats" has 5.4M views as a Short.
- No greeting, no channel name, no number anywhere in the Short.

## 4. Payoff

The payoff is a reframe, then a twist, then the button.
1. **Gag and spectacle (4.95-13.03).** "Lānaʻi snaps onto Maui. Molokaʻi snaps onto Lānaʻi." A paper slip lands on each island as it is named, and a click sounds as each gap closes. The rim traces the merged land, with Kahoʻolawe left out. "Sorry, ferry." He hops over the stranded ferry, which lets out a sad toot. "You're grounded." He wags his finger at it.
2. **Reframe (13.33-15.26).** "The Ice Age did this for real." The IT HAPPENED stamp lands over the land bridge, with Lānaʻi's flank showing its modern shoreline as a bathtub ring high above. The silly premise turns out to be history: the cartoon freezer was the ice sheets.
3. **Twist (15.61-20.47).** "The catch? Nobody ever walked it. People hadn't made it here yet." The NOBODY WALKED IT slip lands, the music stops dead, the tourist stares into the camera, then looks down at his aloha shirt: he is the anachronism. A real "huh", it heads off the certain "there were no humans then" comment, and it is funny.
4. **Button and loop (20.47-25.0).** The sea creeps back: time-lapse cloud shadows, a reversed meltwater slurp, gentle foam, comic chase music; no rumble, no surge. He scrambles home along the real last link, which goes under right behind his heels. The LĀNAʻI slip flutters back out of the freezer and he props the lid open again. "Then the ice melted, the sea crept back, and ever since," runs into "you can't walk to Lānaʻi. Unless you put some ocean in the freezer." On replay the hook means something new: the only freezer that ever worked was the Ice Age.

The Short never spends the long-form's payoff (no 56,000 ft, no dent, no Everest) and reuses none of the long-form's lines.

## 5. Loop check

**Audio.** Last line into first line: "Then the ice melted, the sea crept back, and ever since, you can't walk to Lānaʻi. Unless you put some ocean in the freezer."
- Plain English: a "since" clause completed by a main clause. On a first view, "You can't walk to Lānaʻi." still stands alone.
- On replay it closes a joke circle: the ice melted, so you would need a freezer to do it again.
- Both halves come from ONE TTS take with the text rotated. The cut sits inside the take's own comma pause after "since," (Rodney's comma pauses measure 0.08-0.15 s); at most 0.1 s of room tone is added (about 0.16 s at the end, 0.05 s at the start). No time-stretching; prosody, breath and room tone continue across the seam.
- Music: 96 BPM, 10 bars = 25.000 s. Bar 10's chase resolves on 24.375 into the caper pickup, which lands on bar 1's downbeat at frame 0. The surf bed is a loop. The refill audio (reversed slurp) ends at 24.375 when the lid settles; from 24.45 the bed is surf, swash and the pickup, identical to frame 0. No rumble, no roar, no fade.
- Export: exactly 750 frames and exactly 25.000 s of audio; AAC encoder priming trimmed and checked with ffprobe; played looped for 3 cycles on a phone; plus one cold start from 0.00 to confirm VO1 sounds like an opening.

**Picture.** Frames 684-749 (22.80-24.967 s) and frames 0-151 (0-5.05 s) are ONE continuous render of Shot A, render time t = -2.2 to 5.05. Frame 749 is t = -0.033 and frame 0 is t = 0: consecutive frames of the same render, so the seam is not a cut at all.
- Everything matches by construction: the camera on the frame-0 push path at the same speed since 22.80; the tourist's pose (leaning in 12°, right hand on the lid, suitcase in his left hand, front foot in the swash); the freezer lid at 25° with the frame-0 frost curl and the compressor off; the swash touching his foot and the freezer's base at the seam; the ferry's position and bob phase; the LĀNAʻI and MAUI slips at identical positions; cloud shadows at normal speed since 24.60; same sun and grade.
- The only cut near the end is the visible whip-pan at 22.55-22.80, 2.2 s before the seam. Everything that differs from frame 0 finishes by 24.80, with at least 0.15 s between events; from 24.85 to 25.00 only the swash runs up.
- Captions switch hard by design (none from 24.84; YOU CAN'T at 0.05), so the seam metrics are measured on the picture layer before captions.
- Gates: frame-749-to-frame-0 SSIM no lower than the shot's median consecutive-frame SSIM; first/last MAE ≤ 5/255; the self-concatenated temporal_scan shows no "cut" or "flash".

## 6. Facts

Spine = brief section 4. Ledger = research/ep02/script/ledger_part1.json. GMRT = s02_grid/mauinui.asc (about 60 m cells). Checks: s02v3_scripts/bottleneck.py, raceline.py, maximin.py, pools.py (output bott.npy).

1. **"You can't walk to Lānaʻi." TRUE.** Lānaʻi is a separate island; the shallowest crossing to West Maui (the ʻAuʻau Channel) is about 50-53 m down. Ledger C12-03 gives about -50 m near 20.885N 156.758W; maximin.py finds the best route's lowest point at -53.4 m. The State Data Book's 77 m is the maximum depth along a fixed line, not the saddle.
2. **"Unless you put some ocean in the freezer."** A joke premise, and an honest cartoon of the real mechanism: in an ice age, water leaves the ocean and is stored as ice on land, so the sea falls (C12-04, NASA Sea Level Change). The line says "put ocean in the freezer" (take water out of the sea and store it frozen), not "freeze the ocean": sea ice floats and would not lower the sea. The freezer stands on the beach, never floats.
3. **"Lānaʻi snaps onto Maui." TRUE.** Spine #5 and C12-03: the Lānaʻi-West Maui saddle is about -50 m. bottleneck.py: Lānaʻi stays joined to the Launiupoko beach up to a sea level of -52 m (2 m steps). Shot B closes the gap as the level passes -53 m, on "snaps".
4. **"Molokaʻi snaps onto Lānaʻi." TRUE.** C12-03: the Molokaʻi-Lānaʻi saddle is about -78 m on the Kalohi side (panel measured -78 to -82 m). Molokaʻi joins through Lānaʻi, not directly: the direct Pailolo saddle is about -238 to -242 m, so the Pailolo stays a turquoise inlet in every drained shot (USGS Volcano Watch 2003: East Molokaʻi and West Maui "remained connected via Lānaʻi"). Penguin Bank joins Molokaʻi at about -60 m and sits inside the rim (spine #5). Kahoʻolawe stays separate down to -159 m (C12-03), so it is dimmed and left outside the rim (C12-06). VERIFY (a): re-run sill.py on the HMRG 50 m grid before lock (margins 37 m or more; no change expected).
5. **"Sorry, ferry. You're grounded."** A joke. The paper ferry "runs aground" on the dry floor. A real Maui-Lānaʻi passenger ferry runs; it is never named and the paper ferry carries no livery.
6. **"The Ice Age did this for real." + IT HAPPENED. TRUE.** In the last Ice Age the sea stood about 120 m (400 ft) lower because water was locked up in ice sheets (C12-04, NASA Sea Level Change). Maui, Lānaʻi and Molokaʻi were connected, most recently about 18,000 years ago (C12-05, USGS Volcano Watch 2003); Grigg et al. 2002 describe limestone bridges between them at the last glacial maximum. Our drain stops at -122 m, inside the 120-130 m range of estimates. The mechanism is spoken two lines later ("Then the ice melted"). The stamp lands on the land and Lānaʻi, and the twist corrects the implication about the walker 1 s later.
7. **"The catch? Nobody ever walked it. People hadn't made it here yet." + NOBODY WALKED IT. TRUE. NEW LEDGER LINE; VERIFY (f) to close before lock.** First settlement of Hawaiʻi: AD 940-1130 at 95% HPD, most probably AD 1000-1100 (Athens, Rieth & Dye 2014, American Antiquity 79(1):144-155); other models put it later, in the 13th century (Wilmshurst et al. 2011, PNAS). Spine #9 (Nihoa, about AD 1000) agrees; ledger C4-07 warns the Nihoa dates conflict, so no date is spoken. The bridge was dry only during glacial low stands; the sea has stood near today's level for thousands of years and the shallowest crossing is about 50 m down, so it was underwater long before anyone arrived. "Nobody" means no person; nothing is said about animals.
8. **"Then the ice melted, the sea crept back, and ever since, ..." TRUE.** Spine #5 and C12-04. USGS 2003: "Molokaʻi became isolated, and then the land bridging Lānaʻi and Maui was submerged." Grigg et al. 2002: about 120 m of post-glacial rise flooded the bridges. "Crept" is honest: the rise took thousands of years, and the picture marks the refill as a time-lapse. The refill order follows the data: the Molokaʻi-Lānaʻi link (-78 m) floods first, the ʻAuʻau crest (-53 m) last; the heel-lick happens on that crest.
9. **Picture-only details** (from the grid, not invention).
   - Race geography (bottleneck.py, raceline.py, maximin.py): the straight 265° line from Launiupoko to Lānaʻi is dry at -122 m (lowest point -78 to -80 m, 7-8 km out). On the refill, the last dry link is the crest at 20.885N 156.758W (-53.4 m). The middle leg home stays dry until the crest floods, but its best route hugs the south Lahaina shore (about 20.867N 156.674-156.684W), so it is never shown; the whip-pan at 22.55 is the ellipsis. The final approach is only the Launiupoko shelf (-33 m at 1 km out, -20 m at 0.5 km); every hop lands on ground at least 1 m above the water.
   - Lahaina town (20.873N 156.677W) bearings: 323° from the frame-0 camera, 333° from Shot C, 99° from the crest (Shots D, E, G1): at least 30° outside every frame edge.
   - Pools (pools.py): at -122 m the -136 m hollow at 20.761N 156.809W is OPEN SEA, an inlet. The real enclosed pools are at 20.786N 156.708W (0.32 km², floor -128 m), 20.774N 156.756W (0.26 km², floor -124 m) and a 3.3 km² basin at 20.771N 156.687W (floor -148 m). Turquoise pools only there; the tourist's route (20.83-20.89N) stays north of all of them.
   - Sounds: no gull; the cricket is a sound gag, not a claim.
10. **Big numbers: ZERO** on screen and spoken. 400 ft, "under 200 ft", 18,000 years, 150,000-200,000 years and the settlement date live only in the description and pinned comment.

Spelling: Molokaʻi and ʻAuʻau correct throughout; the Grigg paper is cited by its exact printed title ("Au'au Channel").

**Still open (VERIFY before lock):** (a) saddles and crest on the HMRG 50 m grid; (b) rights for the tourist photo (the long-form cut-out), the ferry photo and the freezer photo, or our own photo or illustration; (c) lexicon check on wehewehe.org and a full phone-speaker listen; (d) Barlow ʻokina: drawn with the U+2018 glyph substitution (Anton already passes, short03/okina_test.png), and Ā confirmed in latin-ext; (e) Launiupoko outside the August 2023 burn area on the county map; (f) add the settlement line to the ledger.

## 7. Renders: new for this Short vs reused

**Reused as-is** (same data, assets and settings; only seen through new vertical cameras):
- The long-form Ch1 0:12.9-0:18 Maui Nui drain: terrain tile and bake (HMRG/GMRT blended into ETOPO 2022), water-plane shader and foam, the -122 m rim polygon (#FFD23F), the Penguin Bank lobe, the Kahoʻolawe dim and desaturate mask, seabed materials.
- The long-form 0:18-0:23 golden-hour land-bridge pass: flight data, sun and grade (re-flown for 9:16 as Shot D).
- The long-form 0:23.6 paper tourist: the same public-domain cut-out, matte, base tab, contact and directional shadows, S11 hop physics.
- Type and paper system: Barlow Condensed 800, Anton, paper slips, the Juice Check stamp, the POST grade.
- SFX library: riser, paper flap, hop whoosh, thunk, impact_deep, stamp cue, whoosh, puzzle click.

**New, for this Short only**
1. **SHOT A, the loop's spine.** ONE continuous shore-level render from t = -2.2 to 5.05 (7.25 s), placed at 22.80-25.00 and 0-5.05. A close coastal tile from NCEI/USGS 3DEP coastal lidar (1-3 m) blended into the Maui Nui tile; beach, wet-basalt and reef-flat materials; the shared near-surface water pass and periodic loop-clock water (shorts_plan.md 5B); tilt-shift over the foreground; a cloud-shadow layer easing from 40x to 1x over t = -2.2 to -0.4; water-level curve: the refill tail (-36 to 0 m), then 0 m, a slow leak into the freezer from 1.2 to 2.95, and a fast fall to about -30 m by 5.05; the incoming half of the whip (t = -2.2 to -1.95) rendered inside it. Motion-test it FIRST (U5). FALLBACK, decided before anything else is built: a 200 m low oblique over the same beach (heading 258.5°, pitch -12°, same push); the tourist becomes an S11 standee at 35-40% of frame height, the freezer goes to cartoon scale, all events and times stay the same.
2. **The FREEZER PROP.** A paper cut-out of a real white chest freezer (our own photo, or a verified public-domain one) with a separate lid card on a hinge. Rig: propped at 25°, flung open (bang on the hinge stop), swung back to 25°; cabinet shudder; lid light; a frost-curl sprite on the loop clock; frosting-over (3.55); meltwater dribble (23.60). Water-rope VFX: a twisting stream peeling off the swash and pouring into the freezer (1.20-5.05), growing into a torrent on "freezer"; reversed and gentle at 23.60.
3. **Water-level curves**, in one file. Drain, keyed to words: -53 m on "snaps" #1, -78 m on "snaps" #2, -122 m at 9.30. Refill: -122 m at 20.75, -110 at 21.28, -85 at 21.85, -53.4 at 22.30 (the crest), -36 at 22.80, -14 at 23.50 (the ferry floats), -3.5 at 24.06, -1.5 at 24.375 (the lid settles), 0 at 24.85.
4. **SHOT B:** a regional vertical camera from the w345 previz, about 1° lower and about 10% tighter; a hidden cut inside the lift blur at 5.05. The material pass must replace the previz's grey-tan shelf placeholder with slate-olive carbonate and dark basalt.
5. **Camera moves:** the lift (4.55-5.05), the crash zoom (9.85-10.07), two whip-pans (13.05-13.32 and 22.55-22.80).
6. **SHOT C:** a ground camera on the dry shelf 400 m off Launiupoko, 3 m up, heading 275°.
7. **SHOT D:** the re-flown pass on the crest approach (heading 275°), with a rise and tilt to show Lānaʻi's 0 m "bathtub ring".
8. **SHOT E:** a front-on medium shot on the crest, heading 5°.
9. **SHOT G1:** a side-tracking race shot along the crest, heading 5°; two gentle foam fronts meet at 20.885N 156.758W at 22.30.
10. **Rigs.** The tourist as a split-pin puppet: an arm for the lid (hold, fling, swing back) and the finger wag; a turning head; the suitcase as a separate piece; a 0.15 s Paper-Mario flip; a mid-skip skid. The paper ferry: a public-domain pre-1929 photo of a small passenger steamer with no livery, or our own paper illustration; bob, ground, flop and right-itself animations; a sad toot and a happy toot.
11. **UI:** paper slips LĀNAʻI (with the small Myth Juice stamp), MAUI, MOLOKAʻI and NOBODY / WALKED IT; the IT HAPPENED stamp; the house caption track.
12. **Audio:** one rotated TTS take (3 candidates); a 96 BPM, 10-bar music cue built to loop (caper theme A, bouncy theme B, a comic full-band stop, tiptoe plucks, a double-time chase resolving into theme A's pickup); a loopable surf bed; compressor THUNK and hum, lid bang, the water-rope slurp, meltwater dribble and reversed slurp, lid clunk, cricket, the two ferry toots.

**Cut from the draft** (de-cloning and panel fixes): the -400 FEET odometer and the race clock; the LAST ICE AGE kicker and its scrim; the ONE ISLAND headline and the MAUI NUI slip; the 5 s crane-up that repeated the merge; the rumble, the roar and the music cut to rumble; the gull; the 6° lean; the bath plug and chain (integrator: the plug belongs to Short 1 only).

**QC gates:** phone sheet at 390 px; every cap ≥ 77 px (the smallest here is 90); all text x ≤ 849; luma ≥ 70 on every shot; gate.py tan ≤ 10% on every drained shot; place-match diff of 0 (Lānaʻi at 0.81, 4.95 and 8.40; Maui at 6.15; Molokaʻi at 6.99); Lahaina bearing gate (the town at least 10° outside every frame edge, no 2023 burn imagery); frame 749 vs frame 0 continuity; one 3-cycle looped playback on a phone.

The long-form does not change. Every Short render is a separate pass from shared data and assets; no long-form shot, line, cue, timing or file is edited.

## 8. Title, description, link

**Release:** D+1. **Related video:** the long-form "Why Can't You See Most of Hawaii? (Look Down)", so its link shows on the Shorts player.

**Title:** You Can't Walk From Maui to Lānaʻi (Unless...) (46 characters). Passes the niche regex (no drained/drain, hidden/hiding, bottom/beneath, nobody, found; no Everest) and carries no "plug" or "freezer". Backup: "Has Anyone Ever Walked From Maui to Lānaʻi?" (43; the twist answers it).

**Description:**

> In the last Ice Age, so much seawater was locked up in ice that the ocean sat about 400 feet lower. Maui, Lānaʻi and Molokaʻi were joined into one island, part of what scientists call Maui Nui (most recently about 18,000 years ago). Lānaʻi would touch Maui if the sea dropped less than 200 feet. Kahoʻolawe stayed separate: its land link to Maui probably broke 150,000 to 200,000 years ago. And nobody ever made the walk. People reached Hawaiʻi only about a thousand years ago, long after the sea came back.
>
> The full film drains the ocean around Hawaiʻi all the way down, to the true base of the mountain:
> Why Can't You See Most of Hawaii? (Look Down)
>
> Every depth in this Short comes from real seafloor survey data. The freezer is a joke; the ice sheets were real.
> Bathymetry: GMRT (Global Multi-Resolution Topography, Lamont-Doherty Earth Observatory); University of Hawaiʻi SOEST HMRG multibeam synthesis; NOAA ETOPO 2022.
> Sources: USGS Hawaiian Volcano Observatory, Volcano Watch, "Once a big island, Maui County now four small islands" (2003); NASA Sea Level Change (Ice Age sea level); Grigg, R.W. et al. (2002), "Drowned reefs and antecedent karst topography, Au'au Channel, S.E. Hawaiian Islands", Coral Reefs 21: 73-82; Athens, J.S., Rieth, T.M. and Dye, T.S. (2014), "A Paleoenvironmental and Archaeological Model-Based Age Estimate for the Colonization of Hawai'i", American Antiquity 79: 144-155.
> Photos: [public-domain credits for the tourist, ferry and freezer photos, filled in after the rights check].

**Tags:** hawaii, maui, lanai, molokai, maui nui, ice age, sea level, ice age sea level, land bridge, hawaii without water, drained ocean, hawaiian islands, geography. The drain words go in the tags and description only, never in the title.

**Pinned comment** (no emojis, live within 5 minutes, owner's OK): "Nobody ever made this walk: Polynesian voyagers reached Hawaiʻi roughly a thousand years ago, long after the sea had covered the land bridge. Have you ever taken the ferry across to Lānaʻi?"

**Captions:** burned-in house captions, plus our own uploaded caption file with the native spellings (Lānaʻi, Molokaʻi) from the lexicon caption_map. Never leave YouTube's auto-captions, which would write "Lanai".

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 66. All must-fixes are in: narration rewritten new (no long-form line reused); the anomaly starts by 1.2 s and "Unless" lands by 1.86 s; the refill is a creeping time-lapse tide with no rumble or roar; the "nobody walked it" twist and the pinned settlement line; one slip per island as each is named, and the slow crane repeat cut; built to the real take with the seam in the take's own comma pause; the G2 hidden cut replaced by one continuous Shot A render; fact #8 corrected (the -136 m hollow is an inlet); Lahaina kept out of frame; typos fixed; a Shot A fallback chosen in advance; the -400 FEET odometer and the scrim kicker removed.
