"""Epistemic POV & Spoiler Firewall Engine for Ars Arcanum (`arcanum validate-epistemic`).

Models Epistemic Asymmetry across a multi-POV manuscript and its linked World Bible:
- Tracks what each character knows at baseline (`Characters/<Name>.md` frontmatter `knows: [...]`).
- Tracks chapter-ordered scene transitions (`chapter`, `pov`, `learns: [...]`, `references: [...]`,
  and wikilinks `[[Entity]]` mapped to secret lore IDs).
- Flags deterministic epistemic violations (`EPI-201` through `EPI-203`).
- Supports cross-vault series federation (`world_root`).

Repository Target: `scripts/lib/epistemic_firewall.py`
Delegated natively to: `src.arcanum.worldbible.epistemics`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("epistemic_firewall", "lib.epistemic_firewall", "scripts.lib.epistemic_firewall"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.epistemics import (  # noqa: E402
    ChapterEpistemicEvent,
    CharacterKnowledgeBaseline,
    EpistemicAuditReport,
    EpistemicViolation,
    audit_epistemic_continuity,
    audit_vault_epistemic,
    main,
)

__all__ = [
    "ChapterEpistemicEvent",
    "CharacterKnowledgeBaseline",
    "EpistemicAuditReport",
    "EpistemicViolation",
    "audit_epistemic_continuity",
    "audit_vault_epistemic",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
