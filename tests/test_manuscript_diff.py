"""Comprehensive unit test suite for native manuscript diff engine.

Module: tests/test_manuscript_diff.py
Verifies: src.arcanum.manuscript.diff
- Paragraph-level hierarchical SHA-256 diffing & churn telemetry.
- Scraps extraction with atomic write backoff.
- Path traversal defense (PathSecurityError).
- Draft promotion with physical inode separation & parent read-only locks.
- Draft lineage tracking and multi-generation history reconstruction.
- Directory-level draft comparison.
- CLI execution.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.storage import PathSecurityError, atomic_write
from src.arcanum.manuscript.diff import (
    compare_chapter_hierarchical,
    compare_draft_directories,
    get_draft_history,
    get_draft_lineage,
    main,
    parse_frontmatter,
    promote_draft_hardlinked,
)


class TestManuscriptDiff(unittest.TestCase):
    """Test cases for src.arcanum.manuscript.diff."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parse_frontmatter(self) -> None:
        content = "---\ntitle: The Way of Kings\npov: Kaladin\nstatus: draft\n---\n\nChapter body begins here."
        meta, body = parse_frontmatter(content)
        self.assertEqual(meta.get("title"), "The Way of Kings")
        self.assertEqual(meta.get("pov"), "Kaladin")
        self.assertEqual(meta.get("status"), "draft")
        self.assertIn("Chapter body begins here.", body)

    def test_pristine_chapter_diff(self) -> None:
        text = "---\ntitle: Ch 1\n---\nFirst paragraph of text.\n\nSecond paragraph of text."
        report = compare_chapter_hierarchical("ch01", text, text)
        self.assertEqual(report.chapter_id, "ch01")
        self.assertEqual(report.words_added, 0)
        self.assertEqual(report.words_deleted, 0)
        self.assertEqual(report.unchanged_paragraphs, 2)
        self.assertEqual(report.modified_paragraphs, 0)
        self.assertEqual(report.churn_ratio, 0.0)
        self.assertTrue(any("REV-101" in d for d in report.diagnostics))

    def test_hierarchical_modifications_and_scraps(self) -> None:
        long_cut = " ".join(f"cutword{i}" for i in range(65))
        old_md = f"---\ntitle: Ch 1\n---\nFirst opening paragraph.\n\n{long_cut}\n\nThird paragraph old text."
        new_md = "---\ntitle: Ch 1\n---\nFirst opening paragraph.\n\nThird paragraph new text inserted here."

        scraps_dir = self.root / "Scraps"
        report = compare_chapter_hierarchical(
            "ch01",
            old_md,
            new_md,
            scraps_dir=scraps_dir,
            vault_root=self.root,
            min_scrap_words=50,
        )

        self.assertEqual(report.unchanged_paragraphs, 1)
        self.assertGreaterEqual(report.words_deleted, 65)
        self.assertEqual(len(report.scraps_extracted), 1)
        scrap_path = Path(report.scraps_extracted[0])
        self.assertTrue(scrap_path.exists())
        self.assertIn("cutword0", scrap_path.read_text(encoding="utf-8"))

    def test_scraps_path_security_error(self) -> None:
        outside_dir = Path(tempfile.gettempdir()) / "outside_scraps_test"
        old_md = " ".join(f"word{i}" for i in range(60))
        new_md = "Replaced text."

        with self.assertRaises(PathSecurityError):
            compare_chapter_hierarchical(
                "ch01",
                old_md,
                new_md,
                scraps_dir=outside_dir,
                vault_root=self.root,
                min_scrap_words=50,
            )

    def test_promote_draft_and_inode_separation(self) -> None:
        draft1_dir = self.root / "Draft-01"
        draft2_dir = self.root / "Draft-02"
        chap1 = draft1_dir / "Act_I" / "01_Prologue.md"
        atomic_write(chap1, "# Prologue\n\nOriginal text.")

        meta = promote_draft_hardlinked(
            self.root,
            "Draft-01",
            "Draft-02",
            milestone_tag="Structural Pass",
            lock_parent=True,
        )

        self.assertEqual(meta["draft"], "Draft-02")
        self.assertEqual(meta["parent_draft"], "Draft-01")
        self.assertEqual(meta["milestone"], "Structural Pass")
        self.assertEqual(meta["copied_files"], 1)

        # Parent should have .locked
        self.assertTrue((draft1_dir / ".locked").exists())
        # Target should have .draft_lineage.json
        self.assertTrue((draft2_dir / ".draft_lineage.json").exists())

        # Target file exists
        chap2 = draft2_dir / "Act_I" / "01_Prologue.md"
        self.assertTrue(chap2.exists())

        # Mutating chap2 must not affect chap1
        atomic_write(chap2, "# Prologue\n\nMutated Draft 2 text.")
        self.assertEqual(chap1.read_text(encoding="utf-8"), "# Prologue\n\nOriginal text.")

    def test_promote_draft_security_and_validation(self) -> None:
        # Parent non-existent
        with self.assertRaises(FileNotFoundError):
            promote_draft_hardlinked(self.root, "NonExistentDraft", "Draft-02")

        # Escapes manuscript root
        with self.assertRaises(PathSecurityError):
            promote_draft_hardlinked(self.root, "../OutsideDraft", "Draft-02")

        # Target already exists
        d1 = self.root / "Draft-01"
        d1.mkdir(parents=True)
        d2 = self.root / "Draft-02"
        d2.mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            promote_draft_hardlinked(self.root, "Draft-01", "Draft-02")

    def test_draft_lineage_and_multi_generation_history(self) -> None:
        d1 = self.root / "Draft-01"
        atomic_write(d1 / "ch1.md", "Draft 1")

        promote_draft_hardlinked(self.root, "Draft-01", "Draft-02", milestone_tag="First Revision", lock_parent=False)
        promote_draft_hardlinked(self.root, "Draft-02", "Draft-03", milestone_tag="Line Edit", lock_parent=False)

        lineage2 = get_draft_lineage(self.root, "Draft-02")
        self.assertIsNotNone(lineage2)
        assert lineage2 is not None
        self.assertEqual(lineage2["parent_draft"], "Draft-01")

        history = get_draft_history(self.root, "Draft-03")
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["draft"], "Draft-01")
        self.assertEqual(history[1]["draft"], "Draft-02")
        self.assertEqual(history[2]["draft"], "Draft-03")
        self.assertEqual(history[2]["milestone"], "Line Edit")

    def test_compare_draft_directories(self) -> None:
        d1 = self.root / "Draft-01"
        d2 = self.root / "Draft-02"
        atomic_write(d1 / "ch1.md", "Paragraph one.\n\nParagraph two.")
        atomic_write(d2 / "ch1.md", "Paragraph one.\n\nParagraph two modified.")
        atomic_write(d2 / "ch2.md", "New chapter added in Draft 2.")

        reports = compare_draft_directories(d1, d2)
        self.assertEqual(len(reports), 2)
        r_map = {r.chapter_id: r for r in reports}
        self.assertIn("ch1.md", r_map)
        self.assertIn("ch2.md", r_map)
        self.assertEqual(r_map["ch1.md"].unchanged_paragraphs, 1)
        self.assertEqual(r_map["ch2.md"].added_paragraphs, 1)

    def test_cli_main(self) -> None:
        old_file = self.root / "old.md"
        new_file = self.root / "new.md"
        atomic_write(old_file, "Old content here.")
        atomic_write(new_file, "New revised content here.")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            ret = main([str(old_file), str(new_file)])

        self.assertEqual(ret, 0)
        output = json.loads(stdout_buf.getvalue())
        self.assertEqual(output["chapter_id"], "new")
        self.assertIn("deltas", output)


if __name__ == "__main__":
    unittest.main()
