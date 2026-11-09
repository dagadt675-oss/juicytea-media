# Thumbnail anatomy: what top performers in our space do on a phone

Date: 2026-11-08. Scope: long-form videos (4 minutes or longer) in the map, geography and earth-story space. I compared top performers, meaning videos with high views relative to channel size, against the rest. Contact sheet: `refs/anatomy_sheet.jpg`, which shows the 15 exemplars at phone-card size and again at compact-card size. Paths in this document are relative to `research/packaging/`.

---

## The short answer

1. **No colour recipe makes a winner.** Top performers are *not* brighter, more saturated or more colourful than the rest. If anything they are darker:
   - median luma 90 vs 105 (p = 0.016);
   - bright or saturated pixels 21% vs 27% (p = 0.008).

   Part of the gap is topic. Deep-ocean titles are 16% of winners and 7% of the rest, and those pictures are dark by nature. With those titles removed, luma is 95 vs 107 (p = 0.13).

   Only 13% of winners meet packaging rule P5's "40% bright or saturated" (31% of the rest do). Brightness is a **relative** game against the cards next to ours in the feed, not an absolute target. `feedstrip.py` measures exactly that.

2. **Text is short and mid-sized, never huge.**
   - Median text on winners is 4 words. With collage grids removed it is 3.5, against 3 for the rest (n.s.).
   - The tallest line is a median 10% of thumbnail height (IQR 9-13%) in both groups.
   - Only 6 of 233 thumbnails with text reach 20%.
   - Among channels under 100K subscribers, the *rest* use *bigger* text than the winners (12% vs 10%, p = 0.01). That is the clone kit's big boxed captions, and the extra size bought nothing.

3. **Graphic devices do not separate winners from the rest.**

   | Device | Winners | Rest |
   |---|---|---|
   | Arrows | 22% | 25% |
   | Rings | 6% | 7% |
   | Red/orange highlighted regions | 13% | 15% |
   | Before/after splits | 6% | 5% |
   | Faces | 5% | 12% |
   | Scale comparisons | 5% | 9% |
   | 0 or 1 device | 84% | 84% |
   | No device at all | 54% (34 of 63) | |

   Among craft videos (clone, template-farm and sleep-doc groups removed), caption boxes are much **rarer** on winners: 6% vs 23% (p = 0.008).

4. **What does separate winners:**
   - **Collage grids** for "Every X" list films: 8% vs 1% (p = 0.03). Examples: Paintify, Earthyphus, Chris Explains. This is a format signal, not a lever for ep02.
   - **Fewer channel logos and series frames:** 3% vs 20% (p = 0.001). This mostly reflects big channels such as Nat Geo's "FULL EPISODE" frame, whose videos have low views per subscriber.
   - **The Everest / tallest-mountain cluster is the worst performer we found.**
     - 0 of the 7 eligible videos are top performers.
     - Their median is 0.77x the channel's own median views, against 9.6x for the whole set.
     - 4 of the 10 videos that fell below their own channel's median are Everest or Mauna Kea comparisons: StarTalk 0.20x, CATASTROPHIYA 0.20x, RealLifeLore 0.85x and Sunless Deep 0.77x. A fifth below-median video, the Korean Hawaiʻi drain at 0.69x, also sells "a mountain taller than Everest".
     - This independently confirms the rule: no Everest in the title, the thumbnail or the first 30 seconds.

5. **Distinctiveness does not cost performance.**
   - 32% of winners pass `niche/work/gate.py`, against 24% of the rest.
   - Winners are no closer to the drain-clone cluster: feature distance 11.6 vs 11.5.
   - The drain-clone group passes the gate 0% of the time.

