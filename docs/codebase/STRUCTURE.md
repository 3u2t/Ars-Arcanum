# Repository Directory & Module Structure (`docs/codebase/STRUCTURE.md`)

Ars Arcanum utilizes a dual-surface architecture: modern modular Python packages reside under `src/arcanum/`, while `scripts/lib/` houses 100% backward-compatible facades that re-export native symbols for legacy scripts and entry points.

```text
7-Scriptorium/
├── .github/workflows/                 # Continuous Integration Pipelines
│   ├── ci.yml                         # Multi-linter, mypy, SAST, coverage, and wheel verification
│   └── narrative-continuity-ci.yml    # Multi-Python version continuity matrix (3.10, 3.11, 3.12)
├── configs/                           # Curated Presets and Configuration Files
│   ├── idioms.json                    # Speculative idioms and linguistic presets
│   ├── leechblock_arcanum_rules.json  # Distraction-free author firewall configurations
│   └── plugin_catalog.json            # Curated catalog of tested Obsidian plugins
├── docs/                              # Comprehensive Craft and Engineering Documentation (70+ docs)
│   ├── adr/                           # Architectural Decision Records (ADR-0001, etc.)
│   ├── codebase/                      # Cited technical deep-dive and onboarding guides
│   │   ├── ARCHITECTURE.md            # Definitive, cited master architecture document
│   │   ├── CONCERNS.md                # Architectural concerns and security remediations
│   │   ├── CONVENTIONS.md             # Coding conventions, atomic writes, and locking
│   │   ├── INTEGRATIONS.md            # Dual-Surface API, Obsidian plugin, Word, Typst
│   │   ├── STACK.md                   # Runtime stack, standard library, and zero-pip guarantee
│   │   ├── STRUCTURE.md               # Complete repository directory and module layout
│   │   └── TESTING.md                 # Testing architecture, coverage gates, and commands
│   └── guides/                        # Author manuals, backup tutorials, typography
├── launchers/                         # Zero-Friction Windows Double-Click Launchers
│   ├── launch_studio.bat              # One-click desktop studio cockpit launcher
│   └── setup_windows.bat              # One-click Windows setup launcher
├── scripts/                           # Primary Runtime Engines & CLI Dispatch
│   ├── arcanum                        # Auto-detecting Python wrapper for POSIX environments
│   ├── ars-arcanum                    # Secondary symlink entry point for package managers
│   ├── setup_arcanum.ps1              # Zero-conf Windows desktop shortcut and environment installer
│   ├── sync_and_verify_docs.py        # Documentation cross-reference synchronizer
│   └── lib/                           # Backward-compatibility facades (re-exporting from src/arcanum/)
│       ├── cli.py                     # Primary argument parser and command router
│       ├── cli_handlers.py            # Handler registry mapping commands to engines
│       ├── diff_core.py               # Facade for src.arcanum.manuscript.diff
│       ├── docx_tracked_changes.py    # Facade for src.arcanum.publishing.docx
│       ├── epistemic_firewall.py      # Facade for src.arcanum.worldbible.epistemics
│       ├── fs_utils.py                # Facade for src.arcanum.core.storage
│       ├── lockfile.py                # Facade for src.arcanum.core.locking
│       ├── narrative_braid.py         # Facade for src.arcanum.manuscript.braid
│       ├── phase_effort_engine.py     # Facade for src.arcanum.manuscript.velocity
│       ├── plugin_sandbox.py          # Facade for src.arcanum.core.sandbox
│       ├── publisher.py               # Facade for src.arcanum.publishing.publisher
│       ├── resource_ledger.py         # Facade for src.arcanum.worldbible.ledger
│       ├── studio_server.py           # Facade for src.arcanum.server.daemon
│       ├── timeline_solver.py         # Facade for src.arcanum.worldbible.timeline
│       ├── typed_constitution.py      # Facade for src.arcanum.worldbible.constitution
│       ├── vault_continuity_runner.py # Facade for src.arcanum.worldbible.runner
│       └── vault_index.py             # Facade for src.arcanum.core.indexer
├── src/arcanum/                       # Canonical Structured Python Package Hierarchy (100% Stdlib)
│   ├── cli_bridge.py                  # CLI bridge connecting arcanum command dispatch to native engines
│   ├── core/                          # Transactional I/O, storage, locking, cache, config, diagnostics
│   │   ├── backup.py                  # Archive snapshots and GPG-encrypted backups
│   │   ├── cache.py                   # Mtime-invalidated AST and token caching
│   │   ├── config.py                  # Hierarchical configuration loader and cascaded settings
│   │   ├── diagnostics.py             # World Doctor toolchain inspector and redacted bug bundle exporter
│   │   ├── frontmatter.py             # YAML frontmatter parser and header injector
│   │   ├── hardening.py               # Lite profile enforcer, security asserts, and directory confinement
│   │   ├── indexer.py                 # SQLite FTS5 indexer and document node parser
│   │   ├── locking.py                 # Cross-platform advisory lock (ArcanumLock: fcntl/msvcrt)
│   │   ├── migrate.py                 # Schema 1.0 upgrade and vault restructuring engine
│   │   ├── registry/                  # Extensible plugin and engine registry specs
│   │   ├── restore.py                 # Vault snapshot restoration and validation
│   │   ├── sandbox.py                 # Subprocess sandbox for third-party plugin execution
│   │   ├── scope.py                   # Manuscript and universe scope resolver
│   │   ├── snapshot.py                # Point-in-time immutable manuscript snapshots
│   │   ├── state.py                   # Persistent session and workspace state management
│   │   └── storage.py                 # Transactional atomic writes with Windows retry backoff
│   ├── manuscript/                    # Manuscript craft, word telemetry, diffing, and structure
│   │   ├── braid.py                   # Multi-POV narrative distribution and drought detection (BRD-601)
│   │   ├── diff.py                    # Two-level SHA-256 paragraph diffing and scrap archiver
│   │   ├── drafts.py                  # Physical disk inode draft promotion with 0o444 read-only locks
│   │   ├── heatmap.py                 # Revision churn heatmap visualizer (REV-*)
│   │   ├── importer.py                # Scrivener, Word, and text manuscript importer
│   │   ├── portfolio.py               # Multi-volume universe portfolio dashboard
│   │   ├── scaffold.py                # Act/Chapter scaffolding and book templating
│   │   ├── velocity.py                # Phase-aware effort point calculator and burnout forecaster
│   │   └── word_counter.py            # Unicode prose counting, CriticMarkup stripping, dialogue/CJK ratios
│   ├── worldbible/                    # Speculative continuity compilers and worldbuilding engines
│   │   ├── codex.py                   # Fictional encyclopedia and codex exporter
│   │   ├── conlang.py                 # PolyGlot XML parser and syllable phonotactic linter (CON-*)
│   │   ├── constitution.py            # 3-tier policy cascade and 1-click rule negation (!RULE_ID)
│   │   ├── epistemics.py              # Character POV knowledge firewall and spoiler auditor (EPI-*)
│   │   ├── ledger.py                  # Hard magic and sci-fi resource conservation auditor (LED-*)
│   │   ├── runner.py                  # Master continuity runner and _Arcanum_Diagnostics.md generator
│   │   ├── timeline.py                # Planetary calendars, Dijkstra route transit physics (TIME-*)
│   │   └── visualizers.py             # Pure-Python SVG calendar wheels, conlang trees, narrative braids
│   ├── publishing/                    # Book compilation, format conversion, and print preflight
│   │   ├── docx.py                    # Bidirectional CriticMarkup <-> Word Tracked Changes sync
│   │   ├── epub.py                    # Zero-pip native IDPF EPUB 3.3 packaging engine
│   │   ├── omnibus.py                 # Multi-novel omnibus compiler and series builder
│   │   ├── preflight.py               # Pre-publication layout and asset validator
│   │   └── publisher.py               # Typst PDF, Pandoc EPUB, and prose sanitizer
│   ├── ui/                            # Presentation, visual themes, and acoustic typewriter models
│   │   ├── studio.py                  # Procedural Web Audio typewriter acoustics (10 physical models)
│   │   ├── theme.py                   # 11 visual theme presets and WCAG AAA CSS palette generator
│   │   └── studio_app.html            # Air-gapped single-file HTML5 Visual Studio Cockpit
│   └── server/                        # Sovereign local HTTP server daemon and REST handlers
│       ├── daemon.py                  # ThreadingHTTPServer daemon bound strictly to 127.0.0.1:4242
│       └── handlers.py                # REST endpoints for continuity, portfolio, sprints, and themes
├── templates/                         # Sovereign Creative Vault Templates
│   ├── demo-cosmos/                   # Eldoria sample fantasy cosmos for integration testing
│   ├── manuscript/                    # Clean novel scaffold with act/chapter metadata structures
│   └── world-bible/                   # Complete worldbuilding vault seed (.rootweave, fileClasses)
│       └── .obsidian/plugins/ars-arcanum/ # Native TypeScript Obsidian companion plugin
│           ├── manifest.json          # Obsidian plugin manifest
│           ├── main.js                # Status bar continuity badge, ribbon, and command palette
│           └── styles.css             # Theme-matched CSS styles
├── tests/                             # 692 standard library unittest test suites (100% passing)
├── pyproject.toml                     # Project packaging, ruff configuration, coverage settings
├── mypy.ini                           # Strict static typing rules across all 220 source files
└── AGENTS.md                          # Sovereign operating manifesto and safety contracts
```


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
