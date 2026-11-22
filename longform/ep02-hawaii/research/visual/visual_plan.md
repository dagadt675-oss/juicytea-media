# Myth Juice ep02 look book: "One Earth"

Art direction for long-form #2. Written 2026-11-08 from the ep01 visual audit (12 findings), the benchmark of breakout channels, the engine tech scout, four working prototypes (globe, drain/terrain, type, story) and a three-person review panel (a teen on a phone, a TV viewer who watches RealLifeLore, a motion director). Where those sources disagree, section 9 gives the decision and the reason.

Evidence at a glance: `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/visual/before_after_all.jpg` (10 before/after rows, phone size at 1:1 on the right).

Two numbers explain why this matters. On ep01, mobile viewers (44% of views) left after 2:11 (14% retention), while computer and TV viewers stayed past 50%. 74% of ep01's frames were at least 45% near-black, and the film's mean luma was about 40/255. Benchmark channels sit at 80-166. Ep01 was a big-screen film. Ep02 is built for the phone first, and the big screen still benefits.

---

## 0. The look in one paragraph

Everything happens on one photoreal Earth, lit by one sun and finished by one colour grade. The default camera is low, tilted and full-bleed: terrain and coastlines fill the frame, the horizon and a blue haze sit in the top 15-25%, and the subject fills at least half the frame height. The whole globe in black space is a 2-4 s establishing beat, not the base. Change happens live on a fixed camera: the sea drains, a shape lifts off and lands, a counter rolls, and the variable shows in a persistent gauge. People enter as real public-domain photos cut out like paper, standing on and hopping across the real map; that is where the comedy lives. Text is huge, one idea at a time, at most 4 headline words, and drawn after the grade so it is never softened. If a frame does not read at 390 px wide, it does not ship.

---

## 1. One visual language

### 1.1 One world, three stages, one finishing pipeline
Every frame is built in three layers, in this order:

1. **WORLD:** one of three stages (below), plus fills that must follow the relief.
2. **POST (shared):** filmic tonemap with a highlight shoulder, one grade (navy blacks, cool shadows, slightly warm highlights), bloom (threshold about 0.8), vignette 0.2-0.3, light sharpening, grain and colour fringing near zero until the compression test passes (U5).
3. **UI (crisp, never post-processed):** text, plates, outlines, arrows, gauge, pins.

| Stage | What it is | Engine | Prototype |
|---|---|---|---|
| CineGlobe | Photoreal globe: real clouds, haze, golden terminator, glint, DOF, 2x supersampling | `lab/globe/cineglobe.js` (same API as `lib/globe.js`) | `lab_globe.html` |
| TerrainStage | Real ETOPO/SRTM terrain and seafloor mesh, live water level, baked soft shadows and AO, curved hazy horizon | `lab/drain/terrain.js` | `lab_drain.html` |
| Archive in the World | Public-domain photos cut out as paper cards, in front of the globe or standing on the map | `lab/story/story.js` | `lab_story.html` |

All three stages must run through the same POST pass and the same UI system. That is the direct fix for YouTube's "corridor scene clashed" critique. Right now each prototype has its own grade and its own fonts (panel issue X3, section 8), so unifying them is upgrade U1/U2.

### 1.2 Palette (final)
| Role | Colour | Rule |
|---|---|---|
| Hero (the subject) | `#FF5A36` | One hero shape per frame. Fill at 55-66% so relief shows through, a 5-6 px white outline and a soft glow. Never 100% opaque. Over ice, use a deeper variant (ovMul 1) so it does not turn salmon. |
| Water / "the other side" | `#3DE3FF` | Water fills (soft edge at the open-sea limit, crisp at coasts), routes, the second colour in overlap reveals. |
| Numbers, arrows, counted things | `#FFD23F` | Odometer numbers, arrows, people pictograms, the gauge. |
| Text | `#F4F6FA` | All words. **No grey text** (`#9AA7B8` is retired for on-screen text). |
| Plates | `rgba(6,9,15,0.86)` / `#0B1D28` at 85% | Rectangular plate with an 8 px accent bar in the colour of the thing it names. |
| Space | Navy gradient `#0B1D28` to `#05070D` | Never flat black. On obliques, a sky gradient above the horizon (deep blue to pale haze). |
| Red `#E8412C` | Danger, borders, routes in conflict | Sparingly. |

Mood comes from light and weather (dusk, a storm front, low sun), never from black frames.

### 1.3 Type (final)
- **Anton** for headlines and numbers. Its heavy stems survive the 0.2x phone downscale and YouTube's re-encode better than Bebas.
- **Barlow Condensed 800**, caps, tracking 0.04, for labels, kickers, name plates, gauge titles and list tags.
- Retired from on-screen text: Bebas Neue (the drain gauge and story quotes migrate to Anton), Inter-as-numbers, Playfair, Special Elite, and pill-shaped labels.
- The API is `lab/type/type.js` (`T.txt`, `T.stack`, `T.label`, `T.slot`, `T.people`, `T.tag`, `T.line`, `T.outline`, `T.arrow`, `T.pin`, `T.scrim`, `T.navySpace`, `T.QC`). Sizes are set by **cap height**; `T.init` measures the ratios (Anton 0.86, Barlow Condensed 0.70).

