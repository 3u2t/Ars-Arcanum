"""Manuscript diffing, draft hardlinking, phase-aware effort, and narrative braid engines."""

from __future__ import annotations

from scripts.lib.audit_hardening import normalize_cjk_and_unicode_prose, sanitize_critic_markup
from scripts.lib.diff_core import (
    ChapterDiffReport,
    ParagraphDelta,
    compare_chapter_hierarchical,
    promote_draft_hardlinked,
)
from scripts.lib.narrative_braid import ChapterBraidNode, analyze_narrative_braid, render_braid_html
from scripts.lib.phase_effort_engine import (
    BookProjectSpec,
    EffortMultiplierConfig,
    PhaseEffortLedger,
    ProjectStage,
    evaluate_session_effort,
)

__all__ = [
    "BookProjectSpec",
    "ChapterBraidNode",
    "ChapterDiffReport",
    "EffortMultiplierConfig",
    "ParagraphDelta",
    "PhaseEffortLedger",
    "ProjectStage",
    "analyze_narrative_braid",
    "compare_chapter_hierarchical",
    "evaluate_session_effort",
    "normalize_cjk_and_unicode_prose",
    "promote_draft_hardlinked",
    "render_braid_html",
    "sanitize_critic_markup",
]
