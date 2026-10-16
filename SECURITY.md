# Security Policy & Defense-in-Depth Specification (`SECURITY.md`)

Ars Arcanum is engineered from the ground up as a **100% sovereign, local-first, air-gapped authoring operating system**. Because author vaults contain unpublished literary intellectual property, private worldbuilding bibles, and sensitive creative notes, the codebase enforces an uncompromising defense-in-depth security architecture.

---

## 1. Supported Versions & Sovereign Posture

| Version | Status | Third-Party Dependencies | Security Architecture & Defense In Depth |
| :--- | :--- | :--- | :--- |
| **`0.1.x` (`main`)** | ✅ **Active** | **Zero-Pip** (`100%` Python `>=3.10` Standard Library) | Strict CSP, `is_safe_subpath`, `atomic_write` with Windows retry backoff, `ArcanumLock`, physical disk inode separation, bounded archive parsers, loopback-only daemon |

---

## 2. Core Security Controls Enforced in Production

### 2.1 Path Traversal Defense (`is_safe_subpath`)
Every file reader, writer, cache updater, and archive extractor in `src/arcanum/core/storage.py` and `scripts/lib/fs_utils.py` validates candidate paths with `is_safe_subpath(root, candidate)` before touching disk. If any path attempts to escape the sovereign vault root via symlinks, relative segments (`..`), or NTFS alternate data streams, execution is halted immediately with a `PathSecurityError`.

### 2.2 Transactional Writes & Windows Backoff Retry
All mutations to `.arcanum_cache.json`, `.arcanum/sprint_log.jsonl`, `_Arcanum_Diagnostics.md`, and prose chapter files use `atomic_write()` (`src/arcanum/core/storage.py`):
1. Content is staged to a sibling temporary file created via `tempfile.mkstemp` in the same directory.
2. User-space buffers are flushed, followed by a hardware sync with `os.fsync()`.
3. The file is promoted atomically via `os.replace()`.
4. On Windows, transient file indexer or antivirus locks are absorbed using exponential backoff retry (up to 5 attempts across 320ms) before re-raising errors.

### 2.3 Physical Inode Separation & Read-Only Draft Locks
Draft promotion (`src/arcanum/manuscript/drafts.py`) copies manuscript chapters using `shutil.copy2` to guarantee physical disk inode separation between parent and child draft versions. Parent baseline files are set to `0o444` read-only permissions, ensuring external text editors (Obsidian, VS Code) cannot accidentally mutate historical draft baselines.

### 2.4 Cross-Platform Advisory File Locking (`ArcanumLock`)
Concurrent access across CLI commands, background HTTP daemons, and background watchers is synchronized via `ArcanumLock` (`src/arcanum/core/locking.py`), utilizing `fcntl.flock` on Linux/macOS and `msvcrt.locking` on Windows.

### 2.5 Archive & Decompression Bomb Protection
When parsing OpenXML Word documents (`.docx`), PolyGlot conlang databases (`.pgd`), Scrivener archives, or EPUB packages:
- Decompression size is capped at $64\text{ MB}$.
- Decompression ratio is bounded at $100:1$ to prevent ZIP bombs.
- XML parsing strictly disables external entity resolution (`DOCTYPE` entity expansions) to prevent quadratic entity expansion and SSRF vulnerabilities.

### 2.6 Air-Gapped Content Security Policy (CSP)
Every generated HTML visualizer (`studio_app.html`, `portfolio`, `revision_heatmap`, `narrative_braid`, `theme_studio`) embeds a strict air-gapped Content-Security-Policy header:
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; media-src data: blob:;">
```
Zero remote CDN script tags (`https://cdn...`, `unpkg`, `cdnjs`) or fonts are permitted anywhere in the repository.

### 2.7 Local Loopback Confinement
The local studio daemon (`src/arcanum/server/daemon.py`) binds strictly to loopback `127.0.0.1:4242` and explicitly rejects non-local host headers. No prose or telemetry is ever transmitted over external networks.

### 2.8 Subprocess Plugin Isolation (`src/arcanum/core/sandbox.py`)
Custom author plugins in `.arcanum/plugins/*.py` run inside an isolated `python -I -B` subprocess with:
- Sanitized environment variables (`PATH=/usr/bin:/bin`, `HOME=/tmp`).
- Standard streams capped at $1\text{ MB}$.
- Strict $5.0$-second wall-clock execution timeouts.

---

## 3. Reporting a Vulnerability

If you discover a potential security vulnerability in Ars Arcanum:

1. **Do not open a public GitHub issue.**
2. Send a detailed report via encrypted email or GitHub Private Security Advisories.
3. Include:
   - Affected module and line citations.
   - Proof of concept (PoC) demonstrating the bypass or vulnerability.
   - Recommended remediation strategy.
4. The maintainers will acknowledge receipt within 48 hours and work with you on a private fix and coordinated disclosure.
