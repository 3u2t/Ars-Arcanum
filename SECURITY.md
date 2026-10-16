# Security Policy (`SECURITY.md`)

## Supported Versions & Sovereign Security Posture

| Version | Supported | Runtime Dependencies | Security Architecture |
| :--- | :--- | :--- | :--- |
| `0.1.x` (`main`) | ✅ Yes | Zero-Pip (`100%` Python `>=3.10` Stdlib) | `is_safe_subpath`, `atomic_write`, `ArcanumLock`, `plugin_sandbox.py`, strict CSP |

## Security Controls Enforced in Production

1. **Path Traversal Confinement (`is_safe_subpath`)**: Every file read, write, cache update, and `.docx`/`.pgd` archive operation in `scripts/lib/vault_index.py` and `scripts/lib/fs_utils.py` verifies that target paths resolve strictly inside the Sovereign Vault root (`PathSecurityError`).
2. **Subprocess Plugin Isolation (`scripts/lib/plugin_sandbox.py`)**: Custom user plugins in `.arcanum/plugins/*.py` execute inside an isolated `python3 -I -B` subprocess with a sanitized environment (`PATH=/usr/bin:/bin`), a 1 MB stdout cap, and a 5.0-second wall-clock timeout.
3. **Air-Gapped HTML/SVG Visualizers (`Content-Security-Policy`)**: All HTML outputs (`narrative_braid.py`, `portfolio.py`, `revision_heatmap.py`, `manuscript_diff.py`, `codex_export.py`) enforce `default-src 'none'; style-src 'unsafe-inline'; img-src data:;` and contain zero external CDN URLs.
4. **Transactional File Integrity (`atomic_write` & `ArcanumLock`)**: All file writes stage to a sibling tempfile (`os.fsync`) and promote atomically via `os.replace`, preserving OS hardlinks across immutable `Draft-*` snapshots.
