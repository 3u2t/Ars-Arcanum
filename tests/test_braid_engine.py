"""Comprehensive unit tests for native narrative braid engine.

Module: tests/test_braid_engine.py
Verifies: src.arcanum.manuscript.braid
- POV word-share calculations and pacing metrics.
- POV Drought detection (BRD-601).
- Dual-axis sorting (manuscript chapter order vs chronological timeline order).
- Air-gapped, CSP-locked HTML + SVG swimlane rendering.
- Directory vault scanning for directives and frontmatter.
- CLI execution.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.storage import atomic_write
from src.arcanum.manuscript.braid import (
    BraidDroughtAlert,
    ChapterBraidNode,
    analyze_narrative_braid,
    main,
    render_braid_html,
    scan_manuscript_braid,
)


class TestBraidEngine(unittest.TestCase):
    """Test suite for src.arcanum.manuscript.braid."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_analyze_narrative_braid_pacing_and_shares(self) -> None:
        chapters = [
            ChapterBraidNode(1, "Prologue", "Kaladin", ("Bridge Four",), 5000, 0.35, tension_score=6, chronological_order=1.0),
            ChapterBraidNode(2, "The Way of Kings", "Shallan", ("Ghostbloods",), 5000, 0.40, tension_score=5, chronological_order=2.0),
            ChapterBraidNode(3, "Highstorm", "Dalinar", ("Visions",), 10000, 0.20, tension_score=8, chronological_order=3.0),
        ]
        res = analyze_narrative_braid(chapters)
        self.assertEqual(res["total_words"], 20000)
        self.assertEqual(res["chapter_count"], 3)
        self.assertEqual(res["pov_word_totals"]["Kaladin"], 5000)
        self.assertEqual(res["pov_word_shares_pct"]["Kaladin"], 25.0)
        self.assertEqual(res["pov_word_shares_pct"]["Dalinar"], 50.0)
        self.assertEqual(len(res["drought_alerts"]), 0)

    def test_drought_alert_detection(self) -> None:
        chapters = [
            ChapterBraidNode(1, "Ch 1", "Lyra", (), 5000, 0.3),
            ChapterBraidNode(2, "Ch 2", "Corin", (), 15000, 0.3),
            ChapterBraidNode(3, "Ch 3", "Corin", (), 15000, 0.3),
            ChapterBraidNode(4, "Ch 4", "Lyra", (), 5000, 0.3),
        ]
        # Lyra is absent for 30,000 words between Ch 1 and Ch 4
        res = analyze_narrative_braid(chapters, max_drought_words=20000)
        self.assertEqual(len(res["drought_alerts"]), 1)
        alert = res["drought_alerts"][0]
        self.assertEqual(alert["rule_id"], "BRD-601")
        self.assertEqual(alert["thread_name"], "Lyra")
        self.assertEqual(alert["absent_words"], 30000)
        self.assertEqual(alert["from_chapter"], 1)
        self.assertEqual(alert["to_chapter"], 4)

        direct_alert = BraidDroughtAlert("BRD-601", "POV", "Lyra", 1, 4, 30000, "test")
        self.assertEqual(direct_alert.thread_name, "Lyra")

    def test_dual_axis_sorting(self) -> None:
        chapters = [
            ChapterBraidNode(1, "Flashforward", "Kaladin", (), 3000, 0.3, chronological_order=50.0),
            ChapterBraidNode(2, "Origins", "Kaladin", (), 4000, 0.3, chronological_order=1.0),
            ChapterBraidNode(3, "Midpoint", "Shallan", (), 5000, 0.3, chronological_order=25.0),
        ]

        ms_order = analyze_narrative_braid(chapters, sort_by="manuscript")
        self.assertEqual([c["chapter_index"] for c in ms_order["chapters"]], [1, 2, 3])

        chrono_order = analyze_narrative_braid(chapters, sort_by="chronological")
        self.assertEqual([c["chapter_index"] for c in chrono_order["chapters"]], [2, 3, 1])

    def test_render_braid_html_csp_and_svg(self) -> None:
        chapters = [
            ChapterBraidNode(1, "Ch 1", "Lyra", (), 3500, 0.3, chronological_order=1.0),
            ChapterBraidNode(2, "Ch 2", "Corin", (), 4500, 0.4, chronological_order=2.0),
        ]
        out_html = self.root / "braid.html"
        html_content = render_braid_html(chapters, out_html, sort_by="chronological")

        self.assertTrue(out_html.exists())
        self.assertIn("Content-Security-Policy", html_content)
        self.assertIn("default-src 'none'", html_content)
        self.assertIn("<svg", html_content)
        self.assertIn("Timeline: Day 1", html_content)
        self.assertIn("Chronological Story Order", html_content)

    def test_scan_manuscript_braid_vault(self) -> None:
        vault = self.root / "Novel"
        chap1 = vault / "01_Act_I" / "01_Ch.md"
        content1 = """---
title: The Storm
pov: Kaladin
subplots: [Slavery, Bridge Four]
tension: 7
timeline_day: 14.5
---
Kaladin looked at the sky.
"""
        atomic_write(chap1, content1)

        nodes = scan_manuscript_braid(vault)
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(node.chapter_title, "The Storm")
        self.assertEqual(node.pov_character, "Kaladin")
        self.assertEqual(node.subplots, ("Slavery", "Bridge Four"))
        self.assertEqual(node.tension_score, 7)
        self.assertEqual(node.chronological_order, 14.5)

    def test_cli_main(self) -> None:
        vault = self.root / "Novel"
        chap1 = vault / "01_Ch.md"
        atomic_write(chap1, "---\ntitle: The Opening\npov: Kaladin\n---\nSome words here.\n")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            ret = main([str(vault)])
        self.assertEqual(ret, 0)
        output = json.loads(stdout_buf.getvalue())
        self.assertEqual(output["chapter_count"], 1)


if __name__ == "__main__":
    unittest.main()
