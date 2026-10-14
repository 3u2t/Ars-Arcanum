"""Unit and integration test suite for `vault_index.py` (Phase 1 Refactor) and `phase_effort_engine.py`.

Follows Ars Arcanum's canonical testing contract (`AGENTS.md` / `tests/`):
- Pure Python standard library `unittest` runner (zero third-party pip packages).
- Verifies path traversal defense (`is_safe_subpath`), atomic writes (`atomic_write`),
  multiline YAML block scalar parsing (`|` and `>`), multi-paragraph dialogue detection,
  $O(1)$ mtime cache hits, hierarchical paragraph diffing, and Phase-Aware Effort Multipliers.

Repository Target: `tests/test_phase1_and_effort.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import sys
import tempfile
import unittest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIB_DIR = _REPO_ROOT / "scripts" / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from phase_effort_engine import (
    BookProjectSpec,
    PhaseEffortLedger,
    ProjectStage,
    evaluate_session_effort,
)
from vault_index import (
    PathSecurityError,
    VaultIndex,
    atomic_write,
    compute_prose_metrics,
    is_safe_subpath,
    parse_frontmatter,
)


class TestVaultIndexAndParsers(unittest.TestCase):
    """Tests for Phase 1 Unified VaultIndex, frontmatter block scalars, and prose metrics."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.vault_root = Path(self._tmp.name) / "ReliquaryVault"
        self.vault_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_is_safe_subpath_blocks_traversal(self) -> None:
        inside = self.vault_root / "Characters" / "kael.md"
        outside = self.vault_root.parent / "escaped.md"
        self.assertTrue(is_safe_subpath(self.vault_root, inside))
        self.assertFalse(is_safe_subpath(self.vault_root, outside))

        index = VaultIndex(self.vault_root)
        with self.assertRaises(PathSecurityError):
            list(index.iter_markdown_files(outside))

    def test_atomic_write_preserves_hardlinked_draft_snapshots(self) -> None:
        draft_01 = self.vault_root / "Draft-01" / "01_Chapter.md"
        draft_02 = self.vault_root / "Draft-02" / "01_Chapter.md"
        atomic_write(draft_01, "Original Draft 1 text.")
        draft_02.parent.mkdir(parents=True, exist_ok=True)
        os.link(draft_01, draft_02)

        # Updating Draft-02 via atomic_write must break the hardlink without mutating Draft-01
        atomic_write(draft_02, "Revised Draft 2 text.")
        self.assertEqual(draft_01.read_text(encoding="utf-8"), "Original Draft 1 text.")
        self.assertEqual(draft_02.read_text(encoding="utf-8"), "Revised Draft 2 text.")

    def test_parse_frontmatter_multiline_block_scalars_and_lists(self) -> None:
        sample = (
            "---\n"
            "title: Prisoner of Sand Sea\n"
            "chapter: 1\n"
            "canonical: true\n"
            "summary: |\n"
            "  Across the glass dunes of Reliquary,\n"
            "  a lone caravan seeks the sunken citadel.\n"
            "folded_note: >-\n"
            "  This folded lore note\n"
            "  becomes a single line.\n"
            "knows:\n"
            "  - sand_sea_treaty\n"
            "  - sunstone_cipher\n"
            "state_delta:\n"
            "  ether_vials: -1\n"
            "  water_liters: 12.5\n"
            "---\n"
            "The wind howled across the dunes.\n"
        )
        fm, body = parse_frontmatter(sample)
        self.assertEqual(fm["title"], "Prisoner of Sand Sea")
        self.assertEqual(fm["chapter"], 1)
        self.assertIs(fm["canonical"], True)
        self.assertEqual(
            fm["summary"],
            "Across the glass dunes of Reliquary,\na lone caravan seeks the sunken citadel.",
        )
        self.assertEqual(fm["folded_note"], "This folded lore note becomes a single line.")
        self.assertEqual(fm["knows"], ["sand_sea_treaty", "sunstone_cipher"])
        self.assertEqual(fm["state_delta"], {"ether_vials": -1, "water_liters": 12.5})
        self.assertEqual(body.strip(), "The wind howled across the dunes.")

    def test_compute_prose_metrics_multipara_dialogue_and_code_wikilinks(self) -> None:
        prose = (
            "@pov: Kael\n"
            "@location: Glass Dunes\n\n"
            '"Listen closely, because I will not repeat the oath across two paragraphs,\n\n'
            '"Even when the storm rises," Kael finished.\n\n'
            "He sheathed his blade beside [[Sunken Citadel#Gatehouse|the Citadel Gate]] "
            "{--old cut words--}{++newly forged++}.\n\n"
            "```\n"
            "[[IgnoredCodeLink]]\n"
            "```\n"
        )
        metrics, directives, wikilinks = compute_prose_metrics(prose)
        self.assertEqual(directives["pov"], "Kael")
        self.assertEqual(directives["location"], "Glass Dunes")
        self.assertEqual(len(wikilinks), 1)
        self.assertEqual(wikilinks[0].target, "Sunken Citadel")
        self.assertEqual(wikilinks[0].heading, "Gatehouse")
        self.assertEqual(wikilinks[0].alias, "the Citadel Gate")
        self.assertGreater(metrics.dialogue_words, 12)
        self.assertEqual(metrics.total_words, metrics.dialogue_words + metrics.narrative_words)

    def test_vault_index_excludes_system_dirs_and_persists_cache(self) -> None:
        chap1 = self.vault_root / "Book-01" / "Draft-01" / "01_Chapter.md"
        backup_file = self.vault_root / "Backups" / "old_backup.md"
        obsidian_file = self.vault_root / ".obsidian" / "workspace.md"

        atomic_write(chap1, "---\ntitle: Chapter One\n---\nFirst paragraph here.\n\nSecond paragraph here.\n")
        atomic_write(backup_file, "Should be ignored.")
        atomic_write(obsidian_file, "Should be ignored.")

        index = VaultIndex(self.vault_root)
        nodes = index.scan_vault()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].relative_path, "Book-01/Draft-01/01_Chapter.md")
        self.assertTrue(index.cache_file.exists())

        # Reload from persistent cache and test fast paragraph diffing
        reloaded_index = VaultIndex(self.vault_root)
        cached_node = reloaded_index.get_document(chap1)
        self.assertEqual(cached_node.sha256, nodes[0].sha256)

        chap1_v2 = self.vault_root / "Book-01" / "Draft-02" / "01_Chapter.md"
        atomic_write(
            chap1_v2,
            "---\ntitle: Chapter One\n---\nFirst paragraph here.\n\nModified second paragraph with extra words.\n",
        )
        node_v2 = reloaded_index.get_document(chap1_v2)
        diff_summary = reloaded_index.diff_paragraphs_fast(cached_node, node_v2)
        self.assertEqual(diff_summary["unchanged_paragraphs"], 1)
        self.assertEqual(diff_summary["added_paragraphs"], 1)
        self.assertEqual(diff_summary["removed_paragraphs"], 1)
        self.assertEqual(diff_summary["net_word_delta"], 3)


