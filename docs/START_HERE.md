# 🚀 Start Here — 15-Minute Onboarding Tour of Ars Arcanum

> **New to Ars Arcanum?** See the [3-Tier Documentation Index (`docs/INDEX.md`)](INDEX.md) or start with [Obsidian Lite Mode (`docs/LITE_MODE.md`)](LITE_MODE.md) for a zero-friction setup using just 1 command and 5 Obsidian plugins.

0. **One-Command Lite Mode Check (Fastest Start)**:
```bash
python3 -m scripts.lib.audit_hardening ~/Universes/Reliquary
```

1. **Scaffold Your Universe & Manuscript**:
```bash
python scripts/arcanum universe ~/Universes/Reliquary
python scripts/arcanum manuscript ~/Manuscripts/Prisoner-of-Sand-Sea
```

2. **Log Phase-Weighted Writing Sessions**:
```bash
python scripts/arcanum sprint-effort --workspace ~/Universes/Reliquary --book "Prisoner of Sand Sea" --stage Drafting --draft 2000 --worldbuilding 500
```

3. **Run the Continuity Suite & View Live Obsidian Diagnostics**:
```bash
python scripts/arcanum continuity-suite ~/Universes/Reliquary
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
