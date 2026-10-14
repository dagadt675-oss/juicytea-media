#!/usr/bin/env python3
"""Download Natural Earth 50m admin-0 and bake the globe cache.

The shapefile and the cache stay in pipeline/data and are gitignored.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jt.data import build_earth, ensure_shapefile  # noqa: E402


def main() -> int:
    shp = ensure_shapefile()
    earth = build_earth(force="--force" in sys.argv)
    print(f"shapefile {shp}")
    print(f"countries {len(earth.meta) - 1}  texture {earth.ids.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
