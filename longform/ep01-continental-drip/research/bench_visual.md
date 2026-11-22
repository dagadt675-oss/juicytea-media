# Visual grammar of million-view geography long-form videos, translated into our production rules

## 1. Benchmark (10 storyboards, about 1 frame every 10 s, all contact sheets viewed)

Contact sheets and thumbnails are in `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/bench-visual/sb/` (`sheet_<ID>.jpg`) and `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/bench-visual/th/thumbs.jpg`. The metric script is `/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/bench-visual-scripts/metrics.py`.

| Video | Views | Length | Avg. time between visual changes* | Visual mix (estimated by eye) |
|---|---|---|---|---|
| RealLifeLore, *Why 95% of Australia is Empty* | 14.7M | 31m | 5.5 s | tilted satellite maps 45%, drone stock footage 40%, public-domain (PD) engravings 10% |
| Atlas Pro, *Geography of the Ice Age* (no host on screen) | 6.0M | 15m | 4.7 s | elevation-coloured relief maps 80%, photos 15%, charts 5% |
| Atlas Pro, *Earth with WAY More Water* | 1.1M | 21m | 4.1 s | 3D globe 45%, host 25%, photos 15%, paper maps and cross-section blocks 15% |
| Map Pack, *50 Geography Facts That Are Fake* (no host) | 2.5M | 30m | 5.0 s | one flat satellite world map 85%, flag-textured fills and line icons, photos 8%, globe 5% |
| Kurzgesagt, *The Deep Sea* | 25.8M | 11m | 4.0 s | 100% vector illustration, depth counter and ruler |
| Johnny Harris, *ocean "dark zones"* | 5.9M | 31m | 3.9 s | host 45%, footage 30%, glowing data-dot maps on navy 20% |
| Wendover, *How Florida Got So Weird* | 4.2M | 21m | 2.6 s | footage and archival 65%, satellite maps 20%, newspapers and vintage maps 10% |
| Scary Interesting, *Most Dangerous Ocean Crossing* | 3.5M (8 weeks) | 27m | 6.1 s | PD paintings and archival 55%, cream paper maps with red routes 20%, ocean footage 20% |
| Scary Interesting, *Texas Tower 4* | 2.4M | 16m | 5.0 s | grainy archival 60%, blueprint line drawings 15%, maps 5% |
| Sideprojects, *50 Most Mysterious Places* | 1.3M | 123m | 5.3 s | host 50%, stock footage 40%, big numbered chapter cards |

*This is estimated from the share of consecutive storyboard frames that changed significantly (a statistical estimate, not a true cut count). In every video, 80–98% of 10-second intervals contained a change. In the first 60 seconds it was 83–100%.

## 2. What the winners share

1. **Nothing is ever static.** The median is about 5 s per visual change. Map-heavy videos hold a shot for 4–5.5 s because labels, highlights and camera moves keep happening inside it. Footage-heavy videos cut faster (Wendover 2.6 s).
2. **One base-map look carries 40–85% of the runtime.** Each channel has a single map style it returns to:
   - RealLifeLore: black ocean, darkened satellite land, one orange-red glowing country.
   - Atlas Pro: elevation-coloured relief with shaded water depth.
   - Map Pack: a flat satellite map.
   - Scary Interesting: cream paper with red routes.