6. **A postcard thumbnail already exists in the Hawaiʻi lane.** The niche study found 0 postcards in its 106 thumbnails. In this wider set of 247, one appears: Extremities, "Kalaupapa: Why Hawaii's Most Isolated Town Stays Isolated".
   - 204K views on 156K subscribers, exactly its channel median.
   - The design: a full-frame vintage "greetings from KALAUPAPA" card in large retro letters, with a stamp top-right, over the Molokaʻi sea cliffs.
   - It is not a hit, but it sits in our host cluster. **Our card must not look like it.** Use an off-white card placed as an *object* on the real 3D mountain. No full-frame postcard, no "Greetings from" script, no retro block letters, no flowers. Keep the stamp small and our own.
   - Travel docs also use "postcard" in their *titles* ("Switzerland Beyond the Postcard", "GREECE: The Country Behind the Postcard"), but none of them uses a postcard thumbnail.

**What this means.** In this lane the thumbnail's job is clarity, not a colour formula. Success relative to channel size is driven mainly by premise and timing: first movers in a format and huge host topics. On a phone, the winners share four habits:

- one recognisable shape;
- one action or partial state, such as a waterline, a lifted lid or a cut-open island;
- 1-3 words that survive at 168x94;
- at most one device.

---

## 1. Data

| Source | Thumbnails |
|---|---|
| Niche study, already coded (`niche/refs`, `thumb_codes.json`, 7 groups) | 106 |
| Earlier packaging pull (context.md outliers, topic_hunt incumbents, 42 probes from 2026-11-08 morning; 36 overlap with the niche set) | 95 new |
| Fresh probes for this report (25 queries plus 3 postcard checks, 2026-11-08 afternoon; `anat/raw/probe_c.json`, `probe_d.json`). Covers missing outliers (Paper Skylines, World Maps Online, TOP 7, Evolution Catalog, Boring Planet, Brofessor Stein), incumbents (Nat Geo Drain the Oceans x5, FAULT LINES Hawaii 1946, OzGeology Nuʻuanu, PBS NOVA Kīlauea, RealLifeLore Hawaii history), and the Hawaiʻi, volcano, seamount, Everest-vs-Mauna-Kea, islands and maps clusters | 46 new |
| **Total downloaded to `refs/thumbs/`** | **247** |
| With views and channel subscribers known | 232 |
| Eligible for the split (7 days or older, 4 minutes or longer, subs known) | 203 |

- **Channel size** came from channel pages (subscribers plus the median of the last ~30 uploads). It was scraped for 186 channels, with the earlier bench data used for the rest. YouTube watch pages and yt-dlp were blocked (429 and bot-check errors), so per-video publish dates are the relative ages shown in search results.
- **Computed with PIL/numpy** (`anat/metrics2.py`, `anat/metrics_pop.py`). Each thumbnail is letterbox-cropped and analysed at 320x180:
  - mean luma (0-255);
  - mean HSV saturation;
  - Hasler-Süsstrunk colourfulness;
  - dark-pixel share (luma under 20%);
  - bright-or-saturated share;
  - navy, tan and red shares (same thresholds as `gate.py`);
  - luma contrast and edge density;
  - focal-subject size, two ways: the largest blob that differs in colour from the border (area and bbox), and a visual bucket (L 50% or more, M 25-50%, S under 25%);
  - `gate.py` distances to the clone and template-farm clusters, and pass/fail.
- **Coded visually, blind.** Tiles were shuffled and shown without titles or views at 380x214, roughly phone-card width, with a 10%-height ruler on each tile. There are 16 sheets (`anat/code_01.jpg` to `code_16.jpg`), and the codes are in `anat/vcodes.txt`. For each thumbnail I recorded:
  - the number of text words;
  - the tallest line's cap height as % of thumbnail height (about ±2 points);
  - caption box, arrow, circle/ring, face (including cartoon faces), before/after split, scale comparison, map/globe, numeral, depth label, red/orange highlighted region, grid/collage, inset picture, logo, waterline over/under view, tan drained basin, and postcard frame.
  - **Agreement with the niche study's independent codes** on the 59 thumbnails both coded: arrow 97%, depth 100%, face 100%, region 93%, box 85%, tan basin 81% (after harmonising). Most box disagreements are heavy outlined captions with no plate.
