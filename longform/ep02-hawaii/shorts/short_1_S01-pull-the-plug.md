# Short 1 (S01-pull-the-plug): "Hawaiʻi's Surfers Are Halfway Up a Mountain"

| | |
|---|---|
| Release | **D0**, 10-30 min after the long-form goes live, same hour (slot 1 of 7) |
| Length | 29.0 s planned (L re-derived from the real take; 28.5-31.0 s allowed) |
| The one big number | ABOUT 18,000 FEET (this Short owns 18,000 among the 7) |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps, 870 frames; one continuous camera, VE 1.0 |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

All times are estimates. Every camera key, label, caption and SFX is re-timed from tts.py `timing.json`; the take is never forced to fit the plan.

## Integrator changes (2026-11-08)

1. "Put the ocean back." became **"Fill it back up."** The long-form says "Now put the ocean back." (s173); the owner wants Short narration written new. The new line also fits the bathtub framing.
2. Captions follow the house spec (shorts_plan.md section 4): Anton cap 80, centred x 460 / y 1515.
3. The kicker HAWAIʻI is set in Barlow Condensed 800, whose own U+02BB glyph draws as a backtick (swipe03/okina_big.png). The text stays U+02BB; type.js draws Barlow's U+2018 glyph in its place (house rule).
4. TTS settings: the locked long-form settings (`"settings": {}`), with stability 0.35 / style 0.4 only as an A/B take.
5. This Short now owns the bathtub plug and chain alone. Short 2's plug was replaced by a freezer so two releases in a row do not share the device.

## 1. Narration and TTS

**TTS setup**
- Voice "Rodney - Clear Educator" (`eY2VJs4Gi8QKG2RV01sS`), model `eleven_v4`, passed explicitly (tts.py still defaults to Brian).
- Settings: the locked ep02 long-form settings, so Rodney sounds the same as in the film. Generate one A/B take of T1 at stability 0.35 / style 0.4; keep the default unless the owner prefers the A/B by ear.
- Text: no break or bracket tags, numbers spelled out, 70 words.
- Sent in story order as three takes. T3 is generated twice (two loop takes); keep the take with the cleaner seam.

**T1 (speed 1.0)**
> Watch the surfer. Sorry, buddy. The beach becomes a ledge. The ledge becomes a drop-off. The drop-off becomes a mountain. And it keeps going. The last water pools in a moat. How deep?

**T2 (speed 0.92; its own take after a 0.55 s pause, per the key-statistic rule)**
> About eighteen thousand feet.

**T3 (speed 1.0)**
> Now look back up. And our surfer? More than halfway up a mountain. Still waiting for a wave. Fine. Fill it back up. And he has no idea, this is what's under Hawaii.

**Placement.** Split T3's last sentence in its own comma pause after "idea,". The second half, "this is what's under Hawaii.", opens the Short at 0.12 s. "And he has no idea" ends 0.15 s before the cut, so the pause across the seam is 0.27 s.

| Planned time | Line |
|---|---|
| 0.12-1.85 | this is what's under Hawaii. |
| 2.10-3.10 | Watch the surfer. |
| 3.70-4.60 | Sorry, buddy. |
| 5.00-6.50 | The beach becomes a ledge. |
| 6.80-8.45 | The ledge becomes a drop-off. |
| 8.75-10.60 | The drop-off becomes a mountain. |
| 10.90-12.00 | And it keeps going. |
| 12.30-14.20 | The last water pools in a moat. |
| 14.45-15.05 | How deep? |
| 15.60-17.50 | About eighteen thousand feet. |
| 18.10-19.10 | Now look back up. |
| 19.85-20.75 | And our surfer? |
| 21.05-22.85 | More than halfway up a mountain. |
| 23.10-24.50 | Still waiting for a wave. |
| 25.00-25.45 | Fine. |
| 25.80-26.95 | Fill it back up. |
| 27.50-28.85 | And he has no idea |

**Timing rules**
- Speed 1.0 (T2 0.92). Never push the deadpan to 1.05.
- Minimum pauses: 0.25 s between sentences; 0.5 s before "Sorry, buddy." and before "Fine."; 0.50-0.55 s guess pause after "How deep?"; 0.27 s across the seam.
- L = end of "idea" + 0.15 s, rounded to whole frames. Target 29.0 s; 28.5-31.0 s allowed. Music tempo = 3840 / L BPM, so 16 bars land exactly on L.
- Cut line: if L would pass 31.0 s, drop "And it keeps going." first. Never cut the hook or the loop line.
- Trim each take to first character -60 ms and last character +90 ms, with 8 ms fades. Run vo_fix.py on stray next-word bursts.

**Delivery**
- Calm and dry throughout. Deadpan on "Sorry, buddy." and "Fine.".
- A small lift on "mountain" in "The drop-off becomes a mountain.".
- "How deep?" light and curious. "About eighteen thousand feet." slower and lower.
- "More than halfway up a mountain." matter-of-fact.
- "And he has no idea," level and open (a comma, not a falling stop).

