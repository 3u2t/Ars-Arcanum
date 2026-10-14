# Codebase Architecture & Internal Data Flow (`docs/codebase/ARCHITECTURE.md`)

- **`src/arcanum/core/` (`scripts/lib/vault_index.py`, `typed_constitution.py`, `plugin_sandbox.py`, `fs_utils.py`, `lockfile.py`)**: Transactional I/O, path confinement (`is_safe_subpath`), mtime-keyed `VaultIndex` (`CACHE_VERSION = 3`), frozen `@dataclass` policy cascades, and isolated plugin execution.
- **`src/arcanum/manuscript/` (`scripts/lib/diff_core.py`, `phase_effort_engine.py`, `narrative_braid.py`)**: Two-level SHA-256 paragraph-hash diffing, hardlinked draft promotion, Phase-Aware Effort telemetry, and SVG narrative braid generation.
- **`src/arcanum/worldbible/` (`scripts/lib/epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `vault_continuity_runner.py`)**: Deterministic continuity compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`) and the live `_Arcanum_Diagnostics.md` Obsidian bridge.
- **`src/arcanum/publishing/` (`scripts/lib/docx_tracked_changes.py`, `publisher.py`, `omnibus.py`, `preflight.py`)**: ElementTree DOM OpenXML generation, CriticMarkup <-> Word Tracked Changes synchronization, and Typst/Pandoc compilation.


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
