# feedsim: YouTube dark-mode feed simulator

`feedsim.py` places a candidate title and thumbnail among real competitor cards. It renders three surfaces in YouTube dark mode at true layout scale. The tool is deterministic: the same spec and seed always give the same pixels.

It builds on `research/niche/work/feedstrip.py`, adding realistic page chrome, title wrapping and timestamp badges, three layouts and a glance view. It reuses `sim_lib.feat()` for the distinctiveness metric, and `--gate` calls `research/niche/work/gate.py` directly.

The tool needs only PIL and numpy, plus the Roboto TTFs in `fonts/`, which come from the Google Fonts CSS API (static 400/500/700).

## Run

```
cd research/packaging/feedsim
python3 -I feedsim.py specs/ep01.json --out ../feeds/ep01 --glance --report --sheet --gate
```

| Flag | Effect |
|---|---|
| `--layouts home,upnext,sidebar` | Picks which layouts to render (default all three). |
| `--seed N` | Shuffles the neighbours and places the candidate. The same seed gives the same neighbours and slot for every candidate in a spec, so arms are compared like for like. Try 3-5 seeds before you trust a verdict. |
| `--pos sidebar=0 upnext=3` | Pins the candidate's slot. `--n home=6` sets the number of cards. |
| `--scale 1` | True layout scale: 1 px per CSS px or iOS pt. On a desktop monitor at 100% this is about the angular size of the real phone at reading distance. `--scale 3` gives an iPhone-density screenshot. |
| `--glance` | Also writes `*_glance.jpg`: half size, Gaussian blur of 1.1 px, and a 5 px vertical smear. This approximates a card caught in peripheral vision while the viewer scrolls. A thumbnail that still reads here survives the scroll. |
| `--report` | Prints pop metrics for every fully visible thumbnail as displayed, with the candidate's rank. See "Reading the metrics" below. |
| `--sheet` | Writes one review image, `PREFIX_sheet.jpg`, with the three screens and their glances. |
| `--gate` | Runs `niche/work/gate.py` on each candidate thumbnail. Every final thumbnail must pass it. |

### Outputs per layout

- `PREFIX_<layout>.jpg` is the screen.
- `PREFIX_<layout>_scroll.jpg` (home and upnext) or `PREFIX_sidebar_page.jpg` is the whole page.
- `PREFIX_<layout>.json` holds every card's thumbnail and card rectangles, with the candidate flagged and a `visible` flag. Use the JSON for blind find-it tests and cropping.

## Layouts

Geometry is taken from the 2025-26 apps and is approximate. Every size is in `STYLE` at the top of `feedsim.py` and can be overridden per spec through `"style": {...}`.

### `home`: mobile Home feed

