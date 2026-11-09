# Blind feed test, round 2: scoring and decisions

Date: 2026-11-08. Key: `feeds/r2_key.json` (14 feeds, `feeds/r2_1.png` to `r2_14.png`). Scorer: `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/r2score/score_r2.py` (picks hand-coded to slots from the vote text) and `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/r2score/pooled.py` (round 1 + round 2 pooled model, persona bootstrap). Paths are relative to `research/packaging/`.

**Read this first: the sample is small.** There were 5 simulated viewer personas. Each candidate was shown in 2 feeds (one Up next, one Home), so it had **10 trials**. Every persona saw every feed, so all the arms of an episode were judged by the same five viewers. Only a difference as large as ep01's (8/10 vs 0/10) is solid. The ep02 differences (4 vs 3 vs 2 picks) are within noise. Section 5 lists the design flaws that make them noisier still.

The personas, as their wording suggests: P1 a novelty-seeking teen, P2 a dad who watches on the TV, P3 a UK commuter, P4 an engineering-minded viewer, P5 a trust-driven retiree.

---

## 1. Decisions

| Question | Decision | Strength of evidence |
|---|---|---|
| ep02 Test & Compare default | **A: `final_ep02_1.jpg` (NO OCEAN)** | Weak. A and B are statistically tied, and the tie-breakers favour A (section 3). |
| ep02 set | **A (default) + B: `final_ep02_2.jpg` (ONE ISLAND). Drop C: `final_ep02_3.jpg` (YOU ARE HERE).** Run a **2-arm** test. | Strong for dropping C (0/10, and all five personas gave the same objection). |
| Launch title vs backup (A vs D, same image) | **The launch title holds:** "Why Can't You See Most of Hawaii? (Look Down)" | Weak. 3 vs 2 picks and 2 vs 0 first clicks, confounded by slot. There is no case to switch. |
| Does the ep01 repackage clearly beat the live control? | **No. The live control clearly beats both proposals.** E 8/10 vs F 0/10 and G 0/10. Do **not** apply the repackage. | Strong. All 5 personas picked E at least once, none picked F or G, and E won in every model specification and in 100% of the persona bootstrap resamples. |

---

## 2. Per-candidate results

Random baseline per candidate (1 Up next feed with 8 cards, 1 Home feed with 4 cards): **1.875 first clicks and 3.75 picks out of 10**.

| ID | Package | Slot (Up next / Home) | First-click share | Any-click share | vs random | Up next / Home | Picked by | Glance read vs promise |
|---|---|---|---|---|---|---|---|---|
| A | Look Down + NO OCEAN | 8/8 · 1/4 | **2/10** (20%) | **3/10** (30%) | 0.80x | 0/5 · 3/5 (2 first) | P1, P2, P5 | **MATCH**, with a caveat |
| B | Look Down + ONE ISLAND | 1/8 · 2/4 | 0/10 | **4/10** (40%) | 1.07x | 4/5 (all second) · 0/5 | P2, P3, P4, P5 | **MATCH** (the arm's promise) |
| C | Look Down + YOU ARE HERE | 3/8 · 3/4 | 0/10 | **0/10** | 0 | 0/5 · 0/5 | none | **WEAK / MISMATCH** at card size |
| D | Slowly Sinking + NO OCEAN | 6/8 · 4/4 | 0/10 | 2/10 (20%) | 0.53x | 0/5 · 2/5 (second) | P1, P3 | **MISMATCH** with the title |
| E | ep01 live control: Not Just a Coincidence + POINTING AT WHAT? | 8/8 · 2/4 | **5/10** (50%) | **8/10** (80%) | 2.13x | 3/5 (second) · 5/5 (all first) | all five | **MATCH** |
| F | Pangaea's Breakup + seam globe (`final_ep01_1.jpg`) | 7/8 · 4/4 | 0/10 | **0/10** | 0 | 0/5 · 0/5 | none | **MISMATCH** (read as Astrum's premise) |
| G | Pangaea's Breakup + real-Earth globe (`final_ep01_2.jpg`) | 6/8 · 3/4 | 0/10 | **0/10** | 0 | 0/5 · 0/5 | none | **MISMATCH** (generic) |

