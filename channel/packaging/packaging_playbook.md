# Myth Juice packaging playbook: titles and thumbnails

Date: 2026-11-08. Status: the permanent rulebook for every Myth Juice long-form title and thumbnail, starting with ep02 (Hawaiʻi).

It merges and updates `principles.md` (PK1-PK12), `title_anatomy.md`, `thumbnail_anatomy.md`, the niche study (`research/niche/niche_report.md`) and the **first blind persona test** (round 1, 12 ep02 packages and 3 ep01 repackages). Where the blind test contradicted an earlier rule, this playbook follows the test and says so.

Paths are relative to `research/packaging/` unless they start with `research/` or `/`.

---

## 0. The short version

1. **The premise wins the click, not the colour.** In the blind test, a new question (with its own picture) took the same film from **1 of 10 picks** (the planned default) to **9 of 10**. Pick reasons quote the title's question again and again; thumbnail brightness did not predict picks (the winner had mean luma 90; the brightest postcard card, 128, got 0).
2. **Ask a question the viewer does not already know the answer to.** "Only the Summit" and "How Tall" were filed under "Mauna Kea is taller than Everest" and lost to PBS Be Smart's 3.6M video. The three specific questions got 23 of 30 picks; the five "Only the Summit" packages got 7 of 50.
3. **The thumbnail shows the strange state and names it in 2-3 words.** NO OCEAN, ONE ISLAND, BIG ISLAND, YOU ARE HERE: 25 of 40 picks. Vague labels (IT KEEPS GOING, THE TOP): 0 of 20. No text at all: 1 of 20 (two packages).
4. **No postcard in the thumbnail.** It read as a travel video: 13 skips across the five postcard packages cite travel, tourism, vacation or "an Expedia ad". Five postcard packages got 5 of 50 picks. The postcard stays a film device only.
5. **Design for the 168x94 card first.** 93% of ep01's impressions were Suggested. Most compact-card skips in the test named darkness, mud or a tiny subject. Floor: mean luma 100, subject at least 12% of the frame.
6. **Title and thumbnail split the job.** Title = the question plus the place name. Thumbnail = the evidence plus a 2-3 word name for it. Zero shared content words.
7. **Look nothing like the clone lane.** No drain/hidden/bottom/nobody words, no black caption box, arrow, depth label, sea-level bar, tan basin, Everest or red highlight. Every final must beat the craft median in `gate.py`.
8. **Promise only what the film shows,** and show it early: frame 1 is the default thumbnail; each test arm's image appears in the film within 30 s.
9. **Test before upload, then let YouTube test.** Gate, feed simulator and blind persona test before upload; then Test & Compare with 3 thumbnails, read only after about 10K impressions.

---

## 1. What went wrong with ep01, in numbers

| Problem | Evidence |
|---|---|
| The card lost the Suggested strip | Suggested CTR **1.97%** on 862 impressions (93% of all), overall 2.27%. Browse/Home 8.82% on only 34 impressions (3 clicks, noise). |
| Darkest card on every surface | Feed simulator, ep01 hosts, 3 seeds: mean luma **61** against neighbour medians of **90-143**; last on p90 luma on every surface. `gate.py`: **FAIL** (68% blue, 9% red). |
| Five competing elements | 3 orange continents, 3 arrows, a ring, a "?" and a black caption box (the template-farm kit). At 168x94 "POINTING AT WHAT?" shrinks to 10 px letters; arrows and ring merge into a squiggle. |
| A question nobody had | "POINTING AT WHAT?" needs the viewer to care about a pattern first (P4 lesson). |
| A hedge bracket | "(Not Just a Coincidence)" spends the bracket on doubt; the title wraps to 3 lines in Up next (55 characters). |
| Wrong premise for the feed | An abstract myth with no named place; ~0 search demand. |

**Correction after blind round 2 (2026-11-08, `round2.md`):** with a live control arm and the same hosts, the live ep01 package beat both repackage proposals, **8/10 against 0/20** (5 of 5 personas preferred it, one-sided p = 0.03). The thumbnail rows of the table above (darkness, "a question nobody had", the hedge bracket) are therefore **not supported**: three personas picked it from the last Up next slot because of the question, and the bracket read as the promise of a real answer. The rows about the premise (an abstract myth, no named place, about 0 search demand, no host cluster) remain the most likely cause of the 1.97% Suggested CTR. Real CTR data outranks simulated personas; any ep01 challenger must start from the live concept (a visible question plus the shapes that pose it) and beat it head to head. Round 1's 8/10 for the seam globe was measured without a control arm.

---

## 2. The evidence base

