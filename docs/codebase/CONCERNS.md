# Architectural Concerns & Remediations (`docs/codebase/CONCERNS.md`)

1. **Unified Vault Traversal (`vault_index.py`)**: Eliminates duplicate `rglob("*.md")` walks via `CACHE_VERSION = 3` mtime memoization.
2. **Hierarchical Diffing (`diff_core.py`)**: Uses 16-char SHA-256 paragraph hashes to skip unchanged paragraphs in $O(1)$ time.
3. **Word Tracked Changes Preservation (`docx_tracked_changes.py`)**: Uses `xml.etree.ElementTree` DOM nodes to map CriticMarkup to and from OpenXML `<w:ins>`, `<w:del>`, and `<w:comment>`.
4. **Plugin Subprocess Sandboxing (`plugin_sandbox.py`)**: Isolates `.arcanum/plugins/*.py` inside `python3 -I -B` subprocesses.


<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1–4 Production CLI & Continuity Cross-Reference

- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
