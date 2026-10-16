"""Unit tests for native Ars Arcanum manuscript velocity and portfolio engines.

Module: tests/test_manuscript_velocity_native.py
Contracts Tested:
- Deterministic Phase-Aware Effort Multipliers (Drafting, Outlining, Lore, Revisions).
- Path Traversal Defense on Ledger writes (PathSecurityError).
- Atomic sprint state file locking and sprint_log.jsonl ledger append.
- Cognitive velocity analytics and rolling 7d/30d habit streaks.
- Native Portfolio scanner and universe codex analyzer.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from src.arcanum.core.storage import PathSecurityError
from src.arcanum.manuscript.portfolio import (
    analyze_manuscript_project,
    analyze_universe_project,
    calculate_portfolio_velocity,
    format_portfolio_terminal,
    scan_portfolio,
)
from src.arcanum.manuscript.velocity import (
    BookProjectSpec,
    EffortMultiplierConfig,
    PhaseEffortLedger,
    ProjectStage,
    cancel_sprint,
    count_prose_words,
    evaluate_session_effort,
    format_stats_markdown,
    format_stats_table,
    get_velocity_metrics,
    log_manual_sprint,
    main as velocity_main,
    start_sprint,
    status_sprint,
    stop_sprint,
)


class TestManuscriptVelocityNative(unittest.TestCase):
    """Verifies native velocity and sprint orchestration in src/arcanum/manuscript/velocity.py."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="arcanum_test_velocity_"))
        self.ms_dir = self.tmp_dir / "Manuscript_Test"
        self.ms_dir.mkdir(parents=True, exist_ok=True)
        (self.ms_dir / "Chapter_01.md").write_text(
            "---\ntitle: Chapter 1\n---\n# Chapter One\n\nIt was a dark and stormy night across the dunes.",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_count_prose_words(self) -> None:
        text = """---
title: Test Note
tags: [lore, magic]
---
# Heading One

```python
def code():
    pass
```

<!-- HTML comment -->
% Typst comment
@tag:scene_anchor

This is the actual prose text of five words.
"""
        count = count_prose_words(text)
        self.assertEqual(count, 11)  # "Heading One This is the actual prose text of five words." = 11 words

    def test_evaluate_session_effort_drafting_and_premature_revision(self) -> None:
        # During Drafting stage: revision gets 0.00x multiplier and flags premature editing
        sess = evaluate_session_effort(
            session_date="2026-10-15",
            book_title="Dune Strider",
            stage=ProjectStage.DRAFTING,
            first_draft_words=1000,
            worldbuilding_words=200,  # 200 * 0.5 = 100
            outlining_words=100,  # off-phase = 100 * 0.5 = 50
            revision_words=500,  # off-phase = 0
            minutes_spent=60.0,
        )
        self.assertEqual(sess.effort_points, 1150.0)
        self.assertTrue(sess.premature_revision_blocked)
        self.assertEqual(sess.total_manuscript_words_added, 1000)
        self.assertEqual(sess.total_raw_words_logged, 1800)
        self.assertEqual(sess.words_per_hour, 1800.0)

    def test_evaluate_session_effort_revision_stage(self) -> None:
        cfg = EffortMultiplierConfig(daily_effort_goal=1500.0, on_phase_revision_weight=0.25)
        sess = evaluate_session_effort(
            session_date="2026-10-15",
            book_title="Dune Strider",
            stage=ProjectStage.REVISION,
            revision_words=6_000,  # 6,000 * 0.25 = 1500
            minutes_spent=120.0,
            config=cfg,
        )
        self.assertEqual(sess.effort_points, 1500.0)
        self.assertFalse(sess.premature_revision_blocked)
        self.assertTrue(sess.goal_met)

    def test_phase_effort_ledger_append_load_and_path_security(self) -> None:
        ledger = PhaseEffortLedger(self.ms_dir)
        sess = evaluate_session_effort(
            session_date="2026-10-15",
            book_title="Dune Strider",
            first_draft_words=500,
        )
        ledger.append_session(sess)

        loaded = ledger.load_sessions()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].book_title, "Dune Strider")
        self.assertEqual(loaded[0].first_draft_words, 500)

        # Test path traversal defense
        escaped_ledger = PhaseEffortLedger(self.ms_dir)
        escaped_ledger.ledger_path = self.tmp_dir.parent / "escaped_sprint_log.jsonl"
        with self.assertRaises(PathSecurityError):
            escaped_ledger.append_session(sess)

    def test_phase_effort_ledger_dashboard_summary(self) -> None:
        ledger = PhaseEffortLedger(self.ms_dir)
        books = [
            BookProjectSpec(
                book_title="Dune Strider",
                universe="Reliquary",
                series="Sand Sea",
                book_type="Novel",
                stage=ProjectStage.DRAFTING,
                target_words=100_000,
                start_date="2026-01-01",
                deadline="2026-12-31",
                initial_words=10_000,
            )
        ]
        sess = evaluate_session_effort(
            session_date="2026-10-15",
            book_title="Dune Strider",
            universe="Reliquary",
            series="Sand Sea",
            stage=ProjectStage.DRAFTING,
            first_draft_words=2000,
        )
        ledger.append_session(sess)

        summary = ledger.build_dashboard_summary(books, reference_date=date(2026, 10, 15))
        self.assertEqual(summary.lifetime_career_words, 12_000)
        self.assertEqual(summary.active_streak_days, 1)
        self.assertTrue(summary.daily_goal_met)
        self.assertEqual(len(summary.book_spotlight), 1)
        self.assertEqual(summary.book_spotlight[0].actual_words, 12_000)

    def test_sprint_lifecycle_and_metrics(self) -> None:
        # Start sprint
        res_start = start_sprint(self.ms_dir, target_words=600, minutes=30, interactive=False)
        self.assertEqual(res_start["status"], "started")
        self.assertEqual(res_start["target_words"], 600)

        # Cannot start duplicate without force
        with self.assertRaises(RuntimeError):
            start_sprint(self.ms_dir, target_words=800, minutes=20, interactive=False)

        # Query status
        status = status_sprint(self.ms_dir)
        self.assertEqual(status["status"], "active")
        self.assertEqual(status["target_words"], 600)

        # Stop sprint with manual words
        res_stop = stop_sprint(self.ms_dir, manual_words=650)
        self.assertEqual(res_stop["status"], "completed")
        self.assertEqual(res_stop["words_written"], 650)

        # Status is now inactive
        status_after = status_sprint(self.ms_dir)
        self.assertEqual(status_after["status"], "inactive")

        # Cancel on inactive
        res_cancel = cancel_sprint(self.ms_dir)
        self.assertEqual(res_cancel["status"], "inactive")

        # Log manual session
        res_log = log_manual_sprint(self.ms_dir, words=500, minutes=25.0)
        self.assertEqual(res_log["status"], "logged")

        # Velocity metrics
        metrics = get_velocity_metrics(self.ms_dir)
        self.assertEqual(metrics["total_sprint_sessions"], 2)
        self.assertEqual(metrics["total_sprint_words"], 1150)

        tbl = format_stats_table(metrics, title="Dune Strider")
        self.assertIn("Dune Strider", tbl)
        md = format_stats_markdown(metrics, title="Dune Strider")
        self.assertIn("Dune Strider", md)

    def test_velocity_cli_dispatch(self) -> None:
        # Test CLI effort command
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            rc = velocity_main([
                "effort",
                "--workspace", str(self.ms_dir),
                "--book", "Dune Strider",
                "--draft", "1500",
                "--minutes", "45",
            ])
            self.assertEqual(rc, 0)
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["first_draft_words"], 1500)
            self.assertEqual(data["effort_points"], 1500.0)


