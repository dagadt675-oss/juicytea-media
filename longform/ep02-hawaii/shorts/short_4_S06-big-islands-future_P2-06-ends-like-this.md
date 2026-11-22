# Short 4 (S06-big-islands-future + P2-06-ends-like-this, with S07 Nihoa as a stage): "Where Hawaiʻi's Big Island Is Headed"

| | |
|---|---|
| Release | **D+5**, same clock hour as the long-form (slot 4 of 7) |
| Length | 29.77 s planned (T, frame 893); conform to the real word times |
| The one big number | ABOUT 28 MILLION YEARS |
| Voice | Rodney - Clear Educator, `eY2VJs4Gi8QKG2RV01sS`, `eleven_v4`, passed explicitly |
| Format | 1080x1920, 30 fps; heading ~300° throughout (northwest is always up) |
| Related Video | "Why Can't You See Most of Hawaii? (Look Down)" |

All times are estimates at Rodney's pace of about 2.8 words/s; every picture event is anchored to a word.

## Integrator changes (2026-11-08)

1. Captions follow the house spec (shorts_plan.md section 4): Anton cap 80, centred x 460 / y 1515 (was x 464; the note about Short 6 sitting 25 px higher is resolved, since all 7 now share one position).
2. The KAUAʻI label is Barlow Condensed 800, whose U+02BB draws as a backtick. type.js draws Barlow's U+2018 glyph for U+02BB (house rule); the text stays U+02BB.
3. TTS settings: the locked long-form settings (`"settings": {}`); stability 0.35 / style 0.4 only as an A/B take.
4. Corrected a claim: the postcard is NOT on all 7 Shorts. It opens and closes Shorts 4, 5 and 7; Short 2 uses the paper name slip with the stamp, Short 6 a sign in postcard paper, Shorts 1 and 3 a headline. The shared brand marks across all 7 are the paper language and the paper-flap sound motif.
5. Release order: this Short and Short 5 both open on Midway's reef with a postcard; they are now 4 days apart (D+5 and D+9) instead of 2.

## 1. Narration and TTS

**As heard (one loop):**
> Hawaiʻi's Big Island is headed here. A hot spot builds a volcano. The sea floor carries it away. Slowly, it sinks. Rain carves it into canyons. Then a sliver of rock that people once farmed. Then one last tooth. Then just a ring of reef. Under it, a volcano about twenty-eight million years old, sunk out of sight. Every island on this line takes the same trip. So,

