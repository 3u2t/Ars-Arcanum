#!/usr/bin/env python3
"""
Ars Arcanum Portfolio Dashboard & Author Velocity Analytics
(scripts/lib/portfolio.py)
================================================================================
Zero-dependency, offline author portfolio dashboard and catalog analytics engine.

Delegated natively to: src.arcanum.manuscript.portfolio
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("portfolio", "lib.portfolio", "scripts.lib.portfolio"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.manuscript.portfolio import (  # noqa: E402
    LORE_CATEGORIES,
    analyze_manuscript_project,
    analyze_universe_project,
    calculate_portfolio_velocity,
    format_portfolio_terminal,
    generate_portfolio_html,
    main,
    scan_portfolio,
)

__all__ = [
    "LORE_CATEGORIES",
    "analyze_manuscript_project",
    "analyze_universe_project",
    "calculate_portfolio_velocity",
    "format_portfolio_terminal",
    "generate_portfolio_html",
    "main",
    "scan_portfolio",
]

if __name__ == "__main__":
    main()
