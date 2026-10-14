# 📚 Ars Arcanum — 3-Tier Documentation Index

To prevent documentation sprawl across the 70+ specialized manuals in `docs/`, all guides are organized into three progressive tiers based on what you need right now.

## Tier 1: 5-Minute Quickstart & Lite Mode (For All Writers)

Start here if you want to write fiction in Markdown and check continuity without learning 32 Obsidian plugins or complex terminal flags:

| Guide | What It Covers |
| :--- | :--- |
| [Start Here (`docs/START_HERE.md`)](START_HERE.md) | 5-minute setup from scaffolding a universe to running your first check |
| [Obsidian Lite Mode (`docs/LITE_MODE.md`)](LITE_MODE.md) | One-command workflow (`scripts/arcanum-lite`) with just 5 Obsidian plugins and the 4 core compilers |
| [CLI Cheatsheet (`docs/CHEATSHEET.md`)](CHEATSHEET.md) | Copy-paste command reference for daily drafting and continuity checks |

## Tier 2: Author Craft & Worldbuilding Reference (Day-to-Day Studio)

Consult these manuals only when configuring a specific worldbuilding subsystem or publishing format:

| Subsystem | Primary Manuals |
| :--- | :--- |
| **Core Authoring Workflow** | [Author Manual (`AUTHOR_MANUAL.md`)](AUTHOR_MANUAL.md), [Writing Sprint (`WRITING_SPRINT.md`)](WRITING_SPRINT.md), [Phase Effort Engine (`PHASE_EFFORT_ENGINE.md`)](PHASE_EFFORT_ENGINE.md), [Zen Studio (`ZEN_STUDIO.md`)](ZEN_STUDIO.md) |
| **The 4 Flagship Continuity Compilers** | [Epistemic Firewall (`EPISTEMIC_FIREWALL.md`)](EPISTEMIC_FIREWALL.md), [Timeline Solver (`TIMELINE_SOLVER.md`)](TIMELINE_SOLVER.md), [Conlang Linter (`CONLANG_LINTER.md`)](CONLANG_LINTER.md), [Resource Ledger (`RESOURCE_LEDGER.md`)](RESOURCE_LEDGER.md) |
| **Revision & Narrative Structure** | [Narrative Braid (`NARRATIVE_BRAID.md`)](NARRATIVE_BRAID.md), [Manuscript Diff (`MANUSCRIPT_DIFF.md`)](MANUSCRIPT_DIFF.md), [Revision Heatmap (`REVISION_HEATMAP.md`)](REVISION_HEATMAP.md), [Plot Matrix (`PLOT_MATRIX.md`)](PLOT_MATRIX.md) |
| **Publishing & Word Sync** | [DOCX Tracked Changes Sync (`DOCX_SYNC.md`)](DOCX_SYNC.md), [Typography (`TYPOGRAPHY.md`)](TYPOGRAPHY.md), [Omnibus (`OMNIBUS.md`)](OMNIBUS.md), [Preflight (`PREFLIGHT.md`)](PREFLIGHT.md) |
| **World Bible Modules** | [Cosmology (`COSMOLOGY.md`)](COSMOLOGY.md), [Magic System (`MAGIC_SYSTEM.md`)](MAGIC_SYSTEM.md), [Factions (`FACTIONS.md`)](FACTIONS.md), [Genealogy (`GENEALOGY.md`)](GENEALOGY.md), [Ecology (`ECOLOGY.md`)](ECOLOGY.md), [Economy (`ECONOMY.md`)](ECONOMY.md) |

## Tier 3: Engine Internals, Architecture & Security (For Developers & Contributors)

Read these documents when contributing code, auditing parsers, or extending the continuity compilers:

| Document | Engineering Scope |
| :--- | :--- |
| [System Architecture (`docs/ARCHITECTURE.md`)](ARCHITECTURE.md) | 3-subsystem model, `VaultIndex` DAL caching, and `src/arcanum/` package layout |
| [Modernization Plan (`docs/MODERNIZATION_PLAN.md`)](MODERNIZATION_PLAN.md) | Phases 1–5 refactoring roadmap, parser hardening, and CLI cross-reference |
| [Threat Model (`docs/THREAT_MODEL.md`)](THREAT_MODEL.md) | STRIDE-Lite security boundaries, ZIP/XML parser limits, and strict CSP |
| [Good First Issues (`.github/ISSUE_BACKLOG/GOOD_FIRST_ISSUES.md`)](../.github/ISSUE_BACKLOG/GOOD_FIRST_ISSUES.md) | Scoped starter tickets for open-source contributors |
