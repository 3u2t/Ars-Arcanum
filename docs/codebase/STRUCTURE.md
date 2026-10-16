# Repository Directory & Module Structure (`docs/codebase/STRUCTURE.md`)

```text
7-Scriptorium/
├── .github/workflows/                 # Continuous Integration Pipelines
│   ├── ci.yml                         # Multi-linter, mypy, SAST, coverage, and wheel verification
│   └── narrative-continuity-ci.yml    # Multi-Python version continuity matrix (3.10, 3.11, 3.12)
├── configs/                           # Curated Presets and Configuration Files
│   ├── idioms.json                    # Speculative idioms and linguistic presets
│   ├── leechblock_arcanum_rules.json  # Distraction-free author firewall configurations
│   └── plugin_catalog.json            # Curated catalog of tested Obsidian plugins
├── docs/                              # Comprehensive Craft and Engineering Documentation
│   ├── adr/                           # Architectural Decision Records (ADR-0001, etc.)
│   ├── audit/                         # Security and refactor audit reports
│   ├── codebase/                      # Cited technical deep-dive and onboarding guides
│   │   ├── ARCHITECTURE.md            # Definitive, cited master architecture document
│   │   ├── CONCERNS.md                # Architectural concerns and security remediations
│   │   ├── CONVENTIONS.md             # Coding conventions, atomic writes, and locking
│   │   ├── INTEGRATIONS.md            # Dual-Surface API, Obsidian plugin, Word, Typst
│   │   ├── STACK.md                   # Runtime stack, standard library, and zero-pip guarantee
│   │   ├── STRUCTURE.md               # Complete repository directory and module layout
│   │   └── TESTING.md                 # Testing architecture, coverage gates, and commands
│   └── guides/                        # Author manuals, backup tutorials, typography
├── scripts/                           # Primary Runtime Engines & CLI Dispatch
│   ├── arcanum                        # Auto-detecting Python wrapper for POSIX environments
│   ├── ars-arcanum                    # Secondary symlink entry point for package managers
│   ├── setup_arcanum.ps1              # Zero-conf Windows desktop shortcut and environment installer
│   ├── sync_and_verify_docs.py        # Documentation cross-reference synchronizer
│   └── lib/                           # 64 production Python modules (100% standard library)
│       ├── cli.py                     # Primary argument parser and command router
│       ├── cli_handlers.py            # Handler registry mapping commands to engines
│       ├── diff_core.py               # Two-level SHA-256 paragraph diffing and safe draft copy
│       ├── docx_tracked_changes.py    # XML DOM CriticMarkup <-> Word Tracked Changes sync
│       ├── epistemic_firewall.py      # POV secret discovery and spoiler firewall (EPI-*)
│       ├── fs_utils.py                # Atomic file replacement with retry backoff & path confinement
│       ├── lockfile.py                # Cross-platform advisory file locking (fcntl / msvcrt)
│       ├── narrative_braid.py         # POV distribution, drought detection, SVG visualizer (BRD-*)
│       ├── phase_effort_engine.py     # Phase-aware effort points and writing velocity ledger
│       ├── plugin_sandbox.py          # Python subprocess isolation for user plugins
│       ├── publisher.py               # Typst PDF and Pandoc EPUB publication compiler
│       ├── resource_ledger.py         # Hard magic and sci-fi resource conservation auditor (LED-*)
│       ├── studio_server.py           # CLI compatibility shim for local visual web studio
│       ├── timeline_solver.py         # Planetary calendars, Dijkstra route transit physics (TIME-*)
│       ├── typed_constitution.py      # 3-tier policy cascade resolution and !RULE_ID negation
│       ├── vault_continuity_runner.py # Unified continuity suite and _Arcanum_Diagnostics.md bridge
│       └── vault_index.py             # Mtime-cached single Data Access Layer (DAL) for markdown
├── src/arcanum/                       # Canonical Structured Python Package Hierarchy
│   ├── core/                          # Transactional I/O, path confinement, locking, and DAL
│   ├── manuscript/                    # Diffing, effort telemetry, narrative braid, sprint engines
│   ├── worldbible/                    # Epistemic firewall, timeline physics, conlang, and ledger
│   ├── publishing/                    # Tracked changes, Typst/Pandoc publishers, preflight
│   ├── ui/                            # Air-gapped single-file HTML5 Visual Studio Cockpit
│   │   └── studio_app.html            # Zero-CDN, strict CSP local web application
│   └── server/                        # Sovereign local HTTP server daemon and REST handlers
│       ├── daemon.py                  # ThreadingHTTPServer daemon bound to 127.0.0.1:4242
│       └── handlers.py                # REST endpoints for continuity, portfolio, sprints, rules
├── templates/                         # Sovereign Creative Vault Templates
│   ├── demo-cosmos/                   # Eldoria sample fantasy cosmos for integration testing
│   ├── manuscript/                    # Clean novel scaffold with act/chapter metadata structures
│   └── world-bible/                   # Complete worldbuilding vault seed (.rootweave, fileClasses)
│       └── .obsidian/plugins/ars-arcanum/ # Native TypeScript Obsidian companion plugin
│           ├── manifest.json          # Obsidian plugin manifest
│           ├── main.js                # Status bar continuity badge, ribbon, and command palette
│           └── styles.css             # Theme-matched CSS styles
├── tests/                             # 58 standard library unittest suites (540 passing tests)
├── pyproject.toml                     # Project packaging, ruff configuration, coverage settings
├── mypy.ini                           # Strict static typing rules and module exclusions
└── AGENTS.md                          # Sovereign operating manifesto and safety contracts
```