### 1.4 Brand devices (what makes a frame recognisably Myth Juice in the Suggested feed)
1. The hero-orange highlight on real imagery, in the praised antipode style: semi-transparent fill, glow and a crisp white outline.
2. The orange accent bar on every plate.
3. The **Juice Check** verdict stamp, used for verdicts only.
4. The persistent gauge in the top-left corner (sea level, ice, depth, year: one variable per film).
5. Paper people with a warm off-white paper edge.

---

## 2. Phone-first rules (numbers)

The phone player in an upright phone is about 390 px wide, which is **0.203x** of 1920x1080. Every size below is a cap height at 1080p.

| Rule | 1080p | % of frame height | On the phone | Check |
|---|---|---|---|---|
| Key number (counter, big stat) | Anton cap 150-190 px | 14-18% | about 30-39 px | QC log |
| Headline | Anton cap 96-120 px | 9-11% | about 20-24 px | QC log |
| Must-read label (place, name plate, gauge title) | Barlow 800 cap **64 px** (font about 91 px) | **5.9%** | about 13 px | QC fail if < 64 on a must-read role |
| Kicker / connector words (NEARLY, MOST OF, MODEL) | Barlow 800 cap 48 px | 4.4% | about 10 px | **Absolute floor for any text.** QC fails below 48 |
| Gauge | Plate 12-15% of frame height, number cap 110-120 px | 10-11% | about 22 px | fixed top-left corner |

**Words**
- Headline: at most 4 words.
- Kicker: at most 2 words.
- Kicker + headline: at most 6 words.
- Label: at most 3 words.
- A number carries its unit plus at most 2 words.
- **Never drop a qualifier to save words** ("MOST OF", "NEARLY", "ABOUT" go in the kicker). This is a no-false-claims rule, not a style rule.

**Elements on screen**
- At most one text block (kicker + headline, or a number block), plus at most one map label, plus the persistent gauge or list tag.
- At most 10 visible words in total.
- No text over text. No legends: coloured headline words are the legend.

**Placement**
- Everything sits inside a 5% title-safe margin.
- Must-read text stays in the **top 62%** of the frame (above y = 670), clear of the mobile player controls. Nothing important goes in the bottom 12%.
- The text block goes in the third opposite the subject.

**Contrast**
- White text sits on an 86% plate (contrast above 12:1), or is unplated with a dark stroke of 0.13 x cap height over a 50-60% side scrim.
- Colour words must reach at least 4.5:1 at headline size. Orange on navy measures 5.5:1; cyan and yellow on navy are above 10:1.
- On bright terrain or sky, always use a plate. A scrim alone fails there (panel note on the type prototype).

**Subject size**
- The subject fills **at least 50-70% of frame height**.
- Story globes fill 100% of frame height or more, with the limb cropped.
- A highlighted shape must measure **at least 25 px on the 390 px phone frame** (about 120 px at 1080p). If it does not, move the camera closer. Ep01's Florida was 6-8 px on a phone.

**Lines**
- Meaningful lines: 9-12 px core, plus a dark under-stroke 8 px wider, plus glow.
- Arrows: 15 px body, 50-63 px head, moving highlight dashes.
- Outlines: 5-6 px white. Pins: r ≥ 11 px with a pulse.
- Nothing meaningful thinner than 6 px. Lines draw on with a head dot.

**Brightness** (measured with `audit_scripts/metrics.py` / `scripts/lum.py` on 96x54 frames)
- Each shot's mean luma is at least 70 on oblique, terrain and story shots.
- The film's mean luma is 85-130.
- Near-black pixels (luma below 18) make up at most 15% of the whole film.
- A shot above 35% near-black must be an establishing globe or a night-lights beat. Those two together get at most 10% of runtime.
- No run longer than 4 s below mean luma 40.

**Cadence**
- First minute: a visual event every 2-3 s. After that, every 3-5 s.
- Hard cuts or mode changes average **4-4.5 s**, and 4 s or less in minute 1.
- Any single composition lasts at most 7 s. The exception is a live drain or flood shot, which may run up to 10 s while the level and camera move the whole time.
- Shot scale changes (wide, then regional, then ground) every 5-7 s, and the subject alternates between the left and right thirds.
- The visual mode changes every 20-40 s. Nothing is fully static for more than 2 s.

**Budgets**
- Whole globe in space: at most 10% of runtime, at most 4 s per shot.
- Archival still: at most 3 s, never two in a row in the first 3 minutes.
- Paper people: at most 1-1.5 min per film.
- Subscribe or CTA graphics: none before the last 20 s.

**QC gate (every render)**
1. Per-frame `[typeqc]` log. Fail on: cap below 48 px; a must-read role below 64 px; more than one text block; a headline over 4 words.
2. A phone sheet of every shot's middle frame at 390x219, reviewed by eye for smudges, blown whites, clipped fills, seams, text over text and invisible highlights.
3. The brightness metrics above, run on the whole film at 5 fps.
4. A seam and hairline check (high-pass) on new textures and overlays.
5. Before any new shot type is used in the film, a 10-15 s motion test encoded at upload settings and watched on a real phone.

---

## 3. Runtime mix target (ep02, about 16 min)

