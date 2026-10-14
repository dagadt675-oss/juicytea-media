# GeoGlobeTales Map Shorts: Production Spec for the Map Engine
Main case: "How America Bought Louisiana" (BmNSUb8HxCA). Benchmarks: Louisiana Purchase (15.4M), Denmark owns Greenland (5.45M), Broadway splits Manhattan (3.65M), Canada lakes (2.98M), plus Märket and Longest vs Shortest flight.
SILENT means the sources don't give the value; choose it yourself and tune against the §8 QA metrics. Where measured [T] values disagree with model-watched ones, use [T].

## 0. Louisiana measured facts
- 1080x1920, 30 fps, 100.90 s; 15,379,281 views.
- 6 hard cuts at 12.13, 25.87, 40.47, 45.97, 53.6 and 58.87 s, none after 58.87; longest shot 42.0 s.
- 52 visual events (pops, zooms, wipes); mean gap 1.90 s, median 1.83 s. Per 10 s window: [5,9,6,4,4,6,3,7,4,4,0].
- Motion mean frame difference 3.80; peaks 13.6 at 25 s, 12.5 at 33 s and 16.6 at 55 s.
- Static holds over 1 s only at 4.13–5.47 and 10.37–11.73 s (character dialogue); 19% of frames near-frozen.
- Speech: 318 words, 3.17 words/s = 190 WPM; 17 sentences, mean 18.7 words, min 2, max 39.
- Loudness −14.5 LUFS, LRA 2.1, TP +0.2 dBTP; music bed throughout, voice about 21.3 dB above it.
- 37 strong SFX hits, 16.7 percussive onsets per 10 s.
- Palette (% of pixels): #5c7e84 38.6, #9f9071 18.3, #2b6a92 13.3, #132a32 12.7, #b92820 5.3, #5b523a 5.1, #c5c9d0 3.6, #be6f23 3.1.

## 1. Louisiana timeline
- 0–2 s: flat parchment map (tan land, slate-blue water, paper grain, hillshade), already moving, NOT a globe. The 1803 US is light blue with white state lines. Two chibi bean diplomats pop in at 0.25 s with a 3D tall ship. VO: "The United States sent two diplomats to France…" (one 33-word sentence, 0–10.64 s). SFX 0.26, 0.74, 1.6.
- 2.0–2.75 s: pan east; the ship crosses the Atlantic.
- About 2.75 s: France fills royal blue with a serif label "France"; chibi Napoleon pops in.
- 3–11 s: a projector screen pulls down; a diplomat points at the New Orleans dot; Napoleon highlights the whole Louisiana territory; jaw drops. Holds at 4.13–5.47 and 10.37–11.73 s. SFX 4.06, 5.94, 6.29, 6.66, 6.92, 8.17 (densest cluster). VO: "…offered to buy just one city, but somehow ended up buying the entire Louisiana territory for almost the same price."
- 11.5–12.2 s: "But let's start from the beginning." Hard cut at 12.13 s.
- 12–19 s: VCR-rewind graphic, big "1802", Jefferson and Napoleon handshake with a sparkle.
- 20–27 s: pan to North America; flat-colour territories; Napoleon thought bubble with expanding arrows; serif italic labels that rotate with the shapes. Hard cut at 25.87 s.
- 27–39 s: darker satellite/bathymetry Caribbean; Haiti in a white translucent fill; 3D money stacks, coffee and sugar drop in; worker icons flood the island. Lines: "It was literally a money-making machine."
- 40–49 s: illustrated cutaway behind a motion-blur whip at 40 s; punch line "Yeah, slavery."; revolution.
- 50–61 s: 3D ships with tricolour sails on curved routes; soldiers turn yellow, get X eyes and fall (yellow fever); Haiti turns green. Motion peak 16.6 at 55 s.
- 60–64 s: Napoleon portrait with a tear. Turn at 60%: "Louisiana suddenly made no sense."
- 65–74 s: one continuous shot to the end. The Mississippi draws on as a glowing blue river; 3D barrels float to a tiny New Orleans model with a French flag.
- 75–86 s: silver 3D "$10M" briefcase; empty wallet with a fly; giant hands swing a baseball bat (Britain) at France.
- 87–91 s: projector callback; briefcase; red "$15M" tag; jaw drops.
- 92–100.9 s: a 3D FOR SALE sign stabs into the map; bench ad "BIG LAND. BIG DISCOUNTS." flips to "SOLD"; the territory turns US teal; gold coin "4¢ / acre". The video stops dead: no outro, no loop.

