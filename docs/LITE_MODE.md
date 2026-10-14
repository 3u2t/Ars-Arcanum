# 🪶 Ars Arcanum Lite Mode — Zero-Friction Continuity for Novelists

**Lite Mode** strips away terminal complexity and plugin bloat so you can focus entirely on drafting your novel while still catching plot holes automatically.

## What Lite Mode Changes

1. **4 Flagship Compilers Only**: Runs only the high-ROI deterministic checks—**Epistemic POV Firewall** (`EPI-*`), **Timeline & Route Physics** (`TIME-*`), **Conlang Phonotactics** (`CON-*`), and **Resource Conservation Ledger** (`LED-*`).
2. **5 Essential Obsidian Plugins (Down from 32)**: Generates `.obsidian/lite_profile.json` enabling only `dataview`, `templater-obsidian`, `omnisearch`, `obsidian-style-settings`, and `longform`.
3. **Single Callout Dashboard**: Writes `_Arcanum_Lite_Dashboard.md` at the root of your vault with a scannable table and zero configuration required.

## Quick Usage

```bash
# Run Lite Mode directly on your Universe or Manuscript folder
python scripts/arcanum-lite ~/Universes/Reliquary

# Or invoke the standalone Lite CLI bridge
python -m src.arcanum.cli_bridge ~/Universes/Reliquary
```
