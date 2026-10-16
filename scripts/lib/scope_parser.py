#!/usr/bin/env python3
"""
Ars Arcanum Scope Parser & CLI Helpers (scripts/lib/scope_parser.py)
===================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.scope.
"""

from __future__ import annotations

from src.arcanum.core.scope import (
    EngineScope,
    ResolvedScope,
    add_scope_arguments,
    format_scope_banner,
    parse_identifier_list,
    parse_number_ranges,
    parse_scope_args,
    parse_unified_scope_string,
)

__all__ = [
    "EngineScope",
    "ResolvedScope",
    "add_scope_arguments",
    "format_scope_banner",
    "parse_identifier_list",
    "parse_number_ranges",
    "parse_scope_args",
    "parse_unified_scope_string",
]
