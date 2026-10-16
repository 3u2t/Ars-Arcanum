# 🚀 Start Here — 15-Minute Onboarding Tour of Ars Arcanum
`docs/START_HERE.md`

> **New to Ars Arcanum?** Explore the [Master System Architecture (`docs/codebase/ARCHITECTURE.md`)](codebase/ARCHITECTURE.md) or see the [3-Tier Documentation Index (`docs/INDEX.md`)](INDEX.md).

---

## The Zero-CLI Experience: Visual Studio Cockpit & Obsidian Plugin

If you are a fiction writer who prefers not to use the terminal:

1. **Launch the Visual Studio Cockpit**:
   ```bash
   python scripts/arcanum studio --open
   ```
   *(Or double-click the desktop shortcut created by running `scripts/setup_arcanum.ps1`)*.
2. **Open Your Vault in Obsidian**:
   Open your world vault or manuscript directory in Obsidian. The pre-installed **Ars Arcanum Companion Plugin** in `.obsidian/plugins/ars-arcanum/` will automatically display a status-bar badge indicating live vault health (`Arcanum: Clean` vs `Arcanum: N Issues`).
3. **Handle Plot Twists in 1 Click**:
   When continuity alerts appear (e.g., an early hint or revelation), open the Visual Studio Cockpit and click **"Allow / Intended Twist"**. Ars Arcanum will automatically record the rule suppression (`!RULE_ID`) inside your vault's `constitution.yaml`, permanently respecting your creative narrative choices without requiring YAML edits.

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

### 5. Multi-Format Publication Export
```bash
# Compile sanitized, camera-ready Typst print PDF, Kindle EPUB, or Shunn DOCX
python scripts/arcanum publish ~/Manuscripts/Prisoner-of-Sand-Sea --format all
```

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
