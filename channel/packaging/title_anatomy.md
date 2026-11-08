# Title anatomy: what wins in our space, and what it means for ep02

Date: 2026-11-08. Packaging lab, title step. This extends the niche study's title-language stats (1,254 clone titles vs 521 craft titles, `research/niche/work/titles_sets.json`) with a new, larger table that has views, age and channel size for every row.

Raw table: `research/packaging/titles.json` (6,528 titles). Stats: `research/packaging/work/title_stats.json`. Code: `research/packaging/work/title_anatomy.py`.

---

## The short answer

1. **Keep the launch title "Hawaii Is Only the Summit. We Measured the Rest." (48 characters).** It is the best-supported candidate on every test we ran, and today's probe of the exact title finds 0 matches. It also passes every word rule.
2. **Title shape matters less than the promise.** Compare a channel's own videos with each other. Most surface features (questions, numbers, ALL-CAPS, place name in the first 3 words) change nothing. What does move views is the curiosity promise:
   - **Access** ("you can't visit or reach it"): **1.56x** the same channel's other videos.
   - **Completeness** ("every X"): **1.81x**.
   - **Transformation** (what if, without, drained): the strongest signal in the pooled samples, **1.7-2.0x** the base rate of top-10% titles.
3. **Short titles do not win.** On the same channel:
   - 31-40 characters: **0.83x**;
   - 30 characters or fewer: **0.90x**;
   - 41-50 characters: **1.03x**, as good as any other length.

   The craft channels' 44-47-character median is a house style, not a lever. Aim for **41-50 characters**: that fits the compact card without the short-title penalty. This rules out the niche report's 25- and 35-character swaps as primary titles.
4. **Fear words lose.** Terrifying, insane, strange, wild, mysterious and secrets score **0.79x**. **Absolute and scale words win**: every (1.82x), deepest (1.49x), isolated (1.41x), lost (1.33x).
5. **Brackets help when they add a twist** (**1.30x** overall, **1.56x** for twist brackets). Ep01 spent its bracket on a hedge.
6. **"Why X" and "How X" openers, number lists and yes/no questions underperform their own channels** (0.71-0.79x). **"X Is Hiding Something" is the worst formula we measured: 0.60x**, so the same channels' other titles did 1.7x better.
7. **The clone vocabulary still pulls some clicks.** In non-clone channels, titles that use those words did **1.18x**. "Bottom" is the strongest single word at 3.4x, on 16 channels. Banning the words is therefore a positioning and trust choice with a small CTR cost, not a free win. We pay that cost back with allowed words that measured well (every, deepest, isolated, lost, only) and with the image.
8. **Swap plan.** If Suggested stalls, change only the second sentence: **"Hawaii Is Only the Summit. You Can't See the Rest."** (50 characters, 0 probe matches). It trades the proof twist for an access gap, the curiosity type with the strongest same-channel evidence.

---

## 1. Data and method

**Collection (today, 2026-11-08)**
- **103 search queries**, each run with 5 YouTube filters (relevance; 4-20 min; 20+ min; this year 4-20 min; this year 20+ min):
  - 73 queries were run this morning by the packaging lab;
  - 30 are new for this step.
- Coverage, by first matching topic: Hawaii (23 queries), ocean floor and deep sea (17), drained or without water or ice (13), islands (9), maps and true size (9), geography mysteries and strange places (9), Everest and tall mountains (8), lost lands and the Ice Age (7), volcanoes (6), and deep time (2). Many queries span two topics. The list is in `title_stats.json` under `queries`.
- **1,424 channel pages**, each giving subscribers and the last ~30 uploads. Another 157 competitor channel pages came from the competition map (`scratchpad/comp/chans.json`).

**Filter ("our space")**
- English long-form, 4 min to 4 h.
- The title must contain a geography or earth word.
- Excluded: travel and vlog, news, lectures, music and ambience, games, and true crime.

**The table**
- 6,528 titles from 1,227 channels.
- Each row has views, age, length, subscribers (6,473 rows), the channel's median recent long-form views, upload rate, the group, and every title feature.

**Two samples**

| Sample | What it is | Size |
|---|---|---|
| **A, search-visible** | Titles that search surfaces, uploaded in the last 24 months | 1,356 titles, 824 channels |
| **B, all uploads** | Every recent long-form upload (14 days to 12 months old) of 388 channels whose recent titles are at least 50% in our space. No search-ranking survivorship | 3,745 titles |

**Performance**
- **Breakout** = views ÷ the channel's own median recent long-form views. This is "views relative to channel size". Views per month of age is the fallback, used for 86 rows in A whose channel had no usable baseline.
- **Top decile** = the top 10% by breakout. **Median band** = the 40th-60th percentile.

**The arbiter: the same-channel test**
- For each of the 285 channels in B with at least 5 uploads, compare the titles that use feature X with the same channel's other titles.
- Views are adjusted for age inside the channel (slope 0.07 per log-month).
- Reported as a ratio. 1.30 means the same channel got 1.3x its usual views with that feature. The range is an 80% bootstrap interval over channels.

