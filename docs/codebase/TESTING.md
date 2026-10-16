# Testing & Quality Assurance Architecture (`docs/codebase/TESTING.md`)

## 1. Test Suite Overview

Ars Arcanum maintains an automated standard library `unittest` verification suite with a **100% pass rate** requirement across all modules:

- **Total Test Suites**: 75 test modules in `tests/`.
- **Total Tests Executed**: **692 unit and integration tests** (690 passed, 2 skipped, 0 failures, 0 errors).
- **Execution Performance**: Complete suite executes in $\approx 60$ seconds.
- **Code Coverage**: **81% total branch coverage** across `src/arcanum/` and `scripts/lib/` (exceeds the $\ge 80\%$ CI threshold).
- **Static Typing**: **220 source files verified with 0 errors** in strict mode via `mypy`.
- **Linting**: 100% clean check via `ruff` (0 errors).

---

## 2. Canonical Verification Commands

### Run Full Test Suite
```bash
# Discover and run all 692 tests
python -m unittest discover -s tests -p "test_*.py"
```

### Run with Coverage Measurement
```bash
# Execute tests with branch coverage tracking
coverage run -m unittest discover -s tests -p "test_*.py"

# Generate report and verify against 80% coverage floor
coverage report --fail-under=80
```

### Run an Individual Test File or Test Case
```bash
# Run a specific native test suite
python -m unittest tests.test_epub_builder
python -m unittest tests.test_visualizers
python -m unittest tests.test_ui_theme_native

# Run a single test method
python -m unittest tests.test_studio_server.TestStudioServer.test_status_endpoint
```

### Run Benchmarks & Scalability Tests
```bash
# Run multi-volume 800,000-word vault indexing and cache benchmarks
python -m unittest tests.test_benchmark_suite
```

### Static Analysis, Linting & Type Safety
```bash
# Fast AST linting
ruff check .

# Strict static type safety check across all 220 source files
mypy --config-file mypy.ini --explicit-package-bases scripts src tests

# Security AST vulnerability scan
bandit -r scripts/lib src/arcanum -ll -ii
```

### Offline & Sovereign Security Assertions
```bash
# Verify air-gapped isolation (zero remote CDN links in engines)
! grep -rnE "https://(cdn|unpkg|cdnjs|ajax)" scripts/lib/ src/arcanum/
```

### Shell Script Syntax & Style Validation
```bash
# Bash syntax verification
bash -n scripts/arcanum scripts/ars-arcanum

# ShellCheck static analysis
shellcheck -S warning scripts/*.sh scripts/arcanum scripts/ars-arcanum
```

---

## 3. Test Organization by Domain

| Test Module | Domain Covered | Key Test Cases |
| :--- | :--- | :--- |
| [`tests/test_epub_builder.py`](../../tests/test_epub_builder.py) | Native Zero-Pip EPUB3 | Compliant OCF packaging, uncompressed `mimetype` header (offset 38), deterministic timestamps, `nav.xhtml` TOC, CriticMarkup sanitization |
| [`tests/test_visualizers.py`](../../tests/test_visualizers.py) | Pure-Python SVG Visualizers | Multi-moon circular calendar wheels, conlang etymology trees, narrative braid matrices |
| [`tests/test_ui_theme_native.py`](../../tests/test_ui_theme_native.py) | Theme Studio & Audio | 11 visual theme presets, WCAG AAA palette generator, 10 procedural Web Audio typewriter acoustic models |
| [`tests/test_core_diagnostics_native.py`](../../tests/test_core_diagnostics_native.py) | Toolchain Doctor | System health inspection (Python, Git, Pandoc, Typst, Ruff), rotating loggers, redacted bug report ZIP bundles |
| [`tests/test_core_migrate_native.py`](../../tests/test_core_migrate_native.py) | Schema Migration | Schema 1.0 upgrade engine, `05-Backups/` $\to$ `Backups/`, `04-Publishing/` $\to$ `Exports/`, `.gitignore` invariant sync |
| [`tests/test_manuscript_word_counter_native.py`](../../tests/test_manuscript_word_counter_native.py) | Prose Metrics | Unicode word counting, CriticMarkup stripping, CJK ideograph segmentation, dialogue ratio calculation |
| [`tests/test_core_locking_storage.py`](../../tests/test_core_locking_storage.py) | Transactional I/O | Atomic writes with Windows backoff retry, path traversal confinement, cross-platform `ArcanumLock` |
| [`tests/test_worldbible_continuity_native.py`](../../tests/test_worldbible_continuity_native.py) | Continuity Compilers | Epistemic POV discovery (`EPI-*`), timeline route physics (`TIME-*`), conlang phonotactics (`CON-*`), resource ledger (`LED-*`) |
| [`tests/test_federated_continuity.py`](../../tests/test_federated_continuity.py) | Series Federation | Cross-vault continuity resolution via `world_root` across multi-book sagas |
| [`tests/test_benchmark_suite.py`](../../tests/test_benchmark_suite.py) | Performance Benchmarks | Sub-150ms cached indexing and sub-1s cold scans across 800,000-word multi-volume sagas |
| [`tests/test_studio_server.py`](../../tests/test_studio_server.py) | Local Studio API | Status, portfolio, diagnostics, sprint start/stop, constitution allow (`!RULE_ID`), CORS OPTIONS, 404s |
| [`tests/test_audit_hardening.py`](../../tests/test_audit_hardening.py) | Security Invariants | Atomic writes with backoff, path traversal defense, ZIP/XML bomb safety, advisory locking |
| [`tests/test_manuscript_diff.py`](../../tests/test_manuscript_diff.py) | Manuscript Diffing | Two-level SHA-256 paragraph diffs, scrap extraction ($\ge 50$ words), draft promotion inode copying |
| [`tests/test_publishing_native.py`](../../tests/test_publishing_native.py) | Publishing Pipeline | Typst character escaping, CriticMarkup resolution, wikilink stripping, EPUB/DOCX compilation |
| [`tests/test_docx_tracked_changes.py`](../../tests/test_docx_tracked_changes.py) | Tracked Changes | XML DOM `<w:ins>`, `<w:del>`, `<w:comment>` preservation and round-trip conversion |
| [`tests/test_manuscript_velocity_native.py`](../../tests/test_manuscript_velocity_native.py) | Velocity & Effort | Phase-weighted effort multipliers (Drafting, Lore, Polish), sprint logging, burnout risk |


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
