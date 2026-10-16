"""Worldbuilding continuity compilers, lore codex exporter, and Obsidian diagnostics runner."""

from __future__ import annotations

from src.arcanum.core.hardening import (
    import_polyglot_lexicon_hardened,
    run_lite_continuity_check,
)
from src.arcanum.worldbible.codex import (
    TAXONOMIES,
    build_single_file_codex,
    convert_markdown_to_basic_html,
    convert_markdown_to_styled_html,
    render_codex_html,
    scan_world_vault,
)
from src.arcanum.worldbible.conlang import (
    ConlangLexeme,
    ConlangViolation,
    PhonotacticSpec,
    audit_conlang_terms,
    compile_glossary_markdown,
    import_polyglot_lexicon,
    render_etymology_tree_svg,
    validate_word_phonotactics,
)
from src.arcanum.worldbible.constitution import (
    AuthorialConstitution,
    CraftPolicyThresholds,
    load_yaml_constitution_file,
    merge_rule_lists_with_negation,
    resolve_constitution_cascade,
)
from src.arcanum.worldbible.epistemics import (
    ChapterEpistemicEvent,
    CharacterKnowledgeBaseline,
    EpistemicAuditReport,
    EpistemicViolation,
    audit_epistemic_continuity,
    audit_vault_epistemic,
)
from src.arcanum.worldbible.ledger import (
    ChapterResourceDelta,
    LedgerViolation,
    ResourcePoolSpec,
    audit_resource_conservation,
    audit_vault_resources,
)
from src.arcanum.worldbible.runner import (
    render_obsidian_diagnostics_markdown,
    run_full_vault_continuity_suite,
)
from src.arcanum.worldbible.timeline import (
    CharacterTimelineEvent,
    CustomCalendarSpec,
    DEFAULT_MODE_SPEED_KMPD,
    DEFAULT_TERRAIN_MULTIPLIER,
    RouteEdge,
    TimelineAnomaly,
    audit_timeline_and_routes,
    audit_vault_timeline,
    compute_relativistic_proper_days,
    compute_shortest_travel_days,
    render_orbital_calendar_svg,
)
from src.arcanum.worldbible.visualizers import (
    export_etymology_tree_html,
    export_orbital_calendar_html,
    wrap_svg_in_standalone_html,
)

__all__ = [
    "AuthorialConstitution",
    "ChapterEpistemicEvent",
    "ChapterResourceDelta",
    "CharacterKnowledgeBaseline",
    "CharacterTimelineEvent",
    "ConlangLexeme",
    "ConlangViolation",
    "CraftPolicyThresholds",
    "CustomCalendarSpec",
    "DEFAULT_MODE_SPEED_KMPD",
    "DEFAULT_TERRAIN_MULTIPLIER",
    "EpistemicAuditReport",
    "EpistemicViolation",
    "LedgerViolation",
    "PhonotacticSpec",
    "ResourcePoolSpec",
    "RouteEdge",
    "TAXONOMIES",
    "TimelineAnomaly",
    "audit_conlang_terms",
    "audit_epistemic_continuity",
    "audit_resource_conservation",
    "audit_timeline_and_routes",
    "audit_vault_epistemic",
    "audit_vault_resources",
    "audit_vault_timeline",
    "build_single_file_codex",
    "compile_glossary_markdown",
    "compute_relativistic_proper_days",
    "compute_shortest_travel_days",
    "convert_markdown_to_basic_html",
    "convert_markdown_to_styled_html",
    "export_etymology_tree_html",
    "export_orbital_calendar_html",
    "import_polyglot_lexicon",
    "import_polyglot_lexicon_hardened",
    "load_yaml_constitution_file",
    "merge_rule_lists_with_negation",
    "render_codex_html",
    "render_etymology_tree_svg",
    "render_obsidian_diagnostics_markdown",
    "render_orbital_calendar_svg",
    "resolve_constitution_cascade",
    "run_full_vault_continuity_suite",
    "run_lite_continuity_check",
    "scan_world_vault",
    "validate_word_phonotactics",
    "wrap_svg_in_standalone_html",
]
