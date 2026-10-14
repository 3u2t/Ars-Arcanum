# Release Notes — `v0.2.0-amber` (Audit Consolidation & Obsidian Lite Mode)

## Highlights
1. **Consolidated `src/arcanum/` Package Facade**: Synchronized package versions (`0.2.0` in `pyproject.toml` and `src/arcanum/__init__.py`) and unified exports across `core`, `manuscript`, `publishing`, `ui`, and `worldbible`.
2. **Obsidian Lite Mode (`scripts/arcanum-lite` / `arcanum-lite`)**: Added a single-command workflow that runs the 4 flagship deterministic compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`), generates `_Arcanum_Lite_Dashboard.md`, and configures a 5-plugin `.obsidian/lite_profile.json`.
3. **Stdlib Parser Fuzz Hardening (`scripts/lib/audit_hardening.py`)**: Added zero-dependency protection against ZIP bombs, path traversal, XML `DOCTYPE`/`ENTITY` expansion, deeply nested/unclosed YAML frontmatter, and unbalanced CriticMarkup tokens, backed by `tests/test_audit_fuzz_hardening.py`.
4. **3-Tier Documentation Index (`docs/INDEX.md`)**: Structured all 70+ documentation files into Quickstart, Author Craft Reference, and Engine Internals tiers.
5. **Collaborative Narrative CI & Contributor Backlog**: Added `.github/workflows/narrative-continuity-ci.yml` and `.github/ISSUE_BACKLOG/GOOD_FIRST_ISSUES.md`.
