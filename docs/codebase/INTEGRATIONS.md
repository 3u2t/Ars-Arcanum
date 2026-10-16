# Local Tool & Format Integrations (`docs/codebase/INTEGRATIONS.md`)

Ars Arcanum integrates deeply with modern authoring software, publication compilers, and local craft environments while remaining 100% offline and sovereign.

---

## 1. Local Visual Web Studio Cockpit

- **Architecture**: Lightweight Python standard library `ThreadingHTTPServer` bound strictly to `127.0.0.1:4242` ([`src/arcanum/server/daemon.py`](../../src/arcanum/server/daemon.py)).
- **Frontend**: Air-gapped, zero-CDN, single-file HTML5/CSS3 application with strict Content Security Policy ([`src/arcanum/ui/studio_app.html`](../../src/arcanum/ui/studio_app.html)).
- **Capabilities**:
  - **Manuscript Catalog**: Instant switching between active novels and universes with real-time word metrics, dialogue ratio, and chapter breakdowns.
  - **Continuity & Twist Assistant**: Point-and-click continuity verification with plain-English alert cards and a 1-click **"Allow / Intended Twist"** rule suppression button (`!RULE_ID` in `constitution.yaml`).
  - **Sprint Engine**: Focused drafting timer with target word tracking, 10 Web Audio typewriter acoustic models, and automatic phase-aware effort point logging.
  - **Theme Studio**: Dynamic switching between 11 visual themes (Dark Cyberpunk, Royal Scriptorium, Parchment Sepia, Monokai Pro, etc.) with WCAG AAA contrast compliance.
  - **Publishing Center**: One-click generation of native EPUB3, sanitized Typst PDF, or Word DOCX files.
- **REST Endpoints**:
  - `GET /api/status`: Local server heartbeat, version, and active sprint status.
  - `GET /api/portfolio`: Discovered manuscripts, acts, chapters, and word metrics.
  - `GET /api/diagnostics`: Consolidated execution of all 4 continuity compilers and narrative braid checks.
  - `POST /api/sprint/start`: Initialize a timed writing session.
  - `POST /api/sprint/stop`: Conclude sprint and commit effort points to `.arcanum/sprint_log.jsonl`.
  - `POST /api/constitution/allow`: Suppress an invariant rule (`!RULE_ID`) inside `constitution.yaml`.
  - `POST /api/action/export`: Trigger asynchronous native EPUB3, Typst, or Pandoc compilation.
  - `GET /api/theme`: Fetch active CSS palette variables and audio typewriter parameters.
  - `GET /api/visualizers/calendar`: Generate celestial calendar wheel SVG.
  - `GET /api/visualizers/conlang`: Generate conlang etymology tree SVG.
  - `GET /api/visualizers/braid`: Generate multi-POV narrative braid chart SVG.

---

## 2. Windows Zero-Friction Desktop Launchers

- **Launcher Script**: [`launchers/launch_studio.bat`](../../launchers/launch_studio.bat)
  - Auto-detects `pythonw` (for silent windowless background execution) or `python`.
  - Launches the sovereign studio server and opens the author's default browser to `http://127.0.0.1:4242`.
- **Setup Script**: [`launchers/setup_windows.bat`](../../launchers/setup_windows.bat)
  - Executes [`scripts/setup_arcanum.ps1`](../../scripts/setup_arcanum.ps1) to configure execution policies and generate a permanent desktop shortcut.

---

## 3. Native Obsidian Companion Plugin

- **Location**: [`templates/world-bible/.obsidian/plugins/ars-arcanum/`](../../templates/world-bible/.obsidian/plugins/ars-arcanum/)
- **Files**: `manifest.json`, `main.js`, `styles.css`.
- **Functionality**:
  - **Status Bar Continuity Badge**: Displays live vault health (`Arcanum: Clean` vs `Arcanum: N Issues`) directly in Obsidian's status bar.
  - **Ribbon Shortcut**: Left-dock ribbon icon that opens the browser Visual Studio Cockpit in one click.
  - **Command Palette Actions**:
    - `Ars Arcanum: Open Visual Studio Cockpit`
    - `Ars Arcanum: Run Continuity Diagnostics`
    - `Ars Arcanum: Start Writing Sprint`
  - **Obsidian Diagnostics Dashboard**: Synchronized with `_Arcanum_Diagnostics.md` native Obsidian callouts (`[!success]`, `[!warning]`).

