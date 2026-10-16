#!/usr/bin/env python3
"""Ars Arcanum Manuscript Batch Importer & Migration Engine (scripts/lib/importer.py).

Delegated wrapper for native `src.arcanum.manuscript.importer`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.manuscript.importer as _native  # noqa: E402, F401
from src.arcanum.manuscript.importer import (  # noqa: E402
    NWX_TEMPLATE,
    EpubImporter,
    HtmlToMarkdownConverter,
    ScrivenerImporter,
    convert_html_to_markdown,
    extract_docx_text,
    import_manuscript_batch,
    main,
    resolve_sequential_draft,
    rtf_to_text,
    split_monolithic_by_headings,
    standardize_chapter_frontmatter,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("importer", "lib.importer", "scripts.lib.importer"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "NWX_TEMPLATE",
    "EpubImporter",
    "HtmlToMarkdownConverter",
    "ScrivenerImporter",
    "convert_html_to_markdown",
    "extract_docx_text",
    "import_manuscript_batch",
    "main",
    "resolve_sequential_draft",
    "rtf_to_text",
    "split_monolithic_by_headings",
    "standardize_chapter_frontmatter",
]

if __name__ == "__main__":
    raise SystemExit(main())