**Why the arbiter matters.** The pooled top decile is mostly small-channel lottery tickets:
- In sample A, the top decile's median channel has 28K subscribers, against 103K in the median band. Its median breakout is 179x, against 3.4x.
- High-variance clone channels also land there more often. Clone-listed channels make the B top decile 1.41x as often as chance; craft-listed ones only 0.73x.

Pooled lifts therefore mix the title with the type of channel. The same-channel test removes channel size, quality and variance.

**Limits**
- Search returns about the top 20 per query and filter.
- Subscriber counts are today's.
- The topic filter misses some in-space titles that have no geography word (for example "Why Can't You Visit Iwo Jima?", 4.4M on 3.5K subs).
- Drain-only and farm-only channels cannot enter the same-channel test, because they post nothing else.
- All of this measures views. Click-through rate is not public. Treat ratios under about 1.2 as directional.

---

## 2. Top decile vs median

| Title feature | A top 10% | A median band | B top 10% | B median band | Same-channel ratio [80% range] |
|---|---|---|---|---|---|
| Median length (characters) | **61** | 53 | **60** | 58 | 31-40 chars: **0.83** [0.73-0.95]; 41-50: 1.03 [0.93-1.14]; 71+: 1.12 [0.98-1.28] |
| Median words | 10 | 9 | 10 | 10 | - |
| Question mark | 17% | 12% | 10% | 11% | 1.01 [0.87-1.19] |
| Place name in the first 3 words | 19% | 22% | 24% | 22% | 1.03 [0.93-1.14] |
| Two sentences (statement + twist) | 2.2% | 1.9% | 2.9% | 1.9% | **1.32** [0.93-1.82] |
| Bracket | 9.4% | 6.0% | 8.5% | 5.6% | **1.30** [1.08-1.56] |
| Colon, dash or pipe (label: subtitle) | 48% | 34% | 37% | 36% | 0.93 [0.82-1.05] |
| A digit | 30% | 29% | 30% | 31% | 1.01 [0.90-1.13] |
| An ALL-CAPS word | 17% | 16% | 22% | 23% | 1.05 [0.91-1.19] |
| "We" or "I" | 8% | 8% | 7.5% | 10% | 1.03 [0.87-1.26] |
| "You" | 11% | 11% | 7.5% | 6.3% | 0.87 [0.72-1.06] |
| Any power word | 57% | 56% | 58% | 49% | **1.13** [1.02-1.25] |
| Fear or shock words (terrifying, insane, strange, wild...) | 9% | 10% | 10% | 14% | **0.79** [0.69-0.91] |
| Mystery or secret words (lost, hidden, forbidden...) | 22% | 22% | 20% | 14% | 1.15 [1.01-1.32] |
| Absolutes (every, all, nobody, never) | 9% | 11% | 15% | 9% | **1.27** [1.11-1.47] |
| Scale and superlative words | 26% | 19% | 23% | 18% | 1.07 [0.96-1.19] |
| Clone vocabulary (niche regex) | 38% | 25% | 34% | 23% | 1.11 [0.98-1.26]; non-clone channels 1.18 [1.03-1.35] |
| Channel size (median subscribers) | 28K | 103K | 12K | 34K | - |
| Median views | 554K | 64K | 115K | 7.2K | - |

**Curiosity structure** (what the viewer is made to want):

| Structure | A pooled lift | B pooled lift | Same-channel ratio [80% range] | Channels |
|---|---|---|---|---|
| **Transformation reveal** (what if, without, drained, looks like) | **1.71** [1.12-2.43] | **2.03** [1.49-2.58] | 1.45 [0.94-2.27] | 27 |
| **Forbidden or impossible access** | 0.60 | 1.02 | **1.61** [1.11-2.49] | 29 |
| Deep-time contrast | 1.21 | 1.71 | 1.18 [0.82-1.76] | 34 |
| Mystery | 1.06 | 1.40 | 1.12 [0.93-1.40] | 77 |
| Superlative | 1.13 | 0.87 | 1.08 [0.96-1.21] | 143 |
| Belief violation (bigger than you think, myth) | 1.04 | 1.17 | 1.00 [0.77-1.29] | 71 |
| Surprising claim (place + verb) | 0.66 | 1.14 | 0.98 [0.84-1.15] | 104 |
| Hidden thing (hidden, beneath, hiding) | 0.67 | 1.15 | **0.87** [0.77-0.99] | 118 |
| Open question (why, how, what) | 0.95 | 0.92 | **0.82** [0.73-0.90] | 161 |
| No curiosity (plain label) | 1.12 | 0.87 | **0.90** [0.82-0.97] | 202 |
| Withheld result ("X. We measured it.") | n=4 | n=4 | not measurable | 4 |

**First 3 words** (same-channel ratio):

