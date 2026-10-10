#!/usr/bin/env python3
"""Render one map Short from a YAML spec.

Exit 0 when QC passes. Exit 2 when QC fails. The report is written either way.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from jt.audio import (  # noqa: E402
    SR,
    assemble,
    loudnorm_two_pass,
    measure_wav,
    mix,
    mux,
    synth_lines,
    write_wav,
)
from jt.data import build_earth  # noqa: E402
from jt.qc import evaluate, write_report  # noqa: E402
from jt.render import FPS, Studio, render_stills, render_video, save_contact  # noqa: E402
from jt.review import write_packet  # noqa: E402
from jt.spec import load_spec  # noqa: E402

PRESETS = {
    "final": (1080, 1920, 17),
    "preview": (540, 960, 20),
}


def _trim(audio, n_frames: int):
    import numpy as np
    samples = n_frames * SR // FPS
    if len(audio) < samples:
        pad = np.zeros((samples - len(audio), audio.shape[1]), np.float32)
        audio = np.concatenate([audio, pad], axis=0)
    return audio[:samples]


def build(spec_path: Path, out: Path, preset: str, hero: bool) -> int:
    spec = load_spec(spec_path)
    out.mkdir(parents=True, exist_ok=True)
    earth = build_earth()
    print("voice…", flush=True)
    takes = synth_lines(spec, out / "takes")
    voice, timeline = assemble(spec, takes)
    write_wav(out / "voice.wav", voice, SR)
    print("mix…", flush=True)
    mixed, mix_report = mix(spec, voice, timeline)
    w, h, crf = PRESETS[preset]
    n = max(2, int(round(timeline["duration"] * FPS)))
    mixed = _trim(mixed, n)
    timeline["duration"] = round(n / FPS, 4)
    write_wav(out / "mix.wav", mixed, SR)
    (out / "timeline.json").write_text(json.dumps(timeline, indent=2))
    (out / "mix_report.json").write_text(json.dumps(mix_report, indent=2))

    norm = out / "norm.wav"
    tp_target = -1.5
    for attempt in range(3):
        loudnorm_two_pass(out / "mix.wav", norm, tp=tp_target)
        measured = measure_wav(norm)
        print(f"loudnorm attempt {attempt + 1}: {measured}", flush=True)
        if measured["tp"] <= -1.4 and abs(measured["lufs"] + 14) <= 1.2:
            break
        tp_target -= 0.6
    mix_report["wav_lufs"] = measured["lufs"]
    mix_report["wav_tp"] = measured["tp"]

    hero_metrics = None
    if hero:
        times = [0.0]
        for ln in timeline["lines"][1:]:
            times.append(round(min(float(ln["start"]) + 0.15, timeline["duration"] - 0.05), 2))
        times = times[:6]
        print("hero stills", times, flush=True)
        hero_studio = Studio(earth, spec, timeline, 1080, 1920)
        hero_metrics = render_stills(hero_studio, times, out / "stills")
        (out / "hero_metrics.json").write_text(json.dumps(hero_metrics, indent=2))

    print(f"video {w}x{h}…", flush=True)
    studio = Studio(earth, spec, timeline, w, h)
    metrics = render_video(studio, out / "silent.mp4", crf=crf)
    contact_frames = metrics.pop("contact")
    save_contact(contact_frames, out / "contact.jpg")
    (out / "render_metrics.json").write_text(json.dumps(metrics, indent=2))

    final = out / "final.mp4"
    mux(out / "silent.mp4", norm, final)
    print("qc…", flush=True)
    report = evaluate(final, timeline, mix_report, metrics, hero_metrics)
    text = write_report(report, out / "qc.txt")
    write_packet(spec, out, report, mix_report)
    print(text)
    if not report["pass"]:
        print("QC FAIL — final.mp4 was still written", flush=True)
        return 2
    print("QC PASS", final, flush=True)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Render a map Short from YAML")
    p.add_argument("spec", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--preset", choices=tuple(PRESETS), default="preview")
    p.add_argument("--no-hero", action="store_true", help="skip the 1080×1920 stills")
    args = p.parse_args(argv)
    return build(args.spec, args.out, args.preset, hero=not args.no_hero)


if __name__ == "__main__":
    raise SystemExit(main())
