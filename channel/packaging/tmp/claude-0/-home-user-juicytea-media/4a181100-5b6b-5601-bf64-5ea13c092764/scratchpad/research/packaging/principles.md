# Packaging principles: titles and thumbnails for a faceless map channel

Date: 2026-11-08. Packaging lab, principles step. This is the rulebook that every Myth Juice title and thumbnail is checked against, starting with ep02 (Hawaiʻi). It replaces the `packaging_rules` P1-P9 in `longform/ep02-hawaii/research/topic_hunt.json` where they conflict (section 5).

Inputs: YouTube's own help pages and Creator Insider statements; MrBeast's production notes and his thumbnail lead; Paddy Galloway; Film Booth; Jenny Hoyos; Aprilynne Alter; one vidIQ call (10 before/after packaging changes in our niche); and the lab's own data: `title_anatomy.md` (6,528 titles), `thumbnail_anatomy.md` (247 thumbnails), and the niche study (`research/niche/niche_report.md`). Paths are relative to `research/packaging/` unless they start with `research/`.

---

## The short answer

Twelve rules. Each one has a pass/fail test (section 2), and none of them needs a face.

| # | Rule | Pass test, in one line |
|---|---|---|
| PK1 | **Package first.** If the idea cannot be packaged, change the angle, not the wording. | A 15-word promise sentence exists, and 2 of 3 cold readers can say what the film shows from the card alone. |
| PK2 | **One glance, one idea.** One hero shape, at most one anchor, at most one text item, no devices. | At most 3 elements; in the dark-mode strip 3 of 3 viewers find ours and name the place within 2 s. |
| PK3 | **The gap is one specific withheld answer** that the film shows on screen. | The viewer's question fits in 8 words, and its answer is one true sentence with a timestamp in the film. |
| PK4 | **Title and thumbnail split the work.** The title is the claim, the thumbnail is the evidence. They never repeat each other. | 0 shared content words, except the place name on the postcard (tested without it in Arm C). |
| PK5 | **Familiar to the host, foreign to the lane.** Use the host videos' words and break the clone lane's picture grammar. | Title regex clean, proper noun in the first 3 words, 41-50 characters; thumbnail passes `gate.py` and beats the craft median distance. |
| PK6 | **Contrast is relative, not absolute.** There is no brightness target. Stand out from the cards next to ours. | Ours is the most distinct card in hue and value in both feed strips; the hero is the high-contrast region of the frame. |
| PK7 | **Replace the face with one anchor:** a familiar object, a true-scale human-sized object, a creature or light. | Exactly 1 anchor; 3 of 3 viewers identify it at 390x220. No faces of any kind. |
| PK8 | **Text must earn its place.** 0-3 words, on the postcard or the image, never in a box. | Cap height 12-18%, at most 2 lines, no digits, readable at 168x94, ʻokina and kahakō correct. |
| PK9 | **Promise no more than the film proves.** Keep every qualifier and use no spent hooks. | Every word and picture maps to a timestamp: part of the promise paid by 0:30, all of it by the end. |
| PK10 | **Frame 1 is the thumbnail.** | SSIM of 0.8 or more at 320x180; the title's words are spoken by 0:10. |
| PK11 | **Test the way YouTube scores.** Watch time share decides, not CTR; arms must be really different. | 3 arms that differ in composition, anchor or state; judged on CTR x AVD within the Suggested source. |
| PK12 | **A signature, not a template.** The visual device repeats; the title grammar changes every episode. | 24 h before upload there is still no postcard-object thumbnail in the place's cluster, and the title grammar differs from the last episode's. |

**Three findings change the old rules.**

1. **Brightness is not the lever.** In our space the top performers are darker than the rest (median luma 90 vs 105, p = 0.016). In the vidIQ before/after cases, 6 of 7 new thumbnails were *less* colourful than the old ones. Only 13% of winners meet P5's "40% bright" rule. P5's absolute brightness target is retired (PK6).
2. **The generic postcard view lost every time it was tested.** Bolivia's lake-and-llama panorama lost to one strange close subject (houses on a cliff): ×3.5 views per hour. The Netherlands' tulips-and-windmill lost to "a country below sea level" (×2.1). This supports "Below the Postcard" only if the postcard stays a *small object* and the strange real shape dominates the frame.
3. **Faces are not missing from what wins here.** Faces appear on 5% of the winners and 12% of the rest. A faceless map channel replaces the face with *scale and one familiar object*, not with a stock or generated face (PK7).

---

## 1. What the evidence says

### 1.1 YouTube's own guidance

| What YouTube says | Source | What it means for us |
|---|---|---|
| Test & Compare picks the winner by **watch time share**, not CTR: "we optimize tests for overall watch time over other metrics, like click-through-rate", because "Great titles and thumbnails serve an important purpose beyond getting viewers to click." Up to 3 titles, thumbnails or combinations. A test runs up to 2 weeks. Outcomes are Winner, Performed Same or Inconclusive; if no option wins, the first one uploaded stays. | Help: A/B test titles & thumbnails (16391400); Test & compare thumbnails (13861714) | A package that clicks but disappoints loses its own test. Score arms on CTR x AVD, never on CTR alone. |
| "Testing titles and thumbnails that are too similar to each other can cause tests to run for longer." Changing the title or thumbnail during a test stops it. Thumbnails below 720p downscale every arm to 480p. | Same page | Arms must differ in idea (composition, anchor or state), not in colour or font. Upload 1280x720 or larger. Never touch the package mid-test. |
| "Half of all channels and videos on YouTube have an impressions CTR that can range between 2% and 10%." "If a video gets a lot of impressions (such as if it appears on the Home Page), it's natural for the CTR to be lower." Differences "might be due to traffic sources, rather than the title or thumbnail." | Help: Impressions and CTR FAQ (7628154) | Ep01's 1.97% Suggested CTR is below the typical band. Compare CTR within one traffic source and against our own videos. A falling CTR while impressions rise is expected; it is not a signal to repackage. |
| As content "gains more impressions, it is possible that your CTR will decrease"; Search gives "fewer impressions but a higher CTR"; the Homepage gives a "high volume of impressions but often a lower CTR". | Help: Decoding CTR & impressions (16767369) | Same. |
| "Make sure your title accurately represents the video. If not, viewers may stop watching, which can impact discoverability." "Put the most important words near the beginning." Searchable titles say what to expect; intriguing titles "spark curiosity" and reach viewers not looking for the topic. The page shows examples of "thumbnails and titles working together to create interest and tell a story". Too much detail can overwhelm a thumbnail. | Help: Thumbnail & title tips (12340300) | A Suggested-first video needs an *intriguing* title that still starts with the searchable proper noun. Title and thumbnail tell one story together (PK4). |
| YouTube removes videos whose title or thumbnail promises something the video does not deliver ("egregious clickbait"). Enforcement began in India in Dec 2024, starting with news and current events. | YouTube India blog, 18 Dec 2024 | Overclaiming is a policy risk as well as a trust risk (PK9). |
| Made on YouTube, 23 Sep 2026: **dynamic thumbnails** (creators upload several; YouTube picks per viewer) and video A/B tests of up to 3 cuts (Shorts from 2027). Todd Beaupré (YouTube, Oct 2026): today's A/B is "pretty much an even split randomly". The new system starts random, then shifts impressions to the images that work for each segment; prior channel watch history (newcomers vs core fans) is the segment he is most excited about. | TechCrunch, 23 Sep 2026; NetInfluencer on Creator Insider, 30 Oct 2026 | Design the 3 arms for 3 different viewers (PK11), not 3 shades of one idea. |

