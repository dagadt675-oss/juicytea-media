# Myth Juice lessons log

One dated entry per episode, project or major task, newest first. Each entry: what was made, the real results, what worked, what failed, and which rules went into PLAYBOOK.md. "Real results" means YouTube Studio numbers when we have them; otherwise QC scores and measurements, labelled as such. Source keys (ctx, brief, hunt, vu, look, R6/, bundle:) are defined at the top of PLAYBOOK.md.

## Topics already used (do not propose again)

- Why the continents point south ("continental drip"): long-form ep01, published 2026-11-06.
- Hawaii drained ("Hawaii Is Only the Tip"): long-form ep02, in production.
- Lake Peigneur, the lake that fell into a salt mine (1980): long-form, before ep01 (whether it is live is not in the sources; confirm with the owner before ep02's hand-off line is voiced).
- The San Juan Pig War: Short, before ep01.
- Bats aren't blind: Short, before ep01.

(ctx 'Topics already used by the channel'; brief)

---

## 2026-11-09: ep02 toolkit round 2 (review fixes before the six chapter builds)

What was made: every must-fix and most should-fixes of the toolkit review, in `engine/www/ep/ep02/` (shared.js, ch1.js, payoff.js, edit.js, API.md, tools/) and the stages (`lab/hawaii/hterrain.js` new optional uniforms, new `lab/hawaii/section.js`, `lab/type/type.js` shadow options). Frame 1 and ONE ISLAND now use the thumbnails' own type (Barlow Condensed 800, ink rgb 16,22,30, soft white glow, no plate). ch1's demo stage is region `mauinui` (78 m) nested in the legacy Big Island bake, so landing, drain and outlines come from the 78 m grid. The payoff is a terrain cut-away (east-west section through Mauna Loa, sagging crust and Moho, old sea-floor line, trench water, Everest's real profile on the same base line) instead of the BlockStage box. The gauge carries its value in the plate. A public-domain postcard photo (USGS, Pohoiki) is in. API.md is rewritten as the manual for six parallel chapter builders (what each may and may not change, windows, regions, shot factories, timing, text rules, checks). Stills: scratch:research/ep02/foundation2/ (ch1, payoff, toolkit). Nothing was published, uploaded or posted.

Real results (measurements on the stills):
- Clone gate (channel/niche/work/gate.py): every ch1 frame from 0 to s006 passes. ONE ISLAND end state red 0 %, tan 3 %, drain-clone distance 11.87-11.92 (was red 17 %, FAIL); Maui Nui landing f344 drain-clone 12.14 (was 9.61), f509 tan 4 % (was 11 %).
- Brightness: look-down frames 91.5-95.8 (was 75.6-82); Maui Nui 122.6-130.0 with the bottom half 99-104 (thumbnail 133 and 92; was 139.6 and 118-123); payoff 95.7-113.6 (was 97-138 with a grey void); STORY globe 97 (was 79); everest_wide 168 with 0 % blown (was 196 and 6.7 %).
- Frame 1: SSIM 0.943 label-free against the label-free thumbnail (0.969 before: the far islands are now muted by design and the white rim fades with distance), 0.837 with the label against final_ep02_1.jpg (the label sits at y = 96 for the safe area where the thumbnail has it at y = 38). ONE ISLAND f586 against final_ep02_2.jpg: SSIM 0.50 (was 0.43), colourfulness 57.5 (thumbnail 65.6; was 111).
- Type QC: no [typeqc] FAIL on the 13 ch1 and 9 payoff stills; payoff 9 visible words; the number block clears the bar by about 400 px.
- lab_hawaii.html renders pixel-identically after all stage changes (MAE 0).

What worked:
- Reading the thumbnails' build configs (packaging cfg_q1c.json, cfg_q3c.json) instead of guessing their type: the review assumed Anton, the files say Barlow Condensed 800 with a white glow.
- Nesting the finer region in the frame-1 stage (stack mauinui > bigisland > skirt, legacy origin and mesh): one continuous camera, frame 1 unchanged, Maui Nui at 78 m.
- Hero fill only on new land bridges (land at the level within 11 km of two of today's islands) plus the exact-level contour; the natural colours carry the shot.
- A class value for hero-filled pixels (0.75) that the shared grade passes through: the cap fill reads #FF5A36, not crimson.
- Refilling the sea as -9000 (1 - p)^5 over the 1.6 s flight: the Maui Nui shelf is wet before it fills the frame.
- A section wall built in world space with the clip plane from the same frame: wall and terrain meet exactly; the section shader shares the stage's sun and haze (with 0.3 of its fog) and the shared grade.

What failed or stays open:
- The first cut-away rendered the wrong half (camera side sign) and lilac rock (full sun on the face plus haze); fixed by the sign, 0.38 sun and 0.3 fog on the section.
- The first contour closed open chains (a ring cut by the grid edge) with a straight line across Maui Nui; open chains now stay open.
- Kahakō on stacked lines need about 30 px of line gap (the Ā macron touched the line above at 16 px).
- Wikimedia Commons' API was rate-limited from the proxy; usgs.gov pages refuse curl but a text fetch gives the licence and the S3 original downloads.
- Open: the section face reads as a fairly uniform brown-grey at phone size during the long holds; the cloud seam near 160° W and the cyan shelf glow on the STORY globe; region data faults (Pali, Nihoa, Gardner, nwhi_west caps, the everest_wide shadow blob only lifted, not re-baked); sub-frame motion blur; the L4 timing of the new stages; the payoff's tip-down start frames are mostly grey section.

Rules added: PLAYBOOK_craft section 8 (thumbnail type as set, joins with natural colours, one seabed and film water, cut-away for height comparisons; DONT masked grade over a fill, dry shelf mid-flight, coarse or closed contours, blocks in a void; the coloured-word rule reworded to a two-colour legend only), section 9 (gauge value in the plate, obstacles for placers, ʻokina in Anton); PLAYBOOK_production section 15 (parallel chapter builders by file, USGS public-domain photos).

## 2026-11-09: ep02 mix v1 (re-recording mixer pass, sound only)

What was made: the full 12:26.9 mix of ep02 from the spotting session (14 music cues, 147 one-shots, 47 ambience beds, 19 dips and lifts) on the prepared Rodney narration: the spec (longform/ep02-hawaii/audio/mix_ep02_v1.json, built by longform/ep02-hawaii/tools/build_mix.py), a 48 kHz mix with four stems (vo, music, sfx, ambience) and a 192 kbps sound-only preview for the owner (scratchpad deliver/ep02/hawaii_hang_elozetes_v1.mp3; media not in git). Tools: mix.py gained spectral ducking ('band' in duck, amb_duck and a new sfx_duck) and limiter runs in its report; audio_scan.py now rebuilds its buses with mix.build; mix_qc.py is new. An ep01 spec still mixes identically (max sample difference 3.6e-7).

Real results (measurements, nothing published, no ear verdict): -14.0 LUFS, true peak -1.7 dBTP, LRA 3.8 LU, no clipping, no -45 dB / 0.3 s silence; voice over music median 21.7 LU, p10 19.0, every sentence 16.6 LU or more; voice over ambience p10 18.5 LU; 1-4 kHz voice margin under 15 dB in 4.2% of speech windows (p5 15.8 dB); 1.6 duck pumps a minute (ep01 18.6); breathing room before all 9 reveals; no one-shot in the three hush windows, no comic sound on a word, at most 7 one-shots in 10 s, no sound three times in 60 s; the limiter worked more than 1 dB for 0.16 s in the whole film. Full numbers: longform/ep02-hawaii/audio/mix_report_v1.md.

What worked: building the spec by script from the spot with an md5 lock on timing.json; placing generated SFX by their measured sync point (29 of 101 files had moved by more than 0.25 s); a 0.8 s duck hold; carving the speech band out of the ambience (the single biggest fix); measuring breathing room per reveal; checking audio_scan's 'masking' windows in the band before acting on them.

What failed: the first render passed every loudness and voice-over-music check but failed the speech band badly (33.4% of speech windows under 15 dB at 1-4 kHz, p5 3.0 dB): bright wind, surf, radio static and the hiss of quietly generated beds sat level with the voice there although they were 18 LU under it overall. A first spec build moved bed material used as swells by its src_in (caught before rendering). Two QC metrics were wrong on the first try (reveal pauses read from the wrong window; an ambience-level swell counted as a hush one-shot) and were corrected. Three unplanned rests inside generated cues (2:38, 3:45, 4:16) remain for the owner's ears.

Rules added: PLAYBOOK_craft section 11 (prepare the voice and duck with a hold; carve the speech band and judge masking there; build the spec by script with measured sync); PLAYBOOK_production section 16 (gate every mix with mix_qc.py plus audio_scan.py).

## 2026-11-09: ep02 terrain data (a baked stage for every terrain shot)

What was made (2026-11-08, finished 2026-11-09): engine/www/lab/hawaii/tools/region_bake.py, a general bake (name, bbox, size) generalised from hawaii_bake.py: ETOPO 2022 15"/30", NOAA NCEI 1/3" and 3" coastal topo-bathy DEMs, Terrarium land detail, a MODIS composite plus HLS 30 m colour, AO, and sea-level facts measured on the grid. engine/www/ep/ep02/tools/regions_spec.json (bbox, size, sources, stack, verification camera, script segments, gaps), rebuild_regions.sh and make_index.py write engine/www/ep/ep02/data/<region>/ (git-ignored except meta.json) and regions.json. HawaiiStage.loadRegion loads nested stacks of up to 3 layers; lab_region.html renders any region. 21 regions: mauinui, oahu_nuuanu, pali, kauai, waimea, main_chain, kilauea_sf, halape, holei (added 2026-11-09 for s086-s088), maunakea, kamaehu, kohala, nwhi_chain, nihoa, lalo, gardner, nwhi_west, midway, kure, everest_wide, everest; the legacy bigisland and hawaii_skirt stay as they were (frame 1 must keep matching the thumbnail).

Real results (measurements, nothing published):
- Size and cost: 58 MB baked plus 23 MB legacy; 15-118 s per bake (network bound); one 1920x1080 still 9-35 s on local software WebGL.
- Facts on the grids: Maui-Lana'i join at -59 m, Maui-Moloka'i at -79 to -80 m, Kaho'olawe at -159 m; at -122 m (-400 ft) one island of 5,696 km2 with Kaho'olawe separate. All main islands from Hawai'i to Ni'ihau on one ridge at -3,500 m (O'ahu-Kaua'i saddle -3,008 m); at -5,500 m the largest water left is 6,471 km2 north-east of the Big Island. Holei arch site -6 m with a 24 m cliff top within 300 m.

What worked: one spec for every region; a still per region before any shot uses it; depth-bin maps of the grid next to the stills; NCEI 1/3" grids for every close main-island shot; HLS imagery as the judge of land in the NW Hawaiian Islands.

What failed (all fixed): round 1 (2026-11-08) found ETOPO false islands (Gardner 859 m over 9 km2, a 57 km2 blob over French Frigate Shoals, a 10 km2 blob east of Nihoa), NCEI 6" gridding artefacts, magenta land from per-channel colour matching, a cloud filter that painted over Everest's snow and refills that pulled from the spikes themselves. Round 2 (2026-11-09) found '+'-shaped pits 10-20 m deep around every Lalo islet (cubic upsampling rings around ETOPO spikes; the refill now takes a two-source-pixel ring); about 20 false islets each on Lalo's SE rim and Kure's NW rim (surf passed the per-pixel land test; a per-islet vote and a Green Island keep box removed them, so Lalo has Tern and East Island and Kure only Green Island); Pali colour neon green (gain matched to cloudy MODIS, 1.34) and its NE-facing cliffs black (winter scenes); everest_wide had no verification camera, so its still crashed and it went unchecked.

Open data gaps (in regions.json per region): La Perouse Pinnacle (about 37 m) and Gardner's two pinnacles are below every grid (model them at surveyed positions); the atoll lagoons and reef rings of Lalo and Kure are ETOPO-flat (sat.jpg carries the look; Midway alone has a surveyed 1/3" grid); Nihoa's cliffs are too gentle (179 m on the grid vs 273 m surveyed); the Holei arch, the Pali lookout and Halape's pre-1975 shore are not in any data; the Ko'olau summit keeps a few cloud specks; Everest colour carries baked north-face shadows (light it from the south); the 2018 East Island before and after needs dated Landsat or HLS scenes.

Rules added: PLAYBOOK_production 15 (verify every region with its own camera; atoll ringing and per-islet land vote; HLS gain and season over cliffs), on top of the 2026-11-08 bake rules.

---

## 2026-11-08: ep02 shot toolkit (foundation for the chapter builders)

What was made (engine/www/ep/ep02/, API.md documents it with examples):
- shared.js: one WebGLRenderer for the page with lazily created, cached stages (terrain per region, Mauna Loa vs Everest blocks, CineGlobe); only active stages render; every stage goes through one shared grade pass (navy lift, cool shadows, warm highlights, vignette, frame-seeded grain) before a crisp UI layer. terrainShot (named regions, keyframed camera, water level, sun, state blends, flights, island masks and outlines from a flood-fill on the production grid), blockShot, cineGlobeShot (STORY, HERO, ESTABLISH presets), paper and postcard devices from story.js, the type.js system with the floors enforced per frame ([typeqc] FAIL logs), the SEA LEVEL gauge, an odometer with commas, xfade and seq, and timing helpers (K.T, K.lead, K.word, K.chapter, tools/frames.py).
- Small backward-compatible options in the lab stages (hterrain.js, blocks.js, cineglobe.js): a shared renderer, render into a target, a class mask in alpha, a hero / dim mask, a lens shift X; lab_hawaii.html renders stayed pixel-identical (MAE 0). type.js FLOOR raised to {must: 64, any: 48}.
- edit.js orchestrator, ch2-ch6 stubs, ch1 s001-s006 built end to end (DEMO 1 and 2), payoff.js with the stand-alone payoff_test.html (DEMO 3), toolkit_test.html smoke tests (globe, paper and postcard, crossfade, region).
- Stills at the markers: scratchpad research/ep02/foundation/ (ch1, payoff, each with a 390 px phone sheet).

Real results (measurements, nothing published):
- Frame 1 against the label-free NO OCEAN thumbnail: SSIM 0.969 at 320x180, luma 105.7 vs 109.8, colourfulness 54.3 vs 56.6.
- ONE ISLAND: the plate camera was lost; a camera search recovered it (layout agreement 0.91). At -400 ft (-121.92 m, so the counter lands exactly on 400) the fused island measures 5,683 km2 on the grid and Kahoʻolawe stays separate.
- Type QC: no [typeqc] FAIL on the final ch1 and payoff stills; frame luma 98-149 on terrain and blocks, 79 on the STORY globe.
- Local cost per frame with a GPU sync: terrain 10-14 s, globe about 3 s, blocks 1.5-2.8 s, shared grade 0.1-0.35 s.

What worked: porting the thumbnail's masked grade into the shader through a class mask in alpha (water untouched, so the grade can fade while the sea refills); one renderer with lazy stages; QC built into the draw calls; marker-keyed timing (the voice was re-timed once and the payoff followed).

What failed (fixed): closed rings simplified to 2 points (Douglas-Peucker on a zero chord); a zoom helper that converted degrees twice and doubled the field of view (caught by logging the camera, {"dbgCam":1}); a hold drift that accumulated through the flight (6.8 degrees off the landing framing); outlines drawn over a text plate; a map label on the number block; the cap and fused-island hero fills too opaque at first; unsynced in-page timings (1-4 ms) that hid the real cost.

Open for the chapter builders: the BlockStage base is flat (the bowl-shaped dent of s163-s168 needs a terrain cut-away); the postcard beat (s003) waits for a public-domain Big Island photo; the CineGlobe cloud seam near 160 W; ch1 Maui Nui close shots should move to the finer 'mauinui' region.

Rules added: PLAYBOOK_craft 8 (toolkit, camera search, no accumulated hold drift), 9 (UI draw order and label placer); PLAYBOOK_production 15 (marker-keyed timing, GPU-synced timing).

---

## 2026-11-08: playbook check against its sources, fixes and the competitive-edge section

What was made:
- A source check of the playbook: 27 numbers spot-checked against the repo, the Drive bundle and the scratch logs; 22 matched exactly. Corrected: Shorts text limit x 900 to 849 (bundle:bats/PLAN.md section 3); 'credits (150 a month)' removed (no source; ctx says only 'very limited'); the panel calibration (the panels predicted 39-40% for the published v3, not 35.7%, so subtract about 15 points, not 10); 'all 68 chunks matched' (frame counts matched on all 68, pixels within 1.7/255 on 61, while 7 chunks differed by 3.2-5.1/255, ep01/research/colab_vs_local_chunks.json); the Florida 6-8 px figure (vu gives it for the CineGlobe prototype, so the rule now cites hunt T8's 'a few millimetres wide on a phone').
- The playbook split into three files that each read whole: PLAYBOOK.md (core, about 31 KB), PLAYBOOK_craft.md and PLAYBOOK_production.md. The old PLAYBOOK.md was 74,656 bytes and the Read tool showed only lines 1-296 of 436, so agents never saw the Shorts, pipeline, QC, delivery and Superseded sections.
- A new section 18, Competitive edge (the owner asked how we stand out next to the competitors): a reveal audit against the 3 closest videos, a 'real number' beat, an opening-frame strip test, fixed brand devices, a weekly re-probe and a per-episode strip-test score log. All [hypothesis] until Studio numbers confirm them.
- Contradictions resolved: one numbers cap (hero vs spoken numbers defined); one shot-template definition; coloured headline words instead of an overlay key; the globe exception for proof overlays and paleo sequences (8 s per framing); the live-change exception covers drains, floods, ice peels and time sliders; a music variation by 2:00 inside long chapters; [S] sources only for non-numeric context; end-screen elements only after the hand-off's last word; one black gate (0.27 s) and one silence gate (0.3 s); one pacing detector pair; one icon and pin floor (about 64 px); chapter-card timing against the voice gap; the payoff wording; low-poly characters banned in ep02; one word budget (1,900-2,000 words for 13:00); 1440p needs x264 level 5.1.
- Tags corrected: [owner] kept only for the owner's own words; small-sample rules marked 'n = 43 views, direction only'; untested thresholds moved to [hypothesis].

Real results: none. Nothing rendered, uploaded or published.

What worked:
- Checking every number against its source file found 5 wrong or unsupported figures out of 27 before they reached ep02.

What failed:
- A 75 KB playbook that agents silently read only in part.
- Gates weaker than the rules they enforce: type.js fails only caps under 44 px (the rule says 64 and 48); qc_video.py flags black only from 0.5 s, silence from 1.2 s and static from 3.5 s; the AI-wording check was a substring grep that cannot pass on a Hawaii film ('ai' is inside Hawaii and Drained: 131 lines of the brief, 0 whole-word hits).
- ep01 delivery: metadata.md told the owner to upload the ~4 Mbps size-capped copy, not the master (now banned).
- [owner] tags on engineering details, which froze them as 'always wins'.

Open items, questions for the owner (ask in Hungarian):
- Make the GitHub repo private? It is public (checked 2026-11-08). It holds the channel handle in ep02/research/context.md, the owner's Studio numbers, summaries of his Drive bundle, 100 commits authored by 'Claude' with Claude co-author lines, and his personal e-mail address in the author field of 7 commits. An autosave job also commits and pushes about every 10 minutes (scratch:autosave.log; HEAD equals origin), so 'push only with his OK' needs that job paused or his OK.
- Is the Lake Peigneur video live? If not, pick another published video for ep02's hand-off before the line is voiced.
- Shorts captions: keep his y=1515 (79%), or test 66-70% on a real phone with the Shorts UI?
- Shorts camera: does 'one continuous camera move, no cuts' still apply to all 7 rebuilt Shorts?
- Is the ElevenLabs plan paid, covering narration and music (music.py uses the ElevenLabs music API)?

Open items, code changes outside the playbook (not made in this task):
- engine/tools/tts.py and ep01/tools/tts.py line 68: default voice Brian to Rodney (eY2VJs4Gi8QKG2RV01sS).
- engine/tools/grab.py: fix the one-frame-late label.
- ep02/lab/type/type.js: FLOOR {must: 64, any: 48}, a text-block count, a 4-word headline check, and the header comment (it still says 60 and 44 px).
- engine/tools/qc_video.py: blackdetect d=0.27, silencedetect d=0.3, static limit 2 s.
- engine/tools/assemble.sh and deliver_encode.sh: -level 5.1 for 1440p (4.2 allows 8,704 macroblocks per frame; 2560x1440 needs 14,400).
- A 'Superseded by the playbook where they differ' banner on engine/ENGINE.md (dark pills, 'nothing static > 3 s', 'max 2 text elements of 7 words'), ep01/research/retention_checklist.md (subscribe at 35-45%), bench_packaging.md (rule 8, authenticity on screen) and bench_visual.md.

Rules added or changed: Read this first items 1, 2, 4, 5, 7; section 1 (public repo, whole-word AI check, ElevenLabs licence covers music, the other-Google-accounts rule, report length); sections 2-6 (calibration, US anchor, named people, [S] use, numbers cap, word budget, payoff wording, hook tags); section 18 (new); PLAYBOOK_craft.md sections 7-13 and PLAYBOOK_production.md sections 14-17 as listed above; new Superseded entries.

---

## 2026-11-08: ep02 planning, "Hawaii Is Only the Tip. We Drained the Ocean."

What was made (all in longform/ep02-hawaii/):
- Topic hunt (research/topic_hunt.json): ep01 lessons, 35 raw ideas, 12 checked candidates, three judges (click, story, feasibility) and a red team on 3 finalists. Hawaii scored 218 (77 / 67 / 74), the only finalist in all three top 3s; Lake Powell 211 (news cycle flipped, template race); Zuiderzee 202 ("KILLED as pitched").
- Production brief (research/brief.md): launch title "Hawaii Is Only the Tip. We Drained the Ocean." (45 characters), 6 chapters, 12:45-13:00, 9 hero shots (first at 0:00 and 0:14), 17 re-hooks, the payoff at 11:10-11:45 (87-91%): Mauna Loa about 56,000 ft from its dented base (USGS), with "taller than Everest" moved to a mid-film beat because Shorts have spent it. Hand-off to Lake Peigneur. The red team's 2 must-fix errors were corrected (Kaho'olawe was not part of Maui Nui at -120 m; the Midway carriers lie 170-190 miles out and over 5 km down).
- Visual upgrade (research/visual_upgrade.json, research/visual/visual_plan.md): a frame audit of ep01, a competitor benchmark, an engine tech scout, 4 prototypes in lab/ (cinematic globe, drain terrain, phone-first type, paper cut-outs) and a review panel; the "One Earth" look book.
- Owner decision: narration by ElevenLabs "Rodney - Clear Educator" from ep02 on (tools/el_voices.py finds voices without printing the key).
- Owner summaries in Hungarian: research/osszefoglalo_hu.md, research/visual/vizualis_terv_hu.md.
- PLAYBOOK.md and this log created; CLAUDE.md and AGENTS.md point every assistant to them.

Real results: none yet. Nothing is rendered or published. Target upload about 2026-11-20 (brief section 12).

What worked:
- Picking by independent judges plus a red team: no attack killed Hawaii, and every fix it needs is in our control (brief section 1).
- A same-day supply re-probe with ytsearch.py: no Hawaii-only drain video above 10K views on 2026-11-08 (brief section 1).
- Prototype verdicts with numbers: the phone-first type system took the panel teen from 2 to 8 (ADOPT); the live drain took the teen from 3 to 8 (vu panel type, panel drain).

What failed or is still open:
- The prototypes were judged as stills only; nothing has been seen moving on a phone (look section 8 X1).
- 3x terrain exaggeration read as "crumpled foil"; 100% hero fills hid the relief; prototypes used different grades and fonts (vu panel drain, story, globe).
- False labels in the prototypes: "LAND BRIDGE" at -300 m and "ALBORAN SEA" (look section 8 B2); a type headline dropped "MOST OF" and overclaimed (B1).
- yt-dlp was blocked by YouTube's bot check; competitor frames now come from i.ytimg.com hq1-hq3.
- The brief conflicted with newer owner rules: one cropped 35 s Shorts teaser ending "The full film is linked" (now 7 rebuilt Shorts) and a cap of 4 big numbers (now 6-10).
- Brief items the playbook overrides (void; fix before script lock): section 6 at 0:25, the low-poly suitcase tourist (ep02 allows paper people or one tested recurring 3D character, and a figure at 35-40% of frame height cannot fit a regional shot); section 6 at 0:11, the same-framing hard cut 'the sea snaps back' (needs one continuous move or an 8-frame dissolve); section 5's fallback title "We Drained Hawaii's Ocean. Here's What Was Hiding." (copies the Contour Atlas template; a title may share at most 3 consecutive words with any top-20 search title); section 7's end-screen elements at 12:31, under the hand-off line (elements only after its last word); the low-poly palms at 0:47 and section 8's CC0 low-poly characters; section 11's 'nothing static over 6 s', 'at most 3 labels', 'lines 8-10 px', 'counters a quarter of the frame tall' and 'globe shots 3 s or less' (now 2 s near-static, one block plus one label plus the gauge, 9-12 px, 150-190 px caps and the playbook's globe limits).
- Open before script lock: run the section 18 reveal audit (watch Unseen Works' Pacific drain and Below The Map's Hawaii video and cut any reveal they show); confirm with the owner that the Lake Peigneur video is live, or pick another published video, before the hand-off line is voiced; close the 8 VERIFY items (brief section 12); make engine/tools/colab/vm_render.sh, redo_v3.sh, finalize_v3.sh and qa_sheet.sh episode-agnostic; run motion tests on a real phone; check the chapter card titles against the chapter rule. The look book's runtime mix assumes about 16 min (look section 3); the brief's 12:45-13:00 governs.
- Owner OK still needed before any Test & Compare, title swap, pinned comment or Drive write.

Rules added to PLAYBOOK.md: research method (judges plus red team, small-sample Studio reading, competitor-frame fetching, the competitor upgrade list); topic (host-cluster greenlight, one phone-sized subject, renderable spatial payoff, unhedged answer, US anchor, unspent climax, saturation and news-number checks); facts (fact spine with VERIFY, sill.py gating, thought-experiment wording); visuals, text and graphics (one visual world, full-bleed obliques, brightness, sizes, palette, type system, gauge, live change, exaggeration); humour (in-world gags, paper cut-outs); packaging (Suggested-feed thumbnail rules, 35-50 character titles, pre-test, Test & Compare reading); Shorts (7 rebuilt Shorts); pipeline (render and encode limits, disk hygiene); owner and security rules gathered in section 1.

---

## 2026-11-06: ep01, "Why the Continents Point South (Not Just a Coincidence)"

What was made (longform/ep01-continental-drip/):
- A 15:34 long-form (v3), 1920x1080 30 fps, six engine chapters and 9 YouTube chapters, English narration by ElevenLabs "Brian" in 109 takes, on the three.js film engine (photoreal globe, paleo-globe, cut-away Earth, CC0 characters).
- Review round 6 found 97 defects (1 blocker, 40 major); 93 were fixed and 61 of 68 chunks re-rendered (R6/SUMMARY.md). The v3 edit cut 77 s in post (1011.0 s to 933.9 s) with no new narration (R6/edl_v3.json).
- Final render on a Colab L4 GPU in about 14 min (against 6-8 h locally). Final QC: -14.0 LUFS, LRA 2.3 LU, true peak -1.4 dBTP (research/qc_v3.json).
- Delivered: CRF 18 master (806 MB), a sub-500 MiB upload copy, English SRT, three thumbnails (B "POINTING AT WHAT?" as default), metadata.md. The owner uploaded it on 2026-11-06. metadata.md named the ~4 Mbps 2-pass copy as the file to upload, so YouTube most likely received that third-generation file, not the master.

Real results, YouTube Studio after about 35 hours (ctx):
- Views 43, impressions 925, CTR 2.27%, average view duration 3:51 of 15:34 (24.7%), likes 2, comments 0, shares 0, subscribers +0.
- Traffic: Suggested 862 impressions (93%) at CTR 1.97%; Browse/Home 34 at 8.82% (3 clicks); Search 9 impressions, 0 clicks.
- Devices: mobile 44% of views at 2:11 (14.1%); tablet 2:45 (17.8%); computer 7:53 (50.7%); TV 8:24 (54.1%).
- 98% non-subscribers. US viewers: 28% of views, 43% of watch time.
- Agent panels had predicted 35.7% AVD for the 16:51 v2 cut and 39-40% for the published v3; the real 24.7% was about 15 points lower and closest to the casual phone lens (28.4%). All Studio figures rest on 43 views (about 19 on mobile, about 12 from the US): direction only.
- Owner verdict: "not very good"; he wants the next one "much, much better".

What worked:
- The 3D antipode overlay (2:40-3:05), which YouTube's own analysis called "remarkably vivid and professional"; the visuals and narration quality as a base (ctx).
- Big-screen viewers stayed for half the film (computer 50.7%, TV 54.1%), which suggests length was not the main problem (very few non-mobile viewers).
- Setups and payoffs, the dry gag rhythm, the Gondwana breakup and the emotional peak, as rated by the review panels (R6/synthesis keep list; not confirmed by audience data).
- The Colab GPU pipeline, frame-exact post tightening with edl.py, and the delivery hand-off without publishing anything.

What failed:
- Topic: chosen on a supply gap ("0 long-form videos") with no search demand; told as the history of an idea across 7 landmasses; the answer hedged ("not entirely").
- Packaging: abstract question text over a dark map, a 55-character hedged title; Suggested CTR 1.97%.
- Phone legibility: 26-35 px label caps, 3-5 px lines, a small globe on black, mean luma about 40; mobile AVD 14.1%.
- Structure (YouTube's critique): a menu in the hook (0:37-0:54), a Juice Check/Subscribe interruption (4:57-5:07), slow archival asides (1:00-1:25), a stylised corridor set (7:35-7:50), early and empty end cards; the answer landed at 59-69% with about 4:50 after it.
- QC: 25 static flags were waived as "slow drifts" on the v2 cut (research/qc_final.json), and the published v3 itself failed qc_video (verdict FAIL: 20 static stretches and 0.83 s of black at 455.27-456.10 s, research/qc_v3.json), so failed gates were waived on the released film; sheet-based reviews missed 97 motion defects until round 6.
- Delivery: the owner was pointed to the size-capped upload copy instead of the master (see What was made).

Rules added to PLAYBOOK.md: most of the hook, pacing, story, visuals, text, audio, ending, packaging, rendering, pipeline and QC rules tagged ep01 (see the R6/ and ctx evidence), including the panel calibration rule and the ban on the ep01 packaging pattern.

---

## 2026-10-28: San Juan Pig War Short

What was made: a story-first script (v1, then a QC rewrite v2) and a build on the older Python map engine: a 33.9 s 1080x1920 60 fps dry run on the box, one C2-spline camera move with no cuts, Esri imagery, the NOAA Haro Strait boundary and NPS coordinates; a self-contained Colab package (bundle:san_juan/BUILD_REPORT.md). Colab was not started; nothing was uploaded or scheduled.

Real results (QC and measurements, no YouTube numbers in the sources): script v1 7.1/10 FAIL, v2 about 8.4 (estimate); facts 7.0 to 8.5; hook 7.5 to 8.5; ending 6.0 to 8.5; length 5.5 to 8.5. Dry-run mix -14.2 LUFS, true peak -1.7; loop seam MAE 4.4/255 (bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md).

What worked: the hook "A farmer shot a pig, and the Royal Navy showed up."; the loop line "...tell them this:" flowing back into the hook; round figures every source supports ("four hundred Americans"); following the primary (FRUS 1872: Berlin, not Geneva); deadpan jokes from verified facts.

What failed: the v1 hook exaggerated ("pointed cannons") with no person on screen; a fact-list ending; 45-50 s of planned motion; an anachronism (English Camp shown in 1859); single-source details; the per-sprite source list was lost in a box reset; the Esri credit sat on screen (now banned).

Rules added: facts (round numbers, no anachronisms, primary over secondary, verified geometry, authoritative coordinates), hook (concrete statement, no exaggeration), Shorts (loop seam, loop line, 25-35 s, one camera move, 2-3 elements), pipeline (asset provenance in the repo, self-contained package, owner OK on stills before the full render).

---

## 2026-10-26 to 2026-10-28: Bats Aren't Blind Short

What was made: script v1 and a QC rewrite v2; a Blender one-take scene (999 frames at 30 fps = 33.3 s, 27 wing-flap cycles, a seamless loop), karaoke captions in Anton 66 px with a cyan active word, a low-res 480x854 preview and a final mix; the full 1080x1920 render was staged for Colab T4 (bundle:bats/STATUS.md). Narration takes were in Brian. Slot planned for 2026-10-29; nothing was uploaded or scheduled.

Real results (QC and measurements, no YouTube numbers in the sources): script v1 7.0/10 FAIL, v2 8.1; facts 6.5 to 8.5; title and thumbnail 5.0 to 8.0. Mix -14.0 LUFS, true peak -1.7. Box render measured 23-41 s/frame (about 8 h), so not run locally (bundle:bats/QC_bats_not_blind_2026-10-26.md).

What worked: a statement hook ("No bat on Earth is blind."), limiting words where the science is limited ("some" bats see UV), the latest dated species count, an exact loop seam after retiming the flap cycle.

What failed: the flap-cycle pop (GLB keys ran 0-37.5 frames, the strip assumed 0-30); captions at y=1515, the owner's own setting, may sit inside the Shorts UI (untested; an open question for the owner, not a ban); ElevenLabs free-tier narration is non-commercial; an ASR pass heard "is" for "as", which needs a human listen.

Rules added: facts (limiting words, dated counts), hook (statement, not question), Shorts (caption style and safe zone, frame 0 as thumbnail, mid-video "guess" beat), rendering (Blender on Colab only, read real GLB key ranges), owner and security (free-tier licence check).

---

## 2026-10-26 to 2026-10-28: Lake Peigneur long-form, "The Lake That Fell Into a Salt Mine"

What was made: a 6:29 (389.3 s) 1080p30 long-form on the older Python map engine with Esri imagery, ElevenLabs v4 narration and burned-in subtitles, packaged for chapter-by-chapter rendering on a Colab CPU runtime; a fact sheet with status keys built from the MSHA 1981 report read page by page; scripts v2 and v3; a v4 fix package after QC (bundle:lake_peigneur_v4/pkg/CHANGES_v4.md). Whether v4 was rendered and published is not in the sources; the channel lists the topic as used. Ep02 hands off to this video, so confirm with the owner that it is live before that line is voiced.

Real results (QC and measurements, no YouTube numbers in the sources): weighted 8.00/10, a PASS exactly at the gate (bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md). Script fidelity 9.5, hook 8.4, visuals 7.5, audio 7.6, pacing 7.5, subtitles 7.2, tech 9.0, closing 8.0, thumbnail 8.5, title and description 7.8. Measured: -14.1 LUFS, LRA 2.3, true peak -3.2; 7 gaps of 8 s or more without a new visual (36 s on one image); 6 frozen stretches of 1.5 s or more (one in the hook); chapter gaps of 1.06-1.50 s; a 0.64 s tail; labels about 25 px; 2 of 12 quote cards truncated without an ellipsis; a highlighter stopping mid-word on 3 cards.

What worked: the fact sheet with status keys and its banned-number list; an 8-word hook claim landing before 3 s; the open loop planted in the cold open and paid off at the end; the owner's second-by-second review of v2, whose 12 animation defects were fixed in v3; a continuous music bed with no silence holes.

What failed: the "v4" sent to re-QC was byte-identical to v3, so nothing had been fixed; static stretches and small labels; source tags on screen; three generated stills had been planned (removed in v3); the description claimed quote cards were exact when two were not.

Rules added: facts (status keys, primary over listicles, verbatim quotes with ellipses, undetermined causes, absolute claims checked), pacing (pause lengths, freeze limits), text (no mid-word highlighter, no overlaps), visuals (chapter cards on top, physically true animation, seam fixes, crossfade ghosts), QC (8.0 gate, md5 before re-QC, measured battery, batched fix lists, no ear verdicts), owner rules (no AI generators, no publishing from operator sessions, no Drive mount).

## 2026-11-08 Competitor research and repo hygiene
- Niche study (channel/niche/niche_report.md): the niche is not saturated; the drain template is (96 uploads from 50 channels in 35 days, median 448 views). Signature-format small channels: median 99K views vs 2,650 for clone channels. Decision: broad umbrella, one signature series ("Below the Postcard"), Hawaii kept with new packaging.
- Failure: the autosave pushed 106 competitor thumbnails and 13 contact sheets to the public repo. Removed from the tree in commit 1282012; history rewrite needs a force push and the owner's OK. Rule added to PLAYBOOK.md.

## 2026-11-08 Packaging lab (channel/packaging/)
- Two blind feed rounds with 5 simulated viewer personas in a dark-mode phone feed simulator. Winners: concrete question titles ("Why Can't You See Most of Hawaii? (Look Down)", 9/10 in round 1). Losers: the postcard signature on thumbnails (read as travel), no-text renders (1 of 40), "Only the Summit" titles.
- Ep02 Test & Compare: NO OCEAN (default) + ONE ISLAND; YOU ARE HERE retired (0/10).
- Ep01 repackage withdrawn: the live package beat it 8/10 vs 0/20 with a control arm. Lesson: never trust a repackage test without the live package as control; simulated personas are direction only, real CTR outranks them.

## 2026-11-08 Ep02 script and narration
- Script locked: 92 sourced facts, 47-word Hawaiian pronunciation lexicon, 1,584 words, 178 segments; four review lenses cut about 330 words of filler (the Pali setup before 2:11, the repeated hot-spot explanation, the pre-payoff recap).
- Rodney narration: 12:15, 212 markers. ASR check passed except the acronym AF ('ay-eff' heard as 'IF'); fixed as 'A.F.' and re-synthesised only those segments (tts.py caches by content hash).
