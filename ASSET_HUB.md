# Asset hub

Standing owner rule. Wherever possible, use existing ready-made assets from this hub (`ASSET_HUB.json`) and from `asset_library/` for everything: icons, 3D pins, vehicles, characters, face parts, animations and Lottie FX, textures, and fonts.

Build from scratch only when nothing suitable exists. When you do, say which hub entries you checked and why they did not fit.

Re-fetch the catalog at the start of each episode. It is updated in place.

The bytes stay in `asset_library/`, which is gitignored. Do not commit a snapshot of the catalog, and do not commit any pack.

```bash
mkdir -p asset_library/manifests
curl -L 'https://drive.usercontent.google.com/download?id=1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV&export=download&confirm=t' -o asset_library/manifests/ASSET_HUB.json
curl -L 'https://drive.usercontent.google.com/download?id=1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T&export=download&confirm=t' -o asset_library/manifests/ASSET_HUB.md
```

`ASSET_HUB.json` is the machine-readable list (Drive id `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV`). `ASSET_HUB.md` is the same catalog in tables (Drive id `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T`). Each entry has a no-login `curl` command.

Public packs are CC0 or the map kit. Private packs are Sketchfab Free Standard and BlendKit: rendered video only. Never commit them, never re-upload them, and never share the raw files.
