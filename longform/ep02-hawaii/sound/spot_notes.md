# Ep02 spotting session: music, ambience, SFX

"Why Can't You See Most of Hawaii? (Look Down)", Rodney narration, 734.85 s of voice, film about 12:27 with the end screen.
Sound designer and music supervisor pass, 2026-11-08; the sounds and cues were generated and measured the same day (section 14). Nothing has been mixed or published. The owner listens before anything is final; no agent claims an ear verdict.

**Röviden (a tulajdonosnak):** 14 zenei blokk íve a csodálattól a feszültségen át a csúcspontig. Minden helyszínnek saját alapzaja van (szél, szörf, mélytengeri nyomás, albatroszkolónia), és a vízleeresztés minden alkalommal ugyanazt a hármas hangot kapja. A nagy leleplezések előtt a zene 0,75–1,8 másodpercre kiesik, utána jön az ütés. A halálesetek, a sírok és a midwayi hadisírok körül csend van: se poén, se zenei ütés. A poénok hangjai a képen látható tárgyakból jönnek (bőröndkerék, papír, fóka), olcsó effekt nélkül. Hat döntés vár rád, ezek a 12. pontban vannak.

## 0. Files and how to rebuild

- `spot_music.json`: 14 cues (t_in, t_out, prompt, composition-plan sections with energy and job tags, sync points, transitions), 17 dips, 1 lift, 5 stop-downs, and a `music_py_cues` block that `engine/tools/music.py` can run as is.
- `spot_sfx.json`: 196 events (47 ambience beds, 147 one-shots and swells, 2 optional), each with id, t, marker, segment, kind, job, asset, file or gen_prompt, length_s, gain_db and trim fields. There is also an asset catalogue (10 ep01 library files, 66 to generate, one of them optional) and the restraint windows.
- `spot_check.txt`: the validation report.
- `build_spot.py`: builds all three from `audio/ep02_vo/timing.json` plus the audible word ends measured from `vo.wav`. **The voice was re-rendered at 22:04:57 while this pass ran (s126 onward moved by up to +0.40 s)**, so no time here is hand-typed. After any voice change, run `python3 -I build_spot.py ../ep02_vo/timing.json .` from this folder. Built on timing.json md5 `183ad505479d8026f58c4b5f7a6d38b1`.
- Rules applied: the owner rules and PLAYBOOK_craft sections 10-11 first. The parallel benchmark `sound_principles.md` (R1-R23) was folded in wherever it does not conflict with the playbook: silent label entrances, a phone-audible layer on hits, variants, hush windows, cues that end on their own, and pre-lapped section changes.

## 1. The music arc

The arc runs from wonder, to dread, to playful curiosity, then discovery and awe, a journey, an elegy, a bright arrival, tension, solemn restraint, descent, the payoff, and the theme coming home. Every chapter card has a new cue. No cue runs longer than 85 s, and every cue longer than 45 s changes section at a story turn. Section changes at turn lines start 0.6 s before the line, never on the word. Only the reveal blooms (the stand-up, the payoff) land on their word.

