#!/usr/bin/env python3
"""Ars Arcanum Multi-Volume Series Omnibus Compiler (scripts/lib/omnibus.py).

Delegated wrapper for native `src.arcanum.publishing.omnibus`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.publishing.omnibus as _native  # noqa: E402, F401
from src.arcanum.publishing.omnibus import (  # noqa: E402
    VolumeData,
    compile_omnibus_manuscript,
    discover_series_volumes,
    generate_omnibus_html_reader,
    main,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("omnibus", "lib.omnibus", "scripts.lib.omnibus"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = [
    "VolumeData",
    "compile_omnibus_manuscript",
    "discover_series_volumes",
    "generate_omnibus_html_reader",
    "main",
]

if __name__ == "__main__":
    main()
