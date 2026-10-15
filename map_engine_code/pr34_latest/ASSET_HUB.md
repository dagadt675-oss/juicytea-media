# Asset hub

Standing owner rule, in this order, for icons, 3D pins, vehicles, characters, face parts, animations and Lottie FX, textures, and fonts:

1. Use a ready-made asset from this hub (`ASSET_HUB.json`) or from `asset_library/`.
2. If it is not there, search the web for a free ready-made asset that allows commercial use with no attribution (CC0, public domain, OFL for fonts). Download it into `asset_library/` and log the license and the source URL in `asset_library/LICENSES.md`.
3. Build it yourself only when neither exists. Then say which hub entries and which web sources you checked, and why they did not fit.

Re-fetch the catalog at the start of each episode. It is updated in place.

The bytes stay in `asset_library/`, which is gitignored. Do not commit a snapshot of the catalog, and do not commit any pack.

```bash
mkdir -p asset_library/manifests
curl -L 'https://drive.usercontent.google.com/download?id=1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV&export=download&confirm=t' -o asset_library/manifests/ASSET_HUB.json
curl -L 'https://drive.usercontent.google.com/download?id=1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T&export=download&confirm=t' -o asset_library/manifests/ASSET_HUB.md
```

`ASSET_HUB.json` is the machine-readable list (Drive id `1KamSsZFG8L8ZJviGNzjLQM-jNg8g9idV`). `ASSET_HUB.md` is the same catalog in tables (Drive id `1ICoBrOKT-tJa_PqtI--LoJ59TiGsOk2T`). Each entry has a no-login `curl` command.

Public packs are CC0 or the map kit. Private packs are Sketchfab Free Standard and BlendKit: rendered video only. Never commit them, never re-upload them, and never share the raw files.
