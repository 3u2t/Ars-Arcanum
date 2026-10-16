# 🚀 Start Here — 15-Minute Onboarding Tour of Ars Arcanum
`docs/START_HERE.md`

> **New to Ars Arcanum?** Explore the [Master System Architecture (`docs/codebase/ARCHITECTURE.md`)](codebase/ARCHITECTURE.md) or see the [3-Tier Documentation Index (`docs/INDEX.md`)](INDEX.md).

---

## The Zero-CLI Experience: Windows Launchers, Studio Cockpit & Obsidian Plugin

If you are a fiction writer who prefers not to touch the terminal:

1. **One-Click Setup**:
   - Double-click [`launchers/setup_windows.bat`](../launchers/setup_windows.bat) to configure execution policies and generate a desktop shortcut.
2. **Launch the Visual Studio Cockpit**:
   - Double-click [`launchers/launch_studio.bat`](../launchers/launch_studio.bat) or run:
     ```bash
     python scripts/arcanum studio --open
     ```
   - This opens your default web browser to `http://127.0.0.1:4242`.
3. **Open Your Vault in Obsidian**:
   - Open your world vault or manuscript directory in Obsidian. The pre-installed **Ars Arcanum Companion Plugin** in `.obsidian/plugins/ars-arcanum/` will automatically display a status-bar badge indicating live vault health (`Arcanum: Clean` vs `Arcanum: N Issues`).
4. **Handle Plot Twists in 1 Click**:
   - When continuity alerts appear (e.g., an early foreshadowing hint or deliberate revelation), open the Visual Studio Cockpit and click **"Allow / Intended Twist"**. Ars Arcanum will automatically record the rule suppression (`!RULE_ID`) inside your vault's `constitution.yaml`, permanently respecting your creative narrative choices without requiring YAML edits.
5. **Switch Themes & Typewriter Acoustics**:
   - In the Visual Studio, pick from 11 visual themes (Dark Cyberpunk, Royal Scriptorium, Parchment Sepia, Monokai Pro, etc.) and 10 procedural mechanical typewriter acoustic models (Underwood, Remington, Hermes 3000, IBM Selectric II) synthesized purely via the Web Audio API.

---

## ⚡ Step-by-Step Command-Line Tour

### 1. Scaffold Your Universe & Manuscript
```bash
# Initialize a sovereign speculative fiction cosmos
python scripts/arcanum universe ~/Universes/Reliquary

# Initialize a manuscript with clean act and chapter scaffolds
python scripts/arcanum manuscript ~/Manuscripts/Prisoner-of-Sand-Sea
```

### 2. Log Phase-Weighted Writing Sessions
```bash
# Log drafting words with 1.0x effort multiplier and worldbuilding notes with 0.5x multiplier
python scripts/arcanum sprint-effort --workspace ~/Universes/Reliquary --book "Prisoner of Sand Sea" --stage Drafting --draft 2000 --worldbuilding 500
```

### 3. Run the Continuity Suite & Generate Live Obsidian Diagnostics
```bash
# Run the 4 flagship continuity compilers and write live callouts to _Arcanum_Diagnostics.md
python scripts/arcanum continuity-suite ~/Universes/Reliquary
```

### 4. Audit Character POV Spoiler Boundaries
```bash
# Verify character POV knowledge barriers (EPI-201..203)
python scripts/arcanum validate-epistemic ~/Manuscripts/Prisoner-of-Sand-Sea
```

### 5. Inspect Prose & Dialogue Metrics
```bash
# Measure unicode word count, CriticMarkup churn, CJK ideographs, and dialogue ratio
python scripts/arcanum count-words ~/Manuscripts/Prisoner-of-Sand-Sea/
```

### 6. Run System Doctor & Toolchain Diagnostics
```bash
# Verify toolchain health, optional compilers (typst, pandoc, ruff), and vault integrity
python scripts/arcanum doctor ~/Universes/Reliquary
```

### 7. Multi-Format Publication Export
```bash
# Compile native zero-pip EPUB3, sanitized Typst print PDF, or Shunn DOCX
python scripts/arcanum publish ~/Manuscripts/Prisoner-of-Sand-Sea --format all
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