- **Split.**
  - **TOP** = 100K views or more AND views at least 10x the channel's subscribers. That gives 63 videos; 52 of them are from channels under 100K subscribers.
  - **REST** = the other 140 eligible videos.
  - A 100K floor stops micro-channels from counting as winners, for example 1,040 views on 2 subscribers.
  - **Robustness checks:**
    - (a) channels under 100K subscribers only;
    - (b) top = 100K views or more AND at least 5x the channel's own median views;
    - (c) craft only, with drain clones, "without ice/water" copies, template farms and sleep docs removed.
- **Tests.** Mann-Whitney U for continuous measures and Fisher's exact test for binary ones.

---

## 2. Top performers vs the rest

### 2.1 Measured image properties (medians; n = 63 vs 140)

| Measure | TOP | REST | p | Holds in checks? |
|---|---|---|---|---|
| Mean brightness (luma 0-255) | **90** (IQR 68-115) | **104** (82-124) | 0.016 | (c) yes, 89 vs 107. (a) no, 94 vs 99. (b) no |
| Bright or saturated pixels | **21%** (11-36) | **27%** (18-42) | 0.008 | (c) yes, 19% vs 26% |
| Navy pixels | 17% | 11% | 0.07 | (c) 18% vs 10%, p = 0.047 |
| Dark pixels (luma under 20%) | 31% | 26% | 0.08 | no |
| Saturation | 46% | 45% | 0.88 | no difference anywhere |
| Colourfulness | 65 | 72 | 0.17 | no |
| Tan pixels | 1.5% | 2.6% | 0.13 | small channels: 1.9% vs 4.3%, p = 0.053 |
| Saturated red pixels | 0.5% | 0.6% | 0.66 | no |
| Contrast (luma SD) | 59 | 62 | 0.06 | no |
| Edge density (clutter) | 22% | 24% | 0.56 | no |
| Focal blob area (computed) | 37% | 39% | 0.26 | no |
| Feature distance to drain clones | 11.6 | 11.5 | 0.66 | no |
| Contrast at compact size (168x94 luma SD) | 56 | 60 | 0.07 | no |

**Reading:** the colour statistics that packaging rule P5 targets ("bright, saturated, not navy") do not separate winners. Winners lean dark and calm. That is partly the deep-ocean topics, and partly because craft channels use moody real-world light rather than poster colours. One lit subject against a calm field shows up again and again in the exemplars, but the "pop" metric (98th-percentile luma minus the median) does not differ significantly between groups (158 vs 153, p = 0.17).

### 2.2 Coded content (share of thumbnails)

