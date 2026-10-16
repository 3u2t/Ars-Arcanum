# Contributing to Ars Arcanum

Thank you for helping build **Ars Arcanum**—the open-source, local-first operating system for speculative fiction writers, storytellers, and worldbuilders!

## 1. Core Engineering Tenets

Before opening a Pull Request, please review [`AGENTS.md`](AGENTS.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md):
- **100% Python `>=3.10` Standard Library Runtime**: Never add third-party PyPI runtime dependencies to `pyproject.toml`.
- **Transactional File Safety**: Always use `atomic_write()` for file writes, `ArcanumLock` for concurrent access, and `is_safe_subpath()` for path validation (`scripts/lib/vault_index.py` / `scripts/lib/fs_utils.py`).
- **100% Offline & Air-Gapped**: Generated HTML/SVG outputs must include the strict `Content-Security-Policy` meta tag and zero external CDN links.
- **Epistemic Humility ([ADR-0001](docs/adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md))**: Keep Subsystem 1 rules strictly deterministic (continuities, schemas, physics, phonotactics) and Subsystem 2 analytics strictly descriptive.

## 2. Local Verification Gates

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
ruff check .
mypy --config-file mypy.ini --explicit-package-bases scripts src tests
bandit -r scripts/lib src/arcanum -ll -ii
```
