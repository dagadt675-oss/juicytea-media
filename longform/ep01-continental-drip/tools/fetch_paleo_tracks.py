import json, urllib.request, concurrent.futures as cf
P = {'cape_horn': (-67.27, -55.98), 'cape_agulhas': (20.0, -34.83), 'kanyakumari': (77.55, 8.08), 'india_c': (79.0, 22.0),
     'cape_farewell': (-43.9, 59.77), 'florida_tip': (-80.9, 25.1), 'baja_tip': (-109.9, 22.9), 'korea_tip': (126.5, 34.3),
     'kamchatka_tip': (156.7, 50.9), 'tasmania_s': (146.8, -43.6), 'madagascar_s': (45.1, -25.6), 'south_pole': (0.0, -89.9),
     'nyc': (-74.0, 40.7), 'africa_c': (20.0, 5.0), 'samerica_c': (-60.0, -15.0), 'australia_c': (134.0, -25.0), 'antarctica_c': (40.0, -80.0)}
names = list(P); pts = ','.join(f'{P[n][0]},{P[n][1]}' for n in names)
def get(t):
    url = f'https://gws.gplates.org/reconstruct/reconstruct_points/?points={pts}&time={t}&model=MULLER2019'
    for a in range(4):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=60).read()); return t, d['coordinates']
        except Exception as e: err = e
    return t, None
out = {}
with cf.ThreadPoolExecutor(8) as ex:
    for t, c in ex.map(get, range(0, 201)):
        out[t] = c
tracks = {n: [out[t][i] if out[t] and i < len(out[t]) else None for t in range(0, 201)] for i, n in enumerate(names)}
json.dump(tracks, open('tracks.json', 'w'))
print({n: tracks[n][140] for n in names})
