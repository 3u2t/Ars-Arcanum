#!/usr/bin/env python3
"""
Ars Arcanum Writing Sprint & Cognitive Velocity Engine (scripts/lib/writing_sprint.py)
====================================================================================
Offline author productivity timer, session velocity analytics logger, and habit
consistency engine for speculative fiction authors.

Delegated natively to: src.arcanum.manuscript.velocity
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("writing_sprint", "lib.writing_sprint", "scripts.lib.writing_sprint"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.manuscript.velocity import (  # noqa: E402
    cancel_sprint,
    format_stats_markdown,
    format_stats_table,
    get_velocity_metrics,
    log_manual_sprint,
    main,
    start_sprint,
    status_sprint,
    stop_sprint,
)

__all__ = [
    "cancel_sprint",
    "format_stats_markdown",
    "format_stats_table",
    "get_velocity_metrics",
    "log_manual_sprint",
    "main",
    "start_sprint",
    "status_sprint",
    "stop_sprint",
]

if __name__ == "__main__":
    sys.exit(main())
