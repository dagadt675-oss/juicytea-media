#!/usr/bin/env python3
"""Downscale the risky seconds and run the cut/dead-air gate before the full encode."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from examples.greenland.gate_v6 import gate  # noqa: E402


def _chunk(indices: list[int]):
    from jt.show.greenland_v5 import Episode
    ep = Episode()
    ep.cache_layers = False
    out = []
    for i in indices:
        img = ep.render(i / 60.0)
        small = np.asarray(Image.fromarray(img).resize((160, 90), Image.Resampling.BOX), np.uint8)
        out.append(small)
        if i % 40 == 0:
            print("frame", i, flush=True)
    return indices, out


def main() -> None:
    ranges = (
        list(range(int(3.3 * 60), int(8.4 * 60)))
        + list(range(int(17.4 * 60), int(18.2 * 60)))
        + list(range(int(31.3 * 60), int(32.6 * 60)))
        + list(range(int(46.1 * 60), int(47.7 * 60)))
        + list(range(int(12.8 * 60), int(15.6 * 60)))
        + list(range(int(22.0 * 60), int(25.8 * 60)))
    )
    workers = 4
    parts = [ranges[i::workers] for i in range(workers)]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        got = pool.map(_chunk, parts)
    order = {}
    for indices, frames in got:
        for i, frame in zip(indices, frames):
            order[i] = frame
    runs = []
    cur = []
    prev = None
    for i in sorted(order):
        if prev is not None and i != prev + 1:
            runs.append((prev - len(cur) + 1, cur))
            cur = []
        cur.append(order[i])
        prev = i
    if cur:
        runs.append((prev - len(cur) + 1, cur))
    failed = False
    for start, frames in runs:
        arr = np.stack(frames)
        a = arr[:-1].astype(np.int16)
        b = arr[1:].astype(np.int16)
        d = np.abs(a - b).mean(axis=(1, 2, 3))
        rep = gate(d)
        print(f"from frame {start} n {len(frames)} max {rep['max']} spikes {len(rep['spikes'])} dead {len(rep['dead'])}", flush=True)
        for row in rep["spikes"][:15]:
            print(" spike", row, flush=True)
        for row in rep["dead"][:8]:
            print(" dead", row, flush=True)
        failed = failed or not rep["pass"]
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