| Source | Size | What it is |
|---|---|---|
| Title anatomy | 6,528 titles, 1,227 channels | Same-channel ratios: a title feature vs the same channel's other titles (`title_anatomy.md`). |
| Thumbnail anatomy | 247 thumbnails, 63 top performers vs 140 rest | Measured and hand-coded image properties (`thumbnail_anatomy.md`). |
| Niche study | 1,606 videos; 106 coded competitor thumbnails; 1,254 clone vs 521 craft titles | Clone lane, craft lane, distinctiveness gate (`research/niche/`). |
| vidIQ before/after | 10 packaging changes that at least doubled views per hour | `work/vidiq_wins.json`, `refs/wins/`. |
| Feed simulator | Real host thumbnails in dark-mode Home, Up next and desktop sidebar, plus a blurred glance view | `feedsim/feedsim.py`. |
| **Blind persona test, round 1** | ep02: 12 packages x 2 feeds x 5 viewer personas = 120 trials; ep01: 3 x 2 x 5 = 30 | Shuffled feed screenshots (`feeds/r1_*.png`), first and second click with reasons, a cold glance reader; scored by `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/r1score/score.py`. |

**Blind test caveats.** 5 personas and 10 trials per candidate; each candidate met different host mixes and slots (a per-slot position term is in the score model); one strong host (a dictatorship video) took 34 of the 120 first clicks; our "1.2K views, unknown channel" meta-line was the same for every arm and cost clicks with 3 personas. Read the results as large effects only.

---

## 3. The permanent rules, each with its evidence

### Titles

**T1. A specific question or claim the viewer cannot already answer.**
- Blind test, ep02 (picked at all, out of 10): "Why Can't You See Most of Hawaii? (Look Down)" **9**; "Hawaii Used to Be Bigger. Where Did It Go?" **7**; "What's Holding Hawaii Up? (It's Slowly Sinking)" **7**. Versus the "Only the Summit" family 4, 2, 1, 0, 0; "How Tall Is Hawaii? We Measured All of It." **0** ("I already know the answer: about 10 km, Mauna Kea", 3 personas).
- Same-channel data: access questions **1.56x**, statement + twist **1.32x**, deep time **1.22x**; "How X" **0.71x**, plain "Why X" **0.78x**.
- **Test:** write the viewer's question in 8 words or fewer. Ask 3 cold readers whether they already know the answer. If any says yes, change the question, not the wording.

**T2. Probe the premise, not only the words.** Before locking a title, search its premise and look at the biggest video that answers it. If a 1M+ video already answers it and sits in our host cluster, change the angle.
- Evidence: PBS Be Smart's "Why No One Can Agree What's REALLY the Tallest Mountain" (3.6M) was named in 9 skip reasons across the "Only the Summit", "Where Does Hawaii's Mountain Begin?" and "How Tall" packages ("same topic as the PBS one right under it"). The exact-title probe had found 0 matches for those titles; a premise probe would have found the collision.

**T3. Proper noun early, 41-50 characters, 2 lines on every card.**
- Same-channel: 41-50 characters **1.03x**; 31-40 **0.83x**; 30 or fewer **0.90x**. Craft winners' median is 47 characters.
- The place may sit later when the question form puts it there (the launch title has "Hawaii" at character 27; position made no difference, 1.03x), but it must be on line 1 of every card.

**T4. A bracket must add a twist or an instruction, in plain words.**
- Twist brackets **1.56x** same-channel. "(Look Down)" was the nudge named by **4 of 5** personas.
- "(It's a Breakup)" was called cutesy, cringe or slangy by **4 of 5** personas and made the trust-driven persona skip twice. "(Not Just a Coincidence)" is a hedge (ep01).
- No slang, no hedge, no exclamation, no ALL-CAPS words.

**T5. Never drop a qualifier; never overclaim.** "Most of", "about", "Slowly", "from its true base" stay. Absolute words need a ledger line. "Why Every Continent Points South" is rejected because the film itself shows exceptions (Cape York points north).

**T6. Change the grammar every episode** (claim, question, plain fact, myth check). Fixed title templates are copied and decay: "X Isn't Really a Lake. It's a Wound." went from 271-291K to 4.6-9K within a month.

### Thumbnails

**B1. One strange real state, shown, not explained.** One hero shape at 50% or more of the frame, or one lit subject in a vast field (scale contrast) at **12% or more** of the frame.
- vidIQ cases: Bolivia's postcard panorama lost to one strange close subject (x3.5 views per hour); the Netherlands' tulips lost to "water above land" (x2.1); the Black Sea's top-down map lost to a side-on boat under a wave (x2.3).
- Blind test: "BIG ISLAND" with the lit island at 7% of the frame was "dark and small", "got lost in the list" on the compact card (3 of 3 compact skips).

