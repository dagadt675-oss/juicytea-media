# ep02 engine integrator: promote r3 shader + integrate_todo engine items (2026-11-22)

F = scratchpad/research/ep02/finish ; G = F/gate/www (gate tree: live + hterrain_r3 + shared_r3 + patch.grid, all else symlinks)
H = F/gate/wwwH (G + step-4 edits: shared.js, lab/type/type.js, ch1.js, ch3.js, ch4.js, tools/texel_audit.js); F/gate/base4 = the
pre-edit copies (shared.js = 46172b07 patched base, ch1 81947b2b, ch3 c0a94b11, ch4 bfd50fac, type.js 548f8a6f, texel_audit 7b931aa8).

## Done / verified
- Live bases unchanged at start (hterrain 35e24a9d, shared 0b0cc852, regions.json 80114d52); promote_r3.sh --dry passes.
- G built, md5s 04240615 / 46172b07 / regions.json 3d4891a9 (grid set).
- Gate (a) on G: G_f0 frame1_check --mask-label SSIM320 0.944 (full 0.850, luma 104.3), GPU 143.8 s.
- Step-4 edits written in H (NOT live yet), node --check OK, diffs read:
  shared.js hub.terrain stack/noDetail + doc comment; line ~291 comment (hero colour 8192^2, HLS box); ui.number lead0: no ghost 0
  (vis(base) ramp = incoming 1's alpha; minus + comma follow); ui.label passes sync:true;
  type.js label o.sync (opt-in): nothing before p 0.3, plate wipes p 0.3-0.6 with the text, leader 0.3-0.75, text curve unchanged;
  ch1 STAGE_ND = {...CH1_STAGE, noDetail} on ch1-demo + ch1-ice; ch4 Maui leg spec.stage {noDetail:true};
  ch3 mkShot set detAmt 0 in the whips; texel_audit colSrcM: bigisland 30 m inside meta.json colour_refine boxes else 250.

## Running
- queue F/gate/q1.txt (queue_f.sh, log F/gate/queue.log): G vs L (live) f0, ch2 3067w,3067,2889,3148,3376,5097; ch4 10320w,10320,
  9803,10290,11742; ch3 7274w,7274,6432,8769,8890; ch1 1089,1526; ch5 13380,13160; ch6 18200,20453,20800,21150,21600.
  Another run renders ch1 packaging stills continuously; queue allows one other still.cjs + MemAvailable >= 5 GB.

## Open / next
1. When q1 done: SSIM/diff triage, crops + 390 px sheets, GPU table (3067, 3376, 10320 gpu_step). Proof: G vs L must differ at 3067.
2. Promote (only when no Chromium of mine runs) -> verify md5 + grid; move .bak_r3* out of the repo (keep path for rollback).
3. Copy H step-4 files to live after checking live == base4 md5s; then step-4 stills on live (q2): ch1 0, 560-640 ONE ISLAND, ice->ride
   cut TC +-2 frames, ch4 10214-10218 MAUI + 10240/10271 GPU, ch3 7396-7399 + 7398 GPU, ch2 gauge 3712-3761, label onsets 4 frames,
   ch3 counter roll frame; texel audit before/after.
4. API.md: draft in F/gate/API.md.draft (base copy API.md.base 25a6fdc2; api_edit.py = 6 unique replacements: stage opts,
   uniform reset note, close-up round 3 paragraph (@F1@ placeholder = final frame-1 SSIM), noDetail per shot, ui.label sync,
   ui.number lead0); cost-table rows still to add from gate numbers; copy to live with the step-4 files. Final frame-1 check after step 4.
5. ch1 noDetail covers frames 0 .. TC 744 (ch1-demo + ch1-ice), NOT 0-615. Watch RSS: island() keeps the CH1_STAGE stage alive too.
6. Backups from promote: hterrain.js.bak_r3 is NOT git-ignored -> move all .bak_r3* to F/gate/bak/ (rollback source).

## Gate results (L = live, G = r3 tree), GPU-process CPU s per still (frames_gpu gpu_step), SSIM full
- f0: G 143.8 / L 141.7; frame1_check SSIM320 G 0.944 (L 0.944).
- ch2 (cmp/ch2_f*.jpg; zooms cmp/ch2_3067_shore2x.png, ch2_3148_steep2x.png):
  3067 warm 187.1 -> 182.5, SSIM 0.976: drained-lagoon foam speckle field gone (r3 clean shallow water), outer rim same; steep face finer.
  2889 196.4 -> 190.3, 0.977 (same lagoon fix); 3148 190.9 -> 182.4, 0.975 (steep face: live smeared crown blobs, r3 finer, PASS);
  3376 118.0 -> 88.4 (-25 %, patch.grid), 0.970, mesh-scale only; 5097 surf coast 63.6 -> 62.6, 0.994: stepped glow bands -> thin rim.
- ch4 (cmp/ch4_f*.jpg, zoom cmp/ch4_9803_cliffrim2x.png): 10320 warm 108.8 -> 86.3 (-21 %), SSIM 0.961, 10290 168.5 -> 145.8, 0.969:
  white foam stripes on the reef flats / Pearl Harbor gone (r3 = shallow grey-olive water with a thin rim), PASS; 9803 sea cliff
  125.8 -> 139.5 (+11 %, foam-on, noise band per r3 notes), 0.990, sea line crisper and continuous, cliff face = live; 11742 Lalo
  74.3 -> 76.3, 0.9999 (identical).
- ch3 (cmp/ch3_f*.jpg): 7274 Everest summit warm 78.5 -> 80.1, SSIM 0.991: finer rock grain on the sunlit steep face, PASS;
  6432 drained 93.3 -> 89.1, 0.963: thinner rim, fewer stepped glow segments; 8769 refill coast 107.5 -> 108.5, 0.990: white speckle
  foam off the shallow point gone; 8890 drained seabed 98.7 -> 101.2, 0.970, grain only. All PASS.
- ch1 (cmp/ch1_f*.jpg): 1089 drained ride 97.7 -> 99.7, full SSIM 0.833 BUT only the per-pixel sediment grain phase differs (the near
  seabed noise is resampled where the mesh diagonal moved the surface; mad 2.9, max 69, no structure change): visually equivalent, PASS
  (r3 notes: "1089 full frame equivalent"). 1526 sea cliff / ground 275.5 -> 283.5 (+3 %), 0.984, equivalent.
- ch5 (cmp/ch5_f*.jpg, zooms ch5_13160_flats2x.png, ch5_13380_horizon2x.png, ch5_13380_ground2x.png): 13160 Midway 97.6 -> 100.6
  (+3 %), SSIM 0.973: live's white texel-stipple foam blotches on the lagoon flats gone; r3 = pale turquoise lagoon, the flats next to
  Sand Island read olive (seabed colour). PASS (foam artefact removed; a whiter sand flat would be a chapter colour choice, not foam).
  13380 albatross ground (NOT a globe hand-off: that is tD1 ~444.4-445.95 s) 82.5 -> 80.5, 0.985: far-lagoon sparkle dashes ~ live's
  streaks, ground equivalent. Globe -> terrain hand-off frames 13340/13355/13368 queued as q3 (G vs F/gate/wwwL = frozen pre-promote
  live copy: hterrain 35e24a9d, shared 0b0cc852, regions.json 80114d52), ch5dbg logs tD1.
- ch6 (cmp/ch6_f*.jpg): 18200 118.3 -> 116.3, 0.995; 20453 payoff cut face 71.3 -> 71.5, 0.9975 (cut face + sea line identical);
  20800 70.0 -> 70.4, 0.998; 21150 drained 79.5 -> 92.3 (+16 %), 0.941, rim thinner/crisper; 21600 refill 73.1 -> 77.2, 0.984. PASS.
- Phone size (390 px pairs, cmp/phone390_water.jpg 18 pairs, cmp/phone390_steep.jpg 4 pairs): L and G read the same at phone size
  (no new artefact, no lost coast line, labels identical); the r3 differences are below phone resolution. PASS.
- Verdict 02:13: every part passes (water, steep, mesh, patch.grid); nothing switched off (foamW 40 / steepAmt 1 stay on).
- (d) heavy frames GPU s live -> r3: 3067 187.1 -> 182.5, 3376 118.0 -> 88.4, 10320 108.8 -> 86.3.
- q2 started 02:09:30 (H vs G): H_f0 gpu 108.8 (G 143.8; noDetail on ch1-demo).

## 02:12 PROMOTED (live now = r3 + step 4)
- promote_r3.sh rc 0: hterrain 04240615, shared 46172b07, regions.json 3d4891a9, oahu_windward patch.grid [640, 504] in
  data/regions.json + tools/regions_spec.json. Backups moved OUT of the repo to F/gate/bak/ (rollback: copy back
  hterrain.js.bak_r3 35e24a9d, shared.js.bak_r3 0b0cc852, regions.json.bak_r3_patchgrid 80114d52, regions_spec.json.bak_r3_patchgrid b6e0b5ac).
- Step 4 copied H -> live after live == base4 check: shared 1d74b47c, type.js ee44df63, ch1 9cbc5d8c, ch3 f85335a3, ch4 b1a16ed0,
  texel_audit e243312b; node --check OK on all; live diffs read (no code after //). Rollback = F/gate/base4 copies.
- Gate trees stay frozen (real copies): G = www, H = wwwH, L = wwwL; q2/q3 unaffected by the promote.
- Final frame 1 (H_f0 = r3 + step 4): frame1_check --mask-label SSIM320 0.944 (full 0.850, luma 104.3 vs ref 101.4), same as G and L.
  H vs G frame 0: SSIM 0.9998 (far East Molokai, no visible change); GPU 143.8 -> 108.8 s (-24 %, ch1-demo noDetail).
- Other files in git status (build_mix.py, audio/v2, release/, sound_v2) belong to the sound/upload run, not to this step.
- q2 ch4 (G4 = r3, H4 = r3 + step 4; cmp/s4_ch4_*.jpg, cmp/s4_ch4_maui_onset.jpg): Maui leg noDetail GPU s per still 10240 149.6 -> 102.2
  (-32 %), blurred 10271 730.5 -> 490.9 (-33 %), 10212-10216 ~144 -> ~110 (-24 %); job total 1758.9 -> 1264.1, GPU-process RSS 1582 -> 1251 MB.
  Picture: 10240 SSIM 0.9999, 10271 0.9975 (only inside the motion blur on Molokai), same framing. MAUI onset: r3 shows an EMPTY plate at
  10212-10213; step 4 shows nothing at 10212-10213, the plate wipes open with "M" at 10214, full at 10215, 10216 identical. PASS.
  ch4.js comment numbers replaced with the measured ones (live + H md5 88981417).
- q2 ch1 (cmp/s4_ch1_*.jpg): FAIL at 600 (ONE ISLAND, ch1-demo): without the patch the near East Molokai slope loses its gullies
  (crop SSIM 0.76, visibly softer). 700 (ice) SSIM 0.9999, 742-745 bit-identical (cut unchanged). GPU 600 193.6 -> 138.9, 700 111.3 -> 102.0.
  RSS with two ch1 stages: GPU process 1544 -> 1786 MB, renderer 1666 -> 1846 MB.
  FIX 02:40: ch1-demo back on CH1_STAGE (full detail), noDetail kept only on ch1-ice (TA = frame 640 .. 743); comment rewritten.
  Live ch1.js + H copy updated, node --check OK. q4 (after q3): live ch1 600/639/640/660 vs G 639/640/660 + live ch2 3738 bit-compare vs H.
- q2 ch2 gauge (cmp/s4_ch2_gauge.jpg, s4_ch2_gauge_full.jpg): r3 shows the ghost 0 ("-09,71x" half alpha at 3738, "-09,988" FULLY
  opaque at 3761); step 4 shows "-9,71x" / "-9,988", then "-10,003" at 3762 (bit-identical to r3). The 1 rolls in and the minus moves one
  digit left within one frame at this rate (about 20 ft per frame). Rest of frame identical. PASS.
