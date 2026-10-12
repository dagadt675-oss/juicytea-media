#!/usr/bin/env python3
"""Frame-diff gate. A cut is a spike. A dead hold is a long run of zeros."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

W, H = 160, 90
FPS = 60


def diffs_of(frames: np.ndarray) -> np.ndarray:
    """frames: N,H,W,3 uint8. Mean abs RGB on the downscale."""
    a = frames[:-1].astype(np.int16)
    b = frames[1:].astype(np.int16)
    return np.abs(a - b).mean(axis=(1, 2, 3))


def gate(d: np.ndarray, fps: int = FPS) -> dict:
    spikes = []
    for i, val in enumerate(d):
        lo = max(0, i - 6)
        hi = min(len(d), i + 7)
        neigh = [float(d[j]) for j in range(lo, hi) if j != i]
        if not neigh:
            continue
        med = float(np.median(neigh))
        hot = val > 8.0 and val > 3.0 * med
        # A single frame can jump the framing while staying under 8. 5× the
        # neighbouring median catches that. The floor ignores sub-pixel noise.
        quiet = val > 1.5 and val > 5.0 * max(med, 0.05)
        if hot or quiet:
            spikes.append({"frame": i + 1, "t": round((i + 1) / fps, 3), "diff": round(float(val), 3), "median": round(med, 3)})
    zeros = []
    run = 0
    start = 0
    limit = int(1.5 * fps)
    for i, val in enumerate(d):
        if val <= 1e-6:
            if run == 0:
                start = i
            run += 1
        else:
            if run > limit:
                zeros.append({"t0": round(start / fps, 3), "t1": round(i / fps, 3), "frames": run})
            run = 0
    if run > limit:
        zeros.append({"t0": round(start / fps, 3), "t1": round(len(d) / fps, 3), "frames": run})
    return {"spikes": spikes, "dead": zeros, "max": round(float(d.max()) if len(d) else 0, 3), "pass": not spikes and not zeros}


def from_video(path: Path) -> np.ndarray:
    import subprocess
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", f"scale={W}:{H}:flags=area",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    frame = W * H * 3
    n = len(raw) // frame
    return np.frombuffer(raw[:n * frame], np.uint8).reshape(n, H, W, 3)


def local_spikes(frames: np.ndarray, rows: int = 6, cols: int = 4, fps: int = FPS) -> list[dict]:
    """A pop in one part of the frame, even when the whole-frame average stays quiet."""
    a = frames[:-1].astype(np.int16)
    b = frames[1:].astype(np.int16)
    diff = np.abs(a - b)
    n, h, w, _ = diff.shape
    bh, bw = h // rows, w // cols
    cells = np.empty((n, rows, cols), np.float32)
    for r in range(rows):
        for c in range(cols):
            cells[:, r, c] = diff[:, r * bh:(r + 1) * bh, c * bw:(c + 1) * bw].mean(axis=(1, 2, 3))
    found = []
    for i in range(n):
        lo = max(0, i - 6)
        hi = min(n, i + 7)
        for r in range(rows):
            for c in range(cols):
                val = float(cells[i, r, c])
                neigh = [float(cells[j, r, c]) for j in range(lo, hi) if j != i]
                if not neigh:
                    continue
                med = float(np.median(neigh))
                # 6x the local median, and an absolute floor of 10. A coast that
                # is only re-encoded lands under 10. An element appearing, or the
                # old single-frame style jump, clears it.
                if val > 10.0 and val > 6.0 * max(med, 0.35):
                    found.append({
                        "frame": i + 1,
                        "t": round((i + 1) / fps, 3),
                        "cell": (r, c),
                        "diff": round(val, 3),
                        "median": round(med, 3),
                    })
                    break
            else:
                continue
            break
    return found


def loop_seam(frames: np.ndarray) -> dict:
    """Last frame into frame 0. A pop is a seam much larger than the motion around it."""
    seam = float(np.abs(frames[-1].astype(np.int16) - frames[0].astype(np.int16)).mean())
    d = diffs_of(frames)
    neigh = [float(v) for v in list(d[-8:]) + list(d[:8])]
    med = float(np.median(neigh)) if neigh else 0.0
    spike = seam > 8.0 and seam > 3.0 * max(med, 1e-6)
    # yuv420 leaves about 1.5 on a perfect loop. Anything past that, against a quiet neighbour, is a pop.
    pop = seam > max(2.4, 2.5 * med)
    return {"seam": round(seam, 3), "median": round(med, 3), "pass": not spike and not pop}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "greenland_africa_v6.mp4"
    frames = from_video(path)
    report = gate(diffs_of(frames))
    seam = loop_seam(frames)
    local = local_spikes(frames)
    print(f"frames {len(frames)} max {report['max']} spikes {len(report['spikes'])} dead {len(report['dead'])} pass {report['pass']}")
    print(f"loop seam {seam['seam']} median {seam['median']} pass {seam['pass']}")
    print(f"local pops {len(local)} pass {not local}")
    for row in report["spikes"][:30]:
        print(" spike", row)
    for row in report["dead"][:20]:
        print(" dead", row)
    for row in local[:40]:
        print(" local", row)
    if not report["pass"] or not seam["pass"] or local:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
