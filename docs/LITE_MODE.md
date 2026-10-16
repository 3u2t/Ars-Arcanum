# 🪶 Ars Arcanum Lite Mode — Zero-Friction Continuity for Novelists (`docs/LITE_MODE.md`)

**Lite Mode** strips away terminal complexity and plugin bloat so you can focus entirely on drafting your novel while still catching plot holes and continuity breaks automatically.

---

## 1. What Lite Mode Changes

1. **4 Flagship Compilers Only**: Focuses strictly on high-ROI deterministic checks:
   - **Epistemic POV Firewall (`EPI-*`)**: Flags premature character knowledge leaks, post-mortem perceptions, and secret discovery errors.
   - **Timeline & Route Physics (`TIME-*`)**: Verifies planetary calendars, transit velocities across biomes, and chronological sequencing regressions.
   - **Conlang Phonotactics (`CON-*`)**: Validates constructed language terms against syllable templates.
   - **Resource Conservation Ledger (`LED-*`)**: Tracks consumable inventories (mana, ether, ammunition, delta-v) across chapters.
2. **5 Essential Obsidian Plugins (Down from 32)**: Generates `.obsidian/lite_profile.json` enabling only the essential plugins:
   - `dataview`, `templater-obsidian`, `omnisearch`, `obsidian-style-settings`, and `longform`.
3. **Single Callout Dashboard**: Writes `_Arcanum_Lite_Dashboard.md` (or updates `_Arcanum_Diagnostics.md`) at the root of your vault with clean native Obsidian callout cards (`[!success]`, `[!warning]`).
4. **Native First-Party Companion Plugin**: Works hand-in-hand with `templates/world-bible/.obsidian/plugins/ars-arcanum/` to render a status bar badge (`Arcanum: Clean` vs `Arcanum: N Issues`).

---

## 2. Quick Usage

### Windows Launchers (Zero Terminal)
- Double-click [`launchers/launch_studio.bat`](../launchers/launch_studio.bat) to open the Visual Studio Cockpit in your browser.

### Command Line
```bash
# Run Lite Mode audit on your Universe or Manuscript folder
python -m arcanum.cli_bridge continuity-suite ~/Universes/Reliquary

# Or via the native core hardening module
python -m arcanum.core.hardening ~/Universes/Reliquary

# Emit structured JSON diagnostics
python -m arcanum.cli_bridge continuity-suite ~/Universes/Reliquary --json
```

---

## Production CLI & Continuity Cross-Reference

| Capability | Command | Native Engine | Compatibility Facade |
| :--- | :--- | :--- | :--- |
| **Visual Studio Cockpit** | `python scripts/arcanum studio [VAULT] [--port 4242]` | `src.arcanum.server.daemon` | `scripts/lib/studio_server.py` |
| **Unified Continuity Suite** | `python scripts/arcanum continuity-suite [VAULT]` | `src.arcanum.worldbible.runner` | `scripts/lib/vault_continuity_runner.py` |
| **Phase-Aware Effort Points** | `python scripts/arcanum sprint-effort [ARGS]` | `src.arcanum.manuscript.velocity` | `scripts/lib/phase_effort_engine.py` |
| **Epistemic POV Firewall** | `python scripts/arcanum validate-epistemic [VAULT]` | `src.arcanum.worldbible.epistemics` | `scripts/lib/epistemic_firewall.py` |
| **Timeline & Route Physics** | `python scripts/arcanum timeline-audit [VAULT]` | `src.arcanum.worldbible.timeline` | `scripts/lib/timeline_solver.py` |
| **PolyGlot Conlang Linter** | `python scripts/arcanum conlang-check [ARGS]` | `src.arcanum.worldbible.conlang` | `scripts/lib/conlang_linter.py` |
| **Resource Conservation Ledger** | `python scripts/arcanum ledger-audit [VAULT]` | `src.arcanum.worldbible.ledger` | `scripts/lib/resource_ledger.py` |
| **Multi-POV Narrative Braid** | `python scripts/arcanum braid [MANUSCRIPT]` | `src.arcanum.manuscript.braid` | `scripts/lib/narrative_braid.py` |
| **Prose Word & Dialogue Metrics** | `python scripts/arcanum count-words [FILE/VAULT]` | `src.arcanum.manuscript.word_counter` | `scripts/lib/word_counter.py` |
| **Fast Paragraph Diff & Scraps** | `python scripts/arcanum diff-fast OLD.md NEW.md` | `src.arcanum.manuscript.diff` | `scripts/lib/diff_core.py` |
| **Word Tracked Changes Sync** | `python scripts/arcanum docx-tracked [export/pull]` | `src.arcanum.publishing.docx` | `scripts/lib/docx_tracked_changes.py` |
| **Multi-Format Publishing** | `python scripts/arcanum publish [MANUSCRIPT] --format ...` | `src.arcanum.publishing.publisher` | `scripts/lib/publisher.py` |
| **System Diagnostics & Doctor** | `python scripts/arcanum doctor [VAULT]` | `src.arcanum.core.diagnostics` | `scripts/lib/diagnostics.py` |
| **Schema Migration Engine** | `python scripts/arcanum migrate [VAULT]` | `src.arcanum.core.migrate` | `scripts/lib/migrate.py` |
