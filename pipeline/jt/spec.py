"""Load a video spec. One YAML file is one Short."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJS = ("ortho", "merc", "laea")
KINDS = ("q", "s", "p", "h")


@dataclass
class Camera:
    proj: str
    lon: float
    lat: float
    span: float

    def copy(self) -> "Camera":
        return Camera(self.proj, self.lon, self.lat, self.span)


@dataclass
class Line:
    text: str
    kind: str
    gap: float
    claim: str
    sub: str
    camera: Camera
    visuals: list
    say: str
    dur: float = 0.0


@dataclass
class Spec:
    id: str
    title: str
    theme: str
    description: str
    tags: list
    sources: list
    lines: list
    voice: dict
    path: str = ""
    notes: str = ""


def _camera(raw: dict) -> Camera:
    proj = str(raw.get("proj", "ortho"))
    if proj not in PROJS:
        raise ValueError(f"proj must be one of {PROJS}, got {proj}")
    return Camera(
        proj=proj,
        lon=float(raw["lon"]),
        lat=float(raw["lat"]),
        span=float(raw.get("span", 60)),
    )


def load_spec(path: str | Path) -> Spec:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    lines = []
    for i, item in enumerate(raw["lines"]):
        kind = str(item.get("kind", "s"))
        if kind not in KINDS:
            raise ValueError(f"line {i} kind {kind} not in {KINDS}")
        text = str(item["text"]).strip()
        say = str(item.get("say", text)).strip()
        lines.append(Line(
            text=text,
            kind=kind,
            gap=float(item.get("gap", 0.0)),
            claim=str(item.get("claim", text)),
            sub=str(item.get("sub", "")),
            camera=_camera(item["camera"]),
            visuals=list(item.get("visuals") or []),
            say=say,
            dur=float(item.get("dur", 0.0) or 0.0),
        ))
    if len(lines) < 2:
        raise ValueError("a short needs at least two lines")
    voice = dict(raw.get("voice") or {})
    voice.setdefault("engine", "espeak")
    voice.setdefault("voice", "en-us")
    voice.setdefault("rate", 138)
    spec = Spec(
        id=str(raw.get("id") or path.stem),
        title=str(raw.get("title") or path.stem),
        theme=str(raw.get("theme") or "midnight"),
        description=str(raw.get("description") or "").strip() + "\n",
        tags=list(raw.get("tags") or []),
        sources=list(raw.get("sources") or []),
        lines=lines,
        voice=voice,
        path=str(path),
        notes=str(raw.get("notes") or ""),
    )
    problems = pause_problems(spec)
    if problems and voice.get("enforce_pauses", True):
        raise ValueError("pause rules failed:\n- " + "\n- ".join(problems))
    return spec


def silent_timeline(spec: Spec) -> dict:
    """Beat clock for a picture with no voice and no burned-in karaoke.

    Each line's `dur` is the beat length. The owner's voice is fitted later.
    """
    if spec.voice.get("engine") != "silent":
        raise ValueError("silent_timeline is only for voice.engine: silent")
    t = 0.0
    lines = []
    for i, ln in enumerate(spec.lines):
        if ln.dur <= 0:
            raise ValueError(f"line {i} needs a positive dur on a silent short")
        start = round(t, 2)
        t = round(t + ln.dur, 2)
        claim = ln.claim
        lines.append({
            "index": i,
            "text": ln.text,
            "say": ln.say,
            "kind": ln.kind,
            "start": start,
            "end": t,
            "gap": 0.0,
            "words": [],
            "on_screen": {"claim": claim, "sub": ln.sub},
            "claim": claim,
            "sub": ln.sub,
        })
    if not lines:
        raise ValueError("silent short has no beats")
    return {
        "duration": t,
        "silent": True,
        "captions_burned_in": False,
        "caption_band": {"y0": 0.64, "y1": 0.72},
        "lead_in": 0.0,
        "lines": lines,
        "beats": lines,
        "words": [],
        "sample_rate": None,
        "voice": "none",
    }


def gaps_of(spec: Spec) -> list[float]:
    """Pauses after each sentence except the last."""
    return [ln.gap for ln in spec.lines[:-1]]


def pause_problems(spec: Spec) -> list[str]:
    """Reviewer pause rules. Empty list means the skeleton is acceptable."""
    gaps = gaps_of(spec)
    problems = []
    if any(abs(a - b) < 0.005 for a, b in zip(gaps, gaps[1:])):
        problems.append("two pauses in a row are equal")
    punch = [i for i, ln in enumerate(spec.lines) if ln.kind == "p"]
    if len(punch) != 1:
        problems.append(f"need exactly one punchline (kind p), found {len(punch)}")
    else:
        before = punch[0] - 1
        if before < 0 or not (0.55 <= spec.lines[before].gap <= 0.60):
            problems.append("the pause before the punchline must be 0.55–0.60 s")
    for i, g in enumerate(gaps):
        is_punch_gap = punch and i == punch[0] - 1
        if is_punch_gap:
            continue
        if not (0.20 <= g <= 0.45):
            problems.append(f"gap {i} is {g:.2f}s; ordinary pauses must be 0.20–0.45 s")
    if len(gaps) >= 2:
        import statistics
        sd = statistics.pstdev(gaps)
        if sd < 0.10:
            problems.append(f"pause SD {sd:.3f}s is under 0.10 s")
    return problems
