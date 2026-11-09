# Ep02 mix v1: re-recording mixer report

"Why Can't You See Most of Hawaii? (Look Down)", Rodney narration, film 746.93 s (12:26.9 = last word + 1.0 s + 12 s end screen).
Mixer pass 2026-11-09. Nothing was published, uploaded or posted. No ear verdict is claimed here: every number below is measured,
and the owner's listen list is in section 7.

## 1. Files

All in the scratchpad `audio/ep02_sound/` unless noted (media are never committed; this folder keeps the text: this report, hang_hu_v1.md, mix_ep02_v1.json and mix_ep02_v1_qc.json).

| File | What |
|---|---|
| `mix_ep02_v1.json` | the mix spec for engine/tools/mix.py (14 cues, 19 dips/lifts, 151 SFX entries, 47 beds, a `qc` block and a `placement_log`) |
| `mix_ep02_v1.wav` | the mix, 48 kHz stereo 24-bit, 746.93 s, md5 fe4f7ab9d5bb76d9f6a7f3837a9dbe2d |
| `stems_v1/vo.flac`, `music.flac`, `sfx.flac`, `amb.flac` | the four stems (amb = ambience), same loudness and limiter gain as the mix; they sum to the mix (max error 0.0). Rendered as 24-bit WAV, then packed to FLAC because the disk reached 99% (decoded md5 identical to the WAVs; 252 MB instead of 821 MB) |
| `mix_ep02_v1_report.json` | mix.py report: loudness passes, limiter, per-bus loudness, every cue and event as placed |
| `mix_ep02_v1_qc.json` | engine/tools/mix_qc.py: every gate and number in section 4 |
| `mix_ep02_v1_audio_scan.json` | engine/tools/audio_scan.py (now rebuilt on mix.build) |
| `phone_check_v1.txt`, `mask_diag_v1.txt` | phone-speaker proxy for the hero hits; diagnosis of audio_scan's broadband masking windows |
| `../ep02_vo/vo_proc.wav` | the prepared narration (moved here from mixwork/) |
| `deliver/ep02/hawaii_hang_elozetes_v1.mp3` | the owner's sound-only preview, MP3 192 kbps 48 kHz, -14.2 LUFS, -1.8 dBTP, md5 5ed6ffa59d8fb170f6ffc4b89bcb1e37 |
| `hang_hu.md` | the owner's listening note (Hungarian) |

Rebuild (from the scratchpad, venv python):
```
python -I /home/user/juicytea-media/longform/ep02-hawaii/tools/build_mix.py audio/ep02_sound audio/ep02_vo/timing.json audio/ep02_vo/vo_proc.wav audio/ep02_sound/mix_ep02_v1.json [--strict]
python /home/user/juicytea-media/engine/tools/mix.py audio/ep02_sound/mix_ep02_v1.json audio/ep02_sound/mix_ep02_v1.wav --stems audio/ep02_sound/stems_v1 --report audio/ep02_sound/mix_ep02_v1_report.json
python /home/user/juicytea-media/engine/tools/mix_qc.py <spec> <wav> <stems> audio/ep02_vo/timing.json <qc.json>
python /home/user/juicytea-media/engine/tools/audio_scan.py <spec> <wav> audio/ep02_vo/timing.json <scan.json>
```
build_mix.py refuses to run if timing.json no longer has the md5 the spot was built on (183ad505...), so every time stays tied to the voice markers.

## 2. Signal chain