**Plackett-Luce top-2 strengths.** These are log-strengths against the mean of all cards. Hosts are estimated jointly. Each column uses a different slot assumption, because slot is the main confound:

| ID | R2, slot term fitted (Home -0.13, Up next -0.50 per slot) | R2, no slot term | R2, slot term from R1+R2 (-0.25 / -0.24) | R1+R2 pooled |
|---|---|---|---|---|
| A | -0.03 | 0.00 | -0.22 | 0.02 |
| B | -0.08 | **+1.23** | +0.50 | 0.07 |
| C | -2.53 | -2.19 | -2.30 | -2.19 |
| D | -1.17 | -1.95 | -1.32 | **+0.42** |
| E | **+4.19** | **+2.69** | **+3.30** | **+3.30** |
| F | -2.62 | -2.81 | -2.49 | -2.49 |
| G | -2.10 | -2.84 | -2.47 | -2.47 |

The persona bootstrap resamples the 5 personas, 60 times, with the pooled slot term. B > A in 83% of resamples, A > D in 92%, and E > F and E > G in 100%. The A/B and A/D orderings flip depending on the slot assumption. The E vs F/G ordering never does.

**Host context.** Astrum's "Earth's Newest Ocean Will Split Africa in Two" took the first click in 10 of 10 appearances. Park Vibes' forbidden-island video took 10 of 15 first clicks. Map Pack's ONLY 8 MILES was picked in 16 of 20 appearances. These three dominate whichever feeds they appear in.

### A: "Why Can't You See Most of Hawaii? (Look Down)" + NO OCEAN

- **Picks (3).** P1: "NO OCEAN looks like someone drained all the water around Hawaii, and 'look down' makes me think most of it is hidden underwater." P2: "reads as a 'Hawaii drained' video… 'Look down' tells me it's about the part underwater." P5: "Hawaii seen from a plane with the ocean taken away… the question in the title is clear." Two of the three cite the top Home slot ("the top one", "the first big picture on the page").
- **Noticed but skipped (7).**
  - Up next, slot 8, 0/5: all five skips are about legibility or position. "Looked cool but small" (P1). "At the very bottom, didn't register" (P2). "Small and greyish" (P3). "Last on the list and looked muted" (P4). "Too dark and gray to tell what it was" (P5).
  - Home: "brown-grey render looked a bit lifeless" (P3). "Greyish-brown, and the topic felt like the same thing the tallest-mountain video will cover" (P4).
- **Glance:** "what this island would look like if all the ocean water were drained away, revealing how tall the mountain really is from the seabed." This is a **MATCH** for "most of Hawaii is under the sea; look down". Caveat: the "how tall" framing leans toward Be Smart's tallest-mountain premise (rule T2), and P4 made exactly that link.
- **Repeated objection:** grey, muted or small at card size. All five personas raised it, counting A and D (same image), in **8 of 10 Up next exposures**.

### B: "Why Can't You See Most of Hawaii? (Look Down)" + ONE ISLAND

- **Picks (4, all second clicks, all from Up next slot 1, directly under the now-playing RealLifeLore boats video).** **All four pick reasons mention the position**: "sits right under the video I just finished" (P2), "at the top follows on nicely" (P3), "the top suggestion" (P4), "at the top of the list caught me" (P5). They also mention the continuity from the boats video. Three of the four over-read the image as "**all** the islands are really one thing underneath", but the film shows Maui Nui (Maui, Molokaʻi, Lānaʻi; Kahoʻolawe stays separate).
- **Noticed but skipped (6).**
  - "Didn't get what 'one island' meant in one second" (P1, twice).
  - On Home, 0/5. It lost every time to the two Unseen Works drained cards (Antarctica, Pacific Drained), the strongest Home host set of the round. Reasons: "lost to the two drained-planet ones" (P2), "the other two were louder" (P3), "the same drained-ocean idea as Pacific Drained right below it, and that one looks more impressive" (P4), "a lovely travel-postcard aerial… a close third" (P5; this is the rule B3 travel-read risk, from one persona).
- **Glance:** "islands joined by exposed land… used to be, or could become, one big connected island when sea level drops." This is a **MATCH** for arm 2's promise, and it supports the title indirectly.
- **No objection was repeated by 3 or more personas.** Across both rounds B has **never been a first click** (0 of 20 trials). It works as a follow-up, not as the main draw.

