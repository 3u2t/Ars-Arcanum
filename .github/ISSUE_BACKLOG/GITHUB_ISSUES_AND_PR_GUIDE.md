# Ars Arcanum — Ready-to-Post GitHub Issues & Contributor Implementation Guide

## Overview: Actionable Issue Pack & Pull Request Blueprint for Contributors

This guide provides copy-pasteable GitHub Issues (structured to match [`.github/ISSUE_TEMPLATE/`](https://github.com/aryansinghnagar/Ars-Arcanum/tree/main/.github/ISSUE_TEMPLATE)) and integration instructions for the three newly created Python modules (`vault_index.py`, `phase_effort_engine.py`, and `test_phase1_and_effort.py`) so contributors joining from your [r/opensource announcement](https://www.reddit.com/r/opensource/comments/1x1cbzx/looking_for_developer_to_help_with_an_open_source/) can immediately pick up well-scoped tasks.

| Issue ID | Proposed GitHub Issue Title | Target Files in Repository | Labels | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **Issue #1** | `[Refactor] Consolidate Vault Traversal & Frontmatter/Prose Caching into Unified VaultIndex` | [`scripts/lib/data_access.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/data_access.py), [`scripts/lib/cache.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/cache.py), [`scripts/lib/frontmatter.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/frontmatter.py), [`scripts/lib/word_counter.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/word_counter.py) | `refactor`, `architecture`, `performance`, `good first issue` | **P0 (Blocker)** |
| **Issue #2** | `[Feature] Phase-Aware Effort Multiplier & Career Pipeline Forecaster (arcanum sprint effort)` | [`scripts/lib/writing_sprint.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/writing_sprint.py), [`scripts/lib/portfolio.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/portfolio.py), [`scripts/lib/cli_handlers.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/cli_handlers.py) | `enhancement`, `analytics`, `subsystem-2` | **P0 (Core Workflow)** |
| **Issue #3** | `[Refactor] Extract Shared Hierarchical Paragraph-Hash Diff Engine (diff_core.py)` | [`scripts/lib/manuscript_diff.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/manuscript_diff.py), [`scripts/lib/revision_heatmap.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/revision_heatmap.py) | `refactor`, `performance` | **P1 (High)** |
| **Issue #4** | `[Enhancement] Bidirectional CriticMarkup <-> Word Tracked Changes Sync in docx_sync.py` | [`scripts/lib/docx_sync.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/docx_sync.py), [`scripts/lib/docx_builder.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/docx_builder.py) | `enhancement`, `publishing`, `docx` | **P1 (High)** |
| **Issue #5** | `[Security & Typing] Re-enable Strict Mypy Error Codes and Isolate User Plugins via Subprocess` | [`mypy.ini`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/mypy.ini), [`scripts/lib/constitution.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/constitution.py), [`scripts/lib/registry.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/registry.py) | `security`, `typing`, `subsystem-1` | **P1 (High)** |
| **Issue #6** | `[Feature] Epistemic POV & Spoiler Firewall (arcanum validate --epistemic)` | [`scripts/lib/frontmatter.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/frontmatter.py), [`scripts/lib/cli.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/cli.py) | `enhancement`, `worldbuilding`, `subsystem-1` | **P2 (Roadmap)** |

## Issue #1: Unified `VaultIndex` & Hardened Frontmatter/Prose Parser (Implemented in `vault_index.py`)

### Problem Statement
Currently, [`writing_sprint.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/writing_sprint.py), [`word_counter.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/word_counter.py), [`portfolio.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/portfolio.py), and [`omnibus.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/omnibus.py) each implement separate `Path.rglob("*.md")` loops and manual folder filtering instead of routing through [`data_access.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/data_access.py) and [`cache.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/cache.py). Additionally:
* [`frontmatter.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/frontmatter.py) does not parse YAML multiline block scalars (`|` literal and `>` folded), which authors frequently use for chapter synopses and lore descriptions.
* [`word_counter.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/word_counter.py) uses single-paragraph quote-pair regexes that misclassify literary multi-paragraph dialogue (where opening quotes appear on each paragraph, but the closing quote appears only on the final spoken paragraph).
* [`codex_export.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/codex_export.py) matches `[[Wikilinks]]` inside fenced code blocks.

### Acceptance Criteria (Delivered in `vault_index.py`)
* [x] Enforce `is_safe_subpath()` on every vault traversal and cache write per [`AGENTS.md`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/AGENTS.md).
* [x] Prune `.arcanum`, `.obsidian`, `Backups`, `Export`, and `Scraps` in-place during `os.walk` so excluded trees are never descended.
* [x] Parse YAML multiline block scalars (`|`, `|-`, `>`, `>-`), inline collections, and indented lists/dicts with zero external dependencies.
* [x] Accurately count literary multi-paragraph dialogue, CJK characters, and CriticMarkup edits while ignoring fenced code blocks when extracting `[[Target#Heading|Alias]]` wikilinks.
* [x] Store SHA-256 paragraph hashes (`paragraph_hashes`) inside `.arcanum_cache.json` (`CACHE_VERSION = 3`) for $O(1)$ unchanged-paragraph skipping during manuscript diffs.

## Issue #2: Phase-Aware Effort & Career Velocity Engine (Implemented in `phase_effort_engine.py`)

### Problem Statement
In [`writing_sprint.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/writing_sprint.py) and [`portfolio.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/portfolio.py), daily velocity is measured strictly by raw manuscript word count deltas. For speculative fiction authors managing complex universes (as structured in the [Master Writing Ecosystem (Google Sheet)](https://drive.google.com/open?id=1JO2b10h_3mXwARlz__d9YhjyQpCvPgzVufjC8WGD9ZQ)), raw word counts create two perverse incentives:
1. Authors get zero credit for essential worldbuilding and outlining days.
2. Authors are tempted to prematurely edit earlier chapters during a First Draft instead of pushing forward.

### Acceptance Criteria (Delivered in `phase_effort_engine.py`)
* [x] Support all 9 canonical project stages: `Concept`, `Pre-Draft Outline`, `Drafting`, `Pre-Revision Outline`, `Revision`, `Beta Review`, `Proofing`, `Querying`, `Publishing`.
* [x] Apply deterministic Phase-Aware Effort Multipliers:
  * `1.00x` for First Draft prose across all stages.
  * `1.00x` for Outlining during designated Outline stages (`Concept`, `Pre-Draft Outline`, `Pre-Revision Outline`), and `0.50x` off-phase.
  * `0.50x` for Worldbuilding / Lore notes (`2` worldbuilding words = `1` effort point).
  * `0.20x` for Revisions during `Revision`, `Beta Review`, and `Proofing` (`5` revised words = `1` effort point), and **`0.00x` outside Revision stages** (flagging `premature_revision_blocked = True`).
* [x] Compute career-wide progress toward the `15,000,000`-word lifetime milestone, `730,000`-word annual target, `2,000`-point daily effort goal, trailing 30-day velocity, active streak, and per-book required daily pace across universes (e.g., *Reliquary*: *Prisoner of Sand Sea*, *Gothic Fantasy*, *Sci Fi Book*, *Ruler of Sand Sea*).

## Issue #3: Shared Hierarchical Diff Engine & Hardlink Draft Promotion

### Problem Statement
[`manuscript_diff.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/manuscript_diff.py) (730 lines) and [`revision_heatmap.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/revision_heatmap.py) (1,084 lines) duplicate tokenization and `difflib.SequenceMatcher` diff matrices, incurring quadratic $O(N^2)$ slowdowns on 200,000-word manuscripts. Meanwhile, [`draft_manager.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/draft_manager.py) (931 lines) performs full recursive file copies when branching `Draft-01` $\to$ `Draft-02`.

### Acceptance Criteria for Contributors
* [ ] Wire `VaultIndex.diff_paragraphs_fast()` from `vault_index.py` into both [`manuscript_diff.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/manuscript_diff.py) and [`revision_heatmap.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/revision_heatmap.py) so `difflib.SequenceMatcher` is invoked only on paragraphs whose 16-char SHA-256 hash changed.
* [ ] Update [`draft_manager.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/draft_manager.py) to create OS hardlinks (`os.link` with fallback to `shutil.copy2` across filesystems) when branching a new draft, relying on `atomic_write()` (`os.replace`) to safely break hardlinks when a chapter is edited in the child draft.

## Issue #4: Bidirectional CriticMarkup <-> Word Tracked Changes in `docx_sync.py`

### Problem Statement
[`docx_sync.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/docx_sync.py) (1,129 lines) unzips `.docx` archives and parses `word/document.xml` via `xml.etree.ElementTree`, while [`docx_builder.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/docx_builder.py) (489 lines) builds OpenXML via string interpolation. When an editor or beta reader returns a `.docx` with Word Tracked Changes (`<w:ins>`, `<w:del>`, `<w:commentRangeStart>`), `arcanum sync pull` currently ignores revision tags.

### Acceptance Criteria for Contributors
* [ ] Refactor [`docx_builder.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/docx_builder.py) to construct `word/document.xml` using `xml.etree.ElementTree` DOM nodes rather than raw string interpolation.
* [ ] In [`docx_sync.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/docx_sync.py), convert `<w:ins>` runs to `{++inserted text++}`, `<w:del>` runs (`<w:delText>`) to `{--deleted text--}`, and Word comments to `{>>Author: comment<<}` during `arcanum sync pull`.

## Issue #5: Strict Mypy Type Enforcement & Subprocess Plugin Sandbox

### Problem Statement
[`mypy.ini`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/mypy.ini) currently disables `union-attr`, `attr-defined`, `index`, `assignment`, and `var-annotated`. Furthermore, [`registry.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/registry.py) (611 lines) loads custom plugins from `.arcanum/plugins/*.py` directly into the main interpreter process via `importlib.util.spec_from_file_location`.

### Acceptance Criteria for Contributors
* [ ] Add `@dataclass(frozen=True)` schemas to [`constitution.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/constitution.py) (including `!rule_id` negation support in `_deep_merge_dict`) and [`config.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/config.py).
* [ ] Remove `union-attr`, `attr-defined`, `index`, `assignment`, and `var-annotated` from `disable_error_code` in [`mypy.ini`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/mypy.ini).
* [ ] Sandbox user plugins in [`registry.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/registry.py) by executing `.arcanum/plugins/*.py` via `subprocess.run([sys.executable, "-I", plugin_path], input=payload_json, capture_output=True, text=True, timeout=10)`.

## Step-by-Step Integration Commands for Your Local Repo

1. **Copy the new modules into your repository**:
   ```bash
   cp vault_index.py scripts/lib/vault_index.py
   cp phase_effort_engine.py scripts/lib/phase_effort_engine.py
   cp test_phase1_and_effort.py tests/test_phase1_and_effort.py
   ```
2. **Register the `sprint effort` subcommand in [`scripts/lib/cli_handlers.py`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/scripts/lib/cli_handlers.py)**:
   Dispatch `arcanum sprint effort` to `scripts.lib.phase_effort_engine:main`.
3. **Run the canonical quality gates ([`README.md`](https://github.com/aryansinghnagar/Ars-Arcanum/blob/main/README.md))**:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   mypy --strict scripts/lib/vault_index.py scripts/lib/phase_effort_engine.py tests/test_phase1_and_effort.py
   ruff check scripts/lib/vault_index.py scripts/lib/phase_effort_engine.py tests/test_phase1_and_effort.py
   ```
