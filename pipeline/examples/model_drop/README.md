# Zoom-to-spot and a model drop-in

Camera moves live in `jt/show/moves.py`, in the grammar of the Budapest reference: `drop_in` (ease-out, blur while fast), `match_cut_dive` (ease-in, radial blur on the last frames), `country_extrude_flag`, `river_trace`, `border_glow`, `district_fill`, `landmark_pop` (ease-out-back), and `snap_explode`. The bridge proofs use the drop, the dive, and a pop on every span.

The flight path itself is not original. `jt/show/flyto.py` is a port of d3-interpolate `src/zoom.js` (ISC, Mike Bostock, 2010-2021), the van Wijk & Nuij curve. MapLibre GL JS `Map.flyTo` (BSD-3-Clause) and deck.gl `FlyToInterpolator` / math.gl `flyToViewport` (MIT) use that same curve; rho is 1.42, MapLibre's default. The intro runs it with ease-out timing, the dive with ease-in, which is MapLibre's `easing` option on `flyTo`. CesiumJS `camera.flyTo` (Apache-2.0) is the same idea with a separate easing function; its flight code is tied to a WebGL globe, so it is not linked. BlenderGIS is GPL, so it is not used.

The radial smear in `apply_zoom_blur` is the glfx.js `zoomBlur` kernel (MIT, Evan Wallace, 2011): samples along the ray to the center, weighted by `4 * (p - p * p)`. Eight taps stand in for the shader's forty. It runs only while a move is inside its window, then the plate is sharp.

Plates and the two code files are logged in `assets/FOUND_ASSETS.md`, with copies of anything under 50 MB in `assets/found/`.

`jt/show/model_drop.py` is the reusable piece. A spec looks like this:

```json
{"type": "model_drop", "asset": "parametric:cable_stayed",
 "geo": [[lat, lon], "..."], "scale": "stylized", "heading": null,
 "at_word": "NINETEEN", "build": "span_by_span",
 "kind": "cable_stayed", "spans_m": [145, 145], "tower_after": [0],
 "label": "19 MI (30 KM) · 2020"}
```

`build` is `span_by_span`, `extrude`, `drop`, or `fly_in`. `kind` is `beam`, `cable_stayed`, or `suspension`. `scale: true` uses the real deck and tower meters. `scale: stylized` keeps the centerline on the real ground and lifts the towers and deck so they read on a 30 m map. Cues are a whoosh into the zoom, a ratchet at each span, and a ding when the last span lands.

The hub has Kenney and Quaternius street bridges and wooden footbridges, plus private landmark meshes. None of those is a sea crossing, so these two shots use the parametric kit. The polylines were traced on USGS Landsat, not taken from OSM.

`temburong_drop.mp4` zooms from Borneo onto the Brunei Bay crossing and builds the deck. The water crossing on the Landsat plate is 17.5 km. The label is the published 30 km link, which also includes the land viaducts and the Mentiri tunnels. The first two spans are the Brunei Channel bridge, 2×145 m, with the pylon between them.

`peljesac_drop.mp4` zooms from the southern Adriatic onto the 13-span deck. The line is the Landsat shore-to-shore trace (about 2.37 km). The span list is the published schedule, 72 + 96 + 118 + 203.5 + 5×285 + 203.5 + 118 + 96 + 72 m, scaled onto that line. Six pylons sit on the cable-stayed joints.

The zoom is an exponential through three public-domain levels: Blue Marble, a NASA GIBS Blue Marble regional plate, then Landsat 30 m. A finer plate is drawn only once the frame fits inside it, and its edge feathers into the coarser level, so the picture stays full-bleed. Past 30 m the ground flattens toward map colors and the bridge stays vector. The camera lays the bridge left to right so it fills about 60% of the width, tilted about 30°. Each span drops in as its own deck, pier, and, on the cable-stayed joints, a pylon and cables, with a shadow on the water. The hold drifts a little and the label pill pulses. Motion blur runs only on the fast part of the zoom.
