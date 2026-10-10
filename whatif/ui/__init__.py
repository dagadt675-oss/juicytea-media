"""UI shared with the format A/C engine.

Counters, label pills, the reference-outline library, the loop helper, and
the words.json clock. Drawing uses ``engine.overlay`` (Noto Serif + Inter,
caption band y 0.64–0.78) instead of a second type stack.
"""

from ui.counter import draw_counter
from ui.loop import dissolve_to_frame
from ui.outlines import OUTLINES, outline
from ui.pills import draw_pill
from ui.words import voice_clock

__all__ = [
    "OUTLINES",
    "dissolve_to_frame",
    "draw_counter",
    "draw_pill",
    "outline",
    "voice_clock",
]
