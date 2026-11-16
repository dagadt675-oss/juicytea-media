# ep02 texel audit (final)

> Verifier note (2026-11-15, after the close-up round 2 and this check). Every terrain shot that exists was audited (ch1-ch3; ch4-ch6 are still placeholders).
> Result: 111 frames, 76 over a limit, 18 of them carried by the detail texturing ('FLAG det'); 58 stay over with no detail cover.
> Those 58 are wides and far ground: Big Island and Maui Nui wides on 250 m MODIS / 30 m HLS colour at 15-110 km (4-13 px), the
> Nu'uanu dive and O'ahu-from-the-NE shots (oahu_nuuanu 10-39 km, 4-18 px), the Everest gag and comparisons (HLS 30 m, 9-13 px),
> and the ch3 hotspot / Mauna Loa / gauge wides. Their colour is not baked finer yet (finer public imagery exists for parts of them);
> the detail texturing is faded out past 6-16 km on purpose (it would read as noise at that distance).
> Pali Lookout s026-s029: centre 0.75-1.1 px per colour texel (crisp); s030 centre is water, its pull-back frames 3258-3266 reach
> 11-18 px on oahu_nuuanu (3258 FLAG det, 3266 FLAG; soft on the still), and s031 (3376, 39 km) is 3.94 px (FLAG). In s026-s029 the lower third 1.78-2.14 px (the 1.44 m photo bake of 0.6 m
> NAIP: soft but inside 2 px except s029, which the detail carries). Height px 'src' 12-15 is the 10 m interpolated lidar band at
> the foot of the wall: the 2 m grid is smooth there, the source is not finer.
> Not measured by this tool: cres.png (photo-resolved ground where the detail fades on purpose) and the shading. A shading defect it
> cannot see was found and fixed in this check: half-float heights drew contour stripes on foreshortened ground (Mauna Kea f7349).

2026-11-15T20:39, 1920x1080. Each cell: visible layer, distance from the camera, then **colour px** / height px = screen pixels covered by one colour texel (at its effective resolution: the texel or the imagery, whichever is coarser) and by one height texel, along the least foreshortened direction. Flag: colour > 2 px or height > 4 px at the centre or the lower third (y = 2/3); 'seabed' = ground below -6 m, where the stage draws its own seabed material instead of the colour map (only the height counts). A seg id with * = a shot no segment middle falls in, sampled at its own middle; with ^ = the closest (worst) frame of the shot named, scanned every few frames. 'src' = height px at the source's own resolution where the source is only interpolated. Band max = worst of 15 points over y 70-90 %. 'det' (points over a limit) = estimated strength of the detail texturing there, 0-1 (hterrain.js gate: colour px, the default detFar 6-16 km, footprint, depth under the water level; cres.png not read); flag 'FLAG det' = every point over a limit has det 0.5 or more, so the detail texturing carries it (the texel itself is still that big). Tool: engine/www/ep/ep02/tools/texel_audit.js.

Notes: ch4: no shots yet (placeholders only); ch5: no shots yet (placeholders only); ch6: no shots yet (placeholders only)

## Film frames (one per segment, plus the closest frame of each shot): 111 sampled, 111 on terrain, 76 flagged, 18 of them carried by the detail texturing

