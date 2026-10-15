"""Unit tests for Obsidian Lite Mode and `scripts.lib.audit_hardening` consolidation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.audit_hardening import (
    LITE_OBSIDIAN_PLUGINS,
    generate_obsidian_lite_profile,
    main_lite,
    run_lite_continuity_check,
)


class TestLiteModeAndConsolidation(unittest.TestCase):
    """Verifies the 5-plugin Obsidian Lite Mode profile, dashboard, and CLI runner."""

    def test_consolidated_package_exports(self) -> None:
        self.assertEqual(len(LITE_OBSIDIAN_PLUGINS), 5)
        self.assertIn("dataview", LITE_OBSIDIAN_PLUGINS)

    def test_lite_continuity_clean_and_violation_vaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "Reliquary"
            with self.assertRaises(FileNotFoundError):
                run_lite_continuity_check(vault)

            vault.mkdir(parents=True)
            ch1 = vault / "01_Chapter.md"
            ch1.write_text(
                "---\npov: Kaelen\nresource_balance: 10\n---\nClean chapter prose.",
                encoding="utf-8",
            )

            report_clean = run_lite_continuity_check(vault)
            self.assertEqual(report_clean.status, "CLEAN")
            self.assertEqual(report_clean.total_issues, 0)
            self.assertTrue((vault / "_Arcanum_Lite_Dashboard.md").is_file())
            self.assertTrue((vault / ".obsidian" / "lite_profile.json").is_file())

            profile_data = json.loads((vault / ".obsidian" / "lite_profile.json").read_text(encoding="utf-8"))
            self.assertEqual(len(profile_data["enabled_plugins"]), 5)

            ch2 = vault / "02_Chapter.md"
            ch2.write_text(
                "---\npov: Kaelen\nresource_balance: -4\n---\nOverdrafted ether vials.",
                encoding="utf-8",
            )
            ch3 = vault / "03_BadFM.md"
            ch3.write_text(
                "---\na:\n                                        b: too_deep\n---\nBad YAML.",
                encoding="utf-8",
            )
            report_warn = run_lite_continuity_check(vault)
            self.assertGreaterEqual(report_warn.total_issues, 2)

    def test_cli_bridge_main_lite_json_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "LiteVault"
            vault.mkdir(parents=True)
            (vault / "01_Scene.md").write_text("---\npov: Aria\n---\nScene body.", encoding="utf-8")

            rc_text = main_lite([str(vault)])
            self.assertIn(rc_text, (0, 1))

            rc_json = main_lite(["lite-check", str(vault), "--json"])
            self.assertIn(rc_json, (0, 1))

            rc_missing = main_lite([str(vault / "nonexistent_dir")])
            self.assertEqual(rc_missing, 2)

            profile_path = generate_obsidian_lite_profile(vault)
            self.assertTrue(profile_path.is_file())


if __name__ == "__main__":
    unittest.main()
