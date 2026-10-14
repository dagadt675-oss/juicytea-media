"""
Juicy Tea Map-Shorts Engine — Production episode specifications.

cut_in_two keeps the close-up end spans (Brunei 4.8°, Musandam 5.4°,
Cabinda 7.2°, Nakhchivan 5.6°) and the orthographic globe on ocean
crossings. Each zoom is staged so the 60 fps linter stays inside
1.2/s on a snap and 0.8 screen-widths/s of pan. A single snap cannot
legally drop from a continental view to 5°.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

from .camera import ContinuousCameraRig
from .labels import MapLabelItem, PillBannerItem
from .retime import LockedCameraMove, build_anchors_with_drift


@dataclass(frozen=True)
class CountryHighlightCue:
    iso_a3: str
    enter_t: float
    exit_t: float
    fill_rgba: Tuple[int, int, int, int]
    where: str = ""


@dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    total_duration: float
    first_highlight_t: float
    moves: List[LockedCameraMove]
    event_timestamps: List[float]
    highlights: List[CountryHighlightCue] = field(default_factory=list)
    labels: List[MapLabelItem] = field(default_factory=list)
    pills: List[PillBannerItem] = field(default_factory=list)
    map_has_yellow: bool = True

    def build_rig(self) -> ContinuousCameraRig:
        return ContinuousCameraRig(
            build_anchors_with_drift(self.moves),
            total_duration=self.total_duration,
        )

    def snap_intervals(self) -> List[Tuple[float, float]]:
        return [(m.start_t, m.start_t + m.duration) for m in self.moves if m.is_snap]


def _chain(opening: Tuple[float, float, float, float], steps: Sequence[tuple]) -> List[LockedCameraMove]:
    """opening is (w, lon, lat, span) at t=0.

    Each step is (name, duration, gap_before, w, lon, lat, span, snap) and
    describes the pose at the END of that move. The start pose is the previous
    end, so a hold cannot teleport.
    """
    prev_w, prev_lon, prev_lat, prev_span = opening
    t = 0.0
    moves: List[LockedCameraMove] = []
    for index, (name, dur, gap, w, lon, lat, span, snap) in enumerate(steps, start=1):
        t = round(t + gap, 3)
        moves.append(
            LockedCameraMove(
                name,
                index,
                t,
                dur,
                prev_w,
                w,
                prev_lon,
                lon,
                prev_lat,
                lat,
                prev_span,
                span,
                drift_scale_rate=-0.01,
                drift_lon_rate=0.04,
                drift_lat_rate=0.012,
                is_snap=snap,
            )
        )
        t = round(t + dur, 3)
        prev_w, prev_lon, prev_lat, prev_span = w, lon, lat, span
    return moves


def _events(moves: List[LockedCameraMove], total: float, extra: Sequence[float] = ()) -> List[float]:
    grid = [round(i * 1.1, 2) for i in range(1, int(total / 1.1) + 1) if i * 1.1 < total]
    return sorted(set(grid + [m.start_t for m in moves] + [float(t) for t in extra]))


def build_greenland_episode() -> EpisodeSpec:
    moves = _chain(
        (0.0, -42.0, 72.0, 84.0),
        [
            ("gr_open", 1.40, 0.00, 0.0, -41.0, 69.0, 64.0, True),
            ("gr_to_africa", 1.90, 2.60, 0.28, -14.0, 42.0, 78.0, False),
            ("gr_drag", 1.85, 2.30, 0.0, 14.0, 14.0, 66.0, False),
            ("gr_pack", 1.60, 3.95, 0.0, 18.0, 6.5, 52.0, False),
            ("gr_widen", 1.90, 2.60, 0.35, 12.0, 16.0, 88.0, True),
            ("gr_globe", 2.00, 1.40, 1.00, -8.0, 36.0, 108.0, True),
            ("gr_denmark", 2.00, 6.10, 0.30, 10.0, 56.0, 62.0, True),
            ("gr_arctic", 1.80, 6.60, 1.00, -22.0, 68.0, 72.0, True),
            ("gr_loop", 1.85, 6.60, 0.0, -42.0, 72.0, 84.0, False),
        ],
    )
    total = 52.42
    return EpisodeSpec(
        episode_id="greenland",
        total_duration=total,
        first_highlight_t=0.25,
        moves=moves,
        event_timestamps=_events(moves, total),
        map_has_yellow=True,
    )


def build_cut_in_two_episode() -> EpisodeSpec:
    """Alaska → Malaysia → Brunei → Hormuz → Cabinda → Nakhchivan → Alaska.

    Longitude is unwrapped. Decreasing values cross the Pacific westward;
    the flight home increases them so the globe takes the short arc back.
    """
    moves = _chain(
        (0.82, -146.0, 63.0, 58.0),
        [
            ("alaska_in", 1.70, 0.00, 0.20, -150.0, 64.2, 30.0, True),
            ("alaska_holdpan", 1.60, 2.40, 0.05, -142.0, 61.5, 26.0, False),
            ("canada", 1.80, 1.80, 0.15, -112.0, 57.0, 42.0, False),
            ("widen_pacific", 1.90, 1.60, 0.72, -128.0, 48.0, 120.0, True),
            ("pacific_a", 1.90, 0.25, 0.88, -180.0, 30.0, 145.0, False),
            ("pacific_b", 1.90, 0.25, 0.84, -246.0, 10.0, 125.0, False),
            ("my_zoom1", 1.85, 0.25, 0.40, -250.0, 6.2, 48.0, True),
            ("my_zoom2", 1.85, 0.22, 0.08, -248.0, 4.9, 17.5, True),
            ("brunei", 1.90, 0.22, 0.00, -245.30, 4.72, 6.20, True),
            ("brunei_tight", 1.70, 0.22, 0.00, -245.28, 4.74, 4.80, True),
            ("br_out1", 1.80, 2.60, 0.05, -246.0, 4.6, 13.2, True),
            ("br_out2", 1.85, 0.22, 0.35, -262.0, 10.0, 38.0, True),
            ("br_out3", 1.90, 0.22, 0.78, -286.0, 18.0, 115.0, True),
            ("to_hormuz", 1.90, 0.22, 0.70, -303.70, 25.5, 108.0, False),
            ("hz_in1", 1.80, 0.22, 0.28, -303.75, 25.9, 40.0, True),
            ("hz_in2", 1.80, 0.22, 0.05, -303.74, 26.08, 14.8, True),
            ("musandam", 1.85, 0.22, 0.00, -303.72, 26.18, 5.40, True),
            ("hz_out1", 1.80, 2.50, 0.10, -305.0, 23.0, 15.2, True),
            ("hz_out2", 1.85, 0.22, 0.50, -314.0, 14.0, 44.0, True),
            ("hz_out3", 1.90, 0.22, 0.88, -328.0, 6.0, 125.0, True),
            ("to_cabinda", 1.80, 0.22, 0.50, -347.80, -4.2, 95.0, False),
            ("cb_in1", 1.80, 0.22, 0.12, -347.82, -5.05, 34.0, True),
            ("cb_in2", 1.80, 0.22, 0.00, -347.84, -5.12, 13.0, True),
            ("cabinda", 1.70, 0.22, 0.00, -347.82, -5.12, 7.20, True),
            ("angola", 1.60, 2.20, 0.00, -344.50, -9.0, 14.0, True),
            ("af_out1", 1.80, 0.30, 0.30, -338.0, 6.0, 40.0, True),
            ("af_out2", 1.90, 0.22, 0.72, -328.0, 24.0, 110.0, True),
            ("to_caucasus", 1.80, 0.22, 0.60, -314.60, 38.6, 90.0, False),
            ("nk_in1", 1.80, 0.22, 0.20, -314.65, 39.15, 32.0, True),
            ("nk_in2", 1.80, 0.22, 0.04, -314.58, 39.25, 12.2, True),
            ("nakhchivan", 1.85, 0.22, 0.00, -314.55, 39.30, 5.60, True),
            ("nk_out1", 1.80, 2.30, 0.10, -308.0, 41.5, 15.8, True),
            ("nk_out2", 1.85, 0.22, 0.42, -292.0, 48.0, 44.0, True),
            ("nk_out3", 1.90, 0.22, 0.86, -240.0, 56.0, 125.0, True),
            ("home_a", 1.90, 0.22, 0.90, -190.0, 60.5, 140.0, False),
            ("home_b", 1.90, 0.22, 0.86, -162.0, 62.4, 90.0, True),
            ("home_settle", 1.85, 0.22, 0.82, -146.0, 63.0, 58.0, True),
        ],
    )
    total = round(moves[-1].start_t + moves[-1].duration + 3.2, 2)
    highlights = [
        CountryHighlightCue("USA", -0.40, 7.20, (242, 198, 65, 210), "alaska"),
        CountryHighlightCue("CAN", 7.40, 11.10, (219, 94, 86, 200)),
        CountryHighlightCue("MYS", 17.20, 23.40, (219, 94, 86, 210)),
        CountryHighlightCue("BRN", 21.30, 27.70, (245, 197, 24, 220)),
        CountryHighlightCue("OMN", 36.20, 44.40, (219, 94, 86, 210)),
        CountryHighlightCue("ARE", 37.00, 44.40, (242, 198, 65, 200)),
        CountryHighlightCue("COD", 53.00, 62.30, (88, 154, 186, 200)),
        CountryHighlightCue("AGO", 54.80, 60.40, (245, 197, 24, 220), "cabinda"),
        CountryHighlightCue("AGO", 56.80, 62.40, (82, 168, 104, 200), "angola_main"),
        CountryHighlightCue("AZE", 69.00, 76.70, (88, 154, 186, 180), "azerbaijan_main"),
        CountryHighlightCue("AZE", 72.60, 76.70, (245, 197, 24, 230), "nakhchivan"),
        CountryHighlightCue("ARM", 70.40, 76.70, (235, 142, 70, 210)),
        CountryHighlightCue("USA", 86.60, total + 1.0, (242, 198, 65, 210), "alaska"),
    ]
    labels = [
        MapLabelItem("ALASKA", -150.0, 64.6, 1.10, 6.90),
        MapLabelItem("BRITISH", -122.0, 54.5, 7.60, 9.40, color_rgba=(255, 150, 150, 255), font_size=32),
        MapLabelItem("CANADA", -108.0, 58.5, 8.40, 11.00, color_rgba=(255, 120, 120, 255), font_size=44),
        MapLabelItem("MALAYSIA", 102.0, 4.6, 17.70, 22.60, color_rgba=(255, 110, 110, 255)),
        MapLabelItem("PENINSULA", 101.2, 2.6, 18.30, 22.60, font_size=32),
        MapLabelItem("BORNEO", 114.2, 1.6, 19.10, 23.20),
        MapLabelItem("BRUNEI", 114.75, 4.95, 23.40, 27.60, font_size=36),
        MapLabelItem("SARAWAK", 112.6, 2.4, 24.00, 27.20, color_rgba=(255, 140, 140, 255), font_size=32),
        MapLabelItem("UAE", 54.2, 24.0, 38.20, 44.20),
        MapLabelItem("OMAN", 57.4, 22.0, 40.20, 44.20, color_rgba=(255, 130, 130, 255)),
        MapLabelItem("MUSANDAM", 56.40, 26.35, 40.10, 44.20, color_rgba=(255, 160, 160, 255), font_size=32),
        MapLabelItem("CABINDA", 12.25, -4.85, 56.50, 60.40, font_size=36),
        MapLabelItem("DR CONGO", 19.5, -2.8, 57.40, 61.40, color_rgba=(140, 205, 255, 255)),
        MapLabelItem("ANGOLA", 17.2, -12.2, 60.50, 62.50, color_rgba=(140, 230, 160, 255)),
        MapLabelItem("NAKHCHIVAN", 45.35, 39.15, 72.70, 76.60, font_size=32),
        MapLabelItem("ARMENIA", 44.4, 40.45, 73.10, 76.60, color_rgba=(255, 180, 110, 255), font_size=34),
        MapLabelItem("AZERBAIJAN", 48.4, 40.55, 72.90, 76.60, color_rgba=(140, 205, 255, 255), font_size=32),
        MapLabelItem("IRAN", 46.3, 37.55, 73.80, 76.60, font_size=32),
    ]
    pills = [
        PillBannerItem("$7.2M · ≈2¢/ACRE · 1867", 540, 340, 0.70, 6.40, "red"),
        PillBannerItem("BORDER CHECK", 540, 430, 6.20, 7.15, "red"),
        PillBannerItem("STILL IN THE WAY", 540, 360, 8.70, 10.70, "red"),
        PillBannerItem("2 PIECES", 540, 340, 12.40, 14.40, "dark"),
        PillBannerItem("1963", 540, 340, 17.50, 20.90, "dark"),
        PillBannerItem("1890", 540, 340, 23.50, 26.10, "dark"),
        PillBannerItem("RIGHT OUT OF THE MIDDLE", 540, 430, 25.90, 27.55, "dark"),
        PillBannerItem("19 MI", 540, 340, 26.30, 27.70, "blue"),
        PillBannerItem("STRAIT OF HORMUZ", 540, 340, 36.30, 39.60, "blue"),
        PillBannerItem("EXIT OMAN", 540, 430, 42.20, 44.30, "red"),
        # Gone before the Africa close-up. They must not ride over the continent.
        PillBannerItem("SAME TRICK", 540, 270, 48.90, 52.10, "dark"),
        PillBannerItem("A WHOLE SEA", 540, 360, 49.30, 52.10, "blue"),
        # Above the globe. These leave before the Cabinda close-up.
        PillBannerItem("ALASKA", 300, 470, 48.70, 52.10, "yellow"),
        PillBannerItem("BRUNEI", 300, 560, 49.20, 52.10, "yellow"),
        PillBannerItem("MALAYSIA", 780, 470, 49.00, 52.10, "red"),
        PillBannerItem("OMAN", 780, 560, 49.50, 52.10, "red"),
        PillBannerItem("1885", 540, 340, 52.90, 55.40, "dark"),
        PillBannerItem("WRONG SIDE", 540, 420, 58.70, 62.20, "red"),
        PillBannerItem("1921", 540, 340, 67.10, 70.60, "dark"),
        # On the Nakhchivan close-up, gone before the flight crosses Europe.
        PillBannerItem("TURKEY · 11 KM", 540, 340, 74.10, 76.30, "red"),
        PillBannerItem("EXCEPT AZERBAIJAN", 540, 440, 74.90, 76.60, "dark"),
    ]
    return EpisodeSpec(
        episode_id="cut_in_two",
        total_duration=total,
        first_highlight_t=0.15,
        moves=moves,
        event_timestamps=_events(moves, total, [p.enter_t for p in pills] + [lb.enter_t for lb in labels]),
        highlights=highlights,
        labels=labels,
        pills=pills,
        map_has_yellow=True,
    )
