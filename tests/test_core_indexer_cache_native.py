#!/usr/bin/env python3
"""
Unit tests for native Ars Arcanum Core Indexer and Cache Engine.
Tests src.arcanum.core.indexer and src.arcanum.core.cache directly.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.arcanum.core import (
    CACHE_FILENAME,
    DataAccessLayer,
    ProseMetrics,
    VaultDocumentNode,
    VaultIndex,
    WikilinkRef,
    cache_main,
    compute_prose_metrics,
    compute_wordcounts,
    count_prose_words,
    count_words,
    extract_tags,
    get_cache_path,
    get_data_access,
    indexer_main,
    load_cache,
    parse_markdown_file,
    save_cache,
    scan_project,
)


class TestCoreIndexerCacheNative(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.manuscript = self.root / "Manuscripts" / "Book1"
        self.manuscript.mkdir(parents=True, exist_ok=True)
        self.world = self.root / "Universes" / "Cosmos"
        self.world.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_prose_metrics_computation(self) -> None:
        text = (
            "@status: in-progress\n"
            "This is the first chapter of the great saga. "
            "\"Speak softly,\" whispered the ancient traveler to [[Eldrin]].\n\n"
            "Second paragraph contains another line of dialogue: \"Never!\" he cried."
        )
        metrics, directives, wikilinks = compute_prose_metrics(text)
        self.assertIsInstance(metrics, ProseMetrics)
        self.assertGreater(metrics.total_words, 15)
        self.assertEqual(metrics.paragraph_count, 2)
        self.assertGreater(metrics.dialogue_words, 0)
        self.assertGreater(metrics.reading_minutes, 0.0)
        self.assertEqual(directives.get("status"), "in-progress")
        self.assertEqual(len(wikilinks), 1)
        self.assertIsInstance(wikilinks[0], WikilinkRef)
        self.assertEqual(wikilinks[0].target, "Eldrin")

    def test_diff_paragraphs_fast(self) -> None:
        f1 = self.manuscript / "v1.md"
        f1.write_text("Paragraph 1 unchanged.\n\nParagraph 2 will change.\n\nParagraph 3 unchanged.", encoding="utf-8")
        f2 = self.manuscript / "v2.md"
        f2.write_text("Paragraph 1 unchanged.\n\nParagraph 2 has changed substantially.\n\nParagraph 3 unchanged.", encoding="utf-8")

        idx = VaultIndex(self.root)
        doc1 = idx.get_document(f1)
        doc2 = idx.get_document(f2)

        diff = idx.diff_paragraphs_fast(doc1, doc2)
        self.assertEqual(diff["unchanged_paragraphs"], 2)
        self.assertEqual(diff["added_paragraphs"], 1)
        self.assertEqual(diff["removed_paragraphs"], 1)
        self.assertGreater(diff["net_word_delta"], 0)

    def test_vault_index_building_and_search(self) -> None:
        ch1 = self.manuscript / "01_intro.md"
        ch1.write_text(
            "---\ntitle: The Beginning\ntags: [prologue, magic]\n---\n\n"
            "The journey began in [[Silverhold]]. The archmage met [[Eldrin|Master Eldrin]].\n"
            "Spells echoed in the chamber.",
            encoding="utf-8",
        )
        lore = self.world / "Silverhold.md"
        lore.write_text(
            "---\ntitle: Silverhold City\n---\n\n"
            "Silverhold is the capital of the realm.",
            encoding="utf-8",
        )

        idx = VaultIndex(self.root)
        nodes = idx.scan_vault()
        node_paths = [n.relative_path for n in nodes]

        self.assertTrue(any("01_intro.md" in p for p in node_paths))
        self.assertTrue(any("Silverhold.md" in p for p in node_paths))

        # Test wikilink extraction
        intro_node = next(n for n in nodes if "01_intro.md" in n.relative_path)
        self.assertIsInstance(intro_node, VaultDocumentNode)
        targets = [w.target for w in intro_node.wikilinks]
        self.assertIn("Silverhold", targets)
        self.assertIn("Eldrin", targets)
        self.assertEqual(next(w.alias for w in intro_node.wikilinks if w.target == "Eldrin"), "Master Eldrin")

    def test_cache_engine_persistence_and_invalidation(self) -> None:
        ch1 = self.manuscript / "ch1.md"
        ch1.write_text("One two three four five.", encoding="utf-8")

        cache_path = get_cache_path(str(self.root))
        self.assertEqual(cache_path, self.root / CACHE_FILENAME)

        # Initial scan
        scan_res = scan_project(str(self.root))
        files_data = scan_res.get("files", {})
        self.assertIn("Manuscripts/Book1/ch1.md", [p.replace("\\", "/") for p in files_data])
        item = next(v for k, v in files_data.items() if "ch1.md" in k)
        self.assertEqual(item["word_count"], 5)

        # Save cache
        save_success = save_cache(str(self.root), {"version": 2, "files": files_data})
        self.assertTrue(save_success)
        self.assertTrue(cache_path.exists())

        # Load cache
        loaded = load_cache(str(self.root))
        self.assertEqual(loaded.get("version"), 2)
        self.assertIn("Manuscripts/Book1/ch1.md", [p.replace("\\", "/") for p in loaded.get("files", {})])

    def test_data_access_layer_caching(self) -> None:
        ch1 = self.manuscript / "scene.md"
        ch1.write_text("# Scene 1\nProse content for testing DAL.", encoding="utf-8")

        dal = get_data_access()
        self.assertIsInstance(dal, DataAccessLayer)

        # Access file and check caching
        content = dal.read_file(ch1)
        self.assertIn("Prose content", content)
        wc = dal.get_word_count(ch1)
        self.assertGreater(wc, 0)

        listed = dal.list_files(self.manuscript)
        self.assertTrue(any(f.name == "scene.md" for f in listed))

    def test_tag_extraction_and_word_counts(self) -> None:
        raw = "@POV: Elena\n@status: draft\n@location: Silverhold"
        tags = extract_tags(raw)
        self.assertEqual(tags.get("pov"), ["Elena"])
        self.assertEqual(tags.get("status"), ["draft"])
        self.assertEqual(tags.get("location"), ["Silverhold"])

        count = count_words("First, second, third; fourth—fifth.")
        self.assertEqual(count, 5)

        prose_count = count_prose_words("Word one <!-- comment ignored --> word two.")
        self.assertEqual(prose_count, 4)

    def test_indexer_and_cache_cli_and_helpers(self) -> None:
        ch1 = self.manuscript / "cli_test.md"
        ch1.write_text("# Chapter Test\nSome prose text here for counting.", encoding="utf-8")

        parsed = parse_markdown_file(ch1)
        self.assertGreater(parsed.get("word_count", 0), 0)

        wc_summary = compute_wordcounts(str(self.root))
        self.assertGreater(wc_summary.get("total_words", 0), 0)

        # Test indexer_main CLI
        exit_code = indexer_main([str(self.root)])
        self.assertEqual(exit_code, 0)

        # Test cache_main CLI
        exit_code_cache = cache_main(["scan", str(self.root)])
        self.assertEqual(exit_code_cache, 0)


if __name__ == "__main__":
    unittest.main()
