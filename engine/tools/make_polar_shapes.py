#!/usr/bin/env python3
"""make_polar_shapes.py WWW_DIR
Rebuilds the two polar shapes chapter 2 compares, without antimeridian/pole seams:
  - geo/arctic_ocean.geojson: union of Natural Earth 10m marine polygons (Arctic Ocean + marginal seas, Hudson Bay/Strait,
    White Sea), merged in north-polar Lambert azimuthal equal-area, islands/holes < 4,000 km2 dropped, simplified 4 km
    (~12.7 M km2, vs the central-basin label polygon of ~4.9 M km2 that Natural Earth ships as 'Arctic Ocean').
  - ep/ep01/ch2_data.json continents.antarctica.rings: the same treatment in south-polar LAEA (~12.3 M km2).
Requires shapely + pyproj."""
import json, sys, numpy as np, shapely
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union
from pyproj import Transformer
www = sys.argv[1] if len(sys.argv) > 1 else 'engine/www'
def tf(lat0):
    crs = f'+proj=laea +lat_0={lat0} +lon_0=0 +datum=WGS84 +units=m'
    f = Transformer.from_crs('EPSG:4326', crs, always_xy=True); b = Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)
    return (lambda g: shapely.transform(g, lambda c: np.column_stack(f.transform(c[:, 0], c[:, 1])))), (lambda g: shapely.transform(g, lambda c: np.column_stack(b.transform(c[:, 0], c[:, 1]))))
def clean(U, tol, min_area):
    out = []
    for p in getattr(U, 'geoms', [U]):
        if p.area < min_area: continue
        out.append(Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area >= min_area]).simplify(tol, preserve_topology=True))
    return MultiPolygon(out)
def rings_ll(MP, bw):
    return [[[[round(float(x), 4), round(float(y), 4)] for x, y in np.array(bw(Polygon(r)).exterior.coords)] for r in [p.exterior] + list(p.interiors)] for p in MP.geoms]
fwN, bwN = tf(90)
m = json.load(open(f'{www}/geo/ne_10m_geography_marine_polys.geojson'))
want = {'Arctic Ocean', 'Beaufort Sea', 'Baffin Bay', 'Greenland Sea', 'Barents Sea', 'Chukchi Sea', 'Kara Sea', 'Laptev Sea', 'East Siberian Sea', 'Lincoln Sea', 'The North Western Passages', 'Amundsen Gulf', 'Viscount Melville Sound', "M'Clure Strait", 'Dmitriy Laptev Strait', 'White Sea', 'Hudson Bay', 'Hudson Strait'}
U = unary_union([fwN(shape(f['geometry']).buffer(0)).buffer(3000) for f in m['features'] if f['properties'].get('name') in want]).buffer(-3000)
A = clean(U, 4000, 4e9); c = bwN(A.centroid)
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': 'Arctic Ocean', 'note': 'union of Natural Earth 10m marine polygons merged in polar LAEA; seam-free rings (tools/make_polar_shapes.py)', 'area_km2': round(A.area / 1e6), 'centroid_latlon': [round(c.y, 3), round(c.x, 3)]}, 'geometry': {'type': 'MultiPolygon', 'coordinates': rings_ll(A, bwN)}}]}, open(f'{www}/geo/arctic_ocean.geojson', 'w'))
fwS, bwS = tf(-90)
p = f'{www}/ep/ep01/ch2_data.json'; d = json.load(open(p)); ant = d['continents']['antarctica']
P = unary_union([fwS(Polygon(r).buffer(0)) for r in ant['rings'] if len(r) > 3])
AA = clean(P.buffer(500).buffer(-500), 2000, 1e9)
ant['rings'] = [r for poly in rings_ll(AA, bwS) for r in poly]
json.dump(d, open(p, 'w'))
print(f'Arctic {A.area / 1e12:.2f} M km2, Antarctica {AA.area / 1e12:.2f} M km2')
