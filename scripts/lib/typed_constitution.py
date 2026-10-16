"""Strict Typed Authorial Constitution & 3-Tier Policy Cascade (Phase 2B Refactor).

Upgrades `scripts/lib/constitution.py` by replacing untyped `dict[str, Any]` payloads with
frozen `@dataclass` schemas and adding explicit `!rule_id` negation support so child
constitutions (World or Manuscript level) can disable inherited diagnostic rules.

Repository Target: `scripts/lib/typed_constitution.py`
Delegated natively to: `src.arcanum.worldbible.constitution`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("typed_constitution", "lib.typed_constitution", "scripts.lib.typed_constitution"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.constitution import (  # noqa: E402
    AuthorialConstitution,
    CraftPolicyThresholds,
    load_yaml_constitution_file,
    main,
    merge_rule_lists_with_negation,
    resolve_constitution_cascade,
)

__all__ = [
    "AuthorialConstitution",
    "CraftPolicyThresholds",
    "load_yaml_constitution_file",
    "main",
    "merge_rule_lists_with_negation",
    "resolve_constitution_cascade",
]

if __name__ == "__main__":
    raise SystemExit(main())
