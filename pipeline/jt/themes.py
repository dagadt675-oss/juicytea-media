"""Colour themes. Map fills stay off the white/yellow/cyan/orange text detector."""

from __future__ import annotations

# Text colours. Anything else drawn on the map must not look like these.
YELLOW = (255, 214, 10, 255)
WHITE = (244, 247, 251, 255)
SUB = (186, 198, 214, 255)
# Title accent. Matches the flat-map Shorts: the stressed word is neon red.
NEON = (228, 32, 72, 255)

# Default is the flat political map: navy field, muted land, one neon country.
# No relief. "flat" tells the renderer to skip shade, lighting and the globe limb.
THEMES = {
    "midnight": {
        "flat": True,
        "bg0": (7, 16, 42),
        "bg1": (7, 16, 42),
        "ocean": (7, 16, 42),
        "ocean2": (7, 16, 42),
        "land": (46, 70, 114),
        "hi": (228, 32, 72),
        "hi2": (186, 36, 96),
        "rim": (228, 32, 72),
        "line": (228, 32, 72),
        "marker": (228, 32, 72),
        "coast": (6, 12, 32),
        "paper": (248, 248, 252),
        "ink": (196, 22, 58),
    },
    "dusk": {
        "flat": True,
        "bg0": (16, 8, 28),
        "bg1": (16, 8, 28),
        "ocean": (16, 8, 28),
        "ocean2": (16, 8, 28),
        "land": (58, 42, 84),
        "hi": (228, 32, 72),
        "hi2": (168, 96, 86),
        "rim": (228, 32, 72),
        "line": (228, 32, 72),
        "marker": (228, 32, 72),
        "coast": (10, 6, 18),
        "paper": (248, 248, 252),
        "ink": (196, 22, 58),
    },
    "emerald": {
        "flat": True,
        "bg0": (6, 18, 22),
        "bg1": (6, 18, 22),
        "ocean": (6, 18, 22),
        "ocean2": (6, 18, 22),
        "land": (28, 72, 68),
        "hi": (228, 32, 72),
        "hi2": (32, 140, 110),
        "rim": (228, 32, 72),
        "line": (228, 32, 72),
        "marker": (228, 32, 72),
        "coast": (4, 12, 14),
        "paper": (248, 248, 252),
        "ink": (196, 22, 58),
    },
    # Hot, low-key grade for danger / scandal stories. Kept under the text mask.
    # Optional grades. Still flat fills — the distance-field "relief" is not used.
    "ember": {
        "flat": True,
        "bg0": (22, 8, 8),
        "bg1": (22, 8, 8),
        "ocean": (22, 8, 8),
        "ocean2": (22, 8, 8),
        "land": (72, 40, 36),
        "hi": (228, 48, 42),
        "hi2": (120, 96, 64),
        "rim": (228, 48, 42),
        "line": (228, 48, 42),
        "marker": (228, 48, 42),
        "coast": (12, 4, 4),
        "paper": (248, 248, 252),
        "ink": (176, 28, 24),
    },
    "noir": {
        "flat": True,
        "bg0": (8, 8, 12),
        "bg1": (8, 8, 12),
        "ocean": (8, 8, 12),
        "ocean2": (8, 8, 12),
        "land": (42, 44, 52),
        "hi": (228, 32, 72),
        "hi2": (70, 110, 150),
        "rim": (228, 32, 72),
        "line": (228, 32, 72),
        "marker": (228, 32, 72),
        "coast": (4, 4, 8),
        "paper": (248, 248, 252),
        "ink": (196, 22, 58),
    },
}


def get_theme(name: str) -> dict:
    if name not in THEMES:
        raise KeyError(f"unknown theme {name!r}; choose from {', '.join(THEMES)}")
    return THEMES[name]


def parse_hex(value: str) -> tuple[int, int, int]:
    s = value.strip().lstrip("#")
    if len(s) != 6:
        raise ValueError(f"bad colour {value!r}")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
