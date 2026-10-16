"""Unit tests for native core storage and hardening modules (`src/arcanum/core/storage.py` & `src/arcanum/core/hardening.py`)."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.storage import (
    atomic_write,
    check_filesystem,
    is_safe_subpath,
    main as storage_main,
    sanitize_identifier,
)
from src.arcanum.core.hardening import (
    normalize_cjk_and_unicode_prose,
    parse_frontmatter_hardened,
    parse_xml_safe_bytes,
    run_lite_continuity_check,
    sanitize_critic_markup,
    validate_safe_zip_archive,
)


class TestCoreFsHardeningNative(unittest.TestCase):
    """Test native storage and hardening utilities directly."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_storage_atomic_write_and_path_safety(self) -> None:
        target = self.tmp_dir / "nested" / "doc.txt"
        atomic_write(target, "Safe Content")
        self.assertTrue(target.is_file())
        self.assertEqual(target.read_text(encoding="utf-8"), "Safe Content")

        # Overwrite with bytes
        atomic_write(target, b"Binary Data")
        self.assertEqual(target.read_bytes(), b"Binary Data")

        # is_safe_subpath
        self.assertTrue(is_safe_subpath(self.tmp_dir, target))
        self.assertFalse(is_safe_subpath(self.tmp_dir, self.tmp_dir / ".." / "escape.txt"))

        # sanitize_identifier
        self.assertEqual(sanitize_identifier("my_chapter-01"), "my_chapter-01")
        self.assertEqual(sanitize_identifier("CON.txt"), "item")
        self.assertEqual(sanitize_identifier("NUL"), "item")
        self.assertEqual(sanitize_identifier("???"), "item")
        self.assertEqual(sanitize_identifier(""), "item")

    def test_storage_check_filesystem_and_main(self) -> None:
        res = check_filesystem(self.tmp_dir)
        self.assertTrue(res["atomic_write_verified"])
        self.assertEqual(res["status"], "PASS")

        # CLI human-readable
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = storage_main([str(self.tmp_dir)])
            self.assertEqual(code, 0)
            self.assertIn("Atomic Filesystem Diagnostics", mock_out.getvalue())

        # CLI JSON
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            code = storage_main([str(self.tmp_dir), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(mock_out.getvalue())
            self.assertTrue(payload["atomic_write_verified"])

    def test_hardening_zip_and_xml_safety(self) -> None:
        # Valid ZIP
        safe_zip = self.tmp_dir / "safe.zip"
        with zipfile.ZipFile(safe_zip, "w") as zf:
            zf.writestr("test.txt", "content")
        members = validate_safe_zip_archive(safe_zip)
        self.assertEqual(members, ["test.txt"])

        # XML entity expansion prevention
        with self.assertRaises(ValueError):
            parse_xml_safe_bytes(b'<!DOCTYPE foo [<!ENTITY xxe "evil">]><foo>&xxe;</foo>')

        # Valid XML
        elem = parse_xml_safe_bytes(b"<note><to>Author</to></note>")
        self.assertEqual(elem.tag, "note")

    def test_hardening_frontmatter_and_critic_markup(self) -> None:
        # Fuzz-hardened frontmatter
        fm_text = "---\ntitle: Novel\nchapter: 1\ntags: [alpha, beta]\n---\nBody"
        meta, body = parse_frontmatter_hardened(fm_text)
        self.assertEqual(meta["title"], "Novel")
        self.assertEqual(meta["chapter"], 1)
        self.assertEqual(meta["tags"], ["alpha", "beta"])
        self.assertEqual(body.strip(), "Body")

        # CriticMarkup sanitization
        unbalanced = "Unbalanced {++addition without close and {--deletion"
        balanced = sanitize_critic_markup(unbalanced)
        self.assertTrue(balanced.endswith("--}"))
        self.assertEqual(balanced.count("{++"), balanced.count("++}"))

        # CJK normalization
        cjk_prose = "English words 砂の海"
        metrics = normalize_cjk_and_unicode_prose(cjk_prose)
        self.assertEqual(metrics["latin_words"], 2)
        self.assertEqual(metrics["cjk_ideographs"], 3)
        self.assertEqual(metrics["effective_words"], 5)

    def test_hardening_lite_mode_continuity_runner(self) -> None:
        vault_root = self.tmp_dir / "UniverseVault"
        vault_root.mkdir()
        chapter = vault_root / "Chapter-01.md"
        chapter.write_text("---\npov: Kaelen\nresource_balance: 10\n---\nProse here.", encoding="utf-8")

        report = run_lite_continuity_check(vault_root, write_dashboard=True)
        self.assertEqual(report.status, "CLEAN")
        self.assertEqual(report.total_issues, 0)
        self.assertTrue((vault_root / "_Arcanum_Lite_Dashboard.md").is_file())
        self.assertTrue((vault_root / ".obsidian" / "lite_profile.json").is_file())

        # Negative balance triggers finding
        bad_chapter = vault_root / "Chapter-02.md"
        bad_chapter.write_text("---\nresource_balance: -5\n---\nDeficit.", encoding="utf-8")
        bad_report = run_lite_continuity_check(vault_root, write_dashboard=True)
        self.assertEqual(bad_report.status, "NEEDS_ATTENTION")
        self.assertEqual(bad_report.counts_by_prefix["LED-"], 1)


if __name__ == "__main__":
    unittest.main()
