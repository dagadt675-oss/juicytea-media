"""
Countries Cut in Two — script v3.

Mercator only (w = 0). The generic renderer crossfades a globe morph, so this
episode never leaves the flat map. Move durations are the script's locked
values. Holds drift. The closing VO line is stored once; the picture loops,
the audio file does not repeat the line.
"""

from __future__ import annotations

from typing import List, Tuple

from .camera import LOOP_TAIL_SEC
from .retime import LockedCameraMove

# Script header: vo_mix_v2.wav is 75.28 s. Word indices in the v3 camera and
# event list run through 189, so the clock is that narration spread across
# 190 word slots. The uploaded take is only the closing sentence.
VO_DURATION_S = 75.28
WORD_SLOTS = 190
TOTAL_DURATION_S = 80.0

START_LON = -98.0
START_LAT = 54.0
START_SPAN = 120.0

# Pull-outs during the short hold before a long hop. The close-up stays on the
# previous move; the flight itself starts wide enough that the pan stays <= 0.8 sw/s.
_SPAN_AT_START = {
    "to_arabia": 38.0,
}

# id, cue word, duration, lon, lat, span
_MOVES: Tuple[Tuple[str, int, float, float, float, float], ...] = (
    ("na_in", 1, 2.0, -128.0, 58.0, 80.0),
    ("alaska", 8, 1.4, -146.0, 61.0, 56.0),
    ("border", 17, 1.0, -140.0, 60.0, 54.0),
    ("canada_out", 20, 1.8, -118.0, 58.0, 90.0),
    ("canada", 29, 1.2, -114.0, 57.0, 84.0),
    ("pivot_out", 34, 2.0, -150.0, 35.0, 155.0),
    ("pacific", 42, 2.0, 150.0, 15.0, 160.0),
    ("malaysia", 44, 2.0, 110.0, 3.0, 90.0),
    ("borneo", 51, 1.4, 110.0, 2.5, 62.0),
    ("brunei", 61, 2.0, 114.6, 4.5, 36.0),
    ("middle", 71, 1.0, 115.0, 4.6, 33.0),
    ("bridge", 82, 1.0, 115.2, 4.8, 31.0),
    ("to_arabia", 86, 2.0, 86.0, 16.0, 54.0),
    ("hormuz", 90, 2.0, 57.0, 24.5, 34.0),
    ("leave", 110, 1.0, 56.6, 25.2, 31.0),
    ("recap_out", 113, 2.0, 60.0, 18.0, 57.0),
    ("recap_wide", 119, 2.0, 38.0, 8.0, 100.0),
    ("africa", 131, 2.0, 15.0, -3.0, 62.0),
    ("cabinda", 135, 1.8, 13.0, -5.5, 36.0),
    ("wrong", 151, 1.0, 13.3, -5.8, 33.0),
    # The close-up cannot fly to the Caucasus inside the pan limit. This
    # pull-out is the leave from Cabinda before "But".
    ("caucasus_out", 153, 1.5, 16.0, 0.0, 50.0),
    ("caucasus", 155, 2.0, 30.0, 22.0, 60.0),
    ("nakhchivan", 167, 2.0, 45.5, 39.2, 34.0),
    ("borders", 173, 1.0, 45.2, 39.4, 31.0),
    ("home_out", 178, 2.0, 30.0, 44.0, 56.0),
    ("home_mid", 182, 2.0, -30.0, 50.0, 98.0),
    ("home", 186, 2.0, -90.0, 53.5, 114.0),
)

# Event cues from script v3. A bare int is a word index. A float is seconds.
_EVENT_CUES: Tuple[float | int, ...] = (
    0.0,
    3, 8, 13, 17, 19, 22, 26, 29, 33, 36, 38, 41,
    44, 45, 48, 51, 52, 56, 59,
    61, 63, 64, 66, 71, 73, 75, 81, 82, 85,
    86, 87, 88, 95, 98, 105, 107, 110,
    114, 116, 117, 119, 121, 124,
    130, 132, 135, 137, 138, 141, 145, 148, 151,
    157, 159, 161, 163, 165, 167, 169, 170, 171, 174, 175, 178,
    180, 182, 184, 187, 189,
)


def word_time(index: int) -> float:
    """Map a v3 word index onto the 75.28 s narration clock."""
    return float(index) * (VO_DURATION_S / WORD_SLOTS)


def _schedule_starts() -> List[float]:
    """Cue each move on its word, and never let two locked moves overlap."""
    starts: List[float] = []
    cursor = 0.0
    for i, (_mid, word, duration, _lon, _lat, _span) in enumerate(_MOVES):
        cue = 0.0 if i == 0 else word_time(word)
        start = max(cue, cursor)
        starts.append(start)
        cursor = start + duration + 0.15
    return starts


def build_cut_in_two_moves() -> List[LockedCameraMove]:
    starts = _schedule_starts()
    lon, lat, span = START_LON, START_LAT, START_SPAN
    moves: List[LockedCameraMove] = []
    for (mid, word, duration, to_lon, to_lat, to_span), start in zip(_MOVES, starts):
        span = _SPAN_AT_START.get(mid, span)
        moves.append(
            LockedCameraMove(
                mid,
                word,
                start,
                duration,
                0.0,
                0.0,
                lon,
                to_lon,
                lat,
                to_lat,
                span,
                to_span,
                drift_scale_rate=-0.012,
                drift_lon_rate=0.12,
                drift_lat_rate=0.02,
                is_snap=False,
            )
        )
        lon, lat, span = to_lon, to_lat, to_span
    return moves


def event_timestamps(total_duration: float = TOTAL_DURATION_S) -> List[float]:
    """Script event instants, with long holds sampled so the 1.5 s rule can see them."""
    times = []
    for cue in _EVENT_CUES:
        times.append(float(cue) if isinstance(cue, float) else word_time(int(cue)))
    # The last highlight stays up through t = 80. That hold is the Alaska
    # loop light, so it counts as the beat that carries the picture home.
    times.append(min(total_duration - 0.4, 79.6))
    times = sorted(t for t in times if 0.0 <= t < total_duration)
    filled: List[float] = []
    for t in times:
        if filled and t - filled[-1] > 1.45:
            cursor = filled[-1] + 1.2
            while cursor < t - 0.05:
                filled.append(round(cursor, 3))
                cursor += 1.2
        filled.append(round(t, 3))
    return filled


def build_cut_in_two_episode():
    from .episodes import EpisodeSpec

    moves = build_cut_in_two_moves()
    last_end = moves[-1].start_t + moves[-1].duration
    # Leave room for the 0.5 s Hermite tail plus the drift into frame 0.
    total = max(TOTAL_DURATION_S, last_end + LOOP_TAIL_SEC + 1.6)
    return EpisodeSpec(
        episode_id="cut_in_two",
        total_duration=total,
        first_highlight_t=0.0,
        moves=moves,
        event_timestamps=event_timestamps(total),
        map_has_yellow=True,
    )