## 2. Camera
- Snap zoom orbit→subject in 1–1.5 s, eased in and out, never linear.
- Continuous slow drift during every narration line; motion is zero only at holds.
- Whip A→B in ≤0.8 s with motion blur.
- Oblique tilt for terrain, top-down for parchment.
- Follow-cam along drawn paths; pull-back to context after a run of close-ups.
- Title-word pull-back (Broadway): a frame-filling word, a 0.75 s pull-back, the label lands at 1.0 s.
- Change comes mostly from in-shot events and basemap crossfades, not cuts.
- Engine targets: motion mean ≥5; no hold over 1 s unless intentional.
- Easing values: SILENT.

## 3. Visual language
**Base maps:**
- Parchment: water #5c7e84 / #6794a3; land #9f9071 / #b0a98d / #baa08c.
- Satellite+bathymetry: olive #3c3f1e / #4a5036 / #605e39; tan #917b58 / #9a8b6f; deep ocean #0b3d4e / #0d4254 / #132a32; teal #2e6975 / #286479 / #48737a.
- Dark desaturated satellite.
- Light vector: land #d8f1e1.
- Vintage paper overlay crossfaded over satellite.

**Colour rule:**
- A muted base covers 85–95% of pixels.
- One saturated accent per beat, red or cyan.
- Yellow #f7d71e only for numbers and keywords.
- White labels and washes in #cdd0ce–#e0dddd.
- Accents: Louisiana #b92820, Greenland #d2573b, Broadway #bb6151, Canada #8d4228.

**Lines:**
- Thin white borders with stroke draw-on.
- Glowing extruded lines; glowing rivers; cyan grids and lakes.
- Dotted trail that turns into a road.
- Solid land border vs dotted sea border.

**Fills:**
- Glow fill plus a thin white edge; translucent white wash; hatched; textured.
- Dim-others mask; batch glow; recolour animations.
- Target opacity 60–80%.

**Characters, props and symbols:**
- Flag-textured country extrusions.
- One consistent chibi cast; country faces with eyes, brows, mouth and sweat; countryballs with hats.
- Isometric 3D props with soft top-left contact shadows.
- Symbols:
  - Red banned circles.
  - White 3D and hand-drawn arrows.
  - "???" marks.
  - Pulsing red radar circle.
  - Stamps: SOLD, NONSTOP, CANCELLED, prohibited, years.
  - Count-ups.
  - Dashed mi/km measurement bars.
  - Year counters.
  - Scale-anchor cutouts.

## 4. Script
**Louisiana structure:**
- Paradox statement at 0–10.6 s (no question).
- Pivot at 11% ("But let's start from the beginning").
- Dated beats: 1802 → Haiti → gag → revolution → yellow fever.
- Turn at 60%.
- $10M offer, then $15M at 84%.
- Numeric payoff at 97% ("4 cents an acre").

**Pace:**
- 185–195 WPM; median sentence gap 0.70–0.88 s.
- Long sentences of 20–39 words alternate with 1–6 word punch lines.
- One joke every 15–25 s.
- Callback (the projector).

**Template:**
1. Paradox (16–33 words) starting by 0.2 s.
2. Optional reaction.
3. Pivot at 8–13 s.
4. 4–7 dated beats, each opened by a time connector.
5. Complication.
6. "So," or "As a result," as the turn at 60–71%.
7. Big number in the last 15–25%.
8. One-line gag, then end. We loop back into the hook instead.

