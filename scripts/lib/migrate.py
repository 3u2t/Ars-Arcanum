#!/usr/bin/env python3
"""
Ars Arcanum Schema & Project Migration Engine (scripts/lib/migrate.py)
=====================================================================
Legacy compatibility facade delegating to src.arcanum.core.migrate.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.arcanum.core.migrate import (  # noqa: E402
    CURRENT_SCHEMA_VERSION,
    REQUIRED_GITIGNORE_ENTRIES,
    ensure_gitignore_entries,
    main,
    migrate_manuscript,
    migrate_project,
    migrate_universe,
    migrate_world,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "REQUIRED_GITIGNORE_ENTRIES",
    "ensure_gitignore_entries",
    "main",
    "migrate_manuscript",
    "migrate_project",
    "migrate_universe",
    "migrate_world",
]

if __name__ == "__main__":
    main()
