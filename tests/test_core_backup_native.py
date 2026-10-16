#!/usr/bin/env python3
"""
Unit tests for Native Core Backup, Restore, and Snapshot Modules
(src.arcanum.core.backup, src.arcanum.core.restore, src.arcanum.core.snapshot).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.arcanum.core.backup import (
    BACKUP_VERSION,
    compute_file_sha256,
    create_backup,
    detect_target_type,
    list_backups,
    should_exclude,
    verify_backup_integrity,
)
from src.arcanum.core.restore import (
    is_safe_tar_member,
    restore_archive,
    restore_backup,
    verify_archive_checksum,
)
from src.arcanum.core.snapshot import (
    save_snapshot,
)
from src.arcanum.core import (
    create_backup as core_create_backup,
    restore_backup as core_restore_backup,
    save_snapshot as core_save_snapshot,
)


class TestNativeCoreDisasterRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.project_dir = self.root / "Project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

        os.environ["GIT_AUTHOR_NAME"] = "Test Author"
        os.environ["GIT_AUTHOR_EMAIL"] = "test@example.com"
        os.environ["GIT_COMMITTER_NAME"] = "Test Author"
        os.environ["GIT_COMMITTER_EMAIL"] = "test@example.com"

        (self.project_dir / "world.yaml").write_text("name: TestWorld\n", encoding="utf-8")
        (self.project_dir / "chapter.md").write_text("# Chapter 1\nProse content.\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_reexport_parity(self):
        self.assertIs(create_backup, core_create_backup)
        self.assertIs(restore_backup, core_restore_backup)
        self.assertIs(save_snapshot, core_save_snapshot)
        self.assertTrue(BACKUP_VERSION)

        # Helper tests
        chapter_file = self.project_dir / "chapter.md"
        sha = compute_file_sha256(chapter_file)
        self.assertEqual(len(sha), 64)

        import tarfile
        ti = tarfile.TarInfo(name="safe/path.txt")
        ti.type = tarfile.REGTYPE
        self.assertTrue(is_safe_tar_member(ti, self.root))

        valid, computed_sha, _ = verify_archive_checksum(chapter_file, require_sidecar=False)
        self.assertTrue(valid)
        self.assertEqual(computed_sha, sha)

    def test_native_backup_and_restore_cycle(self):
        backup_out = self.root / "Backups"
        res = create_backup(self.project_dir, output_dir=backup_out, tag="v1")
        self.assertEqual(res["status"], "success")
        archive = Path(res["archive_path"])
        self.assertTrue(archive.is_file())

        # Verify integrity
        integrity = verify_backup_integrity(archive)
        self.assertTrue(integrity["valid"])
        self.assertEqual(integrity["sha256"], res["sha256"])

        # Listing
        backups = list_backups(backup_out)
        self.assertEqual(len(backups), 1)

        # Restore
        restored = self.root / "Restored"
        res_r = restore_archive(archive, target_dir=restored)
        self.assertEqual(res_r["status"], "success")
        self.assertTrue((restored / "Project" / "chapter.md").is_file())

    def test_detect_target_and_exclusions(self):
        self.assertEqual(detect_target_type(self.project_dir), ("world", "Project"))
        self.assertTrue(should_exclude(".git/objects"))
        self.assertTrue(should_exclude("Backups/archive.tar.gz"))
        self.assertFalse(should_exclude("01-Manuscript/chapter.md"))

    def test_snapshot_git_cycle(self):
        if shutil.which("git") is None:
            self.skipTest("git not available in environment")
        snap = save_snapshot(self.project_dir, message="Milestone 1")
        self.assertEqual(snap["status"], "success")
        self.assertTrue(snap["commit_hash"])

        snap_clean = save_snapshot(self.project_dir)
        self.assertEqual(snap_clean["status"], "clean")


if __name__ == "__main__":
    unittest.main()