## 5. Captions and typography
**Their captions:**
- Small, about 2–3% of frame height, regular light sans.
- No box or stroke; at about 70% height; 2–5 words per phrase; no karaoke highlight.
- Often low-contrast. We do better: a stroke or shadow.

**Labels, four styles:**
1. White rounded box with dark text.
2. White bold sans with a soft shadow, rotated along the feature.
3. Serif italic on parchment.
4. Red pin with a white label.

**Emphasis text:**
- Huge white bold with yellow numbers.
- Big dates.
- Red price tags.

## 6. Sound
- A music bed is always present, about 20 dB under the voice. Ducking curve: SILENT.
- Master to −14 LUFS, LRA ≈2, TP ≤ −1 dBTP.
- SFX: 11–17 onsets per 10 s.
  - Whoosh on every zoom, pop on icons, draw, paper, stamp, thud, tick, boing.
  - Foley: pencil, glass, projector.
- Which SFX fires at which onset: SILENT.

## 7. Retention
- A highlight lands by 1–2 s; VO starts at 0.0 s.
- A visual event every 1.4–2.0 s.
- Few cuts.
- A gag every 15–25 s.
- Escalating numbers ($10M → $15M → 4¢).
- Turn at 60–70%.
- Pattern interrupts: a skit with the music cut (Flights), a comedic hold (Märket).
- Expectation subversion: 70K with the K crossed out.
- Their weaknesses: dead or frozen endings, mid-history sag, AI plates, low-contrast captions, Greenland never showing Mercator.

## 8. Engine checklist
- **Camera solver:** snap zoom 1.0–1.5 s with eased moves; auto-frame the bbox at 9:16; whip ≤0.8 s with blur; tilt and follow-cam; minimum drift during speech; lint motion mean ≥5 and holds ≤1 s.
- **Basemaps:** stack with crossfades.
- **Highlights:** glow fill plus edge, wash, hatch, dim-others, recolour, flag extrude.
- **Lines:** animated path trim, solid/dashed/dotted/glow, route props.
- **Labels:** 4 styles, auto-rotate, collision avoidance, pop ≤0.2 s with overshoot.
- **Kinetic text:** dates, count-ups, yellow keywords, price tags, measurement bars, stamps.
- **Props:** 3D library from the hub with contact shadows; scatter with a staggered pop.
- **Characters:** chibi cast and country-face rigs driven by script tags.
- **Events:** scheduler driven by word timestamps, an event every 1.4–2.0 s; lint any 2 s window with no event.
- **Script lint:** see §4; 250–320 words at about 190 WPM; a true seamless loop.
- **Audio:** music bed about 20 dB under the voice; auto SFX per event; −14 LUFS.
- **Captions:** higher-contrast with a stroke or shadow.
- **QA:** re-run these metrics on every render and compare against §0.

## 9. Others
- **Greenland** (80.8 s): globe zoom; Denmark salmon at 2 s, label at 3 s, whip to Greenland at 4 s; Greenland face; "Marketing" gag; 168 WPM; ends on a frozen hold.
- **Broadway** (78.3 s): "Look at Manhattan."; title-word pull-back; cyan grid; Lenape trail follow-cam; highest motion (8.0); 195 WPM.
- **Canada lakes** (66.5 s): list format; red Canada at 1 s; yellow "+2,000,000 lakes" at 2 s; a pin close-up per funny name; event gap 1.41 s; cat-on-keyboard payoff.
- **Märket** (about 98 s): extrusion; borders; magnifier; double snap-zoom; Costco scale anchor; year stamps; 6 s comedic hold; drone AR ending.
- **Flights** (73 s): in-media-res timer hook; NONSTOP stamp; map wraps into a globe; 16 s skit with the music cut; 70K→70; CANCELLED; callback.
