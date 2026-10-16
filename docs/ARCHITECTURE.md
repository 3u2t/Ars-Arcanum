# Ars Arcanum System Architecture Blueprint
`docs/ARCHITECTURE.md`

> **Note**: For the fully cited, whole-repository technical architecture deep-dive (including C4 models, Commands & Verification Inventory, and confidence assessments), refer to [`docs/codebase/ARCHITECTURE.md`](codebase/ARCHITECTURE.md).

## 1. Executive Architectural Overview

Ars Arcanum is structured around a strict **Three-Subsystem Epistemic Architecture** ([ADR-0001](adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md)) backed by a zero-dependency Python `>=3.10` standard library core and a Dual-Surface Presentation Layer:

| Subsystem | Epistemic Role | Core Modules (`scripts/lib/` & `src/arcanum/`) | Enforcement Mode |
| :--- | :--- | :--- | :--- |
| **Subsystem 1: Deterministic Invariants & Continuity Compilers** | Verifies objective mathematical, chronological, linguistic, and epistemic facts plus transactional file safety. | `vault_index.py`, `fs_utils.py`, `lockfile.py`, `backup.py`, `plugin_sandbox.py`, `epistemic_firewall.py` (`EPI-*`), `timeline_solver.py` (`TIME-*`), `conlang_linter.py` (`CON-*`), `resource_ledger.py` (`LED-*`) | Strict exit codes (`0` pass, `1` violation) |
| **Subsystem 2: Descriptive Telemetry & Craft Analytics** | Measures writing velocity, phase-weighted effort, dialogue ratios, revision churn, and POV pacing without prescriptive dogma. | `phase_effort_engine.py`, `word_counter.py`, `writing_sprint.py`, `diff_core.py`, `manuscript_diff.py`, `revision_heatmap.py` (`REV-*`), `narrative_braid.py` (`BRD-*`), `portfolio.py` | Neutral JSON/HTML/SVG telemetry |
| **Subsystem 3: Authorial Governance & Workspace Integration** | Cascades user-defined policy rules, synchronizes with Obsidian/Word/Typst/Pandoc, and renders live vault dashboards. | `typed_constitution.py`, `constitution.py`, `config.py`, `docx_tracked_changes.py`, `publisher.py`, `omnibus.py`, `codex_export.py`, `vault_continuity_runner.py` | User-controlled via `constitution.yaml` (`!RULE_ID`) |
| **Dual-Surface Presentation Layer** | Provides zero-terminal UI for writers: an air-gapped HTML5 visual studio and native Obsidian companion plugin. | `src/arcanum/server/daemon.py`, `src/arcanum/server/handlers.py`, `src/arcanum/ui/studio_app.html`, `templates/world-bible/.obsidian/plugins/ars-arcanum/` | Local loopback `http://127.0.0.1:4242` |

---

## 2. Core Architectural Invariants

1. **Physical Inode Separation & Read-Only Baselines**: Historical draft snapshots promoted via `promote_draft_hardlinked()` use `shutil.copy2` to physically separate disk inodes, and apply `0o444` read-only permissions to parent drafts so external text editors (Obsidian, VS Code) cannot corrupt historical baselines.
2. **Atomic Writes with Windows Retry Backoff**: All file modifications use `atomic_write()` (staged via `tempfile.mkstemp`, flushed with `os.fsync()`, and replaced via `os.replace()`) with exponential backoff on Windows to absorb transient file indexer or antivirus locks.
3. **Zero-Pip Standard Library Runtime**: The core runtime and local studio server require zero third-party packages from PyPI.
4. **Air-Gapped Content Security Policy**: All generated HTML/SVG interfaces embed `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">` with zero external CDN scripts or fonts.

---

## 3. Production CLI & Continuity Cross-Reference

- **Visual Studio Cockpit**: `arcanum studio [VAULT] [--port 4242] [--open]` (`src/arcanum/server/daemon.py`)
- **Unified Continuity Suite & Obsidian Bridge**: `arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `arcanum docx-tracked export/pull` (`scripts/lib/docx_tracked_changes.py`)
- **Multi-Format Publication & Prose Sanitizer**: `arcanum publish [MANUSCRIPT] --format pdf|epub|docx` (`scripts/lib/publisher.py`)
