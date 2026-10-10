# Adopting this module from the what-if engine

The sibling engine (locked-camera decay time-lapse, `whatif/engine/`) was still uncommitted when this module was written. Nothing under `whatif/engine/`, `whatif/episodes/`, or `whatif/render_episode.py` is created or modified here. Scale-journey is a sibling package: `whatif/scale_journey/`.

## Shared conventions

| Convention | Scale-journey |
| --- | --- |
| One YAML per episode | `episodes/*.yaml` |
| Identity fields | `id`, `title`, `status`, `fps`, `width`, `height` |
| Frame | 1080×1920, 30 fps |
| Host CLI | `python3 render_episode.py <spec.yaml>` |
| Blender | 4.5.9 LTS, `blender --background --python engine/build.py -- <job>` |
| Engine | Cycles CPU. Eevee Next was ~55 s/frame on this machine’s llvmpipe; Cycles direct-lit is ~2 s/frame |
| Colour | AgX |
| Encode | Silent H.264, yuv420p, bt709 |
| Timeline | `timeline.json` with `id`, `title`, `fps`, `width`, `height`, `duration_sec`, `frame_count`, `beats` |
| Caption band | y 1229–1382 left free of type and leader lines (the decay episode uses the same band for karaoke) |
| Assets | CC0, public domain, or OFL. Procedural meshes. Listed in `LICENSES.md` |
| Dispatch | `module: scale_journey` |

## How the parent should call it

When `whatif/render_episode.py` exists, branch on the spec and do not render a decay scene for these files:

```python
raw = yaml.safe_load(open(spec))
if raw.get("module") == "scale_journey":
    subprocess.check_call([
        sys.executable,
        "whatif/scale_journey/render_episode.py",
        spec,
        "--out", out_dir,
    ])
```

`engine/spec.py` has no dependency on `whatif.engine`. The timeline document is a superset of the decay timeline: same top-level timing fields, plus `milestones`, per-frame `counters`, and `caption_band`.

## What is deliberately different

The decay episode is a locked camera and a channel mixer (`flood`, `rust`, `vegetation`, …). A scale-journey episode is one monotonic dolly and a stack of scale layers. It does not use those effect channels, and it does not share the Noto/Inter overlay. The counter here is Anton, orange and white, on the left, because that is the scale-counter format.

Space and the micro stack are in this module. The decay episode dropped them on purpose. Don’t point a humans-disappeared spec at these layers.
