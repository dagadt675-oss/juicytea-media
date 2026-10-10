"""Colour themes. Map fills stay off the white/yellow/cyan/orange text detector."""

from __future__ import annotations

# Text colours. Anything else drawn on the map must not look like these.
YELLOW = (255, 214, 10, 255)
WHITE = (244, 247, 251, 255)
SUB = (186, 198, 214, 255)

THEMES = {
    "midnight": {
        "bg0": (4, 7, 16),
        "bg1": (8, 16, 34),
        "ocean": (6, 26, 52),
        "ocean2": (12, 48, 86),
        "land": (32, 70, 66),
        "hi": (36, 112, 198),
        "hi2": (150, 78, 92),
        "rim": (64, 104, 142),
        "line": (26, 114, 108),
        "marker": (78, 138, 204),
    },
    "dusk": {
        "bg0": (12, 6, 22),
        "bg1": (22, 10, 32),
        "ocean": (18, 14, 48),
        "ocean2": (36, 24, 72),
        "land": (58, 48, 72),
        "hi": (92, 86, 186),
        "hi2": (168, 96, 86),
        "rim": (96, 78, 140),
        "line": (110, 78, 150),
        "marker": (130, 120, 210),
    },
    "emerald": {
        "bg0": (3, 10, 10),
        "bg1": (6, 22, 18),
        "ocean": (6, 32, 36),
        "ocean2": (10, 54, 52),
        "land": (28, 78, 58),
        "hi": (32, 140, 110),
        "hi2": (70, 110, 160),
        "rim": (40, 110, 100),
        "line": (36, 130, 100),
        "marker": (64, 168, 132),
    },
    # Hot, low-key grade for danger / scandal stories. Kept under the text mask.
    "ember": {
        "bg0": (14, 5, 5),
        "bg1": (28, 8, 6),
        "ocean": (24, 12, 14),
        "ocean2": (46, 18, 16),
        "land": (68, 42, 36),
        "hi": (168, 72, 54),
        "hi2": (120, 96, 64),
        "rim": (120, 64, 48),
        "line": (140, 70, 54),
        "marker": (176, 96, 72),
    },
    "noir": {
        "bg0": (2, 2, 4),
        "bg1": (8, 8, 12),
        "ocean": (8, 10, 16),
        "ocean2": (16, 20, 30),
        "land": (42, 44, 48),
        "hi": (186, 48, 58),
        "hi2": (70, 110, 150),
        "rim": (90, 40, 48),
        "line": (150, 46, 54),
        "marker": (200, 70, 78),
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