| Opener | Ratio [80% range] | Channels |
|---|---|---|
| "We" or "I" ("I Found...", "We Measured...") | **1.36** [0.99-1.84] | 39 |
| "Inside" or "Journey" | 1.28 [0.97-1.70] | 31 |
| Place name | 1.00 [0.90-1.11] | 176 |
| "The", "This" or "A" | 0.88 [0.79-0.98] | 185 |
| Why, how or what | **0.80** [0.71-0.92] | 149 |
| A number | **0.76** [0.65-0.89] | 91 |
| Is, can or did | 0.74 [0.52-1.02] | 25 |

**What the numbers say**

1. **Length.** The top decile's titles are longer than the median band's: 61 vs 53 characters in A, 60 vs 58 in B.
   - On the same channel, length barely matters above 40 characters.
   - Titles of 40 characters or fewer lose: **0.81** [0.70-0.92].
   - That holds in non-clone channels (0.84) and in clone channels (0.67).
   - **Use 41-50 characters.** That is long enough to avoid the short-title penalty and short enough for the 168x94 compact card.
2. **Questions and the first 3 words are style, not levers.**
   - Craft channels ask more questions (17% of titles vs 12% for clones; 26% in small craft channels). Clones put the place in the first 3 words more often (31% vs 13%).
   - Neither moves views on the same channel.
   - Keep the place name in the title so YouTube's content matching can place us next to the host videos (rule P3). Its position is free.
3. **Power words split in two.**
   - Fear and shock adjectives lose (0.79).
   - Absolutes and scale words win:

| Word | Ratio [80% range] | Channels |
|---|---|---|
| every | 1.82 [1.32-2.48] | 47 |
| deepest | 1.49 [1.00-2.21] | 29 |
| isolated | 1.41 [1.07-1.88] | 22 |
| lost | 1.33 [1.01-1.79] | 56 |
| nobody | 1.31 [1.03-1.66] | 47 |
| strange | 0.70 | 25 |
| wild | 0.66 | 21 |
| mysterious | 0.72 [0.59-0.92] | 28 |
| secrets | 0.76 [0.63-0.92] | 28 |
| extreme | 0.74 | 16 |
| insane | 0.78 | 20 |

4. **Brackets help** (1.30, and 1.41 in non-clone channels).
   - The best kind adds a twist or emotion (1.56, 26 channels). Examples: "Why Greenland Looks Massive (It's Not)" (4.3M on 61.8K subs) and "What on Earth is the Isle of Man? (Not UK)" (3.2M on 248K).
   - Hedge brackets are too rare to measure (9 videos). Ep01's "(Not Just a Coincidence)" was a hedge.

---

## 3. Formula library, ranked by evidence

How to read the table:
- **Ranking:** first by the low end of the same-channel interval, then by the pooled lifts.
- **Lift:** P(top decile | formula) ÷ 10%.
- **Clone% / craft%:** the share of the niche study's 1,254 clone titles and 521 craft titles that use the formula. A formula can carry more than one label.

