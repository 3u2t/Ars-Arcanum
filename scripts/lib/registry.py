#!/usr/bin/env python3
"""
Ars Arcanum Engine & Plugin Registry (scripts/lib/registry.py)
============================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.registry.
"""

from __future__ import annotations

import sys

from src.arcanum.core.registry import (
    _ENGINES,
    ALL_ENGINES,
    AdvisoryResolution,
    BaseCraftEngine,
    DiagnosticSeverity,
    EngineCategory,
    EngineSpec,
    _load_doc_theory_references,
    disable_engine,
    discover_craft_plugins,
    discover_user_plugins,
    enable_engine,
    format_engine_doc,
    format_unified_bibliography,
    get_all_engine_docs,
    get_core_engines,
    get_craft_engines,
    get_engine,
    get_engine_catalog,
    get_engine_docs,
    get_engine_tips,
    get_registry,
    get_unified_bibliography,
    is_engine_enabled,
    list_engines,
    load_engine_module,
    load_user_plugin,
    register_user_engine,
    reset_registry,
    search_engine_docs,
)

for _alias in ("registry", "lib.registry", "scripts.lib.registry"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = [
    "ALL_ENGINES",
    "AdvisoryResolution",
    "BaseCraftEngine",
    "DiagnosticSeverity",
    "EngineCategory",
    "EngineSpec",
    "_ENGINES",
    "_load_doc_theory_references",
    "disable_engine",
    "discover_craft_plugins",
    "discover_user_plugins",
    "enable_engine",
    "format_engine_doc",
    "format_unified_bibliography",
    "get_all_engine_docs",
    "get_core_engines",
    "get_craft_engines",
    "get_engine",
    "get_engine_catalog",
    "get_engine_docs",
    "get_engine_tips",
    "get_registry",
    "get_unified_bibliography",
    "is_engine_enabled",
    "list_engines",
    "load_engine_module",
    "load_user_plugin",
    "register_user_engine",
    "reset_registry",
    "search_engine_docs",
]
