#!/usr/bin/env python3
"""Render one map Short from a YAML spec.

Exit 0 when QC passes. Exit 2 when QC fails. The report is written either way.
"""

from __future__ import annotations

import argparse
import json
import subprocess
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
from jt.qc import ebur128, evaluate, write_report  # noqa: E402
from jt.render import FPS, Studio, render_stills, render_video, save_contact  # noqa: E402
from jt.review import write_packet  # noqa: E402
from jt.spec import load_spec, silent_timeline  # noqa: E402

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


def _silent_picture_qc(path: Path, timeline: dict) -> tuple[bool, str]:
    """Geometry and an empty karaoke band. No loudness — there is no voice."""
    from jt.qc import ffprobe

    info = ffprobe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    w, h = int(v["width"]), int(v["height"])
    rate = v["r_frame_rate"]
    num, den = [float(x) for x in rate.split("/")]
    fps = num / den if den else 0
    dur = float(v.get("duration") or info["format"].get("duration") or 0)
    lines = [
        f"geometry {w}x{h} @ {fps:.3f} fps  h264 {v.get('pix_fmt')}",
        f"duration {dur:.2f}s  beats {len(timeline['beats'])}",
        f"audio streams {len(audio)}",
        "captions burned in: no",
    ]
    ok = (
        w == 1080 and h == 1920 and abs(fps - 30) < 0.01
        and v.get("codec_name") == "h264"
        and not audio
        and 22.0 <= dur <= 24.0
        and len(timeline["beats"]) == 8
    )
    band = _caption_band_text(path)
    lines.append(f"caption band y 0.64–0.72 text pixels {band}")
    ok = ok and band == 0
    lines.insert(0, "RESULT PASS  silent picture" if ok else "RESULT FAIL  silent picture")
    return ok, "\n".join(lines) + "\n"


def _caption_band_text(path: Path) -> int:
    """White/yellow/cyan/orange pixels inside the karaoke slot, sampled twice a second."""
    import numpy as np
    from jt.draw import text_pixel_mask

    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", "fps=2",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout
    frame = 1080 * 1920 * 3
    n = len(raw) // frame
    worst = 0
    y0, y1 = int(0.64 * 1920), int(0.72 * 1920)
    for i in range(n):
        img = np.frombuffer(raw[i * frame:(i + 1) * frame], np.uint8).reshape(1920, 1080, 3)
        worst = max(worst, int(np.count_nonzero(text_pixel_mask(img[y0:y1]))))
    return worst


def build_silent(spec, out: Path, preset: str, hero: bool) -> int:
    """Picture only. Does not call espeak or ElevenLabs."""
    import shutil

    from jt.review import write_packet

    out.mkdir(parents=True, exist_ok=True)
    w, h, crf = PRESETS[preset]
    earth = build_earth()
    timeline = silent_timeline(spec)
    timeline.update({
        "id": spec.id,
        "title": spec.title,
        "width": w,
        "height": h,
        "fps": FPS,
        "note": (
            "No audio and no burned-in karaoke. "
            "Fit an ElevenLabs read to beats[].say locally. "
            "Leave y 0.64–0.72 of the height empty for captions."
        ),
    })
    (out / "timeline.json").write_text(json.dumps(timeline, indent=2))
    (out / "description.txt").write_text(spec.description)
    print(f"silent picture {w}x{h} {timeline['duration']:.2f}s  no voice", flush=True)
    studio = Studio(earth, spec, timeline, w, h)
    hero_metrics = None
    if hero and (w, h) != (1080, 1920):
        times = [round((ln["start"] + ln["end"]) / 2, 2) for ln in timeline["beats"]]
        hero_metrics = render_stills(Studio(earth, spec, timeline, 1080, 1920), times, out / "stills")
    picture = out / "silent.mp4"
    metrics = render_video(studio, picture, crf=crf)
    contact = metrics.pop("contact")
    save_contact(contact, out / "contact.jpg")
    stills = out / "stills"
    stills.mkdir(exist_ok=True)
    for ln in timeline["beats"]:
        t = (ln["start"] + ln["end"]) / 2.0
        dest = stills / f"t{t:05.2f}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(picture), "-ss", f"{t:.3f}",
             "-frames:v", "1", str(dest)],
            check=True,
        )
    (out / "render_metrics.json").write_text(json.dumps(metrics, indent=2))
    shutil.copyfile(picture, out / "final.mp4")
    ok, text = _silent_picture_qc(picture, timeline)
    (out / "qc.txt").write_text(text)
    write_packet(spec, out, {"checks": [], "pass": ok}, {"voice": "none"})
    print(text)
    if not ok:
        print("PICTURE FAIL — silent.mp4 was still written", flush=True)
        return 2
    print("SILENT PICTURE", picture, flush=True)
    return 0


def build(spec_path: Path, out: Path, preset: str, hero: bool) -> int:
    spec = load_spec(spec_path)
    out.mkdir(parents=True, exist_ok=True)
    if spec.voice.get("engine") == "silent":
        return build_silent(spec, out, preset, hero)
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
    linear = True
    measured = {"lufs": -99.0, "tp": 0.0}
    for attempt in range(3):
        loudnorm_two_pass(out / "mix.wav", norm, tp=tp_target, linear=linear)
        measured = measure_wav(norm)
        print(f"loudnorm attempt {attempt + 1}: {measured} linear={linear}", flush=True)
        if measured["tp"] <= -1.4 and abs(measured["lufs"] + 14) <= 1.0:
            break
        # A quiet result means the peaks blocked a linear gain. Switch to the
        # dynamic pass instead of lowering the ceiling further.
        if measured["lufs"] < -15.0:
            linear = False
            tp_target = -1.5
        elif measured["tp"] > -1.4:
            tp_target -= 0.4
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
    # AAC often lands about 0.2 dB hotter than the wav. Tighten the wav ceiling
    # and remux until the file itself is under -1.5 dBTP. The picture is not rebuilt.
    for attempt in range(3):
        mux(out / "silent.mp4", norm, final)
        aac = ebur128(final)
        print(f"aac attempt {attempt + 1}: {aac}", flush=True)
        mix_report["aac_lufs"] = aac["lufs"]
        mix_report["aac_tp"] = aac["tp"]
        if aac["tp"] <= -1.5 and abs(aac["lufs"] + 14) <= 1.0:
            break
        tp_target = min(tp_target, aac["tp"]) - 0.5
        linear = aac["lufs"] >= -15.0
        loudnorm_two_pass(out / "mix.wav", norm, tp=tp_target, linear=linear)
    (out / "mix_report.json").write_text(json.dumps(mix_report, indent=2))
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
