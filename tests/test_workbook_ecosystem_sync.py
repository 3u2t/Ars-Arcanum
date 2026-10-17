"""End-to-end verification suite for the integrated `Master_Writing_Ecosystem.xlsx` workbook and
live auto-synchronization engine (`scripts/lib/workbook_sync.py`).
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.lib.phase_effort_engine import PhaseEffortLedger, ProjectStage, evaluate_session_effort
from scripts.lib.vault_continuity_runner import run_full_vault_continuity_suite
from scripts.lib.workbook_sync import (
    DEFAULT_WORKBOOK_FILENAME,
    ContinuityBookTelemetry,
    WorldBibleVaultTelemetry,
    add_book_to_ecosystem,
    inspect_workbook_summary,
    main as workbook_main,
    sync_workbook,
    watch_workspace_and_sync,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestWorkbookEcosystemSync(unittest.TestCase):
    """Verifies the 8-sheet, 15-chart workbook structure and automatic workspace synchronization."""

    def test_root_and_template_workbook_integrity(self) -> None:
        root_wb = REPO_ROOT / DEFAULT_WORKBOOK_FILENAME
        tmpl_wb = REPO_ROOT / "templates" / "ecosystem" / DEFAULT_WORKBOOK_FILENAME
        self.assertTrue(root_wb.is_file(), "Root Master_Writing_Ecosystem.xlsx must exist")
        self.assertTrue(tmpl_wb.is_file(), "Template Master_Writing_Ecosystem.xlsx must exist")

        summary = inspect_workbook_summary(root_wb)
        self.assertEqual(summary["sheet_count"], 8)
        self.assertEqual(
            summary["sheets"],
            [
                "Dashboard",
                "Config",
                "Universes & Series",
                "My Books",
                "Daily Writing Log",
                "Calc",
                "Continuity & Compilers",
                "World Bible & Lore",
            ],
        )
        self.assertEqual(summary["charts_count"], 15)
        self.assertIn("All 8 integrity checks pass", summary["integrity_status"])
        self.assertEqual(summary["continuity_gate_status"], "PASS (CLEAN)")
        self.assertGreaterEqual(summary["total_world_bible_entities"], 90)

    def test_auto_populate_on_sprint_effort_and_add_book(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws_root = Path(tmp)
            shutil.copy2(REPO_ROOT / DEFAULT_WORKBOOK_FILENAME, ws_root / DEFAULT_WORKBOOK_FILENAME)

            # Custom series JSON test
            arcanum_dir = ws_root / ".arcanum"
            arcanum_dir.mkdir(parents=True, exist_ok=True)
            (arcanum_dir / "ecosystem_series.json").write_text(
                json.dumps(
                    [
                        {
                            "series_title": "Astral Loom Trilogy",
                            "universe": "Astral-Verse",
                            "planned_books": 3,
                            "premise_notes": "Hard-magic astral resonance trilogy",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            # 1. Add a new book via add_book_to_ecosystem
            res_add = add_book_to_ecosystem(
                ws_root,
                year=2027,
                book_title="Crown of the Astral Loom",
                book_type="Novel",
                universe="Astral-Verse",
                series="Astral Loom Trilogy",
                stage="Drafting",
                draft_target_words=160000,
                start_date="2026-10-16",
                deadline="2027-08-01",
            )
            self.assertEqual(res_add.books_synced, 7)
            self.assertEqual(res_add.series_synced, 6)
            self.assertEqual(res_add.charts_count, 15)

            # 2. Log a writing session via PhaseEffortLedger.append_session -> triggers auto_sync_workbook_if_present
            ledger = PhaseEffortLedger(ws_root)
            session = evaluate_session_effort(
                session_date="2026-10-16",
                book_title="Crown of the Astral Loom",
                universe="Astral-Verse",
                series="Astral Loom Trilogy",
                stage=ProjectStage.DRAFTING,
                worldbuilding_words=500,
                outlining_words=200,
                first_draft_words=2400,
                revision_words=0,
                minutes_spent=90.0,
                notes="Ch. 1 Astral Loom resonance chamber",
            )
            ledger.append_session(session)

            # Log a second session for an unregistered book to trigger auto-book & auto-series registration
            session2 = evaluate_session_effort(
                session_date="2026-10-16",
                book_title="Veil of Starlight",
                universe="Starlight-Verse",
                series="Starlight Cycle",
                stage=ProjectStage.REVISION,
                worldbuilding_words=100,
                outlining_words=0,
                first_draft_words=0,
                revision_words=1000,
                minutes_spent=60.0,
                notes="Revision pass",
            )
            ledger.append_session(session2)

            res_sync = sync_workbook(ws_root)
            self.assertEqual(res_sync.books_synced, 8)
            self.assertEqual(res_sync.sessions_synced, 2)
            self.assertEqual(res_sync.total_career_words, 4200)

    def test_continuity_suite_triggers_workbook_sync_and_cli_commands(self) -> None:
        # Telemetry helper branch checks
        c_pending = ContinuityBookTelemetry("Book A", "Reliquary", "Concept", indexed_docs=0)
        self.assertEqual(c_pending.status_label, "⚪ Pending Vault Scan")
        c_warn = ContinuityBookTelemetry("Book B", "Reliquary", "Drafting", indexed_docs=3, epi_issues=2)
        self.assertIn("2 Finding(s)", c_warn.status_label)
        w_empty = WorldBibleVaultTelemetry("Empty Series", "Reliquary")
        self.assertEqual(w_empty.health_label, "⚪ Empty Lore Vault")

        with tempfile.TemporaryDirectory() as tmp:
            ws_root = Path(tmp)
            res_init = sync_workbook(ws_root)
            self.assertTrue(Path(res_init.workbook_path).is_file())
            self.assertEqual(res_init.charts_count, 15)

            suite_out = run_full_vault_continuity_suite(ws_root, write_obsidian_dashboard=True)
            self.assertIn("workbook_synced", suite_out)

            # Test CLI status (JSON and human-readable)
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                rc = workbook_main(["status", "--workspace", str(ws_root), "--json"])
            self.assertEqual(rc, 0)
            status_payload = json.loads(buf.getvalue())
            self.assertEqual(status_payload["sheet_count"], 8)

            buf_txt = io.StringIO()
            with patch("sys.stdout", buf_txt):
                rc_txt = workbook_main(["status", "--workspace", str(ws_root)])
            self.assertEqual(rc_txt, 0)
            self.assertIn("[WORKBOOK STATUS]", buf_txt.getvalue())

            buf_sync = io.StringIO()
            with patch("sys.stdout", buf_sync):
                rc_sync = workbook_main(["sync", "--workspace", str(ws_root)])
            self.assertEqual(rc_sync, 0)
            self.assertIn("[WORKBOOK SYNCED]", buf_sync.getvalue())

            buf_err = io.StringIO()
            with patch("sys.stderr", buf_err):
                rc_err = workbook_main(["add-book", "--workspace", str(ws_root)])
            self.assertEqual(rc_err, 2)

            buf_add = io.StringIO()
            with patch("sys.stdout", buf_add):
                rc_add = workbook_main(
                    [
                        "add-book",
                        "--workspace",
                        str(ws_root),
                        "--title",
                        "Shadow of the Reliquary",
                        "--series",
                        "New Frontier Saga",
                        "--universe",
                        "Reliquary",
                        "--json",
                    ]
                )
            self.assertEqual(rc_add, 0)
            add_payload = json.loads(buf_add.getvalue())
            self.assertEqual(add_payload["books_synced"], 7)

            rc_watch = watch_workspace_and_sync(ws_root, interval_seconds=0.01, max_iterations=1)
            self.assertEqual(rc_watch, 0)


if __name__ == "__main__":
    unittest.main()
