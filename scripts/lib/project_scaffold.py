#!/usr/bin/env python3
"""Ars Arcanum Project Lifecycle & Scaffolding Engine (scripts/lib/project_scaffold.py).

Delegated wrapper for native `src.arcanum.manuscript.scaffold`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.manuscript.scaffold as _native  # noqa: E402, F401
from src.arcanum.manuscript.scaffold import (  # noqa: E402
    CONSTITUTION_PRESETS,
    STRUCTURE_PRESETS,
    get_constitution_preset,
    get_manuscripts_base,
    get_universes_base,
    list_manuscripts,
    list_universes,
    list_worlds,
    main,
    resolve_structure_layout,
    run_interactive_wizard,
    scaffold_manuscript,
    scaffold_novella,
    scaffold_serial,
    scaffold_universe,
    scaffold_volume,
    scaffold_world,
)

# Register aliases into sys.modules so imports and patches work seamlessly
for _alias in ("project_scaffold", "lib.project_scaffold", "scripts.lib.project_scaffold"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "CONSTITUTION_PRESETS",
    "STRUCTURE_PRESETS",
    "get_constitution_preset",
    "get_manuscripts_base",
    "get_universes_base",
    "list_manuscripts",
    "list_universes",
    "list_worlds",
    "main",
    "resolve_structure_layout",
    "run_interactive_wizard",
    "scaffold_manuscript",
    "scaffold_novella",
    "scaffold_serial",
    "scaffold_universe",
    "scaffold_volume",
    "scaffold_world",
]

if __name__ == "__main__":
    sys.exit(main())
