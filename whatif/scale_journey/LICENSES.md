# Licences

Scale-journey ships only CC0, public-domain, or OFL material, plus original procedural meshes. Nothing here is taken from the @what_if_animator reels.

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

## Blender

Renders are made with Blender 4.5.9 LTS, GPL. Blender itself is not vendored; install it beside the repo (`~/apps/blender-4.5.9-linux-x64`) or pass `--blender`.

## Numbers

Episode YAML files cite the measurements they use (FAO, CODATA, building heights). Those citations are sources for the facts, not a claim that the underlying publications are CC0. Fact-check before publishing a video.
