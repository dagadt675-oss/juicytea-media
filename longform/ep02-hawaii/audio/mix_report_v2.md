# Ep02 mix v2: sound finisher report

"Why Can't You See Most of Hawaii? (Look Down)", Rodney narration, film 746.93 s. Pass of 2026-11-22.
Nothing was published, uploaded or posted. No ear verdict is claimed: every statement below is measured, and the owner's listen
list is in section 9.

## 1. Result in one paragraph

mix_ep02_v2 passes all 16 mix_qc gates: -14.0 LUFS, -1.7 dBTP, LRA 3.8 LU, 1-4 kHz band 4.4 %, pumping 1.61/min. The three
unplanned music rests of v1 (2:36, 3:45, 4:16) are filled inside their cues and no new rest or music hole appears anywhere. Two
flat cues are replaced by new takes: M13, the payoff, now has a real downbeat on "tall", and M11 has a still hush that lifts only
after it. M01, M03, M07, M09 and M14 keep their v1 audio because no new take was clearly better. Two beds lost their hiss floor
(dawn lapping, drained seabed). The rain bed has no separable hiss and is unchanged. The new M13 is brighter than v1: the 1-4 kHz
voice margin on "tall" is at the 15 dB line, not a clear pass, and ten 100 ms windows of narration after the hit (683.8-693.9) fell
under 15 dB, although the film-wide band gate still passes (section 8). The narration, every sync time, every SFX
placement and every dip are the same as v1. Credits used: 8,432 by the account counter (upper bound) against 8,402 estimated
from the seconds requested; the cap was 12,000.

## 2. Files

All paths are under the scratchpad `audio/ep02_sound/` unless noted. Media are never committed. In the repo,
`longform/ep02-hawaii/audio/` keeps the text: this report, hang_hu_v2.md, mix_ep02_v2.json and mix_ep02_v2_qc.json. Its `audio/v2/`
holds the evidence json/txt (rests, fills, gain ride, gates, take checks, budget, spec diff, NOTES_v2.md), and
`longform/ep02-hawaii/tools/sound_v2/` holds the tools_v2 scripts.

| File | What |
|---|---|
| `mix_ep02_v2.wav`, `stems_v2/{vo,music,sfx,amb}.flac` | the mix (48 kHz) and its four stems (FLAC, verified lossless against the WAVs, which were deleted) |
| `deliver/ep02/hawaii_hang_elozetes_v2.mp3` (scratchpad root) | listening copy, 192 kbps |
| `mix_ep02_v2.json` | mix spec (build_mix.py with the v2 options) |
| `mix_ep02_v2_qc.json`, `mix_ep02_v2_report.json`, `mix_ep02_v2_audio_scan.json`, `phone_check_v2.txt` | QC outputs |
| `music_v2/selected_v2.json`, `music_v2/music_ovr_v2.json`, `sfx_v2/selected_v2.json` | v2 selections and cue overrides; v1's `music/selected.json` and `sfx/selected.json` are untouched |
| `music_v2/gen/` | new takes, `budget.json`, `check_probe.json`, `check_r1.json`, `check_r2.json` (sfx_check.py music) |
| `music_v2/check_m13_tail.json` | sfx_check.py music on M13 take3 as generated and with the tail ride (spread 10.4 and 6.1 LU) |
| `music_v2/fill_cfg.json`, `fill_report.json`, `gain_cfg.json`, `gain_report.json` | rest fills (M04, M05), M13 tail ride |
| `sfx_v2/*_gated.wav`, `sfx_v2/gate_*.json` | denoised beds and their gate reports |
| `tools_v2/` | rests.py, fill_rest.py, gain_patch.py, gate.py, gen_music.py, take_view.py, bed_floor.py, band_diff.py; `rests_v1.json`, `rests_v2.json`, `sections_v1_v2.txt`, `band_diff_v1_v2.txt` |
| `NOTES_v2.md` | the running checkpoint of this pass |

Rebuild (from the scratchpad root):

