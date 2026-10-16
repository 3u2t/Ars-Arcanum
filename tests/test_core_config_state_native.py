"""Unit tests for native core configuration and state managers (`src/arcanum/core/config.py` & `src/arcanum/core/state.py`)."""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.config import (
    clear_backup_dest,
    get_active_docx_preset_name,
    get_authorial_constitution,
    get_authorial_policy,
    get_backup_dest,
    get_config_dir,
    get_config_file_path,
    get_crt_fx_enabled,
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
    main as config_main,
    save_config,
    set_authorial_policy,
    set_backup_dest,
    set_crt_fx_enabled,
    set_docx_option,
    set_docx_preset,
    set_engine_enabled,
    set_tips_enabled,
    set_typewriter_sound_preset,
    set_ui_visual_preset,
    set_world_axioms,
    toggle_tips,
)
from src.arcanum.core.state import (
    clear_active_manuscript,
    clear_active_universe,
    clear_active_world,
    get_active_manuscript,
    get_active_manuscript_name,
    get_active_universe,
    get_active_universe_name,
    get_active_world,
    get_active_world_name,
    get_daily_flow_state,
    get_default_scope,
    set_active_manuscript,
    set_active_universe,
    set_active_world,
    set_daily_flow_state,
    set_default_scope,
)


