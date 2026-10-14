# Changelog

All notable changes to **Ars Arcanum** are documented in this file.
This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [0.1.0] - 2026-10-14

### Added
- **Phase 1 Unified VaultIndex DAL (`scripts/lib/vault_index.py`)**: Thread-safe, mtime-keyed `VaultIndex` (`CACHE_VERSION = 3`) with `is_safe_subpath` path-traversal defense, `atomic_write` hardlink-safe replacement, multiline YAML block-scalar (`|`, `>`) frontmatter parsing, literary multi-paragraph dialogue telemetry, code-fence-safe wikilink extraction, and 16-char SHA-256 paragraph hashing (`arcanum vault-index`).
- **Feature 1 — Phase-Aware Effort & Career Velocity Engine (`scripts/lib/phase_effort_engine.py`)**: Implements all 9 canonical project stages (`Concept` through `Publishing`), Phase-Aware Effort Multipliers (`1.00x` First Draft and on-stage Outlining, `0.50x` Worldbuilding and off-phase Outlining, `0.20x` Revision-stage edits, and `0.00x` off-phase Revision block to prevent premature editing), 2,000-point daily goal, 730,000-word annual target, and 15,000,000-word career milestone forecasting (`arcanum sprint-effort` / `arcanum effort`).
- **Feature 2 — Epistemic POV & Spoiler Firewall (`scripts/lib/epistemic_firewall.py`)**: Chronological DAG solver auditing character knowledge baselines (`knows:`) against chapter reveals (`learns:`) and references (`references:`) to flag premature spoiler leaks (`EPI-201`), unframed mythic lore (`EPI-202`), and orphan reveals (`EPI-203`) (`arcanum validate-epistemic` / `arcanum epistemic`).
- **Feature 3 — Custom Planetary Calendar & Biome Route Physics Solver (`scripts/lib/timeline_solver.py`)**: Audits non-Gregorian calendar dates from `world.yaml`, overland/sea/air route distances and terrain friction (`sand_sea`, `mountain_pass`) from `Locations/`, and Lorentz relativistic proper-time dilation (`TIME-301`, `TIME-302`) (`arcanum timeline-audit` / `arcanum timeline-solver`).
- **Feature 4 — PolyGlot Conlang Lexicon Importer & Phonotactic Linter (`scripts/lib/conlang_linter.py`)**: Zero-dependency `.pgd` (ZIP/XML) and `.xml` lexicon importer, phonotactic phoneme/cluster/vowel-hiatus validator (`CON-401`, `CON-402`), and Omnibus IPA pronunciation glossary compiler (`arcanum conlang-check` / `arcanum conlang-linter`).
- **Feature 5 — Hard Magic & Sci-Fi Resource Conservation Ledger (`scripts/lib/resource_ledger.py`)**: Audits finite entity resource pools (`ether_vials`, `mana`, `ammunition`, `delta_v`) across chapter `state_delta` transitions, flagging negative depletion deficits (`LED-501`) and capacity overflows (`LED-502`) (`arcanum ledger-audit` / `arcanum resource-ledger`).
- **Feature 6 — Interactive Narrative Braid & POV Drought Visualizer (`scripts/lib/narrative_braid.py`)**: Computes POV word-share percentages, detects character/subplot absences exceeding threshold words (`BRD-601`), and renders an offline, CSP-locked HTML + SVG swimlane braid matrix (`arcanum braid` / `arcanum narrative-braid`).
- **Phase 4 Unified Vault Continuity Runner & Obsidian Live Callout Bridge (`scripts/lib/vault_continuity_runner.py`)**: End-to-end vault scanner (`arcanum continuity-suite` / `arcanum obsidian-dashboard`) that executes all continuity compilers in one pass and writes `_Arcanum_Diagnostics.md` with native Obsidian callouts.
- **Phase 2 & 3 Architectural Refactor Modules**:
  - `scripts/lib/diff_core.py` (`arcanum diff-fast`)
  - `scripts/lib/typed_constitution.py` (`arcanum typed-constitution`)
  - `scripts/lib/docx_tracked_changes.py` (`arcanum docx-tracked`)
  - `scripts/lib/plugin_sandbox.py` (`arcanum plugin-sandbox`)
  - `src/arcanum/` layered subpackage hierarchy (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).
