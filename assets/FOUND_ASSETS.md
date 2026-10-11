# Found assets

Append-only log of files found on the web for this branch, so they can be mirrored into the shared Drive hub. Files under 50 MB with a redistributable license are also copied under `assets/found/`. Full Landsat scenes are larger than that, so only the windowed extracts are in the repo.

## NASA GIBS Blue Marble, Brunei

- Name: `gibs_brunei_blue_marble.jpg`
- Direct download: https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=BlueMarble_NextGeneration&FORMAT=image/jpeg&CRS=EPSG:4326&BBOX=1.2,112.2,7.6,117.6&WIDTH=1600&HEIGHT=1600
- Source page: https://nasa-gibs.github.io/gibs-api-docs/access-basics/
- License: public domain (NASA). No on-screen credit required.
- Size: 181,869 bytes
- For: regional plate between the globe and the Landsat window on the Temburong zoom
- Copy: `assets/found/gibs/gibs_brunei_blue_marble.jpg`

## NASA GIBS Blue Marble, southern Adriatic

- Name: `gibs_adriatic_blue_marble.jpg`
- Direct download: https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=BlueMarble_NextGeneration&FORMAT=image/jpeg&CRS=EPSG:4326&BBOX=40.2,14.8,45.2,20.2&WIDTH=1600&HEIGHT=1600
- Source page: https://nasa-gibs.github.io/gibs-api-docs/access-basics/
- License: public domain (NASA). No on-screen credit required.
- Size: 229,606 bytes
- For: regional plate on the Pelješac zoom
- Copy: `assets/found/gibs/gibs_adriatic_blue_marble.jpg`

## Landsat 8 Collection 2 Level-2, path 118 row 057

- Name: `LC08_L2SP_118057_20240726_02_T1` (Brunei Bay, 2024-07-26, 5.89% cloud)
- Direct download, red / green / blue surface-reflectance COGs (Planetary Computer signs these hrefs; an anonymous GET of the blob returns 409):
  - https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2024/118/057/LC08_L2SP_118057_20240726_20240801_02_T1/LC08_L2SP_118057_20240726_20240801_02_T1_SR_B4.TIF (79,640,457 bytes)
  - https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2024/118/057/LC08_L2SP_118057_20240726_20240801_02_T1/LC08_L2SP_118057_20240726_20240801_02_T1_SR_B3.TIF (81,936,695 bytes)
  - https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2024/118/057/LC08_L2SP_118057_20240726_20240801_02_T1/LC08_L2SP_118057_20240726_20240801_02_T1_SR_B2.TIF (78,833,006 bytes)
- Source page: https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC08_L2SP_118057_20240726_02_T1
- License: public domain (USGS). No on-screen credit required.
- Size: full COGs above, each over 50 MB, not copied. The window used by the shot (UTM 50N, about 51 by 44 km, bands 2/3/4) is 3,868,817 + 3,964,681 + 3,912,113 bytes.
- For: close satellite plate under the Temburong bridge
- Copy: `assets/found/landsat/LC08_L2SP_118057_20240726_brunei_window_b2.tif`, `..._b3.tif`, `..._b4.tif`

## Landsat 9 Collection 2 Level-2, path 188 row 030

- Name: `LC09_L2SP_188030_20260819_02_T1` (southern Dalmatia, 2026-08-19, 0.47% cloud)
- Direct download, red / green / blue surface-reflectance COGs:
  - https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2026/188/030/LC09_L2SP_188030_20260819_20260820_02_T1/LC09_L2SP_188030_20260819_20260820_02_T1_SR_B4.TIF (79,821,323 bytes)
  - https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2026/188/030/LC09_L2SP_188030_20260819_20260820_02_T1/LC09_L2SP_188030_20260819_20260820_02_T1_SR_B3.TIF (78,466,350 bytes)
  - https://landsateuwest.blob.core.windows.net/landsat-c2/level-2/standard/oli-tirs/2026/188/030/LC09_L2SP_188030_20260819_20260820_02_T1/LC09_L2SP_188030_20260819_20260820_02_T1_SR_B2.TIF (78,481,299 bytes)
