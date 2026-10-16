"""Interactive Pacing, POV Balance & Subplot Braid Matrix (`arcanum braid`).

Analyzes `@pov:`, `@subplot:`, and `@tension:` directives across a multi-POV manuscript:
1. Calculates POV word-share percentages and dialogue-to-narration pacing curves.
2. Detects POV & Subplot Droughts (`BRD-601`).
3. Renders a self-contained, air-gapped HTML + SVG swimlane braid visualization with strict
   Content-Security-Policy (`default-src 'none'; style-src 'unsafe-inline'`).

Repository Target: `scripts/lib/narrative_braid.py`
Delegates implementation to `src.arcanum.manuscript.braid`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is available for imports
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("narrative_braid", "lib.narrative_braid", "scripts.lib.narrative_braid"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.manuscript.braid import (  # noqa: E402
    BraidDroughtAlert,
    ChapterBraidNode,
    analyze_narrative_braid,
    main,
    render_braid_html,
    scan_manuscript_braid,
)

__all__ = [
    "BraidDroughtAlert",
    "ChapterBraidNode",
    "analyze_narrative_braid",
    "main",
    "render_braid_html",
    "scan_manuscript_braid",
]

if __name__ == "__main__":
    raise SystemExit(main())
