#!/usr/bin/env python3
"""Ars Arcanum Configuration Storage Engine (`scripts/lib/config_store.py`).

Manages low-level configuration file resolution and atomic disk I/O in standard
XDG directories (~/.config/ars-arcanum/config.json).
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
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    LEGACY_CONFIG_DIR_NAME,
    clear_backup_dest,
    get_backup_dest,
    get_backup_destination,
    get_config_dir,
    get_config_file_path,
    get_config_path,
    get_tips_enabled,
    load_config,
    save_config,
    set_backup_dest,
    set_tips_enabled,
    toggle_tips,
)

__all__ = [
    "CONFIG_DIR_NAME",
    "CONFIG_FILE_NAME",
    "LEGACY_CONFIG_DIR_NAME",
    "clear_backup_dest",
    "get_backup_dest",
    "get_backup_destination",
    "get_config_dir",
    "get_config_file_path",
    "get_config_path",
    "get_tips_enabled",
    "load_config",
    "save_config",
    "set_backup_dest",
    "set_tips_enabled",
    "toggle_tips",
]