| # | Formula | Same-channel ratio [80% range], channels | B pooled lift | A pooled lift | Clone% / craft% | Verdict for Myth Juice |
|---|---|---|---|---|---|---|
| 1 | **"Every X"** (completeness) | **1.81** [1.20-2.70], 29 | 1.58 | 0.77 | 1.8 / 5.4 | **Use** when the film really covers every item. Not ep02: it shows one island in depth |
| 2 | **"Why Can't You Visit X?"** (forbidden or impossible access) | **1.56** [1.09-2.29], 29 (non-clone 2.12) | 0.98 | 0.57 | 0.9 / 1.0 | **Adapt.** The access gap without "forbidden" lists. Pooled lifts are low because big incumbents own the term |
| 3 | **"Inside X" / "I Did X"** (explorer, first person) | **1.25** [1.00-1.55], 47 | 0.72 | 0.91 | 0.2 / 1.7 | **Use** as a frame ("We Measured"). Proof that is ours |
| 4 | **Discovery or proof** ("Scientists Scanned X", "What We Found") | **1.16** [1.00-1.37], 96 | 0.99 | 1.44 | 14.8 / 4.8 | **Adapt** the proof idea with allowed verbs (measured, mapped, scanned). Found, discovered and revealed are banned |
| 5 | **Statement + twist** (two sentences) | 1.32 [0.96-1.93], 36 | 1.57 | 1.00 | 6.1 / 2.1 | **Use** (ep02 launch). The second sentence must be a short twist, never "Here's What..." |
| 6 | **Transformation** ("What If X", "X Without Y") | 1.11 [0.76-1.54], 22. As a curiosity type: 1.45 [0.94-2.27] | 1.54 (type 2.03) | 1.86 (type 1.71) | 4.6 / 1.7 | **The promise, not the words.** The strongest premise in the data, but every word of it is clone grammar. Carry it in the image and the first spoken line |
| 7 | **Deep time** ("When Earth Had X", "X Used to Be Y", Ice Age) | 1.22 [0.88-1.76], 39 | 1.56 | 1.20 | 1.8 / 5.0 | **Use** (ep03, ep05, ep09-ep11). A craft marker |
| 8 | **"X Is Bigger / Deeper Than You Think"** | 1.66 [0.81-3.72], 12 | 2.50 | 1.32 | 1.4 / 1.5 | **Use elsewhere, never for Hawaii.** Spent: Short "Hawaii Is Much Bigger Than You Think" 14M, plus Shorts at 325K and 110K |
| 9 | Superlative label ("The Deepest Place on Earth") | 1.05 [0.95-1.15], 200 | 1.01 | 1.16 | 16 / 18 | **Neutral.** The adjective decides it: deepest and isolated, yes; strange and weird, no |
| 10 | "What / Where X?" question | 1.07 [0.88-1.32], 82 | 1.15 | 1.18 | 12 / 8 | Neutral |
| 11 | Mystery ("...That Shouldn't Exist", "Impossible") | 1.05 [0.84-1.30], 83 | 1.28 | 1.16 | 3.7 / 3.6 | Neutral. Overclaim risk |
| 12 | Myth correction ("X Isn't Y", "Everything You Know Is Wrong") | 1.05 [0.79-1.42], 42 (non-clone 0.82) | 1.67 | 0.78 | 4.9 / 3.1 | **Caution.** "X Isn't Really a Lake. It's a Wound." is now cloned (first uploads 271-291K, then 4.6-9K a month later) |
| 13 | Plain claim, place first ("Niagara Falls Is Walking Upstream") | 0.94 [0.83-1.05], 136 | 1.25 | 0.58 | 31 / 20 | Neutral. Needs a twist or a longer form |
| 14 | "The X That Y" (story hook) | 0.96 [0.71-1.30], 60 | 0.91 | 1.50 | 2.4 / 4.2 | Neutral |
| 15 | Label: subtitle / label - subtitle | 0.93 [0.83-1.05], 145 | 1.02 | 1.40 | 21 / 5 | Weak. A farm and sleep-doc marker |
| 16 | "Why X" | **0.78** [0.65-0.93], 91 | 1.23 | 0.85 | 16 / 16 | **Avoid as the default.** Works only with an access gap ("Why Can't You...") |
| 17 | Number list ("10 Places...") | **0.79** [0.66-0.93], 83 | 0.76 | 1.23 | 6.5 / 1.0 | **Avoid** (also owner policy: no lists) |
| 18 | Yes/no question ("Is X...?", "Can X...?") | 0.74 [0.52-1.08], 25 | 0.91 | 2.00 (n=10) | 0.8 / 2.9 | Avoid |
| 19 | "How X" | **0.71** [0.55-0.90], 55 | 0.88 | 1.67 | 2.4 / 8.6 | **Avoid as the default** (craft channels use it, but it loses on their own channels) |
| 20 | **"X Is Hiding Something (Nobody Talks About)"** / "Sitting on the Most Valuable Land" | **0.60** [0.46-0.80], 28, win rate 32% | 1.96 | n=8 | **19.5 / 0.2** | **Banned.** Worst on the same channel; a lottery in the pool |
| - | **"We Drained X. Here's What Was Hidden at the Bottom."** | not testable (the channels post nothing else) | 6.7 (n=3) | 2.0 (n=15, 5 channels) | 2.2 / 0 | **Banned** (see section 4) |
| - | **"What X Looks Like Without Y"** | not testable | n=1 | 2.9 (n=7) | 1.0 / 0 | **Banned** (see section 4) |

**Three real examples per formula.** Format: channel (subscribers), views, age, and views as a multiple of that channel's median.

1. **Every X**
   - "Every Forbidden Island You're Not Allowed to Visit": Earthyphus (1.5K), 880K, 5 mo, 38x.
   - "Would Orcas Dominate Every Prehistoric Ocean?": Fossil (54K), 4.0M, 1 mo, 37x.
   - "I Found the Longest Drive on Every Continent": Paper Skylines Mapping (7.6K), 540K, 1 mo, 65x.
2. **Can't visit / can't reach**
   - "The Most Impossible to Reach Islands on Google Earth": Curiosity Dude (38K), 2.57M, 4 mo, 27x.
   - "Why You Can't Travel Between Hawaii's Islands by Boat": RealLifeLore (7.9M), 7.07M, 1 y, 5.9x.
   - "What Satellites Found on North Sentinel Island That No One Is Allowed to Enter": Walter Finds the Last Islands (2.8K), 647K, 1 mo, 154x.
   - Plus, from the outlier pull, "Why Can't You Visit Iwo Jima?": Where They Stood (3.5K), 4.4M.
3. **Inside / explorer**
   - "Journey to the Deepest Place on Earth": See It First (20.6K), 2.85M, 7 mo, 892x.
   - "Inside the Most Dangerous No Man's Land on Earth": Free High-Quality Documentaries (1.53M), 419K, 1 mo, 32x.
   - "I Found the Longest Drive on Every Continent" (above).
