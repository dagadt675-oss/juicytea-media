# Myth Juice playbook

The permanent rulebook for every Myth Juice long-form and Short. Read it before any work. Last merged 2026-11-08 from ep01, the ep02 planning and the older projects (Lake Peigneur, San Juan Pig War, Bats Short).

## Read this first

1. Owner rules beat everything here: no publishing or visible channel change without his OK, never mention AI, no secrets in output or git, billing only with him, no Drive writes without asking, reply in Hungarian.
2. No false claims: every narrated or on-screen fact has a primary source in the fact spine before it is voiced.
3. Pick a proven premise (a moving host cluster of 500K+ videos) with one phone-sized subject, a crisp unhedged answer and an unspent payoff.
4. Beat the competitors on what the clone channels skip: true facts, a real story spine, phone-first craft and live photoreal 3D reveals.
5. Package for the Suggested feed: one focal subject, 3 words or fewer, a 35-50 character title; it must beat ep01's 1.97% Suggested CTR in a side-by-side pre-test.
6. Phone first: judge every frame at phone size; must-read text 64 px cap or more at 1080p; the subject fills a third of the frame; bright frames.
7. Story first: no menu in the hook, first hero shot by 0:30, a re-hook every 60-90 s, the answer at 85-90%, no tail after it.
8. Something moves every second: a new visual event every 3-5 s, nothing static over 2 s, never black mid-film.
9. 6-10 big numbers per film, never stacked; no sources, citations or emojis on screen; narration by Rodney, never Brian.
10. 7 rebuilt Shorts per long-form (never clips), each with hook, payoff and seamless loop. After every task update this file and LESSONS_LOG.md.

## Tags and source keys