| Cue | Window | What it must do | In | Out |
|---|---|---|---|---|
| M01 cold open | 0:00.0-0:52.4 | wonder at the drain, an airy curious pulse (96 bpm, D Lydian), then the pull of the deep | on frame 1, no sting | thins out on "Not always" |
| M02 Halapē 1975 | 0:50.4-1:36.4 | dread, then grief: a low drone, a soft pulse with no hits, one held low note, then an ominous lean | crossfade as the light falls | swell into the Ch2 card |
| M03 Pali | 1:33.8-1:56.0 | playful wind (pizzicato, nylon-guitar harmonics, no ukulele), then the awe of the edge | on the card | 3 s crossfade |
| M04 Nuʻuanu | 1:53.0-3:04.2 | tension in the drain, a 1.8 s held breath, the landslide reveal, dry humour, creeping unease, the question | crossfade | own ending: rings out on the Ch3 card |
| M05 stands up | 3:01.6-4:26.6 | the drain build, then the awe bloom on "up", the trench clue, the Everest stride, then the real giant | on the card | own ending: a suspended note |
| M06 hot spot | 4:24.6-5:18.1 | the twist (a pulse already moving), the candle, sinking, warm pride, a dry wink | 1.4 s on the twist line | own ending on the Ch4 card |
| M07 time machine | 5:15.5-6:14.5 | the journey (100 bpm), a lift for each island, thinning by Nihoa | on the card | resolves on "out here" |
| M08 elegy to Lalo | 6:12.0-7:18.4 | solemn restraint for Nihoa's people and graves, then tenderness, the storm, the seals, calm | as "people lived here" begins | own ending on the Ch5 card |
| M09 Midway | 7:15.8-8:00.2 | bright and a little mischievous, the albatross, wonder at the 28-million-year volcano, the drills | on the card | HARD OUT on the drill hit |
| M10 AF codebreak | 8:00.6-8:44.4 | taut, clandestine tension (112 bpm, Morse-like staccato), a dry wink for the bait, a firm cadence on "AF was Midway" | HARD IN on "In June" | clean stop: the comedy ends here |
| M11 losses to the Darwin Point | 8:43.9-10:01.6 | a respectful pad, still deep drones, one held note through the war graves, then a gentle lift only after the 10 s hush | in the 1.2 s pause | own ending on the Ch6 card |
| M12 newborn and descent | 9:59.0-11:17.9 | reverent mystery, a COMING SOON lift, then the long descent build with the look-down motif | on the card | ABRUPT STOP 1.2 s before "tall" |
| M13 payoff | 11:19.1-11:41.4 | a massive downbeat on "tall", awe, then quiet reflection | HARD IN on the hit | rings out |
| M14 theme reprise | 11:39.1-12:26.9 | the opening theme returns with the ocean (music only, +3 dB), settles under the last lines, curious on the hand-off, ends on one piano note | from "Now put the ocean back" | back-timed to the last frame |

