# img/ch3 licences

| File | Source | Credit | Licence | Checked |
|---|---|---|---|---|
| ch3_geo.json | derived (see below) | see below | Public Domain inputs; derived geometry made for this film | 2026-11-09 |

ch3_geo.json holds line geometry only (lon/lat), built by the ch3 builder's scratch scripts (`ch3work/tools/volcanoes.py`, `terraces.py`, `ch3data.py`, not in git) from:

- VOLC (per-volcano land areas of the Island of Hawaiʻi, simplified 300 m): USGS Open-File Report 2007-1089, "Geologic Map of the State of Hawaiʻi" (Sherrod, Sinton, Watkins, Brunt 2007), Haw_St_shapefiles.zip, field VOLCANO (https://pubs.usgs.gov/of/2007/1089/), public domain (USGS). Mauna Loa: 5,161 km2 = 49 % of the island on this map (USGS text: "just over half").
- MLFULL / MKFULL (Mauna Loa's and Mauna Kea's edifice above AND below the old shoreline): the map areas above, extended over the drained flanks of the Big Island massif (bigisland hero grid above -3,500 m) by a nearest-volcano partition. The submarine boundaries are APPROXIMATE (no published per-volcano submarine map was used); shown only as a fill, never labelled as a boundary.
- MASSIF (the massif's waterline at -3,500 m, open at the Alenuihaha saddle toward Maui), DEEP (water left at -5,500 m in the Hawaiian Deep): the bigisland hero grid (lab/hawaii/data, ETOPO 2022 / NOAA data, public domain).
- COAST (today's 0 m coasts) and CREST (a highest-ground path through the summits from Hawaiʻi to Niʻihau; its lowest point -3,003 m is the Oʻahu-Kauaʻi saddle): the main_chain region grid (ETOPO 2022 15", public domain).
- TERR (drowned-reef terrace edges off Kohala at -170, -460, -700, -960 and -1,210 m, kept only where a flat lies just above a riser): the kohala region grid (NOAA NCEI 1/3" kawaihae_13 north of 19.87 N, public domain).

No photo, no third-party image. Credits for the underlying data go in the video description only, never on screen.
