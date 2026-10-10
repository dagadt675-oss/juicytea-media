"""Render silent Football Earth v5.

The picture is locked to the mapped narration. No voice, no music, and no
burned-in captions — the owner bot adds ElevenLabs and karaoke on top.
The strip y = 0.64–0.72 is left as a clean plate.

    python -m short15.make
    python -m short15.make --stills 0,1,5,8,13,16
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from short15.audio import _V4_WORDS
from short15.film import BAND0, BAND1, H, W, Scene, render_frame, marks_from

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
FPS = 30


def _words() -> list[dict]:
    return [{"text": text, "start": round(a, 4), "end": round(b, 4)} for text, a, b in _V4_WORDS]


def _timeline(words: list[dict], m: dict) -> dict:
    def r(key):
        return round(float(m[key]), 4)

    beats = [
        {"id": "hook", "start": 0.0, "end": r("snap"),
         "visual": "Elongated football Earth spinning from frame 0, Africa forward, laces on the left."},
        {"id": "leather_snap", "start": r("snap"), "end": r("the"),
         "visual": "Surface snaps to smooth leather. Gold continents, white end-stripes, laces."},
        {"id": "north_pole", "start": r("the"), "end": r("sorry"),
         "visual": "Tilt up. The pointy north tip sits in the starfield."},
        {"id": "santa", "start": r("sorry"), "end": r("workshop_end"),
         "visual": "Stylized 3D figure and cabin on the tip. Smoke drifts. Not a copyrighted character."},
        {"id": "oceans", "start": r("oceans"), "end": r("slide_end"),
         "visual": "Real ocean color slides toward the equator. Continents stay put."},
        {"id": "plot_twist", "start": r("plot"), "end": r("forty"),
         "visual": "The football eases toward a rounder Earth."},
        {"id": "fatter", "start": r("forty"), "end": r("tall_end"),
         "visual": "Oblate Earth, wider than it is tall. Dashed limb stays out of the caption strip."},
        {"id": "basically", "start": r("its"), "end": r("someone"),
         "visual": "Shape creeps back toward a football as the sitter appears above it."},
        {"id": "sat_on", "start": r("sat"), "end": r("hold_end"),
         "visual": "Figure sits and the ball squashes. Hold is at least 0.6 s with a settle bounce."},
        {"id": "loop", "start": r("hold_end"), "end": r("duration"),
         "visual": "Figure lifts, ball springs back to the opening football. Last frame equals frame 0."},
    ]
    return {
        "id": "short15_football_earth_v5",
        "silent": True,
        "voice": None,
        "captions_burned_in": False,
        "caption_band": {
            "y0": 0.64,
            "y1": 0.72,
            "px0": BAND0,
            "px1": BAND1,
            "note": "Clean plate. Draw karaoke here. Do not cover with picture.",
        },
        "fps": FPS,
        "width": W,
        "height": H,
        "duration": r("duration"),
        "script": (
            "I turned Earth into an American football. The North Pole is now in space. "
            "Sorry, Santa. Your workshop is now in space. Oceans? They slide. Plot twist: "
            "Earth is already forty-three kilometers fatter than it is tall. "
            "It's basically a football... that someone sat on."
        ),
        "words": words,
        "beats": beats,
        "notes": [
            "Word times are the mapped v4 narration (American English). I starts at 0.03 s; the picture is already moving at frame 0.",
            "Sorry and Santa are the emphasis pair. Micro-gaps are already in the word times before forty-three and before fatter.",
            "Loop the picture into the hook. The last frame is frame 0.",
        ],
    }


def _encode(frames_iter, n: int, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart",
        str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for i, frame in enumerate(frames_iter):
        proc.stdin.write(frame.tobytes())
        if i % 30 == 0:
            print(f"  frame {i}/{n}", flush=True)
    proc.stdin.close()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited {code}")


def _probe(path: Path) -> dict:
    text = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(text)


def _audit(path: Path) -> dict:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", "fps=2",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout
    frame_n = W * H * 3
    count = len(raw) // frame_n
    frames = np.frombuffer(raw, np.uint8).reshape(count, H, W, 3)
    small = frames[:, ::12, ::12].astype(np.int16)
    diff = np.mean(np.abs(small[1:] - small[:-1]), axis=(1, 2, 3)) / 255.0
    frozen = []
    run = 0
    start = 0
    for i, d in enumerate(diff):
        if d < 0.004:
            if run == 0:
                start = i
            run += 1
        elif run:
            if run * 0.5 > 0.5:
                frozen.append({"start": round(start * 0.5, 2), "dur": round(run * 0.5, 2)})
            run = 0
    if run and run * 0.5 > 0.5:
        frozen.append({"start": round(start * 0.5, 2), "dur": round(run * 0.5, 2)})

    head = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-t", "1.0",
         "-vf", "scale=160:90", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True,
    ).stdout
    g = np.frombuffer(head, np.uint8).reshape(-1, 90, 160)
    hook = float(np.mean(np.abs(g[1:].astype(np.int16) - g[:-1].astype(np.int16))) / 255.0) if len(g) > 2 else 0.0

    band_bright = []
    for i, f in enumerate(frames):
        band = f[BAND0:BAND1]
        bright = int(np.count_nonzero(band.max(axis=2) > 40))
        if bright:
            band_bright.append({"t": i * 0.5, "pixels": bright, "max": int(band.max())})
    # fps=2 stops short of the tail. Compare the real first and last pictures.
    def _one(index: int) -> np.ndarray:
        raw_one = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path),
             "-vf", f"select=eq(n\\,{index})", "-fps_mode", "passthrough",
             "-frames:v", "1",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, check=True,
        ).stdout
        need = W * H * 3
        if len(raw_one) < need:
            raise RuntimeError(f"frame {index} extract was {len(raw_one)} bytes")
        return np.frombuffer(raw_one[:need], np.uint8).reshape(H, W, 3)

    probed = _probe(path)
    video = next(s for s in probed["streams"] if s["codec_type"] == "video")
    last_i = int(video.get("nb_frames") or 0) - 1
    if last_i < 1:
        rate = video.get("r_frame_rate", "30/1")
        num, den = [float(x) for x in rate.split("/")]
        last_i = int(round(float(video.get("duration") or 0) * (num / den))) - 1
    first = _one(0)
    last = _one(max(last_i, 0))
    loop = float(np.mean(np.abs(first.astype(np.int16) - last.astype(np.int16))))
    return {
        "samples": count,
        "frozen": frozen,
        "hook_motion": round(hook, 4),
        "band_bright": band_bright,
        "loop_mean_abs": round(loop, 3),
    }


def _contact(path: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(path),
         "-vf",
         "fps=2,scale=180:320,"
         "drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf:"
         "text='%{pts\\:hms}':x=6:y=6:fontsize=14:fontcolor=yellow:box=1:boxcolor=black@0.55,"
         "tile=6x8:padding=4:color=black",
         "-frames:v", "1", str(dest)],
        check=True,
    )


def _qc_text(report: dict) -> str:
    v = report
    checks = []

    def add(name, ok, detail):
        checks.append(f"{'PASS' if ok else 'FAIL'}  {name:16}  {detail}")

    add("geometry", v["width"] == 1080 and v["height"] == 1920 and abs(v["fps"] - 30) < 0.01,
        f"{v['width']}x{v['height']} @ {v['fps']:.3f} fps, {v['frames']} frames, {v['video_s']:.2f}s")
    add("codec", v["codec"] == "h264" and v["pix_fmt"] == "yuv420p" and "bt709" in v["color"],
        f"{v['codec']} {v['pix_fmt']} {v['color']}")
    add("silent", v["audio_streams"] == 0, f"{v['audio_streams']} audio streams")
    add("hook_motion", v["hook_motion"] >= 0.03, f"mean abs diff/255 in 0–1 s = {v['hook_motion']:.4f} (bar 0.03)")
    add("loop", v["loop_mean_abs"] <= 1.0, f"last vs first mean abs {v['loop_mean_abs']:.2f}/255")
    add("frozen", not v["frozen"], f"{v['frozen'] or 'none over 0.5 s'}")
    add("caption_band", not v["band_bright"],
        f"y {BAND0}:{BAND1} bright pixels {v['band_bright'] or 'none'}")
    add("sat_hold", v["sat_hold_s"] >= 0.60, f"{v['sat_hold_s']:.2f}s from sat to spring-back")
    add("length", 16 <= v["video_s"] <= 20, f"{v['video_s']:.2f}s")
    fails = sum(1 for c in checks if c.startswith("FAIL"))
    lines = [
        f"RESULT {'PASS' if fails == 0 else 'FAIL'}  fails={fails}",
        f"silent 1080x1920  {v['video_s']:.2f}s  hook {v['hook_motion']:.4f}  loop {v['loop_mean_abs']:.2f}",
        "",
        *checks,
        "",
        "Weaknesses (honest):",
        "- Santa and the sitter are shaded ellipsoids. They read as a figure and a cabin, not a sculpt.",
        "- The ocean slide is a latitude flow on the real water mask, not a fluid simulation.",
        "- The last frame is an exact copy of frame 0, so the loop seam holds one frame.",
        "- No numerals are burned in. 'Forty-three kilometers' is the oblate shape plus the dashed limb; the bot speaks the number.",
        "- Word times follow the mapped v4 read. A new ElevenLabs take will need a nudge if its pace differs.",
        "",
    ]
    return "\n".join(lines)


def build(stills: list[float] | None = None) -> dict:
    words = _words()
    # Tail after "on." so the sit can hold and the ball can spring back to frame 0.
    duration = 18.4
    n = int(round(duration * FPS))
    duration = n / FPS
    m = marks_from(words, duration)
    sat_hold = m["hold_end"] - m["sat"]
    print(f"duration {duration:.3f}s  frames {n}  sat hold {sat_hold:.2f}s", flush=True)
    if sat_hold < 0.60:
        raise RuntimeError(f"sat hold {sat_hold:.2f}s")
    timeline = _timeline(words, m)
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "short15_timeline.json").write_text(json.dumps(timeline, indent=2))
    scene = Scene()

    if stills:
        from PIL import Image
        still_dir = ART / "build" / "stills"
        still_dir.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        for t in stills:
            frame, meta = render_frame(scene, words, [], m, t)
            Image.fromarray(frame).save(still_dir / f"t{t:05.2f}.jpg", quality=86)
            print(
                f"still {t:.2f}s mode={meta['mode']} globe {meta['globe_top']}–{meta['globe_bottom']} "
                f"band_max={meta['band_max']} ({time.time() - t0:.1f}s)",
                flush=True,
            )
        return {"stills": str(still_dir)}

    t0 = time.time()
    first = {"frame": None}

    def frames():
        for i in range(n):
            if i == n - 1 and first["frame"] is not None:
                yield first["frame"]
                continue
            frame, _meta = render_frame(scene, words, [], m, i / FPS)
            if i == 0:
                first["frame"] = frame.copy()
            yield frame

    out = ART / "short15_football_earth_v5.mp4"
    print("rendering silent picture", flush=True)
    _encode(frames(), n, out)
    print(f"encoded in {time.time() - t0:.1f}s", flush=True)

    contact = ART / "short15_contact.jpg"
    _contact(out, contact)
    probe = _probe(out)
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio_streams = sum(1 for s in probe["streams"] if s["codec_type"] == "audio")
    rate = v.get("r_frame_rate", "0/1")
    num, den = [float(x) for x in rate.split("/")]
    audit = _audit(out)
    report = {
        "width": int(v["width"]),
        "height": int(v["height"]),
        "fps": num / den if den else 0,
        "frames": int(v.get("nb_frames") or n),
        "codec": v.get("codec_name"),
        "pix_fmt": v.get("pix_fmt"),
        "color": f"{v.get('color_space')}/{v.get('color_primaries')}/{v.get('color_transfer')}",
        "video_s": float(v.get("duration") or duration),
        "audio_streams": audio_streams,
        "sat_hold_s": round(sat_hold, 3),
        **audit,
    }
    text = _qc_text(report)
    (ART / "qc.txt").write_text(text)
    (ART / "measurements.md").write_text(
        "# Football Earth v5\n\nSilent picture. Voice and karaoke are added downstream.\n\n"
        "```\n" + text + "```\n\n"
        f"Timeline: `artifacts/short15_timeline.json`\n\n"
        f"Caption plate: y {BAND0}–{BAND1} (0.64–0.72).\n"
    )
    print(text)
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stills", default="")
    args = p.parse_args(argv)
    stills = [float(x) for x in args.stills.split(",") if x.strip()] if args.stills else None
    build(stills)
    return 0


if __name__ == "__main__":
    sys.exit(main())
