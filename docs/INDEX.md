# 📚 Ars Arcanum — 3-Tier Documentation Index
`docs/INDEX.md`

To prevent documentation sprawl across the 70+ specialized manuals in `docs/`, all guides are organized into three progressive tiers based on what you need right now.

---

## Tier 1: Zero-Friction Quickstart & Studio Cockpit (For All Writers)

Start here if you want to write fiction in Markdown and check continuity without learning 32 Obsidian plugins or complex terminal flags:

| Guide | What It Covers |
| :--- | :--- |
| [Start Here (`docs/START_HERE.md`)](START_HERE.md) | Visual Web Studio Cockpit (`arcanum studio`), Obsidian companion plugin, and 5-minute setup tour |
| [Obsidian Lite Mode (`docs/LITE_MODE.md`)](LITE_MODE.md) | One-command workflow (`python -m scripts.lib.audit_hardening`) with just 5 Obsidian plugins and the 4 core compilers |
| [Visual Studio & Integrations (`docs/codebase/INTEGRATIONS.md`)](codebase/INTEGRATIONS.md) | Local HTTP API (`127.0.0.1:4242`), Native Obsidian Companion Plugin, Word Tracked Changes, Typst print PDFs |
| [CLI Cheatsheet (`docs/CHEATSHEET.md`)](CHEATSHEET.md) | Copy-paste command reference for daily drafting, continuity checks, and publishing |

---

## Tier 2: Author Craft & Worldbuilding Reference (Day-to-Day Studio)

Consult these manuals when configuring a specific worldbuilding subsystem or publishing format:

| Subsystem | Primary Manuals |
| :--- | :--- |
| **Core Authoring Workflow** | [Author Manual (`AUTHOR_MANUAL.md`)](AUTHOR_MANUAL.md), [Writing Sprint (`WRITING_SPRINT.md`)](WRITING_SPRINT.md), [Phase Effort Engine (`PHASE_EFFORT_ENGINE.md`)](PHASE_EFFORT_ENGINE.md), [Zen Studio (`ZEN_STUDIO.md`)](ZEN_STUDIO.md) |
| **The 4 Flagship Continuity Compilers** | [Epistemic Firewall (`EPISTEMIC_FIREWALL.md`)](EPISTEMIC_FIREWALL.md), [Timeline Solver (`TIMELINE_SOLVER.md`)](TIMELINE_SOLVER.md), [Conlang Linter (`CONLANG_LINTER.md`)](CONLANG_LINTER.md), [Resource Ledger (`RESOURCE_LEDGER.md`)](RESOURCE_LEDGER.md) |
| **Revision & Narrative Structure** | [Narrative Braid (`NARRATIVE_BRAID.md`)](NARRATIVE_BRAID.md), [Manuscript Diff (`MANUSCRIPT_DIFF.md`)](MANUSCRIPT_DIFF.md), [Revision Heatmap (`REVISION_HEATMAP.md`)](REVISION_HEATMAP.md), [Plot Matrix (`PLOT_MATRIX.md`)](PLOT_MATRIX.md) |
| **Publishing & Word Sync** | [DOCX Tracked Changes Sync (`DOCX_SYNC.md`)](DOCX_SYNC.md), [Typography (`TYPOGRAPHY.md`)](TYPOGRAPHY.md), [Omnibus (`OMNIBUS.md`)](OMNIBUS.md), [Preflight (`PREFLIGHT.md`)](PREFLIGHT.md) |
| **World Bible Modules** | [Cosmology (`COSMOLOGY.md`)](COSMOLOGY.md), [Magic System (`MAGIC_SYSTEM.md`)](MAGIC_SYSTEM.md), [Factions (`FACTIONS.md`)](FACTIONS.md), [Genealogy (`GENEALOGY.md`)](GENEALOGY.md), [Ecology (`ECOLOGY.md`)](ECOLOGY.md), [Economy (`ECONOMY.md`)](ECONOMY.md) |

---

## Tier 3: Engine Internals, Architecture & Security (For Developers & Contributors)

Read these documents when contributing code, auditing parsers, or extending the continuity compilers:

| Document | Engineering Scope |
| :--- | :--- |
| [Master System Architecture (`docs/codebase/ARCHITECTURE.md`)](codebase/ARCHITECTURE.md) | Definitive, cited technical architecture, C4 models, and Commands Inventory |
| [System Architecture Blueprint (`docs/ARCHITECTURE.md`)](ARCHITECTURE.md) | High-level 3-subsystem overview, DAL caching, and security bounds |
| [Testing Architecture (`docs/codebase/TESTING.md`)](codebase/TESTING.md) | Test suite organization, 540 passing tests, coverage requirements, and commands |
| [Technical Stack (`docs/codebase/STACK.md`)](codebase/STACK.md) | Python standard library runtime, zero-pip guarantee, and optional accelerators |
| [Coding Conventions (`docs/codebase/CONVENTIONS.md`)](codebase/CONVENTIONS.md) | Atomic write protocol, advisory locking, and diagnostic code namespaces |
| [Architectural Concerns (`docs/codebase/CONCERNS.md`)](codebase/CONCERNS.md) | Resolved security vulnerabilities, inode protection, and hardening roadmap |
| [Modernization Plan (`docs/MODERNIZATION_PLAN.md`)](MODERNIZATION_PLAN.md) | Phases 1–5 refactoring roadmap, parser hardening, and CLI cross-reference |
| [Threat Model (`docs/THREAT_MODEL.md`)](THREAT_MODEL.md) | STRIDE-Lite security boundaries, ZIP/XML parser limits, and strict CSP |
| [Agentic Manifesto (`AGENTS.md`)](../AGENTS.md) | Sovereign manifesto, non-negotiable safety contracts, and momentum queues |

---

## Production CLI & Continuity Cross-Reference

- **Visual Studio Cockpit**: `python scripts/arcanum studio [VAULT] [--port 4242]` (`src/arcanum/server/daemon.py`)
- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
- **Multi-Format Publication & Prose Sanitizer**: `python scripts/arcanum publish [MANUSCRIPT] --format pdf|epub|docx` (`scripts/lib/publisher.py`)
