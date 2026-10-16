#!/usr/bin/env python3
"""Installer, Template Enhancer & Verification Runner for Expanded Sample Projects (`scripts/install_and_verify_samples.py`)."""

from __future__ import annotations

from pathlib import Path
import subprocess  # nosec B404
import sys

DISCLAIMER = "AI-GENERATED EDUCATIONAL NON-COMMERCIAL CREATIVE WORKFLOW TEMPLATE"
MARKER = "<!-- ARS_ARCANUM_COMPREHENSIVE_CRAFT_AND_ENGINE_SHOWCASE -->"
ENHANCEMENT_BLOCK = """
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
"""


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    wb_dir = repo_root / "templates" / "world-bible"
    ms_dir = repo_root / "templates" / "manuscript"
    tests_dir = repo_root / "tests"

    enhanced_count = 0
    for t_dir in (wb_dir, ms_dir):
        if not t_dir.exists():
            continue
        for md_path in sorted(t_dir.rglob("*.md")):
            if "fileClasses" in md_path.parts:
                continue
            text = md_path.read_text(encoding="utf-8")
            if DISCLAIMER not in text:
                text = f"<!-- {DISCLAIMER} -->\n" + text
            if MARKER not in text:
                text = text.rstrip() + "\n" + ENHANCEMENT_BLOCK
                md_path.write_text(text, encoding="utf-8")
                enhanced_count += 1

    print(f"[Samples Upgrade] Enhanced {enhanced_count} template files in templates/world-bible and templates/manuscript.")
    res = subprocess.run(  # nosec B603
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py", "-v"],
        cwd=str(repo_root),
        check=False,
    )
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
