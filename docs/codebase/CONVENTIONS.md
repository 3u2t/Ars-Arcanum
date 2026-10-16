# Coding & Engineering Conventions (`docs/codebase/CONVENTIONS.md`)

## 1. Core Engineering Contracts

All modules in `scripts/lib/` and `src/arcanum/` must adhere to these five non-negotiable safety contracts ([`AGENTS.md`](../../AGENTS.md)):

### 1.1 Atomic File Mutations
Every file mutation—updating `.arcanum_cache.json`, `.arcanum/sprint_log.jsonl`, `_Arcanum_Diagnostics.md`, or chapter prose—must use `atomic_write()` ([`scripts/lib/vault_index.py#L84-L114`](../../scripts/lib/vault_index.py#L84-L114)):
1. Create a sibling temporary file via `tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))`.
2. Flush user-space buffers with `.flush()`, followed by hardware sync `os.fsync(handle.fileno())`.
3. Promote atomically via `os.replace()`.
4. On Windows, catch transient `PermissionError` locks (from indexers or antivirus) and retry with exponential backoff across 5 attempts (20ms, 40ms, 80ms, 160ms, 320ms).

### 1.2 Physical Inode Separation on Draft Promotion
When promoting a manuscript draft to a new milestone via `promote_draft_hardlinked()` ([`scripts/lib/diff_core.py#L304-L335`](../../scripts/lib/diff_core.py#L304-L335)):
- Use `shutil.copy2` to guarantee physical disk inode separation between parent and child drafts.
- Set `0o444` read-only permissions on all files in the parent draft to prevent accidental mutation by external text editors (Obsidian, VS Code).
- Maintain `.draft_lineage.json` and `.locked` metadata files.

### 1.3 Path Traversal Confinement
Every file reader, exporter, and archive extractor must validate candidate paths with `is_safe_subpath(vault_root, candidate)` before accessing disk ([`scripts/lib/vault_index.py#L70-L81`](../../scripts/lib/vault_index.py#L70-L81)). Raise `PathSecurityError` immediately if any path escapes the sovereign vault root.

### 1.4 Zero-Pip Dependency Guarantee
Core runtime execution must rely strictly on the Python `>=3.10` standard library. No third-party PyPI dependencies may be added to `scripts/lib/` or `src/arcanum/`.

### 1.5 Air-Gapped Content Security Policy (CSP)
All HTML/SVG reports, visualizers, and web cockpits must embed:
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;">
```
Zero remote CDN links (`https://cdn...`, `unpkg`, `cdnjs`) are permitted.

---

## 2. Python Code Style & Typing Standards

- **Future Annotations**: All modules must begin with:
  ```python
  from __future__ import annotations
  ```
- **Frozen Dataclasses**: Data structures representing AST nodes, telemetry points, and configuration rules must be immutable:
  ```python
  @dataclass(frozen=True)
  class VaultDocumentNode:
      ...
  ```
- **Python 3.10 F-String Constraints**: In Python 3.10 and 3.11, backslashes (`\"`) are forbidden inside f-string expressions. Format escaped content into local variables before interpolation.
- **Typing Strictness**: Refactored modules must have full type annotations (`disallow_untyped_defs = True` in `mypy.ini`).

---

## 3. Diagnostic Code Namespaces

The continuity and telemetry engines emit standardized diagnostic codes:

| Namespace | Category | Subsystem | Description |
| :--- | :--- | :--- | :--- |
| `REV-101..106` | Revision Churn | Subsystem 2 (Descriptive) | Revision churn metrics: pristine, turnover $>50\%$, heavy compression, narrative expansion. |
| `EPI-201..203` | Epistemic Firewall | Subsystem 1 (Deterministic) | POV knowledge boundaries: premature knowledge discovery, post-mortem perception, secret disclosure anomalies. |
| `TIME-301..302` | Timeline & Physics | Subsystem 1 (Deterministic) | Temporal invariants: impossible travel velocities (Dijkstra route graph) and chronological sequence regressions. |
| `CON-401..402` | Conlang Phonotactics | Subsystem 1 (Deterministic) | Constructed language linter: illegal syllable structures, invalid phoneme clusters. |
| `LED-501..502` | Resource Ledger | Subsystem 1 (Deterministic) | Hard magic / sci-fi conservation: resource over-consumption, negative inventory balances. |
| `BRD-601` | Narrative Braid | Subsystem 2 (Descriptive) | Multi-POV pacing: character perspective droughts exceeding author-defined chapter thresholds. |

---

## 4. Prose & Markup Conventions

- **CriticMarkup**: Supported for tracked changes in Markdown prose:
  - Addition: `{++added text++}`
  - Deletion: `{--deleted text--}`
  - Substitution: `{~~original~>replacement~~}`
  - Highlight & Comment: `{==highlighted text==}{>>editorial comment<<}`
- **Obsidian Wikilinks**: Internal lore references use `[[Target]]` or `[[Target|Alias]]`. When publishing for print or external distribution, `publisher.py` automatically resolves these to clean reading prose (`Alias` or `Target`).
- **Frontmatter Directives**: Chapter frontmatter supports typed directives:
  - `pov: <CharacterName>`
  - `date: <PlanetaryDateString>`
  - `location: <LocationName>`
  - `flashback: true` (exempts chapter from `TIME-302` regression alerts)
  - `state_delta: { <Entity>: { <resource>: <delta_value> } }`
