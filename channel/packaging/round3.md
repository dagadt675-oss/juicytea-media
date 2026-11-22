# Blind feed test, round 3: the NO OCEAN colour fix

Date: 2026-11-08. Key: `feeds/r3_key.json` (20 feeds, `feeds/r3_1.png` to `r3_20.png`). Scorer: `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/r3score/score_r3.py` (picks hand-coded from the vote text; output in `r3score/r3_scores.json`, our card cropped from every feed in `r3score/cards_sheet.jpg`). Paths are relative to `research/packaging/` unless they start with `/`.

**Read this first: the sample is small.** Five simulated viewer personas, the same five as rounds 1 and 2: P1 a novelty-seeking teen, P2 a dad watching over lunch (a RealLifeLore regular), P3 a UK commuter, P4 an engineering student, P5 a trust-driven retiree. Each arm was shown in 5 feeds (Up next slots 2, 5 and 7; Home slots 1 and 3), so it had **25 trials**. The trials are not independent: five people made all of them. The honest unit of evidence is the persona, and with five personas the strongest possible result is "5 of 5", one-sided p = 0.03. The control vs challenger gap is the largest effect any of our rounds has measured; the gaps between the three challengers are noise.

**Question.** Does a colour fix for the default ep02 thumbnail beat the current one? Rounds 1 and 2 tied NO OCEAN (`final_ep02_1.jpg`) for first, but in round 2 the personas called it grey, muted or small in 8 of 10 Up next exposures. Pass rule: at least +2 any-click picks of 25 over the control and no new repeated objection.

