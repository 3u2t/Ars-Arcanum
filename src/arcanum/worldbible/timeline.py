"""Custom Planetary Calendar & Overland/Relativistic Timeline Solver (src/arcanum/worldbible/timeline.py).

Validates chronological consistency across `world.yaml`, `Locations/`, `History/`, and manuscript
chapters:
1. Custom Planetary Calendars (`CustomCalendarSpec`).
2. Travel Physics & Biome Route Auditing (`TIME-301` & `TIME-302`).
3. Lorentz Relativistic Proper-Time Dilation (`compute_relativistic_proper_days`).
4. Standalone Air-gapped Orbital Wheel SVG Visualizer (`render_orbital_calendar_svg`).
"""

from __future__ import annotations

import argparse
import heapq
import itertools
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODE_SPEED_KMPD: dict[str, float] = {
    "foot": 30.0,
    "camel_caravan": 40.0,
    "horse_mounted": 65.0,
    "sailing_ship": 180.0,
    "airship": 450.0,
}

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
            raise ValueError(
                f"Day {day} out of range (1..{max_day}) for month {self.month_names[month - 1]}"
            )
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
    is_flashback: bool = False


@dataclass(frozen=True)
class TimelineAnomaly:
    """Detected chronological or travel-speed paradox."""

    rule_id: str
    character_name: str
    from_chapter: int
    to_chapter: int
    origin: str
    destination: str
    elapsed_days: int
    required_days: float
    message: str


def compute_relativistic_proper_days(coordinate_days: float, velocity_fraction_c: float) -> float:
    """Compute shipboard proper time $\\Delta \\tau = \\Delta t \\sqrt{1 - (v/c)^2}$."""
    if not (0.0 <= velocity_fraction_c < 1.0):
        raise ValueError("velocity_fraction_c must be in [0.0, 1.0)")
    return round(coordinate_days * math.sqrt(1.0 - (velocity_fraction_c**2)), 4)


def compute_shortest_travel_days(
    routes: list[RouteEdge],
    origin: str,
    destination: str,
    travel_mode: str = "camel_caravan",
) -> tuple[float, float, list[str]] | None:
    """Find minimum travel time (days) and total distance (km) between origin and destination via Dijkstra."""
    if origin == destination:
        return (0.0, 0.0, [origin])

    base_speed = DEFAULT_MODE_SPEED_KMPD.get(travel_mode, 30.0)

    # Build bidirectional graph
    adj: dict[str, list[tuple[str, float, float]]] = {}
    for r in routes:
        terrain_mult = DEFAULT_TERRAIN_MULTIPLIER.get(r.terrain, 0.75)
        speed = max(1.0, base_speed * terrain_mult)
        days = r.distance_km / speed
        adj.setdefault(r.origin, []).append((r.destination, days, r.distance_km))
        adj.setdefault(r.destination, []).append((r.origin, days, r.distance_km))

    if origin not in adj or destination not in adj:
        return None

    pq: list[tuple[float, str, float, list[str]]] = [(0.0, origin, 0.0, [origin])]
    best_days: dict[str, float] = {origin: 0.0}

    while pq:
        curr_days, u, curr_km, path = heapq.heappop(pq)
        if curr_days > best_days.get(u, float("inf")):
            continue

        if u == destination:
            return (round(curr_days, 2), round(curr_km, 2), path)

        for v, edge_days, edge_km in adj.get(u, []):
            new_days = curr_days + edge_days
            if new_days < best_days.get(v, float("inf")):
                best_days[v] = new_days
                heapq.heappush(pq, (new_days, v, curr_km + edge_km, [*path, v]))

    return None


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
                if curr_ev.is_flashback:
                    continue
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
                shortest = compute_shortest_travel_days(
                    routes,
                    prev_ev.location,
                    curr_ev.location,
                    curr_ev.travel_mode,
                )
                if shortest is not None:
                    min_days, total_km, path = shortest
                    if elapsed < math.ceil(min_days):
                        edge = route_lookup.get((prev_ev.location, curr_ev.location))
                        if edge is not None:
                            msg = (
                                f"TIME-301 Impossible Travel Speed: '{char_name}' travels "
                                f"{edge.distance_km:.0f} km across '{edge.terrain}' from "
                                f"'{prev_ev.location}' to '{curr_ev.location}' via "
                                f"'{curr_ev.travel_mode}' in {elapsed} days (minimum required: "
                                f"{min_days:.1f} days)."
                            )
                        else:
                            msg = (
                                f"TIME-301 Impossible Travel Speed: '{char_name}' travels "
                                f"{total_km:.0f} km from '{prev_ev.location}' to '{curr_ev.location}' "
                                f"via '{curr_ev.travel_mode}' ({' -> '.join(path)}) in {elapsed} days "
                                f"(minimum required: {min_days:.1f} days)."
                            )
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
                                message=msg,
                            )
                        )

    return {
        "passed": len(anomalies) == 0,
        "calendar_name": calendar.calendar_name,
        "days_per_year": calendar.days_per_year,
        "events_audited": len(events),
        "routes_loaded": len(routes),
        "anomalies": [asdict(a) for a in anomalies],
    }


