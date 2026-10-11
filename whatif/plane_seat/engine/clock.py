"""Voice clock for the plane-seat Short.

Frame 1 is t=0. 984 frames fill 32.81 s after the 30 fps master is
retimed (984/30 * 32.81/32.8 = 32.81). Word onsets come from words.json.
"""

from __future__ import annotations

import json
from pathlib import Path

FPS = 30
DURATION = 32.81
FRAME_COUNT = 984
WIDTH = 1080
HEIGHT = 1920
# 984 frames at 30/1 is 32.80 s. Stretch the track so the container is 32.81 s.
ITSSCALE = DURATION / (FRAME_COUNT / FPS)

ROOT = Path(__file__).resolve().parents[1]
WORDS_PATH = ROOT / "examples" / "words.json"

CAPTION_X0 = 90
CAPTION_X1 = 900
CAPTION_Y0 = 1120
CAPTION_Y1 = 1420
PILL_Y0 = 300
PILL_Y1 = 1050


def load_words(path: Path | None = None) -> list[dict]:
    data = json.loads((path or WORDS_PATH).read_text(encoding="utf-8"))
    words = data["words"]
    if abs(float(data["duration"]) - DURATION) > 1e-6:
        raise RuntimeError(f"words.json duration {data['duration']} != {DURATION}")
    return words


WORDS = load_words()


def word_time(index: int) -> float:
    return float(WORDS[index]["t0"])


def word_end(index: int) -> float:
    return float(WORDS[index]["t1"])


def frame_time(frame: int) -> float:
    """1-based frame index to seconds on the 32.81 s clock."""
    return (int(frame) - 1) * DURATION / FRAME_COUNT


def frame_at(t: float) -> int:
    """Closest 1-based frame to a time. The seam (t=duration) is not stored."""
    if t <= 0:
        return 1
    if t >= DURATION:
        return FRAME_COUNT
    return max(1, min(FRAME_COUNT, int(round(t / DURATION * FRAME_COUNT)) + 1))


def _shot_beats() -> list[dict]:
    bounds = [
        ("s1_city", 0.0, "The back of the plane had the best odds."),
        ("s2_front", word_time(9), "Not the front."),
        ("s3_forest", 4.08, "Time dug through FAA records: seventeen crashes with both deaths and survivors."),
        ("s4_mountains", 10.02, "Front third: thirty-eight percent died. Middle third: thirty-nine. Back third... thirty-two."),
        ("s5_ocean", 18.05, "Now, seat by seat. The worst? Aisle seats, mid-cabin. Forty-four percent."),
        ("s6_desert", 24.38, "The best? Middle seats in the back. Just twenty-eight percent."),
        ("s7_loop", 28.55, "Small sample, and every crash is different... but in Time's data,"),
        ("_end", DURATION, ""),
    ]
    beats = []
    frames = []
    for name, t, _narr in bounds:
        if t <= 0:
            frames.append(1)
        elif t >= DURATION:
            frames.append(FRAME_COUNT + 1)
        else:
            frames.append(max(1, int(t / DURATION * FRAME_COUNT) + 1))
    for i in range(len(bounds) - 1):
        start = frames[i]
        end = frames[i + 1] - 1
        if i == len(bounds) - 2:
            end = FRAME_COUNT
        beats.append(
            {
                "id": bounds[i][0],
                "start": round(bounds[i][1], 4),
                "end": round(bounds[i + 1][1], 4),
                "start_frame": start,
                "end_frame": end,
                "narration": bounds[i][2],
            }
        )
    return beats


BEATS = _shot_beats()


def resolved_spec() -> dict:
    return {
        "id": "plane_seat",
        "title": "The back of the plane had the best odds",
        "status": "final",
        "format": "plane_seat",
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "duration": DURATION,
        "frame_count": FRAME_COUNT,
        "camera": {"mode": "chase", "lens_mm": 30},
        "scene": {"aircraft": "a321lr-class", "livery": "generic"},
        "beats": BEATS,
        "features": {},
    }


# Word-index groups. A page is up to three lines, shown while its words are current.
PAGES: list[list[list[int]]] = [
    [[0, 1], [2, 3, 4], [5, 6, 7, 8]],
    [[9, 10, 11]],
    [[12, 13, 14], [15, 16], [17, 18]],
    [[19, 20, 21], [22, 23]],
    [[24, 25], [26, 27, 28], [29, 30]],
    [[31], [32, 33], [34]],
    [[35, 36, 37, 38], [39, 40], [41, 42]],
    [[43], [44, 45]],
    [[46, 47], [48, 49], [50, 51, 52]],
    [[53, 54, 55]],
    [[56, 57, 58], [59, 60], [61, 62]],
    [[63, 64, 65, 66]],
]

# Zone colour for number words. Front and middle are the same amber.
NUMBER_TONE = {
    26: "amber",
    27: "amber",
    31: "amber",
    34: "green",
    44: "red",
    45: "red",
    54: "bright",
    55: "bright",
}


def token_text(index: int) -> str:
    word = WORDS[index]
    if "cap" in word:
        return str(word["cap"])
    raw = word["w"]
    if raw.lower().startswith("percent"):
        prev = WORDS[index - 1]
        if str(prev.get("cap", "")).startswith("38"):
            return "%"
        return "PERCENT"
    text = raw.upper().replace("...", "…")
    return text


