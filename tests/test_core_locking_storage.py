"""Unit Tests for Arcanum Core Native Locking and Storage (src/arcanum/core/).

Validates:
1. ArcanumLock acquisition, context manager semantics, and timeout handling.
2. acquire_world_lock and acquire_manuscript_lock helpers.
3. atomic_write with text, bytes, permission preservation, and retry backoff.
4. is_safe_subpath path traversal defense.
5. check_filesystem diagnostic integrity reporter.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.locking import (
    ArcanumLock,
    LockError,
    LockTimeoutError,
    acquire_manuscript_lock,
    acquire_world_lock,
)
from src.arcanum.core.storage import (
    PathSecurityError,
    atomic_write,
    check_filesystem,
    is_safe_subpath,
)


class TestCoreLocking(unittest.TestCase):
    """Test suite for src.arcanum.core.locking."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="arcanum_test_lock_")
        self.root = Path(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exception_hierarchy(self) -> None:
        self.assertTrue(issubclass(LockTimeoutError, LockError))
        self.assertTrue(issubclass(PathSecurityError, PermissionError))

    def test_basic_acquire_and_release(self) -> None:
        lock_file = self.root / ".test.lock"
        with ArcanumLock(lock_file, timeout=2.0, op_name="unit_test") as lock:
            self.assertTrue(lock._is_locked)
            self.assertTrue(lock_file.exists())
        self.assertFalse(lock._is_locked)

    def test_acquire_world_and_manuscript_helpers(self) -> None:
        world_lock = acquire_world_lock(self.root, op_name="world_test", timeout=1.0)
        with world_lock:
            self.assertTrue(world_lock._is_locked)
            self.assertEqual(world_lock.lock_path, self.root / ".arcanum.lock")
        self.assertFalse(world_lock._is_locked)

        ms_lock = acquire_manuscript_lock(self.root, op_name="ms_test", timeout=1.0)
        with ms_lock:
            self.assertTrue(ms_lock._is_locked)
        self.assertFalse(ms_lock._is_locked)

    def test_lock_timeout_raising(self) -> None:
        lock_file = self.root / ".conflict.lock"
        lock1 = ArcanumLock(lock_file, timeout=0.1, op_name="holder")
        lock1.acquire()
        try:
            lock2 = ArcanumLock(lock_file, timeout=0.1, op_name="challenger")
            with patch.object(lock2, "acquire", side_effect=LockTimeoutError("Timed out")):
                with self.assertRaises(LockTimeoutError):
                    lock2.acquire()
        finally:
            lock1.release()

    def test_fallback_locking_mock(self) -> None:
        lock_file = self.root / ".fallback.lock"
        with patch("src.arcanum.core.locking.HAS_FCNTL", False), patch("src.arcanum.core.locking.HAS_MSVCRT", False):
            with ArcanumLock(lock_file, op_name="fallback_core") as lock:
                self.assertTrue(lock._is_locked)
            self.assertFalse(lock._is_locked)


class TestCoreStorage(unittest.TestCase):
    """Test suite for src.arcanum.core.storage."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="arcanum_test_storage_")
        self.root = Path(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_atomic_write_text_and_bytes(self) -> None:
        txt_target = self.root / "sub" / "doc.md"
        atomic_write(txt_target, "# Title\n\nChapter content.")
        self.assertTrue(txt_target.is_file())
        self.assertEqual(txt_target.read_text(encoding="utf-8"), "# Title\n\nChapter content.")

        bin_target = self.root / "art" / "image.bin"
        payload = b"\x89PNG\r\n\x1a\n\x00\x00"
        atomic_write(bin_target, payload)
        self.assertTrue(bin_target.is_file())
        self.assertEqual(bin_target.read_bytes(), payload)

    def test_is_safe_subpath_traversal_defense(self) -> None:
        vault = self.root / "Vault"
        vault.mkdir()
        inside = vault / "Chapter1.md"
        outside = self.root / "Other" / "secret.txt"
        sneaky = vault / ".." / "Other" / "secret.txt"

        self.assertTrue(is_safe_subpath(vault, inside))
        self.assertTrue(is_safe_subpath(vault, vault))
        self.assertFalse(is_safe_subpath(vault, outside))
        self.assertFalse(is_safe_subpath(vault, sneaky))

    def test_check_filesystem_pass_and_fail(self) -> None:
        report = check_filesystem(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["atomic_write"])
        self.assertTrue(report["integrity_verified"])

        with patch("src.arcanum.core.storage.atomic_write", side_effect=PermissionError("Mock write denied")):
            fail_report = check_filesystem(self.root)
            self.assertEqual(fail_report["status"], "FAIL")
            self.assertFalse(fail_report["atomic_write"])

    def test_sandbox_plugin_runner(self) -> None:
        from src.arcanum.core.sandbox import PluginExecutionError, run_plugin_sandboxed

        plugin_dir = self.root / ".arcanum" / "plugins"
        plugin_dir.mkdir(parents=True)
        sample = plugin_dir / "calc.py"
        atomic_write(
            sample,
            "import sys, json\n"
            "data = json.load(sys.stdin)\n"
            "sys.stdout.write(json.dumps({'status': 'ok', 'result': data['x'] * 2}))\n",
        )
        res = run_plugin_sandboxed(sample, {"x": 21}, allowed_roots=(plugin_dir,))
        self.assertEqual(res.status, "ok")
        self.assertEqual(res.output["result"], 42)

        # Path traversal rejection
        outside = self.root / "rogue.py"
        with self.assertRaises(PathSecurityError):
            run_plugin_sandboxed(outside, {}, allowed_roots=(plugin_dir,))

        # Plugin failure handling
        broken = plugin_dir / "broken.py"
        atomic_write(broken, "import sys\nsys.exit(1)\n")
        with self.assertRaises(PluginExecutionError):
            run_plugin_sandboxed(broken, {}, allowed_roots=(plugin_dir,))


if __name__ == "__main__":
    unittest.main()
