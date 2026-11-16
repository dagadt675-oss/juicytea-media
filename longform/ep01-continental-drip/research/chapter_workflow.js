export const meta = {
  name: 'build-chapters',
  description: 'Build, independently review and fix chapter scene modules of the long-form video',
  phases: [
    { title: 'Build', detail: 'one builder per chapter writes ep/ep01/chN.js and self-checks stills' },
    { title: 'Review', detail: 'independent visual QA renders its own stills and lists defects' },
    { title: 'Fix', detail: 'builder fixes every defect and re-verifies' },
  ],
}
const A = args
const E = A.engine
const common = (n) => `MODULE: ${n} — see ${E}/www/ep/ep01/modules.json for its t0/t1 (and segment range for split chapters). You are a senior motion designer + graphics engineer on a faceless YouTube documentary channel (Myth Juice). The video (16:9, 1920x1080, 30 fps, ~16 min) is rendered programmatically by our own engine in headless Chromium (software WebGL) — no stock footage. Your work must look like a million-view documentary (RealLifeLore / Atlas Pro / Kurzgesagt level polish), with real animation and humour, never dry.

READ FIRST (binding):
- ${E}/ENGINE.md (engine API + style rules), and skim the sources in ${E}/www/lib/ (globe.js, fx.js, geo.js, shots.js, beats.js, actors.js, cutaway.js, morph.js, equalearth.js) and ${E}/www/ep/ep01/edit.js (chapter module contract).
- The locked script: ${A.script} — your module is ${n} (chapter = the number in its id; for ch5a/ch5b only the segment range listed in modules.json). Every segment has the exact narration ("text", with {m:name} markers), a detailed "visual" plan, "onscreen" texts, "humor" gags and "sfx". Implement the visual plan faithfully; you may simplify a beat only if the engine truly cannot do it, and then pick an equally strong alternative.
- Timing: ${E}/www/ep/ep01/timing.json (absolute word times: words[], segments[], markers{name:{start,end}}) and ${E}/www/ep/ep01/modules.json (your module's t0/t1); chapters.json lists the 6 chapters (a chapter card should open each chapter: ch1 has none at 0:00 — cold open — show the 'chapter question' card at the first chapter boundary of your module only if your module starts a chapter). Use C.T('marker') / C.seg('s0xx') — never hard-code times that should follow the voice.
- Retention/style research: ${A.research}/bench_visual.md and ${A.research}/retention_checklist.md.
- Assets: images in ${E}/www/ep/ep01/img/ (public domain: bacon.jpg portrait 1617, title_1620.jpg Novum Organum title page, bacon_n239.jpg an old Novum Organum page, forster.jpg, snider_1858.jpg before/after Atlantic map, green_n18.jpg Green 1875 'normal form of a continent' figure, green_fig45.jpg Green's tetrahedral-collapse diagrams, green_globes.jpg, bluemarble_northup.jpg and bluemarble_original.jpg (Apollo 17, original = Antarctica on top), cape_agulhas_aster.jpg, india_tip_iss.jpg, tabula_rogeriana.jpg (1154 south-up world map), hereford_mappa.jpg, wegener_portrait.jpg, wegener_last_026.jpg (last photo, Nov 1930), wegener_villumsen_1930.jpg, wegener_exp_013.jpg); 3D models in ${E}/www/models/ (adventurer.glb = our recurring 'Explorer' character, astronaut.glb, mini_male_a.glb); textures/patches/data overlays/paleo data as listed in ENGINE.md; tex/equal_earth.jpg + lib/equalearth.js (Equal Earth flat world map, ee(lon,lat) gives image px; drawEE/eeScreen helpers).
  If you need another public-domain image (NASA/NOAA/USGS/Wikimedia PD), download it into ${E}/www/ep/ep01/img/${n}_*.jpg (Wikimedia: use https://upload.wikimedia.org/wikipedia/commons/thumb/<a>/<ab>/<File>/1920px-<File> with a descriptive User-Agent) and record title/url/license in ${E}/www/ep/ep01/credits_${n}.json. Public domain or CC0 only.

HARD RULES:
- Write ONLY ${E}/www/ep/ep01/${n}.js (plus optional ${E}/www/ep/ep01/${n}_*.js helpers and ${n}_* images). DO NOT edit anything in www/lib, film.html, render.cjs, still.cjs, other chapters, timing.json or chapters.json. If an engine bug blocks you, work around it inside your module and describe it in your report.
- Export: \`export async function build(api, C) { ... return scenesArray }\`. Base scenes (layer 0) must cover EVERY frame of [C.t0, C.t1) with no gaps (only module ch6, the last one, extends past the final word: it must also cover an end-screen tail of ~12 s after the final word with moving visuals and empty space in the right/center area for YouTube end-screen elements).
- Determinism: no Math.random(), no Date, no timers; everything a pure function of time. Load heavy things once (in build or lazily with memoised promises).
- Performance: average render cost must stay under ~650 ms/frame on one job. Avoid ctx.shadowBlur / ctx.filter on large areas; use cached text (F.text), layered strokes. Only one globe overlay texture at a time (re-uploading an overlay every frame is OK only for short paleo time-scrubs).
- Visual cadence: a meaningful visual change every 2–4 s, a cut/mode change every 5–8 s on average; no static hold > 3 s (everything drifts). Vary modes: globe, flat Equal Earth map, archival photo (Ken Burns, framed, graded), data card, Explorer 3D gag, cutaway/morph/paleo where the script asks.
- Text: only the script's onscreen texts (max 2 elements at once, ≤ 7 words each), Barlow Condensed caps pills / Bebas headlines / Inter numbers; legible on a phone; inside a 5 % safe margin; nothing important in the bottom 12 %. NO burned-in subtitles, NO source credits or citations on screen, NO emojis, never mention AI.
- Sync: elements land on their marker (pop 2–4 frames before the word). Register sound effects with api.cue(absoluteTime, name, gainDb) inside build() following each segment's sfx list (names from ENGINE.md).
- Explorer gags: 2–6 s, low-angle, rim-lit, readable silhouette, character large enough (at least ~30 % of frame height), use only the clips listed in ENGINE.md, and make the joke land on the narration.

SELF-CHECK LOOP (mandatory, at least 2 rounds): render stills of your chapter with
  cd ${E} && node still.cjs --page film.html --q '{"ep":"ep01","only":"${n}"}' --frames <comma list> --outdir ${A.out}/${n}/<round>
choosing frames every ~2 s across your chapter plus every marker moment, then build a labelled contact sheet with python (PIL is in ${A.venv}/bin/python) and LOOK at it with the Read tool. Fix anything amateur: empty/black frames, overlapping or clipped text, unreadable labels, wrong geography, misplaced markers, flat lighting, tiny characters, monotony. Finally time 60 frames: node render.cjs --page film.html --q '{"ep":"ep01","only":"${n}"}' --start <F> --frames 60 --out ${A.out}/${n}/speed.mp4 and report ms/frame.`

