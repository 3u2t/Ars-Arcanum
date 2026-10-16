# Ars Arcanum (Scriptorium) — Agentic Operating Manifesto & Engineering Contracts

**GPA 4.0/4.0 — Grade A+ | Release v0.1.0 | 100% Sovereign Offline Architecture**

## 1. System Identity & Mission

Ars Arcanum is a sovereign, local-first, 100% offline authoring operating system and speculative worldbuilding craft studio. Every human contributor and automated coding agent operating in this repository must uphold five core principles:

1. **Absolute Creative Sovereignty**: Author vaults (`~/Universes/` and `~/Manuscripts/`) belong exclusively to the writer. No feature may transmit prose externally or lock content into proprietary binary formats.
2. **Descriptive Measurement over Prescriptive Dogma ([ADR-0001](docs/adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md))**: We never grade prose with subjective literary scores. Subsystem 1 enforces deterministic continuity invariants (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`), while Subsystem 2 reports objective telemetry (`REV-*`, `BRD-*`, Phase-Aware Effort Points).
3. **Deterministic Rails over Probabilistic Hallucination**: Zero generative AI prose engines. All worldbuilding, linguistic, and timeline verifications are 100% reproducible and deterministic.
4. **Continuous Verification & Anti-Stall Momentum**: Every change must pass `ruff check .`, `mypy --config-file mypy.ini --explicit-package-bases scripts src tests`, and the `unittest` suite (`>=80%` coverage floor; currently 692 tests passing at 81% branch coverage).
5. **Defense in Depth**: Strict path validation, atomic file replacement with Windows indexer retry backoff, cross-platform advisory locking, bounded ZIP/XML archive parsers, and isolated plugin subprocesses.

## 2. Architectural Safety & Security Contracts

Every module in `scripts/lib/` and `src/arcanum/` must enforce these six non-negotiable engineering contracts:

### 2.1 Atomic Writes with Windows Backoff Retry
All file mutations—whether updating `.arcanum_cache.json`, `.arcanum/sprint_log.jsonl`, `_Arcanum_Diagnostics.md`, or chapter Markdown files—must use `atomic_write()` (`src/arcanum/core/storage.py`, `scripts/lib/fs_utils.py`, and `scripts/lib/vault_index.py`). Writes are staged to a sibling temporary file (`tempfile.mkstemp`), flushed with `os.fsync()`, and promoted via atomic `os.replace()`. On Windows, transient file indexer or antivirus locks are absorbed via exponential retry backoff (5 attempts across 320ms) so interrupted operations never corrupt author work.

### 2.2 Physical Inode Separation for Draft Snapshots
When promoting drafts (`promote_draft_hardlinked()` in `scripts/lib/diff_core.py`), files are copied using `shutil.copy2` to guarantee physical disk inode separation between parent and child drafts. Parent draft files are marked `0o444` read-only so external text editors (Obsidian, VS Code) cannot mutate historical snapshots.

### 2.3 Cross-Platform File Locking
Concurrent CLI, daemon, and background watcher operations must acquire advisory locks through `ArcanumLock` (`src/arcanum/core/locking.py` / `scripts/lib/lockfile.py`), utilizing `fcntl.flock` on POSIX (Linux/macOS) and `msvcrt.locking` on Windows.

### 2.4 Path Traversal Defense
Every file reader, exporter, archive extractor, and plugin runner must validate paths with `is_safe_subpath(root, candidate)` (`src/arcanum/core/storage.py` / `scripts/lib/vault_index.py` / `scripts/lib/fs_utils.py`) before touching disk, raising `PathSecurityError` if any symlink or `..` segment escapes the sovereign vault root.

### 2.5 Zero-Pip Dependency Guarantee
Core runtime execution across `scripts/lib/` and `src/arcanum/` must rely strictly on the Python `>=3.10` standard library (`json`, `zipfile`, `xml.etree.ElementTree`, `difflib`, `hashlib`, `sqlite3`, `http.server`, `unittest`). External binaries (`typst`, `pandoc`, `gpg`) are optional publishing/encryption accelerators invoked safely via list-argument `subprocess.run()`. Native zero-pip EPUB3 compilation is guaranteed via `src/arcanum/publishing/epub.py`.

### 2.6 Content-Security-Policy & Air-Gapped Cockpit
Every generated HTML report and local web service (`studio_app.html`, `portfolio`, `revision_heatmap`, `narrative_braid`) must embed an air-gapped `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;">` header and zero external CDN links (`https://cdn...`, `unpkg`, `cdnjs`). The local HTTP daemon (`src/arcanum/server/daemon.py`) binds strictly to loopback `127.0.0.1:4242`.

## 3. Momentum Queues

### `now`
- Maintain 100% pass rate across all 692 unit tests, including Phase 1–5 continuity compilers, native publishing suite, and core modules (`vault_index.py`, `phase_effort_engine.py`, `diff_core.py`, `typed_constitution.py`, `docx_tracked_changes.py`, `plugin_sandbox.py`, `epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py`, `narrative_braid.py`, `vault_continuity_runner.py`, `epub.py`, `locking.py`, `storage.py`, `visualizers.py`, `diff.py`, `braid.py`, `codex.py`, `drafts.py`, `velocity.py`, `portfolio.py`, `constitution.py`, `epistemics.py`, `timeline.py`, `ledger.py`, `conlang.py`, `runner.py`, `preflight.py`, `omnibus.py`, `publisher.py`, `docx.py`, `sandbox.py`, `scaffold.py`, `backup.py`, `restore.py`, `snapshot.py`, `importer.py`, `heatmap.py`, `hardening.py`, `config.py`, `state.py`, `scope.py`, `frontmatter.py`, `indexer.py`, `cache.py`, `registry/base.py`, `registry/__init__.py`, `diagnostics.py`, `migrate.py`, `word_counter.py`, `theme.py`, `studio.py`).
- Keep `_Arcanum_Diagnostics.md` live Obsidian callout generation and the local Visual Web Studio Cockpit (`127.0.0.1:4242`) synchronized with `arcanum continuity-suite` and the native Obsidian companion plugin.
- Support 1-click narrative twist allowance (`!RULE_ID` dynamic negation in `constitution.yaml`).
- Enforce cross-vault series federation (`world_root`) across multi-novel universes.

### `next`
- Continue progressive delegation of remaining legacy `scripts/lib/` internal loops into `src/arcanum/` subpackages (`core`, `manuscript`, `worldbible`, `publishing`, `ui`).

### `blocked`
- None. All parser, CLI dispatch, dual-surface server, CI packaging, and native module migration blockers are resolved.

### `improve`
- Maintain strict `mypy` enforcement across all 26 core/template modules and `src.arcanum.*` packages (220 files clean).
- Maintain sub-150ms cached indexing velocity over 800,000-word multi-volume sagas in `tests/test_benchmark_suite.py`.

### `recurring`
- Weekly CI drift audit (`.github/workflows/ci.yml`), Gitleaks secret scan, Bandit AST audit, and zero-CDN verification.