**TTS take** (ONE take of 74 words; generate it 3 times (`"take": 1, 2, 3`) and pick by ASR (small.en and medium.en) and the owner's listen; 68 of the 74 words go on air):
> Hawaii's Big Island is headed here. A hot spot builds a volcano. The sea floor carries it away. Slowly, it sinks. Rain carves it into canyons. Then a sliver of rock that people once farmed. Then one last tooth. Then just a ring of reef. Under it, a volcano about twenty-eight million years old, sunk out of sight. Every island on this line takes the same trip. So, Hawaii's Big Island is headed here.

- Voice "Rodney - Clear Educator" (`eY2VJs4Gi8QKG2RV01sS`), `eleven_v4`, passed explicitly (tts.py still defaults to Brian); the locked long-form settings.
- The TTS text uses plain "Hawaii's" (lexicon.json); captions map it to "Hawaiʻi's" through caption_map.
- The take's CLOSING sentence, "So, Hawaii's Big Island is headed here.", holds the loop seam. The on-air VO1 is the part of that sentence after "So,". The take's opening read of the same sentence is a spare that gives VO2 a natural run-in.
- Split the take into sentence clips at its natural gaps, place each clip at the times below and fill gaps with the take's own room tone. Never split inside "same trip. So, Hawaii's...".
- T is the cut, in the middle of the comma gap between "So," and "Hawaii's". Planned T = 29.77 s (frame 893).

**Pronunciation** (lexicon.json; still DRAFT: close its open items 1-3 before the narration render)
- Hawaiʻi's (the only Hawaiian word spoken; in the take twice, once on air per play): TTS text plain "Hawaii's", no U+02BB unless a test render shows the voice handles it. Target /həˈwaɪ.ʔi/ + 's: three syllables, light glottal catch before the last "ee". If the test render gives two syllables, use the lexicon alt "hah-WHY-ee's" (keep w, not v). Never accept the two-syllable "huh-WHY-eez". caption_map turns "Hawaii's" and "hah-WHY-ee's" into "Hawaiʻi's".
- On screen, in the description or in this sheet only (never spoken here): Maui "Maui", alt "MAO-ee" (never "MOW"); Kauaʻi "kah-WAH-ee", alt "kow-WAH-ee" (never "KOW-eye"); Nihoa "nee-HOH-ah"; Kīlauea "kee-lao-WAY-ah", alt "kee-lah-oo-AY-ah" (avoid "KILL-uh-WAY-uh"); Mauna Kea "MAO-nah KAY-ah"; Mauna Loa "MAO-nah LOH-ah" ("Loa" two syllables); La Pérouse (French) "lah peh-ROOZ"; Lalo "LAH-loh"; Papahānaumokuākea "pah-pah-HAH-now-moh-koo-ah-KEH-ah" (the monument's own guide: "Pa-pa-hah-now-mo-koo-ah-keh-ah"); Pūhāhonu (Gardner Pinnacles; pin only, rule-derived) "poo-hah-HOH-noo".
- Not in lexicon.json; add before any use beyond this sheet (rule-derived; check on wehewehe.org): Waimea "wai-MAY-ah"; Nā Pali "nah PAH-lee".

## 2. Second-by-second table

**Global settings**
- One sun: azimuth 250°, elevation 25°. VE 1.0 in every terrain shot.
- Camera heading about 300° for the whole Short, so northwest is always UP and the trip climbs the frame. No heading flips, no cut-away.
- Text drawn after the grade, in Anton and Barlow Condensed 800, latin and latin-ext subsets both loaded.
- All text inside x 80-849 and at y ≥ 206. Only captions go below y 1536.
- Colours: white #F4F6FA with dark stroke #0B1D28 at 0.13 x cap; yellow #FFD23F only for the trail line and the number; cyan #00E5FF for the active caption word.
- No boxes, arrows, sea-level line or tan basin.
- Captions: house spec; 1-2 words per card; none while the hook headline or the number block shows the same words, and none on the loop word "So,".
- Measured layout (real font files): /tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/short04v2/layout.py and v2_layout_sheet.jpg: every text box inside the safe area, every cap ≥ 80 px.

**0.00-2.05 · FRAME 0, already moving (the HOOK)**
- Picture:
  - Midway Atoll in true colour: Landsat 8/9 15 m pan-sharpened drape (Sentinel-2 10 m if cleaner) on GEBCO 2024.
  - Opening orbit P(t): target 28.208N 177.373W, range 24.8 km, pitch -55°, vertical FOV 50°; heading 300° + 2.0°/s x t (t from the loop cut); look offset puts the ring centre at (488, 1080).
  - The white-and-turquoise reef ring with Sand and Eastern islands spans x 73-903, y 740-1420 (77% of frame width); a 6 px white rim on the outer reef crest.
  - Deep-blue open ocean lifted to mean luma ≥ 70, sun glint upper left; a soft navy scrim (45% to 0) behind y 200-660.
  - POSTCARD: a 400 x 270 px off-white card (#F6F1E4), 12 px border, 3 px warm edge (#DED2B8), tilted -4°, centred at (300, 356), soft contact shadow on the water (offset 14/18 px); photo: a public-domain USGS HVO photo of a Kīlauea summit lava fountain (VERIFY rights and credit); a plain red stamp with no lettering; bobs ±3 px on the loop clock (period T/4).
  - Rebuilt from: the long-form's Midway ring (Ch5) shot new for vertical; the postcard from the film's "The Hawaiʻi you see on postcards? Only the top." beat and the series device.
- Text: card print "HAWAIʻI" (Anton cap 80, white with dark stroke, screen box x 134-411, y 370-468). Headline "HEADED HERE" (Anton cap 104, x 80-664, cap top 530, baseline 634). No caption.
- VO: VO1 0.05-2.19: "Hawaiʻi's Big Island is headed here." ("Big Island" about 0.48-1.12; "here" about 1.68-2.19, landing on the ring)
- Sound: ocean-swell ambience, a seamless loop of exactly T. Music bed already mid-phrase: warm low pulse, no intro, loop-cut to exactly T (14 bars at 3360/T BPM, 112.9 at T = 29.77).

**2.05-2.52 · WHIP**
- Picture: 2.05-2.30 on "here", the card hinge-pops 8° toward the camera. 2.15-2.35 the headline fades out over 6 frames. 2.25-2.52 the whip: 8 frames with sub-frame motion blur (N 6-8, U14); the world smears straight DOWN the screen, southeast and 2,416 km back down the chain, heading held at 300°. The card stays in screen space with a 6 px lag sway.
- Text: card print only.
- VO: (the VO join is hidden in this gap)
- Sound: paper flap (series motif, use 1 of 3); a snappy down-pitched whip.

**2.52-5.85 · THE BIG ISLAND AND THE HOT SPOT, in-world (3.3 s, no cut-away)**
- Picture: camera heading 300°, pitch -50°, the island about 920 px wide (85%), centred at (500, 1040), slow 2% push. Dark basalt, green windward slopes, Mauna Kea and Mauna Loa; HMRG + ETOPO terrain at VE 1.0 with a Landsat drape; 55% hero-orange fill (#FF5A36) and a 6 px white rim. 2.52-3.10 the card flies to Kīlauea's summit (about (640, 1250)) and shrinks to 40%: its print fades first (2.55-2.70), so no small text is ever drawn, then it dissolves into the glow (2.85-3.10). On "hot spot" (2.85) a soft orange under-glow swells up through the sea and the southeast flank: a diagram light about 180 px across, centred under Kīlauea. The real summit glow only if Kīlauea is erupting at render time (VERIFY, C3-12). On "volcano" (4.15) the glow pulses once and the fill brightens 10%. Rebuilt from: the long-form's Big Island massif (Ch3) re-shot vertical, and its candle-under-paper beat, told in the world.
- Text: "BIG ISLAND" (Barlow 800 cap 84, tracking 0.04, x 80-611, cap top 262; 2.75-5.95). Captions HOT SPOT 2.69-3.50 / BUILDS 3.50-3.95 / A VOLCANO. 3.95-4.95 / SEA FLOOR 5.08-5.85.
- VO: VO2a 2.69-4.83 "A hot spot builds a volcano." VO2b 5.08-7.22 "The sea floor carries it away."
- Sound: low lava hiss; a soft "whumph" on "volcano"; a low grinding slide under "sea floor".

**5.85-7.45 · THE TRIP STARTS (hop 1, 157 km to Maui)**
- Picture: on "carries" (5.85) the TRAIL starts: a 10 px yellow line with a dark under-stroke 8 px wider, a glow and a glowing head dot (radius 12), leaving the Big Island's northwest coast and running up the screen along the real ridge crest (a GEBCO 2024 crest polyline). 6.05-7.45 the camera lifts and follows the head dot (eased hop, apex 0.35 x the hop distance). The Big Island slides down out of frame, keeping its orange fill; the under-glow stays behind with it. From here the islands get only the white rim (they are off the heat). The trail fades out between y 1300 and 1420, so it never reaches the caption band.
- Text: captions CARRIES IT 5.85-6.55 / AWAY. 6.55-7.30.
- VO: VO2b continues ("away" 6.55-7.22).
- Sound: hop whoosh A.

**7.45-8.85 · MAUI**
- Picture: Maui settles at about 80% of frame width with a white rim. On "sinks" the camera eases down 4% in a soft settle. The water is rendered as it is: no rim, tint or glow on the drowned Maui Nui shelf (C12-07). Rebuilt from: the TIME MACHINE flight, Maui.
- Text: "MAUI": x 80-308, cap top 262 (7.20-9.15). Captions SLOWLY, 7.57-8.35 / IT SINKS. 8.35-9.00.
- VO: VO3 7.57-8.79 "Slowly, it sinks." ("sinks" 8.40-8.79)
- Sound: a low descending "sink" tone on "sinks".

**8.85-11.40 · Hop 2 (360 km), then KAUAʻI**
- Picture: 8.85-10.25 the hop; the trail extends up the ridge. 10.25-11.40 the low west-southwest sun throws Waimea Canyon and the Nā Pali valleys into deep shadow; white rim; slow push toward Waimea. Rebuilt from: the TIME MACHINE flight, Kauaʻi.
- Text: "KAUAʻI" (U+02BB, Barlow glyph substitution): x 80-398 (10.00-11.70). Captions RAIN 9.24-9.75 / CARVES IT 9.75-10.45 / INTO CANYONS. 10.45-11.25.
- VO: VO4 9.24-11.03 "Rain carves it into canyons." ("Rain" lands mid-hop; "canyons" 10.55-11.03 is on Kauaʻi)
- Sound: hop whoosh B; a light rain hiss passes (9.2-9.9).

**11.40-14.95 · Hop 3 (272 km), then NIHOA (held 2.3 s after landing)**
- Picture: 11.40-12.70 the hop. 12.70-14.95 a sliver of cliff in deep-blue swell with white foam breaking at its base, at least 40% of frame width; white rim; slow push. On "people once farmed" (13.80-14.70) yellow terrace lines (9 px core, head dot) draw on at the real terrace sites, positions only from the published site map (VERIFY, C4-07); with no site map, no lines, only the push. No gag here (Nihoa has burials). Rebuilt from: Nihoa and its terrace overlay.
- Text: "NIHOA": x 80-366 (12.45-15.20). Captions THEN 11.73-12.03 / A SLIVER 12.03-12.40 / OF ROCK 12.40-13.45 / THAT PEOPLE 13.45-14.10 / ONCE FARMED. 14.10-15.00.
- VO: VO5 11.73-14.94 "Then a sliver of rock that people once farmed."
- Sound: hop whoosh C; a surf boom on the cliff at landing; a soft pencil scratch on the draw-on.

**14.95-17.55 · Hop 4 (450 km), then LA PÉROUSE (the gag)**
- Picture: 14.95-16.20 the hop; the turquoise crescent reef of French Frigate Shoals fills the frame width. On "last" (16.15) a paper cut-out of a real public-domain photo of La Pérouse Pinnacle pops up on its true spot: photo NOAA or USFWS (VERIFY rights); position 23.769N 166.261W (VERIFY); 38% of frame height; warm 3 px paper edge, fold-out base tab, soft contact shadow; hinge pop from 35° with overshoot. On "tooth" (16.55-17.55) the loose-tooth wobble: the standee rocks ±6° on its base, two decaying cycles over 1.0 s. Rebuilt from: La Pérouse plus the paper-people standee device (look book S11).
- Text: "LA PÉROUSE" (with É): x 80-651 (15.95-17.95). Captions THEN ONE 15.64-16.20 / LAST TOOTH. 16.20-17.30.
- VO: VO6 15.64-17.07 "Then one last tooth."
- Sound: hop whoosh A; paper flap on the pop (motif use 2 of 3); a comic wobble "boing" in the gap after "tooth" (17.10, ≤ 0.8 s, about -16 dB); a music dip of -10 dB from 15.3 to 16.5, before the punchline.

**17.55-20.20 · Hop 5 (1,215 km, 2.0 s) to MIDWAY**
- Picture: a long eased hop arriving at pose W (range 60 km, pitch -38°, heading 300°), then a slow orbit of +2°/s. The ring is about 350 px wide, centred at (488, 1000); the trail arrives at the ring from below. On "reef" (19.40-19.90) the white rim redraws. Rebuilt from: the Midway ring and the GEBCO northwest-chain data.
- Text: "MIDWAY": x 80-462 (19.30-21.40). Captions THEN JUST 17.77-18.70 / A RING 18.70-19.40 / OF REEF. 19.40-20.10.
- VO: VO7 17.77-19.91 "Then just a ring of reef."
- Sound: a longer hop whoosh D; soft surf on the reef.

**20.20-24.20 · GLASS SEA AND THE ONE NUMBER (new for the Short)**
- Picture: on "Under it" (20.20-20.90) the water turns clear: absorption x 0.05 with a 20% turquoise tint; glint and caustics kept; depth haze to deep blue below about 2,500 m. It must read as clear water, not a drained basin. Under the ring a whole volcano appears: the real GEBCO 2024 shape at VE 1.0, coloured by substrate (dark basalt flanks, grey-olive sediment aprons, cream reef only on top; no tan). 20.2-22.0 the camera eases to range 80 km and pitch -30°: the flanks fill the frame width below the ring and plunge into blue haze; the ring about 260 px wide, centred at (488, 900). On "twenty-eight" (22.12) the number block lands with a 6% overshoot. The water stays clear through "old", and the reef rim dims to 40%, so the number sits over the visible volcano, not over the reef (C5-01). Rebuilt from: the reef-cap-on-volcano beat, told with clear water instead of a drain or a cut-away.
- Text: captions UNDER IT, 20.21-21.00 / A VOLCANO 21.00-22.05; then none while the number block shows. Number block (22.12-24.20, fading 23.95-24.20): "ABOUT" Barlow cap 80, x 88-388, cap top 250; "28" Anton cap 300, yellow, x 80-425, cap top 362; "MILLION YEARS" Barlow cap 84, x 88-808, cap top 694. The MIDWAY label is already gone (21.40).
- VO: VO8 20.21-25.25 "Under it, a volcano about twenty-eight million years old, sunk out of sight." ("twenty-eight" 22.19-22.85; "old" ends 23.62)
- Sound: the swell turns muffled and glassy; a low resonant tone under the volcano; impact_deep on "twenty-eight" (-8 dB); the music lifts a touch.

**23.80-25.10 · OUT OF SIGHT**
- Picture: on "out of sight" (24.25-24.95) the sea clouds back to deep blue in 0.7 s and the volcano vanishes. The ring and its rim (back to 100%) remain, still orbiting.
- Text: captions SUNK OUT 23.82-24.30 / OF SIGHT. 24.30-25.30.
- VO: VO8 ends ("out of sight" 24.18-25.25).
- Sound: a muffled whoosh back to the open-air swell.

**25.10-26.45 · PULL-OUT to the whole chain (1.35 s)**
- Picture: a log-altitude pull-out to the CineGlobe STORY preset (clouds 0-0.35 and kept off the chain, about 5,000 km altitude, pitch -75°, heading 298°). The chain runs straight up the frame: the Big Island near (610, 1250), Midway near (430, 300). The yellow trail laid during the hops now reads as ONE line up the real Hawaiian Ridge. Rebuilt from: the chain pull-back.
- Text: caption EVERY ISLAND 25.60-26.45.
- VO: VO9 25.60-28.81 "Every island on this line takes the same trip."
- Sound: rising air.

**26.45-28.25 · THE WHOLE CHAIN (1.8 s): the line, then the ride**
- Picture: on "this line" (26.45-27.05) a glow sweep runs up the trail from the Big Island to Midway. White rings pop on the stops: Maui, Kauaʻi, Nihoa, French Frigate Shoals and Midway. A pin (r ≥ 11 px, with a pulse) marks Gardner Pinnacles (Pūhāhonu), the last basalt above the sea (C4-09). The Big Island keeps its orange fill; no pin overlaps another. 26.95-27.45 the postcard rises out of the Big Island's glow and grows to full size; its print fades in only at 100% (27.40). On "takes the same trip" (27.45-28.35) the card slides up the line toward Midway, eased, riding the head of the glow.
- Text: captions ON THIS 26.45-26.85 / LINE 26.85-27.40 / TAKES THE 27.40-28.00 / SAME TRIP. 28.00-28.95. Card print "HAWAIʻI" (cap 80) mid-ride at about x 394-671, y 834-932.
- VO: VO9 continues.
- Sound: a rising shimmer on the sweep; a soft paper slide under the ride.

**28.25-29.40 · DIVE back to the start**
- Picture: an eased log-altitude dive with a long ease-out, reaching the opening path P(t - T) by 29.40. The line and rings fade 28.30-28.80. The card glides into its frame-0 pose (centre (300, 356), -4°), settles at 29.35 with a tiny paper bounce, then bobs on the loop clock. The headline fades in 29.10-29.40 (opacity 0 to 1 with a 12 px upward settle), identical to frame 0.
- Text: card print; the headline from 29.10. No caption.
- VO: a pause, then "So," 29.26-29.62 (no caption).
- Sound: a falling-air whoosh that ends by 29.30; a paper flap on the card's landing (motif use 3 of 3). Ambience and music carry on.

**29.40-29.77 (T) · PURE ORBIT on P, in exactly frame 0's state**
- Picture: in frame the ring, its rim, the deep-blue water, the card and the headline; no label, caption, trail, rings, pins, number or glow. CUT at T to frame 0.
- Text: "HAWAIʻI" card + "HEADED HERE", as at frame 0.
- VO: the comma gap after "So,"; VO1 restarts at 0.05 after the cut.
- Sound: ambience and music sample-continuous across the cut.

**Escalation check.** The largest gap between visual events is about 2.1 s. Events (s): 0.0 moving frame; 2.05 card pop; 2.25 whip; 2.52 Big Island; 2.85 glow; 4.15 pulse; 5.85 trail; 6.05 hop; 7.45 Maui; 8.40 settle; 8.85 hop; 10.25 Kauaʻi; 11.40 hop; 12.70 Nihoa; 13.80 terraces; 14.95 hop; 16.15 pop-up; 16.55 wobble; 17.55 hop; 19.40 rim; 20.20 glass sea; 22.12 "28"; 23.95 number out; 24.25 sea clouds; 25.10 pull-out; 26.45 sweep; 26.95 card rises; 27.45 ride; 28.25 dive; 29.10 headline.

**Mix.** -14 LUFS integrated (±1.5 LU), true peak ≤ -1.0 dBTP; VO at least 12 LU over the music; ambience at -26 to -28 dB; SFX 10-12 dB under the voice. No SFX motif more than 3 times (paper flap 3; hop whoosh A 2, B 1, C 1, D 1). No sting at the end.

## 3. Hook

- VO1 at 0.05 s: "Hawaiʻi's Big Island is headed here." Six words, the place name first; "Big Island" by 1.12 s; "here" lands on the reef ring at 1.7-2.2 s. It uses the ledger's direction framing, not certainty (C5-19).
- FRAME 0 (already moving, readable with the sound off in under 1 s) shows the start state and the end state together: in the upper third the series postcard (a tilted paper card with a public-domain USGS HVO photo of a Kīlauea lava fountain, printed "HAWAIʻI"); directly under it "HEADED HERE" (Anton cap 104, white with dark stroke, no box, no accent word); below, the real Midway reef ring in true colour, orbiting at 2°/s, 77% of the frame width, with a white rim. The read: lava island, then "headed here", then a thin ring of reef in empty ocean. The question: how does a lava-fountain island turn into that?
- Risk and mitigation: the packaging lab found postcards on thumbnails read as travel. Here the card shows lava, not a beach, covers only 37% of the frame width over a real-Earth image, and leaves at 2.05 s on a whip.
- Fallback hook (also from C5-19): "This is the road Hawaiʻi's Big Island is on." The loop line then becomes "So, this is the road Hawaiʻi's Big Island is on." Integrator note: this echoes the long-form's s146 ("That's the road the Big Island is on."), so use it only if the owner asks for the softer framing.

## 4. Payoff

Three steps over the last 10 s, each answering the hook's "here"; every stage is a real island in its real position; nothing morphs.
1. **Glass sea and the one number (20.2-24.9).** On "Under it" the sea turns clear: a whole dark-basalt volcano (real GEBCO shape, VE 1.0) spreads out under the little ring of reef. "ABOUT 28 MILLION YEARS" lands on "twenty-eight" while the volcano is fully visible and the reef rim is dimmed, so the number dates the volcano, not the coral (C5-01). On "sunk out of sight" the water clouds back and the volcano disappears.
2. **The line was the trip (26.45-27.05).** The pull-out shows that the yellow trail, laid behind each hop since 5.85 s, is one line up the real Hawaiian Ridge; on "this line" a glow sweeps up it.
3. **The postcard makes the trip (27.45-29.40).** On "takes the same trip" the Big Island postcard rises out of the hot-spot glow, slides up the line and dives with the camera onto Midway, landing exactly where it was at frame 0. The Big Island and the ring are finally together on screen, and the opening "here" turns from a claim into a conclusion: "Every island on this line takes the same trip. So, Hawaiʻi's Big Island is headed here."

## 5. Loop check

**Last line into first line:** "...Every island on this line takes the same trip. So, Hawaiʻi's Big Island is headed here. A hot spot builds a volcano. The sea floor carries it away..." A premise, then its conclusion; on first play the opening still stands alone.

**Audio.** Both sides of the seam come from one Rodney take ending "...same trip. So, Hawaii's Big Island is headed here." The cut sits in the middle of the take's comma gap between "So," and "Hawaii's", with a 6 ms equal-power crossfade on room tone, so pitch, pace and room tone match. T planned at 29.77 s (frame 893); conform to the real word times. The ocean-swell ambience and the music bed are both seamless loops of exactly T (music 14 bars at 3360/T, about 112.9 BPM), no fade, no cadence. The only other VO join (the take's end spliced to its start) is hidden in the whip gap at 2.19-2.69 s, on room tone.

**Picture (same camera, same state).**
- Camera: the last frame is t = T - 1/30 on the opening path P(t - T): target 28.208N 177.373W, range 24.8 km, pitch -55°, vertical FOV 50°, same look offset; heading 299.93° against 300.00° at frame 0 (one frame of orbit).
- State: same sun; glass effect off; reef rim at 100%; the postcard at its frame-0 pose on the same loop-clock bob; "HEADED HERE" at identical pixels; no label, caption, trail, pin, number or under-glow.
- Settling: the dive reaches P by 29.40, the card settles at 29.35, the headline by 29.40: 0.37 s of pure orbit before the cut. "So," is spoken over the settled frame-0 state, with no caption.
- Animated layers: every time-driven layer runs on a loop clock τ = t mod T with periodic functions at k/T (waves, foam, glint shimmer, caustics, the card bob k = 4, any cloud drift).
- Visual rhyme: the card that leaves Midway at 2.05 s rides the chain back and lands in the same spot on "So, ...headed here".

**QC gate:** first/last-frame MAE ≤ 5/255 and SSIM ≥ 0.98 at 1080x1920; concatenate the Short with itself and run temporal_scan.py (no "cut" or "flash"; optical flow across the cut equals the flow from frame 0 to frame 1); frame 1 not duplicated at the end; no audio click or level step in a 400 ms window around the cut; a person watches 10 consecutive loops on a phone with sound on.

## 6. Facts

Each claim with its spine line (#), its ledger ID (research/ep02/script/ledger_part1-3.json), or VERIFY.
1. **VO1, loop line, headline, title** ("Hawaiʻi's Big Island is headed here" / HEADED HERE / "Where Hawaiʻi's Big Island Is Headed"): ledger C5-19 (verified with wording): "That's where the Big Island is headed", direction not certainty, because whether an island becomes an atoll depends on reef growth against sinking. Builds on spine #8, #11, #12, #13. The long-form now says "That's the road the Big Island is on" (s146).
2. **"A hot spot builds a volcano."** Spine #8; C4-01. The generic "a volcano" keeps every later "it" honest over the differently labelled islands (C3-13). The under-glow is a picture of the hot spot (C4-01 allows a glowing plume as a picture); never "a plume from the core" or "it never moved".
3. **"The sea floor carries it away."** Spine #8; C4-01 (the Pacific plate carries each volcano west-northwest). No rate spoken.
4. **"Slowly, it sinks."** (over Maui) Spine #4; C12-09b ("these islands sink as they age"). No rate spoken (if ever needed, C3-06: "nearly a tenth of an inch a year", 2.4 mm at Hilo). The Maui Nui shelf is not spotlighted (C12-07: it drowned mainly because the sea rose after the Ice Age). Oʻahu is not a stage (C12-09a: rising on the flexural bulge).
5. **"Rain carves it into canyons."** (Kauaʻi) C4-05: shield volcanism ended about 4 million years ago, after which the canyons and cliffs began to form.
6. **"Then a sliver of rock that people once farmed."** Spine #9; C4-06 ("sliver of rock" is fair; never the smallest or "barely above water"); C4-07 (dryland-agriculture terraces; no date, no head count). Terrace lines only from the published site map (VERIFY; with no map, no lines).
7. **"Then one last tooth."** Spine #10; C4-08 (USFWS: "the last remnant of the original volcano"). The label keeps it local to French Frigate Shoals; the whole-chain view pins Gardner Pinnacles (Pūhāhonu), where basalt still shows (C4-09). The wobble is an obvious paper gag.
8. **"Then just a ring of reef."** Spine #11-12; C5-02 ("reef" or "reef rock", never pure "coral"). Why the reef forms a ring is not claimed (C5-07).
9. **"Under it, a volcano about twenty-eight million years old, sunk out of sight."** / ABOUT 28 MILLION YEARS. Spine #11; C5-01 (the age belongs to the volcano; the reef cap is younger; "ABOUT" stays; never 28.7 or the outdated 17.9 Ma); C5-03 (drills hit basalt about 516 ft under Sand Island); C5-02 (never "steadily"). The glass-sea volcano is the real GEBCO 2024 shape at VE 1.0; substrate colours are interpretive.
10. **"Every island on this line takes the same trip."** Spine #8; C3-13; C4-01.
11. **Islands and trail:** every island a real shape at its real position (HMRG + ETOPO for the main islands, GEBCO 2024 for the northwest chain, Landsat drapes), VE 1.0, logged in the per-shot data manifest; the trail follows the real ridge crest (GEBCO 2024).
12. **Kīlauea's summit glow:** C3-12 (episodic summit eruption; episode 56 began 5 Nov 2026). VERIFY at render time; otherwise only the diagram under-glow.
13. **Photos and position:** the postcard photo (USGS HVO, Kīlauea lava fountain) and the La Pérouse photo (NOAA or USFWS) must be public domain (VERIFY rights and credit); VERIFY La Pérouse at 23.769N 166.261W against the USFWS or NOAA chart.
14. **Spellings:** HAWAIʻI, KAUAʻI, LA PÉROUSE, Lalo, Papahānaumokuākea and Pūhāhonu per C4-14 and lexicon.json.
15. **Description claims:** "riding the Pacific plate northwest" (spine #8, C4-01); "each island shows a later stage of the same trip" (C3-13); "a ring of reef on a volcano about 28 million years old" (C5-01, C5-02); Lalo (C4-08); "Nihoa can be visited only with a permit" (C4-07); the reef-against-sinking caveat (C5-19, C5-17b).
16. **Pinned comment:** Nihoa permit-only (C4-07); Midway closed to tourists: VERIFY on the USFWS Midway Atoll NWR page on publish day.

Not used: Everest, 56,000 ft, the dent, "taller than", "bigger than you think", "future", any island ages beyond Midway's. One big number shown and spoken.

## 7. Renders: new for this Short vs reused

Rendered natively at 1080x1920, 30 fps; no long-form frame is cropped and the long-form is not changed.
1. **Midway opening and closing orbit P(t):** target 28.208N 177.373W, range 24.8 km, pitch -55°, vertical FOV 50°, heading 300° + 2°/s x t, ring centre at (488, 1080); Landsat 8/9 15 m pan-sharpened drape (Sentinel-2 10 m if cleaner) on GEBCO 2024; 6 px white reef rim; deep water at mean luma ≥ 70; a periodic loop clock for waves, foam, glint, caustics.
2. **Postcard asset and animation:** card 400 x 270, #F6F1E4 with a 3 px #DED2B8 edge, plain stamp, soft contact shadow; public-domain USGS HVO lava-fountain photo; print "HAWAIʻI" in Anton cap 80; motion: loop-clock bob, hinge pop at 2.05 s, flight to Kīlauea (print fades before any shrink), rise from the glow at 26.95 s, ride up the line, settle into the frame-0 pose.
3. **Whip:** 8 frames with sub-frame motion blur (N 6-8); the world whips straight down the screen while the card stays in screen space.
4. **Big Island vertical oblique:** heading 300°, pitch -50°, island at 85% of frame width; 55% orange fill, white rim; a new "hot spot" under-glow (an emissive radial light under the southeast flank, seen through the water); the real summit glow only if Kīlauea is erupting at render time.
5. **Trail line:** new data product, a ridge-crest polyline from the Big Island to Midway traced on GEBCO 2024 (a small script that follows the crest between island centroids); drawn per hop (10 px yellow core, under-stroke 8 px wider, glow, head dot); fades out between y 1300 and 1420; glow sweep in the whole-chain view.
6. **One continuous eased flight spline:** Big Island to Maui (157 km), Kauaʻi (360 km), Nihoa (272 km), French Frigate Shoals (450 km), Midway (1,215 km); hops of 1.4 / 1.4 / 1.3 / 1.25 / 2.0 s, cubic ease-in-out, apex about 0.35 x the hop distance, heading 300° throughout; Kauaʻi framed for raking light on Waimea.
7. **La Pérouse standee:** a new cut-out of a public-domain NOAA or USFWS photo (cutout.py + card.py: warm 3 px paper edge, colour spill removed, base tab); standee() on its true coordinates at 38% of frame height, hinge pop from 35°; loose-tooth wobble ±6°, two decaying cycles over 1.0 s.
8. **Midway glass sea:** pose W (range 60 km, pitch -38°, easing to 80 km and -30°); a new water-shader mode (about 1-2 h of work: absorption x 0.05, 20% turquoise tint, glint and caustics kept, depth haze); seabed by substrate (dark basalt, grey-olive sediment, cream reef top; no tan); reef-rim dimming to 40% during the number.
9. **Whole-chain pull-out and dive:** CineGlobe STORY preset at about 5,000 km altitude, heading 298°; white rings on the stops and a Gardner Pinnacles pin (r ≥ 11 px), no overlaps; log-altitude curves easing out onto P.
10. **UI:** the HEADED HERE headline; island labels in Barlow 800 cap 84, top-left; the number block (ABOUT cap 80, 28 in Anton cap 300, MILLION YEARS cap 84); the house caption track. Safe-area mock with the real font files: short04v2/layout.py and v2_layout_sheet.jpg (all text within x 80-849 and y ≥ 206; every cap ≥ 80 px).
11. **Audio:** one Rodney take (3 generations); ambience and music beds loop-cut to exactly T; new SFX: the sink tone, the glassy muffled swell, the paper slide, the wobble "boing".

**Reused as-is from the long-form build:** terrain and data bakes (HMRG + ETOPO for the main islands; GEBCO 2024 for the northwest chain; the Midway, French Frigate Shoals and Nihoa patches; the Landsat drapes); the per-island terrain of the TIME MACHINE flight; the Nihoa terrace overlay geometry (only if from the published site map); the La Pérouse location; the Midway ring patch and the reef-cap-on-volcano data; the chain pull-back framing; the Big Island massif bake; the type system; the SFX library (whip, impact_deep, paper flap, swell, hop whooshes, rain hiss, surf boom); the music library, Rodney's voice and the lexicon. No longer needed from the draft: the Ch4 plume and plate cut-away, the age-bar gauge, the gleam sprite.

## 8. Title, description, link

**Title:** Where Hawaiʻi's Big Island Is Headed (36 characters; the place name in the first 3 words; the ledger's direction framing (C5-19); no number; passes the clone-word regex; keeps the ʻokina per the 2026-11-08 spelling rule, with plain "Hawaii" in hashtag and tags). If the owner prefers the long-form's plain spelling: "Where Hawaii's Big Island Is Headed" (35). Backup: "Every Hawaiian Island Takes the Same Trip" (41). Probe 2026-11-08 (short04v2/probe.txt): "where hawaii's big island is headed", "big island will become an atoll" and "every hawaiian island same journey" return no on-premise Short; near misses "How Does a Volcanic Island Become a Coral Atoll?" (1.5K) and "Will Hawaii Get a New Island?" (1.5K); the nearest proven premise is "How Do Atolls Form?" (613K); the spent neighbours are "Hawaii Is Much Bigger Than You Think" (14M) and "How Long Is Hawaii, Really?" (7.4M), and our whole-chain view stays at 1.8 s.

**Description (paste as is):**

> Hawaiʻi's Big Island is riding the Pacific plate northwest, away from the hot spot that is building it. Follow it up the island chain and each island shows a later stage of the same trip: Maui, Kauaʻi, Nihoa, La Pérouse Pinnacle at French Frigate Shoals (Lalo in Hawaiian), and finally Midway, a ring of reef on a volcano about 28 million years old.
>
> That is the direction the Big Island is headed. Whether a sinking island keeps a reef on top depends on how fast the reef grows, so this shows the road, not a promise of how it ends.
>
> Want to see what lies under the Big Island itself? The full film looks down: Why Can't You See Most of Hawaii? (Look Down)
>
> Every island here is real and in its real place, and heights are not exaggerated. The sea is shown clear for a moment so you can see the volcano under Midway's reef. The glow under the Big Island marks the hot spot; it is a picture, not lava. The postcard and the paper cut-out of La Pérouse Pinnacle are not to scale. Nihoa, French Frigate Shoals and Midway are part of Papahānaumokuākea Marine National Monument; Nihoa can be visited only with a permit.
>
> Sources:
> - USGS Hawaiian Volcano Observatory, Evolution of Hawaiian Volcanoes
> - USGS Volcano Watch, Island of Hawaiʻi sits at end of a long, old chain of 125 volcanoes
> - USGS Volcano Watch, A geologic tour of the Hawaiian Islands: Kauaʻi and Niʻihau
> - Moore, Ingram, Ludwig and Clague (1996), Coral ages and island subsidence, Hilo drill hole (USGS)
> - Papahānaumokuākea Marine National Monument: archaeology of Nihoa; history of La Pérouse Pinnacle
> - U.S. Fish and Wildlife Service, Hawaiian Islands National Wildlife Refuge
> - U.S. Fish and Wildlife Service, Midway Atoll National Wildlife Refuge
> - Dalrymple, Clague and Lanphere (1977), Revised age for Midway volcano, Hawaiian volcanic chain (USGS)
> - Ladd, Tracey and Gross (1970), drilling on Midway Atoll, USGS Professional Paper 680-A
>
> Data and images:
> - GEBCO Compilation Group, GEBCO 2024 Grid
> - NOAA ETOPO 2022
> - University of Hawaiʻi SOEST, Hawaii Mapping Research Group multibeam synthesis
> - Landsat imagery courtesy of the U.S. Geological Survey [or, if Sentinel-2 is used: Contains modified Copernicus Sentinel data, year]
> - Postcard photo: [USGS Hawaiian Volcano Observatory, public domain; exact credit from the file record]
> - Photo of La Pérouse Pinnacle: [NOAA or USFWS, public domain; exact credit from the file record]
>
> #Hawaii #Geology #Volcano

**Link to the long-form:** in YouTube Studio the owner sets the Short's Related video to "Why Can't You See Most of Hawaii? (Look Down)"; the description names the film. This is the "Midway reef cap on a sunken volcano" funnel slot (niche report 5.2.7). The clear-water look under Midway previews the film's "look down" premise without spending the 56,000 ft or the dent. Nothing is uploaded, scheduled or posted without his OK.

**Pinned comment:** "Kauaʻi's canyons, Nihoa's cliffs or Midway's reef: two of the three are almost impossible to visit. Which would you pick anyway?" (Nihoa permit-only, C4-07; VERIFY Midway's visitor status on the USFWS refuge page on publish day.)

## 9. Panel must-fixes and how this version answers them

Panel score on the draft: 66. All 8 must-fixes are in: the certainty framing replaced everywhere (C5-19: "headed", no "future", no "in 28 Million Years"); frame 0 shows the start state and HAWAIʻI (the lava postcard over the ring, landing back in the final 0.4 s); "ring of reef", never "coral"; the 28 visibly the volcano's age (clear water through "old", reef rim dimmed); the hot-spot block cut to 3.3 s, in-world, northwest up throughout; pronunciation aligned with the lexicon and LA PÉROUSE with the É; a burned-in caption track; description and pinned comment fixed and the Maui Nui shelf not spotlighted.