---

## 4. Microsoft Word & LibreOffice OpenXML (`.docx`)

- **Engine**: [`src/arcanum/publishing/docx.py`](../../src/arcanum/publishing/docx.py) (and facade [`scripts/lib/docx_tracked_changes.py`](../../scripts/lib/docx_tracked_changes.py))
- **Bidirectional Synchronization**:
  - **Export (`arcanum docx-tracked export`)**: Converts Markdown CriticMarkup additions (`{++...++}`), deletions (`{--...--}`), and comments (`{==...==}{>>...<<}`) into native OpenXML `<w:ins>`, `<w:del>`, and `<w:comment>` elements.
  - **Pull (`arcanum docx-tracked pull`)**: Ingests edited Word documents from editors or copyeditors and writes clean CriticMarkup back into the author's Markdown source.
  - **Bomb Hardening**: Enforces safe 64 MB decompression limits and prohibits DOCTYPE entity expansions.

---

## 5. Native Zero-Pip EPUB3 Generation

- **Engine**: [`src/arcanum/publishing/epub.py`](../../src/arcanum/publishing/epub.py)
- **Standard**: Full IDPF EPUB 3.3 and EPUB Accessibility 1.1 compliance.
- **Pure Standard Library**: Uses `zipfile` and `xml.etree.ElementTree` with zero third-party dependencies.
- **Packaging Guarantees**:
  - Uncompressed `mimetype` header stored at exact byte offset 38.
  - Deterministic archive timestamps (`2026-01-01T00:00:00Z`).
  - Automatic `nav.xhtml` navigation landmarks and fallback `toc.ncx` for legacy e-readers.
  - Automatic CriticMarkup resolution and Obsidian wikilink desugaring.

---

## 6. Pure-Python SVG World Visualizers

- **Engine**: [`src/arcanum/worldbible/visualizers.py`](../../src/arcanum/worldbible/visualizers.py)
- **Visual Models**:
  - **Calendar Wheel**: Concentric celestial circles visualizing planetary months, seasonal solstices, and dual-moon phases.
  - **Conlang Etymology Trees**: Hierarchical tree diagrams tracing ancestral proto-roots into modern daughter languages.
  - **Narrative Braid**: Visual multi-POV pacing timelines tracking character stage distribution and POV droughts across chapters.
- **Air-Gapped Embedding**: Standalone SVG markup with embedded styles, directly embeddable in Obsidian notes or Web Studio dashboards.

---

## 7. PolyGlot Lexicon & Phonotactics (`.pgd`)

- **Engine**: [`src/arcanum/worldbible/conlang.py`](../../src/arcanum/worldbible/conlang.py) (and facade [`scripts/lib/conlang_linter.py`](../../scripts/lib/conlang_linter.py))
- **Format**: Reads PolyGlot `.pgd` (ZIP-compressed XML) lexicon databases.
- **Verification**:
  - Audits constructed vocabulary against defined syllable phonotactic templates (`C(C)V(C)`) and morpheme rules (`CON-401..402`).
  - Emits descriptive warnings for illegal consonant clusters or undeclared grammatical roots.

---

## 8. Publishing Compilers (Typst & Pandoc)

- **Engine**: [`src/arcanum/publishing/publisher.py`](../../src/arcanum/publishing/publisher.py)
- **Typst (`typst`)**:
  - Compiles camera-ready print PDFs using mathematical layout algorithms.
  - Automatic escaping of reserved Typst characters (`#`, `$`, `@`, `\`, `[`, `]`).
- **Pandoc (`pandoc`)**:
  - Optional publishing accelerator for compiling alternative manuscript formats.
  - Automatically resolves CriticMarkup (accepting approved revisions) and strips internal Obsidian wikilinks (`[[Target|Label]] -> Label`).

---

## 9. Encrypted Archival Backups (GnuPG)

- **Engine**: [`src/arcanum/core/backup.py`](../../src/arcanum/core/backup.py) (and facade [`scripts/lib/backup.py`](../../scripts/lib/backup.py))
- **Capabilities**: Creates timestamped, milestone-tagged `.tar.xz` archives of narrative vaults with optional GPG asymmetric encryption (`--encrypt <key-id>`).


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
