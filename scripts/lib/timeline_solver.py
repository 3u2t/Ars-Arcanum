"""Custom Non-Gregorian Calendar & Biome/Relativistic Timeline Solver (`arcanum timeline-audit`).

Validates chronological consistency across `world.yaml`, `Locations/`, `History/`, and manuscript
chapters:
1. Custom Planetary Calendars (`CustomCalendarSpec`).
2. Travel Physics & Biome Route Auditing (`TIME-301` & `TIME-302`).
3. Lorentz Relativistic Proper-Time Dilation (`compute_relativistic_proper_days`).

Repository Target: `scripts/lib/timeline_solver.py`
Delegated natively to: `src.arcanum.worldbible.timeline`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("timeline_solver", "lib.timeline_solver", "scripts.lib.timeline_solver"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.timeline import (  # noqa: E402
    DEFAULT_MODE_SPEED_KMPD,
    DEFAULT_TERRAIN_MULTIPLIER,
    CharacterTimelineEvent,
    CustomCalendarSpec,
    RouteEdge,
    TimelineAnomaly,
    audit_timeline_and_routes,
    audit_vault_timeline,
    compute_relativistic_proper_days,
    compute_shortest_travel_days,
    main,
    render_orbital_calendar_svg,
)

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

if __name__ == "__main__":
    raise SystemExit(main())