### C: "Why Can't You See Most of Hawaii? (Look Down)" + YOU ARE HERE

- **0/10.** **All 10 exposures** gave the same objection, from all five personas: "just a hill and water" (P1), "a pin on a brown hill, couldn't tell what I was looking at" (P2), "looked like nothing… read like a holiday snap" (P3), "couldn't tell what the interesting part was in one second" (P4), "mostly a brown hill" (P5). The title still drew interest: "'look down' was kinda interesting" (P1), "'look down' is a nice hook" (P4), "made me curious" (P5, twice).
- **Glance:** "the point of the pin is unclear and reads more like a travel or location video." This is **WEAK / MISMATCH** and breaks rule B3. C sat in upper-middle slots (Up next 3/8, Home 3/4), so the result is not a slot artefact.

### D: "What's Holding Hawaii Up? (It's Slowly Sinking)" + NO OCEAN (the backup title)

- **Picks (2, both second clicks from the last Home slot).** P1: "'it's slowly sinking' about Hawaii freaked me out." P3: "'slowly sinking' in the title did the work… the thumbnail looked muddy and didn't sell it."
- **Noticed but skipped (8).** The **title drew interest in all 8 skips**: "Hawaii is sinking?? got me" (P1), "'slowly sinking' actually caught me" (P2), "very much my kind of question" (P4), "the title pulled at me" (P5). The **thumbnail was blamed in all 8**: "tiny", "dull grey slope", "hard to make out", "muddy gray landscape". Two personas named the mismatch directly: "the NO OCEAN gray terrain didn't say 'sinking'" (P2), and "NO OCEAN didn't match the title in my head" (P4).
- **Glance:** the same as A, about how tall the mountain is from the seabed. Nothing in it says sinking or support, so it is a **MISMATCH** with D's title.

### E: ep01 live control, "Why the Continents Point South (Not Just a Coincidence)" + POINTING AT WHAT?

- **8/10, with 5 first clicks.** On Home it was the first click for all five personas, from slot 2. On Up next it was picked 3/5 from the **last slot (8/8)**, in a feed that also held Astrum and Map Pack, the round's two strongest ep01 hosts. The other two personas noticed it there and skipped only because they already had two picks ("almost made it", P5).
- **Why picked:** the question itself. "I never noticed that, and now I need to know" (P1, P3, P4). "Not Just a Coincidence" was read as a sign that **a real answer exists**: "makes it sound like there's a real secret" (P1), "says there's an answer" (P2), "makes me want the reason" (P4). The text was read at Up next size from the bottom slot.
- **Objection:** the 1.2K view count made P3 and P4 hesitate. Both still clicked. No legibility objection appeared in any of its 10 exposures.
- **Glance:** "why the continents' tips all point south and what they are pointing at, probably that they were once joined around Antarctica." **MATCH.**

### F: "Why the Continents Point South (Pangaea's Breakup)" + seam globe

- **0/10.**
  - **No text, stock render or model look:** all 5 personas. "A plain white ball with a blue crack… read like a stock render" (P2). "A science-class model" (P2, P5). "Clinical" (P3). "Couldn't even recognise the continents" (P4).
  - **The bracket:** 4 of 5 personas. "Sounds like a lesson" (P1, P3). "Sounds like the video I'm already watching / just finished" (P2, P3, P4).
- **Glance:** "a continent splitting apart or a new ocean forming… at small size only a globe with a blue line." This is a **MISMATCH**. It is Astrum's premise, so the rule B8 problem flagged in the playbook is still there after the camera pull-back.

### G: "Why the Continents Point South (Pangaea's Breakup)" + real-Earth globe

- **0/10.**
  - **No text, dark, small or placeholder:** all 5 personas. "Like a placeholder" (P2). "Couldn't tell what the video was" (P3). "Small dark globe… blended in" (P4). "Didn't register at thumbnail size" (P5).
  - The question itself still attracted: "interesting title" (P2), "the question itself is interesting" (P4), "a question I'd like answered" (P5).
- **Glance:** "a generic geography or Earth documentary… nothing at small size telling me what is unusual." **MISMATCH**, because the image makes no promise.

---

## 3. ep02: why A stays the default, B is arm 2, and C goes

