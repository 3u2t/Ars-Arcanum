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
from src.arcanum.manuscript.drafts import (
    DraftManager,
    list_drafts,
)
from src.arcanum.manuscript.heatmap import analyze_revision_churn
from src.arcanum.manuscript.importer import import_manuscript_batch
from src.arcanum.manuscript.velocity import start_sprint
from src.arcanum.manuscript.word_counter import (
    analyze_manuscript_words,
    count_prose_words_advanced,
    count_words_prose,
    format_ansi_velocity,
    format_words_markdown,
    format_words_table,
)

__all__ = [
    "BookProjectSpec",
    "ChapterBraidNode",
    "ChapterDiffReport",
    "DraftManager",
    "EffortMultiplierConfig",
    "ParagraphDelta",
    "PhaseEffortLedger",
    "ProjectStage",
    "analyze_manuscript_words",
    "analyze_narrative_braid",
    "analyze_revision_churn",
    "compare_chapter_hierarchical",
    "count_prose_words_advanced",
    "count_words_prose",
    "evaluate_session_effort",
    "format_ansi_velocity",
    "format_words_markdown",
    "format_words_table",
    "import_manuscript_batch",
    "list_drafts",
    "normalize_cjk_and_unicode_prose",
    "promote_draft_hardlinked",
    "render_braid_html",
    "sanitize_critic_markup",
    "start_sprint",
]
