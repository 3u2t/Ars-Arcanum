"""Comprehensive unit tests for native manuscript draft versioning & lineage engine.

Module: tests/test_manuscript_drafts_native.py
Verifies: src.arcanum.manuscript.drafts
- Draft lifecycle: listing, discovery, active draft switching.
- Granular chapter scoping & slicing during forking.
- Draft immutability locking & unlocking.
- Lineage tree graph generation.
- Path traversal defense & atomic write resilience.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.arcanum.core.storage import PathSecurityError, atomic_write
from src.arcanum.manuscript.drafts import (
    ChapterInfo,
    DraftInfo,
    DraftManager,
    activate_draft,
    count_prose_words,
    fork_draft,
    get_draft_status,
    list_drafts,
    lock_draft,
    parse_number_ranges,
    sanitize_identifier,
    set_milestone,
    set_notes,
    unlock_draft,
)


class TestManuscriptDraftsNative(unittest.TestCase):
    """Test suite for src.arcanum.manuscript.drafts."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.ms_dir = Path(self._tmp.name).resolve() / "Manuscript"
        self.ms_dir.mkdir(parents=True, exist_ok=True)

        # Create initial Draft-01 with 3 chapters
        d1 = self.ms_dir / "Draft-01"
        d1.mkdir(parents=True, exist_ok=True)
        atomic_write(d1 / "01_Chapter_01.md", "---\ntitle: Opening\n---\n# Chapter 1\n\nWord count one two three.")
        atomic_write(d1 / "02_Chapter_02.md", "---\ntitle: Middle\n---\n# Chapter 2\n\nWord count four five six.")
        atomic_write(d1 / "03_Chapter_03.md", "---\ntitle: Climax\n---\n# Chapter 3\n\nWord count seven eight nine.")

        # Create basic manuscript.yaml
        atomic_write(
            self.ms_dir / "manuscript.yaml",
            "title: The Sovereign Scriptorium\nactive_draft: Draft-01\n",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parse_number_ranges_and_prose_words(self) -> None:
        self.assertEqual(parse_number_ranges("1-3,5,8..10"), [1, 2, 3, 5, 8, 9, 10])
        self.assertEqual(parse_number_ranges(None), [])
        self.assertEqual(count_prose_words("# Heading\n\nOne two three four."), 5)
        self.assertEqual(sanitize_identifier("Draft 02!"), "Draft02")

        ci = ChapterInfo("01.md", "Chapter 1", 1, 500, "/path/01.md")
        self.assertEqual(ci.words, 500)
        self.assertEqual(ci.title, "Chapter 1")

    def test_list_initial_drafts(self) -> None:
        drafts = list_drafts(self.ms_dir)
        self.assertEqual(len(drafts), 1)
        d = drafts[0]
        self.assertEqual(d["name"], "Draft-01")
        self.assertTrue(d["is_active"])
        self.assertFalse(d["locked"])
        self.assertEqual(d["chapter_count"], 3)
        self.assertGreater(d["word_count"], 10)

        di = DraftInfo(name="Draft-01", volume="Root", path=str(self.ms_dir / "Draft-01"))
        self.assertEqual(di.name, "Draft-01")
        self.assertIn("Draft-01", di.to_dict()["name"])

        # Functional activate_draft
        act_res = activate_draft(self.ms_dir, "Draft-01")
        self.assertEqual(act_res["active_draft"], "Draft-01")

    def test_fork_draft_with_chapter_slicing(self) -> None:
        mgr = DraftManager(self.ms_dir)
        res = mgr.fork_draft(
            new_draft_name="Draft-02",
            source_draft_name="Draft-01",
            chapters="1,3",
            milestone="Structural Edit",
            notes="Excluded chapter 2 for rewrite",
            activate=True,
        )

        self.assertEqual(res["draft"], "Draft-02")
        self.assertEqual(res["chapters_copied"], 2)
        self.assertTrue(res["active"])

        d2_dir = self.ms_dir / "Draft-02"
        self.assertTrue((d2_dir / "01_Chapter_01.md").exists())
        self.assertFalse((d2_dir / "02_Chapter_02.md").exists())
        self.assertTrue((d2_dir / "03_Chapter_03.md").exists())

        # Check status and parent delta
        stat = mgr.get_draft_status("Draft-02")
        self.assertEqual(stat["parent_draft"], "Draft-01")
        self.assertEqual(stat["chapter_count"], 2)
        self.assertIsNotNone(stat["delta_words"])

    def test_lock_and_unlock_draft(self) -> None:
        mgr = DraftManager(self.ms_dir)
        res_lock = lock_draft(self.ms_dir, "Draft-01", notes="Sealed draft")
        self.assertTrue(res_lock["locked"])
        self.assertTrue((self.ms_dir / "Draft-01" / ".locked").exists())

        draft1 = mgr.get_draft("Draft-01")
        self.assertIsNotNone(draft1)
        assert draft1 is not None
        self.assertTrue(draft1.locked)

        res_unlock = unlock_draft(self.ms_dir, "Draft-01")
        self.assertFalse(res_unlock["locked"])
        self.assertFalse((self.ms_dir / "Draft-01" / ".locked").exists())

    def test_set_milestone_and_notes(self) -> None:
        res_m = set_milestone(self.ms_dir, "Draft-01", "Beta")
        self.assertEqual(res_m["milestone"], "Beta")

        res_n = set_notes(self.ms_dir, "Draft-01", "Beta feedback complete.")
        self.assertEqual(res_n["notes"], "Beta feedback complete.")

        stat = get_draft_status(self.ms_dir, "Draft-01")
        self.assertEqual(stat["milestone"], "Beta")
        self.assertEqual(stat["notes"], "Beta feedback complete.")

    def test_lineage_graph(self) -> None:
        fork_draft(self.ms_dir, new_draft_name="Draft-02", source_draft_name="Draft-01")
        fork_draft(self.ms_dir, new_draft_name="Draft-03", source_draft_name="Draft-02")

        mgr = DraftManager(self.ms_dir)
        graph = mgr.get_lineage_graph()
        self.assertEqual(len(graph), 1)
        root = graph[0]
        self.assertEqual(root["name"], "Draft-01")
        self.assertEqual(len(root["children"]), 1)
        d2_node = root["children"][0]
        self.assertEqual(d2_node["name"], "Draft-02")
        self.assertEqual(len(d2_node["children"]), 1)
        self.assertEqual(d2_node["children"][0]["name"], "Draft-03")

    def test_render_ansi_tree(self) -> None:
        mgr = DraftManager(self.ms_dir)
        tree = mgr.render_ansi_tree()
        self.assertIn("Draft-01", tree)
        self.assertIn("Genesis", tree)

    def test_path_security_defense(self) -> None:
        mgr = DraftManager(self.ms_dir)
        with self.assertRaises(PathSecurityError):
            mgr.fork_draft(new_draft_name="../../EscapeDraft")


if __name__ == "__main__":
    unittest.main()
