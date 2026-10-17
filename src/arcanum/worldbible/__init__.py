"""Worldbuilding continuity compilers and Obsidian diagnostics runner."""

from __future__ import annotations

from scripts.lib.audit_hardening import (
    import_polyglot_lexicon_hardened,
    run_lite_continuity_check,
)
from src.arcanum.worldbible.conlang import (
    ConlangLexeme,
    PhonotacticSpec,
    audit_conlang_terms,
    compile_glossary_markdown,
    import_polyglot_lexicon,
)
from scripts.lib.epistemic_firewall import (
    ChapterEpistemicEvent,
    CharacterKnowledgeBaseline,
    audit_epistemic_continuity,
    audit_vault_epistemic,
)
from scripts.lib.resource_ledger import (
    ChapterResourceDelta,
    ResourcePoolSpec,
    audit_resource_conservation,
    audit_vault_resources,
)
from src.arcanum.worldbible.timeline import (
    CharacterTimelineEvent,
    CustomCalendarSpec,
    RouteEdge,
    audit_timeline_and_routes,
    audit_vault_timeline,
    compute_relativistic_proper_days,
)
from scripts.lib.vault_continuity_runner import (
    render_obsidian_diagnostics_markdown,
    run_full_vault_continuity_suite,
)
from src.arcanum.worldbible.visualizers import (
    export_etymology_tree_html,
    export_orbital_calendar_html,
    render_etymology_tree_svg,
    render_orbital_calendar_svg,
    wrap_svg_in_standalone_html,
)

__all__ = [
    "ChapterEpistemicEvent",
    "ChapterResourceDelta",
    "CharacterKnowledgeBaseline",
    "CharacterTimelineEvent",
    "ConlangLexeme",
    "CustomCalendarSpec",
    "PhonotacticSpec",
    "ResourcePoolSpec",
    "RouteEdge",
    "audit_conlang_terms",
    "audit_epistemic_continuity",
    "audit_resource_conservation",
    "audit_timeline_and_routes",
    "audit_vault_epistemic",
    "audit_vault_resources",
    "audit_vault_timeline",
    "compile_glossary_markdown",
    "compute_relativistic_proper_days",
    "export_etymology_tree_html",
    "export_orbital_calendar_html",
    "import_polyglot_lexicon",
    "import_polyglot_lexicon_hardened",
    "render_etymology_tree_svg",
    "render_obsidian_diagnostics_markdown",
    "render_orbital_calendar_svg",
    "run_full_vault_continuity_suite",
    "run_lite_continuity_check",
    "wrap_svg_in_standalone_html",
]