```
D=audio/ep02_sound
python -I /home/user/juicytea-media/longform/ep02-hawaii/tools/build_mix.py $D audio/ep02_vo/timing.json $PWD/audio/ep02_vo/vo_proc.wav $PWD/$D/mix_ep02_v2.json \
  --music-sel $D/music_v2/selected_v2.json --sfx-sel $D/sfx_v2/selected_v2.json --music-ovr $D/music_v2/music_ovr_v2.json --version v2
python /home/user/juicytea-media/engine/tools/mix.py $D/mix_ep02_v2.json $D/mix_ep02_v2.wav --stems $D/stems_v2 --report $D/mix_ep02_v2_report.json
python /home/user/juicytea-media/engine/tools/mix_qc.py $D/mix_ep02_v2.json $D/mix_ep02_v2.wav $D/stems_v2 audio/ep02_vo/timing.json $D/mix_ep02_v2_qc.json
python /home/user/juicytea-media/engine/tools/audio_scan.py $D/mix_ep02_v2.json $D/mix_ep02_v2.wav audio/ep02_vo/timing.json $D/mix_ep02_v2_audio_scan.json
python -I $D/tools_v2/rests.py $D/mix_ep02_v2.json $D/stems_v2/music.flac --drop 12 --spot $D/spot_music.json
```

build_mix.py has four new optional arguments: `--music-sel`, `--sfx-sel`, `--music-ovr` and `--version`. With its defaults it
rebuilds `mix_ep02_v1.json` byte for byte. This was checked with cmp before and after the edit (`mixwork/v1_rebuild_pre.json`,
`v1_rebuild_post.json`).

## 3. Music: which takes and why

New takes were made with `tools_v2/gen_music.py`: the same request body, plan_for and file hash as engine/tools/music.py, one
attempt per cue and a budget guard on the seconds requested. There were 13 takes over three rounds: a probe, round 1 with timed
prompt wording, and round 2 with composition plans and short dynamics tags. Every take was measured with sfx_check.py music and
take_view.py against the criteria written before generating (NOTES_v2.md).

| Cue | v2 | Evidence |
|---|---|---|
| M13 payoff | **take3** (prompt), played from file 0.49 s; tail ride +15 dB from file 19.2-19.7 s | The hit is at file 0.52 s. In the mix the music starts at 679.06 and peaks at 679.12-679.14 (spot 679.09), 10-14 dB stronger than v1 in the first 0.1 s. Spread as generated is 10.4 LU; the file in the mix, with its tail ride, measures 6.1 LU (low section -18.1 against -22.4; `check_m13_tail.json`); v1 0.8. It softens at 695.4 for the reflection; v1 swelled to -21 dBFS in that pause at 696.5, the reverse of the brief. Take2 (plan) was rejected: it starts 1.33 s late and its energy is reversed. |
| M11 losses and graves | **take2** (prompt) | The hush (file 2.5-41.4 s) is still: its largest 0.25 s step is 0.96 LU (v1 1.32). A lift of about 2-3 LU comes only after it: it starts at file 42.0 = 565.87, after the hush ends at 565.37. The quoted 9.8 LU spread is mostly the end decay, so read it as a lift of about 3 LU. There is no "hopeful turn" at 597.93: the take decays into the Ch6 card. On the music stem the war-graves section stays at -43.0 and the lift sections sit at -39.7 / -38.9. |
| M04, M05 | v1 audio, rests filled (section 4) | |
| M01 cold open | **v1** | Take3 (plan) measured 12.8 LU, but that was its decayed tail; without the last section it is 4.6 LU and the low and mid labels swap. Its quietest full section is the opening, against a brief that asks for "light and bright from the first beat". In render r1 it thinned 2 s early and left a 2.75 s music trough (48.5-51.25) under "Usually, that's slow. Not". Take2 was flat and in B flat major. Take3 stays on disk as an alternate (`music_v2/gen/M01_cold_open_wonder_take3_4647c4db9d.mp3`). |
| M14 finale | **v1** | Pair rule with M01 (chroma r >= 0.9): take2 r 0.44 against M01 v1; take3 spread 3.5 LU with its energy order reversed. v1 with v1 keeps r 0.976. |
| M03 Pali | **v1** | Take2 has a +4-5 dB crescendo at file 15.5-18.5 s, on "strings open" (15.66), but sections otherwise flat (0.5 LU): not clearly better. Take3 flat. |
| M07 time machine | **v1** | Take2: energy reversed (quiet lift-off, big entry at 9.5 s). Take3: spread 2.8 LU, under the 6 LU bar, plus a new 2.5 s near-silence at file 21-23.5 s (film 336.5-339) under narration, and its entry comes 1.27 s before the Maui lift. |
| M09 Midway | **v1** | Take2 has near-silences at 27-35 and 36-44 s. In take3 the "bright and open" opening is the quietest section (-24.4 for 8.5 s), its energy order is flagged, and the broad low chord does not land. |

