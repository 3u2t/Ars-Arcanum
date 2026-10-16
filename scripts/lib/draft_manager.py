#!/usr/bin/env python3
"""Ars Arcanum Manuscript Draft Versioning & Lineage Manager (scripts/lib/draft_manager.py).

Delegated wrapper for native `src.arcanum.manuscript.drafts`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.manuscript.drafts as _native  # noqa: E402, F401
from src.arcanum.manuscript.drafts import (  # noqa: E402
    WINDOWS_RESERVED_NAMES,
    ChapterInfo,
    DraftInfo,
    DraftManager,
    activate_draft,
    fork_draft,
    get_draft_status,
    list_drafts,
    lock_draft,
    main,
    set_milestone,
    set_notes,
    unlock_draft,
    validate_volume_name,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("draft_manager", "lib.draft_manager", "scripts.lib.draft_manager"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "WINDOWS_RESERVED_NAMES",
    "ChapterInfo",
    "DraftInfo",
    "DraftManager",
    "activate_draft",
    "fork_draft",
    "get_draft_status",
    "list_drafts",
    "lock_draft",
    "main",
    "set_milestone",
    "set_notes",
    "unlock_draft",
    "validate_volume_name",
]

if __name__ == "__main__":
    raise SystemExit(main())
