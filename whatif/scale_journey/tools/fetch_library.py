"""Download CC0 library packs listed in assets/library/cc0_manifest.json.

Zips land in the gitignored cache. They are not committed.

    python3 whatif/scale_journey/tools/fetch_library.py hdri vehicles roads_props
    python3 whatif/scale_journey/tools/fetch_library.py --list

A private overlay manifest may sit at cache/library/private_manifest.json.
That file is gitignored. This script never prints private download URLs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "library" / "cc0_manifest.json"
CACHE = ROOT / "cache" / "library"
URL = "https://drive.usercontent.google.com/download?id={id}&export=download&confirm=t"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(file_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    request = urllib.request.Request(URL.format(id=file_id), headers={"User-Agent": "juicytea-fetch"})
    with urllib.request.urlopen(request, timeout=120) as response, tmp.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    tmp.replace(dest)


def _load() -> list[dict]:
    packs = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    private = CACHE / "private_manifest.json"
    if private.exists():
        extra = json.loads(private.read_text(encoding="utf-8")).get("files", [])
        packs = packs + extra
    return packs


def _match(packs: list[dict], names: list[str]) -> list[dict]:
    if not names:
        return packs
    wanted = []
    for name in names:
        key = name if name.endswith(".zip") else f"assets_cc0_{name}.zip"
        hits = [pack for pack in packs if pack["name"] == key or pack["name"] == name or key in pack["name"]]
        if not hits:
            raise SystemExit(f"no pack matches {name}")
        wanted.extend(hits)
    return wanted


def fetch(pack: dict) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / pack["name"]
    parts_dir = CACHE / "parts"
    if dest.exists() and _sha256(dest) == pack["sha256"]:
        print(f"ok {pack['name']}", flush=True)
    else:
        if pack.get("split"):
            piece_paths = []
            for part in pack["parts"]:
                piece = parts_dir / part["name"]
                if not piece.exists() or _sha256(piece) != part["sha256"]:
                    print(f"get {part['name']}", flush=True)
                    _download(part["drive_file_id"], piece)
                    got = _sha256(piece)
                    if got != part["sha256"]:
                        raise SystemExit(f"checksum mismatch {part['name']}")
                piece_paths.append(piece)
            with dest.open("wb") as handle:
                for piece in piece_paths:
                    handle.write(piece.read_bytes())
        else:
            print(f"get {pack['name']}", flush=True)
            _download(pack["drive_file_id"], dest)
        got = _sha256(dest)
        if got != pack["sha256"]:
            raise SystemExit(f"checksum mismatch {pack['name']}")
        print(f"verified {pack['name']}", flush=True)
    extracted = CACHE / "extracted" / pack["name"].removesuffix(".zip")
    if not extracted.exists():
        extracted.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest) as archive:
            archive.extractall(extracted)
        print(f"extracted {extracted}", flush=True)
    return extracted


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch CC0 library packs into the gitignored cache")
    parser.add_argument("names", nargs="*", help="pack keys, e.g. hdri vehicles city_buildings")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    packs = _load()
    if args.list:
        for pack in packs:
            print(f"{pack['name']}  {pack['size'] / 1e6:.1f} MB  {pack.get('license', '')}")
        return
    for pack in _match(packs, args.names):
        if str(pack.get("license", "")).upper().startswith("BRAND"):
            print(f"skip brand {pack['name']}", flush=True)
            continue
        fetch(pack)


if __name__ == "__main__":
    main()
