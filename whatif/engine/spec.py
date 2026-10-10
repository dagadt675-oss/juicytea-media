"""Episode spec loader.

A spec is YAML. Narration beats are timed at about 2.6 words/second plus a
0.3 s pause. Effect channels are piecewise-linear 0..1 curves (a 1-frame gap
is a hard cut). This module is pure Python so both Blender and the overlay
share one timeline.
"""

from __future__ import annotations

import json
from pathlib import Path

RATE = 2.6
PAUSE = 0.3

# Effect channels are 0..1 unless noted. `water` is signed: negative drops
# a water body (dry seabed), positive raises it on top of `flood`.
CHANNELS = (
    "flood",
    "water",
    "rain",
    "snow",
    "dust",
    "ash",
    "vegetation",
    "wilt",
    "moss",
    "rust",
    "mud",
    "scorch",
    "collapse",
    "sag",
    "ice",
    "fire",
    "heat",
    "vanish",
    "fauna",
    "gravity",
    "geology",
    "day_night",
    "power",
    "power_grid",
    "wet",
    # Format A extras. All 0..1.
    "wind",
    "fog",
    "season",
    "erosion",
    "sand",
    # Format C, real-time disaster. Unused by time-lapse specs.
    "inertia",
    "scatter",
    "fracture",
    "wave",
    "ocean_pull",
    "gravity_off",
    "critical",
)

DEFAULTS = {
    "flood": 0.0,
    "water": 0.0,
    "rain": 0.0,
    "snow": 0.0,
    "dust": 0.0,
    "ash": 0.0,
    "vegetation": 0.0,
    "wilt": 0.0,
    "moss": 0.0,
    "rust": 0.0,
    "mud": 0.0,
    "scorch": 0.0,
    "collapse": 0.0,
    "sag": 0.0,
    "ice": 0.0,
    "fire": 0.0,
    "heat": 0.0,
    "vanish": 0.0,
    "fauna": 0.0,
    "gravity": 0.0,
    "geology": 0.0,
    "day_night": 0.16,
    "power": 0.0,
    "power_grid": 1.0,
    "wet": 0.0,
    "wind": 0.0,
    "fog": 0.0,
    "season": 0.35,
    "erosion": 0.0,
    "sand": 0.0,
    "inertia": 0.0,
    "scatter": 0.0,
    "fracture": 0.0,
    "wave": 0.0,
    "ocean_pull": 0.0,
    "gravity_off": 0.0,
    "critical": 0.0,
}


# Format C presets. u is 0..1 inside the beat that names the preset.
# gravity_off: float, hold, then a fast crash back to the ground.
PRESETS = {
    "gravity_off": {
        "gravity_off": [
            {"u": 0.0, "v": 0.0},
            {"u": 0.18, "v": 1.0},
            {"u": 0.72, "v": 1.0},
            {"u": 0.82, "v": 0.0},
            {"u": 1.0, "v": 0.0},
        ],
        "critical": [
            {"u": 0.0, "v": 0.2},
            {"u": 0.18, "v": 0.85},
            {"u": 0.82, "v": 1.0},
            {"u": 1.0, "v": 0.4},
        ],
        "wind": [
            {"u": 0.0, "v": 0.1},
            {"u": 0.3, "v": 0.35},
            {"u": 1.0, "v": 0.1},
        ],
    },
}


def word_count(text: str) -> int:
    return len([w for w in text.strip().split() if w])


def narration_seconds(text: str) -> float:
    return word_count(text) / RATE + PAUSE


def _as_keys(value, start: float, end: float, previous: float):
    """Turn a scalar or a list of {u, v} into (second, value) keys inside the beat."""
    if isinstance(value, (int, float)):
        return [(end, float(value))]
    keys = []
    for item in value:
        u = float(item["u"])
        v = float(item["v"])
        t = start + (end - start) * u
        keys.append((t, v))
    keys.sort()
    return keys