def audit_vault_timeline(
    vault_root: Path,
    world_root: Path | None = None,
) -> dict[str, Any]:
    """Automatically scan `world.yaml`, `Locations/*.md`, and chapter frontmatter via `VaultIndex`."""
    try:
        from scripts.lib.vault_index import VaultIndex, parse_frontmatter
    except ImportError:
        from lib.vault_index import VaultIndex, parse_frontmatter  # type: ignore[no-redef]

    root = vault_root.resolve()
    w_root = Path(world_root).resolve() if world_root is not None and Path(world_root).is_dir() else None
    cal_name = "Standard Solar Reckoning"
    month_lengths: tuple[int, ...] = (30,) * 12

    world_yaml = root / "world.yaml"
    if not world_yaml.exists() and w_root is not None:
        world_yaml = w_root / "world.yaml"

    if world_yaml.exists():
        raw = world_yaml.read_text(encoding="utf-8")
        wrapped = raw if raw.lstrip().startswith("---") else f"---\n{raw}\n---\n"
        w_meta, _ = parse_frontmatter(wrapped)
        if "calendar_name" in w_meta:
            cal_name = str(w_meta["calendar_name"])
        if isinstance(w_meta.get("month_lengths"), list) and w_meta["month_lengths"]:
            month_lengths = tuple(int(x) for x in w_meta["month_lengths"])

    calendar = CustomCalendarSpec(
        calendar_name=cal_name,
        month_names=tuple(f"Month-{i}" for i in range(1, len(month_lengths) + 1)),
        month_lengths=month_lengths,
    )

    index = VaultIndex(root)
    nodes = list(index.scan_vault())
    world_nodes: list[Any] = []
    if w_root is not None:
        world_nodes = list(VaultIndex(w_root).scan_vault())

    routes: list[RouteEdge] = []
    events: list[CharacterTimelineEvent] = []

    for node in nodes + world_nodes:
        fm = node.frontmatter
        rel = node.relative_path
        if ("Locations/" in rel or fm.get("type") == "route") and (
            "origin" in fm and "destination" in fm and "distance_km" in fm
        ):
            routes.append(
                RouteEdge(
                    origin=str(fm["origin"]),
                    destination=str(fm["destination"]),
                    distance_km=float(fm["distance_km"]),
                    terrain=str(fm.get("terrain", "sand_sea")),
                )
            )

    for idx_num, node in enumerate(nodes, start=1):
        fm = node.frontmatter
        rel = node.relative_path
        if "year" in fm and "month" in fm and "day" in fm:
            char_name = str(fm.get("pov") or node.directives.get("pov") or "Protagonist")
            loc = str(fm.get("location") or node.directives.get("location") or "Unknown")
            is_flashback = bool(
                fm.get("flashback")
                or fm.get("is_flashback")
                or str(node.directives.get("flashback", "")).lower() in ("true", "1")
                or str(node.directives.get("is_flashback", "")).lower() in ("true", "1")
            )
            events.append(
                CharacterTimelineEvent(
                    chapter_index=int(fm.get("chapter", idx_num)),
                    character_name=char_name,
                    location=loc,
                    year=int(fm["year"]),
                    month=int(fm["month"]),
                    day=int(fm["day"]),
                    travel_mode=str(fm.get("travel_mode", "camel_caravan")),
                    is_flashback=is_flashback,
                )
            )

    return audit_timeline_and_routes(calendar=calendar, routes=routes, events=events)