- Source page: https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/LC09_L2SP_188030_20260819_02_T1
- License: public domain (USGS). No on-screen credit required.
- Size: full COGs above, each over 50 MB, not copied. The window used by the Neum and Pelješac shots (UTM 33N, bands 2/3/4) is 8,981,527 + 9,019,282 + 9,215,125 bytes.
- For: close satellite plate under Pelješac, same window as the Neum proof
- Copy: `assets/found/landsat/LC09_L2SP_188030_20260819_dalmatia_window_b2.tif`, `..._b3.tif`, `..._b4.tif`

## SRTM GL1 elevation tiles

- Name: `N42E017.hgt.gz`, `N43E017.hgt.gz`
- Direct download:
  - https://elevation-tiles-prod.s3.amazonaws.com/skadi/N42/N42E017.hgt.gz (3,296,541 bytes)
  - https://elevation-tiles-prod.s3.amazonaws.com/skadi/N43/N43E017.hgt.gz (12,833,209 bytes)
- Source page: https://registry.opendata.aws/terrain-tiles/ (SRTM GL1, NASA/USGS, packed as Mapzen skadi HGT)
- License: public domain (NASA/USGS SRTM). No on-screen credit required.
- Size: 3,296,541 and 12,833,209 bytes
- For: elevation under the southern Dalmatia Landsat window
- Copy: `assets/found/srtm/N42E017.hgt.gz`, `assets/found/srtm/N43E017.hgt.gz`

## d3-interpolate zoom path

- Name: `d3-interpolate` `src/zoom.js` at tag v3.0.1 (`6562b85040f7`)
- Direct download: https://raw.githubusercontent.com/d3/d3-interpolate/v3.0.1/src/zoom.js
- Source page: https://github.com/d3/d3-interpolate/blob/v3.0.1/src/zoom.js
- License: ISC, Mike Bostock, 2010–2021. Commercial use is allowed. No on-screen credit. The copyright notice stays with the file.
- Size: 1,649 bytes (license file 731 bytes)
- For: the van Wijk flyTo curve ported in `pipeline/jt/show/flyto.py`. Same curve as MapLibre `Map.flyTo` and deck.gl `FlyToInterpolator`. Those engines were not downloaded.
- Copy: `assets/found/code/d3-interpolate-zoom.js`, `assets/found/code/d3-interpolate-LICENSE`

## glfx.js zoom blur

- Name: `glfx.js` `src/filters/blur/zoomblur.js` at `86ae72acfffc`
- Direct download: https://raw.githubusercontent.com/evanw/glfx.js/86ae72acfffc/src/filters/blur/zoomblur.js
- Source page: https://github.com/evanw/glfx.js/blob/86ae72acfffc/src/filters/blur/zoomblur.js
- License: MIT, Evan Wallace, 2011. Commercial use is allowed. No on-screen credit. The copyright notice stays with the file.
- Size: 1,988 bytes (license file 1,059 bytes)
- For: the radial zoom-blur kernel used by `apply_zoom_blur` in `pipeline/jt/show/moves.py`
- Copy: `assets/found/code/glfx-zoomblur.js`, `assets/found/code/glfx-LICENSE`

## Poly Haven aerial rocks

- Name: `aerial_rocks_02_diff_1k.jpg`
- Direct download: https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/aerial_rocks_02/aerial_rocks_02_diff_1k.jpg
- Source page: https://polyhaven.com/a/aerial_rocks_02
- License: CC0. No on-screen credit required.
- Size: 785,923 bytes
- For: rocky texture on the Märket close-up, clipped to the islet, instead of a flat fill
- Copy: `assets/found/aerial_rocks_02_diff_1k.jpg`
