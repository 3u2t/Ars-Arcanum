# ⚡ Ars Arcanum CLI Command Cheatsheet

| Command | Description |
| :--- | :--- |
| `arcanum continuity-suite [VAULT]` | Run all continuity compilers (`EPI-*`, `TIME-*`, `LED-*`, `BRD-*`) and write `_Arcanum_Diagnostics.md` |
| `arcanum obsidian-dashboard [VAULT]` | Refresh the live Obsidian Callout Dashboard note in the vault root |
| `arcanum sprint-effort --book TITLE --stage STAGE --draft N` | Log a phase-weighted writing session (`1.0x` draft/on-phase outline, `0.5x` lore, `0.2x` revision, `0.0x` premature edit block) |
| `arcanum validate-epistemic [VAULT]` | Audit character `knows:` vs. chapter `learns:`/`references:` for POV spoiler leaks (`EPI-201`..`203`) |
| `arcanum timeline-audit [VAULT]` | Verify non-Gregorian calendar dates in `world.yaml` and route travel speeds in `Locations/` (`TIME-301`..`302`) |
| `arcanum conlang-check --pgd FILE.pgd` | Import PolyGlot `.pgd`/`.xml` lexicon, validate phonotactics (`CON-401`..`402`), and build IPA glossary |
| `arcanum ledger-audit [VAULT]` | Audit hard-magic/sci-fi `resource_pools` and chapter `state_delta` balances (`LED-501`..`502`) |
| `arcanum braid [MANUSCRIPT] --html OUT.html` | Analyze multi-POV word share, detect POV droughts (`BRD-601`), and render offline SVG swimlane braid |
| `arcanum diff-fast OLD.md NEW.md --scraps-dir Scraps/` | Run fast two-level SHA-256 paragraph-hash diff and archive cuts `>= 50` words to `Scraps/` |
| `arcanum docx-tracked export IN.md OUT.docx` | Export Markdown CriticMarkup into native Word Tracked Changes (`.docx`) |
| `arcanum docx-tracked pull IN.docx OUT.md` | Pull editor Word Tracked Changes and comments back into Markdown CriticMarkup |
| `arcanum vault-index [VAULT]` | Scan and cache all vault Markdown nodes into `.arcanum_cache.json` (`CACHE_VERSION = 3`) |
