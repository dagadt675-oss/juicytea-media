# final_ep02_tc checkpoint (packaging lead, ep02 Test & Compare)
Started 2026-11-22. Do not commit/push (orchestrator saves). Outputs go to longform/ep02-hawaii/release/.

## Done and verified
- Playbook, packaging_playbook, round2/3, feedsim README, SOURCES (img + data + ch LICENSE) read.
- Chapters (floor of card times, engine timing.json and mix agree): 0:00 Only the Top / 1:33 Oʻahu’s Missing Side / 3:01 The Island Stands Up / 5:15 Watch It Grow Old / 7:15 Fought Over a Volcano / 9:58 We Haven’t Hit Bottom. Film 746.93 s (12:26).
- Film frame 0 (renders/scan1/f000000.jpg, ch1 only, 1280x720) vs final_ep02_1.jpg: masked SSIM 0.948 (full 0.838). P2 holds.
- final_ep02_1 has horizon artefacts (white streaks at the left horizon over Maui, dark smudges on the right horizon) that the film frame 0 does not have.

## Plan
- A = NO OCEAN (frame 1). Option: re-render d3 plate (fix_noocean/work/r/queries.json d3, lab_hawaii.html) at 2560x1440 with the 8192 hero colour, rebuild with fix_noocean/tools/build.py cand_2 cfg; or film frame 0 clean plate. Must keep masked SSIM >= 0.94 vs film frame 0.
- B = ONE ISLAND (film ch1 ~f560-640, Maui Nui at -400 ft), no gauge.
- C = look-down plunge (film ch1 ~f900-1180), new concept (YOU ARE HERE retired 0/10).
- Everest gag avoided (packaging playbook P3, clone kit).

## Next step
- Look at renders/scan1 contact sheet (rstill.sh scan running), pick B/C frames, call advisor.
