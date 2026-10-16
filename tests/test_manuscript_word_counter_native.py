#!/usr/bin/env python3
"""
Unit tests for Native Ars Arcanum Unicode Prose Word Count & Telemetry (src/arcanum/manuscript/word_counter.py).
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.manuscript.scaffold import scaffold_manuscript, scaffold_universe, scaffold_world
from src.arcanum.manuscript.word_counter import (
    _is_interactive_tty,
    analyze_manuscript_words,
    count_prose_words_advanced,
    count_words_prose,
    format_ansi_velocity,
    format_words_markdown,
    format_words_table,
    main,
)
from src.arcanum.manuscript import (
    analyze_manuscript_words as ms_analyze_words,
    count_prose_words_advanced as ms_count_adv,
    count_words_prose as ms_count_prose,
    format_ansi_velocity as ms_format_ansi,
    format_words_markdown as ms_format_md,
    format_words_table as ms_format_tbl,
)


class TestManuscriptWordCounterNative(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="arcanum_test_words_native_"))
        self.univ_base = self.tmp_dir / "Universes"
        self.univ_base.mkdir(parents=True, exist_ok=True)

        scaffold_universe("NativeSaga", base_dir=self.univ_base)
        scaffold_world("NativeAvalon", universe_name="NativeSaga", base_dir=self.univ_base)
        res = scaffold_manuscript(
            "NativeSong",
            universe="NativeSaga",
            world="NativeAvalon",
            base_dir=self.univ_base,
            target_words=60000,
        )
        self.ms_dir = Path(res["path"])

    def tearDown(self) -> None:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_reexports(self) -> None:
        self.assertIn(_is_interactive_tty(), (True, False))
        self.assertIs(ms_analyze_words, analyze_manuscript_words)
        self.assertIs(ms_count_adv, count_prose_words_advanced)
        self.assertIs(ms_count_prose, count_words_prose)
        self.assertIs(ms_format_ansi, format_ansi_velocity)
        self.assertIs(ms_format_md, format_words_markdown)
        self.assertIs(ms_format_tbl, format_words_table)

    def test_count_advanced_and_cjk(self) -> None:
        text = 'She said, "The star is falling!" and ran towards the forest. 这是一段中文测试。'
        res = count_prose_words_advanced(text)
        self.assertGreater(res["total_words"], 0)
        self.assertGreater(res["cjk_characters"], 0)
        self.assertGreater(res["dialogue_words"], 0)
        self.assertGreater(res["dialogue_percentage"], 0.0)

    def test_analyze_manuscript(self) -> None:
        data = analyze_manuscript_words(self.ms_dir)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["title"], "NativeSong")
        self.assertEqual(data["target_words"], 60000)
        self.assertIn("chapters", data)
        self.assertIn("pov_distribution", data)

        tbl = format_words_table(data)
        self.assertIn("NativeSong", tbl)

        md = format_words_markdown(data)
        self.assertIn("# NativeSong", md)

    def test_cli_json(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            rc = main([str(self.ms_dir), "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["title"], "NativeSong")


if __name__ == "__main__":
    unittest.main()
