# Architectural Concerns & Security Remediations (`docs/codebase/CONCERNS.md`)

## 1. Resolved Architectural Concerns

During recent architecture reviews and modernization sprints, several latent architectural vulnerabilities and user-experience friction points were identified and permanently resolved:

### 1.1 OS Hardlink Baseline Corruption
- **Vulnerability**: Historical drafts promoted via `os.link` shared physical filesystem inodes with parent snapshots. Text editors such as Obsidian or VS Code write through hardlinks, permanently corrupting supposedly frozen historical baselines.
- **Remediation**: Transitioned `promote_draft_hardlinked()` in [`src/arcanum/manuscript/drafts.py`](../../src/arcanum/manuscript/drafts.py) and [`scripts/lib/diff_core.py`](../../scripts/lib/diff_core.py) to use `shutil.copy2` for physical inode separation. Applied `0o444` read-only filesystem locks to the parent draft directory, ensuring editors cannot modify baseline snapshots.

### 1.2 Windows Indexer Lock Contention on File Replacement
- **Vulnerability**: Windows file indexers (Obsidian background search, Windows Search Indexer, antivirus) frequently acquire transient read locks on recently saved files, causing `os.replace` to throw `PermissionError: [WinError 5] Access is denied`.
- **Remediation**: Implemented exponential backoff retry logic (up to 5 attempts across 320ms) inside `atomic_write()` in [`src/arcanum/core/storage.py`](../../src/arcanum/core/storage.py) and [`scripts/lib/fs_utils.py`](../../scripts/lib/fs_utils.py) when running on `win32`.

### 1.3 Decompression & XML Entity Bomb Vulnerabilities
- **Vulnerability**: Unvalidated ZIP archives (OpenXML `.docx` and PolyGlot `.pgd`) and untrusted XML files could trigger decompression bombs or quadratic XML entity expansions.
- **Remediation**: Enforced safe 64 MB decompression limits, a 100:1 max ratio, and blocked DOCTYPE entity expansions across all XML and ZIP handlers in [`src/arcanum/publishing/docx.py`](../../src/arcanum/publishing/docx.py) and [`src/arcanum/worldbible/conlang.py`](../../src/arcanum/worldbible/conlang.py).

### 1.4 Unsafe HTML Event String Interpolation (XSS Mitigation)
- **Vulnerability**: Inline `onclick="runCommand('{cmd}')"` attributes in portfolio and revision templates allowed HTML attribute breakout when project names contained single or double quotes.
- **Remediation**: Replaced inline event handlers with `data-cli="..."` attributes and document-level event delegation in [`src/arcanum/manuscript/portfolio.py`](../../src/arcanum/manuscript/portfolio.py), bound under strict Content Security Policy.

### 1.5 Publishing Prose Leakage & Typst Syntax Breakage
- **Vulnerability**: Direct pandoc or typst compilation leaked internal Obsidian wikilinks (`[[Character]]`), raw CriticMarkup deletions (`{--...--}`), and unescaped Typst control characters (`#`, `$`, `@`), causing compiler crashes.
- **Remediation**: Implemented `resolve_prose_for_publication()` and `escape_typst_text()` in [`src/arcanum/publishing/publisher.py`](../../src/arcanum/publishing/publisher.py). Wikilinks are transformed into clean reading prose, CriticMarkup edits are accepted, and Typst special characters are safely escaped.

### 1.6 External Tool Dependency for Digital E-Books
- **Vulnerability**: Novelists on minimal or offline setups without Pandoc could not generate standard EPUB3 digital editions from their manuscripts.
- **Remediation**: Implemented a pure standard-library zero-pip EPUB 3.3 generator in [`src/arcanum/publishing/epub.py`](../../src/arcanum/publishing/epub.py), supporting uncompressed mimetype positioning at offset 38, deterministic timestamps, semantic HTML5 navigation landmarks (`nav.xhtml`), and automatic CriticMarkup resolution.