def active_word(t: float) -> int | None:
    """Index whose onset interval contains t. Gaps have no highlight."""
    if t < float(WORDS[0]["t0"]):
        return None
    found = None
    for i, word in enumerate(WORDS):
        if float(word["t0"]) <= t:
            found = i
        else:
            break
    if found is None:
        return None
    if t > float(WORDS[found]["t1"]) + 1e-4:
        return None
    return found


def page_index(t: float) -> int:
    if t < float(WORDS[0]["t0"]):
        return 0
    found = 0
    for i, word in enumerate(WORDS):
        if float(word["t0"]) <= t:
            found = i
    for p, page in enumerate(PAGES):
        for line in page:
            if found in line:
                return p
    return 0


def caption_lines(t: float) -> list[list[dict]]:
    """Lines of {text, tone, active} for the page on screen at t."""
    active = active_word(t)
    lines = []
    for line in PAGES[page_index(t)]:
        tokens = []
        for index in line:
            tone = "white"
            if index == 1:
                tone = "green"
            elif index in NUMBER_TONE:
                tone = NUMBER_TONE[index]
            if active == index and tone == "white":
                tone = "yellow"
            tokens.append({"text": token_text(index), "tone": tone, "active": active == index, "index": index})
        lines.append(tokens)
    return lines


EVENTS = [
    {"id": "back_pulse", "index": 1, "cue": "Back-third green pulse", "sfx": "kenney_digital-audio/Audio/twoTone1.ogg"},
    {"id": "best_glint", "index": 7, "cue": "BEST ODDS glint on the back third", "sfx": "kenney_digital-audio/Audio/twoTone1.ogg"},
    {"id": "sun_flare", "index": 8, "cue": "Sun flare off the wing", "sfx": ""},
    {"id": "front_x", "index": 11, "cue": "X stamp on the nose", "sfx": "kenney_interface-sounds/Audio/back_001.ogg"},
    {"id": "cloud_1", "t": 4.08, "cue": "Cloud punch, city to forest", "sfx": "cloud_whoosh (v1 C1)"},
    {"id": "faa_card", "index": 15, "cue": "TIME · FAA RECORDS card", "sfx": ""},
    {"id": "icons_17", "index": 17, "cue": "17 crash icons drop", "sfx": "oga_ticking-clock/ticks.zip (tick1-4, -20 dB)"},
    {"id": "deaths_split", "index": 21, "cue": "Icons split red/green", "sfx": ""},
    {"id": "cloud_2", "t": 10.02, "cue": "Cloud punch, forest to mountains", "sfx": "cloud_whoosh (v1 C2)"},
    {"id": "pill_38", "index": 26, "cue": "Front 38% pill, same tone as 39 (it is a tie)", "sfx": "kenney_digital-audio/Audio/tone1.ogg"},
    {"id": "pill_39", "index": 31, "cue": "Middle 39% pill, same tone as 38", "sfx": "kenney_digital-audio/Audio/tone1.ogg"},
    {"id": "crane_tail", "index": 32, "cue": "Crane toward the tail", "sfx": ""},
    {"id": "pill_32", "index": 34, "cue": "Back 32% green pulse", "sfx": "kenney_digital-audio/Audio/twoTone1.ogg"},
    {"id": "cloud_dive", "t": 18.05, "cue": "Cloud layer into the cabin dive, mountains to ocean", "sfx": "cloud_whoosh"},
    {"id": "worst", "index": 40, "cue": "Whip down the aisle", "sfx": ""},
    {"id": "aisle_red", "index": 41, "cue": "Mid-cabin aisle seats flare red", "sfx": ""},
    {"id": "pill_44", "index": 44, "cue": "44% red slab", "sfx": "kenney_impact-sounds/Audio/impactGeneric_light_000.ogg (HPF 80 Hz, no LF boom)"},
    {"id": "cloud_3", "t": 24.38, "cue": "Tail exit into cloud, ocean to desert", "sfx": "cloud_whoosh (v1 C3)"},
    {"id": "best_pulse", "index": 47, "cue": "Back-third middle seats pulse", "sfx": "kenney_digital-audio/Audio/twoTone1.ogg"},
    {"id": "pill_28", "index": 54, "cue": "28% pill and shimmer", "sfx": "kenney_digital-audio/Audio/powerUp3.ogg"},
    {"id": "scatter", "index": 59, "cue": "Heatmap scatters once", "sfx": "kenney_digital-audio/Audio/pepSound1.ogg"},
    {"id": "snap_back", "index": 63, "cue": "Colours snap back, nose down into the deck", "sfx": ""},
    {"id": "seam_whoosh", "t": 32.20, "cue": "Wisps cover the lens, whoosh continues into frame 0", "sfx": "cloud_whoosh (continuous across the seam)"},
]


def event_time(event: dict) -> float:
    if "t" in event:
        return float(event["t"])
    return word_time(int(event["index"]))


def sfx_cues() -> list[dict]:
    rows = [
        {
            "time": 0.0,
            "cue": "Exterior wind and jet bed, whole film. Cabin hum while the camera is in the aisle (about 19.2–24.2 s and 25.8–28.4 s). Duck −10 to −12 dB under the VO.",
            "sfx": "wind_jet_bed (as v1); cabin_hum inside S5/S6",
        }
    ]
    for event in EVENTS:
        if not event.get("sfx"):
            continue
        rows.append({"time": round(event_time(event), 3), "cue": event["cue"], "sfx": event["sfx"]})
    rows.sort(key=lambda item: (item["time"], item["cue"]))
    return rows
