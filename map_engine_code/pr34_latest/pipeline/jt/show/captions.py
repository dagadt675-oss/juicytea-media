"""
Juicy Tea Map-Shorts Engine — Cyan (#00E5FF) karaoke captions.

Bold white sans-serif, at least 64px, dark stroke, in the 64–72% band.
The active word switches 0.04s early. Phrases cover the whole word list,
not a tail slice of the timeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

try:
    import skia
except ImportError:
    skia = None

KARAOKE_ACTIVE_CYAN: Tuple[int, int, int, int] = (0, 229, 255, 255)
KARAOKE_INACTIVE_WHITE: Tuple[int, int, int, int] = (255, 255, 255, 255)
STROKE_DARK: Tuple[int, int, int, int] = (14, 18, 26, 245)


@dataclass(frozen=True)
class KaraokeWord:
    text: str
    start: float
    end: float


def load_karaoke_words(words_json_data: List[Dict]) -> List[KaraokeWord]:
    """Parse words.json. Accepts either `word` or `text`."""
    out: List[KaraokeWord] = []
    for item in words_json_data:
        text = str(item.get("word") or item.get("text") or "").strip().upper()
        if not text:
            continue
        out.append(KaraokeWord(text=text, start=float(item["start"]), end=float(item["end"])))
    return out


def get_active_phrase_words(
    all_words: List[KaraokeWord],
    t: float,
    max_words_per_line: int = 4,
) -> List[KaraokeWord]:
    """3–4 word phrase that is on screen at time t."""
    if not all_words:
        return []
    phrases: List[List[KaraokeWord]] = []
    current: List[KaraokeWord] = []
    for word in all_words:
        if current and (len(current) >= max_words_per_line or (word.start - current[-1].end) > 0.45):
            phrases.append(current)
            current = []
        current.append(word)
    if current:
        phrases.append(current)
    for phrase in phrases:
        if (phrase[0].start - 0.12) <= t <= (phrase[-1].end + 0.18):
            return phrase
    return []


def active_karaoke_style(
    words: List[KaraokeWord],
    t: float,
    map_has_yellow: bool = True,
    lead_s: float = 0.04,
) -> List[Tuple[str, Tuple[int, int, int, int]]]:
    t_shifted = t + lead_s
    active_color = KARAOKE_ACTIVE_CYAN if map_has_yellow else (255, 214, 10, 255)
    return [
        (word.text, active_color if word.start <= t_shifted <= word.end else KARAOKE_INACTIVE_WHITE)
        for word in words
    ]


def draw_skia_karaoke_caption(
    canvas,
    all_or_line_words: List[KaraokeWord],
    t: float,
    map_has_yellow: bool = True,
) -> None:
    if skia is None or not all_or_line_words:
        return
    line_words = (
        get_active_phrase_words(all_or_line_words, t)
        if len(all_or_line_words) > 5
        else all_or_line_words
    )
    if not line_words:
        return
    styled = active_karaoke_style(line_words, t, map_has_yellow=map_has_yellow)
    font_size = 66.0
    typeface = skia.Typeface.MakeFromName("Inter", skia.FontStyle.Bold())
    font = skia.Font(typeface, font_size)
    space_w = font.measureText(" ")
    word_widths = [font.measureText(text) for text, _ in styled]
    total_w = sum(word_widths) + space_w * max(0, len(styled) - 1)
    if total_w > 800.0:
        font_size = max(64.0, font_size * (800.0 / total_w))
        font = skia.Font(typeface, font_size)
        space_w = font.measureText(" ")
        word_widths = [font.measureText(text) for text, _ in styled]
        total_w = sum(word_widths) + space_w * max(0, len(styled) - 1)
    start_x = max(75.0, min(480.0 - 0.5 * total_w, 885.0 - total_w))
    baseline_y = 1315.0
    stroke_paint = skia.Paint(
        AntiAlias=True,
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=12.0,
        StrokeJoin=skia.Paint.kRound_Join,
        Color=skia.Color(*STROKE_DARK),
    )
    cursor_x = start_x
    for (text, rgba), width in zip(styled, word_widths):
        fill_paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style, Color=skia.Color(*rgba))
        canvas.drawSimpleText(text, cursor_x, baseline_y, font, stroke_paint)
        canvas.drawSimpleText(text, cursor_x, baseline_y, font, fill_paint)
        cursor_x += width + space_w
