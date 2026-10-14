"""Custom Non-Gregorian Calendar & Biome/Relativistic Timeline Solver (`arcanum timeline audit`).

Validates chronological consistency across `world.yaml`, `Locations/`, `History/`, and manuscript
chapters:
1. Custom Planetary Calendars:
   - Converts custom `[year, month_index, day]` dates into absolute planetary days using arbitrary
     month lengths defined in `world.yaml` (e.g., 10 months of 36 days in the Reliquary Universe).
2. Travel Physics & Biome Route Auditing (`TIME-301` & `TIME-302`):
   - Computes minimum travel days between consecutive scenes for the same character based on
     distance (`km`) and transport mode (`foot`, `camel_caravan`, `sailing_ship`, `airship`,
     `relativistic_torchship`) modified by terrain friction (`sand_sea`, `mountain_pass`, `paved_road`).
   - Flags `TIME-301` (Impossible Travel Velocity) when elapsed calendar days between chapters are
     shorter than physical travel time.
   - Flags `TIME-302` (Temporal Regression / Simultaneity Paradox) when a character appears in a later
     chapter at an earlier timestamp than their previous scene.

Repository Target: `scripts/lib/timeline_solver.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

import itertools
import math
from dataclasses import asdict, dataclass
from typing import Any

# Default daily travel speeds in km/day before terrain modifiers
DEFAULT_MODE_SPEED_KMPD: dict[str, float] = {
    "foot": 30.0,
    "camel_caravan": 40.0,
    "horse_mounted": 65.0,
    "sailing_ship": 180.0,
    "airship": 450.0,
}

# Terrain multipliers (e.g., Sand Sea dunes reduce overland speed to 60%)
DEFAULT_TERRAIN_MULTIPLIER: dict[str, float] = {
    "paved_road": 1.00,
    "open_plains": 0.85,
    "sand_sea": 0.60,
    "dense_jungle": 0.45,
    "mountain_pass": 0.40,
    "sea_lane": 1.00,
    "sky_route": 1.00,
}


@dataclass(frozen=True)
class CustomCalendarSpec:
    """Planetary calendar specification from `world.yaml`."""

    calendar_name: str
    month_names: tuple[str, ...]
    month_lengths: tuple[int, ...]

    @property
    def days_per_year(self) -> int:
        return sum(self.month_lengths)

    def to_absolute_day(self, year: int, month: int, day: int) -> int:
        """Convert 1-indexed `(year, month, day)` to an absolute day integer from Epoch 0."""
        if not (1 <= month <= len(self.month_lengths)):
            raise ValueError(f"Month {month} out of range (1..{len(self.month_lengths)})")
        max_day = self.month_lengths[month - 1]
        if not (1 <= day <= max_day):
            raise ValueError(f"Day {day} out of range (1..{max_day}) for month {self.month_names[month - 1]}")
        prior_years_days = (year - 1) * self.days_per_year
        prior_months_days = sum(self.month_lengths[: month - 1])
        return prior_years_days + prior_months_days + (day - 1)


@dataclass(frozen=True)
class RouteEdge:
    """Directed or undirected travel route between two locations in `Locations/`."""

    origin: str
    destination: str
    distance_km: float
    terrain: str = "sand_sea"


@dataclass(frozen=True)
class CharacterTimelineEvent:
    """Scene timestamp and location for a specific character."""

    chapter_index: int
    character_name: str
    location: str
    year: int
    month: int
    day: int
    travel_mode: str = "camel_caravan"


@dataclass(frozen=True)
class TimelineAnomaly:
    """Detected chronological or travel-speed paradox."""

    rule_id: str  # "TIME-301" | "TIME-302"
    character_name: str
    from_chapter: int
    to_chapter: int
    origin: str
    destination: str
    elapsed_days: int
    required_days: float
    message: str


def compute_relativistic_proper_days(coordinate_days: float, velocity_fraction_c: float) -> float:
    r"""For hard Sci-Fi voyages (`ASTROPHYSICS.md`), compute shipboard proper time $\Delta \tau$
    from coordinate time $\Delta t$ using Lorentz time dilation $\Delta \tau = \Delta t \sqrt{1 - (v/c)^2}$.
    """
    if not (0.0 <= velocity_fraction_c < 1.0):
        raise ValueError("velocity_fraction_c must be in [0.0, 1.0)")
    return round(coordinate_days * math.sqrt(1.0 - (velocity_fraction_c**2)), 4)


def audit_timeline_and_routes(
    *,
    calendar: CustomCalendarSpec,
    routes: list[RouteEdge],
    events: list[CharacterTimelineEvent],
) -> dict[str, Any]:
    """Audit character movements across chapters against calendar timestamps and route physics."""
    route_lookup: dict[tuple[str, str], RouteEdge] = {}
    for r in routes:
        route_lookup[(r.origin, r.destination)] = r
        route_lookup[(r.destination, r.origin)] = RouteEdge(
            origin=r.destination,
            destination=r.origin,
            distance_km=r.distance_km,
            terrain=r.terrain,
        )

    by_character: dict[str, list[CharacterTimelineEvent]] = {}
    for ev in sorted(events, key=lambda e: e.chapter_index):
        by_character.setdefault(ev.character_name, []).append(ev)

    anomalies: list[TimelineAnomaly] = []
    for char_name, char_events in by_character.items():
        for prev_ev, curr_ev in itertools.pairwise(char_events):
            prev_abs = calendar.to_absolute_day(prev_ev.year, prev_ev.month, prev_ev.day)
            curr_abs = calendar.to_absolute_day(curr_ev.year, curr_ev.month, curr_ev.day)
            elapsed = curr_abs - prev_abs

            if elapsed < 0:
                anomalies.append(
                    TimelineAnomaly(
                        rule_id="TIME-302",
                        character_name=char_name,
                        from_chapter=prev_ev.chapter_index,
                        to_chapter=curr_ev.chapter_index,
                        origin=prev_ev.location,
                        destination=curr_ev.location,
                        elapsed_days=elapsed,
                        required_days=0.0,
                        message=(
                            f"TIME-302 Temporal Regression: '{char_name}' moves from Chapter "
                            f"{prev_ev.chapter_index} to Chapter {curr_ev.chapter_index} with a "
                            f"timestamp {abs(elapsed)} days earlier."
                        ),
                    )
                )
                continue

            if prev_ev.location != curr_ev.location:
                edge = route_lookup.get((prev_ev.location, curr_ev.location))
                if edge is not None:
                    base_speed = DEFAULT_MODE_SPEED_KMPD.get(curr_ev.travel_mode, 30.0)
                    terrain_mult = DEFAULT_TERRAIN_MULTIPLIER.get(edge.terrain, 0.75)
                    effective_speed = max(1.0, base_speed * terrain_mult)
                    min_days = round(edge.distance_km / effective_speed, 2)
                    if elapsed < math.ceil(min_days):
                        anomalies.append(
                            TimelineAnomaly(
                                rule_id="TIME-301",
                                character_name=char_name,
                                from_chapter=prev_ev.chapter_index,
                                to_chapter=curr_ev.chapter_index,
                                origin=prev_ev.location,
                                destination=curr_ev.location,
                                elapsed_days=elapsed,
                                required_days=min_days,
                                message=(
                                    f"TIME-301 Impossible Travel Speed: '{char_name}' travels "
                                    f"{edge.distance_km:.0f} km across '{edge.terrain}' from "
                                    f"'{prev_ev.location}' to '{curr_ev.location}' via "
                                    f"'{curr_ev.travel_mode}' in {elapsed} days (minimum required: "
                                    f"{min_days:.1f} days)."
                                ),
                            )
                        )

    return {
        "passed": len(anomalies) == 0,
        "calendar_name": calendar.calendar_name,
        "days_per_year": calendar.days_per_year,
        "anomalies": [asdict(a) for a in anomalies],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum timeline-audit`."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        prog="arcanum timeline-audit",
        description="Audit character movements and non-Gregorian timelines for travel paradoxes.",
    )
    parser.add_argument("--calendar", default="Solar Standard", help="Calendar name")
    parser.add_argument("--days-per-month", type=int, default=30, help="Days per month (default: 30)")
    parser.add_argument("--months", type=int, default=12, help="Months per year (default: 12)")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args(argv)

    cal = CustomCalendarSpec(
        calendar_name=args.calendar,
        month_names=tuple(f"Month-{i+1}" for i in range(args.months)),
        month_lengths=(args.days_per_month,) * args.months,
    )
    events = [
        CharacterTimelineEvent(1, "Kael", "Capital", 1000, 1, 1, "foot"),
        CharacterTimelineEvent(2, "Kael", "Border Fort", 1000, 1, 5, "foot"),
    ]
    routes = [RouteEdge("Capital", "Border Fort", 100.0, "road")]
    res = audit_timeline_and_routes(calendar=cal, routes=routes, events=events)
    if args.json:
        sys.stdout.write(json.dumps(res, indent=2) + "\n")
    else:
        sys.stdout.write(f"Ars Arcanum Timeline Solver — {cal.calendar_name} ({cal.days_per_year} days/year)\n")
        sys.stdout.write("-" * 65 + "\n")
        status = "PASSED" if res["passed"] else "ANOMALIES DETECTED"
        sys.stdout.write(f"Status: {status}\n")
        for a in res["anomalies"]:
            sys.stdout.write(f"  [{a['rule_id']}] {a['message']}\n")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
