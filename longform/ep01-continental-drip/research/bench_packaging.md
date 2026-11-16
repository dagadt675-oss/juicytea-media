## Long-form 1M+ benchmark (packaging side): what it takes in the "weird Earth / myths" niche

**Data base:** 50 search queries plus the upload lists of 18 channels gave 1,461 long-form (6 min or longer) videos with 1M+ views. Of these, 96 are outliers: views at least 10x the channel's subscribers, or a channel under 300K subs. Saved under `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/bench-packaging/` (`all_rows2.json`, `q_all.json`, `q_more.json`, `sheet1.jpg`, `sheet2.jpg`).

### (a) Top outliers (topic and packaging power, not channel power)

| Title | Views | Subs | x subs | Len | Age |
|---|---|---|---|---|---|
| 50 Geography Facts So Crazy They'll Change How You See the World (GeoMap Unveiled) | 5.6M | 48K | 119x (2,090x channel median) | 22m | 17mo |
| 50 Facts About Texas That Sound Fake But Are 100% True (Geography Explored) | 1.9M | 14K | 134x | 73m | 8mo |
| Unseen Drone & Satellite Images of North Sentinel Island | 4.4M | 8K | 576x | 8m | 8y |
| Wildest Borders Around The World (Data World) | 2.1M | 26K | 83x | 10m | 17mo |
| Mariana Trench: What They Found In The Deepest Place On Earth (Uncharted Depths) | 4.1M | 34K | 122x | 18m | 8mo |
| Every Unexplored Place on Earth (Paintify) | 1.6M | 22K | 73x | 12m | 8mo |
| The Most Impossible to Reach Islands on Google Earth (Curiosity Dude) | 2.5M | 38K | 67x | 21m | 5mo |
| Why Deep Sea Creatures Get Creepier the Deeper You Go (Mr. Science) | 17.2M | 265K | 65x | 18m | 12mo |
| This Discovery in the Mariana Trench Will Transform Geopolitics (New Nature) | 12.5M | 234K | 54x | 28m | 16mo |
| What They Found In the Deepest Place on Earth (Astrum Earth) | 13.2M | 503K | 26x | 35m | 15mo |
| When Antarctica Was a Jungle (Mr. Science) | 5.3M | 265K | 20x | 26m | **2.5mo** |
| Why There is No Bridge Between Europe and Africa (Map Pack) | 7.1M | 442K | 16x (62x median) | 33m | 3y |
| Why Nobody Stays in Alaska (It's Not the Cold) (Map Pack) | 5.8M | 442K | 13x | 37m | 21mo |
| 10 Scientifically Impossible Places That Actually Exist (Mind Boggler) | 38.8M | 2.9M | 13x | 11m | 7y |
| Weirdest Places On Earth Explained (Professor Why) | 1.6M | 4K | 414x | 6m | 5mo |

Small faceless channels (4K–50K subs) are still producing 1M+ long-form videos in 2025–26. But it is hit-driven: GeoMap Unveiled's median video gets 2.7K views and Geography Explored's gets 4.4K. Each had 1 hit in roughly 40 uploads, so topic plus packaging decides it, not the channel.

### (b) Title formulas that win

Outlier titles have a median of 51 characters and 8–9 words. The niche as a whole is 45 characters. Keep to 45–60 characters so it isn't cut off on mobile.

1. **Number + "sound fake but true"** (our channel's own tagline): "50 Facts About Texas That Sound Fake But Are 100% True" (54 characters). "50 Geography Facts That Are Fake (But You Believed Them)" got 2.5M and 2.9M in two versions.
2. **"Why + paradox + (It's Not the obvious)":** "Why Nobody Stays in Alaska (It's Not the Cold)" (46). "Real Reason Ships Don't Pass Under South America (It's Not the Distance)" (72, 4.3M). The bracket cancels the obvious answer, which creates a curiosity gap. This pattern is 8% of outlier titles vs 2% of the niche.
3. **"What They Found in [superlative place]":** "What They Found In the Deepest Place on Earth" (45, 13.2M).
4. **"Every [category] on Earth":** "Every Unexplored Place on Earth" (31). It promises completeness.
5. **"Nothing About X Is Normal... Here's Why"** / **"Why X Gets [weirder] the Deeper You Go"** (53–56).
6. **Time-reversal:** "When Antarctica Was a Jungle" (28 characters, 5.3M in 10 weeks).

**Word signals in outlier titles vs the niche:**
- superlative "Most/-est": 38% vs 25%
- "Earth/World": 33% vs 20%
- one ALL-CAPS word ("NOBODY", "NOT"): 24% vs 13%
- "Impossible / Shouldn't Exist / Doesn't Add Up": 9% vs 3%

Plain "How…" and question marks under-index.

**"(No AI)" tags:** they now appear on several 1M+ titles. We may not use the tag (we never mention AI). Instead we should signal authenticity with "real satellite data" or "NASA images".

### (c) Duration sweet spot
- All 1M+ niche long-form: median 17.8 min.
- Explainer-type outliers (excluding 4K stock compilations): median **20.5 min**, interquartile range 15–30 min. 2025–26 uploads: median 21.8 min.
- The 45–190 min "4K travel documentary" compilations depend on stock footage, which we can't use, so they are not reproducible for us.
- The 6–10 min hits are mostly 2016–2019 RealLifeLore/Vox legacy.
- **Target: 16–22 min.** A "50 facts" list format can stretch to 25–30 min.

### (d) Thumbnail rules (from 20 outlier thumbnails viewed)
- **0–4 words**, usually 2–3, as heavy condensed sans-serif in white on black boxes, with **one word in red** ("CAN'T **EXPLAIN**", "WHAT **CHINA** FOUND", "IT'S **TERRIFYING**", "**ONLY** 8 MILES").
- Thumbnail text **adds to the title, never repeats it**. Example: title "No Bridge Between Europe and Africa", thumbnail "ONLY 8 MILES".
- **No presenter faces at all.** The only people are documentary subjects (Sentinelese).
- **Maps dominate the geography winners:** satellite or relief terrain with the target region as an extruded, flat-colour slab with a drop shadow (Texas blue, Alaska navy, Australia yellow with red density). Each has **one white curved arrow** to a red pin or glow. A **flag** is an instant identifier.
- **Circles:** a yellow ring around a tiny object (a creature in a trench), or a red dashed border line.
- **Scale contrast:** a tiny diver next to a huge creature, a tiny rock in an empty ocean ("NO HUMAN HAS EVER BEEN HERE"), a tiny sub in the abyss.
- **Palette:** deep navy/teal and black for deep sea and ice, saturated green-brown terrain, with red and yellow as the only accents.
- **Cutaways** (mountain, ice sheet and lava cross-section plus a flag) work for "under X" topics. These are reproducible in Three.js.
- **Grid of 6 labelled tiles** for "Every X" catalogue videos (Paintify, Professor Why).
- Several outliers use generated art. We must hit the same look with real NASA/USGS imagery and 3D renders.

### (e) Topic archetypes: proven vs saturated (1M+ count / count since May 2025)

**Saturated (avoid as a head-on topic):**
- Mariana Trench / deepest place: 11 / **9**, with a new 1M+ video almost monthly.
- Forbidden / impossible-to-reach places: 18 / 11, plus a Paint Explainer series.
- North Sentinel: 14 / 5.
- Antarctica's hidden secrets: 12 / 7.
- Deepest hole / Kola: 11, with a 48M incumbent.
- "Why nobody lives in X": 67 / 12; Geography By Geoff posts it weekly.

**Proven but under-supplied recently (gaps):**
- **"Facts that sound fake but are true" mega-lists:** a 48K-sub and a 14K-sub channel both broke out, and this is exactly the Myth Juice brand.
- **Strange borders / enclaves / countries that don't exist:** 39 total but only 8 recent. "Enclaves and exclaves explained" has 0 long-form videos at 100K+, while Data World got 2.1M on 26K subs. Our best Short was "Countries Split in Two".
- **Deep-time "When X was Y":** 9 / 1. Mr. Science got 5.3M in 10 weeks.
- **Maps are wrong / projection:** 25.7M and 23.8M incumbents are 9–10 years old, with only 2 recent.
- **Time zones / date line:** 5 / 0.
- **Earth stopped spinning / hypotheticals:** 31 / 0 recent; all incumbents are old.
- **Lost continents / Zealandia:** 4 / 1.

### (f) 10 packaging rules for a 1M-view video here
1. Pick a topic with proven 1M+ demand but **fewer than 2 strong uploads in the last 12 months**. Avoid the saturated list in (e).
2. The topic must sound false on first read. "Sounds fake but is 100% true" is the strongest small-channel formula found.
3. Title: 45–60 characters, 8–10 words, a superlative or "Earth/World", at most one ALL-CAPS word, and an **"(It's Not X)" or "Actually" reversal**.
4. Thumbnail: 2–4 words that **complete** the title, white on black boxes with one red word, and no face.
5. The thumbnail hero is a **3D relief or satellite map** with one flat-coloured extruded region, one white arrow and one red pin or ring. For "under" topics, use a cutaway cross-section.
6. Build in scale contrast: a tiny human or object against something huge.
7. Length 16–22 min. A "50 facts" list can run 25–30 min with numbered chapters to hold retention.
8. Signal authenticity on screen and in the description: real NASA/USGS satellite and elevation data. The audience is rewarding "real" over generated imagery.
9. Plan a series from day one ("Part 2", "Every X"). Paintify, Paint Explainer and Map Pack each got repeat 1M+ videos from one format.
10. Use the channel's own Shorts as a test bed. Turn the top Short angle ("countries split in two") into the long-form and package it the same way. A/B test 3 thumbnails with "Test & Compare".