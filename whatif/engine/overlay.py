"""Crisp UI overlay: the title and the time counter.

Drawn in screen space after the 3D render so type stays sharp. Episode 1
shows those two only. Nothing is placed in the caption band (y 0.64–0.78),
and the center ticker is not drawn.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from engine.spec import beat_at, channels_at

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "fonts"
SERIF = FONT_DIR / "NotoSerifDisplay-Regular.ttf"
SERIF_BOLD = FONT_DIR / "NotoSerifDisplay-Bold.ttf"
SANS = FONT_DIR / "Inter-Medium.ttf"
SANS_SEMI = FONT_DIR / "Inter-SemiBold.ttf"


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def _shadow_text(base: Image.Image, xy, text, font, fill=(255, 255, 255, 255), anchor="lt", radius=8, opacity=150):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.text(xy, text, font=font, fill=(0, 0, 0, opacity), anchor=anchor)
    blurred = layer.filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(blurred)
    draw2 = ImageDraw.Draw(base)
    draw2.text(xy, text, font=font, fill=fill, anchor=anchor)


def _fade(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def format_int(value: int) -> str:
    return f"{max(0, int(value)):,}"


def ui_state(resolved: dict, frame: int) -> dict:
    beat = beat_at(resolved, frame)
    fps = resolved["fps"]
    local = (frame - beat["start_frame"]) / fps
    beat_len = max(0.05, beat["end"] - beat["start"])
    title_alpha = 0.0
    if beat.get("title"):
        # Hold, then leave before the caption-free city shot continues.
        fade_at = beat_len - 0.45
        if local < fade_at:
            title_alpha = 1.0
        else:
            title_alpha = 1.0 - _fade((local - fade_at) / 0.45)
    # The closing beat snaps the title back on so the loop matches frame 1.
    if beat["index"] == len(resolved["beats"]) - 1 and beat.get("title"):
        title_alpha = 1.0

    shown = set((resolved.get("ui") or {}).get("text") or ["title", "counter"])
    ticker_alpha = 0.0
    ticker = beat.get("ticker") if "ticker" in shown else ""
    if ticker and beat["index"] != 0:
        # 0.18 in, 0.85 hold, 0.28 out.
        if local < 0.18:
            ticker_alpha = _fade(local / 0.18)
        elif local < 1.03:
            ticker_alpha = 1.0
        elif local < 1.31:
            ticker_alpha = 1.0 - _fade((local - 1.03) / 0.28)
    counter = beat.get("counter") or {}
    mode = counter.get("mode", "time")
    ch = channels_at(resolved, frame)
    labels = {
        "population": "WORLD POPULATION",
        "time": "TIME WITHOUT HUMANS",
        "sealevel": "SEA LEVEL",
        "temperature": "TEMPERATURE",
    }
    if mode == "population":
        pop = int(resolved["population"])
        # Reach zero at 3.0 s, inside the opening sentence.
        u = min(1.0, max(0.0, ((frame - 1) / fps) / 3.0))
        # Slight ease-in so the last digits rush.
        u = u * u * (3 - 2 * u)
        value = int(round(pop * (1.0 - u)))
        label = counter.get("label") or labels["population"]
        number = format_int(value)
        unit = None
    else:
        label = counter.get("label") or labels.get(mode, "TIME WITHOUT HUMANS")
        raw = beat.get("time_label") or ""
        parts = raw.split()
        if len(parts) >= 2:
            number = parts[0]
            unit = " ".join(parts[1:])
        else:
            number = raw
            unit = None
    hud = None
    if resolved.get("format") == "C":
        failure = float(ch.get("critical", 0.0))
        status = "CRITICAL" if failure >= 0.7 or ch.get("wave", 0) > 0.55 else "NOMINAL" if ch.get("inertia", 0) < 0.08 else "FAULT"
        g = 9.81 * (1.0 - float(ch.get("gravity_off", 0.0)))
        speed = max(float(ch.get("inertia", 0.0)), float(ch.get("scatter", 0.0))) * 1040.0
        elapsed = max(0.0, ((frame - 1) / fps) - beat["start"])
        time_left = max(0.0, (beat["end"] - beat["start"]) - elapsed)
        hud = {
            "status": status,
            "failure": failure,
            "gravity": g,
            "speed": speed,
            "weight": 180.0 * (g / 9.81),
            "time_left": time_left,
            "countdown": beat.get("time_label") or "",
            "critical": status == "CRITICAL",
        }
    return {
        "title": resolved["title"] if title_alpha > 0.01 else "",
        "title_alpha": title_alpha,
        "label": label,
        "number": number,
        "unit": unit,
        "ticker": ticker if ticker_alpha > 0.01 else "",
        "ticker_alpha": ticker_alpha,
        "channels": ch,
        "hud": hud,
    }


def _alpha(color, a: float):
    return (color[0], color[1], color[2], int(max(0, min(255, a))))


def draw_state(image: Image.Image, state: dict, width: int, height: int) -> Image.Image:
    img = image.convert("RGBA")
    title_size = max(36, int(width * 0.042))
    title_font = _font(SERIF, title_size)
    label_font = _font(SANS, max(16, int(width * 0.020)))
    number_font = _font(SERIF, max(42, int(width * 0.052)))
    unit_font = _font(SANS_SEMI, max(18, int(width * 0.024)))
    tick_num = _font(SERIF, max(64, int(width * 0.090)))
    tick_unit = _font(SANS, max(22, int(width * 0.028)))

    if state["title_alpha"] > 0.01:
        a = state["title_alpha"]
        # Two centered lines in the sky, well above the caption band.
        lines = _wrap_title(state["title"])
        # Large, in the open sky left of the portal. The portal's left leg
        # is near x=0.49, so the block is centered in the sky pocket, not
        # on the frame center and not jammed into the corner.
        cx = int(width * 0.24)
        y = int(height * 0.068)
        gap = int(title_size * 1.08)
        block_h = gap * max(0, len(lines) - 1)
        y -= block_h // 2
        _title_scrim(img, cx, y + block_h / 2.0, width * 0.23, gap * max(len(lines), 1) * 0.85, a)
        for line in lines:
            _shadow_text(
                img,
                (cx, y),
                line,
                title_font,
                fill=_alpha((255, 255, 255), 255 * a),
                anchor="mm",
                radius=14,
                opacity=int(170 * a),
            )
            y += gap

    if state.get("hud"):
        _draw_hud(img, state["hud"], width, height)
    else:
        # Left counter. Sits on the open water/park edge, above y=0.64.
        x = int(width * 0.05)
        y = int(height * 0.50)
        _shadow_text(img, (x, y), state["label"], label_font, fill=_alpha((255, 255, 255), 230), anchor="lt", radius=4, opacity=120)
        num_y = y + int(height * 0.022)
        _shadow_text(img, (x, num_y), state["number"], number_font, fill=_alpha((255, 255, 255), 255), anchor="lt", radius=6, opacity=140)
        if state.get("unit"):
            probe = ImageDraw.Draw(img)
            bbox = probe.textbbox((x, num_y), state["number"], font=number_font, anchor="lt")
            unit_x = bbox[2] + int(width * 0.012)
            unit_y = bbox[3] - int(height * 0.012)
            _shadow_text(img, (unit_x, unit_y), state["unit"], unit_font, fill=_alpha((255, 255, 255), 235), anchor="ls", radius=4, opacity=120)

    return img


def _draw_hud(img, hud, width, height):
    """Format C status panel. Format A never calls this."""
    label = _font(SANS, max(15, int(width * 0.018)))
    value = _font(SANS_SEMI, max(18, int(width * 0.026)))
    big = _font(SERIF, max(120, int(width * 0.22)))
    x = int(width * 0.06)
    y = int(height * 0.20)
    status = hud["status"]
    color = (220, 48, 42, 255) if hud["critical"] else (255, 255, 255, 230)
    _shadow_text(img, (x, y), "STATUS  " + status, value, fill=color, anchor="lt", radius=4, opacity=100)
    rows = (
        ("GRAVITY", f"{hud['gravity']:.1f} m/s2"),
        ("SPEED", f"{hud['speed']:.0f} mph"),
        ("WEIGHT", f"{hud['weight']:.0f} lb"),
        ("TIME LEFT", f"{hud['time_left']:.1f}s"),
        ("FAILURE", f"{hud['failure'] * 100:.0f}%"),
    )
    yy = y + int(height * 0.045)
    value_x = int(width * 0.30)
    for name, val in rows:
        _shadow_text(img, (x, yy), name, label, fill=(255, 255, 255, 190), anchor="lt", radius=3, opacity=80)
        _shadow_text(img, (value_x, yy), val, value, fill=color, anchor="lt", radius=3, opacity=80)
        yy += int(height * 0.038)
    if hud["countdown"]:
        _shadow_text(
            img,
            (width * 0.78, height * 0.42),
            hud["countdown"],
            big,
            fill=(255, 255, 255, 70),
            anchor="mm",
            radius=8,
            opacity=40,
        )


def _title_scrim(img: Image.Image, cx: float, cy: float, rx: float, ry: float, alpha: float) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse(
        (cx - rx, cy - ry, cx + rx, cy + ry),
        fill=(6, 10, 18, int(150 * alpha)),
    )
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius=max(18, int(img.size[0] * 0.028)))))


def _wrap_title(title: str) -> list[str]:
    # The reference breaks after "humans".
    lowered = title.lower()
    if lowered.startswith("what if all humans disappeared"):
        return ["What if all humans", "disappeared?"]
    if "every human vanished" in lowered:
        return ["What if every human", "vanished… right now?"]
    words = title.split()
    if len(words) <= 4:
        return [title]
    mid = len(words) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


def composite_directory(resolved: dict, frame_dir: Path, out_dir: Path, frames=None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    width = resolved["width"]
    height = resolved["height"]
    if frames is None:
        frames = range(1, resolved["frame_count"] + 1)
    for frame in frames:
        src = frame_dir / f"f_{frame:04d}.png"
        if not src.exists():
            continue
        state = ui_state(resolved, frame)
        image = Image.open(src)
        # Plates may be rendered at a reduced scale. UI is drawn at plate size
        # so type matches the picture; the encoder scales to delivery size.
        drawn = draw_state(image, state, image.size[0], image.size[1])
        drawn.convert("RGB").save(out_dir / f"f_{frame:04d}.png", quality=95)


def composite_file(resolved: dict, src: Path, dest: Path, frame: int) -> None:
    image = Image.open(src)
    state = ui_state(resolved, frame)
    drawn = draw_state(image, state, image.size[0], image.size[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    drawn.convert("RGB").save(dest)