4. **Discovery or proof**
   - "Mariana Trench: What We Found in the Deepest Place on Earth?": World Untangled (5.4K), 2.36M, 9 mo, 2,707x.
   - "Scientists Scanned the Amazon. Then This Appeared.": Astrum Earth (503K), 1.1M, 5 mo.
   - "What A Robot Found 1.5 Miles Under The South Atlantic": Uncharted Depths (33.9K), 793K, 3 wk, 70x.
5. **Statement + twist**
   - "It Looks Like a Desert. But It Has Thousands of Lakes": PBS Terra (1.05M), 5.9M, 1 y, 8x.
   - "Nobody Has Ever Stood on This Mountain's Summit. The Reason is Surprising.": Echoes of Enigma (38K), 266K, 4 mo, 17x.
   - "The UN Voted to Fix the World Map. The Headlines Got It Wrong": World Maps Online (61.8K), 274K, 1 mo, 51x.
   - The clone version to avoid: "We Drained the Great Lakes. Here's What Was Hidden at the Bottom.": Contour Atlas (1.4K), 165K, 2 wk.
6. **Transformation**
   - "What Antarctica Looks Like Without Ice": Unseen Works (2.9K), 1.75M, 3 wk, 650x.
   - "What If All the Ice on Earth Melted?": Earth Tipping (1.5K), 961K, 1 mo, 337x.
   - "What if Earth's oceans vanished... revealing a hidden world beneath?": HereWeLearn (20.4K), 6.54M, 1 y.
7. **Deep time**
   - "When Earth Had Supermountains": Mr. Science (266K), 3.81M, 1 mo, 2.9x (4.9x on the same channel).
   - "Beyond the Glacier: Life in the Ice Age 20,000 Years Ago": Through the Ages (3.7K), 3.2M, 1 mo, 160x.
   - "What Earth Looked Like 100 Million Years Ago: The CRETACEOUS": PlanetGeo (7.5K), 228K, 3 wk, 88x.
8. **Bigger than you think**
   - "The Ocean Is Much Deeper Than You Think!": Xverse (76.7K), 3.66M, 2 mo, 11x.
   - "The North Sea Is Far Stranger Than We Thought": Boring Planet (1.6K), 279K, 3 mo, 243x.
   - "Real Size of Africa ... Depends on The Map?": World Maps Online (61.8K), 317K, 9 mo, 59x.
9. **Superlative label**
   - "Marquesas: The Most Isolated Islands on the Planet": Terra Nauta (13.6K), 1.36M, 1 y.
   - "Weirdest Places On Earth Explained": Professor Why (3.8K), 1.57M, 4 mo, 87x.
   - "The 15 Most Dangerous Jungles in the World": Extreme Planet (1.1K), 423K, 7 mo.
10. **What / Where question**
    - "What on Earth is the Isle of Man? (Not UK)": The Geography Bible (248K), 3.2M, 1 y, 63x.
    - "What A Robot Found 1.5 Miles Under The South Atlantic" (above).
    - "What Happens If You Drain Lake Superior to the Bottom": High Ground Atlas (69 subs), 62K, 1 mo.
11. **Mystery**
    - "Why The Irish Sea Is Almost Impossible to Cross": Geography 360 (20.3K), 203K, 10 mo, 68x.
    - "30 Most Extreme Places on Earth That Shouldn't Exist": GeoMap Unveiled (47.6K), 141K, 2 mo, 59x.
    - "How the Netherlands Built a Country Below Sea Level that Shouldn't Exist": NextGen Manufacturing (173K), 2.9M, 3 mo, 17x.
12. **Myth correction**
    - "The Megalodon Myth: What We Got Wrong About the Ocean's Apex Predator": World Untangled (5.4K), 314K, 6 mo.
    - "Lake Tahoe Isn't Really a Lake. It's a Wound.": geography (19.2K), 291K, 1 mo.
    - "Why Greenland Looks Massive (It's Not)": World Maps Online (61.8K), 4.3M, 9 mo.
13. **Plain claim, place first**
    - "The North Sea Is Far Stranger Than We Thought" (above).
    - "Blue Whales Are Covered in Hundreds of Shark-Bite Craters (Timor-Leste)": OceanX (613K), 474K, 1 mo, 110x.
    - "Southeast Michigan Has a Geographic Secret Nobody Talks About": The life of the States (67K), 160K, 1 mo.
14. **The X That Y**
    - "The Island That Rose From the Bottom of the Ocean": Latitude Tales (13.9K), 2.4M, 11 mo, 304x.
    - "The Woman Who Became a Landmark on Everest": Fatally Curious (62.6K), 1.99M, 3 mo, 45x.
    - "The Lost Continent That Connected Philippines & Indonesia - Then Vanished": HiddenHistory-02 (2.2K), 272K, 3 mo.
