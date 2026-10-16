#!/usr/bin/env python3
"""Ars Arcanum Pure-Python Snapshot & Version Milestone Engine (scripts/lib/snapshot.py).

Delegated wrapper for native `src.arcanum.core.snapshot`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.core.snapshot as _native  # noqa: E402, F401
from src.arcanum.core.snapshot import (  # noqa: E402
    main,
    save_snapshot,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("snapshot", "lib.snapshot", "scripts.lib.snapshot"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "main",
    "save_snapshot",
]

if __name__ == "__main__":
    raise SystemExit(main())