def resolve(spec: dict) -> dict:
    fps = int(spec.get("fps", 30))
    beats_in = spec["beats"]
    t = 0.0
    beats = []
    current = dict(DEFAULTS)
    current.update(spec.get("defaults") or {})
    channel_keys = {name: [(0.0, float(current[name]))] for name in CHANNELS}

    for index, beat in enumerate(beats_in):
        narration = beat["narration"].strip()
        seconds = float(beat["seconds"]) if beat.get("seconds") is not None else narration_seconds(narration)
        start = t
        end = t + seconds
        t = end
        if beat.get("reset"):
            # Hard cut back to the opening state on the next frame.
            snap = start + 1.0 / fps
            for name in CHANNELS:
                channel_keys[name].append((snap, float(channel_keys[name][0][1])))
                current[name] = float(channel_keys[name][0][1])
        channels = {}
        preset = beat.get("preset")
        if preset:
            if preset not in PRESETS:
                raise KeyError(f"Unknown preset {preset}")
            channels.update(PRESETS[preset])
        channels.update(beat.get("channels") or {})
        for name, value in channels.items():
            if name not in channel_keys:
                raise KeyError(f"Unknown channel {name}")
            for sec, val in _as_keys(value, start, end, current[name]):
                channel_keys[name].append((sec, val))
            end_keys = _as_keys(value, start, end, current[name])
            current[name] = end_keys[-1][1]
        beats.append(
            {
                "index": index,
                "id": beat.get("id") or f"beat_{index+1}",
                "start": round(start, 4),
                "end": round(end, 4),
                "narration": narration,
                "words": word_count(narration),
                "counter": beat.get("counter") or {},
                "time_label": beat.get("time_label"),
                "ticker": beat.get("ticker"),
                "title": bool(beat.get("title", False)),
            }
        )

    duration = t
    frame_count = max(1, int(round(duration * fps)))
    # Convert seconds to frames. Frame 1 is t=0.
    def to_frame(sec: float) -> int:
        return int(round(sec * fps)) + 1

    frame_channels = {}
    for name, keys in channel_keys.items():
        keys = sorted(keys, key=lambda item: (item[0],))
        packed = []
        for sec, val in keys:
            fr = to_frame(sec)
            fr = max(1, min(frame_count, fr))
            if packed and packed[-1][0] == fr:
                packed[-1] = (fr, val)
            else:
                packed.append((fr, val))
        # Ensure the curve holds through the last frame.
        if packed[-1][0] != frame_count:
            packed.append((frame_count, packed[-1][1]))
        frame_channels[name] = packed

    for beat in beats:
        beat["start_frame"] = to_frame(beat["start"])
        beat["end_frame"] = max(beat["start_frame"] + 1, to_frame(beat["end"]) - 1)

    features = {
        name: any(abs(v) > 1e-4 for _, v in frame_channels[name])
        for name in CHANNELS
    }
    # Power grid starts at 1, so "used" is whether it ever changes.
    features["power_grid"] = any(abs(v - 1.0) > 1e-4 for _, v in frame_channels["power_grid"])
    features["day_night"] = True

    camera = spec.get("camera") or {}
    scene = spec.get("scene") or {}
    resolved = {
        "id": spec.get("id") or "episode",
        "title": spec.get("title") or "",
        "status": spec.get("status") or "final",
        "format": spec.get("format") or "A",
        "fps": fps,
        "width": int(spec.get("width", 1080)),
        "height": int(spec.get("height", 1920)),
        "population": int(spec.get("population") or 0),
        "duration": round(duration, 4),
        "frame_count": frame_count,
        "camera": camera,
        "scene": scene,
        "beats": beats,
        "channels": frame_channels,
        "defaults": {k: float(current[k]) for k in CHANNELS},
        "opening": {name: frame_channels[name][0][1] for name in CHANNELS},
        "features": features,
        "ui": spec.get("ui") or {},
    }
    return resolved


def sample(keys, frame: float) -> float:
    if not keys:
        return 0.0
    if frame <= keys[0][0]:
        return float(keys[0][1])
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if frame <= f1 + 1e-6:
            if f1 - f0 <= 2.01:
                return float(v0 if frame < f1 else v1)
            span = f1 - f0
            if span <= 0:
                return float(v1)
            t = (frame - f0) / span
            return float(v0 + (v1 - v0) * t)
    return float(keys[-1][1])


def channels_at(resolved: dict, frame: int) -> dict:
    return {name: sample(keys, frame) for name, keys in resolved["channels"].items()}


def beat_at(resolved: dict, frame: int) -> dict:
    chosen = resolved["beats"][0]
    for beat in resolved["beats"]:
        if beat["start_frame"] <= frame <= beat["end_frame"]:
            return beat
        if frame >= beat["start_frame"]:
            chosen = beat
    return chosen


def load_yaml(path: Path) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_resolved(path: Path) -> dict:
    path = Path(path)
    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return resolve(load_yaml(path))


def words_document(resolved: dict) -> dict:
    """Voice timings in the same shape as pipeline/examples/lax_tokyo/words.json.

    Format B owns captions. This only shares the word clock so the two
    pipelines do not invent two schemas.
    """
    words = []
    for beat in resolved["beats"]:
        tokens = beat["narration"].split()
        if not tokens:
            continue
        span = max(0.05, beat["end"] - beat["start"] - 0.3)
        step = span / len(tokens)
        for i, token in enumerate(tokens):
            t0 = beat["start"] + i * step
            t1 = t0 + step * 0.92
            words.append({"w": token, "t0": round(t0, 3), "t1": round(t1, 3)})
    return {"duration": resolved["duration"], "words": words}


def timeline_document(resolved: dict) -> dict:
    return {
        "id": resolved["id"],
        "title": resolved["title"],
        "fps": resolved["fps"],
        "width": resolved["width"],
        "height": resolved["height"],
        "duration_sec": resolved["duration"],
        "frame_count": resolved["frame_count"],
        "word_rate": RATE,
        "pause_sec": PAUSE,
        "beats": [
            {
                "id": beat["id"],
                "start": beat["start"],
                "end": beat["end"],
                "narration": beat["narration"],
                "time_label": beat["time_label"],
            }
            for beat in resolved["beats"]
        ],
    }


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("episodes/humans_disappeared.yaml")
    resolved = load_resolved(target)
    print(f"{resolved['id']}  {resolved['duration']:.3f}s  {resolved['frame_count']} frames")
    words = 0
    for beat in resolved["beats"]:
        words += beat["words"]
        print(
            f"  {beat['start']:6.2f}-{beat['end']:6.2f}  {beat['words']:2d}w  {beat['time_label'] or beat['id']:16}  {beat['narration']}"
        )
    print("words", words)
