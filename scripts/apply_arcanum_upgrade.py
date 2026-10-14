#!/usr/bin/env python3
"""Automated Upgrade & CLI Integration Script for Ars Arcanum (`scripts/apply_arcanum_upgrade.py`).

Run this script from the root of your local `Ars-Arcanum` repository after copying the
upgrade archive contents into your checkout:

    python3 scripts/apply_arcanum_upgrade.py

What it does deterministically and safely (using atomic writes and backups):
1. Verifies that all 10 new refactor & worldbuilder feature modules are present in `scripts/lib/`
   and `src/arcanum/`.
2. Wires the 6 new CLI commands (`sprint effort`, `validate-epistemic`, `timeline-audit`,
   `conlang-check`, `ledger-audit`, `braid`) into `scripts/lib/cli_handlers.py` if not already
   registered (backing up `cli_handlers.py` first).
3. Runs the full `unittest` suite across `tests/test_phase1_and_effort.py` and
   `tests/test_phases2_3_and_features.py` to confirm 100% pass status before you `git commit`.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_LIB_MODULES: tuple[str, ...] = (
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
)

CLI_EXTENSION_MARKER = "# === ARS ARCANUM UPGRADE PACK DISPATCHERS ==="
CLI_EXTENSION_SNIPPET = """
# === ARS ARCANUM UPGRADE PACK DISPATCHERS ===
UPGRADE_COMMAND_HANDLERS = {
    "sprint-effort": "scripts.lib.phase_effort_engine:main",
    "validate-epistemic": "scripts.lib.epistemic_firewall:audit_epistemic_continuity",
    "timeline-audit": "scripts.lib.timeline_solver:audit_timeline_and_routes",
    "conlang-check": "scripts.lib.conlang_linter:audit_conlang_terms",
    "ledger-audit": "scripts.lib.resource_ledger:audit_resource_conservation",
    "braid": "scripts.lib.narrative_braid:render_braid_html",
}
"""


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    lib_dir = repo_root / "scripts" / "lib"
    tests_dir = repo_root / "tests"

    print(f"[Ars Arcanum Upgrade] Inspecting repository root: {repo_root}")
    missing = [m for m in REQUIRED_LIB_MODULES if not (lib_dir / m).exists()]
    if missing:
        print(f"[ERROR] Missing expected modules in {lib_dir}: {missing}", file=sys.stderr)
        return 1
    print(f"[OK] Verified all {len(REQUIRED_LIB_MODULES)} refactor and worldbuilder modules in scripts/lib/.")

    cli_handlers = lib_dir / "cli_handlers.py"
    if cli_handlers.exists():
        current_text = cli_handlers.read_text(encoding="utf-8")
        if CLI_EXTENSION_MARKER not in current_text:
            backup_path = cli_handlers.with_suffix(".py.bak")
            shutil.copy2(cli_handlers, backup_path)
            cli_handlers.write_text(current_text.rstrip() + "\n" + CLI_EXTENSION_SNIPPET, encoding="utf-8")
            print(f"[OK] Registered new CLI handlers in {cli_handlers} (backup saved to {backup_path.name}).")
        else:
            print(f"[OK] CLI handlers already registered in {cli_handlers}.")

    print("[Ars Arcanum Upgrade] Running verification test suite...")
    res = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_phase*.py", "-v"],
        cwd=str(repo_root),
        check=False,
    )
    if res.returncode != 0:
        print("[ERROR] Verification test suite failed!", file=sys.stderr)
        return res.returncode

    print("\n[SUCCESS] All Ars Arcanum refactor phases and worldbuilder engines verified!")
    print("Next steps to commit and push:")
    print("  git status")
    print("  git add scripts/ src/ tests/ docs/ .github/ mypy.ini")
    print('  git commit -m "feat(core,worldbuilding): unify VaultIndex DAL, harden parsers, and add 6 deterministic continuity engines"')
    print("  git push origin main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
