# ep02 texel audit (before, live 2026-11-15, with closest frames)

2026-11-15T15:01, 1920x1080. Each cell: visible layer, distance from the camera, then **colour px** / height px = screen pixels covered by one colour texel (at its effective resolution: the texel or the imagery, whichever is coarser) and by one height texel, along the least foreshortened direction. Flag: colour > 2 px or height > 4 px at the centre or the lower third (y = 2/3); 'seabed' = ground below -6 m, where the stage draws its own seabed material instead of the colour map (only the height counts). A seg id with * = a shot no segment middle falls in, sampled at its own middle; with ^ = the closest (worst) frame of the shot named, scanned every few frames. 'src' = height px at the source's own resolution where the source is only interpolated. Band max = worst of 15 points over y 70-90 %. Tool: engine/www/ep/ep02/tools/texel_audit.js.

## Film frames (one per segment, plus the closest frame of each shot): 111 sampled, 111 on terrain, 82 flagged

| seg | frame | time | shot | region | centre | lower third | band max col / h | flag |
|---|---|---|---|---|---|---|---|---|
| s001 | 56 | 0:01.9 | ch1-demo | mauinui | bigisland 112.3 km: **4.45** / 2.05 | bigisland 86.6 km: seabed / 2.7 | 7.92 / 4.17 | FLAG |
| s002 | 155 | 0:05.2 | ch1-demo | mauinui | bigisland 91.2 km: **5.5** / 2.54 | bigisland 74.9 km: seabed / 3.11 | 0 / 4.68 | FLAG |
| s003 | 261 | 0:08.7 | ch1-demo | mauinui | bigisland 89.2 km: seabed / 2.63 | bigisland 72.6 km: seabed / 3.25 | 0 / 4.94 |  |
| s004^ | 331 | 0:11.0 | ch1-demo | mauinui | bigisland 79.0 km: **6.29** / 2.9 | bigisland 62.8 km: **7.88** / 3.64 | 10.76 / 4.97 | FLAG |
| s004 | 384 | 0:12.8 | ch1-demo | mauinui | water (mauinui) | water (mauinui) | 5.23 / 5.23 |  |
| s005 | 494 | 0:16.5 | ch1-demo | mauinui | water (mauinui) | mauinui 41.6 km: seabed / 3.2 | 5.16 / 5.16 |  |
| s006 | 572 | 0:19.1 | ch1-demo | mauinui | water (mauinui) | mauinui 41.9 km: seabed / 3.2 | 5.17 / 5.17 |  |
| s007 | 684 | 0:22.8 | ch1-ice | mauinui | mauinui 40.0 km: seabed / 2.96 | mauinui 21.9 km: seabed / 5.44 | 10.29 / 10.29 | FLAG |
| s007^ | 743 | 0:24.8 | ch1-ice | mauinui | mauinui 17.3 km: seabed / 5.95 | mauinui 6.8 km: seabed / 15.18 | 34.42 / 34.42 | FLAG |
| s007^ | 745 | 0:24.8 | ch1-ride | mauinui | mauinui 14.6 km: **10.34** / 10.34 | mauinui 163 m: seabed / 876.81 | 0 / 2462.49 | FLAG |
| s008 | 781 | 0:26.0 | ch1-ride | mauinui | mauinui 14.6 km: **10.44** / 10.44 | mauinui 167 m: seabed / 863.75 | 0 / 2425.17 | FLAG |
| s009 | 863 | 0:28.8 | ch1-ride | mauinui | mauinui 14.6 km: **10.85** / 10.85 | mauinui 183 m: seabed / 819.24 | 0 / 2293.95 | FLAG |
| s010 | 965 | 0:32.2 | ch1-ride | mauinui | mauinui 16.5 km: **6.3** / 6.3 | mauinui 8.3 km: **13.5** / 13.5 | 24.61 / 24.61 | FLAG |
| s011 | 1089 | 0:36.3 | ch1-ride | mauinui | mauinui 4.0 km: seabed / 21.56 | mauinui 3.0 km: seabed / 29.42 | 0 / 64.45 | FLAG |
| s012 | 1208 | 0:40.3 | ch1-ride | mauinui | mauinui 43.7 km: seabed / 2.85 | mauinui 28.5 km: seabed / 4.39 | 0 / 7.45 | FLAG |
| s013 | 1315 | 0:43.8 | ch1-ride | mauinui | mauinui 44.0 km: seabed / 2.61 | mauinui 29.0 km: seabed / 3.99 | 7.06 / 7.06 |  |
| s014 | 1412 | 0:47.1 | ch1-bigisland | kilauea_sf | kilauea_sf 31.3 km: **1.51** / 1.51 | water (kilauea_sf) | - |  |
| s015 | 1511 | 0:50.4 | ch1-bigisland | kilauea_sf | kilauea_sf 7.6 km: **8.51** / 8.51 | kilauea_sf 6.2 km: **10.45** / 10.45 | 14.86 / 14.86 | FLAG |
| s015^ | 1526 | 0:50.9 | ch1-bigisland, ch1-halape | kilauea_sf | kilauea_sf 2.6 km: **33.89** / 33.89 | kilauea_sf 2.1 km: **42.16** / 42.16 | 56.28 / 56.28 | FLAG |
| s015^ | 1526 | 0:50.9 | ch1-bigisland, ch1-halape | halape | halape 2.6 km: **32.12** / 10.86 | halape 2.1 km: **39.49** / 13.36 | 53.03 / 17.94 | FLAG |
| s016 | 1653 | 0:55.1 | ch1-halape | halape | water (halape) | halape 974 m: **118.53** / 40.09 | 141.32 / 47.8 | FLAG |
| s017 | 1787 | 0:59.6 | ch1-halape | halape | halape 845 m: **145.67** / 49.27 | halape 768 m: **160.34** / 54.23 | 186.18 / 62.97 | FLAG |
| s018 | 1893 | 1:03.1 | ch1-halape | halape | water (halape) | halape 907 m: **127.23** / 43.03 | 151.01 / 51.07 | FLAG |
| s019 | 1990 | 1:06.3 | ch1-halape | halape | water (halape) | halape 965 m: **110.84** / 37.49 | 133.18 / 45.04 | FLAG |
| s020 | 2127 | 1:10.9 | ch1-halape | halape | water (halape) | halape 868 m: **142.07** / 48.05 | 165.25 / 55.89 | FLAG |
| s021 | 2264 | 1:15.5 | ch1-halape | halape | water (halape) | water (halape) | 198.15 / 67.02 |  |
| s022 | 2342 | 1:18.1 | ch1-halape | halape | water (halape) | halape 732 m: **165.45** / 55.96 | 194.36 / 65.74 | FLAG |
| s023 | 2480 | 1:22.7 | ch1-halape, ch1-photo1975 | halape | water (halape) | halape 786 m: **109.37** / 36.99 | 144.46 / 48.86 | FLAG |
| s023^ | 2550 | 1:25.0 | ch1-halape | halape | water (halape) | halape 327 m: **234.08** / 79.17 | 342.09 / 115.7 | FLAG |
| s024^ | 2588 | 1:26.3 | ch1-halape, ch1-flank | halape | halape 6.8 km: **7.88** / 2.67 | halape 6.5 km: **8.2** / 2.77 | 10.14 / 3.43 | FLAG |
| s024^ | 2588 | 1:26.3 | ch1-halape, ch1-flank | kilauea_sf | kilauea_sf 6.8 km: **8.36** / 8.36 | kilauea_sf 6.5 km: **8.71** / 8.71 | 10.75 / 10.75 | FLAG |
| s024 | 2614 | 1:27.1 | ch1-flank | kilauea_sf | kilauea_sf 39.6 km: **1.27** / 1.27 | water (kilauea_sf) | - |  |
| s025 | 2743 | 1:31.4 | ch1-flank | kilauea_sf | kilauea_sf 38.0 km: **1.35** / 1.35 | water (kilauea_sf) | - |  |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **10.17** / 3.37 | pali 3.6 km: **11.93** / 3.95 | 22.94 / 7.6 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **7.87** / 2.61 | pali 3.6 km: **11.69** / 3.87 | 23.02 / 7.63 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **11.03** / 3.65 | pali 3.6 km: **11.25** / 3.73 | 23.1 / 7.65 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **7.47** / 2.48 | pali 3.6 km: **11.28** / 3.74 | 23.01 / 7.62 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **11.44** / 3.79 | pali 3.6 km: **11.27** / 3.73 | 22.94 / 7.6 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **7.31** / 2.42 | pali 3.6 km: **11.23** / 3.72 | 22.95 / 7.6 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **7.35** / 2.43 | pali 3.6 km: **12.89** / 4.27 | 22.95 / 7.6 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.6 km: **8.85** / 2.93 | pali 3.5 km: **14.19** / 4.7 | 22.96 / 7.61 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **10.85** / 3.59 | pali 3.4 km: **14.66** / 4.86 | 22.97 / 7.61 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **12.05** / 3.99 | pali 3.4 km: **14.79** / 4.9 | 22.97 / 7.61 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **7.45** / 2.47 | pali 3.4 km: **14.81** / 4.91 | 22.98 / 7.61 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **9.53** / 3.16 | pali 3.4 km: **14.32** / 4.74 | 22.98 / 7.61 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **7.41** / 2.45 | pali 3.4 km: **14.42** / 4.78 | 22.99 / 7.62 | FLAG |
| s025^ | 2756 | 1:31.9 | ch1-oahu | pali | pali 5.5 km: **15.12** / 5.01 | pali 3.4 km: **12.54** / 4.15 | 22.97 / 7.61 | FLAG |
| s025* | 2789 | 1:33.0 | ch1-oahu | pali | pali 10.4 km: **3.85** / 1.28 | pali 3.4 km: **12.3** / 4.08 | 23.11 / 7.66 | FLAG |
| s026 | 2889 | 1:36.3 | ch2-pali | pali | pali 2.5 km: **15.01** / 4.97 | pali 1.0 km: **36.46** / 12.08 | 76.08 / 25.21 | FLAG |
| s027 | 2975 | 1:39.2 | ch2-pali | pali | pali 4.8 km: **7.58** / 2.51 | pali 3.4 km: **10.78** / 3.57 | 44.27 / 14.67 | FLAG |
| s028 | 3067 | 1:42.2 | ch2-pali | pali | pali 2.6 km: **14.04** / 4.65 | pali 938 m: **39.43** / 13.06 | 103.08 / 34.15 | FLAG |
| s029 | 3148 | 1:44.9 | ch2-pali | pali | pali 2.5 km: **15.55** / 5.15 | pali 857 m: **43.84** / 14.52 | 100.81 / 33.4 | FLAG |
| s029^ | 3176 | 1:45.9 | ch2-pali | pali | pali 2.4 km: **15.59** / 5.17 | pali 847 m: **44.62** / 14.78 | 91.17 / 30.2 | FLAG |
| s030 | 3252 | 1:48.4 | ch2-pali | pali | water (oahu_nuuanu) | pali 6.1 km: **5.84** / 1.94 | 10.93 / 3.62 | FLAG |
| s030^ | 3258 | 1:48.6 | ch2-pali, ch2-nuuanu | pali | oahu_nuuanu 10.2 km: **12.66** / 12.66 | pali 6.8 km: **5.35** / 1.77 | 19.77 / 6.55 | FLAG |
| s030^ | 3258 | 1:48.6 | ch2-pali, ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 10.2 km: **12.69** / 12.69 | oahu_nuuanu 6.8 km: **18.65** / 18.65 | 48.1 / 48.1 | FLAG |
| s031 | 3376 | 1:52.5 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 39.2 km: **3.94** / 3.94 | water (oahu_nuuanu) | - | FLAG |
| s032 | 3515 | 1:57.2 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 32.5 km: **4.75** / 4.75 | water (oahu_nuuanu) | 6.4 / 6.4 | FLAG |
| s033 | 3654 | 2:01.8 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 28.3 km: **5.17** / 5.17 | oahu_nuuanu 22.0 km: seabed / 6.72 | 0 / 8.22 | FLAG |
| s034 | 3820 | 2:07.3 | ch2-nuuanu | oahu_nuuanu | water (oahu_nuuanu) | oahu_nuuanu 38.0 km: seabed / 3.89 | 0 / 4.17 |  |
| s035 | 4050 | 2:15.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 225.9 km: seabed / 0.65 | oahu_nuuanu 175.9 km: seabed / 0.84 | 0 / 1.3 |  |
| s036 | 4185 | 2:19.5 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 32.8 km: **4.75** / 4.75 | oahu_nuuanu 26.9 km: **5.77** / 5.77 | 0 / 8.27 | FLAG |
| s037 | 4300 | 2:23.3 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 32.3 km: seabed / 4.74 | oahu_nuuanu 27.0 km: seabed / 5.77 | 0 / 9.49 | FLAG |
| s038 | 4381 | 2:26.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 19.7 km: seabed / 7.09 | oahu_nuuanu 16.1 km: seabed / 8.93 | 0 / 12.86 | FLAG |
| s039 | 4441 | 2:28.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 18.2 km: seabed / 7.67 | oahu_nuuanu 15.1 km: seabed / 10.18 | 0 / 13.83 | FLAG |
| s040 | 4500 | 2:30.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 17.6 km: seabed / 7.9 | oahu_nuuanu 14.8 km: seabed / 10.11 | 0 / 13.91 | FLAG |
| s041 | 4590 | 2:33.0 | ch2-nuuanu | oahu_nuuanu | oahu_nuuanu 172.8 km: seabed / 0.88 | oahu_nuuanu 149.0 km: seabed / 1.15 | 0 / 1.48 |  |
| s042 | 4723 | 2:37.4 | ch2-chain | main_chain | sky | sky | - |  |
| s043 | 4835 | 2:41.2 | ch2-chain | main_chain | sky | sky | - |  |
| s044^ | 4937 | 2:44.6 | ch2-chain, ch2-kilauea | main_chain | main_chain 157.1 km: **3.06** / 3.06 | main_chain 137.5 km: **3.53** / 3.53 | 4.85 / 4.85 | FLAG |
| s044^ | 4937 | 2:44.6 | ch2-chain, ch2-kilauea | bigisland | hero 156.8 km: **2.29** / 1.06 | hero 137.2 km: **2.65** / 1.22 | 3.6 / 1.66 | FLAG |
| s044 | 4958 | 2:45.3 | ch2-kilauea | bigisland | hero 78.8 km: **4.49** / 2.07 | hero 67.0 km: **5.33** / 2.46 | 7.13 / 3.29 | FLAG |
| s045 | 5097 | 2:49.9 | ch2-kilauea | bigisland | hero 43.0 km: **8.2** / 3.79 | water (hero) | - | FLAG |
| s046 | 5205 | 2:53.5 | ch2-kilauea | bigisland | hero 37.1 km: **9.47** / 4.37 | water (hero) | - | FLAG |
| s046^ | 5255 | 2:55.2 | ch2-kilauea | bigisland | hero 35.5 km: **9.9** / 4.57 | water (hero) | - | FLAG |
| s047 | 5315 | 2:57.2 | ch2-kilauea | bigisland | hero 159.8 km: **2.4** / 1.11 | hero 141.9 km: **2.73** / 1.26 | 3.13 / 1.45 | FLAG |
| s048 | 5412 | 3:00.4 | ch2-kilauea | bigisland | hero 124.0 km: **3.05** / 1.4 | water (hero) | - | FLAG |
| s049^ | 5481 | 3:02.7 | ch3-stand-a, ch3-gauge, card-3 | bigisland | hero 41.4 km: **11.16** / 5.13 | water (hero) | - | FLAG |
| s049 | 5528 | 3:04.3 | ch3-stand-a, ch3-gauge | bigisland | hero 22.7 km: seabed / 10.49 | water (hero) | - | FLAG |
| s050 | 5628 | 3:07.6 | ch3-chain-ridge, ch3-gauge | main_chain | sky | sky | - |  |
| s051 | 5717 | 3:10.6 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | main_chain | main_chain 122.6 km: seabed / 8.6 | main_chain 89.6 km: seabed / 11.81 | 0 / 15.66 | FLAG |
| s051 | 5717 | 3:10.6 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | bigisland | hero 123.4 km: seabed / 2.91 | hero 89.9 km: seabed / 3.99 | 0 / 5.3 |  |
| s051^ | 5725 | 3:10.8 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | main_chain | main_chain 70.2 km: **19.2** / 19.2 | main_chain 53.9 km: seabed / 24.84 | 0 / 34.79 | FLAG |
| s051^ | 5725 | 3:10.8 | ch3-chain-ridge, ch3-stand-c, ch3-gauge | bigisland | hero 70.3 km: **15.08** / 6.93 | hero 54.0 km: seabed / 8.41 | 0 / 11.83 | FLAG |
| s051^ | 5745 | 3:11.5 | ch3-stand-c, ch3-gauge | bigisland | hero 29.1 km: seabed / 21.41 | hero 19.1 km: seabed / 32.57 | 0 / 43.16 | FLAG |
| s052 | 5896 | 3:16.5 | ch3-stand-c, ch3-gauge | bigisland | hero 261.3 km: **1.96** / 0.9 | hero 230.3 km: **2.25** / 1.03 | 2.34 / 1.33 | FLAG |
| s053 | 6012 | 3:20.4 | ch3-stand-c, ch3-gauge | bigisland | hero 240.4 km: **1.81** / 0.84 | hero 211.4 km: seabed / 0.95 | 0 / 1.25 |  |
| s054 | 6139 | 3:24.6 | ch3-stand-c, ch3-gauge | bigisland | hero 54.2 km: seabed / 3.53 | hero 49.0 km: seabed / 3.93 | 0 / 5.46 |  |
| s055 | 6251 | 3:28.4 | ch3-stand-c, ch3-gauge | bigisland | hero 55.9 km: seabed / 3.43 | hero 47.5 km: seabed / 4.06 | 0 / 5.73 | FLAG |
| s056 | 6362 | 3:32.1 | ch3-stand-c, ch3-gauge | bigisland | hero 50.2 km: seabed / 3.82 | hero 43.7 km: seabed / 4.48 | 0 / 6.25 | FLAG |
| s057 | 6504 | 3:36.8 | ch3-trench, ch3-gauge | bigisland | hero 74.8 km: seabed / 2.29 | hero 55.3 km: seabed / 3.13 | 0 / 4.58 |  |
| s058 | 6620 | 3:40.7 | ch3-trench | bigisland | hero 66.4 km: seabed / 2.61 | hero 49.5 km: seabed / 3.53 | 0 / 5.42 |  |
| s058^ | 6672 | 3:42.4 | ch3-trench | bigisland | hero 57.0 km: seabed / 3.17 | hero 43.1 km: seabed / 4.26 | 0 / 6.86 | FLAG |
| s059 | 6723 | 3:44.1 | ch3-everest-cmp | bigisland | sky | hero 86.8 km: seabed / 5.72 | 0 / 8.55 | FLAG |
| s060 | 6816 | 3:47.2 | ch3-everest-cmp | bigisland | sky | hero 87.7 km: seabed / 6.25 | 0 / 8.9 | FLAG |
| s061^ | 6915 | 3:50.5 | ch3-everest-cmp | bigisland | sky | hero 99.4 km: **14.18** / 6.51 | 0 / 9.23 | FLAG |
| s061 | 6960 | 3:52.0 | ch3-everest-cmp | bigisland | hero 99.3 km: **13.1** / 6.02 | hero 76.6 km: seabed / 7.8 | 0 / 11.14 | FLAG |
| s062 | 7082 | 3:56.1 | ch3-everest-cmp | bigisland | hero 87.1 km: seabed / 7.24 | hero 61.8 km: seabed / 10.15 | 0 / 26.9 | FLAG |
| s063 | 7151 | 3:58.4 | ch3-everest-cmp | bigisland | hero 87.2 km: seabed / 7.78 | hero 66.2 km: seabed / 10.26 | 0 / 25.61 | FLAG |
| s064 | 7246 | 4:01.5 | ch3-gag-everest | everest | everest_wide 22.7 km: **10.55** / 10.55 | everest 10.2 km: **8.09** / 3.89 | 20.74 / 15.03 | FLAG |
| s064^ | 7274 | 4:02.5 | ch3-gag-everest | everest | everest_wide 23.1 km: **9.21** / 9.21 | everest 9.9 km: **12.75** / 6.12 | 19.32 / 17.28 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 6.3 km: **14.72** / 4.8 | maunakea 4.6 km: **20.23** / 6.6 | 27.74 / 9.05 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 6.3 km: **14.73** / 4.8 | maunakea 4.6 km: **20.24** / 6.6 | 27.75 / 9.05 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 6.3 km: **14.73** / 4.8 | maunakea 4.6 km: **20.25** / 6.6 | 27.75 / 9.05 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 6.3 km: **14.73** / 4.8 | maunakea 4.6 km: **20.25** / 6.61 | 27.75 / 9.05 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 6.3 km: **14.73** / 4.81 | maunakea 4.6 km: **20.26** / 6.61 | 27.75 / 9.05 | FLAG |
| s065 | 7349 | 4:05.0 | ch3-gag-road | maunakea | maunakea 6.3 km: **14.74** / 4.81 | maunakea 4.6 km: **20.27** / 6.61 | 27.76 / 9.05 | FLAG |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 6.0 km: **15.31** / 4.99 | maunakea 4.7 km: **19.72** / 6.43 | 27.52 / 8.98 | FLAG |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 6.0 km: **15.3** / 4.99 | maunakea 4.4 km: **21.09** / 6.88 | 27.17 / 8.86 | FLAG |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 6.0 km: **15.27** / 4.98 | maunakea 4.4 km: **21.11** / 6.88 | 26.94 / 8.79 | FLAG |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 6.0 km: **15.27** / 4.98 | maunakea 4.6 km: **19.94** / 6.5 | 27.48 / 8.96 | FLAG |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 6.0 km: **15.27** / 4.98 | maunakea 4.6 km: **19.95** / 6.51 | 28.27 / 9.22 | FLAG |
| s065^ | 7398 | 4:06.6 | ch3-gag-road | maunakea | maunakea 6.0 km: **15.27** / 4.98 | maunakea 4.6 km: **19.98** / 6.52 | 31.11 / 10.15 | FLAG |
| s065* | 7414 | 4:07.1 | ch3-gag-everest-b | everest | everest_wide 23.4 km: **8.6** / 8.6 | everest 9.5 km: **11.15** / 5.35 | 35.71 / 17.14 | FLAG |
| s065^ | 7416 | 4:07.2 | ch3-gag-everest-b | everest | everest_wide 23.4 km: **8.6** / 8.6 | everest 9.5 km: **11.15** / 5.35 | 35.71 / 17.14 | FLAG |
| s066 | 7457 | 4:08.6 | ch3-maunaloa | bigisland | hero 141.4 km: **2.96** / 1.36 | hero 117.8 km: **3.55** / 1.63 | 4.69 / 2.36 | FLAG |
| s067 | 7575 | 4:12.5 | ch3-maunaloa | bigisland | hero 148.0 km: **2.81** / 1.3 | hero 124.3 km: **3.36** / 1.55 | 0 / 2.15 | FLAG |
| s068^ | 7654 | 4:15.1 | ch3-maunaloa | bigisland | hero 138.5 km: **3** / 1.39 | hero 116.5 km: **3.61** / 1.67 | 3.83 / 2.4 | FLAG |
| s068 | 7699 | 4:16.6 | ch3-maunaloa | bigisland | hero 147.2 km: **2.84** / 1.31 | hero 121.1 km: **3.47** / 1.6 | 4.08 / 2.25 | FLAG |
| s069 | 7794 | 4:19.8 | ch3-today-half | bigisland | hero 195.6 km: **2.13** / 0.98 | hero 182.4 km: **2.29** / 1.06 | 2.67 / 1.24 | FLAG |
| s070^ | 7841 | 4:21.4 | ch3-today-half | bigisland | hero 185.3 km: **2.25** / 1.03 | hero 172.6 km: **2.43** / 1.12 | 2.81 / 1.3 | FLAG |
| s070 | 7880 | 4:22.7 | ch3-ml-base | bigisland | hero 49.8 km: **7.46** / 3.45 | hero 38.9 km: **9.61** / 4.44 | 11.95 / 6.56 | FLAG |
| s070^ | 7889 | 4:23.0 | ch3-ml-base | bigisland | hero 44.0 km: **8.44** / 3.9 | hero 34.2 km: **10.92** / 5.05 | 11.92 / 7.95 | FLAG |
| s071 | 7994 | 4:26.5 | ch3-hotspot | bigisland | hero 28.8 km: **11.68** / 5.39 | hero 21.6 km: **15.7** / 7.26 | 26.31 / 12.16 | FLAG |
| s071^ | 7999 | 4:26.6 | ch3-hotspot | bigisland | hero 28.7 km: **11.69** / 5.4 | hero 21.5 km: **15.86** / 7.33 | 26.44 / 12.22 | FLAG |
| s072 | 8102 | 4:30.1 | ch3-hotspot | bigisland | hero 31.8 km: seabed / 4.86 | hero 24.2 km: seabed / 6.47 | 0 / 11.06 | FLAG |
| s073 | 8213 | 4:33.8 | ch3-chain-sheet | main_chain | sky | sky | - |  |
| s074 | 8362 | 4:38.7 | ch3-chain-sheet | main_chain | sky | sky | - |  |
| s075 | 8499 | 4:43.3 | ch3-chain-sheet | main_chain | sky | sky | - |  |
| s076 | 8594 | 4:46.5 | ch3-chain-sheet | main_chain | main_chain 302.1 km: **1.75** / 1.75 | water (main_chain) | - |  |
| s076^ | 8600 | 4:46.7 | ch3-chain-sheet | main_chain | main_chain 300.3 km: **1.76** / 1.76 | water (main_chain) | - |  |
| s077 | 8700 | 4:50.0 | ch3-kohala | kohala | kohala 12.1 km: seabed / 2.91 | kohala 9.0 km: seabed / 4 | 0 / 6.5 |  |
| s078 | 8826 | 4:54.2 | ch3-kohala | kohala | water (kohala) | water (kohala) | - |  |
| s079 | 8937 | 4:57.9 | ch3-kohala | kohala | kohala 8.3 km: seabed / 4.07 | kohala 6.4 km: seabed / 5.31 | 0 / 8.37 | FLAG |
| s079^ | 8993 | 4:59.8 | ch3-kohala | kohala | kohala 5.7 km: seabed / 5.89 | kohala 4.7 km: seabed / 7.25 | 0 / 10.9 | FLAG |
| s080 | 9053 | 5:01.8 | ch3-born-here | main_chain | main_chain 196.6 km: **2.69** / 2.69 | main_chain 173.1 km: **3.07** / 3.07 | 3.53 / 3.53 | FLAG |
| s080^ | 9070 | 5:02.3 | ch3-born-here | main_chain | main_chain 195.2 km: **2.71** / 2.71 | main_chain 171.9 km: **3.1** / 3.1 | 3.56 / 3.56 | FLAG |
| s081 | 9149 | 5:05.0 | ch3-born-here | main_chain | sky | sky | - |  |
| s082 | 9273 | 5:09.1 | ch3-born-here | main_chain | water (main_chain) | water (main_chain) | - |  |
| s083 | 9414 | 5:13.8 | ch3-born-here | main_chain | sky | sky | - |  |

