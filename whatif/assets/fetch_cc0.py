#!/usr/bin/env python3
"""Download the public CC0 library and cache it outside git.

    python3 whatif/assets/fetch_cc0.py
    python3 whatif/assets/fetch_cc0.py --only city_buildings,nature,characters

PRIVATE entries in the manifest are skipped. Split zips are reassembled and
checked against the whole-file sha256. The cache defaults to
/opt/cursor/asset-cache/cc0 (override with CC0_CACHE).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).resolve().parent / "fetch" / "drive_manifest.json"
DEFAULT_CACHE = Path(os.environ.get("CC0_CACHE", "/opt/cursor/asset-cache/cc0"))
URL = "https://drive.usercontent.google.com/download?id={id}&export=download&confirm=t"

# Packs the river-city episode instances. The rest of the library can be
# fetched with --only all.
CITY = (
    "city_buildings",
    "roads_props",
    "vehicles",
    "characters",
    "animations",
    "nature",
    "ruins_decay",
    "animals",
    "hdri",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(file_id: str, dest: Path, expected: int | None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and expected and dest.stat().st_size == expected:
        return
    partial = dest.with_suffix(dest.suffix + ".partial")
    cmd = [
        "curl",
        "-L",
        "--fail",
        "--retry",
        "4",
        "--retry-delay",
        "2",
        "-o",
        str(partial),
        URL.format(id=file_id),
    ]
    subprocess.check_call(cmd)
    partial.replace(dest)
    if expected and dest.stat().st_size != expected:
        raise SystemExit(f"{dest.name} is {dest.stat().st_size} bytes, expected {expected}")


def _public(entry: dict) -> bool:
    name = entry["name"]
    if name.startswith("PRIVATE"):
        return False
    if "DO_NOT_REDISTRIBUTE" in name:
        return False
    license_text = (entry.get("license") or "").lower()
    if "restricted" in license_text or "do not redistribute" in license_text:
        return False
    return name.startswith("assets_cc0_")


def _wanted(entry: dict, only: set[str] | None) -> bool:
    if not _public(entry):
        return False
    if only is None:
        return True
    stem = entry["name"].removeprefix("assets_cc0_").removesuffix(".zip")
    return stem in only


def fetch(only: set[str] | None, cache: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    zips = cache / "zips"
    extracted = cache / "extracted"
    zips.mkdir(parents=True, exist_ok=True)
    extracted.mkdir(parents=True, exist_ok=True)
    for entry in manifest["files"]:
        if not _wanted(entry, only):
            continue
        name = entry["name"]
        dest = zips / name
        print("fetch", name)
        if entry.get("split"):
            parts = []
            for part in entry["parts"]:
                part_path = zips / part["name"]
                _download(part["drive_file_id"], part_path, part.get("size"))
                got = _sha256(part_path)
                if got != part["sha256"]:
                    raise SystemExit(f"{part['name']} sha256 {got} != {part['sha256']}")
                parts.append(part_path)
            if not dest.exists() or _sha256(dest) != entry["sha256"]:
                with dest.open("wb") as out:
                    for part_path in parts:
                        out.write(part_path.read_bytes())
        else:
            _download(entry["drive_file_id"], dest, entry.get("size"))
        got = _sha256(dest)
        if got != entry["sha256"]:
            raise SystemExit(f"{name} sha256 {got} != {entry['sha256']}")
        marker = extracted / (name + ".ok")
        if marker.exists():
            print("extracted", name)
            continue
        subprocess.check_call(["unzip", "-q", "-o", str(dest), "-d", str(extracted)])
        marker.write_text(got + "\n", encoding="utf-8")
        print("unzipped", name)
    print("cache", cache)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=",".join(CITY), help="comma list, or 'all'")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    args = parser.parse_args()
    only = None if args.only.strip() == "all" else {item.strip() for item in args.only.split(",") if item.strip()}
    fetch(only, Path(args.cache))


if __name__ == "__main__":
    main()