15. **Label: subtitle**
    - "India's Lost Cities Found 120 Feet Under: Gulf of Kambay's Ice Age Metropolis": Ice Cold History (3.3K), 506K, 1 mo.
    - "Everest Never Gave Back Bodies - Until Glaciers Started Melting": SummitX (2.3K), 340K, 6 mo.
    - "Drop a Steel Ball Into the Mariana Trench - It'll Fall for 4 Hours": Planet Within (2K), 217K, 3 mo.
16. **Why X**
    - "Why Greenland Looks Massive (It's Not)" (above).
    - "Why We Stopped Exploring the Bottom of the Ocean and What Is Down There?": The Ocean Chronicler (7.3K), 948K, 6 mo.
    - "Why Lake Erie is the Deadliest of Them All": HiddenHistoryForSleep (7.8K), 499K, 9 mo.
17. **Number list**
    - "12 Most GUARDED Objects On Earth You Can't Even Touch": Placeologist (27K), 1.0M, 1 mo.
    - "50 Geography Facts You Never Knew About Poland": Navigating Geography (18.9K), 649K, 1 mo.
    - "30 Most Extreme Places on Earth That Shouldn't Exist" (above).
18. **Yes/no question**
    - "Would Orcas Dominate Every Prehistoric Ocean?" (above).
    - "Can Sperm Whales Reach The Mariana Trench?": Uncharted Depths (33.9K), 235K, 2 mo.
    - "Could This Italian Supervolcano Trigger a Global Catastrophe?": Down The Rabbit Hole (81.9K), 404K, 1 y.
19. **How X**
    - "How the Netherlands Built a Country Below Sea Level that Shouldn't Exist" (above).
    - "How The Most Isolated Towns Actually Work": Versed (203K), 1.29M, 9 mo.
    - "How Long You'd Last in Every Prehistoric Ocean": BeyondTheBlue (263K), 3.56M, 1 mo.
20. **Is Hiding Something**
    - "The Missouri River Is Hiding Something Nobody Talks About": Hidden on Earth (12.3K), 272K, 3 mo.
    - "Chesapeake Bay Is Hiding Something Nobody Talks About": The Hidden States (24K), 154K, 2 mo.
    - "Why Florida Is Sitting On The Most Valuable Land In Human History": statesXplained (4.7K), 195K, 2 mo.
21. **We Drained**
    - "We Drained the Great Lakes. Here's What Was Hidden at the Bottom.": Contour Atlas (1.4K), 165K, 2 wk.
    - "We Drained Lake Superior. Its Floor Is 733 Feet Below Sea Level": Drained Atlas (240), 82K, 2 wk.
    - "We Drained the Ocean Until Only 1 Island Was Left": Map Tally (745), 54K, 9 d.
22. **Looks like without**
    - "What Antarctica Looks Like Without Ice" (above).
    - "What Would the Pacific Ocean Look Like Without Water?": Origins of Everyday Things (12.3K), 171K, 7 mo.
    - "What Hawaii Looks Like Without Water (The 30,000 ft Drop)": Bright Side Dark Secrets, 9.0K (105-min sleep doc).

**The Hawaii host cluster's own grammar.** These are the titles our Suggested placement depends on: short possessive labels and access questions, never drain words.
- "Hawaii's Forgotten Islands": Signore Galilei (57.7K), 3.04M.
- "Why You Can't Travel Between Hawaii's Islands by Boat": RealLifeLore, 7.07M.
- "Hawaii's Logistics Problem": Wendover, 2.04M.
- "The Amazing BIOGEOGRAPHY of Hawaii": Atlas Pro, 1.46M.
- "What's Hidden on Hawaii's Forbidden Island?": Park Vibes (33.6K), 1.30M, 7 mo.

In the last ~90 days, the only Hawaii geology titles above 10K are the farm template "Hawaii Is Hiding Something Nobody Talks About":
- Below The Map, 124K (niche report);
- Geo Metrics (13.5K subs), 78K at 2 months.

---

## 4. Banned patterns