### 1.2 Practitioners

| Who | What they say (verbatim where marked) | Reliability |
|---|---|---|
| **MrBeast production notes** ("How to Succeed in MrBeast Production", leaked Sept 2024) | "CTR is what dictates what we do for videos." The creative process starts with the title and thumbnail, which "set the expectations for the viewer". The first minute must show that "their expectations from the thumbnail will be met". "I Spent 50 Hours In My Front Yard" is lame; "I Spent 50 Hours In Ketchup" gets the click. | Authenticity never confirmed; quoted from Simon Willison's write-up. |
| **Chucky Appleby**, MrBeast's thumbnail lead, on Creator Insider | "Make your thumbnail easy to understand." Viewers who need "10 or 20 seconds" to get it keep scrolling. Designing on a big screen hides how small details look at thumbnail size. Across about 30 tested videos, "all 30 of them with the closed mouth actually led to higher watch time." The face "typically wins" in early tests, but in back-catalog tests images without it "sometimes win"; "it always flip-flops based off the audiences." | Social Media Today; NetInfluencer. Secondary write-ups of primary interviews. |
| **Paddy Galloway** | Opening a curiosity gap is "the most important thing". "If they don't click, they don't watch." "Your video should be familiar but also unexpected." "Pull your packaging to the most exaggerated version of what it is", then scale back. "Writing 30 titles and thumbnail concepts together can take 10 minutes or less." Predict each video's score out of 10 before upload. When the category copies your visual language, "I usually advise doubling down rather than changing." On logos in thumbnails: "I'm not a fan of that." The intro should make viewers feel they "made the right decision and not stupid for clicking." "The difference between a million views and 28 million views is how you package it." | Edited transcript of Colin and Samir, "The New Rules of YouTube (2025)"; Colin and Samir resource page. |
| **Film Booth** (Ed Lawrence), "Sneaky Tricks YouTubers Use To Hook You" | A video that was really "I sat in silence for 45 minutes" became an exciting challenge through "the way he presented this idea with his thumbnail and title". "Think about how to present an idea so it creates anticipation." "There is no room for confusion." The best creators' first line "tells the entire story". | GoTranscript transcript with unlabelled speakers; the title matches Film Booth's 348K-view video. Medium reliability. |
| **Jenny Hoyos** | Packaging means the title and thumbnail. If an idea cannot be titled and thumbnailed in a clickable way, it is not an idea, and she scraps it. | Creator Science #167 episode page summary. Medium reliability. |
| **Aprilynne Alter** (strategist) | Thumbnail text "should only be used if it's additive to the story". "Your text should never just repeat your title." "Ensure your main character always remains the dominant element." A thumbnail that "contrasts with every thumbnail around it" pops. Recognisable interfaces (iMessage, PayPal) stop the scroll the way faces do. Check that it "makes sense at any size", including the small Suggested card, in a 2-second glance. | SozAI transcripts of her videos. Medium reliability. |

**Where they agree:** decide the package before the production; one idea readable in about 2 seconds at small size; a specific curiosity gap; title and thumbnail complement each other; the first minute confirms the promise; generate many options and test a few really different ones; keep a recognisable style and evolve it when copied.

