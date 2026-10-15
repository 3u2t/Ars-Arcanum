# Changelog

All notable changes to **Ars Arcanum** are documented in this file.
This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [0.1.0] - 2026-10-15

### Added
- **Phase 5 Audit Hardening & Obsidian Lite Mode (`scripts/lib/audit_hardening.py`, `src/arcanum/cli_bridge.py`)**: Bounded ZIP/XML archive validation (`validate_safe_zip_archive`, `parse_xml_safe_bytes`), fuzz-resilient YAML frontmatter extraction (`parse_frontmatter_hardened`), CriticMarkup token balancing (`sanitize_critic_markup`), hybrid Latin + CJK Unicode telemetry (`normalize_cjk_and_unicode_prose`), 5-plugin Obsidian Lite Mode (`run_lite_continuity_check`), and 3-tier documentation index (`docs/INDEX.md`, `docs/LITE_MODE.md`).
- **Phase 1 Unified VaultIndex DAL (`scripts/lib/vault_index.py`)**: Thread-safe, mtime-keyed `VaultIndex` (`CACHE_VERSION = 3`) with `is_safe_subpath` path-traversal defense, `atomic_write` hardlink-safe replacement, multiline YAML block-scalar (`|`, `>`) frontmatter parsing, literary multi-paragraph dialogue telemetry, code-fence-safe wikilink extraction, and 16-char SHA-256 paragraph hashing (`arcanum vault-index`).
- **Feature 1 — Phase-Aware Effort & Career Velocity Engine (`scripts/lib/phase_effort_engine.py`)**: Implements all 9 canonical project stages (`Concept` through `Publishing`), Phase-Aware Effort Multipliers (`1.00x` First Draft and on-stage Outlining, `0.50x` Worldbuilding and off-phase Outlining, `0.20x` Revision-stage edits, and `0.00x` off-phase Revision block to prevent premature editing), 2,000-point daily goal, 730,000-word annual target, and 15,000,000-word career milestone forecasting (`arcanum sprint-effort` / `arcanum effort`).
- **Feature 2 — Epistemic POV & Spoiler Firewall (`scripts/lib/epistemic_firewall.py`)**: Chronological DAG solver auditing character knowledge baselines (`knows:`) against chapter reveals (`learns:`) and references (`references:`) to flag premature spoiler leaks (`EPI-201`), unframed mythic lore (`EPI-202`), and orphan reveals (`EPI-203`) (`arcanum validate-epistemic` / `arcanum epistemic`).
- **Feature 3 — Custom Planetary Calendar & Biome Route Physics Solver (`scripts/lib/timeline_solver.py`)**: Audits multi-planetary travel routes, orbital calendar conversions, and biome movement constraints.
- **Feature 4 — PolyGlot Conlang Lexicon Importer & Phonotactic Linter (`scripts/lib/conlang_linter.py`)**: Zero-dependency phonotactic linter and lexicon validator.
- **Feature 5 — Hard Magic & Sci-Fi Resource Conservation Ledger (`scripts/lib/resource_ledger.py`)**: Audits finite resource balance in fictional magic/sci-fi systems.
- **Feature 6 — Interactive Narrative Braid & POV Drought Visualizer (`scripts/lib/narrative_braid.py`)**: Computes character POV distribution and drought metrics across manuscript chapters.
- **Phase 4 Unified Vault Continuity Runner & Obsidian Live Callout Bridge (`scripts/lib/vault_continuity_runner.py`)**
- **Phase 2 & 3 Architectural Refactor Modules**:
  - `scripts/lib/diff_core.py` (`arcanum diff-fast`)
  - `scripts/lib/typed_constitution.py` (`arcanum typed-constitution`)
  - `scripts/lib/docx_tracked_changes.py` (`arcanum docx-tracked`)
  - `scripts/lib/plugin_sandbox.py` (`arcanum plugin-sandbox`)
  - `src/arcanum/` layered subpackage hierarchy (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).