**Design.** All four arms carried the launch title "Why Can't You See Most of Hawaii? (Look Down)", the same NO OCEAN label and the same meta line ("Myth Juice · 1.2K views · 2d ago", 12:53). Each surface had one fixed host set in one fixed order, and every arm sat once in each of the same five slots. This fixes round 2's two big confounds (random slots and different host mixes). Up next: our card plus Signore Galilei, Nat Geo Drain the Oceans, Unseen Works PACIFIC DRAINED, Physics Girl, Park Vibes (forbidden island), Atlas Pro and Be Smart, under RealLifeLore's boats video as the now-playing video. Home: our card plus Below The Map (IT'S MOVING), PACIFIC DRAINED and RealLifeLore.

| Arm | File | Change |
|---|---|---|
| CTRL | `final_ep02_1.jpg` as it was (now `final_ep02_1_prev.jpg`) | The round 1/2 default: grey basalt flank, muted green-rust cap |
| cand_1 | `fix_noocean/cand_1.jpg` | Same camera and crop; saturated cap (emerald and rust), darker cool flank, thin white line on today's coast |
| cand_2 | `fix_noocean/cand_2.jpg` | The same fix with a tighter crop (zoom 1.32), rainforest green, a deeper blue sky gradient at the top |
| cand_3 | `fix_noocean/cand_3.jpg` | Medium crop (1.27), higher sun, browns pulled to rust-red, the most chromatic cap |

---

## 1. Decision

| Question | Decision | Strength of evidence |
|---|---|---|
| Does a variant clearly beat CTRL? | **Yes. All three do.** cand_2 10/25, cand_1 9/25, cand_3 8/25 against CTRL 2/25 (+6 to +8, the bar is +2). | **Strong for "fix beats control"**: cand_1 and cand_2 were picked more often than CTRL by **all 5** personas (one-sided p = 0.03, the floor for n = 5); in matched cells (same persona, slot and hosts) cand_2 won 9 and lost 1 (p = 0.02); CTRL was called grey, washed out or dark in 22 of its 25 exposures, each challenger in 1. |
| Which one? | **cand_2**, installed as `final_ep02_1.jpg`. | **Weak.** 10 vs 9 vs 8 picks is noise (matched cells: cand_2 vs cand_1 3 to 2, vs cand_3 2 to 0). cand_2 wins on the tie-breakers in section 4. |
| New repeated objection? | **None caused by the image.** One repeated objection appears on every challenger and not on CTRL: "the same idea as PACIFIC DRAINED". It is a premise collision with a host that every arm faces once its card is read; CTRL avoided it only because it was not read at all (section 6). It is logged as a package risk. | Judgment call, stated so it can be challenged. |
| Up next slots 5 and 7 | **Unsolved.** 0 of 40 trials across all four arms, the control included. | Solid as a description of this host set. |

What changed on disk: `final_ep02_1.jpg` (old) was copied to `final_ep02_1_prev.jpg`; `fix_noocean/cand_2.jpg` was copied to `final_ep02_1.jpg` (md5 `bbb4e3bb750f1681f0ef7c11d9244e37`); `final_overview.jpg` was re-rendered (old copy `final_overview_prev.jpg`). Nothing was uploaded to YouTube.

---

## 2. Per-candidate results

Random baseline per arm (3 Up next feeds with 8 cards, 2 Home feeds with 4 cards, 5 personas): **4.4 first clicks and 8.75 picks of 25**.

| Arm | First-click share | Any-click share | vs random | Up next (any / first) | Home (any / first) | Picks per persona P1-P5 |
|---|---|---|---|---|---|---|
| CTRL | **0/25** (0%) | **2/25** (8%) | 0.23x | 2/15 / 0 | 0/10 / 0 | 1, 0, 0, 1, 0 |
| cand_1 | 1/25 (4%) | 9/25 (36%) | 1.03x | **4/15** / 0 | 5/10 / 1 | 2, 1, 3, 2, 1 |
| **cand_2** | **4/25** (16%) | **10/25** (40%) | **1.14x** | 3/15 / 0 | **7/10 / 4** | 2, 1, 3, 2, 2 |
| cand_3 | **4/25** (16%) | 8/25 (32%) | 0.91x | 2/15 / 1 | 6/10 / 3 | 1, 1, 3, 2, 1 |

**By slot** (F = first click, S = second click, - = not picked; personas in the order P1 P2 P3 P4 P5):

| Slot (feed) | CTRL | cand_1 | cand_2 | cand_3 |
|---|---|---|---|---|
| Up next 2 | `S--S-` 2/5 (r3_3) | `SSSS-` 4/5 (r3_17) | `--SSS` 3/5 (r3_9) | `--FS-` 2/5 (r3_19) |
| Up next 5 | `-----` 0/5 (r3_20) | `-----` 0/5 (r3_12) | `-----` 0/5 (r3_1) | `-----` 0/5 (r3_6) |
| Up next 7 | `-----` 0/5 (r3_8) | `-----` 0/5 (r3_15) | `-----` 0/5 (r3_13) | `-----` 0/5 (r3_16) |
| Home 1 | `-----` 0/5 (r3_2) | `F-SSS` 4/5 (r3_10) | `FSFFF` **5/5, 4 first** (r3_14) | `SSFFF` 5/5, 3 first (r3_7) |
| Home 3 | `-----` 0/5 (r3_5) | `--S--` 1/5 (r3_18) | `S-S--` 2/5 (r3_11) | `--S--` 1/5 (r3_4) |

Reading the table:
- **Home slot 1 is the cleanest head-to-head.** The four feeds are identical except for our thumbnail. CTRL got 0 of 5; each challenger got 4 or 5 of 5. All five personas skipped CTRL there as grey, dark or ordinary, and four said they could not tell what it showed or that it did not match the label ("'no ocean' didn't make sense against that picture", P3; "'No Ocean' didn't click for me at a glance", P5).
- **Up next slot 2 moved less.** CTRL 2/5, challengers 2-4/5. On Up next the gain is +0 to +2 of 15. Most of the total gain came from Home.
- **Up next slots 5 and 7 gave nothing to any arm.** See section 5.

**Statistics.** Treat them as a sanity check, not as proof; personas are the unit and there are five.

| Test | cand_1 | cand_2 | cand_3 |
|---|---|---|---|
| Personas picking it more often than CTRL (up / down / tie), one-sided sign test | 5 / 0 / 0, p = 0.031 | 5 / 0 / 0, p = 0.031 | 4 / 0 / 1, p = 0.063 |
| Matched cells vs CTRL (same persona, slot and hosts): arm-only / CTRL-only picks, exact two-sided | 7 / 0, p = 0.016 | 9 / 1, p = 0.021 | 7 / 1, p = 0.070 |
| Fisher exact vs CTRL on 25 vs 25 (ignores clustering, so optimistic) | p = 0.037 | p = 0.018 | p = 0.074 |
| Plackett-Luce top-2 log-strength, no slot term (CTRL -1.38) | +0.33 | **+0.64** | +0.29 |
| Plackett-Luce, linear slot term (CTRL -2.27) | -0.31 | **+0.22** | -0.22 |
| Persona bootstrap (40 resamples): beats CTRL / is the top arm | 100% / 0% | 100% / **85%** | 100% / 15% |

The slot term is poorly identified in this design (the hosts never move, so position and host identity are tangled; it gives Be Smart, always last, an implausible +2.38). Because every arm sat in the same slots, the raw counts compare the arms fairly without it.

**Host context.** Park Vibes' forbidden island took the first click in 35 of its 60 appearances (58%), PACIFIC DRAINED was picked in 50 of 100 (31 first), IT'S MOVING in 18 of 40, RealLifeLore in 14 of 40, Nat Geo in 12 of 60 (all first clicks, all from P5). Atlas Pro's Biogeography got 0 of 60. Our arms together took 29 of 100 trials (CTRL 2, challengers 27).

---

## 3. Skip reasons: the grey objection is gone, "small" is not

Coded from the `noticed_but_skipped` and `why` text of all 100 trials. A trial can carry several codes; "personas" is how many of the five raised it at least once for that arm.

| Reason given about our card | CTRL | cand_1 | cand_2 | cand_3 |
|---|---|---|---|---|
| **Grey, greyish, muted, dull, washed out, pale, dark, dim or muddy** | **22 trials, 5 personas** | 1 (P4: "muddy") | 1 (P5: "small dark aerial picture") | 1 (P5: "dull grey-green") |
| The picture does not say "no ocean" / can't tell what it shows | 6 trials, 5 personas | 2 trials, 2 personas | 2 trials, 2 personas | **3 trials, 3 personas** (all in r3_19, Up next 2) |
| Small or tiny at card size | 4 trials, 3 personas | 3 trials, 3 personas (all at Up next 5) | 4 trials, 4 personas | 5 trials, 3 personas |
| Same idea as PACIFIC DRAINED | 0 | 7 trials, 4 personas | 4 trials, 3 personas | 5 trials, 4 personas |
| Same payoff as Be Smart's tallest-mountain video | 1 | 2 | 1 | 0 |
| Low views or unknown channel (identical meta line for every arm) | 3 trials, 3 personas | 4 trials, 3 personas | 2 trials, 1 persona | 3 trials, 2 personas |
| Position: already decided, stopped scrolling, too far down | 5 (all at Up next 7) | 3 | 6 | 6 |
| *Positive colour words (colourful, bright, vivid, glowing, red and green), any trial* | *1 of 25* | *22 of 25* | *22 of 25* | *21 of 25* |

Typical quotes:
- **CTRL:** "grey and kind of blurry, like a regular photo of a mountain" (P1, Home 1); "a grayish, washed-out Google Earth screenshot and I wasn't sure what I was looking at" (P2, Home 1); "at that size it was a dark, muddy smudge" (P2, Up next 2); "looks pale and washed out, like a generic aerial photo, so it blended in" (P3, Up next 5); "a normal greenish aerial photo with a grey seabed and nothing pops" (P4, Up next 5).
- **cand_2:** "super vivid, like a glowing 3D map of a giant mountain, and the huge NO OCEAN text plus 'look down' made me curious right away" (P1, Home 1, first click); "a real mountain rising out of a dry seafloor, at an angle where you can feel how deep it goes" (P2, Home 1); "vivid red and green with a white coastline looks almost unreal" (P3, Home 3); "bright red/green terrain that stood out from the blue/grey ones" (P3, Up next 2).
- **The white coast line did semantic work:** "the white coastline make it look like the ocean has been peeled off" (P4, cand_1); "white edges" (P2, cand_3); "a heat map with a white coastline and the sea gone. Together with 'Look Down' I instantly got that most of the mountain is underwater" (P4, cand_3).

**Conclusion.** The round 2 objection is fixed: grey/muted fell from 22 of 25 trials to 1 of 25 in every challenger, and the image now carries the label (all five personas described CTRL as an ordinary or unreadable photo at least once; 2-3 said so about each challenger). "Small" is **not** fixed. It was raised by 3-4 personas for every arm, CTRL included, and it is not new. It is the residual cost of the 168x94 card in the lower half of the list.

---

## 4. Why cand_2 and not cand_1 or cand_3

The three challengers are statistically tied (8-10 of 25; no pair differs by more than 3 to 2 in matched cells). The pick rests on tie-breakers:

1. **Picks and first clicks.** cand_2 has the most picks (10) and ties cand_3 for the most first clicks (4). cand_1 drew 1 first click. At Home slot 1, with everything else identical, cand_2 got 4 first clicks of 5, cand_3 3 and cand_1 1 (P3 on cand_1 there: "the darker, moodier NO OCEAN at the top caught my eye but didn't quite hook me").
2. **Model and bootstrap.** cand_2 has the highest Plackett-Luce strength with and without a slot term, and is the top arm in 85% of persona resamples (cand_3 15%, cand_1 0%).
3. **Objections.** cand_3 carries the only repeated "can't tell what it shows" objection (3 personas, one feed: "kind of like a regular map", "a colorful blob of land", "dull grey-green"). Three personas also read cand_3 as a "heat map". cand_2 has the fewest personas raising the PACIFIC DRAINED overlap (3, against 4 for cand_1 and cand_3).
4. **Gate.** cand_2 has the widest clone margin (11.92 vs bar 11.71) and a safe farm margin (11.51 vs 11.43). cand_3's farm margin is 11.45, as thin as ONE ISLAND's.
5. **Feed metrics.** cand_2 is the most colourful (Hasler-Susstrunk 54.7, +64% over CTRL's 33.3) and ranks 3-4 of 10 for bright saturated pixels in the simulated Up next (CTRL 7).

**What speaks for cand_1:** the most Up next picks (4 of 15 vs 3), the most near-miss skips (4: "almost tapped it", "almost got me"), and the same camera and crop as the old final, so the film's frame 1 would change less. Because the film is not produced yet (ep02 production A is still pending), the crop difference costs nothing now. **cand_1 is the fallback** if the tighter crop causes a problem in the film.

**Costs of cand_2 to know about.**
- Mean luma 101: above the floor of 100 but below the playbook's target of 105-120. This round says luma was not the problem: CTRL at 109 lost to cand_2 at 101.
- p90 200 (spec 190 or more); label cap height 16% (spec 13-16%, at the top of the range); label contrast 147 levels at 168x94 (spec 100 or more); text width 47% (spec 62% or less); bottom-right timestamp corner clear (flank at luma 36).

---

## 5. What did not change: the low Up next slots

**0 picks in 40 trials** at Up next slots 5 and 7, across all four arms. The skip reasons there are position ("I'd already decided", "stopped scrolling"), size ("tiny", "small and halfway down"), the identical low view count, and the PACIFIC DRAINED overlap. Under the fixed host order, the cards above slot 5 include the forbidden island, Nat Geo and PACIFIC DRAINED, the three strongest hosts in this set. No grade can fix that. Do not read the fix as "Up next is solved": the improvement is real on Home and at Up next slot 2, and absent lower down.

---

## 6. The "same idea as PACIFIC DRAINED" objection

- **What it is.** 3-4 personas per challenger skipped our card because Unseen Works' "What the Pacific Ocean Looks Like Drained?" (120K views, 4 days old, big yellow text and a lava cutaway) had already given them the "water gone" idea. It cuts both ways: in 8 trials where our card was picked, 3 personas (P2, P3, P4) skipped PACIFIC DRAINED for the same reason ("Pacific Drained, which felt redundant once I'd picked NO OCEAN", P2; "similar idea to NO OCEAN, I only want one of these", P3).
- **Why it is not a new objection to the image.** CTRL never got far enough to collide: it was dismissed as grey before its premise was read (all five personas described it as an ordinary or unreadable photo). The challengers communicate the label, so they meet the same-premise host head on. The objection belongs to the premise and the host set. Any NO OCEAN image that works will face it.
- **What to do with it.** Log it as a package risk under rule T2 (premise probe): a same-premise upload now sits in our host cluster. Watch the real Suggested sources after upload. If PACIFIC DRAINED keeps growing, the ONE ISLAND arm (a premise PACIFIC DRAINED does not cover) becomes more valuable, and the bracket "(Look Down)" is our differentiator: the personas who picked our card named it again ("'look down' made me curious", P1; "'Look Down' sealed it", P3).
- **Guardrail on the white coast line.** It must stay a thin, solid line that follows the terrain, reading as surf or coastline. A dashed, straight or labelled sea-level line is clone kit (rule B6, banned patterns) and must not be added.

---

## 7. Flaws in this round

1. **Five simulated personas.** 25 trials per arm, but only five independent viewers. The control vs fix result is as strong as five personas can make it; the challenger ranking is not.
2. **Within-subject design, and the personas noticed it.** Every persona saw all four versions of the same card, 20 times in total, and several compared them ("this NO OCEAN version is washed out", "the colours popped a bit more", "this time"). Real viewers see one version once. This likely sharpens the contrast between versions beyond what real viewers would show. The direction of the result is credible; its size is probably inflated.
3. **Fixed feed order.** CTRL's feeds came early (feeds 2, 3, 5, 8 and 20), cand_1's late (10-18). A learning or fatigue effect could favour late arms. Check: CTRL's last feed (r3_20, the final feed of the round) still got 0 of 5 picks, and all five called it grey, pale, washed out or flat ("nothing pops"). The objection is about the image, not the order.
4. **Host order fixed per surface.** This makes the arms comparable, but position and host identity cannot be separated, so the slot term and the host strengths are unreliable (section 2).
5. **No separate cold-glance reader** this round; the glance read comes only from the personas' own descriptions.
6. **ONE ISLAND (arm B) was not in this round.** Its status is unchanged from round 2. The new A has not been tested against it.
7. **Same title, label and meta line for every arm**, by design. The low view count was cited against every arm, mostly by P4 and P5. That is real at launch and cannot be fixed by packaging.

---

## 8. What was installed

| Item | Value |
|---|---|
| New default | `final_ep02_1.jpg` = `fix_noocean/cand_2.jpg` (byte-identical, md5 `bbb4e3bb750f1681f0ef7c11d9244e37`), 1280x720, progressive JPEG, 196 KB |
| Previous default | `final_ep02_1_prev.jpg` (md5 `769959bf1b4de9ef42a0f5a49405d5e2`). Keep it as the round 1/2 record; do not upload it as a test arm (2/25) |
| Gate (re-run today) | `gate.py` PASS: drain clones 11.92 (bar 11.71), template farms 11.51 (bar 11.43); tan 1%, red 1%, blue 35% |
| Metrics | Mean luma 101, p90 200, SD 66, colourfulness 54.7 (CTRL 33.3), cap share 24%, NO OCEAN at 16% cap height and 47% width, label contrast 147 levels at 168x94 |
| Plate | `fix_noocean/work/r/d3.jpg`, engine query in `fix_noocean/work/r/queries.json` key `d3` (same camera as the old plate: lon -155.32, lat 18.42, 26 km, fov 40; `landSat` 1.6, `landGain` 2.7, `sun` [262,9], darker cool basalt and sediment, `line` 1 with `lineW` 1.1) rendered with `fix_noocean/tools/rend.py` |
| Rebuild | `python3 -I fix_noocean/tools/build.py fix_noocean/final_cfg.json OUTDIR` (key `cand_2`). Checked today: it reproduces the installed file byte for byte |
| Overview | `final_overview.jpg` re-rendered with `final_work/tools/overview.py` (old copy `final_overview_prev.jpg`). The NO OCEAN card text now gives the round 3 numbers. The two labels the round 2 results had made stale are corrected too: YOU ARE HERE is marked as dropped, and the ep01 proposal as withdrawn |

**Film condition.** Frame 1 must match the new default: the `d3` engine settings, the crop at zoom 1.32 (centre 0.47/0.49) or the equivalent camera, and the cap/flank grade, at SSIM 0.8+ at 320x180 without the label against the new `final_ep02_1.jpg`.

---

## 9. Changes to the playbook

Applied:
- **Section 9:** the new default and its round 3 result, the fallback (cand_1), the PACIFIC DRAINED risk, the unsolved low Up next slots, and the frame 1 condition.
- **Section 4:** the "Ep02 finals" column for `final_ep02_1` and its rebuild line now describe the new file. Without this the spec sheet would rebuild the old grey version.
- **Section 11:** the round 3 files.

Proposed, not applied (rules in section 3 need the owner's eye; one round of five personas is thin ground for a permanent rule):
- **B5/B7:** replace "lift brightness with cool, desaturated grey basalt" with "keep the flank dark and cool, and put chroma on the hero (cap): saturated greens and rust against a neutral ground". Round 3 is the third round in which luma did not predict picks (CTRL 109 lost to 101), and the first in which chroma clearly did.
- **B4:** add "the image must carry the label at card size". CTRL's NO OCEAN label lost 5 of 5 personas because the picture did not show the ocean gone; a thin white coast line fixed that.
- **Section 8, step 4:** rotate the feed order per persona (not one fixed order for all), and show each persona only one version of a card, or at most two, so that personas cannot compare versions.
