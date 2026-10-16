# Ars Arcanum (Scriptorium) — Agentic Operating Manifesto & Engineering Contracts

**GPA 4.0/4.0 — Grade A+ | Release v0.1.0 | 100% Sovereign Offline Architecture**

## 1. System Identity & Mission

Ars Arcanum is a sovereign, local-first, 100% offline authoring operating system and speculative worldbuilding craft studio. Every human contributor and automated coding agent operating in this repository must uphold five core principles:

1. **Absolute Creative Sovereignty**: Author vaults (`~/Universes/` and `~/Manuscripts/`) belong exclusively to the writer. No feature may transmit prose externally or lock content into proprietary binary formats.
2. **Descriptive Measurement over Prescriptive Dogma ([ADR-0001](docs/adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md))**: We never grade prose with subjective literary scores. Subsystem 1 enforces deterministic continuity invariants (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`), while Subsystem 2 reports objective telemetry (`REV-*`, `BRD-*`, Phase-Aware Effort Points).
3. **Deterministic Rails over Probabilistic Hallucination**: Zero generative AI prose engines. All worldbuilding, linguistic, and timeline verifications are 100% reproducible and deterministic.
4. **Continuous Verification & Anti-Stall Momentum**: Every change must pass `ruff check .`, `mypy --config-file mypy.ini --explicit-package-bases scripts src tests`, `bandit -r scripts/lib src/arcanum -ll -ii`, and the `unittest` suite (`>=80%` coverage).
5. **Defense in Depth**: Strict path validation, atomic file replacement, cross-platform advisory locking, and isolated plugin subprocesses.

## 2. Architectural Safety & Security Contracts

Every module in `scripts/lib/` and `src/arcanum/` must enforce these five non-negotiable engineering contracts:

### 2.1 Atomic Writes
All file mutations—whether updating `.arcanum_cache.json`, `.arcanum/sprint_log.jsonl`, `_Arcanum_Diagnostics.md`, or chapter Markdown files—must use `atomic_write()` (`scripts/lib/fs_utils.py` and `scripts/lib/vault_index.py`). Writes are staged to a sibling temporary file (`tempfile.mkstemp`), flushed with `os.fsync()`, and promoted via atomic `os.replace()` so interrupted operations never corrupt or truncate author work, and OS hardlinks across `Draft-*` snapshots break cleanly on write.

### 2.2 Cross-Platform File Locking
Concurrent CLI and background watcher operations must acquire advisory locks through `ArcanumLock` (`scripts/lib/lockfile.py`), utilizing `fcntl.flock` on POSIX (Linux/macOS) and `msvcrt.locking` on Windows.

### 2.3 Path Traversal Defense
Every file reader, exporter, archive extractor, and plugin runner must validate paths with `is_safe_subpath(root, candidate)` (`scripts/lib/vault_index.py` / `scripts/lib/fs_utils.py`) before touching disk, raising `PathSecurityError` if any symlink or `..` segment escapes the sovereign vault root.

### 2.4 Zero-Pip Dependency Guarantee
Core runtime execution across `scripts/lib/` and `src/arcanum/` must rely strictly on the Python `>=3.10` standard library (`json`, `zipfile`, `xml.etree.ElementTree`, `difflib`, `hashlib`, `sqlite3`, `unittest`). External binaries (`typst`, `pandoc`, `gpg`) are optional publishing/encryption accelerators invoked safely via list-argument `subprocess.run()`.

### 2.5 Content-Security-Policy
Every generated HTML report (`portfolio`, `revision_heatmap`, `manuscript_diff`, `codex_export`, `narrative_braid`) must embed an air-gapped `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">` header and zero external CDN links (`https://cdn...`, `unpkg`, `cdnjs`).

## 3. Momentum Queues

### `now`
- Maintain 100% pass rate across all test modules, including the Phase 1–4 continuity compilers (`vault_index.py`, `phase_effort_engine.py`, `diff_core.py`, `typed_constitution.py`, `docx_tracked_changes.py`, `plugin_sandbox.py`, `epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `narrative_braid.py`, `vault_continuity_runner.py`).
- Keep `_Arcanum_Diagnostics.md` live Obsidian callout generation synchronized with `arcanum continuity-suite`.

### `next`
- Expand progressive delegation of legacy `scripts/lib/` internal loops into `src/arcanum/` subpackages (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).
- Add interactive SVG export presets for custom planetary orbital calendars and PolyGlot etymology trees.

### `blocked`
- None. All parser, CLI dispatch, and CI packaging blockers from Phases 1–4 are resolved.

### `improve`
- Continue ratcheting per-module strict `mypy` enforcement across remaining legacy template modules.
- Expand benchmark corpus coverage in `tests/test_benchmark_suite.py` for 800,000-word multi-volume series.

### `recurring`
- Weekly CI drift audit (`.github/workflows/ci.yml`), Gitleaks secret scan, Bandit AST audit, and zero-CDN verification.