- **Voice.** engine/tools/vo_proc.py on the raw Rodney stem: 70 Hz high-pass, split-band de-esser (max 6 dB), 2.5:1 soft-knee compressor (median 1.2 dB, max 8.9 dB), true-peak limiter. -26.5 LUFS / PLR 23.2 dB in, -18.0 LUFS / -3.2 dBTP / PLR 14.8 dB out; nothing moves in time. The limiter takes up to 8.6 dB off five plosive peaks (1:45.1 "hat", 4:19.6 "half", 6:28.6 "French", 8:03.0 "battle", 10:00.0 "Back"), each 18 dB over the median word peak.
- **Music.** 14 cues, each loudness-matched to -16 LUFS before its gain (the raw files ran from -13.9 to -23.2 LUFS), gains -9 (solemn -11/-12, payoff -7, finale -8), equal-power fades, every chapter card on a new cue. Measured offsets: M02 skips 0.5 s of its silent lead; M05 +0.16 s so its biggest rise sits on "up"; M12 delayed 1.12 s so the composition-plan take's own stop (file 77.80 s, -13 to -34 dB inside 0.25 s) lands on the payoff dropout at 677.89 s together with the riser; M14 back-timed (offset 2.86 s) so its natural end is the last frame.
- **Duck (music).** -12 dB broadband plus -4 dB more at 0.8-5 kHz, attack 80 ms, release 0.6 s, hold 0.8 s, lookahead 50 ms. The hold keeps the bed down through pauses inside sentences: 1.6 pump events a minute (ep01 had 18.6).
- **Dips.** 3 stop-downs with 40/30 ms ramps (0:15.8 -24 dB, 2:11.0 -30 dB, 3:10.6 -24 dB) plus the two cue gaps (8:00.2, 11:17.9); 9 gag dips (-9/-10, 0.25 s ramps); solemn dips (-3, then nested -6 at Nihoa without a bump, 1 s ramps); a new reveal thin before 33,000+ FT (3:52.3-3:54.0, -10 dB, back with the hit on "tall"); the +3 dB music-only refill lift.
- **Ambience bus.** 47 beds (every place has its own), looped with 1 s equal-power seams. Duck -6 dB broadband plus a spectral duck of -15 dB at 0.6-7 kHz under the voice (attack 0.15 s, release 1.0 s, hold 0.8 s), so the beds bloom back in every gap.
- **SFX bus.** 147 one-shots on (x147 aircraft, x154 tank wobble, x155 radio squelch and the optional x197 tourist tap are off by design). Speech-band duck only (-8 dB at 0.8-5 kHz, attack 30 ms, release 0.12 s, no hold), so gags and hit bodies in the gaps are untouched.
- **Master.** BS.1770 loudness to -14 LUFS, 4x oversampled look-ahead true-peak limiter at -1.7 dBTP (5 ms look-ahead, 120 ms release). The limiter does more than 1 dB of reduction for 0.16 s in the whole film (the payoff hit 11:19.1, -1.8 dB; the 1975 main shock 1:04.9, -1.5 dB).

## 3. Placement (marker-accurate)

- Every time comes from build_spot.py on the current timing.json; build_mix.py asserts the md5 and that each hero hit sits 0.06-0.08 s before its marker word (ft400, slides, miles, up, tall33, seven, old28, tall56).
- Generated SFX are placed by their measured sync point (sfx/selected.json), not the design one: the sync point keeps its film time; a file whose sync comes earlier than designed starts later; a long pre-roll is trimmed to at most 0.7 s more than designed (src_in plus a short fade-in); comic sounds never start earlier than spotted; no start moves into a restraint window. 97 changes are listed in the spec's `placement_log`, for example: postcards slap now lands at 0:09.12 (just after "postcards?"), the four age-slide stops land on Maui, O'ahu, Kaua'i and the last atoll, the stand-up riser ends on "up" (3:11.39), the payoff riser ends on the dropout (11:17.89), the refill inrush rises under "back" and peaks at 11:40.1.
- Bed material used as a swell keeps its spotted src_in (a first build moved those; caught and fixed before any render).
- Level fixes from the producer pass (-level_vs_norm_db) are applied: amb_dawn_lapping +12.2 (its 18.0 s splash is never reached), pop_cascade +7.2, paper_flutter +5.4/+5.8, drain_start v2 +5.6, suitcase_gravel +5.4 and others.
- Overrides: jeep_climb plays its loudest 0.62 s under the road shot and stops at the whip back (its peak is its last sample); rubble_emerge gets an 80 ms fade (it also peaks on its last sample).
- Gain trims after the speech-band check (section 4): x004 -3, x019 -5, x076 -3, x100 -6, x153 -3, x162 -3, x149 radio static -3, x059 -4 dB.

