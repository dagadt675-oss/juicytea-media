"""BlendKit meshes for the river city. Rendered videos only.

The files live in the gitignored cache. Branded models are never placed.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy

from engine.cc0_city import _mesh_size, _sit_on_ground, _spawn

PRIVATE = Path(os.environ.get("PRIVATE_CACHE", "/opt/cursor/asset-cache/private"))
ROOT = PRIVATE / "blendkit"

# Real-world marques. Skip even if a caller asks for them by name.
BRAND_TOKENS = (
    "mustang",
    "beetle",
    "volkswagen",
    "audi",
    "bmw",
    "ramcharger",
    "escalade",
    "vaz_2107",
    "pinzgauer",
    "neoplan",
    "cessna",
    "yamaha",
    "fire_extinguisher",
    "lego",
)

_FILES = None
_MESHES = {}

TOWERS = (
    "Skyline_Vista_Tower_ff2c8a98",
    "Horizon_Glow_Tower_b9db0504",
    "Urban_Pulse_Tower_cf4883e9",
)


def ready() -> bool:
    return bool(_blends())


def is_brand(path: Path) -> bool:
    text = path.as_posix().lower()
    return any(token in text for token in BRAND_TOKENS)


def _blends():
    global _FILES
    if _FILES is None:
        _FILES = [] if not ROOT.is_dir() else [path for path in ROOT.rglob("*.blend") if not is_brand(path)]
    return _FILES


def find_blend(token: str):
    token_l = token.lower()
    hits = [path for path in _blends() if token_l in path.name.lower()]
    return hits[0] if hits else None


def _keep(name: str) -> bool:
    low = name.lower()
    if low.startswith("wgt-") or "wgt-" in low:
        return False
    if "lod1" in low or "lod2" in low or "lod3" in low:
        return False
    return True


def _mesh(token: str):
    if token in _MESHES:
        return _MESHES[token]
    path = find_blend(token)
    if path is None:
        _MESHES[token] = None
        return None
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = [name for name in src.objects if _keep(name)]
    objs = [obj for obj in dst.objects if obj is not None]
    col = bpy.data.collections.new("blend_src")
    bpy.context.scene.collection.children.link(col)
    for obj in objs:
        try:
            col.objects.link(obj)
        except RuntimeError:
            pass
    bpy.context.view_layer.update()
    meshes = [obj for obj in objs if obj.type == "MESH"]
    if not meshes:
        _MESHES[token] = None
        return None
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    _sit_on_ground(obj)
    mesh = obj.data
    mesh.name = "bk_" + path.stem[:40]
    for item in list(col.objects):
        try:
            bpy.data.objects.remove(item, do_unlink=True)
        except ReferenceError:
            pass
    bpy.data.collections.remove(col)
    _MESHES[token] = mesh
    return mesh


def place(coll, token, loc, yaw, height=None, longest=None, name="prop"):
    mesh = _mesh(token)
    if mesh is None:
        return None
    size = _mesh_size(mesh)
    if height is not None:
        scale = float(height) / max(size[2], 0.01)
    elif longest is not None:
        scale = float(longest) / max(max(size), 0.01)
    else:
        scale = 1.0
    return _spawn(coll, mesh, loc, yaw, scale, name)


def place_tower(coll, x, y, z, height):
    if not ready():
        return None
    token = TOWERS[int(abs(x * 3 + y)) % len(TOWERS)]
    return place(coll, token, (x, y, z), 0.0, height=height, name="tower")


def place_bench(coll, x, y, z, yaw):
    return place(coll, "Stylish_bench_7383c436", (x, y, z), yaw, height=0.85, name="bench")


def place_hydrant(coll, x, y, z, yaw=0.3):
    return place(coll, "Fire_Hydrant_b8013eb2", (x, y, z), yaw, height=0.85, name="hydrant")


def place_cat(coll, x, y, z, yaw=1.1):
    return place(coll, "Domestic_cat_rigged__731d9ed6", (x, y, z), yaw, height=0.32, name="cat")


# RMS Queen Mary, PeeJaa, Sketchfab Free Standard. Ocean episodes only.
# The file is a harbor tile. This length is the hull axis, not the tile.
QUEEN_MARY_LENGTH = 310.7
QUEEN_MARY_NATIVE = 260.7
# The hull runs along +Y. This swing lays that axis on +X.
QUEEN_MARY_ALIGN = -math.pi / 2


def queen_mary_scale() -> float:
    return QUEEN_MARY_LENGTH / QUEEN_MARY_NATIVE


def queen_mary_path(distant: bool = False):
    name = "RMS_Queen_Mary_distant.glb" if distant else "RMS_Queen_Mary.glb"
    path = PRIVATE / "ships" / name
    return path if path.exists() else None


def place_queen_mary(coll, loc, yaw=0.0, distant=False):
    """Place the liner at 310.7 m. Distant shots use the decimated mesh.

    Not used by the river-city episode.
    """
    path = queen_mary_path(distant=distant)
    if path is None:
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [obj for obj in bpy.data.objects if obj not in before]
    roots = [obj for obj in new if obj.parent not in new]
    empty = bpy.data.objects.new("queen_mary", None)
    coll.objects.link(empty)
    for obj in new:
        try:
            coll.objects.link(obj)
        except RuntimeError:
            pass
    bpy.context.view_layer.update()
    for root in roots:
        world = root.matrix_world.copy()
        root.parent = empty
        root.matrix_world = world
    scale = queen_mary_scale()
    empty.scale = (scale, scale, scale)
    empty.rotation_euler.z = float(yaw) + QUEEN_MARY_ALIGN
    empty.location = loc
    return empty