| seg | frame | time | shot | region | centre | lower third | band max col / h | flag |
|---|---|---|---|---|---|---|---|---|
| s001 | 56 | 0:01.9 | ch1-demo | mauinui | bigisland 112.3 km: **4.45** / 2.05, det 0 | bigisland 86.6 km: seabed / 2.7 | 7.92 / 4.17 | FLAG |
| s002 | 155 | 0:05.2 | ch1-demo | mauinui | bigisland 91.2 km: **5.5** / 2.54, det 0 | bigisland 74.9 km: seabed / 3.11 | 0 / 4.68 | FLAG |
| s003 | 261 | 0:08.7 | ch1-demo | mauinui | bigisland 89.2 km: seabed / 2.63 | bigisland 72.6 km: seabed / 3.25 | 0 / 4.94 |  |
| s004^ | 331 | 0:11.0 | ch1-demo | mauinui | bigisland 79.0 km: **6.29** / 2.9, det 0 | bigisland 62.8 km: **7.88** / 3.64, det 0 | 10.76 / 4.97 | FLAG |
| s004 | 384 | 0:12.8 | ch1-demo | mauinui | water (mauinui) | water (mauinui) | 5.23 / 5.23 |  |
| s005 | 494 | 0:16.5 | ch1-demo | mauinui | water (mauinui) | mauinui 41.6 km: seabed / 3.2 | 5.16 / 5.16 |  |
| s006 | 572 | 0:19.1 | ch1-demo | mauinui | water (mauinui) | mauinui 41.9 km: seabed / 3.2 | 5.17 / 5.17 |  |
| s007 | 684 | 0:22.8 | ch1-ice | mauinui | mauinui 40.0 km: seabed / 2.96 | mauinui 21.9 km: seabed / 5.44, det 0 | 10.29 / 10.29 | FLAG |
| s007^ | 743 | 0:24.8 | ch1-ice | mauinui | mauinui 17.3 km: seabed / 5.95, det 0 | mauinui 6.8 km: seabed / 15.18, det 0.98 | 34.42 / 34.42 | FLAG |
| s007^ | 745 | 0:24.8 | ch1-ride | mauinui | mauinui 14.6 km: **10.34** / 10.34, det 0.05 | mauinui 163 m: seabed / 876.81, det 1 | 0 / 2462.49 | FLAG |
| s008 | 781 | 0:26.0 | ch1-ride | mauinui | mauinui 14.6 km: **10.44** / 10.44, det 0.05 | mauinui 167 m: seabed / 863.75, det 1 | 0 / 2425.17 | FLAG |
| s009 | 863 | 0:28.8 | ch1-ride | mauinui | mauinui 14.6 km: **10.85** / 10.85, det 0.05 | mauinui 183 m: seabed / 819.24, det 1 | 0 / 2293.95 | FLAG |
| s010 | 965 | 0:32.2 | ch1-ride | mauinui | mauinui 16.5 km: **6.3** / 6.3, det 0 | mauinui 8.3 km: **13.5** / 13.5, det 0.87 | 24.61 / 24.61 | FLAG |
| s011 | 1089 | 0:36.3 | ch1-ride | mauinui | mauinui 3.6 km: seabed / 24.01, det 1 | mauinui 2.8 km: seabed / 31.74, det 1 | 0 / 67.47 | FLAG det |
| s012 | 1208 | 0:40.3 | ch1-ride | mauinui | mauinui 43.7 km: seabed / 2.85 | mauinui 28.5 km: seabed / 4.39, det 0 | 0 / 7.45 | FLAG |
| s013 | 1315 | 0:43.8 | ch1-ride | mauinui | mauinui 44.0 km: seabed / 2.61 | mauinui 29.0 km: seabed / 3.99 | 7.06 / 7.06 |  |
| s014 | 1412 | 0:47.1 | ch1-bigisland | kilauea_sf | kilauea_coast 31.3 km: **0.24** / 0.36 | water (kilauea_sf) | - |  |
| s015 | 1511 | 0:50.4 | ch1-bigisland | kilauea_sf | kilauea_coast 7.6 km: **1.33** / 2 | kilauea_coast 6.1 km: **1.63** / 2.45 | 2.32 / 3.49 |  |
| s015^ | 1526 | 0:50.9 | ch1-bigisland, ch1-halape | kilauea_sf | kilauea_coast 2.6 km: **5.33** / 8.02, det 1 | kilauea_coast 2.1 km: **6.62** / 9.97, det 1 | 8.78 / 13.23 | FLAG det |
| s015^ | 1526 | 0:50.9 | ch1-bigisland, ch1-halape | halape | halape_cove 2.6 km: **0.8** / 1.12 | halape_cove 2.1 km: **0.96** / 1.33 | 6.36 / 8.86 |  |
| s016 | 1653 | 0:55.1 | ch1-halape | halape | water (halape_cove) | halape_cove 970 m: **2.85** / 3.98, det 1 | 3.44 / 4.8 | FLAG det |
| s017 | 1787 | 0:59.6 | ch1-halape | halape | halape_cove 614 m: **5.55** / 7.75, det 1 | halape_cove 569 m: **5.99** / 8.36, det 1 | 7.84 / 10.94 | FLAG det |
| s017^ | 1830 | 1:01.0 | ch1-halape | halape | halape_cove 579 m: **5.89** / 8.23, det 1 | halape_cove 536 m: **6.35** / 8.87, det 1 | 7.29 / 10.17 | FLAG det |
| s018 | 1893 | 1:03.1 | ch1-halape | halape | halape_cove 963 m: **2.1** / 2.93, det 1 | halape_cove 820 m: **2.75** / 3.84, det 1 | 3.77 / 5.26 | FLAG det |
| s019 | 1990 | 1:06.3 | ch1-halape | halape | halape_cove 1.0 km: **1.9** / 2.65 | halape_cove 884 m: **2.18** / 3.04, det 1 | 3.26 / 4.55 | FLAG det |
| s020 | 2127 | 1:10.9 | ch1-halape | halape | water (halape_cove) | halape_cove 867 m: **3.41** / 4.77, det 1 | 3.99 / 5.57 | FLAG det |
| s021 | 2264 | 1:15.5 | ch1-halape | halape | water (halape_cove) | halape_cove 726 m: **4.06** / 5.67, det 1 | 4.86 / 6.78 | FLAG det |
| s022 | 2342 | 1:18.1 | ch1-halape | halape | water (halape_cove) | halape_cove 729 m: **4** / 5.59, det 1 | 4.73 / 6.6 | FLAG det |
| s023 | 2480 | 1:22.7 | ch1-halape, ch1-photo1975 | halape | water (halape_cove) | halape_cove 786 m: **2.63** / 3.67, det 1 | 3.5 / 4.88 | FLAG det |
| s024^ | 2588 | 1:26.3 | ch1-halape, ch1-flank | halape | halape 6.8 km: **0.94** / 1.3 | halape 6.5 km: **0.98** / 1.37 | 1.22 / 1.7 |  |
| s024^ | 2588 | 1:26.3 | ch1-halape, ch1-flank | kilauea_sf | kilauea_coast 6.8 km: **1.29** / 1.95 | kilauea_coast 6.5 km: **1.35** / 2.04 | 1.69 / 2.54 |  |
| s024 | 2614 | 1:27.1 | ch1-flank | kilauea_sf | kilauea_coast 39.6 km: **0.2** / 0.3 | water (kilauea_sf) | - |  |
| s025 | 2743 | 1:31.4 | ch1-flank | kilauea_sf | kilauea_coast 38.0 km: **0.21** / 0.32 | water (kilauea_sf) | - |  |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **2.61** / 3.04, det 1 | pali 3.6 km: **1.74** / 2.04 (src 4.05) | 2.85 / 3.32 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.8** / 2.1 | pali 3.6 km: **1.7** / 1.98 (src 3.95) | 2.83 / 3.3 |  |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **2.81** / 3.28, det 1 | pali 3.6 km: **1.62** / 1.89 (src 3.76) | 2.81 / 3.28 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **2.35** / 2.74, det 1 | pali 3.6 km: **1.62** / 1.9 (src 3.78) | 2.81 / 3.28 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.5** / 1.76 | pali 3.6 km: **1.62** / 1.89 (src 3.77) | 3.15 / 3.67 |  |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.89** / 2.2 | pali 3.6 km: **1.61** / 1.87 (src 3.73) | 3.07 / 3.58 |  |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.39** / 1.62 | pali 3.6 km: **1.87** / 2.19 (src 4.35) | 2.96 / 3.45 |  |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.29** / 1.5 | pali 3.5 km: **2.12** / 2.48 (src 4.93), det 1 | 2.75 / 3.21 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.03** / 1.2 | pali 3.5 km: **2.07** / 2.41 (src 4.8), det 1 | 2.76 / 3.22 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **1.29** / 1.51 | pali 3.4 km: **2.09** / 2.43 (src 4.85), det 1 | 2.75 / 3.21 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **1.74** / 2.03 | pali 3.4 km: **2.08** / 2.43 (src 4.84), det 1 | 2.76 / 3.22 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **1.34** / 1.56 | pali 3.4 km: **2.04** / 2.38 (src 4.74), det 1 | 2.77 / 3.23 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **1.31** / 1.53 | pali 3.4 km: **2.06** / 2.4 (src 4.78), det 1 | 2.78 / 3.24 | FLAG det |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **1.27** / 1.49 | pali 3.4 km: **1.73** / 2.02 (src 4.02) | 2.78 / 3.25 |  |
| s025* | 2789 | 1:33.0 | ch1-oahu | pali | pali 10.4 km: **0.56** / 0.65 | pali_lookout 3.4 km: **0.59** / 0.82 (src 4.11) | 1.11 / 1.54 |  |
| s026 | 2889 | 1:36.3 | ch2-pali | pali | pali_lookout 2.5 km: **0.75** / 1.04 (src 5.21) | pali_lookout 1.0 km: **1.78** / 2.47 (src 12.35) | 3.69 / 5.13 |  |
| s027 | 2975 | 1:39.2 | ch2-pali | pali | pali 4.8 km: **1.1** / 1.28 | pali_lookout 3.4 km: **0.52** / 0.72 (src 3.59) | 2.28 / 3.17 |  |
| s028 | 3067 | 1:42.2 | ch2-pali | pali | pali_lookout 2.6 km: **0.82** / 1.14 (src 5.7) | pali_lookout 933 m: **1.91** / 2.66 (src 13.29) | 4.42 / 6.13 |  |
| s029 | 3148 | 1:44.9 | ch2-pali | pali | pali_lookout 2.4 km: **0.75** / 1.04 (src 5.22) | pali_lookout 853 m: **2.14** / 2.97 (src 14.85), det 1 | 4.52 / 6.28 | FLAG det |
| s030 | 3252 | 1:48.4 | ch2-pali | pali | water (oahu_nuuanu) | pali 6.0 km: **0.87** / 1.01 | 1.57 / 1.84 |  |
| s030^ | 3258 | 1:48.6 | ch2-pali, ch2-nuuanu | pali | oahu_nuuanu 10.4 km: **12.39** / 12.39, det 0.59 | pali 7.1 km: **0.76** / 0.88 | 2.96 / 3.46 | FLAG det |
| s030^ | 3258 | 1:48.6 | ch2-pali, ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 10.4 km: **12.42** / 12.42, det 0.59 | oahu_nuuanu 7.1 km: **18.38** / 18.38, det 0.97 | 45.77 / 45.77 | FLAG det |
| s030^ | 3266 | 1:48.9 | ch2-pali, ch2-nuuanu | pali | oahu_nuuanu 12.4 km: **10.74** / 10.74, det 0.29 | pali 8.7 km: **0.66** / 0.77 (src 1.54) | 18.91 / 18.91 | FLAG |
| s030^ | 3266 | 1:48.9 | ch2-pali, ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 12.4 km: **10.79** / 10.79, det 0.29 | oahu_nuuanu 8.7 km: **15.82** / 15.82, det 0.82 | 34.07 / 34.07 | FLAG |
| s031 | 3376 | 1:52.5 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 39.2 km: **3.94** / 3.94, det 0 | water (oahu_nuuanu) | - | FLAG |
| s032 | 3515 | 1:57.2 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 32.5 km: **4.75** / 4.75, det 0 | water (oahu_nuuanu) | 6.4 / 6.4 | FLAG |
| s033 | 3654 | 2:01.8 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 28.1 km: **5.21** / 5.21, det 0 | oahu_nuuanu 21.9 km: seabed / 6.74, det 0 | 0 / 8.23 | FLAG |
| s034 | 3820 | 2:07.3 | ch2-nuuanu | oahu_nuuanu | water (oahu_nuuanu) | oahu_nuuanu 37.6 km: seabed / 3.94 | 0 / 4.21 |  |
| s035 | 4050 | 2:15.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 225.9 km: seabed / 0.65 | oahu_nuuanu 175.9 km: seabed / 0.84 | 0 / 1.3 |  |
| s036 | 4185 | 2:19.5 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 33.1 km: **4.66** / 4.66, det 0 | oahu_nuuanu 27.1 km: seabed / 5.74, det 0 | 0 / 8.29 | FLAG |
| s037 | 4300 | 2:23.3 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 32.0 km: seabed / 4.78, det 0 | oahu_nuuanu 27.2 km: seabed / 5.71, det 0 | 0 / 8.36 | FLAG |
| s038 | 4381 | 2:26.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 19.7 km: seabed / 7.09, det 0 | oahu_nuuanu 16.1 km: seabed / 8.93, det 0 | 0 / 12.86 | FLAG |
| s039 | 4441 | 2:28.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 18.2 km: seabed / 7.67, det 0 | oahu_nuuanu 15.1 km: seabed / 10.18, det 0.02 | 0 / 13.83 | FLAG |
| s040 | 4500 | 2:30.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 17.4 km: seabed / 7.99, det 0 | oahu_nuuanu 14.7 km: seabed / 10.17, det 0.05 | 0 / 14.12 | FLAG |
| s041 | 4590 | 2:33.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 181.2 km: seabed / 0.84 | oahu_nuuanu 156.7 km: seabed / 1.07 | 0 / 1.44 |  |
| s042 | 4723 | 2:37.4 | ch2-chain | main_chain | sky | sky | - |  |
| s043 | 4835 | 2:41.2 | ch2-chain | main_chain | sky | sky | - |  |
| s044^ | 4937 | 2:44.6 | ch2-chain, ch2-kilauea | main_chain | main_chain 174.7 km: **2.77** / 2.77, det 0 | main_chain 153.6 km: **3.19** / 3.19, det 0 | 4.4 / 4.4 | FLAG |
| s044^ | 4937 | 2:44.6 | ch2-chain, ch2-kilauea | bigisland | hero 174.5 km: **2.08** / 0.96, det 0 | hero 153.4 km: **2.39** / 1.1, det 0 | 3.26 / 1.51 | FLAG |
| s044 | 4958 | 2:45.3 | ch2-kilauea | bigisland | hero 86.1 km: **4.11** / 1.9, det 0 | hero 73.2 km: **4.87** / 2.25, det 0 | 7.15 / 3.3 | FLAG |
| s045 | 5097 | 2:49.9 | ch2-kilauea | bigisland | hero 43.0 km: **8.2** / 3.79, det 0 | water (hero) | - | FLAG |
| s046 | 5205 | 2:53.5 | ch2-kilauea | bigisland | hero 37.1 km: **9.47** / 4.37, det 0 | water (hero) | - | FLAG |
| s046^ | 5255 | 2:55.2 | ch2-kilauea | bigisland | hero 35.5 km: **9.9** / 4.57, det 0 | water (hero) | - | FLAG |
| s047 | 5315 | 2:57.2 | ch2-kilauea | bigisland | hero 159.2 km: **2.41** / 1.11, det 0 | hero 141.4 km: **2.73** / 1.26, det 0 | 3.13 / 1.45 | FLAG |
| s048 | 5412 | 3:00.4 | ch2-kilauea | bigisland | hero 124.0 km: **3.05** / 1.4, det 0 | water (hero) | 4.41 / 2.03 | FLAG |
| s049^ | 5481 | 3:02.7 | ch3-stand-a, ch3-gauge, card-3 | bigisland | hero 41.4 km: **11.16** / 5.13, det 0 | water (hero) | - | FLAG |
| s049 | 5528 | 3:04.3 | ch3-stand-a, ch3-gauge | bigisland | hero 22.7 km: seabed / 10.49, det 0 | water (hero) | - | FLAG |
| s050 | 5628 | 3:07.6 | ch3-chain-ridge, ch3-gauge | main_chain | sky | sky | - |  |
| s051 | 5717 | 3:10.6 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | main_chain | main_chain 122.6 km: seabed / 8.6, det 0 | main_chain 89.6 km: seabed / 11.81, det 0 | 0 / 15.66 | FLAG |
| s051 | 5717 | 3:10.6 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | bigisland | hero 123.4 km: seabed / 2.91 | hero 89.9 km: seabed / 3.99 | 0 / 5.3 |  |
| s051^ | 5725 | 3:10.8 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | main_chain | main_chain 70.2 km: **19.2** / 19.2, det 0 | main_chain 53.9 km: seabed / 24.84, det 0 | 0 / 34.79 | FLAG |
| s051^ | 5725 | 3:10.8 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | bigisland | hero 70.3 km: **15.08** / 6.93, det 0 | hero 54.0 km: seabed / 8.41, det 0 | 0 / 11.83 | FLAG |
| s051^ | 5745 | 3:11.5 | ch3-stand-c, ch3-gauge | bigisland | hero 29.1 km: seabed / 21.41, det 0 | hero 19.1 km: seabed / 32.57, det 0 | 0 / 43.16 | FLAG |
| s052 | 5896 | 3:16.5 | ch3-stand-c, ch3-gauge | bigisland | hero 261.3 km: **1.96** / 0.9 | hero 230.3 km: **2.25** / 1.03, det 0 | 2.34 / 1.33 | FLAG |
| s053 | 6012 | 3:20.4 | ch3-stand-c, ch3-gauge | bigisland | hero 240.4 km: **1.81** / 0.84 | hero 211.4 km: seabed / 0.95 | 0 / 1.25 |  |
| s054 | 6139 | 3:24.6 | ch3-stand-c, ch3-gauge | bigisland | hero 52.5 km: seabed / 3.65 | hero 48.3 km: seabed / 3.99 | 0 / 5.55 |  |
| s055 | 6251 | 3:28.4 | ch3-stand-c, ch3-gauge | bigisland | hero 54.7 km: seabed / 3.5 | hero 46.3 km: seabed / 4.17, det 0 | 0 / 5.66 | FLAG |
| s056 | 6362 | 3:32.1 | ch3-stand-c, ch3-gauge | bigisland | hero 49.0 km: seabed / 3.91 | hero 42.8 km: seabed / 4.51, det 0 | 0 / 6.1 | FLAG |
| s057 | 6504 | 3:36.8 | ch3-trench, ch3-gauge | bigisland | hero 74.8 km: seabed / 2.29 | hero 55.3 km: seabed / 3.13 | 0 / 4.58 |  |
| s058 | 6620 | 3:40.7 | ch3-trench | bigisland | hero 66.4 km: seabed / 2.61 | hero 49.5 km: seabed / 3.53 | 0 / 5.42 |  |
| s058^ | 6672 | 3:42.4 | ch3-trench | bigisland | hero 57.0 km: seabed / 3.17 | hero 43.1 km: seabed / 4.26, det 0 | 0 / 6.86 | FLAG |
| s059 | 6723 | 3:44.1 | ch3-everest-cmp | bigisland | sky | hero 86.8 km: seabed / 5.72, det 0 | 0 / 8.55 | FLAG |
| s060 | 6816 | 3:47.2 | ch3-everest-cmp | bigisland | sky | hero 87.7 km: seabed / 6.25, det 0 | 0 / 8.9 | FLAG |
| s061^ | 6915 | 3:50.5 | ch3-everest-cmp | bigisland | sky | hero 99.4 km: **14.18** / 6.51, det 0 | 0 / 9.23 | FLAG |
| s061 | 6960 | 3:52.0 | ch3-everest-cmp | bigisland | hero 99.3 km: **13.1** / 6.02, det 0 | hero 76.6 km: seabed / 7.8, det 0 | 0 / 11.14 | FLAG |
| s062 | 7082 | 3:56.1 | ch3-everest-cmp | bigisland | hero 87.1 km: seabed / 7.24, det 0 | hero 61.8 km: seabed / 10.15, det 0 | 0 / 26.9 | FLAG |
| s063 | 7151 | 3:58.4 | ch3-everest-cmp | bigisland | hero 87.2 km: seabed / 7.78, det 0 | hero 66.2 km: seabed / 10.26, det 0 | 0 / 25.61 | FLAG |
| s064 | 7246 | 4:01.5 | ch3-gag-everest | everest | everest_wide 22.7 km: **10.55** / 10.55, det 0 | everest 10.2 km: **8.09** / 3.89, det 0.62 | 20.74 / 15.03 | FLAG |
| s064^ | 7274 | 4:02.5 | ch3-gag-everest | everest | everest_wide 23.1 km: **9.21** / 9.21, det 0 | everest 9.9 km: **12.75** / 6.12, det 0.67 | 19.32 / 17.28 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 7.2 km: **2.37** / 3.57, det 0.96 | maunakea 5.7 km: **3.13** / 4.71, det 1 | 3.84 / 5.78 | FLAG det |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 7.2 km: **2.37** / 3.57, det 0.96 | maunakea 5.7 km: **3.13** / 4.71, det 1 | 3.84 / 5.78 | FLAG det |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 7.2 km: **2.37** / 3.57, det 0.96 | maunakea 5.6 km: **3.13** / 4.71, det 1 | 3.84 / 5.79 | FLAG det |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 7.2 km: **2.37** / 3.57, det 0.96 | maunakea 5.6 km: **3.13** / 4.72, det 1 | 3.84 / 5.79 | FLAG det |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 7.2 km: **2.37** / 3.57, det 0.96 | maunakea 5.6 km: **3.13** / 4.72, det 1 | 3.84 / 5.79 | FLAG det |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 7.2 km: **2.37** / 3.57, det 0.96 | maunakea 5.6 km: **3.13** / 4.72, det 1 | 3.84 / 5.79 | FLAG det |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 7.6 km: **2.24** / 3.38, det 0.93 | maunakea 5.5 km: **3.47** / 5.23, det 1 | 4.65 / 7.01 | FLAG det |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 7.6 km: **2.24** / 3.38, det 0.93 | maunakea 5.5 km: **3.45** / 5.21, det 1 | 4.07 / 6.13 | FLAG det |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 7.8 km: **2.18** / 3.29, det 0.91 | maunakea 5.5 km: **3.35** / 5.05, det 1 | 4.06 / 6.12 | FLAG det |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 7.8 km: **2.2** / 3.31, det 0.91 | maunakea 5.5 km: **3.38** / 5.1, det 1 | 4.04 / 6.08 | FLAG det |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 8.2 km: **2.09** / 3.15, det 0.88 | maunakea 5.5 km: **3.19** / 4.81, det 1 | 4.05 / 6.11 | FLAG det |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | sky | maunakea 5.5 km: **3.17** / 4.78, det 1 | 4.23 / 6.37 | FLAG det |
| s065* | 7414 | 4:07.1 | ch3-gag-everest-b | everest | everest_wide 23.4 km: **8.6** / 8.6, det 0 | everest 9.5 km: **11.15** / 5.35, det 0.71 | 35.71 / 17.14 | FLAG |
| s065^ | 7416 | 4:07.2 | ch3-gag-everest-b | everest | everest_wide 23.4 km: **8.6** / 8.6, det 0 | everest 9.5 km: **11.15** / 5.35, det 0.71 | 35.71 / 17.14 | FLAG |
| s066 | 7457 | 4:08.6 | ch3-maunaloa | bigisland | hero 141.4 km: **2.96** / 1.36, det 0 | hero 117.8 km: **3.55** / 1.63, det 0 | 4.69 / 2.36 | FLAG |
| s067 | 7575 | 4:12.5 | ch3-maunaloa | bigisland | hero 148.0 km: **2.81** / 1.3, det 0 | hero 124.3 km: **3.36** / 1.55, det 0 | 0 / 2.15 | FLAG |
| s068^ | 7654 | 4:15.1 | ch3-maunaloa | bigisland | hero 138.5 km: **3** / 1.39, det 0 | hero 116.5 km: **3.61** / 1.67, det 0 | 3.83 / 2.4 | FLAG |
| s068 | 7699 | 4:16.6 | ch3-maunaloa | bigisland | hero 147.2 km: **2.84** / 1.31, det 0 | hero 121.1 km: **3.47** / 1.6, det 0 | 4.08 / 2.25 | FLAG |
| s069 | 7794 | 4:19.8 | ch3-today-half | bigisland | hero 195.6 km: **2.13** / 0.98, det 0 | hero 182.4 km: **2.29** / 1.06, det 0 | 2.67 / 1.24 | FLAG |
| s070^ | 7841 | 4:21.4 | ch3-today-half | bigisland | hero 185.3 km: **2.25** / 1.03, det 0 | hero 172.6 km: **2.43** / 1.12, det 0 | 2.81 / 1.3 | FLAG |
| s070 | 7880 | 4:22.7 | ch3-ml-base | bigisland | hero 49.8 km: **7.46** / 3.45, det 0 | hero 38.9 km: **9.61** / 4.44, det 0 | 11.95 / 6.56 | FLAG |
| s070^ | 7889 | 4:23.0 | ch3-ml-base | bigisland | hero 44.0 km: **8.44** / 3.9, det 0 | hero 34.2 km: **10.92** / 5.05, det 0 | 11.92 / 7.95 | FLAG |
| s071 | 7994 | 4:26.5 | ch3-hotspot | bigisland | hero 28.8 km: **11.68** / 5.39, det 0 | hero 21.6 km: **15.7** / 7.26, det 0 | 26.31 / 12.16 | FLAG |
| s071^ | 7999 | 4:26.6 | ch3-hotspot | bigisland | hero 28.7 km: **11.69** / 5.4, det 0 | hero 21.5 km: **15.86** / 7.33, det 0 | 26.44 / 12.22 | FLAG |
| s072 | 8102 | 4:30.1 | ch3-hotspot | bigisland | hero 31.8 km: seabed / 4.86, det 0 | hero 24.2 km: seabed / 6.47, det 0 | 0 / 11.06 | FLAG |
| s073 | 8213 | 4:33.8 | ch3-chain-sheet | main_chain | sky | sky | - |  |
| s074 | 8362 | 4:38.7 | ch3-chain-sheet | main_chain | sky | sky | - |  |
| s075 | 8499 | 4:43.3 | ch3-chain-sheet | main_chain | sky | sky | - |  |
| s076 | 8594 | 4:46.5 | ch3-chain-sheet | main_chain | main_chain 302.1 km: **1.75** / 1.75 | water (main_chain) | - |  |
| s076^ | 8600 | 4:46.7 | ch3-chain-sheet | main_chain | main_chain 300.3 km: **1.76** / 1.76 | water (main_chain) | - |  |
| s077 | 8700 | 4:50.0 | ch3-kohala | kohala | kohala 12.1 km: seabed / 2.91 | kohala 9.0 km: seabed / 4 | 0 / 6.5 |  |
| s078 | 8826 | 4:54.2 | ch3-kohala | kohala | water (kohala) | water (kohala) | - |  |
| s079 | 8937 | 4:57.9 | ch3-kohala | kohala | kohala 8.3 km: seabed / 4.07, det 0.87 | kohala 6.4 km: seabed / 5.31, det 1 | 0 / 8.37 | FLAG det |
| s079^ | 8993 | 4:59.8 | ch3-kohala | kohala | kohala 5.7 km: seabed / 5.89, det 1 | kohala 4.7 km: seabed / 7.25, det 1 | 0 / 10.9 | FLAG det |
| s080 | 9053 | 5:01.8 | ch3-born-here | main_chain | main_chain 196.6 km: **2.69** / 2.69, det 0 | main_chain 173.1 km: **3.07** / 3.07, det 0 | 3.53 / 3.53 | FLAG |
| s080^ | 9070 | 5:02.3 | ch3-born-here | main_chain | main_chain 195.2 km: **2.71** / 2.71, det 0 | main_chain 171.9 km: **3.1** / 3.1, det 0 | 3.56 / 3.56 | FLAG |
| s081 | 9149 | 5:05.0 | ch3-born-here | main_chain | sky | sky | - |  |
| s082 | 9273 | 5:09.1 | ch3-born-here | main_chain | water (main_chain) | water (main_chain) | - |  |
| s083 | 9414 | 5:13.8 | ch3-born-here | main_chain | sky | sky | - |  |

