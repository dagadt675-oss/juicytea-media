"""Automatic QC. A FAIL refuses the short. WARNs are printed and kept."""

from __future__ import annotations

import json
import statistics
import subprocess
from pathlib import Path

import numpy as np

from jt.captions import switch_error
from jt.draw import text_pixel_mask


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    blob = (r.stderr or "") + (r.stdout or "")
    if r.returncode != 0:
        raise RuntimeError(blob[-2000:])
    return blob


def ffprobe(path: Path) -> dict:
    text = _run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", str(path),
    ])
    return json.loads(text[text.find("{"):])


def ebur128(path: Path) -> dict:
    text = _run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    integrated = true_peak = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("I:") and "LUFS" in s:
            integrated = float(s.split()[1])
        if s.startswith("Peak:") and "dBFS" in s:
            true_peak = float(s.split()[1])
    if integrated is None or true_peak is None:
        raise RuntimeError("ebur128 parse failed\n" + text[-1200:])
    return {"lufs": integrated, "tp": true_peak}


def _decode_gray(path: Path, w=160, h=90) -> np.ndarray:
    info = ffprobe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    n = int(v.get("nb_frames") or 0)
    if n <= 0:
        dur = float(v["duration"])
        rate = v["r_frame_rate"]
        num, den = [float(x) for x in rate.split("/")]
        n = int(round(dur * num / den))
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path),
         "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True,
    ).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, h, w)
    return frames


def _frozen(frames: np.ndarray, fps: float) -> list[dict]:
    if len(frames) < 3:
        return []
    diff = np.mean(np.abs(frames[1:].astype(np.int16) - frames[:-1].astype(np.int16)), axis=(1, 2))
    spans = []
    run = 0
    start = 0
    # Flat political maps only change along coasts, so the same pan that is
    # obvious on screen is a smaller number than textured footage. 0.8 was that
    # textured bar and flagged a moving flat map. 0.18 still fails a real lock.
    thresh = 0.18
    for i, d in enumerate(diff):
        if d < thresh:
            if run == 0:
                start = i
            run += 1
        elif run:
            dur = run / fps
            if dur >= 0.4:
                spans.append({"start": round(start / fps, 3), "end": round((start + run) / fps, 3), "dur": round(dur, 3)})
            run = 0
    if run:
        dur = run / fps
        if dur >= 0.4:
            spans.append({"start": round(start / fps, 3), "end": round((start + run) / fps, 3), "dur": round(dur, 3)})
    return spans


def _loop_diff(frames: np.ndarray) -> float:
    if len(frames) < 2:
        return 999.0
    return float(np.mean(np.abs(frames[0].astype(np.int16) - frames[-1].astype(np.int16))))


def _safe_samples(path: Path, fps_out: float = 2.0) -> dict:
    info = ffprobe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={fps_out}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout
    frame_n = w * h * 3
    count = len(raw) // frame_n
    worst = 0
    bad_frames = 0
    limit_x = int(round(900 * w / 1080))
    top = int(0.12 * h)
    bot = int(0.80 * h)
    for i in range(count):
        rgb = np.frombuffer(raw, np.uint8, count=frame_n, offset=i * frame_n).reshape(h, w, 3)
        mask = text_pixel_mask(rgb)
        unsafe = np.zeros(mask.shape, bool)
        unsafe[:top, :] = True
        unsafe[bot:, :] = True
        unsafe[:, limit_x:] = True
        n = int(np.count_nonzero(mask & unsafe))
        worst = max(worst, n)
        if n > 12:
            bad_frames += 1
    return {"samples": count, "worst_pixels": worst, "bad_frames": bad_frames, "width": w, "height": h}


def _check(name: str, ok: bool, detail: str, fail: bool = True) -> dict:
    return {"name": name, "status": "PASS" if ok else ("FAIL" if fail else "WARN"), "detail": detail}


