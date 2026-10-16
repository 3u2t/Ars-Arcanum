# Testing & Quality Assurance Architecture (`docs/codebase/TESTING.md`)

## 1. Test Suite Overview

Ars Arcanum maintains an automated standard library `unittest` verification suite with a **100% pass rate** requirement across all modules:

- **Total Test Suites**: 58 test modules in `tests/`.
- **Total Tests Executed**: **540 unit and integration tests**.
- **Execution Performance**: Complete suite executes in $\approx 40$ seconds.
- **Code Coverage**: **81% total branch coverage** across `scripts/lib/` and `src/arcanum/` (exceeds the $\ge 80\%$ CI threshold).
- **Static Typing**: 152 source files verified with **0 errors** via `mypy`.
- **Linting**: 100% clean check via `ruff`.

---

## 2. Canonical Verification Commands

### Run Full Test Suite
```bash
# Discover and run all 540 tests
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
# Run a specific test suite
python -m unittest tests.test_studio_server

# Run a single test method
python -m unittest tests.test_studio_server.TestStudioServer.test_status_endpoint
```

### Static Analysis, Linting & Type Safety
```bash
# Fast AST linting
ruff check .

# Strict static type safety check
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
| [`tests/test_studio_server.py`](../../tests/test_studio_server.py) | Local HTTP Server & API | Status, portfolio, diagnostics, sprint start/stop, constitution allow (`!RULE_ID`), CORS OPTIONS, 404s |
| [`tests/test_audit_hardening.py`](../../tests/test_audit_hardening.py) | Security Invariants | Atomic writes with backoff, path traversal defense, ZIP/XML bomb safety, advisory locking |
| [`tests/test_phases2_3_and_features.py`](../../tests/test_phases2_3_and_features.py) | Continuity Compilers | Epistemic firewall (`EPI-*`), timeline solver (`TIME-*`), conlang linter (`CON-*`), resource ledger (`LED-*`), narrative braid (`BRD-*`) |
| [`tests/test_diff_core.py`](../../tests/test_diff_core.py) | Manuscript Diffing | Two-level SHA-256 paragraph diffs, scrap extraction ($\ge 50$ words), draft promotion inode copying |
| [`tests/test_publisher.py`](../../tests/test_publisher.py) | Publishing Pipeline | Typst character escaping, CriticMarkup resolution, wikilink stripping, EPUB/DOCX compilation |
| [`tests/test_docx_tracked_changes.py`](../../tests/test_docx_tracked_changes.py) | Tracked Changes | XML DOM `<w:ins>`, `<w:del>`, `<w:comment>` preservation and round-trip conversion |
| [`tests/test_phase_effort_engine.py`](../../tests/test_phase_effort_engine.py) | Velocity & Effort | Phase-weighted effort multipliers (Drafting, Lore, Polish), sprint logging, burnout risk |
| [`tests/test_typed_constitution.py`](../../tests/test_typed_constitution.py) | Governance | 3-tier policy cascades, rule negation (`!RULE_ID`), frozen dataclass models |
