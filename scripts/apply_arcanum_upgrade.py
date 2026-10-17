#!/usr/bin/env python3
"""Master Upgrade, Documentation Synchronizer, Workbook Auto-Sync & Test Runner (`scripts/apply_arcanum_upgrade.py`)."""

from __future__ import annotations

import datetime
import enum
import os
from pathlib import Path
import subprocess  # nosec B404
import sys
import typing

# Ensure Python 3.10 compatibility if any module in the repo references Python 3.11+ stdlib attributes
if not hasattr(datetime, "UTC"):
    setattr(datetime, "UTC", datetime.timezone.utc)  # noqa: B010
if not hasattr(enum, "StrEnum"):
    class _StrEnum(str, enum.Enum):
        pass
    setattr(enum, "StrEnum", _StrEnum)  # noqa: B010
if not hasattr(typing, "Self"):
    setattr(typing, "Self", typing.Any)  # noqa: B010

REQUIRED_MODULES: tuple[str, ...] = (
    "vault_index.py",
    "phase_effort_engine.py",
    "diff_core.py",
    "typed_constitution.py",
    "docx_tracked_changes.py",
    "plugin_sandbox.py",
    "epistemic_firewall.py",
    "timeline_solver.py",
    "conlang_linter.py",
    "resource_ledger.py",
    "narrative_braid.py",
    "vault_continuity_runner.py",
    "audit_hardening.py",
    "workbook_sync.py",
)

ZERO_PIP_TEST_SUITES: tuple[str, ...] = (
    "tests.test_audit_fuzz_hardening",
    "tests.test_lite_mode_and_consolidation",
    "tests.test_modernized_docs_integrity",
    "tests.test_phase1_and_effort",
    "tests.test_phases2_3_and_features",
    "tests.test_production_cli_and_obsidian_bridge",
    "tests.test_sample_projects_showcase",
    "tests.test_workbook_ecosystem_sync",
)

CLUTTER_PATHS: tuple[str, ...] = (
    "UPGRADE_INSTALL.md",
    "scripts/arcanum-lite",
    "launchers/arcanum-lite.desktop",
    ".github/RELEASE_v0.2.0_NOTES.md",
)

CROSS_REF_MARKER = "<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->"
CROSS_REF_FOOTER = """

<!-- ARS_ARCANUM_PHASE4_DOCS_SYNC -->
## Phase 1-5 Production CLI, Workbook Sync & Continuity Cross-Reference

- **Master Writing Ecosystem Workbook Sync**: `python scripts/arcanum workbook sync` (`scripts/lib/workbook_sync.py` & `Master_Writing_Ecosystem.xlsx`)
- **Obsidian Lite Mode (4 Core Compilers + 5-Plugin Profile)**: `python3 -m scripts.lib.audit_hardening [VAULT]` (`scripts/lib/audit_hardening.py`)
- **Unified Continuity Suite & Obsidian Bridge**: `python scripts/arcanum continuity-suite [VAULT]` (`scripts/lib/vault_continuity_runner.py`)
- **Phase-Aware Effort & Career Velocity**: `python scripts/arcanum sprint-effort` (`scripts/lib/phase_effort_engine.py`)
- **Epistemic POV & Spoiler Firewall**: `python scripts/arcanum validate-epistemic [VAULT]` (`scripts/lib/epistemic_firewall.py`)
- **Custom Calendar & Route Physics**: `python scripts/arcanum timeline-audit [VAULT]` (`scripts/lib/timeline_solver.py`)
- **PolyGlot Conlang & Phonotactic Linter**: `python scripts/arcanum conlang-check` (`scripts/lib/conlang_linter.py`)
- **Hard Magic & Sci-Fi Resource Ledger**: `python scripts/arcanum ledger-audit [VAULT]` (`scripts/lib/resource_ledger.py`)
- **Multi-POV Narrative Braid & Droughts**: `python scripts/arcanum braid [MANUSCRIPT]` (`scripts/lib/narrative_braid.py`)
- **Fast SHA-256 Paragraph Diff & Scraps**: `python scripts/arcanum diff-fast OLD.md NEW.md` (`scripts/lib/diff_core.py`)
- **Bidirectional Word Tracked Changes Sync**: `python scripts/arcanum docx-tracked` (`scripts/lib/docx_tracked_changes.py`)
"""


