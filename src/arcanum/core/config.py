"""Ars Arcanum Configuration, Workspace State, and Authorial Governance Engine (`src/arcanum/core/config.py`).

Provides:
- XDG-compliant persistent configuration store (`~/.config/ars-arcanum/config.json`)
- Atomic file writes with Windows backoff and 0o600 permissions
- DOCX manuscript typography and formatting presets (CMOS, Shunn, Modern, Classic)
- Workspace target resolution (active manuscript, world, universe, default scope)
- Daily flow state and cursor tracking
- Authorial Constitution policies, rule suppression, and engine switchboard
- Full CLI command dispatch for configuration management
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from src.arcanum.core.storage import atomic_write

logger = logging.getLogger("arcanum.config")

CONFIG_DIR_NAME = "ars-arcanum"
LEGACY_CONFIG_DIR_NAME = "arcanum"
CONFIG_FILE_NAME = "config.json"


# ==============================================================================
# 1. Low-Level XDG Configuration Storage
# ==============================================================================


def get_config_dir() -> Path:
    """Returns the XDG configuration directory for Ars Arcanum."""
    custom = os.environ.get("ARCANUM_CONFIG_DIR")
    if custom:
        return Path(custom).resolve()
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    return base / CONFIG_DIR_NAME


def get_config_file_path() -> Path:
    """Returns the primary configuration file path, checking legacy fallback if needed."""
    primary_dir = get_config_dir()
    primary_file = primary_dir / CONFIG_FILE_NAME
    if primary_file.is_file():
        return primary_file

    # Check legacy fallback (~/.config/arcanum/config.json)
    legacy_dir = primary_dir.parent / LEGACY_CONFIG_DIR_NAME
    legacy_file = legacy_dir / CONFIG_FILE_NAME
    if legacy_file.is_file():
        return legacy_file

    return primary_file


get_config_path = get_config_file_path


def load_config() -> dict[str, Any]:
    """Loads configuration dictionary from disk."""
    config_path = get_config_file_path()
    if not config_path.is_file():
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception as e:
        logger.warning("Failed to parse configuration file at %s: %s", config_path, e)
    return {}


def save_config(config_data: dict[str, Any]) -> bool:
    """Saves configuration dictionary to disk with restrictive 0o600 permissions."""
    config_path = get_config_file_path()
    try:
        data_str = json.dumps(config_data, indent=2, ensure_ascii=False) + "\n"
        atomic_write(config_path, data_str)
        try:
            os.chmod(config_path, 0o600)
        except OSError:
            pass
        return True
    except Exception as e:
        logger.error("Failed to write configuration file at %s: %s", config_path, e)
        return False


def get_backup_dest() -> str:
    """Returns configured external secure backup destination path or empty string."""
    cfg = load_config()
    dest = cfg.get("secure_backup_destination") or cfg.get("backup_destination") or ""
    return str(dest).strip()


get_backup_destination = get_backup_dest


def set_backup_dest(dest_path: str) -> bool:
    """Sets and persists the secure external backup destination."""
    cfg = load_config()
    clean_path = str(Path(dest_path).expanduser().resolve())
    cfg["secure_backup_destination"] = clean_path
    return save_config(cfg)


def clear_backup_dest() -> bool:
    """Clears the configured secure external backup destination."""
    cfg = load_config()
    cfg.pop("secure_backup_destination", None)
    cfg.pop("backup_destination", None)
    return save_config(cfg)


def get_tips_enabled() -> bool:
    """Returns True if dynamic contextual tips are enabled (default: True)."""
    cfg = load_config()
    return bool(cfg.get("tips_enabled", True))


def set_tips_enabled(enabled: bool) -> bool:
    """Sets and persists dynamic tips enabled state."""
    cfg = load_config()
    cfg["tips_enabled"] = bool(enabled)
    return save_config(cfg)


def toggle_tips() -> bool:
    """Toggles dynamic tips enabled state and returns new value."""
    current = get_tips_enabled()
    set_tips_enabled(not current)
    return not current


# ==============================================================================
# 2. DOCX Presets & Manuscript Typography
# ==============================================================================

DOCX_PRESETS: dict[str, dict[str, Any]] = {
    "chicago-manual": {
        "name": "Chicago Manual of Style (CMOS)",
        "description": "Chicago Manual of Style (17th/18th ed.) author manuscript guidelines. Times New Roman 12pt, double-spaced, 1-inch margins, 0.5-inch indent, '#' scene breaks, running header (Surname / Short Title / Page #).",
        "font_family": "Times New Roman",
        "font_size_pt": 12.0,
        "line_spacing": 2.0,
        "margin_inches": 1.0,
        "first_line_indent_inches": 0.5,
        "scene_break_symbol": "#",
        "page_break_chapters": True,
        "include_header_slug": True,
    },
    "standard-submission": {
        "name": "Standard Submission (Shunn / Industry)",
        "description": "William Shunn standard manuscript format. Times New Roman 12pt, double-spaced, 1-inch margins, 0.5-inch indent, '#' scene breaks.",
        "font_family": "Times New Roman",
        "font_size_pt": 12.0,
        "line_spacing": 2.0,
        "margin_inches": 1.0,
        "first_line_indent_inches": 0.5,
        "scene_break_symbol": "#",
        "page_break_chapters": True,
        "include_header_slug": True,
    },
    "modern-manuscript": {
        "name": "Modern Manuscript",
        "description": "Clean modern editorial layout. Georgia 11.5pt, 1.35 line spacing, 1-inch margins, 0.35-inch indent, '* * *' scene breaks.",
        "font_family": "Georgia",
        "font_size_pt": 11.5,
        "line_spacing": 1.35,
        "margin_inches": 1.0,
        "first_line_indent_inches": 0.35,
        "scene_break_symbol": "* * *",
        "page_break_chapters": True,
        "include_header_slug": True,
    },
    "classic-trade": {
        "name": "Classic Literary & Trade",
        "description": "Classic book proportions. EB Garamond 12pt, 1.5 line spacing, 1-inch margins, 0.5-inch indent.",
        "font_family": "EB Garamond",
        "font_size_pt": 12.0,
        "line_spacing": 1.5,
        "margin_inches": 1.0,
        "first_line_indent_inches": 0.5,
        "scene_break_symbol": "* * *",
        "page_break_chapters": True,
        "include_header_slug": False,
    },
    "custom": {
        "name": "Custom User Formatting",
        "description": "User-customized manuscript typography and spacing.",
        "font_family": "Times New Roman",
        "font_size_pt": 12.0,
        "line_spacing": 2.0,
        "margin_inches": 1.0,
        "first_line_indent_inches": 0.5,
        "scene_break_symbol": "#",
        "page_break_chapters": True,
        "include_header_slug": True,
    },
}

PRESET_ALIASES: dict[str, str] = {
    "cmos": "chicago-manual",
    "chicago": "chicago-manual",
    "shunn": "standard-submission",
    "industry": "standard-submission",
    "modern": "modern-manuscript",
    "trade": "classic-trade",
    "classic": "classic-trade",
}


def _normalize_preset_name(preset_name: str) -> str:
    norm = preset_name.strip().lower().replace("_", "-")
    return PRESET_ALIASES.get(norm, norm)


def get_active_docx_preset_name() -> str:
    """Returns the name of the currently active DOCX preset."""
    cfg = load_config()
    docx_cfg = cfg.get("docx_formatting", {})
    preset = _normalize_preset_name(docx_cfg.get("active_preset", "standard-submission"))
    if preset not in DOCX_PRESETS:
        preset = "standard-submission"
    return preset


def get_docx_preset_names() -> list[str]:
    """Returns list of canonical DOCX preset names."""
    return list(DOCX_PRESETS.keys())


def list_docx_presets() -> dict[str, Any]:
    """Returns a copy of all registered DOCX presets."""
    return copy.deepcopy(DOCX_PRESETS)


def set_docx_preset(preset_name: str) -> bool:
    """Sets active DOCX formatting preset."""
    norm = _normalize_preset_name(preset_name)
    if norm not in DOCX_PRESETS:
        logger.error("Unknown DOCX preset: %s", preset_name)
        return False
    cfg = load_config()
    if "docx_formatting" not in cfg or not isinstance(cfg["docx_formatting"], dict):
        cfg["docx_formatting"] = {}
    cfg["docx_formatting"]["active_preset"] = norm
    return save_config(cfg)


def get_docx_config(preset_name: str | None = None) -> dict[str, Any]:
    """Returns merged active DOCX formatting configuration."""
    if preset_name:
        norm_name = _normalize_preset_name(preset_name)
        if norm_name in DOCX_PRESETS:
            return dict(DOCX_PRESETS[norm_name])

    cfg = load_config()
    docx_cfg = cfg.get("docx_formatting", {})
    active = _normalize_preset_name(docx_cfg.get("active_preset", "standard-submission"))
    base = dict(DOCX_PRESETS.get(active, DOCX_PRESETS["standard-submission"]))
    base["active_preset"] = active
    if "custom_overrides" in docx_cfg and isinstance(docx_cfg["custom_overrides"], dict):
        base.update(docx_cfg["custom_overrides"])
    return base


def set_docx_option(key: str, value: Any) -> bool:
    """Sets a custom override option for DOCX export and switches to custom preset."""
    cfg = load_config()
    if "docx_formatting" not in cfg or not isinstance(cfg["docx_formatting"], dict):
        cfg["docx_formatting"] = {}
    if "custom_overrides" not in cfg["docx_formatting"] or not isinstance(cfg["docx_formatting"]["custom_overrides"], dict):
        cfg["docx_formatting"]["custom_overrides"] = {}
    cfg["docx_formatting"]["custom_overrides"][key] = value
    cfg["docx_formatting"]["active_preset"] = "custom"
    return save_config(cfg)


# ==============================================================================
# 3. Workspace Targets & Author Daily Flow State
# ==============================================================================


def get_active_manuscript_name() -> str:
    """Returns configured active manuscript name/path or empty string."""
    cfg = load_config()
    return str(cfg.get("active_manuscript") or "").strip()


def set_active_manuscript(name: str) -> bool:
    """Sets and persists the active manuscript name or path."""
    cfg = load_config()
    cfg["active_manuscript"] = str(name).strip()
    return save_config(cfg)


def clear_active_manuscript() -> bool:
    """Clears the active manuscript preference."""
    cfg = load_config()
    cfg.pop("active_manuscript", None)
    return save_config(cfg)


def get_active_world_name() -> str:
    """Returns configured active world name/path or empty string."""
    cfg = load_config()
    return str(cfg.get("active_world") or "").strip()


def set_active_world(name: str) -> bool:
    """Sets and persists the active world name or path."""
    cfg = load_config()
    cfg["active_world"] = str(name).strip()
    return save_config(cfg)


def clear_active_world() -> bool:
    """Clears the active world preference."""
    cfg = load_config()
    cfg.pop("active_world", None)
    return save_config(cfg)


def get_active_universe_name() -> str:
    """Returns configured active universe name/path or empty string."""
    cfg = load_config()
    return str(cfg.get("active_universe") or "").strip()


def set_active_universe(name: str) -> bool:
    """Sets and persists the active universe name or path."""
    cfg = load_config()
    cfg["active_universe"] = str(name).strip()
    return save_config(cfg)


def clear_active_universe() -> bool:
    """Clears the active universe preference."""
    cfg = load_config()
    cfg.pop("active_universe", None)
    return save_config(cfg)


get_active_manuscript = get_active_manuscript_name
get_active_world = get_active_world_name
get_active_universe = get_active_universe_name


def get_default_scope() -> dict[str, Any]:
    """Returns default scope settings dictionary."""
    cfg = load_config()
    scope = cfg.get("default_scope", {})
    return scope if isinstance(scope, dict) else {}


def set_default_scope(scope_data: dict[str, Any]) -> bool:
    """Sets and persists default scope dictionary."""
    cfg = load_config()
    cfg["default_scope"] = scope_data
    return save_config(cfg)


def get_daily_flow_state() -> dict[str, Any]:
    """Returns the daily flow ritual and cursor state dictionary."""
    cfg = load_config()
    flow = cfg.get("daily_flow_state", {})
    if not isinstance(flow, dict):
        flow = {}
    return {
        "last_active_manuscript": flow.get("last_active_manuscript", ""),
        "last_active_file": flow.get("last_active_file", ""),
        "last_cursor_line": int(flow.get("last_cursor_line", 1)),
        "next_time_bridge": flow.get("next_time_bridge", ""),
        "active_workspace_phase": flow.get("active_workspace_phase", "drafting"),
        "fast_idea_scraps": list(flow.get("fast_idea_scraps", [])),
    }


def set_daily_flow_state(state_data: dict[str, Any]) -> bool:
    """Sets and persists the daily flow ritual state."""
    cfg = load_config()
    current = get_daily_flow_state()
    current.update(state_data)
    cfg["daily_flow_state"] = current
    return save_config(cfg)


# ==============================================================================
# 4. Visual Themes & Procedural Sensory Settings
# ==============================================================================


def get_ui_visual_preset() -> str:
    """Returns active UI visual preset name (default: sovereign-dark)."""
    cfg = load_config()
    return str(cfg.get("ui_visual_preset") or "sovereign-dark").strip()


def set_ui_visual_preset(preset: str) -> bool:
    """Sets and persists the active UI visual preset."""
    cfg = load_config()
    cfg["ui_visual_preset"] = preset.strip().lower()
    return save_config(cfg)


def get_typewriter_sound_preset() -> str:
    """Returns active typewriter procedural audio preset model (default: remington_1890)."""
    cfg = load_config()
    return str(cfg.get("typewriter_sound_preset") or "remington_1890").strip()


def set_typewriter_sound_preset(preset: str) -> bool:
    """Sets and persists the active typewriter procedural audio model."""
    cfg = load_config()
    cfg["typewriter_sound_preset"] = preset.strip().lower()
    return save_config(cfg)


def get_crt_fx_enabled() -> bool:
    """Returns whether CRT scanline mode is globally enabled."""
    cfg = load_config()
    return bool(cfg.get("crt_fx_enabled", False))


def set_crt_fx_enabled(enabled: bool) -> bool:
    """Sets and persists the CRT scanline effect preference."""
    cfg = load_config()
    cfg["crt_fx_enabled"] = bool(enabled)
    return save_config(cfg)


# ==============================================================================
# 5. Authorial Constitution & Diagnostic Governance
# ==============================================================================

DEFAULT_AUTHORIAL_POLICY: dict[str, Any] = {
    "default_mode": "observational",
    "dry_run_default": True,
    "suggestion_mode_only": True,
    "framework_free_default": False,
    "whitelisted_terms": [],
    "disabled_engines": [],
    "active_tradition": "unconstrained",
    "canon": {
        "authority": "author",
        "narrator_reliability": "reliable",
        "allow_unresolved_mysteries": True,
    },
    "style": {
        "passive_voice": "observe",
        "repetition": "observe",
        "filter_verbs": "observe",
    },
    "structure": {
        "framework": "none",
        "score_enabled": False,
        "mode": "descriptive",
    },
    "magic": {
        "modality": "unconstrained",
        "enforce_thermodynamics": False,
        "causal_accountability": "optional",
    },
    "continuity": {
        "timeline": "flexible",
        "preserve_poetic_variation": True,
        "allow_figurative_language": True,
    },
    "naming": {
        "collision_heuristics": "advisory",
        "whitelisted_pairs": [],
    },
    "diagnostics": {
        "default_severity": "advisory",
        "suppressed_rules": [],
    },
    "ui_visual_preset": "sovereign-dark",
    "typewriter_sound_preset": "remington_1890",
    "crt_fx_enabled": False,
}


def _deep_merge_dict(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Recursively merges source dict into target dict in-place, extending lists without duplicates."""
    for k, v in source.items():
        if isinstance(v, dict) and isinstance(target.get(k), dict):
            _deep_merge_dict(target[k], v)
        elif isinstance(v, list) and isinstance(target.get(k), list):
            for item in v:
                if item not in target[k]:
                    target[k].append(copy.deepcopy(item) if isinstance(item, (dict, list)) else item)
        elif isinstance(v, (dict, list)):
            target[k] = copy.deepcopy(v)
        else:
            target[k] = v


