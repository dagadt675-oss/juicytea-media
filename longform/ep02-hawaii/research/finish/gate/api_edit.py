import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
R = [
("  stage: { origin, midGrid },     // optional stage options (one stage per region + vex + options; reuse the same object across shots)",
 "  stage: { origin, midGrid, noDetail, stack },   // optional stage options (one stage per region + vex + options; reuse the same object\n"
 "                                  // across shots); noDetail: true leaves out the region's close-up detail patch (wide shots: cheaper)"),
("Every uniform is reset from `TERRAIN_DEFAULTS` + preset + state on every frame, so shots on one stage never leak into each other.",
 "Every uniform is reset from `TERRAIN_DEFAULTS` + preset + state on every frame, so shots on one stage never leak into each other. Only keys present in `TERRAIN_DEFAULTS.set` are reset: a new per-shot uniform gets its default there too (`foamW`, `steepAmt` since 2026-11-22)."),
("Frame 1 is unchanged (SSIM 0.942 vs 0.943 against the label-free thumbnail). Stills: scratch `research/ep02/closeup/shader/`.",
 "Frame 1 is unchanged (SSIM 0.942 vs 0.943 against the label-free thumbnail). Stills: scratch `research/ep02/closeup/shader/`.\n\n"
 "Round 3 (2026-11-22; on with the film's `crisp` 1, each with a per-shot off switch in `set`): (1) water: the shore rim's width reads the depth gradient of the finest layer (continuous), not `fwidth` of the bilinear depth, so the stepped cyan rings offshore are gone (ch2 5097); the shore foam band is capped at `foamW` metres of the bottom's drop (default 40; `foamW: 0` = the old band), so shallow reef flats no longer turn white in wavy stripes (ch4 10290/10320 reef heads, ch5 13160 Midway flats); the pixel foam term and the edge glow are unchanged. (2) Steep faces: `steepAmt` (default 1, 0 = off; scaled by `detAmt`) adds a biplanar rock and plant pass on near faces of displayed slope about 0.9-1.8 where the photo is coarser than the pixel (Pali lookout, sea cliffs; `dbg: 8` shows its weight); mid-distance faces whose photo already resolves keep the photo. (3) Mesh: with `crisp` on, each terrain quad takes the diagonal nearer the bicubic surface at its centre (no zigzag ridge lines; the water mesh is untouched). (4) A region's `patch.grid: [nx, ny]` sets its detail patch's mesh (`oahu_windward` [640, 504]: Oʻahu shots about 21 % cheaper), and `stage.noDetail` / `{\"noPatch\":1}` really drop the patch (before, it stayed in the stack as a full layer). Frame 1 on the promoted code: SSIM320 @F1@ against the label-free thumbnail. Gate stills: scratch `research/ep02/finish/gate/`."),
("nothing to set (HawaiiStage `o.noDetail` skips it; shared.js does not pass it, so every shot gets the patch).",
 "nothing to set; a shot's `stage: { noDetail: true }` leaves it out (its own cached stage: for wide shots where the patch only costs GPU time, as in ch1's cold open and ice shot and ch4's Maui leg), `{\"noPatch\":1}` leaves every patch out (before stills)."),
("Draw blocks first |",
 "Draw blocks first. The plate opens with its text (type.js `label` `sync`): never an empty plate |"),
("`minus`, `lead0: false`, `win` (the window digits roll inside) |",
 "`minus`, `lead0: false` (leading zeros hidden completely: a hidden digit appears only as its 1 rolls in, its comma and the minus follow at that moment, never a faint 0), `win` (the window digits roll inside) |"),
]
for a, b in R:
    n = s.count(a)
    if n != 1: sys.exit(f'EDIT NOT UNIQUE ({n}): {a[:70]}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok', len(R))
