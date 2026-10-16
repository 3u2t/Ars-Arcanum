"""Unified Vault Continuity Runner & Live Obsidian Diagnostics Bridge (`arcanum continuity-suite`).

Executes all 6 deterministic Ars Arcanum continuity and velocity engines in a single pass over
a Sovereign Vault (`VaultIndex`) and optionally writes a live Obsidian Callout Dashboard
(`_Arcanum_Diagnostics.md`) directly into the vault root so authors see real-time continuity
alerts (`EPI-201`, `TIME-301`, `CON-401`, `LED-501`, `BRD-601`) and daily Phase-Aware Effort
metrics inside their Obsidian sidebar without leaving their prose editor.

Repository Target: `scripts/lib/vault_continuity_runner.py`
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

try:
    from lib.epistemic_firewall import audit_vault_epistemic
    from lib.narrative_braid import analyze_narrative_braid, scan_manuscript_braid
    from lib.phase_effort_engine import PhaseEffortLedger
    from lib.resource_ledger import audit_vault_resources
    from lib.timeline_solver import audit_vault_timeline
    from lib.vault_index import PathSecurityError, VaultIndex, atomic_write, is_safe_subpath
except ImportError:
    from epistemic_firewall import audit_vault_epistemic
    from narrative_braid import analyze_narrative_braid, scan_manuscript_braid
    from phase_effort_engine import PhaseEffortLedger
    from resource_ledger import audit_vault_resources
    from timeline_solver import audit_vault_timeline
    from vault_index import PathSecurityError, VaultIndex, atomic_write, is_safe_subpath


def run_full_vault_continuity_suite(
    vault_root: Path,
    *,
    write_obsidian_dashboard: bool = True,
    dashboard_filename: str = "_Arcanum_Diagnostics.md",
) -> dict[str, Any]:
    """Run all deterministic continuity engines over `vault_root` and optionally write the
    Obsidian callout dashboard note.
    """
    resolved_root = vault_root.resolve()
    index = VaultIndex(resolved_root)
    nodes = index.scan_vault()

    epistemic_report = audit_vault_epistemic(resolved_root).to_dict()
    timeline_report = audit_vault_timeline(resolved_root)
    ledger_report = audit_vault_resources(resolved_root)
    braid_nodes = scan_manuscript_braid(resolved_root)
    braid_report = analyze_narrative_braid(braid_nodes)

    effort_ledger = PhaseEffortLedger(resolved_root)
    sessions = effort_ledger.load_sessions()
    total_effort_points = round(sum(s.effort_points for s in sessions), 2)

    all_passed = bool(
        epistemic_report["passed"]
        and timeline_report["passed"]
        and ledger_report["passed"]
        and len(braid_report["drought_alerts"]) == 0
    )

    consolidated: dict[str, Any] = {
        "vault_root": str(resolved_root),
        "passed": all_passed,
        "documents_indexed": len(nodes),
        "total_words": sum(n.metrics.total_words for n in nodes),
        "logged_sprint_sessions": len(sessions),
        "cumulative_effort_points": total_effort_points,
        "epistemic": epistemic_report,
        "timeline": timeline_report,
        "resource_ledger": ledger_report,
        "narrative_braid": braid_report,
    }

    if write_obsidian_dashboard:
        dash_path = resolved_root / dashboard_filename
        if not is_safe_subpath(resolved_root, dash_path):
            raise PathSecurityError(f"Dashboard path escapes vault root: {dash_path}")
        markdown_callout = render_obsidian_diagnostics_markdown(consolidated)
        atomic_write(dash_path, markdown_callout)
        consolidated["obsidian_dashboard"] = str(dash_path)

    return consolidated


def render_obsidian_diagnostics_markdown(suite_result: dict[str, Any]) -> str:
    """Format the continuity suite output as a native Obsidian Callout Dashboard (`.md`)."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_badge = "PASS" if suite_result["passed"] else "ACTION REQUIRED"
    callout_type = "success" if suite_result["passed"] else "warning"

    epi_violations = suite_result["epistemic"]["violations"]
    time_anomalies = suite_result["timeline"]["anomalies"]
    led_violations = suite_result["resource_ledger"]["violations"]
    droughts = suite_result["narrative_braid"]["drought_alerts"]

    lines = [
        "---",
        "title: Ars Arcanum Live Continuity & Effort Dashboard",
        f"updated_at: {stamp}",
        f"status: {status_badge}",
        "---",
        "",
        f"> [!{callout_type}] Ars Arcanum Continuity Compiler — {status_badge}",
        f"> **Documents Indexed**: `{suite_result['documents_indexed']}` | "
        f"**Total Vault Words**: `{suite_result['total_words']:,}` | "
        f"**Cumulative Effort Points**: `{suite_result['cumulative_effort_points']:,.1f}`",
        "",
        "## 1. Epistemic POV & Spoiler Firewall (`EPI-*`)",
    ]

    if not epi_violations:
        lines.append("- No POV spoiler leaks or epistemic breaches detected.")
    else:
        for v in epi_violations:
            lines.append(f"- **{v['rule_id']} ({v['severity']})**: {v['message']}")

    lines.extend(["", "## 2. Planetary Calendar & Route Physics (`TIME-*`)"])
    if not time_anomalies:
        lines.append("- All character movements satisfy terrain and calendar constraints.")
    else:
        for a in time_anomalies:
            lines.append(f"- **{a['rule_id']}**: {a['message']}")

    lines.extend(["", "## 3. Hard Magic & Sci-Fi Resource Ledger (`LED-*`)"])
    if not led_violations:
        lines.append("- All tracked resource pools remain within conservation bounds.")
    else:
        for lv in led_violations:
            lines.append(f"- **{lv['rule_id']}**: {lv['message']}")

    lines.extend(["", "## 4. Narrative Braid & POV Droughts (`BRD-*`)"])
    if not droughts:
        lines.append("- All POV characters remain within active word-drought thresholds.")
    else:
        for dr in droughts:
            lines.append(f"- **{dr['rule_id']}**: {dr['message']}")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum continuity-suite` / `arcanum obsidian-dashboard`."""
    parser = argparse.ArgumentParser(
        prog="arcanum continuity-suite",
        description="Run all deterministic continuity compilers and update the Obsidian diagnostics note.",
    )
    parser.add_argument("vault", nargs="?", type=Path, default=Path.cwd(), help="Vault or manuscript root")
    parser.add_argument(
        "--no-obsidian-dashboard",
        action="store_true",
        help="Skip writing _Arcanum_Diagnostics.md into the vault root",
    )
    args = parser.parse_args(argv)

    res = run_full_vault_continuity_suite(
        args.vault,
        write_obsidian_dashboard=not args.no_obsidian_dashboard,
    )
    sys.stdout.write(json.dumps(res, indent=2) + "\n")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
