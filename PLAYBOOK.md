# Myth Juice playbook

The permanent rulebook for every Myth Juice long-form and Short, in three files (listed below). Read all three in full before any work. Last merged 2026-11-08 from ep01, the ep02 planning and the older projects (Lake Peigneur, San Juan Pig War, Bats Short); checked against its sources and corrected the same day.

## Read this first

1. Owner rules beat everything here: no publishing or visible channel change without his OK, never mention AI, no secrets in output or git, billing only with him, no Drive writes without asking, reply in Hungarian. The owner asked on 2026-11-08 to save all good work in this repo, so commit and push. The repo is public (checked 2026-11-08); the owner was advised to make it private. Until then, never push secrets, personal data, other channels' thumbnails or unreleased video.
2. No false claims: every narrated or on-screen fact has a primary or verified source in the fact spine, per its status key (section 4), before it is voiced.
3. Pick a proven premise (a moving host cluster of 500K+ videos) with one phone-sized subject, a crisp unhedged answer and an unspent payoff.
4. Beat the competitors on what the clone channels skip: true facts, a real story spine, phone-first craft and live photoreal 3D reveals; run the competitive-edge checks in section 18.
5. Package for the Suggested feed: one focal subject, 3 words or fewer, a 35-50 character title. Pre-test: in the dark-mode strip at 390x220 pt, 168x94 px and 120 px our card must be the brightest and most readable next to the 5 strongest Suggested neighbours. After launch: Suggested CTR above ep01's 1.97% at about 10K impressions; otherwise one change, with the owner's OK.
6. Phone first: judge every frame at phone size; must-read text 64 px cap or more (all px sizes are at 1080p); the subject fills a third of the frame; bright frames.
7. Story first: no menu in the hook, first hero shot and part of the promise paid by 0:30, a re-hook every 60-90 s, the final answer at 85-90%, no tail after it.
8. Something moves every second: a new visual event every 3-5 s, nothing static over 2 s, never black mid-film.
9. 6-10 big numbers per film, never stacked; no sources, citations or emojis on screen; narration by Rodney, never Brian.
10. 7 rebuilt Shorts per long-form (never clips), each with hook, payoff and seamless loop. After every task update the playbook and LESSONS_LOG.md.

## Playbook files

The playbook is split so that every file can be read whole. Read all three to the end; if a read says it is partial or truncated, read the rest with an offset.

- PLAYBOOK.md (this file): Read this first, tags and source keys, 1 Owner rules and security, 2 Research method, 3 Topic, 4 Facts, 5 Story and script, 6 Hook, 18 Competitive edge, How to update.
- PLAYBOOK_craft.md: 7 Pacing, 8 Visuals, 9 Text and graphics, 10 Humour, 11 Audio, voice and music, 12 Ending, 13 Packaging.
- PLAYBOOK_production.md: 14 Shorts, 15 Production pipeline and rendering, 16 QC gates, 17 Delivery, Superseded (do not revive).

Where engine/ENGINE.md, ep01/research/retention_checklist.md, bench_packaging.md, bench_visual.md or an episode brief differs from the playbook, the playbook wins.

## Tags and source keys

