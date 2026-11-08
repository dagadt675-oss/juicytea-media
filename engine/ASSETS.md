# Engine assets: what they are, where they come from, licences

| Path | Content | Source | Licence |
|---|---|---|---|
| `www/tex/day_8k.jpg` | Day texture with relief and bathymetry | NASA Blue Marble (NASA Earth Observatory / Visible Earth) | Public domain (NASA) |
| `www/tex/night_8k.jpg` | Night lights | NASA Black Marble / VIIRS | Public domain (NASA) |
| `www/tex/hgt_8k.png`, `normal_8k.png`, `normal_4k.png` | Global height map and derived normal maps | Built from AWS Terrain Tiles (Mapzen/Tilezen: SRTM, GMTED2010, ETOPO1 and others) with `tools/dem.py` | Terrain Tiles data terms (attribution: Mapzen / data sources); derived files |
| `www/tex/equal_earth.jpg` | Equal Earth projection of the day texture | Derived from the NASA texture | Public domain base |
| `www/tex/patch/*.jpg` | Hi-res regional satellite patches | NASA GIBS, built with `tools/gibs.py` | Public domain (NASA) |
| `www/geo/*.geojson` | Countries, coastlines, land, lakes, rivers, places, marine polygons | Natural Earth | Public domain |
| `www/paleo/coast_TTT.json`, `tracks.json` | Reconstructed coastlines 0-250 Ma and point tracks | GPlates Web Service, EarthByte Group; plate model Müller et al. (2019), simplified; fetched with `tools/fetch_paleo.py`, `fetch_paleo_tracks.py` | CC BY 4.0: credit "GPlates / EarthByte, Müller et al. (2019)" in the video description |
| `www/models/*.glb`, `www/models/Textures` | Animated low-poly characters | Quaternius, Kenney | CC0 |
| `www/fonts/*.woff2` | Anton, Archivo Black, Barlow Condensed, Bebas Neue, Inter, JetBrains Mono, Oswald, Playfair Display | Google Fonts | SIL Open Font License 1.1 |
| `www/three.module.min.js`, `www/jsm/` | three.js r170 and its example modules | three.js | MIT |
| `www/d3.min.js` | d3 v7 | d3 | ISC |
| `www/lab/globe/clouds_8k.jpg` | Cloud layer for the cinematic globe | NASA (built with `www/lab/scripts_globe/clouds.py`) | Public domain (NASA) |

Not committed, rebuilt by tools when needed: regional DEM/terrain bakes for drain shots (`www/lab/drain/tools/terrain_bake.py`, `fetch_drain_data.sh`), episode-specific photo cut-outs (`www/lab/story/tools/cutout.py`), renders, chunks, audio.
Episode credits for the video description: list NASA imagery, Natural Earth, GPlates/EarthByte (CC BY 4.0), Quaternius/Kenney and every public-domain archival image used.
