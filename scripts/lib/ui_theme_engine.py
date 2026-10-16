#!/usr/bin/env python3
"""
Ars Arcanum UI Visual Presets & Procedural Typewriter Sound Engine (scripts/lib/ui_theme_engine.py)
=================================================================================================
Legacy compatibility facade delegating to src.arcanum.ui.theme.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.arcanum.ui.theme import (  # noqa: E402
    SOUND_PRESETS,
    VISUAL_PRESETS,
    get_theme_control_center_html,
    get_theme_engine_css,
    get_theme_engine_js,
)

__all__ = [
    "SOUND_PRESETS",
    "VISUAL_PRESETS",
    "get_theme_control_center_html",
    "get_theme_engine_css",
    "get_theme_engine_js",
]