- [owner] the owner's own instruction (always wins); [measured] our own numbers (YouTube Studio, ffprobe, loudness, frame scans); [reviewed] found by a QC or review pass on our own work; [benchmark] seen in competitor or 1M-view videos; [hypothesis] planned, not yet proven by us.
- Conflicts: the owner's newest instruction wins; otherwise measured beats reviewed beats benchmark beats hypothesis. Rules that lost are listed under Superseded at the end. Do not revive them.
- ep01/ = longform/ep01-continental-drip/; ep02/ = longform/ep02-hawaii/; R6/ = ep01/research/review6/ (R6/synthesis, R6/voice_audio and R6/panel_* are the wf_96e8f33f-afb__*.json files; R6/fix_chN and R6/finish_chN are the wf_*__fix_chN.json and wf_*__finish_chN.json files).
- ctx = ep02/research/context.md (ep01 Studio numbers and YouTube's critique); brief = ep02/research/brief.md; hunt = ep02/research/topic_hunt.json; vu = ep02/research/visual_upgrade.json; look = ep02/research/visual/visual_plan.md.
- bundle:PATH = the owner's Drive bundle of the older projects (Lake Peigneur, San Juan Pig War, Bats Short), 2026-10-29, cited by original file path; not in the repo.
- scratch:PATH = ep01 session logs in the agent scratchpad; not in the repo and may be gone.

## 1. Owner rules and security

### DO (proven)

- Report to the owner in Hungarian, short and useful: about 300-360 words with the decision, why it is better, the honest weak points and the next date; keep paste-ready YouTube blocks (title, description, tags, pinned comment) in English. (owner rule; examples ep02/research/osszefoglalo_hu.md, ep01/release/metadata.md) [owner]
- Hold every long-form to the owner's content rules: storytelling first, 6-10 big vivid numbers, no emojis, funny scenes with real animation (at least one per chapter), ElevenLabs narration, credits only in the description. (owner rule; ctx 'The channel') [owner]
- Read the ElevenLabs key only from the ELEVENLABS_API_KEY environment variable, loaded from the owner's secrets file outside the repo, and pipe every Colab CLI output through `sed -E 's#(token|code|access_token|refresh_token)=[^& ]+#\1=***#g'` before it reaches a log. (owner rule; engine/tools/tts.py, music.py, engine/tools/colab/bg.sh, cx.sh, upload_parts.sh) [owner]
- Use only official clients and pinned packages: google-colab-cli from pip, the REST API at api.elevenlabs.io, playwright@1.63.0, faster-whisper. (owner rule against gateways and mods; engine/tools/colab/vm_setup.sh) [owner]
- Stop paid compute the moment its job is done (colab stop -s mj after the last chunk is downloaded and md5-checked; L4 costs 1.94 compute units/h) and confirm nothing is left running. (owner billing rule; engine/tools/colab/README.md; bundle:san_juan/RUN_COLAB.md) [owner]
- After every video and every review round, add what worked to DO and what failed to DONT in this file, with evidence and path, and commit before the next video starts. (owner rule; brief section 11 maps 25 ep01 problems to ep02 fixes) [owner]

### DONT (banned)

- Never publish, upload, schedule or post anything (YouTube, Instagram, vidIQ upload or update tools, Metricool, any platform) and make no visible channel change (title or thumbnail swap, Test & Compare, pinned comment, end screen, settings) without the owner's explicit OK for that specific action. (owner rule; ep01/release/metadata.md; brief section 5 lists actions that need it) [owner]
- In computer-use sessions never open YouTube or send e-mail, and end every QC or operator report by stating that nothing was posted, scheduled or deleted. (bundle:lake_peigneur_v4/COLAB_OPERATOR_STEPS_v4.md; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [owner]
- Never mention AI anywhere: narration, on-screen text, titles, descriptions, tags, thumbnails, comments, replies, channel page; no '(No AI)' or 'AI-free' tags. Before hand-off grep every release text for AI, artificial, generated, ElevenLabs, Claude and synthetic and require zero hits. (owner rule; ep01/research/bench_packaging.md (b); ep01/release/metadata.md) [owner]
- Never use AI image or video generators for any shot; build every shot in the engine. (Lake Peigneur v2 planned 3 generated stills, all removed in v3; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_production_table.md) [owner]
- Never print, log, write or commit API keys, tokens, passwords or OAuth token files (~/.config/colab-cli/token.json); the owner does the one-time OAuth login himself. (owner rule; engine/tools/colab/README.md; bundle:san_juan/RUN_COLAB.md) [owner]
- Never sign in to ElevenLabs with any account but the one the owner designates; in Google or Colab computer-use never click consent or Allow dialogs or change sign-in settings, and stop and report at any password, 2FA or captcha prompt. (owner rule; bundle:lake_peigneur_v4/COLAB_OPERATOR_STEPS_v4.md) [owner]
- Never route traffic through random gateways, proxies or relays, and never install unofficial mods. (owner rule) [owner]
- Never change billing, a plan or a paid setting, buy credits, or start or extend paid compute without the owner. (owner rule; engine/tools/colab/README.md cost note) [owner]
- Never call a vidIQ tool unless the task explicitly allows it; credits (150 a month) go only to outlier pulls and keyword checks, after vidiq_balance. (ctx 'Tools you can use'; the whole ep02 hunt used one call, hunt ranked[hawaii-without-ocean].demand) [owner]
- Never write to the owner's Google Drive or push files to public temp hosts (litterbox, temp.sh) without asking first, even where a plan says to keep files on Drive; never use drive.mount from an agent (the Colab token has drive.file scope only and returned 403). (owner rule; look section 7; scratch:colab/drive_upload.log; bundle:lake_peigneur_v4/pkg/COLAB_RUN_v4_HU.md) [owner]
- Never publish a monetised video voiced on an ElevenLabs free tier (non-commercial licence); confirm the paid plan with the owner or re-voice first. (bundle:bats/PLAN.md section 8) [reviewed]

## 2. Research method (how to choose a topic with data)

### DO (proven)

- Read small-sample Studio data for direction, not decimals: first work out views from impressions (impressions x CTR) and how many clicks each percentage rests on. (ep01: 43 views, about 20 from impressions; Browse 8.82% = 3 clicks; hunt lessons.topic_rules; ctx) [measured]
- Calibrate agent retention panels against real analytics: subtract about 10 points from a panel's predicted AVD, treat the casual phone lens as the base case, and when a panel praises something YouTube's own analysis of our video criticises, follow YouTube. (panels predicted 35.7%, real 24.7%; the panels praised the hook menu, the mid-film ask and the corridor set; R6/synthesis; ctx) [measured]
- Probe supply and saturation with the free ep01/tools/ytsearch.py (no key, unlimited) when pitching and again on decision day. (owner credit rule; brief section 1 re-probe 2026-11-08) [owner]
- Pick topics with independent judges (click, story, feasibility) plus a red-team pass on each finalist; prefer the finalist that sits in every judge's top 3 and whose fixes are all in our own control. (Hawaii 218, the only finalist in all three top 3s; hunt verdicts; brief section 1) [reviewed]
- Get competitor frames from https://i.ytimg.com/vi/ID/hq1.jpg, hq2.jpg and hq3.jpg, plus a vidIQ watch only when credits are allowed. (vu cites 'ZWZWjXTnyEQ hq1-hq3') [measured]
- Read primary documents page by page and log the printed page for each claim; when curl gets 403 use a text fetch, and record which sources actually loaded. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_facts.md URL load check) [reviewed]
- Before script lock, list what the 3 closest competitor videos show and plan one visible upgrade over each: a fact they got wrong or hyped, a story spine, phone legibility, a live 3D reveal. (many small-channel outliers are mass-produced and prove demand, not a quality bar; ctx vidIQ note; brief section 3 'Our edge over the drain clones is a story arc') [hypothesis]

### DONT (banned)

- Never run yt-dlp or sb2sheet.py storyboards against YouTube; it hits the bot check. (incident in the ep02 playbook task; engine/tools/sb2sheet.py still assumes yt-dlp) [measured]

## 3. Topic

### DO (proven)

- Greenlight a topic only on proven demand: at least 3 host videos on the same place or premise with 500K+ views, one under 3 months old and still gaining 300+ views/hour; if search is under about 50K/month, build the packaging purely for the Suggested feed. (ep01: 93% Suggested, 9 search impressions; Hawaii hosts 7.07M, 3.64M, 3.04M; ctx; hunt lessons T5; brief section 1) [benchmark]
- Pick a premise a viewer can retell in one sentence: an absurd-but-true twist or a 'what is hidden' reveal with one crisp answer. (San Juan topic 9.0; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md; brief one-sentence answer) [reviewed]
- Pick topics whose payoff is a photoreal spatial change our engine renders (drain, ice removal, before/after coastline, true-size overlay, cut-away) and whose story holds 5-7 such reveals; an argument is never the payoff. (ep01's only praised moment was the antipode overlay; Antarctica Without Ice 1.8M on 2.9K subs; ctx; hunt lessons T2) [reviewed]
- Give every topic a US anchor; say scale in US units and familiar comparisons (feet, miles, football fields, Manhattan) and show them as true-scale props or outlines in the 3D scene. (US viewers were 28% of ep01 views but 43% of watch time; ctx; vu diag.bench 'Show scale with familiar objects') [measured]
- Make the climax the least-claimed true number: search the climax claim with ytsearch.py, place it at 85-90% of runtime, and keep a fact that mega-view Shorts already spent as a mid-film beat. (Everest fact spent by a 17M Short; Mauna Loa's 56,000 ft had only 38K and 1.4K videos; hunt finalists[hawaii-without-ocean].red; brief sections 3, 7) [reviewed]

### DONT (banned)

- Never choose a long-form topic because zero long-forms cover it or because a Short on it did well. (ep01 was chosen on '0 long-form videos' plus a 27M Short and got 9 search impressions, 0 clicks; ep01/research/brief.md section 1; ctx) [measured]
- Never pick a subject that cannot be pictured from 3 words or that needs many places or the whole globe at once; it must be one named place, object or event that fills a third of a phone frame at regional zoom. (ep01 spread over 7 landmasses; mobile AVD 2:11, 14.1%; ctx; hunt lessons T1, T8) [measured]
- Never structure a film as the history of an idea; one protagonist or event with a turning point and real stakes, at most 3 named people per film and 1 new named person per chapter. (ep01 ran through 7 thinkers; hunt lessons T4) [measured]
- Reject a topic whose honest one-sentence answer is 'partly', 'not entirely' or 'scientists still debate it'. (ep01 'They're not. Not entirely.'; hunt lessons T3 and curated.dropped) [reviewed]
- Reject a topic if 2 or more recent, well-made 1M+ long-forms tell the same story from the same angle; before script lock watch the closest competitors and cut any reveal they already show. (Eddystone, Northwest Angle and Zuiderzee dropped; hunt curated.dropped; brief sections 1, 12) [benchmark]
- Never build a premise on a live news number that can flip before we publish; prefer evergreen subjects and date-stamp any live number. (Lake Powell rose 21.5 ft after its record low; hunt finalists[lake-powell-drained].red) [reviewed]
- Never choose or open with subjects where humour is off-limits or taste is risky (living residents of a tragedy, child deaths). (Kalaupapa dropped, the Laupahoehoe cold open cut; hunt curated.dropped; brief section 4 must-fix 5) [reviewed]

## 4. Facts

### DO (proven)

- Keep a fact spine per episode with a primary-source URL (USGS, NOAA, NPS, the official report) for every narrated claim and on-screen string, status keys [V] primary, [V2] two sources, [S] secondary only, [!] conflicting, [X] never; narrate only V, V2 and S, use [!] only as a hedge or range, and close every VERIFY item before script lock (narrate the neutral version until then). (brief sections 4, 12; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_facts.md; script fidelity 9.5) [reviewed]
- Before voicing, run an adversarial fact-check of every segment and on-screen string and fix every overclaim ('first', 'the proof', 'the best explanation') to match the evidence. (ep01 red team found 8 of 109 segments wrong; ep01/research/redteam.json) [reviewed]
- Follow the primary document when popular secondary sources contradict it, and keep the disputed detail out of the narration. (award signed in Berlin per FRUS 1872, not Geneva; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Word disputed or modelled numbers so a pedant cannot fault them ('more than', 'about', 'from its true base', 'could become'), present modelled events as modelled, skip hype such as mega-tsunamis, and narrate every drain as a thought experiment ('if we drained it'). (hunt red kill shot 10; brief section 4; look section 8 B3) [reviewed]
- Use limiting words exactly where the science is limited, with the latest dated counts ('some' bats see UV; '1,500-plus species', not the stale 1,400). (facts 6.5 to 8.5; bundle:bats/QC_bats_not_blind_2026-10-26.md) [reviewed]
- Quote only verbatim, verified words and mark every cut with an ellipsis; never put quotation marks around a paraphrase or add punctuation. (ep01 '1912: "THE CONTINENTS MOVE"' card, ep01/research/redteam.json s059; 2 of 12 Lake Peigneur quote cards truncated, bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md section 5b) [measured]
- Pin every place from an authoritative coordinate source (NPS places API, surveyed positions) and correct the script to it. (bundle:san_juan/BUILD_REPORT.md) [reviewed]
- Gate every land-bridge, join, lake or island label in a drain shot with sill.py flood-fill on the same DEM at the shot's water level, and let the narration follow the grid. ('LAND BRIDGE' at -300 m was false, 'ALBORAN SEA' mislabelled; look section 8 B2; ep02/lab/drain/tools/sill.py) [reviewed]
- Make the description's citation name the same edition and page that the video shows. (ep01 ledger p.232 vs shown p.239; ep01/research/redteam.json notes) [reviewed]

### DONT (banned)

- Never stack numbers: at most 2 hero numbers in any 60 s window and 6-10 in a long-form (about 3 in a Short), each turned into an image. (ep01 put 6 numbers in 53 s, R6/synthesis fix 6; San Juan's 461/14/64 beat was its biggest drop-off, bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md; owner rule) [owner]
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
- Write for about 153 wpm with sentences of 15 words or fewer, at most 2 new ideas and 1 spoken number per minute, every idea shown on screen, and quotes under 10 words used only when the picture shows the action. (ep01 chapter 1 had 5 names, 5 dates, 2 statistics; hunt lessons H8, C5, C6; brief section 7) [hypothesis]
- Re-hook every 60-90 s (a reveal, a change of place, an in-world gag or a new open question) and make each chapter top the last; use 5-6 chapters of 2-3 min, chapter 1 at most 1:30. (ep01 had 9 chapters averaging 1:44; brief section 7 has 17 re-hooks; hunt lessons C7, C8) [hypothesis]
- Target 12:30-14:00 (aim 13:00, about 1,950-2,100 words), hard ceiling 15:00; a longer film needs its own hero shot for every extra minute. (ep01 ran 15:34 with 4:50 after its answer; hunt lessons.target_length) [hypothesis]
- Plan a second engine for the second half: when the repeating reveal bottoms out, switch to a new device with its own counter (drain half, then a '+ million years' time-machine half). (hunt finalists[hawaii-without-ocean].red kill shot 1, fix 2) [hypothesis]

### DONT (banned)

- Never answer the core question before about 85% of the runtime, and add no recap, extra section or speculative coda after it. (ep01 answered at 59-69% and ran 4:50 more; hunt lessons C9, E1; ctx) [reviewed]
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
- Never hold back the first hero shot past 0:30; show the best photoreal reveal by 0:14-0:30, then a new hero shot every 1.5-2 min. (ep01's best shot came at 2:40, after phone viewers left at 2:11; hunt lessons H4, V4; ctx) [measured]
- Never use more than 2 named people, 1 date and 1 number in 0:00-1:00, or sentences over 15 words (12 in the first 30 s). (ep01 chapter 1 packed about 5 names and 5 dates; hunt lessons H8; brief section 6) [measured]
- Never open on a near-still frame, a slow whole-globe drift or a small globe in black. (ep01's opening globe was a 190 px disc in 390 px of black; vu diag.audit finding 1) [measured]
- Never open with a question; use a statement claim. (bundle:bats/QC_bats_not_blind_2026-10-26.md) [benchmark]
- Never exaggerate in the hook, and never open without a person or concrete subject on screen. (San Juan v1 'pointed cannons' scored 7.5; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]

## 7. Pacing

### DO (proven)

- Cut or add a new visual event every 3-5 s (every 2-3 s in minute 1), average shot 4-4.5 s or less; change shot scale every 5-7 s, alternate the subject between the left and right thirds, and fly point to point in 1.5-3 s with easing. (ep01 longest uncut stretch 32.2 s; Contour Atlas 3.5-4.2 s per shot; vu diag.audit finding 11; hunt lessons C1, C2) [measured]
- Pause unevenly: 0.2-0.5 s inside a chapter, about 0.4 s after a turn line, 0.7-1.1 s before key reveals, 1.5-1.8 s after big beats, and 0.8-0.9 s chapter gaps around a 0.8-1.1 s card. (Lake Peigneur gaps of 1.06-1.50 s left holes at all 6 cards, bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md open item 4; R6/voice_audio) [measured]

### DONT (banned)

- Never hold one composition longer than 7 s (10 s for a live drain whose level and camera keep moving), a frozen frame for 1.5 s or more (freezedetect -45 dB), or a near-static run over 2 s (still_s mean frame difference under 0.15). (ep01 cuts 10.99 s apart on average, up to 84.8 s, ep01/research/qc_v3.json; 36 s of one image in Lake Peigneur, bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md sections 2, 4; look section 9) [measured]
- Never put a subscribe, like or comment ask, or a Juice Check/Subscribe graphic, inside the story; no call-to-action graphic before the last 20 s. (YouTube: the 4:57-5:07 ask broke the flow before the strongest reveal; subs +0; ctx; vu diag.audit finding 9) [reviewed]
- Never cut or blink to black mid-film, and never show more than 8 frames of black except after the last frame; keep the outgoing scene drawing until the incoming fade ends. (1.43 s of black at 0:53 read as buffering; R6/synthesis fix 3; R6/finish_ch6 S10-3; engine/ENGINE.md) [reviewed]

## 8. Visuals

### DO (proven)

- Judge every draft and every review pass at phone size (a 480x270 downscale or a 390x219 sheet), not only on a desktop frame. (ep01 AVD: mobile 2:11 (14.1%) vs TV 8:24 (54.1%); ctx) [measured]
- Build the film as one visual world: photoreal Earth stages (globe, DEM terrain and seafloor, paper cut-outs on the map) as WORLD, then one shared POST grade, then a crisp UI layer drawn after post, so labels, outlines, arrows, numbers and hero fills never pass through bloom, DOF, tonemap, vignette or grain. (YouTube criticised ep01's stylised corridor; 12 visual languages in 15 min; vu diag.audit finding 4; look section 1.1, U1; ep02/lab/globe/cineglobe.js) [reviewed]
- Make tilted full-bleed oblique and terrain shots the signature look for 60% or more of runtime. (74% of ep01 frames were at least 45% near-black, only 7.1% full-bleed; vu diag.audit finding 1; look section 3) [measured]
- Keep story shots at mean luma 70/255 or more, the film at 85-130, near-black pixels (luma under 18) at 15% or less, and no run over 4 s below luma 40; show a night-side globe only when the city lights are the point. (ep01 mean luma about 40; benchmarks 105-166; vu diag.audit finding 6; look section 2) [measured]
- Make whatever the narration names fill at least a third of the frame width (aim for 50-70% of frame height), and every highlighted shape at least 25 px wide on a 390 px phone frame (about 120 px at 1080p); otherwise move closer or add an inset zoom. (ep01's Florida highlight was 6-8 px on a phone; look section 2; hunt lessons T8, C4) [measured]
- Draw hero highlights in the antipode style: hero orange #FF5A36, one hero shape per frame, 55-66% fill, 5-6 px white outline, soft glow, surroundings dimmed and desaturated. (YouTube called the antipode overlay 'remarkably vivid and professional', ctx; look sections 1.2, 9) [reviewed]
- Use the look-book palette: water and second colour #3DE3FF, numbers, arrows and gauge #FFD23F, text #F4F6FA, red #E8412C sparingly for danger, a navy gradient #0B1D28 to #05070D for space (never flat black), a sky gradient on obliques. (look section 1.2) [reviewed]
- Prove key claims with 3D data overlays on the photoreal globe, and keep the overlay and a two-item key on screen for the whole spoken claim. (the antipode overlay first showed for 1.2-1.5 s and was fixed to hold 3:47.7-3:53.5; R6/SUMMARY.md S3-8; R6/finish_ch2) [reviewed]
- Show change live on one fixed camera (drain, flood, ice peel, time slider) for 4-10 s while the gauge ticks and a riser plays. (the live drain took the panel teen from 3 to 8; vu panel drain; vu diag.bench findings 3-4) [reviewed]
- Give each film one persistent gauge for its one changing variable (sea level, depth, year) in a fixed corner at 12-15% of frame height, in the same place in every mode for the chapter, ticking while it moves. (Contour Atlas WATER LEVEL widget; vu diag.bench finding 3) [benchmark]
- Anchor every visual event to the narration word timings: highlights land 2-4 frames before their key word and nothing lands more than 0.2 s after it; a counter never passes through wrong values and a label never covers its own pin. (ep01 lags of 0.4-2.8 s; R6/SUMMARY.md; ep01/research/bench_visual.md section 3; bundle:lake_peigneur_v4/pkg/COLAB_RUN.md section 7) [reviewed]
- Make every animation physically and geographically true to the story: objects follow real paths and corridors, sink and vanish where the narration says, and drained water exposes a muddy, cracked bed, never a black patch. (owner's second-by-second review of Lake Peigneur v2 found 12 such defects; bundle:lake_peigneur_v4/pkg/COLAB_RUN.md section 7) [reviewed]
- Render terrain at vertical exaggeration 1.0 in every shot that compares heights and at most 2x elsewhere (2x default), never mix values within a shot, and say 'heights exaggerated' once in the narration when above 1.0. (3x looked like crumpled foil and game terrain; vu panel drain; look sections 8 B3, 9) [reviewed]
- Reuse the paleo-globe module for deep time (GPlates snapshots, a continuous front, a zipper, named-plate gags), with a highlight and a trail-laying tip marker on each moving plate. (the Gondwana breakup was 'the best animation in the film'; R6/synthesis keep; R6/panel_fan) [reviewed]
- Show public-domain archival stills full-bleed and always moving (Ken Burns 1.5-3% per 10 s) in the shared grade: at most 3 s per still, 5 s per clip and 1 per minute, never a static portrait under an aside, and back to an animated scene within 10 s. (vu diag.audit finding 3; R6/panel_casual; look section 4 S12) [reviewed]
- Join consecutive shots that share subject and framing (within about 25%) with one continuous camera move or an 8-frame dissolve (assemble_edl.py --xfade J:8), never a hard cut, and never dissolve between differently sized globes in under 0.5 s. (S1-3, S8-2, S6-3; R6/SUMMARY.md; scratch:engine/finalize_v3b.log) [reviewed]
- When a 3D character is used, match the clip's playback speed to its root speed, check its travel direction with a foot logger, and accept the shot only when the stance foot drifts 4 px/frame or less. (7 major character defects, after fixes 0.5-3.6 px/frame; R6/SUMMARY.md; R6/fix_ch1) [measured]
- Draw chapter cards last (on top) with a near-opaque navy veil, a 1.1 s hold and a 0.26 s dissolve. (owner review of Lake Peigneur v2; bundle:lake_peigneur_v4/pkg/COLAB_RUN.md section 7 item 1) [reviewed]
- Pad equirect overlay bounds to plus or minus 181.5 degrees and fill each ring's -360/0/+360 copies into one opaque mask before tinting. (lib/globe.js drops pixels outside u (0,1), leaving a date-line hairline; ep02/lab/type/shots.js; commit 79e272e) [measured]
- Fix satellite tile seams (different Esri acquisitions) with the water-seam polish or a lake-mask blur before compositing. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_production_table.md; bundle:san_juan/BUILD_REPORT.md caveat 7) [reviewed]
- Keep any flashing at 3 flashes per second or fewer. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_production_table.md) [benchmark]

### DONT (banned)

- Never let an element appear or vanish in a single frame: enter and exit over at least 6 frames (fade, scale or wipe) unless it is a deliberate stamp with its own SFX, and never hide a moving or visible element with a visibility toggle. (18 of 97 round-6 findings were pops; R6/SUMMARY.md) [measured]
- Never use a small centred globe on black as the default shot: whole-globe-in-space shots at most 10% of runtime and 4 s each, filling the frame height, with clouds at 0-0.35 and off the subject on globes that carry a fact. (vu diag.audit finding 1; vu panel globe) [measured]
- Never cut a stylised, differently lit set into the photoreal film: no gradient voids, low-poly or Kenney block-kid scenes or flat-vector interiors (paper people only in ep02); any figure stands on the real terrain at 35-40% of frame height or more, same sun, soft contact shadow. (YouTube on ep01's 7:35-7:50 corridor, ctx; vu diag.audit finding 5; look section 9) [reviewed]
- Never open a scene on an empty or near-empty frame; no blank lead-in over 6 frames under narration. (12:55.87 empty navy frame 'looks like a missing render layer'; R6/synthesis fix 8) [reviewed]
- Never move a character's root while it plays Idle, and never cut away from Roll or another acrobatic clip before it ends; play it once:true at speed = clip duration / path time, then crossfade to Idle over about 0.25 s. (S10-2, S3-4, S5-3; R6/fix_ch3) [measured]
- Never spin a globe faster than about 14 degrees per frame at its peak, and add sub-frame motion blur to any high-contrast pan over about 20 px/frame. (a 38 degrees/frame spin strobed; R6/finish_ch6 S10-6, S10-11) [measured]
- Never use one shot template more than twice in a film; give every list item its own transition. (four future models in one template; R6/synthesis fix 17; R6/panel_fan) [reviewed]
- Never use grids, thumbnail mosaics, 4-way split screens, overlapping pins, ghosted texture backgrounds or colour legends; state colour meaning with coloured headline words and show lists as full-frame tilted shots joined by whip-pans (1-1.5 s per quick item, 4-7 s per explained item). (ep01's 12:00 thumbnails were 36x24 px on a phone; vu diag.audit findings 6, 10) [measured]
- Never draw a meaningful line thinner than 6 px at 1080p or a meaning-carrying icon at about 30 px or smaller: lines get a 9-12 px core with a dark under-stroke 8 px wider plus glow, arrows a 15 px body and a 50-63 px head, outlines 5-6 px, pins a radius of 11 px or more, and every line draws on with a moving head dot. (ep01 strokes were 3-5 px, about 1 px on a phone; vu diag.audit finding 12; R6/synthesis fix 18) [measured]
- Never ship compositing or render artefacts: inset globes masked to their disc with a soft rim, overlays kept off characters, graphics kept inside their tiles, and no camera-sun specular smudge, additive blob sprites, dark smears as text plates, rectangle-clipped fills, texture seams or hairlines; check every overlay at full resolution. (S4-4, S5-2, S8-4, R6/SUMMARY.md; vu diag.audit finding 7) [measured]
- Never show mock documents, fake papers with grey dash 'text' or placeholder graphics; use a real public-domain scan cropped to 5 big words or fewer, or tell the moment on the map. (ep01's 'THE DRIP, REVISITED' mock paper risked a false claim; vu diag.audit finding 8) [reviewed]
- Never leave crossfade ghosts: clear the previous beat's elements before a card's plate appears, and hard-cut between contiguous diagram beats. (bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md item 7) [measured]
- Never use a stock clip without a per-file licence check on the day of use (Pexels and Pixabay are not CC0; Wikimedia varies), and never film or franchise clips. (bundle:bats/bats_not_blind_script_v2_2026-10-26.md) [reviewed]

## 9. Text and graphics

### DO (proven)

- Size text by cap height at 1080p with ep02/lab/type/type.js: must-read text (place labels, name plates, gauge titles) 64 px or more (about 13 px on a phone), connectors at least 48 px, headlines in Anton at 96-120 px with at most 4 words. (ep01 caps were 26-35 px, 5-7 px on a phone; the type prototype took the panel teen from 2 to 8; vu diag.audit finding 2; look sections 2, 9) [reviewed]
- Use one type system: Anton for headlines and numbers, Barlow Condensed 800 caps for labels, #F4F6FA text on a rectangular rgba(6,9,15,0.86) plate with an 8 px accent bar in the colour of the thing it names, and always a plate (not just a scrim) on bright terrain or sky. (look sections 1.2, 1.3, 9) [reviewed]
- Show 6-10 big vivid numbers per long-form, each landing on its spoken word as a rolling counter in Anton at 150-190 px cap height (14-18% of frame height). (owner rule; look section 2) [owner]
- Show at most one text block plus one map label plus the gauge (10 visible words or fewer); keep must-read text in the top 62% of the frame (above y=670 at 1080p), out of the top 8%, inside a 5% safe margin and in the third opposite the subject; rotate 3-4 layouts. (phone controls cover the bottom; vu diag.tech finding 1; vu panel type; look section 2) [reviewed]

### DONT (banned)

- Never show sources, citations, author-year names, page numbers, data credits, 'real NASA data', 'computed from data' or 'SIMPLIFIED' lines on screen; say a simplification once in the narration and put every credit only in the description. (owner rule; ep01 'DIETZ & HOLDEN (1970)' at 11:40, vu diag.audit finding 8; older 'MSHA 1981, p.21' tags, bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v3.md) [owner]
- Never use emojis anywhere: on screen, titles, descriptions, thumbnails, Shorts titles, pinned comments or replies. (owner rule; ctx 'The channel') [owner]
- Never use grey on-screen text, pill-shaped labels, Bebas or near-transparent plates. (ep01 grey 'NEARLY 9 IN 10 OF US' and an unreadable pill at 5:20; vu diag.audit finding 2; look section 1.3) [reviewed]
- Never drop a qualifier ('MOST OF', 'NEARLY', 'ABOUT', 'FROM ITS TRUE BASE') to fit a word cap; use a kicker of up to 2 words or show the share as a number. (type prototype overclaim, blocker B1; look section 8) [reviewed]
- Never let text overlap another graphic, label, headline or subtitle, leave its container or appear twice; every text element sits inside its panel with padding, centred on its own panel, with a dark backing on bright ground. (S6-12, S8-3, S3-7, S2-8, R6/SUMMARY.md; bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md open items 2-3) [measured]
- Never show a readable caption or gag card for less than 2 s, and never bring it in after its spoken word or the joke. (the 'ACUMINATI' pill showed for 0.7 s; R6/SUMMARY.md S1-6; R6/synthesis fix 17) [reviewed]
- Never show more than one time counter per sequence or a counter over a picture that does not change with it; fade each number out before the next label fades in. (the 10:00-10:13 counter restarted, 'wait, is it repeating?'; R6/synthesis fix 10) [reviewed]
- Never stop a highlighter sweep mid-word: reveal whole words and end the marker 6 px or more past the last glyph. (3 cards cut mid-word; bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md item 13; bundle:lake_peigneur_v4/pkg/CHANGES_v4.md) [measured]

## 10. Humour

### DO (proven)

- Land one dry, true punchline every 60-90 s exactly on a cut, with a 1.0-1.4 s music dip of -9 to -12 dB (mix.json 'dips', 0.25 s ramps) right before it. (ep01 gag rhythm praised by all 4 lenses; R6/panel_fatigue; ep01/audio/mix_v3_cut.json) [reviewed]
- Put a 2-6 s in-world visual gag about every 2 minutes, made with real animation on the real terrain (paper standee hop, drain plug, true-size drag that does not fit, whip-pan to the punchline); give every funny line its own visual and use comic SFX only on gags. (the Wegener hop scored 8/10 with the teen; vu panel story; vu diag.bench finding 6) [reviewed]
- Build jokes only from verified facts delivered deadpan, and keep 1-2 sourced reserve jokes for length cuts. (San Juan humour 8.0; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Use the JUICE CHECK stamp (FALSE / TRUE / IT'S COMPLICATED) only as an on-the-word verdict beat, about 4 per film at most, never paired with a call to action. (praised as the brand device; the stamp plus SUBSCRIBE at 4:57 was faulted; R6/synthesis; ctx) [reviewed]
- Use paper cut-outs of real public-domain photos for human beats, at most 1-1.5 min per film: clean matte (erode 2-3 px, no spill), a warm off-white 2-4 px paper edge, a fold-out base tab, a soft contact shadow, a pop-up hinge starting at 30-40 degrees, landing on the true coordinates. (vu panel story; look sections 4 S10-S11, 8, 9) [reviewed]

### DONT (banned)

- Never place gags, comic SFX or music stings over deaths, disasters or war graves; treat wrecks as war graves, with no gore and no 'treasure' framing. (hunt red kill shot 5; brief sections 4, 7, 12) [reviewed]

## 11. Audio, voice and music

### DO (proven)

- Narrate every long-form and Short from ep02 on with ElevenLabs 'Rodney - Clear Educator' (voice_id eY2VJs4Gi8QKG2RV01sS, model eleven_v4), passed explicitly ('voice' in segments.json or --voice), and budget scripts at about 153 wpm (13:00 is about 1,950-2,000 words). (owner decision 2026-11-08; ctx; ep02/README.md) [owner]
- Generate narration only after the owner OKs the script text, then re-time every beat, caption and camera key from the real word timings, never from the wpm estimate. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v2.md; bundle:bats/QC_bats_not_blind_2026-10-26.md) [owner]
- Assemble narration with tts.py: trim each take to first character -60 ms and last character +90 ms with 8 ms fades, give each segment an explicit pause, and place {m:name} markers so counters and reveals land on the spoken word. (no clipped first phoneme in 109 takes; engine/tools/tts.py; R6/voice_audio) [reviewed]
- Set a per-take speed: about 0.9 for somber beats and the central question, about 1.05 for montages, never above 1.05; split each key-statistic line into its own take after a 0.5 s pause. (all 109 ep01 takes used default speed; R6/voice_audio; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v3.md) [reviewed]
- Write ElevenLabs text with no break or bracket tags and numbers spelled as spoken (stability about 0.35, style about 0.4); test-render hard names first and respell only in the VO text, never on screen. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v3.md) [reviewed]
- ASR-check every take with faster-whisper small.en and medium.en on the voice stem and the mix (ffmpeg-decoded to 16 kHz); accept a take only when names and payoff lines come back as scripted, and fix a misheard name by regenerating the take (bump 'take', tts.py --force id) within 0.15 s of the old length or by pasting the same word from another take with 15 ms equal-power crossfades. ('Wegener' heard as 'Wedner' in 6/6 passes; engine/tools/asr_check.py, vo_fix.py; R6/voice_audio) [measured]
- After TTS, silence every stray next-word false start at take tails: any voiced burst under 250 ms after 300 ms or more of silence, with 10 ms fades and nothing moved in time (vo_fix.py), or stop sending next_text for sentence-final takes. (7 of 109 takes had one, e.g. '[Nei-]' on the death beat; R6/voice_audio; engine/tools/vo_fix.py) [measured]
- Put a comma after a word whose final stop the voice swallows ('a bent card, dipped in water'), then confirm with ASR. (heard as 'bent car' in 4/4 passes; R6/voice_audio) [hypothesis]
- Keep music under the whole film without a hole but change the cue at every chapter card: beds at -9 dB, ducked -11 dB under the voice (attack 0.08 s, release 0.6 s), 14-19 dB under speech, 2.5 s fade-in and 3 s fade-out crossfades overlapping by 3 s, and no silence of 0.3 s or more below -45 dB. (ep01 10 chapter cues cleared by the audio check, R6/voice_audio, ep01/audio/mix_v3_cut.json; continuous bed, bundle:lake_peigneur_v4/pkg/COLAB_RUN.md section 5) [reviewed]
- Back-time the last music cue so its file ends on the film's last frame, and bring the opening theme back after the last word. (ep01 music ended 7 s early until commit 162d236; ep01/audio/mix_v3_cut.json) [measured]
- Request each ElevenLabs music cue at least 3 s longer than its window (music.py dur+3) and require audio_scan.py ends_early = false. (m02 still ended 0.76 s early; R6/voice_audio) [measured]
- Tie a sound cue to every visual device (whoosh on flights, ticks under counters and the gauge, impact on reveals, riser and rumble on drains, paper flap and thunk on standees): one SFX per visible event, 10-12 dB under the voice, ambience beds at -26 to -28 dB, no copyrighted music. (vu diag.bench keep; look section 6 U13; bundle:bats/PLAN.md section 6) [reviewed]
- Allow impact hits under reveal words only when their energy sits below about 300 Hz (impact_deep at -6 to -10 dB) and the voice keeps 15 dB or more at 1-4 kHz. (R6/synthesis disagreement 3) [measured]
- Place comedic SFX in the gap after the line, 0.8 s or shorter at about -16 dB, never over the line's last words. (a record scratch at -14 dB rose 5.8 dB above the voice; R6/voice_audio) [measured]
- Master to -14 LUFS integrated with mix.py's 4x-oversampled look-ahead true-peak limiter at -1.5 dBTP, and gate the final file at -14 plus or minus 1.5 LU and a true peak of -1.0 dBTP or lower. (ep01 -14.0 LUFS, TP -1.4; ep01/research/qc_v3.json; engine/tools/mix.py, qc_video.py; bundle QC files) [measured]

### DONT (banned)

- Never use Brian (nPczCjzI2devNBz1zQrb); engine/tools/tts.py and ep01/tools/tts.py still fall back to him at line 68, so always pass Rodney explicitly or change the default. (owner decision 2026-11-08; ctx) [owner]
- Never let a 30 s narration window exceed 165 wpm, or a take run more than 15% above the film's median syllable rate, least of all on a key statistic. (take s035 ran 27% over the median on the 1-in-8 statistic; R6/SUMMARY.md; R6/panel_casual) [reviewed]
- Never run one unchanged music bed for more than about 2 minutes or across a chapter change under dense narration. (bed m03 ran 3 min across two chapters where fatigue began; R6/synthesis fix 16) [reviewed]

## 12. Ending

### DO (proven)

- End on one sentence that answers the thumbnail question over the final hero shot (or a callback to the frame-0 shot), then within 0-3 s hand off by voice to one specific, already published channel video phrased as a new question, and cut to the end screen about 1 s after that line. (YouTube advised a concrete hand-off; ep01 had none and got 0 comments, 0 shares; ctx; brief section 9; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v3.md) [reviewed]
- Show end-screen elements only after the last word and hold the end screen 10-12 s (15 s at most) over a shot that is still moving. (ep01's WATCH NEXT box appeared before the last word, then 12 s of near-static hold; vu diag.audit finding 9; R6/SUMMARY.md) [measured]
- Put any comment prompt in a pinned comment as a story-tied opinion question, never a generic ask. (brief sections 5, 9; hunt lessons E5) [hypothesis]

### DONT (banned)

- Never promise a 'next story' unless that video or playlist already exists when the end screen goes live. (ep01 promised an Africa episode that did not exist; R6/synthesis fix 13) [reviewed]
- Never put a recap or a 'so is it just X?' summary before the last promised payoff, and never end on a recap list of facts; at most one closing line before the final beat. (ep01's 30 s recap at 84% read as the ending, R6/synthesis fix 5; San Juan's list ending scored 6.0, bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]

## 13. Packaging (title, thumbnail, description)

### DO (proven)

- Pre-test every title and thumbnail pair before upload: mock it in dark mode at 390x220 pt, 168x94 px and 120 px next to the 5 strongest Suggested competitors; if it is not the brightest, most readable card in the strip, redo it or use the no-text variant. (ep01 Suggested CTR 1.97% on 93% of impressions; ctx; brief section 5) [hypothesis]
- Make the thumbnail an honest, stronger render of a real shot from the film showing the before or partial state of the hero reveal; use that composition as frame 1 in motion, pay off part of the promise within 30 s and return to the same camera, subject and accent colour for the payoff. (breakout drain thumbnails are stronger versions of their films' shots; vu diag.bench; hunt lessons P6, P7, V7) [benchmark]
- Let the thumbnail text add a different angle to the title, never repeat it. (bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_v3_title_description.md; thumbnail 8.5 in bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md) [reviewed]
- Write a 35-50 character title that states the 'what', with the proper noun in the first 3 words and one concrete noun the viewer can picture; reuse the host cluster's key nouns in our own sentence and keep exact search phrases in the description and tags. (niche outlier median 51 characters, compact cards cut at about 45; hunt lessons P2, P3; brief section 5) [benchmark]
- Test 3 thumbnails in Test & Compare (with the owner's OK) and judge nothing before about 10K impressions: judge on Suggested CTR (target 5%+) and watch time per impression = CTR x AVD (ep01 5.2 s, target 15 s+); change one variable at a time, never title and thumbnail on the same day, and if impressions stall below about 3K after 72 h make one change and wait 72 h. (hunt lessons P8, P9; brief section 5) [measured]
- Write the description with the subject in the first line and the core fact in sentence 1, one CTA line, 3-5 relevant hashtags, and chapters from 0:00 (at least 3, each 10 s or longer, ascending, within 1 s of the on-screen cards). (YouTube Help checked 2026-10-28; bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md section 5c) [benchmark]
- Title every chapter in the story's own words, matching the on-screen chapter card word for word (a question works well), never naming the answer and never 'Intro' or 'Conclusion'. (ep01 chapters mismatched the card and put the answer in the progress bar; R6/synthesis fix 12; ep01/release/metadata.md; hunt lessons C8) [reviewed]

### DONT (banned)

- Never reuse ep01's packaging pattern: abstract question text over a flat dark map with arrows and a '?' ring, plus a 'Why X (Not Just Y)' title; every new pair must beat ep01's 1.97% Suggested CTR. (925 impressions, CTR 2.27%, Suggested 1.97% on 862; ctx; ep01/release/thumb_B_pointing_at_what.jpg) [measured]
- Never ship a thumbnail with more than one graphic device, more than 3 words or a navy- or dark-dominated background: one focal subject fills 50% or more, 40% or more of the area is bright or saturated, each text line is at least 20% of the thumbnail height, white on a black box with one accent word. (ep01's thumbnail had about 5 competing elements on dark navy; hunt lessons P5; vu diag.bench finding 1) [measured]
- Never build the curiosity gap on an abstract question the viewer did not have; withhold one concrete thing they already want to know (what is at the bottom, the tip of what). (ep01 'POINTING AT WHAT?'; hunt lessons P4) [measured]
- Never use a title over 50 characters or with hedge words ('Not Just', 'Sort Of', 'Maybe', 'Kind Of'). (ep01 55 characters with a hedge, CTR 2.27%; hunt lessons P2) [benchmark]
- Never copy an incumbent's exact title words or a template clone channels are farming. ('We Drained X. Here's What Was Hidden at the Bottom.' was cloned lake by lake with falling views; hunt lessons P3; brief section 4 must-fix 6) [reviewed]
- Never put wording on a thumbnail or title stronger than the facts. ('GONE IN 3 HOURS' became 'DRAINED IN ~3 HOURS'; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_v3_title_description.md) [reviewed]

## 14. Shorts

### DO (proven)

- Make exactly 7 Shorts per long-form, each a full-value vertical piece rebuilt from the long-form's scenes, 3D assets and facts with its own composition, camera, order, jokes and narration, rendered with render_chunks.py --w 1080 --h 1920 (own chunk dir EP_1080x1920); never change the long-form because of the Shorts. (owner rule; engine/tools/render_chunks.py) [owner]
- Give every Short a genius hook on frame 1 (already moving, subject instantly readable, one headline of 4 words or fewer in the upper third at 64 px or more, readable with the sound off), a genius payoff that lands its own fact, and a seamless loop whose last frame and line flow back into the first. (owner rule; brief section 10; bundle:bats/PLAN.md section 7) [owner]
- Build the loop seam: the last 0.5 s of picture matches frame 0, camera keys are cyclic (same value and slope at both ends), animation cycles are retimed to whole numbers, frame 1 is not duplicated at the end, audio is cut at the last word with a 5-8 ms fade and beds crossfade tail into head; require first/last-frame MAE of about 5/255 or less, then concatenate the Short with itself, run temporal_scan.py and require no 'cut' or 'flash' at the join. (San Juan MAE 4.4/255, bundle:san_juan/BUILD_REPORT.md; bundle:bats/STATUS.md; git 40a9083) [measured]
- Write the last line so it flows grammatically into the hook ('...tell them this:' into 'A farmer shot a pig...') and record 2 takes of it with an open, rising end. (bundle:san_juan/san_juan_pig_war_script_v2_2026-10-28.md; bundle:bats/QC_bats_not_blind_2026-10-26.md) [reviewed]
- Keep Shorts at 25-35 s (net 4.2-4.5 syllables/s) with about 3 big numbers, and name a cut line in advance for a real VO over 36 s; never cut the hook or the loop line. (San Juan length 5.5 at 45-50 s to 8.5 at 33.9 s; bundle:san_juan/QC_san_juan_pig_war_2026-10-28.md) [reviewed]
- Show the first visual event by 2 s and a new one at least every 3 s; at the mid-video dip put a 'guess before the reveal' question with a 0.4-0.55 s pause covered by the longest smooth camera move. (bundle:bats/QC_bats_not_blind_2026-10-26.md doomscroll table; bundle:bats/PLAN.md section 1) [reviewed]
- Shoot each Short as one continuous eased camera move with no cuts (San Juan: one C2 spline, max pan 8.4 px/frame, max zoom 1.97%/frame). (owner rules applied in bundle:bats/PLAN.md; bundle:san_juan/BUILD_REPORT.md) [owner]
- Caption Shorts with 1-3 words per card, ALL CAPS, Anton at 56-66 px or more, white with one active-word colour (cyan #00E5FF, never yellow on a yellow map), synced within 0.1 s to the word times, no card shorter than 0.3 s. (bundle:san_juan/san_juan_pig_war_script_v2_2026-10-28.md; bundle:bats/PLAN.md section 3) [reviewed]

### DONT (banned)

- Never cut, crop or clip a Short out of the long-form, even when a brief or a review suggests it. (ep01/research/brief.md section 6, R6/synthesis fix 13 and brief section 10 all proposed clips; owner rule) [owner]
- Never end a Short on teaser copy ('The full film is linked', 'Full story on the channel'); every Short has its own payoff and loop ending. (brief section 10; bundle:lake_peigneur_v4/orig/LONGFORM_lake_peigneur_script_v3.md Shorts teaser; owner rule) [owner]
- Never show more than 2-3 elements at once; check the widest beat on a test still before the full render. (clutter at 25 km; bundle:san_juan/san_juan_pig_war_script_v2_2026-10-28.md; bundle:san_juan/BUILD_REPORT.md caveat 4) [reviewed]
- Never put anything but captions in the bottom 20% of a 1080x1920 frame (y 1536 or more); centre captions at 64-72% of the height and keep all text at x 900 px or less. (captions at 79% may sit in the Shorts UI; bundle:bats/PLAN.md sections 2-3; bundle:bats/STATUS.md) [reviewed]

## 15. Production pipeline and rendering

### DO (proven)

- Make every frame a pure function of the frame index: set every uniform and runtime-toggled three.js state on every frame, and set material.needsUpdate = true when material.transparent changes (only on change). (the 1875 globe dropped to half brightness at the chunk 22/23 seam, ratio 12.4; commit 25aa800; R6/finish_ch2) [measured]
- Render long-forms only through engine/tools/render_chunks.py in restart-safe 450-frame chunks (tmp_NNNNN.mp4, ffprobe frame-count check, atomic rename to c_NNNNN.mp4, finished chunks skipped, 20 s heartbeat locks so a forward and a --reverse runner share one dir); after any interruption re-run the same command. (61 of 68 chunks re-rendered with no lost or short chunk; scratch:engine/finalize_v3.log) [measured]
- Run final renders on a Colab L4 with GPU=1 (fails fast unless the WebGL renderer is NVIDIA, discards one warm-up frame); set up each VM with engine/tools/colab/vm_setup.sh (NVIDIA EGL ICD, playwright@1.63.0, --use-gl=angle --use-angle=gl-egl) and render only after glcheck prints 'ANGLE (NVIDIA Corporation, NVIDIA L4...'. (32 s per chunk, a 16-min film in 14-15 min at --par 4, against 6-8 h locally; engine/tools/colab/README.md; scratch:colab/full.log) [measured]
- Render all chunks of one master on the same renderer (the GPU from ep02 on); never swap a SwiftShader chunk into a GPU set. (they differ by up to 5.1/255 on flat-map and photo scenes; ep01/research/colab_vs_local_chunks.json) [hypothesis]
- Drive Colab safely: start long jobs detached (run_bg.py), give every colab exec an explicit --timeout, never pipe a long remote command into head, touch the session every 4 min (keepalive.sh), and download each chunk with an md5 check (3 tries). (engine/tools/colab/README.md; scratch:colab/full.log) [measured]
- Before any Colab run prove the package is self-contained (unzip to a clean folder, re-render stills byte-identically with cmp), render with checkpoints and version-suffix every output so earlier versions are never overwritten. (bundle:san_juan/BUILD_REPORT.md; bundle:lake_peigneur_v4/pkg/CHANGES_v4.md) [measured]
- Make the shared tools episode-agnostic before rendering ep02 (vm_render.sh, redo_v3.sh, finalize_v3.sh and qa_sheet.sh hardcode ep01 values); compute chunk i's frames as min(450, N - 450*i). (grep of engine/tools on 2026-11-08) [hypothesis]
- Re-render chunks into a separate redo dir, verify each redo chunk's frame count before the swap, move replaced chunks to chunks/old_vN, and delete old_vN only after the new master passes QC. (engine/tools/redo_v3.sh, finalize_v3.sh; scratch:engine/finalize_v3.log) [measured]
- Fix pacing in post with edl.py before any re-voicing: cut only at joins on digital silence that keep a 0.25-0.45 s pause, keep every planted line, move picture, narration, SFX and captions together, keep music on the main timeline, fade joins over 8 ms, and regenerate chapters and end-screen times from report.json. (ep01 v3 removed 77 s with no new narration or render; retention effect unproven at 24.7% AVD; R6/edl_v3.json; ep01/tools/edl.py) [measured]
- In assemble_edl.py seek half a frame early (-ss (k-0.5)/30) and cut the exact count with trim=end_frame=N, build holds with tpad clones on the range's own stream, append settb=1/30,setpts=N after every range, concat and xfade node, and clamp every range end to the source's real nb_frames. (commits 907a75b, 3eeb674, 758024e; ep01/tools/assemble_edl.py) [measured]
- Interpolate every element driven by data sampled at discrete steps (paleo snapshots, path points, looping chevrons) so nothing jumps between frames; verify with phase correlation (residual jitter about 1 px or less). (S7-3, S10-13, S6-9; R6/finish_ch5a; R6/finish_ch6) [measured]
- Build each camera move as one eased segment with the ease on the destination key (shots.js camAt ignores an ease on keys[0]), and check that its velocity curve has one peak and no interior stops. (S2-2 whip stopped and restarted; R6/fix_ch1; R6/SUMMARY.md) [measured]
- Use a normalised outExpo that reaches exactly 1 at t=1, t => t >= 1 ? 1 : (1 - 2^(-10t)) / (1 - 2^-10), for every slide-in. (stock lib/fx.js outExpo left a 1-1.5 px twitch; R6/fix_ch3) [measured]
- Name the exact chapter id in a test render's 'only' filter ("only":"ch5a"); a bare number renders background only. (R6/finish_ch5a; R6/finish_ch5b) [measured]
- Prove every animation fix on a test render of the changed frames before marking it done; record the render file, frame numbers and what was measured, and keep prev_notes.md plus a diff so a successor can resume. (the first S7-5 fix failed and was caught on a render; R6/finish_ch5a; ep01/research/RUN_IDS.md) [measured]
- Render review stills (frame 0, each beat, last frame, loop seam) and get the owner's OK before the full video render. (bundle:san_juan/RUN_COLAB.md) [owner]
- Use only ready-made assets with a known free licence (CC0: Quaternius, Kenney, Poly Pizza, Poly Haven, Kenney/OGA SFX; public domain: Natural Earth; OFL fonts; Sonniss GDC) and write each file's licence and exact source filename into a repo file the moment it is chosen. (San Juan lost its sprite list in a box reset; bundle:san_juan/BUILD_REPORT.md; bundle:bats/PLAN.md section 8; engine/ASSETS.md) [reviewed]
- Keep at least 5 GB free before a full assembly; after the master passes QC delete split upload parts, superseded masters, old chunk sets and x264 pass logs, and delete raw DEM and model downloads right after each bake. (disk 93% full on 2026-11-08 with 21 GB in the scratchpad; look section 7) [measured]

### DONT (banned)

- Never drive anything drawn with Math.random, Date.now or performance.now; seed with F.rng(seed) and seed grain with the frame index. (all 68 ep01 chunks matched across GPU and local; ep01/research/colab_vs_local_chunks.json; CONTRIBUTING.md) [measured]
- Never clamp an exit animation's progress at 1 while the element is still in frame; drive it until the bounding box is fully off-frame, then stop drawing. (S2-1 paper snagging on the edge, S2-4; R6/fix_ch1) [measured]
- Never render a full film locally; local SwiftShader is for draft stills (ss 1, post off), phone sheets and motion tests under 30 MB, deleted after review. (ep01 took 6-8 h locally; terrain stage 4.6 s/frame; look section 7) [measured]
- Never start parallel headless-Chromium renders without checking free memory; cap concurrent jobs so their total fits in RAM. (an OOM kill hit another agent's Chromium; scratch:review6/fix_ch4/prev_notes.md) [measured]
- Never master through two lossy steps at about 6.6 Mbps 4:2:0; from ep02 pipe frames at JPEG quality 0.98 or as raw RGBA, master at CRF 14-16, upload at 2560x1440 and keep grain at 0.02 or less until a compression test passes. (ffprobe of ep01 video_final.mp4; vu diag.tech finding 10; look section 7) [measured]
- Never use ctx.shadowBlur or ctx.filter on large canvas areas; use cached text sprites, layered strokes and down/up-scaled blur. (engine/ENGINE.md; ep02/lab/story/story.js line 39) [hypothesis]
- Never pass ep01's LOOK0 (specAmt .5, desat .12) into CineGlobe or stack the default vignette or grain on it; set EDIT.post = () => {} and pass only the keys a shot changes. (ep02/lab/globe/cineglobe.js lines 17-19; look section 8 X5) [hypothesis]
- Never use drive.mount on the owner's Colab account (blocked by 2-Step Verification); move files with files.upload(), files.download() or the Files panel, with a zip -0 fallback for big downloads. (bundle:lake_peigneur_v4/pkg/COLAB_RUN_v4_HU.md) [reviewed]
- If Blender is used, never final-render Cycles on the box (23-41 s/frame, about 8 h for 999 frames): render on Colab T4 OptiX at 48 samples or more, build and test in the Colab version (4.2.3), and read each GLB action's real key range before retiming loops. (bundle:bats/STATUS.md; bundle:bats/PLAN.md section 4) [measured]

## 16. QC gates

### DO (proven)

- Before any preview reaches the owner, run the motion-aware checks (temporal_scan.py for cuts, flashes, pops and seams; audio_scan.py; asr_check.py) and a per-segment frame-exact review; sampled contact sheets alone are not enough. (ep01 passed five sheet-based waves, then round 6 found 97 defects, 40 major; ep01/README.md; R6/SUMMARY.md) [measured]
- Run the measured battery on the actual file: ffprobe, ebur128, silencedetect (-45 dB, 0.3 s), freezedetect (-45 dB, 1.5 s), blackdetect (nothing black for 0.5 s or more, pix_th 0.08), no mid-film silence over 1.2 s, scene changes vs the chapter list (within 1 s), a 48-frame contact sheet checked by eye and a full-HD layout scan for clipping, safe zone and overlaps. (engine/tools/qc_video.py; bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md section 2) [measured]
- Fail any render with a [typeqc] FAIL; before sign-off review a 390x219 phone sheet of every shot's middle frame, run the brightness metrics at 5 fps and run a high-pass seam check. (ep01's sub-floor labels and dark stretches were caught only after release; vu diag.audit findings 2, 6, 7; look section 2, U3) [reviewed]
- Before any new shot type enters the film, render a 10-15 s motion test encoded at upload settings and watch it on a real phone (waterline and texture shimmer, grain and banding, comedy timing with sound). (all four ep02 prototypes were judged as stills only; look section 8 X1) [reviewed]
- Run temporal_scan.py on the raw chunk concatenation before any EDL cut and check every seam pair (frames 450k-1 and 450k): a diff ratio of 10 or more or a mean RGB shift over 0.5 levels is a state leak; ratio 4-9 with a shift of 0.4 or less is x264 keyframe noise. (5:45 seam ratio 12.4; benign seams in R6/SUMMARY.md) [measured]
- Extract frames for exact checks with passthrough decoding (ffmpeg -fps_mode passthrough); tools/grab.py labels frames one late until it is fixed. (all four fix agents; R6/finish_ch5b; R6/finish_ch4; R6/finish_ch6) [measured]
- After every assembly assert output frames = expected frames (ffprobe -count_frames), and run assemble_edl.py --test first. (28016 expected = 28016 read; scratch:engine/finalize_v3b.log) [measured]
- Gate every script and video at a weighted 8.0/10 or more (long-form: 10 areas, visuals and retention x2, divided by 12; Short script: hook and facts x2, divided by 9), and rewrite anything below 8 before production. (Lake Peigneur 8.00; San Juan 7.1 to 8.4; Bats 7.0 to 8.1; bundle QC files) [reviewed]
- Return QC fixes as one batched list split into MANDATORY and NICE-TO-HAVE, each with exact timecodes and target values (px, s, dB). (bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md section 6) [reviewed]

### DONT (banned)

- Never waive qc_video static flags as 'slow drifts'; release with zero static flags. (ep01 waived 25, including the 13:30-14:30 stillest minute the panels blamed; ep01/research/qc_final.json; R6/synthesis) [measured]
- Never send an unchanged file to re-QC; md5-check that the reviewed file is the new render. (Lake Peigneur 'v4' was byte-identical to v3; bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md header) [measured]
- Never let an agent claim an ear verdict; voice tone, music mood and SFX levels go to the owner to listen. (bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md header; bundle:bats/STATUS.md) [reviewed]
- Never chase ASR diffs that are only numerals, hyphens or quote marks, or correctly transcribed low-probability words; judge misheard names, swapped words and inserted bursts. (about 40 ep01 diffs were spelling only; R6/voice_audio) [measured]

## 17. Delivery

### DO (proven)

- Deliver to the owner, who uploads himself: the master, an upload copy, a separate English SRT (never burned in), three 1280x720 thumbnails for Test & Compare and a ready-to-paste metadata.md. (ep01/README.md Deliverables; ep01/release/metadata.md) [measured]
- Build the master with the assemble.sh / assemble_edl.py chain: light grade (eq contrast 1.04, saturation 1.06, colorbalance), BT.601 to BT.709 matrix conversion plus BT.709 tags, x264 slow High@4.2 aq-mode=3 at the CRF in section 15, AAC 320k 48 kHz, 30 fps CFR, yuv420p, equal A/V lengths, +faststart. (engine/tools/assemble.sh; ep01/research/qc_v3.json; Lake Peigneur tech 9.0, bundle:lake_peigneur_v4/QC_lake_peigneur_v4_full_2026-10-28.md section 1) [measured]
- Make size-capped copies only for transfer limits, with 2-pass x264 from the master and the audio copied: video kbps = cap_MiB x 8388.6 / duration_s - audio_kbps - 2% (upload copy under 500 MiB, chat copy 400 MiB or less). (ep01 upload copy 492,532,809 B; engine/tools/colab/README.md) [measured]
- Build captions with make_srt.py from the narration word timings (at most 2 lines of 42 characters and 6 s per cue, no overlaps) and re-run it on timing_cut.json after any post cut. (commit 950eb32; none of the 10 benchmark videos burn subtitles in, ep01/research/bench_visual.md section 2.4) [benchmark]
- Hand files over 400 MiB to the owner by uploading 40 MB parts to a Colab CPU session, md5-verifying the reassembled file there, giving him colab url -s up so he runs the two-line Drive copy cell himself, then stopping the session. (the 806,486,391-byte v3 master arrived with a matching md5; engine/tools/colab/README.md; commit 602e7bf) [measured]
- Put every credit in the description only: 'Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics)', GEBCO, SOEST HMRG, USGS, NOAA, NASA, Natural Earth, GPlates/EarthByte (Müller et al. 2019, CC BY 4.0), Quaternius/Kenney and each public-domain image; check Esri's terms before the first monetised upload. (engine/ASSETS.md; brief section 5; bundle:san_juan/BUILD_REPORT.md) [reviewed]

### DONT (banned)

- Never send a single file over 40 MB with colab upload (it returns HTTP 500); split -b 40m, upload each part with up to 4 retries, cat on the VM and compare md5s. (the 343 MB tar failed, then passed as parts; scratch:colab/upload.log; scratch:colab/upload_parts.log) [measured]

## Superseded (do not revive)

- Teaser stack or roadmap in the hook (ep01/research/brief.md '0:30-0:50 teaser stack', bench_structure.md): replaced by no menu in the hook (YouTube's ep01 critique).
- First subscribe ask at 35-45% (ep01/research/retention_checklist.md E): replaced by no call to action inside the story.
- On-screen authenticity, source or 'simplified' lines (bench_packaging.md rule 8, ep01 brief 'every number is computed on screen', engine/ENGINE.md 'mark as simplified', older on-screen source tags and Esri credit): owner rule, credits in the description only.
- '(No AI)' tags and an 'AI reconstruction' disclosure for generated stills: owner rule, never mention AI and never use generators.
- Caps of 4 big numbers (brief section 7) and 5 (hunt lessons C5): owner rule, 6-10 per long-form, at most 2 per 60 s.
- Narrators Brian (ep01, Bats Short) and Chris, and 'no fixed narrator, pick by Studio data': owner decision, Rodney from ep02 on.
- Shorts as clips or crops (ep01 brief 'cut 2 Shorts', R6/synthesis fix 13, brief section 10 single 35 s cropped teaser published as a funnel, Lake Peigneur 'Full story on the channel'): owner rule, 7 rebuilt Shorts with loops.
- Dark pill labels (ep01 ENGINE.md), 'white text in a black pill' (brief section 8), Bebas headlines, and the older Montserrat house look with cyan #4FD1FF, warm #FFB547 and alert #FF5A5F: replaced by the look-book type system and palette (look sections 1.2, 1.3).
- Label floors of 28 px (Lake Peigneur QC) and 44 px (type.js header): replaced by 64 px for must-read text and 48 px for connectors (ep01 phone retention; look section 9).
- 'At most 2 text elements of 7 words, key info out of the bottom 12%' (ep01 bench_visual.md): replaced by one block plus one label plus the gauge in the top 62%.
- One continuous music bed never changing per chapter (Lake Peigneur): replaced by a new cue at every chapter card with overlapping crossfades; the no-silence rule stays.
- 'Dark-space photoreal globe' as the base look (ep01 bench_visual.md): replaced by tilted full-bleed terrain for 60% or more, whole globe 10% or less.
- Static portraits up to 5 s in the first 3 minutes (ep01 review): replaced by no archival asides in the first 2 minutes, then 3 s per still.
- Static limits of 3 s (ep01 ENGINE.md, QC) and 8 s without a new visual (Lake Peigneur): replaced by 1.5 s frozen, 2 s near-static, 7 s per composition.
- End screen of 8 s or less (R6/synthesis fix 13) and an end-screen video element from duration - 17 s (edl.py report.json): replaced by elements only after the last word, 10-12 s over a moving shot.
- 'Make no next-video promise' (Lake Peigneur): replaced by a voice hand-off to one already published video (YouTube's advice).
- File tail of 0.45 s or less after the last word (Lake Peigneur, no end screen): now applies only to Short loops.
- Titles up to 60 characters, and thumbnails with 3 focal points and 3-4 words (Lake Peigneur): replaced by 35-50 characters and one focal subject with 3 words at most.
- Hook line 'They're not. Not entirely.' (ep01): replaced by an unhedged break of the myth.
- Terrain at 3x (drain prototype meta.json) or 6x (tech scout): replaced by 1.0 for comparisons and 2x at most elsewhere.
- One ElevenLabs generation per chapter pasted in the web UI (Lake Peigneur): replaced by per-take tts.py with per-take speed and ASR checks.
- 30 ms tail fades (R6/synthesis fix 7) and a 170 wpm window cap: replaced by vo_fix.py's 10 ms fades and a 165 wpm cap.
- settb=AVTB before xfade: replaced by settb=1/30,setpts=N on every node (the code in ep01/tools/assemble_edl.py).
- CRF 18 1080p master (ep01) and a CRF 20 1080p upload re-encode (San Juan): replaced from ep02 by a CRF 14-16 master and a 2560x1440 upload.
- Colab CPU runtime for renders (the legacy Python map engine): the shared engine renders on the L4 GPU.
- Burned-in long-form subtitles (Lake Peigneur): replaced by a separate caption track; if one is ever burned in, use the owner's style (plain white sentence cues, one at a time, no karaoke, never a quote split over two cues).
- tools/grab.py for frame-exact checks: replaced by passthrough extraction until it is fixed.

## How to update this playbook

After every task, before the next one starts:

1. Add what worked to the right section's DO list, with its evidence, source path and tag.
2. Add what failed to the DONT list the same way.
3. Move a [hypothesis] or [benchmark] rule to [measured] only when our own YouTube numbers (Studio, Test & Compare) confirm it, and add those numbers to its evidence.
4. When a new rule contradicts an old one, apply the precedence above and move the loser to Superseded with the reason.
5. Log the episode's or task's results in LESSONS_LOG.md (what was made, real numbers, what worked, what failed, rules added).
6. Keep Read this first at 10 lines; change it only for a new non-negotiable.
7. Commit and push PLAYBOOK.md and LESSONS_LOG.md (never secrets or large media).
