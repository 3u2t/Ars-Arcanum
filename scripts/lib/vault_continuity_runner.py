"""Unified Vault Continuity Runner & Live Obsidian Diagnostics Bridge (`arcanum continuity-suite`).

Executes all 6 deterministic Ars Arcanum continuity and velocity engines in a single pass over
a Sovereign Vault (`VaultIndex`) and optionally writes a live Obsidian Callout Dashboard
(`_Arcanum_Diagnostics.md`) directly into the vault root so authors see real-time continuity
alerts (`EPI-201`, `TIME-301`, `CON-401`, `LED-501`, `BRD-601`) and daily Phase-Aware Effort
metrics inside their Obsidian sidebar without leaving their prose editor.

Repository Target: `scripts/lib/vault_continuity_runner.py`
Delegated natively to: `src.arcanum.worldbible.runner`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("vault_continuity_runner", "lib.vault_continuity_runner", "scripts.lib.vault_continuity_runner"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.worldbible.runner import (  # noqa: E402
    main,
    render_obsidian_diagnostics_markdown,
    run_full_vault_continuity_suite,
)

__all__ = [
    "main",
    "render_obsidian_diagnostics_markdown",
    "run_full_vault_continuity_suite",
]

if __name__ == "__main__":
    raise SystemExit(main())
