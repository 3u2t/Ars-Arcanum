# 📖 Ars Arcanum Complete Author & Worldbuilder Manual

## 1. The Nine-Stage Authorial Lifecycle & Phase-Aware Effort Multipliers

Ars Arcanum supports nine canonical project stages (`Concept`, `Pre-Draft Outline`, `Drafting`, `Pre-Revision Outline`, `Revision`, `Beta Review`, `Proofing`, `Querying`, `Publishing`) via `arcanum sprint-effort`:
- **First Draft Prose**: `1.00x` across all stages.
- **Outlining**: `1.00x` during `Concept`, `Pre-Draft Outline`, and `Pre-Revision Outline` (`0.50x` off-phase).
- **Worldbuilding / Lore**: `0.50x` (`2` lore words = `1` effort point).
- **Revisions**: `0.20x` during `Revision`, `Beta Review`, and `Proofing` (`5` revised words = `1` effort point), and **`0.00x` during `Drafting`** to prevent premature editing.

## 2. Frontmatter Keys for Continuity Compilers (`arcanum continuity-suite`)

- **`Characters/<Name>.md`**: `knows: [fact_id, ...]` and `resource_pools: {ether_vials: 4}`.
- **`Locations/<Route>.md`**: `type: route`, `origin`, `destination`, `distance_km`, `terrain`.
- **Chapter Markdown Files**: `chapter`, `pov`, `location`, `year`, `month`, `day`, `travel_mode`, `references: [...]`, `learns: [...]`, `state_delta: {...}`, `subplots: [...]`, `tension: 1..10`.
