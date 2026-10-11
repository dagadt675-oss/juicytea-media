#!/usr/bin/env python3
"""Segmented silent proof that every vfx_core feature gets a beat.

    python3 examples/vfx/render_vfx.py
"""

from __future__ import annotations

import json
import math
import multiprocessing
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
    adaptive_blur,
    apply_focus_mask,
    apply_glitch,
    apply_lens_dust,
    apply_light_spill,
    badge_state,
    barrel_distort,
    border_strands,
    bezier_ease_out,
    box_luminance,
    click_squash,
    cloud_alpha_for_span,
    draw_anamorphic,
    draw_svg,
    draw_atmosphere,
    draw_badge,
    draw_clouds,
    draw_ink_bleed,
    exp_zoom,
    glitch_active,
    displace_line,
    flash_envelope,
    focus_amount,
    glow_hillshade,
    grade,
    icon_parallax,
    icon_pop,
    label_style,
    lens_atmosphere,
    multiply_rgb,
    overlay_grain,
    overshoot,
    place_labels,
    shadow_offset,
    spring_approach,
    stress_glow,
    stroke_for_zoom,
    travel_blur_sigma,
    ease_in_out_cubic,
    ease_in_out_quintic,
)

W, H = 1080, 1920
HERE = Path(__file__).resolve().parent
SPEC = HERE / "vfx_test.yaml"

