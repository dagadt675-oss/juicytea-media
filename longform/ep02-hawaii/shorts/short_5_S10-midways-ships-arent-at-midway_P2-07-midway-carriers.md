# Short 5 (S10-midways-ships-arent-at-midway + P2-07-midway-carriers): "The Carriers Sunk at Midway Aren't at Midway"

| | |
|---|---|
| Release | **D+9**, same clock hour as the long-form (slot 6 of 7; moved from D+7, see below) |
| Length | T = 27.000 s nominal (810 frames, 0-809); lock T to the take |
| The one big number | MORE THAN 3 MILES DOWN |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps; VE 1.0 in every shot; solemn: no music, a drone bed only |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

All picture events lock to the take's word timestamps; the times below are nominal.

## Integrator changes (2026-11-08)

1. **"Two have never been found." became "Two more are down there somewhere."** Ledger C5-13 bans "still lost" and "never found" for Sōryū and Hiryū (no public report of a discovery is not proof that they have not been found). The new line is true under every scenario: both carriers sank in June 1942, so their wrecks lie somewhere on the sea floor, and no position is drawn. The on-screen NEVER / FOUND became **SOMEWHERE**; the two discs still lose their ink and the third ping still gets no echo. The description line changed the same way. Hold after the line: 0.85 s (was 0.9) so T stays 27.000 s.
2. **Release moved to D+9** (from D+7). Short 4 (D+5) also opens on Midway's reef with a postcard; 4 days apart instead of 2. Short 6 takes D+7.
3. Captions follow the house spec (shorts_plan.md section 4): Anton cap 80, centred x 460 / y 1515 (was cap 77 at cap top 1452).
4. Pronunciation aligned with lexicon.json: Akagi "ah-KAH-ghee" (not AH-kah-gee); Papahānaumokuākea "pah-pah-HAH-now-moh-koo-ah-KEH-ah"; Hawaiʻi "hah-WHY-ee" (not hah-VAI-ee).
5. TTS settings: the locked long-form settings are the base; the solemn read (stability 0.6, style 0) is an A/B the owner picks by ear.

## 1. Narration and TTS

**Exact TTS input.** One ElevenLabs call (tts.py, one segment) with voice "Rodney - Clear Educator" (`eY2VJs4Gi8QKG2RV01sS`), model `eleven_v4`, passed explicitly. Base settings: the locked long-form settings; A/B: stability about 0.6, style 0, speed 1.0 (solemn).

> In June of nineteen forty-two, four Japanese carriers and the USS Yorktown went down. Drain the Pacific, and there's one, as far from Midway as Boston is from New York. More than three miles down, it's still sitting upright. Two more are down there somewhere. The carriers never even saw each other. They fought with planes, from far out at sea. That's why the carriers sunk at Midway aren't at Midway. In June of nineteen forty-two, four Japanese carriers and the USS Yorktown went down.

The repeated last sentence is a prosody guard and is never used: it puts the hook sentence in the middle of the paragraph, so Rodney does not read it with a falling, final close.

**Variants** (generate all three, choose on a phone speaker): V1 the text above; V2 the same with "...from far out at sea — that's why the carriers...", so "sea" keeps a continuing intonation; V3 V1 with "U.S.S." in place of "USS". Keep the take that passes all four checks: (a) piece B works cold (energy, an audible "the"); (b) "sea" does not fall to a final close; (c) the ship prefix is read "you-ess-ess" with no pause; (d) "one" in "there's one" is clear.

**How the take is cut (this makes the loop)**
- Find the natural gap (80-150 ms) between "why" and "the"; the cut point c is a zero crossing in the middle of that gap.
- Piece B runs from c to the end of "...aren't at Midway." plus 60 ms of room tone; it plays at 0.00, so "the" starts at about 0.04.
- Piece A runs from "In June" to c; it plays from 3.15.
- A ends at c and B starts at c, so across the seam the replay is the take's own continuous audio, with no fade and no splice.
- Inside A, change only the room-tone pauses: 0.5 s after "New York", 0.85 s after "somewhere", 0.3 s after "sea".
- T = 3.15 + the length of A; snap T to a whole frame by trimming the 0.15-0.25 s of room tone after the hook. Nominal T 27.000 s (810 frames).

**As heard, in order** (70 words; about 23.8 s of speech and 3.2 s of pauses):

| Time | Line |
|---|---|
| 0.04-2.95 | The carriers sunk at Midway aren't at Midway. |
| 3.15-9.00 | In June of nineteen forty-two, four Japanese carriers and the USS Yorktown went down. |
| 9.35-14.35 | Drain the Pacific, and there's one, as far from Midway as Boston is from New York. |
| (0.5 s) | |
| 14.85-17.60 | More than three miles down, it's still sitting upright. |
| 17.95-19.75 | Two more are down there somewhere. |
| (0.85 s hold) | |
| 20.60-23.50 | The carriers never even saw each other. |
| 23.80-26.05 | They fought with planes, from far out at sea. |
| (0.3 s) | |
| 26.35-26.92 | That's why |
| (loop) | the carriers sunk at Midway aren't at Midway. |

