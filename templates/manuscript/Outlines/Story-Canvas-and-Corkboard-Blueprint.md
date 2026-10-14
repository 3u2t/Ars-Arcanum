<!-- AI-GENERATED EDUCATIONAL NON-COMMERCIAL CREATIVE WORKFLOW TEMPLATE -->
# Visual Story Canvas, Corkboard & Scene Reordering Blueprint
### Spatial Narrative Architecture & Atomic File Renumbering in Ars Arcanum

> [!NOTE] ⚠️ EDUCATIONAL TEMPLATE (AI-GENERATED)
> **Notice**: This template was AI-generated for educational demonstration and craft guidance within the Ars Arcanum operating system. It is strictly non-commercial and provided solely to demonstrate system features, mechanical schemas, and engine capabilities. Authors should replace placeholder values with their original story canvas layouts and scene cards.

<details>
<summary>💡 <b>Ars Arcanum Engine Guidance & Feature Breakdown (Click to Expand)</b></summary>

### Features Demonstrated in This Blueprint:
- **Visual Story Canvas & Corkboard**: `story_canvas` (`arcanum canvas Manuscripts/Book-01`) — Renders interactive 2D spatial corkboard layouts with color-coded act lanes, POV filters, and tension meters.
- **Atomic Disk Renumberer**: `story_canvas` (`arcanum canvas Manuscripts/Book-01 --renumber`) — Reorders and renumbers disk markdown files (`01_Chapter_01.md` $\to$ `02_Chapter_02.md`) atomically using `os.replace` without corrupting internal cross-links.
- **Hierarchical Tree Outliner**: `obsidian-outliner` (`Outlines/Master-Outline.md`) — Keyboard-driven indentation, folding, and hoisting of beat structures.
- **Obsidian Canvas Integration**: Generates `.canvas` JSON coordinate maps bridging local markdown chapters into Obsidian's visual canvas view.

### How to Use for Your Projects:
1. Arrange scenes horizontally across Act bands on the visual canvas.
2. Color-code cards by POV character or subplot thread.
3. When restructuring your novel's middle act, drag cards to new positions and run `arcanum canvas --renumber` to safely sync your filesystem.
</details>

> *"A novel is not just a sequence of sentences; it is an architecture of scenes occupying space and rhythm."*

---

## 1. Spatial Corkboard Grid Layout (4-Act Band Model)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🎬 ACT I: SETUP & CALL (0% – 25%)                                                                │
│ ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐                   │
│ │ Card 01: Scriptorium │──>│ Card 02: Seal Thefts │──>│ Card 03: Pass Ride   │                   │
│ │ POV: Kaelen [Act I]   │   │ POV: Kaelen [Act I]   │   │ POV: Kaelen [Act I]   │                   │
│ └──────────────────────┘   └──────────────────────┘   └──────────────────────┘                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ ACT II-A: TRIALS & ALLIES (25% – 50%)                                                          │
│ ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐                   │
│ │ Card 04: Vale Refuge │──>│ Card 05: Ambush Run  │──>│ Card 06: Midpoint    │                   │
│ │ POV: Aeloria [Act II]│   │ POV: Kaelen [Act II] │   │ POV: Kaelen [Turn]   │                   │
│ └──────────────────────┘   └──────────────────────┘   └──────────────────────┘                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔥 ACT II-B: CRISIS & DARK NIGHT (50% – 75%)                                                     │
│ ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐                   │
│ │ Card 07: Ridge Clash │──>│ Card 08: Well Blast  │──>│ Card 09: All Is Lost │                   │
│ │ POV: Kaelen [Battle] │   │ POV: Aeloria [Chaos] │   │ POV: Kaelen [Crisis] │                   │
│ └──────────────────────┘   └──────────────────────┘   └──────────────────────┘                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🏆 ACT III: CLIMAX & RESOLUTION (75% – 100%)                                                     │
│ ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐                   │
│ │ Card 10: Resistance  │──>│ Card 11: Final Duel  │──>│ Card 12: New Dawn    │                   │
│ │ POV: Kaelen [Lead]   │   │ POV: Both [Climax]   │   │ POV: Kaelen [Normal] │                   │
│ └──────────────────────┘   └──────────────────────┘   └──────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Card Color-Coding & Metadata Mapping

