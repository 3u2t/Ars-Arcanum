# 🎯 Ars Arcanum — Curated `good first issue` Tickets for Contributors

Copy-paste any of the self-contained issues below into GitHub Issues to onboard developers from `r/opensource`. Every ticket enforces the **Zero-Pip Python 3.10+ Standard Library** contract.

## Issue A: `[Good First Issue] Add Property-Based Corpus Fuzzing for YAML Frontmatter Block Scalars`
- **Labels**: `good first issue`, `testing`, `parser-hardening`
- **Target Files**: `scripts/lib/audit_hardening.py`, `tests/test_audit_fuzz_hardening.py`
- **Scope**: Expand test fixtures covering folded (`>`) and literal (`|`) YAML block scalars containing colons, quotes, and CJK punctuation (`「...」`) without external packages.
- **Verification**: `python3 -m unittest tests/test_audit_fuzz_hardening.py -v`

## Issue B: `[Good First Issue] Add Multi-Paragraph CriticMarkup Comment ({>>...<<}) Export to Word Tracked Changes`
- **Labels**: `good first issue`, `publishing`, `docx`
- **Target Files**: `scripts/lib/docx_tracked_changes.py`, `scripts/lib/audit_hardening.py`
- **Scope**: Map CriticMarkup comment blocks (`{==highlighted==}{>>author note<<}`) to OpenXML comment references while preserving strict `validate_safe_zip_archive` bounds.
- **Verification**: `python3 scripts/apply_arcanum_upgrade.py`

## Issue C: `[Good First Issue] Add Relativistic Time-Dilation Lore Examples to Eldoria-Cosmos Template`
- **Labels**: `good first issue`, `templates`, `worldbuilding`
- **Target Files**: `templates/demo-cosmos/Eldoria-Cosmos/`, `tests/`
- **Scope**: Add a sample sci-fi interstellar transit ledger demonstrating `compute_relativistic_proper_days` (`TIME-*`) and `scripts/arcanum-lite`.
- **Verification**: `python3 scripts/arcanum-lite templates/demo-cosmos/Eldoria-Cosmos`

## Issue D: `[Good First Issue] Create One-Click Obsidian Community Command Snippet for Lite Mode`
- **Labels**: `good first issue`, `ux`, `obsidian`
- **Target Files**: `docs/LITE_MODE.md`, `configs/`
- **Scope**: Provide a pre-configured Obsidian Shell Commands snippet that triggers `python scripts/arcanum-lite` on file save and opens `_Arcanum_Lite_Dashboard.md`.
- **Verification**: `python3 scripts/sync_and_verify_docs.py`

## Issue E: `[Good First Issue] Add Cross-Platform Path Locking Regression Tests for Windows UNC Paths`
- **Labels**: `good first issue`, `core`, `cross-platform`
- **Target Files**: `scripts/lib/lockfile.py`, `tests/`
- **Scope**: Add unit tests simulating Windows drive-letter and UNC path normalization inside `is_safe_subpath` and `lockfile.py`.
- **Verification**: `python3 scripts/apply_arcanum_upgrade.py`
