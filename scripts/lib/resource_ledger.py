"""Hard Magic & Sci-Fi Resource Conservation Ledger (`arcanum ledger-audit`).

Audits state transitions across manuscript chapters against rules defined in
`Magic-Technology/` and `Artifacts/`:
- Tracks finite character/ship pools (e.g., `ether_vials`, `mana`, `ammunition`, `water_liters`,
  `delta_v_mps`, `corruption_index`) across chronological chapter `state_delta` blocks.
- Flags deterministic continuity errors (`LED-501` & `LED-502`).

Repository Target: `scripts/lib/resource_ledger.py`
Delegated natively to: `src.arcanum.worldbible.ledger`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("resource_ledger", "lib.resource_ledger", "scripts.lib.resource_ledger"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.ledger import (  # noqa: E402
    ChapterResourceDelta,
    LedgerViolation,
    ResourcePoolSpec,
    audit_resource_conservation,
    audit_vault_resources,
    main,
)

__all__ = [
    "ChapterResourceDelta",
    "LedgerViolation",
    "ResourcePoolSpec",
    "audit_resource_conservation",
    "audit_vault_resources",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