def get_authorial_policy() -> dict[str, Any]:
    """Returns configured authorial policy settings dictionary."""
    cfg = load_config()
    pol = cfg.get("authorial_policy", {})
    res = copy.deepcopy(DEFAULT_AUTHORIAL_POLICY)
    if isinstance(pol, dict):
        _deep_merge_dict(res, pol)
    return res


def set_authorial_policy(policy_data: dict[str, Any]) -> bool:
    """Sets and persists authorial policy dictionary."""
    cfg = load_config()
    current = get_authorial_policy()
    current.update(policy_data)
    cfg["authorial_policy"] = current
    return save_config(cfg)


def get_authorial_constitution(
    world_path: str | Path | None = None,
    manuscript_path: str | Path | None = None,
) -> dict[str, Any]:
    """Returns the resolved Authorial Constitution merging global policy with local vault/manuscript declarations."""
    base = get_authorial_policy()
    res = copy.deepcopy(base)

    def _try_load_vault_constitution(folder: Path | None) -> None:
        if not folder:
            return
        for cand in [folder / "constitution.json", folder / "constitution.yaml", folder / "world_config.json", folder / "manuscript_config.json"]:
            if cand.is_file():
                try:
                    if cand.suffix == ".json":
                        with open(cand, encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        try:
                            from src.arcanum.core.frontmatter import parse_yaml_document
                            data = parse_yaml_document(cand.read_text(encoding="utf-8"))
                        except Exception:
                            from src.arcanum.core.hardening import parse_frontmatter_hardened
                            raw = cand.read_text(encoding="utf-8")
                            wrapped = raw if raw.lstrip().startswith("---") else f"---\n{raw}\n---\n"
                            data, _ = parse_frontmatter_hardened(wrapped)
                    if isinstance(data, dict):
                        _deep_merge_dict(res, data)
                except Exception as e:
                    logger.debug("Failed reading constitution at %s: %s", cand, e)

    if world_path:
        _try_load_vault_constitution(Path(world_path))
    if manuscript_path:
        _try_load_vault_constitution(Path(manuscript_path))

    return res


def deep_merge_constitution(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Returns a new dictionary with override merged recursively into base."""
    res = copy.deepcopy(base)
    _deep_merge_dict(res, override)
    return res


def load_authorial_constitution(project_dir: Path | str | None = None) -> dict[str, Any]:
    """Loads and resolves the Authorial Constitution for a specific project directory or global policy."""
    if not project_dir:
        return get_authorial_policy()
    return get_authorial_constitution(world_path=project_dir, manuscript_path=project_dir)


def get_suppressed_rules(project_dir: Path | str | None = None) -> list[str]:
    """Returns the list of all suppressed diagnostic rules."""
    c = load_authorial_constitution(project_dir) if project_dir else get_authorial_policy()
    suppressed: set[str] = set()
    diag = c.get("diagnostics", {})
    if isinstance(diag, dict):
        suppressed.update(str(r).upper().strip() for r in diag.get("suppressed_rules", []))
    suppressed.update(str(r).upper().strip() for r in c.get("suppressed_rules", []))
    return sorted(suppressed)


def is_rule_suppressed(rule_id: str, constitution: dict[str, Any] | Path | str | None = None) -> bool:
    """Checks whether a diagnostic rule ID is suppressed by the active Authorial Constitution."""
    if constitution is None:
        c_dict = get_authorial_policy()
    elif isinstance(constitution, (str, Path)):
        c_dict = load_authorial_constitution(constitution)
    else:
        c_dict = constitution

    diag = c_dict.get("diagnostics", {})
    suppressed: set[str] = set()
    if isinstance(diag, dict):
        suppressed.update(str(r).upper().strip() for r in diag.get("suppressed_rules", []))
    suppressed.update(str(r).upper().strip() for r in c_dict.get("suppressed_rules", []))
    return rule_id.upper().strip() in suppressed


def get_world_axioms(world_name: str | None = None) -> dict[str, Any]:
    """Returns world axioms dictionary for world or global default."""
    cfg = load_config()
    axioms = cfg.get("world_axioms", {})
    if not isinstance(axioms, dict):
        axioms = {}
    if world_name and world_name in axioms and isinstance(axioms[world_name], dict):
        return dict(axioms[world_name])
    default_axioms: dict[str, Any] = {
        "magic_modality": "unconstrained",
        "epistemic_truth_default": "cultural_belief",
        "allow_anachronisms": True,
        "shared_universes": [],
        "custom_categories": [],
    }
    fallback = axioms.get("default", default_axioms)
    return dict(fallback) if isinstance(fallback, dict) else default_axioms


def set_world_axioms(world_name: str, axioms_data: dict[str, Any]) -> bool:
    """Sets and persists world axioms for a specific world or default."""
    cfg = load_config()
    if "world_axioms" not in cfg or not isinstance(cfg["world_axioms"], dict):
        cfg["world_axioms"] = {}
    cfg["world_axioms"][world_name] = axioms_data
    return save_config(cfg)


def get_disabled_engines() -> list[str]:
    """Returns list of disabled engine names."""
    pol = get_authorial_policy()
    return list(pol.get("disabled_engines", []))


def is_engine_enabled(engine_name: str) -> bool:
    """Checks if a specific engine is currently enabled."""
    disabled = get_disabled_engines()
    return engine_name.lower().strip() not in [d.lower().strip() for d in disabled]


def set_engine_enabled(engine_name: str, enabled: bool) -> bool:
    """Enables or disables an engine in authorial policy."""
    pol = get_authorial_policy()
    disabled = {d.lower().strip() for d in pol.get("disabled_engines", [])}
    clean_name = engine_name.lower().strip()
    if enabled:
        disabled.discard(clean_name)
    else:
        disabled.add(clean_name)
    pol["disabled_engines"] = sorted(disabled)
    return set_authorial_policy(pol)


# ==============================================================================
# 6. CLI Command Dispatchers
# ==============================================================================


def _handle_backup_dest_cli(args: argparse.Namespace) -> int:
    if args.action == "get":
        dest = get_backup_dest()
        if dest:
            print(dest)
            return 0
        return 1
    if args.action == "set":
        if set_backup_dest(args.path):
            print(f"[CONFIG] Secure backup destination set to: {get_backup_dest()}")
            return 0
        print("[!] Error saving configuration.", file=sys.stderr)
        return 1
    if args.action == "clear":
        if clear_backup_dest():
            print("[CONFIG] Secure backup destination cleared.")
            return 0
        print("[!] Error updating configuration.", file=sys.stderr)
        return 1
    return 0


def _handle_docx_cli(args: argparse.Namespace) -> int:
    if args.subcommand == "docx-preset":
        if args.preset:
            if set_docx_preset(args.preset):
                print(f"[CONFIG] Active DOCX preset set to: {args.preset}")
                return 0
            print(
                f"[!] Error: Invalid preset '{args.preset}'. Available: {', '.join(DOCX_PRESETS.keys())}",
                file=sys.stderr,
            )
            return 1
        print(get_active_docx_preset_name())
        return 0

    if args.subcommand == "docx-presets":
        active = get_active_docx_preset_name()
        print("=== Ars Arcanum DOCX Formatting Presets ===")
        for pid, info in DOCX_PRESETS.items():
            mark = " (active)" if pid == active else ""
            print(f"- {pid}{mark}: {info['name']}")
            print(
                f"    Font: {info['font_family']} {info['font_size_pt']}pt | Spacing: {info['line_spacing']}x | Margins: {info['margin_inches']}\""
            )
            print(f"    Description: {info['description']}")
        return 0

    if args.subcommand == "docx-config":
        if args.key and args.value is not None:
            val: Any = args.value
            try:
                val = float(val) if "." in str(val) else int(val)
            except ValueError:
                if str(val).lower() == "true":
                    val = True
                elif str(val).lower() == "false":
                    val = False
            if set_docx_option(args.key, val):
                print(f"[CONFIG] DOCX option '{args.key}' set to: {val}")
                return 0
            print("[!] Error updating DOCX option.", file=sys.stderr)
            return 1
        if args.key:
            cfg = get_docx_config()
            if args.key in cfg:
                print(cfg[args.key])
                return 0
            print(f"[!] Key '{args.key}' not found in DOCX configuration.", file=sys.stderr)
            return 1
        print(json.dumps(get_docx_config(), indent=2))
        return 0
    return 0


def _handle_tips_cli(args: argparse.Namespace) -> int:
    action = getattr(args, "action", None)
    if action == "enable" or (action == "set" and getattr(args, "state", "").lower() in ("true", "1", "yes", "on")):
        set_tips_enabled(True)
        print("[CONFIG] Dynamic tips display enabled.")
        return 0
    if action == "disable" or (action == "set" and getattr(args, "state", "").lower() in ("false", "0", "no", "off")):
        set_tips_enabled(False)
        print("[CONFIG] Dynamic tips display disabled.")
        return 0
    if action == "toggle":
        new_val = toggle_tips()
        print(f"[CONFIG] Dynamic tips display {'enabled' if new_val else 'disabled'}.")
        return 0
    enabled = get_tips_enabled()
    print(f"tips_enabled: {enabled}")
    return 0


def _handle_state_cli(args: argparse.Namespace) -> int:
    action = getattr(args, "action", None)
    if args.subcommand == "active-manuscript":
        if action == "set" and hasattr(args, "name"):
            set_active_manuscript(args.name)
            print(f"[CONFIG] Active manuscript set to: {args.name}")
            return 0
        if action == "clear":
            clear_active_manuscript()
            print("[CONFIG] Active manuscript cleared.")
            return 0
        val = get_active_manuscript_name()
        print(val or "None")
        return 0

    if args.subcommand == "active-world":
        if action == "set" and hasattr(args, "name"):
            set_active_world(args.name)
            print(f"[CONFIG] Active world set to: {args.name}")
            return 0
        if action == "clear":
            clear_active_world()
            print("[CONFIG] Active world cleared.")
            return 0
        val = get_active_world_name()
        print(val or "None")
        return 0

    if args.subcommand == "active-universe":
        if action == "set" and hasattr(args, "name"):
            set_active_universe(args.name)
            print(f"[CONFIG] Active universe set to: {args.name}")
            return 0
        if action == "clear":
            clear_active_universe()
            print("[CONFIG] Active universe cleared.")
            return 0
        val = get_active_universe_name()
        print(val or "None")
        return 0
    return 0


def _handle_theme_cli(args: argparse.Namespace) -> int:
    if args.subcommand == "theme":
        if args.preset:
            if set_ui_visual_preset(args.preset):
                print(f"[CONFIG] Active UI visual preset set to: {args.preset}")
                return 0
            print("[!] Error saving UI preset.", file=sys.stderr)
            return 1
        print(get_ui_visual_preset())
        return 0

    if args.subcommand == "sound-preset":
        if args.preset:
            if set_typewriter_sound_preset(args.preset):
                print(f"[CONFIG] Active typewriter sound preset set to: {args.preset}")
                return 0
            print("[!] Error saving sound preset.", file=sys.stderr)
            return 1
        print(get_typewriter_sound_preset())
        return 0

    if args.subcommand == "crt-fx":
        action = getattr(args, "action", None)
        if action == "enable":
            set_crt_fx_enabled(True)
            print("[CONFIG] CRT scanline effect enabled.")
            return 0
        if action == "disable":
            set_crt_fx_enabled(False)
            print("[CONFIG] CRT scanline effect disabled.")
            return 0
        val = get_crt_fx_enabled()
        print(f"crt_fx_enabled: {val}")
        return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for managing Ars Arcanum configurations."""
    parser = argparse.ArgumentParser(description="Ars Arcanum Configuration Tool")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # backup-dest subcommand
    bd_parser = subparsers.add_parser("backup-dest", help="Manage secure backup destination")
    bd_sub = bd_parser.add_subparsers(dest="action", required=True)
    bd_sub.add_parser("get", help="Print current secure backup destination")
    set_p = bd_sub.add_parser("set", help="Set secure backup destination")
    set_p.add_argument("path", help="Absolute or relative path to secure backup directory")
    bd_sub.add_parser("clear", help="Clear configured secure backup destination")

    # docx subcommands
    preset_parser = subparsers.add_parser("docx-preset", help="Manage DOCX formatting presets")
    preset_parser.add_argument(
        "preset",
        nargs="?",
        help="Preset name to activate (standard-submission, modern-manuscript, classic-trade, custom)",
    )
    subparsers.add_parser("docx-presets", help="List all available DOCX formatting presets")
    dcfg_parser = subparsers.add_parser("docx-config", help="View or set DOCX formatting options")
    dcfg_parser.add_argument(
        "key",
        nargs="?",
        help="Option key (e.g. font_family, font_size_pt, line_spacing, margin_inches)",
    )
    dcfg_parser.add_argument("value", nargs="?", help="Option value")

    # tips subcommand
    tips_parser = subparsers.add_parser("tips", help="Manage dynamic tips display preference")
    tips_sub = tips_parser.add_subparsers(dest="action", required=False)
    tips_sub.add_parser("get", help="Get current tips enabled status")
    tips_sub.add_parser("enable", help="Enable dynamic tips display")
    tips_sub.add_parser("disable", help="Disable dynamic tips display")
    tips_sub.add_parser("toggle", help="Toggle dynamic tips display")
    set_tips_p = tips_sub.add_parser("set", help="Set tips enabled status (true/false)")
    set_tips_p.add_argument("state", help="true or false")

    # state subcommands
    ams_parser = subparsers.add_parser("active-manuscript", help="Manage active manuscript default")
    ams_sub = ams_parser.add_subparsers(dest="action", required=False)
    ams_sub.add_parser("get", help="Get active manuscript")
    ams_set = ams_sub.add_parser("set", help="Set active manuscript")
    ams_set.add_argument("name", help="Manuscript name or directory")
    ams_sub.add_parser("clear", help="Clear active manuscript")

    aw_parser = subparsers.add_parser("active-world", help="Manage active world default")
    aw_sub = aw_parser.add_subparsers(dest="action", required=False)
    aw_sub.add_parser("get", help="Get active world")
    aw_set = aw_sub.add_parser("set", help="Set active world")
    aw_set.add_argument("name", help="World name or directory")
    aw_sub.add_parser("clear", help="Clear active world")

    au_parser = subparsers.add_parser("active-universe", help="Manage active universe default")
    au_sub = au_parser.add_subparsers(dest="action", required=False)
    au_sub.add_parser("get", help="Get active universe")
    au_set = au_sub.add_parser("set", help="Set active universe")
    au_set.add_argument("name", help="Universe name or directory")
    au_sub.add_parser("clear", help="Clear active universe")

    # theme subcommands
    theme_parser = subparsers.add_parser("theme", help="Manage UI visual preset")
    theme_parser.add_argument("preset", nargs="?", help="Preset name to activate")

    sound_parser = subparsers.add_parser("sound-preset", help="Manage typewriter audio model preset")
    sound_parser.add_argument("preset", nargs="?", help="Acoustic sound model to activate")

    crt_parser = subparsers.add_parser("crt-fx", help="Manage CRT scanline effect preference")
    crt_sub = crt_parser.add_subparsers(dest="action", required=False)
    crt_sub.add_parser("get", help="Get CRT scanline preference")
    crt_sub.add_parser("enable", help="Enable CRT scanlines")
    crt_sub.add_parser("disable", help="Disable CRT scanlines")

    args = parser.parse_args(argv)

    if args.subcommand == "backup-dest":
        return _handle_backup_dest_cli(args)
    if args.subcommand in ("docx-preset", "docx-presets", "docx-config"):
        return _handle_docx_cli(args)
    if args.subcommand == "tips":
        return _handle_tips_cli(args)
    if args.subcommand in ("active-manuscript", "active-world", "active-universe"):
        return _handle_state_cli(args)
    if args.subcommand in ("theme", "sound-preset", "crt-fx"):
        return _handle_theme_cli(args)

    return 0


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
