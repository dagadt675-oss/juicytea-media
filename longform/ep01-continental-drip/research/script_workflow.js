export const meta = {
  name: 'script-forge-drippy-earth',
  description: 'Research facts, draft, multi-lens critique and revise the long-form script for the drippy-Earth video',
  phases: [
    { title: 'Research', detail: '4 parallel fact researchers build the sourced facts ledger' },
    { title: 'Draft', detail: 'head writer drafts the full retention-engineered script' },
    { title: 'Critique', detail: '5 critics: facts, retention, humor/animation, hook+packaging, visual feasibility' },
    { title: 'Revise', detail: 'head writer merges critiques into the final script' },
    { title: 'Red team', detail: 'adversarial fact verification of the final script' },
  ],
}

const A = args
const READ = `Before anything else, READ these files with the Read tool (they are your brief):
- ${A.brief}  (creative brief for the chosen topic, written by the creative director)
- ${A.context}  (production constraints, humor/animation rules, engine capabilities — binding)
- ${A.retention}  (evidence-based retention + subscribe checklist — binding)
- ${A.structure}  (how 1M-view scripts in this niche are structured — blueprint)
Work directory for your notes: ${A.out}/<your-label>/ (create it). Today is 2026-11-04.`

const FACTS = {
  type: 'object',
  properties: {
    facts: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, claim: { type: 'string' }, spoken_form: { type: 'string', description: 'how the narrator should say it (numbers in words)' },
      display: { type: 'string', description: 'on-screen value/label, US units first' },
      source_title: { type: 'string' }, source_url: { type: 'string' }, quote: { type: 'string', description: 'verbatim supporting quote from the source' },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] }, caveat: { type: 'string' },
    }, required: ['id', 'claim', 'spoken_form', 'display', 'source_title', 'source_url', 'quote', 'confidence', 'caveat'] } },
    visual_assets: { type: 'array', items: { type: 'object', properties: { desc: { type: 'string' }, url: { type: 'string' }, license: { type: 'string' } }, required: ['desc', 'url', 'license'] } },
    notes: { type: 'string' },
  },
  required: ['facts', 'visual_assets', 'notes'],
}

const SEG = { type: 'object', properties: {
  id: { type: 'string', description: 's001, s002, ...' }, chapter: { type: 'integer' },
  text: { type: 'string', description: 'exact spoken narration (numbers as words). May contain {m:name} markers right before a word to sync visuals.' },
  pause_after: { type: 'number', description: 'seconds of silence after this segment (0.25-1.2; ~1.0 before big reveals)' },
  visual: { type: 'string', description: 'concrete visual beats for this segment, in order, referencing markers' },
  onscreen: { type: 'array', items: { type: 'string' }, description: 'exact on-screen texts (labels/numbers/cards), max 7 words each' },
  humor: { type: 'string', description: 'comic beat if any (narration joke or Explorer gag), else empty' },
  sfx: { type: 'array', items: { type: 'string' } }, music: { type: 'string', description: 'music mood/change cue if any' },
  fact_ids: { type: 'array', items: { type: 'string' } },
}, required: ['id', 'chapter', 'text', 'pause_after', 'visual', 'onscreen', 'humor', 'sfx', 'music', 'fact_ids'] }

const SCRIPT = {
  type: 'object',
  properties: {
    title_options: { type: 'array', items: { type: 'string' } },
    thumbnail_concepts: { type: 'array', items: { type: 'string' } },
    chapters: { type: 'array', items: { type: 'object', properties: { n: { type: 'integer' }, title: { type: 'string' }, first_segment: { type: 'string' } }, required: ['n', 'title', 'first_segment'] } },
    segments: { type: 'array', items: SEG },
    loop_ledger: { type: 'array', items: { type: 'object', properties: { opened_in: { type: 'string' }, closed_in: { type: 'string' }, loop: { type: 'string' } }, required: ['opened_in', 'closed_in', 'loop'] } },
    word_count: { type: 'integer' },
    notes: { type: 'string' },
  },
  required: ['title_options', 'thumbnail_concepts', 'chapters', 'segments', 'loop_ledger', 'word_count', 'notes'],
}