| # | Pattern | Why it is banned (evidence) |
|---|---|---|
| 1 | **Drain verb in the title**: "We Drained X", "Draining X", "If We Drained X", plus "Here's What Was Hidden at the Bottom" | 96 drain uploads from 50 channels in 35 days, median 448 views; 14+ channels use the exact template (niche report). Copies of a place someone already drained get 0.01-2% of the original. The drain words go in the first spoken line, the description and the tags only. |
| 2 | **"What X Looks Like Without Water/Ice"** and "without water/ice" anywhere | The Antarctica original got 1.75M, then copies got 33K, 13K, 1.7K, and down to 5 views. Bright Side Dark Secrets owns "What Hawaii Looks Like Without Water". |
| 3 | **"X Is Hiding Something (Nobody Talks About)"** and "Is Sitting On the Most Valuable Land" | **0.60x** the same channel's other titles (28 channels; only 32% of channels did better with it). 19.5% of clone titles use it, against 0.2% of craft titles. |
| 4 | **Clone vocabulary**: hidden, hiding, hides, bottom, beneath, nobody, no one, never, secret, found, discovered, reveal*, what if, here's what, talks about, sitting on, isn't really, survives, sleep, documentary (the niche report's 4.1 regex plus "never") | These words are clone markers: hidden or hiding in 19% of clone titles vs 1% of craft. Honest cost: in non-clone channels they still did 1.18x ("bottom" 3.4x, "found" 1.29x, "nobody" 1.31x). Some of them do not even help: "beneath" 0.85x, "secrets" 0.76x, "sitting on" 0.69x. We accept a small cost for distinctiveness and trust. |
| 5 | **Fear and shock adjectives**: terrifying, shocking, insane, creepy, strange, weird, wild, extreme, mysterious, nightmare | 0.79x on the same channel [0.69-0.91]. They also overclaim. |
| 6 | **Hedges**: "Not Just", "Maybe", "Sort Of", "Kind Of", "Probably" | Ep01 lesson (rule P2). Hedges are too rare in the data to measure; the rule stands on the CTR result. |
| 7 | **Spent hooks**: "Taller Than Everest", "Bigger Than You Think" for Hawaii, "Hidden Islands" | Shorts: 14M "Hawaii Is Much Bigger Than You Think", 325K and 110K copies; Everest-vs-Mauna-Kea Shorts at 255K, 174K and 109K; "taller than Everest" at 17M. Four of the Hawaii lane's 12 uploads use the Everest angle, and none passed 2.3K. Keep Everest out of the title, the thumbnail and the first 30 seconds. |
| 8 | **Ambiguous words that pull the wrong neighbours** | "Tip" (Hawaii Is Only the Tip) matches tipping culture. "Underwater" next to Hawaii matches flood news ("Hawaii Is UNDERWATER And People Are Losing EVERYTHING") and relaxation videos. "Really" matches "what it's really like living in Hawaii" travel videos. |
| 9 | **Number-first lists, "Why X", "How X" and yes/no openers as the default** | 0.71-0.79x on the same channel. They are allowed only when the curiosity type carries them (for example "Why Can't You..."). |
| 10 | **Primary titles of 40 characters or fewer** | 0.81x on the same channel [0.70-0.92]. Short phrasings go to the description's first line and chapter titles. |
| 11 | **Owner rules** | No emojis; never mention AI ("No AI Used" already appears in this niche); no false or overclaiming text and never drop a qualifier ("Most Of" stays); English only; no sources in the title; Hawaiian names spelled correctly. ʻOkina and kahakō are fine in the description; in the title "Hawaii" is the matching term. |
| 12 | **Farm separators and labels**: "Full Documentary", "\| 4K \|", "for Sleep", pipe chains | A sleep-doc and farm marker (label: subtitle is 21% of clone titles vs 5% of craft); 0.93x. |

---

## 5. Ep02 title check

The prescribed probe (`ytsearch.py --json`) was run today on 16 candidates. The output is in `work/raw/probe_candidates.json` and `probe_candidates2.json`.

| Candidate | Chars | Formula | Evidence | Probe today | Rules | Verdict |
|---|---|---|---|---|---|---|
| **Hawaii Is Only the Summit. We Measured the Rest.** | 48 | Statement + twist; a withheld result; implies the transformation | Statement + twist 1.32 same-channel, 1.57 pooled; length bin 41-50 is 1.03 (no penalty); first-person proof (indirect: a "We/I" opener scores 1.36, ours is in the second sentence) | **0 matches**. Nearest: a 25K Short, "Hawaii Is Way Bigger Than You Think" | Passes. No clone words, no Everest, no hedge | **LAUNCH** |
| Hawaii Is Only the Summit. You Can't See the Rest. | 50 | Statement + twist with an access gap | Access curiosity 1.61 same-channel (its closest evidence is "can't visit or reach", so this is an adaptation) | **0 matches** | Passes. True: the rest of the mountain is below sea level | **Swap B** (first 72-hour stall). Only the twist changes |
| Hawaii Is a Mountain. You've Only Seen the Top. | 47 | Statement + twist, second person | Same structure as the launch; speaks straight to the postcard | 0 exact; nearest a travel doc at 393K | "A Mountain" simplifies (Hawaiʻi Island is 5 volcanoes) | Reserve. Use only if the narration says "Hawaiʻi Island" |
| Hawaii Is Only the Summit (We Measured the Rest) | 48 | Plain claim plus a twist bracket | Brackets 1.30, twist brackets 1.56 | 0 matches | Passes | Reserve. Too close to the launch to teach us anything as an A/B arm |
| How Tall Is Hawaii? (Measured From Its True Base) | 49 | How question plus bracket | How 0.71 vs bracket 1.30 | 0 matches | Passes | Weak |
| Why You Can't See Most of Hawaii | 32 | Why plus access | Access 1.56-1.61 vs 40 characters or fewer, 0.83 | Lands among travel docs ("The Real Hawaii Most People Miss", 1.2M) | Passes; keeps "Most Of" | Swap C only if B fails |
| Hawaii, Measured From Its True Base | 35 | Label | Label 0.90; 31-40 characters 0.83 | 0 relevant | Passes | Demote to the description's first line |
| Hawaii Is Only the Summit | 25 | Plain claim | 30 characters or fewer, 0.90; plain claim 0.94 | Summit-tour travel videos | Passes | Demote (use as Ch1's title) |
| How Tall Is Hawaii, Really? | 27 | How question | How 0.71; 30 characters or fewer | "Really like living in Hawaii" travel; the 14M "bigger than you think" Short | Passes | Reject |
| Hawaii Is Only the Tip. We Measured the Rest. | 45 | Statement + twist | As for the launch | Tipping-culture cluster | Passes | Reject ("tip") |
| Hawaii Is Much Taller Than You Think | 36 | Bigger than you think | 1.66 same-channel, 2.50 pooled | Sits under the 14M Short "Hawaii Is Much Bigger Than You Think" | Spent hook | Reject |
| We Measured Hawaii From Its True Base | 37 | We-opener, explorer | 1.36 / 1.25 vs 40 characters or fewer | "True Size of Hawaii" Shorts cluster (2.3M) | Passes | Weak |
| Most of Hawaii Is Underwater / The Rest of Hawaii Is Underwater | 28 / 32 | Superlative / label | Short | Flood news and relaxation videos | Ambiguous | Reject |
| Every Hawaiian Island Is a Mountaintop | 38 | Every X | "Every" 1.81 | "Exploring Every Island in Hawaii" (15.5M travel); "Why You Can't Visit This Hawaiian Island" Short (589K) | Promises a tour of every island, which the film is not | Reject for ep02 |

**Conditions for the launch title**

1. **"We Measured" must be literally true on screen.**
   - Run the measurement on the real survey data: a scale bar from the dented true base to the summit, at vertical exaggeration 1.0.
   - The narration credits the data ("Ships mapped every ridge with sonar. We measured it.").
   - Say "about 56,000 feet, from its true base" and always name Mauna Loa.
   - Without that shot, the title overclaims. Use swap B instead.
2. **Structure risk.** "X. We [verb]ed the Y." faintly echoes the clone first sentence "We Drained X." The two-sentence form is a clone marker overall (6.1% of clone titles vs 2.1% of craft), but the clone version always carries "Here's What" or "It's a Wound." Ours has neither, and its exact-title probe is empty.
3. **Untested grammar.** Only 4 of the 6,528 titles use a first-person "result" twist, so there is no direct evidence for or against it. That is the price of being distinct. Judge it in the feed-strip test (P1) and by Suggested CTR at about 10K impressions (P9), not by gut.
4. **Thumbnail overlap, for the thumbnail step.** The postcard's only word will be "HAWAII", which repeats the title's first word, against rule P6.
   - Either accept it as the brand device (the postcard is a place card, not a caption) or drop the name from the card.
   - Do not drop "Hawaii" from the title: it is the matching word for the RealLifeLore, Signore Galilei and Wendover host videos.
5. **Swap discipline.** Change one variable at a time, and never change the title and the thumbnail on the same day.
   - B changes only the second sentence.
   - C ("Why You Can't See Most of Hawaii") is a full grammar change, so use it only if B also stalls.

**Quick check of the ep03-ep12 working titles from the niche report**
- 9 of the 10 are 40 characters or fewer, in the bins that lose about 15% on the same channel.
- Consider a short twist sentence or a twist bracket to reach 41-50 characters.
- Ep04's "Lituya Bay's Wave Was Never 1,720 Feet" uses "Never", which this word list avoids.
- The deep-time titles (ep05, ep10, ep11) sit in the best-supported craft formula (1.22 same-channel, 1.56 pooled).

---

## 6. Files

- `research/packaging/titles.json`: the raw table, 6,528 rows. Fields include:
  - title, channel, subs, channel_baseline_views, views, age, age_months, len_s;
  - views_per_month, views_per_sub, breakout, within_channel_index;
  - formula, formulas, curiosity, first3, first3_kind, proper_nouns, power_words, farm_regex_hit, bracket;
  - in_A_core, in_B_core, top_decile_A, top_decile_B, group (clone_listed, craft_listed, mass_producer or other), source and queries.
- `research/packaging/work/title_stats.json`: every number in this report, with the pooled cells and bootstrap intervals, the same-channel tests, the examples and the query list.
- `research/packaging/work/title_cloneset.json`: the formula classifier run on the niche study's clone and craft title sets.
- `research/packaging/work/title_anatomy.py`: the pipeline, which re-runs in about 8 s. The collectors are `yt_collect.py` and `chan.py`. Raw pulls are in `work/raw/` (search1-4, channels, filtered and the probes).
