#!/usr/bin/env python3
"""
Unit tests for Native Ars Arcanum Diagnostics Engine (src/arcanum/core/diagnostics.py).
"""

from __future__ import annotations

import io
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.diagnostics import (
    VERSION,
    format_diagnostic_report_markdown,
    generate_diagnostic_report,
    get_command_version,
    get_state_dir,
    get_toolchain_diagnostics,
    main,
    redact_sensitive_paths,
    run_doctor_report,
    setup_logging,
)
from src.arcanum.core import (
    format_diagnostic_report_markdown as core_format_md,
    generate_diagnostic_report as core_gen_report,
    get_state_dir as core_get_state_dir,
    get_toolchain_diagnostics as core_get_tc,
    redact_sensitive_paths as core_redact,
    run_doctor_report as core_doctor,
    setup_logging as core_setup_log,
)


class TestCoreDiagnosticsNative(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_reexports(self) -> None:
        self.assertIs(core_format_md, format_diagnostic_report_markdown)
        self.assertIs(core_gen_report, generate_diagnostic_report)
        self.assertIs(core_get_state_dir, get_state_dir)
        self.assertIs(core_get_tc, get_toolchain_diagnostics)
        self.assertIs(core_redact, redact_sensitive_paths)
        self.assertIs(core_doctor, run_doctor_report)
        self.assertIs(core_setup_log, setup_logging)

    def test_state_dir_and_logging(self) -> None:
        state_dir = get_state_dir()
        self.assertTrue(state_dir.is_dir())
        self.assertIn("ars-arcanum", str(state_dir))

        logger = setup_logging()
        self.assertIsInstance(logger, logging.Logger)
        logger.info("Native diagnostics logger verified")

    def test_redact_paths(self) -> None:
        home_path = str(Path.home())
        sensitive = f"Path: {home_path}/vault/novel.md"
        redacted = redact_sensitive_paths(sensitive)
        self.assertNotIn(home_path, redacted)
        self.assertIn("~/vault/novel.md", redacted)

    def test_toolchain_and_report_generation(self) -> None:
        import sys
        self.assertIsNotNone(get_command_version([sys.executable, "--version"]))
        tc = get_toolchain_diagnostics()
        self.assertIn("python", tc["tools"])
        self.assertTrue(tc["tools"]["python"]["available"])

        proj = self.work_dir / "TestLoreVault"
        proj.mkdir()
        (proj / "00-World-Bible").mkdir()
        (proj / "01-Manuscript").mkdir()
        (proj / "world.yaml").write_text("name: Test\n", encoding="utf-8")

        report = generate_diagnostic_report(project_path=str(proj))
        self.assertEqual(report["version"], VERSION)
        self.assertTrue(report["project"]["has_world_bible"])
        self.assertTrue(report["project"]["has_manuscript"])
        self.assertTrue(report["project"]["manifest_found"])

        md = format_diagnostic_report_markdown(report)
        self.assertIn("Ars Arcanum Diagnostic Triage Report", md)
        self.assertIn("Toolchain & Dependencies", md)
        self.assertIn("Target Project Inspection", md)

    def test_run_doctor_and_cli(self) -> None:
        w_dir = self.work_dir / "DoctorVault"
        w_dir.mkdir()
        (w_dir / "world.yaml").write_text('schema_version: "1.0"\n', encoding="utf-8")

        rc = run_doctor_report(world_filter=str(w_dir), as_json=True)
        self.assertIn(rc, (0, 1))

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc_cli = main(["--report", str(w_dir)])
            self.assertEqual(rc_cli, 0)
            self.assertIn("Diagnostic Triage Report", mock_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