## 4. QC (mix_qc.py on the real files): all gates pass

| Check | Result | Gate |
|---|---|---|
| Integrated loudness (ffmpeg ebur128) | -14.0 LUFS | -14 +-0.5 |
| True peak | -1.7 dBTP | <= -1.5 |
| Sample peak / clipped samples | -1.71 dBFS / 0 | 0 |
| LRA | 3.8 LU | [info] 3-6 wanted (R6) |
| Silence (-45 dB, 0.3 s) | none | none |
| Stems sum to mix | max error 0.0 | <= 1e-3 |
| Voice minus music, 3 s windows that are >= 60% narration (n = 628) | median 21.7, p10 19.0, min 14.4 LU | p10 >= 15, median 17-23 |
| Voice minus ambience | median 22.9, p10 18.5 LU | p10 >= 15 |
| Voice minus music + ambience | median 19.2, p10 15.9 LU | [info] |
| Voice minus music per sentence (178 segments) | min 16.6 LU (s172 "never get to see"), median 22.2 | every sentence >= 12 |
| 1-4 kHz voice margin over music + SFX + ambience, 100 ms speech windows (n = 2719) | median 31.7 dB, p5 15.8 dB, 4.2% under 15 dB, 0.6% under 10 dB | <= 5% under 15 |
| Duck pumping | 1.61 per minute | <= 2 |
| Breathing room before the 9 reveals | all pass (table below) | pause >= 0.5 s, music drop >= 6 dB or music >= 25 LU under the voice |
| SFX one-shots in the hush windows (1975, Nihoa, Midway) | 0 (one ambience-level drain swell, x158, sits in the Midway hush by design) | 0 |
| Comic SFX on a word | 0 | 0 |
| One-shots | 147; per minute 16, 14, 15, 16, 12, 11, 9, 18, 6, 6, 11, 12, 1; max 7 in 10 s | <= 7 in 10 s |
| Same sound 3 times in 60 s | 0 | 0 |

Breathing room before reveals (music levels are of the music stem):

