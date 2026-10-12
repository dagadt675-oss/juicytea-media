"""Asset registry. Categories swap without rewriting the scene.

A record is procedural, or a file under ``whatif/assets``. File records with
``enabled`` and a path that exists replace the procedural fallback for that
kind. Scale is normalized to the record's target size: height for trees,
people, and buildings; length, width, and height for cars.

Drop CC0 Quaternius, Kenney, Poly Haven, BlendKit, or Sketchfab files into
``assets/`` and set ``enabled`` on the matching record. Missing files stay
on the procedural mesh.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

# target_height is meters. Cars also carry target_length (nose on +X) and
# target_width. Buildings are fit to the footprint the lot asks for, then
# to target_height when the record sets one.
CATALOG = {
    "person": (
        {"id": "kenney_a", "source": "file", "path": "cc0/kenney/people/character-a.glb", "kinds": ["person"], "target_height": 1.75, "enabled": True},
        {"id": "kenney_b", "source": "file", "path": "cc0/kenney/people/character-b.glb", "kinds": ["person"], "target_height": 1.75, "enabled": True},
        {"id": "kenney_c", "source": "file", "path": "cc0/kenney/people/character-c.glb", "kinds": ["person"], "target_height": 1.75, "enabled": True},
        {"id": "kenney_d", "source": "file", "path": "cc0/kenney/people/character-d.glb", "kinds": ["person"], "target_height": 1.75, "enabled": True},
        {"id": "box_person", "source": "procedural", "kinds": ["person"], "target_height": 1.75, "enabled": True},
    ),
    "car": (
        {"id": "kenney_sedan", "source": "file", "path": "cc0/kenney/cars/sedan.fbx", "kinds": ["sedan"], "target_length": 4.6, "target_width": 1.8, "target_height": 1.5, "enabled": True},
        {"id": "kenney_suv", "source": "file", "path": "cc0/kenney/cars/suv.fbx", "kinds": ["suv"], "target_length": 4.8, "target_width": 2.0, "target_height": 1.8, "enabled": True},
        {"id": "kenney_taxi", "source": "file", "path": "cc0/kenney/cars/taxi.fbx", "kinds": ["taxi"], "target_length": 4.6, "target_width": 1.8, "target_height": 1.6, "enabled": True},
        {"id": "kenney_sport", "source": "file", "path": "cc0/kenney/cars/hatchback-sports.fbx", "kinds": ["hatchback-sports"], "target_length": 4.2, "target_width": 1.8, "target_height": 1.4, "enabled": True},
        {"id": "box_car", "source": "procedural", "kinds": ["sedan", "suv", "taxi", "hatchback-sports"], "target_length": 4.6, "target_width": 1.8, "target_height": 1.5, "enabled": True},
    ),
    "tree": (
        {"id": "lobe", "source": "procedural", "kinds": ["round", "broad", "pine"], "target_height": 8.0, "enabled": True},
        # Curated packs land here. Leave them off until the file is in the tree.
        {"id": "kenney_round", "source": "file", "path": "cc0/kenney/trees/tree-round.glb", "kinds": ["round"], "target_height": 8.0, "enabled": False},
        {"id": "quaternius_oak", "source": "file", "path": "cc0/quaternius/trees/oak.glb", "kinds": ["round", "broad"], "target_height": 8.0, "enabled": False},
        {"id": "quaternius_pine", "source": "file", "path": "cc0/quaternius/trees/pine.glb", "kinds": ["pine"], "target_height": 9.0, "enabled": False},
    ),
    "building": (
        {"id": "facade_tower", "source": "procedural", "kinds": ["tower"], "target_height": 48.0, "enabled": True},
        {"id": "downtown_megakit", "source": "file", "path": "cc0/downtown/tower.glb", "kinds": ["tower"], "target_height": 48.0, "enabled": False},
        {"id": "ruin_shell", "source": "file", "path": "cc0/ruins/shell.glb", "kinds": ["ruin"], "target_height": 12.0, "enabled": False},
    ),
    "prop": (
        {"id": "kenney_lamp", "source": "file", "path": "cc0/kenney/props/light-curved.glb", "kinds": ["lamp"], "target_height": 5.0, "enabled": True},
        {"id": "kenney_signal", "source": "file", "path": "cc0/kenney/props/traffic-light.glb", "kinds": ["signal"], "target_height": 5.0, "enabled": True},
        {"id": "kenney_bench", "source": "file", "path": "cc0/kenney/props/bench/bench.glb", "kinds": ["bench"], "target_height": 0.8, "enabled": True},
    ),
    "hdri": (
        {"id": "kloofendal_day", "source": "file", "path": "cc0/hdri/kloofendal_48d_partly_cloudy_1k.hdr", "kinds": ["day"], "enabled": True},
    ),
}


def height_scale(measured_height: float, target_height: float) -> float:
    """Uniform scale that brings a mesh's height to ``target_height`` meters."""
    measured_height = float(measured_height)
    if measured_height <= 1e-8:
        return 1.0
    return float(target_height) / measured_height


def fit_scale(measured, target):
    """Per-axis scale from full extents to a target box. Axes are independent."""
    out = []
    for got, want in zip(measured, target):
        got = float(got)
        out.append(1.0 if got <= 1e-8 else float(want) / got)
    return tuple(out)


def _matches(record, kind):
    if not kind:
        return True
    kinds = record.get("kinds") or []
    return kind == record.get("id") or kind in kinds


def existing_path(record):
    """Absolute path when this file record is enabled and on disk."""
    if not record or record.get("source") != "file" or not record.get("enabled", True):
        return None
    rel = record.get("path")
    if not rel:
        return None
    path = ASSETS / rel
    return path if path.exists() else None


def choose(category: str, kind: str | None = None, rng=None):
    """The record to instance. Enabled files that exist beat the procedural mesh."""
    rows = [row for row in CATALOG[category] if _matches(row, kind)]
    if not rows:
        raise KeyError(f"no {category} asset for {kind}")
    files = [row for row in rows if existing_path(row) is not None]
    pool = files or [row for row in rows if row.get("source") == "procedural" and row.get("enabled", True)]
    if not pool:
        pool = [row for row in rows if row.get("source") == "procedural"] or rows
    if rng is None or len(pool) == 1:
        return pool[0]
    return pool[rng.randrange(len(pool))]
