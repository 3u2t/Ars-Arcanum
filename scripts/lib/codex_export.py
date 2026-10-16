"""Ars Arcanum Static World Wiki & Lore Codex Exporter (scripts/lib/codex_export.py).

Zero-dependency, offline static site generator compiling Obsidian World Bibles
into a sovereign, searchable encyclopedia and reader codex.

Repository Target: `scripts/lib/codex_export.py`
Delegates implementation to `src.arcanum.worldbible.codex`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("codex_export", "lib.codex_export", "scripts.lib.codex_export"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.codex import (  # noqa: E402
    TAXONOMIES,
    build_single_file_codex,
    convert_markdown_to_basic_html,
    convert_markdown_to_styled_html,
    main,
    render_codex_html,
    scan_world_vault,
)

# Backward-compatibility aliases
_md_to_styled_html = convert_markdown_to_styled_html
_md_to_basic_html = convert_markdown_to_basic_html

__all__ = [
    "TAXONOMIES",
    "_md_to_basic_html",
    "_md_to_styled_html",
    "build_single_file_codex",
    "convert_markdown_to_basic_html",
    "convert_markdown_to_styled_html",
    "main",
    "render_codex_html",
    "scan_world_vault",
]

if __name__ == "__main__":
    raise SystemExit(main())
