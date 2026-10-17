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
    from lib.typed_constitution import (
        load_yaml_constitution_file,
        resolve_constitution_cascade,
    )
    from lib.vault_index import PathSecurityError, VaultIndex, atomic_write, is_safe_subpath, parse_frontmatter
except ImportError:
    from epistemic_firewall import audit_vault_epistemic
    from narrative_braid import analyze_narrative_braid, scan_manuscript_braid
    from phase_effort_engine import PhaseEffortLedger
    from resource_ledger import audit_vault_resources
    from timeline_solver import audit_vault_timeline
    from typed_constitution import (
        load_yaml_constitution_file,
        resolve_constitution_cascade,
    )
    from vault_index import PathSecurityError, VaultIndex, atomic_write, is_safe_subpath, parse_frontmatter


def run_full_vault_continuity_suite(
    vault_root: Path,
    *,
    world_root: Path | None = None,
    write_obsidian_dashboard: bool = True,
    dashboard_filename: str = "_Arcanum_Diagnostics.md",
) -> dict[str, Any]:
    """Run all deterministic continuity engines over `vault_root` and optionally write the
    Obsidian callout dashboard note.
    """
    resolved_root = vault_root.resolve()
    resolved_world_root: Path | None = None
    if world_root is not None:
        cand_dir = Path(world_root).resolve()
        if cand_dir.is_dir():
            resolved_world_root = cand_dir
    else:
        ms_yaml = resolved_root / "manuscript.yaml"
        if not ms_yaml.is_file() and (resolved_root.parent / "manuscript.yaml").is_file():
            ms_yaml = resolved_root.parent / "manuscript.yaml"

        if ms_yaml.is_file():
            try:
                ms_raw = ms_yaml.read_text(encoding="utf-8")
                wrapped = ms_raw if ms_raw.lstrip().startswith("---") else f"---\n{ms_raw}\n---\n"
                ms_meta, _ = parse_frontmatter(wrapped)
                uni_path_str = ms_meta.get("universe") or ms_meta.get("world_bible") or ms_meta.get("series_bible")
                if uni_path_str:
                    cand = (ms_yaml.parent / str(uni_path_str)).resolve()
                    if not cand.is_dir():
                        cand = (resolved_root / str(uni_path_str)).resolve()
                    if cand.is_dir():
                        resolved_world_root = cand
            except Exception:
                pass

    index = VaultIndex(resolved_root)
    nodes = index.scan_vault()

    epistemic_report = audit_vault_epistemic(resolved_root, world_root=resolved_world_root).to_dict()
    timeline_report = audit_vault_timeline(resolved_root, world_root=resolved_world_root)
    ledger_report = audit_vault_resources(resolved_root, world_root=resolved_world_root)
    braid_nodes = scan_manuscript_braid(resolved_root)
    braid_report = analyze_narrative_braid(braid_nodes)

    effort_ledger = PhaseEffortLedger(resolved_root)
    sessions = effort_ledger.load_sessions()
    total_effort_points = round(sum(s.effort_points for s in sessions), 2)

    constitution_path = None
    for cand_file in (
        resolved_root / "constitution.yaml",
        resolved_root / "constitution.json",
        resolved_root.parent / "constitution.yaml",
        resolved_root.parent / "manuscript.yaml",
        resolved_root / "manuscript.yaml",
    ):
        if cand_file.is_file():
            constitution_path = cand_file
            break

    const_dict = load_yaml_constitution_file(constitution_path) if constitution_path else None

    world_dict = None
    if resolved_world_root:
        for cand_w in (
            resolved_world_root / "constitution.yaml",
            resolved_world_root / "constitution.json",
            resolved_world_root / "world.yaml",
            resolved_world_root / ".arcanum" / "constitution.yaml",
        ):
            if cand_w.is_file():
                world_dict = load_yaml_constitution_file(cand_w)
                break

    constitution = resolve_constitution_cascade(world_dict=world_dict, manuscript_dict=const_dict)

    if "violations" in epistemic_report:
        epistemic_report["violations"] = [
            v for v in epistemic_report["violations"]
            if constitution.is_rule_enabled(str(v.get("rule_id", "EPI-201")))
        ]
        epistemic_report["passed"] = len(epistemic_report["violations"]) == 0

    if "anomalies" in timeline_report:
        timeline_report["anomalies"] = [
            a for a in timeline_report["anomalies"]
            if constitution.is_rule_enabled(str(a.get("rule_id", "TIME-301")))
        ]
        timeline_report["passed"] = len(timeline_report["anomalies"]) == 0

    if "violations" in ledger_report:
        ledger_report["violations"] = [
            lv for lv in ledger_report["violations"]
            if constitution.is_rule_enabled(str(lv.get("rule_id", "LED-501")))
        ]
        ledger_report["passed"] = len(ledger_report["violations"]) == 0

    if "drought_alerts" in braid_report and not constitution.is_rule_enabled("BRD-601"):
        braid_report["drought_alerts"] = []

    all_passed = bool(
        epistemic_report["passed"]
        and timeline_report["passed"]
        and ledger_report["passed"]
        and len(braid_report["drought_alerts"]) == 0
    )

    consolidated: dict[str, Any] = {
        "vault_root": str(resolved_root),
        "world_root": str(resolved_world_root) if resolved_world_root else None,
        "constitution": constitution.to_dict(),
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

    try:
        from lib.workbook_sync import auto_sync_workbook_if_present
    except ImportError:
        try:
            from workbook_sync import auto_sync_workbook_if_present  # type: ignore[no-redef]
        except ImportError:
            auto_sync_workbook_if_present = None  # type: ignore[assignment]
    if auto_sync_workbook_if_present is not None:
        wb_res = auto_sync_workbook_if_present(resolved_root)
        if wb_res is not None:
            consolidated["workbook_synced"] = wb_res.workbook_path

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
    ]

    if suite_result.get("world_root"):
        lines.append(f"> 🌌 **Federated Series Universe**: `{Path(suite_result['world_root']).name}`")

    lines.extend(["", "## 1. Epistemic POV & Spoiler Firewall (`EPI-*`)"])

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
    parser.add_argument("--world", "--universe", type=Path, default=None, help="World bible / universe root")
    parser.add_argument(
        "--no-obsidian-dashboard",
        action="store_true",
        help="Skip writing _Arcanum_Diagnostics.md into the vault root",
    )
    args = parser.parse_args(argv)

    res = run_full_vault_continuity_suite(
        args.vault,
        world_root=args.world,
        write_obsidian_dashboard=not args.no_obsidian_dashboard,
    )
    sys.stdout.write(json.dumps(res, indent=2) + "\n")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
