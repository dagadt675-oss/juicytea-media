# Private assets

BlendKit royalty-free and Sketchfab Free Standard files go here, or in
`/opt/cursor/asset-cache/private`. They are for rendered videos only.

Do not commit the raw `.blend`, `.glb`, `.fbx`, or zip files. Do not publish
them. `*.blend` is already ignored; everything else in this folder is ignored
except this note.

The Sketchfab Free Standard set and the BlendKit set are unpacked under
`/opt/cursor/asset-cache/private` (also gitignored). The scene reads them from
there for the rendered short only. Branded models in that cache are not placed.

RMS Queen Mary (PeeJaa, Sketchfab Free Standard) is cached at
`ships/RMS_Queen_Mary.glb` for the ocean episodes only: oceans_drained,
ice_melted, and rain_million. It is not placed in the river-city episode.
Real overall length is 310.7 m. The hull axis in the file is 260.7 units, so
placement scales by 310.7/260.7. Distant shots use `ships/RMS_Queen_Mary_distant.glb`
(49,980 faces) at that same scale. See the private section of
`assets/fetch/CATALOG.md`.
