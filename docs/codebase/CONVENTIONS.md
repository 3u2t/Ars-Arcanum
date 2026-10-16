# Coding & Engineering Conventions (`docs/codebase/CONVENTIONS.md`)

## 1. Core Engineering Contracts

All modules in `src/arcanum/` and `scripts/lib/` must adhere to these six non-negotiable safety contracts ([`AGENTS.md`](../../AGENTS.md)):

### 1.1 Atomic File Mutations with Windows Backoff Retry
Every file mutation—updating `.arcanum_cache.json`, `.arcanum/sprint_log.jsonl`, `_Arcanum_Diagnostics.md`, or chapter prose—must use `atomic_write()` ([`src/arcanum/core/storage.py#L15-L80`](../../src/arcanum/core/storage.py#L15-L80)):
1. Create a sibling temporary file via `tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))`.
2. Flush user-space buffers with `.flush()`, followed by hardware sync `os.fsync(handle.fileno())`.
3. Promote atomically via `os.replace()`.
4. On Windows, catch transient `PermissionError` locks (from indexers or antivirus) and retry with exponential backoff across 5 attempts (20ms, 40ms, 80ms, 160ms, 320ms).

### 1.2 Physical Inode Separation on Draft Promotion
When promoting a manuscript draft to a new milestone via `promote_draft_hardlinked()` ([`src/arcanum/manuscript/drafts.py`](../../src/arcanum/manuscript/drafts.py) and [`scripts/lib/diff_core.py`](../../scripts/lib/diff_core.py)):
- Use `shutil.copy2` to guarantee physical disk inode separation between parent and child drafts.
- Set `0o444` read-only permissions on all files in the parent draft to prevent accidental mutation by external text editors (Obsidian, VS Code).
- Maintain `.draft_lineage.json` and `.locked` metadata files.

### 1.3 Path Traversal Confinement
Every file reader, exporter, and archive extractor must validate candidate paths with `is_safe_subpath(vault_root, candidate)` before accessing disk ([`src/arcanum/core/storage.py#L82-L105`](../../src/arcanum/core/storage.py#L82-L105)). Raise `PathSecurityError` immediately if any path escapes the sovereign vault root.

### 1.4 Cross-Platform Advisory Locking
Concurrent CLI operations, background HTTP daemons, and file watchers must acquire `ArcanumLock` ([`src/arcanum/core/locking.py`](../../src/arcanum/core/locking.py)), using `fcntl.flock` on POSIX and `msvcrt.locking` on Windows.

### 1.5 Zero-Pip Dependency Guarantee
Core runtime execution must rely strictly on the Python `>=3.10` standard library. No third-party PyPI dependencies may be added to `src/arcanum/` or `scripts/lib/`.

### 1.6 Air-Gapped Content Security Policy (CSP)
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
- **Typing Strictness**: All 220 source files must maintain full type annotations (`disallow_untyped_defs = True` in `mypy.ini`).
- **Facade Delegation Pattern**: Compatibility shims in `scripts/lib/` must re-export symbols from `src/arcanum/` without adding side-effects or breaking existing positional/keyword arguments:
  ```python
  from src.arcanum.core.storage import atomic_write, is_safe_subpath, PathSecurityError
  ```

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
| `DOC-701..705` | System Diagnostics | Subsystem 1 (Deterministic) | Toolchain health: missing publishing accelerators, Python version mismatch, corrupt cache indexes. |

---

## 4. Prose, Markup & Governance Conventions

- **1-Click Rule Negation (`!RULE_ID`)**: Authors can suppress specific continuity rules for deliberate creative twists by prefixing the rule ID with `!` in `constitution.yaml`:
  ```yaml
  rules:
    - "!EPI-201"  # Allow premature knowledge leak for dramatic irony in Book 2
  ```
- **CriticMarkup**: Supported for tracked changes in Markdown prose:
  - Addition: `{++added text++}`
  - Deletion: `{--deleted text--}`
  - Substitution: `{~~original~>replacement~~}`
  - Highlight & Comment: `{==highlighted text==}{>>editorial comment<<}`
- **Obsidian Wikilinks**: Internal lore references use `[[Target]]` or `[[Target|Alias]]`. When publishing for print or external distribution, `src/arcanum/publishing/publisher.py` automatically resolves these to clean reading prose (`Alias` or `Target`).
- **Frontmatter Directives**: Chapter frontmatter supports typed directives:
  - `pov: <CharacterName>`
  - `date: <PlanetaryDateString>`
  - `location: <LocationName>`
  - `flashback: true` (exempts chapter from `TIME-302` regression alerts)
  - `state_delta: { <Entity>: { <resource>: <delta_value> } }`


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