**Picks cannot separate A and B.**
- Round 2: B 4/10, A 3/10.
- Across both rounds: A **12/20**, B **11/20**. B's round 1 picks came under a different title.
- The models disagree on the order. Without a slot term B leads. With the pooled slot term the two are tied (0.07 vs 0.02).
- Each arm's picks came mostly from its best slot: B's 4 from Up next slot 1, and all of A's from Home slot 1.

**The tie-breakers favour A, three to one.**
1. **First clicks:** A 4 of 20 across both rounds, B **0 of 20**. A is the arm that has drawn a viewer's first tap.
2. **Title match:** A's glance read says the launch title's promise outright ("the part under the sea"). B's says it only indirectly. Three of B's four pickers also over-read it as "all the islands are one".
3. **Frame 1 is already built for A** (rule P2). Making B the default would mean re-cutting the opening to the 0:14 Maui Nui shot.
4. For B: **compact-card legibility.** NO OCEAN drew grey, muted or small objections in 8 of 10 Up next exposures, from all five personas. ONE ISLAND drew none. But B was never shown low in an Up next list, so this is missing evidence on B, not proof that B is better.

The protocol says "keep arm 1 as the default unless round 2 contradicts it". On picks, round 2 does not contradict it. **The open risk is A's Up next card.** It has the round's one repeated objection, and Up next is the surface that carried 93% of ep01's impressions.

**Why a 2-arm test instead of adding C.**
- C scored 0/10, with a unanimous objection and a travel read, from middle slots.
- Test & Compare splits the early impressions evenly, so a third arm would hand a third of the launch window to the card least likely to be clicked.
- Two arms also need fewer impressions to reach a result.
- The playbook's reserve, BIG ISLAND (`design_question/cand_2.jpg`), was not in this round. Its round 1 card-size skips ("dark and small") are the same failure NO OCEAN shows here. Add it as a third arm only after a luma and chroma fix and a mini blind check at a low Up next slot.

**Conditions for the set.**
- Frame 1 = NO OCEAN.
- The Maui Nui shot by 0:14, and the narration names the islands that join ("Maui, Molokaʻi and Lānaʻi were one island"), so ONE ISLAND does not over-promise "all of Hawaii".
- C's "you are here" insert in the film is no longer needed for the thumbnail. It can stay as a film gag.

**Optional fix to A before upload (it does not block the upload).**
- The complaints are about *grey, muted, muddy*, not darkness. NO OCEAN already sits at mean luma 109.
- This round's luma does not predict picks: E is the **darkest** card at **62** and won 8/10; F at 104 and G at 113 got 0/10; B at 132 got 4/10.
- What E has is saturated shapes against a neutral ground. The playbook's B7 advice ("lift with cool, desaturated grey basalt") may have traded colour for luma.
- If A is touched, add chroma to the green and rust island cap against the grey flank. Do not add more luma. Re-run `gate.py` (tan 10% or less, red 3% or less) and the 168x94 glance.

---

## 4. Title: the launch title holds

**The test:** A and D carry the same image.
- A: 3/10 picks, 2 first clicks. D: 2/10 picks, 0 first clicks.
- Round 2 models favour A (A > D in 92% of persona resamples). The pooled round 1 + round 2 model slightly favours D (+0.42 vs +0.02). Round 1 had A 9/10 and D 7/10, with different images.
- The test is confounded: A had the top Home slot and D the bottom one.

**Verdict:** nothing here argues for a switch, and nothing proves A is better. **Keep "Why Can't You See Most of Hawaii? (Look Down)" word for word.**

**What round 2 adds about D.** D's title is the most consistently attractive line in the ep02 set. It drew interest in all 10 of its exposures, including 8 skips, and the skips blamed the image. It stays **backup 1** under the stall rule, with one condition. The stall rule changes the title only, so all the arms would then carry "sinking" over images that do not show it, and two personas and the glance read flagged that mismatch. If the stall rule fires, pair D with an image that shows the island pressing down or subsiding. In round 1, D's own pairing was BIG ISLAND, which scored 7/10.

---

## 5. ep01: the repackage loses to the control. Do not apply it.

**Result.**
- E: 8/10, with 5 first clicks.
- F and G: **0/10 each**, so 0 of 20 between them.
- The persona-level sign test is 5/5 personas preferring E, one-sided p = 0.03. That is the strongest result five personas can give.

