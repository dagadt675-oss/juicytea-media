# Short 7 (S12-almost-twice-everest + P2-01-cropped, with the P2-04 beat): "This Beach Is on a Mountain Almost Twice Everest"

| | |
|---|---|
| Release | **D+11**, same clock hour as the long-form (slot 7 of 7; never before D+7) |
| Length | L = 27.40 s planned (822 frames); recompute from the real timing.json |
| The one big number | ABOUT 56,000 FEET (the only Short allowed to spend the long-form's payoff) |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps, VE 1.0; TerrainStage curvature on |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

## Integrator changes (2026-11-08)

1. **Two long-form lines rewritten** (the owner wants Short narration written new):
   - k06 "Like a bowling ball on a mattress." (verbatim long-form s164) became **"Bowling ball, meet mattress."** The metaphor stays (it is a long-form element); the line is new and deadpan.
   - k07 "Measured from its true base, Mauna Loa is about fifty-six thousand feet tall." (verbatim s169) became **"From its true base, Mauna Loa stands about fifty-six thousand feet tall."** The ledger qualifier "from its true base" (C6-06) stays word for word on purpose.
   - Retime: from k06 on, events moved earlier (about -0.5 s through "tall", -0.8 s after it); L went from 28.20 to 27.40 s. Every anchor is re-derived from the real timing.json anyway.
2. **Burned-in captions added** in the house style (shorts_plan.md section 4), suppressed while the SEA FLOOR tag sits near the caption band (8.05-10.25) and while the number card shows ABOUT / 56,000 / FEET. The writer's reason for no captions (the accent-word ban) does not apply: the ban is on a black caption box with an accent word, and the house captions are unboxed. Our own SRT is uploaded too.
3. **Known kinship with Short 1, accepted:** both end on an oblivious beach creature ("And he has no idea" / "Somebody tell that turtle:") and both titles say "mountain". They are 11 days apart; Short 1 owns position (more than halfway up) and the moat, this Short owns height (56,000 ft) and the true base.

## 1. Narration and TTS

**TTS input.** engine/tools/tts.py segments with voice `eY2VJs4Gi8QKG2RV01sS` ("Rodney - Clear Educator"), passed explicitly (never the Brian default), model `eleven_v4`, the locked ep02 settings, `lead_in` 0. Markers use the `{m:}` syntax of ep02 tts_spec.json. Respellings go in the voice text only.

```
k01  This {m:beach}beach is on a {m:mountain}mountain almost {m:twice}twice as tall as {m:ev1}Everest.   [pause 0.30]
k02  It's {m:loa}MAO-nah LOH-ah, and most of this mountain is {m:under}underwater.   [pause 0.30]
k03  From the {m:sea}sea floor, it already beats {m:ev2}Everest.   [pause 0.40]
k04  But that's not the {m:bottom}bottom.   [pause 0.40]
k05  It's so {m:heavy}heavy, it {m:pushed}pushed the sea floor down by {m:miles}miles.   [pause 0.15]
k06  {m:bowl}Bowling {m:ball}ball, meet {m:mattress}mattress.   [pause 0.75]
k07  {m:from}From its {m:truebase}true base, MAO-nah LOH-ah stands {m:about}about fifty-six {m:thousand}thousand {m:feet}feet {m:tall}tall.   [speed 0.95, pause 0.95]
k08  Somebody tell that {m:turtle}turtle:   [pause to the file end, about 0.27 s]
```

**As heard** (66 words, about 27.4 s):
> This beach is on a mountain almost twice as tall as Everest. It's Mauna Loa, and most of this mountain is underwater. From the sea floor, it already beats Everest. But that's not the bottom. It's so heavy, it pushed the sea floor down by miles. Bowling ball, meet mattress. From its true base, Mauna Loa stands about fifty-six thousand feet tall. Somebody tell that turtle:

**Estimated times** (Rodney's measured ep02 rate: 153 wpm median within segments; s164 took 2.56 s; s169 took 5.76 s at 0.9x). Retime every anchor from the real timing.json.

| Seg | Time |
|---|---|
| k01 | 0.06-4.25 |
| k02 | 4.55-7.85 |
| k03 | 8.15-10.85 |
| k04 | 11.25-12.95 |
| k05 | 13.35-17.05 |
| k06 | 17.20-18.90 |
| k07 | 19.65-24.83 ("about" ~21.90, "thousand" ~22.95, "feet" ~23.38) |
| k08 | 25.78-27.13 |
| L | 27.40 s |

**Why the hook is clean:** the loop line is a separate clause ending on a colon. On the replay, the hook is the message the turtle needs to hear, so it is a complete, stressed, falling declarative that starts its own take, not a mid-clause splice (the playbook's proven "...tell them this:" pattern).

**Loop takes** (needs a small, default-off tts.py change):
- Add a spec flag `"loop": true`. When set, the last segment's next_text becomes k01's text, and k01's previous_text becomes k08's text. Default off, so no other spec (including the long-form's) changes behaviour.
- Make 3 takes of k01 with the wrap and 3 "fresh" takes (no previous_text), and 3 takes of k08 (bump `"take"`).
- Pick k01 by a cold test: play 0.0-2.0 s on a phone speaker; "THIS beach" must be stressed and sound like a new statement. Pick k08 for an open, slightly rising end on "turtle".
- Test the chosen pair in both directions: five loops of "turtle: | This" on a phone; loudness matched within 0.5 LU short-term; no pitch jump beyond a normal new-sentence reset.
- asr_check.py: "MAO-nah LOH-ah" must come back as "Mauna Loa" (lexicon asr_accept); "mattress" and "fifty-six thousand" as scripted.

**Pronunciation**
- Mauna Loa is the only Hawaiian name spoken (twice). Voice text uses the lexicon's "MAO-nah LOH-ah" (lexicon id mauna_loa): voiced in the locked long-form (s067, s165, s169) and passed the ASR check on 2026-11-08. "Mau" rhymes with "cow"; "Loa" has two syllables (LOH-ah), never one. IPA /ˈmaʊ.nə ˈloʊ.ə/; Hawaiian [ˈmɐwnə ˈlowə]. Never "Mow-nuh" (the lexicon warns "ow" can be read /moʊ/).
- Hawaiian words in writing only (notes in case one is ever voiced): Hawaiʻi plain "Hawaii" or hah-WHY-ee with a light glottal catch before the final "ee"; Punaluʻu poo-nah-LOO-oo, glottal stop before the last "oo" (rule-derived, not in the lexicon; VERIFY on wehewehe.org); Kaʻū kah-OO, glottal stop and a long final "oo" (rule-derived; VERIFY); honu HOH-noo.
- Lexicon open item 1 (a person checks wehewehe.org) still applies to Mauna Loa before the final mix.

## 2. Second-by-second table

**Poses.** All at VE 1.0. The shot axis runs at bearing 164.7° from Mauna Loa's summit (19.475 N, 155.603 W) through Punaluʻu (19.1361 N, 155.5047 W); the camera always faces back up the axis, heading 344.7°. TerrainStage curvature is on.
- A "Aerial" (frame 0 = last frame): 3.0 km off the beach at 19.1101 N, 155.4971 W; alt 600 m, pitch -3.0°, vfov 34°; computed with curvature: summit skyline at y ≈ 538, beach at y ≈ 1417.
- M "Massif" (mid-dive, about 5.0 s): about 80 km from the summit, alt about -1.0 km, pitch about -2°, vfov about 16°; the whole drained dome in frame (green top at y ≈ 320-577, bathtub ring at y ≈ 577, dark flank to the bottom).
- S "Section": camera 150 km down the axis at 18.1753 N, 155.2259 W; alt -3.5 km (1.56 km above the local floor, ETOPO -5,057 m); pitch 0.0°, vfov 6.0°, 8.19 m/px; summit edge at y 240, in-plane 0 m line at y 749, sea-floor band at y 1360. The cut plane is vertical, running ENE-WSW (74.7°/254.7°) through the summit.
- D "Deep": the same camera at vfov 6.0°; pitch -2.8° puts the band at y 472 before the dent; pitch -4.9° puts the true base at y 760 after it.
- H "Hero": the same camera at vfov 11.5° (15.73 m/px), pitch -2.0°; summit edge at y 250, true base at y 1340, Everest's peak at y 778 (51.6%).
- All section moves are tilts and zooms of one camera; it never enters rock, even when the cut closes; foreshortening ≤ 0.4%. Check every pixel target on the render.

**Layout.** Text at x 74-849, y 200-1500 (captions per house spec), caps ≥ 80 px (widths measured on the engine's fonts). Style: ink #1E1A16 on paper #F6F1E4, 2-4 px deckled edge, soft shadow (S11 paper grammar); no plates, scrims, black boxes, arrows, dashed lines or accent colours. Summit point at x 540. Tape: a 32 px paper strip at x 524-556, ink ticks every 1,000 m, no numbers. Number card hangs from the tape head on its left, x 74-524, 408 px tall: ABOUT (Barlow Condensed 800, cap 80, 277 px wide), 56,000 (Anton, cap 132, 417 px), FEET (Barlow Condensed 800, cap 88, 224 px). Everest: the SRTM summit on a plain grey pedestal, footprint 2.2 km, 5 px white outline, standing in the cut plane 50 m in front of the face, centred 1.6 km ENE of the summit; on screen x 600-870 at 8.19 m/px, x 572-712 at 15.73 m/px.

**Captions:** house spec; suppressed 8.05-10.25 (the SEA FLOOR tag at y 1372-1482 sits too close to the band) and 21.90-24.83 (the number card shows ABOUT / 56,000 / FEET); none on frame 0 (the first card appears at 0.06) and none after 27.13.

**0.00-0.95**
- Picture: POSE A; frame 0 = the last frame. A new aerial plate on the long-form's Big Island terrain. Sky (deep blue to pale haze) fills y 0-530; Mauna Loa's broad dome on the skyline at y ≈ 538-590, above green-brown Kaʻū slopes; a black-sand crescent with its palm grove at y ≈ 1400-1430, about 525 px wide; turquoise water and rolling surf to the bottom edge. A giant paper honu standee basks on the sand (x 360-800, y 1150-1417): a cut-out of a public-domain NOAA or USFWS photo, warm paper edge, base tab, contact shadow, clearly paper and giant. Frame 0 is a wave's run-up crest, foam at the honu's base tab, velocity 0. From frame 0 the backwash pulls the foam sheet down the sand; the whole sea starts sinking (0 to -25 m by 0.95, ease-in). The surf keeps rolling and the honu's edge flutters on the loop clock. The camera eases away from rest.
- Text: POSTCARD at x 90-846, y 200-512, tilt -3°, deckled edge: "ALMOST TWICE" (Anton cap 96), "EVEREST" (Anton cap 130), a blank stamp with no words at x 740-830, y 400-490. Captions from 0.06: THIS BEACH / IS ON A.
- VO: VO1 "This beach is on a" (from 0.06)
- Sound: seamless surf bed and trade wind. Music silent; a soft plucked pulse fades in from 0.40.

**0.95-2.40 · THE OCEAN EMPTIES, on "mountain"**
- Picture: the water plane plunges with smootherstep from -25 to -5,200 m by 4.00. The coastline peels away from the beach; a white foam rim races down and out toward the camera. Dark basalt (#2B2927-#3A3532), olive-brown sediment drapes and drowned reef steps rise as a widening band below the coast. A subtle bathtub ring stays at 0 m (a wet dark band with a thin salt-white line). The honu never moves. The camera starts easing back and down at 1.60. Rebuilt from the long-form's drain water plane on HMRG/ETOPO, with a new camera.
- Text: the postcard holds. Captions MOUNTAIN / ALMOST TWICE.
- VO: "...mountain almost twice"
- Sound: a big water-recede whoosh plus a sub rumble from 0.95. Low bass joins the pulse.

**2.40-4.25 · THE DIVE**
- Picture: one eased dolly-zoom back and down the axis, from POSE A to POSE S (2.40-7.40, vfov 34° to 6°), on a straight line that clears the ETOPO profile by at least 1.4 km; the water always stays at least 40 m below the camera. 2.55-3.30 the postcard tips forward into the falling sea, rides the foam rim down the flank and leaves the frame bottom with paper physics.
- Text: the postcard leaves at 2.55 (readable for 2.55 s). Captions AS TALL AS / EVEREST.
- VO: "...as tall as Everest." (to 4.25)
- Sound: a paper flap and a small splash (the series' postcard-drop motif).

**4.25-5.95 · POSE M passes**
- Picture: the whole drained dome rises out of the dark floor and reads as one huge mountain: green top, bathtub ring high up, dark flank below, sediment-toned floor.
- Text: "MAUNA LOA" tag (Barlow 800 cap 88, x 80-651, y 760-880, tilt +2°) on the flank, anchored with S.project(); lands at 4.70. Captions IT'S MAUNA LOA, / AND MOST.
- VO: VO2 "It's Mauna Loa, and"
- Sound: paper tick.

**5.95-7.40 · THE SLICE** (rebuilt from the long-form's Ch6 cut-away material in a new orientation)
- Picture: a vertical ENE-WSW cake cut sweeps from just in front of the camera to the summit plane (5.95-7.25); its moving face shows the strata; it stops as the dolly-zoom lands on POSE S (7.40). The face, top to bottom: dark sunlit flows with thin red layers down to the in-plane 0 m wet line at y 749; black-green pillow lavas; the old sea floor as a red-brown sediment band (14 px core with a dark under-stroke) at y 1360; grey oceanic crust; olive-dark mantle. 55% of the column sits below the 0 m line: the claim drawn true. The face is graded to mean luma ≥ 70.
- Text: "MAUNA LOA" holds and flips off at 7.75 (3.05 s on screen). Captions OF THIS MOUNTAIN / IS UNDERWATER.
- VO: "...most of this mountain is underwater." (to 7.85)
- Sound: a blade "shhk" and stone grind along the sweep.

**7.40-8.30**
- Picture: POSE S with a slow push (vfov 6.3° to 6.0°, 7.40-11.25).
- Text: "SEA FLOOR" tag (cap 80, x 80-562, y 1372-1482) hangs from the band by a paper tab; lands at 8.05. Caption FROM THE (to 8.05), then suppressed.
- VO: VO3 "From the sea floor,"
- Sound: paper tick.

**8.30-10.85 · EVEREST LIFT in the cut plane** (rebuilt from the long-form's Ch3 SRTM Everest asset, lab/hawaii/data/everest_h16.png)
- Picture: an in-scene mesh, its summit pinned at 8,849 m above the band, rises from below the band like a stage lift (8.30-9.80); overshoots by 2% with its peak still at least 10 px below the summit edge; settles at 10.10 with its peak 39 px below the top edge (gate 30-45 px).
- Text: "EVEREST" tag (cap 80, x 443-849, y 560-670) lands at 9.85 on Everest's body. "SEA FLOOR" flips off 10.05-10.25. Captions resume at 10.25: BEATS EVEREST.
- VO: "...it already beats Everest." (to 10.85)
- Sound: a mechanical lift whoosh, then a soft stone clunk at 10.10 (not comic).

**10.85-11.50 · GAG in the pause**
- Picture: Everest gives one small hopeful hop (about 60 px), falls back short and wobbles; its peak stays at least 10 px below the summit edge.
- Text: "EVEREST" holds. Caption BUT THAT'S (from 11.25).
- VO: (pause), then "But that's" from 11.25
- Sound: a tiny comic boing in the gap (≤ 0.4 s, about -16 dB). The music stops hard on "But".

**11.50-12.15 · THE DROP**
- Picture: a fast tilt down to POSE D (pitch 0° to -2.8°) past the band: the band climbs to y 472; grey crust and olive mantle fill the frame below; Everest's top leaves the frame.
- Text: "EVEREST" flips off 11.65-11.85 (2.0 s on screen). Captions NOT THE / BOTTOM.
- VO: VO4 "...not the bottom."
- Sound: impact_deep on "bottom" (11.90).

**12.15-13.70**
- Picture: POSE D with a slow push; Everest's lower half stands on the band.
- Text: caption IT'S SO (from 13.35).
- VO: (pause), then "It's so"
- Sound: a low rock creak (13.40).

**13.70-18.40 · THE DENT** (schematic, drawn from the USGS description and the long-form's Ch6 sag curve)
- Picture: from "heavy" the band and crust sink 8 km; the main motion falls on "pushed ... miles", and the sag settles at 18.40, in sync with the inset's mattress bounce. Everest rides down with a small wobble. Rock grows down behind the sinking band; the summit, out of frame, never moves. The camera tilts from -2.8° to -4.9°, so on screen the band moves from y 472 to y 760. The real flexure is far wider than this 9 km frame, so the band sinks almost level; the dent's shape lives in the inset.
- Text: captions HEAVY, IT PUSHED / THE SEA FLOOR / DOWN BY MILES.
- VO: VO5 "...heavy, it pushed the sea floor down by miles." (to 17.05)
- Sound: a deep rock groan and sub swell. Low strings enter.

**17.05-19.50 · BOWLING-BALL INSET (gag)** (the long-form's metaphor rebuilt in paper)
- Picture: an off-white card flips in at x 80-450, y 230-610 (tilt +3°), clear of the band and of Everest. A cut-out bowling ball drops and lands on "ball" (17.75); on "mattress" (about 18.35) it sinks into a quilted paper mattress, which dents with one small bounce in sync with the band's last settle (18.40). The card flips away 19.30-19.50.
- Text: the inset has no words. "TRUE BASE" tag (cap 80, x 76-560, y 772-882) hangs from the settled band; lands at 18.40. Captions BOWLING BALL, / MEET MATTRESS.
- VO: VO6 "Bowling ball, meet mattress." (17.20-18.90)
- Sound: paper flaps in and out; a soft low thud on "ball"; a bedspring creak in the gap at 18.95 (gag).

**19.50-20.40**
- Picture: POSE D, settled. Everest stands on the true base (base at y 760, peak above the frame). Slow push. On "From" (19.65) the paper tape starts unrolling upward from the TRUE BASE tag; the number card flips out of the tape head.
- Text: "TRUE BASE" holds. The card shows "0". Captions FROM ITS / TRUE BASE,
- VO: VO7 "From its true base,"
- Sound: a riser starts, with a paper zip for the tape.

**20.40-23.30 · THE CLIMB**
- Picture: a tilt-up from -4.9° to 0.0° with ease-in-out and sub-frame motion blur at the peak speed (about 25 px/frame). The face scrolls down; the tape head climbs from y 760 to y 250 and the card rides with it (from y 770-1178 to y 260-668); Everest slides down on the right. At about 21.85 the tape head passes Everest's peak side by side, at y ≈ 495, with the counter at about 29,000. On "thousand" (22.95) the head clicks onto the summit point (x 540, y 250).
- Text: the digits roll with the tape head: 56,000 x (head height above the true base) / 17,170 m. "ABOUT" stamps on above the digits on "about" (21.90). "56,000" lands on "thousand" (22.95). "TRUE BASE" fades 21.60-21.80, before it reaches y 1500. Captions MAUNA LOA STANDS (to 21.90), then suppressed.
- VO: VO7 "...Mauna Loa stands about fifty-six thousand"
- Sound: tick_counter accelerating; an impact and a paper click on "thousand".

**23.30-24.45 · HERO PULL-BACK to POSE H**
- Picture: vfov 6° to 11.5°, pitch 0° to -2.0°, the summit edge held at y 250 (23.30-24.20). The whole column in frame: the true base at y 1340 and the tape running from base to summit. Everest stands on the same base and reaches 52% (peak at y 778).
- Text: "FEET" stamps on under the digits on "feet" (23.38). "TRUE BASE" returns at the tape's foot (x 76-560, y 1350-1460) at 23.95. Captions suppressed.
- VO: VO7 "...feet tall." (to 24.83)
- Sound: the impact tail and a music sustain.

**24.43-25.35 · STACK (gag)**
- Picture: a second Everest drops from above the frame onto the first one's peak and lands at 25.13 (0.3 s after "tall") with a dust puff and a small squash. Its tip ends 34 px above the summit edge (gate 25-45 px): two Everests are just over one Mauna Loa. The card (x ≤ 524) and the stack (x 572-712) never touch.
- Text: the card and "TRUE BASE" hold; 56,000 is landed for about 2.4 s in all.
- VO: (none)
- Sound: a drop whoosh, then thunk_heavy at 25.13 (gag) and a music button.

**25.35-26.35 · SNAP-BACK (a 1.0 s comic rewind)**
- Picture: the card and the tag flip away (25.35-25.55). Both Everests tip and fall out of the frame bottom (25.35-25.65). The cut slams shut toward the camera like a door (25.45-25.75). A crash move flies back up the same straight line to near POSE A (25.60-26.35): vfov 11.5° to 30°, sub-frame motion blur; the sea rushes back up the flank and stays at least 40 m below the camera.
- Text: caption SOMEBODY TELL (from 25.78).
- VO: VO8 "Somebody tell" (from 25.78)
- Sound: a reverse-tape zip (gag), a reverse blade on the slam, then a water rush. Music out by 26.20.

**26.35-27.40 · SETTLE into POSE A**
- Picture: position, heading, pitch and vfov (30° to 34°) all reach velocity 0 at 27.40. The unmoved honu is readable from about 26.4. The last surge runs up the black sand and crests at the honu's tab at 27.40 with velocity 0: that is frame 0.
- Text: the postcard drops back in at 26.50 with a 3% overshoot and is settled by 26.90, identical to frame 0. Caption THAT TURTLE: (gone at 27.13).
- VO: VO8 "...that turtle:" (to 27.13), then about 0.27 s of silence.
- Sound: the water rush gives way to the surf bed by 26.60; a paper flap at 26.50; surf only from 27.13.

27.40 = frame 0. That is 822 frames at 30 fps; frame 822 is never rendered.

## 3. Hook

- VO from 0.06 s: "This beach is on a mountain almost twice as tall as Everest." (12 words, ending at 4.25 s; the paradox "This beach is on a mountain" is spoken by about 1.4 s). The sentence is complete and starts its own take; on the replay it is the message the last line asks for ("Somebody tell that turtle:"), so it opens as a stressed, falling statement.
- Frame 0 = the last frame: POSE A, a 600 m aerial oblique 3 km off Punaluʻu, looking up the slope at Mauna Loa: turquoise surf on a black-sand crescent; a giant paper honu basking on the sand (plainly a paper cut-out of a real photo); green Kaʻū slopes climbing to Mauna Loa's broad dome on the skyline; the off-white postcard "ALMOST TWICE / EVEREST" in the sky, 3 words that read in about 1 s with the sound off.
- In the swipe window: frame 0 is a wave at its run-up crest, the backwash starts at once and the whole sea begins to sink; on "mountain" (0.95 s) the ocean plunges, a white foam rim races away from the beach and a dark basalt flank rises below the coast; at 2.55 s the postcard tips into the falling sea. By 2 s a famous turtle beach has visibly lost its ocean: not travel footage.
- The question: a beach sits at sea level, so how can it be on a mountain almost twice Everest? The picture starts answering on "mountain".

## 4. Payoff

**The climb and the number (19.65-23.30).** On "From" a paper measuring tape starts unrolling from the TRUE BASE tag, at the bottom of the dent. The camera climbs the sliced face; the tape head climbs with it, carrying the ink-on-paper number card. At about 21.85 the tape head passes Everest's peak side by side with the counter near 29,000: the viewer feels Everest left behind before the number lands. "ABOUT" stamps on with "about"; "56,000" lands on "thousand" as the tape head clicks onto Mauna Loa's summit; "FEET" stamps on with "feet".

**The proof frame and the gag (23.30-25.35).** On "feet tall" the camera pulls back to the hero frame: the whole column from the true base to the summit, the tape running its full height, and Everest on the same base reaching 52%. 0.3 s after "tall" a second Everest drops onto the first with a thunk, its tip just 34 px above the summit edge: "almost twice", proved on screen with no second number, and a laugh. The 56,000 card stays on screen, landed, for about 2.4 s.

**The button (25.35-27.40).** 0.95 s after "tall" a 1.0 s comic snap-back runs: the cut slams shut, both Everests topple out, the camera crash-zooms up the axis while the sea rushes back, and it lands on the giant paper turtle, unmoved, as Rodney says "Somebody tell that turtle:". First-time viewers get a finished joke; the replay delivers the message.

**Funnel note:** the one payoff Short allowed to spend the 56,000-ft true base. Keep the hold (never before D+7; planned D+11). The long-form is not changed.

## 5. Loop check

**Lines, as one passage:** "Somebody tell that turtle: this beach is on a mountain almost twice as tall as Everest." Plain English: a colon introducing a reported message. The hook is a complete sentence in its own take, so it works cold and as the continuation. k08 is generated with k01 as next_text, so it ends open; k01 can carry k08 as previous_text, and the fresh takes are kept for the cold test. Seam silence about 0.33 s (a colon pause): 0.27 s after "turtle" plus about 0.06 s before "This".

**Frames.** The last frame (821, at 27.367 s) and frame 0 share the same camera (POSE A: 19.1101 N, 155.4971 W, 600 m, heading 344.7°, pitch -3.0°, vfov 34°), the same POST grade and sun, and the same state: the sea at 0 m with a wave at its run-up crest at the honu's base tab and water velocity 0; surf and honu flutter on a loop clock (surf period L/5 = 5.48 s, flutter L/10 = 2.74 s); the honu at rest and the postcard settled (from 26.90) in the same place; no tags, card, tape or Everest; the cut closed; no caption (the last card is gone at 27.13; the first appears at 0.06).

**Motion.** Position, heading, pitch and vfov all reach velocity 0 at 27.40 (the snap-back decelerates from vfov 30° to 34° and to rest) and all ease away from rest at 0.00, so there is no lens-breathing gap. The camera turns around like a pendulum at the seam (arrives moving toward the coast, leaves easing back down the axis); the water does the same (rises to the crest, then backwashes). Every channel sits at a natural hang point.

**Audio.** The surf bed is one seamless loop of exactly L, tail crossfaded into head, the run-up wash on the seam. VO edges get 5-8 ms fades. Music is silent from 26.20 through 0.40. No SFX crosses the seam.

**After the TTS retime:** recompute L; set the surf period to L/5 and the flutter period to L/10; re-cut the surf bed to exactly L; re-key the run-up crest to t = 0 ≡ L.

**QC:** first/last-frame MAE ≤ 5/255; concatenate the Short with itself and run temporal_scan.py (no "cut" or "flash"); loop it 5 times on a phone speaker and listen at "turtle: | This" for any click, loudness step or pitch jump; play 0.0-2.0 s cold on a phone to check the hook's prosody.

## 6. Facts

Every claim is inside spine #2 and #3 or the ep02 ledger. No fact VERIFY is open; the open items are assets and lexicon only.
1. **"This beach is on a mountain"** (Punaluʻu Black Sand Beach, 19.1361 N, 155.5047 W). VERIFIED: the USGS Geologic Map of the Island of Hawaiʻi (Wolfe and Morris 1996), served by the Hawaiʻi Statewide GIS layer "Geologic Units", gives volcano "mloa" here: Kaʻū Basalt, Qk1y, 3,000-5,000 yr (point-queried by the writer and re-queried by the panel on 2026-11-08). Kīlauea's Puna Basalt begins about 1 km NE (19.145 N, 155.495 W); at 3 km out, POSE A frames only ±0.5 km of shore, west of that contact.
2. **Hook and postcard "almost twice as tall as Everest".** Spine #2: about 17,170 m (56,000 ft) from the true base; spine #3: Everest 8,849 m (29,032 ft); ratio 1.94 (ledger C6-07). The narration says "almost" and names Mauna Loa every time.
3. **"It's Mauna Loa, and most of this mountain is underwater."** Spine #2 (USGS Volcano Watch, "How high is Mauna Loa?"): 4,170 m above sea level and 5,000 m below to the sea floor, so 55% is under water measured from the sea floor (76% from the true base). Wording per C3-02 ("mountain" or "height", never volume) and C12-01. The section draws it true: 55% of the column below the in-plane 0 m line.
4. **"From the sea floor, it already beats Everest."** Arithmetic on the same Volcano Watch figures: 4,170 + 5,000 = 9,170 m (30,080 ft) against 8,849 m, a 3.6% margin. ETOPO 2022 along this axis (computed 2026-11-08): -5,057 m at 150 km, -5,084 m at 130-140 km; the claim holds for any sea-floor depth beyond about 4,680 m. ADD to the ledger: "C6-xx Mauna Loa from the sea floor vs Everest", verified (arithmetic on a primary source).
5. **"But that's not the bottom."** Spine #2 "from its true base"; ledger C6-04.
6. **"It's so heavy, it pushed the sea floor down by miles."** Spine #2: the sea floor "depressed ... another 8,000 m"; the Moho "bowed downward by as much as 8 km". C6-05: "by miles" is safe. No number in the animation; the band sinks almost level in the 9 km frame (no false bowl); the shape is carried by the metaphor.
7. **"Bowling ball, meet mattress."** The long-form's metaphor (brief Ch6; s164), in new words. No claim.
8. **"From its true base, Mauna Loa stands about fifty-six thousand feet tall."** / ABOUT 56,000 FEET. Spine #2 (USGS Volcano Watch: "total relief of Mauna Loa, from its true base to its summit, is about 17,170 m (56,000 ft)"); ledger C6-06. The USGS Mauna Loa page gives "17 km (55,700 ft)", which "about" also covers. "From its true base" is on screen the whole time (TRUE BASE tag and card joined by the tape). The counter runs on the USGS figures (base -13,000 m, summit +4,169 m), scaled by 0.3% so it lands exactly on the round figure; it never shows a wrong value.
9. **Picture: Everest on the same base reaches 52%** (8,849 / 17,170), true only with a full-height Everest on a pedestal (C3-03, C6-07). The counter passes about 29,000 at Everest's peak (spine #3, 29,032 ft).
10. **Stack gag:** two Everests (17,698 m) top Mauna Loa (17,170 m) by 528 m = 34 px at 15.73 m/px; a playful prop gag that claims nothing beyond "almost twice".
11. **On-screen tags:** MAUNA LOA (the volcano), SEA FLOOR (-5,000 m, spine #2), EVEREST (the prop), TRUE BASE (the USGS phrase, C6-06); the postcard repeats item 2; no qualifier is dropped.
12. **"Somebody tell that turtle:"** A joke. Honu basking at Punaluʻu is documented (Wikipedia, Punaluʻu Beach) but not narrated.

**Staging fact behind the design:** ETOPO 2022 shows a ridge 100-110 km down the axis (-3,770 m on the axis, -2,100 m 10 km WSW). With the engine's curvature it hides everything at the summit plane below about +130 m from the draft's POSE F, so both Everest comparisons sit in the cut plane, where curvature cannot change the 39 px margin.

**Still open (assets and lexicon):** VERIFY that the turtle photo is public domain (a federal-employee credit line from NOAA Fisheries or USFWS, not a permit holder's); if none passes, use the S12 paper sunbather and change VO8 to "Somebody tell that sunbather:". VERIFY a PD or CC0 bowling-ball photo, or model a glossy ball with finger holes and print it on the card. Use only public-domain coastal DEM and ortho (NCEI, USGS 3DEP, NOAA or USGS orthos). The lexicon's wehewehe.org check for Mauna Loa. Add Punaluʻu and Kaʻū to the lexicon before any voicing.

## 7. Renders: new for this Short vs reused

New, for this Short only. Every shot is a new 1080x1920 camera pass; no frame is cut from the long-form, and the long-form does not change.
1. **POSE A aerial plate:** 600 m up, 3 km off Punaluʻu. Terrain: the NCEI Hawaiʻi coastal DEM plus USGS 3DEP 10 m, blended into the HMRG/ETOPO Big Island terrain. Drape: a 0.5-1 m public-domain ortho at the coast. Water: turquoise with surf, a run-up crest and backwash, all on the L/5 loop clock (shared periodic water, shorts_plan.md 5B). Sky gradient deep blue to pale haze. The paper honu standee (cutout.py, card.py; warm paper edge, base tab, contact shadow, flutter on L/10). FRAME-0 GATE: a phone test of the frame-0 still with the teen panel ("real place or game?"); if it fails, go to 1,000 m and 5 km out, re-solve the card and skyline layout, and keep the identical pose at both ends.
2. **The early drain and the dive:** backwash from 0 s, the plunge from 0.95 s, then the dolly-zoom from POSE A through POSE M to POSE S. Anti-clone seabed: dark basalt, olive-brown sediment drapes, reef steps, desaturated red-brown clay; never a pale tan basin. A subtle wet-and-salt bathtub ring at 0 m. No gauge, countdown, dashed line or arrows.
3. **The moving slice:** a vertical ENE-WSW cut sweeping from the camera to the summit plane; the section face from the long-form's Ch6 strata textures, with an in-plane 0 m wet line and a 14 px sediment band; mean luma ≥ 70. The cake cut is look-book upgrade U19, which the long-form's Ch6 also needs: built once in the shared engine (default-off for any scene that does not call it) and used by both; the Short does not change how the long-form uses it.
4. **Everest in the plane:** re-crop the long-form's everest_h16.png to a 2.2 km footprint, pin the summit at 8,849 m above the band, plain grey pedestal, 5 px white outline, 50 m in front of the face; the stage lift, the 2% overshoot, the settle and the hop gag.
5. **The drop under the band, the 8 km dent** (Everest rides down, rock fills in), and the bowling-ball paper inset (a card, a ball cut-out or modelled ball, a quilted paper mattress with a warped dent).
6. **The climb, the hero shot and the stack:** the tilt-up with sub-frame motion blur (look U14; peak about 25 px/frame); the paper tape and the riding number card; the pull-back to POSE H; the second Everest with its dust puff.
7. **The snap-back and the settle:** the cut slam, both Everests falling, the crash move with motion blur; the refill clamped 40 m below the camera; velocity 0 on every channel and a water run-up crest exactly at L.
8. **Type and paper:** the postcard (Anton ink on #F6F1E4, blank stamp); tags in Barlow Condensed 800 (MAUNA LOA, SEA FLOOR, EVEREST, TRUE BASE); the number card (ABOUT / 56,000 / FEET) and the 32 px tape; the house caption track. No black boxes, accent words, yellow, scrims, arrows or dashed lines in the picture layer.
9. **Audio:** a new Rodney VO from tts.py segments with the loop wrap; a new mix at -14 LUFS with VO at least 12 LU over the music; a seamless L-length surf bed; a music edit (the stop on "But" at 11.25, strings at 13.4, a riser and ticks on the climb, a button on the thunk, out by 26.20); comic SFX only on the gags, in the gaps between lines.

**Engine rules** (from lab/drain/terrain.js): TerrainStage curves geometry by d²/2R (1.77 km at 150 km), so Everest, the band, the tape anchor and the slice are in-scene geometry with the same vertex transform; every 2D tag is placed with S.project(), never flat overlay maths; in the section shots the camera stays 1.56 km above the local floor and frames by tilt and zoom only.

**Reused as-is (assets only, no long-form footage):** the HMRG 50 m and ETOPO 2022 Big Island terrain and its bake, with the long-form's sun; the water-plane drain and refill shader; the Ch3 SRTM Everest asset; the Ch6 cut-away strata and the sag curve; the T.slot odometer re-skinned as ink on paper; the shared POST grade; SFX library cues (whooshes, impact_deep, thunk_heavy, tick_counter, paper flap); the long-form's score stems if they suit, otherwise a library cue. Long-form elements it is rebuilt from: Ch3 Everest at the same scale and the Mauna Loa beat; Ch6 the slice, the dent, the bowling ball, the 56,000 counter and Everest on the same base; the refill.

**QC before sign-off:** a phone sheet of every shot's middle frame; the [typeqc] log (every cap ≥ 80 px; at most one block plus one label at a time); luma ≥ 70 per shot; on the 10.10 s frame Everest's peak 30-45 px below the summit edge, and at least 10 px below on the overshoot and hop frames; on the 24.3 s frame Everest reaches 50-54%; on the 25.13 s frame the stack's tip 25-45 px above the summit edge; along the dive and snap-back line the camera at least 1 km above terrain and the water at least 40 m below it; the loop gates above.

## 8. Title, description, link

**Title** (48 characters): This Beach Is on a Mountain Almost Twice Everest. **Backup** (37): Mauna Loa Is Almost Two Everests Tall. Both pass the title regex and the update's clone words (no drained/drain, hidden/hiding, bottom/beneath, nobody, found) and avoid "taller than Everest". Probe 2026-11-08: no Short uses this premise ("this beach is on a mountain": nearest a 20K Short about Salt Lake City's old shoreline; "mauna loa almost twice everest": only "taller/bigger than Everest" Shorts at 0.2K-37K).

**Description:**

> Punaluʻu, the black sand beach on Hawaiʻi's Big Island, sits on the lava of Mauna Loa. Measured from its true base, miles below the sea floor, Mauna Loa is about 56,000 feet tall: almost twice Everest.
> The full film drains the ocean around Hawaiʻi, step by step: Why Can't You See Most of Hawaii? (Look Down) [long-form link]
>
> Sources: USGS Volcano Watch, "How high is Mauna Loa?"; USGS, Mauna Loa volcano page; USGS Geologic Map of the Island of Hawaiʻi (Wolfe and Morris, 1996), via the Hawaiʻi Statewide GIS Program; Mount Everest 8,848.86 m (Nepal-China survey, 2020).
> Data and images: NOAA NCEI ETOPO 2022 and Hawaiʻi coastal DEM; USGS 3DEP; University of Hawaiʻi SOEST HMRG multibeam synthesis; NASA SRTM (Everest); coastal imagery [exact NOAA or USGS ortho credit], public domain; turtle photo [exact NOAA Fisheries or USFWS credit], public domain; bowling ball photo [credit, if a photo is used].
> #Hawaii #MaunaLoa #Everest

**Link and timing:** set the Short's Related Video to "Why Can't You See Most of Hawaii? (Look Down)" (the long-form title stays exactly as approved). Publish no earlier than D+7 (planned D+11), only with the owner's OK. Nothing in the long-form changes.

**Pinned comment:** "Have you seen the turtles at Punaluʻu? Did you know what they were lying on?"

**Pronunciation** of the Hawaiian names written above, in case they are ever voiced: Punaluʻu poo-nah-LOO-oo (VERIFY on wehewehe.org); Hawaiʻi hah-WHY-ee (glottal catch before the last "ee"); Mauna Loa MAO-nah LOH-ah.

**Checks run on this text:** the whole-word AI grep from the playbook (no hits); no emojis; no sources on screen.

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 77 (the highest of the 7). All 7 must-fixes are in: the loop line is its own clause and the hook a fresh sentence in its own take; the first visual event on frame 0 (backwash) and the plunge on "mountain"; the dead air after the payoff cut (stack 0.3 s after "tall", a 1.0 s snap-back, speech back 0.95 s after "tall"); the number set as ink on a paper card (no yellow, no scrim); both Everest comparisons in the cut plane as in-scene geometry with S.project() tags and measured pixel gates; zero velocity at L on every camera channel and a recomputed loop clock; POSE A as a 600 m aerial with the phone gate kept.
