# Myth Juice long-form #2: topic hunt context (2026-11-08)

## The channel
- YouTube "Myth Juice" (@juicytea-l6l). Faceless, English narration (ep01 used ElevenLabs "Brian"; OWNER DECISION 2026-11-08: ep02 onward uses ElevenLabs "Rodney - Clear Educator", voice_id eY2VJs4Gi8QKG2RV01sS, calm clear young American (Midwest) male, model eleven_v4, ~153 wpm; already in the account and tested), small channel (essentially new; ~1 subscriber-driven view per video).
- Niche so far: map / geography / earth myth-busting and true stories about places. Owner wants: storytelling first, funny scenes and real animation, no emojis, no on-screen sources/citations (description only), only a few big vivid numbers, never mention AI anywhere, no false claims.
- Owner goal: a long-form video that can reach 1M+ views. Owner's verdict on ep01: "not very good". He wants the next one "much, much better".

## Topics already used by the channel (do NOT propose again)
- Why the continents point south / "continental drip" (long-form ep01, published 2026-11-06).
- Lake Peigneur (lake that drained into a salt mine, 1980) (long-form, earlier).
- Pig War / San Juan Islands border (earlier project).
- "Bats aren't blind" (Short).

## Ep01 results after ~35 hours (YouTube Studio)
- Views 43, impressions 925, CTR 2.27%, avg view duration 3:51 of 15:34 (24.7%), likes 2, comments 0, shares 0, subs +0.
- Traffic: Suggested 862 impressions (93%) at CTR 1.97%; Browse/Home 34 impressions at CTR 8.82%; Search 9 impressions, 0 clicks.
- Devices: Mobile 44% of views, avg 2:11 (14.1%!); Tablet 2:45 (17.8%); Computer 7:53 (50.7%); TV 8:24 (54.1%).
- 98% non-subscribers. US = 28% of views, 43% of watch time.
- Reading: (1) the packaging loses in the Suggested feed (2% CTR next to other videos); (2) phone viewers quit fast: the film was built for a big screen (dense maps, small labels, slow globe moves, abstract geology); big-screen viewers liked it (50%+). (3) Search demand for the topic was ~0.

## Viewer-retention critique of ep01 (YouTube's own analysis, owner pasted it)
- Hook: the intro stacked promises/"table of contents" (0:37-0:54: "dig to China, 1875 theory, future collisions"). Cut the menu; go straight into the story.
- A "Juice Check / Subscribe" interruption mid-content (4:57-5:07) broke the flow right before the strongest reveal. Never put a subscribe ask mid-story.
- Historical asides (Bacon Latin quote + static portrait, 1:00-1:25) too slow; get back to motion faster.
- A stylised animated corridor scene (7:35-7:50) clashed with the photoreal globe look: keep one consistent visual language.
- Ending: the conclusion lands, then end cards/empty frame appear too early. End the moment the last line lands and hand off to a concrete next video.
- Praised: the 3D antipode overlay (2:40-3:05) was "remarkably vivid and professional". The visuals and narration quality are a strong base.

## What our production pipeline can do (feasibility)
- Programmatic film engine: headless Chromium + three.js + Canvas2D -> ffmpeg, 1080p30. Rendered on a Colab L4 GPU (~15 min for a 16-min film).
- Photoreal 3D globe (NASA Blue Marble with bathymetry, VIIRS night lights, DEM relief, atmosphere), Natural Earth borders/coastlines/rivers/lakes, great-circle arcs, true-size moves, hi-res regional satellite patches (NASA GIBS), DEM terrain builder (SRTM/GMTED/ETOPO terrain tiles => we can render real 3D terrain AND seafloor, i.e. "drain the water" shots are natural for this engine), paleo-geography (GPlates), cut-away Earth, morphs.
- Animated CC0 3D characters (Quaternius/Kenney low-poly people/animals), motion graphics, counters, Ken Burns on public-domain photos (US gov / NASA / NOAA / Library of Congress / Wikimedia PD).
- ElevenLabs narration with word timings, music + SFX mixer at -14 LUFS.
- No live-action filming, no presenter face, no paid stock footage. Public-domain archival photos are fine.

