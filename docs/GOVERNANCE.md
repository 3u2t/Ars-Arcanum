# Ars Arcanum Project Governance

## Governance Principles

Ars Arcanum is governed as an independent, sovereign, local-first open-source project under the MIT License. All architectural and product decisions prioritize authorial ownership, deterministic verification ([ADR-0001](adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md)), zero-cloud survivability, and long-term backward compatibility of plain-text Markdown and YAML vaults.

## Roles & Responsibilities

- **Lead Architect & Maintainer**: Guides the overall vision, safeguards the 5 core engineering contracts in [`AGENTS.md`](../AGENTS.md), reviews architectural RFCs, and manages release signing.
- **Subsystem Maintainers**: Steward specific layered domains across `src/arcanum/` and `scripts/lib/` (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).
- **Contributors & Community Auditors**: Submit bug fixes, continuity rules, test cases, and documentation improvements via Pull Requests.

## Decision-Making & RFC Process

Major architectural changes—such as modifying the `.arcanum_cache.json` schema (`CACHE_VERSION`), adding new CLI subcommands to `DISPATCH_TABLE`, or altering the 3-tier `constitution.yaml` cascade—are recorded as Architecture Decision Records (ADRs) under `docs/adr/` and reviewed against the test harness before merging.

## Release Cadence & Versioning

Ars Arcanum follows Semantic Versioning (`MAJOR.MINOR.PATCH`). Version identifiers are strictly synchronized across `scripts/arcanum`, `scripts/lib/cli.py`, `scripts/lib/diagnostics.py`, `pyproject.toml`, and `CHANGELOG.md`, and verified automatically on every commit by `tests/test_version_consistency.py`.

## Security & Vulnerability Disclosure

Security vulnerabilities—particularly involving path traversal (`is_safe_subpath`), plugin subprocess isolation (`plugin_sandbox.py`), OpenXML/ZIP parsing (`docx_tracked_changes.py`, `conlang_linter.py`), or CSP headers—should be reported according to [`SECURITY.md`](../SECURITY.md) and evaluated against [`docs/THREAT_MODEL.md`](THREAT_MODEL.md).


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
