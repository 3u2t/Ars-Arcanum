#!/usr/bin/env python3
"""Bidirectional CriticMarkup <-> OpenXML Word Tracked Changes Bridge (scripts/lib/docx_tracked_changes.py).

Delegated wrapper for native `src.arcanum.publishing.docx`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.publishing.docx as _native  # noqa: E402, F401
from src.arcanum.publishing.docx import (  # noqa: E402
    build_tracked_document_xml,
    export_markdown_to_docx,
    main,
    pull_docx_to_markdown,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("docx_tracked_changes", "lib.docx_tracked_changes", "scripts.lib.docx_tracked_changes"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = [
    "build_tracked_document_xml",
    "export_markdown_to_docx",
    "main",
    "pull_docx_to_markdown",
]

if __name__ == "__main__":
    raise SystemExit(main())
