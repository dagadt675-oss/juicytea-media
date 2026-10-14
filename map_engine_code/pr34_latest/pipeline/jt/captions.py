"""
Juicy Tea Map-Shorts Engine — Skia Cyan (#00E5FF) Karaoke & Stroked Caption Renderer.
Enforces Rule 9 & Section 6.4:
- Bold white sans-serif with dark stroke, glyph >= 64px, in 64-72% height band.
- Active word switches 0.04s early to Cyan #00E5FF whenever yellow exists on map.
- Safe zones: top 12% (y<230), bottom 20% (y>1536), and x>900 remain empty.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

try:
    import skia
except ImportError:
    skia = None

KARAOKE_ACTIVE_CYAN: Tuple[int, int, int, int] = (0, 229, 255, 255)   # #00E5FF
KARAOKE_INACTIVE_WHITE: Tuple[int, int, int, int] = (255, 255, 255, 255)
STROKE_DARK: Tuple[int, int, int, int] = (14, 18, 26, 245)


@dataclass(frozen=True)
class KaraokeWord:
    text: str
    start: float
    end: float


def active_karaoke_style(
    words: List[KaraokeWord],
    t: float,
    map_has_yellow: bool = True,
    lead_s: float = 0.04,
) -> List[Tuple[str, Tuple[int, int, int, int]]]:
    """Switches active word highlight 0.04s early to Cyan #00E5FF."""
    t_shifted = t + lead_s
    active_color = KARAOKE_ACTIVE_CYAN if map_has_yellow else (255, 214, 10, 255)
    return [
        (w.text, active_color if (w.start <= t_shifted <= w.end) else KARAOKE_INACTIVE_WHITE)
        for w in words
    ]


def draw_skia_karaoke_caption(
    canvas: "skia.Canvas",
    active_line_words: List[KaraokeWord],
    t: float,
    map_has_yellow: bool = True,
) -> None:
    """Renders >= 64px bold stroked captions in the 64-72% height band (y = 1228..1382)."""
    if skia is None or not active_line_words:
        return

    styled = active_karaoke_style(active_line_words, t, map_has_yellow=map_has_yellow)
    font_size = 68.0
    typeface = skia.Typeface.MakeFromName("Inter", skia.FontStyle.Bold())
    font = skia.Font(typeface, font_size)

    space_w = font.measureText(" ")
    word_widths = [font.measureText(w_text) for w_text, _ in styled]
    total_w = sum(word_widths) + space_w * max(0, len(styled) - 1)

    safe_center_x = 480.0
    start_x = max(80.0, min(safe_center_x - 0.5 * total_w, 880.0 - total_w))
    baseline_y = 1310.0

    stroke_paint = skia.Paint(
        AntiAlias=True,
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=11.0,
        StrokeJoin=skia.Paint.kRound_Join,
        Color=skia.Color(*STROKE_DARK),
    )

    cursor_x = start_x
    for (w_text, rgba), ww in zip(styled, word_widths):
        fill_paint = skia.Paint(
            AntiAlias=True,
            Style=skia.Paint.kFill_Style,
            Color=skia.Color(*rgba),
        )
        canvas.drawSimpleText(w_text, cursor_x, baseline_y, font, stroke_paint)
        canvas.drawSimpleText(w_text, cursor_x, baseline_y, font, fill_paint)
        cursor_x += ww + space_w