const CRIT = {
  type: 'object',
  properties: {
    score: { type: 'number', description: '0-10 for your lens' },
    verdict: { type: 'string' },
    issues: { type: 'array', items: { type: 'object', properties: { segment_id: { type: 'string' }, severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['segment_id', 'severity', 'problem', 'fix'] } },
    rewrites: { type: 'array', items: { type: 'object', properties: { segment_id: { type: 'string' }, new_text: { type: 'string' }, why: { type: 'string' } }, required: ['segment_id', 'new_text', 'why'] } },
  },
  required: ['score', 'verdict', 'issues', 'rewrites'],
}

phase('Research')
const TOPICS = [
  { key: 'pattern', q: `THE PATTERN ITSELF + HISTORY OF NOTICING IT: which landmasses really taper/point south (South America, Africa, India, Greenland, Florida, Baja California, Kamchatka, Korea, Scandinavia, Italy, Balkans/Greece, Indochina/Malay Peninsula, Arabia?, Cape York?, Antarctic Peninsula points NORTH), counterexamples (Australia, Antarctica, Eurasia), the famous 'drippy Earth' framing (Vsauce Short, Hank Green Short — titles/dates only), who noticed it historically and EXACTLY what they wrote: Francis Bacon (Novum Organum 1620 — verify the exact quote about Africa and Peru/South America both narrowing toward the south), J.R. Forster (1778), Alexander von Humboldt, James Dwight Dana, others. Get verbatim quotes and page/edition references from primary sources or reliable secondary sources (archive.org, Wikipedia with citations, Geological Society).` },
  { key: 'numbers', q: `THE HARD NUMBERS (compute them yourself where possible): share of Earth's land in the Northern Hemisphere; the "land hemisphere" (centre location, % of land) and "water hemisphere" (centre near Antipodes Islands, NZ; % water); antipodal land: what fraction of land has land exactly opposite (compute with Natural Earth 50m at 0.1° — a reference script exists at ${A.antipode} and Natural Earth GeoJSON at ${A.geo}; you may run python3 with numpy/PIL from ${A.venv}/bin/python), the Arctic Ocean ↔ Antarctica antipodal match (how much of Antarctica sits opposite the Arctic Ocean), the expected value if land were placed randomly (≈29% land coverage → expected 29% of land opposite land; actual ~13–15%), Earth land/ocean percentages, largest antipodal land pairs (Malay Archipelago ↔ Amazon/Andes; Greenland/Canadian Arctic ↔ East Antarctica). Produce precise, reproducible numbers with method notes and the best published citations to cross-check.` },
  { key: 'science', q: `THE REAL SCIENCE (honest, nuanced): why South America, Africa and India taper south — Gondwana breakup geometry (pie-slice/wedge rifting radiating from around Antarctica, Jurassic–Cretaceous timeline), triple junctions, the South Atlantic opening from south to north (zipper), and any specific peer-reviewed paper (incl. a 2022 South Atlantic paper if it exists) explaining continental tapering; Greenland's shape (rifting from North America/Europe, Labrador Sea/Baffin Bay), Baja (Gulf of California opening ~6 Ma), Florida (carbonate platform), Kamchatka/Korea (arc/peninsula tectonics), Scandinavia, Italy. Hemispheric land asymmetry: why ~2/3 of land is north today (Pangaea's breakup position, plate motions; is there evidence for a deep cause like degree-1 mantle convection?). Also: the "Tetrahedral hypothesis" (William Lowthian Green, 1875, 'Vestiges of the Molten Globe'): its exact claims (land/water antipodality, north polar ocean opposite south polar continent, three southward-tapering continents) and why it was abandoned; the satirical "Continental Drip" theory (de Kay 1973; Holden 1976) — exact publication details and what it joked; Wegener (1912/1915) and how shapes (fit of Africa & South America) led to continental drift; Wegener was ridiculed. Real "lithospheric drip" geology (dense crust dripping into the mantle) — does it exist (e.g. Anatolia, Andes, Sierra Nevada) — as a fun true twist. Distinguish solid facts from hypotheses with citations.` },
  { key: 'future-visuals', q: `FUTURE + VISUAL SOURCES + COMEDY MATERIAL: future supercontinent scenarios (Pangaea Proxima/Ultima, Novopangaea, Amasia, Aurica — who proposed, when, timescale; clearly model scenarios), current plate speeds (in inches/year, compared to fingernail growth), how far Africa and South America have separated per year; the convention of north-up maps (history, Stuart McArthur's 1979 'Universal Corrective Map' south-up map; ancient maps oriented differently) — so "pointing south" is real geometry but "dripping DOWN" is just our north-up habit (great humor beat). Find public-domain/CC images we can legally use (with direct URLs + license): Francis Bacon portrait, Wegener portrait/photo, 1858 Snider-Pellegrini map of continents fitting, Lowthian Green's tetrahedron figure (1875 book on archive.org), Cape Horn / Cape Agulhas / Kanyakumari / Cape of Good Hope photos (NASA/Wikimedia PD/CC), NASA Blue Marble photos (Apollo 17). Also collect 6–10 TRUE funny/absurd facts tied to the topic (e.g. the southern tips' nicknames, record winds at Cape Horn, how Cape Agulhas — not Cape of Good Hope — is Africa's real southern tip — a myth-bust!).` },
]
const research = await parallel(TOPICS.map(T => () => agent(`${READ}

YOUR JOB (label: research-${T.key}): build the sourced facts ledger for this part of the video. Use WebSearch/WebFetch heavily (load via ToolSearch). Prefer primary sources (papers, archive.org scans, agency pages); record a verbatim supporting quote for every fact. Mark confidence honestly; give caveats. 15–30 facts. Topic:
${T.q}`, { label: 'research-' + T.key, phase: 'Research', schema: FACTS })))

const ledger = []
research.filter(Boolean).forEach((r, i) => (r.facts || []).forEach((f, j) => ledger.push({ ...f, id: `${TOPICS[i].key}-${j + 1}` })))
const assets = research.filter(Boolean).flatMap(r => r.visual_assets || [])
const researchNotes = research.filter(Boolean).map((r, i) => `## ${TOPICS[i].key}\n${r.notes}`).join('\n\n')
log(`facts ledger: ${ledger.length} facts, ${assets.length} visual assets`)

phase('Draft')
const writerPrompt = (extra) => `${READ}

You are the HEAD WRITER of a 1M-view faceless documentary channel. Write the COMPLETE narration script for this video as structured segments.
Requirements (all binding): follow the creative brief's topic/angle; obey every hard rule in the constraints file; engineer retention per the checklist and blueprint (cold open that works as a standalone Short, promise by 0:30, first payoff < 2:00, jaw-drop ~3:00, re-hooks every 2–3 min, stair-step escalation, honest myth-check beats, biggest payoff last, cliffhanger bridge to Part 2, subscribe ask after first big payoff + over end screen, a one-word comment prompt); include humor (witty lines + 6–10 Explorer animation gags using ONLY the available clips) so it's never dry; every factual sentence must cite fact_ids from the ledger (do not state anything not in the ledger; if you need a fact that is missing, write the claim cautiously and flag it in notes). Spoken text: numbers as words, short punchy sentences, conversational US English, no jargon without instant explanation, vary sentence length for rhythm; place {m:name} markers before words where visuals must land (e.g. "{m:india}India"). 2,250–2,500 words total. Segments of 1–4 sentences (each will be voiced separately), ~60–110 segments. Visual beats must be concrete and achievable with the engine (see constraints). Provide 6 title options (≤55 chars) and 3 thumbnail concepts (≤3 words + one striking visual), chapters titled as questions.
${extra}

FACTS LEDGER (JSON):
${JSON.stringify(ledger)}

RESEARCH NOTES:
${researchNotes}

AVAILABLE VISUAL ASSETS:
${JSON.stringify(assets)}`

const draft = await agent(writerPrompt(''), { label: 'writer-draft', phase: 'Draft', schema: SCRIPT })
log(`draft: ${draft ? draft.segments.length : 0} segments, ${draft ? draft.word_count : 0} words`)

phase('Critique')
const LENSES = [
  { key: 'facts', p: 'FACT-CHECKER (adversarial): check EVERY factual sentence against the ledger and, where doubtful, against the web. Flag anything overstated, unsourced, mis-hedged, or myth-busting that is itself a myth. Numbers must match sources exactly. Provide corrected text.' },
  { key: 'retention', p: 'RETENTION AUDITOR: simulate a skeptical 25-year-old US viewer and a curious 14-year-old watching at TV size. Second-by-second "boring-second audit": find any 10-s stretch without new info or new visual, any slow setup, any loop opened but not closed (verify the loop ledger), any segment where the viewer would click away, weak re-hooks, a payoff that disappoints, signals of ending. Estimate a retention curve (0:30, 1:00, 3:00, 50%, end). Provide concrete rewrites that fix the dips.' },
  { key: 'humor', p: 'COMEDY PUNCH-UP WRITER + ANIMATION DIRECTOR: make it genuinely funny without cringe, in the dry-witty documentary register (think Half as Interesting / Kurzgesagt jokes). Check every Explorer gag: does it use only available clips, is it 2–6 s, does it land on the narration, does it support the point? Add or replace gags so there is a laugh roughly every 60–90 s. Provide rewritten lines.' },
  { key: 'hook', p: 'HOOK + PACKAGING SPECIALIST: rewrite/tighten the first 60 seconds word by word for maximum 30-s retention (myth stated as viewer believes it → visual refutation → stakes → promise). Check title/thumbnail ↔ opening alignment (thumbnail image visible by 0:05, title claim proven by 1:00). Improve the title options and thumbnail concepts using honest psychological levers (curiosity gap, negativity words, scale contrast). Check the subscribe asks and comment prompt wording.' },
  { key: 'visual', p: 'VISUAL DIRECTOR: check every segment\'s visual beats against the engine capabilities. Flag impossible/vague beats and rewrite them concretely; make sure a visual change happens every 3–5 s and a full scene change every 20–40 s; vary modes (globe, data card, photo, diorama with the Explorer, chapter card) so 13+ minutes never feel monotonous; propose on-screen texts (≤7 words).' },
]
const critiques = await parallel(LENSES.map(L => () => agent(`${READ}

You are a critic with ONE lens. ${L.p}
Be specific: reference segment ids; give a fix for every issue and full replacement text where useful. Score 0–10 for your lens.

FACTS LEDGER: ${JSON.stringify(ledger)}

DRAFT SCRIPT (JSON): ${JSON.stringify(draft)}`, { label: 'critic-' + L.key, phase: 'Critique', schema: CRIT })))
critiques.forEach((c, i) => c && log(`${LENSES[i].key}: ${c.score}/10 — ${c.issues.length} issues`))

phase('Revise')
const final = await agent(writerPrompt(`
This is the REVISION pass. Below is your draft and five critiques. Produce the FINAL script: apply every blocker and major fix, adopt the best rewrites (you may improve them further), keep it coherent and within 2,250–2,500 words. In notes, list which critique items you rejected and why.

YOUR DRAFT: ${JSON.stringify(draft)}

CRITIQUES: ${JSON.stringify(critiques.map((c, i) => ({ lens: LENSES[i].key, ...(c || {}) })))}`), { label: 'writer-final', phase: 'Revise', schema: SCRIPT })

phase('Red team')
const RT = { type: 'object', properties: {
  problems: { type: 'array', items: { type: 'object', properties: { segment_id: { type: 'string' }, claim: { type: 'string' }, problem: { type: 'string' }, corrected_text: { type: 'string' }, evidence_url: { type: 'string' } }, required: ['segment_id', 'claim', 'problem', 'corrected_text', 'evidence_url'] } },
  ok_count: { type: 'integer' }, notes: { type: 'string' },
}, required: ['problems', 'ok_count', 'notes'] }
const redteam = await agent(`${READ}

You are an adversarial fact-checker. Try to REFUTE every factual claim in this FINAL script (default to flagging when uncertain). Verify against the cited ledger facts and independently on the web (load WebSearch/WebFetch via ToolSearch). Check numbers, dates, names, quotes, superlatives, and that hedges are honest. Return only real problems with corrected narration text.

LEDGER: ${JSON.stringify(ledger)}

FINAL SCRIPT: ${JSON.stringify(final)}`, { label: 'redteam', phase: 'Red team', schema: RT })

return { final, redteam, ledger, assets, critiques: critiques.map((c, i) => ({ lens: LENSES[i].key, score: c && c.score, verdict: c && c.verdict })) }
