"""Hard Magic & Sci-Fi Resource Conservation Ledger (`arcanum ledger audit`).

Audits state transitions across manuscript chapters against rules defined in
`Magic-Technology/` and `Artifacts/`:
- Tracks finite character/ship pools (e.g., `ether_vials`, `mana`, `ammunition`, `water_liters`,
  `delta_v_mps`, `corruption_index`) across chronological chapter `state_delta` blocks.
- Flags deterministic continuity errors (`LED-501` & `LED-502`):
  * `LED-501` (Resource Depletion Deficit): A character or vessel expends more of a finite resource
    than remains in their inventory/pool (balance drops below `min_bound`, default `0.0`).
  * `LED-502` (Capacity / Corruption Cap Breach): A resource or corruption meter exceeds its
    maximum physiological or structural cap (`max_bound`) without triggering the declared
    consequence state.

Repository Target: `scripts/lib/resource_ledger.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
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

    rule_id: str  # "LED-501" | "LED-502"
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


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum ledger-audit`."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        prog="arcanum ledger-audit",
        description="Audit magic spell slots, ammunition, and resource conservation bounds.",
    )
    parser.add_argument("--entity", default="Protagonist", help="Character or faction name")
    parser.add_argument("--resource", default="mana", help="Resource identifier")
    parser.add_argument("--initial", type=float, default=100.0, help="Initial resource balance (default: 100)")
    parser.add_argument("--min", type=float, default=0.0, help="Minimum balance bound (default: 0)")
    parser.add_argument("--max", type=float, default=100.0, help="Maximum capacity bound (default: 100)")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args(argv)

    pools = [
        ResourcePoolSpec(
            entity_name=args.entity,
            resource_name=args.resource,
            initial_value=args.initial,
            min_bound=args.min,
            max_bound=args.max,
        )
    ]
    deltas = [
        ChapterResourceDelta(1, "Sample Scene", args.entity, args.resource, 0.0, "Baseline check")
    ]
    res = audit_resource_conservation(pools=pools, deltas=deltas)
    if args.json:
        sys.stdout.write(json.dumps(res, indent=2) + "\n")
    else:
        sys.stdout.write(f"Ars Arcanum Resource Conservation Ledger — {args.entity}::{args.resource}\n")
        sys.stdout.write("-" * 65 + "\n")
        status = "PASSED" if res["passed"] else "VIOLATIONS FOUND"
        sys.stdout.write(f"Status: {status}\n")
        for k, bal in res["final_balances"].items():
            sys.stdout.write(f"  • {k}: {bal}\n")
        for v in res["violations"]:
            sys.stdout.write(f"  [{v['rule_id']}] {v['message']}\n")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
