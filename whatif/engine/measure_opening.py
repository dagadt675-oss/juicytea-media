"""Render one frame with an object-index pass and score it against zenith.

    blender --background --python engine/measure_opening.py -- resolved.json --out dir --scale 0.5 --samples 1
Writes beauty PNG, index EXR, and metrics.json. Exits 0 when every metric is
within tolerance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import build as build_mod  # noqa: E402
from engine.opening_metrics import measure_masks  # noqa: E402


def _args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    out = {"spec": argv[0], "out": "/tmp/opening_metric", "scale": 0.5, "samples": 1}
    i = 1
    while i < len(argv):
        key = argv[i]
        if key == "--out":
            out["out"] = argv[i + 1]
            i += 2
        elif key == "--scale":
            out["scale"] = float(argv[i + 1])
            i += 2
        elif key == "--samples":
            out["samples"] = int(argv[i + 1])
            i += 2
        else:
            raise SystemExit(f"unknown arg {key}")
    return out


def _attach_index(scene, directory):
    scene.view_layers[0].use_pass_object_index = True
    tree = scene.node_tree
    layers = tree.nodes.get("Render Layers")
    node = tree.nodes.new("CompositorNodeOutputFile")
    node.name = "IndexOut"
    node.base_path = str(directory)
    node.format.file_format = "OPEN_EXR"
    node.format.color_depth = "32"
    node.format.color_mode = "RGB"
    node.file_slots[0].path = "index"
    tree.links.new(layers.outputs["IndexOB"], node.inputs[0])
    return node


def _load_array(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    flat = np.array(image.pixels[:], dtype=np.float64)
    channels = image.channels
    array = flat.reshape((height, width, channels))
    # Blender stores pixels from the bottom row.
    return np.flipud(array), image


def _plain(value):
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def _print_table(metrics):
    print(f"{'metric':<22} {'ours':>10} {'zenith':>10} {'error':>8}  ok")
    for row in metrics["rows"]:
        got = row["got"]
        target = row["target"]
        err = row["error"]
        got_s = "—" if got is None else (f"{got[0]:.0f},{got[1]:.0f},{got[2]:.0f}" if isinstance(got, (tuple, list)) else f"{got:.4f}")
        tgt_s = f"{target[0]:.0f},{target[1]:.0f},{target[2]:.0f}" if isinstance(target, tuple) else f"{target:.4f}"
        err_s = "—" if err is None else f"{err * 100:.1f}%"
        print(f"{row['name']:<22} {got_s:>10} {tgt_s:>10} {err_s:>8}  {'yes' if row['ok'] else 'NO'}")
    print("passed" if metrics["passed"] else "FAILED")


def main():
    opts = _args(sys.argv)
    with open(opts["spec"], "r", encoding="utf-8") as handle:
        resolved = json.load(handle)
    out = Path(opts["out"])
    out.mkdir(parents=True, exist_ok=True)
    build_mod.RESOLVED = resolved
    build_mod._clear()
    scene = bpy.context.scene
    build_mod._init_props(scene, resolved)
    features = resolved.get("features") or {}
    kit = build_mod.build_scene(scene, resolved, features)
    build_mod.KIT = kit
    print("objects", len(kit.items), "kind", kit.kind)
    build_mod._key_channels(scene, resolved)
    build_mod._camera(scene, resolved)
    skin = kit.mats.get("trim") or kit.mats.get("car")
    if skin is not None:
        build_mod.attach_pov(scene, kit, resolved, skin)
    # Pass 1: one sample and no pixel filter, so object ids are not blended.
    build_mod._render_settings(scene, resolved, 1, opts["scale"])
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.render.filter_size = 0.01
    index_node = _attach_index(scene, out)
    bpy.app.handlers.frame_change_post.append(build_mod._on_frame)
    scene.frame_set(1)
    build_mod._on_frame(scene)
    scene.render.filepath = str(out / "index_beauty.png")
    bpy.ops.render.render(write_still=True)
    # Pass 2: the picture we judge color on. The index file is already written.
    index_node.mute = True
    scene.cycles.samples = max(1, opts["samples"])
    scene.cycles.use_denoising = opts["samples"] > 1
    scene.render.filter_size = 1.5
    scene.render.filepath = str(out / "beauty.png")
    bpy.ops.render.render(write_still=True)
    index_path = out / "index0001.exr"
    if not index_path.exists():
        found = sorted(out.glob("index*.exr"))
        if not found:
            raise SystemExit(f"no index exr in {out}")
        index_path = found[-1]
    index_arr, _index_image = _load_array(index_path)
    beauty_arr, _beauty_image = _load_array(out / "beauty.png")
    index = np.rint(index_arr[:, :, 0]).astype(np.int32)
    # The beauty PNG is already display sRGB. Blender returns those bytes as 0..1.
    image = np.clip(np.rint(beauty_arr[:, :, :3] * 255.0), 0, 255).astype(np.uint8)
    metrics = measure_masks(index, image)
    metrics["index_values"] = [int(v) for v in np.unique(index)[:12]]
    (out / "metrics.json").write_text(json.dumps(_plain(metrics), indent=2), encoding="utf-8")
    _print_table(metrics)
    print("wrote", out / "metrics.json")
    if not metrics["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