3. **Highlighting works one way everywhere.** The target is filled with a saturated colour and an outer glow, with a thin white outline. Everything else is dimmed.
4. **On-screen text is sparse.** It is limited to place labels (caps, small pill or leader line), numbers (heights, areas, depths, years), segment headers (Map Pack's "FACT 37 – OTTAWA, CANADA") and numbered chapter cards. **None of the 10 videos burn in subtitles.**
5. **Scale comparisons follow a few patterns:**
   - Drag a true-shape outline over the viewer's home turf (RealLifeLore puts Australia over the USA at 0:29).
   - Side-by-side shapes with square-mile labels (Map Pack: Madagascar vs Britain, Greenland vs Africa).
   - Height diagrams with numbers (Everest).
   - A live depth counter plus a vertical ruler (Kurzgesagt, "10,929 m").
6. **Motion graphics live inside the map:**
   - curved migration arcs
   - cyan ocean-current arrows
   - a dashed route ending in a red skull (Scary Interesting thumbnail)
   - pulse markers
   - glowing data-dot densities (Johnny Harris)
7. **Inserts are graded to match the map.** Archival material is turned sepia or teal with grain, placed in rounded photo-print frames with drop shadows, or shown as newspaper headlines, documents and blueprints.
8. **The first 30 seconds follow a pattern:**
   - The first frame is never a title. It is a moving establishing shot (aerial or map).
   - The subject is highlighted by about 10 s.
   - A scale comparison or a shocking number arrives by about 30 s.
   - The title sting comes at 0:34–1:08, or there is none at all.
9. **Thumbnails** use one map or globe hero with a single saturated highlight, a yellow arrow or circle, and 4 words or fewer ("YOU'VE BEEN LIED TO", "WHY EVERYBODY LIVES IN RED"). Some use no text: a dark globe with a red route and a skull.

**Proof that our setup can work:** Atlas Pro's Ice Age video (6M views, about 80% elevation maps), Map Pack (2.5M, about 85% one flat map) and Scary Interesting (PD art plus paper maps) are all faceless and could be produced programmatically. The footage share in RealLifeLore and Wendover we replace with NASA/NOAA public-domain video (ISS time-lapses, NASA SVS visualisations, NOAA Ocean Exploration footage) and Ken Burns moves on PD photos.

## 3. Production style guide for our video

### Format
- 1920x1080 at 30 fps.
- Render raw RGB frames and pipe them to ffmpeg: `-f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i -`, then x264 at CRF 16, yuv420p, tagged BT.709.
- Optionally upscale the master to 2560x1440 for upload. That makes YouTube use its higher-quality VP9 encode, so grain and gradients survive.
- Keep key information out of the bottom 12% of the frame. Reserve the last 20 s for the end-screen layout.

### Cut cadence
- **0:00–1:00:** a visual event (cut, label, highlight, counter or camera change) every 2–3 s.
- **After the first minute:** an event every 3–5 s, a hard cut every 5–7 s on average, and no shot longer than 12 s without an internal event.
- Cuts and highlights land on ElevenLabs word timestamps. Highlights pop 2–4 frames before the key word.
- **Rhythm:** a map sequence of 15–40 s with 4–8 events, then 2–3 inserts of 3–4 s each (PD photo or video), then back to the map. A chapter card every 2–4 min, held for 3 s, with a big number and a 2–4 word title.
- **Opening template:**
  - 0–3 s: the globe is already rotating, with the claim.
  - 3–8 s: zoom from space down to the place while the outline draws on.
  - 8–15 s: glowing highlight plus a counter.
  - 15–30 s: true-size overlay on the USA.
  - 30–40 s: a "but…" twist and a 3-cut montage.
  - Title sting of 2 s, no later than 0:40.

### Camera rules
- Every frame moves. Stills get at least 1.5–3% scale drift or a 20–40 px pan per 10 s. All moves use cubic or exponential easing, never linear.
- **Zoom from space to place:**
  - Interpolate log(altitude) over 3–5 s.
  - Tilt from 0° to 35–45° on arrival, with the last 30% eased out.
  - Hold at least 1.5 s before the next label.
- Travelling east means moving screen-right. Never reverse a zoom within the same shot.
- **Parallax:** the label layer moves at 1.15x the map; the cloud layer at 1.3x.
- **Whip transitions** between distant places: 6–8 frames, with motion blur from averaging 4 sub-frames (only on these shots).
- **Match-cut:** zoom into a map point, then dissolve into a photo of the same spot.

### Palette
| Use | Colour |
|---|---|
| Space | #05070D |
| Deep ocean to shelf | #0A1A2E to #12385A |
| Land | Blue Marble, 30% desaturated, 15% darker (elevation tint for terrain chapters) |
| Hero highlight | #FF5A36, with glow |
| Water, routes, data | #3DE3FF |
| Arrows and circles (match the thumbnail) | #FFD23F |
| Primary label | #F4F6FA |
| Secondary label | #9AA7B8 |
| Archival split-tone | shadows #0E2A33, highlights #E8DCC0 |

One shared colour-grade lookup table (.cube): teal shadows, warm highlights, contrast +8%.

### Typography (all free Google Fonts)
| Use | Font and treatment |
|---|---|
| Labels | Barlow Condensed SemiBold, all caps, +8% tracking, 30–38 px, on a 70% black pill or with a leader line and dot |
| Counters | Inter Bold with tabular figures, 96–180 px, units at 50% size |
| Hook words and chapter cards | Bebas Neue, 180–260 px. Animate from 108% to 100% scale with a 6-frame blur-in; accent word in orange |
| Dates on archival inserts | Special Elite |

Limits: at most 2 text elements on screen, at most 7 words each, no subtitles.

### Premium finishing (all cheap)
- **Bloom:** blur the highlight layer at quarter resolution (σ 8–20) and add it at 35–60%.
- **Vignette:** 15–25% (`vignette=PI/5`).
- **Grain:** `noise=alls=5:allf=t` normally; strength 10 on archival.
- **Depth of field:** tilt-shift blur on the top and bottom 20% of tilted maps; blur the background behind text cards.
- **Light leaks:** procedural warm radial gradients at 10–20% opacity, on transitions and archival only.
- **Globe atmosphere:** rim glow #6FC3FF and a star field.
- **Archival look:** rounded print frames, 30 px shadow, dust overlay, ±1 px gate weave.

### Sound design per visual device
| Visual device | Sound cue |
|---|---|
| Zoom from space | Reverse-cymbal riser, then a sub-boom on arrival, over a wind bed |
| Outline draw-on | Soft swish plus a tonal ping |
| Fill or highlight pop | Low thump or pluck |
| Label pop-in | Quiet UI tick (about -24 dB) |
| Counter | Ticks matched to the count rate, ending in a ding or impact |
| Route or arrow | Pen scratch or a whoosh scaled to the line's length |
| True-size drag | Drag whoosh, then a heavy impact when the shape lands |
| Depth or cross-section | Sonar ping, creaks, a descending drone |
| Archival insert | Projector loop and crackle under the music |
| Chapter card or reveal | Music cuts out 0.5 s before, then a boom and reverse swell |

Use only CC0 sound effects.

## 4. Devices ranked by quality per effort (4-core CPU, no GPU)

| Rank | Device | How to build it | Estimated cost per frame |
|---|---|---|---|
| 1 | **Relief or satellite base map** | Pre-render once at 16k px from DEM hillshade with elevation tint, or Blue Marble (21600x10800). Animate with crops and `cv2.warpPerspective` for a 2.5D tilt | about 20–30 ms |
| 2 | **Vector overlays** | Cairo or skia: border draw-on via dash offset, glowing fills, arcs, pulse markers, labels | about 10–30 ms |
| 3 | **True-size comparison** | Reproject the outline to an equal-area projection at each location, then drag it. The single best device for this niche | cheap |
| 4 | **2D globe with simulated 3D (numpy)** | Orthographic lat/lon lookup plus `cv2.remap` on a mipmapped texture. Day/night blend with Black Marble, sun shading, rim glow | about 50–150 ms |
| 5 | **Counters, depth rulers, bars, cross-sections** | Draw elevation or depth profiles taken from real GEBCO/SRTM data | cheap |
| 6 | **PD photos** | Ken Burns moves, grade, grain, print frames | about 15 ms |
| 7 | **NASA/NOAA PD video** | Grade only | almost free |
| 8 | **Three.js WebGL (software renderer)** | DEM terrain flyovers only | about 1–3 s per frame (my estimate) |

Three.js should be limited to hero shots totalling 60 s or less (about 1,800 frames, roughly 30–90 min of rendering).

**Render budget:** a 15-min video is 27,000 frames. At about 0.15 s per frame across 4 workers, that is roughly 20 min of rendering, plus WebGL hero shots.

**Avoid:**
- particles, volumetric clouds and ocean shaders in software WebGL
- capturing frames from a headless browser
- full-resolution Gaussian blur on every frame
- linear moves and static holds
- busy labels
- Sentinel-2 cloudless imagery after 2016, because it is licensed non-commercial (CC BY-NC-SA). Use NASA GIBS imagery through the existing `gibs.py`, or Landsat, instead.