- **Screen:** a 390x844 pt phone with a status bar, the YouTube header and chips row, and a bottom nav.
- **Cards:** each card is a full-bleed 390x219 thumbnail (16:9) with the duration badge 8 pt from the corner.
- **Text:** a 36 pt avatar; the title in Roboto Medium 16/22, clamped at 2 lines with an ellipsis; one meta line ("Channel · views · age", 12/18, #aaa) ellipsized; and a kebab menu.
- **Scroll:** the screen is scrolled to a seeded offset that keeps the candidate's whole card on screen.

### `upnext`: mobile watch page

- **Top of the page:** the player is pinned (390x219, red progress line). Under it come the title (18/24), the views/age line, the channel row with a Subscribe pill, the action pills, the comments teaser and a chips row.
- **Compact list:** 168x94 thumbnails with radius 8 and the badge 4 px from the corner. The title (14/20 Medium) sits to the right and is clamped at 3 lines; the channel and the "views · age" line follow.
- **Caveat:** on many current phone builds, Up next uses full-width cards instead. For that case, read the `home` layout as the phone Suggested surface too.

### `sidebar`: desktop watch page, 1280 px wide

- **Page:** the masthead, an 806x453 player with controls, the title, the channel row and the description box.
- **Right column:** 402 px wide, with chips and then compact cards. Each card has a 168x94 thumbnail, a title at 14/20 Medium clamped at 2 lines, the channel at 12/18, "views • age" at 12/18, and the grey "New" chip for uploads under a week old.
- **Placement:** the screen is the 1280x720 viewport. The candidate is placed in one of the 5 slots above the fold.

### Text and colour details

- **Line breaking:** greedy word wrap with `-webkit-line-clamp` behaviour. The last visible line keeps its words, and characters are trimmed until "…" fits.
- **Missing glyphs:** characters missing from Roboto, such as the ʻokina in Hawaiʻi, fall back to Inter glyph by glyph, as a browser would. Emoji are not supported and render as boxes, so keep them out of specs.
- **Colours:** background #0f0f0f, text #f1f1f1, secondary text #aaa, chips #272727. The badge is black at 70% with 12 px Medium white text.

## Spec format

```json
{ "candidate": {"thumb": "cand_A.jpg", "title": "...", "channel": "Myth Juice", "views": "52 views",
                "age": "1d ago", "duration": "16:40", "avatar": "../ours_avatar.jpg"},
  "candidates": [ ... several arms, one output set each: PREFIX_1_*, PREFIX_2_* ... ],
  "hosts": "../../refs/hosts/hosts.json#hawaii",          // or "#hawaii+hawaii_direct", or a list
  "competitors": [ {thumb, title, channel, views, age, duration, avatar?, watched?, badge?, id?} ],
  "exclude": ["videoId"], "now_playing": "34Ojnyi9xLw", "seed": 2,
  "n": {"home": 6, "upnext": 10, "sidebar": 10}, "pos": {"sidebar": 1}, "style": {"home_title_px": 15} }
```

- **Paths:** relative paths resolve from the spec file. Host thumbnails resolve from `hosts.json`.
- **`watched`** (a value from 0 to 1) draws the red watched bar.
- **`now_playing`** is the host video being watched in `upnext` and `sidebar`. It defaults to the most-viewed host.
- **Text strings:** views and age are drawn exactly as given. Use YouTube's own forms ("7.1M views", "1d ago"). YouTube currently serves the short age form.
- **Template:** `specs/ep02_hawaii_template.json` is ready for ep02. Swap in a `cand_*.jpg` and the title arm under test.

## Competitor sets (`research/packaging/refs/hosts/`, other channels' images: never commit)

`fetch_hosts.py SET ID[::query] ...` reads each video's search-result renderer and saves:

- the title, channel, view count, age and duration;
- the thumbnail (`maxresdefault`, with fallbacks);
- the channel avatar.

These go into `hosts.json`. Watch pages answer HTTP 429 from this sandbox, so the tool does not use them. `fetch_hosts.py --channel @juicytea-l6l ours_avatar.jpg` fetched our own avatar. The candidates were chosen with `ytsearch.py` probes, saved in `probes/`, on 2026-11-08.

### `hawaii`: 12 big Hawaii and drain videos ep02 would be suggested next to

- RealLifeLore, "Why You Can't Travel Between Hawaii's Islands by Boat" (7M)
- Signore Galilei, "Hawaii's Forgotten Islands" (3M)
- Be Smart, "Why No One Can Agree What's REALLY the Tallest Mountain" (3.6M)
- Physics Girl, "Why Hawaii's volcano is so UNUSUAL" (7M)
- Atlas Pro, "The Amazing BIOGEOGRAPHY of Hawaii" (1.4M)
- Park Vibes, "What's Hidden on Hawaii's Forbidden Island?" (1.2M)
- Below The Map, "Hawaii Is Hiding Something Nobody Talks About" (124K)
- Big Island Video News, "Iconic Hawaiʻi Sea Arch Collapses Into Ocean" (2.7M)
- Unseen Works, "What the Pacific Ocean Looks Like Drained?" (120K, 4 days)
- National Geographic, "Deadly Pacific | Drain the Oceans" (10M)
- Contour Atlas, "We Drained the Chesapeake Bay..." (171K)
- Unseen Works, "What Antarctica Looks Like Without Ice" (1.7M)

### `hawaii_direct`: 5 same-premise uploads to mix in

- Bright Side Dark Secrets, "What Hawaii Looks Like Without Water" (9K)
- Shape Of America (3 views)
- WATERLINE (6 views)
- 지구다큐관 (2.2K). Its title is stored as the English auto-translation, the version English viewers see.
- Geo Metrics, "Hawaii Is Hiding Something Nobody Talks About" (77K)

### `ep01`: 12 continent, map and plate-tectonics videos

- Atlas Pro, "What Did Pangaea Look like?" (7.1M)
- History of the Earth, "A Tour of Earth's Ancient Supercontinents" (4.7M)
- PBS Eons, "The Whole Saga of the Supercontinents" (2.5M)
- RealLifeLore, "How the World Map Looks Wildly Different Than You Think" (25M)
- Vox, "Why all world maps are wrong" (23M)
- Map Pack, "Why There is No Bridge Between Europe and Africa" (7.1M)
- SEA, "Before Pangea: The Supercontinents" (1.4M)
- Astrum Earth, "Earth's Newest Ocean Will Split Africa in Two" (1.8M)
- Atlas Pro, "Earth 250 Million Years In The FUTURE" (452K)
- Be Smart, "Why It Took Scientists So Long To Accept This Very Obvious Idea" (964K)
- World Maps Online, "Why Greenland Looks Massive (It's Not)" (4.3M)
- Captain Cipher, "Every Supercontinent That Ever Existed" (534K)

Before the ep02 upload, re-run the probes and `fetch_hosts.py hawaii ...` to refresh the views and ages, and add any new neighbour above 10K.

## Reading the metrics (`--report`)

| Metric | What it measures |
|---|---|
| `luma` | Mean Rec.709 luma (0-255) of the thumbnail as displayed. |
| `p90luma` | The 90th-percentile luma, which tracks the brightest region. |
| `colorful` | The Hasler-Süsstrunk colourfulness index. |
| `brightsat` | The share of bright or saturated pixels (the same definition as gate.py). |
| `edges` | The share of strong-gradient pixels, a clutter proxy. |
| `distinct` | The mean `sim_lib` feature distance to the other visible cards. |

**Caution on `distinct`:** a card can be distinct simply by being darker than its neighbours. In dark mode, that makes it sink into the #0f0f0f page, not pop. Read `distinct` together with `luma` and `p90luma`.

The metrics are proxies. The pass rule in packaging rule P1 still applies: 3 of 3 people find our card in 2 seconds or less, and can read the place name at 168x94, with `gate.py` passing.

## Validation: ep01 (2.27% CTR overall, 1.97% in Suggested)

Files are in `research/packaging/feeds/ep01_*`; `ep01_sheet.jpg` shows all three layouts at once. Ep01's real thumbnail (`thumb_B_pointing_at_what.jpg`) and title sit among the ep01 hosts. The now-playing video is Atlas Pro's Pangaea video, and the seed is 1.

### What the simulator shows

**1. Ep01 is the darkest card on every surface.**

| Surface | Mean luma, ours vs competitor median | p90 luma, ours vs median | brightsat, ours vs median |
|---|---|---|---|
| Home (6 cards) | 61 vs 136, rank 6/6 | 123 vs 213, last | 15% vs 25% |
| Desktop sidebar above the fold (5 cards) | 61 vs 98, rank 5/5 | 123 vs 201, last | 14% vs 22% |
| Up next list (10 cards) | 61 vs 106, rank 10/10 | 123 vs 205, last | 14% vs 22% |

- The neighbours are white relief maps, turquoise seas and bright globes.
- Ours is a navy field (gate.py: 68% blue, 9% red, so **gate FAIL**). It recedes into the dark page.
- Its high `distinct` score (rank 1-2) comes from that darkness, not from pop.

**2. At 168x94 the idea falls apart.**

- "POINTING AT WHAT?" shrinks to letters about 10 px tall.
- The three arrows, the ring and the "?" merge into a small white squiggle at the bottom.
- What remains is "orange continents on a world map". That is the same category of picture as the four Pangaea and supercontinent maps beside it, only darker.
- In the compact glance views (up next and sidebar) the text is gone. Neighbour words such as NEW OCEAN, NOT THAT BIG! and BEFORE PANGAEA still read.

**3. The title spends its second line on a hedge.**

- On desktop it wraps as "Why the Continents Point South / (Not Just a Coincidence)". On Home it breaks after "(Not", and in the up-next list it runs to 3 lines.
- The neighbours name concrete things (Bridge, Europe, Africa, Greenland). World Maps Online's bracket cancels the obvious answer ("(It's Not)") instead of hedging.

