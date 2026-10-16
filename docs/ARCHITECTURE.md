# Ars Arcanum System Architecture Blueprint

## 1. Executive Architectural Overview

Ars Arcanum is structured around a strict **Three-Subsystem Epistemic Architecture** ([ADR-0001](adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md)) backed by a zero-dependency Python `>=3.10` standard library core:

| Subsystem | Epistemic Role | Core Modules (`scripts/lib/` & `src/arcanum/`) | Enforcement Mode |
| :--- | :--- | :--- | :--- |
| **Subsystem 1: Deterministic Invariants & Continuity Compilers** | Verifies objective mathematical, chronological, linguistic, and epistemic facts plus transactional file safety. | `vault_index.py`, `fs_utils.py`, `lockfile.py`, `backup.py`, `plugin_sandbox.py`, `epistemic_firewall.py` (`EPI-*`), `timeline_solver.py` (`TIME-*`), `conlang_linter.py` (`CON-*`), `resource_ledger.py` (`LED-*`) | Strict exit codes (`0` pass, `1` violation) |
| **Subsystem 2: Descriptive Telemetry & Craft Analytics** | Measures writing velocity, phase-weighted effort, dialogue ratios, revision churn, and POV pacing without prescriptive dogma. | `phase_effort_engine.py`, `word_counter.py`, `writing_sprint.py`, `diff_core.py`, `manuscript_diff.py`, `revision_heatmap.py` (`REV-*`), `narrative_braid.py` (`BRD-*`), `portfolio.py` | Neutral JSON/HTML/SVG telemetry |
| **Subsystem 3: Authorial Governance & Workspace Integration** | Cascades user-defined policy rules, synchronizes with Obsidian/Word/Typst/Pandoc, and renders live vault dashboards. | `typed_constitution.py`, `constitution.py`, `config.py`, `docx_tracked_changes.py`, `publisher.py`, `omnibus.py`, `codex_export.py`, `vault_continuity_runner.py` | User-controlled via `constitution.yaml` (`!RULE_ID`) |


<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1–4 Production CLI & Continuity Cross-Reference

- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
