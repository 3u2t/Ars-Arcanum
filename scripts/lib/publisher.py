#!/usr/bin/env python3
"""Ars Arcanum Sovereign Typesetting & Publication Pipeline (scripts/lib/publisher.py).

Delegated wrapper for native `src.arcanum.publishing.publisher`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.publishing.publisher as _native  # noqa: E402, F401
from src.arcanum.publishing.publisher import (  # noqa: E402
    collect_manuscript_content,
    compile_docx,
    compile_pandoc_epub,
    compile_typst_pdf,
    escape_typst_text,
    find_tool,
    get_manuscript_metadata,
    main,
    publish_manuscript,
    resolve_prose_for_publication,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("publisher", "lib.publisher", "scripts.lib.publisher"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "collect_manuscript_content",
    "compile_docx",
    "compile_pandoc_epub",
    "compile_typst_pdf",
    "escape_typst_text",
    "find_tool",
    "get_manuscript_metadata",
    "main",
    "publish_manuscript",
    "resolve_prose_for_publication",
]

if __name__ == "__main__":
    sys.exit(main())
