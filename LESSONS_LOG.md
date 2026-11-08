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
