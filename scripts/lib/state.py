#!/usr/bin/env python3
"""Ars Arcanum Workspace & Author Flow State Manager (`scripts/lib/state.py`).

Manages active manuscript, world, universe defaults, target scoping preferences,
and author daily flow state / cursor tracking.
Delegates to native `src.arcanum.core.state` while maintaining backward compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path if not present
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.arcanum.core.state import (  # noqa: E402
    clear_active_manuscript,
    clear_active_universe,
    clear_active_world,
    get_active_manuscript,
    get_active_manuscript_name,
    get_active_universe,
    get_active_universe_name,
    get_active_world,
    get_active_world_name,
    get_daily_flow_state,
    get_default_scope,
    set_active_manuscript,
    set_active_universe,
    set_active_world,
    set_daily_flow_state,
    set_default_scope,
)

__all__ = [
    "clear_active_manuscript",
    "clear_active_universe",
    "clear_active_world",
    "get_active_manuscript",
    "get_active_manuscript_name",
    "get_active_universe",
    "get_active_universe_name",
    "get_active_world",
    "get_active_world_name",
    "get_daily_flow_state",
    "get_default_scope",
    "set_active_manuscript",
    "set_active_universe",
    "set_active_world",
    "set_daily_flow_state",
    "set_default_scope",
]
