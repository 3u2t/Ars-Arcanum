#!/usr/bin/env python3
"""
Ars Arcanum Engine & Plugin Registry Base (scripts/lib/registry_base.py)
========================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.registry.
"""

from __future__ import annotations

import sys

from src.arcanum.core.registry.base import (
    AdvisoryResolution,
    BaseCraftEngine,
    DiagnosticSeverity,
    EngineCategory,
    EngineSpec,
    _load_doc_theory_references,
)

for _alias in ("registry_base", "lib.registry_base", "scripts.lib.registry_base"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = [
    "AdvisoryResolution",
    "BaseCraftEngine",
    "DiagnosticSeverity",
    "EngineCategory",
    "EngineSpec",
    "_load_doc_theory_references",
]