## vidIQ outlier pull (long-form, English, channels <= 1.5-2M subs, sorted by breakout = views / channel's typical views). Date 2026-11-07.
Spectacle / "what's hidden" / drain format:
- "What Antarctica Looks Like Without Ice" - Unseen Works, 2.9K subs - 1.8M views, 773x, 11:21, 3 weeks old, 964 views/hour.
- "What If All the Ice on Earth Melted?" - Earth Tipping, 1.5K subs - 961K, 178x, 11:58.
- "We Drained the Chesapeake Bay. Here's What Was Hidden at the Bottom." - Contour Atlas, 1.4K subs - 170K in 1 week, 696x, 21:20, 511 views/hour.
- "We Drained the Great Lakes. Here's What Was Hidden at the Bottom." - Contour Atlas, 1.4K subs - 165K in 2 weeks, 345x, 22:12.
- "We Finally Know What's Hidden Under The Mediterranean Sea" - Spinosnack 603K subs - 719K.
- "Zanclean Flood: The Refilling of the Mediterranean" - Super Freaky Science 8.8K subs - 219K, 382x.
- "The Lost Continent That Connected Philippines & Indonesia - Then Vanished" - 2.2K subs - 272K, 1047x.
- "This North Sea Survey Uncovered Something That Could Rewrite the Story of Doggerland" - 1.1K subs - 213K, 526x. "The North Sea Is Far Stranger Than We Thought" - 1.6K subs - 279K (2h sleep doc).
- "8 Holes in the Earth No Geologist Can Explain" - 2.6K subs - 225K. "What If The Ocean Rose 2,500 Meters? Only 1 Country Survives" - 2.8K subs - 170K in 6 days.
- "The Insane Future of Earth (2026 to 1 Trillion Years)" 3.3K subs 607K; "History of the World: Every Year" 2.5K subs 553K.
Forbidden / remote places:
- "Why Can't You Visit Iwo Jima?" - Where They Stood, 3.5K subs - 4.4M views, 26x, 20:02, 1 month old, 1.5K views/hour.  <-- huge
- "The Most Impossible to Reach Islands on Google Earth" - Curiosity Dude 38K subs - 2.6M; "What Is the Hardest Island in the World to Reach?" same channel 669K.
- "Why America Abandoned Its Best Islands" - Geography By Geoff 1.1M subs - 3M.
- "Every Forbidden Island You're Not Allowed to Visit" - Earthyphus 1.5K subs - 878K, 90x, 7:13.
- "Every Unexplored Place on Earth (Full Series)" - Paintify 22K - 1.7M. "The World's Most Forbidden Places You Can Never Enter" - 391K subs - 1.2M.
- "The Real Reason You Can't go to North Sentinel Island" - 434K (saturated topic).
Map / geography explainers:
- "People Are Only Just Realising How Big Australia Is" - Paper Skylines 7.6K subs - 814K, 575x, 5:02.
- "Why the UN Voted on a World Map (And Why the US Voted No)" - World Maps Online 62K - 790K (news-driven, 2026 Mercator/UN map story) and "The UN Voted to Fix the World Map. The Headlines Got It Wrong" 274K.
- "7 Borders That Make Absolutely No Sense - But Actually Exist" - 17.7K subs - 702K. "Shortest Borders Between Countries" Glore 806K in 6 days.
- US-region "is hiding something" format: "Why Appalachia Is Sitting on the Most Unexplained Land..." 6.1K subs 473K; "What's Really Going On in the Midwest?" 2.7K subs 313K; "What's Hiding In The Deep South..." 14K subs 302K; "The UK Is Hiding Something Nobody Talks About" 2.2K subs 336K; "California Is Hiding..." 311K.
Disaster / true story:
- "Pinatubo: The Volcano That Claimed 850 Lives" - 44.5K subs - 703K, 663x (52 min).
- "The 119-Day Survival Story That NOBODY Believed!! | SV Rose-Noelle" - 257K subs - 1.5M.
Myth-busting lists:
- "The History 'Facts' You Were Never Supposed to Question" 5.7K subs 614K (1821x); "Old Wives' Tales Science Finally Proved True" 1.2K subs 350K in 1 week; "Things You Learned in School That Are No Longer True" 1.6K subs 245K; "10 Famous Ancient Events That Never Happened" 1.1M.

Note: many of these small-channel outliers are mass-produced "AI-labeled" channels; their success shows DEMAND for the premise, not a quality bar. A well-made, true, story-driven version of a proven premise should beat them on retention.

## vidIQ rising keywords (geography / earth / strange places niche, last month)
- "tristan da cunha" ~315K est. monthly searches, +118%.
- "lake powell" ~163K, +150% (US).
- "underwater archaeology discoveries" ~168K, +185% (US 95%).
- "disasters explained" ~239K, +110%.
- "lost british cities" ~136K, +232%.
- "how lighthouse keepers survived winter on a rock in the middle of the ocean" ~173K, +147%.
- "how long would you survive in every era of earth?" ~113K, +6464%.
- "prehistoric survival" ~125K, +165%. "what would happen if" ~217K, +134%.
- "karl bushby" ~281K, +148% (man walking around the world).
- "colossal squid" ~187K, +150%. "ancient polynesian star navigation methods" ~205K.

## Tools you can use
- Free YouTube supply probe (no API key, unlimited): `python3 /home/user/juicytea-media/longform/ep01-continental-drip/tools/ytsearch.py "query one" "query two"` prints the top results (views, length, age, channel) and a supply summary (count of long-form >=6 min results with >=100K views whose title matches the query). Use it to judge saturation: a topic is saturated if several recent, well-made long-form videos with >1M views already tell the same story with the same angle.
- WebSearch / WebFetch for facts and current events.
- Do NOT call any vidIQ tool unless your instructions explicitly allow it (credits are very limited).
