#!/usr/bin/env python3
"""
Unit tests for Native Manuscript Importer and Heatmap Modules
(src.arcanum.manuscript.importer, src.arcanum.manuscript.heatmap).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.arcanum.manuscript.importer import (
    EpubImporter,
    HtmlToMarkdownConverter,
    convert_html_to_markdown,
    import_manuscript_batch,
    resolve_sequential_draft,
    rtf_to_text,
    split_monolithic_by_headings,
    standardize_chapter_frontmatter,
)
from src.arcanum.manuscript.heatmap import (
    ChapterRevisionStats,
    analyze_revision_churn,
    count_words,
    diff_line_counts,
    diff_word_counts,
    extract_dialogue_and_prose,
    extract_sub_scenes,
    scan_manuscript_snapshots,
)
from src.arcanum.manuscript import (
    import_manuscript_batch as ms_import_manuscript_batch,
    analyze_revision_churn as ms_analyze_revision_churn,
)


class TestNativeManuscriptImporterHeatmap(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_reexport_parity(self):
        self.assertIs(import_manuscript_batch, ms_import_manuscript_batch)
        self.assertIs(analyze_revision_churn, ms_analyze_revision_churn)
        self.assertTrue(issubclass(HtmlToMarkdownConverter, object))
        self.assertTrue(issubclass(EpubImporter, object))

        # Check sequential draft resolver
        seq = resolve_sequential_draft(self.root, "Book-01", "Draft-01")
        self.assertEqual(seq, "Draft-01")

    def test_html_and_rtf_converters(self):
        html_input = "<h1>Title</h1><p>This is <strong>bold</strong> and <em>italic</em>.</p>"
        md_out = convert_html_to_markdown(html_input)
        self.assertIn("# Title", md_out)
        self.assertIn("**bold**", md_out)
        self.assertIn("*italic*", md_out)

        rtf_input = r"{\rtf1\ansi\deff0 {\fonttbl{\f0 Times New Roman;}} \b Bold\b0  Normal \par Second Line}"
        rtf_out = rtf_to_text(rtf_input)
        self.assertIn("Bold Normal", rtf_out)
        self.assertIn("Second Line", rtf_out)

    def test_split_monolithic_and_frontmatter(self):
        mono = "# Chapter 1: The Beginning\nProse line.\n\n# Chapter 2: The Middle\nMore prose."
        chaps = split_monolithic_by_headings(mono)
        self.assertEqual(len(chaps), 2)
        self.assertEqual(chaps[0]["title"], "Chapter 1: The Beginning")
        self.assertEqual(chaps[1]["title"], "Chapter 2: The Middle")

        content, wc = standardize_chapter_frontmatter("Prose line.", "The Beginning", 1)
        self.assertIn("title: The Beginning", content)
        self.assertIn("chapter: 1", content)
        self.assertGreater(wc, 0)

    def test_heatmap_word_and_dialogue_diffing(self):
        text = 'She said, "Wait!" before entering the cavern.'
        d_text, p_text, d_wc, p_wc = extract_dialogue_and_prose(text)
        self.assertIn("Wait", d_text)
        self.assertIn("entering", p_text)
        self.assertGreater(d_wc, 0)
        self.assertGreater(p_wc, 0)
        self.assertEqual(count_words(text), 7)

        base = 'She said, "Go!" before leaving the cavern.'
        curr = 'She said, "Wait!" before entering the dark cavern.'
        tot_add, tot_del, _d_add, _d_del, _pr_add, _pr_del = diff_word_counts(curr, base)
        self.assertGreater(tot_add, 0)
        self.assertGreater(tot_del, 0)

        ins, dels = diff_line_counts("line 1\nline 2\n", "line 1\nline 3\n")
        self.assertEqual((ins, dels), (1, 1))

        scenes = extract_sub_scenes("Scene 1\n---\nScene 2")
        self.assertEqual(len(scenes), 2)

        stats = ChapterRevisionStats(
            chapter="ch1.md",
            rel_path="ch1.md",
            word_count=100,
            insertions=10,
            deletions=5,
            churn_score=15,
            churn_ratio=0.15,
            has_snapshot=True,
        )
        self.assertEqual(stats.churn_score, 15)

        summary = analyze_revision_churn([stats])
        self.assertEqual(summary["total_chapters"], 1)

        empty_scan = scan_manuscript_snapshots(self.root)
        self.assertEqual(empty_scan, [])


if __name__ == "__main__":
    unittest.main()
