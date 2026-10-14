# Repository Directory & Module Structure (`docs/codebase/STRUCTURE.md`)

- **`scripts/lib/` (64 Python Modules)**: Contains all zero-dependency core, manuscript, worldbuilding, and publishing engines, including the 12 Phase 1–4 modules (`vault_index.py`, `phase_effort_engine.py`, `diff_core.py`, `typed_constitution.py`, `docx_tracked_changes.py`, `plugin_sandbox.py`, `epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `narrative_braid.py`, `vault_continuity_runner.py`).
- **`src/arcanum/`**: Layered subpackage hierarchy (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).
- **`tests/`**: 58 stdlib `unittest` suites verifying every invariant, CLI command, and documentation contract.
