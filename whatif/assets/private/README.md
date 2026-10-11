# Private assets

BlendKit royalty-free and Sketchfab Free Standard files go here, or in
`/opt/cursor/asset-cache/private`. They are for rendered videos only.

One shared hub lists every pack (CC0 and private). The order is the hub, then
a no-attribution CC0 download logged in the catalog, then hand-built geometry.
Never CC-BY, NC, ND, or brand IP. Re-fetch the hub at the start of each
episode. The copy on disk is gitignored because the JSON includes private
download commands. See `docs/whatif_engine.md`.

The airport scene has a Malaysia Airlines livery on the main jet. Do not
place that aircraft until the livery is a plain white or generic one.
Ruined city FREE 5 is the late-year skyline. The commute pack (bike, scooter,
skateboard) is abandoned street clutter.

```bash
curl -L 'https://drive.usercontent.google.com/download?id=1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV&export=download&confirm=t' -o ASSET_HUB.json
```

The human-readable twin is Drive id `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T`
(`ASSET_HUB.md`). As of 2026-10-11 the hub has 59 entries: 33 public, 26
private. Private Free Standard and BlendKit files stay in the cache.

Do not commit the raw `.blend`, `.glb`, `.fbx`, or zip files. Do not publish
them. `*.blend` is already ignored; everything else in this folder is ignored
except this note.

The Sketchfab Free Standard set and the BlendKit set are unpacked under
`/opt/cursor/asset-cache/private` (also gitignored). The scene reads them from
there for the rendered short only. Branded models in that cache are not placed.
Extra Sketchfab packs are in `sketchfab/`. The river city uses the city-props
pack (street lights, a bin, a meter, a dumpster) and the generic cars from the
vehicle mini pack. The night diorama, the SketchUp city pack, the kitchen, and
the first-person arms stay indexed for their own episodes.

RMS Queen Mary (PeeJaa, Sketchfab Free Standard) is cached at
`ships/RMS_Queen_Mary.glb` for the ocean episodes only: oceans_drained,
ice_melted, and rain_million. It is not placed in the river-city episode.
Real overall length is 310.7 m. The hull axis in the file is 260.7 units, so
placement scales by 310.7/260.7. Distant shots use `ships/RMS_Queen_Mary_distant.glb`
(49,980 faces) at that same scale. See the private section of
`assets/fetch/CATALOG.md`.

Also cached, and not placed in the river city: a low-poly tree pack (scale each tree to 6–10 m), a hazmat suit for disaster episodes (about 1.9 m tall), a cottage-in-the-forest diorama for snow_forever, an animated civilian helicopter (one clip, scale the 2.6 m model to about 10 m), and Classroom 01 for interior POV (scale the 10.7 m height to about 3.2 m).
