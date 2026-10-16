# Changelog

All notable changes to **Ars Arcanum** are documented in this file.
This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [0.1.0] - 2026-10-16

### Added
- **Visual Web Studio Cockpit & Local Daemon (`src/arcanum/server/daemon.py`, `src/arcanum/ui/studio_app.html`)**:
  - Sovereign, air-gapped `ThreadingHTTPServer` bound strictly to `127.0.0.1:4242` with zero network transmission.
  - Single-file HTML5/CSS3 cockpit enforcing strict Content-Security-Policy (`default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; media-src data: blob:;`).
  - Four integrated studios: Manuscript Catalog, Continuity & Twist Assistant, Sprint Engine, and Publishing Center.
- **Native Obsidian Companion Plugin (`templates/world-bible/.obsidian/plugins/ars-arcanum/`)**:
  - Real-time status bar continuity badge (`Arcanum: Clean` vs `Arcanum: N Issues`).
  - One-click ribbon icon opening the Visual Studio Cockpit in the user's default browser.
  - Native command palette shortcuts for running diagnostics and writing sprints.
- **1-Click "Allow / Intended Twist" Rule Suppression (`!RULE_ID`)**:
  - Dynamic negation pattern in `constitution.yaml` allowing deliberate authorial twists without disabling entire continuity compilers.
- **Native Zero-Pip EPUB3 Compiler (`src/arcanum/publishing/epub.py`)**:
  - Pure standard-library EPUB 3.3 and EPUB Accessibility 1.1 generator using `zipfile` and `xml.etree.ElementTree`.
  - Enforces uncompressed `mimetype` header at byte offset 38, deterministic timestamps, semantic navigation documents (`nav.xhtml`), fallback `toc.ncx`, and automatic CriticMarkup resolution.
- **Pure-Python SVG World Visualizers (`src/arcanum/worldbible/visualizers.py`)**:
  - Concentric celestial calendar wheels visualizing planetary months, dual-moon phases, and seasonal solstices.
  - Hierarchical node-link conlang etymology trees tracing proto-roots into modern daughter languages.
  - Visual multi-POV narrative braid swimlanes showing character pacing and perspective droughts across acts.
- **Theme Studio & Procedural Typewriter Acoustics (`src/arcanum/ui/theme.py`, `src/arcanum/ui/studio.py`)**:
  - 11 WCAG AAA compliant visual theme presets (Sovereign Dark, Classic Light, Amber CRT, Cyber Neon, Synthwave Outrun, Illuminated Codex, Grimdark Iron, etc.).
  - 10 mechanical typewriter acoustic models synthesized on the fly via the browser Web Audio API (Underwood, Remington, Selectric II, Smith Corona, Cherry Blue, Thock, Cyber Terminal, Steampunk, Scribe Quill, Gothic Relic).
- **Unicode Prose Word Counter & Literary Metrics (`src/arcanum/manuscript/word_counter.py`)**:
  - Unicode-aware prose word counting, CriticMarkup revision stripping, dialogue vs. exposition ratio calculation, and CJK ideograph segmentation.
- **System Doctor & Diagnostic Bundler (`src/arcanum/core/diagnostics.py`)**:
  - Automated inspection of developer toolchain (`python`, `git`, `typst`, `pandoc`, `ruff`, `shellcheck`, GTK).
  - Generation of redacted, anonymized bug report ZIP bundles stripping author prose and sensitive tokens.
- **Schema Migration Engine (`src/arcanum/core/migrate.py`)**:
  - Automatic Schema 1.0 upgrade and non-destructive folder restructuring (`05-Backups/` $\to$ `Backups/`, `04-Publishing/` $\to$ `Exports/`, `.gitignore` invariant sync).
- **Windows Zero-Friction Double-Click Launchers (`launchers/launch_studio.bat`, `launchers/setup_windows.bat`)**:
  - One-click desktop shortcuts and background `pythonw` studio launching for non-technical fiction writers.
- **Cross-Vault Series Federation**:
  - Support for `world_root` directive in `manuscript_config.json`, enabling multi-book sagas to share a single master universe bible.

### Changed
- **Draft Promotion Physical Inode Separation**:
  - Transitioned `promote_draft_hardlinked()` in `src/arcanum/manuscript/drafts.py` and `scripts/lib/diff_core.py` to use `shutil.copy2` for physical inode separation.
  - Set `0o444` read-only permissions on parent draft directories, ensuring text editors (Obsidian, VS Code) cannot mutate historical baselines.
- **Windows File Indexer Backoff Retry**:
  - Added exponential retry backoff (5 attempts across 320ms) inside `atomic_write()` in `src/arcanum/core/storage.py` and `scripts/lib/fs_utils.py` to absorb transient indexer/antivirus locks on Windows.
- **Cross-Platform Advisory Locking**:
  - Unified `ArcanumLock` (`src/arcanum/core/locking.py`, `scripts/lib/lockfile.py`) utilizing `fcntl.flock` on Linux/macOS and `msvcrt.locking` on Windows.
- **Modular Native Package Migration**:
  - Migrated all engine implementations into structured Python packages under `src/arcanum/` (`core`, `manuscript`, `worldbible`, `publishing`, `ui`, `server`).
  - Refactored `scripts/lib/` modules into 100% backward-compatible facades re-exporting native symbols.
- **Test Suite & Type Safety Expansion**:
  - Test suite expanded to **692 unit and integration tests passing at 100%** (690 passed, 2 skipped, 0 failures, 0 errors).
  - Static type checking verified clean across all **220 source files** in strict `mypy` mode.
  - Branch test coverage verified at **81%** across all packages.
