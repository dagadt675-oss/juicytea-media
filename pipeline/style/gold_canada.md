# Gold Canada Short — measured from the 1080 file

Source file: the channel's 23.06 s Short, 1080×1920, 30 fps, H.264 plus AAC. 690 frames. The YouTube page is [Part of Canada Is Further South Than Rome?!](https://www.youtube.com/shorts/_DCZ6z5Vkfc) (Myth Juice). The picture spends most of its time on Chicago and California, then crosses to Rome.

Numbers below are from that file, one frame per second (`fps=1`, so frame `t` is second `t`). Karaoke text is OCR of the lower band. Colours are medians of the pixels in each role.

## Palette

| role | RGB | hex |
| --- | --- | --- |
| ocean / background | 8, 8, 24 | `#080818` |
| land | 40, 48, 72 and 32, 32, 56 | `#283048` / `#202038` |
| Canada highlight | 232, 34, 71 | `#E82247` |
| latitude line and stressed karaoke | 254, 212, 10 | `#FED40A` |
| karaoke white | 255, 255, 255 | `#FFFFFF` |
| Italy highlight | 5, 174, 224 | `#05AEE0` |
| California-border pill | 200, 29, 159 | `#C81D9F` |
| California fill | about 213, 120, 15 | kept at 200, 112, 18 so it stays off the orange text mask |
| Atlantic pill | 3, 89, 169 | `#0359A9` |

Flat fills. A faint graticule sits on the field. Country coasts are a light gray-blue, about 168, 184, 204. No shaded relief.

## Frame and karaoke

The map is full-bleed. Land and ocean run to the edges.

Karaoke is one line, bottom-center, white with a black outline. The stressed word is `#FED40A`. On a settled card the ink box is about y **0.619–0.672**, about **102 px** tall including the outline (the yellow core is about 80 px). It is centered, and a short card such as "OF ROME" spans about x 0.33–0.67. A long card such as "NORTHERN BORDER" spans about x 0.13–0.87.

This kit does not burn that line. The pipeline still reserves y 0.64–0.72 so a caption pass can. The gold text starts a little higher, at 0.619.

## Timing

Each row is the karaoke at that second. The camera holds inside a group.

| t | karaoke | picture |
| --- | --- | --- |
| 0 | WAIT... | Wide North America, Canada in red. Ocean about 0.63, red about 0.12. |
| 1 | FURTHER SOUTH | Same view, pushed in. Ocean about 0.51, red about 0.17. |
| 2 | THAN CHICAGO?! | Great Lakes. White CHICAGO pill, a face over Ontario. |
| 3 | MIDDLE ISLAND | Tight on Lake Erie. Red pill, white 3-ring reticle. |
| 4 | A TINY DOT | Same hold. "46 ACRES · POPULATION 0", blue USA pill. |
| 5 | IN LAKE ERIE | Same hold, plus a red CANADA pill. |
| 6 | SOUTHERNMOST | Yellow "CANADA'S SOUTHERNMOST POINT". |
| 7 | POINT OF CANADA | Yellow "41.68°N" pill near y 0.10. |
| 8 | A LINE WEST | The yellow parallel draws across 41.68°N. |
| 9 | IT'S SOUTH | Line held. |
| 10 | OF CHICAGO | White pill "CHICAGO 41.88°N" on the line. |
| 11 | CALIFORNIA'S | Wider US. California in orange. Purple "CALIFORNIA BORDER = 42°N". Yellow line at 42°N, about y 0.41, across about 93% of the width. |
| 12 | NORTHERN BORDER | Hold. |
| 13 | NOW GO EAST | Hold. |
| 14–15 | THE ATLANTIC | Cut east. Red is gone. Blue "ATLANTIC OCEAN". The 41.68°N line is still there. |
| 16 | OF ROME | Italy. White "ROME 41.90°N". No cyan yet. |
| 17 | ROME, | Italy fills with cyan, about 0.24 of the frame, ocean about 0.49. |
| 18 | ITALY! | Hold. |
| 19 | SOMEONE SAYS | Cut back to the wide continent. Snow specks. |
| 20 | ALL SNOW | Snow. White specks reach about 0.03 of the frame, and the big type is extra. |
| 21 | AND POLAR BEARS | Snow. |
| 22 | JUST SAY... | Wide again, Canada red returns. Layout is close to second 0. |

The opening move is a push: from t=0 to t=1 the ocean share falls and the red share rises, with no cut. The Erie arrival is in by t=3. The jump to the US-wide frame is between t=10 and t=11. The Atlantic and Italy views are cuts (the red mass disappears, then cyan appears). The snow section cuts back west. Nothing in that list reverses inside a shot.

## Devices

- **Pill.** Fully rounded. White fill with black type (CHICAGO, ROME 41.90°N). Red fill `#E82247` with white type (MIDDLE ISLAND, CANADA). Yellow fill `#FED40A` with black type (41.68°N, CANADA'S SOUTHERNMOST POINT, CALIFORNIA). Purple fill with white type. Blue fill with white type (USA, ATLANTIC OCEAN).
- **Pin.** White dot. On Middle Island, three standing white rings plus a short white stem. The rings are already drawn by t=3 and they hold.
- **Latitude line.** Solid `#FED40A`, about 6 px at 1080, with round ends. It draws on once ("A LINE WEST") and then stays. It sits near mid-frame on the lake shots (about y 0.50) and near y 0.41 on the US-wide shots. It does not cross the karaoke line.
- **Highlight.** Canada is `#E82247` until the Atlantic cut. Italy is `#05AEE0` from t=17. California is a separate orange fill on the US-wide beats.
- **Snow.** From t=19, small white specks over the whole frame, falling.
- **Face.** One beat (t=2), over Ontario, the mind-blown reaction. The kit draws a simple face there.
- **Top title.** This Short does not use one. The words are the karaoke line. The title-band component still exists for other films.

## What the 50m map cannot match

Natural Earth 50m fills Lake Erie with the Canada polygon, and Middle Island is not a ring. The kit cuts simplified Great Lakes back to navy so the tight shot has water. The Ontario shore is still thicker than the gold frame, so the tight shot carries more red (about 0.27 of the frame versus about 0.12). US state lines are not in the country file. The California shape is a drawn outline, not a state polygon.

## Similarity

Scored against the 1080 file, not the storyboard. Each pixel is labeled ocean, land, red, or cyan by nearest measured colour. The score is the mean absolute difference of the land, red, and cyan shares across ten horizontal bands. White and yellow are left out, because those are the karaoke we do not burn.

Mean over seconds 0–22: **0.094**. Best 0.040 (second 19, the wide return). Worst 0.168 (second 3, the tight lake). Italy at seconds 17–18 is cyan 0.25 against the gold's 0.25–0.27.

Honest similarity: **7.5 / 10**. The palette, the full-bleed frame, the Italy zoom, the wide return, and the US-wide colour split are close. It is not near-identical. The tight lake is redder than the gold frame, the karaoke line is absent on purpose, there are no state borders, and the reaction face is drawn rather than the emoji.
