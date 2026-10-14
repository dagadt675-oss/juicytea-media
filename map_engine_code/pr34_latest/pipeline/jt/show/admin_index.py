"""Natural Earth admin-0, queried by bounding box.

The shapefile is public domain. Boxes live in a SQLite R*Tree so a frame
loads only the countries that intersect the view. Geopandas is used when
it is installed; the same boxes are written either way.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from jt.data import DATA, ensure_shapefile

DB_PATH = DATA / "cache" / "admin0_bbox.sqlite"


def _iso(record) -> str:
    info = record.as_dict()
    for key in ("ADM0_A3", "ISO_A3", "SOV_A3"):
        value = str(info.get(key) or "").strip()
        if value and value != "-99":
            return value
    return ""


def ensure_index(path: Path = DB_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    import shapefile
    reader = shapefile.Reader(str(ensure_shapefile()))
    con = sqlite3.connect(path)
    con.execute("CREATE VIRTUAL TABLE box USING rtree(id, minx, maxx, miny, maxy)")
    con.execute("CREATE TABLE meta(id INTEGER PRIMARY KEY, iso TEXT)")
    rows_box = []
    rows_meta = []
    for i, shape in enumerate(reader.iterShapes()):
        xmin, ymin, xmax, ymax = shape.bbox
        rows_box.append((i, xmin, xmax, ymin, ymax))
        rows_meta.append((i, _iso(reader.record(i))))
    con.executemany("INSERT INTO box VALUES (?,?,?,?,?)", rows_box)
    con.executemany("INSERT INTO meta VALUES (?,?)", rows_meta)
    con.commit()
    con.close()
    return path


def countries_in_bbox(west: float, south: float, east: float, north: float,
                      path: Path = DB_PATH) -> list[str]:
    """ISO codes whose envelope intersects the view. Not the whole planet."""
    ensure_index(path)
    con = sqlite3.connect(path)
    try:
        found = con.execute(
            """
            SELECT meta.iso FROM meta
            JOIN box ON box.id = meta.id
            WHERE box.minx <= ? AND box.maxx >= ? AND box.miny <= ? AND box.maxy >= ?
              AND meta.iso != ''
            """,
            (east, west, north, south),
        ).fetchall()
    finally:
        con.close()
    return sorted({row[0] for row in found})


def geopandas_hits(west: float, south: float, east: float, north: float) -> list[str] | None:
    """The same query through geopandas, when that package is installed."""
    try:
        import geopandas as gpd
        from shapely.geometry import box
    except ImportError:
        return None
    frame = gpd.read_file(ensure_shapefile())
    hit = frame.iloc[frame.sindex.query(box(west, south, east, north), predicate="intersects")]
    column = "ADM0_A3" if "ADM0_A3" in hit.columns else "ISO_A3"
    return sorted({str(v) for v in hit[column] if v and str(v) != "-99"})
