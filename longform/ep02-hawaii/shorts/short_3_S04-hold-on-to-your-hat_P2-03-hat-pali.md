# Short 3 (S04-hold-on-to-your-hat + P2-03-hat-pali): "Where Did This Volcano's Other Side Go?"

| | |
|---|---|
| Release | **D+3**, same clock hour as the long-form (slot 3 of 7) |
| Length | about 26.4 s (792 frames, 0-791); final L from the real TTS |
| The one big number | MORE THAN 100 MILES |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps, VE 1.0 in every shot |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

All times are estimates from the Rodney model; every picture cue locks to the real word timestamps.

## Integrator changes (2026-11-08)

1. Captions follow the house spec (shorts_plan.md section 4): Anton cap 80, centred x 460 / y 1515. The writer's cap-77 box at y 1452-1529 and its flag to the owner are replaced by the one house position for all 7.
2. TTS settings: the locked long-form settings (`"settings": {}`); stability 0.35 / style 0.4 only as an A/B take.
3. Known echo, accepted: the long-form has the same Pali hat gag line, "Hold on to your hat." (s029). Here the idiom is new narration inside a new sentence, it is the loop device, and the physical gag is new (the hat lifts and comes back, the missing side re-forms, he ducks). Flagged for the owner; if he wants zero overlap, the fallback loop line is "So if you're ever up here, mind the wind, because... this volcano is missing a whole side." (weaker).
4. Add Kailua, Kāneʻohe, Mōkapu and Lanihuli to the lexicon (not voiced here).

## 1. Narration and TTS

**Voice:** "Rodney - Clear Educator" (`eY2VJs4Gi8QKG2RV01sS`), `eleven_v4`, passed explicitly. Same settings for every take: the locked ep02 long-form settings, speed 1.0; never above 1.05. Generate only after the owner OKs this text, then re-time every cue from the real word timestamps.

