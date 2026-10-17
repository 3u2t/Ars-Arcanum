# Master Writing Ecosystem Workbook & Live Auto-Sync Engine (`WORKBOOK_SYNC`)

> **Module**: `scripts/lib/workbook_sync.py`
> **Workbook Artifact**: `Master_Writing_Ecosystem.xlsx` (Root) & `templates/ecosystem/Master_Writing_Ecosystem.xlsx`
> **CLI Commands**: `arcanum workbook [sync|status|watch|add-book]`, `arcanum tracker`, `arcanum excel`
> **Runtime Dependencies**: Zero third-party pip packages required (pure-stdlib OpenXML `zipfile` + `xml.etree.ElementTree`, with optional headless LibreOffice recalculation).

---

## 1. Architectural Overview

`Master_Writing_Ecosystem.xlsx` is the live, multi-sheet executive command center for **Ars Arcanum**. Rather than acting as a static spreadsheet that drifts out of sync with your Markdown vaults, `scripts/lib/workbook_sync.py` binds the workbook directly to your project files so tables, formulas, and all **15 native Excel charts across 8 worksheets** auto-populate, auto-update, and auto-generate whenever changes occur across the repository.

### Automatic Trigger Hooks

| Project Event / Action | Engine Module | Automatic Workbook Update Performed |
| :--- | :--- | :--- |
| **Log Writing Sprint** (`arcanum sprint-effort`) | `scripts/lib/phase_effort_engine.py` | Appends session to `.arcanum/sprint_log.jsonl` and auto-updates `Daily Writing Log`, `My Books`, `Universes & Series`, `Dashboard`, and `Calc` Blocks 1–10. |
| **Run Continuity Suite** (`arcanum continuity-suite`) | `scripts/lib/vault_continuity_runner.py` | Audits `EPI-*`, `TIME-*`, `CON-*`, `LED-*`, and `BRD-*` rules, writes `_Arcanum_Diagnostics.md`, and auto-updates `Continuity & Compilers`, `World Bible & Lore`, and `Calc` Blocks 12–15. |
| **Run Lite Check** (`arcanum lite-check`) | `scripts/lib/audit_hardening.py` | Audits vault continuity and refreshes workbook compiler telemetry if `Master_Writing_Ecosystem.xlsx` is present. |
| **Add / Update Book** (`arcanum workbook add-book`) | `scripts/lib/workbook_sync.py` | Updates `.arcanum/ecosystem_books.json`, populates row formulas in `My Books` (`INDEX/MATCH`, `SUMIFS`, ASCII progress bar), and refreshes all 8 sheets. |
| **Live File Watcher** (`arcanum workbook watch`) | `scripts/lib/workbook_sync.py` | Polls `.md`, `.yaml`, `.yml`, `.jsonl`, and `.json` modification timestamps and auto-syncs `Master_Writing_Ecosystem.xlsx` on every save. |

---

## 2. The 8 Worksheets & 15 Dynamic Charts

