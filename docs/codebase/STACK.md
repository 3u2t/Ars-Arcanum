# Technical Stack & Runtime Surface (`docs/codebase/STACK.md`)

## 1. Core Runtime Stack

| Layer | Implementation | Version / Constraints | Evidence |
| :--- | :--- | :--- | :--- |
| **Language Runtime** | Python Standard Library | `>=3.10` (Tested on 3.10, 3.11, 3.12, 3.14) | [`pyproject.toml#L10`](../../pyproject.toml#L10) |
| **PyPI Dependencies** | **Zero Third-Party Packages** | `0` runtime dependencies | [`AGENTS.md#L28-L30`](../../AGENTS.md#L28-L30) |
| **Packaging & Build** | `setuptools` | `>=61.0` | [`pyproject.toml#L2-L3`](../../pyproject.toml#L2-L3) |
| **Local Studio Daemon** | `http.server.ThreadingHTTPServer` | Standard Library (`127.0.0.1:4242`) | [`src/arcanum/server/daemon.py#L22-L26`](../../src/arcanum/server/daemon.py#L22-L26) |
| **Visual Studio UI** | Single-File HTML5/CSS3/Vanilla JS | Air-gapped, Zero-CDN, Strict CSP | [`src/arcanum/ui/studio_app.html#L7-L13`](../../src/arcanum/ui/studio_app.html#L7-L13) |
| **Obsidian Companion** | Native JavaScript/CSS Plugin | Obsidian API v1.0+ | [`templates/world-bible/.obsidian/plugins/ars-arcanum/manifest.json`](../../templates/world-bible/.obsidian/plugins/ars-arcanum/manifest.json) |

---

## 2. Standard Library Modules Utilized

The entire production engine is assembled from Python standard library primitives:
- **`json`**: AST serialization, `.arcanum_cache.json`, `.draft_lineage.json`, and studio REST API payloads.
- **`xml.etree.ElementTree`**: Secure, entity-safe parsing and generation of OpenXML Word documents (`.docx`), PolyGlot conlang dictionaries (`.pgd`), and Scrivener projects.
- **`zipfile`**: Archive processing with decompression bomb limits (enforcing $\le 64\text{ MB}$ uncompressed limits and $\le 100:1$ ratio).
- **`difflib`**: Word-level diffing algorithms (`SequenceMatcher`) layered on top of SHA-256 paragraph hashes.
- **`hashlib`**: Deterministic 16-character SHA-256 paragraph hashes for $O(1)$ equality checks.
- **`sqlite3`**: Embedded FTS5 full-text search indexing across entire narrative vaults (`vault_search.py`).
- **`tempfile` / `os` / `shutil`**: Atomic sibling file staging (`tempfile.mkstemp`), `os.fsync()`, atomic `os.replace()`, and physical inode copying (`shutil.copy2`).
- **`http.server` / `urllib`**: Multi-threaded local HTTP server and REST endpoints.
- **`unittest`**: 58 test suites providing continuous verification across 540 test cases.

---

## 3. Optional Publishing & Encryption Accelerators

External command-line binaries are purely optional accelerators invoked via list-argument `subprocess.run()`, never via shell string interpolation:

1. **Typst (`typst`)**: Version `0.14.2` used for sub-second, mathematical-grade print PDF typesetting ([`scripts/lib/publisher.py#L116`](../../scripts/lib/publisher.py#L116)).
2. **Pandoc (`pandoc`)**: Used for compiling multi-chapter manuscripts to EPUB3 and standard manuscript format (.docx) ([`scripts/lib/publisher.py#L170`](../../scripts/lib/publisher.py#L170)).
3. **GnuPG (`gpg`)**: Used for optional encrypted archival backups of author vaults ([`scripts/lib/backup.py`](../../scripts/lib/backup.py)).

---

## 4. Development & CI Quality Stack

- **`ruff` (`0.16.8`)**: High-performance AST linter checking imports, bug patterns, code quality, and security invariants.
- **`mypy` (`1.15.0`)**: Static type checking enforcing strict typing across refactored continuity and core modules.
- **`bandit` (`1.8.3`)**: Security static analysis scanning for subprocess safety and injection risks (`-ll -ii`).
- **`coverage.py` (`7.6.12` / `7.15.1`)**: Branch test coverage monitoring enforcing an 80% coverage threshold in CI.
- **`shellcheck`**: POSIX shell script static analysis with warning thresholds.
