"""Unified CLI bridge for `arcanum-lite` and `arcanum lite-check` (`src/arcanum/cli_bridge.py`)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from scripts.lib.audit_hardening import run_lite_continuity_check


def build_lite_parser() -> argparse.ArgumentParser:
    """Create the argument parser for `arcanum-lite` / `arcanum lite-check`."""
    parser = argparse.ArgumentParser(
        prog="arcanum-lite",
        description="One-command Obsidian Lite Mode continuity runner (EPI-*, TIME-*, CON-*, LED-*).",
    )
    parser.add_argument(
        "vault",
        nargs="?",
        default=".",
        help="Path to the target Universe or Manuscript vault directory (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON summary to stdout.",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Skip writing `_Arcanum_Lite_Dashboard.md` to the vault root.",
    )
    return parser


def main_lite(argv: Sequence[str] | None = None) -> int:
    """Execute the Obsidian Lite Mode continuity check from the command line."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] == "lite-check":
        args_list = args_list[1:]

    parser = build_lite_parser()
    parsed = parser.parse_args(args_list)
    vault_path = Path(parsed.vault).resolve()
    if not vault_path.exists():
        print(f"[ERROR] Vault path does not exist: {vault_path}", file=sys.stderr)
        return 2

    report = run_lite_continuity_check(vault_path, write_dashboard=not parsed.no_dashboard)
    if parsed.as_json:
        payload = {
            "vault_root": str(report.vault_root),
            "status": report.status,
            "total_issues": report.total_issues,
            "counts_by_prefix": report.counts_by_prefix,
            "dashboard_path": str(report.dashboard_path) if report.dashboard_path else None,
            "profile_path": str(report.profile_path) if report.profile_path else None,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"[ARCANUM LITE] Status: {report.status} | "
            f"Findings: {report.total_issues} | "
            f"Dashboard: {report.dashboard_path}"
        )
    return 0 if report.total_issues == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main_lite())