| Feature | TOP | REST | p |
|---|---|---|---|
| Words: median | 4 | 3 | 0.03 (no-grid: 3.5 vs 3, p = 0.14) |
| 1-3 words | 40% | 55% | 0.049 |
| 7+ words | 22% | 9% | 0.024. These are collage labels (Paintify, Earthyphus) and early drain clones with place labels |
| No text | 6% | 7% | 1.0 |
| Tallest line, % of height: median (IQR, text only) | 10% (9-13) | 11% (9-13) | 0.55 |
| Tallest line 15% or more | 10% | 13% | 0.64 |
| Tallest line 20% or more | 3% (Fossil's "12", the "8TH" graphic) | 2% | |
| Caption box / banner | 16% | 24% | 0.27 (craft only: **6% vs 23%, p = 0.008**) |
| Arrow | 22% | 25% | 0.73 |
| Circle / ring | 6% | 7% | 1.0 |
| Face (including cartoon) | 5% | 12% | 0.13 |
| Before/after or left/right split | 6% | 5% | 0.74 |
| Scale comparison (Everest bars, landmark ladders) | 5% | 9% | 0.40 |
| Numeral in text | 29% | 18% | 0.10 |
| Depth or height label | 11% | 9% | 0.61 |
| Red/orange highlighted region | 13% | 15% | 0.83 |
| Map or globe as subject | 40% | 44% | 0.65 |
| Collage grid | **8%** | **1%** | 0.03 |
| Channel logo or series frame | **3%** | **20%** | 0.001 |
| Waterline over/under view | 2% | 4% | 0.44 |
| Tan drained basin | 6% | 7% | 1.0 |
| Focal subject L (50% or more of frame) | 52% | 65% | 0.12 (no-grid: 57% vs 66%) |
| Focal subject S (under 25%) | 17% | 3% | 0.001 (almost all collage grids) |
| 0-1 graphic devices | 84% | 84% | 1.0 |
| Clone kit (box + arrow + depth label) | 3% | 1% | 0.59 |
| Passes gate.py | 32% | 24% | 0.30 |

### 2.3 Robustness checks

| Check | Top / rest | What still holds |
|---|---|---|
| (a) Channels under 100K subs | 52 / 49 | Rest use *bigger* text: 12% vs 10% (p = 0.01); text 15% or more: 8% vs 22%. Tan pixels lower on winners (1.9% vs 4.3%, p = 0.053). Scale comparisons 4% vs 10% (n.s.). Brightness gap disappears (94 vs 99) |
| (b) Views at least 5x the channel median | 100 / 102 | Winners use more caption boxes (28% vs 15%, p = 0.03) and more arrows (34% vs 19%, p = 0.02). These are the template-farm and first-mover drain hits measured against their own channels' weaker uploads. Faces rarer on winners: 4% vs 16% (p = 0.008) |
| (c) Craft only (clone, farm, sleep groups removed) | 51 / 117 | Darker (89 vs 107, p = 0.02); fewer bright/saturated pixels (19% vs 26%, p = 0.004); **caption boxes 6% vs 23% (p = 0.008)**; logos 4% vs 23% |

**Honest summary:** the only robust signals are these.

- Faces and Everest-style scale comparisons go with *under*performance.
- Craft winners do not use caption boxes.
- Collage grids win, but only for "Every X" lists.
- Brightness and colour do not predict success on their own.
- The clone kit (box, arrow, depth label) won for **first movers**: Contour Atlas got 170K on 1.4K subscribers, and Hidden Provinces' Lake Ontario got 134K. Measured against their own channels, the kit still looks good in check (b).

  It is now saturated: the niche study measured a median of 448 views across 96 drain uploads in 35 days. In this set, the 5 drain clones that are 7 days or older are:
  - the two Contour Atlas first movers (170K and 165K);
  - two micro-channel copies under 100K (Drained Atlas 82K, High Ground Atlas 62K);
  - one stall (Map Whys, 40 views).

  The younger copies are mostly in the hundreds to low thousands. Copying the kit now means copying a decaying signal.
- **Top vs the 10 eligible videos below their own channel's median:**
  - faces 5% vs 30% (p = 0.03);
  - scale comparisons 5% vs 30% (p = 0.03);
  - bright or saturated pixels 21% vs 43% (p = 0.049). The underperformers are the *brighter* ones.

### 2.4 By lane (all 247; medians, except where marked as means or shares)

| Group | n | Views | Words | Text h | Luma | Bright/sat | Tan | Devices (mean) | Box | Arrow | Gate pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A drain clones | 24 | 10.6K | **10** | 12% | 108 | 20% | **21.6%** | 1.6 | **83%** | **79%** | **0%** |
| B "without ice/water" | 16 | 40K | 3 | 12% | 111 | 40% | 2.0% | 0.9 | 19% | 19% | 12% |
| C Hawaiʻi lane (niche) | 9 | 124K | 3 | 14% | 76 | 21% | 2.3% | 0.9 | 22% | 22% | 22% |
| D template farms | 14 | 302K | 4 | 12% | 89 | 23% | 0.8% | 1.6 | 57% | 71% | 14% |
| E sleep docs | 10 | 95K | 3 | 10% | 94 | 18% | 7.1% | 0.1 | 0% | 0% | 30% |
| F craft baseline | 21 | **2.57M** | 3 | 10% | 89 | 35% | 0.6% | **0.3** | **10%** | **14%** | **43%** |
| G real-data 3D | 12 | 947 | 4 | 12% | 82 | 15% | 3.4% | 0.9 | 8% | 8% | 25% |
| Probes / other | 141 | 929K | 3 | 10% | 104 | 25% | 2.6% | 0.6 | 20% | 26% | 26% |

**The craft winners' pattern:** 3 words, text at 10% height, 0.3 devices, almost no boxes or arrows, and the highest gate pass rate.

### 2.5 The Hawaiʻi lane on its own

There are 29 eligible Hawaiʻi titles. The 4 top performers are Signore Galilei (3.04M, 53x subs), Park Vibes (1.30M, 39x), GlobeHaven (125K, 50x) and Below The Map (124K, 15x).

The big-channel hosts are judged against their own channel median:

| Video | Views | vs channel median |
|---|---|---|
| RealLifeLore, boats | 7.07M | 6.1x |
| RealLifeLore, history | 4.73M | 4.1x |
| Wendover | 2.04M | 1.9x |
| Atlas Pro | 1.46M | 9.1x |
| PBS America NOVA | 1.39M | **103x** |
| BRIGHT SIDE, boats | 1.29M | **76x** |

Hawaiʻi thumbnails have a median of 3 words, the tallest line at 12% and luma 96. 48% are maps or globes, 38% have caption boxes and 28% have arrows.

The neighbours we will sit next to are mostly **teal or navy sea with green islands**. A card with a dark basalt mass, warm low sun and a pale off-white card will differ from them on hue, not only on brightness. Check this with `feedstrip.py`, not with absolute thresholds.

---

## 3. The 15 exemplars and why each works on a phone

The exemplars were chosen from top performers under at least one of the two relative definitions: 10x subscribers, or 5x the channel median. Each one teaches something Myth Juice can use. They are numbered as on `refs/anatomy_sheet.jpg`, which shows each at 390x219 (a full-width phone card) and at 168x94 (the compact card) on YouTube's dark-mode #0F0F0F.

**What survives the compact-card squint:**

- single words with a cap height of about 12% or more ("Kīlauea", NEPAL FLOOD, SEALED SINCE 1945, 12 Minutes, NO BOATS?);
- luminous accent shapes (cyan tunnels, magenta X marks, the white ice peel, a lit submersible);
- clean silhouettes (the island chain, Niʻihau).

**What dies:**

- labels under about 5% (Earthyphus's island names, Tetis's subtitle, the Google Maps route card);
- thin spaced caps (Astrum's MARIANA TRENCH is barely there);
- small parentheticals ("(all of)").

| # | Video (channel) | Views / subs (relative) | What is in it | Why it works on a phone | Take / don't take |
|---|---|---|---|---|---|
| 1 | Hawaii's Forgotten Islands (Signore Galilei) | 3.04M / 57.7K (53x subs, 26x median) | The whole island chain as small green silhouettes on near-black navy. Orange two-size text: "This isn't (all of) Hawaii". 5 words, tallest line 16%; luma 25, navy 87% | Only two things are bright, the orange words and the islands, so the eye has two places to land. At 168x94 "This isn't ... Hawaii" still reads (about 15 px letters, orange on navy), and the brain fills in "(all of)". The text is a myth correction about the place, which is our exact promise | **Take:** a plain correction statement about a famous place; the island chain as a shape. **Don't take:** the navy field (fails gate.py's blue rule and loses its edge in dark mode) or the line itself. It is our host video, and its text is close to "Hawaii Is Only the Summit", so our *thumbnail* must not repeat it |
| 2 | Why You Can't Travel Between Hawaii's Islands by Boat (RealLifeLore) | 7.07M / 7.93M (6.1x median) | A light teal sea, 3D islands and four magenta X marks on dashed ferry lines. "WHY NO BOATS?" in black plates with a yellow accent. 3 words at 10%; luma 140, the brightest Hawaiʻi card | The story is told by one repeated mark: you see how close the islands are, and four crosses say "but not by boat". The crosses are big saturated shapes, so they read at any size. The light sea separates it from the navy neighbours | **Take:** a bright, light sea; islands as shapes; one repeated mark carrying the curiosity. **Don't take:** black caption plates (clone-kit grammar now) |
| 3 | What's Hidden on Hawaii's Forbidden Island? (Park Vibes) | 1.30M / 33.6K (39x) | Niʻihau from above on deep blue, a red dot zooming to a ringed inset of the island's owners at microphones. "SECRET DICTATORSHIP" in 2 words at 12%, the second word in red | The island outline reads instantly as "remote island". The human inset adds stakes ("who runs this?"). The red word still reads at compact size | **Take:** one small piece of human proof inside a land and sea picture. Our ep02 human story could be a small paper cut-out. **Don't take:** the overclaim wording (owner rule), the ring inset or the faces |
| 4 | Kīlauea: Hawaiʻi on Fire (PBS America / NOVA) | 1.39M / 396K (3.5x subs, 103x median) | Full-frame lava texture with the title in white serif, **correctly spelled with kahakō and ʻokina**. "Kīlauea" at 14%, plus a PBS logo | One texture and one name, like a film poster. At 168x94 "Kīlauea" is still the largest legible element. Warm red and black stand out against blue ocean cards. Correct diacritics signal a trustworthy source | **Take:** the place name as the type hero, correctly spelled. Our postcard should read HAWAIʻI with the ʻokina. **Don't take:** lava (a spent Hawaiʻi image, and not our story) |
| 5 | Why Can't You Visit Iwo Jima? (Where They Stood) | 4.44M / 3.5K (**1,267x**, the strongest in the set) | The famous island cut open: glowing cyan tunnels inside dark rock, sea on the right. "SEALED SINCE 1945" in yellow with a dark outline, 3 words at 17% | A famous silhouette made new by seeing inside it. With one accent colour, the tunnels read as glowing lines even at 168x94. Short, heavy yellow text | **Take:** "the place you know, cut open to show its real shape". This is *Below the Postcard* in one frame. One luminous accent (our cyan waterline) |
| 6 | What's Still Under the Water at Omaha Beach? (Where They Stood) | 320K / 3.5K (91x at 14 days) | An over/under waterline shot: beach and cliff above, a tank on the turquoise sea bottom below. "AIMING SINCE 1944", 3 words at 14% | The waterline shows two worlds at once, and you read "under the water there is..." before any word. Turquoise stays bright at any size | **Take:** the partial-reveal grammar for **Arm B** (water still clinging to the flank, the shape showing below). This is the craft way to show a drain without the drain kit |
| 7 | What Antarctica Looks Like Without Ice (Unseen Works) | 1.75M / 2.9K (601x) | A globe with the white ice sheet peeled back like a lid over brown and blue bedrock. "LIFT THE LID", 3 words at 14% | An action half done on a shape everyone knows. The white peel is the brightest shape in any feed, and the text is one short verb phrase | **Take:** show the action mid-way, in a partial state. **Don't take:** the peel. Three copies appeared within 3 weeks (The Primal Years, Oddly Told, Bare Earth) |
| 8 | People Are Only Just Realising How Big Australia Is (Paper Skylines Mapping) | 814K / 7.6K (107x) | A Google Maps screenshot of Australia with a route card ("12 hr 31 min, 1,009 km") and an arrow. "AUSTRALIA REALLY IS KINDA BIG" stacked one word per line, 9% | A familiar everyday artefact (the maps app everyone uses) gives instant recognition and belief. The stacked words read as a column even at compact size | **Take:** this is the same mechanism as our postcard. A familiar object says "you know this place; you don't know it". **Don't take:** 8 words. It works only because each word sits on its own line in a quiet zone |
| 9 | Nepal's 2026 Disaster Explained: The Glacier That Wiped Out a Valley (The Last Day) | 5.19M / 35.5K (146x) | A real aerial photo of a valley town, a brown river and a dust cloud. "NEPAL FLOOD" in white with a shadow, 2 words at 12% | A real photo from above reads as true. The place and the event take 2 words. No device. It is still a believable photo at 168x94 | **Take:** the place name as the only text, over real terrain seen from above |
| 10 | The Wave That Was Taller Than a Skyscraper (The Last Day) | 1.56M / 35.5K (44x) | One dark storm wave fills the frame, with lightning and tiny city lights at the base. "LITUYA BAY" at 10% plus a small arrow | One giant shape. Scale comes from tiny lights, not a diagram. The unfamiliar place name is itself the curiosity | **Take:** imply scale with a tiny human-scale detail (a boat, a road, lights) instead of an Everest bar. **Don't take:** an 82% navy field |
| 11 | 8 Holes in the Earth No Geologist Can Explain (Before Humanity) | 225K / 2.65K (85x) | A mountain range with a perfect cylinder of rock pulled out and floating beside its hole. "EIGHT HOLES ZERO ANSWERS" | An impossible operation on a familiar landform reads as a silhouette (cylinder plus hole) even at compact size. Bright sky | **Take:** one surreal operation on real terrain. Our postcard lifted off the real mountain is the same move. **Don't take:** "no one can explain" (overclaim) |
| 12 | The Ocean That Vanished: How the Tethys Closed (Tetis) | 142K / 1.8K (78x at 7 days) | Real-data 3D relief of Anatolia with a dotted old coastline, a "today" inset map and a yellow headline. YouTube serves a Turkish localised thumbnail | Shaded real relief plus one warm accent reads as "real data". The yellow headline and the relief survive at compact size. It passes gate.py (distance 13.2 from the clones) | **Take:** our engine's DEM look is competitive for a 1.8K-subscriber channel, and a small "today" inset can anchor time. **Don't take:** 8 words and several numbers |
| 13 | What They Found In the Deepest Place on Earth (Astrum Earth) | 13.25M / 504K (26x) | Near-black water, one lit submersible and an anglerfish in its light. "MARIANA TRENCH" in spaced caps at 10% | One light source in the dark, so the eye goes to it. At 168x94 the lit sub is the only element besides the name | **Take:** light as the focal tool. **Don't take:** darkness for Hawaiʻi. Our subject is a sunlit mountain, and darkness only works where the topic *is* the dark |
| 14 | How Long You'd Last in Every Prehistoric Era (Fossil) | 12.5M / 54K (231x) | One illustrated creature with a torch on black. "12 Minutes" with a red numeral, 2 words at 17% | One subject plus a two-word number promise. The red "12" reads at any size. Episodes repeat the same look, so the series is recognisable | **Take:** one subject, 2 words, a repeatable series look (our postcard plus stamp). **Don't take:** the illustration style (we are photoreal real Earth) |
| 15 | Every Forbidden Island You're Not Allowed to Visit (Earthyphus) | 880K / 1.5K (595x) | A white card with 8 circular satellite crops of islands and tiny labels (3%) | The white card is the brightest object in a dark-mode feed (luma 183, 6% dark pixels). The grid says "a complete collection" before any word is read; the labels are not meant to be read | **Take:** a light card stands out in dark mode, which is why the off-white postcard is a strong feed signal. **Don't take for ep02:** grids belong to "Every X" lists |

**Also strong, but not taken as models:**

- **Tomas Pueyo, MEGAFLOOD (2.16M on 14.3K subs, 151x).** A BEFORE/AFTER split, which is on our ban list.
- **Contour Atlas, Chesapeake (170K on 1.4K, 124x).** The first-mover clone kit.
- **Mr. Science, Deep Sea Creatures (17.25M on 266K, 65x).** A saturated green field with a diver for scale; a deep-sea topic.
- **GeoMap Unveiled, 50 Facts (5.68M on 47.6K, 119x).** A giant "50", arrows, a cluttered map.
- **Paintify, Every Unexplored Place (1.66M on 22.3K, 74x).** A collage grid.

---

## 4. What this changes in our packaging rules (input for the ep02 thumbnail step)

1. **P5 "text: each line at least 20% of height" → "1-3 words, cap height 12-18%, at most 2 lines".**
   - The market median is 10-11%, and only 6 of 233 thumbnails reach 20%.
   - At 12% or more, a word is about 11 px tall on the 168x94 card and readable.
   - The postcard's place name at 18% (niche report) already puts us in the top ~10% for size. More words would cost more than a bigger size gains.
2. **Retire P5's "white on a black box with one accent word".** It is the clone kit. Craft winners use it 6% of the time, the rest 23% (p = 0.008), and the niche report bans it. Put text on the card or straight on the image with a soft shadow.
3. **Retire P5's absolute "40% bright/saturated, never navy".** Only 13% of winners meet the 40% mark. Replace it with relative tests:
   - (a) pass `gate.py`;
   - (b) in `feedstrip.py`, ours is the most distinct card *in hue and value* next to the Hawaiʻi hosts, which are teal or navy sea with green islands;
   - (c) aim for mid-tone luma 95-120 with one luminous accent (the cyan waterline or the off-white card), never a dark field.
4. **One focal subject.** Single-subject winners fill the frame (focal L) 57% of the time. Keep the massif at 50% or more of the frame, and use **0 devices**: no arrow, ring, box, number or label. Fifty-four percent of winners use no device.
5. **Show a partial state, not a split.** Use the waterline over/under (Omaha Beach, 91x), the lid half-lifted (Antarctica, 601x) or the island cut open (Iwo Jima, 1,267x). This confirms Arm B (half-drained, water clinging to the flank) as the strongest test arm. The ban on left/right before/after splits stands.
6. **The familiar-artefact frame is proven** (Google Maps card, 107x), so keep the postcard. Make it **unlike Extremities' Kalaupapa card**: a tilted off-white object sitting *on* the 3D terrain, plain postcard type, no "Greetings from", no retro block letters, no flowers, and a small stamp of our own.
7. **Spell like PBS.** The Hawaiian name on the card carries the ʻokina (HAWAIʻI). The correctly spelled "Kīlauea" title earned 103x its channel's median.
8. **No Everest anywhere in the package.** The cluster sits at 0.77x the channel median against 9.6x for the set, with 0 of 7 top performers. Use implied scale instead (Lituya Bay's tiny lights): a tiny boat or road for scale at the foot of the flank.
9. **No faces.** Faces appear on 5% of winners and 12% of the rest (with channel-median outliers: 4% vs 16%, p = 0.008).
10. **The gate stays mandatory.** Being far from the clone cluster costs nothing (32% of winners pass vs 24% of the rest), and the clone group passes 0%.

---

## 5. Caveats

- **Search bias.** The sample comes from search results, so successful videos are over-represented: only 10 eligible videos fall below their own channel's median.
- **Correlation, not cause.** Topic and timing confound everything; that is why the robustness checks exist.
- **Measurement error.** Text heights are visual estimates (±2 points). Ages are YouTube's rounded relative ages.
- **Thumbnails can change.** These are today's thumbnails. Some channels A/B test or swap thumbnails, and Tetis's is served in a Turkish localisation.
- **Small cells.** Only 5 drain clones are 7 days or older, so their outcome comes from the niche study (median 448 views across 96 uploads), not from this split.

## 6. Files

All paths are relative to `research/packaging/`.

| What | Path |
|---|---|
| Thumbnails | `refs/thumbs/` (247 files; niche refs hard-linked; never committed) |
| Merged dataset (views, subs, channel median, ratios, PIL metrics, gate, visual codes) | `anat/merged.json` |
| Visual codes, blind code map, coding sheets | `anat/vcodes.txt`, `anat/blind_codes.json`, `anat/code_01.jpg` to `code_16.jpg` |
| Statistics | `anat/analysis.txt`, `anat/analysis.json`, `anat/top_flags.json` |
| Exemplar list | `anat/exemplars.json` |
| Exemplar contact sheet | `refs/anatomy_sheet.jpg` |
| Scripts | `anat/merge_all.py` (data merge; rebuilds merged.json from scratch, so run it first), then `anat/metrics2.py`, `anat/metrics_pop.py`, `anat/analyze.py`, `anat/anatomy_sheet.py`. Also `anat/codesheets.py`, `anat/ysearch2.py` (search with channel ids) and `anat/chfetch.py` (channel pages) |
| Raw probes | `anat/raw/probe_c.json`, `probe_d.json`, `ch_add.json`, `ch_extra.json`, `ch_extremities.json` |
