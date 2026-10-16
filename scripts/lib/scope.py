#!/usr/bin/env python3
"""
Ars Arcanum Scope & Granular Target Resolution Engine (scripts/lib/scope.py)
===========================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.scope.
"""

from __future__ import annotations

import sys

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
    add_scope_arguments,
    extract_scenes_from_text,
    filter_manuscript_scope,
    filter_world_scope,
    format_scope_banner,
    get_active_manuscript,
    get_active_universe,
    get_active_world,
    main,
    parse_identifier_list,
    parse_number_ranges,
    parse_scope_args,
    parse_unified_scope_string,
    resolve_manuscript_dir,
    resolve_manuscript_path,
    resolve_scope,
    resolve_universe_dir,
    resolve_universe_path,
    resolve_world_dir,
    resolve_world_path,
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
    "add_scope_arguments",
    "extract_scenes_from_text",
    "filter_manuscript_scope",
    "filter_world_scope",
    "format_scope_banner",
    "get_active_manuscript",
    "get_active_universe",
    "get_active_world",
    "main",
    "parse_identifier_list",
    "parse_number_ranges",
    "parse_scope_args",
    "parse_unified_scope_string",
    "resolve_manuscript_dir",
    "resolve_manuscript_path",
    "resolve_scope",
    "resolve_universe_dir",
    "resolve_universe_path",
    "resolve_world_dir",
    "resolve_world_path",
]

if __name__ == "__main__":
    sys.exit(main())
