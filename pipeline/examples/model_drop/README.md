# Zoom-to-spot and a model drop-in

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

The close map is Landsat at 30 m, crossfaded from Blue Marble. Pelješac is framed a little inside that sample so the thirteen spans read; the vector bridge stays sharp. Motion blur runs only while the zoom is still fast. The oblique tilt is 28°, then it returns toward top-down.