**Pronunciation** (longform/ep02-hawaii/script/lexicon.json)
- Hawaiʻi is the only spoken Hawaiian word. Send ASCII "Hawaii" (the lexicon never puts U+02BB or kahakō in TTS text until a test render passes). Target /həˈwaɪ.ʔi/: three syllables, a light glottal catch before the last "ee" (hah-WHY-ee). If the test render gives two syllables, regenerate T3 with the lexicon alternative "hah-WHY-ee"; captions still map it to Hawaiʻi.
- ASR-check with faster-whisper small.en and medium.en; accept only "hawaii" or "hawai'i". It is the hook's last word, so a mangled take is regenerated, never kept.
- On screen and in captions: HAWAIʻI with U+02BB; load the latin-ext font subsets.
- Hawaiian words in the description or production notes only (never voiced here): Hilo HEE-loh; Honoliʻi hoh-noh-LEE-ee, glottal catch before the last "ee" (rule-derived, add to the lexicon); Mauna Kea MAO-nah KAY-ah; Mauna Loa MAO-nah LOH-ah; Waikīkī why-kee-KEE (photo-search note only, add to the lexicon).
- Lexicon open item 1 applies: a person confirms every entry on wehewehe.org before any of them is voiced.
- Map timing words through caption_map before make_srt.py and asr_check.py.

## 2. Second-by-second table

One continuous camera at VE 1.0, plus one loupe inset (20.05-24.85). "+250 m" = 250 m above the OLD sea level. Positions are px on 1080x1920. Bars at 132.41 BPM (bar 1.8125 s = 3840 / 29.0). Captions are suppressed whenever the headline, the label stack or the number block already shows the same words.

**0.00-1.00 · P0, at rest at frame 0**
- Picture: camera 4.0 m behind the paper surfer on his seaward side (bearing 70° from him), 1.4 m above the water; heading 247, pitch -3, VFOV 58; sunrise key from behind-right (azimuth ~100, elevation ~15).
  - Sky y 0-655; green Honoliʻi bluffs y 655-890.
  - The surfer from behind, anonymous, riding a small turquoise wave: x ~500-760, head at y ~673, board to y ~1360 (36% of frame height).
  - On the black boulder beach ~100 m beyond him, an 18 m chrome bathtub overflow plate with two slots: x ~187-487, y ~760-893 (29% of frame width).
  - A chrome ball chain (1.0 m balls) runs from the plate down the boulders and across the reef, seen through clear water, to the left edge at y ~1470; nearest balls ~145 px.
  - FRAME 1 (0.03): the chain rips taut out of the water in a straight spray line from the plate to the left edge at y ~999, all in the left half.
  - 0.40: the whole sea level starts dropping straight down, like a tub (no outflow current). The camera sinks at ~60% of the water's rate.
  - Rebuilt from: LF Big Island terrain bake and water-plane shader. New: Honoliʻi close tile, plate, chain, surfer.
- Text: kicker HAWAIʻI (Barlow Condensed 800, cap 80, white, dark stroke), x 120-450, cap-top y 180. Headline WATCH THE / SURFER (Anton, cap 110, white, 0.13 x cap dark stroke, soft 35% scrim, no box): x 120-646 / 120-465, cap-tops y 290 / 430. Captions: THIS IS (0.10-0.55), WHAT'S UNDER (0.55-1.20).
- VO: 0.12- "this is what's under Hawaiʻi."
- Sound: 0.00-0.25 GLUG tail (pre-lap). 0.03 CLANK, chain rattle and spray hiss, ducked to -18 dB under the voice from 0.12. 0.40 distant sub-bass THOOMP (the plug popping far out). Bar 1: pizzicato bass and marimba motif.

**1.00-2.00**
- Picture: level -0.6 to -1.6 m. The surf flattens. The waterline falls down the boulders and leaves a salt-white bathtub ring (at least 6 px) on the real 0 m line; the plate stands high and dry over the ring. The surfer sinks ~220 px in frame. The depth gauge has faded in top-left (0.40-0.90).
- Text: headline holds; gauge (no digits); caption HAWAIʻI. (1.20-1.95).
- VO: (ends 1.85).
- Sound: LF drain gurgle swells; surf wash fades out.

**2.00-3.00**
- Picture: level -2.4 m. His board scrapes the reef top showing through the water. Camera pitch eases to -8.
- Text: headline holds; caption suppressed.
- VO: 2.10-3.10 "Watch the surfer."
- Sound: music dips -10 dB from 2.2 to 3.3 (0.25 s ramps); reef trickles.

**3.00-4.00**
- Picture: 3.10-3.30 headline fades out. 3.35 the board lands flat on dry black reef with a paper squash and overshoot; he stays frozen in riding stance. The water drains down the reef away from him. 3.95 paper yaw wobble of ±12° (he looks around).
- Text: caption SORRY, (3.70-4.15).
- VO: 3.70- "Sorry, buddy."
- Sound: 3.35 soft BOING and paper flap (in the gap); 3.95 paper flick.

**4.00-5.00**
- Picture: 4.40 second wobble. Level -6 m; rocks dripping. The plate and its ring tower over him. 4.80 the eased pull-back starts, dollying back and rising along the chain (the ETOPO-checked line 60° from him); heading 247 to 240.
- Text: caption BUDDY. (4.15-4.65).
- VO: (ends 4.60).
- Sound: 4.80 whoosh; music back to full.

