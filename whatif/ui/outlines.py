"""Reference outlines shared by format B episodes.

Heights are the real objects. Meshes are generic massing: no logos, no
copied likenesses. Blender builders ask this table for the dimensions.
"""

from __future__ import annotations

# US customary is what the counter shows. Metres are the scene unit.
FT = 0.3048

OUTLINES: dict[str, dict] = {
    "person": {
        "label": "A PERSON",
        "sub": "5 ft 9 in",
        "height_m": 69.0 * 0.0254,  # 5'9"
        "kind": "person",
        "source": "Round adult outline at 5 ft 9 in. CDC NCHS adult means differ for men and women.",
    },
    "liberty": {
        "label": "STATUE OF LIBERTY",
        "sub": "305 ft",
        "height_m": 93.0,
        "kind": "monument",
        "source": "Ground to torch, about 305 ft (93 m), pedestal included. National Park Service.",
    },
    "empire": {
        "label": "EMPIRE STATE",
        "sub": "1,454 ft",
        "height_m": 443.2,
        "deck_m": 1250 * FT,  # 102nd-floor observatory / roof, the penny's ledge
        "roof_m": 1250 * FT,
        "kind": "tower",
        "source": "Roof and 102nd-floor observatory 1,250 ft. Tip 1,454 ft. Empire State Building facts and figures.",
    },
    "burj": {
        "label": "BURJ KHALIFA",
        "sub": "2,717 ft",
        "height_m": 828.0,
        "kind": "spire",
        "source": "828 m / 2,717 ft architectural height. CTBUH.",
    },
    "stadium": {
        "label": "A STADIUM",
        "sub": "230 m bowl",
        "length_m": 230.0,
        "width_m": 190.0,
        "height_m": 48.0,
        "kind": "bowl",
        "source": "Generic bowl around a 105 × 68 m pitch. Envelope is approximate, not one club's building.",
    },
    "titanic": {
        "label": "TITANIC",
        "sub": "882 ft",
        "length_m": 269.1,
        "beam_m": 28.2,
        "height_m": 53.0,
        "kind": "ship",
        "source": "Length 882 ft 9 in (269.1 m), beam 92 ft (28.2 m). Height is keel to the boat deck, approximate.",
    },
}


def outline(name: str) -> dict:
    if name not in OUTLINES:
        raise KeyError(name)
    return OUTLINES[name]