class TestCoreConfigStateNative(unittest.TestCase):
    """Test native config and state management directly."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.tmp.name)
        self.env_patch = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.work_dir)})
        self.env_patch.start()

    def tearDown(self) -> None:
        self.env_patch.stop()
        self.tmp.cleanup()

    def test_config_paths_and_storage(self) -> None:
        self.assertEqual(get_config_dir(), self.work_dir / "ars-arcanum")
        self.assertEqual(get_config_file_path(), self.work_dir / "ars-arcanum" / "config.json")
        self.assertEqual(load_config(), {})

        data = {"author": "Lyra", "mode": "sovereign"}
        self.assertTrue(save_config(data))
        self.assertEqual(load_config(), data)

    def test_backup_dest_and_tips(self) -> None:
        self.assertEqual(get_backup_dest(), "")
        backup_path = str(self.work_dir / "vault_backups")
        self.assertTrue(set_backup_dest(backup_path))
        self.assertEqual(get_backup_dest(), str(Path(backup_path).resolve()))
        self.assertTrue(clear_backup_dest())
        self.assertEqual(get_backup_dest(), "")

        # Tips
        self.assertTrue(get_tips_enabled())
        self.assertFalse(toggle_tips())
        self.assertFalse(get_tips_enabled())
        set_tips_enabled(True)
        self.assertTrue(get_tips_enabled())

    def test_docx_presets_and_options(self) -> None:
        self.assertIn("standard-submission", get_docx_preset_names())
        presets = list_docx_presets()
        self.assertIn("chicago-manual", presets)

        self.assertEqual(get_active_docx_preset_name(), "standard-submission")
        self.assertTrue(set_docx_preset("modern-manuscript"))
        self.assertEqual(get_active_docx_preset_name(), "modern-manuscript")

        # Custom option switches to custom preset
        self.assertTrue(set_docx_option("line_spacing", 1.8))
        self.assertEqual(get_active_docx_preset_name(), "custom")
        cfg = get_docx_config()
        self.assertEqual(cfg["line_spacing"], 1.8)

    def test_ui_and_audio_presets(self) -> None:
        self.assertEqual(get_ui_visual_preset(), "sovereign-dark")
        self.assertTrue(set_ui_visual_preset("amber-terminal"))
        self.assertEqual(get_ui_visual_preset(), "amber-terminal")

        self.assertEqual(get_typewriter_sound_preset(), "remington_1890")
        self.assertTrue(set_typewriter_sound_preset("olympia_sm3"))
        self.assertEqual(get_typewriter_sound_preset(), "olympia_sm3")

        self.assertFalse(get_crt_fx_enabled())
        self.assertTrue(set_crt_fx_enabled(True))
        self.assertTrue(get_crt_fx_enabled())

    def test_authorial_policy_and_constitution(self) -> None:
        pol = get_authorial_policy()
        self.assertEqual(pol.get("default_mode"), "observational")

        self.assertTrue(set_authorial_policy({"default_mode": "strict"}))
        self.assertEqual(get_authorial_policy()["default_mode"], "strict")

        # Engine toggles
        self.assertEqual(get_disabled_engines(), [])
        self.assertTrue(is_engine_enabled("timeline_solver"))
        set_engine_enabled("timeline_solver", False)
        self.assertFalse(is_engine_enabled("timeline_solver"))
        self.assertIn("timeline_solver", get_disabled_engines())
        set_engine_enabled("timeline_solver", True)
        self.assertTrue(is_engine_enabled("timeline_solver"))

        # World axioms
        axioms = get_world_axioms()
        self.assertIn("magic_modality", axioms)
        self.assertTrue(set_world_axioms("Eldoria", {"magic_modality": "rationalist"}))
        self.assertEqual(get_world_axioms("Eldoria")["magic_modality"], "rationalist")

        # Constitution and rule suppression
        c_loaded = load_authorial_constitution()
        self.assertIn("default_mode", c_loaded)
        c_resolved = get_authorial_constitution()
        self.assertIn("canon", c_resolved)
        self.assertIsInstance(get_suppressed_rules(), list)
        self.assertFalse(is_rule_suppressed("NON_EXISTENT_RULE_123"))

    def test_workspace_state_and_flow(self) -> None:
        # Manuscript target
        self.assertEqual(get_active_manuscript(), "")
        self.assertTrue(set_active_manuscript("Book-One"))
        self.assertEqual(get_active_manuscript(), "Book-One")
        self.assertEqual(get_active_manuscript_name(), "Book-One")
        self.assertTrue(clear_active_manuscript())
        self.assertEqual(get_active_manuscript(), "")

        # World target
        self.assertEqual(get_active_world(), "")
        self.assertTrue(set_active_world("Veridion"))
        self.assertEqual(get_active_world(), "Veridion")
        self.assertEqual(get_active_world_name(), "Veridion")
        self.assertTrue(clear_active_world())
        self.assertEqual(get_active_world(), "")

        # Universe target
        self.assertEqual(get_active_universe(), "")
        self.assertTrue(set_active_universe("Cosmos-Prime"))
        self.assertEqual(get_active_universe(), "Cosmos-Prime")
        self.assertEqual(get_active_universe_name(), "Cosmos-Prime")
        self.assertTrue(clear_active_universe())
        self.assertEqual(get_active_universe(), "")

        # Default scope
        self.assertEqual(get_default_scope(), {})
        self.assertTrue(set_default_scope({"active_stage": "Revision"}))
        self.assertEqual(get_default_scope()["active_stage"], "Revision")

        # Daily flow state
        flow = get_daily_flow_state()
        self.assertEqual(flow["last_cursor_line"], 1)
        self.assertEqual(flow["active_workspace_phase"], "drafting")
        self.assertTrue(set_daily_flow_state({"last_cursor_line": 42, "next_time_bridge": "Midday scene"}))
        updated_flow = get_daily_flow_state()
        self.assertEqual(updated_flow["last_cursor_line"], 42)
        self.assertEqual(updated_flow["next_time_bridge"], "Midday scene")

    def test_cli_dispatch(self) -> None:
        # backup-dest set and get
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = config_main(["backup-dest", "set", str(self.work_dir / "cli_backups")])
            self.assertEqual(code, 0)
            self.assertIn("Secure backup destination set", mock_out.getvalue())

        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = config_main(["backup-dest", "get"])
            self.assertEqual(code, 0)
            self.assertIn("cli_backups", mock_out.getvalue())

        # tips toggle
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = config_main(["tips", "toggle"])
            self.assertEqual(code, 0)

        # docx-presets
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = config_main(["docx-presets"])
            self.assertEqual(code, 0)
            self.assertIn("Standard Submission", mock_out.getvalue())


if __name__ == "__main__":
    unittest.main()