No level-ride dips were added, so the dips list is identical to v1. The film-wide contrast (R6) comes from M11 and M13; LRA stays
3.8 LU.

## 4. The three unplanned rests: filled and proved gone

`tools_v2/rests.py` marks a rest when 0.25 s frames sit 12 dB or more under the 12 s rolling median for at least 0.5 s. It excludes
planned dips, intended holes and cue fades, then classes each rest as card, xfade, pre_sync or unplanned. On v1 it finds exactly
the three reported rests (`rests_v1.json`).

`tools_v2/fill_rest.py` fills each rest by extending the cue's own music 8 beats earlier: it measures the local beat with librosa's
beat tracker and refines it by ±2 % with onset autocorrelation. The fill is crossfaded with equal power and shaped by a gain curve.
The output file has the same length, and every sample outside a patch is bit-identical to the original. norm_lufs keeps the v1
cue gain (M04 -16.014, M05 -16.222).

| Rest (film) | Cue, file region | Beat / shift | Lowest 0.25 s frame before -> after |
|---|---|---|---|
| 2:35.9-2:40.9 | M04 42.9-47.95 | 89.1 bpm, 5.335 s | -65.7 -> -30.5 dBFS |
| 3:41.8-3:46.9 | M05 40.4-45.47 (diminuendo held into the re-entry) | 95.7 bpm, 5.056 s | -53.2 -> -28.8 |
| 4:14.3-4:17.1 | M05 72.9-75.7 | 95.7 bpm, 5.050 s | -43.6 -> -31.8 |

Proof on the rendered v2 music stem:
- **rests.py** (`rests_v2.json`): 4 rests, and each one also appears in v1's list: 264.0 M05->M06 crossfade, the 314.75 and 435.5 chapter cards, and the 1 s breath before M08's storm swell at 413.87. Of v1's list, exactly the three unplanned rests are gone.
- **mix_qc music_holes** (music stem under -60 dBFS for 0.3 s or more): no entry that v1 lacks. v1's 158.0-160.5, 224.8-226.9 and 256.45-257.2 are gone.

The first render (r1) passed every gate but added two troughs that rests.py classed as "xfade": M01 take3 at 48.5-51.25 and the M13
take3 tail at 698.0-699.0. That class alone is therefore not proof, and the v1/v2 comparison by time is the acceptance test. M01 went
back to v1. The M13 tail sits at -36 dBFS in the file, but stacked normalisation (-4.1 dB), cue gain (-7) and duck (-12) pushed it to
-61 dBFS under "Now put the ocean back". `tools_v2/gain_patch.py` raised it +15 dB in the file, with a ramp from file 19.2-19.7 s. Its
music now sits at -45.1 dBFS over 697.8-699.2 (v1 -30.6). The patch lowered the file's gated LUFS by 0.646 LU, so norm_lufs -16.646
keeps the hit level.

## 5. Beds: denoise

`tools_v2/gate.py` is a spectral gate. It builds a noise profile from the 20th percentile per bin and applies it above 4 kHz with a
cosine ramp from 2 kHz: floor -18 dB, thresholds 3/9 dB, 5x5 smoothing, with no renormalising, so `level_vs_norm_db` and every bed
gain stay as v1.