| Mode | Share | Note |
|---|---|---|
| S3 Hero oblique / regional (CineGlobe) | 30% | The default camera |
| S4 Ground: terrain stage (drain, flood, peel, cross-section) | 20-25% | More if the topic is a drain or flood story |
| S2 / S6 / S7 / S9 Story globe with graphics | 15-20% | Overlap reveals, true-size drags, model beats |
| S1 / S5 Establishing globe and dusk lights | at most 10% | Openers and transitions |
| S10 / S11 Paper people | 6-10% | Human beats only |
| S12 Real PD photo or footage, full-bleed | 5-10% | At most 3 s per still, 5 s per clip |

Tilted full-bleed modes (S3 + S4 + S11 + S12) must add up to **60% or more** of runtime. Number blocks and the stamp are overlays on top of these modes, not modes of their own.

---

## 4. Shot types and how to make each one

Paths are relative to `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/visual_lab/engine/www/` unless shown in full. Render any lab page with `node still.cjs --page <page> --frames ... --outdir ...` from `visual_lab/engine`.

### S1 ESTABLISH globe (at most 4 s, openers and transitions only)
- **Recipe:** CineGlobe, fov 22, alt 3.85 so the globe overfills the frame height, `sun:'world'` with the terminator near one limb, clouds 0.6, cloud drift `0.04*t`, haze 0.2-0.3, `post({dof:0})`.
- **Prototype:** `lab_globe.html` `{shot:'atlantic', mode:'after'}`.
- **Caution:** at clouds 0.62 this frame reads the map *worse* on a phone than ep01 did (panel). It is a mood shot, never the shot that carries a map fact.

### S2 STORY globe (when the map itself is the point)
- **Recipe:** the CineGlobe STORY preset (to build, U4):
  - clouds 0-0.35 and never over the subject continent;
  - clouds thinned with noise around the subject, not cut out as an elliptical hole;
  - terminator off the disc or on the limb;
  - haze 0.2 and exposure +0.5 stop;
  - alt 1.5-1.9 with lookOffset -0.12 to -0.3, so the globe fills the frame height on one side;
  - the text block in the opposite third over a 50-60% scrim.
- **Overlays:** fill drawn in the globe texture at 55-66% so the relief shows, but masked out of bloom and DOF. The white outline is drawn in the UI layer, so the edges stay as crisp as the praised 2:40 shot.
- **Prototype:** `lab_type.html` shots A and C (currently on the old `globe.js`) plus `lab/globe/cineglobe.js`. Helpers in `lab/type/shots.js`: `ringMask`/`fillRings` (pole-closing fills), `blurInto`, `fadeLat`, and OVB padded bounds of ±181.5° until the shader seam is fixed.
- **Layout:** rotate between 3-4 layouts (U11): text top-centre over the sky on obliques; a bottom-left plate on bright terrain; a full-frame number card; label only. The same left-third layout in every shot becomes a template (panel).

### S3 HERO OBLIQUE: the default camera
- **Recipe:**
  - CineGlobe, fov 26, alt about 0.36 (range 0.12-0.5), tilt 55-58 (range 35-60).
  - Horizon 15-25% from the top of the frame.
  - Sun elevation about 30 as side light.
  - Clear-weather zone over the subject (noise-broken).
  - `post({dof:6-8, contrast:1.12})`, haze 0.24.
  - A slow push of 1.5-3% per 10 s plus heading drift.