class TestPhaseEffortEngine(unittest.TestCase):
    """Tests for Phase-Aware Effort Multipliers and Career Pipeline Telemetry."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_premature_revision_gets_zero_credit_during_drafting(self) -> None:
        # Revising during Drafting stage must earn 0.0x effort points and flag premature editing
        sess = evaluate_session_effort(
            session_date="2026-10-14",
            book_title="Prisoner of Sand Sea",
            universe="Reliquary",
            series="Sand Sea Saga",
            stage=ProjectStage.DRAFTING,
            worldbuilding_words=400,  # 400 * 0.50 = 200 pts
            outlining_words=200,  # 200 * 0.50 (off-phase) = 100 pts
            first_draft_words=1_700,  # 1700 * 1.00 = 1700 pts
            revision_words=1_500,  # 1500 * 0.00 (off-phase) = 0 pts
            minutes_spent=90.0,
        )
        self.assertEqual(sess.effort_points, 2_000.0)
        self.assertTrue(sess.goal_met)
        self.assertTrue(sess.premature_revision_blocked)
        self.assertEqual(sess.total_manuscript_words_added, 1_700)

    def test_on_phase_outlining_and_revision_weights(self) -> None:
        outline_sess = evaluate_session_effort(
            session_date="2026-10-14",
            book_title="Gothic Fantasy",
            stage=ProjectStage.PRE_DRAFT_OUTLINE,
            outlining_words=2_000,  # 1.00x during Pre-Draft Outline
        )
        self.assertEqual(outline_sess.effort_points, 2_000.0)
        self.assertTrue(outline_sess.goal_met)

        rev_sess = evaluate_session_effort(
            session_date="2026-10-14",
            book_title="Prisoner of Sand Sea",
            stage=ProjectStage.REVISION,
            revision_words=10_000,  # 10,000 * 0.20 = 2,000 pts during Revision stage
        )
        self.assertEqual(rev_sess.effort_points, 2_000.0)
        self.assertFalse(rev_sess.premature_revision_blocked)

    def test_career_dashboard_summary_and_forecasting(self) -> None:
        ledger = PhaseEffortLedger(self.workspace_root)
        books = [
            BookProjectSpec(
                book_title="Prisoner of Sand Sea",
                universe="Reliquary",
                series="Sand Sea Saga",
                book_type="Novel",
                stage=ProjectStage.CONCEPT,
                target_words=200_000,
                start_date="2027-01-01",
                deadline="2027-07-01",
            ),
            BookProjectSpec(
                book_title="Gothic Fantasy",
                universe="Reliquary",
                series="Gothic Fantasy Series",
                book_type="Novel",
                stage=ProjectStage.CONCEPT,
                target_words=200_000,
                start_date="2027-07-01",
                deadline="2028-01-01",
            ),
        ]

        s1 = evaluate_session_effort(
            session_date="2026-10-11",
            book_title="Prisoner of Sand Sea",
            universe="Reliquary",
            series="Sand Sea Saga",
            stage=ProjectStage.CONCEPT,
            first_draft_words=2_000,
        )
        ledger.append_session(s1)

        summary = ledger.build_dashboard_summary(books, reference_date=date(2026, 10, 11))
        self.assertEqual(summary.lifetime_career_words, 2_000)
        self.assertEqual(summary.universe_word_totals["Reliquary"], 2_000)
        self.assertEqual(summary.active_streak_days, 1)
        self.assertTrue(summary.daily_goal_met)
        self.assertEqual(summary.book_spotlight[0].actual_words, 2_000)
        self.assertEqual(summary.book_spotlight[0].progress_pct, 1.0)
        self.assertEqual(summary.book_spotlight[0].days_left, 181)
        self.assertEqual(summary.book_spotlight[0].required_daily_pace, 1_094)


if __name__ == "__main__":
    unittest.main()
