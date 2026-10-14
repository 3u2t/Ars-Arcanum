# 🚀 Start Here — 15-Minute Onboarding Tour of Ars Arcanum

> **New to Ars Arcanum?** See the [3-Tier Documentation Index (`docs/INDEX.md`)](INDEX.md) or start with [Obsidian Lite Mode (`docs/LITE_MODE.md`)](LITE_MODE.md) for a zero-friction setup using just 1 command and 5 Obsidian plugins.

0. **One-Command Lite Mode Check (Fastest Start)**:
```bash
python scripts/arcanum-lite ~/Universes/Reliquary
```

1. **Scaffold Your Universe & Manuscript**:
```bash
python scripts/arcanum universe ~/Universes/Reliquary
python scripts/arcanum manuscript ~/Manuscripts/Prisoner-of-Sand-Sea
```

2. **Log Phase-Weighted Writing Sessions**:
```bash
python scripts/arcanum sprint-effort --workspace ~/Universes/Reliquary --book "Prisoner of Sand Sea" --stage Drafting --draft 2000 --worldbuilding 500
```

3. **Run the Continuity Suite & View Live Obsidian Diagnostics**:
```bash
python scripts/arcanum continuity-suite ~/Universes/Reliquary
```
