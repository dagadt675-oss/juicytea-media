"""Natural Earth admin-0 raster. Public domain. Downloaded by setup, never committed.

The cache stores a country-id map plus a baked hillshade so highlights are
recoloured per frame without redrawing polygons.
"""

from __future__ import annotations

import json
import pickle
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NE_DIR = DATA / "ne"
CACHE = DATA / "cache"
ZIP_URL = "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip"
CACHE_VER = "v3"
TW, TH = 4096, 2048


@dataclass
class Earth:
    ids: np.ndarray       # uint16 (TH, TW), 0 = ocean
    shade: np.ndarray     # uint8 hillshade
    meta: list            # index by id, [None, {iso,name,sov,sov_a3}, ...]
    rings: dict           # iso -> list of float32 Nx2 (lon, lat)
    by_iso: dict
    by_sov: dict
    by_name: dict


def ensure_shapefile() -> Path:
    shp = NE_DIR / "ne_50m_admin_0_countries.shp"
    if shp.exists():
        return shp
    NE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA / "ne_50m_admin_0_countries.zip"
    if not zip_path.exists():
        print("downloading Natural Earth 50m admin-0 …", flush=True)
        urllib.request.urlretrieve(ZIP_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(NE_DIR)
    if not shp.exists():
        raise FileNotFoundError(f"shapefile missing after extract: {shp}")
    return shp


def _split_antimeridian(lons, lats):
    lons = np.asarray(lons, np.float64)
    lats = np.asarray(lats, np.float64)
    if len(lons) < 4:
        return []
    cuts = [0]
    for i in range(1, len(lons)):
        if abs(lons[i] - lons[i - 1]) > 180:
            cuts.append(i)
    cuts.append(len(lons))
    rings = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a >= 4:
            rings.append((lons[a:b], lats[a:b]))
    return rings


def _decimate(pts: np.ndarray, maxn: int = 420) -> np.ndarray:
    if len(pts) <= maxn:
        return pts
    step = int(np.ceil(len(pts) / maxn))
    out = pts[::step]
    if not np.allclose(out[0], out[-1]):
        out = np.vstack([out, out[:1]])
    return out


def build_earth(force: bool = False) -> Earth:
    CACHE.mkdir(parents=True, exist_ok=True)
    tag = CACHE / f"earth_{CACHE_VER}.json"
    ids_path = CACHE / f"ids_{CACHE_VER}.npy"
    shade_path = CACHE / f"shade_{CACHE_VER}.npy"
    rings_path = CACHE / f"rings_{CACHE_VER}.pkl"
    if not force and tag.exists() and ids_path.exists() and shade_path.exists() and rings_path.exists():
        meta = json.loads(tag.read_text())
        rings = pickle.loads(rings_path.read_bytes())
        return _index(np.load(ids_path), np.load(shade_path), meta, rings)

    import skia
    from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter
    import shapefile

    shp = ensure_shapefile()
    print("rasterising Natural Earth", shp.name, flush=True)
    reader = shapefile.Reader(str(shp))
    surface = skia.Surface(TW, TH)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorSetARGB(0, 0, 0, 0))

    meta = [None]
    rings: dict[str, list] = {}
    records = list(reader.iterShapeRecords())
    for sr in records:
        rec = sr.record.as_dict()
        iso = str(rec.get("ADM0_A3") or "").strip()
        if not iso or iso == "-99":
            continue
        cid = len(meta)
        meta.append({
            "iso": iso,
            "name": str(rec.get("NAME") or iso),
            "sov": str(rec.get("SOVEREIGNT") or ""),
            "sov_a3": str(rec.get("SOV_A3") or ""),
            "label": [float(rec.get("LABEL_X") or 0), float(rec.get("LABEL_Y") or 0)],
        })
        r = cid & 255
        g = (cid >> 8) & 255
        paint = skia.Paint(AntiAlias=False)
        paint.setColor(skia.ColorSetARGB(255, r, g, 1))
        paint.setStyle(skia.Paint.kFill_Style)
        shape = sr.shape
        if not shape.points:
            continue
        pts = np.asarray(shape.points, np.float64)
        parts = list(shape.parts) + [len(pts)]
        path = skia.Path()
        path.setFillType(skia.PathFillType.kEvenOdd)
        kept = []
        for i in range(len(parts) - 1):
            ring = pts[parts[i]:parts[i + 1]]
            if len(ring) < 4:
                continue
            kept.append(_decimate(ring.astype(np.float32)))
            for lons, lats in _split_antimeridian(ring[:, 0], ring[:, 1]):
                xs = (lons + 180.0) / 360.0 * TW
                ys = (90.0 - lats) / 180.0 * TH
                path.moveTo(float(xs[0]), float(ys[0]))
                for x, y in zip(xs[1:], ys[1:]):
                    path.lineTo(float(x), float(y))
                path.close()
        if kept:
            rings.setdefault(iso, []).extend(kept)
        canvas.drawPath(path, paint)

    bgra = surface.makeImageSnapshot().toarray()
    red = bgra[:, :, 2].astype(np.uint16)
    green = bgra[:, :, 1].astype(np.uint16)
    alpha = bgra[:, :, 3]
    ids = red | (green << 8)
    ids[alpha == 0] = 0

    land = ids > 0
    elev = distance_transform_edt(land).astype(np.float32)
    elev = gaussian_filter(elev, 1.4)
    if land.any():
        elev /= np.percentile(elev[land], 92) + 1e-6
    elev = np.clip(elev, 0, 1)
    gy, gx = np.gradient(elev)
    hs = (-0.55 * gx) + (-0.85 * gy)
    if land.any():
        hs /= np.percentile(np.abs(hs[land]), 96) + 1e-6
    shade = np.clip(0.58 + 0.42 * hs, 0.32, 1.12)
    coast = land & ~binary_erosion(land, iterations=2)
    shade[coast] *= 0.62
    shade_u8 = np.clip(shade * 220, 0, 255).astype(np.uint8)
    shade_u8[~land] = 170

    np.save(ids_path, ids)
    np.save(shade_path, shade_u8)
    rings_path.write_bytes(pickle.dumps(rings, protocol=4))
    tag.write_text(json.dumps(meta))
    print(f"earth cache: {len(meta) - 1} countries", flush=True)
    return _index(ids, shade_u8, meta, rings)


