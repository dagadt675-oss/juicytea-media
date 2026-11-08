# Myth Juice lessons log

One dated entry per episode, project or major task, newest first. Each entry: what was made, the real results, what worked, what failed, and which rules went into PLAYBOOK.md. "Real results" means YouTube Studio numbers when we have them; otherwise QC scores and measurements, labelled as such. Source keys (ctx, brief, hunt, vu, look, R6/, bundle:) are defined at the top of PLAYBOOK.md.

## Topics already used (do not propose again)

- Why the continents point south ("continental drip"): long-form ep01, published 2026-11-06.
- Hawaii drained ("Hawaii Is Only the Tip"): long-form ep02, in production.
- Lake Peigneur, the lake that fell into a salt mine (1980): long-form, before ep01.
- The San Juan Pig War: Short, before ep01.
- Bats aren't blind: Short, before ep01.

(ctx 'Topics already used by the channel'; brief)

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
- Open before script lock: watch Unseen Works' Pacific drain and Below The Map's Hawaii video and cut any reveal they show; close the 8 VERIFY items (brief section 12); make engine/tools/colab/vm_render.sh, redo_v3.sh, finalize_v3.sh and qa_sheet.sh episode-agnostic; run motion tests on a real phone; check the chapter card titles against the chapter rule. The look book's runtime mix assumes about 16 min (look section 3); the brief's 12:45-13:00 governs.
- Owner OK still needed before any Test & Compare, title swap, pinned comment or Drive write.

Rules added to PLAYBOOK.md: research method (judges plus red team, small-sample Studio reading, competitor-frame fetching, the competitor upgrade list); topic (host-cluster greenlight, one phone-sized subject, renderable spatial payoff, unhedged answer, US anchor, unspent climax, saturation and news-number checks); facts (fact spine with VERIFY, sill.py gating, thought-experiment wording); visuals, text and graphics (one visual world, full-bleed obliques, brightness, sizes, palette, type system, gauge, live change, exaggeration); humour (in-world gags, paper cut-outs); packaging (Suggested-feed thumbnail rules, 35-50 character titles, pre-test, Test & Compare reading); Shorts (7 rebuilt Shorts); pipeline (render and encode limits, disk hygiene); owner and security rules gathered in section 1.

---

## 2026-11-06: ep01, "Why the Continents Point South (Not Just a Coincidence)"

What was made (longform/ep01-continental-drip/):
- A 15:34 long-form (v3), 1920x1080 30 fps, six engine chapters and 9 YouTube chapters, English narration by ElevenLabs "Brian" in 109 takes, on the three.js film engine (photoreal globe, paleo-globe, cut-away Earth, CC0 characters).
- Review round 6 found 97 defects (1 blocker, 40 major); 93 were fixed and 61 of 68 chunks re-rendered (R6/SUMMARY.md). The v3 edit cut 77 s in post (1011.0 s to 933.9 s) with no new narration (R6/edl_v3.json).
- Final render on a Colab L4 GPU in about 14 min (against 6-8 h locally). Final QC: -14.0 LUFS, LRA 2.3 LU, true peak -1.4 dBTP (research/qc_v3.json).
- Delivered: CRF 18 master (806 MB), a sub-500 MiB upload copy, English SRT, three thumbnails (B "POINTING AT WHAT?" as default), metadata.md. The owner uploaded it on 2026-11-06.

Real results, YouTube Studio after about 35 hours (ctx):
- Views 43, impressions 925, CTR 2.27%, average view duration 3:51 of 15:34 (24.7%), likes 2, comments 0, shares 0, subscribers +0.
- Traffic: Suggested 862 impressions (93%) at CTR 1.97%; Browse/Home 34 at 8.82% (3 clicks); Search 9 impressions, 0 clicks.
- Devices: mobile 44% of views at 2:11 (14.1%); tablet 2:45 (17.8%); computer 7:53 (50.7%); TV 8:24 (54.1%).
- 98% non-subscribers. US viewers: 28% of views, 43% of watch time.
- Agent panels had predicted 35.7% AVD (39-40% after fixes); the real 24.7% was closest to the casual phone lens (28.4%).
- Owner verdict: "not very good"; he wants the next one "much, much better".

