"""Segmented episode renders.

A film is cut into beat-sized chunks of about 2–5 seconds. Each chunk is a
PNG or EXR sequence in its own cache directory. The cache key is a hash of
the render code, the asset fingerprints, the camera and scene, and the
channel samples for that chunk including its handle frames. A spec edit
re-renders only the chunks whose samples changed. A code or asset edit
re-renders every chunk, because those inputs are shared.

Boundary continuity: every segment is built from the same spec, the same
scene seed, and the same camera. The Cycles seed is the frame number, not
the segment index. Each segment also renders one or two handle frames on
either side (clipped at the head and tail of the film) so motion blur sees
the same neighbors a full render would, then those handles are dropped.
Overlapping handles are hashed against each other, and can be hashed against
a full render of the same frames.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from engine.spec import channels_at

HANDLE_MIN = 1
HANDLE_MAX = 2
DEFAULT_HANDLES = 2
MIN_SECONDS = 2.0
MAX_SECONDS = 5.0
# Centered shutter, in frames. Two handle frames cover it on both sides.
MOTION_BLUR_SHUTTER = 1.0

_PICTURE_SUFFIXES = {
    ".blend",
    ".exr",
    ".fbx",
    ".glb",
    ".gltf",
    ".hdr",
    ".jpeg",
    ".jpg",
    ".obj",
    ".png",
    ".tga",
    ".tif",
    ".tiff",
    ".webp",
}
# Composited in a later pass. Editing it must not bust the beauty cache.
_CODE_SKIP = {"overlay.py", "segments.py"}


class SegmentContinuityError(RuntimeError):
    """A boundary frame did not match its neighbor or a full render."""

    def __init__(self, mismatches):
        self.mismatches = mismatches
        frames = ", ".join(str(item.get("frame")) for item in mismatches[:8])
        super().__init__(f"{len(mismatches)} boundary frame(s) disagree: {frames}")


def frame_seed(frame: int) -> int:
    """Cycles noise seed. It follows the frame, so a segment and a full render match."""
    return int(frame) * 997 + 17


def plan_segments(resolved, min_seconds=MIN_SECONDS, max_seconds=MAX_SECONDS, handles=DEFAULT_HANDLES):
    """Cover frames 1..frame_count with no gaps or overlaps.

    A beat inside the window becomes one segment. A longer beat is split.
    A shorter beat is merged with its neighbors until the window is full
    or the next piece would pass the maximum.
    """
    if handles < HANDLE_MIN or handles > HANDLE_MAX:
        raise ValueError(f"handles must be {HANDLE_MIN} or {HANDLE_MAX}")
    if min_seconds <= 0 or max_seconds < min_seconds:
        raise ValueError("segment window must satisfy 0 < min <= max")
    fps = int(resolved["fps"])
    frame_count = int(resolved["frame_count"])
    max_frames = max(1, int(round(max_seconds * fps)))
    min_frames = max(1, int(round(min_seconds * fps)))
    target = max(1, int(round((min_seconds + max_seconds) * 0.5 * fps)))
    target = min(target, max_frames)

    pieces = []
    for beat in resolved["beats"]:
        start = max(1, int(beat["start_frame"]))
        end = min(frame_count, int(beat["end_frame"]))
        if end < start:
            continue
        for span_start, span_end in _split_span(start, end, min_frames, max_frames, target):
            pieces.append({"start": span_start, "end": span_end, "beats": [beat["id"]]})
    pieces = _fill_gaps(pieces, frame_count)

    merged = []
    for piece in pieces:
        if not merged:
            merged.append(piece)
            continue
        current = merged[-1]
        combined = piece["end"] - current["start"] + 1
        current_len = current["end"] - current["start"] + 1
        piece_len = piece["end"] - piece["start"] + 1
        short = current_len < min_frames or piece_len < min_frames
        if combined <= max_frames and short:
            current["end"] = piece["end"]
            current["beats"].extend(piece["beats"])
        else:
            merged.append(piece)

    segments = []
    for index, piece in enumerate(merged):
        start = piece["start"]
        end = piece["end"]
        segments.append(
            {
                "index": index,
                "id": _segment_id(index, piece["beats"]),
                "beat_ids": list(piece["beats"]),
                "start_frame": start,
                "end_frame": end,
                "render_start": max(1, start - handles),
                "render_end": min(frame_count, end + handles),
                "handles": handles,
            }
        )
    _check_coverage(segments, frame_count)
    return segments


def _split_span(start, end, min_frames, max_frames, target):
    spans = []
    cursor = start
    while cursor <= end:
        remain = end - cursor + 1
        if remain <= max_frames:
            spans.append((cursor, end))
            break
        take = target
        tail = remain - take
        if 0 < tail < min_frames:
            take = remain - min_frames
            if take < min_frames:
                take = max(1, remain // 2)
            take = max(1, min(take, max_frames))
        spans.append((cursor, cursor + take - 1))
        cursor += take
    return spans


def _fill_gaps(pieces, frame_count):
    pieces = sorted(pieces, key=lambda item: (item["start"], item["end"]))
    filled = []
    cursor = 1
    for piece in pieces:
        if piece["end"] < cursor:
            continue
        start = max(piece["start"], cursor)
        if start > cursor:
            filled.append({"start": cursor, "end": start - 1, "beats": []})
        filled.append({"start": start, "end": piece["end"], "beats": list(piece["beats"])})
        cursor = piece["end"] + 1
    if cursor <= frame_count:
        filled.append({"start": cursor, "end": frame_count, "beats": []})
    return filled


def _check_coverage(segments, frame_count):
    frames = []
    for segment in segments:
        frames.extend(range(segment["start_frame"], segment["end_frame"] + 1))
    if frames != list(range(1, frame_count + 1)):
        raise RuntimeError("segments do not cover every frame exactly once")


def _segment_id(index, beat_ids):
    raw = "+".join(beat_ids) if beat_ids else "gap"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in raw)[:40]
    return f"seg_{index:03d}_{safe}"


def project_code_digest(project_root: Path) -> str:
    engine = Path(project_root) / "engine"
    paths = [path for path in engine.glob("*.py") if path.name not in _CODE_SKIP]
    return code_digest(paths)


def code_digest(paths) -> str:
    digest = hashlib.sha256()
    for path in sorted((Path(path) for path in paths), key=lambda item: str(item)):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def default_asset_roots(project_root: Path | None = None) -> list[Path]:
    root = Path(project_root) if project_root else Path(__file__).resolve().parents[1]
    roots = []
    assets = root / "assets"
    if assets.is_dir():
        roots.append(assets)
    private = Path(os.environ.get("PRIVATE_CACHE", "/opt/cursor/asset-cache/private"))
    cc0 = Path(os.environ.get("CC0_CACHE", "/opt/cursor/asset-cache/cc0"))
    for path in (private, cc0):
        if path.is_dir():
            roots.append(path)
    return roots


def asset_digest(roots, cache_file: Path | None = None) -> str:
    """Fingerprint picture files. A stat cache skips the re-read when nothing changed."""
    files = _picture_files(roots)
    stats = hashlib.sha256()
    for path in files:
        st = path.stat()
        stats.update(f"{path}\0{st.st_size}\0{st.st_mtime_ns}\n".encode())
    stats_key = stats.hexdigest()
    if cache_file is not None and cache_file.is_file():
        try:
            saved = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            saved = None
        if saved and saved.get("stats") == stats_key and saved.get("digest"):
            return saved["digest"]
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path).encode())
        digest.update(b"\0")
        digest.update(_fingerprint(path))
        digest.update(b"\0")
    hex_digest = digest.hexdigest()
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"stats": stats_key, "digest": hex_digest, "files": len(files)}),
            encoding="utf-8",
        )
    return hex_digest


def _picture_files(roots) -> list[Path]:
    found = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name != "__pycache__"]
            for name in filenames:
                path = Path(dirpath) / name
                if path.suffix.lower() in _PICTURE_SUFFIXES:
                    found.append(path)
    found.sort()
    return found


def _fingerprint(path: Path) -> bytes:
    size = path.stat().st_size
    digest = hashlib.sha256()
    digest.update(str(size).encode())
    with path.open("rb") as handle:
        digest.update(handle.read(65536))
        if size > 131072:
            handle.seek(size - 65536)
            digest.update(handle.read(65536))
    return digest.digest()


def _jsonable(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    return str(value)


def segment_key(resolved, segment, *, code, assets, samples, scale, image_format) -> str:
    """Hash the inputs that can change this segment's pixels.

    Channel samples are taken on the rendered range, handles included, so a
    curve edit re-renders the chunk it touches and the neighbor that uses
    those frames as motion-blur handles. The camera, scene seed, features,
    code, and assets are shared, so a change there re-renders every chunk.
    """
    frames = {}
    for frame in range(segment["render_start"], segment["render_end"] + 1):
        sample = channels_at(resolved, frame)
        frames[str(frame)] = {name: round(float(value), 6) for name, value in sample.items()}
    payload = {
        "code": code,
        "assets": assets,
        "samples": int(samples),
        "scale": round(float(scale), 6),
        "format": image_format,
        "width": int(resolved["width"]),
        "height": int(resolved["height"]),
        "fps": int(resolved["fps"]),
        "camera": resolved.get("camera") or {},
        "scene": resolved.get("scene") or {},
        "episode_format": resolved.get("format"),
        "features": resolved.get("features") or {},
        "frames": frames,
        "handles": int(segment["handles"]),
        "seed_rule": "frame",
        "shutter": MOTION_BLUR_SHUTTER,
    }
    raw = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def frame_name(frame: int, ext: str) -> str:
    return f"f_{int(frame):04d}.{ext}"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def overlap_frames(segments):
    """Frames rendered by two neighboring segments. Handles make this non-empty."""
    found = []
    for left, right in zip(segments, segments[1:]):
        lo = max(left["render_start"], right["render_start"])
        hi = min(left["render_end"], right["render_end"])
        for frame in range(lo, hi + 1):
            found.append((left, right, frame))
    return found


def verify_overlaps(segments, cache_for, ext) -> list[dict]:
    mismatches = []
    for left, right, frame in overlap_frames(segments):
        left_path = Path(cache_for(left)) / frame_name(frame, ext)
        right_path = Path(cache_for(right)) / frame_name(frame, ext)
        if not left_path.is_file() or not right_path.is_file():
            mismatches.append(
                {
                    "frame": frame,
                    "left": left["id"],
                    "right": right["id"],
                    "missing": not left_path.is_file() or not right_path.is_file(),
                }
            )
            continue
        left_hash = file_hash(left_path)
        right_hash = file_hash(right_path)
        if left_hash != right_hash:
            mismatches.append(
                {
                    "frame": frame,
                    "left": left["id"],
                    "right": right["id"],
                    "left_hash": left_hash,
                    "right_hash": right_hash,
                }
            )
    return mismatches


def verify_boundaries_against_full(segments, cache_for, full_dir, ext) -> list[dict]:
    """Compare each segment's first and last kept frame to a full render."""
    mismatches = []
    full_dir = Path(full_dir)
    for segment in segments:
        for frame in (segment["start_frame"], segment["end_frame"]):
            ours = Path(cache_for(segment)) / frame_name(frame, ext)
            reference = full_dir / frame_name(frame, ext)
            if not ours.is_file() or not reference.is_file():
                mismatches.append({"frame": frame, "segment": segment["id"], "missing": True})
                continue
            if file_hash(ours) != file_hash(reference):
                mismatches.append(
                    {
                        "frame": frame,
                        "segment": segment["id"],
                        "segment_hash": file_hash(ours),
                        "full_hash": file_hash(reference),
                    }
                )
    return mismatches


