"""Unit and integration tests for the expanded Eldoria-Cosmos & Sample Fixtures Showcase."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"
for _p in (str(REPO_ROOT), str(SCRIPTS_DIR), str(LIB_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from conlang_linter import PhonotacticSpec, audit_conlang_terms, import_polyglot_lexicon
from diff_core import compare_chapter_hierarchical
from epistemic_firewall import (
    ChapterEpistemicEvent,
    CharacterKnowledgeBaseline,
    audit_epistemic_continuity,
)
from phase_effort_engine import PhaseEffortLedger
from resource_ledger import ChapterResourceDelta, ResourcePoolSpec, audit_resource_conservation
from timeline_solver import CharacterTimelineEvent, CustomCalendarSpec, RouteEdge, audit_timeline_and_routes
from vault_index import VaultIndex


class TestSampleProjectsShowcase(unittest.TestCase):
    """Verifies that `Eldoria-Cosmos` demonstrates all continuity, conlang, diff, and effort features."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.eldoria_src = REPO_ROOT / "templates" / "demo-cosmos" / "Eldoria-Cosmos"
        self.eldoria_copy = Path(self._tmp.name) / "Eldoria-Cosmos"
        shutil.copytree(self.eldoria_src, self.eldoria_copy)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_eldoria_cosmos_vault_index_and_effort_ledger(self) -> None:
        index = VaultIndex(self.eldoria_copy)
        nodes = index.scan_vault()
        self.assertGreaterEqual(len(nodes), 15)

        ledger = PhaseEffortLedger(self.eldoria_copy)
        sessions = ledger.load_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertEqual(sum(s.effort_points for s in sessions), 4200.0)
        self.assertTrue(sessions[1].premature_revision_blocked)

    def test_eldoria_polyglot_conlang_and_draft_diff_showcase(self) -> None:
        xml_path = self.eldoria_copy / "Eldoria-Prime" / "Languages" / "High-Eldorian.xml"
        lexemes = import_polyglot_lexicon(xml_path)
        self.assertEqual(len(lexemes), 3)

        spec = PhonotacticSpec(
            language_name="High Eldorian",
            allowed_consonants=("k", "l", "th", "s", "r", "n", "m", "v"),
            allowed_vowels=("a", "e", "i", "o", "u"),
            banned_clusters=("sr", "zt"),
            allow_vowel_hiatus=False,
        )
        res = audit_conlang_terms([lx.con_word for lx in lexemes], spec)
        self.assertTrue(res["passed"], f"Conlang check failed: {res}")

        ch1_d1 = (
            self.eldoria_copy
            / "Manuscripts"
            / "The-Silver-Chronicles"
            / "Book-01"
            / "Draft-01"
            / "01_Chapter_01.md"
        ).read_text(encoding="utf-8")
        ch1_d2 = (
            self.eldoria_copy
            / "Manuscripts"
            / "The-Silver-Chronicles"
            / "Book-01"
            / "Draft-02"
            / "01_Chapter_01.md"
        ).read_text(encoding="utf-8")
        diff_rep = compare_chapter_hierarchical("01_Chapter_01", ch1_d1, ch1_d2)
        self.assertGreaterEqual(diff_rep.unchanged_paragraphs, 1)
        self.assertGreaterEqual(diff_rep.modified_paragraphs, 1)

    def test_eldoria_continuity_engines_pass_cleanly(self) -> None:
        cal = CustomCalendarSpec("Eldorian Celestial Reckoning", tuple(f"M{i}" for i in range(1, 11)), (36,) * 10)
        routes = [RouteEdge("High Sanctuary", "Whispering Vale", 120.0, "mountain_pass")]
        events = [
            CharacterTimelineEvent(1, "Aeloria Vael", "High Sanctuary", 1042, 1, 1, "horse_mounted"),
            CharacterTimelineEvent(3, "Aeloria Vael", "Whispering Vale", 1042, 1, 6, "horse_mounted"),
        ]
        t_res = audit_timeline_and_routes(calendar=cal, routes=routes, events=events)
        self.assertTrue(t_res["passed"])

        e_res = audit_epistemic_continuity(
            characters=[CharacterKnowledgeBaseline("Aeloria Vael", frozenset({"aether_basic_cadence", "high_sanctuary_layout"}))],
            chapters=[
                ChapterEpistemicEvent(1, "Ch 1", "Aeloria Vael", ("aether_basic_cadence",), ("vale_beacon_signal",)),
                ChapterEpistemicEvent(3, "Ch 3", "Aeloria Vael", ("vale_beacon_signal",), ()),
            ],
        )
        self.assertTrue(e_res.passed)

        l_res = audit_resource_conservation(
            pools=[ResourcePoolSpec("Aeloria Vael", "aether_vials", 5.0)],
            deltas=[
                ChapterResourceDelta(1, "Ch 1", "Aeloria Vael", "aether_vials", -1.0),
                ChapterResourceDelta(3, "Ch 3", "Aeloria Vael", "aether_vials", -2.0),
            ],
        )
        self.assertTrue(l_res["passed"])
        self.assertEqual(l_res["final_balances"]["Aeloria Vael::aether_vials"], 2.0)


if __name__ == "__main__":
    unittest.main()
