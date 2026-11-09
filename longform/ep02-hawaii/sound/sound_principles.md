# Myth Juice sound principles (benchmark for ep02)

Status: research for the ep02 sound design, 2026-11-08. Not yet owner-approved and not yet in the playbook. Owner rules and the playbook (PLAYBOOK_craft.md section 11, section 10 humour) win wherever this file differs; the conflicts found are listed at the end with how they were resolved. Tags follow PLAYBOOK.md: [benchmark] = what documentary editors, sound designers or top channels say or do; [hypothesis] = our own threshold, not yet proven; [measured] = our own numbers.

What this file is for: the owner asked for professional, mood-setting, tension-building sound. These 23 rules turn that into things a script can check, each with a test and with what ep01's mix did. ep01 passed 2 (R1, R2), half-passed 2 (R7, R14) and failed 18; R15 was not checked.

## How ep01 was measured

- Mix: scratchpad audio/mix_v3.json (1011 s, the uncut v3 timeline), rebuilt bus by bus exactly as engine/tools/mix.py does (VO, ducked music, SFX), then loudness-matched like the final file.
- Tools (scratchpad, not in the repo): audio/ep02_sound/tools/measure_ep01.py (short-term loudness per stem, duck pumping, SFX density, repeats, drops, ambience) and tools/band_ep01.py (1-4 kHz voice margin). Results: audio/ep02_sound/ep01_mix_measure.json. Final-file loudness: ffmpeg ebur128 peak=true on audio/mix_v3.wav.
- Reveal and death-beat times come from R6/voice_audio and the playbook's antipode-overlay times (same timeline: R6's record-scratch fix to 589.55 s is in mix_v3.json).

ep01 in numbers [measured]:

| Metric | ep01 mix_v3 |
|---|---|
| Integrated / true peak / LRA | -14.0 LUFS / -1.5 dBTP / 2.3 LU |
| Short-term (3 s) mix loudness p10-p95 | -14.9 to -13.2 LUFS (1.7 LU spread) |
| Voice minus music under speech (3 s windows, n = 876) | median 18.9 LU, p10 15.6, p90 22.7 |
| Voice margin over music+SFX at 1-4 kHz, speech windows (100 ms) | median 28.0 dB, p5 12.4 dB; 8.6% of windows under 15 dB, 2.8% under 10 dB |
| Music cues | 10 cues, 56-185 s long (mean 104 s), every cue at gain -9 dB, every change the same 2.5 s fade-in / 3 s fade-out crossfade |
| Cue energy (median raw bed loudness per cue) | -21.5 to -25.6 LUFS, a 4.1 LU spread across the whole film |
| Duck pumping (music rises 4 dB or more inside 0.25-1.5 s speech gaps) | 314 events, 18.6 per minute |
| Music stop-downs (bed 20 dB or more under its median, 0.5 s or more) | 5 (44.3, 107.2, 346.4, 353.3, 478.6 s), all from cue content or crossfades; none at the 4 key reveals (28.9, about 227.7, 590.4, 844.8 s) |
| Music dips | 2, both before gags (233.2 s, 273.0 s) |
| SFX | 340 hits = 20.2 per minute; 27 in the first minute; 281 (83%) start while the voice is speaking |
| SFX level vs typical voice (50 ms) | median -12.7 dB; 67 hits within 10 dB of the voice; impact_short peaks reach -0.5 dB of the voice (304.4 s, 511.9 s) |
| Same file repeated within 10 s | 138 times; whoosh_soft used 83 times and pop_ui 78 times, one file each |
| Risers | 8; only 1 (342.6 s) peaks into a hit; the rest trail into whooshes, pops or nothing |
| Place ambience | 61 s in total (ice wind, rumble, crickets) = 6% of runtime |
| Low-end impacts on a phone | impact_deep keeps only -31.7 dB of its energy above 250 Hz (rumble_quake -31.6 dB, impact_short -21.7 dB); impact_deep was used 8 times |

## The rules

Each rule: what to do, the test, why (sources are numbered, see the end), and what ep01 did.