def assemble(segments, cache_for, dest, ext, frame_count) -> list[int]:
    """Hardlink kept frames into one sequence. Handle frames stay in the cache."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob(f"f_*.{ext}"):
        old.unlink()
    kept = []
    for segment in segments:
        for frame in range(segment["start_frame"], segment["end_frame"] + 1):
            kept.append(frame)
            src = Path(cache_for(segment)) / frame_name(frame, ext)
            if not src.is_file():
                raise RuntimeError(f"missing kept frame {src}")
            dst = dest / frame_name(frame, ext)
            if dst.exists():
                dst.unlink()
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
    if kept != list(range(1, frame_count + 1)):
        raise RuntimeError(f"assembly covers {len(kept)} frames, film has {frame_count}")
    return kept


def ffmpeg_command(frame_dir, dest, *, fps, frame_count, ext, ffmpeg="ffmpeg"):
    return [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-start_number",
        "1",
        "-i",
        str(Path(frame_dir) / f"f_%04d.{ext}"),
        "-frames:v",
        str(frame_count),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-movflags",
        "+faststart",
        str(dest),
    ]


def encode_sequence(frame_dir, dest, *, fps, frame_count, ext, ffmpeg="ffmpeg"):
    if shutil.which(ffmpeg) is None:
        raise RuntimeError("ffmpeg is not installed; the frame sequence is assembled but not encoded")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = ffmpeg_command(frame_dir, dest, fps=fps, frame_count=frame_count, ext=ext, ffmpeg=ffmpeg)
    subprocess.check_call(command)
    return command


def _cache_ready(directory: Path, segment, ext: str) -> bool:
    if not directory.is_dir():
        return False
    meta_path = directory / "meta.json"
    if not meta_path.is_file():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if meta.get("render_start") != segment["render_start"] or meta.get("render_end") != segment["render_end"]:
        return False
    for frame in range(segment["render_start"], segment["render_end"] + 1):
        if not (directory / frame_name(frame, ext)).is_file():
            return False
    return True


def run_segments(
    resolved,
    *,
    cache_dir,
    assemble_dir,
    render_fn,
    code,
    assets,
    samples,
    scale,
    image_format,
    handles=DEFAULT_HANDLES,
    min_seconds=MIN_SECONDS,
    max_seconds=MAX_SECONDS,
    force=False,
    full_reference=None,
    render=True,
):
    """Render dirty segments, check boundaries, and concat the kept frames.

    ``render_fn(segment, directory)`` writes ``f_####.<ext>`` for every frame
    from ``render_start`` through ``render_end``. Cached segments are not
    passed to it.
    """
    ext = "exr" if image_format == "exr" else "png"
    if image_format not in ("png", "exr"):
        raise ValueError(f"unsupported image format {image_format}")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    segments = plan_segments(resolved, min_seconds=min_seconds, max_seconds=max_seconds, handles=handles)
    entries = []
    for segment in segments:
        key = segment_key(
            resolved,
            segment,
            code=code,
            assets=assets,
            samples=samples,
            scale=scale,
            image_format=image_format,
        )
        final = cache_dir / key
        hit = not force and _cache_ready(final, segment, ext)
        if render and not hit:
            partial = cache_dir / f".partial-{key[:16]}"
            if partial.exists():
                shutil.rmtree(partial)
            partial.mkdir(parents=True)
            try:
                render_fn(segment, partial)
                missing = [
                    frame
                    for frame in range(segment["render_start"], segment["render_end"] + 1)
                    if not (partial / frame_name(frame, ext)).is_file()
                ]
                if missing:
                    raise RuntimeError(f"{segment['id']} did not write frames {missing[:6]}")
                meta = {
                    "key": key,
                    "id": segment["id"],
                    "beat_ids": segment["beat_ids"],
                    "start_frame": segment["start_frame"],
                    "end_frame": segment["end_frame"],
                    "render_start": segment["render_start"],
                    "render_end": segment["render_end"],
                    "handles": segment["handles"],
                    "format": ext,
                }
                (partial / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                if final.exists():
                    shutil.rmtree(final)
                partial.rename(final)
            except Exception:
                shutil.rmtree(partial, ignore_errors=True)
                raise
            hit = False
        segment = dict(segment)
        segment["key"] = key
        segment["cache"] = str(final)
        segment["cached"] = bool(hit)
        entries.append(segment)

    def cache_for(segment):
        return Path(segment["cache"])

    overlaps = []
    full_mismatches = []
    if render:
        overlaps = verify_overlaps(entries, cache_for, ext)
        if full_reference:
            full_mismatches = verify_boundaries_against_full(entries, cache_for, full_reference, ext)
        mismatches = overlaps + full_mismatches
        if mismatches:
            raise SegmentContinuityError(mismatches)
        assemble(entries, cache_for, assemble_dir, ext, int(resolved["frame_count"]))

    return {
        "id": resolved.get("id"),
        "frame_count": int(resolved["frame_count"]),
        "fps": int(resolved["fps"]),
        "format": ext,
        "handles": handles,
        "segments": [
            {
                "id": segment["id"],
                "beat_ids": segment["beat_ids"],
                "start_frame": segment["start_frame"],
                "end_frame": segment["end_frame"],
                "render_start": segment["render_start"],
                "render_end": segment["render_end"],
                "key": segment["key"],
                "cached": segment["cached"],
            }
            for segment in entries
        ],
        "overlaps_ok": not overlaps,
        "full_match": not full_mismatches,
        "entries": entries,
    }
