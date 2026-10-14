# Ars Arcanum Security & Threat Model (`STRIDE-Lite`)

## Overview: STRIDE-Lite Analysis for a Sovereign Local-First Authoring OS

Ars Arcanum processes untrusted external inputs in three primary workflows: importing third-party `.docx` files from editors (`docx_tracked_changes.py` / `docx_sync.py`), importing PolyGlot `.pgd` lexicons (`conlang_linter.py`), and executing custom user plugins (`.arcanum/plugins/*.py` via `plugin_sandbox.py`). Below is our **STRIDE-Lite** threat matrix and deterministic mitigations.

## Spoofing Identity

- **Risk**: Malicious plugin scripts or imported archives attempting to masquerade as core engines or spoof author revision attribution in `.arcanum/sprint_log.jsonl`.
- **Mitigation**: `plugin_sandbox.py` executes third-party plugins in an isolated `python3 -I -B` subprocess with a sanitized environment (`PATH=/usr/bin:/bin`, no user `PYTHONPATH`), and `backup.py` signs and verifies archives with SHA-256 manifests and optional GPG encryption.

## Tampering with Data

- **Risk**: Interrupted writes, concurrent CLI invocations, or rogue scripts corrupting manuscript chapters or mutating locked historical drafts (`Draft-01`).
- **Mitigation**: Mandatory `atomic_write()` (`fs_utils.py` / `vault_index.py`) stages writes to temporary files and commits via `os.replace` (which safely breaks OS hardlinks created by `promote_draft_hardlinked()` without mutating parent drafts), paired with cross-platform `ArcanumLock` advisory locking (`lockfile.py`).

## Repudiation

- **Risk**: Unattributed destructive edits across multi-draft revisions or unverified backup archives.
- **Mitigation**: Immutable `.locked` seals and `.draft_lineage.json` provenance manifests on promoted drafts (`diff_core.py`), automatic archival of excised cuts `>= 50` words into `Scraps/`, and cryptographic SHA-256 manifest verification in `backup.py`.

## Information Disclosure

- **Risk**: Path traversal attacks (`../../etc/passwd`) via crafted wikilinks or plugin paths, or silent exfiltration of unpublished manuscripts via embedded remote assets in HTML reports.
- **Mitigation**: Strict `is_safe_subpath(root, candidate)` checks before every read/write operation (`PathSecurityError`), and CI enforcement verifying zero external CDN URLs across all engines.

## Denial of Service

- **Risk**: Quadratic $O(N^2)$ diff freezes on 200,000-word novels, infinite loops in user plugins, or recursive directory traversal into `.git`/`Backups`.
- **Mitigation**: Two-level SHA-256 paragraph-hash skipping in `diff_core.py` and `vault_index.py`, in-place pruning of excluded directories during `os.walk`, and strict wall-clock timeouts (`timeout_seconds=5.0`) + 1 MB stdout caps in `plugin_sandbox.py`.

## Elevation of Privilege

- **Risk**: Arbitrary code execution when discovering or running custom plugins in `.arcanum/plugins/*.py`.
- **Mitigation**: `run_plugin_sandboxed()` (`scripts/lib/plugin_sandbox.py`) isolates plugin execution in a separate OS process (`sys.executable -I -B`) communicating strictly over serialized JSON `stdin`/`stdout`.

## Content Security Policy

Every static HTML visualizer (`narrative_braid.py`, `portfolio.py`, `revision_heatmap.py`, `manuscript_diff.py`, `codex_export.py`) embeds a strict **Content Security Policy** meta header:

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">
```


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