**5.00-6.00**
- Picture: flying back and up out of Honoliʻi to K1 (19.7865 N 155.0454 W, +250 m, heading 240, pitch -21, VFOV 54; reached at 6.0). 5.30 a white ring (6 px stroke, r 34, dark under-stroke) pops on the shrinking surfer and settles at (541, 334). The drained shelf (wet black lava, dark sand channels, sparse cream reef) fills y 334-1055. The taut chain runs from the frame bottom up the shelf to him. Level -20 to -60.
- Text: none (captions suppressed for the triad).
- VO: 5.00- "The beach becomes a ledge."
- Sound: 5.30 ring pop. Bar 4 (5.44): LF drain riser starts.

**6.00-7.00**
- Picture: 6.07 LEDGE slaps in. The shelf drains to its edge (-400 m at 7.0) while the camera keeps retreating. Ring fades 6.6-6.8.
- Text: LEDGE (Anton cap 110, white, dark stroke), x 120-401, cap-top y 470.
- VO: (ends 6.50); 6.80- "The ledge becomes a drop-off."
- Sound: 6.07 label slap, low.

**7.00-8.00**
- Picture: past the shelf edge the slope plunges. Drowned reef steps appear on the face, only where the HMRG grid shows terraces. Level -400 to -1,500. 7.88 DROP-OFF slaps in under LEDGE. Rebuilt from: LF drain level curve and terrain bake.
- Text: LEDGE / DROP-OFF (Anton cap 130), x 120-653, cap-top y 615.
- Sound: 7.88 slap, mid. LF rumble in.

**8.00-9.00**
- Picture: K2 at 8.0 (19.9010 N 154.8342 W, +250, heading 241, pitch -19). The face spans y 475-1308 with a foam rim at the waterline; the surfer's spot is at (510, 333).
- Text: LEDGE / DROP-OFF.
- VO: (ends 8.45); 8.75- "The drop-off becomes a mountain."
- Sound: riser builds.

**9.00-10.00**
- Picture: level -1,500 to -3,000; the flank lengthens under the coast. 9.98 MOUNTAIN slaps in.
- Text: LEDGE / DROP-OFF / MOUNTAIN (Anton cap 150), x 120-785, cap-top y 785; the stack ends at y 935.
- VO: ("mountain" ~10.05).
- Sound: 9.98 slap, high.

**10.00-11.00**
- Picture: K3 at 10.0 (19.9638 N 154.7181 W, heading 243, pitch -19). The flank spans y 388-1371; Mauna Kea's shoulder enters at the right edge.
- Text: stack holds; caption AND IT (10.90-11.35).
- VO: (ends 10.60); 10.90- "And it keeps going."
- Sound: rumble.

**11.00-12.00**
- Picture: level -3,000 to -4,500. The camera (~55 km out) tilts down to follow the water. The island is now a thin band on top of a huge dark flank.
- Text: stack; caption KEEPS GOING. (11.35-12.05).
- VO: (ends 12.00).
- Sound: rumble peaks.

**12.00-13.00**
- Picture: 12.20-12.45 the stack wipes up and out. K4 at 12.3 (20.0220 N 154.6102 W, heading 245, pitch -21): the waterline reaches the foot of the flank. 12.50 a slow whirl opens over the plug far below; the taut chain runs down the flank into it. Rebuilt from: the LF Ch3 -4,000 to -5,500 m step with the Hawaiian Deep.
- Text: caption THE LAST WATER (12.30-13.05).
- VO: 12.30- "The last water pools in a moat."
- Sound: whirl swirl, deep gurgle.

**13.00-14.00**
- Picture: level -5,200 at 13.6. The water separates into the trough, drawn only where ETOPO is below -5,486 m. The pool runs out of both frame edges: a strip, never a closed basin.
- Text: captions POOLS (13.05-13.45), IN A MOAT. (13.45-14.25).
- VO: (ends 14.20).
- Sound: whirl.

**14.00-15.00**
- Picture: the camera eases into the moat pose K5 (20.0578 N 154.5437 W, +250, heading 247, pitch -30, VFOV 54; arrives 15.40). The turquoise pool fills the lower half; the black plug shows under ~90 m of clear water at (687, 1206), with water spinning around the chain.
- Text: caption HOW DEEP? (14.45-15.40).
- VO: 14.45-15.05 "How deep?"
- Sound: the music holds one sustained note through the guess pause (15.05-15.60).

**15.00-16.00**
- Picture: 15.41 the chain goes slack (a ripple runs up it), the plug drops into its chrome plughole, a bubble dome rises, the whirl stops, the gauge marker bottoms out, the frame shakes 2 px. 15.55 ABOUT pops in. 15.88 18,000 and FEET DEEP slam in.
- Text (number block; no box; dark stroke 0.13 x cap; soft 35% radial scrim):
  - ABOUT: Barlow 800 cap 90, white, x 120-432, cap-top y 250;
  - 18,000: Anton cap 245, #FFD23F, x 120-845, cap-top y 372;
  - FEET DEEP: Barlow 800 cap 110, white, x 120-722, cap-top y 650.
- VO: 15.60- "About eighteen thousand feet."
- Sound: 15.41 PLUNK with bubble burp, gauge thunk and music hit (bar 9, beat 3). 15.88 slam.

