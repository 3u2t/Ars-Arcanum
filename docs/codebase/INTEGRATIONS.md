# Local Tool & Format Integrations (`docs/codebase/INTEGRATIONS.md`)

Ars Arcanum integrates deeply with modern authoring software, publication compilers, and local craft environments while remaining 100% offline and sovereign.

---

## 1. Local Visual Web Studio Cockpit

- **Architecture**: Lightweight Python standard library `ThreadingHTTPServer` bound strictly to `127.0.0.1:4242` ([`src/arcanum/server/daemon.py`](../../src/arcanum/server/daemon.py)).
- **Frontend**: Air-gapped, zero-CDN, single-file HTML5/CSS3 application with strict Content Security Policy ([`src/arcanum/ui/studio_app.html`](../../src/arcanum/ui/studio_app.html)).
- **Capabilities**:
  - **Manuscript Catalog**: Instant switching between active novels and universes with real-time word metrics.
  - **Continuity & Twist Assistant**: Point-and-click continuity verification with plain-English alert cards and a 1-click **"Allow / Intended Twist"** rule suppression button.
  - **Sprint Engine**: Focused drafting timer with target word tracking, Web Audio synthesized chimes, and automatic phase-aware effort point logging.
  - **Publishing Center**: One-click generation of sanitized Typst PDF, Pandoc EPUB, or Word DOCX files.
- **REST Endpoints**:
  - `GET /api/status`: Local server heartbeat, version, and active sprint status.
  - `GET /api/portfolio`: Discovered manuscripts, acts, chapters, and word metrics.
  - `GET /api/diagnostics`: Consolidated execution of all 4 continuity compilers and narrative braid checks.
  - `POST /api/sprint/start`: Initialize a timed writing session.
  - `POST /api/sprint/stop`: Conclude sprint and commit effort points to `.arcanum/sprint_log.jsonl`.
  - `POST /api/constitution/allow`: Suppress an invariant rule (`!RULE_ID`) inside `constitution.yaml`.
  - `POST /api/action/export`: Trigger asynchronous Typst or Pandoc manuscript compilation.

---

## 2. Native Obsidian Companion Plugin

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

## 3. Microsoft Word & LibreOffice OpenXML (`.docx`)

- **Engine**: [`scripts/lib/docx_tracked_changes.py`](../../scripts/lib/docx_tracked_changes.py)
- **Bidirectional Synchronization**:
  - **Export (`arcanum docx-tracked export`)**: Converts Markdown CriticMarkup additions (`{++...++}`), deletions (`{--...--}`), and comments (`{==...==}{>>...<<}`) into native OpenXML `<w:ins>`, `<w:del>`, and `<w:comment>` elements.
  - **Pull (`arcanum docx-tracked pull`)**: Ingests edited Word documents from editors or copyeditors and writes clean CriticMarkup back into the author's Markdown source.
  - **Bomb Hardening**: Enforces safe 64 MB decompression limits and prohibits DOCTYPE entity expansions.

---

## 4. PolyGlot Lexicon & Phonotactics (`.pgd`)

- **Engine**: [`scripts/lib/conlang_linter.py`](../../scripts/lib/conlang_linter.py)
- **Format**: Reads PolyGlot `.pgd` (ZIP-compressed XML) lexicon databases.
- **Verification**:
  - Audits constructed vocabulary against defined syllable phonotactic templates (`C(C)V(C)`) and morpheme rules (`CON-401..402`).
  - Emits descriptive warnings for illegal consonant clusters or undeclared grammatical roots.

---

## 5. Publishing Compilers (Typst & Pandoc)

- **Engine**: [`scripts/lib/publisher.py`](../../scripts/lib/publisher.py)
- **Typst (`typst`)**:
  - Compiles camera-ready print PDFs using mathematical layout algorithms.
  - Automatic escaping of reserved Typst characters (`#`, `$`, `@`, `\`, `[`, `]`).
- **Pandoc (`pandoc`)**:
  - Compiles standard e-book packages (EPUB3) and standard manuscript format (.docx).
  - Automatically resolves CriticMarkup (accepting approved revisions) and strips internal Obsidian wikilinks (`[[Target|Label]] -> Label`).

---

## 6. Encrypted Archival Backups (GnuPG)

- **Engine**: [`scripts/lib/backup.py`](../../scripts/lib/backup.py)
- **Capabilities**: Creates timestamped, milestone-tagged `.tar.xz` archives of narrative vaults with optional GPG asymmetric encryption (`--encrypt <key-id>`).
