#!/usr/bin/env python3
"""Ars Arcanum Pure-Python Standalone Restore Engine (scripts/lib/restore.py).

Delegated wrapper for native `src.arcanum.core.restore`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.core.restore as _native  # noqa: E402, F401
from src.arcanum.core.restore import (  # noqa: E402
    compute_file_sha256,
    is_safe_tar_member,
    main,
    restore_archive,
    restore_backup,
    verify_archive_checksum,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("restore", "lib.restore", "scripts.lib.restore"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "compute_file_sha256",
    "is_safe_tar_member",
    "main",
    "restore_archive",
    "restore_backup",
    "verify_archive_checksum",
]

if __name__ == "__main__":
    raise SystemExit(main())