**16.00-17.00**
- Picture: hold with a slow 1.5% push; bubbles settle.
- Text: number block (captions suppressed).
- Sound: low pad, glockenspiel.

**17.00-18.00**
- Picture: hold.
- Text: number block.
- VO: (ends 17.50).
- Sound: 17.60 glockenspiel tick.

**18.00-19.00**
- Picture: 18.10-18.35 the block wipes up and out. The tilt to K6 starts: pitch -30 to -20, VFOV 54 to 60, heading 247 to 250, eased, settling at 19.60. The flank scrolls down; the shelf edge, the coast and Mauna Kea arrive on top.
- Text: captions NOW LOOK (18.10-18.60), BACK UP. (18.60-19.15).
- VO: 18.10-19.10 "Now look back up."
- Sound: soft whoosh. Bar 11 (18.13): the motif returns.

**19.00-20.00**
- Picture: the payoff pose K6 settles at 19.60: Mauna Kea's summit at (683, 295); the old coast with the surfer's speck at (252, 372); the shelf edge at y 397 and the dark flank from y 397 to 1317; the pool from y ~1317 down, running out of both sides. 19.78 the ring pops on the speck.
- Text: caption AND OUR (19.85-20.25).
- VO: 19.85- "And our surfer?"
- Sound: 19.78 pop.

**20.00-21.00**
- Picture: 20.05-20.35 a loupe opens: a 600 px circle centred at (600, 840), spanning x 300-900, y 540-1140, with a straight 6 px white leader from the ring. Inside is the frame-0 view, drained: the surfer from behind, frozen in riding stance on his board on dry black reef, with the overflow plate high and dry behind him over its white ring and the slack chain on the reef. 20.80 he hops once.
- Text: caption SURFER? (20.25-20.80).
- VO: (ends 20.75).
- Sound: 20.10 glass tick. 20.80 mini boing (in the gap).

**21.00-22.00**
- Picture: 21.40-21.85 on "halfway" he leans 15° forward on his paper hinge, peering down. The wide frame holds with a 1% push.
- Text: captions MORE THAN (21.05-21.45), HALFWAY UP (21.45-22.15).
- VO: 21.05- "More than halfway up a mountain."
- Sound: none (the line breathes).

**22.00-23.00**
- Picture: he holds the lean; the push continues.
- Text: caption A MOUNTAIN. (22.15-22.90).
- VO: (ends 22.85).

**23.00-24.00**
- Picture: 23.10 he snaps upright into riding stance and resumes his 2.9 s ride bob on dry rock.
- Text: caption STILL WAITING (23.10-23.75).
- VO: 23.10- "Still waiting for a wave."
- Sound: 23.10 soft paper rustle (-18 dB).

**24.00-25.00**
- Picture: 24.55-24.85 the loupe shrinks back into the ring; the ring stays.
- Text: caption FOR A WAVE. (23.75-24.55).
- VO: (ends 24.50).
- Sound: music dips -10 dB from 24.0 to 25.0. 24.55 close tick.

**25.00-26.00**
- Picture: 25.375 (bar 15) the pool rises up the flank as one smooth flat sheet behind a thin foam rim, with no wave front; the gauge marker climbs. 25.40 one log-eased fly-in starts, toward the ring on the surfer: heading 250 to 247, pitch -20 to -3, VFOV 60 to 58.
- Text: captions FINE. (25.00-25.45), FILL IT (25.80-26.35).
- VO: 25.00 "Fine." 25.80- "Fill it back up."
- Sound: 25.375 tub-filling gurgle-up and a strings swell (no roar).

**26.00-27.00**
- Picture: the sea climbs over the shelf edge (-400 m at 26.60) and floods the shelf as a smooth rising sheet. The camera descends toward Honoliʻi at a constant zoom factor per frame, flying into the ring.
- Text: caption BACK UP. (26.35-27.00).
- VO: (ends 26.95).
- Sound: gurgle-up continues; strings swell.

**27.00-28.00**
- Picture: 27.00-27.60 gauge fades out. 27.10-27.40 the ring fades as he grows past it. The camera arrives low behind him. The water rises calmly up the reef (-2.8 m at 27.60), reaches his board and lifts him back onto his small wave at 27.75.
- Text: caption AND HE HAS (27.50-28.10).
- VO: 27.50- "And he has no idea"
- Sound: 27.75 paper flap and a gentle wave slap (-16 dB). Bar 16 (27.19): strings resolve.

**28.00-29.00**
- Picture: 28.35 the camera comes to rest at P0. The water reaches 0 m and touches the overflow's slots. The surf settles into the frame-0 pattern, and the chain lies slack in its authored pose. 28.30-28.80 the kicker and headline fade back in. The last frame (t 28.967) equals frame 0.
- Text: caption NO IDEA (28.10-28.85, fully gone by 28.93). HAWAIʻI / WATCH THE SURFER back in by 28.80.
- VO: (ends 28.85).
- Sound: 28.35 the overflow GLUG starts low under "idea" (below 300 Hz), peaks at 28.90 in the gap; its last 0.25 s is copied to 0.00-0.25. Bar 16 resolves into bar 1. Hard cut at 29.000 on the bar line.

## 3. Hook