def _unclutter_repo(repo_root: Path) -> None:
    """Remove duplicate or superseded files so the repository stays minimal and clean."""
    for rel in CLUTTER_PATHS:
        target = repo_root / rel
        if target.is_file():
            target.unlink()
            print(f"[CLEANUP] Removed redundant file: {rel}")


def _sync_docs_footers(docs_dir: Path) -> None:
    """Ensure every `docs/*.md` file embeds the required Phase 1-5 cross-reference footer."""
    if not docs_dir.is_dir():
        return
    synced = 0
    for md_file in sorted(docs_dir.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        if (
            CROSS_REF_MARKER not in text
            and "Phase 1-4" not in text
            and "Phase 1-5" not in text
            and "continuity-suite" not in text
        ):
            md_file.write_text(text.rstrip() + "\n" + CROSS_REF_FOOTER, encoding="utf-8")
            synced += 1
    if synced:
        print(f"[DOCS] Synchronized cross-reference footer across {synced} docs/*.md file(s).")


def _prune_git_branches(repo_root: Path) -> None:
    """Fetch, prune stale remote-tracking refs, and delete local branches already merged into main."""
    if not (repo_root / ".git").exists():
        return
    subprocess.run(["git", "fetch", "--all", "--prune"], cwd=str(repo_root), check=False)  # nosec B603, B607
    merged = subprocess.run(  # nosec B603, B607
        ["git", "branch", "--merged", "main"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    for line in merged.stdout.splitlines():
        branch = line.strip().lstrip("* ").strip()
        if branch and branch not in ("main", "master"):
            subprocess.run(["git", "branch", "-d", branch], cwd=str(repo_root), check=False)  # nosec B603, B607
            print(f"[GIT PRUNE] Deleted merged local branch: {branch}")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    lib_dir = repo_root / "scripts" / "lib"

    _unclutter_repo(repo_root)
    if "--prepare-release" in sys.argv:
        _sync_docs_footers(repo_root / "docs")
        _prune_git_branches(repo_root)

    missing = [m for m in REQUIRED_MODULES if not (lib_dir / m).exists()]
    if missing:
        print(f"[ERROR] Missing modules in scripts/lib/: {missing}", file=sys.stderr)
        return 1
    print(f"[OK] Verified all {len(REQUIRED_MODULES)} production modules in scripts/lib/.")

    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    extra_pp = f"{repo_root}:{repo_root / 'scripts'}:{lib_dir}"
    env["PYTHONPATH"] = f"{extra_pp}:{existing_pp}" if existing_pp else extra_pp

    # Synchronize Master_Writing_Ecosystem.xlsx if present
    wb_path = repo_root / "Master_Writing_Ecosystem.xlsx"
    if wb_path.is_file():
        sync_res = subprocess.run(  # nosec B603
            [sys.executable, "-m", "scripts.lib.workbook_sync", "sync", "--workspace", str(repo_root)],
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        if sync_res.returncode != 0:
            return sync_res.returncode

    runner_code = (
        "import datetime, enum, typing, unittest, sys; "
        "setattr(datetime, 'UTC', getattr(datetime, 'UTC', datetime.timezone.utc)); "
        f"suites = unittest.defaultTestLoader.loadTestsFromNames({list(ZERO_PIP_TEST_SUITES)!r}); "
        "sys.exit(0 if unittest.TextTestRunner(verbosity=2).run(suites).wasSuccessful() else 1)"
    )
    res = subprocess.run(  # nosec B603
        [sys.executable, "-c", runner_code],
        cwd=str(repo_root),
        env=env,
        check=False,
    )
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