| Bed | Hiss band 8-16 kHz p10 | Content 125-4k p90 | HF p90 / p98 | Verdict |
|---|---|---|---|---|
| amb_drained_seabed (5 uses) | -7.37 dB | -0.16 | -2.53 / -1.02 | pass, used |
| amb_dawn_lapping (1:16.6-1:33.3) | -6.46 dB | -0.06 | -3.20 / -1.91 | used. The HF p90 bound is 3.0, so this is a **miss** by 0.2 dB; its HF above 4 kHz is mostly hiss (r(LF,HF envelope) 0.35, HF flatness 0.38) |
| amb_rain_canyon | not gated | | | Its HF follows the rain (r 0.86 and HF flatness 0.09, like the clean surf 0.87 and lagoon 0.79 references), so there is no separable hiss floor. It was not regenerated. That was my call: the gate cannot separate anything here and the measurements show no hiss floor. About 3,570 credits of the 12,000 cap are unused if the owner wants a new take after listening |

The silence gate (-45 dB / 0.3 s) passes in the mix, including under the seabed during the 130.95-132.75 stop-down.

## 6. Sync proof: v1 and v2 specs compared

A recursive diff of `mix_ep02_v1.json` against `mix_ep02_v2.json` (`tools_v2/spec_diff_v1_v2.txt`) finds only these differences:
- six bed file paths (dawn x1, seabed x5 -> `_gated.wav`)
- four music file paths (M04, M05, M11, M13)
- raw_lufs (information only)
- norm_lufs for M04 (-16.014), M05 (-16.222) and M13 (-16.646)
- the M13 file offset 0.49 (start, end and fades unchanged)
- `version`

Every SFX and bed `t`, `src_in`, `dur` and `t_out` is unchanged, and so are every dip, every music start and end and `marker_check_s`.
No dips were added. The narration input is the same file at gain 0. After the master stage the voice stem differs from v1 only by
the loudness gain (-0.012 dB) and by limiter gain in 16 of the 100 ms windows (at most 0.3 dB, at 546-548 and 679-694).

## 7. QC, v1 against v2

| Check | v1 | v2 | Rule |
|---|---|---|---|
| Integrated (mix_qc and ffmpeg ebur128) | -14.0 | -14.0 | -14 ±0.5 |
| True peak | -1.7 | -1.7 | <= -1.0 (playbook), mix_qc <= -1.5 |
| LRA | 3.8 | 3.8 | 3-6 (R6) |
| Silence -45 dB / 0.3 s (mix_qc and ffmpeg silencedetect) | none | none | none |
| Voice over music p10 / median | 19.0 / 21.7 | 18.9 / 21.7 | >= 15 / 17-23 |
| Voice over ambience p10 | 18.5 | 18.5 | >= 15 |
| Worst sentence, voice over music | 16.6 | 16.7 | >= 12 |
| 1-4 kHz windows under 15 dB | 4.2 % (113) | 4.4 % (119) | <= 5 % |
| 1-4 kHz windows newly under 15 dB / no longer under | | 11 / 5 (10 new at 683.8-693.9, after the M13 hit) | info (`band_diff_v1_v2.txt`) |
| Duck pumps per minute | 1.61 | 1.61 | <= 2 |
| Reveals, hush, comic, density, repeats | pass | pass | |
| Limiter max GR (at 679.14-679.25) | -1.80 | -1.87 dB | |
| audio_scan: masking / sfx_loud / dead_air / clicks / early ends | 33 / 0 / 0 / 0 / 0 | 32 / 0 / 0 / 0 / 0 | no new masking window, one gone (694.5) |
| Phone check, 7 hero hits over music+amb | | same or better (tall56 +15.9 against +15.2) | |

## 8. M13 hit checks (679.0-680.5)

