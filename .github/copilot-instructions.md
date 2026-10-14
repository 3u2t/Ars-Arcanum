# GitHub Copilot & Coding Agent Instructions for Ars Arcanum

When generating or refactoring code in this repository, strictly follow [`AGENTS.md`](../AGENTS.md):

1. **Zero Third-Party Pip Dependencies**: Use only Python `>=3.10` standard library modules (`pathlib`, `dataclasses`, `json`, `zipfile`, `xml.etree.ElementTree`, `difflib`, `hashlib`, `unittest`).
2. **Use `VaultIndex` for All Vault Walks**: Never write ad-hoc `Path.rglob("*.md")` loops. Import `VaultIndex`, `atomic_write`, `is_safe_subpath`, and `parse_frontmatter` from `lib.vault_index` (or `src.arcanum.core`).
3. **Security & Static Analysis Compliance**:
   - Never use `assert` inside `scripts/lib/` or `src/arcanum/` (raise typed exceptions instead).
   - Annotate `xml.etree.ElementTree` XML parsing of trusted local archives with `# noqa: S314` and `# nosec B314, B405`, and list-based `subprocess.run` calls with `# nosec B603`.
   - Maintain full type annotations (`from __future__ import annotations`) compatible with strict `mypy`.
