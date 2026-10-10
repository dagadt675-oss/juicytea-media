# Gold Canada Short — measured style

Source: [Part of Canada Is Further South Than Rome?!](https://www.youtube.com/shorts/_DCZ6z5Vkfc) (Myth Juice, 23 s).

The 1080 stream on YouTube would not download from this environment (the player URL returned 403, and the caption track came back empty). The numbers below are from the official 1 fps storyboard, 24 frames at 101×180, plus the colour clusters in those JPEGs. Treat positions as fractions of the frame, not as font pixel sizes. The spoken lines in `specs/canada_rome.yaml` are reconstructed from the title and the geography, not from a transcript.

## Palette

Quantised storyboard colours, most common first:

| role | measured RGB | kit |
| --- | --- | --- |
| ocean / background | 8, 8, 24 and 0, 8, 24 | 8, 10, 26 |
| land | 40, 48, 72 | 40, 50, 74 |
| neon highlight | 224–232, 32, 64–72 | 228, 32, 68 |
| pill paper | 248, 248, 248 | 248, 248, 248 |
| pill ink | red, close to the neon | 196, 20, 52 |

Flat fills only. No shaded relief, no Voronoi.

## Frame

1080×1920, about 30 fps, 23 seconds.

The map is full-bleed. Land reaches the bottom edge on the zoomed shots (the bottom 30% of frames 4–10 is about 99% land colour). Ocean is the same navy as the background, so a wide shot looks like a map floating in navy only because most of it is water.

White pixels, when they are a thin band, sit near y 0.62–0.67. That is the burned-in karaoke. This kit leaves y 0.64–0.72 empty so a caption pass can use it. Titles sit in the top band, and the punchline sits near y 0.40, which is where frames 20–21 put a large white mass (about 8% of the frame, peak at y 0.41).

## What the storyboard actually does

Fractions are neon / land / white inside each tenth of the height.

- 0–1 s. Neon in the upper middle (y 0.2–0.5, about 11–16% of the frame). Land continues underneath. White only in the karaoke band. Neon is spread across the middle, slightly left.
- 2–10 s. The camera has pushed in. Neon fills the top (up to ~80% of the top bands). The bottom is almost solid land. A little white appears around y 0.3 (a pill or a short label) and again at the karaoke line.
- 11–14 s. Still tight. The top band goes as high as 93% neon, so the highlighted country is touching the top edge.
- 15–18 s. Neon drops to zero. Land remains, stronger at the top. This is a different view, not a sway back: the highlight is gone.
- 19 s. Neon returns.
- 20–21 s. White jumps to about 8% of the frame, centred near y 0.41. Punchline type, not a bottom caption.
- 23 s. The layout is close to second 0 again. The film loops.

Camera behaviour that matches those jumps: one opening push-in (span only decreases), then a hold, then a cut when the continent changes. No longitude sway. A shot that reverses direction more than once fails QC, and the sway parameter is gone.

## Kit motion (more alive than the gold film, still clean)

These are element moves, not camera moves:

- Titles and pills scale past 1 and settle, once.
- Pins drop, squash once, and throw three radar ripples that die.
- Lines draw on with a glowing tip, once per beat.
- A highlight brightens once when the beat starts, then holds.
- Numbers count up and pop.
- Stars drift right. Clouds drift right, slower. A soft light band crosses left to right once per beat, and a brighter glint crosses the highlighted country once.
- Small specks keep drifting right on a hold, including when land covers the stars. They skip the caption slot.
- A few sparkles burst on a pin, then they are gone.
- The punchline word scales in and overshoots once. Pills do the same, smaller.

Something small keeps moving (the drift) on a hold. It never reverses.

## Components

`pipeline/style/gold.py` is the default. The map renderer calls it for pills, pins, lines, the highlight pulse, the highlight glint, counters, and the X stamp. The same pills are used on the A320 seat map in `pipeline/style/seatmap.py`.

## Similarity, measured

The 1080 stream was not available (HTTP 403). The comparison is this kit's silent film against the 24-frame storyboard, one frame per second.

Each pixel is labeled ocean, land, neon, or white by nearest measured color. The score is the mean absolute difference of the **land** and **neon** fractions in ten horizontal bands. White is left out of the score: the gold film burns karaoke into about y 0.62–0.67, and this kit leaves y 0.64–0.72 empty on purpose.

Mean band difference over seconds 0–22: **0.110**. Best 0.047 (second 20). Worst 0.187 (second 5).

Honest similarity: **7.5 / 10**. The opening second is close (0.068: neon 0.12 vs 0.13, land 0.16 vs 0.18). The lake hold, the zoom back out, the cut to Rome, and the wide return land in the same parts of the frame. It is not near-identical.

What is still different:

- No burned karaoke. Seconds 20–22 of the gold film are about 12% white. Ours are about 1%, which is the punchline type at y 0.40.
- The tight lake shot is land-heavier (about 0.82 vs about 0.70) and shows almost no water. A wider span adds water and makes the neon layout worse, so the shot stays at span 8.
- Second 5 of the gold film opens up (land about 0.51) and second 6 tightens again (land about 0.73). Copying that would reverse the camera. This film holds.
- Coasts are Natural Earth 50m, decimated, not the gold film's artwork. Rome's land fraction matches (about 0.45). The band layout does not (difference about 0.16).
- The reference is a 101×180 JPEG storyboard, not a 1080 frame.
- The spoken lines are reconstructed. The caption track came back empty.
- Element motion is deliberately busier than the gold film: one scale-in with a single overshoot, a pin drop, three ripples, a drawing line, one glint, and a one-way drift. The camera does not sway. QC recorded 0 direction changes in a shot.