| Card Color Code | Narrative Association | Obsidian Tag / novelWriter Filter |
| :--- | :--- | :--- |
| 🔵 **Blue (Hex `#2563eb`)** | Primary Protagonist (Kaelen) POV | `@pov: Kaelen` |
| 🟣 **Purple (Hex `#7c3aed`)** | Secondary (Aeloria) POV | `@pov: Aeloria` |
| 🔴 **Red (Hex `#dc2626`)** | High Pacing / Combat / Climax Scene | `@pacing: High-Tension` |
| 🟢 **Green (Hex `#16a34a`)** | Sequel / Introspection / World Exploration | `@pacing: Lyrical-Slow` |
| 🟡 **Yellow (Hex `#d97706`)| Major Midpoint / Act Turning Point | `@beat: Midpoint-Shift` |

---

## 3. Scene Card Anatomy (Atomic Unit)

Each card on the corkboard maps to an atomic scene markdown file with structured frontmatter:

```yaml
---
type: scene_card
card_id: "CH01_SC01"
title: "The Broken Seal in the Archives"
pov: "[[Characters/Character-Template|Kaelen]]"
act: "Act_I"
beat_type: "Inciting Incident"
dramatic_question: "Will Kaelen conceal the stolen treaty before the inquisitors enter?"
value_shift: "Scholarly Calm (+0) -> Desperate Flight (-4)"
target_words: 2200
file_link: "Book-01/01_Act_I/01_Chapter_01.md"
---
```

---

## 4. Reordering Discipline & Disk Synchronization

When dragging cards to a new act or sequence:

```bash
# 1. Preview new sequence without modifying files
arcanum canvas Manuscripts/Book-01 --dry-run

# 2. Execute safe atomic renumbering across disk folders
arcanum canvas Manuscripts/Book-01 --renumber

# 3. Verify internal wikilinks remain 100% intact
arcanum doctor Manuscripts/Book-01
```

<!-- ARS_ARCANUM_COMPREHENSIVE_CRAFT_AND_ENGINE_SHOWCASE -->
<details>
<summary><strong>⚙️ Ars Arcanum Deterministic Engine &amp; Craft Doctrine Integration Guide (Click to Expand)</strong></summary>

### How the CLI Compilers &amp; Craft Engines Use This Template
- **Unified VaultIndex (`arcanum vault-index`)**: Indexes YAML frontmatter (including `|` and `>` multiline block scalars), `@directives`, `[[Wikilinks]]`, multi-paragraph dialogue ratios, and SHA-256 paragraph hashes (`CACHE_VERSION = 3`).
- **Epistemic POV Firewall (`arcanum validate-epistemic`)**: Compares character `knows:` baselines against chapter `learns:` and `references:` (`EPI-201..203`).
- **Planetary Calendar &amp; Route Solver (`arcanum timeline-audit`)**: Audits `world.yaml` month lengths and `Locations/` route distances (`TIME-301..302`).
- **PolyGlot Conlang Linter (`arcanum conlang-check`)**: Validates lexicon terms and phonotactics (`CON-401..402`).
- **Resource Conservation Ledger (`arcanum ledger-audit`)**: Audits `resource_pools` and chapter `state_delta` transitions (`LED-501..502`).
- **Multi-POV Narrative Braid (`arcanum braid`)**: Tracks POV word shares, tension curves, and drought alerts (`BRD-601`).
- **Phase-Aware Effort (`arcanum sprint-effort`)**: Weights First Draft (`1.00x`), On-Phase Outline (`1.00x`), Worldbuilding (`0.50x`), Revision (`0.20x`), and blocks premature editing during Drafting (`0.00x`).
- **Live Obsidian Bridge (`arcanum continuity-suite`)**: Generates `_Arcanum_Diagnostics.md` inside your vault root.

</details>
