#!/usr/bin/env python3
"""Ars Arcanum Manuscript Revision Density & Churn Heatmap Engine (scripts/lib/revision_heatmap.py).

Delegated wrapper for native `src.arcanum.manuscript.heatmap`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.manuscript.heatmap as _native  # noqa: E402, F401
from src.arcanum.manuscript.heatmap import (  # noqa: E402
    _CSP,
    _FLAG_LABELS,
    ChapterRevisionStats,
    _bar_width,
    _churn_color,
    analyze_revision_churn,
    clean_prose_lines,
    count_words,
    diff_line_counts,
    diff_word_counts,
    extract_dialogue_and_prose,
    extract_sub_scenes,
    generate_revision_heatmap_html,
    main,
    scan_manuscript_snapshots,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("revision_heatmap", "lib.revision_heatmap", "scripts.lib.revision_heatmap"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "_CSP",
    "_FLAG_LABELS",
    "ChapterRevisionStats",
    "_bar_width",
    "_churn_color",
    "analyze_revision_churn",
    "clean_prose_lines",
    "count_words",
    "diff_line_counts",
    "diff_word_counts",
    "extract_dialogue_and_prose",
    "extract_sub_scenes",
    "generate_revision_heatmap_html",
    "main",
    "scan_manuscript_snapshots",
]

if __name__ == "__main__":
    main()
