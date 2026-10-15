# Repository Directory & Module Structure (`docs/codebase/STRUCTURE.md`)

- **`scripts/lib/` (64 Python Modules)**: Contains all zero-dependency core, manuscript, worldbuilding, and publishing engines, including the 12 Phase 1–4 modules (`vault_index.py`, `phase_effort_engine.py`, `diff_core.py`, `typed_constitution.py`, `docx_tracked_changes.py`, `plugin_sandbox.py`, `epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `narrative_braid.py`, `vault_continuity_runner.py`).
- **`src/arcanum/`**: Layered subpackage hierarchy (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).
- **`tests/`**: 58 stdlib `unittest` suites verifying every invariant, CLI command, and documentation contract.


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
