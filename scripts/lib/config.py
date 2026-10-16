#!/usr/bin/env python3
"""Ars Arcanum Configuration Engine Facade (`scripts/lib/config.py`).

Provides high-level programmatic API and CLI commands for managing:
- User preferences & XDG persistence
- Standard DOCX formatting presets & typography
- Active workspace targets & flow state
- Authorial Constitution & governance policies

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
    DEFAULT_AUTHORIAL_POLICY,
    DOCX_PRESETS,
    LEGACY_CONFIG_DIR_NAME,
    PRESET_ALIASES,
    _deep_merge_dict,
    clear_active_manuscript,
    clear_active_universe,
    clear_active_world,
    clear_backup_dest,
    deep_merge_constitution,
    get_active_docx_preset_name,
    get_active_manuscript,
    get_active_manuscript_name,
    get_active_universe,
    get_active_universe_name,
    get_active_world,
    get_active_world_name,
    get_authorial_constitution,
    get_authorial_policy,
    get_backup_dest,
    get_backup_destination,
    get_config_dir,
    get_config_file_path,
    get_config_path,
    get_crt_fx_enabled,
    get_daily_flow_state,
    get_default_scope,
    get_disabled_engines,
    get_docx_config,
    get_docx_preset_names,
    get_suppressed_rules,
    get_tips_enabled,
    get_typewriter_sound_preset,
    get_ui_visual_preset,
    get_world_axioms,
    is_engine_enabled,
    is_rule_suppressed,
    list_docx_presets,
    load_authorial_constitution,
    load_config,
    main,
    save_config,
    set_active_manuscript,
    set_active_universe,
    set_active_world,
    set_authorial_policy,
    set_backup_dest,
    set_crt_fx_enabled,
    set_daily_flow_state,
    set_default_scope,
    set_docx_option,
    set_docx_preset,
    set_engine_enabled,
    set_tips_enabled,
    set_typewriter_sound_preset,
    set_ui_visual_preset,
    set_world_axioms,
    toggle_tips,
)

__all__ = [
    "CONFIG_DIR_NAME",
    "CONFIG_FILE_NAME",
    "DEFAULT_AUTHORIAL_POLICY",
    "DOCX_PRESETS",
    "LEGACY_CONFIG_DIR_NAME",
    "PRESET_ALIASES",
    "_deep_merge_dict",
    "clear_active_manuscript",
    "clear_active_universe",
    "clear_active_world",
    "clear_backup_dest",
    "deep_merge_constitution",
    "get_active_docx_preset_name",
    "get_active_manuscript",
    "get_active_manuscript_name",
    "get_active_universe",
    "get_active_universe_name",
    "get_active_world",
    "get_active_world_name",
    "get_authorial_constitution",
    "get_authorial_policy",
    "get_backup_dest",
    "get_backup_destination",
    "get_config_dir",
    "get_config_file_path",
    "get_config_path",
    "get_crt_fx_enabled",
    "get_daily_flow_state",
    "get_default_scope",
    "get_disabled_engines",
    "get_docx_config",
    "get_docx_preset_names",
    "get_suppressed_rules",
    "get_tips_enabled",
    "get_typewriter_sound_preset",
    "get_ui_visual_preset",
    "get_world_axioms",
    "is_engine_enabled",
    "is_rule_suppressed",
    "list_docx_presets",
    "load_authorial_constitution",
    "load_config",
    "main",
    "save_config",
    "set_active_manuscript",
    "set_active_universe",
    "set_active_world",
    "set_authorial_policy",
    "set_backup_dest",
    "set_crt_fx_enabled",
    "set_daily_flow_state",
    "set_default_scope",
    "set_docx_option",
    "set_docx_preset",
    "set_engine_enabled",
    "set_tips_enabled",
    "set_typewriter_sound_preset",
    "set_ui_visual_preset",
    "set_world_axioms",
    "toggle_tips",
]

if __name__ == "__main__":
    sys.exit(main())
