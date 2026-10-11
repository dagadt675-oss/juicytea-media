# Licences

Scale-journey ships CC0, public-domain, or OFL material. Hand-built meshes are a last resort. The standing asset rule in `README.md` is the order: the asset hub, then a no-attribution free download logged here, then original geometry. Nothing here is taken from the @what_if_animator reels. Never add CC-BY, NC, ND, or game/brand IP.

## Code and meshes

All Python, and every mesh built in `engine/build.py` (rice grain, pile, person, buildings, terrain, planets-as-spheres), is original to this repository.

## Font

| File | Licence | Source |
| --- | --- | --- |
| `assets/fonts/Anton-Regular.ttf` | SIL Open Font License 1.1 (`assets/fonts/OFL.txt`) | [Anton](https://fonts.google.com/specimen/Anton), Vernon Adams, Google Fonts |

## Textures

| File | Licence | Source |
| --- | --- | --- |
| `assets/textures/wood_diff_4k.jpg` | CC0 | Poly Haven, `wood_table_001` diffuse 4k. https://polyhaven.com/a/wood_table_001 |
| `assets/textures/wood_rough_2k.jpg` | CC0 | Poly Haven, `wood_table_001` roughness 2k. Not used by the 1-sample render (JPEG roughness speckles); kept so a higher-sample lookdev can turn it on. |
| `assets/textures/wood_nor_2k.jpg` | CC0 | Poly Haven, `wood_table_001` GL normal 2k. Same as roughness: shipped, not wired into the fast render. |
| `assets/textures/earth_2k.jpg` | Public domain (US government work) | NASA Visible Earth, Blue Marble / land surface, shallow water, shaded topography, 2048×1024. https://visibleearth.nasa.gov/images/57752 |
| `assets/textures/moon_1k.jpg` | Public domain (US government work) | NASA/GSFC/LRO LROC colour mosaic, 1k. https://svs.gsfc.nasa.gov/4720 |
| `assets/hdri/sunset_jhbcentral_1k.hdr` | CC0 | Poly Haven, `sunset_jhbcentral` 1k HDR. https://polyhaven.com/a/sunset_jhbcentral |

## Characters

| File | Licence | Source |
| --- | --- | --- |
| `assets/characters/characterMedium.fbx` | CC0 | Kenney, Animated Characters Protagonists. https://kenney.nl/assets/animated-characters-protagonists |
| `assets/characters/skaterMaleA.png` | CC0 | Same pack, skater skin. |

`engine/gen_textures.py` bakes the facade, bokeh card, and starfield at render time. Those images are procedural and original.

## Hero models kept out of git

The Empire State Building mesh (Sketchfab Free Standard, PeeJaa, model `47187dafbafa47948f9af4e140e72582`) and the Statue of Liberty mesh (Sketchfab Free Standard, vikramart2001, model `6cb75e326e784acb8e40d192281a93fe`) are commercial-use and not redistributed. `engine/build_b.py` reads them from `cache/private/`, which is gitignored. Do not commit the glb files.

City blocks, roads, taxis, and pedestrians start from the asset hub. CC0 packs fetched by `tools/fetch_library.py` stay in `cache/library/`. Sketchfab Free Standard files (Procedural City blocks, One WTC, the commute pack, the Empire State scan, the Statue of Liberty) stay in gitignored `cache/private/`. Do not commit them.

The hub’s airport city scene contains a Malaysia Airlines livery. Do not render that livery. If the scene is used, repaint the airline aircraft plain white. The ruined-city pack is optional and is not part of the penny episode.

When a CC0 file is downloaded because the hub did not have it, add a row to the tables above with the licence and the source URL, and add `assets/library/cc0_manifest.json` if the fetch should be repeatable.

## Blender

Renders are made with Blender 4.5.9 LTS, GPL. Blender itself is not vendored; install it beside the repo (`~/apps/blender-4.5.9-linux-x64`) or pass `--blender`.

## Numbers

Episode YAML files cite the measurements they use (FAO, CODATA, building heights). Those citations are sources for the facts, not a claim that the underlying publications are CC0. Fact-check before publishing a video.
