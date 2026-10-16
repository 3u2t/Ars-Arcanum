#!/usr/bin/env python3
"""
Unit tests for Native Ars Arcanum Schema & Project Migration Engine (src/arcanum/core/migrate.py).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.migrate import (
    CURRENT_SCHEMA_VERSION,
    REQUIRED_GITIGNORE_ENTRIES,
    ensure_gitignore_entries,
    main,
    migrate_manuscript,
    migrate_project,
    migrate_universe,
    migrate_world,
)
from src.arcanum.core import (
    CURRENT_SCHEMA_VERSION as CORE_SCHEMA_VER,
    REQUIRED_GITIGNORE_ENTRIES as CORE_GITIGNORE_ENTRIES,
    ensure_gitignore_entries as core_ensure_gi,
    migrate_manuscript as core_migrate_ms,
    migrate_project as core_migrate_proj,
    migrate_universe as core_migrate_univ,
    migrate_world as core_migrate_w,
)


class TestCoreMigrateNative(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_reexports(self) -> None:
        self.assertEqual(CORE_SCHEMA_VER, CURRENT_SCHEMA_VERSION)
        self.assertEqual(CORE_GITIGNORE_ENTRIES, REQUIRED_GITIGNORE_ENTRIES)
        self.assertIs(core_ensure_gi, ensure_gitignore_entries)
        self.assertIs(core_migrate_ms, migrate_manuscript)
        self.assertIs(core_migrate_proj, migrate_project)
        self.assertIs(core_migrate_univ, migrate_universe)
        self.assertIs(core_migrate_w, migrate_world)

    def test_ensure_gitignore(self) -> None:
        gi = self.work_dir / ".gitignore"
        gi.write_text("*.pyc\n", encoding="utf-8")
        actions = ensure_gitignore_entries(self.work_dir)
        self.assertTrue(len(actions) > 0)
        content = gi.read_text(encoding="utf-8")
        for entry in REQUIRED_GITIGNORE_ENTRIES:
            self.assertIn(entry, content)

    def test_migrate_universe_native(self) -> None:
        u_dir = self.work_dir / "NativeUniverse"
        u_dir.mkdir()
        actions = migrate_universe(u_dir)
        self.assertTrue(any("Created universe.yaml" in a for a in actions))
        manifest = u_dir / "universe.yaml"
        self.assertTrue(manifest.is_file())
        self.assertIn(CURRENT_SCHEMA_VERSION, manifest.read_text(encoding="utf-8"))

    def test_migrate_world_legacy_cleanup(self) -> None:
        w_dir = self.work_dir / "NativeWorld"
        w_dir.mkdir()
        (w_dir / "Characters").mkdir()
        (w_dir / "05-Backups").mkdir()
        (w_dir / "scriptorium.yaml").write_text("name: NativeWorld\n", encoding="utf-8")

        res = migrate_project(w_dir)
        self.assertEqual(res["type"], "world")
        self.assertTrue((w_dir / "world.yaml").is_file())
        self.assertTrue((w_dir / "Backups").is_dir())
        self.assertFalse((w_dir / "05-Backups").exists())

    def test_migrate_manuscript_native(self) -> None:
        m_dir = self.work_dir / "NativeNovel"
        m_dir.mkdir()
        (m_dir / "Book-01").mkdir()
        (m_dir / "04-Publishing").mkdir()

        res = migrate_project(m_dir)
        self.assertEqual(res["type"], "manuscript")
        self.assertTrue((m_dir / "Exports").is_dir())
        self.assertFalse((m_dir / "04-Publishing").exists())
        self.assertTrue((m_dir / "manuscript.yaml").is_file())

    def test_cli_native(self) -> None:
        m_dir = self.work_dir / "CLINovel"
        m_dir.mkdir()
        (m_dir / "manuscript.yaml").write_text("title: CLI\n", encoding="utf-8")

        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            rc = main([str(m_dir), "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["type"], "manuscript")


if __name__ == "__main__":
    unittest.main()