**B2. Name the state in 2-3 concrete words, on the image, no box.**
- Named-state labels: NO OCEAN 9/10, ONE ISLAND 7/10, BIG ISLAND 7/10, YOU ARE HERE 2/10 (lost on its title; both picks cited the pin).
- Vague labels: IT KEEPS GOING 0/10 ("it" was vague in 6 skip reasons), THE TOP 0/10 ("says nothing").
- No text: 1/20 across two packages ("screensaver", "stock photo", "a gray blur").
- Market: median text height 10% (IQR 9-13%); caption boxes on 6% of craft winners vs 23% of the rest (p = 0.008).

**B3. No postcard in the thumbnail (this reverses PK12's signature).**
- Five postcard packages: 5 of 50 picks; the intended launch default (postcard on the drained plinth) 1 of 10, glance read "a Hawaii travel or geography video". 13 skips cite travel, tourism, vacation or an Expedia ad.
- The postcard is kept as a **film** device (the opening drop) only until a new postcard thumbnail passes a blind round on its own.
- The series signature is now the **look**: real terrain at true vertical scale, a low oblique camera, warm low light on grey-dark basalt, a pale sky band and one plain condensed 2-3 word label. Titles still change grammar every episode.

**B4. Compact card first.** Design at 168x94 and in the blurred glance view before looking at full size.
- Ep01 real-Earth globe: Home 5/5, Up next 0/5. Wax-drip globe: Up next 0/5, "loses the effect at small size".
- Most compact-card skip reasons in the ep02 round named darkness or size: "a brown aerial photo", "dark muddy gray, nothing popped", "a dark, blurry, low-contrast slab".

**B5. Brightness: a floor for our card, not a market formula.** Mean luma (0-255) at least **100**, target **105-120** (up to ~135 for bright sea scenes); p90 at least 190; the label contrasts with its surround by 100+ levels at 168x94.
- Why a floor and not "brighter is better": market winners have a *lower* median luma (90 vs 105, p = 0.016), and across our 12 blind-test arms mean luma did not predict picks. But darkness was the most frequent compact-card skip reason, so dark cards lose skips we could keep.
- Before/after: NO OCEAN lifted from 90 to 109 moved its luma rank from 7-8/10 to 3-4/10 in Up next and from 3-5/6 to 2-3/6 on Home (3 seeds). The ep01 breakup globe went from 80 to 104 (Up next rank 8-9/10 to 5-6/10).

**B6. Zero devices; at most one map-native anchor.** No arrow, ring, box, banner, depth or height label, digits, split, logo or face. One recognisable anchor is allowed when it *is* the idea (the YOU ARE HERE pin), at 2% red or less.
- 54% of market winners use no device; faces on 5% of winners vs 12% of the rest; logos and series frames 3% vs 20% (p = 0.001).

**B7. Look nothing like the clone lane, and prove it.** Every final passes `research/niche/work/gate.py` (tan 10% or less, red 3% or less, blue 45% or less) **and** beats the craft median distance: **11.71 or more to drain clones and 11.43 or more to template farms**.
- The drain lane: 96 uploads from 50 channels in 35 days, median 448 views; clone thumbnails average 21% tan pixels; 18 of 24 use a dark caption box, 17 a curved arrow, 17 a depth label.
- Grading warning from this cycle: a warm dawn sky (peach) counts as tan and failed the gate (16-20% tan); a rose sky and a lifted brown flank pulled the clone distance below 11.71. Lift brightness with **cool, desaturated grey basalt**, not with warmth.

**B8. Make the image say the title's claim.** The ep01 breakup globe's glance read was "a continent splitting", the same read as Astrum's 1.8M "Earth's Newest Ocean Will Split Africa in Two", and it "doesn't tell me where on Earth it is". Fix: both southern tips and Antarctica in frame, so the image carries "point south". Check the glance read against the strongest same-topic host; if they read the same, change the image.

### The package

**P1. Title and thumbnail never repeat each other** (0 shared content words; pronouns do not count). Cover test: each half alone must raise a question.

**P2. Frame 1 is the default thumbnail; each arm's image is paid within 30 s** (MrBeast production notes: the first minute must show that "their expectations from the thumbnail will be met"; YouTube: a title that misrepresents the video makes viewers stop watching).

**P3. No spent hooks:** no "taller than Everest", no "bigger than you think" for Hawaiʻi, in the title, thumbnail, first 30 s or Shorts hooks. Everest/Mauna Kea comparison videos run at **0.77x** their channel median; 0 of 7 eligible were top performers.

**P4. Owner rules:** no emojis; never mention AI anywhere (and never "No AI"); English titles and thumbnails; no sources on screen; correct Hawaiian spelling (ʻokina U+02BB, kahakō) wherever the font allows, "Hawaii" as the plain matching word in titles.

---

## 4. Thumbnail spec sheet

| Item | Spec | Ep02 finals (1 / 2 / 3) |
|---|---|---|
| Canvas | 1280x720, 16:9, sRGB JPEG, quality 92 progressive, under 2 MB (upload 1280x720 or larger: one arm under 720p downscales every arm to 480p) | 1280x720, 192 / 145 / 153 KB |
| Words | 2-3, one line, naming the shown state; no digits | 2 / 2 / 3 |
| Text height | Cap height 13-16% of frame height (93-115 px) | 15% / 13% / 15% |
| Text width | 62% of frame width at most | 44% / 45% / 61% |
| Font | Barlow Condensed ExtraBold (800). Use the latin-ext file whenever a kahakō appears and check that every glyph renders (no boxes) | Barlow Condensed 800 |
| Text colour, pale sky | Charcoal #10161E with a soft white glow (blur 8 px, alpha 110/255) | 1, 2 |
| Text colour, mixed ground | Navy #101E2C with an 8 px white halo (map-label style) | 3 |
| Text colour, dark ground | White #FFFFFF, soft black shadow (alpha 200/255, blur 7 px, offset 0/3 px) | (BIG ISLAND, reserve) |
| Never | Boxes, banners, bars, outlines in accent colours, script or retro type | - |
| Label legibility | Text vs surround at least 100 levels at 168x94 after a 1.1 px blur. Measured: charcoal NO OCEAN 133; the white variant 9, so it was rejected | 133 / - / - |
| Mean luma | Floor 100, target 105-120, up to ~135 for bright sea scenes | 109 / 133 / 103 |
| p90 luma | 190 or more (one luminous region) | 223 / 215 / 193 |
| Contrast | Luma SD 55 or more; hero vs background 40+ levels | SD 68 / 61 / 66 |
| Colour shares | Tan 10% or less, red 3% or less (an accent icon 2% or less), blue 45% or less | 2/0/27, 8/1/7, 2/1/22 |
| Palette | Grey-dark basalt, green and rust island cap, pale blue sky band, turquoise only where water is the point. Ep01 globes: slate backdrop #6B7078 to #42454D, pale stone land, one cyan seam #73EBF2 | - |
| Distinctiveness | `gate.py` PASS, drain clones 11.71+, template farms 11.43+ | 12.04/11.48, 11.79/11.45, 11.87/11.65 |
| Focal size | Hero 50%+ of frame, or a lit subject 12%+ in a vast field | terrain ~78% / land ~50% / cap + flank ~50% (sky-mask estimates) |
| Camera | Low oblique, true vertical scale (VE 1.0); never top-down | all |
| Anchor | 0 or 1 (map pin, true-scale object); no faces, no logo | 0 / 0 / 1 pin |
| **Timestamp corner** | Keep text and the key subject out of the **bottom-right 25% x 23%** (the "12:53" badge on the 168x94 card is 39x18 px, 4 px from the corner; on the full-width Home card it takes the bottom-right 12% x 12%). Longer durations ("1:02:33") are wider | clear |
| Other safe areas | Bottom 4% (red watched bar for returning viewers); 4% from every edge (rounded corners, radius 8 px on the compact card). Put text in the calm sky band in the top third | clear |
| Brand | No wordmark, logo, stamp text or series frame | none |

Reproduce (all PIL/numpy; plates from `engine/www/lab_hawaii.html` via `design_question/tools/rb19.sh`):
- `final_ep02_1`: plate `final_work/plates/ours_P1_lift_a.jpg` (query in `design_question/pairs.json` cand_1 with `"exposure":1.7,"basalt":[0.036,0.036,0.039],"sed":[0.058,0.055,0.054]`), then `python3 -I final_work/tools/finalize.py final_work/cfg_q1c.json OUT` (key `ours_q1_s4`; reproduces the final pixel for pixel).
- `final_ep02_2`: `finalize.py final_work/cfg_q3c.json OUT` (key `ours_q3_e3`).
- `final_ep02_3`: `python3 -I final_work/tools/pin_arm.py ours_pin_a 54 0.15 70 28 800`.
- `final_ep01_1`: `cd design_ep01/work && python3 breakup.py OUT.jpg T=116 lat=-45 lon=-14 dist=2.45 fov=50 bgtop=0.42,0.44,0.47 bgbot=0.26,0.27,0.3 rim=0.6 sea=0.14,0.17,0.18`.
- `final_ep01_2`: `python3 target.py OUT.jpg lat=-44 lon=-17 dist=2.45 fov=52 land=1.4 bgtop=0.80,0.80,0.80 bgbot=0.55,0.55,0.56`.

---

## 5. Title formula library

Ranked by our evidence. "Same-channel" = the formula vs the same channel's other titles (`title_anatomy.md`).

| # | Formula | Evidence | Use when | Example |
|---|---|---|---|---|
| 1 | **Access question:** "Why Can't You See / Visit / Reach X?" plus an instruction or twist bracket | 1.56x same-channel; Iwo Jima 4.4M; blind test **9/10** | The subject is physically out of sight or out of reach, and the film shows it | "Why Can't You See Most of Hawaii? (Look Down)" |
| 2 | **Physical contradiction:** "What's Holding X Up? (It's Slowly Sinking)" | Twist bracket 1.56x; blind **7/10**, the title alone drove 5 of the 7 picks | The film explains a mechanism the viewer has never wondered about but instantly wants | "What's Holding Hawaii Up? (It's Slowly Sinking)" |
| 3 | **Deep time + where:** "X Used to Be Y. Where Did It Go?" | Deep time 1.22x (1.56 pooled), a craft marker; blind **7/10** | The film shows a real past state on real data | "Hawaii Used to Be Bigger. Where Did It Go?" |
| 4 | **Known phrase + twist bracket** | 1.56x | Repackaging: keep the phrase that already matched hosts, replace a hedge with a plain twist | "Why the Continents Point South (Pangaea's Breakup)" |
| 5 | **Completeness:** "Every X" | 1.81x | Only when the film covers every item (lists are against owner policy otherwise) | ep-level, not ep02 |
| 6 | **Statement + twist** (two sentences) | 1.32x; but the "Only the Summit" family got 7/50 picks | The first sentence is not a premise the audience already files under a famous answer | "It Looks Like a Desert. But It Has Thousands of Lakes" (PBS Terra, 5.9M) |
| 7 | **Literal fact with a picturable verb** | Plain claim 0.94x (neutral); blind 5/10 with ep01 globes, best on Home | Back-up or swap when the owner wants zero assertiveness | "Why South America and Africa Point at Antarctica" |
| 8 | **Explorer / proof:** "We Measured X" | 1.25x; blind: "We Measured" read as "homework" (2 personas) | Only as a second sentence, and only if the measurement is on screen | (reserve) |
| 9 | "X Is Bigger / Deeper Than You Think" | 1.66x | Never for Hawaiʻi (spent: 14M Short); fine elsewhere | - |

**Avoid as a default:** "How X" (0.71x; "How Tall Is Hawaii?" 0/10), "Where Does X Begin?" (0/20 across two packages: "sounds like a geography class", "like a riddle"), "Why X" without access (0.78x), number lists (0.79x), yes/no questions (0.74x).

---

## 6. Banned patterns

| Pattern | Why |
|---|---|
| Title regex (case-insensitive) `\b(hidden\|hiding\|hides\|nobody\|no one\|never\|secret\|found\|discovered\|reveal\w*\|bottom\|beneath\|drain\w*\|without (water\|ice)\|what if\|here'?s what\|talks about\|sitting on\|isn'?t really\|no longer makes sense\|survives\|shocking\|terrifying\|sleep\|documentary)\b` | Clone vocabulary: hidden/hiding in 19% of clone titles vs 1% of craft; nobody/never 19% vs 3%; "X Is Hiding Something" 0.60x same-channel. The drain words live in the first spoken line, the description and the tags only. |
| "We Drained X. Here's What Was Hidden at the Bottom." and "What X Looks Like Without Water/Ice" | Verbatim on 14+ channels; copies of an already-drained place get 0.01-2% of the original. |
| Fear adjectives: terrifying, insane, creepy, strange, weird, wild, extreme, mysterious | 0.79x same-channel; overclaim risk. |
| Hedge words: Not Just, Maybe, Sort Of, Kind Of, Probably | Ep01's bracket. |
| Slang brackets: (It's a Breakup), (No Way), (Insane) | 4/5 personas: cutesy; trust-driven viewers skip. |
| Spent hooks: Taller Than Everest, Bigger Than You Think (Hawaiʻi), Hidden Islands | 0.77x channel median for the Everest cluster; the 14M "Hawaii Is Much Bigger Than You Think" Short. |
| Ambiguous neighbour words: "Tip" (tipping culture), "Underwater" (flood news), "Really" (travel videos) | Probe results. |
| Answer-known premises: "How Tall Is X", "X Is Only the Summit" (Hawaiʻi) | Blind test: 0/10 and 7/50; viewers chose PBS. |
| Thumbnail clone kit: black caption box with an accent word, curved white arrow, negative-depth label, sea-level bar or dashed sea-level line, tan drained basin dominating the frame, Everest cross-section, saturated red/orange highlighted region, before/after split | Present on 0% of gate passes; the clone lane has a 448-view median. |
| Postcard as the thumbnail's main device | Read as travel (13 skips); 5/50 picks. |
| Vague labels ("IT", "THE TOP"), no-text thumbnails as a default | 0/20 and 1/20. |
| Faces, generated presenters, reaction cut-outs, logos, wordmarks, emojis, any mention of AI, on-screen sources | Market data (faces 5% vs 12%, logos 3% vs 20%) and owner rules. |

---

## 7. How title and thumbnail split the job

| Layer | Job | Must | Must not |
|---|---|---|---|
| **Title** | The question or claim, plus the host-matching proper noun | Be answerable only by watching; keep qualifiers; 41-50 characters | Describe the picture; repeat the label |
| **Thumbnail image** | The evidence: the strange real state, at true scale | Read in 2 s at 168x94; carry the title's claim visually (B8) | Answer the question (no numbers, no "56,000 FT") |
| **Thumbnail label** | Name the state in 2-3 words | Concrete noun phrase; 0 content words shared with the title | Pronouns without a referent, captions, claims the image cannot show |
| **First 30 s** | Confirm the click | Frame 1 = the default thumbnail; the title's words spoken by 0:10; every arm's image on screen by 0:30 | Spend the payoff number |

**Ep02 worked example.**

| | Title | Label | Picture | Together they say |
|---|---|---|---|---|
| Arm 1 | Why Can't You See Most of Hawaii? (Look Down) | NO OCEAN | The Big Island massif with the ocean gone: green-rust island cap on a vast grey basalt mountain | "Most of Hawaii is the part under the sea, and we will see it." The answer (how big, why it sinks) stays withheld. |
| Arm 2 | (same) | ONE ISLAND | Ice Age Maui Nui: Maui, Molokaʻi and Lānaʻi fused by dry shelf | "Some of the Hawaii you can't see was once dry land." |
| Arm 3 | (same) | YOU ARE HERE | A map pin on today's shore, the dark flank dropping far below to a half-drained sea | "You stand on the top; look down." |

---

## 8. Testing protocol (before every upload)

1. **Package sprint before script lock.** 20+ titles, 5+ thumbnail concepts from at least 2 different design directions; keep 6-12 packages for the blind round. Predict the video's score out of 10 and log it.
2. **Hard checks** on every package:
   - title regex clean, 41-50 characters, qualifiers kept, no spent hook;
   - exact-title probe and **premise probe**: `python3 /home/user/juicytea-media/longform/ep01-continental-drip/tools/ytsearch.py "<title>" "<premise words>"` (no on-topic long-form with the same first 4 words; no 1M+ host that already answers the question);
   - `cd research/niche/work && python3 -I gate.py <thumb>`: PASS and 11.71 / 11.43 or more.
3. **Feed simulator.** `cd research/packaging/feedsim && python3 -I feedsim.py SPEC --out ../feeds/NAME --report --glance` with the place's host set, at least 3 runs (seeds 2 and 5, plus seed 3 with the same-premise uploads mixed in, e.g. `hosts.json#hawaii+hawaii_direct`). Pass: the label reads in every glance; mean luma in the top half and p90 in the top 3 on the compact surfaces.
4. **Blind persona test** (round 1: all packages; round 2: the refined top 3 under the launch title).
   - Render shuffled feeds with `feedsim/blind/blind_r1.py PAIRS.json` (writes `feeds/r<N>_*.png` and the key): each package in a mobile Up next list (our card + 7 hosts) and a mobile Home feed (our card + 3 hosts), with the SAME host set for every arm and fixed or rotated slots per arm (round 2 showed slot 8 carries about 0.19x the pick weight of slot 1), identical small-channel meta-line. Whenever an existing video is being repackaged, include its live package as a control arm.
   - 5 fixed viewer personas (e.g. a novelty-seeking teen, a commuter, a trust-driven retiree) pick a first and second click per feed and give reasons; a separate cold reader writes what each card is about from a 2 s glance.
   - Score with `score.py`: 0.45 x choice strength (Plackett-Luce top-2 with a per-slot position term) + 0.15 x first-click index + 0.2 x glance match + 0.2 x quality of the skips.
   - **Launch gate:** picked in 7 or more of 10 trials, glance MATCH, no objection repeated by 3 or more personas, and the default tops its round. Round 2 places our card in middle slots (Home 2-3, Up next 5-7) and away from the strongest same-topic host.
5. **Upload.** YouTube Test & Compare with **3 thumbnails** under the launch title (thumbnails first; titles only under the stall rule). The default arm is uploaded first: if the test is inconclusive, the first one stays. 1280x720, under 2 MB.
6. **Read only after about 10K impressions** (or when the 2-week test ends). YouTube picks by watch time share, so judge with it: Suggested CTR and watch time per impression (CTR x average view duration) in the Suggested source, against ep01 (1.97%, about 5.2 s). Targets: Suggested CTR 5% or more, 15 s or more per impression. At our traffic expect "Inconclusive"; then the pre-upload tests decide.
7. **Stall rule.** If impressions are below about 3K after 72 h, make ONE change: the title to backup 1. Changing a title or thumbnail stops a running test, so keep the current leader as the default first. Log every change with its time, wait another 72 h, never change two things in one day.

---

## 9. Ep02 final package

### Launch title

**"Why Can't You See Most of Hawaii? (Look Down)"** (45 characters, regex clean)

- Blind round 1: picked in **9 of 10** trials (2.4x the random baseline of 3.75), 2 first clicks, the top score of 12 packages (**78**); from the last Home slot it took 5 of 5 picks against Nat Geo, Be Smart and IT'S MOVING; 4 of 5 personas named "(Look Down)" as the nudge; seven pick reasons restated the promise unprompted ("Hawaii with the water gone and the seafloor showing").
- Probe today: 0 matching long-forms; neighbours are the right hosts (RealLifeLore's 7.07M boats video) plus the spent 14M "bigger than you think" Short, which we do not echo.
- Keep it word for word.

### Thumbnails for Test & Compare

| File | Arm | What changed after round 1 | Tests |
|---|---|---|---|
| `final_ep02_1.jpg` | **Default.** NO OCEAN on the fully drained massif | Lifted in the renderer (exposure 1.45 to 1.7, lighter cool basalt) and graded the dry flank to cool grey (saturation 0.5): mean luma **90 to 109**; NO OCEAN **13% to 15%** cap height; the white-text alternative was measured and rejected (9 vs 133 levels of contrast at 168x94). Warmer lifts failed the gate. | Gate 12.04 / 11.48. Feed sim luma rank 2-3/6 Home, 3-4/10 Up next, 1-3/5 sidebar (was 3-5, 7-8, 3-5); p90 rank 1-3 everywhere. |
| `final_ep02_2.jpg` | ONE ISLAND, Ice Age Maui Nui | Tried the judge's palette fixes (dawn sky, warmer shelf, deeper water): all failed the craft-median bar (tan up to 20%, clone distance down to 10.84). Ships as tested with a +15% dodge on the Molokaʻi-Maui land bridge. | Round 1 (own title): 7/10 picks, 3 near-miss skips. Gate 11.79 / 11.45 (thin). Luma 133, rank 1-2 on every surface. |
| `final_ep02_3.jpg` | YOU ARE HERE pin on today's shore, mid-drain | Pin radius 40 to 54 px, label 12.6% to 15%, paper tourist 22 to 28 px | Round 1 lost on the "Summit" title (2/10); both picks cited the pin; glance MATCH. Gate 11.87 / 11.65. |

**Round 2 result (`round2.md`):** A (NO OCEAN) 3/10 with 2 first clicks, B (ONE ISLAND) 4/10, C (YOU ARE HERE) **0/10** ("a pin on a brown hill" in all 10 exposures). A and B are statistically tied; A stays the default on the tie-breakers (4 of 20 first clicks across both rounds vs 0 of 20, its glance read states the title's promise, and frame 1 is built for it). **Test & Compare runs 2 arms: A (default) and B. C is retired.** BIG ISLAND (`design_question/cand_2.jpg`) is a reserve third arm only after a luma and chroma fix and a mini blind check at a low Up next slot. Open risk for A: in 8 of 10 Up next exposures the personas called it grey, muted or small; the optional fix is more chroma on the island cap (not more luma), then re-run `gate.py` and the 168x94 glance. Condition for B: by 0:14 the narration names Maui, Molokaʻi and Lānaʻi as the islands that join (3 of its 4 pickers over-read it as all the islands becoming one).

### Backup titles (stall rule, in this order)

1. **"What's Holding Hawaii Up? (It's Slowly Sinking)"** (47). Blind 7/10, 5 of the 7 picks driven by the title. Round 2: 2/10 with the NO OCEAN image, which was blamed in all 8 skips ("no sinking in the image"); if the stall rule fires, pair it with an image that shows subsidence (e.g. BIG ISLAND, its round 1 pairing). True: Hawaiʻi Island subsides about 2.5 mm a year (fact 4); the payoff shows the crust pushed down by the weight. Keep "Slowly".
2. **"Hawaii Used to Be Bigger. Where Did It Go?"** (42). Blind 7/10. Pairs best with arm 2. Condition: the 0:30-0:47 line must name both causes (the sea rose after the Ice Age, and the islands sink).
3. **"Hawaii's Volcanoes Go Down Farther Than They Go Up"** (50). The title drew 3 favourable mentions while its no-text image failed. Condition: a ledger line for the plural (Mauna Kea 4,205 m up and about 6,000 m down to the sea floor; Mauna Loa about 17 km from its true base), or narrate Mauna Kea and Mauna Loa only.

Retired: every "Only the Summit" title, "How Tall Is Hawaii?", "Where Does Hawaii Begin?", the postcard thumbnails, the no-text control.

### Conditions the film must meet (promise map)

| Package element | Where the film pays it |
|---|---|
| "Hawaii" | First spoken words, 0:00 |
| "Most of" | Ledger: Mauna Kea about 6,000 m below vs 4,205 m above sea level (USGS); Mauna Loa about 56,000 ft from its true base. The narration must say it means the mountain, not the land area |
| "Why can't you see" | 0:00-0:10: the ocean hides it; fully at the 11:10-11:45 payoff |
| "(Look Down)" | The camera tips down the flank by about 0:27, and again at the payoff |
| Arm 1, NO OCEAN | **Frame 1 = this composition** (camera lon -155.32, lat 18.42, 26 km up, looking north; SSIM 0.8+ at 320x180 without the label). This replaces the brief's dashed SEA LEVEL frame (clone kit) |
| Arm 2, ONE ISLAND | 0:14 Maui Nui hero shot at about -400 ft (Kahoʻolawe stays separate) |
| Arm 3 | Retired after round 2 (YOU ARE HERE 0/10). Reserve: BIG ISLAND after its fix and a blind check |
| Never | "Taller than Everest" or 56,000 in the package or the first 30 s |

---

## 10. Ep01 repackage: WITHDRAWN (blind round 2)

The proposal ("Why the Continents Point South (Pangaea's Breakup)" with `final_ep01_1.jpg` / `final_ep01_2.jpg`) lost to the live package 0/20 against 8/10 in a controlled blind round (`round2.md` section 5). Nothing was changed on YouTube and nothing should be. Keep the live title and thumbnail. If ep01 is worked on again, start from the live concept (a visible question plus the shapes that pose it), keep its bracket, and require a head-to-head win against the live package in a balanced round with a control arm. Lessons kept: no-text thumbnails lost in both rounds (1 of 40 picks), and a mean luma floor did not predict picks (the live card at luma 62 won).

---

## 11. Files

| What | Path |
|---|---|
| Final thumbnails | `final_ep02_1.jpg`, `final_ep02_2.jpg`, `final_ep02_3.jpg`, `final_ep01_1.jpg`, `final_ep01_2.jpg` |
| Overview (Hungarian labels) | `final_overview.jpg` |
| Owner summary (Hungarian) | `packaging_hu.md` |
| Rebuild scripts and configs | `final_work/tools/finalize.py`, `pin_arm.py`, `overview.py`; `final_work/cfg_q1c.json`, `cfg_q3c.json`; plate `final_work/plates/ours_P1_lift_a.jpg`; intermediates `final_work/out1-3/ours_*.jpg`, `final_work/ep01/ours_*.jpg` |
| Feed-sim specs and ranks | `final_work/specs/`, `final_work/feed_final_ranks.json`, `final_work/feed_ep01_ranks.json`; screens in `feeds/final_ep02/`, `feeds/final_ep01/` (never committed) |
| Round 1 blind test | `feeds/r1_*.png`, `feedsim/blind/`, `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/r1score/score.py` |
| Earlier rulebooks (superseded where they conflict) | `principles.md`, `title_anatomy.md`, `thumbnail_anatomy.md`, `research/niche/niche_report.md` |
| Gate, feed strip | `research/niche/work/gate.py`, `sim_lib.py`, `feedstrip.py`; `work/craft_median.py` |
