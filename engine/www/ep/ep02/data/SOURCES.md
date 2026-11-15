# ep02 terrain data: sources and licences

Every height grid and colour texture in this folder is baked from the sources below by `engine/www/lab/hawaii/tools/region_bake.py` (base bake) and `engine/www/lab/hawaii/tools/detail_bake.py` (close-up detail, 2026-11-09), driven by `../tools/regions_spec.json` and rebuilt with `../tools/rebuild_regions.sh`. The baked files are git-ignored; each region's `meta.json` (committed) lists the exact datasets, scenes, quarter quads and dates it used, and `regions.json` its resolutions (`res`). Nothing here is a photo of another channel, a stock clip or generated imagery.

Credits belong in the video description only (owner rule: no sources on screen). Suggested line for ep02: "Elevation: USGS 3D Elevation Program (3DEP), NOAA NCEI (ETOPO 2022, coastal DEMs), Mapzen Terrain Tiles. Imagery: USDA NAIP (via NOAA Digital Coast), NASA HLS, MODIS and Blue Marble, USGS Landsat, contains modified Copernicus Sentinel data 2023-2025."

## Heights

| Source | Resolution | Used in | Licence / credit | Access |
|---|---|---|---|---|
| NOAA NCEI ETOPO 2022 (15" and 30" surface) | about 460 m / 920 m | every region (base) | US Government work, public domain; credit NOAA NCEI | THREDDS WCS, ngdc.noaa.gov |
| NOAA NCEI coastal topo-bathy DEMs (oahu_13_mhw_2011, hilo_13_mhw_2011, kauai_13_mhw_2012, kawaihae_13_mhw_2011, midway_island_13/3_mhw_2012) | 1/3" (about 10 m), 3" | pali, oahu_nuuanu, halape, holei, kilauea_sf, maunakea, kohala, kauai, waimea, midway, nwhi_west, kamaehu | public domain; credit NOAA NCEI | OPeNDAP, ngdc.noaa.gov |
| USGS 3D Elevation Program (3DEP), best available bare-earth DEM: 1 m lidar DEMs HI_NOAAMauiOahu_2020_B20 (O'ahu), HI_Hawaii_Island_Lidar_NOAA_2017_B17 (Hawai'i Island), HI_FEMAR9Kauai_2019_D19 (Kaua'i) | 1 m source, baked at 1-7.5 m | pali (5 m), pali_lookout (2 m), halape (5 m), halape_cove (1 m), holei (2 m), kilauea_coast (7.5 m), maunakea (5 m) | US Government work, public domain; credit "USGS 3D Elevation Program" | USGS 3DEPElevation ImageServer (exportImage, EPSG:4326, float32), elevation.nationalmap.gov |
| AWS Terrain Tiles / Terrarium (Mapzen/Tilezen; sources include USGS NED/3DEP, SRTM, GMTED, ETOPO1) | zoom 9-14 (about 280-8 m) | land detail where no coastal DEM covers (mauinui, main_chain, kamaehu, kohala, nihoa, lalo, gardner, kure, nwhi, everest) | open data; credit "Terrain Tiles: Mapzen, data sources" | s3.amazonaws.com/elevation-tiles-prod |

Vertical datums: 3DEP in Hawai'i is local mean sea level, the NCEI coastal grids mean high water (about 0.3 m higher); detail_bake.py takes the lidar on land only (above 0.5 m) and feathers it into the NCEI grid at the coast, so the sea floor keeps the NCEI bathymetry.

## Colour

| Source | Resolution | Used in | Licence / credit | Access |
|---|---|---|---|---|
| NASA GIBS MODIS Terra/Aqua Corrected Reflectance, Blue Marble Next Generation | 250 m / 500 m | every region (base composite) | NASA, public domain; credit NASA | gibs.earthdata.nasa.gov |
| NASA HLS v2 (Harmonized Landsat Sentinel-2, S30 + L30), GIBS layers or with Fmask from the Planetary Computer | 30 m | close regions (the reference tone of the detail bakes) | NASA LP DAAC, no restrictions on use; HLS S30 derives from Copernicus Sentinel-2 | gibs.earthdata.nasa.gov, planetarycomputer.microsoft.com |
| USGS Landsat 8 Collection 2 Level-2 (dated scenes) | 30 m | lalo_2018_before / lalo_2018_after | USGS, public domain; credit USGS | planetarycomputer.microsoft.com |
| USDA NAIP 2021-2023 Hawai'i, 4-band, distributed by NOAA Digital Coast (dataset id 9668, "2021 - 2023 USDA NAIP 4-Band 8 Bit Imagery: Hawaii") | 0.6 m source, baked at 0.7-6.3 m | pali (4.3 m), pali_lookout (1.4 m), halape (3.6 m), halape_cove (0.7 m), holei (1.8 m), kilauea_coast (5 m), maunakea (3.3 m), waimea (6.3 m) | USDA Farm Production and Conservation Business Center, public domain; credit "USDA NAIP" | cloud-optimised GeoTIFFs, coastalimagery.blob.core.windows.net/digitalcoast/HI_NAIP_2021_9668 (read by HTTP range requests, nothing stored) |
| Copernicus Sentinel-2 L2A (ESA), median of SCL-clear observations, 12 scenes 2023-2025 | 10 m, baked at 7.2 m | midway (the atoll only; NAIP does not cover the NW Hawaiian Islands) | Copernicus free and open data licence: use is free, attribution required: "Contains modified Copernicus Sentinel data 2023-2025" (description) | planetarycomputer.microsoft.com |

How the aerial and Sentinel-2 colour is matched to the existing grade (detail_bake.py, "detail transfer"): the region's own graded colour stays the tone and the colour at its own scale (HLS 30 m), the imagery only adds what is finer (its luminance detail as a ratio to its local mean, plus its residual colour detail times one chroma factor, after one luminance gain). A winter photo's baked cliff shadow (Pali NAIP of 15 Dec 2022: 8.6 % of the land far darker than the summer reference at 30 m) and clouds bigger than 30 m take the reference's tone; the photo's own hue never replaces the grade.

## Not used, and why

- NAIP does not cover Midway, Kure, Lalo or the other NW Hawaiian Islands. The National Map's product API lists no High Resolution Orthoimagery dataset and its NAIP ImageServer ends at about 24.5° N (no Hawai'i); the USGS Imagery Only basemap tiles stop at zoom 16 (about 2 m) over Hawai'i (checked 2026-11-09).
- NOAA's 2021 NW Hawaiian Islands topo-bathy lidar DEM (NGS_NWHawaiianIslands_Topobathy_2021_10191) covers only French Frigate Shoals (Lalo): a candidate for a later Lalo / East Island close-up, not used yet.
- The NCEI 6" Hawai'i grid (hawaii_6_mllw_2005): gridding artefacts and track striping (PLAYBOOK_production section 15).
- Esri World Imagery: not public domain (its terms must be checked before monetised use); not used for terrain textures.
