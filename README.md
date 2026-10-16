# 🖋️ Ars Arcanum – Sovereign Authoring Operating System & Craft Studio

[![Release](https://img.shields.io/badge/Release-v0.1.0--amber)](https://github.com/aryansinghnagar/Ars-Arcanum)
[![Status](https://img.shields.io/badge/Status-Sovereign_Studio-emerald)](https://github.com/aryansinghnagar/Ars-Arcanum)
[![Tests](https://img.shields.io/badge/Tests-540_Passing_(100%25)-brightgreen)](https://github.com/aryansinghnagar/Ars-Arcanum/actions)
[![Coverage](https://img.shields.io/badge/Coverage-%E2%89%A580%25_(81%25_Verified)-blue)](https://github.com/aryansinghnagar/Ars-Arcanum)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero--Pip_(100%25_Stdlib)-orange)](pyproject.toml)

**Ars Arcanum** is an open-source, local-first, 100% offline sovereign worldbuilding, narrative continuity, and manuscript engineering operating system designed for speculative fiction (Science Fiction & Fantasy) writers, storytellers, and worldbuilders.

---

## 🏛️ The Sovereignty Principle

1. **100% Offline & Air-Gapped by Default**: Zero cloud lock-in, zero remote telemetry, and strict Content-Security-Policy (`default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;`) across all generated HTML/SVG interfaces and local studio servers.
2. **Deterministic Continuity Compilers over Generative Slop**: Ars Arcanum never writes or hallucinates prose for you. Instead, it treats your World Bible and Manuscript like an executable repository—auditing POV spoiler boundaries (`EPI-*`), custom planetary calendars and route transit physics (`TIME-*`), PolyGlot conlang phonotactics (`CON-*`), and hard-magic resource conservation (`LED-*`).
3. **Zero-Pip Runtime Survivability**: Built entirely on Python `>=3.10` standard library primitives (`scripts/lib/` and `src/arcanum/`) so your creative vaults remain readable and compilable 30 years from now without dependency rot.
4. **Dual-Surface Zero-Friction UX**: Non-technical writers can operate every feature without the command line via the local **Visual Web Studio Cockpit** (`http://127.0.0.1:4242`) and the native **Obsidian Companion Plugin**, complete with 1-click **"Allow / Intended Twist"** rule suppression in `constitution.yaml`.
5. **Physical Inode Protection on Drafts**: Draft promotion uses `shutil.copy2` with `0o444` read-only permissions on parent baselines, guaranteeing external text editors (Obsidian, VS Code) can never mutate historical snapshots.
6. **Three-Subsystem Epistemic Safety ([ADR-0001](docs/adr/0001-demotion-of-normative-evaluators-and-three-subsystem-epistemic-safety.md))**:
   - **Subsystem 1 (Deterministic Invariants & Continuity Compilers)**: Atomic file writes, cross-platform locks, schema validation, POV epistemic firewalls (`EPI-*`), timeline/route physics (`TIME-*`), conlang phonotactics (`CON-*`), and resource conservation ledgers (`LED-*`).
   - **Subsystem 2 (Descriptive Telemetry & Craft Analytics)**: Phase-Aware Effort Multipliers, word/dialogue/CJK telemetry, SHA-256 paragraph-hash diffing, revision heatmaps (`REV-*`), and multi-POV narrative braid matrices (`BRD-*`).
   - **Subsystem 3 (Authorial Governance & Obsidian Integration)**: 3-tier `constitution.yaml` cascade (`!RULE_ID` negation), 5-plugin **Lite Mode** profile (`lite_profile.json`) or 32-plugin Full Studio, and live `_Arcanum_Diagnostics.md` callout dashboards.

---

## ⚡ Quick Start & Core Workflows

### 0. The Layman Experience: Visual Studio Cockpit & Obsidian Plugin (Zero Terminal Required)
```bash
# Launch the sovereign local web studio cockpit in your default browser (127.0.0.1:4242)
python scripts/arcanum studio --open

# Or on Windows, double-click the desktop shortcut created by scripts/setup_arcanum.ps1
```
Inside the Visual Studio:
- **Manuscript Catalog**: Browse your universes and novels with real-time word telemetry.
- **Continuity & Twist Assistant**: Run one-click continuity checks; allow intentional narrative deviations with the **"Allow / Intended Twist"** button (suppresses `!RULE_ID` in `constitution.yaml`).
- **Sprint Engine**: Focused writing timer with Web Audio sound chimes and automatic phase-effort point calculation.
- **One-Click Publishing**: Export sanitized Typst print PDFs, Kindle EPUB3s, or standard manuscript Word documents.

### 1. Terminal & Automation CLI Workflows
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

---

## 📚 Documentation Matrix

| Guide / Reference Manual | Primary Focus |
| :--- | :--- |
| [Master System Architecture (`docs/codebase/ARCHITECTURE.md`)](docs/codebase/ARCHITECTURE.md) | Definitive, cited technical architecture, C4 models, and Commands Inventory |
| [3-Tier Documentation Index (`docs/INDEX.md`)](docs/INDEX.md) | Organized map of all 70+ manuals across Quickstart, Author Craft, and Internals |
| [Visual Studio & Integrations (`docs/codebase/INTEGRATIONS.md`)](docs/codebase/INTEGRATIONS.md) | Local HTTP API, Native Obsidian Plugin, OpenXML Word, and Typst/Pandoc |
| [Obsidian Lite Mode (`docs/LITE_MODE.md`)](docs/LITE_MODE.md) | Zero-friction 4-compiler + 5-plugin workflow for novelists |
| [Start Here (`docs/START_HERE.md`)](docs/START_HERE.md) | 15-minute onboarding tour from vault scaffolding to first sprint |
| [Author Manual (`docs/AUTHOR_MANUAL.md`)](docs/AUTHOR_MANUAL.md) | Complete day-to-day workflow guide for novelists and worldbuilders |
| [CLI Cheatsheet (`docs/CHEATSHEET.md`)](docs/CHEATSHEET.md) | Fast command reference for all core, continuity, and publishing engines |
| [System Architecture Blueprint (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md) | Architectural overview of the 3-subsystem model and safety bounds |
| [Testing Architecture (`docs/codebase/TESTING.md`)](docs/codebase/TESTING.md) | Test suite organization, coverage requirements, and verification commands |
| [Coding Conventions (`docs/codebase/CONVENTIONS.md`)](docs/codebase/CONVENTIONS.md) | Atomic write protocol, advisory locking, and diagnostic code namespaces |
| [Agentic Manifesto (`AGENTS.md`)](AGENTS.md) | Invariant engineering contracts, security guarantees, and momentum queues |
| [Threat Model (`docs/THREAT_MODEL.md`)](docs/THREAT_MODEL.md) | STRIDE-Lite security analysis, subprocess sandboxing, and CSP enforcement |
