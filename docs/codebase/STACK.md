# Technical Stack & Runtime Surface (`docs/codebase/STACK.md`)

## 1. Core Runtime Stack

| Layer | Implementation | Version / Constraints | Evidence |
| :--- | :--- | :--- | :--- |
| **Language Runtime** | Python Standard Library | `>=3.10` (Tested on 3.10, 3.11, 3.12, 3.13, 3.14) | [`pyproject.toml#L10`](../../pyproject.toml#L10) |
| **PyPI Dependencies** | **Zero Third-Party Packages** | `0` runtime dependencies | [`AGENTS.md#L28-L30`](../../AGENTS.md#L28-L30) |
| **Packaging & Build** | `setuptools` | `>=61.0` | [`pyproject.toml#L2-L3`](../../pyproject.toml#L2-L3) |
| **Local Studio Daemon** | `http.server.ThreadingHTTPServer` | Standard Library (`127.0.0.1:4242`) | [`src/arcanum/server/daemon.py#L22-L26`](../../src/arcanum/server/daemon.py#L22-L26) |
| **Visual Studio UI** | Single-File HTML5/CSS3/Vanilla JS | Air-gapped, Zero-CDN, Strict CSP | [`src/arcanum/ui/studio_app.html#L7-L13`](../../src/arcanum/ui/studio_app.html#L7-L13) |
| **Desktop Companion** | Native JavaScript/CSS Plugin | Obsidian API v1.0+ | [`templates/world-bible/.obsidian/plugins/ars-arcanum/manifest.json`](../../templates/world-bible/.obsidian/plugins/ars-arcanum/manifest.json) |
| **Native EPUB3 Compiler** | Standard Library `zipfile` + `xml.etree` | Zero-pip IDPF EPUB 3.3 compliant | [`src/arcanum/publishing/epub.py`](../../src/arcanum/publishing/epub.py) |
| **SVG Visualizers Engine** | Pure-Python XML/SVG | Calendar wheels, conlang trees, narrative braids | [`src/arcanum/worldbible/visualizers.py`](../../src/arcanum/worldbible/visualizers.py) |
| **Theme & Audio Engine** | Pure Web Audio API + CSS Variables | 11 visual theme presets, 10 typewriter acoustic models | [`src/arcanum/ui/theme.py`](../../src/arcanum/ui/theme.py), [`src/arcanum/ui/studio.py`](../../src/arcanum/ui/studio.py) |

---

## 2. Standard Library Modules Utilized

The entire production engine is assembled from Python standard library primitives:
- **`json`**: AST serialization, `.arcanum_cache.json`, `.draft_lineage.json`, `.arcanum/sprint_log.jsonl`, and studio REST API payloads.
- **`xml.etree.ElementTree`**: Secure, entity-safe parsing and generation of OpenXML Word documents (`.docx`), PolyGlot conlang dictionaries (`.pgd`), Scrivener projects, and native EPUB3 package XML (`content.opf`, `toc.ncx`, `nav.xhtml`).
- **`zipfile`**: Archive processing with decompression bomb limits (enforcing $\le 64\text{ MB}$ uncompressed limits and $\le 100:1$ ratio) and native EPUB3 package assembly with uncompressed `mimetype` headers.
- **`difflib`**: Word-level diffing algorithms (`SequenceMatcher`) layered on top of SHA-256 paragraph hashes.
- **`hashlib`**: Deterministic 16-character SHA-256 paragraph hashes for $O(1)$ equality checks.
- **`unicodedata`**: Unicode-aware prose counting, CriticMarkup stripping, and CJK ideograph segmentation (`src/arcanum/manuscript/word_counter.py`).
- **`sqlite3`**: Embedded FTS5 full-text search indexing across entire narrative vaults (`src/arcanum/core/indexer.py`).
- **`tempfile` / `os` / `shutil`**: Atomic sibling file staging (`tempfile.mkstemp`), `os.fsync()`, atomic `os.replace()`, and physical disk inode copying (`shutil.copy2`).
- **`fcntl` / `msvcrt`**: Cross-platform advisory locking (`ArcanumLock`) absorbing concurrency between CLI, background daemons, and desktop editors.
- **`http.server` / `urllib`**: Multi-threaded local HTTP server and REST endpoints.
- **`unittest`**: Comprehensive test suite providing continuous verification across 692 test cases.

---

## 3. Optional Publishing & Encryption Accelerators

External command-line binaries are purely optional accelerators invoked via list-argument `subprocess.run()`, never via shell string interpolation:

1. **Typst (`typst`)**: Version `0.14.2` used for sub-second, mathematical-grade print PDF typesetting ([`src/arcanum/publishing/publisher.py#L116`](../../src/arcanum/publishing/publisher.py#L116)).
2. **Pandoc (`pandoc`)**: Optional accelerator for compiling multi-chapter manuscripts to alternative formats ([`src/arcanum/publishing/publisher.py#L170`](../../src/arcanum/publishing/publisher.py#L170)). *Note: Native standard-library EPUB3 generation is available without Pandoc via `src/arcanum/publishing/epub.py`.*
3. **GnuPG (`gpg`)**: Used for optional encrypted archival backups of author vaults ([`src/arcanum/core/backup.py`](../../src/arcanum/core/backup.py)).

---

## 4. Development & CI Quality Stack

- **`ruff` (`0.16.8`)**: High-performance AST linter checking imports, bug patterns, code quality, and security invariants across all files.
- **`mypy` (`1.15.0`)**: Static type checking enforcing strict typing across all 220 source files in `src/arcanum`, `scripts`, and `tests`.
- **`bandit` (`1.8.3`)**: Security static analysis scanning for subprocess safety and injection risks (`-ll -ii`).
- **`coverage.py` (`7.6.12` / `7.15.1`)**: Branch test coverage monitoring enforcing an 80% coverage threshold in CI (currently at 81% verified).
- **`shellcheck`**: POSIX shell script static analysis with warning thresholds.


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