- **Below alt 0.5:** load a 500 m GIBS patch (`lab/story/tools/gibs_patch.py LON0 LAT0 LON1 LAT1 out.jpg`, or the engine's `gibs.py`).
- **Above the horizon:** a sky gradient, never stars. Clouds and the limb stay out of DOF (fix U4).
- **Prototype:** `lab_globe.html` `{shot:'froward'}` (luma 43 to 89, near-black 23% to 0%). `lab_story.html` scene B shows the same camera over Europe with a patch and sky gradient.

### S4 GROUND: terrain stage (drain, flood, peel, time slider)
- **Recipe:**
  - `TerrainStage` from `lab/drain/terrain.js`: `S.setCamera({lon, lat, alt km, heading, pitch, fov})`, `S.setLevel(m)`, `ctx.drawImage(S.render(t, seed), 0, 0)`, then the UI.
  - Camera at 20-60 km, pitch -12 to -20 degrees, horizon 15-25% from the top.
  - **Vertical exaggeration 2x** (1.5x below 30 km; 3x only above 60 km). Narrate "heights exaggerated" once.
  - Sun 15-25 degrees high, three-quarter front-side, for long shadows. Target mean luma 95-120 *with* real dark shadows, not a milky wash.
- **One camera, the variable changes:** the level moves live for 4-10 s while the gauge rolls with ticks and a riser or rumble plays.
- **Data per location:**
  - `lab/drain/tools/fetch_drain_data.sh` (ETOPO 2022 15" + Terrarium z10 + BMNG 500 m pan-sharpened with clear MODIS 250 m) and `terrain_bake.py` (shadows and AO, about 50 s): 3-5 min and 25-30 MB per location.
  - `sill.py` flood-fill **gates every "land bridge", "lake" or "island" label** (Gibraltar disconnects below -287 m in the data).
- **Prototype:** `lab_drain.html` (16 s timeline: 0, -350, -1,100 m). Before/after: luma 73 to 119-143, near-black 2.5% to 0%.
- **Not yet good enough (panel, U6):**
  - spiky "crumpled-foil" relief at 3x;
  - soft foreground drape;
  - a seabed that looks like dunes or snow;
  - flat milky grade;
  - swimming-pool shallows;
  - an oversized label.
- **To build:** a land-bridge close-up kit (U17) that pushes in on the crest, draws an orange crest line and adds a data callout.

### S5 DUSK / city-lights beat (at most 4 s, only when the lights are the point)
- **Recipe:** CineGlobe with the world sun and the terminator through mid-frame, bloom 0.26, glint suppressed for sun elevation below 3 degrees, city lights ramped across civil twilight (so Italy does not vanish), and a navy earthshine rim on the night disc.
- **Prototype:** `lab_globe.html` `{shot:'dusk'}`.

### S6 OVERLAP REVEAL (the praised antipode device; the house template for any "A vs B" claim)
- **Recipe:**
  - Fixed camera. The shape lifts off, flies and lands.
  - The **target region gets the cyan fill (35-40%)**. The **moving shape gets a white outline plus a 35-45% orange fill**, so the overlap reads as a third colour (yellow).
  - The headline's coloured words are the legend.
  - Animate the flip (for example Antarctica over the pole).
- **Prototype:** `lab_type.html` shot B shows the *wrong* way. Its 66% salmon fill sits on top of the cyan and hides the overlap, and its headline dropped "MOST OF". Rebuild it before reuse (blocker B1).

### S7 TRUE-SIZE DRAG over the USA (a recurring device)
- **Recipe:** ep01 `geo.js` `moves` on a STORY globe: a drag whoosh, then `impact_deep` when the shape lands. Use a STORY or regional camera so the shape is at least 25 px on a phone.

### S8 NUMBER block and persistent GAUGE
- `T.slot` odometer: Anton cap 150-190, yellow, landing on the spoken word with `tick_counter`.
- `T.people(ctx, x, y, n, k)` for "N in 10": warm yellow dots, sized by population, never grey.
- The gauge (`T.gauge`, U8) is generalised from the drain's SEA LEVEL plate: fixed top-left, plate 12-15% of frame height, a moving level bar, an impact cue on milestones, and the same position across every mode for the whole chapter.

### S9 LIST / MODEL beat
- `T.tag('MODEL', i, n, x, y)` with progress pips ("2 of 4") and one headline.
- Each list item gets its own full-frame tilted shot joined by a whip-pan: 1-1.5 s per item for quick lists, 4-7 s for explained items. **Never grids or thumbnail mosaics.**
- **Prototype:** `lab_type.html` shot C. Fixes: split it into two beats so the Antarctica arrow is not cropped, and raise the Pacific tint to a clear 35-40% cyan.

### S10 PAPER PEOPLE A: cut-out in front of the globe (at most 3-4 s)
- **Recipe:**
  - `story.js` `prepCard` and `drawCard`. The person sits in the left third at 60% or more of frame height and slides in with an overshoot. The globe behind pushes slower than the card, for parallax.
  - The globe behind is a STORY globe **framed so the claim is visible**. For "pointed toward the south": lat about -15, alt about 2.2, with South America and Africa whole and their tips pointing down the frame.
  - Arrows to spec, starting exactly at the capes.
  - Quote at headline size (Anton cap 96-120, at most 4 words). Name plate at label size.
- **Assets:**
  - `lab/story/tools/cutout.py` (MODNet, 25 MB: download, use, delete), then `card.py --h 900 --edge 9 [--bw] [--close 21]`.
  - New rule (U9): remove colour spill from the edges, erode 2-3 px, use a **warm off-white paper edge of 2-4 px** (no blue rim) and a soft offset shadow.
- **Prototype:** `lab_story.html` scene A (Bacon). Rated "needs rework": the continents cannot be seen pointing south, there is red spill, and there is a blue stroke.

### S11 PAPER PEOPLE B: standee on the map (the comedy engine, 3-6 s)
- **Recipe:**
  - `story.js` `standee(ctx, globe, card, {lat, lon, h, hinge, squash, lean})` on a HERO OBLIQUE with a sky gradient and tilt-shift.
  - The standee is **35-40% of frame height** and gets a fold-out paper base tab, so the straight crop of a bust photo makes sense.
  - Soft short contact shadow plus a blurred directional shadow. No slab.
  - The pop-up hinge starts at 30-40 degrees.
  - The hop arc follows the camera, squashes and overshoots on landing with a dust puff, and **lands on the true coordinates** (`standee()` returns `{x, y, top, w, h}`; anchor the name plate to the base).
  - Cues: paper flap, whoosh on the hop, `thunk_heavy` or `impact_short` on landing.
- **Prototype:** `lab_story.html` scene B (Wegener, Hamburg to Graz). The teen rated it 8/10: "genuinely funny and readable".

### S12 REAL PHOTO / PD footage (at most 3 s per still, at most 5 s per clip)
- **Recipe:** full-bleed, shared grade, Ken Burns of 1.5-3% per 10 s.
- Documents are cropped to 5 big words or fewer. Never mock documents. No credits on screen (the description carries them).
- A "living photo" 2.5D template is planned (U20, after ep02).

### S13 VERDICT STAMP (Juice Check)
- **Recipe:** a 1-1.5 s stamp with the `stamp` cue, laid over the moving world shot. Used for verdicts only, never as a subscribe ask.

### S14 TRANSITIONS
- **Whip-pan:** 6-8 frames with sub-frame motion blur (U14).
- **Globe-to-terrain match-cut:** the same lat/lon/heading, a short fade and a sound sweetener (U7, not built).
- **Zoom from space to place:** log-altitude over 3-5 s, tilt from 0 to 35-45 degrees on arrival.

### S15 END (last 20 s only)
- The end-screen layout starts only when the last VO word ends.
- The background keeps moving: a slow push on the final place.
- The hold lasts 10-12 s. No empty boxes, no film strips.

### Comedy inside the world
- **Where the humour comes from:**
  - paper physics: pop-up, hop, squash, wobble, a fall-over;
  - map objects that behave physically: a drain plug, a shape that slams down with an impact, a true-size drag that "doesn't fit";
  - comic camera: a whip-pan to the punchline, a crash zoom;
  - a sound gag on the VO word.
- **Timing:** each gag lasts 2-4 s. Comedic sound effects are used only on gags.
- **Honesty:** scale gags stay obviously playful and nothing staged is passed off as real. Every gag is real animation, never a still with a funny line under it.

---

## 5. What we stop doing (from ep01)

| Stop | Ep01 evidence |
|---|---|
| A small centred globe in black as the default shot | 74% of frames ≥ 45% near-black; 79% in the first 131 s; 13:27-14:17 |
| 26-38 px labels, grey secondary text, legends, "SIMPLIFIED" sub-lines (say it in the VO instead) | 0:20, 0:25, 2:20, 3:02, 3:12 legend, 5:20, 10:00, 15:11 |
| Static portraits, Latin or book pages, mock "papers" with grey dash bars | 0:57-1:16, 1:40-2:12, 11:40 |
| On-screen citations or author-year names | 11:40 "DIETZ & HOLDEN (1970)" |
| Low-poly characters in gradient voids, Kenney block kids, flat-vector interiors, pinboards, flat cartoon cutaway Earth, cream paleo discs, the film-strip recap | 2:21, 5:25-5:53, 6:20, 7:00, 7:35-7:50, 9:20-10:20, 14:59 |
| 4-way split screens, ghosted texture backgrounds, night-side globes without a reason | 0:54, 4:50-5:06, 13:27-14:17 |
| Mid-film subscribe graphics, early end cards, a 19.8 s uncut end hold | 5:00-5:07, 15:15-15:34 |
| Grids, thumbnail mosaics, overlapping translucent pins | 11:00-11:20, 12:00 |
| 1-5 px lines and arrows | 0:05, 3:40, 13:30-14:00 |
| Render defects: the camera-sun specular smudge, additive blob sprites, blurred dark smears as text plates, clipped rectangular fills, headlines over page text | 0:00, 1:18-1:24, 10:00, 12:00, 5:08 |
| Pill labels and Bebas; fully opaque hero fills | the whole film; the story prototype's 100% fills too |
| One look per scene ("12 visual languages in 15 minutes") | full_grid20s sheets |
| Two lossy JPEG/x264 steps at 6.6 Mbps, 4:2:0 | the ep01 master |

---

## 6. Prioritised upgrade list (impact x effort)

Status: **P** = prototyped in the lab, **Part** = partly prototyped, **No** = not built yet. Effort is in focused hours. Nothing has been merged into the production engine yet; all prototypes live in the sandbox `visual_lab/engine`.

### Tier 0: the foundation (before any ep02 scene is built). About 19-27 h.
| ID | Upgrade | Impact | Effort | Status | Done when |
|---|---|---|---|---|---|
| U1 | Split every frame into WORLD, then POST, then UI in `film.html` (a scene `ui(ctx, lt)` hook, or layer ≥ 50 drawn after post). Add a `Q.draft` flag (ss 1, samples 0, post off). | High | 3-4 h | Part (each lab page does this on its own) | Text is never vignetted, bloomed or blurred in any stage |
| U2 | Promote `lab/type/type.js` to `lib/type.js`. Swap `F.pill`, `F.headline` and `F.counter` for `T.*` (keep the old functions as deprecated). **Unify all prototypes:** Anton plus Barlow 800, rectangular plates, 55-66% fills, one arrow spec. Move the drain gauge and story quotes onto it. | High | 4-6 h | P (panel: ADOPT) | One type system across globe, terrain and story |
| U3 | QC gate: `render.cjs` fails on `[typeqc] FAIL`; a phone sheet of every shot's middle frame (`visual_lab/type_tools/sheet.py`); brightness metrics; a seam check | High | 3-4 h | Part | A render cannot pass with sub-floor text or a hidden highlight |
| U4 | Adopt CineGlobe (`lab/globe/cineglobe.js` to `lib/`, `clouds_8k.jpg` to `tex/`) with **two presets, STORY and HERO**. Composite fills and outlines outside bloom and DOF. Keep clouds and the limb out of DOF. Steps are in the cineglobe.js header (do not pass LOOK0; make `post` a no-op). | High | 6-10 h | P (panel: more work) | The Atlantic story frame reads faster on a phone than ep01's |
| U5 | Motion tests: 10-15 s of each stage, encoded at 1440p CRF 14-16 and watched on a phone. Plus a 300-frame L4 timing run per stage. | High (risk) | 3 h + GPU | No | Grain and fringing settings signed off; real L4 ms per frame known |

### Tier 1: must have for ep02. About 34-50 h.
| ID | Upgrade | Impact | Effort | Status | Done when |
|---|---|---|---|---|---|
| U6 | Terrain stage to production: `api.terrain(key, dir)`; bbox and seed CLI arguments for `terrain_bake.py` and `sill.py`; 2x exaggeration; a 30 m normal map in the foreground; mipmapped heights; relight (low three-quarter sun, contrast 1.15); a seabed material pass (depth colours, darker canyons, a former-shoreline line, salt only in the last basin, softened shadow blotches); deeper water and surf; runs through the shared POST | Very high | 12-18 h | P (panel: more work; teen 8/10) | The drained frame reads as Earth, not a game; motion test passes |
| U7 | Globe-to-terrain match-cut (same lat/lon/heading, fade, sound) | High | 6-8 h | No | No visible seam between the two stages |
| U8 | `T.gauge` as a lib primitive, plus chapter or list tags, with tick SFX | High | 2-3 h | Part (drain gauge, `T.tag`) | One gauge across all modes |
| U9 | Paper people fixes: matte clean-up, base tab, soft shadows, hinge start, exact landing, the Bacon-style reframe, shared grade on cards, `api.drawStandee` / `api.drawCutout` | Medium-high | 5-7 h | P (panel: more work) | Template B standard; template A re-approved |
| U10 | Globe defects: the Antilles swath seam (fill from the adjacent day), the sea-ice ring, noise-based clear zone, a shallow-shelf tone control (about -40% saturation, teal-green), the meridian hairline, the overlay `fract()` seam, the pole dot | Medium | 4-6 h | Part | High-pass QC is clean on the cloud map and overlays |
| U11 | Layout variants plus an auto-layout helper (free third from the subject's projected bounding box; a label-on-line placer with collision avoidance) | Medium | 3-4 h | No | 3-4 layouts in rotation, no hand placement |
| U12 | Encoding: frame JPEG at 0.98 or raw RGBA on the GPU, CRF 14-16, a 1440p master | Medium | 1-2 h | No | Grain and gradients survive the YouTube re-encode |
| U13 | Sound cues for the new devices: drain riser and rumble, paper flap, hop whoosh, landing thunk, gauge ticks | Medium | 1-2 h | No (the library has most of them) | Every device has its cue |

### Tier 2: strong if time allows. About 26-38 h.
| ID | Upgrade | Impact | Effort | Status |
|---|---|---|---|---|
| U14 | Motion blur from sub-frame accumulation on flagged fast frames (N = 6-8, 180-degree shutter, into the HDR target, before the UI) | Medium | 4-5 h | No |
| U15 | Sharper close-ups: 2-3 patch slots with cross-fades, `normal_8k`, a 16k base on the GPU, a 30 m HLS/Landsat drape in the terrain foreground | Medium | 6-10 h | Part (a single 500 m patch) |
| U16 | Terrain sky life: sparse cumulus with shadows, glint on the remaining water | Medium | 4-6 h | No |
| U17 | Land-bridge / sill close-up kit (crest line, data callout from `sill.py`) | Medium (depends on topic) | 2-3 h | No |
| U18 | Scale props at true scale (landmark, surveyor pole) with a height counter | Medium | 6-8 h | No |
| U19 | Terrain cross-section "cake cut" | Medium | 4-6 h | No |

### Tier 3: after ep02
- U20: Living-photo 2.5D template. Needs a general matting model; BiRefNet does not fit the disk now.
- U21: Per-basin water levels and a refill waterfall.
- U22: One recurring 3D character on terrain, only if a test passes the phone QC.
- U23: A precomputed-scattering atmosphere. The cheap analytic rim currently looks better.

**Order of work:** U1, U2, U3, then U4 and U6 in parallel, then U5 motion tests on both, then U7 and U8, then everything else as the script needs it. Do not build scenes on the old `globe.js` or the old `fx.js` labels.

---

## 7. Render cost (Colab L4 GPU)

| Item | Local (SwiftShader, 4 cores) | L4 (estimate, **not measured**) |
|---|---|---|
| Ep01 baseline | 0.36 s per frame | about 71 ms per frame (mostly JPEG encode and transfer); a 16-min film in about 15 min |
| CineGlobe at 2x SS | 2.7 s (globe), 3.5 s (oblique with DOF); 2.0 s draft at 1x | +30-60% per globe frame; +70 MB GPU memory for the 4K half-float target |
| TerrainStage (about 3M triangles, 3 passes) | 4.6 s with 4x MSAA; 2.0 s draft | under 100 ms render per frame; a 16 s drain shot is about 1 min |
| Type / UI layer | 0-5 ms per frame (cached sprites) | negligible |
| Paper people | about 1.0 s per frame including the globe | under 10 ms per frame extra |
| Motion blur N = 6 on about 15% of frames | prohibitive, so previews stay at N = 1 | about 1.3x total |

- **Whole-film estimate:** about 25-35 min on the L4 for a 16-min ep02, against 15 min for ep01. U5 replaces this guess with a 300-frame measurement per stage before the schedule is fixed.
- **Per-location terrain cost:** 1-2 min fetch, about 50 s bake, 25-30 MB of data. Six to ten locations come to 200-300 MB, which lives on Colab or Drive, **not on the local disk** (about 3.5 GB free). Re-bake if the sun direction changes.
- **GPU memory per terrain location:** about 16 MB of R16F heights plus 2 x 32 MB of RGBA light and colour textures. Fine on an L4.
- **Local rules:**
  - Draft flag only, stills and phone sheets only.
  - Motion tests under 30 MB each, deleted after review.
  - Never a full-film render locally.
  - Delete raw downloads after each bake (the prototypes deleted 113 MB of DEM data and the 25 MB MODNet model).
- **Masters:** CRF 14-16 at 1440p gives a much larger master than ep01's 6.6 Mbps (a rough guess is 2-3 GB for 16 min). Keep it on Drive and bring only a 720p preview local.
- **Upload:** 2560x1440 so YouTube serves its higher-bitrate encode. Keep grain at about 0.02 or lower until the compression test passes.

---

## 8. Open issues from the review panel

### Blockers: these must be fixed before the device is used (facts and owner rules)
| # | Issue | Fix |
|---|---|---|
| B1 | Type shot B: the headline "ANTARCTICA IS OPPOSITE THE ARCTIC OCEAN" dropped "MOST OF" and overclaims; the 66% fill sits on top of the cyan and hides the overlap that *is* the claim | Put "MOST OF" in the kicker (or show the share as a number). Arctic Ocean as the cyan fill, Antarctica as a white outline with a 35-45% fill, overlap as a third colour, animated flip |
| B2 | Drain: the label "ALBORAN SEA" sits on the leftover -1,100 m lake, which is the West Alboran Basin | Label it "WEST ALBORAN BASIN" or name it only in the VO. Every land-bridge, lake or island label is gated by `sill.py` |
| B3 | Drain: 3x exaggeration is not stated, and a thought-experiment drain could read as history | Say "heights exaggerated" once and frame the drain as "if we drained it" in the VO |
| B4 | Story B: the hop ends at the card's corner on the Czech-Austrian border, not at Graz | Land the anchor point on Graz's projected coordinates |

### Quality issues by prototype
**Globe (verdict: more work; panel scores went from 4-5 before to 6-7.5 after)**
- The Atlantic story globe at clouds 0.62 reads the map worse than ep01 on a phone, and Florida is a 6-8 px smear. Fix: the two presets (U4).
- The hero overlay is softened by bloom, DOF and tonemap. Fix: composite it outside post.
- There is a swath seam east of the Lesser Antilles, and the sea-ice ring is only faded. Fix: U10.
- The terminator over Iberia looks like a beige filter, not golden light.
- On Froward, the clear zone is an obvious ellipse, the foreground clouds are mushy, DOF on clouds and limb looks like a miniature, the sky is foggy grey, and stars blurred by DOF look like dust on the lens.
- The shelf is electric cyan, and a hairline seam on the shelf is present in both before and after.
- The Froward subject marker is about 4 px on a phone. Fix: use a label plus a pin to spec.
- Dusk: the glint looks like land, Italy is lost in the twilight band, and the night half disappears (49% near-black).
- Nothing has been checked in motion or after compression.

**Drain / terrain (verdict: more work; teen 3 to 8, TV viewer 5 to 7, motion director 4 to 6)**
- The relief looks like crumpled foil at 3x, the foreground drape is soft with stretched texels and ink-blot shadows, and the seabed reads as dunes or snow.
- The land bridge at -350 m is a sliver of a few pixels. It needs its own shot (U17).
- The grade is flat and milky: no clouds, no glint, no modelled water. The shallows look like a swimming pool, with no surf line.
- The UI is oversized for a TV: the pill is 40% of the frame width over the horizon, and the "M" unit is tiny. Use type-system plates (label cap 64) placed beside the horizon.
- There are no landmarks (Rock of Gibraltar, Tangier) for scale.
- The style clashes with CineGlobe (Bebas pills, different grade).
- It has not been seen moving, and the waterline and height-texture shimmer are untested.

**Type (verdict: ADOPT; teen 2 to 8)**
- Shot A: the population dots read as grey dust, the equator sits too low for the dimmed south to show, and the EQUATOR plate covers dots.
- Shot C: the Pacific tint is too faint and the Antarctica arrow is cropped.
- Every shot uses the same left-third layout and the look is a generic explainer kit. Fix: U11 plus the brand devices in 1.4.
- It is untested on CineGlobe clouds and on bright terrain.
- The mid-roll odometer digit is clipped for a frame. Check it at 30 fps.
- The pole dot and the salmon colour over ice remain.

**Story (verdict: more work; teen 3 to 7, TV viewer 4 to 6.5, motion director 3 to 5.5)**
- Bacon frame: the claim is not visible (the continents are slivers), 60% of the frame is dark ocean (luma 50), the arrows float and are under spec, there is red matte spill and a blue rim stroke, and the face is softer than the type.
- The fills are 100% opaque, which breaks the 55-66% rule.
- The Wegener shadow is a slab, the card has no thickness, and the pop-up smears for its first 0.2 s.
- The paper collage plus tilt-shift risks becoming a second visual language. Budget: 1-1.5 min per film, always on the CineGlobe or terrain base, with the shared grade.
- The comedy timing has not been judged at 30 fps with sound.

### Cross-cutting
- X1: All four prototypes were reviewed as stills only. U5 is the gate.
- X2: L4 cost is estimated, not measured. U5 measures it.
- X3: The prototypes use different fonts, plates, fill opacities and grades. U1 and U2 unify them.
- X4: The type system has not been tested over CineGlobe or terrain.
- X5: Nothing is in the production engine yet. The integration risks are the LOOK0 and `ambient`/`exposure` semantics, the paleo `flatBase` path, and per-frame `refreshOverlay` (CineGlobe remaining work #4).

---

## 9. Decisions where the sources disagreed

| Topic | Options on the table | Decision | Why |
|---|---|---|---|
| Label floor | 54 px (benchmark), 56-64 (scout), 64 (audit, type prototype) | 64 px cap for must-read text, 48 px for connectors | Proven readable at 390 px in the type prototype; the teen scored it 8/10 |
| Headline font | Bebas (ep01's surviving headlines, drain, story) or Anton (type prototype) | Anton only | Heavier stems survive the downscale and compression; the panel asked for one font |
| Characters | Low-poly diorama mode for 20-30% of runtime (benchmark); one higher-fidelity rig (audit); paper people (story prototype) | Paper people for ep02, at most 1-1.5 min; no low-poly characters | Real PD photos keep it honest and in-world; the Wegener hop was the panel's funniest frame; the low-poly look was ep01's weakest |
| Frame background | Daylight sky base (benchmark) or navy space (CineGlobe) | Sky gradient on obliques and terrain; a navy gradient (never black) only on whole-globe shots | Fits both, with brightness targets enforced by QC |
| Brightness target | 70-110 (audit) or 90-140 (benchmark) | Shots ≥ 70; film mean 85-130; ≤ 15% near-black | Allows dusk and establishing beats without returning to ep01's 40 |
| Longest hold | 8 s (audit), 7 s (benchmark), 3 s static (ENGINE) | 7 s per composition (10 s for a live drain); nothing static over 2 s | A live drain is a continuous event; static frames are what lose phone viewers |
| Vertical exaggeration | 2-3x (scout), 3x (prototype), 1.5-2x (panel) | 2x by default, depending on altitude | 3x looked like game terrain to the TV viewer and the motion director |
| Hero fill opacity | 100% (story), 66% (type), 55-66% (panel) | 55-66% plus a 5-6 px white outline | Matches the praised antipode style; the relief stays visible |
| Clouds on story globes | 0.6-0.8 (CineGlobe recipe) or none (ep01) | STORY 0-0.35, never over the subject; HERO 0.6 for at most 10% of globe time | The panel found the Atlantic map harder to read with a full cloud deck |

---

## 10. File index (reuse these)

The sandbox engine root is `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/visual_lab/engine/` (tools `still.cjs`, `render.cjs`; pages in `www/`).

- **Globe:** `www/lab/globe/cineglobe.js`, `www/lab/globe/clouds_8k.jpg` (7 MB), `www/lab_globe.html` (`q = {shot: atlantic|froward|dusk, mode: before|after, ss}`). Cloud rebuild: `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/visual_lab/scripts_globe/clouds.py` (+ `gibs_level.py`).
- **Terrain:** `www/lab/drain/terrain.js` (`TerrainStage`), `www/lab_drain.html`, `www/lab_drain_before.html`, data in `www/lab/drain/data/` (26 MB, Gibraltar), tools in `www/lab/drain/tools/` (`fetch_drain_data.sh`, `gibs_bbox.py`, `terrain_bake.py`, `sill.py`, `sheets.py`).
- **Type:** `www/lab/type/type.js`, `www/lab/type/shots.js`, `www/lab_type.html` (`q {"shot":"B"}`), plus sheets in `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/visual_lab/type_tools/` (`sheet.py`, `strip.py`).
- **Story:** `www/lab/story/story.js`, `www/lab/story/edit.js`, `www/lab_story.html`, tools in `www/lab/story/tools/` (`cutout.py`, `card.py`, `gibs_patch.py`), cards in `www/lab/story/img/`.
- **Metrics:** `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/visual/audit_scripts/metrics.py`, `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/visual/scripts/lum.py`.
- **Evidence sheets:** `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/visual/before_after_all.jpg` (all pairs; built by `scripts/before_after_all.py`), and the per-prototype `compare.jpg` in `research/visual/proto_globe/`, `proto_drain/`, `proto_type/` and `proto_story/`. Also `proto_type/style_card.jpg` (every type role at real size), `proto_type/anim_strip.jpg`, `proto_drain/sequence.jpg` and `proto_story/motion_strip.jpg`.
- **Audit sheets:** `research/visual/audit/sheets/curated_phone_fails.jpg` and `curated_phone_premium.jpg`.