LASER = [(14.0, 66.0), (16.5, 64.5), (18.0, 63.2), (20.5, 62.4), (23.0, 61.2), (24.5, 59.8)]
SVG_ICON = Path("/workspace/asset_library/extra/kenney/crosshair-pack/Vector/Light/crosshair-037.svg")


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
    if name == "expo":
        from jt.show.vfx_core import ease_in_out_expo
        return ease_in_out_expo(u)
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
        words_path = spec.get("words")
        if words_path:
            path = Path(words_path)
            if not path.is_absolute():
                path = SPEC.parent / path
            self.words = json.loads(path.read_text(encoding="utf-8")).get("words") or []
        else:
            self.words = []

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
        duration = float(b["t"]) - float(a["t"])
        # Snaps integrate the spring. Long dives keep the eased exponential zoom.
        # Impact shake is not applied: a snap settles, it does not sway.
        if b.get("ease") == "spring" and 0.05 < duration <= 0.90:
            elapsed = max(0.0, t - float(a["t"]))
            lon = spring_approach(float(a["lon"]), float(b["lon"]), elapsed)
            lat = spring_approach(float(a["lat"]), float(b["lat"]), elapsed)
            span = math.exp(spring_approach(math.log(float(a["span"])), math.log(float(b["span"])), elapsed))
            return Cam(b["proj"], lon, lat, max(4.0, span))
        eased = _ease(b.get("ease", "quintic"), u)
        lon = float(a["lon"]) + (float(b["lon"]) - float(a["lon"])) * eased
        lat = float(a["lat"]) + (float(b["lat"]) - float(a["lat"])) * eased
        if b.get("exp", True):
            span = exp_zoom(float(a["span"]), float(b["span"]), eased)
        else:
            span = float(a["span"]) + (float(b["span"]) - float(a["span"])) * eased
        return Cam(b["proj"] if eased > 0.55 else a["proj"], lon, lat, max(4.0, span))

    def _segment(self, t: float) -> tuple[float, float, float]:
        """Linear time through the current zoom, plus the start and end spans."""
        keys = self.spec["camera"]
        if t <= float(keys[0]["t"]):
            span = float(keys[0]["span"])
            return 0.0, span, span
        if t >= float(keys[-1]["t"]):
            span = float(keys[-1]["span"])
            return 1.0, span, span
        a, b = keys[0], keys[1]
        for left, right in zip(keys, keys[1:]):
            if float(left["t"]) <= t <= float(right["t"]):
                a, b = left, right
                break
        span_t = float(b["t"]) - float(a["t"])
        u = 0.0 if span_t <= 1e-6 else (t - float(a["t"])) / span_t
        return u, float(a["span"]), float(b["span"])

    def _moving(self, t: float) -> bool:
        a = self.cam(max(0.0, t - 0.03))
        b = self.cam(t)
        return abs(math.log(a.span) - math.log(b.span)) > 0.035

    def render(self, t: float) -> np.ndarray:
        # Travel blur is applied to the map inside _draw. The composited frame
        # is not averaged, so captions and the focus country stay sharp.
        return self._draw(t)

    def _speed(self, t: float) -> float:
        a = self.cam(max(0.0, t - (1.0 / self.fps)))
        b = self.cam(t)
        dspan = abs(math.log(max(b.span, 1e-3)) - math.log(max(a.span, 1e-3))) * self.fps
        dpos = math.hypot(b.lon - a.lon, b.lat - a.lat) * self.fps
        return dspan * 3.0 + dpos * 0.12

    def _glow_level(self, t: float) -> float:
        level = 0.0
        for beat in self.spec["beats"]:
            if beat["type"] == "extrude" and t >= float(beat["t"]):
                level = max(level, 0.42)
            if beat["type"] == "stress":
                level = max(level, stress_glow(t, [(float(beat["t"]), float(beat.get("dur", 0.6)))]))
            if beat["type"] == "impact":
                dur = float(beat.get("dur", 0.25))
                age = t - float(beat["t"])
                if dur > 0 and 0.0 <= age <= dur:
                    level = max(level, math.sin(math.pi * age / dur))
        # Word timestamps own the flashes. A beat can still push a stress word higher.
        level = max(level, 0.85 * flash_envelope(t, self.words))
        return level

    def _glow_gain(self, t: float) -> float:
        gain = 0.55 if self.spec.get("spill", True) else 0.0
        for beat in self.spec["beats"]:
            if beat["type"] != "impact":
                continue
            dur = float(beat.get("dur", 0.25))
            age = t - float(beat["t"])
            if dur > 0 and 0.0 <= age <= dur:
                # A light pulse, not a camera shake.
                gain += 0.45 * math.sin(math.pi * age / dur)
        return gain

    def _spill(self, img: np.ndarray, cam: Cam, t: float) -> tuple[np.ndarray, np.ndarray]:
        protect = np.zeros(img.shape[:2], np.bool_)
        gain = self._glow_gain(t)
        if gain <= 0.02:
            return img, protect
        from scipy.ndimage import distance_transform_edt, zoom
        for beat in self.spec["beats"]:
            if beat["type"] != "extrude" or t < float(beat["t"]):
                continue
            iso = beat.get("iso", "SWE")
            color = tuple(beat.get("color") or (80, 180, 255))
            sw, sh = W // 2, H // 2
            surf = skia.Surface(sw, sh)
            canvas = surf.getCanvas()
            canvas.clear(skia.Color4f(0, 0, 0, 0))
            fill_iso(canvas, self.earth, cam, iso, (255, 255, 255), 255, w=sw, h=sh)
            alpha = surf.makeImageSnapshot().toarray()[:, :, 3] > 24
            if int(alpha.sum()) < 8:
                continue
            mask = np.repeat(np.repeat(alpha, 2, axis=0), 2, axis=1)[:H, :W]
            protect |= mask
            dist = distance_transform_edt(~alpha) * 2.0
            dist = zoom(dist, (H / sh, W / sw), order=1)[:H, :W]
            img = apply_light_spill(img, dist, color, radius=110.0, gain=gain)
        return img, protect

    def _draw(self, t: float) -> np.ndarray:
        t = min(self.duration, max(0.0, t))
        cam = self.cam(t)
        seg = self._segment(t)
        from jt.show.lod import load_local, load_regional, paint_lod
        if not hasattr(self, "_lod_plates"):
            globe = self.plates["satellite"]
            regional = load_regional()
            self._lod_plates = {"globe": globe, "regional": regional if regional is not None else globe, "local": load_local()}
        img = paint_lod(
            cam, W, H, self._lod_plates,
            time_u=seg[0], span_a=seg[1], span_b=seg[2],
        )
        paper = 0.0
        for beat in self.spec["beats"]:
            if beat["type"] == "multiply" and t >= float(beat["t"]):
                paper = max(paper, float(beat.get("amount", 0.25)))
        if paper:
            img = multiply_rgb(img, (214, 186, 140), paper)
        glow = self._glow_level(t)
        img = glow_hillshade(img, glow)
        img, protect = self._spill(img, cam, t)
        speed = self._speed(t)
        zoom = self.open_span / max(1e-3, cam.span)
        travel = _clamp(speed / 0.55)
        arrive = 1.0 - travel
        focus_pt = project_one(15.0, 62.5, view_for(cam, W, H)) if cam.proj else None
        fx, fy = (focus_pt if focus_pt is not None else (W * 0.5, H * 0.46))
        # Dark focus is a dramatic beat, not the default colourful plate.
        drama = focus_amount(t, self.spec["beats"])
        # Edge blur stays off. The owner rejected blurry frames.
        sigma = travel_blur_sigma(speed, zoom) if self.spec.get("dof", False) else 0.0
        img = lens_atmosphere(
            img, sigma, glow, protect if protect.any() else None,
            focus=drama, cx=fx, cy=fy, travel=travel, arrive=arrive,
        )
        rgba = np.dstack([img, np.full((H, W), 255, np.uint8)])
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(rgba), 0, 0)
        view = view_for(cam, W, H)
        zoom = self.open_span / cam.span
        if cam.proj == "ortho":
            strength = max(0.0, 1.0 - (3.0 - min(zoom, 3.0)) / 3.0)
            strength = max(0.0, 1.0 - _clamp((zoom - 1.2) / 1.6))
            draw_atmosphere(canvas, view.cx, view.cy, view.r, strength)
            draw_clouds(canvas, t, zoom, alpha=cloud_alpha_for_span(cam.span))
        self._country(canvas, cam, t, zoom)
        self._laser(canvas, cam, t, zoom)
        if glow >= 0.55:
            prev = self.cam(max(0.0, t - 0.05))
            drift = (cam.lon - prev.lon) * -18.0
            draw_anamorphic(canvas, fx, fy, glow, drift=drift, width=W)
        bgra = surface.makeImageSnapshot().toarray()
        map_rgb = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
        if self.spec.get("barrel", True):
            map_rgb = barrel_distort(map_rgb)
        map_rgb = apply_lens_dust(map_rgb, glow)
        for beat in self.spec["beats"]:
            if beat["type"] != "glitch":
                continue
            if glitch_active(t, float(beat["t"]), self.fps, int(beat.get("frames", 3))):
                map_rgb = apply_glitch(map_rgb, salt=int(beat["t"] * 10))
        plate = np.dstack([map_rgb, np.full((H, W), 255, np.uint8)])
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        canvas.drawImage(skia.Image.fromarray(plate), 0, 0)
        self._badges(canvas, t, map_rgb)
        self._svg(canvas, t, cam)
        bgra = surface.makeImageSnapshot().toarray()
        rgb = np.ascontiguousarray(bgra[:, :, [2, 1, 0]])
        if self.spec.get("grade", True):
            rgb = grade(rgb, t)
        if self.spec.get("grain", True):
            rgb = overlay_grain(rgb, t, self.fps)
        return rgb

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
            screen = displace_line(screen, t, amp=1.15)
            origins = int(beat.get("origins", 4))
            strands = border_strands(screen, origins=origins, progress=u)
            color = (80, 220, 255) if hot < 0.4 else (255, 220, 80)
            if beat.get("ink", True):
                draw_ink_bleed(canvas, strands, color, salt=int(beat["t"] * 10))
            else:
                from jt.show.vfx_core import draw_neon_path, trim_polyline
                shown = trim_polyline(screen, u)
                core = stroke_for_zoom(2.4 + 1.6 * hot, zoom)
                draw_neon_path(canvas, shown, color, core=core, dash=28)

    def _badges(self, canvas, t: float, background: np.ndarray) -> None:
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
                draw_badge(canvas, str(beat.get("text", "BADGE")), x, y, age, background=background)
            else:
                scale = overshoot(min(1.0, age / 0.45))
                if scale <= 0.02:
                    continue
                lum = box_luminance(background, x, y, 120, 120)
                ink_rgb, backing = label_style(lum)
                canvas.save()
                canvas.translate(x, y)
                canvas.scale(scale, scale)
                if backing:
                    shade = skia.Paint(AntiAlias=True)
                    shade.setColor(skia.ColorSetARGB(backing, 8, 10, 16))
                    shade.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
                    canvas.drawCircle(0, 0, 54, shade)
                paint = skia.Paint(AntiAlias=True)
                paint.setColor(skia.ColorSetARGB(255, 255, 214, 48))
                canvas.drawCircle(0, 0, 46, paint)
                try:
                    from jt.show.labels import faces
                    font = skia.Font(faces()["black"], 64)
                except Exception:
                    font = skia.Font(None, 64)
                ink = skia.Paint(AntiAlias=True)
                ink.setColor(skia.ColorSetARGB(255, ink_rgb[0], ink_rgb[1], ink_rgb[2]))
                text = str(beat.get("text", "!"))
                canvas.drawString(text, -font.measureText(text) / 2, 22, font, ink)
                canvas.restore()

    def _svg(self, canvas, t: float, cam: Cam) -> None:
        if not SVG_ICON.exists():
            return
        for beat in self.spec["beats"]:
            if beat["type"] != "svg" or t < float(beat["t"]):
                continue
            dur = float(beat.get("dur", 0.64))
            age = t - float(beat["t"])
            if age > dur:
                continue
            pop = icon_pop(age * self.fps, 18)
            u = 0.0 if dur <= 0 else age / dur
            x, y = bezier_ease_out(
                u, (220.0, 1500.0), (380.0, 980.0), (760.0, 760.0), (560.0, 620.0),
            )
            squash = click_squash(age - (dur - 0.18))
            px, py = icon_parallax((cam.lon - 18.0) * 80.0, (cam.lat - 62.0) * 80.0, 0.015)
            draw_svg(canvas, SVG_ICON, x + px, y + py, 160.0, scale=pop * squash)


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


