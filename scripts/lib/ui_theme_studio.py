#!/usr/bin/env python3
"""
Ars Arcanum UI Theme & Procedural Sound Studio (scripts/lib/ui_theme_studio.py)
=============================================================================
Legacy compatibility facade delegating to src.arcanum.ui.studio.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.arcanum.ui.studio import main, render_theme_studio_html  # noqa: E402

__all__ = [
    "main",
    "render_theme_studio_html",
]

if __name__ == "__main__":
    sys.exit(main())