What worked:
- The 3D antipode overlay (2:40-3:05), which YouTube's own analysis called "remarkably vivid and professional"; the visuals and narration quality as a base (ctx).
- Big-screen viewers stayed for half the film (computer 50.7%, TV 54.1%), so length was not the problem.
- Setups and payoffs, the dry gag rhythm, the Gondwana breakup and the emotional peak, as rated by the review panels (R6/synthesis keep list; not confirmed by audience data).
- The Colab GPU pipeline, frame-exact post tightening with edl.py, and the delivery hand-off without publishing anything.

What failed:
- Topic: chosen on a supply gap ("0 long-form videos") with no search demand; told as the history of an idea across 7 landmasses; the answer hedged ("not entirely").
- Packaging: abstract question text over a dark map, a 55-character hedged title; Suggested CTR 1.97%.
- Phone legibility: 26-35 px label caps, 3-5 px lines, a small globe on black, mean luma about 40; mobile AVD 14.1%.
- Structure (YouTube's critique): a menu in the hook (0:37-0:54), a Juice Check/Subscribe interruption (4:57-5:07), slow archival asides (1:00-1:25), a stylised corridor set (7:35-7:50), early and empty end cards; the answer landed at 59-69% with about 4:50 after it.
- QC: 25 static flags were waived as "slow drifts"; sheet-based reviews missed 97 motion defects until round 6.

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

What failed: the flap-cycle pop (GLB keys ran 0-37.5 frames, the strip assumed 0-30); captions at y=1515 may sit inside the Shorts UI; ElevenLabs free-tier narration is non-commercial; an ASR pass heard "is" for "as", which needs a human listen.

Rules added: facts (limiting words, dated counts), hook (statement, not question), Shorts (caption style and safe zone, frame 0 as thumbnail, mid-video "guess" beat), rendering (Blender on Colab only, read real GLB key ranges), owner and security (free-tier licence check).

---

## 2026-10-26 to 2026-10-28: Lake Peigneur long-form, "The Lake That Fell Into a Salt Mine"

What was made: a 6:29 (389.3 s) 1080p30 long-form on the older Python map engine with Esri imagery, ElevenLabs v4 narration and burned-in subtitles, packaged for chapter-by-chapter rendering on a Colab CPU runtime; a fact sheet with status keys built from the MSHA 1981 report read page by page; scripts v2 and v3; a v4 fix package after QC (bundle:lake_peigneur_v4/pkg/CHANGES_v4.md). Whether v4 was rendered and published is not in the sources; the channel lists the topic as used.

Real results (QC and measurements, no YouTube numbers in the sources): weighted 8.00/10, a PASS exactly at the gate (bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md). Script fidelity 9.5, hook 8.4, visuals 7.5, audio 7.6, pacing 7.5, subtitles 7.2, tech 9.0, closing 8.0, thumbnail 8.5, title and description 7.8. Measured: -14.1 LUFS, LRA 2.3, true peak -3.2; 7 gaps of 8 s or more without a new visual (36 s on one image); 6 frozen stretches of 1.5 s or more (one in the hook); chapter gaps of 1.06-1.50 s; a 0.64 s tail; labels about 25 px; 2 of 12 quote cards truncated without an ellipsis; a highlighter stopping mid-word on 3 cards.

What worked: the fact sheet with status keys and its banned-number list; an 8-word hook claim landing before 3 s; the open loop planted in the cold open and paid off at the end; the owner's second-by-second review of v2, whose 12 animation defects were fixed in v3; a continuous music bed with no silence holes.

What failed: the "v4" sent to re-QC was byte-identical to v3, so nothing had been fixed; static stretches and small labels; source tags on screen; three generated stills had been planned (removed in v3); the description claimed quote cards were exact when two were not.

Rules added: facts (status keys, primary over listicles, verbatim quotes with ellipses, undetermined causes, absolute claims checked), pacing (pause lengths, freeze limits), text (no mid-word highlighter, no overlaps), visuals (chapter cards on top, physically true animation, seam fixes, crossfade ghosts), QC (8.0 gate, md5 before re-QC, measured battery, batched fix lists, no ear verdicts), owner rules (no AI generators, no publishing from operator sessions, no Drive mount).