def _encode_interleaved(spec_path: str, offset: int, step: int, n: int, raw_path: str) -> str:
    """Worker `offset` renders frames offset, offset+step, offset+2step, ..."""
    spec = load_spec(Path(spec_path))
    show = Proof(spec)
    frame_bytes = W * H * 3
    with open(raw_path, "wb") as handle:
        for i in range(offset, n, step):
            frame = show.render(i / show.fps)
            if frame.nbytes != frame_bytes:
                raise RuntimeError(f"frame {i} is {frame.shape}")
            handle.write(frame.tobytes())
            if i % 30 == 0:
                print(f"frame {i}/{n}", flush=True)
    return raw_path


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
    cues = cues_for(spec)
    worst, bad = lint_gaps(cues, spec["duration"], 2.0)
    if bad:
        raise SystemExit(f"cue gaps {bad}")
    (HERE / "vfx_cues.json").write_text(json.dumps({"cues": cues, "duration": spec["duration"]}, indent=2) + "\n")
    frames = int(round(spec["duration"] * spec["fps"]))
    workers = 3
    tmp = HERE / "_interleaved"
    tmp.mkdir(parents=True, exist_ok=True)
    jobs = [(str(SPEC), offset, workers, frames, str(tmp / f"part_{offset}.raw")) for offset in range(workers)]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        raws = [Path(p) for p in pool.starmap(_encode_interleaved, jobs)]
    dest = HERE / "vfx_proof.mp4"
    frame_bytes = W * H * 3
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(spec["fps"]), "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
        "-movflags", "+faststart", str(dest),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    handles = [path.open("rb") for path in raws]
    try:
        for i in range(frames):
            handle = handles[i % workers]
            chunk = handle.read(frame_bytes)
            if len(chunk) != frame_bytes:
                raise RuntimeError(f"short frame {i}")
            proc.stdin.write(chunk)
    finally:
        proc.stdin.close()
        for handle in handles:
            handle.close()
        code = proc.wait()
    for path in raws:
        path.unlink(missing_ok=True)
    if code != 0:
        raise SystemExit(f"ffmpeg failed {code}")
    from jt.show.qa import motion_per_second, report, write_report
    qa = report(dest, cues)
    write_report(HERE / "qa.json", qa)
    motion = motion_per_second(dest)
    write_report(HERE / "motion.json", motion)
    _contact(Proof(spec), HERE / "contact.jpg")
    summary = {
        "structural_motion_mean": qa.get("structural_motion_mean"),
        "structural_event_gap_max": qa.get("structural_event_gap_max"),
        "structural_pass": (
            float(qa.get("structural_motion_mean") or 0) >= 3.7
            and float(qa.get("structural_event_gap_max") or 99) <= 2.5
        ),
        "seconds_under_1": motion.get("seconds_under_1"),
        "cue_gap": worst,
        "clouds_wide": round(cloud_alpha_for_span(90), 2),
        "clouds_close": round(cloud_alpha_for_span(20), 2),
    }
    print(json.dumps(summary, indent=2))
    if not summary["structural_pass"]:
        raise SystemExit(
            f"structural QC failed: mean {summary['structural_motion_mean']} "
            f"gap {summary['structural_event_gap_max']}"
        )


if __name__ == "__main__":
    main()