**Pronunciation notes for Rodney**
- No Hawaiian word is voiced in this Short.
- Midway MID-way; USS you-ess-ess; Yorktown YORK-town; Japanese jap-uh-NEEZ; Pacific puh-SIF-ik; Boston BAW-stun; New York noo YORK. "nineteen forty-two" spelled out so it is read as a year; "In June of" avoids the comma pause.
- Description only (not voiced): Papahānaumokuākea pah-pah-HAH-now-moh-koo-ah-KEH-ah (lexicon); Hawaiʻi hah-WHY-ee, with a glottal catch before the final "ee".
- Ship names (never voiced): Kaga KAH-gah; Akagi ah-KAH-ghee (hard g); Sōryū SOH-ryoo; Hiryū HEE-ryoo.

**Fallback if VERIFY fails on "The carriers never even saw each other."** Use "The carriers stayed far apart." (true: their strikes flew to targets far beyond sight), read at 20.9-22.6; then "They fought with planes," at 22.9 and "from far out at sea." ending at 25.15; then "That's why" at 25.45-26.0, with T at about 26.1. Shots 7-10 compress by 0.9 s.

## 2. Second-by-second table

**Global specs**
- 1080x1920, 30 fps, T = 27.000 s (810 frames). Text safe box x 72-849, y 200-1529 (captions per house spec); no key element right of x 900 or below y 1536. Every cap ≥ 77 px; labels cap 80 or more.
- Fonts: Barlow Condensed 800 caps (tracking 0.04) for words; Anton for the "3" and the captions. White words get a navy (#0B1D28) stroke of 0.13 x cap; ink text #1C2228 sits on paper or pale sky only.
- Captions: house spec (Anton cap 80, centred x 460 / y 1515, white, active word cyan #00E5FF, unboxed, 1-3 words per card, synced within 0.1 s, no card shorter than 0.3 s); suppressed while a label shows the same word.
- Terrain at VE 1.0 in every shot.
- Palette (gate.py tan-free): water #3DE3FF / #1FA3B8 / #13627E with a white foam rim; drained floor in pelagic-clay browns (lit #5E4A3E, brightest channel capped at 110 after grade; shade #3E3129); volcano flanks basalt #2A2B2D; limestone crowns (Midway, and Kure dimmed to 60%) neutral pale #E8E5DC (saturation 0.05); sky #E4ECEF at the horizon through #B5CCDD to #86A9C8 at the top (saturation below 0.35); paper #F6F1E4 with a #D9D6CE edge and soft offset shadow; line yellow #FFD23F, 12 px core, 20 px under-stroke rgba(8,12,18,0.75), soft glow, head dot r 20 with one slow pulse ring.
- Exposure: mean luma ≥ 70 per shot, from the sky and water, never from pushing the floor.
- Sun: azimuth about 70, elevation about 14, behind-right of a camera facing 323°; no glare.
- Banned devices: plates or boxes, arrows, a dashed sea-level line, a tan basin. Mood: solemn; no music, only a low drone bed; no gags, no stings.

**Camera poses** (vertical FOV 62°; computed by haversine and projection in /tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/short05/v2/geo.py, cams.py, c0b.py)
- C0 (frame 0): on the 323° line, 2.5 km southeast (inside the lagoon) of the NW outer-reef crest where the line leaves the atoll (about 28.29°N 177.41°W; pick it on the imagery); 700 m up, heading 323°, pitch -15°. Lagoon y 1000-1920, reef surf y ≈ 980, horizon y ≈ 557; the line runs up the centre column (x 540). H(t) pushes northwest at 40 m/s.
- A (the atoll): about 12 km further southeast along the axis, 5 km up, pitch -24°; reef ring at y ≈ 650-1250, horizon y ≈ 330.
- HO (high oblique): on the axis, 150 km southeast of Sand Island, 120 km up, heading 323°, pitch -32°. Midway at (549, 1158); the dot at Kaga's recorded position at (552, 542); Kure at (176, 886); horizon y ≈ 348.
- P1: 7 km southeast of the Kaga point on the line, at the old sea-surface height, heading 316°, pitch -22°. Floor dot at (701, 1415); surface tick at (752, 316); floor horizon y ≈ 390.
- P2: same spot, 300 m above the floor, heading 316°, pitch +13°. The plumb runs from (713, 273) to (744, 1403); horizon y ≈ 1345.

**00.0-01.0 · SHOT 1 POSTCARD (frame 0)**
- Picture: new camera C0 with motion H(t), already pushing northwest. Rebuilt from the long-form's Midway reef-ring terrain, drape, water shader and foam. Turquoise lagoon foreground, white surf on the NW reef, darker open sea, pale horizon. The yellow line is already drawing out from the reef crest up the centre column; its head dot at y ≈ 800 at frame 0 and accelerating. Postcard card: off-white paper, tilt -3°, x 80-560, y 205-585. A paper slip tucked into its lower edge (x 160-480, y 465-555) carries one solid ink carrier silhouette (home-built, generic, unmarked, 300x70).
- Text: MIDWAY (Barlow cap 96, 5.0%, y 235-331); ATOLL (cap 80, y 355-435). Caption THE CARRIERS.
- VO: "The carriers sunk at"
- Sound: low drone bed; soft reef surf.

**01.0-02.0**
- Picture: the push continues; the head dot reaches y ≈ 700. At 1.60, on "aren't", the slip peels off the card, drops onto the line at the reef and skims out along it after the head dot, shrinking with perspective (UI layer, positioned on the projected line).
- Text: MIDWAY ATOLL. Captions SUNK AT MIDWAY (0.70-1.55), AREN'T AT MIDWAY. (1.60-2.95).
- VO: "Midway aren't at"
- Sound: paper peel at 1.60 (postcard motif 1 of 2).

**02.0-03.15**
- Picture: the slip catches the head dot near the horizon (y ≈ 585, about 14 mi of line) at 2.85 and vanishes into it with one pulse. The card, now just MIDWAY ATOLL, lifts out 2.95-3.15.
- Text: MIDWAY ATOLL (out at 3.15).
- VO: "Midway." (ends 2.95)
- Sound: drone.

**03.15-04.2 · SHOT 2 THE ATOLL**
- Picture: the push eases out; the camera rises and pulls back southeast along the axis to pose A (reached at 6.0). The whole reef ring comes into the lower half; the line still runs from the reef to the horizon. Live sea. Rebuilt from the long-form reef ring, new camera.
- Text: caption IN JUNE.
- VO: "In June of"
- Sound: drone; surf thins with altitude.

**04.2-05.15**
- Picture: the rise continues; something moves every frame (camera and line).
- Text: caption OF 1942,
- VO: "nineteen forty-two,"

**05.15-06.2**
- Picture: four paper discs (D 104, off-white, each with the same ink carrier silhouette as the slip) pop in at 5.30, 5.55, 5.80 and 6.05, on "four Japanese carriers", at x 72-530, y 300-404.
- Text: 4 discs. Caption FOUR JAPANESE.
- VO: "four Japanese"
- Sound: one soft paper tap at 5.30 (taps 1 of 2).

**06.2-07.2**
- Picture: 6.85-7.10 the Yorktown print slides up into place: the long-form's Ch5 NHHC public-domain photo of USS Yorktown listing on 4 June 1942, as a paper print with an 18 px off-white border, x 96-876, y 600-1120 (780 px wide), tilt +2°, pushing 1.00 to 1.03. The scene behind dims to 65%.
- Text: 4 discs. Captions CARRIERS (6.15-6.80), AND THE USS.
- VO: "carriers and the USS"
- Sound: very soft paper slide.

**07.2-08.4**
- Picture: the print holds. The fifth disc pops in at 7.75, on "Yorktown", after a 40 px gap: x 570-674.
- Text: 5 discs. Caption YORKTOWN.
- VO: "Yorktown"
- Sound: soft paper tap (2 of 2).

**08.4-09.35**
- Picture: on "went down", the print sinks slowly down and out through the bottom edge (8.55-8.95). The discs fade 9.05-9.35. The photo was on screen 2.05 s, on the name.
- Text: caption WENT DOWN.
- VO: "went down." (ends 9.00)
- Sound: drone.

**09.35-10.5 · SHOT 3 DRAIN, a thought experiment that starts on the word**
- Picture: at 9.35, on "Drain", the sea starts falling: 0 to -5,400 m over 9.40-12.40, ease-in-out (the long-form's drain level curve, retimed). The camera pulls back and up from pose A toward HO, at log altitude. Midway's reef stands up as a pale limestone crown on dark basalt flanks. The line peels down with the water and drapes over the reef edge and down the flank (z = max(terrain, water level)).
- Text: captions DRAIN, / THE PACIFIC,
- VO: "Drain the Pacific,"
- Sound: a deep, slow water-recession rumble starts; surf fades out.

**10.5-11.5**
- Picture: dark brown sediment spreads around the volcano's base. The head dot runs out along the floor and eases to a stop at 11.20 at Kaga's recorded position, (552, 542) in HO, with one pulse ring. Kure's dimmed reef crown rises on its own drowned volcano at left (about 176, 886).
- Text: caption AND THERE'S ONE,
- VO: "and there's one,"
- Sound: sonar ping 1 at 11.20 (soft, short echo). Rumble thins.

**11.5-12.6**
- Picture: HO is reached at 11.9, then a slow 1% push. At 11.55 the MIDWAY paper card drops in under the crown. The drain finishes at 12.40.
- Text: MIDWAY (ink on paper, cap 80, card x 330-750, y 1215-1335, tilt -2°). Captions AS FAR FROM, / MIDWAY.
- VO: "as far from Midway"
- Sound: high, thin air bed.

**12.6-13.4 · TRUE SIZE**
- Picture: a paper cut-out of the real US Northeast coast, Boston to New York City (off-white at 85%, ink coastline, two ink city dots), slides in from the left over 12.65-12.95 and lies flat on the floor at true scale, rotated 88.8° so its Boston dot sits at the foot of Midway's volcano, directly under the crown, and its New York dot on the yellow dot. The yellow line stays on top.
- Text: MIDWAY; BOSTON (white, cap 80, x 150-437, y 1060-1140, in at 12.80). Caption AS BOSTON.
- VO: "as Boston"
- Sound: soft paper drag.

**13.4-14.4**
- Picture: hold to read (three labels at most, seven words at most including the caption).
- Text: MIDWAY, BOSTON, NEW YORK (cap 80, x 120-503, y 502-582, in at 13.50). Captions IS FROM, / NEW YORK.
- VO: "is from New York." (ends 14.35)
- Sound: air bed.

**14.4-14.95 · SHOT 4 DIVE**
- Picture: at 14.45 the cut-out, labels and card peel away. Over 14.50-14.95 the camera whip-dives down the line to the dot: log altitude from 120 km to the old sea surface, heading 323° to 316°, with motion blur. It lands in P1.
- Text: none. VO: (0.5 s gap). Sound: low air rush.

**14.95-16.1 · SHOT 4 PLUNGE** (new, native vertical)
- Picture: P1: a flat, dark, sunlit plain runs to a horizon at y ≈ 390. The line enters from the bottom edge and ends at the floor dot (701, 1415). A short turquoise wave tick (a solid 80 px wavy stroke at x 712-792, y ≈ 316) marks the old sea surface above it, with a second yellow dot on the tick. Over 15.00-16.05 the camera falls straight down to P2 (ease-in-out), pitching -22° to +13°. The second dot falls with the camera's depth fraction and draws the yellow plumb; the plumb holds nearly still on screen while the horizon sweeps down and the sky opens.
- Text: DEPTH CARD (off-white paper, tilt -2°, x 72-560, y 290-830, in at 14.95): line 1 MORE THAN (ink, Barlow cap 80, already printed); line 2, stamped in at 15.35 as one unit: 3 (Anton cap 280, ink, with a 12 px #FFD23F bar under it matching the plumb) and MILES (Barlow cap 96); line 3 DOWN (Barlow cap 96), stamped in at 15.80. Captions suppressed while the card shows the same words.
- VO: "More than three miles down,"
- Sound: slow descending pressure tone. Sonar ping 2 at 16.05, when the dot lands (deeper, long echo).

**16.1-17.0 · SHOT 5 UPRIGHT**
- Picture: P2: the plumb spans y 273-1403, so the whole frame is the 3-mile gauge. 16.30-16.55 an inset zoom circle irises open (D 340, centre (380, 1150), 6 px off-white rim, a thin off-white leader to the plumb foot). Inside: a plain hull silhouette, upright, its lower hull buried in dark sediment, with no island, no flight deck and no debris (the long-form's honest wreck-line hull art, trimmed to match the surveyed wreck).
- Text: depth card holds. Caption IT'S STILL.
- VO: "it's still"
- Sound: echo tail.

**17.0-17.95**
- Picture: hold with a 2% push. The depth card fades 17.65-17.95.
- Text: caption SITTING UPRIGHT.
- VO: "sitting upright." (ends 17.60)
- Sound: drone.

**17.95-19.0 · SHOT 6 SOMEWHERE**
- Picture: same pose, 1% push. The five discs return to their shot-2 places (x 72-674, y 300-404), all solid, 17.95-18.10. On "down there" (18.55-19.00), discs 3 and 4 (Sōryū and Hiryū) lose their ink: the silhouette drains out and the rim turns into a dashed outline.
- Text: 5 discs. Captions TWO MORE ARE / DOWN THERE.
- VO: "Two more are down there"
- Sound: drone only.

**19.0-19.75**
- Picture: hold.
- Text: SOMEWHERE (ink with a 3 px off-white halo, Barlow cap 80, 549 px wide, on the pale sky centred under discs 3-4: x 145-694, y 440-520), in at 19.05. Caption suppressed (the label carries the word).
- VO: "somewhere." (ends 19.75)
- Sound: drone.

**19.75-20.6**
- Picture: hold for 0.85 s.
- Text: same.
- VO: (silence)
- Sound: sonar ping 3 at 19.85, with no echo.

**20.6-21.5 · SHOT 7 THE SEA COMES BACK** (the long-form drain reversed)
- Picture: the discs and the word fade 20.40-20.70. Turquoise water rises from the plain, 20.50-22.40, ease-in-out. The inset irises shut as the water covers the hull (20.75-21.05). The camera rides up with the surface, 300 m above it, pitching +13° to -16° and turning from heading 316° to 323°.
- Text: caption THE CARRIERS.
- VO: "The carriers"
- Sound: deep, slow water swell.

**21.5-22.4**
- Picture: the water climbs the plumb; the plumb is gone when the surface reaches the tick (22.30). The line lifts with the water and lies on the surface.
- Text: caption NEVER EVEN.
- VO: "never even"
- Sound: swell.

**22.4-23.5 · SHOT 8 WIDE**
- Picture: over 22.40-23.90 the camera climbs from 300 m over the restored sea and pulls back to HO at log altitude (most of the translation high up; motion blur at a 180° shutter). The whole line lies on a turquoise ocean, from Midway's reef at the surface to the dot; Kure's dimmed reef at left. HO again: sea gone, then sea back.
- Text: caption SAW EACH OTHER.
- VO: "saw each other." (ends 23.50)
- Sound: swell settles; light sea air.

**23.5-24.8**
- Picture: HO with a slow 1% push. At 23.85 three paper plane silhouettes (home-built, generic single-engine monoplanes, unmarked, off-white with ink) lift off near the dot and fly down the line toward Midway in a loose V, growing slightly with perspective, soft shadows on the water.
- Text: captions THEY FOUGHT, / WITH PLANES,
- VO: "They fought with planes,"
- Sound: faint distant engine hum (-32 dB), 23.85-25.3.

**24.8-25.9 · SHOT 9 HOME**
- Picture: at 24.60 the camera starts a log-altitude descent from HO toward C0, following the planes, pitch -32° to -15°: a zoom into place, mostly along the line of sight, so it does not strobe. The planes pass beneath the camera and exit through the bottom edge by 25.40. The line rewinds: its head retracts toward Midway and holds near y 780 as the camera comes down.
- Text: captions FROM FAR, / OUT AT SEA.
- VO: "from far out at sea." (ends 26.05)
- Sound: soft air rush.

**25.9-26.4**
- Picture: the atoll slides in from the bottom edge and the camera eases into C0. Over 25.90-26.30 the MIDWAY ATOLL card, with its carrier slip tucked in, drops into its frame-0 place. The line's head reaches the reef crest, and its velocity crosses zero at 26.40 (one frame, no hold).
- Text: MIDWAY ATOLL (frame-0 layout).
- VO: (0.3 s gap)
- Sound: paper drop (postcard motif 2 of 2). Surf fades in to its frame-0 level.

**26.4-27.0 · SHOT 10 SEAM**
- Picture: frames 792-809 are rendered from the hook motion H(t-27.0): the camera pushes northwest at 40 m/s and the line draws out again. Frame 809 is frame 0 one frame earlier.
- Text: MIDWAY ATOLL. Caption THAT'S WHY.
- VO: "That's why" (26.35-26.92), which loops into "the carriers sunk at Midway..."
- Sound: the drone bed (a seamless 27.000 s loop) runs across the seam.

**Audio master:** -14 LUFS integrated, VO at least 12 LU above the bed; exactly 3 sonar pings; 2 disc taps; the paper postcard motif twice (peel, drop); no SFX motif more than 3 times. Master as a loop: render T + 2 s and fold the tail onto the head. Test by playing 26.0-27.0 and 0.0-1.0 back to back on a phone speaker.

## 3. Hook

- VO at 0.04: "The carriers sunk at Midway aren't at Midway." (8 words, about 2.9 s, word for word the title.) The contradiction opens "then where are they?", which the next 14 s answer. The take puts this sentence mid-paragraph, for a lifted, non-final read.
- Frame 0 is already moving and carries the question with the sound off: a low golden-morning oblique from inside Midway's lagoon looks northwest across turquoise water and the white surf of the outer reef to an empty horizon; a thick yellow line is already racing out from the reef up the centre; an off-white postcard (MIDWAY / ATOLL) in the upper third with a tucked-in paper slip carrying one ink carrier silhouette. "ATOLL" plus the reef reads as a place (not the USS Midway museum ship); the carrier reads as war, not travel.
- At 1.60, on "aren't", the carrier slip peels off the card and skims out along the line to the horizon, vanishing into the head dot as "Midway" ends (2.85): the paradox is seen as well as heard by about 2.9 s.
- No clone device (no black caption box, curved arrow, depth label, dashed sea-level line or tan basin); not Short 4's top-down ring; no Everest, no "taller than", no title clone words.
- Premise check (ytsearch, 2026-11-08; short05/probe.txt, probe2.txt, probe3.txt): the exact angle returns 0 on-angle Shorts; "how deep are the midway wrecks" finds wreck long-forms at 140K-613K but no Short on where the wrecks are; Midway Shorts pull 1.5M-5.1M.

## 4. Payoff

Four beats, each landing on a picture; only one number shown big.
1. **Where (9.35-14.35).** "Drain the Pacific" starts the drain on the word, so it reads as a thought experiment, not history. The camera pulls out to a 120 km high oblique where the line runs straight up the frame from Midway's limestone crown to a dot at Kaga's recorded position. "...and there's one, as far from Midway as Boston is from New York." A true-size paper cut-out of the Northeast coast lies down on the drained floor, Boston at Midway and New York at the dot: US viewers feel the 190 miles without hearing the number.
2. **Depth (14.45-16.05).** The camera whip-dives down the line to the old sea surface, then falls straight down beside a yellow plumb that holds still while the world rushes up: the whole 9:16 frame becomes the gauge. MORE THAN / 3 MILES / DOWN stamps on, 3 and MILES together; the second ping hits as the plumb touches bottom.
3. **Upright (16.3-17.6).** An inset opens on a plain hull standing upright, buried in sediment: "it's still sitting upright." A war-grave image with no wreck footage and no debris.
4. **The count and the why (17.95-26.92).** The five discs return; on "down there" the ink drains out of two of them and SOMEWHERE appears; a third ping goes out and gets no echo (the emotional peak, held 0.85 s). The sea rises back over the grave; the camera climbs to the same high oblique with the ocean restored. "The carriers never even saw each other." (a real "huh" late in the Short). "They fought with planes, from far out at sea": three paper planes fly the whole line toward Midway, and the camera follows them home. "That's why..." completes the hook on the replay.

Tone throughout: war graves. No music, no gags, no treasure framing, no real wreck imagery.

## 5. Loop check

**Audio.** "The carriers never even saw each other. They fought with planes, from far out at sea. That's why the carriers sunk at Midway aren't at Midway. In June of nineteen forty-two, four Japanese carriers..." "That's why" plus the hook is one ordinary English sentence; heard cold, the hook is a plain statement. Both pieces come from one take, cut at a zero crossing in the middle of the 80-150 ms gap between "why" and "the", so the replay plays the take's own continuous audio with its real breath; the gap also absorbs YouTube's small loop hitch. Both sides of the seam have mid-paragraph prosody; "sea" has a continuing-intonation variant (V2) and the beat before "That's why" is 0.3 s, so nothing sounds like THE END. The drone bed is a seamless 27.000 s loop; the surf ends at its frame-0 level; the mix is loop-mastered.

**Picture.** The last frame (809, t 26.967) is frame 0's camera and state one frame earlier: pose C0 (on the 323° line, 2.5 km inside the NW reef crest, 700 m up, heading 323°, pitch -15°, vertical FOV 62°); same sun; same lagoon, surf and horizon; the same MIDWAY ATOLL card with the carrier slip tucked in, settled by 26.30. The descent into C0 is a C1 spline whose end conditions equal H(-0.6) in position and velocity; frames 792-809 are rendered from H(t-27.0); the line's rewind and redraw reverse as one velocity zero-crossing at 26.40 (one frame, no hold); the planes left the frame by 25.40; water, foam, glints and the bed run on a periodic 27.000 s clock. The caption flips from THAT'S WHY to THE CARRIERS exactly at the word boundary.

**Seam tests before upload:** frame 809 to frame 0 MAE ≤ about 5/255 and SSIM ≥ 0.97; concatenate the Short with itself and run temporal_scan.py (no "cut" or "flash"); play 26.0-27.0 and 0.0-1.0 back to back (no pop, click or doubled frame); after a private test upload (owner's OK needed even for private or unlisted), check the loop on a real phone.

## 6. Facts

Claim by claim against the brief's fact spine (brief section 4) and the ledger (C5-xx in research/ep02/script/ledger_part3.json).
1. **"The carriers sunk at Midway aren't at Midway."** Spine #15 plus brief must-fix #2: the wrecks lie on the deep ocean floor, not on the atoll; Kaga about 304 km (189 mi) out, Yorktown about 277 km (172 mi) (C5-15).
2. **"In June of nineteen forty-two, four Japanese carriers and the USS Yorktown went down."** Spine #14; C5-12 (all four Japanese fleet carriers present; Yorktown crippled on 4 June, sank 7 June 1942). All five sank in June 1942. Never "Japan lost all its carriers".
3. **"Drain the Pacific, and there's one, as far from Midway as Boston is from New York."** A thought experiment ("Drain..."), with the drain starting on that word (look-book blocker B3). "One" is Kaga: its recorded sinking position, 30°23'N 179°17'W, is 304.3 km / 189.1 mi from Sand Island at a bearing of 323.0° (haversine; C5-15: 304 km / 189 mi). NEW LEDGER ITEM (computed 2026-11-08): Boston City Hall (42.3601N, 71.0589W) to New York City Hall (40.7128N, 74.0060W) is 306.1 km / 190.2 mi great-circle (BOS-JFK 186.3 mi); "as far as" holds to within 1%. Akagi (176 mi) and Yorktown (172 mi) are not compared; the narration says "one".
4. **"More than three miles down,"** C5-14: Kaga and Akagi "found 5,400 meters (more than 17,000 feet) below the surface"; Yorktown 16,650 ft (3.15 mi); "more than three miles down" is true for all three. Brief unit table: 5.4 km = 3.4 mi.
5. **"it's still sitting upright."** NEW LEDGER ITEM: Wikipedia, Japanese aircraft carrier Kaga: "She sits upright", "buried up to the degaussing wires in the seafloor and with most of her superstructure and flight deck missing"; so the inset hull is upright, partly buried, with no island and no flight deck. Nautilus surveyed the wreck in Sept 2023 (spine #15). Re-read the article on upload day.
6. **"Two more are down there somewhere."** TRUE under every scenario. Sōryū and Hiryū sank in June 1942 (C5-12), so their wrecks lie somewhere on the sea floor; C5-13 found no public report of their discovery as of 2026-11-08 and bans "still lost" and "never found" (absence of a report is not proof). This line claims neither, and no position is drawn for them. Re-check the news on upload day.
7. **"The carriers never even saw each other."** VERIFY (not in the spine; add to the ledger). NHHC, "Battle of Midway, 3-6 June 1942, Combat Narrative": "The surface ships in both forces never see each other; all attacks are by air." (quoted by the search engine on 2026-11-08; the page returned 503). Air & Space Forces Magazine, "The Battle of Midway": "At Midway, the opposing fleets never came within sight of each other." "Carriers" rather than "fleets" because submarine I-168 did sight Yorktown. Never say "first" (Coral Sea came first). Read the NHHC page before lock; if it fails, use the fallback line.
8. **"They fought with planes, from far out at sea."** VERIFY-light (standard history): land-based planes from Midway and carrier planes attacked Nagumo's force; Spruance launched "at extreme range" (Wikipedia, Battle of Midway). It describes how the carriers fought, not what finished each ship (a submarine finished Yorktown; Japanese destroyers scuttled burning carriers). C5-10: the carrier fight happened at sea, far from the atoll.
9. **"That's why the carriers sunk at Midway aren't at Midway."** Follows from 3, 7 and 8.

**Visual facts**
- The dot is at Kaga's recorded sinking position (the description says "about"). HO projections: Midway (549, 1158), Kaga (552, 542), Kure (176, 886). Akagi's position would fall at about (752, 566) but is not drawn: Akagi and Yorktown are counted only in the disc row (no fake positions). Pearl and Hermes is out of frame.
- Kure is 92 km from Sand Island at 283°; it gets its own reef crown, dimmed (spine #13).
- Midway's crown on a drowned basalt volcano follows spines #11-12; the crown band is schematic (limestone above about -400 m).
- The Boston-New York cut-out is a real coastline (Natural Earth, public domain) at true scale, rotated 88.8° (Boston-NYC bearing 234.2° onto the line's 323.0°); its dots land within about 2 km of the line ends.
- Disc order Akagi, Kaga, Sōryū, Hiryū, then Yorktown: discs 1, 2 and 5 stay solid; discs 3 and 4 lose their ink (spine #15, C5-13).
- Plane silhouettes are home-built, generic and unmarked; no narration says whose they are; consistent with the Japanese air strike on Midway on 4 June, but an illustration only.
- Hull and plane art home-built; no OET, NOAA or Vulcan imagery, no flags, no gore, no treasure framing. War-grave framing: C5-16 (NHHC Director Cox: "important war graves of both American and Japanese sailors").
- The plunge depth uses real ETOPO/GEBCO depth at Kaga's position (expect about 5.4 km). The C0 reef-crest point is approximate; set it on the imagery.
- Yorktown photo VERIFY: best NHHC catalogue match 80-G-17062 ("dead in the water and listing heavily", afternoon of 4 June 1942, before abandonment); a U.S. Navy photo is public domain. Confirm it is the same file the long-form uses and that no casualties are visible (alternatives 80-G-21666, 80-G-414423).

Dropped or avoided: the "AF is short of water" decoy, Everest, 56,000 ft, the dent, any Hawaiian name in the narration, on-screen sources, "three have been found", "never found", and the long-form's own wreck line.

## 7. Renders: new for this Short vs reused

New, Short-only, vertical 1080x1920 at 30 fps. The long-form and its files are not touched; every changed asset is a copy.
1. **Pose C0 and the hook motion H(t)** for t from -0.6 to 3.15 s; the seam frames 792-809 rendered from H(t-27.0); re-bake shadows and AO for the morning sun (azimuth 70, elevation 14) if the long-form used another sun. The lagoon foreground needs the sharpest drape available (Sentinel-2 10 m or Landsat 15 m pan); if soft, raise C0 to about 1.0 km and re-aim so the reef surf sits at y ≈ 980.
2. **Shot 2:** the rise and pull-back from C0 to pose A over the live sea, with the line drawn on the water surface to the horizon.
3. **Shot 3:** the drain on "Drain" (0 to -5,400 m over 9.40-12.40) with a log pull-back to HO; the line drapes by z = max(terrain, water level); the head dot stops at Kaga's recorded position.
4. **Regional terrain:** GEBCO 2024 15" over lat 27.0-31.5, lon -180.0 to -175.5 (does not cross the antimeridian). Materials: pelagic-clay browns below about -4,500 m; basalt on the volcanoes; neutral pale limestone crowns on Midway and Kure (Kure dimmed to 60%, new mask). gate.py on frames 0.0, 7.5, 11.9, 15.0, 16.2 and 24.0 (tan ≤ 10%; log the blue share). Mean luma ≥ 70 per shot.
5. **True-size paper cut-out** (new asset): Natural Earth or TIGER (public domain) Massachusetts-Rhode Island-Connecticut-New York coastline, Boston to New York City, true scale, rotated 88.8°, rendered as off-white paper at 85% with an ink coast and two city dots, projected flat onto the sampled floor; slide in, then peel away.
6. **Shot 4 dive and plunge:** a 0.45 s log-altitude whip-dive from HO down the line to P1 with motion blur, then a straight drop to P2. The plumb is a 3D vertical line from z 0 to the floor, projected and drawn crisp in the UI layer ((713, 273) to (744, 1403) at P2); the falling dot synced to the camera's depth fraction; the turquoise wave tick a new glyph.
7. **Shot 7 refill:** the camera rides 300 m above the rising water, pitch +13° to -16°, heading 316° to 323°; the plumb consumed by the rising water; the inset closes as the water covers the hull.
8. **Shot 8:** the climb from 300 m back to HO over the restored sea, translation weighted to high altitude, motion blur at a 180° shutter; peak feature motion ≤ 90 px/frame (check with temporal_scan.py).
9. **Shot 9:** three home-built paper plane silhouettes fly down the line with soft water shadows; the log descent from HO into C0 as a C1 spline ending at H(-0.6) in position and velocity, while the line rewinds.
10. **New UI pieces:** MIDWAY ATOLL postcard (two lines) with a removable carrier slip (peels at 1.60, drops back in at 25.90); the MIDWAY card (cap 80); five paper discs with an ink-drain-to-dashed transition; the depth card MORE THAN / 3 MILES / DOWN with stamp-in; SOMEWHERE in ink with a halo; BOSTON and NEW YORK labels; the inset zoom circle (iris open and close); the house caption track.
11. **Hull art:** a copy of the long-form's honest wreck-line hull silhouette, trimmed to a plain hull with no island and no flight deck, lower part buried in sediment.
12. **Shot 2 print:** a 780 px paper-print treatment of the existing Yorktown photo (x 96-876, tilt +2°, push 1.00 to 1.03), sliding up in and sinking out (a print rather than full-bleed because a 9:16 crop would cut the hull).
13. **Audio:** loop-mastered mix on a 27.000 s drone bed; three sonar pings (soft; deep with an echo; no echo); drain rumble and refill swell, surf, faint engine hum; paper peel and drop (postcard motif), two disc taps, a paper drag; the VO cut at the zero crossing in the middle of the "why | the" gap.

QC sheets: a 390 px phone sheet of every shot's middle frame; a typeqc log (every cap ≥ 77 px; all text inside x 72-849, y 200-1529, captions per house spec); the seam MAE/SSIM and self-concatenation scan.

**Reused as-is from the long-form:** the NHHC Yorktown public-domain photo file and its grade (Ch5); the Midway terrain data, drape, water shader, foam rim and drain level curve (the reef ring and drain/reef cap), only retimed and re-cammed; the yellow line and head-dot style, the Anton and Barlow type system and the paper style; the music-down tone of the wreck beat.

## 8. Title, description, link

**Title:** The Carriers Sunk at Midway Aren't at Midway (44 characters; passes the niche title regex and the clone-word ban; word for word the spoken hook; exact-title probe found 0 on-angle matches). Trade-off: "Midway" is word 5, not in the first 3 words; fallback "Midway's Sunken Carriers Aren't at Midway" (41, also passes) loses the "sunk at / aren't at" mirror.

**Release:** D+9. Related Video set to "Why Can't You See Most of Hawaii? (Look Down)". Nothing is uploaded, scheduled or made visible without the owner's explicit OK.

**Description** (no emojis; sources only here):

> The Battle of Midway is named for the atoll, but the carriers sunk in it lie far out on the open Pacific floor. Kaga rests about 190 miles from Midway, roughly as far as Boston is from New York, more than three miles down and still upright. Akagi and USS Yorktown have also been found. No discovery of Sōryū or Hiryū has been reported. The wrecks are war graves of Japanese and American sailors, inside Papahānaumokuākea Marine National Monument.
>
> Watch the full film, with the ocean around Hawaiʻi drained away: Why Can't You See Most of Hawaii? (Look Down). It is linked above.
>
> Approximate depths and distances:
> - Kaga about 5.4 km (more than 17,000 ft) down, about 190 miles from Midway.
> - Akagi more than 17,000 ft down.
> - USS Yorktown about 5.1 km (16,650 ft) down, about 172 miles from Midway.
> - Boston to New York City is about 190 miles in a straight line.
> Seafloor from GEBCO and NOAA ETOPO 2022; coastline from Natural Earth. The ship and plane shapes and the coastline cut-out are our own simple drawings, not images of the wrecks.
>
> Sources:
> - Naval History and Heritage Command, Battle of Midway, 3-6 June 1942, Combat Narrative
> - Air & Space Forces Magazine, "The Battle of Midway"
> - Ocean Exploration Trust, Nautilus Live, "Exploring Iconic Shipwrecks of the Battle of Midway" (Sept 2023)
> - Papahānaumokuākea Marine National Monument, Kaga discovery (Oct 2019)
> - MIT News, Yorktown found (June 1998)
> - Wikipedia: Battle of Midway; Japanese aircraft carrier Kaga; Japanese aircraft carrier Akagi; USS Yorktown (CV-5)
>
> Photo: USS Yorktown, 4 June 1942, U.S. Navy / Naval History and Heritage Command, public domain. [Catalogue number after VERIFY.]

Integrator note: the Akagi depth uses the ledger's C5-14 wording ("more than 17,000 feet", Papahānaumokuākea), since the ledger gives no Akagi-specific depth beyond that.

**Pinned comment** (a place with living memory): "Did someone in your family serve at Midway, on either side? Tell us their story." Heart and answer the family stories; no jokes in replies.

**Tags:** Battle of Midway, Midway Atoll, USS Yorktown, Kaga, Akagi, WW2 shipwrecks, Pacific Ocean floor, drained ocean, Hawaii, Papahānaumokuākea. "Drained" is allowed in tags, not in the title.

**How it links to the long-form:** it rebuilds the long-form's Ch5 Midway elements as a solemn myth-bust (the reef ring, the drain and reef cap, the NHHC Yorktown photo, the honest wreck line with the home-built hull) and adds Short-only devices (the postcard carrier slip, the Boston-New York true-size cut-out, the vertical plunge gauge, the ink-draining discs). It never spends the long-form's payoff (no 56,000 ft, no dent, no Everest, no "taller than"). The long-form is unchanged.

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 68. All 9 must-fixes are in: the drain starts on "Drain the Pacific" with the 1942 sentence on the live reef; the "three ... three" collision is gone (no spoken count of found wrecks; 3 and MILES land together); WHERE is answered with the Boston-New York cut-out and no second big number; "fleets" became "carriers" (VERIFY); the beat before "That's why" is 0.3 s with a continuing-intonation variant; the hook sentence sits mid-paragraph; the palette is tan-free; Kure has a dimmed reef crown; frame 0 carries a war signal (the carrier slip), with the plumb at x 713-744 and the print 780 px wide.
