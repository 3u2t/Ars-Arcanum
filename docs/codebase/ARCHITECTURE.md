# Ars Arcanum — Master System Architecture & Engineering Blueprint
`docs/codebase/ARCHITECTURE.md`

> **Snapshot Identity**: Anchored to commit `f5f54879e4f146ec03f1742b9921198d224c3a00` (`main`) | Release `v0.1.0` | 100% Sovereign Offline Architecture

---

## Part 1 — Whole-Repository Technical Deep-Dive

### 1.1 Repository Identity & Mission
**Ars Arcanum** (Scriptorium) is an open-source, local-first, 100% offline sovereign worldbuilding, narrative continuity, and manuscript engineering operating system designed for speculative fiction (Science Fiction & Fantasy) novelists, storytellers, and worldbuilders ([`README.md#L10`](../../README.md#L10)). It treats the author's narrative vault (`~/Universes/` and `~/Manuscripts/`) as a compilable software repository, enforcing deterministic mathematical, chronological, spatial, linguistic, and epistemic invariants without probabilistic AI hallucination or external network transmission ([`AGENTS.md#L7-L14`](../../AGENTS.md#L7-L14)).

### 1.2 Tech-Stack Detection Table

| Layer | Technology | Version / Pinned Constraint | Evidence (File & Line) |
| :--- | :--- | :--- | :--- |
| **Core Runtime** | Python Standard Library | `>=3.10` (Target: Python 3.10–3.14) | [`pyproject.toml#L10`](../../pyproject.toml#L10), [`AGENTS.md#L28-L30`](../../AGENTS.md#L28-L30) |
| **Build Backend** | `setuptools` | `>=61.0` | [`pyproject.toml#L2-L3`](../../pyproject.toml#L2-L3) |
| **Static Linter & Formatter** | `ruff` | `0.16.8` (Target `py310`) | [`pyproject.toml#L20-L59`](../../pyproject.toml#L20-L59), [`.github/workflows/ci.yml#L58`](../../.github/workflows/ci.yml#L58) |
| **Static Type Checker** | `mypy` | `1.15.0` (Strict on all 220 source files) | [`mypy.ini#L1-L35`](../../mypy.ini#L1-L35), [`.github/workflows/ci.yml#L63`](../../.github/workflows/ci.yml#L63) |
| **Security SAST Scanner** | `bandit` | `1.8.3` (`-ll -ii`) | [`AGENTS.md#L12`](../../AGENTS.md#L12), [`.github/workflows/ci.yml#L68-L69`](../../.github/workflows/ci.yml#L68-L69) |
| **Secret Scanner** | `gitleaks` | `v3.0.0` (Pinned Action) | [`.github/workflows/ci.yml#L51-L55`](../../.github/workflows/ci.yml#L51-L55) |
| **Shell Validator** | `shellcheck` / `bash -n` | Warning level (`-S warning`) | [`.github/workflows/ci.yml#L82-L98`](../../.github/workflows/ci.yml#L82-L98) |
| **Test & Coverage Runner** | `unittest` / `coverage.py` | `coverage 7.6.12` (Fail under: 80% / 81% floor verified) | [`pyproject.toml#L60-L80`](../../pyproject.toml#L60-L80), [`.github/workflows/ci.yml#L78-L80`](../../.github/workflows/ci.yml#L78-L80) |
| **Local Studio Daemon** | `http.server.ThreadingHTTPServer` | Standard Library (`127.0.0.1:4242`) | [`src/arcanum/server/daemon.py#L10-L26`](../../src/arcanum/server/daemon.py#L10-L26) |
| **Visual Studio UI** | Single-File HTML5/CSS3/JS | Air-gapped, Zero-CDN, Strict CSP | [`src/arcanum/ui/studio_app.html#L7-L13`](../../src/arcanum/ui/studio_app.html#L7-L13) |
| **Desktop Companion** | Obsidian Native Plugin | Obsidian API v1.0+ (`manifest.json`) | [`templates/world-bible/.obsidian/plugins/ars-arcanum/manifest.json#L1-L10`](../../templates/world-bible/.obsidian/plugins/ars-arcanum/manifest.json#L1-L10) |
| **Zero-Pip EPUB3 Generator** | Python `zipfile` + `xml.etree` | Native EPUB 3.3 IDPF standard library compiler | [`src/arcanum/publishing/epub.py#L1-L280`](../../src/arcanum/publishing/epub.py#L1-L280) |
| **SVG Visualizers Engine** | Pure-Python XML/SVG | Calendar wheels, conlang trees, narrative braids | [`src/arcanum/worldbible/visualizers.py#L1-L240`](../../src/arcanum/worldbible/visualizers.py#L1-L240) |
| **Theme & Acoustic Studio** | Web Audio API + CSS Variables | 11 visual theme presets, 10 typewriter acoustics | [`src/arcanum/ui/theme.py#L1-L180`](../../src/arcanum/ui/theme.py#L1-L180), [`src/arcanum/ui/studio.py#L1-L120`](../../src/arcanum/ui/studio.py#L1-L120) |
| **Publishing (Print PDF)** | Typst CLI | `0.14.2` (Optional accelerator) | [`src/arcanum/publishing/publisher.py#L116-L140`](../../src/arcanum/publishing/publisher.py#L116-L140), [`.github/workflows/ci.yml#L41`](../../.github/workflows/ci.yml#L41) |
| **Publishing (EPUB/DOCX)** | Pandoc CLI | Optional accelerator | [`src/arcanum/publishing/publisher.py#L170-L220`](../../src/arcanum/publishing/publisher.py#L170-L220), [`.github/workflows/ci.yml#L36`](../../.github/workflows/ci.yml#L36) |
| **Tracked Changes Engine** | `xml.etree.ElementTree` | Standard Library DOM Parser | [`src/arcanum/publishing/docx.py#L20-L60`](../../src/arcanum/publishing/docx.py#L20-L60) |
| **Transactional Storage** | Atomic File Swaps + SQLite FTS5 | Standard Library `sqlite3`, `tempfile` | [`src/arcanum/core/storage.py#L15-L80`](../../src/arcanum/core/storage.py#L15-L80), [`src/arcanum/core/indexer.py#L84-L114`](../../src/arcanum/core/indexer.py#L84-L114) |

---

### 1.3 System Entry Points

1. **Unified CLI Gateway** (`arcanum` / `ars-arcanum`):
   - Entry points: `scripts.lib.cli:main` registered via `pyproject.toml` (`[project.scripts]`) ([`pyproject.toml#L12-L14`](../../pyproject.toml#L12-L14)) and `src.arcanum.cli_bridge:main`.
   - Dispatches subcommands through `scripts/lib/cli_handlers.py` ([`scripts/lib/cli_handlers.py#L40-L120`](../../scripts/lib/cli_handlers.py#L40-L120)) and native package engines.
2. **Sovereign Local Studio Daemon** (`arcanum studio`):
   - Entry point: `src.arcanum.server.daemon:main` ([`src/arcanum/server/daemon.py#L60-L81`](../../src/arcanum/server/daemon.py#L60-L81)) and compatibility shim [`scripts/lib/studio_server.py#L12-L17`](../../scripts/lib/studio_server.py#L12-L17).
   - Serves the air-gapped HTML5 Visual Studio at `http://127.0.0.1:4242` and exposes REST APIs for the native Obsidian Companion Plugin.
3. **Windows Zero-Friction Desktop Launchers**:
   - `launchers/launch_studio.bat`: Double-click launcher that discovers `pythonw` or `python` and starts the studio silently in the background with browser auto-open.
   - `launchers/setup_windows.bat`: One-click setup launcher that configures PowerShell execution and desktop shortcuts via `scripts/setup_arcanum.ps1`.
4. **Native Obsidian Companion Plugin** (`ars-arcanum`):
   - Entry point: `templates/world-bible/.obsidian/plugins/ars-arcanum/main.js` ([`templates/world-bible/.obsidian/plugins/ars-arcanum/main.js#L1-L85`](../../templates/world-bible/.obsidian/plugins/ars-arcanum/main.js#L1-L85)).
   - Renders a status bar continuity badge, adds command palette shortcuts, and provides a one-click ribbon icon opening the Visual Studio.

---

### 1.4 Commands & Verification Inventory

| Command | Purpose | Evidence | CI Gate / Enforced Status |
| :--- | :--- | :--- | :--- |
| `python -m unittest discover -s tests -p "test_*.py"` | Run full test suite (692 tests in ~60s) | [`tests/`](../../tests/), [`pyproject.toml#L60`](../../pyproject.toml#L60) | Enforced in CI ([`.github/workflows/ci.yml#L79`](../../.github/workflows/ci.yml#L79)) |
| `python -m coverage run -m unittest discover -s tests -p "test_*.py"` | Measure code execution branch coverage | [`pyproject.toml#L60-L80`](../../pyproject.toml#L60-L80) | Enforced ($\ge 80\%$ floor; 81% verified) |
| `ruff check .` | AST linting, style, and security rules | [`pyproject.toml#L20-L59`](../../pyproject.toml#L20-L59) | Enforced in CI ([`.github/workflows/ci.yml#L59`](../../.github/workflows/ci.yml#L59)) |
| `mypy --config-file mypy.ini --explicit-package-bases scripts src tests` | Static type checking (220 source files clean) | [`mypy.ini#L1-L35`](../../mypy.ini#L1-L35) | Enforced in CI ([`.github/workflows/ci.yml#L64`](../../.github/workflows/ci.yml#L64)) |
| `bandit -r scripts/lib src/arcanum -ll -ii` | Python AST vulnerability and injection audit | [`AGENTS.md#L12`](../../AGENTS.md#L12) | Enforced in CI ([`.github/workflows/ci.yml#L69`](../../.github/workflows/ci.yml#L69)) |
| `gitleaks detect` | Prevent credential or secret leakage | [`.github/workflows/ci.yml#L51-L55`](../../.github/workflows/ci.yml#L51-L55) | Enforced via GitHub Action |
| `bash -n scripts/*.sh scripts/arcanum` | Syntax validation for POSIX wrappers | [`.github/workflows/ci.yml#L82-L95`](../../.github/workflows/ci.yml#L82-L95) | Enforced in CI |
| `shellcheck -S warning scripts/*.sh scripts/arcanum` | Static analysis for shell wrappers | [`.github/workflows/ci.yml#L98`](../../.github/workflows/ci.yml#L98) | Enforced in CI |
| `python -m build --wheel && pip install dist/*.whl` | Validate wheel build and CLI entry points | [`.github/workflows/ci.yml#L100-L115`](../../.github/workflows/ci.yml#L100-L115) | Enforced in CI |
| `arcanum studio [VAULT] [--port 4242]` | Launch local HTTP studio server and browser UI | [`src/arcanum/server/daemon.py#L60-L78`](../../src/arcanum/server/daemon.py#L60-L78) | Verified via [`tests/test_studio_server.py`](../../tests/test_studio_server.py) |
| `arcanum continuity-suite [VAULT]` | Run all 4 continuity compilers and update dashboard | [`src/arcanum/worldbible/runner.py#L38-L130`](../../src/arcanum/worldbible/runner.py#L38-L130) | Verified in unit and CI runs |
| `arcanum sprint-effort [ARGS]` | Calculate and log phase-aware effort points | [`src/arcanum/manuscript/velocity.py#L280-L360`](../../src/arcanum/manuscript/velocity.py#L280-L360) | Verified in unit and CI runs |
| `arcanum validate-epistemic [VAULT]` | Check POV knowledge barriers (`EPI-201..203`) | [`src/arcanum/worldbible/epistemics.py#L120-L240`](../../src/arcanum/worldbible/epistemics.py#L120-L240) | Verified in unit and CI runs |
| `arcanum timeline-audit [VAULT]` | Check timeline regressions & route physics (`TIME-301..302`) | [`src/arcanum/worldbible/timeline.py#L180-L310`](../../src/arcanum/worldbible/timeline.py#L180-L310) | Verified in unit and CI runs |
| `arcanum conlang-check [ARGS]` | Audit PolyGlot dictionary & syllable phonotactics (`CON-401..402`) | [`src/arcanum/worldbible/conlang.py#L140-L240`](../../src/arcanum/worldbible/conlang.py#L140-L240) | Verified in unit and CI runs |
| `arcanum ledger-audit [VAULT]` | Audit resource conservation pools (`LED-501..502`) | [`src/arcanum/worldbible/ledger.py#L120-L210`](../../src/arcanum/worldbible/ledger.py#L120-L210) | Verified in unit and CI runs |
| `arcanum braid [MANUSCRIPT]` | Generate POV pacing & drought telemetry (`BRD-601`) | [`src/arcanum/manuscript/braid.py#L160-L240`](../../src/arcanum/manuscript/braid.py#L160-L240) | Verified in unit and CI runs |
| `arcanum diff-fast OLD NEW` | SHA-256 paragraph diff & excise cuts $\ge 50$ words | [`src/arcanum/manuscript/diff.py#L347-L368`](../../src/arcanum/manuscript/diff.py#L347-L368) | Verified in unit and CI runs |
| `arcanum docx-tracked [export/pull]` | Bidirectional CriticMarkup $\leftrightarrow$ Word Tracked Changes | [`src/arcanum/publishing/docx.py#L300-L360`](../../src/arcanum/publishing/docx.py#L300-L360) | Verified in unit and CI runs |
| `arcanum count-words [FILE/VAULT]` | Unicode prose, dialogue ratio, and CJK ideograph metrics | [`src/arcanum/manuscript/word_counter.py#L30-L150`](../../src/arcanum/manuscript/word_counter.py#L30-L150) | Verified in unit and CI runs |
| `arcanum doctor [VAULT]` | Toolchain inspection, health diagnostics, and log bundles | [`src/arcanum/core/diagnostics.py#L50-L180`](../../src/arcanum/core/diagnostics.py#L50-L180) | Verified in unit and CI runs |
| `arcanum migrate [VAULT]` | Invariant schema upgrades & vault structure migrations | [`src/arcanum/core/migrate.py#L30-L150`](../../src/arcanum/core/migrate.py#L30-L150) | Verified in unit and CI runs |
| `arcanum publish [MANUSCRIPT] [--format fmt]` | Compile prose to native EPUB3, Typst PDF, or DOCX | [`src/arcanum/publishing/publisher.py#L400-L490`](../../src/arcanum/publishing/publisher.py#L400-L490) | Verified in unit and CI runs |

*CI Enforcement Note*: Both `.github/workflows/ci.yml` and `.github/workflows/narrative-continuity-ci.yml` run on `push` and `pull_request` to `main`, plus weekly drift cron (`23 4 * * 1`). Required status checks on GitHub block merges if any step fails.

---

### 1.5 Directory & Module Layout

```text
7-Scriptorium/
├── .github/workflows/             # Continuous integration and matrix pipelines
│   ├── ci.yml                     # Primary multi-linter, SAST, coverage, and wheel test
│   └── narrative-continuity-ci.yml# Python 3.10/3.11/3.12 multi-version continuity matrix
├── configs/                       # Static JSON configuration files and seed rules
│   ├── idioms.json                # Speculative idiom templates and cultural presets
│   ├── leechblock_arcanum_rules.json # Distraction-blocking firewall configurations
│   └── plugin_catalog.json        # Curated catalog of tested Obsidian companion plugins
├── docs/                          # Comprehensive technical manual and craft guides (70+ docs)
│   ├── adr/                       # Architectural Decision Records (ADR-0001, etc.)
│   ├── codebase/                  # Cited codebase architecture, testing, and stack guides
│   └── guides/                    # Author tutorials, backup setup, typography, and plugins
├── launchers/                     # Zero-friction Windows double-click launchers
│   ├── launch_studio.bat          # One-click desktop studio cockpit launcher
│   └── setup_windows.bat          # One-click Windows setup launcher
├── scripts/                       # Unified CLI and backward-compatibility facades
│   ├── arcanum                    # Bash executable CLI wrapper with auto-Python detection
│   ├── ars-arcanum                # Alternate symlink entrypoint for POSIX package managers
│   ├── setup_arcanum.ps1          # Zero-conf Windows desktop shortcut installer
│   ├── sync_and_verify_docs.py    # Documentation cross-reference and integrity synchronizer
│   └── lib/                       # Backward-compatibility facades (re-exporting native symbols)
├── src/arcanum/                   # Structured modern package tree (100% zero-pip standard library)
│   ├── core/                      # Transactional I/O, storage, locking, cache, config, state, scope, sandbox, diagnostics, migrate
│   ├── manuscript/                # Diffing, drafts, narrative braid, heatmap, word counter, velocity, portfolio, scaffold
│   ├── worldbible/                # Epistemic firewall, timeline physics, conlang, ledger, codex, and SVG visualizers
│   ├── publishing/                # Zero-pip EPUB3 compiler, docx tracked changes, omnibus, preflight, and publisher
│   ├── ui/                        # Theme studio (11 visual themes, 10 Web Audio typewriter models), studio cockpit
│   └── server/                    # Lightweight standard library ThreadingHTTPServer daemon and REST handlers
├── templates/                     # Sovereign creative vault templates and Obsidian seed files
│   ├── demo-cosmos/               # Sample fantasy cosmos (Eldoria) for continuity integration testing
│   ├── manuscript/                # Clean novel scaffold with act/chapter metadata structures
│   └── world-bible/               # Complete worldbuilding vault seed (.rootweave, fileClasses)
│       └── .obsidian/plugins/ars-arcanum/ # Native TypeScript Obsidian companion plugin
├── tests/                         # 692 standard library unittest test suites (100% passing)
├── pyproject.toml                 # Package definition, ruff config, and coverage thresholds
├── mypy.ini                       # Strict static typing rules (220 source files clean)
└── AGENTS.md                      # Sovereign manifesto, safety contracts, and momentum queues
```

---

### 1.6 Deployment & Runtime Surface

| Runtime / Tool | Specification | Surface Pinning Evidence |
| :--- | :--- | :--- |
| **Language Runtime** | Python 3.10, 3.11, 3.12, 3.13, 3.14 | [`pyproject.toml#L10`](../../pyproject.toml#L10), [`.github/workflows/narrative-continuity-ci.yml#L24`](../../.github/workflows/narrative-continuity-ci.yml#L24) |
| **Primary CI Runner** | Ubuntu 24.04 LTS (`noble`) | [`.github/workflows/ci.yml#L20`](../../.github/workflows/ci.yml#L20), [`.github/workflows/narrative-continuity-ci.yml#L20`](../../.github/workflows/narrative-continuity-ci.yml#L20) |
| **GitHub Actions SHAs** | Full 40-character commit hashes | `actions/checkout@3d3c4...`, `actions/setup-python@5fda3...` ([`.github/workflows/ci.yml#L24-L29`](../../.github/workflows/ci.yml#L24-L29)) |
| **Native EPUB3 Engine** | Standard library `zipfile` + `xml.etree` | Pure Python, zero-pip IDPF EPUB 3.3 compliance in [`src/arcanum/publishing/epub.py`](../../src/arcanum/publishing/epub.py) |
| **Typst Compiler** | `typst 0.14.2` | [`.github/workflows/ci.yml#L39-L41`](../../.github/workflows/ci.yml#L39-L41) |
| **Local Host Binding** | `127.0.0.1:4242` | Strictly loopback bound in [`src/arcanum/server/daemon.py#L26`](../../src/arcanum/server/daemon.py#L26) |

### 1.7 EOL & Dead-Dependency Scan
- **Third-Party PyPI Packages**: **0 runtime dependencies**. The production execution runtime is 100% built on the Python standard library. It is immune to supply-chain package takeovers, dependency rot, or deprecations.
- **Python Version EOL**: Support begins at Python 3.10 (active security fixes). CI tests against 3.10, 3.11, and 3.12, while local development verifies against Python 3.14.
- **External Publishing Binaries**: `typst` and `pandoc` are optional publishing accelerators invoked safely via list-form `subprocess.run()`. If missing, the native EPUB3 generator and HTML export operate unconditionally without external binaries.

---

## Part 2 — Context & Ecosystem

### 2.1 Local Checkout Identity

| Attribute | Local Value | Source Verification |
| :--- | :--- | :--- |
| **Remote Origin** | `https://github.com/aryansinghnagar/Ars-Arcanum.git` | `git remote -v` |
| **Active Branch** | `main` | `git branch --show-current` |
| **HEAD Commit** | `f5f54879e4f146ec03f1742b9921198d224c3a00` | `git log -1` |
| **Project Version** | `0.1.0` | [`pyproject.toml#L7`](../../pyproject.toml#L7), [`src/arcanum/__init__.py#L4`](../../src/arcanum/__init__.py#L4) |
| **License** | MIT License | [`LICENSE`](../../LICENSE), [`README.md#L7`](../../README.md#L7) |

### 2.2 Agentic & Engineering Contracts ([`AGENTS.md`](../../AGENTS.md))

The repository enforces six immutable engineering contracts:
1. **Atomic File Writes with Windows Backoff Retry**: All writes to cache files, manuscripts, logs, and diagnostics must use `atomic_write()` (staged via `tempfile.mkstemp`, flushed with `os.fsync()`, and promoted via `os.replace()` with exponential backoff on Windows) ([`AGENTS.md#L19-L20`](../../AGENTS.md#L19-L20), [`src/arcanum/core/storage.py#L15-L80`](../../src/arcanum/core/storage.py#L15-L80)).
2. **Physical Inode Separation for Draft Snapshots**: Draft promotion uses `shutil.copy2` with `0o444` read-only permissions on parent baselines, guaranteeing permanent snapshot immutability against external editors ([`src/arcanum/manuscript/drafts.py#L20-L80`](../../src/arcanum/manuscript/drafts.py#L20-L80)).
3. **Cross-Platform Advisory Locking**: Concurrent CLI, daemon, and watcher access acquires `ArcanumLock` (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows) ([`AGENTS.md#L22-L23`](../../AGENTS.md#L22-L23), [`src/arcanum/core/locking.py#L43-L100`](../../src/arcanum/core/locking.py#L43-L100)).
4. **Path Traversal Defense**: All file readers and exporters strictly validate subpaths with `is_safe_subpath(root, candidate)` before touching disk, raising `PathSecurityError` on symlink or `..` directory escapes ([`AGENTS.md#L25-L26`](../../AGENTS.md#L25-L26), [`src/arcanum/core/storage.py#L82-L105`](../../src/arcanum/core/storage.py#L82-L105)).
5. **Zero-Pip Dependency Guarantee**: Runtime code relies solely on standard library modules (`json`, `xml.etree.ElementTree`, `zipfile`, `difflib`, `hashlib`, `sqlite3`, `http.server`) ([`AGENTS.md#L28-L30`](../../AGENTS.md#L28-L30)).
6. **Content-Security-Policy (CSP)**: All generated HTML/SVG files embed `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;">` and contain zero external CDN script/link tags ([`AGENTS.md#L31-L33`](../../AGENTS.md#L31-L33)).

---

## Part 3 — Architectural Blueprint

### 3.1 C4 Architecture Models

#### Level 1: System Context Diagram

```mermaid
flowchart TD
    Author["Author / Speculative Fiction Novelist"]
    
    subgraph ArsArcanum["Ars Arcanum Sovereign Ecosystem (100% Offline)"]
        Launchers["Windows Launchers (launch_studio.bat)"]
        CLI["Unified CLI (arcanum / src.arcanum.cli_bridge)"]
        Daemon["Local Studio Daemon (127.0.0.1:4242)"]
        WebStudio["Air-Gapped HTML5 Visual Cockpit & Theme Studio"]
        ObsidianPlugin["Native Obsidian Companion Plugin"]
        Compilers["Subsystem 1: Deterministic Continuity Compilers (EPI, TIME, CON, LED)"]
        Telemetry["Subsystem 2: Descriptive Telemetry & Churn (REV, BRD, Effort)"]
        Governance["Subsystem 3: Authorial Governance (constitution.yaml)"]
        PubEngine["Native Zero-Pip EPUB3 & SVG Visualizer Engine"]
    end
    
    Vault["Author Creative Vault (~/Universes/ & ~/Manuscripts/)"]
    PublishingTargets["Publishing Outputs (Native EPUB3, Typst PDF, DOCX)"]
    
    Author -->|Double-Clicks| Launchers
    Author -->|Points & Clicks| WebStudio
    Author -->|Types Prose & Lore| ObsidianPlugin
    Author -->|Executes Commands| CLI
    
    Launchers --> Daemon
    WebStudio <-->|REST JSON| Daemon
    ObsidianPlugin <-->|REST JSON| Daemon
    
    Daemon --> Compilers
    Daemon --> Telemetry
    Daemon --> PubEngine
    CLI --> Compilers
    CLI --> Telemetry
    CLI --> Governance
    CLI --> PubEngine
    
    Compilers -->|Validates Invariants| Vault
    Telemetry -->|Measures Word Churn & Effort| Vault
    Governance -->|Applies Cascading Policies| Vault
    
    PubEngine -->|Compiles Publications| PublishingTargets
```

#### Level 2: Container Diagram (Native Package Hierarchy)

```mermaid
flowchart LR
    subgraph Presentation_Layer["Dual-Surface Presentation Layer"]
        HTML["studio_app.html\n(Visual Web Cockpit)"]
        Obsidian["ars-arcanum plugin\n(Obsidian TS/JS)"]
        CLIBridge["src/arcanum/cli_bridge.py\n(CLI Dispatch)"]
        Launchers["launchers/launch_studio.bat\n(Windows Launcher)"]
    end

    subgraph Server_Layer["Local Server & API Layer"]
        DaemonModule["src/arcanum/server/daemon.py\n(ThreadingHTTPServer)"]
        Handlers["src/arcanum/server/handlers.py\n(REST Handlers)"]
    end

    subgraph Native_Packages["Native Modular Engine Packages (src/arcanum/)"]
        CorePkg["src/arcanum/core/\n(storage, locking, cache, config,\nstate, scope, diagnostics, migrate)"]
        ManuscriptPkg["src/arcanum/manuscript/\n(diff, drafts, braid, heatmap,\nword_counter, velocity, portfolio)"]
        WorldbiblePkg["src/arcanum/worldbible/\n(runner, epistemics, timeline,\nconlang, ledger, visualizers)"]
        PublishingPkg["src/arcanum/publishing/\n(epub, docx, omnibus,\npreflight, publisher)"]
        UIPkg["src/arcanum/ui/\n(theme, studio)"]
    end

    subgraph Storage["Sovereign Vault Storage"]
        MarkdownVault["Markdown Files (*.md)"]
        Frontmatter["YAML Directives"]
        CacheFile[".arcanum_cache.json"]
        Constitution["constitution.yaml"]
    end

    Launchers --> DaemonModule
    HTML <-->|HTTP /api/*| Handlers
    Obsidian <-->|HTTP /api/*| Handlers
    CLIBridge --> Native_Packages
    
    Handlers --> DaemonModule
    Handlers --> Native_Packages
    
    WorldbiblePkg --> CorePkg
    ManuscriptPkg --> CorePkg
    PublishingPkg --> CorePkg
    UIPkg --> CorePkg
    
    CorePkg <--> CacheFile
    CorePkg --> MarkdownVault
    CorePkg --> Frontmatter
    WorldbiblePkg <--> Constitution
```

#### Level 3: Representative Request Lifecycle (1-Click Twist Allowance)

```mermaid
sequenceDiagram
    autonumber
    actor Author as Author (Web Studio / Obsidian)
    participant UI as studio_app.html / main.js
    participant API as ArcanumStudioHandler (server/handlers.py)
    participant Runner as worldbible.runner (WorldContinuityRunner)
    participant Firewall as worldbible.epistemics (EpistemicFirewall)
    participant Const as worldbible.constitution (TypedConstitution)
    participant Storage as core.storage (atomic_write)
    participant Disk as Sovereign Vault (constitution.yaml)

    Author->>UI: Clicks "Check Continuity"
    UI->>API: GET /api/diagnostics
    API->>Runner: run_full_vault_continuity_suite(vault_root)
    Runner->>Const: resolve_constitution_cascade()
    Const-->>Runner: active_rules (e.g. ['*'])
    Runner->>Firewall: audit_epistemic_firewall(vault_index)
    Firewall-->>Runner: violations (e.g. EPI-201 on Chapter 4)
    Runner->>Runner: Filter violations against constitution.is_rule_enabled("EPI-201")
    Runner-->>API: consolidated_report (passed: false, violations: [EPI-201])
    API-->>UI: 200 OK (JSON diagnostics)
    UI-->>Author: Renders Alert Card: "Premature Lore Leak in Chapter 4"

    Author->>UI: Clicks "Allow / Intended Twist"
    UI->>API: POST /api/constitution/allow {"rule_id": "EPI-201"}
    API->>Storage: atomic_write(constitution.yaml, rules: ['!EPI-201'])
    Storage->>Disk: Atomic swap with retry backoff
    API-->>UI: 200 OK {"status": "allowed", "active_rules": ["!EPI-201"]}
    UI-->>Author: Card turns green: "Rule EPI-201 suppressed for this project"
```

---

## Subsystem Deep-Dives

### Subsystem Deep-Dive 1: Deterministic Continuity Compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`)

1. **Epistemic POV Firewall (`src/arcanum/worldbible/epistemics.py`)**:
   - Compares the point-of-view (`pov: <Character>`) of each chapter against the character's chronological knowledge base (`discovered_at: <Chapter>`).
   - Flags premature knowledge leakage (`EPI-201`), post-mortem perception (`EPI-202`), and secret disclosure anomalies (`EPI-203`) by parsing both YAML frontmatter and inline prose wikilinks (`[[LoreEntity]]`).
2. **Timeline & Route Physics Solver (`src/arcanum/worldbible/timeline.py`)**:
   - Parses custom planetary calendars (`days_per_year`, `months`, `leap_rules`) and calculates chronological day indices.
   - Evaluates inter-location journey vectors using a Dijkstra shortest-path route graph across biomes (`plains: 20 mi/day`, `mountains: 8 mi/day`).
   - Emits `TIME-301` for impossible transit speeds and `TIME-302` for chronological regressions (with full exemption for `@flashback: true` chapters).
3. **PolyGlot Conlang Linter (`src/arcanum/worldbible/conlang.py`)**:
   - Imports `.pgd` (PolyGlot dictionary XML) using bomb-hardened parsers.
   - Validates fictional words against defined syllable phonotactic templates (`C(C)V(C)`) and morpheme clusters (`CON-401..402`).
4. **Hard Magic & Sci-Fi Resource Ledger (`src/arcanum/worldbible/ledger.py`)**:
   - Tracks consumable inventory and energy pools (mana, ether, ammunition, delta-v) across sequential chapters.
   - Flags conservation violations where characters consume resources they do not possess (`LED-501..502`).
5. **Cross-Vault Series Federation**:
   - Multi-book sagas can specify a shared `world_root` in `manuscript_config.json`. The continuity compilers seamlessly resolve character POVs, lore definitions, and timeline benchmarks across multiple independent novel vaults.

---

### Subsystem Deep-Dive 2: Native Zero-Pip EPUB3 & SVG World Visualizers

1. **Zero-Pip EPUB3 Compiler (`src/arcanum/publishing/epub.py`)**:
   - Standard-library-only EPUB 3.3 generator using `zipfile` and `xml.etree.ElementTree`.
   - Generates compliant Open Container Format (OCF) archives with uncompressed `mimetype` as the first entry (offset 38), deterministic timestamps (2026-01-01), and clean XML navigation documents (`nav.xhtml`).
   - Automatically sanitizes CriticMarkup annotations (`{++...++}`, `{--...--}`), escapes XML entities, and embeds cover art metadata without third-party tools.
2. **SVG World Visualizers (`src/arcanum/worldbible/visualizers.py`)**:
   - **Calendar Wheel**: Generates multi-ring SVG celestial charts visualizing orbital months, seasonal solstices, and dual-moon phases.
   - **Conlang Etymology Trees**: Emits hierarchical SVG node-link trees mapping ancestral proto-roots into modern daughter languages.
   - **Narrative Braid**: Visualizes character POV pacing, stage presence, and narrative droughts over manuscript acts.

---

### Subsystem Deep-Dive 3: Theme Studio & Procedural Typewriter Audio

1. **Theme Studio Engine (`src/arcanum/ui/theme.py`)**:
   - Defines 11 built-in visual presets: `Dark Cyberpunk`, `Royal Scriptorium`, `Parchment Sepia`, `Solarized Dark`, `Monokai Pro`, `Nordic Frost`, `Dracula Gothic`, `Forest Moss`, `Alabaster Light`, `Obsidian Monochrome`, and `High Contrast Gold`.
   - Generates CSS custom property palettes with WCAG AAA compliant contrast ratios and air-gapped typography font stacks.
2. **Procedural Typewriter Acoustics (`src/arcanum/ui/studio.py`)**:
   - Synthesizes 10 acoustic mechanical typewriter models via pure browser Web Audio API oscillator nodes (no external audio assets or network downloads):
     - `Underwood Model 5`, `Remington Standard`, `Smith Corona Sterling`, `Hermes 3000`, `Olympia SM9`, `IBM Selectric II`, `Imperial Good Companion`, `Olivetti Lettera 32`, `Royal Quiet De Luxe`, `Adler Gabriele 35`.
   - Each model simulates mechanical key-down strike clicks, resonant metal basket rings, carriage return bell chimes, and spacebar clatter with physical acoustic parameters (frequency, Q-factor, decay).

---

### Subsystem Deep-Dive 4: System Doctor & Schema Migration Engine

1. **World Doctor Diagnostics (`src/arcanum/core/diagnostics.py`)**:
   - Audits local developer environment, inspecting Python version, Git status, optional CLI accelerators (`pandoc`, `typst`, `shellcheck`, `ruff`), and GTK desktop environments.
   - Generates anonymized, redacted bug report ZIP bundles containing configuration dumps, system doctor logs, and sanitized tracebacks.
2. **Schema Migration Engine (`src/arcanum/core/migrate.py`)**:
   - Automatically detects and migrates legacy vault directory schemas to modern standards:
     - Promotes `05-Backups/` to top-level `Backups/`.
     - Promotes `04-Publishing/` to top-level `Exports/`.
     - Syncs `.gitignore` rules to safeguard ephemeral `.arcanum_cache.json` and internal lockfiles.

---

## Part 4 — Confidence Assessment

| Architectural Claim Area | Confidence Level | Verification Rationale |
| :--- | :--- | :--- |
| **Zero-Pip Standard Library Runtime** | **High** | Verified by inspecting all imports in `src/arcanum/` and `scripts/lib/`, passing CI wheel builds without third-party dependencies. |
| **692 Unit Test Pass Rate** | **High** | Verified locally via `unittest discover` (Ran 692 tests in 63.8s, 0 failures, 0 errors, 2 skipped, 100% pass rate). |
| **Mypy Static Typing** | **High** | Verified clean across all 220 source files with strict type-checking flags. |
| **Test Coverage $\ge 80\%$** | **High** | Measured via `coverage.py` at **81% total branch coverage** floor across `src/arcanum` and `scripts/lib`. |
| **Cross-Platform Advisory Locking** | **High** | Tested on POSIX (`fcntl`) and Windows (`msvcrt`) in `tests/test_audit_hardening.py` and `tests/test_core_locking_storage.py`. |
| **Physical Inode Copying on Draft Promotion** | **High** | Verified in `src/arcanum/manuscript/drafts.py` and `scripts/lib/diff_core.py` via `shutil.copy2` and `os.chmod(..., 0o444)`. |
| **Local Studio REST API Lifecycle** | **High** | Verified via automated unit tests in `tests/test_studio_server.py`. |
| **CI Merge Blocking Enforcement** | **High** | Verified in `.github/workflows/ci.yml` and `.github/workflows/narrative-continuity-ci.yml`. |

---

## Footnotes — Local File Citations

1. [`pyproject.toml`](../../pyproject.toml) — Package definition, script entry points, ruff configuration, and coverage thresholds.
2. [`AGENTS.md`](../../AGENTS.md) — Non-negotiable safety contracts, atomic write specifications, and offline principles.
3. [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — GitHub Actions CI definition, tool versions, and security audits.
4. [`src/arcanum/core/storage.py`](../../src/arcanum/core/storage.py) — Master transactional I/O (`atomic_write`) with Windows backoff retry and path confinement.
5. [`src/arcanum/core/locking.py`](../../src/arcanum/core/locking.py) — Cross-platform advisory locking (`ArcanumLock`).
6. [`src/arcanum/core/diagnostics.py`](../../src/arcanum/core/diagnostics.py) — Doctor toolchain diagnostics and redacted bug bundle exporter.
7. [`src/arcanum/core/migrate.py`](../../src/arcanum/core/migrate.py) — Legacy vault schema upgrade and folder restructuring engine.
8. [`src/arcanum/manuscript/diff.py`](../../src/arcanum/manuscript/diff.py) — Two-level SHA-256 paragraph diffing and scrap harvesting.
9. [`src/arcanum/manuscript/drafts.py`](../../src/arcanum/manuscript/drafts.py) — Safe draft promotion via physical disk inode copying and read-only locks.
10. [`src/arcanum/manuscript/word_counter.py`](../../src/arcanum/manuscript/word_counter.py) — Unicode prose word counts, dialogue ratios, and CJK ideograph metrics.
11. [`src/arcanum/worldbible/epistemics.py`](../../src/arcanum/worldbible/epistemics.py) — POV knowledge firewall and spoiler boundary auditing.
12. [`src/arcanum/worldbible/timeline.py`](../../src/arcanum/worldbible/timeline.py) — Custom planetary calendars, Dijkstra route transit physics, and flashback exemptions.
13. [`src/arcanum/worldbible/conlang.py`](../../src/arcanum/worldbible/conlang.py) — PolyGlot dictionary import, syllable phonotactics, and XML-safe parsing.
14. [`src/arcanum/worldbible/ledger.py`](../../src/arcanum/worldbible/ledger.py) — Hard magic and sci-fi resource conservation auditor.
15. [`src/arcanum/worldbible/visualizers.py`](../../src/arcanum/worldbible/visualizers.py) — Pure-Python SVG calendar wheels, conlang etymology trees, and narrative braid charts.
16. [`src/arcanum/publishing/epub.py`](../../src/arcanum/publishing/epub.py) — Zero-pip native standard-library EPUB3 generation engine.
17. [`src/arcanum/publishing/docx.py`](../../src/arcanum/publishing/docx.py) — XML DOM bidirectional CriticMarkup $\leftrightarrow$ Word Tracked Changes sync.
18. [`src/arcanum/ui/theme.py`](../../src/arcanum/ui/theme.py) — 11 visual theme presets and WCAG AAA CSS palette generator.
19. [`src/arcanum/ui/studio.py`](../../src/arcanum/ui/studio.py) — 10 procedural mechanical typewriter acoustic models via Web Audio API.
20. [`src/arcanum/server/daemon.py`](../../src/arcanum/server/daemon.py) — Zero-pip multi-threaded local HTTP daemon.
21. [`launchers/launch_studio.bat`](../../launchers/launch_studio.bat) — Windows double-click zero-friction studio launcher.
22. [`launchers/setup_windows.bat`](../../launchers/setup_windows.bat) — Windows automated setup launcher.
