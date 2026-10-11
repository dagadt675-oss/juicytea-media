# Private assets

BlendKit royalty-free and Sketchfab Free Standard files go here, or in
`/opt/cursor/asset-cache/private`. They are for rendered videos only.

Do not commit the raw `.blend`, `.glb`, `.fbx`, or zip files. Do not publish
them. `*.blend` is already ignored; everything else in this folder is ignored
except this note.

The Sketchfab Free Standard set and the BlendKit set are unpacked under
`/opt/cursor/asset-cache/private` (also gitignored). The scene reads them from
there for the rendered short only. Branded models in that cache are not placed.