class TestManuscriptPortfolioNative(unittest.TestCase):
    """Verifies native portfolio scanning in src/arcanum/manuscript/portfolio.py."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="arcanum_test_portfolio_"))
        self.ms_dir = self.tmp_dir / "Novel_Alpha"
        self.ms_dir.mkdir(parents=True, exist_ok=True)
        (self.ms_dir / "manuscript.yaml").write_text(
            "title: Novel Alpha\nauthor: Jane Doe\nseries: Alpha Saga\ntarget_words: 50000\n",
            encoding="utf-8",
        )
        chap_dir = self.ms_dir / "Draft-01"
        chap_dir.mkdir(parents=True, exist_ok=True)
        (chap_dir / "01_Prologue.md").write_text("# Prologue\n\nWords words words words words.", encoding="utf-8")

        self.uni_dir = self.tmp_dir / "Universe_Alpha"
        self.uni_dir.mkdir(parents=True, exist_ok=True)
        (self.uni_dir / "universe.yaml").write_text("name: Alphaverse\ndescription: Epic cosmos\n", encoding="utf-8")
        loc_dir = self.uni_dir / "Locations"
        loc_dir.mkdir(parents=True, exist_ok=True)
        (loc_dir / "Citadel.md").write_text("# Citadel\n\nA great [[Tower]] stands tall.", encoding="utf-8")

    def tearDown(self) -> None:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_analyze_manuscript_and_universe(self) -> None:
        ms_report = analyze_manuscript_project(self.ms_dir)
        self.assertEqual(ms_report["title"], "Novel Alpha")
        self.assertEqual(ms_report["author"], "Jane Doe")
        self.assertEqual(ms_report["target_words"], 50000)
        self.assertGreater(ms_report["word_count"], 0)

        uni_report = analyze_universe_project(self.uni_dir)
        self.assertEqual(uni_report["name"], "Alphaverse")
        self.assertEqual(uni_report["total_notes"], 1)
        self.assertIn("Locations", uni_report["categories"])

        vel = calculate_portfolio_velocity([self.tmp_dir])
        self.assertIn("total_sessions", vel)
        self.assertIn("overall_wpm", vel)

    def test_scan_portfolio_and_format_terminal(self) -> None:
        report = scan_portfolio(self.tmp_dir)
        self.assertEqual(report["total_projects"], 1)
        self.assertEqual(report["total_universes"], 1)
        self.assertIn("Alpha Saga", report["series"])

        output = format_portfolio_terminal(report, show_tree=True)
        self.assertIn("Novel Alpha", output)
        self.assertIn("Alphaverse", output)
        self.assertIn("Series & Franchise Hierarchy", output)


if __name__ == "__main__":
    unittest.main()
