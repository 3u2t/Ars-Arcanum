<!-- AI-GENERATED EDUCATIONAL NON-COMMERCIAL CREATIVE WORKFLOW TEMPLATE -->
# Print Typesetting, Preflight Validation & Spine Width Specification

> [!NOTE] ⚠️ EDUCATIONAL TEMPLATE (AI-GENERATED)
> **Notice**: This template was AI-generated for educational demonstration and craft guidance within the Ars Arcanum operating system. It is strictly non-commercial and provided solely to demonstrate system features, mechanical schemas, and engine capabilities. Authors should replace placeholder values with their original publication specifications.

<details>
<summary>💡 <b>Ars Arcanum Engine Guidance & Feature Breakdown (Click to Expand)</b></summary>

### Features Demonstrated in This Specification:
- **Spine Width Calculator**: `preflight` (`arcanum preflight Manuscripts/Book-01 --pages 380 --paper cream-55`) — Calculates exact spine thickness across KDP and IngramSpark paper types ($T_s = \text{Pages} / \text{PPI}$) to prevent spine wrap misalignment.
- **POD Signature Auditor**: `preflight` (`arcanum preflight Manuscripts/Book-01`) — Ensures final page counts align to 4-page and 16-page press signatures, avoiding unwanted blank trailing leaves.
- **Typst Book Template Engine**: `typst` (`templates/typst/book_template.typ`) — Reusable, high-performance, offline typesetting layout engine.
- **Acoustic & Audio Proofing Pipeline**: `audio_proof` (`arcanum audio-proof Manuscripts/Book-01`) — Synthesizes acoustic SSML markup and listening timing estimation.
- **SSML Prosody Optimization**: `audio_proof` (`arcanum audio-proof --ssml`) — Calibrates prosodic rate, pitch, and dialogue pause durations.
- **Chunked Buffer Exporter**: `audio_proof` (`arcanum audio-proof --chunk 500`) — Chunks manuscripts into deterministic buffers for offline Piper / eSpeak NG TTS synthesis.
- **Audio Listening Estimator**: `audio_proof` (`arcanum audio-proof --estimate`) — Calculates total narration listening time and word cadence distributions.

### How to Use for Your Projects:
1. Select your target trim size (e.g. 5.5" × 8.5" or 6" × 9" Royal Hardcover).
2. Calculate your exact spine width before commissioning cover artwork.
3. Run `arcanum preflight` before uploading final interior PDFs to distributors.
4. Run `arcanum audio-proof` to generate SSML audiobooks and proof prose rhythm acoustically.
</details>

---

## 📏 Trim Size & Spine Width Calculation Matrix

```
[Total Manuscript Word Count: ~95,000 Words]
  └── Formatted Interior Page Count: 384 Pages (Divisible by 4-Page Signature)
```

| Paper Stock Type | Paper Color | Pages Per Inch (PPI) | Formula for Spine Thickness ($T_s$) | 384-Page Spine Width |
| :--- | :--- | :--- | :--- | :--- |
| **KDP Standard Cream** | 55# Cream | `434 PPI` | $T_s = \text{Pages} / 434$ | **0.885 inches (22.5 mm)** |
| **KDP Standard White** | 50# White | `490 PPI` | $T_s = \text{Pages} / 490$ | **0.784 inches (19.9 mm)** |
| **IngramSpark Groundwood**| 50# Cream | `444 PPI` | $T_s = \text{Pages} / 444$ | **0.865 inches (22.0 mm)** |
| **IngramSpark Premium Color**| 70# White| `357 PPI` | $T_s = \text{Pages} / 357$ | **1.076 inches (27.3 mm)** |

---

## 📐 Preflight Margin & Gutter Invariants (5.5" × 8.5" Standard)

```
       ┌─────────────────────────────┐
       │     Top Margin: 0.75 in     │
       │  ┌───────────────────────┐  │
       │  │                       │  │
Outer  │  │                       │  │ Gutter / Inner
Margin │  │   Body Text Area      │  │ Margin:
0.625" │  │   (Min 10.5pt Typst)  │  │ 0.875 in (Accounts for spine glue)
       │  │                       │  │
       │  └───────────────────────┘  │
       │    Bottom Margin: 0.75 in   │
       └─────────────────────────────┘
```

---

## 🛡️ Preflight Checklist Before Press Submission
- [x] All chapter title pages start on a **recto** (right-hand / odd-numbered) page.
- [x] Running headers and page folios suppressed on blank verso pages.
- [x] Total page count is a multiple of 4 (zero orphan blank pages).
- [x] All embedded chapter header ornament graphics are vector SVGs or 300+ DPI bitmaps.
- [x] Font licenses validated for offline commercial embedding.

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