const REVIEW = {
  type: 'object',
  properties: {
    score: { type: 'number' }, verdict: { type: 'string' },
    issues: { type: 'array', items: { type: 'object', properties: { time: { type: 'number' }, segment: { type: 'string' }, severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['time', 'segment', 'severity', 'problem', 'fix'] } },
  },
  required: ['score', 'verdict', 'issues'],
}

const results = await pipeline(
  A.chapters,
  (n) => agent(`${common(n)}

YOUR TASK (label build-${n}): build module ${n} completely, run the self-check loop, and return a short report: file paths, which segments are implemented and how, known limitations, measured ms/frame.`, { label: `build-${n}`, phase: 'Build' }),
  (rep, n) => agent(`You are an independent, demanding visual QA director for a million-view documentary channel. Module ${n} of our programmatic video was just built (builder report below). Read ${E}/ENGINE.md, the locked script ${A.script} (module ${n}: see modules.json for its time range / segments; narration, visual plan, onscreen, humor), ${E}/www/ep/ep01/timing.json and modules.json.
Render your OWN stills (do not trust the builder's): cd ${E} && node still.cjs --page film.html --q '{"ep":"ep01","only":"${n}"}' --frames <every 1.5 s across the module + every marker + mid-transition frames> --outdir ${A.out}/${n}/qa ; build labelled contact sheets with ${A.venv}/bin/python (PIL) and LOOK at every sheet with the Read tool. Judge against the script's visual plan and the style rules: missing beats, sync to narration, empty or near-empty frames, black frames, text collisions/clipping/legibility (phone + TV), safe margins, wrong geography or labels, static holds > 3 s, monotony, amateur look (flat lighting, tiny characters, jaggy lines, ugly colours), humour gags that don't land, anything that would make a viewer click away. Be specific with timestamps and concrete fixes. Score 0–10.

BUILDER REPORT:
${rep}`, { label: `review-${n}`, phase: 'Review', schema: REVIEW }).then(r => ({ rep, review: r })),
  (x, n) => agent(`${common(n)}

YOUR TASK (label fix-${n}): module ${n} is already built at ${E}/www/ep/ep01/${n}.js. An independent QA director reviewed it. Fix EVERY blocker and major issue and as many minor ones as sensible, then re-run the self-check loop (≥ 2 rounds) and confirm each fix on real stills. Return a short report: what you fixed, what you rejected (and why), remaining known issues, ms/frame.

QA REVIEW (JSON): ${JSON.stringify(x && x.review)}

ORIGINAL BUILDER REPORT: ${x && x.rep}`, { label: `fix-${n}`, phase: 'Fix' }).then(r => ({ n, review: x && x.review, fix: r })),
)
return results
