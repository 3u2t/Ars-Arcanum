# Contributing to Ars Arcanum

Thank you for helping build **Ars Arcanum**—the sovereign, local-first, 100% offline authoring operating system and craft studio for speculative fiction novelists and worldbuilders!

---

## 1. Core Engineering Tenets & Contracts

Before opening an issue or Pull Request, please familiarize yourself with [`AGENTS.md`](AGENTS.md) and [`docs/codebase/ARCHITECTURE.md`](docs/codebase/ARCHITECTURE.md). Every contribution must uphold six non-negotiable engineering contracts:

1. **Zero-Pip Dependency Guarantee**: Core runtime code across `src/arcanum/` and `scripts/lib/` must rely strictly on the Python `>=3.10` standard library (`json`, `xml.etree.ElementTree`, `zipfile`, `difflib`, `hashlib`, `sqlite3`, `http.server`). Never add third-party PyPI dependencies to `pyproject.toml`.
2. **Transactional File Safety with Windows Retry Backoff**: Every file mutation must use `atomic_write()` (`src/arcanum/core/storage.py`). Writes are staged to a sibling temporary file, flushed with `os.fsync()`, and replaced atomically via `os.replace()`. On Windows, transient file indexer or antivirus locks are absorbed via exponential backoff retry (5 attempts across 320ms).
3. **Physical Inode Separation for Draft Snapshots**: Draft promotions must copy files via `shutil.copy2` to guarantee physical disk inode separation, and apply `0o444` read-only permissions to parent drafts so external text editors (Obsidian, VS Code) cannot corrupt historical baselines.
4. **Cross-Platform Advisory Locking**: Concurrent CLI, daemon, and background watcher processes must acquire `ArcanumLock` (`src/arcanum/core/locking.py`), using `fcntl.flock` on Linux/macOS and `msvcrt.locking` on Windows.
5. **Path Traversal Defense**: Every file reader, exporter, and archive extractor must validate paths with `is_safe_subpath(root, candidate)` (`src/arcanum/core/storage.py`), raising `PathSecurityError` on any directory traversal escape.
6. **Air-Gapped Content Security Policy**: Generated HTML and SVG interfaces must include the strict air-gapped CSP meta header:
   ```html
   <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; media-src data: blob:;">
   ```
   Zero remote CDN links (`https://cdn...`, `unpkg`, `cdnjs`) are permitted.

---

## 2. Codebase Organization

- `src/arcanum/`: Canonical, modular Python packages:
  - `core/`: Storage, locking, cache, config, state, scope, sandbox, diagnostics, migrate, hardening.
  - `manuscript/`: Drafts, diffing, narrative braid, heatmap, word counter, velocity, portfolio, scaffold.
  - `worldbible/`: Continuity runner, epistemics, timeline solver, conlang linter, resource ledger, visualizers.
  - `publishing/`: Zero-pip EPUB3 generator, docx tracked changes, omnibus compiler, preflight, publisher.
  - `ui/`: Theme studio (11 visual themes, 10 Web Audio typewriter models), studio cockpit.
  - `server/`: ThreadingHTTPServer daemon (`127.0.0.1:4242`) and REST API handlers.
- `scripts/lib/`: Backward-compatibility facades re-exporting native symbols from `src/arcanum/`.
- `launchers/`: Windows double-click zero-friction desktop launchers (`launch_studio.bat`, `setup_windows.bat`).
- `templates/`: Sovereign creative vaults (including the native Obsidian companion plugin).
- `tests/`: Standard library `unittest` suites (692 tests passing at 100%).

---

## 3. Local Verification Gates

Before submitting a PR, ensure all quality gates pass locally:

```bash
# 1. Run full test suite (692 tests in ~60s)
python -m unittest discover -s tests -p "test_*.py"

# 2. Verify branch coverage floor (>=80%; currently 81%)
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report --fail-under=80

# 3. Static type safety check (220 source files clean)
mypy --config-file mypy.ini --explicit-package-bases scripts src tests

# 4. AST style and bug linting (0 errors)
ruff check .

# 5. Security AST vulnerability audit
bandit -r scripts/lib src/arcanum -ll -ii

# 6. Verify zero remote CDN links
! grep -rnE "https://(cdn|unpkg|cdnjs|ajax)" scripts/lib/ src/arcanum/
```

---

## 4. Coding Conventions

- **Future Annotations**: All Python modules must begin with `from __future__ import annotations`.
- **Immutable Data Structures**: Use `@dataclass(frozen=True)` for AST nodes, configuration models, and telemetry points.
- **Python 3.10 Compatibility**: Python 3.10 and 3.11 forbid backslashes (`\"`) inside f-string expressions. Always pre-format quotes or escaped characters into distinct local variables before string substitution.
- **Facade Delegation Pattern**: When adding new functionality to `src/arcanum/`, ensure corresponding facades in `scripts/lib/` re-export the public symbols without side effects.
- **Descriptive Telemetry over Normative Dogma**: Never grade creative prose with arbitrary scores. Subsystem 1 enforces deterministic physical, spatial, and chronological invariants, while Subsystem 2 reports objective telemetry.
