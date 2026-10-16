#!/usr/bin/env python3
"""Safe Documentation Synchronizer & Full Test Suite Verifier (`scripts/sync_and_verify_docs.py`)."""

from __future__ import annotations

from pathlib import Path
import subprocess  # nosec B404
import sys

CROSS_REF_MARKER = "<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->"
CROSS_REF_FOOTER = """

<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
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
