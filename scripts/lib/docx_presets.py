#!/usr/bin/env python3
"""Ars Arcanum DOCX Presets & Typography Configuration Engine (`scripts/lib/docx_presets.py`).

Defines standard manuscript typography presets and custom overrides for .docx export.
Delegates to native `src.arcanum.core.config` while maintaining backward compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path if not present
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.arcanum.core.config import (  # noqa: E402
    DOCX_PRESETS,
    PRESET_ALIASES,
    _normalize_preset_name,
    get_active_docx_preset_name,
    get_docx_config,
    get_docx_preset_names,
    list_docx_presets,
    set_docx_option,
    set_docx_preset,
)

__all__ = [
    "DOCX_PRESETS",
    "PRESET_ALIASES",
    "_normalize_preset_name",
    "get_active_docx_preset_name",
    "get_docx_config",
    "get_docx_preset_names",
    "list_docx_presets",
    "set_docx_option",
    "set_docx_preset",
]