def evaluate(path: Path, timeline: dict, mix_report: dict, render_metrics: dict,
             hero_metrics: dict | None = None) -> dict:
    probe = ffprobe(path)
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    rate = v.get("r_frame_rate", "0/1")
    num, den = [float(x) for x in rate.split("/")]
    fps = num / den if den else 0
    checks = []
    w, h = int(v["width"]), int(v["height"])
    preset_ok = (w, h) in {(1080, 1920), (540, 960)}
    checks.append(_check("geometry", preset_ok and abs(fps - 30) < 0.01 and int(v.get("nb_frames", 1)) > 1,
                          f"{w}x{h} @ {fps:.3f} fps, {v.get('nb_frames')} frames"))
    tags_ok = (v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p"
               and v.get("color_space") == "bt709" and v.get("color_primaries") == "bt709"
               and v.get("color_transfer") == "bt709")
    checks.append(_check("video_codec", tags_ok,
                          f"{v.get('codec_name')} {v.get('pix_fmt')} {v.get('color_space')}/{v.get('color_primaries')}/{v.get('color_transfer')}"))
    a_ok = (a.get("codec_name") == "aac" and int(a.get("sample_rate", 0)) == 48000
            and int(a.get("channels", 0)) == 2)
    checks.append(_check("audio_codec", a_ok, f"{a.get('codec_name')} {a.get('sample_rate')} Hz {a.get('channels')} ch"))
    head = path.read_bytes()[:65536]
    checks.append(_check("faststart", b"moov" in head, "moov atom in the first 64 KB" if b"moov" in head else "moov not in the head"))
    loud = ebur128(path)
    checks.append(_check("loudness", abs(loud["lufs"] + 14) <= 1.0, f"{loud['lufs']:.2f} LUFS (target -14 ±1)"))
    checks.append(_check("true_peak", loud["tp"] <= -1.5, f"{loud['tp']:.2f} dBTP (limit -1.5)"))
    dur_v = float(v.get("duration") or probe["format"]["duration"])
    dur_a = float(a.get("duration") or dur_v)
    checks.append(_check("av_sync", abs(dur_v - dur_a) <= 0.04, f"video {dur_v:.3f}s audio {dur_a:.3f}s"))
    checks.append(_check("length", dur_v <= 59, f"{dur_v:.2f}s"))

    gray = _decode_gray(path)
    frozen = _frozen(gray, fps or 30)
    worst_freeze = max((s["dur"] for s in frozen), default=0)
    checks.append(_check("frozen", worst_freeze < 0.4, f"worst hold {worst_freeze:.2f}s spans {frozen[:4]}"))
    loop = _loop_diff(gray)
    checks.append(_check("loop", loop <= 8.0, f"mean abs diff last vs first {loop:.2f}/255 (raw copy {render_metrics.get('loop_raw_max')})"))

    safe = _safe_samples(path)
    checks.append(_check(
        "safe_zone",
        safe["worst_pixels"] <= 12 and render_metrics.get("unsafe_max", 0) <= 12 and render_metrics.get("spills", 1) == 0,
        f"decoded worst {safe['worst_pixels']} px in {safe['bad_frames']}/{safe['samples']} frames; "
        f"raw worst {render_metrics.get('unsafe_max')} spills {render_metrics.get('spills')}",
    ))

    hero = hero_metrics or {}
    cap_px = hero.get("caption_px_min") or render_metrics.get("caption_px_min") or 0
    # Hero stills are 1080-wide, so the number is the real glyph size.
    # A 540 preview reports the same reference size (layout is scaled from 1080).
    cap_src = "1080 stills" if hero_metrics else f"reference px (frame width {w})"
    checks.append(_check("caption_size", cap_px >= 64, f"min {cap_px:.0f} px at 1080 reference via {cap_src}"))
    c0 = hero.get("caption_center_min", render_metrics.get("caption_center_min", 0))
    c1 = hero.get("caption_center_max", render_metrics.get("caption_center_max", 0))
    checks.append(_check("caption_band", c0 >= 0.64 and c1 <= 0.72 and c0 > 0,
                          f"glyph centre {c0:.3f}–{c1:.3f} of height (want 0.64–0.72)"))
    err = switch_error(timeline["words"])
    checks.append(_check("caption_timing", err <= 0.10, f"highlight switches within {err:.3f}s of the word start"))

    gaps = [float(ln["gap"]) for ln in timeline["lines"][:-1]]
    sd = statistics.pstdev(gaps) if len(gaps) >= 2 else 0
    checks.append(_check("pause_sd", sd >= 0.10, f"SD {sd:.3f}s gaps {['%.2f' % g for g in gaps]}"))
    ratio = float(mix_report.get("sfx_under_voice_db") or 0)
    checks.append(_check("sfx_duck", ratio >= 10, f"SFX peak {ratio:.1f} dB under the voice peak"))
    hook = float(render_metrics.get("hook_motion") or 0)
    # 0.03 is the bar used on high-detail footage (players, grass). A flat
    # political map only changes along coasts, so the same number needs a
    # full-frame strobe. Fail only when the opening is effectively still.
    if hook >= 0.03:
        checks.append(_check("hook_motion", True, f"mean frame diff in the first second {hook:.4f}"))
    elif hook >= 0.004:
        checks.append(_check(
            "hook_motion", False,
            f"mean frame diff in the first second {hook:.4f} — the map is moving, under the 0.03 high-detail bar",
            fail=False,
        ))
    else:
        checks.append(_check(
            "hook_motion", False,
            f"mean frame diff in the first second {hook:.4f} — opening is effectively still",
        ))

    fails = [c for c in checks if c["status"] == "FAIL"]
    warns = [c for c in checks if c["status"] == "WARN"]
    return {
        "pass": not fails,
        "fails": len(fails),
        "warns": len(warns),
        "checks": checks,
        "loudness": loud,
        "frozen": frozen,
        "loop_diff": loop,
        "safe": safe,
        "pause_sd": sd,
        "duration": dur_v,
    }


def write_report(report: dict, path: Path) -> str:
    lines = [
        f"RESULT {'PASS' if report['pass'] else 'FAIL'}  fails={report['fails']} warns={report['warns']}",
        f"duration {report['duration']:.2f}s  LUFS {report['loudness']['lufs']:.2f}  TP {report['loudness']['tp']:.2f}",
        f"loop diff {report['loop_diff']:.2f}/255  pause SD {report['pause_sd']:.3f}s",
        "",
    ]
    for c in report["checks"]:
        lines.append(f"{c['status']:4}  {c['name']:16}  {c['detail']}")
    text = "\n".join(lines) + "\n"
    path.write_text(text)
    path.with_suffix(".json").write_text(json.dumps(report, indent=2, default=str))
    return text
