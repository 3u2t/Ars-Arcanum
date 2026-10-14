"""Hard Magic & Sci-Fi Resource Conservation Ledger (`arcanum ledger-audit`).

Audits state transitions across manuscript chapters against rules defined in
`Magic-Technology/` and `Artifacts/`:
- Tracks finite character/ship pools (e.g., `ether_vials`, `mana`, `ammunition`, `water_liters`,
  `delta_v_mps`, `corruption_index`) across chronological chapter `state_delta` blocks.
- Flags deterministic continuity errors (`LED-501` & `LED-502`).

Repository Target: `scripts/lib/resource_ledger.py`
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import Any

try:
    from lib.vault_index import VaultIndex
except ImportError:
    from vault_index import VaultIndex


@dataclass(frozen=True)
class ResourcePoolSpec:
    """Constraint specification for a tracked resource on an entity (`character` or `vessel`)."""

    entity_name: str
    resource_name: str
    initial_value: float
    min_bound: float = 0.0
    max_bound: float = 1_000_000.0
    unit: str = "units"


@dataclass(frozen=True)
class ChapterResourceDelta:
    """Resource change occurring in a specific chapter."""

    chapter_index: int
    chapter_title: str
    entity_name: str
    resource_name: str
    delta: float
    reason: str = ""


@dataclass(frozen=True)
class LedgerViolation:
    """Detected resource conservation or capacity cap breach."""

    rule_id: str
    chapter_index: int
    chapter_title: str
    entity_name: str
    resource_name: str
    balance_after: float
    bound_violated: float
    message: str


def audit_resource_conservation(
    *,
    pools: list[ResourcePoolSpec],
    deltas: list[ChapterResourceDelta],
) -> dict[str, Any]:
    """Simulate resource balances across chapters and report any negative deficits or cap breaches."""
    spec_map: dict[tuple[str, str], ResourcePoolSpec] = {
        (p.entity_name, p.resource_name): p for p in pools
    }
    balances: dict[tuple[str, str], float] = {
        (p.entity_name, p.resource_name): float(p.initial_value) for p in pools
    }
    history: list[dict[str, Any]] = []
    violations: list[LedgerViolation] = []

    for d in sorted(deltas, key=lambda x: x.chapter_index):
        key = (d.entity_name, d.resource_name)
        spec = spec_map.get(
            key,
            ResourcePoolSpec(entity_name=d.entity_name, resource_name=d.resource_name, initial_value=0.0),
        )
        prev_bal = balances.get(key, spec.initial_value)
        new_bal = round(prev_bal + d.delta, 4)
        balances[key] = new_bal

        history.append(
            {
                "chapter_index": d.chapter_index,
                "chapter_title": d.chapter_title,
                "entity_name": d.entity_name,
                "resource_name": d.resource_name,
                "delta": d.delta,
                "balance_before": prev_bal,
                "balance_after": new_bal,
                "unit": spec.unit,
                "reason": d.reason,
            }
        )

        if new_bal < spec.min_bound:
            violations.append(
                LedgerViolation(
                    rule_id="LED-501",
                    chapter_index=d.chapter_index,
                    chapter_title=d.chapter_title,
                    entity_name=d.entity_name,
                    resource_name=d.resource_name,
                    balance_after=new_bal,
                    bound_violated=spec.min_bound,
                    message=(
                        f"LED-501 Resource Deficit: '{d.entity_name}' expends {abs(d.delta)} "
                        f"{spec.unit} of '{d.resource_name}' in Chapter {d.chapter_index} "
                        f"('{d.chapter_title}'), dropping balance to {new_bal} {spec.unit} "
                        f"(minimum allowed: {spec.min_bound})."
                    ),
                )
            )
        elif new_bal > spec.max_bound:
            violations.append(
                LedgerViolation(
                    rule_id="LED-502",
                    chapter_index=d.chapter_index,
                    chapter_title=d.chapter_title,
                    entity_name=d.entity_name,
                    resource_name=d.resource_name,
                    balance_after=new_bal,
                    bound_violated=spec.max_bound,
                    message=(
                        f"LED-502 Capacity Overflow: '{d.entity_name}' reaches {new_bal} "
                        f"{spec.unit} of '{d.resource_name}' in Chapter {d.chapter_index} "
                        f"('{d.chapter_title}'), exceeding maximum cap of {spec.max_bound} {spec.unit}."
                    ),
                )
            )

    return {
        "passed": len(violations) == 0,
        "final_balances": {f"{k[0]}::{k[1]}": v for k, v in balances.items()},
        "ledger_history": history,
        "violations": [asdict(v) for v in violations],
    }


def audit_vault_resources(vault_root: Path) -> dict[str, Any]:
    """Automatically scan `Characters/`, `Magic-Technology/`, `Artifacts/`, and chapter `state_delta` blocks."""
    index = VaultIndex(vault_root)
    nodes = index.scan_vault()

    pools: list[ResourcePoolSpec] = []
    deltas: list[ChapterResourceDelta] = []

    for idx_num, node in enumerate(nodes, start=1):
        fm = node.frontmatter
        rel = node.relative_path
        entity = str(fm.get("entity") or fm.get("pov") or node.directives.get("pov") or Path(rel).stem)

        if isinstance(fm.get("resource_pools"), dict):
            for res_name, init_val in fm["resource_pools"].items():
                if isinstance(init_val, (int, float)):
                    pools.append(
                        ResourcePoolSpec(
                            entity_name=entity,
                            resource_name=str(res_name),
                            initial_value=float(init_val),
                        )
                    )

        if isinstance(fm.get("state_delta"), dict):
            chap_idx = int(fm.get("chapter", idx_num))
            chap_title = str(fm.get("title") or Path(rel).stem)
            for res_name, delta_val in fm["state_delta"].items():
                if isinstance(delta_val, (int, float)):
                    deltas.append(
                        ChapterResourceDelta(
                            chapter_index=chap_idx,
                            chapter_title=chap_title,
                            entity_name=entity,
                            resource_name=str(res_name),
                            delta=float(delta_val),
                        )
                    )

    return audit_resource_conservation(pools=pools, deltas=deltas)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum ledger-audit` / `arcanum resource-ledger`."""
    parser = argparse.ArgumentParser(
        prog="arcanum ledger-audit",
        description="Audit hard-magic and sci-fi resource conservation across manuscript chapters.",
    )
    parser.add_argument("vault", nargs="?", type=Path, default=Path.cwd(), help="Vault or manuscript directory")
    args = parser.parse_args(argv)

    result = audit_vault_resources(args.vault)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
