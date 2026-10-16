#!/usr/bin/env python3
"""Ars Arcanum Pre-Flight Typesetting & Publishing Compliance Linter (scripts/lib/preflight.py).

Delegated wrapper for native `src.arcanum.publishing.preflight`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.publishing.preflight as _native  # noqa: E402, F401
from src.arcanum.publishing.preflight import (  # noqa: E402
    check_cover_and_assets,
    check_metadata,
    generate_preflight_html_report,
    main,
    run_preflight_linter,
    validate_chapter_formatting,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("preflight", "lib.preflight", "scripts.lib.preflight"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = [
    "check_cover_and_assets",
    "check_metadata",
    "generate_preflight_html_report",
    "main",
    "run_preflight_linter",
    "validate_chapter_formatting",
]

if __name__ == "__main__":
    main()
