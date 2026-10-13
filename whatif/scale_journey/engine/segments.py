"""Segmented episode renders.

A full episode is cut into beat-aligned chunks of about 2–5 seconds.
Each chunk is a PNG (and, when asked, OpenEXR) sequence in a cache whose
key is a hash of the scene code, the assets, the spec text, and that
chunk's own frame records. A later fix re-renders only the chunks whose
key changed.

The chunks are concatenated by frame number and encoded once. That is
frame-accurate: ffmpeg never joins compressed files. Each chunk is
rendered with one or two extra handle frames before its first frame so
motion blur and any previous-frame state match a single full pass. The
handles are dropped and are not part of the sequence.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache" / "segments"

HANDLE_FRAMES = 2
TARGET_SEC = 4.0
MAX_SEC = 5.0
MIN_SEC = 2.0


@dataclass(frozen=True)
class Segment:
    index: int
    start: int
    end: int
    handles: tuple[int, ...]

    @property
    def body(self) -> range:
        return range(self.start, self.end)

    @property
    def render_frames(self) -> list[int]:
        return list(self.handles) + list(self.body)


def plan_segments(
    n_frames: int,
    fps: int,
    beats: list[dict] | None = None,
    *,
    target_sec: float = TARGET_SEC,
    max_sec: float = MAX_SEC,
    min_sec: float = MIN_SEC,
    handles: int = HANDLE_FRAMES,
) -> list[Segment]:
    """Cover every frame. Prefer beat edges. Split a long beat into 2–5 s pieces."""
    if n_frames <= 0:
        return []
    fps = max(1, int(fps))
    max_f = max(1, int(round(max_sec * fps)))
    target_f = max(1, min(max_f, int(round(target_sec * fps))))
    min_f = max(1, min(target_f, int(round(min_sec * fps))))
    edges = _beat_edges(n_frames, fps, beats or [])
    pieces: list[tuple[int, int]] = []
    for left, right in zip(edges, edges[1:]):
        pieces.extend(_split_span(left, right, target_f, max_f, min_f))
    segments = []
    for index, (start, end) in enumerate(pieces):
        lead = tuple(frame for frame in range(start - handles, start) if frame >= 0)
        segments.append(Segment(index, start, end, lead))
    return segments


def _beat_edges(n_frames: int, fps: int, beats: list[dict]) -> list[int]:
    edges = {0, n_frames}
    for beat in beats:
        start = int(round(float(beat.get("start", 0.0)) * fps))
        end = int(round(float(beat.get("end", 0.0)) * fps))
        if 0 < start < n_frames:
            edges.add(start)
        if 0 < end < n_frames:
            edges.add(end)
    return sorted(edges)


def _split_span(start: int, end: int, target: int, limit: int, minimum: int) -> list[tuple[int, int]]:
    pieces = []
    cursor = start
    while cursor < end:
        remain = end - cursor
        if remain <= limit:
            pieces.append((cursor, end))
            break
        take = target
        if remain - take < minimum:
            take = max(minimum, remain // 2)
        take = min(limit, max(minimum, take))
        if remain - take < minimum and remain <= limit:
            pieces.append((cursor, end))
            break
        pieces.append((cursor, cursor + take))
        cursor += take
    return pieces


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset_manifest(paths: list[Path]) -> list[str]:
    rows = []
    for path in paths:
        if path is None or not path.exists():
            rows.append(f"missing:{path}")
            continue
        if path.is_file():
            stat = path.stat()
            rows.append(f"{path}:{stat.st_size}:{stat.st_mtime_ns}")
            continue
        files = [item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".glb", ".gltf", ".fbx", ".hdr", ".png", ".jpg", ".exr"}]
        for item in sorted(files):
            stat = item.stat()
            rows.append(f"{item.relative_to(path)}:{stat.st_size}:{stat.st_mtime_ns}")
    return rows


def hash_key(*parts: object) -> str:
    digest = hashlib.sha256()
    for part in parts:
        if isinstance(part, (bytes, bytearray)):
            payload = part
        else:
            payload = json.dumps(part, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


def code_hash(paths: list[Path]) -> str:
    blobs = []
    for path in paths:
        blobs.append(path.read_bytes() if path.exists() else b"")
    return hash_key(*blobs)


def scene_hash(code_paths: list[Path], asset_paths: list[Path], settings: dict) -> str:
    return hash_key(code_hash(code_paths), _asset_manifest(asset_paths), settings)


def cache_dir(episode_id: str, kind: str, key: str) -> Path:
    return CACHE / episode_id / kind / key


def is_ready(path: Path) -> bool:
    return (path / "READY").is_file()


def store_ready(path: Path, meta: dict) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (path / "READY").write_text(meta.get("key", ""), encoding="utf-8")


def publish_frames(src: Path, dest: Path, frames: list[int]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for frame in frames:
        source = src / f"f_{frame:04d}.png"
        if not source.exists():
            raise FileNotFoundError(source)
        target = dest / f"f_{frame:04d}.png"
        if target.exists():
            target.unlink()
        os.link(source, target) if _can_link(source, target) else shutil.copyfile(source, target)


def _can_link(source: Path, target: Path) -> bool:
    try:
        os.link(source, target)
    except OSError:
        return False
    target.unlink()
    return True


def encode_sequence(frame_dir: Path, fps: int, mp4: Path) -> None:
    """One encode of the assembled frame sequence. No compressed-file concat."""
    mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-start_number", "0",
            "-i", str(frame_dir / "f_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-colorspace", "bt709",
            "-crf", "16",
            "-movflags", "+faststart",
            "-an",
            str(mp4),
        ]
    )


def boundary_pairs(segments: list[Segment]) -> list[int]:
    """First body frame of every segment after the first. These must match a full render."""
    return [segment.start for segment in segments if segment.index > 0]