**On-screen order** (61 words, a loop of about 26.4 s; estimate from Rodney's measured eleven_v4 take, 32 words in 12.16 s; model 0.19 s per syllable + 0.36 s per comma + 0.45 s sentence-final lengthening):
> This volcano is missing a whole side. Long before anyone lived here, it slid into the sea. One of the largest landslides on Earth. Drain the ocean, and there it is. In pieces. The biggest piece? Bigger than Manhattan. And the wreckage runs for more than a hundred miles. So if you're ever up here, hold on to your hat, because...

**Exact TTS strings** (three takes, identical settings):
- **TAKE A** (the story, 2.76-17.91 s): "Long before anyone lived here, it slid into the sea. One of the largest landslides on Earth. Drain the ocean, and there it is. In pieces. The biggest piece? Bigger than Manhattan."
- **TAKE C** (the key-statistic line in its own take, 18.66-21.54 s): "And the wreckage runs for more than a hundred miles."
- **TAKE B** (the loop seam, ONE performance): "So if you're ever up here, hold on to your hat, because... this volcano is missing a whole side."
  - Split at the zero crossing inside the pause after "because...". The tail plays at 21.84-25.85 s; the head ("this volcano is missing a whole side.") plays at 0.05-2.51 s.
  - The head is the main clause, so it carries a falling statement cadence and no hedge word up front.

**Takes:** render each take 3 times (`"take": 1, 2, 3` in the tts.py segment) with identical settings; the owner picks by ear. ASR check with faster-whisper small.en and medium.en: accept only if "landslides", "Manhattan" and "a hundred miles" come back as scripted.

**TAKE B acceptance:** the head played alone must sound like a confident cold open (full onset energy on "This", a firm fall on "side", no trailing continuation tone). If none of 6 takes passes, use a separate take of "This volcano is missing a whole side." as the head and keep the seam pause at 0.6 s or more; the owner judges that seam by ear.

**Edit pauses** (set from word timestamps, never typed into the TTS): 0.25 s after "side."; 0.30 after "sea."; 0.55 after "Earth."; 0.66 in total between "ocean," and "and" (the water visibly falls first); 0.75 after "is."; 0.45 after "pieces."; 0.55 after "piece?" (the guess beat, covered by the camera's dive); 0.75 after "Manhattan." (the slam lands); 0.30 after "miles."; 0.55 after "because..." plus 0.05 s head silence = 0.60 s across the cut (pad with room tone if TAKE B's natural pause is shorter).

**Flex rule:** if L comes out under 25.5 s, add up to 0.5 s after "Manhattan." and up to 0.3 s after "pieces."; if over 29 s, trim pauses first. Never cut the hook or the loop line; never speed Rodney past 1.05.

**Pronunciation:** Rodney speaks no Hawaiian word in this Short ("here" replaced the draft's spoken "Oʻahu"), so no respelling and no U+02BB go into the TTS text. Lexicon notes for every Hawaiian word in the package (on screen, title, description, tags, pinned comment, production notes):
- Oʻahu: oh-AH-hoo [oˈʔahu]; TTS token if ever voiced "oh-AH-hoo"; never "oh-WAH-hoo".
- Hawaiʻi: hah-WHY-ee [həˈwɐiʔi], light catch before the final "ee".
- Koʻolau: koh-oh-LAO [koˈʔolɐu], "lau" as in cow.
- Nuʻuanu: noo-oo-AH-noo [nuʔuˈwɐnu], four syllables with a glottal break.
- Pali: PAH-lee [ˈpɐli]; never PAL-ee or PAY-lee.
- Kailua: kye-LOO-ah [kɐiˈluwɐ]. Kāneʻohe: kah-neh-OH-heh [kaːneˈʔohe]. Mōkapu: moh-KAH-poo [moːˈkɐpu]. Lanihuli: lah-nee-HOO-lee [lɐniˈhuli]. These four are not yet in lexicon.json; add them.
- Lexicon status is DRAFT (not test-rendered, not checked on wehewehe.org, not heard by a Hawaiian speaker). This Short voices none of them.

## 2. Second-by-second table

**Spec.** 1080x1920, 30 fps, L ≈ 26.4 s (792 frames); the loop cuts from frame L-1 to frame 0. Safe text box x 72-849, y 200-1529 (captions per house spec). Every cap ≥ 77 px. VE 1.0 in every shot. One low morning sun (azimuth ~100°, elevation ~18°). The trade wind blows FROM the northeast, so cloud streaks drift southwest. No boxes, plates, arrows, depth gauge or sea-level line.

**Text style.** White #F4F6FA, navy #0B1D28 stroke of 0.13 x cap, drawn after the grade. Anton for the headline, numbers and any string with an ʻokina (Anton's U+02BB is the correct 6-shaped turned comma); Barlow Condensed 800 for other labels. Load both "latin" and "latin-ext" subsets.

**Captions:** house spec (Anton cap 80, ALL CAPS, 1-3 words per card, white with one active word cyan #00E5FF, no box, synced within 0.1 s, no card shorter than 0.3 s, centred x 460 / y 1515). The widest card, "THE WRECKAGE", is about 511 px at cap 80 (x 205-716).

**0.00-2.55 · HOOK, camera C0, the missing piece**
- Picture:
  - Camera: a high oblique over Oʻahu's windward Koʻolau. DEM-checked start pose 21.240 N, 157.929 W, altitude 45 km, heading 45, pitch -58, vertical FOV 50, pushing in at 1.2%/s with zero roll.
  - Leeward Koʻolau ridges fill y 1250-1920. The straight windward coast crosses at about y 1180; the Pali at about x 540, y 1250.
  - THE GHOST, the missing northeast side, is attached beyond the coast and fills y about 560-1180 from edge to edge; open sea above it, under the headline. It is a lit, translucent volume made by mirroring the surviving leeward flank across a NW-SE line through the Kailua-area caldera. Fill cool white #EAF6FF at 22% on shaded facets and 38% on sunlit ones, so the real coast and sea show through; a crisp 6 px white edge including a clean footprint line where it meets the sea; 200 m contours at 35% white.
  - Frame-0 motion: the camera push, trade-wind cloud streaks crossing the crest (periodic with period L), and one light sweep along the ghost edge starting at 0.0.
  - Rebuilt from: the long-form Ch2 island terrain, the Nuʻuanu drain tile and the shared grade, with a new vertical camera. The ghost is a new, Short-only asset.
- Text: headline at full opacity from frame 0, fading out 2.55-2.95. Line 1 OʻAHU’S: Anton cap 96, x 80-408, cap top 236. Line 2 MISSING SIDE: Anton cap 120, x 80-770, cap top 368. Captions THIS VOLCANO / IS MISSING / A WHOLE SIDE.
- VO: H (0.05-2.51): "This volcano is missing a whole side." ("missing" at about 1.05-1.44.)
- Sound: the paper-flap and gust tails carry over from the previous loop. Wind bed. Music bar 1: a playful pizzicato and marimba groove over a warm low pad.

**2.55-4.60 · PULL-BACK to R1 (one motion only)**
- Picture: an eased log-altitude pull-back from 45 to 220 km; pitch -58 to -50, heading 45 to 42. R1 sits about 120 km SW of Oʻahu's NE coast: the coast lands at about y 1375, the island fills the bottom, and the 200 km line toward Tuscaloosa runs up to about y 390. The ghost shrinks into a white lobe on the island's NE side. 4.05-4.60, after the camera stops: white crack lines (4 px) draw across the ghost and split it into 6 pieces whose outlines match the real block field. Rebuilt from: the long-form Ch2 drain tile (script 2:00-2:14), new camera.
- Text: OʻAHU place label, 3.95-6.20: Anton cap 84 (ʻokina-safe), centred x 540, cap top 1320, baseline 1404; lands 0.2 s before "here". Captions LONG BEFORE / ANYONE / LIVED HERE,
- VO: A1 begins (2.76): "Long before anyone lived here,"
- Sound: pull-back whoosh, then a dry stone crackle on the cracks.

**4.60-9.35 · THE SLIDE, on the held R1 camera** (it creeps 1%/s and does not climb)
- Picture: on "slid" (4.92) the 6 pieces slump and skid NE (up the frame), 4.92-7.60. Each leaves a white churn streak as it goes under; no ring wave and no tsunami imagery. Underwater the pieces stay faintly visible, fading to 15% with depth, and come to rest at the real block positions by 7.8: the biggest at Tuscaloosa (about 22.07 N, 157.08 W, about 108 km out). The streaks fade 7.6-9.0. Rebuilt from: new, Short-only animation.
- Text: captions IT SLID / INTO THE SEA. / ONE OF THE / LARGEST / LANDSLIDES / ON EARTH.
- VO: A1 ends (4.71-6.38): "it slid into the sea." A2 (6.68-8.94): "One of the largest landslides on Earth."
- Sound: a deep rumble and grind 4.9-7.6 (energy under 300 Hz, no sting). Water churn. The music thins.

**9.35-14.05 · THE DRAIN, on the same held R1 camera** (one live change; the composition lasts 9.5 s from 4.6 to 14.05, inside the 10 s limit)
- Picture: water level keyframes 0 m at 9.35; -1,200 m at 10.30; -2,700 m at 11.15 (the first crown, Tuscaloosa, GMRT summit -2,691 m, breaks the surface on "there"); -3,300 m at 12.00; -3,750 m at 12.80; -4,000 m at 13.20. Oʻahu's submarine flank swells out of the sea as a dark mountain; a white foam rim slides down its slopes and around each block. The faint underwater ghost pieces cross-fade into the real blocks as they surface: the pieces are still there. Crown order from the HMRG/GMRT crown depths. Materials: blocks dark basalt with a wet sheen that fades over 1.5 s; sediment drape dark olive and grey-brown at value ≤ 0.40; turquoise water lingers in the deep moat; tan ≤ 10%, red ≤ 3%. Rebuilt from: the long-form Ch2 drain (script 2:00-2:30), new vertical camera and keyframes.
- Text: captions DRAIN / THE OCEAN, / AND THERE / IT IS. / IN PIECES.
- VO: A3 (9.49-10.29): "Drain the ocean," then 0.66 s, then (10.96-12.23) "and there it is." A4 (12.98-14.03): "In pieces."
- Sound: drain riser and gurgle 9.35-11.2. Three thumps in total (no SFX motif more than 3 times): on the first crown at 11.15 and on the last two crowns under "In pieces". The music drops to pad and pulse.

**14.05-16.30 · THE GUESS BEAT** (the longest smooth camera move covers the question and the pause)
- Picture: 14.45-16.20 an eased dive from R1 to slam camera R2 over the biggest block. R2 at altitude about 42 km, pitch -62, heading set so the block's long axis (measured on the grid) runs up the frame. The block's base, about 27-30 x 17-18 km, fills about x 260-890, y 340-1450. On "piece?" (15.1-15.6) the block's -4,100 m base contour traces once in 6 px white, so the "piece" is defined. The music drops out at 15.9.
- Text: captions THE BIGGEST / PIECE?
- VO: A5 (14.48-15.73): "The biggest piece?" then a 0.55 s pause.
- Sound: a flight whoosh and a soft tick on the trace. Wind bed only in the pause.

**16.30-18.40 · THE SLAM**
- Picture: 16.30 a TRUE-SIZE PAPER MANHATTAN drops in from above the top edge as its contact shadow grows: a cut-out of a public-domain Landsat 9 true-colour scene masked to the US Census TIGER New York County outline, Central Park's green rectangle readable, warm off-white 3 px paper edge. 16.88 on "Man-": it SLAMS flat onto the block along its long axis, with room to spare at both ends and sides; at 37 px/km it covers about x 600-740, y 500-1300. A puff of dark sediment dust, a 4-frame 6 px shake; the sheet wobbles and settles flat over 6 frames. No orange fill, so the red gate is not at risk. Rebuilt from: the long-form Manhattan hero beat (script 2:32-2:37), recomposed vertically with a new paper-photo asset.
- Text: MANHATTAN label 16.88-18.90, popping from scale 1.12 to 1.0 over 6 frames: Barlow 800 cap 84, tracking 0.04, x 88-681, cap top 700, left of the block. Captions BIGGER / THAN / MANHATTAN.
- VO: A6 (16.28-17.91): "Bigger than Manhattan."
- Sound: a drop whoosh 16.3-16.88, impact_deep at 16.88 and a paper slap. The music comes back on the slam.

**18.40-21.75 · PULL-BACK AND FAN (the peak)**
- Picture: 18.40-19.90 an eased log-altitude pull-back from R2 to R3 (the R1 framing, used for the second and last time). The paper Manhattan stays on the block as a light sliver. 19.30-21.00 the Nuʻuanu debris footprint draws on from Oʻahu's NE coast to the toe and reaches the toe on "miles" (20.89): hero orange #FF5A36 at 25% fill (on the dark seabed that blend stays under the gate's saturation threshold); 6 px white outline; a bright white leading edge with a head dot; traced from USGS I-2809 and checked against the hummocks on the HMRG/GMRT grid. Rebuilt from: the long-form "more than a hundred miles" beat (script 2:40) and its slide-footprint device, on a new camera.
- Text: NUMBER BLOCK (the one big number), in the left column over the drained floor west of the fan:
  - MORE THAN: Barlow 800 cap 80, x 88-603, cap top 250, in at 19.85 on "more".
  - 100: Anton cap 260, yellow #FFD23F, stroke 0.08 x cap, x 80-478, cap top 360. An odometer rolls 000 to 100 from 19.95 and lands on "hundred" (20.49) with a 4-frame bounce.
  - MILES: Barlow cap 96, x 88-407, cap top 650; pops on "miles" (20.89).
  - The block holds to 22.30 and fades out 22.30-22.70.
  - Captions AND THE / WRECKAGE / RUNS FOR, then suppressed while the number block shows MORE THAN / 100 / MILES.
- VO: C (18.66-21.54): "And the wreckage runs for more than a hundred miles."
- Sound: a pull-back whoosh, tick_counter 19.95-20.49, a soft thunk on MILES, and a warm (not ominous) swell.

**21.75-23.60 · REFILL AND RETURN** (no dead air: the tail starts 0.30 s after "miles")
- Picture: 21.75-22.65 the sea rushes back from -4,000 m to 0 as a cyan sheet over the dark floor. The fan and the paper Manhattan sink, their opacity following the water depth, gone by 22.50. 22.00-23.50 an eased push-in from R3 back onto the C0 push line (220 to 47 km, pitch -50 to -58, heading 42 to 45), arriving with its velocity matched to the C0 push. 23.00 on "up here": the paper tourist pops up on the Pali: hinge from 35° to 90° in 8 frames; base tab on the crest at about x 540, y 1250; 35% of frame height (head top at about y 578); he smiles at the camera with his hat on. He is the long-form's recurring public-domain photo cut-out: warm off-white 2-4 px edge, soft contact shadow, same sun. Rebuilt from: the long-form refill device and the Ch2 Pali tourist and hat (script 1:30-1:44), at map scale.
- Text: captions SO IF / YOU’RE EVER / UP HERE,
- VO: B tail (21.84-23.26): "So if you're ever up here,"
- Sound: a water-rush riser, a flight whoosh, a paper flap on the pop-up.

**23.60-25.95 · THE HAT GAG** (the physics follows the real wind; nothing falls off the Pali)
- Picture: 23.62 on "hold": a trade-wind cloud streak crosses the crest from the NE; his paper hat lifts about 150 px, flips once at 24.2, then hovers with its brim flapping. 25.01 on "because...": the hat drops; at 25.25 it lands back on his head with a paper squash. 25.25-25.95 the ghost of the missing side re-forms behind him, its fill rising from 0 to full and its edge drawing on from left to right. He glances at it (a 6-frame head tilt) and ducks: he slides down behind the Koʻolau crest on the leeward side (25.60-25.95) and is fully hidden by 25.95.
- Text: the headline fades in 25.75-26.35, opacity 0 to 1, at exactly its frame-0 position. The standee's head (y ≥ 578) never overlaps the headline (y 236-488). Captions HOLD ON / TO YOUR / HAT, / BECAUSE...; the last card ends at 26.20.
- VO: B tail continues (23.62-25.85): "hold on to your hat, because..."
- Sound: a gust whoosh with paper flutter at 23.6, a paper "pat" at 25.25, a paper flap on the duck at 25.6. A new gust whoosh starts at 26.2 and runs across the cut.

**25.95-26.40 · THE SEAM**
- Picture: the camera is on the C0 push line, the same deterministic shot function of t mod L as 0.00-2.55. The ghost is at full, the standee hidden, the headline at full from 26.35, the clouds back in their periodic positions. Frame L-1 is exactly one motion step before frame 0; frame 0 is not duplicated at the end. CUT to frame 0.
- Text: the headline at full opacity.
- VO: a 0.60 s voice pause; the sentence completes with VO H after the cut.
- Sound: the music is N bars with N x 4 x 60 / bpm = L (an estimated 13 bars at 118.2 bpm for 26.4 s). Bar N has no cadence and resolves into bar 1. The mix is rendered wrapped, with a 0.5 s crossfade into 0.0.

## 3. Hook

FRAME 0 is a high oblique over Oʻahu's windward Koʻolau, already pushing in. Beyond the island's straight northeast coast, a translucent white lobe is attached: the volcano's missing side (crisp white edge, faint contours, the real coast and sea visible through it). It fills about a third of the frame and ends in a clean footprint line on the sea. Above it, in open sea, the headline OʻAHU’S / MISSING SIDE (Anton, cap 96/120, upper third, with the correct 6-shaped ʻokina). Trade-wind clouds stream over the crest and a light sweep runs along the ghost's edge.

VO at 0.05 s: "This volcano is missing a whole side." (7 words; "missing" at about 1.05-1.44 s; the line ends at about 2.5 s, from the measured Rodney rate). The first caption card, THIS VOLCANO, is on screen from frame 0.

How this answers the swipe panel:
1. No longer a travel snapshot: the odd thing, a piece of a familiar island outlined as missing, is the subject of frame 0 and reads at 390 px (m_f0_phone390.jpg).
2. The line points at something visible: "This volcano" over the Koʻolau range, "a whole side" over the glowing lobe.
3. Works with the sound off: the headline names the anomaly and the place; burned captions carry every word.
4. No hedge word: "About" is gone, and the hook is the main clause of TAKE B, with an acceptance test and a fallback.
5. Realistic timing, from Rodney's one measured take.

Why the frame is no longer the eye-level lookout: from the lookout (bearings.py, 110 m hero grid) Kāneʻohe Bay is at 348°, the Lanihuli-side crest at 315°, Mōkapu at 29° and Kailua at 55°; an honest mirrored ghost (break line through the Kailua-area caldera, USGS) stands only 3-5° above the horizon, 5-8 km away, and renders as a flat pale band that reads as haze (pair2.jpg). From the high oblique the same ghost is a large, unmistakable missing piece (reg_f.png).

The premise is open: probes on 2026-11-08 ("where did this volcano's other side go", "oahu missing side volcano landslide", "nuuanu landslide oahu") found no Short on it; the best on-topic Short is the 1K "Hawaii Landslide: HUGE!". Hōlei Sea Arch collapse Shorts (1.6M and 371K) show "Hawaii falls into the sea" is live in the feed. No "taller than Everest", no number before 18 s, no greeting.

## 4. Payoff

The payoff escalates in four steps; the top step comes last, and each image over-delivers the words.
1. **"Drain the ocean, and there it is. In pieces." (9.5-14.0 s).** On the same fixed camera where the pieces slid under, the sea drains; the faint ghost pieces turn into the real dark basalt blocks as they break the surface, exactly where they sank. Cause and effect in one uncut shot.
2. **"The biggest piece?"** (a guess beat over the dive, base contour traced in white), then **"Bigger than Manhattan."** A true-size paper Manhattan from a real Landsat photo, Central Park visible, drops from the top edge and slams flat onto the block along its long axis with room to spare: dust, a shake, a paper wobble. The picture shows about 6-7 times Manhattan's area while the line modestly says "bigger". The laugh beat.
3. **"And the wreckage runs for more than a hundred miles."** (the peak) The camera pulls back to the slide framing; the debris footprint draws on from Oʻahu's own coast to the toe, dwarfing the island it came from. MORE THAN / 100 / MILES rolls in and lands on "hundred" and "miles": the one number, a quarter-plus of the frame tall.
4. **The gag payoff,** starting 0.3 s after "miles" (no dead air after the climax). The sea refills and the camera pushes back to the opening frame. The recurring paper tourist pops up on the Pali ("So if you're ever up here"); on "hold on to your hat" a trade-wind gust flips his hat up, and on "because..." it drops back onto his head. Then the missing side re-forms right behind him; he takes one look and ducks behind the crest. The idiom lands literally, the wind behaves as it really does at the Pali (the hat goes up and comes back; nothing falls off the cliff), and the unfinished sentence completes itself in the opening line.

Everything after the last fact (21.54-26.4 s) is narrated, except the 0.6 s seam pause.

## 5. Loop check

**Last line into first line:** "So if you're ever up here, hold on to your hat, because... this volcano is missing a whole side."
- Natural English: "hold on to your hat, because..." is the standard brace-yourself idiom; literal here (the gust has just flipped his hat; the missing side has just re-formed behind him).
- Recorded as one performance (TAKE B) and split in the pause after "because", so the intonation across the cut is continuous. The pause is 0.60 s (0.55 tail + 0.05 head); the duck's paper flap and the new gust sit inside it.
- Fallback (owner's ear): a separate head take with the pause kept at 0.6 s or more.

**Last frame against first frame.** Frame L-1 and frame 0 come from one deterministic shot function of t mod L, so the step from L-1 to 0 is one motion step, not a match cut.
- Camera: the same C0 push-in line at 1.2%/s, zero roll; the return push from R3 merges into this line with matched velocity by 23.5 s, almost 3 s before the seam.
- Ghost: full fill and edge in both frames (finished re-forming at 25.95).
- Tourist and hat: hidden behind the crest in both frames since 25.95.
- Headline OʻAHU’S / MISSING SIDE at full opacity and the same position in both (in from 26.35).
- Clouds and the edge light sweep repeat with period L. Grade and sun identical.
- Captions: none in the last frame (the BECAUSE... card ended at 26.20); THIS VOLCANO appears at frame 0. Caption cards switch hard by design, so the seam metrics are measured on the picture layer before captions.
- The big camera moves and the gag end before the final 0.45 s.

**Audio.** The VO ends on "because..." with a 5-8 ms fade. The new gust whoosh starts at 26.2 and runs across the cut. The wind bed and music are rendered wrapped with a 0.5 s tail-into-head crossfade. Music: N bars with N x 4 x 60 / bpm = L (13 bars at 118.2 bpm, or 12 at 109.1, or 14 at 127.3; pick after the real TTS). Bar N has no cadence and resolves into bar 1.

**QC gate:** first-to-last-frame MAE ≤ 5/255 and SSIM ≥ 0.97 on the picture layer; concatenate the Short with itself and run temporal_scan.py (no "cut" or "flash" at the join); the owner plays 3 consecutive loops on a phone with sound. Ear verdicts are his.

## 6. Facts

"Spine" = brief.md section 4; "ledger" = research/ep02/script/ledger_part1.json (production fact check of 2026-11-08).
1. **"This volcano is missing a whole side."** (on screen OʻAHU’S MISSING SIDE). Spine #6 (the Nuʻuanu slide, the Koʻolau collapse). Worded to the ledger's primary-source version (C12-21b): USGS Volcano Watch, "Oahu, Niihau and Kauai": "The caldera was bisected by the catastrophic collapse of the Nu'uanu landslide"; USGS 2016 geologic tour of Oʻahu: Koʻolau "forms the east side of the island". Ledger wording: "Its whole northeast side is lying out here." "Half" was dropped from hook and title: C12-21a marks it disputed (secondary sources only). VERIFIED.
2. **"Long before anyone lived here, it slid into the sea."** Spine #6, "more than a million years ago" (ODP Leg 200: 1.8-2.4 Ma; Wikipedia 1-1.5 Ma) against settlement around AD 1000. True under every estimate; no age spoken. VERIFIED.
3. **"One of the largest landslides on Earth."** Spine #6; USGS 2016: "one of the largest landslides in the world"; Moore et al. 1989: Hawaiian debris avalanches "rank among the largest on Earth". Never "the largest". VERIFIED.
4. **"Drain the ocean, and there it is. In pieces."** Spine #6; USGS 1995: the slide "deposited numerous blocks on the sea floor as far as 100 miles northeast of the island". Phrased as a thought experiment. VERIFIED.
5. **"The biggest piece? Bigger than Manhattan."** Spine #6 (USGS: "the largest of these blocks is about the same size as Manhattan Island"); brief section 7: if the block measures larger, say "bigger than Manhattan". Ledger C12-23b/23a: on GMRT the Tuscaloosa block's summit is -2,691 m and its base at the -4,100 m contour about 27 x 18 km (~380 km²); Moore et al. about 30 x 17 km; USGS 2016 "over 29 km (18 mi) long"; Manhattan about 59 km², 21.6 x 3.7 km. VERIFIED. The long-form says "bigger than Manhattan" too. Production check: lay the true-size TIGER outline on the grid's base contour before the slam (long axis 27 vs 21.6 km).
6. **"And the wreckage runs for more than a hundred miles."** (MORE THAN / 100 / MILES). Spine #6 (about 200 km); USGS 2016 "about 200 km (120 mi)"; ODP "more than 200 km"; USGS 1995 blocks "as far as 100 miles". Ledger C12-22: "more than a hundred miles" is the only wording all sources support. Matches the long-form. VERIFIED.
7. **"So if you're ever up here, hold on to your hat"** An idiom and a gag. Hawaiʻi DLNR (ledger C12-18): "Winds are usually so strong that one can lean against the wall of wind." No wind speed given.

**Visual honesty**
- Ghost: a sketch, never labelled; the description calls it a sketch. It is the surviving leeward flank mirrored across a NW-SE line through the caldera (USGS 2016: "in the Kailua area"), with a crest-height plateau out to the mirrored crest distance, then the mirrored leeward profile down to sea level about 16 km out; VE 1.0 (short03v3/ghost3.py).
- Six pieces: schematic; their resting places are the real block positions, the biggest at Tuscaloosa (about 22.07 N, 157.08 W).
- No tsunami imagery and no wave rings (brief must-fix 3).
- Hat physics follow C12-18: the trade wind blows from the NE, up the windward cliff, so the hat goes up and comes back. The draft's hat over the parapet is cut (it reversed the real wind). C12-18 also notes the 1795 Battle of Nuʻuanu: nothing falling off the Pali is ever the joke. The tourist ducks down the leeward side at map scale.
- Manhattan: true size, US Census TIGER outline, public-domain Landsat 9 imagery, on the real block.
- Footprint: VERIFY that the USGS I-2809 outline layer is legible enough to trace; otherwise use the Moore et al. 1989 figure.
- Depths: HMRG multibeam, GMRT and ETOPO 2022; the first crown uses GMRT's -2,691 m (Wikipedia gives -2,756 m).
- No Everest, no 56,000 ft, no dent. One spoken number ("a hundred") and one on-screen number (100).

## 7. Renders: new for this Short vs reused

Everything on screen is a new vertical render at 1080x1920, 30 fps. Nothing is cropped from the long-form, and the long-form is not changed.

**New cameras, assets and animation**
1. **C0**, the high oblique over the windward Koʻolau (0-2.55 s and 23.5 s to the end): one deterministic shot function of t mod L (push-in, cloud streaks with period L, edge light sweep, ghost state). Start pose 21.240 N, 157.929 W, 45 km, heading 45, pitch -58, vertical FOV 50; tune in a test still so the ghost fills y 560-1180 and the Pali sits near x 540, y 1250. Terrain: HMRG 50 m plus ETOPO 2022, with 3DEP 10 m on the island.
2. **The ghost asset** (Short-only): the mirrored ghost (ghost3.py, VE 1.0); a lit translucent shader (#EAF6FF at 22-38%, 6 px white silhouette and footprint edge, 200 m contours); crack lines and 6 pieces matched to the real block layout; the slide-and-sink animation (churn streaks, no ring waves, underwater fade to 15%, cross-fade into the real blocks during the drain); the re-form animation.
3. **R1/R3 regional camera:** about 220 km altitude, pitch -50, heading 42, about 120 km SW of the NE coast (verify the coast at y ≈ 1375 and the 200 km toe at y ≈ 390 in a test still). Drain keyframes as in the table. Seabed material pass: dark basalt, dark olive and grey-brown sediment drape at value ≤ 0.40, wet sheen, foam rim, turquoise moat.
4. **R2 slam camera** with heading set to the block's measured long axis. New asset: the paper Manhattan (public-domain Landsat 9 crop masked by the TIGER New York County outline, 3 px paper edge, contact shadow).
5. **The footprint draw-on** at 25% hero-orange fill with white outline and leading edge, plus the number block (odometer).
6. **The refill sweep** and the eased push-in from R3 back onto the C0 line.
7. **The paper tourist at map scale:** pop-up hinge, hat lift and flip, landing squash, head tilt, duck behind the crest.
8. **Audio:** three Rodney takes (A, C, B), 3 takes each, generated after the owner OKs the text; the music edited to N whole bars; a wrapped mix with a 0.5 s crossfade at -14 LUFS integrated, -1.5 dBTP, VO 12 LU or more above the music. Music from engine/tools/music.py, so the plan's licence check covers it too.

**Reused as-is** (assets, not footage): the Ch2 Nuʻuanu drain tile (HMRG 50 m plus ETOPO 2022, baked shadows and AO) and the island terrain and drape; the water and foam material and the refill device; the recurring public-domain tourist card and hat piece (source must be US government work or "No known restrictions"; record the ID in the asset manifest); the TIGER Manhattan polygon and the Nuʻuanu footprint polygon; the type system (both subsets), the POST grade, the SFX library (impact_deep, impact_short, tick_counter, thunk, paper flap, whooshes, riser).

**Dropped from the draft, and why:** the eye-level C0 (the bay and cliff wall were out of frame; an honest ghost is a 3-5° haze band from the lookout), and with it the cliff dive, the hat over the edge, the tracker ring, the crash zoom and macro set, the sea flight, the updraft and the cloud wipe; the 600 km pull-out; "half", "about 125" and the parapet rail.

**Previz and evidence** (ray-cast on the 110 m hero DEM; layout, not look), all under /tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/short03v3/: reg_f.png (frame-0 geometry); m_f0_guides.jpg, m_slam_guides.jpg, m_fan_guides.jpg, m_tail_guides.jpg, mock_sheet_v3.jpg (safe box and real fonts; every text block inside x 72-849, y 200-1529); m_f0_phone390.jpg (the phone read); pair2.jpg and c0_h45_v18.png (why the eye-level ghost fails); bearings.py, ghost3.py, render3.py, mock3.py, timing3.py.

**QC before sign-off:** type QC (no cap below 77 px); a 390 px phone sheet of every shot's middle frame; gate.py on frames at 0.0, 13.2, 17.5 and 21.0 s (tan ≤ 10%, red ≤ 3%, numbers recorded; if the fan fails, drop its fill to 20%); mean luma ≥ 70 per shot; the loop MAE/SSIM and temporal_scan gates; owner review stills (frame 0, each beat, the seam) before the full render.

## 8. Title, description, link

**Release:** D+3. At upload the owner sets the Short's Related Video to "Why Can't You See Most of Hawaii? (Look Down)". Links in Shorts comments are not clickable. Nothing is uploaded, scheduled or set by us.

**Title:** Where Did This Volcano's Other Side Go? (39 characters; a concrete question; none of drain/drained, hidden/hiding, bottom/beneath, nobody, found; no Everest; passes the niche regex; exact-title probe 2026-11-08: 0 on-topic matches; does not repeat the frame-0 headline, which names the place). Alternative for a later test: "Where Did Oʻahu's Other Side Go?" (32).

**Description (paste as is):**

> More than a million years ago, the Koʻolau volcano, which built the east side of Oʻahu, split through its summit, and its whole northeast side slid into the Pacific. It is called the Nuʻuanu landslide, one of the largest landslides on Earth. Drain the ocean off the island's northeast coast and the pieces are still there. The biggest block, Tuscaloosa Seamount, is about 30 km (19 mi) long and 17 km (11 mi) wide: bigger than Manhattan. The debris runs more than 100 miles (about 200 km) across the sea floor.
>
> The full story of what's under Hawaiʻi: Why Can't You See Most of Hawaii? (Look Down)
>
> Every depth comes from real seafloor maps. The pale shape of the missing side is a sketch, not a measurement: the surviving west flank of the volcano, mirrored.
> Seafloor: University of Hawaiʻi SOEST HMRG multibeam synthesis; GMRT; NOAA ETOPO 2022. Island terrain: USGS 3DEP. Manhattan: Landsat 9 imagery (USGS/NASA) and U.S. Census TIGER outline.
> Sources: USGS Volcano Watch, "Oahu, Niihau and Kauai"; USGS Volcano Watch, "A geologic tour of the Hawaiian Islands: Oʻahu"; Moore et al. 1989, "Prodigious submarine landslides on the Hawaiian Ridge" (USGS); Moore, Normark and Holcomb 1994, "Giant Hawaiian landslides"; ODP Leg 200 Initial Reports, Chapter 1 (Nuuanu Landslide); USGS Geologic Investigations Series I-2809, "Hawaii's Volcanoes Revealed" (Eakins et al. 2003).
>
> #Oahu #Hawaii #Geology

Notes: all readable text spells Oʻahu, Koʻolau, Nuʻuanu and Hawaiʻi with U+02BB; the long-form title is quoted exactly as launched; hashtags and tags use ASCII search spellings on purpose.

**Tags:** Nuʻuanu landslide, Nuuanu slide, Oahu, Oʻahu, Pali Lookout, Koolau volcano, Tuscaloosa Seamount, Hawaii without water, ocean drained Hawaii, largest landslide on Earth, Hawaii geology. The drain words live in the tags, the description and the spoken "Drain the ocean" at about 9.5 s; the title and on-screen text carry none.

**Pinned comment** (live within 5 minutes, posted by the owner): "Have you stood at the Pali Lookout? Did your hat make it?" Heart and reply to visitor stories; reply to any correction within 48 hours.

**How it feeds the long-form:** it reuses the film's Ch2 world (the Nuʻuanu drain, the Manhattan block at true size, the debris footprint, the recurring paper tourist and his hat at the Pali), plays as a complete looped story with its own payoff, spends nothing from Ch3-Ch6 (no Everest, no 56,000 ft, no dent), and matches the long-form's fact wording ("bigger than Manhattan", "more than a hundred miles", "whole side").

**Fact-check sources:** USGS Volcano Watch: Oahu, Niihau and Kauai (https://www.usgs.gov/news/volcano-watch-oahu-niihau-and-kauai); USGS Volcano Watch: A geologic tour of the Hawaiian Islands, Oʻahu (https://www.usgs.gov/center-news/volcano-watch-a-geologic-tour-hawaiian-islands-o-ahu; re-fetched 2026-11-08: "Koʻolau's caldera is located in the Kailua area"; "about 200 km (120 mi)"; a block "over 29 km (18 mi) long"); ODP Leg 200 IR ch.1 (https://www-odp.tamu.edu/publications/200_IR/chap_01/c1_3.htm); USGS: Prodigious submarine landslides on the Hawaiian Ridge (https://www.usgs.gov/publications/prodigious-submarine-landslides-hawaiian-ridge); USGS: Giant Hawaiian landslides (https://www.usgs.gov/publications/giant-hawaiian-landslides); USGS I-2809 (https://pubs.usgs.gov/publication/i2809); Hawaiʻi DLNR: Nuʻuanu Pali State Wayside (https://dlnr.hawaii.gov/dsp/parks/oahu/nuuanu-pali-state-wayside/); Wikipedia: Tuscaloosa Seamount (https://en.wikipedia.org/wiki/Tuscaloosa_Seamount).

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 70. All 8 must-fixes are in: re-timed from a measured Rodney model with TTS after the owner's OK and a bars formula; the post-climax dead air gone (tail 0.3 s after "miles", total ≈ 26.4 s); a visual hook in frame 0 (the ghost plus the headline); C0 rebuilt and DEM-checked; the ʻokina drawn only with Anton's U+02BB; the fan at 25% fill and Manhattan no longer an orange shape; the slide on a held camera and no spoken Hawaiian word; the description wording, takes and drain-word note fixed, and the Manhattan wording consistent with the long-form.
