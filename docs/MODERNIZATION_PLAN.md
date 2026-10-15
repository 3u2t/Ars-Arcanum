# Ars Arcanum Modernization & Architecture Completion Plan (Phases 1–4)

1. **Phase 1 — Unified `VaultIndex` DAL & Layered Package Tree (`src/arcanum/`)**: Consolidated scattered `rglob("*.md")` loops into `scripts/lib/vault_index.py` (`CACHE_VERSION = 3`) with YAML block-scalar (`|`, `>`) and multi-paragraph dialogue support.
2. **Phase 2 — Hierarchical Diffing, Hardlink Drafts & Strict Typed Constitution**: Added `scripts/lib/diff_core.py` (`arcanum diff-fast`), `scripts/lib/typed_constitution.py` (`arcanum typed-constitution`), and strict per-module Mypy typing in `mypy.ini`.
3. **Phase 3 — OpenXML Tracked Changes DOM Bridge & Subprocess Plugin Sandbox**: Added `scripts/lib/docx_tracked_changes.py` (`arcanum docx-tracked`) and `scripts/lib/plugin_sandbox.py` (`arcanum plugin-sandbox`).
4. **Phase 4 — Six Deterministic Continuity Engines & Live Obsidian Callout Bridge**: Added `phase_effort_engine.py`, `epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `narrative_braid.py`, and `vault_continuity_runner.py` (`_Arcanum_Diagnostics.md`).
5. **Phase 5 — Production Audit Hardening, 3-Tier Documentation & Obsidian Lite Mode**: Added `scripts/lib/audit_hardening.py`, `src/arcanum/cli_bridge.py`, 3-tier documentation index (`docs/INDEX.md`, `docs/LITE_MODE.md`), SHA-pinned CI (`.github/workflows/narrative-continuity-ci.yml`), and fuzz-test coverage (`tests/test_audit_fuzz_hardening.py`).

<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1-4 Production CLI & Continuity Cross-Reference

- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