- [owner] the owner's own instruction (always wins); [measured] our own numbers (YouTube Studio, ffprobe, loudness, frame scans); [reviewed] found by a QC or review pass on our own work; [benchmark] seen in competitor or 1M-view videos; [hypothesis] planned, not yet proven by us. [owner] is used only for the owner's own words; how we implement an owner rule carries its own tag.
- Conflicts: the owner's newest instruction wins; otherwise measured beats reviewed beats benchmark beats hypothesis. Rules that lost are listed under Superseded at the end of PLAYBOOK_production.md. Do not revive them.
- Small samples: every ep01 Studio figure rests on 43 views (about 19 on mobile, about 12 from the US). Read them for direction only.
- Sizes: all px sizes are at 1080p. At 1440p multiply by 4/3; type.js px() already scales by H/1080 and its QC records caps in 1080p units, but phone-sheet, layout-scan, line-width and shape-size checks must be scaled.
- ep01/ = longform/ep01-continental-drip/; ep02/ = longform/ep02-hawaii/; R6/ = ep01/research/review6/ (R6/synthesis, R6/voice_audio and R6/panel_* are the wf_96e8f33f-afb__*.json files; R6/fix_chN and R6/finish_chN are the wf_*__fix_chN.json and wf_*__finish_chN.json files).
- ctx = ep02/research/context.md (ep01 Studio numbers and YouTube's critique); brief = ep02/research/brief.md; hunt = ep02/research/topic_hunt.json; vu = ep02/research/visual_upgrade.json; look = ep02/research/visual/visual_plan.md.
- bundle:PATH = the owner's Drive bundle of the older projects (Lake Peigneur, San Juan Pig War, Bats Short), 2026-10-29, cited by original file path; not in the repo.
- scratch:PATH = ep01 session logs in the agent scratchpad; not in the repo and may be gone.

## 1. Owner rules and security

### DO (proven)

- Report to the owner in Hungarian, as short as the decision allows (300 words at most for big decisions), with the decision, why it is better, the honest weak points and the next date; keep paste-ready YouTube blocks (title, description, tags, pinned comment) in English. (owner rule; examples ep02/research/osszefoglalo_hu.md, ep01/release/metadata.md) [owner]
- Hold every long-form to the owner's content rules: storytelling first, 6-10 big vivid numbers, no emojis, funny scenes with real animation (our pacing for them is in section 10), ElevenLabs narration, credits only in the description. (owner rule; ctx 'The channel') [owner]
- Read the ElevenLabs key only from the ELEVENLABS_API_KEY environment variable, loaded from the owner's secrets file outside the repo, and pipe every Colab CLI output through `sed -E 's#(token|code|access_token|refresh_token)=[^& ]+#\1=***#g'` before it reaches a log. (implements the owner's no-secrets rule; engine/tools/tts.py, music.py, engine/tools/colab/bg.sh, cx.sh, upload_parts.sh) [reviewed]
- Use only official clients and pinned packages: google-colab-cli from pip, the REST API at api.elevenlabs.io, playwright@1.63.0, faster-whisper. (implements the owner rule against gateways and mods; engine/tools/colab/vm_setup.sh) [reviewed]
- Stop paid compute the moment its job is done (colab stop -s mj after the last chunk is downloaded and md5-checked; L4 costs 1.94 compute units/h) and confirm nothing is left running. (owner billing rule; engine/tools/colab/README.md; bundle:san_juan/RUN_COLAB.md) [owner]
- After every video and every review round, add what worked to DO and what failed to DONT in the playbook, with evidence and path, and commit and push before the next video starts (the owner asked for this on 2026-11-08). (owner rule; brief section 11 maps 25 ep01 problems to ep02 fixes) [owner]

### DONT (banned)

- Never publish, upload, schedule or post anything (YouTube, Instagram, vidIQ upload or update tools, Metricool, any platform) and make no visible channel change (title or thumbnail swap, Test & Compare, pinned comment, end screen, settings) without the owner's explicit OK for that specific action. (owner rule; ep01/release/metadata.md; brief section 5 lists actions that need it) [owner]
- In computer-use sessions never open YouTube or send e-mail, and end every QC or operator report by stating that nothing was posted, scheduled or deleted. (bundle:lake_peigneur_v4/COLAB_OPERATOR_STEPS_v4.md; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [owner]
- Never mention AI anywhere: narration, on-screen text, titles, descriptions, tags, thumbnails, comments, replies, channel page; no '(No AI)' or 'AI-free' tags. Before hand-off run a whole-word, case-insensitive check, `grep -nwiE 'AI|A\.I\.|artificial|synthetic|generated|generative|text-to-speech|TTS|voice clone|ElevenLabs|Claude|GPT|Midjourney'`, on the title, description, tags, pinned comment, SRT, thumbnail text, narration script and on-screen string list of the long-form and of all 7 Shorts, and have a person review every hit. A plain substring grep can never pass on this channel: 'ai' sits inside Hawaii and Drained (131 lines of ep02's brief, 0 whole-word hits). (owner rule; ep01/research/bench_packaging.md (b); ep01/release/metadata.md; grep of brief.md 2026-11-08) [owner]
- Never use AI image or video generators for any shot; build every shot in the engine. (Lake Peigneur v2 planned 3 generated stills, all removed in v3; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_production_table.md) [owner]
- Never print, log, write or commit API keys, tokens, passwords or OAuth token files (~/.config/colab-cli/token.json); the owner does the one-time OAuth login himself. (owner rule; engine/tools/colab/README.md; bundle:san_juan/RUN_COLAB.md) [owner]
- Never sign in to ElevenLabs with any account but the one the owner designates, and never with the owner's other Google accounts; in Google or Colab computer-use never click consent or Allow dialogs or change sign-in settings, and stop and report at any password, 2FA or captcha prompt. (owner rule; bundle:lake_peigneur_v4/COLAB_OPERATOR_STEPS_v4.md) [owner]
- Never route traffic through random gateways, proxies or relays, and never install unofficial mods. (owner rule) [owner]
- Never change billing, a plan or a paid setting, buy credits, or start or extend paid compute without the owner. (owner rule; engine/tools/colab/README.md cost note) [owner]
- Never call a vidIQ tool unless the task explicitly allows it; credits are very limited, so spend them only on outlier pulls and keyword checks, after vidiq_balance. (ctx 'Tools you can use'; the whole ep02 hunt used one call, hunt ranked[hawaii-without-ocean].demand) [owner]
- Never commit or push other channels' thumbnails, frames, contact sheets or feed screenshots: keep them in the scratchpad (refs/, feeds/) and commit only text, data and our own images. Autosave must filter by name and folder. (2026-11-08: an autosave pushed 106 competitor thumbnails from the niche study; removed in commit 1282012, still in older history because a force push needs the owner's OK) [owner]
- Never write to the owner's Google Drive or push files to public temp hosts (litterbox, temp.sh) without asking first, even where a plan says to keep files on Drive; never use drive.mount from an agent (the Colab token has drive.file scope only and returned 403). (owner rule; look section 7; scratch:colab/drive_upload.log; bundle:lake_peigneur_v4/pkg/COLAB_RUN_v4_HU.md) [owner]
- Never publish a monetised video whose narration, music cues or SFX were made with ElevenLabs on a free tier (non-commercial licence); engine/tools/music.py generates the music through the ElevenLabs music API, so the licence check covers music as well as voice. Confirm the paid plan with the owner or re-make the audio first. (bundle:bats/PLAN.md section 8; engine/tools/music.py) [reviewed]

## 2. Research method (how to choose a topic with data)

### DO (proven)

- Read small-sample Studio data for direction, not decimals: first work out views from impressions (impressions x CTR) and how many clicks each percentage rests on. (ep01: 43 views, about 20 from impressions; Browse 8.82% = 3 clicks; hunt lessons.topic_rules; ctx) [measured]
- Calibrate agent retention panels against real analytics: subtract about 15 points from a panel's predicted AVD (n = 1 video, 43 views, direction only; re-calibrate after ep02), treat the casual phone lens as the base case, and when a panel praises something YouTube's own analysis of our video criticises, follow YouTube. (for the published 15:34 v3 the panels predicted 39-40% and the real figure was 24.7%; for the 16:51 v2 cut they had predicted 35.7%; the panels praised the hook menu, the mid-film ask and the corridor set; R6/synthesis; ctx) [measured]
- Probe supply and saturation with the free ep01/tools/ytsearch.py (no key, unlimited) when pitching, weekly until upload (section 18) and again on decision day. (owner credit rule; brief section 1 re-probe 2026-11-08) [owner]
- Pick topics with independent judges (click, story, feasibility) plus a red-team pass on each finalist; prefer the finalist that sits in every judge's top 3 and whose fixes are all in our own control. (Hawaii 218, the only finalist in all three top 3s; hunt verdicts; brief section 1) [reviewed]
- Get competitor frames from https://i.ytimg.com/vi/ID/hq1.jpg, hq2.jpg and hq3.jpg, plus a vidIQ watch only when credits are allowed. (vu cites 'ZWZWjXTnyEQ hq1-hq3') [measured]
- Read primary documents page by page and log the printed page for each claim; when curl gets 403 use a text fetch, and record which sources actually loaded. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_facts.md URL load check) [reviewed]
- Before script lock, list what the 3 closest competitor videos show and plan one visible upgrade over each: a fact they got wrong or hyped, a story spine, phone legibility, a live 3D reveal; the full checks are in section 18. (many small-channel outliers are mass-produced and prove demand, not a quality bar; ctx vidIQ note; brief section 3 'Our edge over the drain clones is a story arc') [hypothesis]

### DONT (banned)

- Never run yt-dlp or sb2sheet.py storyboards against YouTube; it hits the bot check. (incident in the ep02 playbook task; engine/tools/sb2sheet.py still assumes yt-dlp) [measured]

## 3. Topic

### DO (proven)

- Greenlight a topic only on proven demand: at least 3 host videos on the same place or premise with 500K+ views, one under 3 months old and still gaining 300+ views/hour; if search is under about 50K/month, build the packaging purely for the Suggested feed. (ep01: 93% Suggested, 9 search impressions; Hawaii hosts 7.07M, 3.64M, 3.04M; ctx; hunt lessons T5; brief section 1) [benchmark]
- Pick a premise a viewer can retell in one sentence: an absurd-but-true twist or a 'what is hidden' reveal with one crisp answer. (San Juan topic 9.0; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md; brief one-sentence answer) [reviewed]
- Pick topics whose payoff is a photoreal spatial change our engine renders (drain, ice removal, before/after coastline, true-size overlay, cut-away) and whose story holds 5-7 such reveals; an argument is never the payoff. (ep01's only praised moment was the antipode overlay; Antarctica Without Ice 1.8M on 2.9K subs; ctx; hunt lessons T2) [reviewed]
- Give every topic a US anchor; say scale in US units and familiar comparisons (feet, miles, football fields, Manhattan) and show them as true-scale props or outlines in the 3D scene. (US viewers were 28% of ep01 views but 43% of watch time: about 12 of 43 views, direction only; ctx; vu diag.bench 'Show scale with familiar objects') [hypothesis]
- Make the climax the least-claimed true number: search the climax claim with ytsearch.py, place it at 85-90% of runtime, and keep a fact that mega-view Shorts already spent as a mid-film beat. (Everest fact spent by a 17M Short; Mauna Loa's 56,000 ft had only 38K and 1.4K videos; hunt finalists[hawaii-without-ocean].red; brief sections 3, 7) [reviewed]

### DONT (banned)

- Never choose a long-form topic because zero long-forms cover it or because a Short on it did well. (ep01 was chosen on '0 long-form videos' plus a 27M Short and got 9 search impressions, 0 clicks; ep01/research/brief.md section 1; ctx) [measured]
- Never pick a subject that cannot be pictured from 3 words or that needs many places or the whole globe at once; it must be one named place, object or event that fills a third of a phone frame at regional zoom. (ep01 spread over 7 landmasses; mobile AVD 2:11, 14.1%; ctx; hunt lessons T1, T8) [measured]
- Never structure a film as the history of an idea; tell one protagonist or event with a turning point and real stakes. (ep01 ran through 7 thinkers; hunt lessons T4) [measured]
- Never name more than 3 people in a film or more than 1 new named person per chapter. (hunt lessons T4, C5) [hypothesis]
- Reject a topic whose honest one-sentence answer is 'partly', 'not entirely' or 'scientists still debate it'. (ep01 'They're not. Not entirely.'; hunt lessons T3 and curated.dropped) [reviewed]
- Reject a topic if 2 or more recent, well-made 1M+ long-forms tell the same story from the same angle; before script lock watch the closest competitors and cut any reveal they already show (section 18). (Eddystone, Northwest Angle and Zuiderzee dropped; hunt curated.dropped; brief sections 1, 12) [benchmark]
- Never build a premise on a live news number that can flip before we publish; prefer evergreen subjects and date-stamp any live number. (Lake Powell rose 21.5 ft after its record low; hunt finalists[lake-powell-drained].red) [reviewed]
- Never choose or open with subjects where humour is off-limits or taste is risky (living residents of a tragedy, child deaths). (Kalaupapa dropped, the Laupahoehoe cold open cut; hunt curated.dropped; brief section 4 must-fix 5) [reviewed]

## 4. Facts

### DO (proven)

- Keep a fact spine per episode with a primary-source URL (USGS, NOAA, NPS, the official report) for every narrated claim and on-screen string, status keys [V] primary, [V2] two sources, [S] secondary only, [!] conflicting, [X] never; narrate only V, V2 and S, use [S] only for non-numeric context (never for a hero number, a title claim or a payoff line), use [!] only as a hedge or range, and close every VERIFY item before script lock (narrate the neutral version until then). (brief sections 4, 12; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_facts.md; script fidelity 9.5) [reviewed]
- Before voicing, run an adversarial fact-check of every segment and on-screen string and fix every overclaim ('first', 'the proof', 'the best explanation') to match the evidence. (ep01 red team found 8 of 109 segments wrong; ep01/research/redteam.json) [reviewed]
- Follow the primary document when popular secondary sources contradict it, and keep the disputed detail out of the narration. (award signed in Berlin per FRUS 1872, not Geneva; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Word disputed or modelled numbers so a pedant cannot fault them ('more than', 'about', 'from its true base', 'could become'), present modelled events as modelled, skip hype such as mega-tsunamis, and narrate every drain as a thought experiment ('if we drained it'). (hunt red kill shot 10; brief section 4; look section 8 B3) [reviewed]
- Use limiting words exactly where the science is limited, with the latest dated counts ('some' bats see UV; '1,500-plus species', not the stale 1,400). (facts 6.5 to 8.5; bundle:bats/QC_bats_not_blind_2026-10-26.md) [reviewed]
- Quote only verbatim, verified words and mark every cut with an ellipsis; never put quotation marks around a paraphrase or add punctuation. (ep01 '1912: "THE CONTINENTS MOVE"' card, ep01/research/redteam.json s059; 2 of 12 Lake Peigneur quote cards truncated, bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md section 5b) [measured]
- Pin every place from an authoritative coordinate source (NPS places API, surveyed positions) and correct the script to it. (bundle:san_juan/BUILD_REPORT.md) [reviewed]
- Gate every land-bridge, join, lake or island label in a drain shot with sill.py flood-fill on the same DEM at the shot's water level, and let the narration follow the grid. ('LAND BRIDGE' at -300 m was false, 'ALBORAN SEA' mislabelled; look section 8 B2; ep02/lab/drain/tools/sill.py) [reviewed]
- Make the description's citation name the same edition and page that the video shows. (ep01 ledger p.232 vs shown p.239; ep01/research/redteam.json notes) [reviewed]

### DONT (banned)

- Never stack numbers. Terms: a hero number is one of the owner's 6-10 big vivid numbers per long-form, shown on screen as an image; a spoken number is any number said aloud, dates included. The one cap: in any 60 s window at most 2 spoken numbers, and at most 1 of them a hero number (a 25-35 s Short carries about 3 big numbers, section 14). (ep01 put 6 numbers in 53 s, R6/synthesis fix 6; San Juan's 461/14/64 beat was its biggest drop-off, bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md; hunt lessons C5, H8) [reviewed]
- Never drop a hedge in the punchline: if the setup says 'the best-known story says', the payoff keeps 'if that story is right'. (ep01/research/redteam.json s094) [reviewed]
- Never let an absolute word be false ('Nobody fired at anyone', not 'no shots were fired'; 'normally flows', not 'always flowed'). (bundle:san_juan/san_juan_pig_war_script_v2_2026-10-28.md wording rules; bundle:bats/QC_bats_not_blind_2026-10-26.md) [reviewed]
- Never speak a number the sources disagree on; say a round figure every source supports or drop it. (San Juan 461 vs 439 soldiers; facts 7.0 to 8.5; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Never take a number from explainer or listicle sites when it conflicts with the primary. (Lake Peigneur bans '$45 million', '55 workers' and every waterfall height; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_facts.md) [reviewed]
- Never state single-source, interested-party or 'reportedly' material as fact or quote; cut it or attribute it by name. (San Juan 'Jacob' and the potato line; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Never assert a cause the official investigation left undetermined, in title, thumbnail or narration. (MSHA could not determine the Peigneur cause; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v2.md) [reviewed]
- Never show or say a join, split, land bridge, lake, island, border or object position the data does not support; draw geometry only from verified datasets, use surveyed positions, and mark unsourced shapes approximate or leave them out. (Kaho'olawe join and 'nearby' Midway carriers, hunt red kill shots 3-4; Rosario Strait line omitted, bundle:san_juan/BUILD_REPORT.md) [reviewed]
- Never show a place or thing before it existed in the story's timeline. (English Camp, founded March 1860, shown in June 1859 beats; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Never write an absolute claim in a title or description that was not checked item by item. ('Quote cards reproduce the source wording exactly' was false; bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md sections 5b, 7) [measured]

## 5. Story and script

### DO (proven)

- Keep a loop ledger: plant an open loop in the cold open, give every planted line a scheduled payoff timestamp, and leave none unpaid at lock. (ep01 Bacon 1:15 paid at 10:23, praised by all 4 lenses; R6/synthesis keep list; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v2.md) [reviewed]
- Show the answer to the title question as visible animated proof of at least 3 s under the exact sentence that states it. (ep01 'They're scars' drift ran in 1.1 s; R6/SUMMARY.md S7-6; R6/finish_ch5a) [reviewed]
- Give the emotional peak a real pause of at least 1.2 s and slower narration (speed about 0.9). (Wegener death beat rated the peak; R6/synthesis keep and fix 22) [reviewed]
- Write for about 153 wpm with sentences of 15 words or fewer, at most 2 new ideas per minute and the numbers cap in section 4 (at most 2 spoken numbers, dates included, in any 60 s), every idea shown on screen, and quotes under 10 words used only when the picture shows the action. (ep01 chapter 1 had 5 names, 5 dates, 2 statistics; hunt lessons H8, C5, C6; brief section 7) [hypothesis]
- Re-hook every 60-90 s (a reveal, a change of place, an in-world gag or a new open question) and make each chapter top the last; use 5-6 chapters of 2-3 min, chapter 1 at most 1:30. (ep01 had 9 chapters averaging 1:44; brief section 7 has 17 re-hooks; hunt lessons C7, C8) [hypothesis]
- Target 12:30-14:00 (aim 13:00; at about 153 wpm including pauses that is about 1,900-2,000 words), hard ceiling 15:00; a longer film needs its own hero shot for every extra minute. (ep01 ran 15:34 with 4:50 after its answer; hunt lessons.target_length; the brief's 1,930 words fits) [hypothesis]
- Plan a second engine for the second half: when the repeating reveal bottoms out, switch to a new device with its own counter (drain half, then a '+ million years' time-machine half). (hunt finalists[hawaii-without-ocean].red kill shot 1, fix 2) [hypothesis]

### DONT (banned)

- Never land the biggest, final answer to the core question before about 85% of the runtime, and after it add nothing but the final line and the hand-off (no recap, extra section or speculative coda). This is not withholding: pay part of the thumbnail promise by 0:30 and a real payoff every 60-90 s. (ep01 answered at 59-69% and ran 4:50 more; hunt lessons C9, E1; ctx) [reviewed]
- Never spend more than about 60 s on 'who noticed it first' before the first answer; pay off the first hook promise by 2:00. (ep01 roll-call 1:39-2:55, first payoff at 4:09; R6/synthesis fix 1) [reviewed]
- Never read a list twice or restate a statistic in a second sentence; each fact is said once, with one image. (v3 cut 19 s of re-reads; R6/edl_v3.json; R6/synthesis fixes 6, 11) [reviewed]
- Never open a new topic or tangent after the title question is answered. (the Nevada drip after both payoffs was cut, 17.9 s; R6/synthesis fix 9) [reviewed]
- Never read more than 3 new proper nouns in any 10 s, and give each its own visual event on its word. (7 names in 9 s over a still map; R6/panel_fatigue; R6/synthesis fix 2) [reviewed]
- Never explain an abstract mechanism for more than about 20 s; use one physical metaphor in motion ('a bowling ball on a mattress') with no jargon on screen. (hunt finalists[hawaii-without-ocean].red kill shot 7, fix 8) [reviewed]

## 6. Hook

### DO (proven)

- Make frame 1 the thumbnail image in motion, with no logo, title card or intro sting. (Contour Atlas opens on its gag at 0:01; vu diag.bench; hunt lessons H1-H3, P6) [benchmark]
- Open with a flat, concrete statement (person, place or object plus the twist) of 12 words or fewer, voice starting at 0.0-0.2 s and landed before 3 s, with the hook text already on frame 0. (San Juan hook 7.5 to 8.5 with 'A farmer shot a pig, and the Royal Navy showed up.'; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md; bundle:bats/QC_bats_not_blind_2026-10-26.md) [reviewed]
- State the myth the way the viewer believes it, break it with a short, unhedged line before 0:30, and state the central question in the title's own words by 0:15. (ep01 broke its myth at 0:28.9, panel consensus 68% at 0:30; R6/synthesis keep; brief section 6) [reviewed]
- Make the first 10 s work with the sound off: motion plus one big label. (home-feed autoplay starts muted; hunt lessons H1-H3) [benchmark]
- Open close, at regional zoom, with clear motion from frame 0 (the first motion graphic before frame 10) and a new visual event every 2-3 s in minute 1. (ep01 frames 0-90 were identical; R6/synthesis fix 2; 79.4% of ep01's first 131 s was near-black, vu diag.audit finding 1) [measured]

### DONT (banned)

- Never put a menu, roadmap or teaser stack in the hook ('along the way', 'by the end you'll know'); allow one forward promise at most, the story's own question. (YouTube's critique of ep01 0:37-0:54; ctx) [reviewed]
- Never put historical asides, quotes, Latin, static portraits, book pages or idea-history dates in the first 2 minutes. (about 44% of ep01's first 131 s was static paper and portraits; vu diag.audit finding 3; ctx) [measured]
- Never hold back the first hero shot past 0:30; show the best photoreal reveal by 0:14-0:30, then a new hero shot every 1.5-2 min. (ep01's best shot came at 2:40, after phone viewers left at 2:11; hunt lessons H4, V4; ctx) [hypothesis]
- Never use more than 2 named people, 1 date and 1 number in 0:00-1:00, or sentences over 15 words (12 in the first 30 s). (ep01 chapter 1 packed about 5 names and 5 dates; hunt lessons H8; brief section 6) [hypothesis]
- Never open on a near-still frame, a slow whole-globe drift or a small globe in black. (ep01's opening globe was a 190 px disc in 390 px of black; vu diag.audit finding 1) [measured]
- Never open with a question; use a statement claim. (one QC remark, bundle:bats/QC_bats_not_blind_2026-10-26.md) [hypothesis]
- Never exaggerate in the hook, and never open without a person or concrete subject on screen. (San Juan v1 'pointed cannons' scored 7.5; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]

## 18. Competitive edge (how we stand out next to the competitors)

The owner wants every film to stand out clearly next to its competitors in the Suggested feed. These checks make that testable. All are [hypothesis] until our Studio numbers (CTR, AVD) confirm them; then move them to [measured] with the numbers.

### DO

- Run a reveal audit before script lock: list every reveal, with timecodes, in the 3 closest competitor videos (ep02: Unseen Works' Pacific drain, Below The Map's Hawaii video and the closest Contour Atlas drain). Our film must have at least 3 hero reveals that none of them shows, and any overlap is cut or re-angled. Save the audit in the episode's research folder. (hunt curated.dropped; brief sections 3, 12; LESSONS_LOG.md ep02 open items) [hypothesis]
- Put a 'real number' beat in every film: the popular figure first, then the sourced, truer figure as an image (ep02: Mauna Loa about 56,000 ft from its true base, USGS, against the height above sea level everyone quotes). It is the Myth Juice brand promise, and clone channels, which repeat the popular figure, are weakest here. (brief sections 3-4; hunt finalists[hawaii-without-ocean].red) [hypothesis]
- Strip-test the opening as well as the thumbnail: place our frames at 0:00, 0:10 and 0:30 at 390 px wide next to the 3 closest competitors' hq1-hq3 frames; ours must be brighter (mean luma 85 or more) and carry fewer, larger words. (ep01 mean luma about 40 against benchmarks of 105-166; vu diag.audit finding 6; section 2 frame fetching) [hypothesis]
- Keep brand devices the same across episodes, so a Suggested viewer recognises the channel: the persistent gauge, the JUICE CHECK verdict stamp, the antipode-style hero highlight (hero orange, white outline, dimmed surroundings) and one title grammar of our own that is not a clone template (section 13). (the antipode overlay and the stamp were the praised devices; ctx; R6/synthesis) [hypothesis]
- Move fast on a premise: re-probe with ytsearch.py every week until upload; if a same-premise video passes 100K views, re-angle the film before the voice is recorded. (the 'We Drained X' title was cloned lake by lake with falling views; hunt lessons P3; brief section 1 re-probe) [hypothesis]
- Log a strip-test score per episode in LESSONS_LOG.md: the thumbnail's rank in the strip, opening-frame luma and word counts against the 3 competitors, and the count of unique hero reveals, so the edge can later be checked against real CTR and AVD. (How to update, step 3) [hypothesis]

## How to update this playbook

After every task, before the next one starts:

1. Add what worked to the right section's DO list, with its evidence, source path and tag.
2. Add what failed to the DONT list the same way.
3. Move a [hypothesis] or [benchmark] rule to [measured] only when our own YouTube numbers (Studio, Test & Compare) confirm it, and add those numbers to its evidence.
4. When a new rule contradicts an old one, apply the precedence above and move the loser to Superseded (PLAYBOOK_production.md) with the reason.
5. Log the episode's or task's results in LESSONS_LOG.md (what was made, real numbers, what worked, what failed, rules added).
6. Keep Read this first at 10 items; change it only for a new non-negotiable.
7. Keep each playbook file small enough to read whole (about 15K tokens, about 35 KB); when one grows past that, split it and update the file list at the top.
8. Commit PLAYBOOK.md, PLAYBOOK_craft.md, PLAYBOOK_production.md and LESSONS_LOG.md (never secrets or large media); push (owner request, 2026-11-08); never push secrets, personal data, other channels' images or unreleased video.
