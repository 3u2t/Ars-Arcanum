#!/usr/bin/env python3
"""Ars Arcanum Pure-Python Standalone Backup Engine (scripts/lib/backup.py).

Delegated wrapper for native `src.arcanum.core.backup`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.core.backup as _native  # noqa: E402, F401
from src.arcanum.core.backup import (  # noqa: E402
    BACKUP_VERSION,
    EXCLUDE_PATTERNS,
    compute_file_sha256,
    create_backup,
    detect_target_type,
    list_backups,
    main,
    resolve_backup_destination,
    should_exclude,
    verify_backup_integrity,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("backup", "lib.backup", "scripts.lib.backup"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "BACKUP_VERSION",
    "EXCLUDE_PATTERNS",
    "compute_file_sha256",
    "create_backup",
    "detect_target_type",
    "list_backups",
    "main",
    "resolve_backup_destination",
    "should_exclude",
    "verify_backup_integrity",
]

if __name__ == "__main__":
    raise SystemExit(main())