- **Music onset**: 679.06, peak 679.12-679.14. The downbeat is within 0.05 s of the spotted 679.09 and lands with impact_deep and payoff_boom.
- **1-4 kHz voice margin over "tall."** (679.09-680.05): 15.1 dB against all background on a whole-word average (v1 23.9). That is **at** the playbook's 15 dB line, inside measurement noise, so it is not a clear pass. By mix_qc's 100 ms windows, the two windows it counts on the word (679.1, 679.2) have 22.4 and 16.5 dB (v1 56.9 and 45.8). The soft end of the word (679.3-679.9, not counted because the voice there is more than 10 dB under its median) went from 3.6..14.8 dB in v1 to -11.7..+2.2 dB: the "-ll" decay sits under the hit. The phone proxy (mono, 250 Hz high-pass) gives 14.7 dB over the whole word (v1 14.3) and 23.7 dB over its first 0.3 s (v1 29.5).
- **Narration after the hit (683.8-693.9)**: ten 100 ms windows fell under 15 dB that were above it in v1, on "Everest." (x2), "Stand", "that", "base,", "still", "underwater." (x2), "mountain" and "you", with margins 6.1-12.1 dB against v1's 16-43 dB. Two of them (689.6, 693.7) are new under-10 dB runs in mix_qc. The cause is spectral: on the music stem take3 is 1-5 dB quieter than v1 broadband but carries 20-30 dB more energy at 1-4 kHz (about -51 dBFS per second against v1's -56 to -82). The per-second voice margin there is still 23-25 dB, the sentences pass (worst 16.7 LU), and the film-wide band gate passes (4.4 % of 5 %). A -1.5 dB trim on M13 would not close these windows; a 1-4 kHz cut of about 6 dB on M13 from 681 to 695 would. mix.py has no per-cue EQ, so that would be an in-file edit with gain_patch-style tooling and a re-render. (`tools_v2/band_diff_v1_v2.txt`)
- **Limiter**: max -1.87 dB over 0.11 s at 679.14-679.25 (v1 -1.80 dB over the same run).

## 9. For the owner to listen (no ear verdict claimed)

Listening copy: `deliver/ep02/hawaii_hang_elozetes_v2.mp3`.
1. 2:35-2:41, 3:41-3:47 and 4:14-4:17: the music continues through the three former gaps. Does the loop seam sound musical?
2. 8:44-10:02 (M11): does the hush stay still under the losses and graves, and does the gentle lift come only after 9:25?
3. 11:18-11:41 (M13): the hit on "tall", then the soft reflection. Is "tall" still clear on a phone, including the end of the word? Are "Everest ... Stand on that base ... still underwater ... a mountain you" (11:23-11:34) clear over the brighter music? If only "tall" is crowded, the first fix is about -1.5 dB on M13; if the lines after it are, a 1-4 kHz cut of about 6 dB on M13 under 11:21-11:35.
4. 11:36-11:40: the soft M13 tail under "Now put the ocean back" (raised in the file).
5. Beds: 1:16-1:33 (dawn lapping) and 2:10-2:43 (drained seabed) against v1, for less hiss and no "breathing".
6. Optional: M01 take3 as an alternate cold open (quiet start, a build to 0:15, a big stop-down). It is not in v2.

## 10. Open items

- M01, M03, M07, M09 and M14 are still flat by section (v1 audio). Of the 10 new takes for these cues (two each), none was clearly better. A next round should use one cue per call with a single dynamics change placed at a time, and be judged on the rendered stem.
- M11 has no "hopeful turn" at 597.93.
- The dawn bed's HF p90 is 0.2 dB past the gate bound (section 5).
- The 412.5-413.5 one-second breath before M08's storm swell is unchanged from v1 (classed pre_sync).
- When the chapter renders exist, re-sync to the render's event log and rebuild. The spec's times are identical to v1, so the picture made on spot_notes section 10 still matches.
- The "tall" 1-4 kHz margin is at the 15 dB line (15.1 dB, v1 23.9), and ten narration windows after the hit (683.8-693.9) are under 15 dB (section 8). Remedies: -1.5 dB on M13 for "tall"; a 1-4 kHz cut of about 6 dB on M13 at 681-695 for the lines after it. The owner decides after listening.
- The rain bed is unchanged by my call (no separable hiss, section 5). About 3,570 credits of the 12,000 cap are unused if a new take is wanted.
- All media (mix, stems, new takes, gated beds, listening copy) exist only in the scratchpad, which a cleanup can clear. Hand them to the owner outside git.
- The playbook DO/DONT lists, LESSONS_LOG.md and the episode README are not updated by this pass; the lessons are in section 12 for the orchestrator.
- Nothing was uploaded, published or posted.
- About 33,909 credits are left until 1 Dec (counter 87,218 / 121,127).