### A. Loudness and a voice you can always follow

**R1. Master to -14 LUFS integrated (plus or minus 0.5 LU), true peak -1.5 dBTP or lower, never quieter than -15 LUFS.** [benchmark]
- Test: ebur128 peak=true on the final file.
- Why: YouTube plays back at -14 LUFS and turns louder files down but does not turn quieter ones up (Ian Shepherd [1][2]); a quiet master just plays quieter than its neighbours. Same as playbook section 11.
- ep01: PASS (-14.0 LUFS, -1.5 dBTP).

**R2. Keep music at least 15 LU under the voice in 90% of speech windows (median 18-22 LU), and ambience at least 15 LU under it.** [benchmark]
- Test: 3 s short-term loudness of the voice stem minus the ducked music bus (and the ambience bus) over speech windows.
- Why: the AES listening study on documentary ducking recommends at least 10 LU for commentary over music and at least 15 LU for commentary over ambience, and found that ordinary viewers prefer 4 LU more than engineers [3]; practitioners start documentaries at 18-24 dB below the narration [4].
- ep01: PASS (median 18.9 LU, p10 15.6 LU). Keep the playbook's -9 dB bed and -11 dB duck as the starting point.

**R3. Protect the speech band and the key words: the voice beats music plus SFX by 15 dB or more at 1-4 kHz in at least 95% of speech windows, and no SFX starts on a name, a number or a payoff line.** [benchmark; threshold hypothesis]
- Test: 1-4 kHz band level of the voice stem minus music+SFX in 100 ms speech windows; list every SFX onset that falls on a marked key word ({m:} markers in timing.json).
- Why: memory for what is heard drops first when pacing and arousal rise (Lang's limited-capacity research [5]); practitioners keep SFX off important words and thin the music around statistics and names [4]; the playbook already asks for 15 dB at 1-4 kHz under impacts.
- ep01: FAIL (91.4% of windows at 15 dB or more, p5 12.4 dB; 83% of SFX started under speech; two bell dings at 843.4 and 845.9 s bracket the film's central question at 844.8 s).

**R4. No pumping: the duck holds through the pauses inside and between sentences (hold about 0.8-1.0 s, then a 0.5-0.8 s release), so the music only rises in planned gaps of 1.2 s or more; 2 or fewer pump events per minute.** [benchmark; threshold hypothesis]
- Test: count gaps of 0.25-1.5 s in which the music gain rises 4 dB or more (measure_ep01.py).
- Why: a release that is too fast 'causes the music to snap back up during natural pauses inside a sentence', 'an audible pumping rhythm that draws attention to itself'; hold is the control for 'smoothing over short pauses mid-sentence' [6]; music that pumps 'like breathing' is a known tell of automatic ducking [7].
- ep01: FAIL (314 events, 18.6 per minute; the 0.6 s release was already in the guide's range, but mix.py has no hold, so every pause over about 0.3 s let the bed swell).

**R5. Every hit that carries a beat must be audible on a phone: give it a 250-700 Hz harmonic layer (energy above 250 Hz no more than 10 dB below its total) and place it in a voice gap; sub-only booms are decoration and may sit under words.** [benchmark; threshold hypothesis]
- Test: high-pass each impact file at 250 Hz and compare energy; play the mix through a phone-speaker check (high-pass 250 Hz, mono sum) at every reveal.
- Why: most phone speakers 'struggle to reproduce anything below 200Hz', and the ear can only rebuild a bass hit from its upper harmonics [8]; ep01's weakest audience was mobile (playbook section 8). This keeps the playbook rule that impacts under words stay below about 300 Hz: the audible layer goes in the gap, not under the word.
- ep01: FAIL (impact_deep, used 8 times on reveals, keeps only -31.7 dB of its energy above 250 Hz, so on a phone it is close to silent).

### B. Music: mood, energy and when it changes

**R6. Plan an energy map before generating music: label every cue section low, mid or high; the quietest and loudest cue sections differ by 6 LU or more, and the final mix LRA lands at 3-6 LU while the voice itself stays steady.** [benchmark; thresholds hypothesis]
- Test: median raw loudness per cue section from the music bus; ebur128 LRA of the final mix; short-term spread of the voice stem alone 3 LU or less.
- Why: 'If it's all the same all the time, it will lose its impact' (Jonny Elwyn, with Joe Walker on making contrasts 'as sharp and intense as possible') [9]; trailer designers get power 'from increasing the dynamic range of your content, not decreasing it' [10].
- ep01: FAIL (cue medians within 4.1 LU of each other; LRA 2.3 LU; short-term mix spread 1.7 LU: one even level for 17 minutes).

**R7. Match the music to the job: 'thinking' music (pulse or texture, no lead melody) under explanation; 'feeling' music only where the story has earned it, mostly in voice gaps and hero shots; alternate the two without a fixed ratio.** [benchmark]
- Test: each cue section is tagged thinking or feeling in the cue sheet; no feeling section under a segment with a hero number or a mechanism explanation; every feeling section follows a planted emotional set-up.
- Why: Johnny Harris sorts music into thinking and feeling, warns against narrating explainer information over feeling music, calls unearned emotional music 'abusing this music' that 'cheapens your video', and alternates the two so the viewer does not tire [11]; documentary composers prefer 'a subtle mood' over drama [12].
- ep01: PARTIAL (the global prompt banned a lead melody, good; but the densest explanation, the 'honest part' at 782-875 s that R6/voice_audio called the most monotonous stretch, ran under one reflective, warm cue (m09, 103 s): a feeling-type cue under the film's densest explanation).

**R8. Change the music audibly every 45-90 s and never let one unchanged section run past 120 s; change it at a story turn, entering 0.5-2 s before the turn line rather than on the word.** [benchmark; interval hypothesis]
- Test: list every cue or section change (new cue, a step of 3 LU or more, or a new instrument group) with its time; max interval 120 s; each change sits 0.5-2 s before a turn line in timing.json.
- Why: NPR Throughline's sound designer brings music in where 'the narrative is about to change', 'slightly before, where it's not so predictable', never 'And then I had an idea. Boom.' [13]; documentary composers place every cue for a reason at spotted story beats [12]; the playbook already asks for a change by 2:00.
- ep01: FAIL (m03 ran 185 s and m10 139 s; all 9 cue changes were the same symmetric 3 s crossfade at chapter boundaries, none placed on a turn line).

**R9. End cues on purpose: each cue exits on its own ending (a cadence or ring-out) or hard-outs into a stop-down or hit; plain crossfades for at most a third of transitions.** [benchmark; ratio hypothesis]
- Test: classify every transition in the mix json.
- Why: 'whenever you get out, it's going to be noticed' (composer Miriam Cutler [12]); end a cue on its natural conclusion or close it with an impact or ring-out [9].
- ep01: FAIL (9 of 9 transitions were the same 2.5 s / 3 s crossfade).

**R10. Make the music hit the picture: generate each cue from an ElevenLabs composition plan whose chunk boundaries sit on the planned turns, drops and reveals; accept a cue only if each planned drop or build lands within 0.5 s of its time, otherwise cut it at a bar line.** [benchmark for the API; tolerance hypothesis]
- Test: energy scan of each cue against its plan.
- Why: composition plans set each chunk's duration_ms (3-120 s, up to 30 chunks) with its own positive and negative styles [14], while a free-text prompt cannot place an event.
- ep01: FAIL (m01's prompt asked for a drop 'around 31 seconds'; the only 20 dB drop in m01 came at 44.3-46.7 s). engine/tools/music.py does not support composition plans yet.

**R11. Justify every sound: each cue and each SFX has a stated job (sync, information, emotion, continuity or emphasis); mute half of the decorative SFX as a test and keep the version that feels cleaner, not emptier.** [benchmark]
- Test: the cue sheet has a 'job' column with no blanks; a remove-50% A/B for the owner on one chapter.
- Why: 'ask yourself why you're using it and justify it... If you don't, then don't do it' and 'restraint is as important as laying it on' (Ramtin Arablouei, NPR Throughline [13]); 'sometimes you can watch a scene and realize that it doesn't even need music' (editor Bill Weber [15]); 'What changes if I remove this sound?' [7].
- ep01: FAIL (340 SFX with no recorded job; 20.2 per minute).

### C. Tension and reveals

**R12. Give every hero reveal a stop-down: the music bus drops 20 dB or more for 0.4-1.2 s (ramps of 50 ms or less), ending on the reveal word, while ambience or a sub drone stays above the -45 dB silence gate; then the hit, the new section or the bigger cue lands on the word. Use it as punctuation: about one per 60-90 s at most.** [benchmark; durations hypothesis]
- Test: for each hero reveal in the script, the music bus level in the window before the reveal word; silencedetect (-45 dB, 0.3 s) still passes.
- Why: trailer stopdowns 'clear space and create silence, which makes the coming drop feel even bigger' and spotlight a line [16]; 'Lack of sound can be as gripping as an explosion' (cut almost everything at the riser's peak) [10]; 'Sometimes the silence, even a minute amount, makes a huge difference' (re-recording mixer Tony Volante [17]); keep room tone at about -30 to -25 dB under intended silence [18]. The narration's 0.7-1.1 s pause before key reveals (playbook section 7) is where it goes.
- ep01: FAIL (no stop-down at any of the 4 key reveals; the only dips were 2 gag dips).

**R13. Every riser resolves on the frame: its peak lands within 1 frame of a hit, a stop-down or the reveal word, and never runs on under narration; no two risers of the same sound within 60 s (each live drain keeps its rising sound, as the playbook asks, but successive drains use different rising devices: water suck, rumble rise, pitch-rising drone).** [benchmark; spacing hypothesis]
- Test: riser file peak time plus placement vs the next hit or reveal marker; identical riser files per 60 s.
- Why: a hit that lands 'even a fraction of a second off from the hero shot or title card' loses impact, and hits serve 'as emphatic punctuation at the end of a rise' [19]; risers are followed 'by a hit, or even a brief moment of silence' [20]; repeated production effects stop drawing attention by the third time [26].
- ep01: FAIL (1 of 8 risers resolved into a hit at its peak).

**R14. Build tension with more than one-shots: under each chapter climax run a build of 8 s or more whose music energy rises 4 LU or more into the reveal, made from a pulse or ticking ostinato, rising pitch (a Shepard-style climb), a low sub drone and layered, blended place sound.** [benchmark; numbers hypothesis]
- Test: music-bus short-term loudness over the 8 s before each chapter's main reveal; the cue sheet names the tension device.
- Why: Dunkirk's score uses a Shepard tone that seems to rise forever, over the ticking of Nolan's own watch (Vox [21]); 'looming sub drones' under hits [20]; Throughline layered 8-9 sound layers, roughened so they blend, to make listeners 'uncomfortable for a couple of minutes' [13].
- ep01: PARTIAL (tension came almost only from 8 riser one-shots; ticks were used only on counters).

**R15. Make contrast that survives YouTube's Stable volume: create drops by removing layers and changing register (full bed to sub drone), not only by lowering level, and check every reveal after a dynamic-normaliser pass.** [hypothesis]
- Test: render a check copy through ffmpeg dynaudnorm and confirm each stop-down still reads as a change (fewer layers, different register).
- Why: Stable volume is on by default and 'balances the range between quiet and loud' [22], so pure level contrast is partly flattened for many viewers.
- ep01: not checked.

### D. SFX craft

**R16. Sound the devices, not the text: SFX go on the playbook's device list (flights, counters and gauge, reveals, drains, standees) and on gags; text, label and pin entrances are silent; at most 3 SFX in any 10 s of narration and about 10 per minute outside montages.** [benchmark; numbers hypothesis]
- Test: SFX count per 10 s and per minute; every SFX names its device or gag.
- Why: 'Sound effects do not need to be added to every movement' [23]; a sound on every cut teaches viewers to hear the edit, and density should follow the story, not a timer [7]; 'you sometimes do not need many sounds to wrap up a scene' [10]; over-use of production features uses up the attention the message needs [5]; transitions 'give you no information' and serve pacing only (Vox's Estelle Caswell [24]).
- ep01: FAIL (20.2 SFX per minute; 78 pop_ui on labels; 8 pops in the first 14 s and 27 SFX in minute 1).

**R17. Spot SFX to the final picture, within 1 frame of the event, from the render's event log; a whoosh only where something actually moves.** [benchmark]
- Test: each SFX entry carries the event id and frame of its visual event; offset 1 frame or less.
- Why: Kurzgesagt adds music and SFX as the last step, after voice-over and animation, with a soundtrack composed for each video [25]; whooshes belong 'where movement exists', not on static cuts or slow dissolves [7].
- ep01: FAIL (mix.json SFX entries carry only time, file and gain, no event id, so sync could not be checked; 83 identical soft whooshes).

**R18. Never let the same sound repeat identically: 4 or more variants per recurring family, chosen round-robin with seeded pitch (plus or minus 1.5 semitones) and level (plus or minus 2 dB) variation; no identical file more than twice in 60 s.** [benchmark; numbers hypothesis]
- Test: count identical file uses per 60 s window.
- Why: the attention response to a repeated production effect fades by its third onset, while a change of voice keeps working (Potter et al., radio listening studies [26]); trailer designers randomise layered banks so no hit repeats (625 combinations from four banks of five) [10].
- ep01: FAIL (138 repeats of the same file within 10 s).

**R19. Give every place its own ambience bed: surf, wind, forest, deep-water pressure; continuous across cuts inside the same place, changing with the place, 15 LU or more under the voice and rising in gaps; ambience under at least half of the runtime.** [benchmark; share hypothesis]
- Test: ambience-bus coverage and its loudness against the voice (R2).
- Why: location ambience creates 'a sense of place' so the listener feels 'immersed in a particular location' [13]; Alex Gibney's team built a soundscape you 'feel subconsciously' [17]; ambience should be felt more than heard and continuous ambience hides hard cuts [7].
- ep01: FAIL (61 s of ambience, 6% of runtime).

**R20. Let sound lead the picture at every change of place: the next place's ambience, and a new cue where there is one, starts 0.3-1.0 s before the visual cut.** [benchmark; offsets hypothesis]
- Test: for each location change, the next ambience start minus the cut time.
- Why: 'bring the music in or bring the sound design in before you hear any kind of mention of what that's supposed to be highlighting' [13]; a cut placed just before an incoming sound hides the change [9].
- ep01: FAIL (no pre-lap planned; mix.json has no field for it; music only crossfaded symmetrically around chapter starts).

### E. Humour and taste

**R21. Make gag sounds in-world and never cheap: the comic sound is what the on-screen thing would make (paper flap, suitcase wheels, a radio squelch), in the gap after the line, 0.8 s or shorter, one per gag; no meme stingers (record scratch, crickets, cartoon fall whistle, 'vine boom', sad trombone, bell ding as a punchline).** [owner + benchmark]
- Test: every comic SFX is tied to a gag id and a visible object, starts after the line's last word; grep the SFX list for the banned names.
- Why: the owner wants funny scenes without cheap gags; comedy editors leave a pause after the punchline and warn that an extra joke sound in that gap weakens it [27]; calling attention to single showy sounds 'is kind of old school radio' [13]. The playbook already sets the gap, length and level (section 11).
- ep01: FAIL (cartoon_fall at 17.5 s inside the hook, record scratch twice, crickets, 9 bell dings, 4 splashes).

**R22. Protect tragic deaths and graves (ep02: the 1975 Halape deaths, the Nihoa burials, the Battle of Midway and its war graves) on two levels. Scene: from the scene's first line until the music cue or section changes after the last death or grave line, no stings, risers, musical hits, UI ticks, comic SFX or playful cue; realistic event sound (the quake, the wave) is allowed. Hush: from 1 s before each death or grave line until 10 s after it, only ambience and one sustained pad (or no music).** [owner + benchmark; windows hypothesis]
- Test: list every SFX and cue change inside each scene and hush window; the hush may hold ambience only; a comic SFX after a death line needs a cue or section change between them.
- Why: owner rule (no stings or comedy near the 1975 deaths, the Nihoa graves or the Midway war graves; playbook section 10); documentary composers' 'this is somebody's real story' and 'Don't bring up the drama' [12]; on sad and serious material 'we may not have leaned so heavily into the sound' [13]. A passing mention of a natural death (a scientist who 'died' long ago) is not covered.
- ep01: FAIL (record scratch at 589.55 s while the grief cue m06 was still playing, about 39 s after 'Neither of them made it back' at 550.9 s; the next cue started at 602.9 s).

### F. Gate

**R23. Gate with numbers, then the owner's ears: run audio_scan.py plus the metrics above (pump events per minute, SFX per minute and per 10 s, identical repeats, riser resolution, stop-downs at reveals, protected-window SFX, 1-4 kHz margin, phone check) and give the owner a list of about 10 timestamps to listen to (each hero reveal, each gag, each protected zone). No agent claims an ear verdict.** [reviewed]
- Why: playbook section 16; ep01's audio checks covered masking and level only, so density, pumping and flat energy were never caught.
- ep01: FAIL (none of these metrics existed).

## ep02 check of the locked script's SFX and music notes

Times from audio/ep02_vo/timing.json (734.85 s).

Protected zones (R22):

| Zone | Scene / hush window | What the script has | Verdict |
|---|---|---|---|
| 1975 Halape deaths | scene s016 52.6 s to the Ch2 crossfade at s025 (89.2 s); hush 76.2-88.9 s around 'Two people died' (s022, 77.2-78.9 s) | solemn pad, single low note, music -3 dB; realistic quake, crack, flood and wave sounds in s017-s021; nothing in the hush; whip at s025 (89.2 s); first comic SFX at s029 (104.3 s) after the cue change | passes if the wave_rush (-12) of s021 (74.1 s) has faded to ambience by 76.2 s and the s025 whip sits on 'One did.' rather than at the segment start |
| Nihoa graves | scene s096 372.9 s to the next cue or section change; hush 379.8-393.0 s around 'buried their dead' (s098) | nothing in the scene; tick_counter and impact_soft in s094 (364.2 s) come before it; but bloop_comic in s106 (415.0 s) comes 32 s after the graves line with no music change in between (the Ch4 cue runs on to the Ch5 crossfade at s111, 434.4 s) | FAIL as written: add a music section change at the hurricane turn (s105, 410.1 s), before the seal gag |
| Midway war graves | hush from 1 s before 'Japan lost every carrier' (s133, 525.3 s) to 10 s after 'war graves' (s139 ends 555.3 s) = 524.3-565.3 s | tick_soft (-20) on 'three miles down' in s138, about 0.4 s before 'These are war graves' | FAIL: remove the tick; pad and ambience only |
| Battle of Midway scene | scene s123 480.7 s to the Kure lift after s139 | drip_comic in s125 (488.7 s) and s129 (509.6 s), line_tug in s130 (513.7 s): 12-37 s before 'Japan lost every carrier' and 37-62 s before the war-graves line; thunk_soft on 'confirmed' in s132 (about 521 s) | FAIL under the scene rule; owner's call, because the codebreaking ruse is a genuinely light story: keep the deadpan narration and the music dip, and swap the comic drip and tug for in-world sounds (a real tap drip, radio static, teletype) and drop or soften the s132 thunk, a hit 4 s before the casualty line |

Other script notes (101 SFX planned = 8.2 per minute, within R16):
- R8: two music stretches run past 120 s without a planned change: the Ch3 cue from s048 (179.2 s) to s083 (312.2 s), 133 s, and the Ch4 cue from s083 to s111 (434.4 s), 122 s. Add a section change in each (for Ch4, the s105 change above).
- R13: drain risers sit 12 s apart at s005 (15.2 s) and s009 (27.5 s) and 3.3 s apart at s048 (179.2 s) and s049 (182.6 s); use different rising devices and let each resolve on its frame.
- R5: impact_deep is planned 7 times on hero-number words (s005, s039, s051, s061, s118, s122, s169); keep the sub layer on the word and put an audible harmonic layer in the gap after it, or phone viewers hear nothing.
- R12: the script plans one music dip before a reveal (s169, 1.2 s before the 56,000 ft payoff); the other hero reveals need their stop-downs added in the cue plan.

## Conflicts with the playbook and how they were resolved

- Silence before reveals vs the playbook's 'no silence of 0.3 s or more below -45 dB': no conflict if the stop-down removes only the music and keeps ambience or a sub drone above the gate (R12).
- 'One SFX per visible event' (playbook section 11, [reviewed]) vs 'not every movement needs a sound' [benchmark]: the playbook wins by precedence, so its device list keeps its sounds; R16 only silences text, label and pin entrances, which are not on that list and caused 78 of ep01's 340 hits.
- Ducking levels: the playbook's -9 dB bed and -11 dB duck produced 18.9 LU under speech, inside the benchmark range, so R2 keeps them; R4 keeps the 0.6 s release and only adds a hold.
- Comic SFX placement and level (playbook section 11) are kept; R21 adds the in-world and no-meme conditions.
- 'A riser plays' under every live drain (playbook sections 8 and 11, [reviewed]) vs a rate cap on risers: the playbook wins, so R13 caps only identical riser sounds and asks each to resolve.
- Loudness: R1's -14 plus or minus 0.5 LU and -1.5 dBTP is the mix target; the playbook's gate on the final file (-14 plus or minus 1.5 LU, -1.0 dBTP) stays the pass/fail gate.

## Engine changes these rules need (not made here)

- engine/tools/mix.py: a duck 'hold' (about 0.8-1.0 s); per-dip ramp length (a stop-down needs 20-50 ms ramps, dips use a fixed 0.25 s); an ambience bus measured separately; optional pre-lap offsets.
- engine/tools/music.py: composition-plan requests (chunks with duration_ms and styles) instead of one prompt per cue.
- engine/tools/audio_scan.py: add the R23 metrics (the logic is in the scratchpad tools above).
- SFX library: 4 or more variants per recurring family and a harmonic layer on impacts; event ids from the render's event log.

## Gaps in the research

- No first-party statement was found on Kurzgesagt's per-animation SFX method, or on RealLifeLore's or Wendover's music practice; their videos could not be measured (yt-dlp is banned on YouTube by the playbook and vidIQ credits are not allowed for this task). Change rates and SFX densities of those channels are therefore not benchmarked; R8 and R16 thresholds are our hypotheses, set against ep01's measured failures.
- The full Torcoli et al. paper (documentary practice numbers) was behind a 403; only its abstract was read.
- Several practitioner sources are vendor or secondary blogs ([4], [6], [7], [19], [23], [27]); they are used only where they agree with the primary sources.

## Sources

1. Ian Shepherd, 'YouTube loudness', Production Advice: https://productionadvice.co.uk/youtube-loudness/
2. Ian Shepherd, 'Stats for nerds' ('YouTube doesn't turn up quieter videos'): https://productionadvice.co.uk/stats-for-nerds/
3. Torcoli, Freke-Morin, Paulus, Simon, Shirley, 'Preferred levels for background ducking to produce esthetically pleasing audio for TV with clear speech', JAES 67(12), 2019, doi 10.17743/jaes.2019.0052 (abstract): https://cris.fau.de/publications/234640600
4. OverseerOS, 'Background music volume under voiceover' (vendor): https://www.overseeros.com/blog/background-music-volume-under-voiceover
5. Limited capacity model of motivated mediated message processing (Lang), summary and references: https://en.wikipedia.org/wiki/LC4MP
6. DaVinci Resolve ducking guide (hold and recovery; vendor): https://tryuncle.com/learn/davinci-resolve/how-to-duck-background-music-under-dialogue-in-davinci-resolve
7. OverseerOS, 'YouTube sound design' (vendor): https://www.overseeros.com/blog/youtube-sound-design
8. LANDR, 'How to make bass audible on phone speakers': https://blog.landr.com/make-bass-audible-phone-speakers
9. Jonny Elwyn, 'Better editing through sound design' (quotes Chris McCaleb, Joe Walker, Erik Aadahl): https://jonnyelwyn.co.uk/film-and-video-editing/better-editing-through-sound-design/
10. Krotos, '5 tips for designing trailer sound effects': https://krotos.studio/blog/trailer-sound-design-tips-tricks
11. Johnny Harris, 'How I Use Music | Thoughts on the Creative Power of Music' (transcript summary): https://rosetta.to/u/johnnyharris/how-i-use-music-thoughts-on-the-creative-power-of-music
12. International Documentary Association, documentary composers roundtable (Jeff Beal, Joel Goodman, Miriam Cutler, Peter Davison, Mark Adler): https://documentary.org/node/34094
13. Ramtin Arablouei (NPR Throughline), 'Sound design 101' interview transcript: https://journalismcourses.org/wp-content/uploads/2020/11/Interview_2_Sound_design_101_from_Ramtin_Arablouei_of_the_podcast_Throughline.pdf
14. ElevenLabs, 'Composition plans' (music API): https://elevenlabs.io/docs/eleven-api/guides/how-to/music/composition-plans
15. Frame.io, 'Finding the flow: a musical approach to cutting documentaries' (Bill Weber): https://blog.frame.io/2017/06/19/a-musical-approach-to-cutting-documentaries/
16. Rareform Audio, 'Trailer music: drop vs stopdown': https://www.rareformaudio.com/blog/trailer-music-drop-vs-stopdown
17. Post Super, 'Balancing verite and emotion in documentary sound: Alex Gibney and Tony Volante': https://post-super.com/blog/balancing-verit-and-emotion-in-documentary-sound-a-conversation-between-alex-gibney-and-tony-volante
18. Krotos, 'No sound in sound design': https://krotos.studio/blog/no-sound-in-sound-design
19. Two secondary trailer-sound blogs (weak): 'What makes great trailer music' (hit timing; 'remove sound entirely for even a fraction of a second before a major hit'): https://tonalchaos.pages.dev/blog/what-makes-great-trailer-music/ and 'Sound design for trailers: hits, rises, drones, pulses' ('Silence gives the next hit somewhere to land'): https://add-app.pages.dev/sound-effects/sound-design-for-trailers-hits-rises-drones-pulses/
20. Ableton, 'Learn how to make high-impact sounds for movies and trailers' (Richard Veenstra): https://www.ableton.com/en/blog/learn-how-to-make-high-impact-sounds-for-movies-and-trailers/
21. Vox, 'The sound illusion that makes Dunkirk so intense' (transcript page): https://rosetta.to/u/vox/the-sound-illusion-that-makes-dunkirk-so-intense
22. YouTube Help, 'Control video volume on your device' (Stable volume): https://support.google.com/youtube/answer/14106294
23. Motion The Agency, 'Sound design for explainer videos' (vendor): https://www.motiontheagency.com/blog/sound-design-for-explainer-videos
24. School of Motion podcast, Estelle Caswell (Vox Earworm): https://www.schoolofmotion.com/podcast/estelle-caswell-vox-interview
25. Kurzgesagt, 'Our video process': https://kurzgesagt.org/youtube/
26. Potter, Sites, Jamison-Koenig, Zheng, 'The impact of cognitive load on the cardiac orienting response to auditory structural features during natural radio listening situations', Journal of Cognition 1(1):39, 2018: https://journalofcognition.org/articles/10.5334/joc.43
27. Comedy editing guides on the pause after a punchline (vendor, weak): https://www.finchley.co.uk/finchley-learning/best-practices-for-comedy-video-editing-on-youtube and https://sfxengine.com/blog/sound-effects-timing-in-comedy-videos
