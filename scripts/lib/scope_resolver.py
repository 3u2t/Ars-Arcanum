#!/usr/bin/env python3
"""
Ars Arcanum Scope & Context Resolver (scripts/lib/scope_resolver.py)
===================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.scope.
"""

from __future__ import annotations

from src.arcanum.core.scope import (
    EngineScope,
    get_active_manuscript,
    get_active_universe,
    get_active_world,
    resolve_manuscript_dir,
    resolve_manuscript_path,
    resolve_universe_dir,
    resolve_universe_path,
    resolve_world_dir,
    resolve_world_path,
)

__all__ = [
    "EngineScope",
    "get_active_manuscript",
    "get_active_universe",
    "get_active_world",
    "resolve_manuscript_dir",
    "resolve_manuscript_path",
    "resolve_universe_dir",
    "resolve_universe_path",
    "resolve_world_dir",
    "resolve_world_path",
]
