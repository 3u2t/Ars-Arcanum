"""Hard Magic & Sci-Fi Resource Conservation Ledger (src/arcanum/worldbible/ledger.py).

Audits state transitions across manuscript chapters against rules defined in
`Magic-Technology/` and `Artifacts/`:
- Tracks finite character/ship pools (e.g., `ether_vials`, `mana`, `ammunition`, `water_liters`,
  `delta_v_mps`, `corruption_index`) across chronological chapter `state_delta` blocks.
- Flags deterministic continuity errors (`LED-501` deficit & `LED-502` capacity overflow).
- Supports cross-vault series federation (`world_root`).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any



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


def audit_vault_resources(
    vault_root: Path,
    world_root: Path | None = None,
) -> dict[str, Any]:
    """Automatically scan `Characters/`, `Magic-Technology/`, `Artifacts/`, and chapter `state_delta` blocks."""
    try:
        from scripts.lib.vault_index import VaultIndex
    except ImportError:
        from lib.vault_index import VaultIndex  # type: ignore[no-redef]

    index = VaultIndex(vault_root)
    nodes = list(index.scan_vault())

    world_nodes: list[Any] = []
    if world_root is not None and Path(world_root).is_dir():
        world_nodes = list(VaultIndex(Path(world_root)).scan_vault())

    pools: list[ResourcePoolSpec] = []
    deltas: list[ChapterResourceDelta] = []

    for node in nodes + world_nodes:
        fm = node.frontmatter
        rel = node.relative_path
        entity = str(fm.get("entity") or fm.get("pov") or node.directives.get("pov") or Path(rel).stem)

        if isinstance(fm.get("resource_pools"), dict):
            for key, val in fm["resource_pools"].items():
                if isinstance(val, (int, float)):
                    pools.append(
                        ResourcePoolSpec(
                            entity_name=entity,
                            resource_name=str(key),
                            initial_value=float(val),
                        )
                    )
                elif isinstance(val, dict):
                    for sub_res, sub_val in val.items():
                        if isinstance(sub_val, (int, float)):
                            pools.append(
                                ResourcePoolSpec(
                                    entity_name=str(key),
                                    resource_name=str(sub_res),
                                    initial_value=float(sub_val),
                                )
                            )

    for idx_num, node in enumerate(nodes, start=1):
        fm = node.frontmatter
        rel = node.relative_path
        entity = str(fm.get("entity") or fm.get("pov") or node.directives.get("pov") or Path(rel).stem)

        if isinstance(fm.get("state_delta"), dict):
            chap_idx = int(fm.get("chapter", idx_num))
            chap_title = str(fm.get("title") or Path(rel).stem)
            for key, delta_val in fm["state_delta"].items():
                if isinstance(delta_val, (int, float)):
                    deltas.append(
                        ChapterResourceDelta(
                            chapter_index=chap_idx,
                            chapter_title=chap_title,
                            entity_name=entity,
                            resource_name=str(key),
                            delta=float(delta_val),
                        )
                    )
                elif isinstance(delta_val, dict):
                    for sub_res, sub_delta in delta_val.items():
                        if isinstance(sub_delta, (int, float)):
                            deltas.append(
                                ChapterResourceDelta(
                                    chapter_index=chap_idx,
                                    chapter_title=chap_title,
                                    entity_name=str(key),
                                    resource_name=str(sub_res),
                                    delta=float(sub_delta),
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


__all__ = [
    "ChapterResourceDelta",
    "LedgerViolation",
    "ResourcePoolSpec",
    "audit_resource_conservation",
    "audit_vault_resources",
    "main",
]
