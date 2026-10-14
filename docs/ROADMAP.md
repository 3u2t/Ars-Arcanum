# Ars Arcanum Product & Engineering Roadmap

## Momentum Queues & Phased Evolution

Ars Arcanum tracks engineering execution through five canonical momentum queues synchronized with [`AGENTS.md`](../AGENTS.md):

### `now`
- **Phase 1–4 Production Stabilization (Completed & Live)**:
  - Unified `VaultIndex` DAL (`scripts/lib/vault_index.py`, `CACHE_VERSION = 3`) with YAML block-scalar support and multi-paragraph dialogue metrics.
  - Phase-Aware Effort & Career Velocity Engine (`scripts/lib/phase_effort_engine.py`, `arcanum sprint-effort`).
  - Shared SHA-256 paragraph-hash diff engine & hardlink draft branching (`scripts/lib/diff_core.py`, `arcanum diff-fast`).
  - Strictly typed 3-tier `AuthorialConstitution` with `!RULE_ID` negation (`scripts/lib/typed_constitution.py`).
  - Bidirectional CriticMarkup <-> Word Tracked Changes `.docx` bridge (`scripts/lib/docx_tracked_changes.py`, `arcanum docx-tracked`).
  - Subprocess-isolated plugin runner (`scripts/lib/plugin_sandbox.py`, `arcanum plugin-sandbox`).
  - Deterministic Worldbuilding Continuity Compilers (`epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `narrative_braid.py`) and unified Obsidian callout dashboard runner (`vault_continuity_runner.py`, `arcanum continuity-suite`).

### `next`
- **Phase 5 — Deep Legacy Cutover & Interactive Atlas Visualizers**:
  - Route remaining legacy callers in `manuscript_diff.py`, `revision_heatmap.py`, `docx_sync.py`, and `frontmatter.py` directly through `diff_core.py`, `docx_tracked_changes.py`, and `vault_index.py`.
  - Add offline SVG timeline & route map rendering to `timeline_solver.py`.
  - Add sound-change applier (SCA) diachronic evolution rules to `conlang_linter.py`.

### `blocked`
- Zero blocked items. All core runtime features operate with 100% stdlib dependencies.

### `improve`
- Extend strict Mypy per-module rules to legacy `*_template.py` modules as HTML/CSS assets migrate to `importlib.resources`.
- Add automated multi-book omnibus continuity cross-checks across `Book-01`..`Book-04`.

### `recurring`
- Weekly CI verification (`.github/workflows/ci.yml`), Bandit SAST scanning, Gitleaks secret auditing, and `>=80%` test coverage enforcement.