def render_orbital_calendar_svg(
    calendar: CustomCalendarSpec,
    width: int = 640,
    height: int = 640,
    theme: str = "dark",
) -> str:
    """Renders a standalone, air-gapped SVG orbital diagram of a custom planetary calendar."""
    cx = width / 2.0
    cy = height / 2.0
    outer_r = min(width, height) * 0.42
    inner_r = outer_r * 0.70
    hub_r = outer_r * 0.22
    total_days = max(1, calendar.days_per_year)

    is_light = (theme.lower() == "light")
    bg_color = "#ffffff" if is_light else "#0d1117"
    text_primary = "#1f2328" if is_light else "#e6edf3"
    text_secondary = "#59636e" if is_light else "#8b949e"
    guide_color = "#d0d7de" if is_light else "#30363d"
    title_color = "#0969da" if is_light else "#58a6ff"
    sector_opacity = "0.35" if is_light else "0.22"

    palette = [
        "#2a9d8f", "#e76f51", "#f4a261", "#457b9d",
        "#1d3557", "#8338ec", "#3a86ff", "#06d6a0",
        "#e63946", "#fb8500", "#023047", "#2b9348",
    ]

    elements: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background-color: {bg_color}; font-family: system-ui, -apple-system, sans-serif;">',
        "  <defs>",
        '    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
        '      <feGaussianBlur stdDeviation="6" result="blur" />',
        '      <feComposite in="SourceGraphic" in2="blur" operator="over" />',
        "    </filter>",
        "  </defs>",
        f"  <title>{calendar.calendar_name} — Orbital Calendar Wheel</title>",
        "  <!-- Background guide rings -->",
        f'  <circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="{guide_color}" stroke-width="2" />',
        f'  <circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="none" stroke="{guide_color}" stroke-width="1.5" stroke-dasharray="4,4" />',
    ]

    current_day = 0
    for idx, (m_name, m_days) in enumerate(zip(calendar.month_names, calendar.month_lengths)):
        start_angle = 2.0 * math.pi * (current_day / total_days) - (math.pi / 2.0)
        end_day = current_day + m_days
        end_angle = 2.0 * math.pi * (end_day / total_days) - (math.pi / 2.0)
        mid_angle = (start_angle + end_angle) / 2.0
        current_day = end_day

        x1_out = cx + outer_r * math.cos(start_angle)
        y1_out = cy + outer_r * math.sin(start_angle)
        x2_out = cx + outer_r * math.cos(end_angle)
        y2_out = cy + outer_r * math.sin(end_angle)

        x1_in = cx + inner_r * math.cos(end_angle)
        y1_in = cy + inner_r * math.sin(end_angle)
        x2_in = cx + inner_r * math.cos(start_angle)
        y2_in = cy + inner_r * math.sin(start_angle)

        large_arc = 1 if (end_angle - start_angle) > math.pi else 0
        fill_color = palette[idx % len(palette)]

        path_d = (
            f"M {x1_out:.1f} {y1_out:.1f} "
            f"A {outer_r:.1f} {outer_r:.1f} 0 {large_arc} 1 {x2_out:.1f} {y2_out:.1f} "
            f"L {x1_in:.1f} {y1_in:.1f} "
            f"A {inner_r:.1f} {inner_r:.1f} 0 {large_arc} 0 {x2_in:.1f} {y2_in:.1f} Z"
        )
        elements.append(
            f'  <path d="{path_d}" fill="{fill_color}" fill-opacity="{sector_opacity}" stroke="{fill_color}" stroke-width="1.5" />'
        )

        label_r = (inner_r + outer_r) / 2.0
        lx = cx + label_r * math.cos(mid_angle)
        ly = cy + label_r * math.sin(mid_angle)
        rot_deg = math.degrees(mid_angle) + 90.0
        if 90.0 < rot_deg < 270.0:
            rot_deg += 180.0

        elements.append(
            f'  <text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'fill="{text_primary}" font-size="11" font-weight="600" '
            f'transform="rotate({rot_deg:.1f}, {lx:.1f}, {ly:.1f})">{m_name} ({m_days}d)</text>'
        )

    elements.extend([
        "  <!-- Central Star -->",
        f'  <circle cx="{cx}" cy="{cy}" r="{hub_r}" fill="#ffb703" fill-opacity="0.15" stroke="#fb8500" stroke-width="1.5" />',
        f'  <circle cx="{cx}" cy="{cy}" r="{hub_r * 0.55:.1f}" fill="#ffd166" filter="url(#glow)" />',
        f'  <text x="{cx}" y="{cy - 6}" text-anchor="middle" fill="#0d1117" font-size="10" font-weight="700">SOL</text>',
        f'  <text x="{cx}" y="{cy + 7}" text-anchor="middle" fill="#0d1117" font-size="8">{total_days} DAYS</text>',
        "  <!-- Calendar Title Banner -->",
        f'  <text x="{cx}" y="32" text-anchor="middle" fill="{title_color}" font-size="15" font-weight="700" letter-spacing="1">{calendar.calendar_name.upper()}</text>',
        f'  <text x="{cx}" y="48" text-anchor="middle" fill="{text_secondary}" font-size="11">{len(calendar.month_lengths)} Months · {total_days} Days per Orbital Revolution</text>',
        "</svg>",
    ])

    return "\n".join(elements)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum timeline-audit` / `arcanum timeline-solver`."""
    parser = argparse.ArgumentParser(
        prog="arcanum timeline-audit",
        description="Audit custom planetary calendar dates and overland/relativistic travel routes.",
    )
    parser.add_argument("vault", nargs="?", type=Path, default=Path.cwd(), help="Vault or manuscript directory")
    args = parser.parse_args(argv)

    result = audit_vault_timeline(args.vault)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if result["passed"] else 1


__all__ = [
    "CharacterTimelineEvent",
    "CustomCalendarSpec",
    "DEFAULT_MODE_SPEED_KMPD",
    "DEFAULT_TERRAIN_MULTIPLIER",
    "RouteEdge",
    "TimelineAnomaly",
    "audit_timeline_and_routes",
    "audit_vault_timeline",
    "compute_relativistic_proper_days",
    "compute_shortest_travel_days",
    "main",
    "render_orbital_calendar_svg",
]
