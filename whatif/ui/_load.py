"""Load the format A overlay without colliding with scale_journey's `engine` package."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
_CACHE: dict[str, object] = {}


def _load(alias: str, filename: str):
    if alias in _CACHE:
        return _CACHE[alias]
    spec = importlib.util.spec_from_file_location(alias, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    _CACHE[alias] = module
    return module


def sibling_spec():
    return _load("whatif_engine_spec", "spec.py")


def sibling_overlay():
    """overlay.py imports engine.spec. Point that at the sibling spec, then restore."""
    if "whatif_engine_overlay" in _CACHE:
        return _CACHE["whatif_engine_overlay"]
    spec_mod = sibling_spec()
    saved = sys.modules.get("engine.spec")
    sys.modules["engine.spec"] = spec_mod
    try:
        module = _load("whatif_engine_overlay", "overlay.py")
    finally:
        if saved is None:
            sys.modules.pop("engine.spec", None)
        else:
            sys.modules["engine.spec"] = saved
    return module