**Where they disagree with our old rules:** nobody recommends absolute brightness targets, and the best-documented face experiment (MrBeast's closed mouth) was judged on *watch time*, not clicks.

### 1.3 Suggested vs Browse: what is and is not known

- **There is no credible public benchmark of CTR by traffic source.** Third-party "benchmarks" for Suggested range from 0.6% to 9.5% and contradict each other. YouTube publishes only the overall 2-10% band and says that traffic source explains much of the difference.
- **How Suggested works.** YouTube describes Suggested videos as topically related to the video being watched (same or other channels). Third-party analyses add co-viewing: videos often watched by the same viewers. So the Suggested viewer is *mid-watch on a host video*, not searching. Our card is a candidate "next video" for someone who already chose the topic.
- **Our own numbers:**
  - Ep01's Suggested CTR was 1.97% on 862 impressions.
  - Browse/Home was 8.82% on 34 impressions, which is 3 clicks and statistically meaningless.
  - Mobile was 44% of views. The Up Next list on a phone is a full-width card (about 390x220); the desktop sidebar is compact (168x94).
- **Rule.** Targets stay relative to our own baselines: ep02 Suggested CTR of 5% or more, and watch time per impression (CTR x AVD) of 15 s or more against ep01's 5.2 s. They are judged in the Suggested source only.

### 1.4 Our own data

| Finding | Number | Source |
|---|---|---|
| Top performers (100K+ views and 10x+ subscribers) are darker, not brighter | Median luma 90 vs 105 (p = 0.016); bright/saturated pixels 21% vs 27% (p = 0.008). Without deep-ocean titles, 95 vs 107 (n.s.) | `thumbnail_anatomy.md` 2.1 |
| Dark edges are not penalised | 35% of winners vs 16% of the rest have more than half of the outer border band near-black (luma < 35). Ep01's thumbnail: 45%, mean luma 60 | `work/darkmode_edge.py --calibrate` (this step) |
| Caption boxes are a non-winner marker among craft channels | 6% of winners vs 23% of the rest (p = 0.008) | `thumbnail_anatomy.md` |
| No device at all on winners | 54% (34 of 63) use no arrow, ring, box or label | same |
| Faces | 5% of winners, 12% of the rest | same |
| Logos and series frames | 3% of winners, 20% of the rest (p = 0.001), mostly big channels' frames | same |
| The Everest cluster is the worst performer | 0 of 7 eligible are top performers; 0.77x the channel median | same |
| Distinctiveness costs nothing | 32% of winners pass `gate.py` vs 24% of the rest; the drain clones pass 0% | same |
| **Distinctiveness is not sufficient** | Ep01's own thumbnail is far from the clones (12.09 to drain clones, 11.97 to farms) and still got 1.97% Suggested CTR | `gate.py` run (this step) |
| The craft median distance (the bar for "farther than the craft median") | Craft baseline to drain clones: median **11.71**; to template farms: median **11.43**. Clones to themselves: 8.72 | `work/craft_median.py` (this step) |
| Title promise beats title shape | Same-channel ratios: "Every X" 1.81, access 1.56, statement + twist 1.32, "Why X" 0.78, "How X" 0.71, "X Is Hiding Something" 0.60. 41-50 characters 1.03; 31-40 characters 0.83 | `title_anatomy.md` |
| Clone words still pull clicks outside clone channels | 1.18x; banning them is a positioning and trust choice with a small cost | same |

### 1.5 The vidIQ call: 10 packaging changes that at least doubled views per hour

One call, `vidiq_title_thumbnail_wins` (summary "geography, maps, earth science and history documentaries", sort views_ratio, limit 10, 5 credits).

- Data: `work/vidiq_wins.json`.
- Before/after crops: `refs/wins/NN_<name>_before.jpg` and `_after.jpg` (from vidIQ's sheet, `refs/wins/vidiq_wins_sheet.jpg`).
- Current thumbnails: `refs/wins/after_<id>.jpg`.
- Side-by-side sheet (before, after per vidIQ, current): `refs/wins/wins_compare.jpg`.
- The current thumbnails matched vidIQ's "after" for 6 of the 7 thumbnail changes. The Netherlands video has since changed again.

**Lift** is views per hour in hours 12-84 after the change divided by the same window before it.

| # | Video (channel, subs) | Change | Views/h | Why the new version probably worked |
|---|---|---|---|---|
| 1 | California (Odd Atlas Files, 7.4K) | Title: "California Is Not What You Think — The Map Proves It" → "California Is Hiding Something That Will Catch You Off Guard" | 2.9 → 12.5 (×4.3) | "Not what you think" names nothing to picture. The new title implies one concrete withheld thing. **But** it is the farm template, which scores 0.60x on the same channel in our data, and the channel has since renamed it again ("The Most Dangerous Parts Of California You've Never Heard Of"), so the win did not hold. The lesson is the *specific withheld object*, not the words. |
| 2 | Bolivia (TRUE GLOBE, 158K) | Thumbnail: a wide postcard panorama (lake, llama, woman in costume; 44% bright pixels) → one strange subject (houses clinging to a sheer cliff) filling the frame; the same one-word place label | 3.7 → 12.9 (×3.5) | The postcard view is the picture the viewer already has; the click comes from the view they do not have. One dominant, slightly impossible-looking subject. Bright pixels fell to 9%. **The strongest single support for "Below the Postcard"**, with the card small and the strange shape dominant. |
| 3 | Antarctica (Theodore's History, 57) | Thumbnail: bright poster with huge title text and a "1820 → 2026" timeline → dark storm, a lone figure with a lantern seen from behind, facing a wrecked ship | 1.4 → 4.2 (×3.0) | A small human figure gives emotion and story without a face. The information device (the timeline arrow) was dropped. Mean luma fell from 131 to 83, so darker won. |
| 4 | Black Sea flood (Silence of the Earth, 62.3K) | Thumbnail: top-down map of the basin + "DOCUMENTARY FOR SLEEP" → a small boat under a towering wave + "THE FLOOD THAT CHANGED HISTORY" | 4.3 → 10.0 (×2.3) | The text names the event and the stakes instead of the format. A human-sized object inside the giant force gives scale and fear. A flat top-down map is a weak hook; a low, side-on view of the force is strong. **Relevant: our engine's default top-down map views make weak thumbnails.** |
| 5 | 2004 tsunami (Sparkeology, 1.9K) | Title: "2004 Boxing Day Tsunami: The First 90 Minutes, Banda Aceh to Thailand" → "The Day 746 Miles Of Earth Suddenly Snapped" | 23.3 → 53.5 (×2.3) | A known news label ("I know this story") became a physical claim with one picturable number in US units. The thumbnail ("08 14 / 16 MINUTES AFTER EARTHQUAKE") carries time, not the title's miles, so the two complement each other. **Closest analogue to ep02:** reframe a famous place as a physical object. |
| 6 | Gold river (Hidden Ground, 231) | Thumbnail: a busy scene (man panning, river, mountains, "GOLD IS STILL HERE") → macro of gold flakes in a pan filling the frame + "175 YEARS LATER" | 1.4 → 3.3 (×2.3) | One object at macro scale replaced a five-element scene. The text moved from restating the claim to adding time. The text does echo the title's "175 Years", so repetition is not always fatal when the picture carries the message. |
| 7 | Impossible places (Travel Cipher, 6.1K) | Both: a fantasy floating rock → a believable giant baobab market; title "The Secrets Behind 50 UNESCO World Heritage Sites" → "50 Mysterious Places That Shouldn't Exist" | 1.8 → 4.0 (×2.2) | Confounded, because both changed. If anything, the implausible picture lost to a plausible-but-strange one. |
| 8 | Dangerous places (Mysteryon, 111) | Title: "The 6 Most Dangerous Places on Earth (Never Go Here)" → "6 Deadliest Places on Earth That Still Terrify Scientists" | 3.8 → 8.0 (×2.1) | Borrowed authority ("scientists") replaced a command bracket. The sample is tiny, and "terrify" is on our ban list. Our honest equivalent of authority is proof: "We Measured". |
| 9 | Snake prison island (CreatureCam, 1.4K) | Thumbnail: a "RESTRICTED AREA" sign on a buoy before a distant island → no text: barbed wire, a no-entry snake sign and an abandoned jacket on the shore | 1.8 → 3.8 (×2.1) | The caption went, and the image tells the threat itself. The abandoned jacket is a human trace that asks "what happened to them?" without a face. |
| 10 | Netherlands (Draft & Document 4k, 38) | Thumbnail: tulips and windmill (cliché postcard) → "A COUNTRY BELOW SEA LEVEL", a 7 m arrow, and the sea standing higher than the farmland behind a dike | 1.7 → 3.6 (×2.1) | The cliché lost to the geography concept: water higher than land. The arrow and number are the clone kit in *our* lane; we carry "water above land" with the waterline instead. The channel has since swapped to a third image, so the win was not stable. |

**Patterns across the 7 thumbnail changes**, measured on the crops (`refs/wins/`):
- **Specific beats pretty.** 5 of 7 dropped a generic, wide or pretty view for one specific, stranger subject (Bolivia, Netherlands, Antarctica, Gold, Snake island).
- **Less colour, not more.** 6 of 7 new images were less colourful (Hasler-Süsstrunk colourfulness, for example Bolivia 101 → 37 and Antarctica 31 → 22). Only one got clearly brighter (Gold, luma 82 → 104).
- **Human scale without a face.** 4 of 7 added or enlarged a human-scale cue: the lantern figure, the boat, the jacket, the market crowd. The other two that removed a person (Gold, Bolivia) replaced them with one object at close range.
- **Text has no consistent direction.** It was kept, changed, removed or added. *What* the text says mattered (event and stakes over format) more than whether there was text.

**Caveats:**
- These are tiny numbers (most lifts are from 1-4 views per hour).
- The sample is selected on outcome: vidIQ returns only wins, so failed changes are invisible.
- Late changes (day 6-42) re-expose a fading video, and some of the lift is YouTube re-testing it.
- 2 of the 10 "winners" were changed again later.
- Several of these channels look mass-produced.

Read the cases as *hypotheses that agree with the larger data sets*, not as proof.

---

## 2. The principles

Format for each: the **rule**, **why** (evidence), the **test** (pass/fail), and **ep02**.

### PK1. Package first

- **Rule.** Before script lock, write a one-sentence promise of 15 words or fewer: the place, plus one picturable twist. Then run a 10-minute sprint: 20 or more titles and 5 or more thumbnail concepts, from which 3 arms are kept. If no concept passes PK2-PK4, change the angle or the reveal, not the wording.
- **Why.** The MrBeast process starts with title and thumbnail. Hoyos scraps ideas she cannot package. Galloway: 30 concepts in 10 minutes. Film Booth: the same footage became a hit through how it was presented.
- **Test.**
  - The promise sentence exists in the brief.
  - Shown only the title and the 390x220 card for 2 s, 2 of 3 cold readers correctly say what the film will show.
  - Before upload, predict the video's score out of 10 (Galloway), and log it next to the result.
- **Ep02.** "The Hawaiʻi on the postcard is only the top of a mountain; we measure all of it, from its true base." Passes.

### PK2. One glance, one idea

- **Rule.**
  - At most 3 elements: one hero shape, at most one anchor (PK7) and at most one text item (PK8).
  - 0 graphic devices (no arrow, ring, box, depth label, split or number).
  - The composition is either (a) the hero shape at 50% or more of the frame, or (b) a small recognisable object in a vast field (scale contrast). Never several mid-sized things competing.
  - A low oblique camera, never a top-down map.
- **Why.** Appleby: "Make your thumbnail easy to understand". Film Booth: "no room for confusion". YouTube: too much detail overwhelms. 54% of winners use no device. Ep01 had about 5 competing elements and got a 1.97% Suggested CTR. Black Sea case: the side-on force beat the top-down map.
- **Test.**
  1. Count the elements: 3 or fewer.
  2. Blur check: at 168x94 with a 1.5 px Gaussian blur, the hero silhouette is still recognisable.
  3. Feed strip (`research/niche/work/feedstrip.py`, see PK6): shown for 2 s each, 3 of 3 viewers find our card and name the place.
- **Ep02.** The Big Island massif from low off its flank fills 50% or more of the frame. The postcard is the only anchor, and its place name is the only text.

### PK3. The curiosity gap is one specific withheld answer

- **Rule.**
  - The package withholds exactly one answer that the viewer wants once they see the card: a size, a fate, a reason or what something looks like.
  - The film shows that answer on screen.
  - The gap must be specific (an inverted U: too vague and nobody cares, fully answered and nobody clicks).
  - No abstract "not what you think" framings, no question the viewer did not have before the card, and no answer in the package.
  - Gap types, by same-channel evidence:
    - completeness, "Every X" (1.81), only when the film really covers every item;
    - access (1.56);
    - statement + twist (1.32);
    - proof or explorer, "We Measured" (1.16-1.25);
    - transformation, carried by the *image* (the strongest pooled signal, but its words are clone grammar).
- **Why.** Galloway calls the gap "the most important thing". Loewenstein's information-gap account: curiosity needs a specific unanswered question. California case: the vague framing lost to a specific implied object. Ep01's "POINTING AT WHAT?" asked a question nobody had yet.
- **Test.**
  - Write the viewer's question in 8 words or fewer.
  - The answer is one unhedged true sentence in the fact ledger, with the timestamp where the film shows it.
  - **"I'll save you 15 minutes" test:** knowing the answer must not make the film skippable, because the value is in *seeing* it.
- **Ep02.** Question: "How big is the rest of Hawaiʻi?" Answer: Mauna Loa is about 56,000 ft from its true base, at about 11:20. Part of it is paid by 0:30: the flank drains and Maui Nui appears at -400 ft. The number 56,000 never appears in the package.

### PK4. Title and thumbnail split the work; they never repeat

- **Rule.**
  - **The title** carries the claim or frame and the matching proper noun. It is what Search, Suggested matching and the reader use.
  - **The thumbnail** carries the evidence: the picture of the partial or strange state, plus one anchor.
  - The thumbnail text shares **no content word** with the title. The only exception is the place name on the postcard, which is the brand device; Arm C tests without it.
  - Each half must raise interest on its own. Together they must say *what you will see*, never *what the answer is*.
- **Why.**
  - Alter: "your text should never just repeat your title."
  - YouTube's tips page: titles and thumbnails "working together to create interest and tell a story".
  - Tsunami case: the title carries the cause and the thumbnail carries the time.
  - The Gold case shows a repeat is not always fatal, so this rule protects space more than it prevents disaster.
- **Test.**
  1. Content-word overlap between thumbnail text and title = 0, place name on the card excepted.
  2. **Cover test:** with the title covered, does the thumbnail alone raise a question? With the thumbnail covered, does the title? Both must.
  3. **Together test:** a cold reader predicts what the film shows (a drained mountain, measured) but not the number.
- **Ep02.** Title: "Hawaii Is Only the Summit. We Measured the Rest." Thumbnail: the postcard sits at the old shoreline, and the dark flank plunges below it. The title says *only the summit*; the picture shows *the rest*. They complement each other.

### PK5. Familiar to the host, foreign to the lane

- **Rule.**
  - **Title:** use the host cluster's words, with the proper noun in the first 3 words, so Suggested matching and the viewer place us next to the Hawaiʻi videos. It must be 41-50 characters and clear of the niche report's regex, which bans: hidden, hiding, nobody, never, found, discovered, revealed, bottom, beneath, drain*, what if, here's what, sleep, documentary and the rest of the list.
  - **Thumbnail:** break the drain lane's grammar, using none of the clone kit:
    - caption box with an accent word;
    - curved arrow;
    - negative-depth label;
    - sea-level bar or dashed line;
    - a tan basin dominating the frame;
    - an Everest cross-section;
    - a red or orange highlighted region.
- **Why.**
  - Galloway: "familiar but also unexpected".
  - YouTube: Suggested is topically related.
  - The drain lane has 96 uploads from 50 channels in 35 days, median 448 views.
  - Ep01 shows that distinctiveness is necessary but not sufficient.
- **Test.**
  - **Title:** regex no match; proper noun in the first 3 words; 41-50 characters; a probe of the exact title 24 h before upload finds no on-topic video with the same first 4 words.
  - **Thumbnail:** `python3 -I research/niche/work/gate.py final_*.jpg` prints PASS (tan ≤10%, red ≤3%, blue ≤45%, distances ≥11.0). Its distances must also beat the craft median: **11.71 or more to A_drain_clones and 11.43 or more to D_template_farms** (`work/craft_median.py`). A manual check finds 0 clone-kit items.
- **Ep02.** The launch title passes (48 characters, 0 probe matches). The tan-ramp mocks M1-M3 all fail the gate (9.4-9.8 to the clones), so the final renders must colour the seafloor by real substrate (dark basalt), not by the tan ramp.

### PK6. Contrast is relative, not absolute

- **Rule.**
  - There is no absolute brightness or saturation target. Retire "40% bright or saturated, never navy".
  - Our card must be the most distinct card in hue and value next to its neighbours, in two strips:
    - **(a) lane strip:** `feedstrip.py`'s 9 drain-lane and Hawaiʻi-lane cards;
    - **(b) host strip:** the 5 biggest host videos, rebuilt 24 h before upload. These include RealLifeLore Hawaii 7.07M, Signore Galilei 3.04M, Be Smart 3.64M, Wendover and Atlas Pro.
  - Inside the frame, the hero is the high-contrast region, with one luminous accent (the off-white card or a cyan waterline).
  - Aim for an overall mean luma of about 95-120 (`thumbnail_anatomy.md`); a dark field is allowed only if the subject inside it is luminous.
- **Why.**
  - Winners are darker than the rest (90 vs 105).
  - Only 13% of winners meet the old 40% rule.
  - 6 of 7 vidIQ "after" images were less colourful.
  - Dark borders are not penalised (35% of winners vs 16% of the rest).
  - Alter: the card that "contrasts with every thumbnail around it" pops.
  - The Hawaiʻi hosts are teal or navy sea with green islands, so another blue-green card disappears among them.
- **Test.**
  1. Run `python3 -I research/niche/work/feedstrip.py final_X.jpg feeds/strip_X.jpg` for the lane strip, and the same layout with host thumbnails for the host strip.
  2. In both strips, 3 of 3 viewers find ours in 2 s or less and can read the place name at 168x94.
  3. Render an object-ID mask with the frame. The hero's mean luma differs from the background's by 40 levels or more (0-255). This is a starting threshold, not yet calibrated.
  4. `python3 -I work/darkmode_edge.py final_X.jpg` is a diagnostic only. Ep01 measured 0.45 edge-dark at mean luma 60, below the 95-120 band.
- **Ep02.** Warm low sun on dark basalt, with a pale sky band at the top. The off-white card is the luminous accent. This is warm against the hosts' cool blues, and dark against the clones' tan.

### PK7. Replace the face with one anchor

- **Rule.** Exactly one emotional or scale anchor besides the hero shape. Use no faces at all: not generated, not stock, not cartoon reactions. The menu is in section 3.
- **Why.**
  - Faces are 5% of winners vs 12% of the rest.
  - Appleby: even MrBeast's face "flip-flops based off the audiences".
  - The vidIQ cases won with a lantern figure, a boat and an abandoned jacket.
  - Alter: recognisable objects stop the scroll the way faces do.
  - The clone channels use generated presenter faces, so a face would make us *look like* them.
- **Test.**
  - Exactly 1 anchor.
  - 3 of 3 viewers name it at 390x220.
  - At 168x94 the hero still reads even if the anchor does not.
- **Ep02.** The anchor is the tilted postcard. If a scale object is tested, such as a tiny ship at the waterline in Arm B, it *replaces* the postcard in that arm and is never added beside it.

### PK8. Text must earn its place

- **Rule.**
  - 0-3 words, ideally 1: the place name on the postcard.
  - Cap height 12-18% of the frame height, at most 2 lines.
  - Set it on the card or straight on the image with a soft shadow. Never in a box, banner or bar.
  - No digits, no depth or height labels, no claims the picture cannot back up.
  - Spell the place correctly: **HAWAIʻI**, with the ʻokina (U+02BB), on the card.
  - Use a plain postcard typeface. Avoid "Greetings from" script and retro block letters, which belong to the Extremities Kalaupapa card already in the host cluster.
- **Why.**
  - The market's median text height is 10-11%; only 6 of 233 thumbnails reach 20%.
  - Small channels' bigger boxed text bought nothing.
  - Caption boxes are on 6% of winners vs 23% of the rest.
  - Alter: text only if it is "additive to the story".
  - Correct spelling earns trust: the correctly spelled "Kīlauea" title earned 103x its channel's median. Pronunciation attacks took 47% of the comment likes on a 124K Hawaiʻi video.
- **Test.**
  - Word count 3 or fewer.
  - Cap height measured at 12-18%.
  - The regex `\d` finds nothing in the thumbnail text.
  - 3 of 3 readers read it at 168x94.
  - The ʻokina character is checked in the source file.
- **Ep02.** Arms A and B carry "HAWAIʻI" on the card; Arm C has no lettering.

### PK9. Promise no more than the film proves

- **Rule.**
  - **Map the promise.** Every word of the title and every element of the thumbnail must appear in the film: part of it by 0:30, all of it by the end.
  - **Keep qualifiers.** "Most of", "about", "almost" and "from its true base" never drop out.
  - **Literal title verbs.** A verb like "We Measured" requires an on-screen measurement: a scale bar from the true base at vertical exaggeration 1.0.
  - **Maximum true version.** Exaggerate to the strongest version the fact ledger supports, then stop (Galloway's "most exaggerated version", bounded by the owner's no-overclaim rule).
  - **No spent hooks.** No "taller than Everest" in the title, the thumbnail, the first 30 s or the Shorts hooks.
- **Why.**
  - YouTube: inaccurate titles make viewers stop watching, which hurts discoverability, and egregious clickbait is removed.
  - Test & Compare scores watch time, so an overclaim loses its own test.
  - MrBeast: the first minute confirms the thumbnail.
  - Trust data: videos where 5% or more of comments flag a concrete mistake average 14.5% voice complaints, against 2.3% for the rest.
  - The Everest cluster sits at 0.77x the channel median.
- **Test.**
  - A promise-map table: each package element → its proof timestamp.
  - A qualifier diff of the package text against the fact ledger.
  - A regex for `everest|taller` over the title, the thumbnail text and the first 30 s of narration finds no match.

### PK10. Frame 1 is the thumbnail

- **Rule.**
  - The opening frame is the thumbnail image in motion.
  - The first line names the place within its first 3 words.
  - The title's own words are spoken by 0:10.
  - The postcard drop happens by 0:06.
- **Why.** P7 (kept); the niche report's postcard drop; MrBeast's first-minute rule; Galloway: the viewer should feel they "made the right decision".
- **Test.** SSIM of 0.8 or more between frame 1 and the default thumbnail at 320x180; a transcript check at 0:10.

### PK11. Test the way YouTube scores

- **Rule.**
  - Upload 3 arms that differ in *idea*: composition, anchor or state. YouTube itself says that similar arms make tests drag.
  - Test the thumbnails first, under one title. Change the title only under the stall rule, and never on the same day as the thumbnail.
  - Judge on watch time per impression (CTR x AVD) and on Suggested CTR, within the Suggested source, against our own videos at the same age.
  - Read nothing before about 10K impressions. At our traffic, expect "Inconclusive", so the pre-upload strip test (PK6) picks the default arm.
  - When dynamic thumbnails arrive, keep the 3 arms aimed at 3 viewers: the host-video viewer who knows Hawaiʻi, the spectacle viewer, and the returning viewer.
  - Upload 1280x720 or larger, under 2 MB.
- **Why.** The help pages on the outcome labels, similar arms and the 480p downscale; Beaupré on segments; Appleby on audience flip-flops.
- **Test.**
  - The arms log lists, for each arm, what differs.
  - Every package change is logged with its time.
  - No change is made while a test runs.
- **Ep02.**
  - **A:** postcard on the drained massif.
  - **B:** half-drained, with real water clinging to the flank and the card floating on the waterline. This is the partial state no competitor shows.
  - **C:** the card photo only, with no lettering. It tests the PK4 exception.

### PK12. A signature, not a template

- **Rule.**
  - The series is recognised by its visual device: the postcard as an object on the real 3D Earth, one accent colour and the low oblique camera. A title template never plays that role.
  - The title grammar changes every episode: claim, plain fact, myth check, question.
  - If a copy appears, change the card's composition but keep the device.
  - No channel logo or wordmark on the thumbnail. The postage stamp on the card is a small picture (for example a volcano silhouette), not the words "Myth Juice", so at feed size it reads as a stamp, not a logo.
- **Why.**
  - Galloway: double down rather than change, evolve when copied; not a fan of logos.
  - Logos and series frames: 3% of winners vs 20% of the rest.
  - The niche report: Fossil and Paintify outlived their copies, while "It's a Wound." title templates decayed within a month.
- **Test.**
  - 24 h before upload, probe the place's cluster for postcard-object thumbnails, and compare against Extremities' Kalaupapa card (`thumbnail_anatomy.md`, finding 6).
  - The title grammar differs from the previous episode's.
  - No wordmark is readable at 390x220.

---

## 3. What replaces the face: the faceless anchor menu

A presenter's face does three jobs: it stops the scroll (a recognisable shape), it carries emotion, and it gives scale. A map channel needs one object per thumbnail that does at least two of them.

| Anchor | Jobs | When to use it | Evidence | Test |
|---|---|---|---|---|
| **Familiar artefact: the postcard** | Recognition and meaning ("the version you know") | Default for the series: the place has a famous view | Alter: recognisable interfaces stop the scroll. The Google Maps-card frame scored 107x (`thumbnail_anatomy.md`). Bolivia and Netherlands: the generic view loses as the *main* image, so the card must stay small (30-45% of the width) and the real shape must dominate. | 3 of 3 viewers say "postcard" at 390x220. The card is no more than 45% of the frame width. |
| **True-scale human-sized object** (ship, car on a road, a lit town, the paper cut-out tourist) | Scale and awe | When the size *is* the story and the object stays recognisable at phone size | Black Sea boat; Lituya Bay's tiny lights; Mr. Science's diver; Curiosity Dude's lone rock in the ocean. Winners have a small focal subject (under 25% of the frame) 17% of the time, the rest 3% (p = 0.001) | The object is at least 10% of the frame height at 390x220, or it reads as a known silhouette (ship, car). Its scale is real (VE 1.0). |
| **Human trace** (abandoned object, footprints, terraces, a road ending at the water) | Story and emotion without a person | Human stories: Nihoa's terraces, the 1975 coast | Snake island's abandoned jacket; Antarctica's lone figure seen from behind | It is clearly made by people at 390x220. It is never at a grave or wreck site (respect rule). |
| **A creature from the film** (monk seal, albatross) | Emotion and recognition | Only if the creature is on screen in the film, and as the hero, not decoration | Fossil and Mr. Science use creatures as their "face". It is a weaker fit for geology films | It appears in the film within the first 3 minutes, or the promise map fails. |
| **Light and weather** (low sun, storm, the glow of a waterline) | Emotion | Always available; combine with one of the above | Antarctica's storm and lantern; the darker winners in our set | No extra element is needed. Check against the PK6 contrast test. |

**Never:** faces of any kind, generated presenters, reaction cut-outs, skulls, warning signs or any danger icon the film does not show.

---

## 4. Ep02 worked example: the division of labour

| Layer | Job | Content |
|---|---|---|
| Title | The claim plus the host-matching noun; withholds the size | "Hawaii Is Only the Summit. We Measured the Rest." (48 characters; passes PK5) |
| Thumbnail, Arm A | The evidence: what "the rest" looks like; one anchor | The drained Big Island massif from low off its flank, dark basalt in warm low sun at 55% or more of the frame. A tilted off-white HAWAIʻI card sits at the old shoreline. No numbers, no arrows, no boxes |
| Thumbnail, Arm B | The partial state | The same camera, half-drained: real turquoise water and a foam rim clinging to the flank, and the card floating on the waterline |
| Thumbnail, Arm C | The PK4 exception test | Arm A's composition, but the card shows only the photo, with no lettering |
| 0:00-0:10 | Confirm the promise | Frame 1 = the default arm. "This is Hawaii. The postcard version." The card tips into the sea; "Hawaii is only the summit" is spoken by about 0:08 |
| By 0:30 | Pay part of the promise | The flank fills the frame by 0:06; Maui Nui appears at -400 ft at about 0:14 |
| About 11:20 | Pay all of it | A scale bar from the dented true base: about 56,000 ft, measured on the survey data, said with "from its true base" |

**Status of the proposed titles under these rules:**

| Title | Verdict |
|---|---|
| "Hawaii Is Only the Summit. We Measured the Rest." | **Launch.** Conditional on the on-screen measurement (PK9). |
| "Hawaii Is Only the Summit. You Can't See the Rest." | Swap B for the 72-hour stall rule: an access gap; only the second sentence changes. From `title_anatomy.md`. |
| "Hawaii Is Only the Tip. We Measured the Rest." | Reject. "Tip" pulls in tipping-culture videos (PK5). |
| "How Tall Is Hawaii, Really?" | Reject. "How X" scores 0.71 on the same channel; 27 characters; "really" pulls travel videos; it lands in the spent Everest-Shorts cluster. |
| "Hawaii, Measured From Its True Base" | Use as the description's first line or a chapter title. A label with no withheld object (PK3), at 35 characters. |
| "Hawaii Is Only the Summit" | Reserve. A claim with no proof twist, at 25 characters. |

---

## 5. What changes in the old rules (topic_hunt.json P1-P9)

| Old rule | Status | Change |
|---|---|---|
| P1: dark-mode mock at 390x220 and 168x94 beside the 5 hosts; "the most readable and brightest card" | **Kept, test changed** | Two strips (lane and hosts). Pass on "found in 2 s or less and name readable, 3 of 3", not "brightest" (PK6). |
| P2: title 35-50 characters, noun in the first 3 words, no hedges | **Tightened** | 41-50 characters (31-40 characters scores 0.83 on the same channel), plus the regex ban (PK5). |
| P3: use the host and search words; name the place in the first spoken sentence and the first description line | **Kept** | Drain words live in the first spoken line, the description and the tags only. |
| P4: a specific withheld thing, not an abstract question | **Kept, sharpened** | PK3: the 8-word question test plus a timestamped answer. |
| P5: one subject at 50% or more; 0-3 words at 20% or more of height; **white on a black box with an accent word**; one device; **40% bright, never navy** | **Split** | One subject: kept (PK2, with the scale-contrast alternative added). Words: 12-18% cap height (PK8). **Black box: retired** (clone kit). One device: **now 0** devices. 40% bright and never navy: **retired**, replaced by relative contrast (PK6). |
| P6: the image shows the before or partial state; the text never repeats the title | **Kept** | The partial state is Arm B. One documented exception: the place name on the postcard, tested by Arm C (PK4). |
| P7: frame 1 = the thumbnail; part of the promise paid by 30 s | **Kept** | PK10. |
| P8: Suggested CTR 5% or more; watch time per impression 15 s or more | **Kept** | Measured within the Suggested source only (1.3). |
| P9: 3 thumbnails in Test & Compare; read at about 10K impressions; the strip test picks the default | **Kept, extended** | Arms must differ in idea; Test & Compare scores watch time share; plan for dynamic thumbnails (PK11). |

---

## 6. Pre-upload checklist (pass/fail)

Title
- [ ] 41-50 characters; the proper noun in the first 3 words; regex clean; no hedge words.
- [ ] An exact-title probe 24 h before upload finds no on-topic video with the same first 4 words.
- [ ] Every word is literally true, with qualifiers kept; no Everest.

Thumbnail (for each arm: `cand_*.jpg` → `final_*.jpg`)
- [ ] At most 3 elements; 0 devices; low oblique camera; hero at 50% or more of the frame, or scale contrast.
- [ ] Exactly 1 anchor from the section 3 menu; no faces; no logo or wordmark.
- [ ] Text: 3 words or fewer, cap height 12-18%, no digits, HAWAIʻI with the ʻokina, no box.
- [ ] 0 content words shared with the title (place name on the card excepted).
- [ ] `gate.py` PASS, and distances of 11.71 or more (to drain clones) and 11.43 or more (to farms).
- [ ] Both feed strips: found in 2 s or less and name readable at 168x94, 3 of 3 viewers.
- [ ] Hero vs background luma difference of 40 or more on the mask render.
- [ ] 1280x720 or larger, under 2 MB, JPG.

Film
- [ ] Frame 1 SSIM of 0.8 or more against the default arm at 320x180.
- [ ] The title's words are spoken by 0:10; part of the promise is paid by 0:30.
- [ ] The promise-map table is complete, with a proof timestamp for every package element.

After upload
- [ ] The predicted score out of 10 is logged.
- [ ] No package change before about 10K impressions, except under the 72-hour stall rule. Only one variable changes at a time, and each change is logged with its time.

---

## 7. Sources

Official YouTube:
- [A/B test titles & thumbnails (Help 16391400)](https://support.google.com/youtube/answer/16391400?hl=en)
- [Test & compare thumbnails (Help 13861714)](https://support.google.com/youtube/answer/13861714)
- [Impressions and click-through rate FAQ (Help 7628154)](https://support.google.com/youtube/answer/7628154?hl=en)
- [Decoding CTR & impressions in your Analytics (Help 16767369)](https://support.google.com/youtube/answer/16767369?hl=en)
- [Thumbnail & title tips (Help 12340300)](https://support.google.com/youtube/answer/12340300?hl=en)
- [Understand your YouTube video reach (Help 9314355)](https://support.google.com/youtube/answer/9314355?hl=en)
- [Strengthening enforcement against egregious clickbait (YouTube India blog, 18 Dec 2024)](https://blog.google/intl/en-in/products/platforms/strengthening-enforcement-against-egregious-clickbait-on-youtube/)

Coverage of YouTube announcements:
- [TechCrunch, Made on YouTube 2026: video A/B tests and dynamic thumbnails (23 Sep 2026)](https://techcrunch.com/2026/09/23/youtube-adds-new-creator-tools-like-video-a-b-testing-dynamic-thumbnails-and-live-dubbing/)
- [NetInfluencer, Todd Beaupré and Chucky Appleby on dynamic thumbnails (Creator Insider, 27 Oct 2026)](https://www.netinfluencer.com/youtubes-dynamic-thumbnails-will-shift-traffic-toward-winning-images-by-viewer-segment-discovery-lead-says/)
- [Social Media Today, Chucky Appleby on MrBeast thumbnails (Creator Insider)](https://www.socialmediatoday.com/news/youtube-shares-insights-mrbeasts-team-creates-compelling-thumbnail/709817/)

Practitioners:
- [Simon Willison on "How to Succeed in MrBeast Production" (authenticity unconfirmed)](https://simonwillison.net/2024/Sep/15/how-to-succeed-in-mrbeast-production/)
- [Creator Handbook summary of the same document](https://www.creatorhandbook.net/leaked-document-allegedly-reveals-mrbeasts-secrets-to-youtube-success-the-key-takeaways/)
- [Paddy Galloway, The New Rules of YouTube (2025), edited transcript](https://thetranscriptdesk.substack.com/p/the-new-rules-of-youtube-2025-edited)
- [Colin and Samir, The new rules of YouTube from Paddy Galloway](https://www.colinandsamir.com/resources/the-new-rules-of-youtube-from-paddy-galloway)
- [Film Booth, "Sneaky Tricks YouTubers Use To Hook You", transcript (speakers unlabelled)](https://gotranscript.com/public/discover-the-sneaky-tricks-top-youtubers-use-to-create-viral-hits-and-hook-viewers)
- [Creator Science, Paddy Galloway episode](https://podcast.creatorscience.com/paddy-galloway/); Jenny Hoyos, Creator Science #167 (episode page summary, via search)
- [Aprilynne Alter, "This Is Why Your Thumbnails Feel OFF", transcript](https://sozai.app/transcript/why-your-thumbnails-feel-off/)
- [Aprilynne Alter, "how to make a killer youtube thumbnail", transcript](https://sozai.app/transcript/make-killer-youtube-thumbnail/index.md)

Research context (low weight):
- Koh and Cui (2022), "An exploration of the relation between the visual attributes of thumbnails and the view-through of videos", *Decision Support Systems*, doi:10.1016/j.dss.2022.113820. 3,745 brand videos; element complexity and aesthetics both relate to view-through. Directions of the effects were not verified here.
- Loewenstein's information-gap account of curiosity (1994), via secondary summaries ([arXiv 1806.04212](https://arxiv.org/pdf/1806.04212)).
- Third-party CTR-by-source "benchmarks" (focus-digital.co, thumbmagic.co, outlierkit.com) contradict each other. They are cited only to show that no reliable benchmark exists.

Not reachable in this step: YouTube watch pages and transcripts (rate-limited or bot-checked; not bypassed). The Creator Insider videos "A deep thumbnail discussion with Chucky (MrBeast) and Todd" (HP-rqigfw2s), "Paddy Galloway Dives Deep on Video A/B & Ask Studio" (j7GtybYc6gk) and "Chucky (MrBeast) on Dynamic Thumbnails, Video A/B, and the YouTube Algorithm" (Au_x7IRClH4) are worth a human watch.

---

## 8. Files

| What | Path |
|---|---|
| This rulebook | `principles.md` |
| vidIQ case data (10 cases, lifts, titles, dates) | `work/vidiq_wins.json` |
| Before/after crops, current thumbnails, side-by-side sheet | `refs/wins/` (other channels' images; never committed) |
| Craft-median distance bar for the gate | `work/craft_median.py` (run: `python3 -I work/craft_median.py`) |
| Dark-mode edge diagnostic and its calibration | `work/darkmode_edge.py` (`--calibrate` for the refs split) |
| Advice-video probe (IDs of the Creator Insider, Paddy Galloway, Film Booth and Alter videos) | `work/raw/advice_probe.json` |
| Gate and feed strip (reused) | `research/niche/work/gate.py`, `sim_lib.py`, `feedstrip.py` |
| Companion reports | `title_anatomy.md`, `thumbnail_anatomy.md`, `research/niche/niche_report.md` |