**4. The full-width Home card holds up much better.**

- The text box is legible and the orange reads.
- This matches the only surface where ep01 did well (Browse, 8.8% CTR). That surface had just 34 impressions, so treat it as directional only.

**5. Social proof is a gap that packaging cannot close.**

- "43 views · 1d ago" sits next to "7.1M views · 7y ago".
- The desktop "New" chip is ep01's only advantage there.

### Verdict

**Yes, the mechanism is reproduced.** On the compact Suggested surfaces, where 93% of the impressions were, ep01's card is the dimmest, smallest-reading and least specific card in a strip of bright map thumbnails. It is legible only at full width.

The simulator cannot predict the CTR number. It does show why the package lost the comparison in that strip. That is the same diagnosis as packaging rules P1, P4 and P5, now visible on the real neighbours.

## Smoke test

`feeds/smoke_standin_hawaii_*` exist only to exercise the Hawaii set: the ʻokina fallback, long-title ellipsis and the New chips. The candidate there is an old stand-in mock (`niche/work/mock_M3_postcard_basalt.jpg`). **It is not an ep02 candidate. Do not judge packaging from it.**

## Files

- `feedsim.py`: the simulator.
- `fetch_hosts.py`: fetches the host sets.
- `specs/`: `ep01.json` and `ep02_hawaii_template.json`.
- `fonts/`: Roboto Regular, Medium and Bold.
- `probes/`: the `ytsearch.py --json` probe output used to choose the hosts.
- `ours_avatar.jpg`: the Myth Juice channel avatar.
- Outputs go to `research/packaging/feeds/`, and competitor images to `research/packaging/refs/hosts/`. Neither folder is ever committed.