## 11. Credits

| Read (credits.log) | Used | Note |
|---|---|---|
| v2_before 01:19:22 | 78,786 | |
| v2_after_round1 01:42:36 | 84,252 | +5,466 against 5,446 by seconds |
| v2_after 02:04:32 | 87,218 | **+8,432** in total: an upper bound, because the account is shared |

By seconds requested: 8,402 credits over 13 takes (`music_v2/gen/budget.json`, 13.7 credits/s). No SFX were regenerated.

## 12. Lessons (for the playbook)

Worked:
- **Beat-aligned loop extension inside the cue file** removed all three unplanned rests without moving a sync, a dip or the cue gain. It uses librosa beat_track at hop 512, the median beat interval over the 14 s before the rest, a ±2 % autocorrelation refine and a shift of 8 beats; norm_lufs compensates the gain. (`fill_report.json`, `rests_v1.json`, `rests_v2.json`)
- **A gate on stationary hiss above 4 kHz** (20th-percentile profile, floor -18 dB) dropped the hiss floor 6.5-7.4 dB with content within 0.2 dB. Decide first whether the HF is hiss: an LF/HF envelope correlation of about 0.3 means hiss, about 0.8 or more means the sound itself. (`gate_*.json`)
- **Timed prompt wording** for a cue that must hit on its first frame beat the composition plan: M13 take3 put the hit at file 0.52 s, while take2 (plan) came in 1.33 s late. (`check_probe.json`)
- **Budget by seconds requested** (13.7 credits/s, one attempt per cue, a guard file) tracked the account counter within 0.4 %.
- **New build options with a byte-identical v1 rebuild check** keep the old mix reproducible.

Failed:
- **A spread number on its own picked the wrong take.** M01 take3's 12.8 LU was its end decay (4.6 LU without it), and the take left a 2.75 s trough under narration. Read the spread without the last section and check where the quietest section sits. (`check_r2.json`, `NOTES_v2.md` render r1)
- **"Unplanned: 0" from the rest classifier was not proof**: a new trough at a cue edge passes as "xfade". Compare v2's rest list and mix_qc's music holes with v1 by time.
- **A soft passage that measures fine in the file** (-36 dBFS) fell to -61 dBFS in the mix through stacked normalisation, cue gain and duck. Render before accepting a take. Raising a soft passage also lowers the file's gated LUFS (-0.65 LU here), so recompute norm_lufs after any in-file edit. (`gain_report.json`)
- **ElevenLabs music does not follow section-level dynamics reliably.** 6 of the 10 takes for the five cues kept on v1 placed their contrast in the wrong section or added near-silences (M01 t3, M07 t2/t3, M09 t2/t3, M14 t3); the other four were flat or failed the M01/M14 pair rule. Plan 2-3 takes per cue and keep v1 as the fallback. (`check_r1.json`, `check_r2.json`)
- **A brighter take moved the voice margin, and the gate percentage hid it.** M13 take3 is 1-5 dB quieter than v1 broadband but 20-30 dB louder at 1-4 kHz, so ten narration windows after the hit fell under 15 dB while the film-wide band gate moved only from 4.2 % to 4.4 %. Compare the band windows with the previous mix by time (`tools_v2/band_diff.py`), and check a new cue's 1-4 kHz level under the narration it sits under, not only its loudness. (`band_diff_v1_v2.txt`)
- **The first loop-period estimate (onset autocorrelation, beat_track at hop 128) read 120/126 bpm** and copied a hit into the fill. Use beat_track at hop 512.
- **A section median on the music stem is contaminated by overlapping cues** (M14 enters inside M13's last section), so judge a section's energy on the file and confirm the transitions on the stem.
