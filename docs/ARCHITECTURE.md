# Ars Arcanum System Architecture Blueprint
`docs/ARCHITECTURE.md`

> **Note**: For the fully cited, whole-repository technical architecture deep-dive (including C4 models, Commands & Verification Inventory, and confidence assessments), refer to [`docs/codebase/ARCHITECTURE.md`](codebase/ARCHITECTURE.md).

## 1. Executive Architectural Overview

Ars Arcanum is structured around a strict **Three-Subsystem Epistemic Architecture** ([ADR-0001](adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md)) backed by a zero-dependency Python `>=3.10` standard library core, native modular packages (`src/arcanum/`), backward-compatible facades (`scripts/lib/`), and a Dual-Surface Presentation Layer:

| Subsystem | Epistemic Role | Native Modules (`src/arcanum/`) | Compatibility Facades (`scripts/lib/`) | Enforcement Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Subsystem 1: Deterministic Invariants & Continuity Compilers** | Verifies objective mathematical, chronological, spatial, linguistic, and epistemic facts plus transactional file safety. | `core.storage`, `core.locking`, `core.indexer`, `core.diagnostics`, `core.migrate`, `worldbible.runner`, `worldbible.epistemics` (`EPI-*`), `worldbible.timeline` (`TIME-*`), `worldbible.conlang` (`CON-*`), `worldbible.ledger` (`LED-*`) | `vault_index.py`, `fs_utils.py`, `lockfile.py`, `diagnostics.py`, `migrate.py`, `vault_continuity_runner.py`, `epistemic_firewall.py`, `timeline_solver.py`, `conlang_linter.py`, `resource_ledger.py` | Strict exit codes (`0` pass, `1` violation) |
| **Subsystem 2: Descriptive Telemetry & Craft Analytics** | Measures writing velocity, phase-weighted effort, dialogue ratios, revision churn, and POV pacing without prescriptive dogma. | `manuscript.velocity`, `manuscript.word_counter`, `manuscript.diff`, `manuscript.braid` (`BRD-*`), `manuscript.heatmap` (`REV-*`), `manuscript.portfolio` | `phase_effort_engine.py`, `word_counter.py`, `writing_sprint.py`, `diff_core.py`, `narrative_braid.py`, `revision_heatmap.py`, `portfolio.py` | Neutral JSON/HTML/SVG telemetry |
| **Subsystem 3: Authorial Governance & Publishing** | Cascades user-defined policy rules, compiles camera-ready publications, synchronizes with Word/Typst/Pandoc, and renders live vault dashboards. | `worldbible.constitution`, `publishing.epub`, `publishing.docx`, `publishing.publisher`, `publishing.omnibus`, `publishing.preflight`, `worldbible.codex` | `typed_constitution.py`, `constitution.py`, `docx_tracked_changes.py`, `publisher.py`, `omnibus.py`, `preflight.py`, `codex_export.py` | User-controlled via `constitution.yaml` (`!RULE_ID`) |
| **Dual-Surface Presentation Layer** | Provides zero-terminal UI for writers: an air-gapped HTML5 visual studio cockpit, 11 themes, 10 Web Audio typewriter models, and native Obsidian companion plugin. | `server.daemon`, `server.handlers`, `ui.theme`, `ui.studio`, `ui.studio_app.html` | `studio_server.py`, `ui_theme_engine.py`, `ui_theme_studio.py` | Local loopback `http://127.0.0.1:4242` |

---

## 2. Core Architectural Invariants

1. **Physical Inode Separation & Read-Only Baselines**: Historical draft snapshots promoted via `promote_draft_hardlinked()` use `shutil.copy2` to physically separate disk inodes, and apply `0o444` read-only permissions to parent drafts so external text editors (Obsidian, VS Code) cannot corrupt historical baselines.
2. **Atomic Writes with Windows Retry Backoff**: All file modifications use `atomic_write()` (staged via `tempfile.mkstemp`, flushed with `os.fsync()`, and replaced via `os.replace()`) with exponential backoff on Windows to absorb transient file indexer or antivirus locks.
3. **Cross-Platform Advisory Locking**: All concurrent CLI, daemon, and background watcher processes acquire `ArcanumLock` (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows).
4. **Path Confinement**: All file reads, writes, and archive extractions validate `is_safe_subpath(root, candidate)`, raising `PathSecurityError` on traversal attempts.
5. **Zero-Pip Standard Library Runtime**: The core runtime and local studio server require zero third-party packages from PyPI.
6. **Air-Gapped Content Security Policy**: All generated HTML/SVG interfaces embed `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;">` with zero external CDN scripts or fonts.

---

## 3. Production CLI & Continuity Cross-Reference

| Capability | Command | Native Engine | Compatibility Facade |
| :--- | :--- | :--- | :--- |
| **Visual Studio Cockpit** | `arcanum studio [VAULT] [--port 4242] [--open]` | `src.arcanum.server.daemon` | `scripts/lib/studio_server.py` |
| **Unified Continuity Suite** | `arcanum continuity-suite [VAULT]` | `src.arcanum.worldbible.runner` | `scripts/lib/vault_continuity_runner.py` |
| **Phase-Aware Effort & Velocity** | `arcanum sprint-effort [ARGS]` | `src.arcanum.manuscript.velocity` | `scripts/lib/phase_effort_engine.py` |
| **Epistemic POV Firewall** | `arcanum validate-epistemic [VAULT]` | `src.arcanum.worldbible.epistemics` | `scripts/lib/epistemic_firewall.py` |
| **Timeline & Route Physics** | `arcanum timeline-audit [VAULT]` | `src.arcanum.worldbible.timeline` | `scripts/lib/timeline_solver.py` |
| **PolyGlot Conlang Linter** | `arcanum conlang-check [ARGS]` | `src.arcanum.worldbible.conlang` | `scripts/lib/conlang_linter.py` |
| **Resource Conservation Ledger** | `arcanum ledger-audit [VAULT]` | `src.arcanum.worldbible.ledger` | `scripts/lib/resource_ledger.py` |
| **Multi-POV Narrative Braid** | `arcanum braid [MANUSCRIPT]` | `src.arcanum.manuscript.braid` | `scripts/lib/narrative_braid.py` |
| **Prose Word & Dialogue Metrics** | `arcanum count-words [FILE/VAULT]` | `src.arcanum.manuscript.word_counter` | `scripts/lib/word_counter.py` |
| **Fast Paragraph Diff & Scraps** | `arcanum diff-fast OLD.md NEW.md` | `src.arcanum.manuscript.diff` | `scripts/lib/diff_core.py` |
| **Word Tracked Changes Sync** | `arcanum docx-tracked [export/pull]` | `src.arcanum.publishing.docx` | `scripts/lib/docx_tracked_changes.py` |
| **Multi-Format Publication** | `arcanum publish [MANUSCRIPT] --format ...` | `src.arcanum.publishing.publisher` | `scripts/lib/publisher.py` |
| **System Diagnostics & Doctor** | `arcanum doctor [VAULT]` | `src.arcanum.core.diagnostics` | `scripts/lib/diagnostics.py` |
| **Schema Migration Engine** | `arcanum migrate [VAULT]` | `src.arcanum.core.migrate` | `scripts/lib/migrate.py` |
