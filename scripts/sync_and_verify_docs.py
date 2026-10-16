#!/usr/bin/env python3
"""Safe Documentation Synchronizer & Full Test Suite Verifier (`scripts/sync_and_verify_docs.py`)."""

from __future__ import annotations

from pathlib import Path
import subprocess  # nosec B404
import sys

CROSS_REF_MARKER = "<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->"
CROSS_REF_FOOTER = """

<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1–4 Production CLI & Continuity Cross-Reference

- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Visual Studio Cockpit**: `python scripts/arcanum studio [VAULT]` (`src/arcanum/server/daemon.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
- **Multi-Format Publication & Prose Sanitizer**: `python scripts/arcanum publish [MANUSCRIPT]` (`scripts/lib/publisher.py`)
"""


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    tests_dir = repo_root / "tests"

    updated_count = 0
    if docs_dir.exists():
        for md_file in sorted(docs_dir.rglob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            if CROSS_REF_MARKER not in text and "Phase 1–4" not in text and "continuity-suite" not in text:
                md_file.write_text(text.rstrip() + "\n" + CROSS_REF_FOOTER, encoding="utf-8")
                updated_count += 1

    print(f"[Docs Sync] Synchronized cross-reference footers across {updated_count} additional docs/*.md manuals.")
    res = subprocess.run(  # nosec B603
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py", "-v"],
        cwd=str(repo_root),
        check=False,
    )
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
