# Mix v2 checkpoint (sound finisher, started 2026-11-22 01:19 UTC)

Python: scratchpad venv/bin/python (pyloudnorm, soundfile, scipy, librosa, faster_whisper). No noisereduce (own spectral gate).
Credits (credits.log, used/limit): v2_before 78,786 / 121,127 (42,341 left). Budget 12,000 -> hard stop at used 90,786.
Budget is tracked by SECONDS REQUESTED x 13.7 (music) / x 11 (sfx) in music_v2/budget.json (the counter lags 30 s+).
Disk at start: 5.1 GB free. Pack stems to FLAC, delete WAVs.

## Plan
1. Probe: M13 (plan + prompt) and M03 (plan) first; measure with sfx_check.py music; roll the wording that works to M01 M07 M09 M11 M14.
   One cue per call, own outdir music_v2/<run>/, single attempt (tools_v2/gen_music.py, imports music.plan_for).
2. Fill rests by same-length in-file patch (M04 file ~43-48 s, M05 ~40.5-45.5 and ~71-75.8): music_v2/*_filled.wav.
   Detector (tools_v2/rests.py) must find exactly the three on stems_v1/music.flac, zero on v2.
3. Beds: own spectral gate. Only dawn_lapping shows a hiss floor (flat 8-16 kHz, flatness 0.38); seabed/rain look like clean refs.
4. build_mix.py: new optional args only (--music-sel --sfx-sel --version --music-ovr); defaults must rebuild v1 json byte-identical.
5. Diff v1/v2 specs: every sfx/amb t, src_in, dur, t_out, dips, music start/end, marker_check_s identical; only files differ.

## Acceptance criteria (written before generating)
- Every take: voice check vad < 1 s, holes_in_window empty, not ends_early (M14 natural end >= 47.8 s + offset).
- M13: onset at file 0-0.2 s (trim lead so downbeat at 0); first 0.5 s peak vs cue median >= 6 dB (v1: 3 dB); softens after ~15.8 s.
  Mix check 679.0-680.5: 1-4 kHz voice margin on "tall", limiter GR.
- M11: file 0.4-41.4 s = Midway hush: no onset/level step (>= 3 LU per 0.25 s) there; contrast only after file 41.5 s.
- M03: judge the pizzicato -> strings change near file 11.9 s (spectral/timbre change + level step), not spread.
- M01/M14: decided as a pair; chroma r(M01, M14) >= 0.9 (v1 0.93) or keep both old.
- Others: section spread >= 6 LU with label order, more sync landings than old, spectral flatness not worse, key/tempo per brief.
- Beds: hiss-band (8-16 kHz) p10 floor drop >= 6 dB, p90 content in 125-4000 Hz within 2 dB, no renormalising.
  Seabed/rain: if the gate cannot meet this without eating the bed -> regenerate (reserve ~1,000 credits, sfx_gen.py).

## Done and verified
- tools_v2/rests.py (drop 12 dB vs 12 s rolling median, >= 0.5 s, classified card/xfade/pre_sync/unplanned):
  v1 stem -> 7 candidates, exactly 3 unplanned (156.25-160.75 M04, 225.25-226.75 M05, 256.5-257.0 M05) = tools_v2/rests_v1.json.
  Others: 264.0 xfade M05->M06, 314.75 + 435.5 chapter cards, 412.5 M08 1 s pre-swell breath before sync 413.87 (left as is, report it).
- Rest fills (tools_v2/fill_rest.py, music_v2/fill_cfg.json -> fill_report.json): 8-beat loop extension (librosa beats, ac-refined),
  M04 42.9-47.95 (shift 5.335 s, min -65.7 -> -30.5 dBFS, section level), M05 40.4-45.47 (5.056 s, diminuendo to -28, -53 -> -29),
  M05 72.9-75.7 (5.050 s, prev phrase tail, -43.6 -> -31.8). Files music_v2/M04_..._filled.wav, M05_..._filled.wav (float WAV, same
  length, samples outside patches bit-identical to the ffmpeg decode). norm_lufs override to keep cue gain: M04 -16.014, M05 -16.222.

- Beds (tools_v2/gate.py, sfx_v2/): r(LF,HF env) dawn 0.35 (independent stationary HF floor = hiss), seabed 0.30 (HF drips,
  std 3.2 dB), rain 0.86 (HF is the rain, like clean refs surf 0.87 / lagoon 0.79).
  dawn gated (flo 4k, floor -18, thr 3/9): 8-16k p10 -6.5 dB, 125-4k p90 -0.06, HF p98 -1.9 (HF p90 -3.2: HF is mostly hiss).
  seabed gated same settings: -7.4 dB floor, content -0.16, HF p90 -2.5, p98 -1.0 -> sfx_v2/*_gated.wav (+ gate_*.json).
  rain: gate cannot separate (HF p90 -3.3, p50 -4); NOT gated; regenerate only if budget allows after music (sfx_gen.py).
- Music probe (music_v2/gen, budget.json by seconds): 1,040 credits. M13 take2 plan FAIL (starts 1.33 s late, energy reversed).
  M13 take3 prompt (timed wording) ACCEPT candidate: spread 10.4 LU (v1 0.8), hit at file 0.52 s (pre-swell 0.12-0.5) ->
  offset 0.49 puts the downbeat on 679.07; softens at file ~16.8 = film ~695.4 (end of "never get to see.", 2.3 s pause).
  M03 take2 plan: strings open ~16 s with +4 dB swell (v1 flat, change ~18 s); modest. Lesson: timed prompt wording > plan.

- Round 1 (prompt, timed wording; check_r1.json), counter after: 84,252 (+5,466 vs 5,446 by seconds):
  M01 t2 REJECT (flat, Bb major), M14 t2 spread 5.4 but chroma r with M01 v1 0.44 (pair rule) -> keep M01+M14 v1 (r 0.976) unless a
  pair passes; M07 t2 REJECT (energy reversed: quiet lift-off, big entry at 9.5 s), M09 t2 REJECT (near-silence 27-35 and 36-44 s),
  M11 t2 ACCEPT candidate (hush 2.5-41.4 dead still, max step 0.96 LU vs v1 1.32; +2-3 LU lift after 41.5; decays from 71 s to the
  Ch6 card; no hopeful turn), M03 t3 REJECT (flat). M03: t2 marginal (+5 dB crescendo at 15.5-18.5 on "strings open" 15.66).

- Round 2 (plan mode, concise dynamics tags; check_r2.json), by-seconds total 8,402 credits (counter not yet re-read):
  M01 t3: spread 12.8 LU, order ok, D major, chroma r with M14 v1 0.968 (pair rule passes); 0-15 s quiet (-21..-23 file dB), jump at
  15.0 (0.77 s before the -24 stop-down dip at 15.77), accents at 30/35/40/42.5/45, thins 45-50 to -41 (M02 enters 50.43). No sync
  lands (v1: none either); stop-down found at 15.75 (step -1.3). First 0.5 s 1.2 dB over median (v1 6.9): the hook is ~4 dB quieter.
  M14 t3 REJECT (spread 3.5, order reversed). M07 t3 REJECT (spread 2.8 < 6; NEW 2.5 s near-silence at 21-23.5 = film 336.5-339 under
  narration; entry 1.27 s before the Maui lift). M09 t3 REJECT (opening 'bright and open' section is the quietest, -24.4 for 8.5 s,
  order flagged; broad low chord not landing).

## Decisions (final selection for v2)
- M01 take3 (with M14 v1; flag to owner: listen 0:00-0:52 vs v1, quieter hook, jump at 0:15).
- M11 take2, offset 0 (lift starts at file 42.0 = film 565.87, after the 565.37 hush end; v1 lead was 0.64 s too).
- M13 take3, offset 0.49, fade_in 0.02 (downbeat at ~679.07).
- M04, M05: v1 audio with rest fills (norm_lufs -16.014 / -16.222).
- Keep v1: M03 (t2 +4-5 dB crescendo on 'strings open' only, not clearly better; t3 flat), M07, M09, M14. No level-ride dips
  added (film-wide R6 contrast comes from M01/M11/M13; keeps the dips list identical to v1 for the sync proof).
- Beds: dawn + seabed gated; rain NOT changed and NOT regenerated (HF flatness 0.09 vs dawn 0.38, r(LF,HF) 0.86: HF is the rain).

## Open / next step
- Build v2: music_v2/selected_v2.json + sfx_v2/selected_v2.json; build_mix.py optional args (v1 byte-identical check);
  mix.py render + stems (FLAC); mix_qc, audio_scan, phone check, silencedetect, rests.py zero unplanned, spec diff v1/v2,
  M13 679.0-680.5 check; then reports + credits after.
- [done 2026-11-22] build_mix.py: optional --music-sel --sfx-sel --music-ovr --version; defaults rebuild mix_ep02_v1.json byte-identical
  (cmp before and after the edit: mixwork/v1_rebuild_pre.json, v1_rebuild_post.json). mix_ep02_v2.json built from
  music_v2/selected_v2.json, sfx_v2/selected_v2.json, music_v2/music_ovr_v2.json. Spec diff v1 -> v2: only files, raw_lufs (info),
  norm_lufs M04/M05, M13 offset 0.49; every t, src_in, dur, t_out, dip, music start/end, marker_check_s identical.
- [render r1 2026-11-22] mix_ep02_v2.wav (first render): all 16 mix_qc gates pass, but two NEW troughs vs v1: 48.5-51.25 (M01 t3 thins
  2 s early, under "Usually, that's slow. Not") and 698.0-699.0 (M13 t3 soft tail -36 dBFS file, pushed to -61 by norm -4.1, cue gain -7,
  duck -12, under "Now put the ocean back"). rests.py classed both 'xfade' -> classification alone is not proof.
  Fix (advisor): M01 back to v1 (t3's 12.8 LU was the decayed tail: 4.6 LU without it, low/mid order flipped, quiet opening = hook;
  t3 listed as alternate). M13 t3 tail lifted +15 dB in-file (tools_v2/gain_patch.py, music_v2/gain_cfg.json -> gain_report.json;
  file 19.2-19.7 ramp, outside bit-identical; norm_lufs -16.646 keeps the hit level). Dips list stays identical to v1.
  Proof rule now: v2 rest list and mix_qc music_holes must have no entry v1 lacks (compare by time), not just 'unplanned: 0'.
  Dawn gate: HF p90 drop 3.2 > 3.0 limit -> pass=false in gate json; report as a miss (HF is mostly hiss there), still used.
  M11 t2: 9.8 LU spread is mostly the end decay; report as ~3 LU lift after the hush.
- [render r2 2026-11-22, VERIFIED] mix_ep02_v2.wav: 16/16 mix_qc gates pass (-14.0 LUFS, -1.7 dBTP, LRA 3.8, band 4.4 %, pumping 1.61).
  mix_qc music_holes: no entry v1 lacks; v1's 158.0-160.5, 224.8-226.9, 256.45-257.2 gone. rests.py (tools_v2/rests_v2.json): 4 entries,
  all present in v1 (264.0 xfade, 314.75 + 435.5 cards, 412.5 pre-swell); the 3 unplanned v1 rests gone.
  Next: M13 hit check (onset, 1-4 kHz margin on "tall", limiter 679-680.5), audio_scan, phone_check, ffmpeg silencedetect/ebur128,
  pack stems to FLAC, reports, credits read.
- [checks 2026-11-22, VERIFIED] M13 hit: music onset 679.06, peak 679.12-679.14 (spot 679.09), music 10-14 dB stronger than v1 in the
  first 0.1 s; "tall" 1-4 kHz voice margin 15.1 dB (v1 23.9; gate 15: tight), phone proxy over the word 14.7 (v1 14.3), first 0.3 s 23.7
  (v1 29.5); limiter max GR -1.87 dB at 679.14-679.25 (v1 -1.80 same run). Tail 697.8-699.2 music -45.1 dBFS (r1 -61, v1 -30.6).
  phone_check_v2.txt: all 7 hero hits same or better. ffmpeg: no -45 dB/0.3 s silence, I -14.0, LRA 3.8, TP -1.7.
  Narration input identical (same vo file, gain 0); vo stem differs only by master gain (-0.012 dB) and limiter (16 x 100 ms windows,
  max 0.3 dB, at 546-548 and 679-694). Stems packed to FLAC (lossless verified), WAVs deleted.
  Credits: v2_after 87,218 -> delta 8,432 vs v2_before (by-seconds 8,402; upper bound, shared account). 33,909 left.
  Next: audio_scan result, mix_report_v2.md, hang_hu_v2.md, copy json/md to repo audio/, advisor, StructuredOutput.
- [reports 2026-11-22, DONE] mix_report_v2.md, hang_hu_v2.md written; listening copy deliver/ep02/hawaii_hang_elozetes_v2.mp3.
  Copied to repo: longform/ep02-hawaii/audio/{mix_report_v2.md, hang_hu_v2.md, mix_ep02_v2.json, mix_ep02_v2_qc.json}, audio/v2/ (evidence
  json/txt, NOTES), tools/sound_v2/ (scripts). build_mix.py edited (optional args). Not committed (orchestrator saves the repo).
  Next: advisor final check, then StructuredOutput.
- [final review 2026-11-22, DONE] Advisor review: text fixes only, r2 render ships as is. Recounted: 10 takes for the five cues kept on v1
  (6 with misplaced contrast or near-silences). M13 spread re-measured on the mixed file (tail ride): 6.1 LU (as generated 10.4;
  music_v2/check_m13_tail.json). Band windows v1 vs v2 by time (tools_v2/band_diff.py -> band_diff_v1_v2.txt): the two counted "tall"
  windows 22.4/16.5 dB (v1 56.9/45.8), the soft word end 679.3-679.9 now -11.7..+2.2 (v1 3.6..14.8); 10 NEW windows under 15 dB at
  683.8-693.9 (6.1-12.1 dB, v1 16-43; take3 is 20-30 dB brighter at 1-4 kHz, 1-5 dB quieter broadband); gate still 4.4 %. Reported as
  owner's call with remedies (-1.5 dB M13 for "tall"; ~6 dB 1-4 kHz cut on M13 at 681-695). "tall" margin worded as "at the line".
  Rain bed: stated as my call, ~3,570 credits of the cap unused. hang_hu_v2.md and mix_report_v2.md corrected and re-copied to the repo.
  Next: StructuredOutput (no commit; the orchestrator saves the repo).
