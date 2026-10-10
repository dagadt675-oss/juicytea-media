"""YAML episode -> per-frame timeline.

Conventions shared with the sibling what-if engine (whatif/engine/spec.py,
when that lands): id, title, status, fps, width, height, and a timeline
document with beats. This module adds the scale-journey fields. It does not
import the sibling package.
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .camera import (
    layer_weights,
    place_proxy,
    pose_for,
    project,
    to_bu,
)
from .quantity import (
    Metrics,
    RiceParams,
    ShrinkParams,
    format_count,
    format_length,
    format_mass_tonnes,
    harvest_years,
    rice_day_for_height,
    rice_day_for_volume,
    rice_metrics,
    shrink_metrics,
)

CAPTION_BAND = (1229, 1382)


@dataclass
class Milestone:
    id: str
    t: float
    label: str
    sub: str
    fact: str
    say: str
    word: str
    proxy: str  # "" | grain | tower | person | mountain | coin | sphere | marker
    param: float
    height_m: float
    anchor: tuple[float, float, float]


@dataclass
class Frame:
    frame: int
    t: float
    phase: str  # hook | journey | ending | dissolve
    param: float
    param_next: float
    metrics: Metrics
    pose_cam: tuple[float, float, float]
    pose_target: tuple[float, float, float]
    distance_m: float
    pitch_deg: float
    weights: dict[str, float]
    title_opacity: float
    ending_opacity: float
    dissolve: float
    fact: str
    fact_opacity: float
    labels: list[dict]
    primary_text: str
    secondary_text: str


@dataclass
class Episode:
    raw: dict
    milestones: list[Milestone]
    frames: list[Frame] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def fps(self) -> int:
        return int(self.raw["fps"])

    @property
    def width(self) -> int:
        return int(self.raw["width"])

    @property
    def height(self) -> int:
        return int(self.raw["height"])

    @property
    def direction(self) -> str:
        return self.raw["direction"]

    @property
    def duration(self) -> float:
        timing = self.raw["timing"]
        return float(timing["hook_hold"]) + (
            float(timing["journey_end"]) - float(timing["hook_hold"])
        ) + float(timing["ending_hold"]) + float(timing["dissolve"])


def load_raw(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a YAML mapping")
    for key in ("id", "title", "status", "fps", "width", "height", "direction", "module", "timing", "camera", "counter", "quantity", "milestones"):
        if key not in data:
            raise ValueError(f"{path} missing '{key}'")
    if data["module"] != "scale_journey":
        raise ValueError(f"{path} module is {data['module']!r}, expected scale_journey")
    if data["direction"] not in ("out", "in"):
        raise ValueError("direction must be 'out' or 'in'")
    return data


def _rice_params(raw: dict) -> RiceParams:
    q = raw["quantity"]
    return RiceParams(
        days=int(q.get("days", 64)),
        grain_length_m=float(q["grain_length_m"]),
        grain_width_m=float(q["grain_width_m"]),
        grain_thickness_m=float(q["grain_thickness_m"]),
        grain_mass_kg=float(q["grain_mass_kg"]),
        bulk_density_kg_m3=float(q["bulk_density_kg_m3"]),
        repose_deg=float(q["repose_deg"]),
        world_production_tonnes=float(q["world_production_tonnes"]),
    )


def _shrink_params(raw: dict) -> ShrinkParams:
    q = raw["quantity"]
    return ShrinkParams(start_m=float(q["start_m"]))


def _metrics_at(raw: dict, param: float) -> Metrics:
    kind = raw["quantity"]["preset"]
    if kind == "rice_doubling":
        return rice_metrics(param, _rice_params(raw))
    if kind == "shrink_half":
        return shrink_metrics(param, _shrink_params(raw))
    raise ValueError(f"unknown quantity preset {kind!r}")


def _param_for_milestone(raw: dict, item: dict) -> tuple[float, float]:
    """Return (param, height_m) for one milestone entry."""
    kind = raw["quantity"]["preset"]
    if "day" in item and kind == "rice_doubling":
        m = rice_metrics(float(item["day"]), _rice_params(raw))
        return m.param, m.height_m
    if "second" in item and kind == "shrink_half":
        m = shrink_metrics(float(item["second"]), _shrink_params(raw))
        return m.param, m.height_m
    if "match_height_m" in item and kind == "rice_doubling":
        day = rice_day_for_height(float(item["match_height_m"]), _rice_params(raw))
        m = rice_metrics(day, _rice_params(raw))
        return m.param, m.height_m
    if "match_volume_m3" in item and kind == "rice_doubling":
        day = rice_day_for_volume(float(item["match_volume_m3"]), _rice_params(raw))
        m = rice_metrics(day, _rice_params(raw))
        return m.param, m.height_m
    if "match_height_m" in item and kind == "shrink_half":
        target = float(item["match_height_m"])
        start = float(raw["quantity"]["start_m"])
        if target >= start:
            second = 0.0
        else:
            second = math.log2(start / target)
        m = shrink_metrics(second, _shrink_params(raw))
        return m.param, m.height_m
    raise ValueError(f"milestone {item.get('id')} has no day/second/match_*")


def _pchip_slopes(xs: list[float], ys: list[float]) -> list[float]:
    n = len(xs)
    if n == 1:
        return [0.0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] if h[i] else 0.0 for i in range(n - 1)]
    m = [0.0] * n
    m[0] = d[0]
    m[-1] = d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0.0:
            m[i] = 0.0
        else:
            m[i] = (h[i - 1] + h[i]) / ((h[i] / d[i - 1]) + (h[i - 1] / d[i]))
    return m


def _hermite(xs: list[float], ys: list[float], slopes: list[float], t: float) -> float:
    if t <= xs[0]:
        return ys[0]
    if t >= xs[-1]:
        return ys[-1]
    i = bisect.bisect_right(xs, t) - 1
    i = min(max(i, 0), len(xs) - 2)
    h = xs[i + 1] - xs[i]
    if h <= 0:
        return ys[i]
    s = (t - xs[i]) / h
    s2 = s * s
    s3 = s2 * s
    h00 = 2 * s3 - 3 * s2 + 1
    h10 = s3 - 2 * s2 + s
    h01 = -2 * s3 + 3 * s2
    h11 = s3 - s2
    return h00 * ys[i] + h10 * h * slopes[i] + h01 * ys[i + 1] + h11 * h * slopes[i + 1]


def _tokens(raw: dict, metrics: Metrics) -> dict[str, str]:
    kind = raw["quantity"]["preset"]
    tokens = {
        "height": format_length(metrics.height_m),
        "day": f"{metrics.param:.0f}",
        "second": f"{metrics.param:.0f}",
        "grains": format_count(metrics.grains) if metrics.grains else "0",
        "mass": format_mass_tonnes(metrics.mass_kg) if metrics.mass_kg else "0 tonnes",
        "years": "0",
    }
    if kind == "rice_doubling":
        years = harvest_years(metrics.grains, _rice_params(raw))
        tokens["years"] = str(int(round(years)))
        tokens["day"] = str(int(round(metrics.param)))
    return tokens


def _fill(text: str, tokens: dict[str, str]) -> str:
    if not text:
        return ""
    out = text
    for key, value in tokens.items():
        out = out.replace("{" + key + "}", value)
    return out


def retime_milestones(raw: dict, words_path: str | Path) -> dict:
    """Shift milestone ``t`` values onto ElevenLabs word starts. Monotone."""
    import json

    with open(words_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    words = payload.get("words", payload)
    index: dict[str, float] = {}
    for entry in words:
        token = str(entry["word"]).strip().lower().strip(".,!?:;\"'")
        if token and token not in index:
            index[token] = float(entry["start"])
    timing = raw["timing"]
    t0 = float(timing["hook_hold"])
    t1 = float(timing["journey_end"])
    updated = []
    warnings = []
    last_t = t0
    for item in raw["milestones"]:
        item = dict(item)
        word = str(item.get("word", "")).strip().lower()
        if word:
            if word not in index:
                warnings.append(f"word {word!r} not in words.json; kept t={item['t']}")
            else:
                new_t = index[word]
                if new_t <= last_t + 0.15 or new_t >= t1:
                    warnings.append(f"word {word!r} at {new_t:.2f}s would break the forward zoom; kept t={item['t']}")
                else:
                    item["t"] = round(new_t, 3)
        last_t = float(item["t"])
        updated.append(item)
    raw = dict(raw)
    raw["milestones"] = updated
    raw["_retime_warnings"] = warnings
    return raw


def _build_milestones(raw: dict) -> list[Milestone]:
    cam = raw["camera"]
    milestones: list[Milestone] = []
    for item in raw["milestones"]:
        param, height_m = _param_for_milestone(raw, item)
        metrics = _metrics_at(raw, param)
        tokens = _tokens(raw, metrics)
        pose = pose_for(
            height_m,
            raw["direction"],
            float(cam["hold_distance_m"]),
            float(cam["framing"]),
            float(cam["pitch_deg"]),
            float(cam["look_frac"]),
            float(cam["lens_mm"]),
            float(cam["sensor_height_mm"]),
        )
        proxy = str(item.get("proxy", ""))
        if proxy in ("", "grain", "marker"):
            anchor = (0.0, 0.0, height_m)
        else:
            anchor = place_proxy(
                float(item.get("proxy_height_m", height_m)),
                metrics.height_m,
                metrics.radius_m,
                pose,
                float(cam["lens_mm"]),
                float(cam["sensor_height_mm"]),
                int(raw["width"]),
                int(raw["height"]),
                side=float(item.get("side", 1.0)),
            )
            anchor = (anchor[0], anchor[1], float(item.get("proxy_height_m", height_m)))
        milestones.append(
            Milestone(
                id=str(item["id"]),
                t=float(item["t"]),
                label=_fill(str(item.get("label", "")), tokens),
                sub=_fill(str(item.get("sub", "")), tokens),
                fact=_fill(str(item.get("fact", "")), tokens),
                say=_fill(str(item.get("say", "")), tokens),
                word=str(item.get("word", "")),
                proxy=proxy,
                param=param,
                height_m=height_m,
                anchor=anchor,
            )
        )
    times = [m.t for m in milestones]
    if times != sorted(times):
        raise ValueError("milestone times must increase")
    params = [m.param for m in milestones]
    if params != sorted(params):
        raise ValueError("milestone parameters must increase (days, or shrink-seconds)")
    if raw["direction"] == "in":
        heights = [m.height_m for m in milestones]
        if heights != sorted(heights, reverse=True):
            raise ValueError("zoom-in milestones must shrink")
    return milestones


def _param_at(raw: dict, milestones: list[Milestone], t: float) -> float:
    timing = raw["timing"]
    hook = float(timing["hook_hold"])
    journey_end = float(timing["journey_end"])
    start_param = milestones[0].param
    end_param = milestones[-1].param
    if t <= hook:
        return start_param
    if t >= journey_end:
        return end_param
    xs = [hook]
    ys = [start_param]
    for m in milestones:
        if hook < m.t < journey_end and m.t not in xs:
            xs.append(m.t)
            ys.append(m.param)
        elif abs(m.t - journey_end) < 1e-6:
            pass
    if xs[-1] < journey_end:
        xs.append(journey_end)
        ys.append(end_param)
    # Drop non-monotone duplicates that would stall the spline backwards.
    clean_x = [xs[0]]
    clean_y = [ys[0]]
    for x, y in zip(xs[1:], ys[1:]):
        if x <= clean_x[-1]:
            continue
        if raw["direction"] == "out" and y < clean_y[-1]:
            y = clean_y[-1]
        if raw["direction"] == "in" and y < clean_y[-1]:
            y = clean_y[-1]
        clean_x.append(x)
        clean_y.append(y)
    slopes = _pchip_slopes(clean_x, clean_y)
    value = _hermite(clean_x, clean_y, slopes, t)
    if raw["direction"] == "out":
        return min(max(value, start_param), end_param)
    return min(max(value, start_param), end_param)


def _fade(t: float, t0: float, t1: float) -> float:
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    u = (t - t0) / (t1 - t0)
    return u * u * (3.0 - 2.0 * u)


def resolve(raw: dict) -> Episode:
    milestones = _build_milestones(raw)
    fps = int(raw["fps"])
    timing = raw["timing"]
    hook = float(timing["hook_hold"])
    journey_end = float(timing["journey_end"])
    ending_hold = float(timing["ending_hold"])
    dissolve_dur = float(timing["dissolve"])
    ending_start = journey_end
    dissolve_start = journey_end + ending_hold
    duration = dissolve_start + dissolve_dur
    n_frames = int(round(duration * fps))
    cam = raw["camera"]
    title = raw.get("hook", {})
    ending = raw.get("ending", {})
    frames: list[Frame] = []
    params = []
    for i in range(n_frames):
        t = i / fps
        if t < hook:
            phase = "hook"
        elif t < journey_end:
            phase = "journey"
        elif t < dissolve_start:
            phase = "ending"
        else:
            phase = "dissolve"
        param = _param_at(raw, milestones, min(t, dissolve_start))
        params.append(param)
    for i in range(n_frames):
        t = i / fps
        if t < hook:
            phase = "hook"
        elif t < journey_end:
            phase = "journey"
        elif t < dissolve_start:
            phase = "ending"
        else:
            phase = "dissolve"
        param = params[i]
        param_next = params[i + 1] if i + 1 < n_frames else param
        # Never let a spline wiggle reverse the zoom.
        if raw["direction"] == "out":
            param = max(param, params[i - 1] if i else param)
            param_next = max(param_next, param)
        else:
            param = max(param, params[i - 1] if i else param)
            param_next = max(param_next, param)
        params[i] = param
        metrics = _metrics_at(raw, param)
        tokens = _tokens(raw, metrics)
        pose = pose_for(
            metrics.height_m,
            raw["direction"],
            float(cam["hold_distance_m"]),
            float(cam["framing"]),
            float(cam["pitch_deg"]),
            float(cam["look_frac"]),
            float(cam["lens_mm"]),
            float(cam["sensor_height_mm"]),
        )
        weights = layer_weights(metrics.height_m, raw["direction"])
        title_out = _fade(t, float(title.get("fade_start", hook)), float(title.get("fade_end", hook + 0.6)))
        title_opacity = 1.0 - title_out if t < float(title.get("fade_end", hook + 0.6)) else 0.0
        if phase == "dissolve":
            title_opacity = 0.0
        end_in = _fade(t, ending_start, ending_start + 0.35)
        end_out = _fade(t, dissolve_start, dissolve_start + dissolve_dur * 0.55)
        ending_opacity = end_in * (1.0 - end_out) if phase in ("ending", "dissolve") else 0.0
        dissolve = 0.0
        if phase == "dissolve":
            dissolve = _fade(t, dissolve_start, dissolve_start + dissolve_dur)
        fact = ""
        fact_opacity = 0.0
        labels = []
        for m in milestones:
            # Leader + fact live a couple of seconds around the milestone.
            span_in, span_out = 0.35, 2.4
            local = t - m.t
            if -span_in <= local <= span_out and phase != "hook" or (m.t < hook and phase == "hook" and m.proxy == "grain"):
                appear = _fade(t, m.t - span_in, m.t - span_in + 0.28)
                depart = _fade(t, m.t + span_out - 0.4, m.t + span_out)
                opacity = appear * (1.0 - depart)
                if m.t < hook and phase == "hook":
                    opacity = title_opacity
                if opacity <= 0.02:
                    continue
                screen = project(
                    pose,
                    m.anchor,
                    int(raw["width"]),
                    int(raw["height"]),
                    float(cam["lens_mm"]),
                    float(cam["sensor_height_mm"]),
                )
                labels.append(
                    {
                        "id": m.id,
                        "label": m.label,
                        "sub": m.sub,
                        "opacity": opacity,
                        "screen": screen,
                        "anchor_m": m.anchor,
                    }
                )
                if m.fact and opacity > fact_opacity and phase == "journey":
                    fact = m.fact
                    fact_opacity = opacity
        if phase == "hook":
            fact = ""
            fact_opacity = 0.0
        counter = raw["counter"]
        if counter["primary"]["source"] == "day":
            primary_text = f"{param:.3f}"
        elif counter["primary"]["source"] == "second":
            primary_text = f"{param:.3f}"
        else:
            primary_text = f"{param:.3f}"
        secondary_text = format_length(metrics.height_m)
        if t < hook:
            phase_name = "hook"
        elif t < journey_end:
            phase_name = "journey"
        elif t < dissolve_start:
            phase_name = "ending"
        else:
            phase_name = "dissolve"
        frames.append(
            Frame(
                frame=i,
                t=t,
                phase=phase_name,
                param=param,
                param_next=param_next,
                metrics=metrics,
                pose_cam=pose.cam,
                pose_target=pose.target,
                distance_m=pose.distance_m,
                pitch_deg=pose.pitch_deg,
                weights=weights,
                title_opacity=title_opacity,
                ending_opacity=ending_opacity,
                dissolve=dissolve,
                fact=fact,
                fact_opacity=fact_opacity,
                labels=labels,
                primary_text=primary_text,
                secondary_text=secondary_text,
            )
        )
    # Fill templates that should use the FINAL metrics (ending card).
    final = _metrics_at(raw, milestones[-1].param)
    raw["_tokens_final"] = _tokens(raw, final)
    ep = Episode(raw=raw, milestones=milestones, frames=frames)
    return ep


def ending_lines(ep: Episode) -> list[str]:
    tokens = ep.raw.get("_tokens_final", {})
    lines = []
    for line in ep.raw.get("ending", {}).get("lines", []):
        lines.append(_fill(str(line), tokens))
    return lines


def title_lines(ep: Episode) -> list[str]:
    return [str(line) for line in ep.raw.get("hook", {}).get("lines", [])]


def highlight_phrase(ep: Episode, which: str) -> str:
    tokens = ep.raw.get("_tokens_final", {})
    return _fill(str(ep.raw.get(which, {}).get("highlight", "")), tokens)


def timeline_document(ep: Episode) -> dict:
    fps = ep.fps
    timing = ep.raw["timing"]
    beats = [
        {
            "id": "hook",
            "start": 0.0,
            "end": float(timing["hook_hold"]),
            "narration": ep.raw.get("hook", {}).get("say", ep.raw["title"]),
            "on_screen": " ".join(title_lines(ep)),
        }
    ]
    for m in ep.milestones:
        if m.t < float(timing["hook_hold"]) and m.proxy == "grain":
            continue
        beats.append(
            {
                "id": m.id,
                "start": max(0.0, m.t - 0.3),
                "end": m.t + 2.4,
                "narration": m.say,
                "label": m.label,
                "sub": m.sub,
                "fact": m.fact,
                "param": m.param,
                "height_m": m.height_m,
                "height": format_length(m.height_m),
            }
        )
    dissolve_start = float(timing["journey_end"]) + float(timing["ending_hold"])
    beats.append(
        {
            "id": "ending",
            "start": float(timing["journey_end"]),
            "end": dissolve_start + float(timing["dissolve"]),
            "narration": " ".join(ending_lines(ep)),
            "on_screen": " ".join(ending_lines(ep)),
        }
    )
    counters = []
    for fr in ep.frames:
        counters.append(
            {
                "f": fr.frame,
                "t": round(fr.t, 4),
                "phase": fr.phase,
                "param": fr.param,
                "primary": ep.raw["counter"]["primary"]["label"],
                "secondary": ep.raw["counter"]["secondary"]["label"],
                "height_m": fr.metrics.height_m,
                "height": fr.secondary_text,
                "grains": fr.metrics.grains,
                "layers": fr.weights,
            }
        )
    band = ep.raw.get("caption_band", list(CAPTION_BAND))
    return {
        "id": ep.id,
        "title": ep.raw["title"],
        "module": "scale_journey",
        "status": ep.raw["status"],
        "fps": fps,
        "width": ep.width,
        "height": ep.height,
        "direction": ep.direction,
        "duration_sec": ep.frames[-1].t + 1.0 / fps if ep.frames else 0.0,
        "frame_count": len(ep.frames),
        "caption_band": {"y0": int(band[0]), "y1": int(band[1])},
        "loop_to_frame": 0,
        "seamless_loop": True,
        "retime_warnings": ep.raw.get("_retime_warnings", []),
        "beats": beats,
        "milestones": [
            {
                "id": m.id,
                "t": m.t,
                "frame": int(round(m.t * fps)),
                "label": m.label,
                "sub": m.sub,
                "fact": m.fact,
                "say": m.say,
                "word": m.word,
                "param": m.param,
                "height_m": m.height_m,
                "height": format_length(m.height_m),
                "anchor_m": list(m.anchor),
            }
            for m in ep.milestones
        ],
        "counters": counters,
        "ending": ending_lines(ep),
    }


def blender_frames(ep: Episode, frames: list[Frame]) -> dict[str, list[dict]]:
    """Per-layer jobs. Coordinates are layer-local Blender units."""
    from .camera import layer_by_id

    jobs: dict[str, list[dict]] = {}
    cam = ep.raw["camera"]
    for fr in frames:
        for layer_id, weight in fr.weights.items():
            if weight < 0.04:
                continue
            layer = layer_by_id(layer_id)
            jobs.setdefault(layer_id, [])
            anchor_bu = []
            for label in fr.labels:
                anchor_bu.append(to_bu(tuple(label["anchor_m"]), layer.meters_per_bu))
            jobs[layer_id].append(
                {
                    "frame": fr.frame,
                    "weight": weight,
                    "cam": to_bu(fr.pose_cam, layer.meters_per_bu),
                    "target": to_bu(fr.pose_target, layer.meters_per_bu),
                    "h_bu": fr.metrics.height_m / layer.meters_per_bu,
                    "r_bu": fr.metrics.radius_m / layer.meters_per_bu,
                    "grains": fr.metrics.grains,
                    "visual": fr.metrics.visual,
                    "param": fr.param,
                    "meters_per_bu": layer.meters_per_bu,
                    "lens_mm": float(cam["lens_mm"]),
                    "sensor_height_mm": float(cam["sensor_height_mm"]),
                }
            )
    return jobs