| Reveal | Time | Longest pause in the 4 s before | Music drop | Music under the voice, last 1.5 s |
|---|---|---|---|---|
| -400 FT | 0:16.97 | 0.50 s | 25.5 dB (stop-down) | 26.6 LU |
| landslides | 2:15.17 | 1.92 s | 27.2 dB (held breath) | 20.8 LU |
| 100 MILES | 2:33.51 | 0.52 s | 3.9 dB | 22.5 LU |
| stands up | 3:11.39 | 0.16 s | 28.9 dB (inhale) | 28.4 LU |
| 33,000+ FT | 3:54.05 | 0.16 s | 4.6 dB against a reference already quiet (M05's own rest at 3:44.8-3:46.9); the thin takes the bar before it from -43 to -57 dBFS | 40.6 LU |
| 7 MILLION YEARS | 6:04.21 | 0.60 s | 1.9 dB | 16.4 LU |
| 28 MILLION YEARS | 7:40.65 | 2.00 s | none | 22.2 LU |
| 3 MILES DOWN (silent by design, Midway hush) | 9:07.87 | 0.50 s | 1.2 dB | 23.8 LU |
| 56,000 FT payoff | 11:19.09 | 0.24 s | full stop 1.2 s | music out |

audio_scan.py (rebuilt on mix.build so it sees the real buses): sfx_loud 0, dead_air 0, clicks 0, no cue ends early. Its 33 broadband 'masking' windows are all low-frequency: in every one the background has at least half of its energy under 300 Hz (sub impacts, the quake, risers, the bowling-ball thump), which the playbook allows under reveal words, and the 1-4 kHz voice margin there is 13.3 dB or more (31 of 33 at 15 dB or more; mask_diag_v1.txt). Its 44 'vo_cuts' are the narration's own take edges (tts.py trims with 8 ms fades onto digital silence); in the mix every one sits on a bed, so none is heard as a drop-out.

Phone-speaker proxy (mono, 250 Hz high-pass): every hero hit body sits 8.6-15.4 dB over the music and ambience in its gap and 7-10 dB under the typical voice level.

## 5. Tool changes (repo)

- engine/tools/mix.py: on top of the ep02 keys added on 2026-11-08 (equal-power fades, norm_lufs, back_time, negative offsets, event trims, loops, pitch, EQ, enable/strict filters, ambience bus with its own duck, duck hold and lookahead, per-dip ramps, loudness passes, stems, report), this pass adds spectral ducking (`band` in `duck`, `amb_duck` and a new `sfx_duck`) and limiter runs in the report. An ep01 spec still mixes identically: max sample difference 3.6e-7 against the original mix.py (compat_test.json, 75 s).
- engine/tools/audio_scan.py: rebuilds its buses with mix.build(), so new keys and dips count (before, it rebuilt ep01-style buses and ignored dips).
- engine/tools/mix_qc.py (new): the gates in section 4, on the final file and the stems.
- longform/ep02-hawaii/tools/build_mix.py (new): spot files plus measured assets to the mix spec.

## 6. What changed between the three QC rounds

1. First render: loudness, peak, silence, voice-vs-music, pumping all passed, but the 1-4 kHz speech band failed badly (33.4% of speech windows under 15 dB, p5 3.0 dB). The cause was the ambience bus (803 of 906 bad windows): bright wind, surf, static and the hiss of quietly generated beds, 18 LU under the voice overall but level with it in the speech band. Two checks were also mis-measured (reveal pauses, an ambience-level swell counted as a hush one-shot); the metrics were fixed.
2. Spectral duck on the ambience (-12 dB, 0.7-6 kHz): 10.6% under 15 dB.
3. Ambience band -15 dB at 0.6-7 kHz, music band -4 dB, SFX band -8 dB (gaps untouched), eight gain trims on broadband water and wind one-shots that sat on words, a -10 dB thin before 33,000+ FT: 4.2%, p5 15.8 dB; all gates pass.

## 7. For the owner's ears (not measurable)

- Three music rests inside cues that were not planned, all under narration and covered by the ambience: 2:38.0-2:40.5 (M04, "...island chain. They're rare."), 3:44.8-3:46.9 (M05, "Above sea level, Everest wins easily"), 4:16.5-4:17.2 (M05). They may read as breaths or as holes.
- The spectral duck makes beds duller while Rodney speaks and brighter in the gaps; check that the wind and surf do not seem to 'breathe' with him (Pali 1:33-1:57, Lalo 6:28-6:53, the AF radio room 8:07-8:44).
- M13 has no strong downbeat; the payoff hit at 11:19.1 rests on impact_deep + payoff_boom + the hit body.
- The five plosive peaks limited in the voice prep (section 2).
- The producer's open music notes still stand (tempo and key misses, flat cues M01, M03, M07, M09, M11, M13, M14) and the beds that were generated very quietly may carry hiss (amb_drained_seabed, amb_dawn_lapping, amb_rain_canyon).

## 8. Owner decisions still open

1. AF ruse gag sounds (default: drip and telegram flick on, tank wobble and squelch off) or the strict version (`--strict`: all four off).
2. The 1942 aircraft stays off unless a formation is drawn.
3. Public-domain field recordings for the albatross colony, seabirds and monk seal instead of the generated ones.
4. Confirm the ElevenLabs plan is a paid commercial one before any monetised upload (music and SFX were generated there).
5. When the chapter renders exist, re-sync to the render's event log (frame-exact) and re-run build_mix.py, mix.py and mix_qc.py.
