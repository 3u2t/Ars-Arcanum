#!/usr/bin/env python3
"""
Ars Arcanum Scope Models & Dataclasses (scripts/lib/scope_models.py)
===================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.scope.
"""

from __future__ import annotations

from src.arcanum.core.scope import (
    EXCLUDED_DIRS,
    FRONTMATTER_REGEX,
    LORE_CATEGORIES,
    SCENE_BREAK_REGEX,
    TAG_REGEX,
    ChapterItem,
    EngineScope,
    LoreItem,
    ResolvedScope,
    SceneSlice,
)

__all__ = [
    "EXCLUDED_DIRS",
    "FRONTMATTER_REGEX",
    "LORE_CATEGORIES",
    "SCENE_BREAK_REGEX",
    "TAG_REGEX",
    "ChapterItem",
    "EngineScope",
    "LoreItem",
    "ResolvedScope",
    "SceneSlice",
]
