# ⚡ Ars Arcanum CLI Command Cheatsheet (`docs/CHEATSHEET.md`)

A comprehensive reference for the Ars Arcanum CLI (`arcanum`, `ars-arcanum`, or `python -m arcanum.cli_bridge`).

---

## 1. Visual Studio Cockpit & Launchers

| Command / Action | Description | Notes / Flags |
| :--- | :--- | :--- |
| `launchers/launch_studio.bat` | Double-click desktop launcher on Windows | Starts daemon silently (`pythonw`) and opens browser |
| `launchers/setup_windows.bat` | One-click automated setup and shortcut installer | Configures PowerShell execution policy bypass |
| `arcanum studio [VAULT]` | Launch local HTTP studio server daemon | Binds strictly to `127.0.0.1:4242` |
| `arcanum studio --open` | Launch studio daemon and automatically open default browser | Zero-friction author entry point |
| `arcanum studio --port 8080` | Bind studio daemon to custom local port | Default port: `4242` |

---

## 2. Flagship Continuity Compilers

| Command | Description | Diagnostic Codes |
| :--- | :--- | :--- |
| `arcanum continuity-suite [VAULT]` | Run all 4 continuity compilers and update `_Arcanum_Diagnostics.md` | `EPI-*`, `TIME-*`, `CON-*`, `LED-*`, `BRD-*` |
| `arcanum validate-epistemic [VAULT]` | Audit POV spoiler boundaries and premature lore leakage | `EPI-201` (Leak), `EPI-202` (Post-mortem), `EPI-203` (Secret) |
| `arcanum timeline-audit [VAULT]` | Audit planetary calendars, Dijkstra route physics, and regressions | `TIME-301` (Velocity), `TIME-302` (Regression) |
| `arcanum conlang-check --pgd FILE.pgd` | Import PolyGlot dictionary and audit syllable phonotactics | `CON-401` (Syllable), `CON-402` (Morpheme) |
| `arcanum ledger-audit [VAULT]` | Audit hard-magic and sci-fi resource conservation pools | `LED-501` (Exhaustion), `LED-502` (Over-consumption) |
| `arcanum braid [MANUSCRIPT]` | Analyze character POV distribution and detect narrative droughts | `BRD-601` (Perspective drought) |

---

## 3. Manuscript Engineering, Diffing & Prose Metrics

| Command | Description | Flags / Options |
| :--- | :--- | :--- |
| `arcanum count-words [FILE/VAULT]` | Measure Unicode prose, dialogue ratio, CriticMarkup, and CJK ideographs | `--json`, `--detailed` |
| `arcanum diff-fast OLD.md NEW.md` | Fast two-level SHA-256 paragraph diff and scrap harvester | `--scraps-dir Scraps/` (extracts cuts $\ge 50$ words) |
| `arcanum docx-tracked export IN.md OUT.docx` | Convert Markdown CriticMarkup into native Word Tracked Changes | Supports `{++..++}`, `{--..--}`, `{==..==}{>>..<<}` |
| `arcanum docx-tracked pull IN.docx OUT.md` | Pull editor Word Tracked Changes back into Markdown CriticMarkup | Preserves author source structure |
| `arcanum sprint-effort [ARGS]` | Calculate and log phase-aware effort points to ledger | `--book`, `--stage`, `--draft`, `--worldbuilding` |
| `arcanum draft-promote [DRAFT_DIR]` | Promote draft with physical inode copy and `0o444` read-only lock | Maintains `.draft_lineage.json` |

---

## 4. Multi-Format Publishing & Compilation

| Command | Description | Flags / Options |
| :--- | :--- | :--- |
| `arcanum publish [MANUSCRIPT]` | Compile manuscript to sanitized publication formats | `--format epub` (Zero-pip native EPUB 3.3) |
| `arcanum publish [MANUSCRIPT]` | Compile manuscript to camera-ready print PDF via Typst | `--format pdf` (Escapes Typst special chars) |
| `arcanum publish [MANUSCRIPT]` | Compile manuscript to standard Word document via Pandoc | `--format docx` (Resolves CriticMarkup) |
| `arcanum publish [MANUSCRIPT] --format all` | Compile all supported publication formats in one pass | Generates PDF, EPUB, and DOCX |
| `arcanum preflight [MANUSCRIPT]` | Validate publication readiness, frontmatter, and assets | Catches missing covers, unresolved tags |
| `arcanum omnibus [SERIES_DIR]` | Compile multi-volume series into a unified omnibus edition | Generates master TOC and series apparatus |

---

## 5. System Doctor, Migration & Administration

| Command | Description | Flags / Options |
| :--- | :--- | :--- |
| `arcanum doctor [VAULT]` | Run system health diagnostics and toolchain inspection | Checks Python, Git, Pandoc, Typst, Ruff |
| `arcanum doctor --bundle [OUT.zip]` | Generate redacted bug report ZIP bundle for troubleshooting | Strips prose and sensitive data |
| `arcanum migrate [VAULT]` | Upgrade vault schema to 1.0 (restructures Backups & Exports) | Safe non-destructive folder migration |
| `arcanum backup [VAULT]` | Create timestamped archive snapshot of vault | `--encrypt <KEY_ID>` for GPG encryption |
| `arcanum restore [ARCHIVE] [DEST]` | Safely restore vault from snapshot with path validation | Confines extraction to destination root |
| `arcanum universe [PATH]` | Scaffold a sovereign speculative fiction worldbuilding vault | Generates `.rootweave/` and templates |
| `arcanum manuscript [PATH]` | Scaffold a novel manuscript with act and chapter structure | Generates frontmatter and metadata |
