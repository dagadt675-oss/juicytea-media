#!/usr/bin/env python3
"""Segmented silent proof that every vfx_core feature gets a beat.

    python3 examples/vfx/render_vfx.py
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jt.data import build_earth  # noqa: E402
from jt.project import project_one  # noqa: E402
from jt.show.basemap import build_plates, paint_plate, view_for  # noqa: E402
from jt.show.camera import Cam  # noqa: E402
from jt.show.cues import lint_gaps, pack  # noqa: E402
from jt.show.polys import fill_iso  # noqa: E402
from jt.show.vfx_core import (  # noqa: E402
    BADGE_TEXT_S,
    accumulate,
    badge_state,
    cloud_alpha,
    draw_atmosphere,
    draw_badge,
    draw_clouds,
    draw_neon_path,
    exp_zoom,
    grade,
    impact_shake,
    multiply_rgb,
    overshoot,
    place_labels,
    shadow_offset,
    stress_glow,
    stroke_for_zoom,
    trim_polyline,
    ease_in_out_cubic,
    ease_in_out_quintic,
)

W, H = 1080, 1920
HERE = Path(__file__).resolve().parent
SPEC = HERE / "vfx_test.yaml"

LASER = [(14.0, 66.0), (16.5, 64.5), (18.0, 63.2), (20.5, 62.4), (23.0, 61.2), (24.5, 59.8)]


def load_spec(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["duration"] = float(raw["duration"])
    raw["fps"] = int(raw.get("fps") or 30)
    return raw


def _ease(name: str, u: float) -> float:
    u = 0.0 if u < 0 else 1.0 if u > 1 else u
    if name == "out":
        return 1.0 - (1.0 - u) ** 3
    if name == "cubic":
        return ease_in_out_cubic(u)
    return ease_in_out_quintic(u)


class Proof:
    def __init__(self, spec: dict):
        self.spec = spec
        self.duration = spec["duration"]
        self.fps = spec["fps"]
        self.frames = int(round(self.duration * self.fps))
        self.earth = build_earth()
        self.plates = build_plates(self.earth)
        self.open_span = float(spec["camera"][0]["span"])

    def cam(self, t: float) -> Cam:
        keys = self.spec["camera"]
        if t <= float(keys[0]["t"]):
            k = keys[0]
            return Cam(k["proj"], float(k["lon"]), float(k["lat"]), float(k["span"]))
        if t >= float(keys[-1]["t"]):
            k = keys[-1]
            return Cam(k["proj"], float(k["lon"]), float(k["lat"]), float(k["span"]))
        a, b = keys[0], keys[1]
        for left, right in zip(keys, keys[1:]):
            if float(left["t"]) <= t <= float(right["t"]):
                a, b = left, right
                break
        u = 0.0 if float(b["t"]) <= float(a["t"]) else (t - float(a["t"])) / (float(b["t"]) - float(a["t"]))
        eased = _ease(b.get("ease", "quintic"), u)
        lon = float(a["lon"]) + (float(b["lon"]) - float(a["lon"])) * eased
        lat = float(a["lat"]) + (float(b["lat"]) - float(a["lat"])) * eased
        if b.get("exp", True):
            span = exp_zoom(float(a["span"]), float(b["span"]), eased)
        else:
            span = float(a["span"]) + (float(b["span"]) - float(a["span"])) * eased
        cam = Cam(b["proj"] if eased > 0.55 else a["proj"], lon, lat, max(4.0, span))
        for beat in self.spec["beats"]:
            if beat["type"] != "impact":
                continue
            dx, dy = impact_shake(t, float(beat["t"]), float(beat.get("dur", 0.25)), float(beat.get("amp", 8)))
            if dx or dy:
                cam = Cam(cam.proj, cam.lon + dx * cam.span / W, cam.lat - dy * cam.span / H, cam.span)
        return cam

    def _moving(self, t: float) -> bool:
        a = self.cam(max(0.0, t - 0.03))
        b = self.cam(t)
        return abs(math.log(a.span) - math.log(b.span)) > 0.035

    def render(self, t: float) -> np.ndarray:
        # Sub-frame accumulation only while the camera is actually moving fast.
        if self._moving(t):
            return accumulate([self._draw(t + dt) for dt in (-1.0 / 90.0, 0.0, 1.0 / 90.0)])
        return self._draw(t)

    def _draw(self, t: float) -> np.ndarray:
        t = min(self.duration, max(0.0, t))
        cam = self.cam(t)
        img = paint_plate(self.plates["satellite"], cam, W, H)
        paper = 0.0
        for beat in self.spec["beats"]:
            if beat["type"] == "multiply" and t >= float(beat["t"]):
                paper = max(paper, float(beat.get("amount", 0.25)))
        if paper:
            img = multiply_rgb(img, (214, 186, 140), paper)
        rgba = np.dstack([img, np.full((H, W), 255, np.uint8)])
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        view = view_for(cam, W, H)
        zoom = self.open_span / cam.span
        if cam.proj == "ortho":
            strength = max(0.0, 1.0 - (3.0 - min(zoom, 3.0)) / 3.0)
            # Wider views (zoom near 1) keep the rim. Close views drop it.
            strength = max(0.0, 1.0 - _clamp((zoom - 1.2) / 1.6))
            draw_atmosphere(canvas, view.cx, view.cy, view.r, strength)
            draw_clouds(canvas, t, zoom)
        self._country(canvas, cam, t, zoom)
        self._laser(canvas, cam, t, zoom)
        self._badges(canvas, t)
        if self.spec.get("grade", True):
            bgra = surface.makeImageSnapshot().toarray()
            rgb = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
            return grade(rgb, t)
        bgra = surface.makeImageSnapshot().toarray()
        return np.ascontiguousarray(bgra[:, :, [2, 1, 0]])

    def _country(self, canvas, cam: Cam, t: float, zoom: float) -> None:
        view = view_for(cam, W, H)
        shadow_on = any(b["type"] == "shadow" and t >= float(b["t"]) for b in self.spec["beats"])
        for beat in self.spec["beats"]:
            if beat["type"] != "extrude" or t < float(beat["t"]):
                continue
            iso = beat.get("iso", "SWE")
            rgb = tuple(beat.get("color") or (0, 90, 160))
            pop = overshoot(min(1.0, (t - float(beat["t"])) / 0.55))
            anchor_ll = (15.0, 62.5) if iso == "SWE" else (26.0, 64.0)
            anchor = project_one(*anchor_ll, view)
            if anchor is not None and shadow_on:
                dx, dy = shadow_offset(anchor[0], anchor[1], zoom=zoom)
                fill_iso(
                    canvas, self.earth, cam, iso, (8, 16, 28), int(110 * min(1.0, pop)),
                    dlon=dx * cam.span / W, dlat=-dy * cam.span / H, w=W, h=H,
                )
            fill_iso(
                canvas, self.earth, cam, iso, rgb, int(200 * min(1.0, pop)),
                stroke=(255, 255, 255), stroke_w=stroke_for_zoom(4.5, zoom), w=W, h=H,
            )

    def _laser(self, canvas, cam: Cam, t: float, zoom: float) -> None:
        view = view_for(cam, W, H)
        hot = stress_glow(t, [(float(b["t"]), float(b.get("dur", 0.6))) for b in self.spec["beats"] if b["type"] == "stress"])
        for beat in self.spec["beats"]:
            if beat["type"] != "laser" or t < float(beat["t"]):
                continue
            dur = float(beat.get("dur", 1.2))
            u = min(1.0, (t - float(beat["t"])) / dur)
            # About 15 frames at 30 fps is half a second. The spec dur stretches that.
            screen = []
            for lon, lat in LASER:
                p = project_one(lon, lat, view)
                if p is not None:
                    screen.append(p)
            shown = trim_polyline(screen, u)
            core = stroke_for_zoom(2.4 + 1.6 * hot, zoom)
            draw_neon_path(canvas, shown, (80, 220, 255) if hot < 0.4 else (255, 220, 80), core=core, dash=28)

    def _badges(self, canvas, t: float) -> None:
        pending = []
        for beat in self.spec["beats"]:
            if beat["type"] not in ("badge", "overshoot") or t < float(beat["t"]):
                continue
            pending.append(beat)
        boxes = []
        for beat in pending:
            if beat["type"] == "badge":
                boxes.append((float(beat.get("x", 540)), float(beat.get("y", 400)), 360, 88))
            else:
                boxes.append((float(beat.get("x", 540)), float(beat.get("y", 640)), 120, 120))
        placed = place_labels(boxes)
        for beat, (x, y) in zip(pending, placed):
            age = t - float(beat["t"])
            if beat["type"] == "badge":
                draw_badge(canvas, str(beat.get("text", "BADGE")), x, y, age)
            else:
                scale = overshoot(min(1.0, age / 0.45))
                if scale <= 0.02:
                    continue
                canvas.save()
                canvas.translate(x, y)
                canvas.scale(scale, scale)
                paint = skia.Paint(AntiAlias=True)
                paint.setColor(skia.ColorSetARGB(255, 255, 214, 48))
                canvas.drawCircle(0, 0, 46, paint)
                try:
                    from jt.show.labels import faces
                    font = skia.Font(faces()["black"], 64)
                except Exception:
                    font = skia.Font(None, 64)
                ink = skia.Paint(AntiAlias=True)
                ink.setColor(skia.ColorSetARGB(255, 16, 16, 20))
                text = str(beat.get("text", "!"))
                canvas.drawString(text, -font.measureText(text) / 2, 22, font, ink)
                canvas.restore()


def cues_for(spec: dict) -> list[dict]:
    rows = []
    for beat in spec["beats"]:
        kind = {"laser": "draw", "badge": "pop", "overshoot": "pop", "impact": "impact", "extrude": "pop"}.get(beat["type"], "tick")
        rows.append((float(beat["t"]), kind, beat.get("name") or beat["type"]))
    return pack(rows)


def _encode(show: Proof, i0: int, i1: int, path: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(show.fps), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
        "-movflags", "+faststart", str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(i0, i1):
            proc.stdin.write(show.render(i / show.fps).tobytes())
            if i % 30 == 0:
                print(f"frame {i}/{show.frames}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")


def _concat(parts: list[Path], dest: Path) -> None:
    listing = HERE / "_concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)],
        check=True,
    )
    listing.unlink(missing_ok=True)


def _contact(show: Proof, path: Path) -> None:
    cols, thumb_w, thumb_h = 6, 180, 320
    times = [i * show.duration / 11 for i in range(12)]
    sheet = Image.new("RGB", (cols * thumb_w, 2 * thumb_h), (8, 10, 16))
    for i, t in enumerate(times):
        thumb = Image.fromarray(show.render(t)).resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        sheet.paste(thumb, ((i % cols) * thumb_w, (i // cols) * thumb_h))
    sheet.save(path, quality=86)


def _clamp(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def main() -> None:
    spec = load_spec(SPEC)
    assert badge_state(0.0) == (0.0, False)
    assert badge_state(BADGE_OPEN_S := 5 / 30)[0] == 1.0 or badge_state(5 / 30)[1] is False
    assert badge_state(0.0) == (0.0, False)
    assert badge_state(5.0 / 30.0)[1] is False
    assert badge_state(6.0 / 30.0)[1] is True
    show = Proof(spec)
    cues = cues_for(spec)
    worst, bad = lint_gaps(cues, spec["duration"], 2.0)
    if bad:
        raise SystemExit(f"cue gaps {bad}")
    (HERE / "vfx_cues.json").write_text(json.dumps({"cues": cues, "duration": spec["duration"]}, indent=2) + "\n")
    ranges = [(0, 180), (180, 360), (360, show.frames)]
    parts = []
    for i0, i1 in ranges:
        part = HERE / f"_part_{i0}_{i1}.mp4"
        _encode(show, i0, i1, part)
        parts.append(part)
    dest = HERE / "vfx_proof.mp4"
    _concat(parts, dest)
    for part in parts:
        part.unlink(missing_ok=True)
    from jt.show.qa import motion_per_second, report, write_report
    qa = report(dest, cues)
    write_report(HERE / "qa.json", qa)
    motion = motion_per_second(dest)
    write_report(HERE / "motion.json", motion)
    _contact(show, HERE / "contact.jpg")
    print(json.dumps({
        "structural_motion_mean": qa.get("structural_motion_mean"),
        "structural_event_gap_max": qa.get("structural_event_gap_max"),
        "structural_pass": qa.get("structural_pass"),
        "seconds_under_1": motion.get("seconds_under_1"),
        "cue_gap": worst,
        "clouds_wide": round(cloud_alpha(1.0), 2),
        "clouds_close": round(cloud_alpha(4.0), 2),
    }, indent=2))


if __name__ == "__main__":
    main()
