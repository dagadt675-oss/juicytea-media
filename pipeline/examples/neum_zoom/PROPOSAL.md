# Globe to border: can the engine zoom like Google Earth?

Verdict: yes, down to about 15–30 m per pixel anywhere on Earth, and about 1 m per pixel inside the United States, using only public-domain sources. A true 10 m global picture needs Sentinel-2, and that is not allowed. This folder is a 5-second proof of the allowed path, not the tile cache.

The asset hub (fetched 2026-10-11, 56 entries) has Blue Marble and no Landsat, SRTM, NAIP, or DEM pack. The proof therefore uses the public-domain web sources below. Raw rasters stay in `asset_library/` and are not committed.

## What is allowed

| Source | Ground sample | Where | License |
|---|---:|---|---|
| NASA Blue Marble, 21600×10800 | 1.9 km | Global | Public domain |
| Landsat 8/9 Collection 2, multispectral | 30 m | Global | Public domain (USGS) |
| Landsat 8/9 panchromatic, pansharpened | 15 m | Global | Public domain (USGS). Not in this proof |
| SRTM GL1 and NASADEM | ~30 m | Global, 60°N–56°S | Public domain (NASA/USGS) |
| NAIP | 0.6–1 m | United States | Public domain (USDA) |
| USGS 3DEP | ~1 m | United States | Public domain |

USGS and NASA ask for a credit when someone reprints the data. That is a request, not a condition. The files are public domain, so commercial use does not require attribution. HLS L30 is Landsat-only and is also allowed, but it is still 30 m.

## What is not allowed

These need an on-screen or distributed credit, or they are someone else's service:

- Sentinel-2 and anything else under the Copernicus licence. The licence requires “Copernicus Sentinel data [year]” whenever the picture is communicated to the public.
- HLS S30. It is a NASA product, but the pixels include Sentinel-2, so the Copernicus notice still applies.
- Sentinel-2 cloudless (EOX) and other CC-BY mosaics.
- ESRI, Mapbox, Google.
- ASTER GDEM. METI/NASA require a citation.
- Mapzen/AWS terrain PNG tiles. The packaging is not the raw SRTM grant. Use the original HGT or NASADEM instead.

So Neum, Musandam/Madha, and Kaliningrad can all reach a sharp 15–30 m picture. They cannot reach 10 m without breaking the attribution rule. A US border can go to about 1 m with NAIP plus 3DEP.

## Sharpness by zoom

Web-Mercator meters per pixel at the equator, and the public-domain layer that actually fills that zoom:

| Zoom | m/px | Layer |
|---:|---:|---|
| 0–6 | 156 km – 2.4 km | Blue Marble |
| 7 | 1.2 km | Blue Marble starts to run out (the 21600 plate is 1.9 km) |
| 8–11 | 610 – 76 m | Soft. MODIS is public domain but only ~250 m, so this band stays blurry |
| 12 | 38 m | Landsat 30 m, shown almost 1:1 |
| 13 | 19 m | Landsat 15 m pan, or 30 m upscaled once |
| 14 | 9.5 m | Would be Sentinel-2. Not allowed. Landsat pan upscaled is the ceiling |
| 17 | ~1.2 m | NAIP and 3DEP, United States only |

The engine today stops on Blue Marble, which is why a border crossing turns to mush. The missing piece is not a new camera. It is a second, finer plate that fades in once the ground sample passes about 80 m.

## How to build it, without baking the whole Earth

Do not pre-render the planet at 15 m. That is petabytes. Keep a tile cache and fill it when the camera asks:

1. Pick the Landsat 8/9 scenes over the view with cloud cover under a few percent (STAC). Read only the window from the cloud-optimized GeoTIFF.
2. For a cloud-free tile, keep several dates and composite the clear pixels (`QA_PIXEL`). One clear scene is enough when the date is already clean, as Neum was (0.47% cloud).
3. Optional: pansharpen the 30 m color with the 15 m pan band. Same USGS archive.
4. Drape NASADEM or SRTM at 30 m. Inside the US, swap in 3DEP and NAIP.
5. Shift the color a third of the way toward the Blue Marble mean of that same ground, so the crossfade does not jump from olive to gray.
6. In the camera, blend marble to Landsat across roughly 80 m/px to 40 m/px, then tilt the mesh. Cache the window. The next visit is free.

A 50 by 90 km window in this proof was a few seconds of ranged reads per band. That is the cost of the first visit to a place, not a separate production.

## This proof

`neum_zoom_proof.mp4` is 5.0 s, 1080×1920, 30 fps. It opens on the Blue Marble globe, zooms down the Adriatic, crossfades onto Landsat 9 as the marble goes soft, and settles on an oblique view of the Neum corridor with SRTM terrain and the Natural Earth Croatia/Bosnia line.

- Scene: `LC09_L2SP_188030_20260819`, 2026-08-19, 0.47% cloud.
- Center: 42.923°N, 17.616°E.
- Source and display sample: 30 m per pixel. The close view is not upscaled.
- Terrain exaggeration on the tilt is 2.6× so the ridges read. The heights are the SRTM meters.
