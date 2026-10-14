#!/usr/bin/env python3
"""Production Release Verification & Cleanup Helper (`scripts/apply_arcanum_upgrade.py`)."""

from __future__ import annotations

from pathlib import Path
import subprocess  # nosec B404
import sys

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
)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    lib_dir = repo_root / "scripts" / "lib"
    tests_dir = repo_root / "tests"

    # Clean up duplicate root UPGRADE_INSTALL.md if present from earlier pack
    dup_root_file = repo_root / "UPGRADE_INSTALL.md"
    if dup_root_file.exists():
        dup_root_file.unlink()
        print("[CLEANUP] Removed duplicate root UPGRADE_INSTALL.md")

    missing = [m for m in REQUIRED_MODULES if not (lib_dir / m).exists()]
    if missing:
        print(f"[ERROR] Missing modules in scripts/lib/: {missing}", file=sys.stderr)
        return 1
    print(f"[OK] Verified all {len(REQUIRED_MODULES)} production modules in scripts/lib/.")

    res = subprocess.run(  # nosec B603
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py", "-v"],
        cwd=str(repo_root),
        check=False,
    )
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(main())
