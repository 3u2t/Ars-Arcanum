"""Shared Hierarchical Paragraph-Hash Diff Engine & Hardlink Draft Promotion (Phase 2A Refactor).

Eliminates duplicated $O(N^2)$ diff pipelines across `scripts/lib/manuscript_diff.py` and
`scripts/lib/revision_heatmap.py`, and replaces slow recursive directory copies in
`scripts/lib/draft_manager.py` with physical disk copies (`shutil.copy2`) ensuring
inode separation and read-only parent locking.

Repository Target: `scripts/lib/diff_core.py`
Delegates core implementation to `src.arcanum.manuscript.diff`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("diff_core", "lib.diff_core", "scripts.lib.diff_core"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.manuscript.diff import (  # noqa: E402
    ChapterDiffReport,
    DraftLineageRecord,
    ParagraphDelta,
    compare_chapter_hierarchical,
    compare_draft_directories,
    get_draft_history,
    get_draft_lineage,
    main,
    parse_frontmatter,
    promote_draft_hardlinked,
)

__all__ = [
    "ChapterDiffReport",
    "DraftLineageRecord",
    "ParagraphDelta",
    "compare_chapter_hierarchical",
    "compare_draft_directories",
    "get_draft_history",
    "get_draft_lineage",
    "main",
    "parse_frontmatter",
    "promote_draft_hardlinked",
]

if __name__ == "__main__":
    raise SystemExit(main())