- **Thinking vs feeling.** Explanation sits on pulse and texture ("thinking"). "Feeling" sections sit only where the story earned them, mostly in pauses and hero shots: the stand-up, the debris reveal, Mauna Loa, Nihoa's graves, the payoff and the refill. Each section in the json carries `energy` (low, mid or high) and `job`.
- **Look-down motif.** A simple three-note descending felt-piano figure is asked for in M01 (the first "look down"), M05 ("keeps going. And going."), M12 (the payoff dive) and M14 (the final "look down"). Separate generations will not reproduce it exactly, but each prompt describes it the same way, so it reads as one family. If the M14 reprise does not sound like M01, lay M01's own first 10-15 s under the refill (the fallback in the json).
- **Generation.** `music_py_cues` runs on today's `music.py` with prompts only. The `sections` (duration_ms, positive and negative styles) are written for ElevenLabs composition plans, so drops and blooms land on their marks. music.py sends plans since 2026-11-08 (a cue with "plan": true; see section 14 for how they measured). Where a cue misses, place sync points by editing: set each cue's `offset` so the listed downbeat lands on its `sync_points` time (M05's bloom on "up" is the critical one), and cut at bar lines.

## 2. Signature devices (the sound of the brand)

- **Drain signature, three sounds:** `drain_start` (a giant plughole suck), `drain_flow` (a receding rush bed) and `drain_gurgle_tail`. Every live drain uses it, like the gauge. The second drain, 12 s after the first, uses `rumble_rise` instead, so no identical riser repeats within 60 s.
- **Clue ping, three times:** one ping on "It's a clue" (3:41), the callback on "Remember that deep trench at its feet?" (10:42), and the payoff ping that resolves into a low tone on "the edge of that dent" (11:06). The loop the script plants is also paid in sound.
- **The ping with no return** on "we won't hit bottom" (0:33): one sonar ping into the blue with no echo coming back. That is the film's forward promise, in sound.
- **Hero hit = two layers.** `impact_deep`, which is pure sub energy, lands on the visual landing; the playbook allows it under a word. A `hit_body` layer (300-600 Hz), placed at the measured audible end of the word, makes the hit audible on phone speakers, where impact_deep is nearly silent. The hit_body sound is 0.05 s after the measured audible end of the word.
- **AGE gauge slide** (Ch4): a fine ratchet that stops when the marker lands. It is used on every age move except the silent Lalo flight, which falls in the Nihoa hush.
- **Paper world:** every cut-out has a soft paper sound (a tap, a flutter, a card creak). Text, labels, names and pins make no sound.

## 3. Scene by scene

### Ch1 Only the Top (0:00-1:33.8)
- **Frame 0:** soft high wind over dry rock, audible on frame 0. M01 starts on frame 1 with no sting. A low earth swell under "drained" (0:02.1) gives the dry mountain its weight.
- **0:08.2 postcard:** the drop starts on "postcards" and its slap lands just after the word. **0:10.5:** the sea refills during the flight (a water rush plus a soft whoosh) and the surf bed comes in.
- **Hero #1, −400 FT:** the drain signature starts at "Drop". **The music stops for 1.15 s while the sea drops (0:15.8-0:16.9)**, so the drain sound carries alone into the hit and the arrival chord. A ticking counter lands on the number, and the body layer sits in the gap at 0:17.3.
- **0:20.6** Ice Age pass: distant seabirds over the dry channel. **Gag "No ferry needed":** a 1.2 s music dip before the line, one paper hop, and suitcase wheels on gravel in the 0.7 s gap.
- **0:27** "Keep draining. And look down.": a rumble rise and the drain bed, and a soft whoosh on the look-down camera move. The deep-pressure bed takes over as the camera rides down the slope, with the ping that never returns. The sea rises back (0:43.8) and an 8-frame whip-pan reaches the Big Island's south coast.
- **1975 Halapē (0:50.8-1:29):** M01 thins on "Not always" and M02's drone takes over. The pre-dawn bed is crickets and katydids with lapping water, and **no coquí frogs**: they reached Hawaiʻi long after 1975, and a wrong sound would be a false claim. The foreshock is a quiet low rumble under "woke them up". **On the main shock (1:04.2) the insects cut out in 0.12 s**: nature goes silent. The sea keeps churning underneath. A low groan comes on "lurched", a crack and settling thud on "dropped", then water flooding in, and a human-scale surge peaking on "rushed", faded before the hush. The music never hits; the sound effects carry the shock.
- **Hush 1:16.2-1:28.9:** "Two people died." and the archival still sit on lapping water and one held low note (music −3 dB). Nothing else plays.
- **1:29.4** "Now picture a whole side of a volcano letting go": a low ominous groan, not a sting, and the whip lands on Oʻahu under the Ch2 card.

### Ch2 Oʻahu's Missing Side (1:33.8-3:01.6)
- The Pali trade-wind bed is the subject of the gags. It is low-passed under speech, and the gusts go in the gaps. On "lean" the paper card creaks. On "hat" a gust rises under the word and peaks just after it. The **gag** is the paper hat fluttering away in the 0.7 s gap, followed by the camera's dive down the cliff.
- On "tore apart" a felt low groan plays, more felt than heard. Then a 3 s crossfade into M04 as the camera moves out to sea.
- **Nuʻuanu drain:** the drain signature plays, block tops break the falling water (3 variants: first, then more), then the rubble field. **Stop-down 2:10.95-2:12.75:** the last water gurgles away and the music cuts out for the 2 s pause, leaving only the drained-seabed bed. The music returns as the line starts, and `impact_deep` plus the swell land on "landslides" (2:15.1).
- **Manhattan:** a drag whoosh, then a low drape thud a frame before the name. **Gag:** a dip before "With room to spare" and a tiny tok as the outline settles in the gap.
- **Hero #2, 100 MILES:** the line-draw sweep ends exactly on the landing, with a lighter hit (impact_short) and a body layer in the 0.8 s gap. Then one pop cascade for the slide footprints.
- **The callback to the coast that dropped in the dark** gets a quiet creeping pulse. The dry button "Creeping" gets a 1 s dip and no comic sound, because it refers back to the 1975 coast. "Let's drain all the way down" starts the drain under the Ch3 card.

### Ch3 The Island Stands Up (3:01.6-5:15.5)
- **The stand-up:** the drain flow and a deep riser end exactly on the hit. A **0.75 s inhale (music −24 dB)** sits under "Big Island stands". `impact_deep` lands on "up", the body sits in the 2.5 s pause, and M05 blooms. The drained-seabed bed carries the whole drained massif.
- "Keeps going. And going.": a soft tilt whoosh plus a deep pressure swell. On "It's a clue" comes the first clue ping.
- **Everest:** a rumble rise as it lifts, and a low whoosh as it sinks to the shared base. **Hero #3, 33,000+ FT:** the counter ticks land on the number, then the hit and the body in the gap.
- **JUICE CHECK: TRUE:** the stamp falls at the end of "one." (3:59.2), in the 0.6 s pause, never over the last word. The render should land the graphic there too.
- **Summit gag:** real summit wind on Everest (the ep01 library ice wind) and the paper climber's tap. Whip to the road, a light 4WD crunch, whip back. **The flag droops in the 0.8 s gap**, which replaces the script draft's "deflate_comic" (too cheap).
- **Mauna Loa:** a low earth swell for the real giant's weight, and 3 s of surf for the cut to today's island.
- **Twist (4:25.9):** M05 rings out and M06's pulse is already running. A tectonic groan plays and the magma bed comes in for the only hot-spot cut-away. Candle flicker, then paper sliding with three tiny scorches. On the hard cut "it sinks", a descending tone and a hard-in seabed bed.
- **"A very big baby":** a dip, a low crash-zoom whoosh, and a dry low thoom of weight in the gap instead of the draft's boing.

### Ch4 Watch It Grow Old (5:15.5-7:15.8)
- The AGE gauge appears with its slide. The lava-coast surf runs under the archival arch wipe (no paper sound on the photos), and a wave washes through where the arch stood.
- **Flights:** high air plus a single whoosh per flight, and the age slide stops on each island. On Oʻahu the hat callback is visual only (VO runs on): a gust, no comic sound. Rain squall on Kauaʻi.
- **Nihoa:** wind, surf and seabirds. **Hero #4, 7 MILLION YEARS:** only the last 0.55 s of the age slide plays, after the name Nihoa, plus a light hit. The dry irony gets no comic sound, because it comes 3 s before the people beat.
- **Nihoa people and graves (6:12.9-6:32.9):** M08's solo piano and strings, music −3 then −6 dB, the **same wind with the birds removed**, and no sound effects at all. The flight to Lalo and its age slide are silent because they fall inside the hush. The birds come back on "nobody lives here".
- **Lalo:** the lagoon bed and a paper seal tap. On "hurricane" the storm passes (M08 changes section here, so the next gag has a cue change between it and the graves). The sand wash plays on "away". **Seal gag in the 2.4 s pause:** a soft surfacing plop, then one puzzled monk-seal snort. These are real sounds, not a cartoon bloop, and the seal's bark is not a sea-lion bark. Warm lift: the seal flops onto the regrown sand and gives a contented grunt.

### Ch5 Fought Over a Volcano (7:15.8-9:59.0)
- **Midway:** the reef bed, and the drag whoosh for the New York-Miami line (the landing makes no sound). The dive into the albatross colony bed (a real Laysan colony recording is preferred), a soft glide whoosh, and **the tumble in the 0.8 s gap** after "Landing is another story".
- **Hero #5, 28 MILLION YEARS:** the atoll drain starts in the 2 s pause, the slice sound opens the cut-away (the same device sound as the payoff slice), then the hit and the body. The volcano sinks in steps (two soft settles), the drills grind, and **the drill strike is the hard out of M09**.
- **June 1942 (8:00.6):** M10 hits hard on "In June" over a quiet atoll dawn. The 1942 aircraft drone is designed but **OFF**: off-screen period texture would break the one-sound-per-visible-event rule, and it would be the first war sound in the film.
- **The AF ruse** (story humour, before any death): a faint radio-room static bed and Morse streams for the intercepts. In-world sounds go in the gaps: a drip on the water icon, the telegram's return flick, the radio pulse for the plain-language message, the tank's wobble-and-drip, and a radio squelch on "Japan bit" (in place of a reel twang). A dip runs under "AF is short of water". **No thunk on AF = MIDWAY**: M10's cadence lands it, and the comedy ends in the 1.2 s pause.
- **Midway hush (8:44.3-9:25.3):** from 1 s before "Japan lost every carrier" to 10 s after "war graves". Only open-ocean air, a quiet ambience-level flow for the drain, the deep-pressure bed, and M11's held pad. There is no sound on the carriers, Yorktown or the wrecks, no line sound, no sonar, and **hero #6 (3 MILES DOWN) lands silently**. The Kure lift waits until the hush ends.
- **Kure to Kamchatka:** reef and seabirds, a line sweep for the Darwin Point, a quiet flow as the drowned seamounts appear, the globe whoosh, a tectonic groan as the plate takes the last seamount down, and the whip back under the Ch6 card.

### Ch6 We Haven't Hit Bottom (9:59.0-end)
- The flight down is followed by the drained-seabed bed, and a ping finds the young volcano. **There is no sound on Kamaʻehuakanaloa or its meaning.** The felt quake is a quiet rumble with no damage.
- **COMING SOON:** the paper sign pops up in the 0.4 s gap after "the next Hawaiian island". A dip runs before "At least.", then a soft hinge creak as it droops.
- **The last drain:** the drain signature plays and the last water gurgles away. The clue-ping callback plays at "Remember that deep trench at its feet?". The slice opens the cut-away, the earth-deep bed comes in, and a groan plays as the sea floor bends. The bowling ball is a low thump (under 300 Hz) on "mattress". On "edge" the resolving ping plays.
- **The payoff run:** the second look-down move (a long descending whoosh), then a soft landing on the dented base. A deep riser builds under the payoff line, and **music and riser stop together 1.2 s before "tall"**. The voice says "fifty-six thousand feet" over only the earth tone and a low, high-shelved counter, so the number stays clear. On "tall", `impact_deep` + `payoff_boom` (used once in the film) + M13's downbeat hit together, and the body layer lands in the 1.8 s pause. The second swell comes as Everest rises. "That's how much of this mountain you never get to see" and its 2.3 s pause carry no sound effects, only the soft chord and a faint earth tone.
- **The refill, music only (11:39.8-11:55.1):** a deep inrush, then a 15 s rising roar that settles into surf, while the theme reprise swells (+3 dB). The surf and the frame-0 wind return for the frame-1 composition. The postcard slap lands just after "giant". A paper flick plays as the postcard flips, after "hole?" and before "Louisiana". The end screen gets no new sounds, only the surf and M14's last piano note on the last frame.

## 4. Stop-downs and hard cuts (punctuation, not decoration)

| Time | What | Floor kept above the −45 dB silence gate |
|---|---|---|
| 0:15.8-0:16.9 | the sea drops, the music drops, then −400 FT | drain sound + surf |
| 2:10.95-2:12.75 | the held breath before the landslide | drained-seabed bed + the gurgle tail |
| 3:10.6-3:11.3 | the inhale before the island stands up | drain flow + the deep riser |
| 8:00.2-8:00.6 | hard cut from the drill hit into 1942 | the impact tail + the cut-away bed |
| 11:17.9-11:19.05 | the payoff dropout | the voice + the counter + the earth tone |

There are five stop-downs in 12.5 min, about 60 s or more apart. Each one removes layers and drops register rather than only lowering level, so it still reads with YouTube's Stable volume on. mix.py's dips have fixed 0.25 s ramps, but stop-downs want 20-50 ms ramps (see section 9).

## 5. Restraint and silence

| Window | Rule |
|---|---|
| 1975 scene 0:50.8-1:29.2, hush 1:16.2-1:28.9 | No gags, stings, risers, UI sounds or playful cue. Real quake and wave sound at human scale. The hush has only lapping water and one low note. |
| Nihoa 6:12.9-6:32.9 | No sound effects at all, wind with the birds removed, music −3 then −6 dB. The next gag (the seal) comes after a music section change. |
| Midway hush 8:44.3-9:25.3 | Ambience and one held pad only. Nothing on the losses, the wrecks or the war graves. Hero #6 lands silently. |
| Kamaʻehuakanaloa 10:09.5-10:16.5 | No sound and no musical accent on the name. |
| 11:32.3-11:38.0 | "never get to see" plus its pause: no sound effects. |
| 11:39.8-11:55.1 | The refill: music and water only. |

The validator confirms that the three hush windows (1975, Nihoa, Midway) contain no one-shot at all and that their scenes contain no comic sound, hit or stamp. The other windows were checked against the event list.

## 6. Gags: in-world, in the gap, never cheap

Each gag has one sound. It is what the thing on screen would make, it plays after the line's last word, it is 0.8 s or shorter, and it sits at −16 to −18 dB. The validator checks that no gag sound overlaps a word. Replacements for the script draft: deflate_comic becomes the flag droop, boing_small becomes a low thoom of weight, bloop_comic becomes a seal plop and snort, line_tug becomes a radio squelch, and pop_comic becomes a paper sign snap. The thunk on AF = MIDWAY is removed. There is no record scratch, crickets, cartoon fall or bell ding anywhere.

The AF bait sounds (the drip, the telegram flick, the tank wobble and the squelch) come 10-30 s before the first loss line. That is story humour the script reviews kept, but it is close to the Midway rule, so all four carry `strict_off: true`. The owner can hear both versions.

## 7. Truth in sound

- No coquí frogs in 1975 (they arrived decades later). No birds in the pre-dawn bed. The Nihoa graves bed has its birds removed.
- Hawaiian monk seals grunt and snort; they do not bark like sea lions. The Laysan albatross colony should be a real recording of the species. Both assets name a public-domain field recording (NOAA, USFWS or NPS) as the preferred source; log the licence the day it is chosen.
- The war has no gunfire, explosions or diving planes anywhere. The distant formation drone is off unless a visible formation is drawn.
- The drain is a thought experiment, so its sound stays stylised (a giant plughole) and never claims a real event.

## 8. Levels and calibration

- **The voice must be prepared first.** ep02's vo.wav measures −26.4 LUFS integrated with a −3.2 dBFS peak, a 23 dB peak-to-loudness ratio. mix.py normalises the whole mix to −14 LUFS, so that peak would force about 10 dB of limiting on the voice. ep01's prepared voice (vo_proc_v3) was −17.4 LUFS with a −0.6 peak and LRA 2.3. Make `vo_proc.wav` the same way: a high-pass about 70 Hz, gentle compression, de-essing and peak control, so the voice sits about −17 LUFS with a ratio of about 13-14 dB. Every gain below assumes that.
- **gain_db convention:** mix.json gain on files normalised to about −20 LUFS, like the ep01 `sfx/norm` library. Normalise every new file the same way before mixing.
- **Levels:** music beds −9 (solemn −11/−12, payoff −7, finale −8), ducked −11 under the voice. ep01 measured 18.9 LU under speech this way, inside the 15-22 LU target. One-shots −12 to −20, comic −16 to −18, impact_deep −8 to −10 on reveal words (sub only), hit_body −13 to −15 in gaps. Beds −6 to −9 (about −26 to −29 LUFS) and −10 to −12 for second layers. Repeated library files get round-robin pitch (±1 semitone; impacts ±0.5) and level (±2 dB) variation, and recurring generated sounds get 2-4 takes. The validator finds no identical sound more than twice in 60 s.
- **Targets:** −14 LUFS integrated (±0.5 to aim, ±1.5 gate), true peak −1.5 dBTP or lower through mix.py's limiter, no clipping, and silencedetect at −45 dB / 0.3 s clean on the final file. audio_scan's 1.2 s dead-air test is looser than the playbook gate, so run the gate directly.
- **Density:** 147 one-shots, 6-17 per full minute and at most 7 in any 10 s. The busiest minutes are the cold open, the stand-up and the Midway minute, where the picture changes fastest. Every sound names its visual event or gag.

## 9. What the mix needs that the tools lack (not changed here)

- **mix.py:** sfx entries need `t_out`/`loop`/`fade_in`/`fade_out` (beds), `dur`/`src_in` (trims), `pitch_st`, `variant` and `eq`; or prebake each event to a file with ffmpeg first. It also needs per-dip ramp length (stop-downs want 20-50 ms), a duck hold of about 0.8-1.0 s against pumping (ep01 pumped 18.6 times a minute), and `enabled`/`strict_off` filtering. Positive dips already work as lifts, because dips multiply.
- **music.py:** composition-plan requests (sections with duration_ms) and a per-cue offset step after generation.
- **SFX generator (done 2026-11-08: engine/tools/sfx_gen.py and sfx_check.py, section 14):** ep01's library was made outside the repo (list.tsv). A small `sfx.py` like music.py is needed: key from ELEVENLABS_API_KEY, cache by content hash, `duration_seconds`, `prompt_influence`, a loop flag for beds (check the API reference), N takes per asset, then normalise to −20 LUFS. That is 101 calls, about 610 s of audio, plus 14 music cues of about 810 s (each window + 3 s).
- **Licence:** confirm with the owner that the ElevenLabs plan is a paid commercial one before any of this goes into a monetised upload (PLAYBOOK section 1).

## 10. Requests to the render team (sync)

- Land the JUICE CHECK stamp at the end of "one." (3:59.2), not on its start.
- Land the Halapē surge on "rushed", not on "in".
- Add a 6-frame lock-in punch on −400 FT, 33,000+ FT, 28 MILLION YEARS and ABOUT 56,000 FT at their hit_body times, so phone viewers see what they hear.
- Twitch the paper fishing line at the end of "bit".
- Land the postcard drops just after "postcards" and "giant".
- The telegram's flight out is silent; only its return gets a flick.
- When the chapter builds exist, re-sync every event to the render's event log (frame-exact). Today's times come from the voice markers.

## 11. Owner listen list (about 10 stops)

0:13-0:28 (stop-down, −400 FT, the ferry gag) · 0:50-1:33 (Halapē and the hush) · 1:42-1:47 (the hat) · 2:09-2:17 (held breath and the landslide) · 3:04-3:15 (stand-up) · 3:50-4:08 (33,000, the stamp, the summit road) · 6:12-6:33 (Nihoa) · 6:50-7:06 (storm and seal) · 8:07-9:26 (the AF ruse, normal and strict, into the war graves) · 11:07-11:21 (payoff) · 11:39-12:27 (refill, finale, last frame).

## 12. Owner decisions

1. AF bait: in-world gag sounds on (default) or the strict variant (all four off).
2. The 1942 distant aircraft: off (recommended) or on, with a drawn formation.
3. Public-domain field recordings for the albatross colony, seabirds and monk seal (recommended) or generated ones.
4. ElevenLabs paid commercial plan confirmed for music and sound effects.
5. The optional fourth tourist peek at 12:06 keeps its tiny paper tap only if the shot is used.
6. Section 10's render changes.

## 13. Proposed playbook lines (for the parent to log; not written here)

- DO: build the sound spot from the voice markers with a script, and use measured audible word ends (timing.json word ends carry about 0.3-0.5 s of trimmed tail). The voice changed mid-pass, and every time re-derived. [reviewed]
- DO: two-layer hero hits: sub on the landing (allowed under the word), a 300-600 Hz body in the next voice gap for phone speakers. [hypothesis]
- DO: hush windows around deaths and graves, from 1 s before the line to 10 s after it, with ambience and one pad only, checked by script. [owner + benchmark]
- DONT: generic night "crickets" or coquí in a pre-1990 Hawaiʻi scene; a wrong species or an anachronism in sound is a false claim. [reviewed]
- DONT: pass raw ElevenLabs voice (PLR 23 dB) into mix.py; prepare it to about −17 LUFS with a ratio of about 13-14 dB first. [measured]

## 14. Sound producer pass, 2026-11-08 (generation and objective checks)

**Röviden:** minden hang és zene elkészült és le van mérve. 67 effekt (101 fájl, 129 változatból válogatva) és 14 zenei blokk, énekhang sehol. A telefonon is hallható ütésréteg az első próbára nem sikerült (csak mélybasszus lett), új leírással javítva. A zenék a tervezett belépési pontokat jórészt nem találják el (26-ból 1), ezt a keverésnél kell igazítani. Halló ítéletet nem mondok, a meghallgatási lista a 11. pontban van.

### Spotting revisions (build_spot.py, re-run; old files in prev/)
- R5: added a hit_body (phone layer) after "hit the volcano." (x144, 479.67 s), in the 0.8 s gap before the 1942 hard cut, ending with M09. Hero #4 (Seven million years) and the landslide reveal have no voice gap, so they keep sub-only hits (the age slide carries #4 on a phone).
- R5: added quake_debris (x025, -15 dB, 3 s) under the 1975 main shock: quake_main came out pure sub (centroid 20-31 Hz, above-250 Hz share -22 to -32 dB in both takes), silent on a phone. Realistic event sound, so the 1975 scene rule still passes.
- R22: tank_wobble (x153) and radio_squelch (x154), 12 and 10 s before "Japan lost every carrier", are now OFF by default (owner decision 1 can switch them on). The drip and the telegram flutter (33 and 20 s before) stay on.
- Prompts revised after the first takes failed their measures: hit_body (8 of 8 takes sub-heavy, centroid 42-291 Hz; the new prompt plus a 120 Hz high-pass gives centroid 297-342 Hz and 37-49% of the energy above 250 Hz), amb_high_air (was a 74 Hz rumble; now 597 Hz air), postcard_drop (1.2 s takes put the slap at the very start or end; now 1.6 s), albatross_tumble (peaked in its last 10 ms; now 1.0 s). ball_mattress is low-passed at 300 Hz because it sits under the word mattress.
- Event ids after x024 moved by up to +2 (two events added).

### Files
- Prepared SFX (48 kHz, 24-bit, -20 LUFS or the -2 dBFS peak cap, leading silence trimmed to a 10 ms pre-roll): `sfx/<asset>_v<n>.wav`; manifest `sfx/selected.json` (chosen take, every take's score and flags, measured sync point, level); report `sfx/report.txt`. Raw takes: `sfx/raw/` (`sfx_done.json`). Generation spec: `sfx/spec.json`; intent checks: `sfx/expect.json`.
- Music: `music/selected.json` (the pick per cue, measures, flags), checks `music/music_check.json` and `music/plan/music_check.json`; files `music/M*.mp3`, composition-plan alternates in `music/plan/`.
- Tools: `engine/tools/sfx_gen.py` (new), `engine/tools/sfx_check.py` (new), `engine/tools/music.py` (composition-plan mode added; prompt mode and its cache unchanged).

### What the mix must do with these files
- Place every SFX by its measured sync point, not the design one: film t = spot t + design sync_s - `sync_s_measured`. 29 of 101 files moved by more than 0.25 s (largest: refill_inrush peaks 3.4 s in, rubble_emerge 2.8 s, jeep_climb 3.0 s, deep_sink 1.4-2.2 s, the four age_slide stops at 0.33-0.67 s instead of 1.1 s, so the src_in/dur trims on x111 need re-deriving).
- Add `-level_vs_norm_db` to gain_db where the peak cap kept a file under -20 LUFS: amb_dawn_lapping +12.2 dB (one 40 ms splash at 18.0 s sets its peak; the hush use reads only 0-12.5 s), pop_cascade +7.2, paper_flutter +5.4/+5.8, drain_start v2 +5.6, suitcase_gravel +5.4, postcard_drop v0 +4.5, amb_albatross_colony +4.2, age_slide v0 +3.9, albatross_tumble +3.8, amb_drained_seabed +3.5, amb_rain_canyon +3.2.
- Music: M05 offset 0.16 s puts its biggest rise on "up"; M12 is the composition-plan take (its own stop lands 0.67 s before the dropout); every stop-down stays a mix dip with a 20-50 ms ramp, because the cues do not stop where planned.

### Measured problems left for the owner's ears (none is a hard failure)
- Music: 1 of 26 planned events lands within 0.5 s (M08's storm swell). M05's Mauna Loa swell comes 3 s late after a near-silent stretch (energy labels inverted); M01, M03, M07, M09, M11, M13, M14 are flat (section spread 0.4-1.6 LU, against R6's 6 LU); M04 has an unplanned 1.2 s hole at film 159.0-160.2 s; M13 has no strong downbeat (its first second is 3 dB over its median), so the payoff hit rests on impact_deep + payoff_boom + hit_body. Composition plans (tried on M04, M05, M12) held section lengths but not the asked dynamics: only M12 improved.
- Rough key/tempo estimates: M09 sounds like C major (asked A major); M01, M14 and M06 lock to 4:3 of the asked tempo (both theme cues identically, and M14's chroma matches M01 at r = 0.93, so the reprise reads as the same theme).
- SFX: 17 files were generated very quietly (-45 to -55 LUFS raw, up to +35 dB to normalise): listen for hiss first in amb_drained_seabed, amb_dawn_lapping, amb_rain_canyon, paper_tap v0 and postcard_drop. 10 one-shots had a click in their last 10 ms (cut and faded). amb_drained_seabed had 3 isolated clicks (repaired). Beds amb_deep_pressure (second take, std 4.3 dB), amb_earth_deep, drain_flow and amb_seabirds_far swell by 4-5 dB std. line_draw's 4 variants range from 124 Hz to 12.5 kHz centroid and may not read as one device; wind_gust's 2 variants 88-952 Hz. rumble_rise, tension_groan, deep_sink and payoff_boom are sub-only by design (decoration under words; R5).
- No voice-like content in any SFX or music cue (Silero VAD 0.0 s on all 14 cues and on every bed).

### Credits
The account counter moved from 39,836 to 63,020 (23,184 credits, Creator plan, 58,107 left of 121,127): music about 13.7 credits per second of audio (14 prompt cues about 11.1K, 3 plan alternates about 3.4K), sound effects about 11 per second (129 takes about 8.5K). Other sessions on the same account could be inside that window.
