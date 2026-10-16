# Architectural Concerns & Security Remediations (`docs/codebase/CONCERNS.md`)

## 1. Resolved Architectural Concerns

During the production hardening audit, several latent architectural vulnerabilities and user-experience friction points were identified and permanently resolved:

### 1.1 OS Hardlink Baseline Corruption
- **Vulnerability**: Historical drafts promoted via `os.link` shared physical filesystem inodes with parent snapshots. Text editors such as Obsidian or VS Code write through hardlinks, permanently corrupting supposedly frozen historical baselines.
- **Remediation**: Transitioned `promote_draft_hardlinked()` in [`scripts/lib/diff_core.py`](../../scripts/lib/diff_core.py) to use `shutil.copy2` for physical inode separation. Applied `0o444` read-only filesystem locks to the parent draft directory, ensuring editors cannot modify baseline snapshots.

### 1.2 Windows Indexer Lock Contention on File Replacement
- **Vulnerability**: Windows file indexers (Obsidian background search, Windows Search Indexer, antivirus) frequently acquire transient read locks on recently saved files, causing `os.replace` to throw `PermissionError: [WinError 5] Access is denied`.
- **Remediation**: Implemented exponential backoff retry logic (up to 5 attempts across 320ms) inside `atomic_write()` in [`scripts/lib/vault_index.py`](../../scripts/lib/vault_index.py) and [`scripts/lib/fs_utils.py`](../../scripts/lib/fs_utils.py) when running on `win32`.

### 1.3 Decompression & XML Entity Bomb Vulnerabilities
- **Vulnerability**: Unvalidated ZIP archives (OpenXML `.docx` and PolyGlot `.pgd`) and untrusted XML files could trigger decompression bombs or quadratic XML entity expansions.
- **Remediation**: Wired `validate_safe_zip_archive()` and `parse_xml_safe_bytes()` from `audit_hardening.py` into [`docx_tracked_changes.py`](../../scripts/lib/docx_tracked_changes.py) and [`conlang_linter.py`](../../scripts/lib/conlang_linter.py), enforcing a 64 MB uncompressed limit, a 100:1 max ratio, and blocking DOCTYPE entity expansions.

### 1.4 Unsafe HTML Event String Interpolation (XSS Mitigation)
- **Vulnerability**: Inline `onclick="runCommand('{cmd}')"` attributes in portfolio and revision templates allowed HTML attribute breakout when project names contained single or double quotes.
- **Remediation**: Replaced inline event handlers with `data-cli="..."` attributes and document-level event delegation in [`scripts/lib/portfolio_template.py`](../../scripts/lib/portfolio_template.py), bound under strict Content Security Policy.

### 1.5 Publishing Prose Leakage & Typst Syntax Breakage
- **Vulnerability**: Direct pandoc or typst compilation leaked internal Obsidian wikilinks (`[[Character]]`), raw CriticMarkup deletions (`{--...--}`), and unescaped Typst control characters (`#`, `$`, `@`), causing compiler crashes.
- **Remediation**: Implemented `resolve_prose_for_publication()` and `escape_typst_text()` in [`scripts/lib/publisher.py`](../../scripts/lib/publisher.py). Wikilinks are transformed into clean reading prose, CriticMarkup edits are accepted, and Typst special characters are safely escaped.

### 1.6 Non-Technical Fiction Author Barrier
- **Vulnerability**: Novelists and speculative fiction authors without CLI experience were unable to run terminal commands, inspect continuity alerts, or safely manage configuration files.
- **Remediation**: Created a sovereign **Dual-Surface UX**:
  1. A zero-pip local HTTP server daemon (`src/arcanum/server/daemon.py`) serving an air-gapped HTML5 Visual Studio at `http://127.0.0.1:4242`.
  2. A native Obsidian companion plugin (`templates/world-bible/.obsidian/plugins/ars-arcanum/`) featuring a live status bar health indicator.
  3. A 1-click **"Allow / Intended Twist"** action that automatically updates `constitution.yaml` (`!RULE_ID`), eliminating YAML editing overhead for writers.

---

## 2. Active Quality & Hardening Focus

1. **Strict Type Safety Ratcheting**: Expand strict `mypy` typing across remaining legacy template modules in `scripts/lib/`.
2. **Multi-Volume Benchmark Suite**: Expand corpus benchmarks in `tests/test_benchmark_suite.py` to evaluate sub-second indexing across 800,000-word fantasy series.
3. **Weekly CI Drift Auditing**: The `.github/workflows/ci.yml` weekly cron job (`23 4 * * 1`) continuously guards against upstream toolchain decay, secret leakage, and CDN creep.