**Confound check.**
- E's Home feed had the weakest hosts: PBS Eons, Greenland, RealLifeLore's 10-year-old map video, and no Map Pack. F's and G's Home feeds both had Map Pack, which took 9 of 10 first clicks there.
- On Up next the confound runs the other way. E sat at the **last slot**, next to **both** Astrum and Map Pack, and was still picked 3/5. F at slot 7 (no Astrum) and G at slot 6 got 0/5.
- So the result does not rest on the host mix.

**What drove it.**
- **The thumbnail text and the bracket.** The title phrase "Why the Continents Point South" is shared by all three arms and attracted interest even on F and G.
- E differs from F and G in both the thumbnail and the bracket, so this round cannot say which one did the work.
- Each failed in a stated way:
  - No text: 5/5 personas.
  - "(Pangaea's Breakup)" read as a lesson, or as the now-playing video: 4/5.
  - "(Not Just a Coincidence)" read as the promise of a real answer: 3 personas.

**Why round 1's 8/10 for the seam globe did not hold.**
- **Host set:** round 1's ep01 hosts were older and weaker, with no Map Pack, Greenland, History of the Earth or Atlas Pro future video.
- **Bracket:** it changed from "(It's a Breakup)" to "(Pangaea's Breakup)".
- **Image:** the camera was pulled back, which made the seam smaller.
- Round 1 also had **no control arm**, so its 8/10 measured the globe against hosts, never against the live package.

**Consequences for the playbook.**
- Retract the "Proposed" ep01 package in section 10 and retire `final_ep01_1.jpg` and `final_ep01_2.jpg`.
- Section 1's diagnosis of the live thumbnail is **not supported** by this round: "POINTING AT WHAT? shrinks to 10 px letters", "a question nobody had", and the hedge bracket. Three personas read and picked it from the bottom of Up next, and the question was the reason.
- Ep01's real Suggested CTR of 1.97% is real data and outranks simulated personas. If ep01 is worked on, start **from E's concept** (a visible question plus the shapes that pose it) and keep its bracket. Any challenger must beat E head to head in a balanced round.
- Rule B2 is confirmed: no-text thumbnails are now **1 of 40** across both rounds.
- Rule B5's luma floor did not predict picks here: E at 62 won.

---

## 6. Flaws in this round, and the fix for round 3

1. **Slots were seeded random draws, not the planned middle slots** (Home 2-3, Up next 5-7).
   - A sat at Up next 8/8 and Home 1/4. B sat at Up next 1/8. D and F sat at Home 4/4. E sat at Up next 8/8.
   - The pooled slot term is about -0.24 per slot. So the same card at Up next slot 8 has roughly **0.19x** the pick weight it would have at slot 1, which is as big as any arm difference in ep02.
   - Pick reasons confirm it: all 4 of B's picks and 2 of A's 3 cite position.
2. **Host mixes differed between arms of the same episode.**
   - Park Vibes was in the Up next feeds of A, C and D but not B.
   - Map Pack was in the Home feeds of F and G but not E.
3. **Within-subject design.** Each persona saw every arm, and some carried over ("forbidden island again", "the engineering question again").
4. **Five simulated personas, 10 trials per arm.** Treat ep02's 4 vs 3 vs 2 as ties.

**Fix.** Within each (episode, surface), give every arm **the same host set in the same order, and our card in the same slot**. Better still, rotate every arm through the same 2-3 middle slots (a Latin square), so that slot and hosts cancel out.

---

## 7. Changes to make in `packaging_playbook.md`

- Section 9: thumbnails for Test & Compare become **A (default) and B**, with C retired. Keep BIG ISLAND as a reserve, which needs a fix and a blind check. Add the narration condition on Maui Nui.
- Section 9, backup titles: add the pairing note to backup 1, that D needs an image that says "sinking".
- Section 10: the ep01 repackage is **withdrawn**. Keep the live package.
- Section 1: soften the ep01 thumbnail diagnosis (see section 5 above).
- Section 8, protocol step 4: replace "slots balanced" with a fixed host set and fixed or rotated slots per arm, and require a live control arm whenever an existing video is being repackaged.
