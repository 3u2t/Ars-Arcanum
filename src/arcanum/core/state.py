"""Ars Arcanum Workspace & Author Flow State Manager (`src/arcanum/core/state.py`).

Manages active manuscript, world, universe defaults, target scoping preferences,
and author daily flow state / cursor tracking.
"""

from __future__ import annotations

from src.arcanum.core.config import (
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
