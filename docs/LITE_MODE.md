# 🪶 Ars Arcanum Lite Mode — Zero-Friction Continuity for Novelists

**Lite Mode** strips away terminal complexity and plugin bloat so you can focus entirely on drafting your novel while still catching plot holes automatically.

## What Lite Mode Changes

1. **4 Flagship Compilers Only**: Runs only the high-ROI deterministic checks—**Epistemic POV Firewall** (`EPI-*`), **Timeline & Route Physics** (`TIME-*`), **Conlang Phonotactics** (`CON-*`), and **Resource Conservation Ledger** (`LED-*`).
2. **5 Essential Obsidian Plugins (Down from 32)**: Generates `.obsidian/lite_profile.json` enabling only `dataview`, `templater-obsidian`, `omnisearch`, `obsidian-style-settings`, and `longform`.
3. **Single Callout Dashboard**: Writes `_Arcanum_Lite_Dashboard.md` at the root of your vault with a scannable table and zero configuration required.

## Quick Usage

```bash
# Run Lite Mode directly on your Universe or Manuscript folder
python3 -m scripts.lib.audit_hardening ~/Universes/Reliquary

# Or emit machine-readable JSON diagnostics
python3 -m scripts.lib.audit_hardening ~/Universes/Reliquary --json
```

<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1-4 Production CLI & Continuity Cross-Reference

- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