| Sheet # | Worksheet Name | Purpose & Auto-Generated Formula Blocks | Embedded Native Charts |
| :---: | :--- | :--- | :--- |
| **1** | `Dashboard` | Executive KPI ribbon (`Lifetime Career Words`, `Reliquary Universe`, `Standalone Projects`, `Trailing 30D Velocity`) + 8-slot `Current Active Books Spotlight` sorted by soonest deadline. | **4 Charts**: `30-Day Writing Velocity`, `Daily Effort Target Ring`, `Active Books Spotlight Pace`, `Multi-Year Production Load` |
| **2** | `Config` | Centralized system reference date (`Config!$A$2`), Phase-Aware Effort Multipliers (`1.0x` Drafting/In-Phase Outlining, `0.5x` Worldbuilding/Off-Phase Outlining, `0.2x` In-Phase Revision, `0.0x` Premature Revision), dropdown validation lists, and **8 Automated Data Integrity Checks** (`B25:B33`). | *Feeds Donut Rings & Validation Dropdowns* |
| **3** | `Universes & Series` | Multi-series canon portfolio (`Sand Sea Saga`, `Gothic Fantasy Series`, `Classic Quest Fantasy`, `Stormbreaker Chronicles`, `Chronicles of Eldoria`) with live catalog alignment checks. | **2 Charts**: `Series Canon Architecture (Completed / Active / Future)`, `Series Word Volume vs Target` |
| **4** | `My Books` | 20-slot multi-year book pipeline (`Rows 5:24`) with automatic `INDEX/MATCH` Universe resolution, `SUMIFS` Total Work Words & First Draft Words, ASCII progress bars, Required Daily Pace, 30D Speed, and Forecasted Finish Date. | **3 Charts**: `Book Draft Target vs Actual Words`, `Required Daily Pace vs Recent 30D Speed`, `Pipeline Stage Funnel` |
| **5** | `Daily Writing Log` | Session-by-session habit tracker (`Rows 5:34`) recording Worldbuilding, Outlining, First Draft, and Revision words, duration, Words/Hour, and Phase-Weighted Effort Points. | **2 Charts**: `Creative Pillar Mix (Raw Words vs Weighted Effort)`, `Weekly Writing Rhythm (Mon–Sun)` |
| **6** | `Calc` | 730-day streak & grace-day ledger (`Cols A:H`), 30-day velocity (`Cols J:K`), Spotlight sorter (`Cols M:P`), Headline KPIs (`Cols R:S`), and Dynamic Chart Telemetry Blocks 5–15 (`Cols U:BC`). | *Central Calculation Engine feeding all 15 Charts* |
| **7** | `Continuity & Compilers` | **Ars-Arcanum Engine Telemetry (`Rows 10:21`)**: Tracks `Epistemic (EPI-*)`, `Chronology (TIME-*)`, `Conlang (CON-*)`, `Unpaid Promises (LED-*)`, `Braid Droughts (BRD-*)`, `High-Churn Scenes`, `Graveyard Scraps`, `Total Issues`, `Health Score %`, and `Compiler Status`. | **2 Charts**: `Engine Health & Active Findings by Compiler`, `Book Continuity Health Score & Open Findings` |
| **8** | `World Bible & Lore` | **World Bible Domain Matrix (`Rows 10:21`)**: Tracks `Characters`, `Locations`, `Factions`, `Magic / Systems`, `Artifacts / Items`, `Timeline Events`, `Conlang Lexicon`, `Avg Backlinks / Note`, `Total Canon Entities`, and `Bible Completeness %`. | **2 Charts**: `World Bible Entity Volume by Domain`, `Vault Lore Completeness & Backlink Density` |

---

## 3. CLI Usage Examples

```bash
# 1. Synchronize Master_Writing_Ecosystem.xlsx with current project vaults & sprint logs
python scripts/arcanum workbook sync

# 2. Inspect workbook sheet, chart, and integrity check status as JSON
python scripts/arcanum workbook status --json

# 3. Register a new book into the pipeline and auto-update all 8 sheets & 15 charts
python scripts/arcanum workbook add-book \
  --title "Crown of the Astral Loom" \
  --year 2027 \
  --universe "Eldoria-Cosmos" \
  --series "Chronicles of Eldoria" \
  --stage "Drafting" \
  --target-words 160000 \
  --start-date "2026-10-16" \
  --deadline "2027-08-01"

# 4. Log a writing session (automatically triggers workbook sync!)
python scripts/arcanum sprint-effort \
  --book "Prisoner of Sand Sea" \
  --stage "Drafting" \
  --draft 2200 \
  --worldbuilding 400 \
  --minutes 95 \
  --notes "Ch. 4 Obsidian storm-wall crossing"

# 5. Watch project files and auto-update Master_Writing_Ecosystem.xlsx on every save
python scripts/arcanum workbook watch --interval 2.0
```

<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1-5 Production CLI, Workbook Sync & Continuity Cross-Reference

- **Master Writing Ecosystem Workbook Sync**: `python scripts/arcanum workbook sync` (`scripts/lib/workbook_sync.py` & `Master_Writing_Ecosystem.xlsx`)
- **Obsidian Lite Mode (4 Core Compilers + 5-Plugin Profile)**: `python3 -m scripts.lib.audit_hardening [VAULT]` (`scripts/lib/audit_hardening.py`)
- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