Frame 0 is already moving (the surfer's ride bob, the surf, the haze) and carries the whole premise with the sound off.
- We sit low on the water, 4 m behind a paper surfer at the Honoliʻi break off Hilo. He is seen from behind, so he stays anonymous, and fills 36% of the frame height on the right.
- Straight ahead of him, bolted to the black boulder beach, is an 18 m chrome bathtub overflow plate taking 29% of the frame width. A chrome ball chain runs from it down the rocks and across the reef, through the clear turquoise water, to the left frame edge (nearest balls ~145 px).
- The visual question is a bath fixture on a Hawaiian beach. In the upper third, unboxed: the kicker HAWAIʻI and the headline WATCH THE / SURFER (Anton cap 110), which gives muted viewers the place and an instruction.
- Frame 1 (0.03 s): CLANK. The chain rips taut out of the water in a straight spray line across the left half (y 880-999 at the edge), well clear of the Shorts button rail.
- 0.40 s: a far-off THOOMP, and the whole sea level starts dropping straight down like a tub: a vertical drop, not a drawback. By 1.0 s a salt-white bathtub ring shows on the boulders; by 1.6 s he has sunk ~220 px.
- VO at 0.12 s: "this is what's under Hawaiʻi." (5 words, done by 1.85 s). "Watch the surfer." follows at 2.10 s, reading the headline aloud for sound-on viewers. Two questions open at once: what is down there, and what happens to him? The first gag answers the second by 3.35 s (BOING, he lands on dry reef, "Sorry, buddy.").
- No greeting, no channel name, no number before 15 s. The CLANK and rattle sit at -18 dB under "this".

## 4. Payoff

Three stages, each landing its own beat.
1. **The number (15.4-18.3).** The camera eases into the moat pose as Rodney asks "How deep?", then holds a 0.55 s guess pause. PLUNK: the plug drops back into its plughole and the whirl stops. The last water sits in the real Hawaiian Deep as a turquoise strip that runs out of both frame edges. ABOUT / 18,000 / FEET DEEP slams in over dark basalt.
2. **The real payoff (18.1-24.9).** "Now look back up." tilts from the pool up the whole dark flank to the old shoreline. One frame holds the scale: the pool at the bottom, 920 px of flank, a ring on a speck at the old coast, Mauna Kea's summit above it. "And our surfer?" A 600 px loupe opens on the speck: the frame-0 view drained, him frozen in riding stance on dry reef, the overflow plate high and dry behind him. He hops. "More than halfway up a mountain." He leans over and peers down. "Still waiting for a wave." He snaps upright and keeps riding nothing. It turns "far away" into "high up", and it is true: sea level is 57-59% of the way up Mauna Kea from the moat or from its USGS base.
3. **The callback (25.0-29.0).** "Fine. Fill it back up." The pool rises up the flank as one smooth sheet, a tub filling with no wave front. The camera flies home into the ring in one log-eased move. The water reaches the reef and lifts him back onto his wave at 27.75. "And he has no idea" lands in the last 1.35 s, and the opening line completes it.

Held back for the long-form and Short 7: why the moat exists (the weight and the dent), Everest, 56,000 ft and 33,500 ft. "Why is there a moat?" stays open; line 2 of the description and the Related Video answer it.

## 5. Loop check

**Last line into first line, as one passage:** "Fine. Fill it back up. And he has no idea, this is what's under Hawaiʻi. Watch the surfer."
- One natural sentence across the cut: he has no idea that this is what is under him.
- Generated as one TTS sentence (T3), split in its own comma pause. "idea" ends at 28.85, the cut is at 29.00, "this" starts at 0.12: 0.27 s across the seam.
- T3 is recorded twice; keep the take whose "idea" stays level and open. The second half is a falling statement, which suits a hook.

**Last frame = frame 0.** The last frame is frame 869 (t = 28.967), rendered at its own time, not copied from frame 0 (a copy would show a 1-frame freeze).
- Camera: P0, at rest from 28.35 with zero velocity; frame 0 also starts at rest. Keys are cyclic in value and slope.
- Water: exactly 0 m from 28.35, touching the overflow slots.
- Surfer: on his small wave in the same ride pose. Bob period 2.9 s = L/10.
- Chain: the single authored SLACK pose, used from 15.41 to 29.0 and at frame 0. Sway period 5.8 s = L/5.
- Surf shader: only periods that divide L (9.667, 5.8, 4.143, 2.9, 1.933 s = L/3, /5, /7, /10, /15). Haze and clouds static. Every time-driven water term runs on the loop clock (cos/sin 2πt/L; see shorts_plan.md section 5).
- Text: kicker and headline fully back by 28.80, as on frame 0. No gauge (out 27.0-27.6, in 0.40-0.90), no ring (out 27.10-27.40), loupe, label or caption (gone by 28.93; the first caption appears at 0.10).
- If L changes after the real take, re-derive every period as L/n.

**Gates:** first/last-frame MAE ≤ 5/255; SSIM ≥ 0.95 at 540x960; concatenate the Short with itself and run temporal_scan.py: no "cut" or "flash" at the join.

**First new event after the seam:** the chain snapping taut on frame 1 (CLANK at 0.03). A replay reads as "the tub is full again, and someone pulls the chain again".

**Audio seam:** the overflow GLUG starts low under "idea" at 28.35 (below 300 Hz, at least 16 dB under the voice), peaks at 28.90 in the gap and runs into the CLANK. Copy the last 0.25 s of the GLUG, the music reverb and the surf ambience to 0.00-0.25 (pre-lap). Music: 16 bars at 3840/L BPM, cut on the bar line; bar 16 resolves into the bar-1 motif. The voice is cut at the last word with a 5-8 ms fade.

## 6. Facts (all inside the spine; one big number)

Script paths below are in the scratchpad folder s1v3.
- "this is what's under Hawaiʻi" and the flank shown: spine #1 (USGS FAQ: Mauna Kea rises 4,205 m above sea level and about 6,000 m below); ledger C12-01, C3-02. Terrain is real: UH SOEST HMRG 50 m blended into NOAA ETOPO 2022, with the NCEI 1/3" Hilo coastal DEM near shore, at VE 1.0.
- "The beach becomes a ledge." No number. ETOPO 15" on the camera line (60° from the surfer): 45 m at the coast, then -67 m (5 km), -311 (10 km), -351 (15 km), -619 m (20 km): a shelf about 20 km wide (p1.py).
- "The ledge becomes a drop-off." Replaces "cliff" per ledger C12-10 ("say 'the slope plunges' below the shelf edge, not 'cliffs'"). Past 20 km the floor falls to -1,191 m (25 km), -2,100 (35), -4,251 (45), -5,053 m (50); the steepest 1-km step is 14.5° on the 15" grid. No number spoken.
- "The drop-off becomes a mountain." / "And it keeps going." Spine #1 (about 6,000 m below sea level). 33,500 is not spoken.
- "The last water pools in a moat." Spine #4 (Hawaiian Deep, a flexural trough); ledger C3-04 (trench, moat or trough) and C3-05 (never a ring). Our ETOPO 15" flood at -5,486 m (pool.py): one connected strip of about 9,200 km² (155.54-154.09 W, 19.05-21.20 N, deepest -5,764 m) along the NE base, continuing north past the grid edge. Drawn only from those cells; runs out of both frame edges; never cropped into a closed basin. "The last water" is true within the frame only. At this level the Big Island is joined to Maui by dry ridge (C3-08): Maui stays out of frame (bearing ~292°; the right frame edge is ~263-268°), and nothing says or shows the island standing alone.
- "How deep? About eighteen thousand feet." / ABOUT 18,000 FEET DEEP. Spine #4 ("about 5,500 m (18,000 ft) deep") and the brief's unit table; ledger C3-04 wording. Moat floor -5,350 to -5,600 m within 100 km. Pool surface at exactly -5,486 m; ABOUT stays on screen.
- "More than halfway up a mountain." Ledger C12-01 and C3-02, from the USGS FAQ: Mauna Kea is 13,796 ft above sea level and about 19,700 ft below, so sea level is 58.8% of the way up from its USGS base and 56.7% from the ~5,500 m moat (pool.py). Also holds for Mauna Loa: about 54% from its ~5 km submarine base (C3-02), about 76% from the dented base (spine #2). The payoff frame shows base, surfer and summit together. "Halfway" is a proportion, not a big number.
- "And he has no idea, this is what's under Hawaiʻi." True: from the sea surface the flank is hidden behind the shelf edge (line of sight on ETOPO).
- Gags (overflow, chain, plug, bathtub ring, "Sorry, buddy", waiting for a wave, "Fill it back up") are obviously playful; the description says "The plug is not real. The moat is."

Spoken numbers: 1 ("eighteen thousand"). On-screen numbers: 1 (18,000).

Not said (held for the long-form and Short 7): why the moat exists, Everest, 56,000 ft, 33,500 ft. "Five volcanoes become one" stays cut (C3-07).

**VERIFY (production checks, not narration)**
- Surfer photo: public domain only, anonymous, seen from behind; never Duke Kahanamoku or any named surfer; never an identifiable Native Hawaiian waterman as the stranded figure.
- On the HMRG 50 m bake, re-check the payoff lines of sight (ETOPO margins: surfer +26 m, Mauna Kea summit +90 m). Mauna Loa's summit at (246, 316) is hidden by 29 m on ETOPO: do not label it either way.
- Drowned reef steps only where the HMRG grid shows terraces (C12-10).
- Read the reef depth under the break from the NCEI DEM; it retimes the 3.35 s landing.
- Honoliʻi lies on Mauna Kea lavas (USGS geologic map, Sherrod et al. 2007). The line holds either way.
- Hawaiian pronunciations on wehewehe.org (lexicon open item 1).
- Licence: confirm the paid ElevenLabs plan with the owner before a monetised upload (covers the voice and music.py's music).

## 7. Renders: new for this Short vs reused

**New, in the Shorts project only (the long-form edit stays locked).**
1. **Camera path S1_SURF.** One continuous camera, 870 frames at 30 fps, 1080x1920 (1440x2560 master only after the 1440p encode test passes). TerrainStage at VE 1.0. Each segment eased on its destination key, one velocity peak per segment; sub-frame blur on any pan over 20 px/frame. Keys:
   - P0 (0.00, and 28.35-29.00 at rest): 4.0 m from the surfer on his seaward side (bearing 70°), 1.4 m above the 0 m water; heading 247, pitch -3, VFOV 58; surfer at the Honoliʻi break, ~100 m off the boulder beach at the stream mouth, placed on the NCEI 1/3" Hilo DEM (ETOPO-scale 19.762 N 155.091 W).
   - 0.40-3.35: the camera sinks 1.7 m at ~60% of the water's rate; pitch -3 to -10. 3.35-4.80: hold with a 1% push; pull-back starts at 4.80.
   - K1 6.00: 19.7865 N 155.0454 W, +250 m, heading 240, pitch -21, VFOV 54; surfer at (541, 334).
   - K2 8.00: 19.9010 N 154.8342 W, +250 m, heading 241, pitch -19.
   - K3 10.00: 19.9638 N 154.7181 W, +250 m, heading 243, pitch -19.
   - K4 12.30: 20.0220 N 154.6102 W, +250 m, heading 245, pitch -21.
   - K5 15.40 (moat pose): 20.0578 N 154.5437 W, +250 m, heading 247, pitch -30, VFOV 54; plug at (687, 1206); 1.5% push to 18.10.
   - K6 19.60 (payoff pose): same position, heading 250, pitch -20, VFOV 60; 1% push to 25.40. ETOPO-checked (pay.py, pool.py): Mauna Kea summit (683, 295); surfer (252, 372); shelf edge y 397; pool edge y 874-1313 across the frame; plug (582, 1482).
   - 25.40-28.35: fly-in back to P0, distance and height interpolated in log space (look book S14); heading 250 to 247, pitch -20 to -3, VFOV 60 to 58; arrives with zero velocity; the camera always stays above the rising water.
2. **Water level.** One flat plane with a foam rim at the contact line; no waterfalls, no outflow current, no wave front. Drain: 0 m (to 0.40), -0.6 (1.0), -1.6 (1.6), -2.4 (2.4), -2.8 (3.35, the board lands), -6 (4.5), -20 (5.0), -60 (6.0), -400 (7.0), -1,500 (8.0), -3,000 (10.0), -4,500 (12.0), -5,200 (13.6), -5,486 (15.41, ease-out, held to 25.375). Refill: -400 (26.60), -2.8 (27.60), -2.0 (27.75, the board lifts), 0 (28.35, ease-out, then held).
3. **Honoliʻi close tile.** NCEI 1/3" Hilo DEM (or USGS 3DEP 10 m) with an ortho drape; hand-placed basalt boulders within 150 m of P0 and the reef under the break; a small-swell surf shader using only periods L/3, /5, /7, /10, /15; the salt-white bathtub ring on the 0 m contour, revealed as the water leaves, never thinner than 6 px on screen. Needs the shared near-surface water pass (shorts_plan.md section 5B), since the eye is 1.4 m above the water.
4. **Props.** Chrome overflow plate (18 m wide, oval, two slots) on the boulder beach ~100 m beyond him. Chrome ball chain: from the plate down the boulders, along the reef 3 m to his left (passing ~3.7 m left of P0), then out along the 60° line to the plug; balls 1.0 m near the plate growing to ~60 m at the plug, never thinner than 8 px; states SLACK (one authored pose, used at frame 0 and 15.41-29.0, sway L/5) and TAUT (0.03-15.41, snaps on frame 1 with a spray line). Black rubber plug, 1.2 km across, in a chrome plughole ring at 20.0363 N 154.6118 W (ETOPO -5,579 m, under 93 m of pool water). Whirl shader over the plug (12.50-15.41) and a bubble dome at 15.41.
5. **Paper surfer.** Cut with cutout.py and card.py from a public-domain photo of an anonymous surfer seen from behind; warm off-white 3 px paper edge; the board a separate card; soft contact shadow; true scale, 36% of frame height at P0. Rig: ride bob (period L/10, phase-locked); follows the water while floating; landing squash and overshoot (3.35); yaw wobbles ±12° (3.95, 4.40); hop (20.80); 15° forward lean (21.40-21.85, held to 23.10); dry ride bob (23.10-25.40); lift back onto the wave (27.75).
6. **Loupe camera** (inset only, 20.05-24.85): a 600x600 render in a circle centred at (600, 840); camera 4.0 m behind him at bearing 70°, 1.4 m above the dry reef; heading 247, pitch -6, FOV 36; the surfer ~63% of the loupe (about 380 px).
7. **UI layer** (drawn after POST). Kicker and headline 0.00-3.30 and back 28.30-28.80. Depth gauge (T.gauge; in 0.40-0.90, out 27.0-27.6): top-left, bar x 58-78, y 236-516 (14.6% of frame height), 64 px chrome overflow icon at the top tick (0 m), bottom -6,000 m, turquoise below the marker, basalt above, 40 px marker, no digits. Label stack LEDGE / DROP-OFF / MOUNTAIN at caps 110/130/150. Number block. Ring with a straight leader to the loupe. Captions per the house spec. All text at x 120-849 and y ≥ 180; every cap ≥ 80 px (4.2%). Widths measured with fontTools on engine/www/fonts: Anton WATCH THE 526 / SURFER 345 at cap 110; LEDGE 281 at 110; DROP-OFF 533 at 130; MOUNTAIN 665 at 150; 18,000 725 at 245; widest caption card 611 at 80. Barlow Condensed 800: HAWAIʻI 330 at cap 80; FEET DEEP 602 at 110.
8. **Audio.** A 16-bar cue in the LF music palette (pizzicato bass, marimba, strings), from music.py (dur+3) or edited from the LF bed, conformed to 3840/L BPM, dips of -10 dB at 2.2-3.3 and 24.0-25.0, hits snapped to the nearest beat within 0.1 s. SFX: CLANK, chain rattle, THOOMP, gurgles, BOING (x2), paper flap (x2), label slaps (x3), PLUNK, bubble burp, glass tick, tub-filling gurgle-up (no roar), GLUG with a 0.25 s pre-lap. No motif more than 3 times. Mix -14 LUFS, true peak ≤ -1.0 dBTP, VO at least 12 LU above the music, comedic SFX in the gaps at about -16 dB.

**Reused as-is:** the ep02 Big Island terrain stack (HMRG 50 m into ETOPO 2022); the water-plane shader with foam rim and turquoise depth gradient; the Hawaiian Deep pool as ETOPO draws it (the LF Ch3 -4,000 to -5,500 m step); the LF refill curve shape, time-compressed for 25.375-26.60; the POST grade with the NO OCEAN exposure lift; Anton, Barlow Condensed 800, #FFD23F and T.gauge; the LF rumble, riser and gurgle SFX. No long-form frame or camera is reused.

**Look and QC gates.** Colours: dark basalt #2E2924 to #4A4038; moat mud #4E4C43; sparse cream reef; turquoise #22C3D6 (shallows) to #0F86A3 (deep). Tan ≤ 10% per frame (gate.py). Mean luma ≥ 85 per frame. Phone sheet at 390 px wide; a type check by hand (caps, 4-word headline, x ≤ 849). Loop gates as above. ASR on the VO, "Hawaii" first. A 10-15 s phone motion test of 0-6 s (waterline shimmer, chain spray, landing timing with sound). Review stills (frame 0, each beat, the last frame, the seam) go to the owner for an OK before the full render.

## 8. Title, description, link

**Title:** Hawaiʻi's Surfers Are Halfway Up a Mountain (43 characters)
- Proper noun first, plain-claim form. No clone words (drain/drained, hidden/hiding, bottom/beneath, nobody, found); no match for the niche report's banned-word regex.
- ytsearch probes 2026-11-08 ("surfers halfway up a mountain", "what's under hawaii", "hawaii surfers mountain underwater"): no Short or long-form uses this premise or these first 4 words; no top-20 title shares 3 consecutive words with it.
- It leaves the farmed plug-pulling family behind ("I Pulled the Plug on the Ocean" at 10M, 88K and the copies). True: sea level is 57-59% of the way up Mauna Kea from the moat or its base.
- Fallback (owner's choice): "What Hawaiʻi's Surfers Can't See" (32). Integrator note: kept as the fallback only, because Short 2's title also starts "You Can't..." the next day.

**Description (exact):**

> Pull the plug on the ocean beside Hawaiʻi's Big Island and a surf break off Hilo turns into a ledge, a drop-off, then a mountain, with the last water in a moat at its foot, about 18,000 feet down.
> Why is there a moat at the foot of Hawaiʻi? Full film: Why Can't You See Most of Hawaii? (Look Down) [long-form link]
> Real seafloor and coast data at true vertical scale: University of Hawaiʻi SOEST multibeam synthesis, NOAA ETOPO 2022 and the NOAA NCEI Hilo coastal elevation model. Surfer: [public-domain photo credit]. The plug is not real. The moat is.
> #Hawaii #BigIsland #Hilo #surfing #geography

The long-form title is quoted exactly as published, with plain "Hawaii".

**Tags:** Hawaii, Big Island, Hilo, Mauna Kea, Hawaii without water, ocean drained, Hawaiian Deep, surfing Hawaii, geography.

**Link setup** (every step needs the owner's explicit OK; we publish, schedule and change nothing ourselves): on D0 the long-form goes live first; this Short follows 10-30 minutes later, in the same hour. In YouTube Studio set this Short's Related Video to the long-form, and paste the long-form URL into line 2 of the description. The Short shows the moat but never explains it; the long-form's payoff (the weight denting the sea floor) answers line 2, so the Related Video is the natural next tap.

**Pinned comment** (after the owner's OK): "Have you ever paddled out off Hilo? Would you still, knowing you're more than halfway up a mountain?"

**Before upload:** run the whole-word, case-insensitive AI-term grep on the title, description, tags, pinned comment, SRT, burned-in captions and narration. Expect 0 hits ("ai" inside Hawaii is not a hit).

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 66. All 11 must-fixes are in this version: frame-1 headline (kicker HAWAIʻI + WATCH THE SURFER, back in by 28.80); "cliff" replaced by "drop-off" (C12-10); retitled away from the plug clone family; readable hook subject (surfer 36% of frame height, plate 29% of width, chain balls ~145 px in the left half, visible drop by 1.6 s); timeline built from the real take ("Now look back up."); the 22.45-26.2 dead hold killed and the loupe at 600 px; labels held ≥ 2 s; all text at x ≤ 849; ASCII "Hawaii" in TTS with ASR check; the Hilo tsunami read defused (vertical level drop, tub-filling refill, anonymous back-turned surfer); description wording "a moat at its foot" (C3-05).