### 1.7 Non-Technical Fiction Author Barrier
- **Vulnerability**: Novelists and speculative fiction authors without CLI experience were unable to run terminal commands, inspect continuity alerts, or safely manage configuration files.
- **Remediation**: Created a sovereign **Dual-Surface UX**:
  1. Windows double-click zero-friction launchers ([`launchers/launch_studio.bat`](../../launchers/launch_studio.bat)).
  2. A zero-pip local HTTP server daemon (`src/arcanum/server/daemon.py`) serving an air-gapped HTML5 Visual Studio at `http://127.0.0.1:4242`.
  3. A native Obsidian companion plugin (`templates/world-bible/.obsidian/plugins/ars-arcanum/`) featuring a live status bar health indicator.
  4. A 1-click **"Allow / Intended Twist"** action that automatically updates `constitution.yaml` (`!RULE_ID`), eliminating YAML editing overhead for writers.

---

## 2. Active Quality & Hardening Status

1. **Complete Modular Package Migration**: All core, manuscript, worldbible, publishing, and UI modules have been migrated into structured subpackages under `src/arcanum/`, with `scripts/lib/` retained as 100% backward-compatible facades.
2. **Strict Type Safety Clean Across Entire Repo**: Strict `mypy` typing verified clean with **0 errors across all 220 source files**.
3. **Continuous Verification Suite**: **692 unit and integration tests passing at 100%** in ~60s, maintaining an 81% branch coverage floor.
4. **Multi-Volume Benchmark Suite**: Multi-volume corpus benchmarks in [`tests/test_benchmark_suite.py`](../../tests/test_benchmark_suite.py) evaluate sub-150ms cached indexing and sub-1s cold scans across 800,000-word sagas.
5. **Weekly CI Drift Auditing**: The `.github/workflows/ci.yml` weekly cron job (`23 4 * * 1`) continuously guards against upstream toolchain decay, secret leakage, and CDN creep.


<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Production CLI & Continuity Cross-Reference

| Capability | Command | Native Engine | Compatibility Facade |
| :--- | :--- | :--- | :--- |
| **Visual Studio Cockpit** | `python scripts/arcanum studio [VAULT] [--port 4242]` | `src.arcanum.server.daemon` | `scripts/lib/studio_server.py` |
| **Unified Continuity Suite** | `python scripts/arcanum continuity-suite [VAULT]` | `src.arcanum.worldbible.runner` | `scripts/lib/vault_continuity_runner.py` |
| **Phase-Aware Effort Points** | `python scripts/arcanum sprint-effort [ARGS]` | `src.arcanum.manuscript.velocity` | `scripts/lib/phase_effort_engine.py` |
| **Epistemic POV Firewall** | `python scripts/arcanum validate-epistemic [VAULT]` | `src.arcanum.worldbible.epistemics` | `scripts/lib/epistemic_firewall.py` |
| **Timeline & Route Physics** | `python scripts/arcanum timeline-audit [VAULT]` | `src.arcanum.worldbible.timeline` | `scripts/lib/timeline_solver.py` |
| **PolyGlot Conlang Linter** | `python scripts/arcanum conlang-check [ARGS]` | `src.arcanum.worldbible.conlang` | `scripts/lib/conlang_linter.py` |
| **Resource Conservation Ledger** | `python scripts/arcanum ledger-audit [VAULT]` | `src.arcanum.worldbible.ledger` | `scripts/lib/resource_ledger.py` |
| **Multi-POV Narrative Braid** | `python scripts/arcanum braid [MANUSCRIPT]` | `src.arcanum.manuscript.braid` | `scripts/lib/narrative_braid.py` |
| **Prose Word & Dialogue Metrics** | `python scripts/arcanum count-words [FILE/VAULT]` | `src.arcanum.manuscript.word_counter` | `scripts/lib/word_counter.py` |
| **Fast Paragraph Diff & Scraps** | `python scripts/arcanum diff-fast OLD.md NEW.md` | `src.arcanum.manuscript.diff` | `scripts/lib/diff_core.py` |
| **Word Tracked Changes Sync** | `python scripts/arcanum docx-tracked [export/pull]` | `src.arcanum.publishing.docx` | `scripts/lib/docx_tracked_changes.py` |
| **Multi-Format Publishing** | `python scripts/arcanum publish [MANUSCRIPT] --format ...` | `src.arcanum.publishing.publisher` | `scripts/lib/publisher.py` |
| **System Diagnostics & Doctor** | `python scripts/arcanum doctor [VAULT]` | `src.arcanum.core.diagnostics` | `scripts/lib/diagnostics.py` |
| **Schema Migration Engine** | `python scripts/arcanum migrate [VAULT]` | `src.arcanum.core.migrate` | `scripts/lib/migrate.py` |
