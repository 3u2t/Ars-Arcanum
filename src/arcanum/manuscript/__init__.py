"""Manuscript diffing, draft hardlinking, phase-aware effort, and narrative braid engines."""
from scripts.lib.diff_core import ChapterDiffReport, ParagraphDelta, compare_chapter_hierarchical, promote_draft_hardlinked
from scripts.lib.phase_effort_engine import BookProjectSpec, EffortMultiplierConfig, PhaseEffortLedger, ProjectStage, evaluate_session_effort
from scripts.lib.narrative_braid import ChapterBraidNode, analyze_narrative_braid, render_braid_html

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
    "promote_draft_hardlinked",
    "render_braid_html",
]