## Region verification cameras (regions.json 'view'): 28, 8 flagged

| region | cam agl km | centre | lower third | band max col / h | flag |
|---|---|---|---|---|---|
| bigisland | 30.8333 | bigisland 121.6 km: **3.65** / 1.68, det 0 | bigisland 89.5 km: seabed / 2.3 | 7.07 / 3.81 | FLAG |
| mauinui | 30.122 | mauinui 88.5 km: **1.98** / 1.98 | water (mauinui) | 2.98 / 2.98 |  |
| oahu_nuuanu | 26.3858 | oahu_nuuanu 131.0 km: seabed / 1.25 | water (oahu_nuuanu) | 0 / 2.53 |  |
| kauai | 14 | kauai 63.0 km: **1.5** / 1.5 | water (kauai) | - |  |
| main_chain | 144 | sky | main_chain 379.3 km: seabed / 1.6 | 2.32 / 2.52 |  |
| kilauea_sf | 6 | kilauea_coast 34.2 km: **0.27** / 0.4 | water (kilauea_sf) | 2.82 / 2.82 |  |
| kilauea_coast | 1.5 | kilauea_coast 8.0 km: **0.92** / 1.38 | water (kilauea_coast) | - |  |
| halape | 1.2 | halape_cove 4.0 km: **0.39** / 0.54 | water (halape_cove) | 2.23 / 3.11 |  |
| halape_cove | 0.25 | halape_cove 954 m: **1.12** / 1.56 | water (halape_cove) | - |  |
| holei | 0.35 | water (holei) | water (holei) | - |  |
| pali | 0.03 | pali_lookout 1.9 km: **0.74** / 1.03 | pali_lookout 444 m: **3.82** / 5.3 (src 26.51), det 1 | 43.48 / 60.36 | FLAG det |
| pali_lookout | 0.03 | pali_lookout 1.9 km: **0.74** / 1.03 | pali_lookout 444 m: **3.82** / 5.3 (src 26.51), det 1 | 43.48 / 60.36 | FLAG det |
| waimea | 2.1656 | waimea 10.3 km: **0.84** / 1.62 | waimea 7.8 km: **1.06** / 2.06 | 2.36 / 4.57 |  |
| maunakea | 1.5643 | water (bigisland) | maunakea 3.8 km: **1.34** / 2.02 | 2.43 / 3.66 |  |
| kamaehu | 2.5 | kamaehu 34.6 km: seabed / 2.69 | water (kamaehu) | - |  |
| kohala | 2 | kohala 24.3 km: seabed / 1.57 | kohala 9.0 km: seabed / 4.19, det 0.79 | 0 / 9.28 | FLAG det |
| nwhi_chain | 263 | sky | sky | - |  |
| nihoa | 0.7 | nihoa 3.8 km: **12.94** / 8.63, det 1 | water (nihoa) | - | FLAG det |
| lalo | 14 | water (lalo) | water (lalo) | - |  |
| lalo_2018_before | 14 | water (lalo_2018_before) | water (lalo_2018_before) | - |  |
| lalo_2018_after | 14 | water (lalo_2018_after) | water (lalo_2018_after) | - |  |
| laperouse | 0.09 | laperouse 667 m: **861.75** / 73.16 (src 735.99), det 1 | water (laperouse) | - | FLAG det |
| gardner | 1.2 | water (gardner) | water (gardner) | - |  |
| nwhi_west | 94.6781 | nwhi_west 317.7 km: seabed / 2.02 | nwhi_west 232.7 km: seabed / 2.78 | 0 / 4.35 |  |
| midway | 7 | water (midway) | midway 12.1 km: **1.18** / 1.7 | 1.22 / 1.76 |  |
| kure | 6 | water (kure) | water (kure) | - |  |
| everest_wide | 10.3706 | everest_wide 33.5 km: **7.19** / 7.19, det 0 | everest_wide 24.3 km: **6.3** / 6.3, det 0 | 27.57 / 27.57 | FLAG |
| everest | 4.3687 | everest_wide 20.0 km: **8.99** / 8.99, det 0 | everest 5.4 km: **12.54** / 6.02, det 1 | 15.71 / 10.86 | FLAG |