## Region verification cameras (regions.json 'view'): 25, 11 flagged

| region | cam agl km | centre | lower third | band max col / h | flag |
|---|---|---|---|---|---|
| bigisland | 30.8333 | bigisland 121.6 km: **3.65** / 1.68 | bigisland 89.5 km: seabed / 2.3 | 7.07 / 3.81 | FLAG |
| mauinui | 30.122 | mauinui 88.5 km: **1.98** / 1.98 | water (mauinui) | 2.98 / 2.98 |  |
| oahu_nuuanu | 26.3858 | oahu_nuuanu 131.0 km: seabed / 1.25 | water (oahu_nuuanu) | 0 / 2.53 |  |
| kauai | 14 | kauai 63.0 km: **1.5** / 1.5 | water (kauai) | - |  |
| main_chain | 144 | sky | main_chain 379.3 km: seabed / 1.6 | 2.32 / 2.52 |  |
| kilauea_sf | 6 | kilauea_sf 34.2 km: **1.66** / 1.66 | water (kilauea_sf) | 2.82 / 2.82 |  |
| halape | 1.2 | halape 4.0 km: **11.12** / 3.76 | water (halape) | 18.66 / 6.31 | FLAG |
| holei | 0.35 | water (holei) | water (holei) | - |  |
| pali | 0.03 | pali 1.9 km: **15.01** / 4.97 | pali 453 m: **75.02** / 24.85 | 879.05 / 291.24 | FLAG |
| waimea | 2.1656 | waimea 10.3 km: **4.01** / 1.62 | waimea 7.8 km: **5.1** / 2.06 | 11.32 / 4.57 | FLAG |
| maunakea | 1.5424 | water (bigisland) | maunakea 3.8 km: **12.14** / 3.96 | 22.45 / 7.32 | FLAG |
| kamaehu | 2.5 | kamaehu 34.6 km: seabed / 2.69 | water (kamaehu) | - |  |
| kohala | 2 | kohala 24.3 km: seabed / 1.57 | kohala 9.0 km: seabed / 4.19 | 0 / 9.28 | FLAG |
| nwhi_chain | 263 | sky | sky | - |  |
| nihoa | 0.7 | nihoa 3.8 km: **12.94** / 8.63 | water (nihoa) | - | FLAG |
| lalo | 14 | water (lalo) | water (lalo) | - |  |
| lalo_2018_before | 14 | water (lalo_2018_before) | water (lalo_2018_before) | - |  |
| lalo_2018_after | 14 | water (lalo_2018_after) | water (lalo_2018_after) | - |  |
| laperouse | 0.09 | laperouse 667 m: **861.75** / 73.16 (src 735.99) | water (laperouse) | - | FLAG |
| gardner | 1.2 | water (gardner) | water (gardner) | - |  |
| nwhi_west | 94.6781 | nwhi_west 317.7 km: seabed / 2.02 | nwhi_west 232.7 km: seabed / 2.78 | 0 / 4.35 |  |
| midway | 7 | water (midway) | midway 12.1 km: **3.53** / 1.7 | 3.66 / 1.76 | FLAG |
| kure | 6 | water (kure) | water (kure) | - |  |
| everest_wide | 10.3706 | everest_wide 33.5 km: **7.19** / 7.19 | everest_wide 24.3 km: **6.3** / 6.3 | 27.57 / 27.57 | FLAG |
| everest | 4.3687 | everest_wide 20.0 km: **8.99** / 8.99 | everest 5.4 km: **12.54** / 6.02 | 15.71 / 10.86 | FLAG |