def _index(ids, shade, meta, rings) -> Earth:
    by_iso, by_sov, by_name = {}, {}, {}
    for i, row in enumerate(meta):
        if not row:
            continue
        by_iso.setdefault(row["iso"].upper(), []).append(i)
        if row["sov_a3"]:
            by_sov.setdefault(row["sov_a3"].upper(), []).append(i)
        by_sov.setdefault(row["sov"].upper(), []).append(i)
        by_name.setdefault(row["name"].upper(), []).append(i)
        by_name.setdefault(row["iso"].upper(), []).append(i)
    return Earth(ids, shade, meta, rings, by_iso, by_sov, by_name)


def resolve_ids(earth: Earth, visuals: list) -> dict[int, tuple[int, int, int]]:
    """Map country id -> RGB highlight for this beat."""
    from jt.themes import parse_hex

    out: dict[int, tuple[int, int, int]] = {}
    for vis in visuals:
        if vis.get("type") != "highlight":
            continue
        colors = vis.get("colors") or []
        tokens = list(vis.get("countries") or [])
        for sov in vis.get("sovereignties") or []:
            tokens.append("sov:" + str(sov))
        for n, token in enumerate(tokens):
            if colors:
                col = parse_hex(colors[min(n, len(colors) - 1)])
            else:
                col = None
            ids = _lookup(earth, str(token))
            for cid in ids:
                out[cid] = col if col is not None else (-1, -1, -1)
    return out


def _lookup(earth: Earth, token: str) -> list[int]:
    if token.lower().startswith("sov:"):
        key = token.split(":", 1)[1].strip().upper()
        return list(earth.by_sov.get(key, []))
    key = token.strip().upper()
    if key in earth.by_iso:
        return list(earth.by_iso[key])
    if key in earth.by_name:
        return list(earth.by_name[key])
    if key in earth.by_sov:
        return list(earth.by_sov[key])
    return []
