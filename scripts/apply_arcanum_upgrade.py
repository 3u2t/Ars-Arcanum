#!/usr/bin/env python3
"""Production Release Verification & Audit Upgrade Helper (`scripts/apply_arcanum_upgrade.py`)."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
from pathlib import Path

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
)

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/INDEX.md",
    "docs/LITE_MODE.md",
    "docs/START_HERE.md",
    "docs/MODERNIZATION_PLAN.md",
    ".github/ISSUE_BACKLOG/GOOD_FIRST_ISSUES.md",
    ".github/workflows/narrative-continuity-ci.yml",
)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    lib_dir = repo_root / "scripts" / "lib"
    src_dir = repo_root / "src" / "arcanum"
    tests_dir = repo_root / "tests"

    dup_root_file = repo_root / "UPGRADE_INSTALL.md"
    if dup_root_file.exists():
        dup_root_file.unlink()
        print("[CLEANUP] Removed duplicate root UPGRADE_INSTALL.md")

    missing = [m for m in REQUIRED_MODULES if not (lib_dir / m).exists()]
    if missing:
        print(f"[ERROR] Missing modules in scripts/lib/: {missing}", file=sys.stderr)
        return 1
    print(f"[OK] Verified all {len(REQUIRED_MODULES)} production modules in scripts/lib/.")

    if not (src_dir / "cli_bridge.py").exists():
        print("[ERROR] Missing src/arcanum/cli_bridge.py", file=sys.stderr)
        return 1
    print("[OK] Verified consolidated src/arcanum/ package hierarchy and cli_bridge.py.")

    missing_docs = [d for d in REQUIRED_DOCS if not (repo_root / d).exists()]
    if missing_docs:
        print(f"[ERROR] Missing required audit docs/workflows: {missing_docs}", file=sys.stderr)
        return 1
    print(f"[OK] Verified all {len(REQUIRED_DOCS)} tiered documentation and CI backlog artifacts.")

    res = subprocess.run(  # nosec B603
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py", "-v"],
        cwd=str(repo_root),
        check=False,
    )
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
