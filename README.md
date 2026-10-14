# 🖊️ Ars Arcanum — Sovereign Authoring Operating System & Craft Studio

[![Release](https://img.shields.io/badge/Release-v0.1.0-amber)](https://github.com/aryansinghnagar/Ars-Arcanum)
[![Status](https://img.shields.io/badge/Status-Sovereign_Studio-emerald)](https://github.com/aryansinghnagar/Ars-Arcanum)
[![Tests](https://img.shields.io/badge/Tests-507_Passing_(100%25)-brightgreen)](https://github.com/aryansinghnagar/Ars-Arcanum/actions)
[![Coverage](https://img.shields.io/badge/Coverage-%E2%89%A580%25-blue)](https://github.com/aryansinghnagar/Ars-Arcanum)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero--Pip_(100%25_Stdlib)-orange)](pyproject.toml)

**Ars Arcanum** is an open-source, local-first, 100% offline sovereign worldbuilding, narrative continuity, and manuscript engineering operating system designed for speculative fiction (Science Fiction & Fantasy) writers, storytellers, and worldbuilders.

## 🏛️ The Sovereignty Principle

1. **100% Offline & Air-Gapped by Default**: Zero cloud lock-in, zero remote telemetry, and strict Content-Security-Policy (`default-src 'none'; style-src 'unsafe-inline'`) across all generated HTML/SVG visualizers.
2. **Deterministic Continuity Compilers over Generative Slop**: Ars Arcanum never writes or hallucinates prose for you. Instead, it treats your World Bible and Manuscript like an executable repository—auditing POV spoiler boundaries, custom planetary calendars, overland/relativistic travel physics, PolyGlot conlang phonotactics, and hard-magic resource conservation.
3. **Zero-Pip Runtime Survivability**: Built entirely on Python `>=3.10` standard library primitives (`scripts/lib/` and `src/arcanum/`) so your creative vaults remain readable and compilable 30 years from now.
4. **Three-Subsystem Epistemic Safety ([ADR-0001](docs/adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md))**:
   - **Subsystem 1 (Deterministic Invariants & Continuity Compilers)**: Atomic file writes, cross-platform locks, schema validation, POV epistemic firewalls (`EPI-*`), timeline/route physics (`TIME-*`), conlang phonotactics (`CON-*`), and resource conservation ledgers (`LED-*`).
   - **Subsystem 2 (Descriptive Telemetry & Craft Analytics)**: Phase-Aware Effort Multipliers, word/dialogue/CJK telemetry, SHA-256 paragraph-hash diffing, revision heatmaps (`REV-*`), and multi-POV narrative braid matrices (`BRD-*`).
   - **Subsystem 3 (Authorial Governance & Obsidian Integration)**: 3-tier `constitution.yaml` cascade (`!RULE_ID` negation), 32 pre-configured offline Obsidian plugins, and live `_Arcanum_Diagnostics.md` callout dashboards.

## ⚡ Quick Start & Core CLI Workflows

```bash
# 1. Unified Continuity Suite & Live Obsidian Dashboard (_Arcanum_Diagnostics.md)
python scripts/arcanum continuity-suite ~/Universes/Reliquary/

# 2. Phase-Aware Effort Logging & Career Velocity Forecaster (1.0x Draft, 0.5x Lore, 0.2x Revision, 0.0x Premature Edit Block)
python scripts/arcanum sprint-effort --workspace ~/Universes/Reliquary/ --book "Prisoner of Sand Sea" --stage Drafting --draft 2000 --worldbuilding 400

# 3. Epistemic POV & Spoiler Firewall (Flags premature knowledge leaks across chapters)
python scripts/arcanum validate-epistemic ~/Manuscripts/Prisoner-of-Sand-Sea/

# 4. Custom Planetary Calendar & Biome Route Physics Auditor
python scripts/arcanum timeline-audit ~/Universes/Reliquary/

# 5. PolyGlot (.pgd / XML) Conlang Importer & Phonotactic Syllable Linter
python scripts/arcanum conlang-check --pgd ~/Universes/Reliquary/Languages/sand_tongue.pgd --language "Sand Tongue"

# 6. Hard Magic & Sci-Fi Resource Conservation Ledger (Tracks ether vials, mana, delta-v)
python scripts/arcanum ledger-audit ~/Manuscripts/Prisoner-of-Sand-Sea/

# 7. Interactive Multi-POV Narrative Braid & Drought Visualizer (Exports CSP-locked SVG/HTML)
python scripts/arcanum braid ~/Manuscripts/Prisoner-of-Sand-Sea/ --html dist/narrative_braid.html

# 8. Two-Level SHA-256 Paragraph-Hash Diffing & Excised Scrap Archiver (>=50 words -> Scraps/)
python scripts/arcanum diff-fast Draft-01/01_Chapter.md Draft-02/01_Chapter.md --scraps-dir Scraps/

# 9. Bidirectional Markdown CriticMarkup <-> Word Tracked Changes (.docx) Sync
python scripts/arcanum docx-tracked export Draft-02/01_Chapter.md Export/01_Chapter_Tracked.docx
python scripts/arcanum docx-tracked pull Export/01_Chapter_Edited.docx Draft-02/01_Chapter.md

# 10. Multi-Format Publishing (Typst PDF, Pandoc EPUB3, Shunn DOCX) & GPG-Verified Backups
python scripts/arcanum publish Manuscript/ --format all
python scripts/arcanum backup --tag milestone-1
```

## 📚 Documentation Matrix

| Guide / Reference Manual | Primary Focus |
| :--- | :--- |
| [Start Here (`docs/START_HERE.md`)](docs/START_HERE.md) | 15-minute onboarding tour from vault scaffolding to first sprint |
| [Author Manual (`docs/AUTHOR_MANUAL.md`)](docs/AUTHOR_MANUAL.md) | Complete day-to-day workflow guide for novelists and worldbuilders |
| [CLI Cheatsheet (`docs/CHEATSHEET.md`)](docs/CHEATSHEET.md) | Fast command reference for all core, continuity, and publishing engines |
| [System Architecture (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md) | Master blueprint of the 3-subsystem model, DAL caching, and security bounds |
| [Modernization Plan (`docs/MODERNIZATION_PLAN.md`)](docs/MODERNIZATION_PLAN.md) | Phases 1–4 architectural refactoring and continuity compiler specifications |
| [Agentic Manifesto (`AGENTS.md`)](AGENTS.md) | Invariant engineering contracts, security guarantees, and momentum queues |
| [Threat Model (`docs/THREAT_MODEL.md`)](docs/THREAT_MODEL.md) | STRIDE-Lite security analysis, subprocess sandboxing, and CSP enforcement |
