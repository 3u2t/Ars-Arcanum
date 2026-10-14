"""Comprehensive unit test suite for Phases 2 & 3 Refactors and All 5 Worldbuilder Feature Engines.

Tests:
1. `diff_core.py`: Two-level SHA-256 paragraph-hash diffing, Scrap extraction (>=50 words),
   and OS hardlink draft promotion (`promote_draft_hardlinked`) with `.locked` parent seal.
2. `typed_constitution.py`: 3-tier policy cascade with `!RULE_ID` negation override and frozen dataclasses.
3. `docx_tracked_changes.py`: Bidirectional Markdown CriticMarkup <-> OpenXML `<w:ins>`, `<w:del>`,
   and `<w:comment>` conversion inside `.docx` ZIP packages.
4. `plugin_sandbox.py`: Isolated `python -I` subprocess execution, timeout enforcement, and path traversal block.
5. `epistemic_firewall.py`: Chronological POV spoiler leak detection (`EPI-201`), mythic framing (`EPI-202`),
   and unresolved reveal warnings (`EPI-203`).
6. `timeline_solver.py`: Non-Gregorian calendar conversion, Sand Sea caravan travel speed checks (`TIME-301`),
   temporal regression (`TIME-302`), and Lorentz relativistic time dilation.
7. `conlang_linter.py`: Zero-dependency PolyGlot `.pgd` ZIP/XML dictionary import, phonotactic cluster/hiatus
   validation (`CON-401`, `CON-402`), and Markdown pronunciation glossary generation.
8. `resource_ledger.py`: Hard magic / Sci-Fi resource deficit (`LED-501`) and overflow cap (`LED-502`) auditing.
9. `narrative_braid.py`: POV word-share analytics, drought detection (`BRD-601`), and CSP-locked SVG/HTML output.

Repository Target: `tests/test_phases2_3_and_features.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

# Ensure `scripts/lib` is importable whether run from repo root or `tests/`
_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIB_DIR = _REPO_ROOT / "scripts" / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from conlang_linter import (
    PhonotacticSpec,
    audit_conlang_terms,
    compile_glossary_markdown,
    import_polyglot_lexicon,
)
from diff_core import compare_chapter_hierarchical, promote_draft_hardlinked
from docx_tracked_changes import export_markdown_to_docx, pull_docx_to_markdown
from epistemic_firewall import (
    ChapterEpistemicEvent,
    CharacterKnowledgeBaseline,
    audit_epistemic_continuity,
)
from narrative_braid import ChapterBraidNode, analyze_narrative_braid, render_braid_html
from plugin_sandbox import PluginExecutionError, run_plugin_sandboxed
from resource_ledger import ChapterResourceDelta, ResourcePoolSpec, audit_resource_conservation
from timeline_solver import (
    CharacterTimelineEvent,
    CustomCalendarSpec,
    RouteEdge,
    audit_timeline_and_routes,
    compute_relativistic_proper_days,
)
from typed_constitution import resolve_constitution_cascade
from vault_index import PathSecurityError, atomic_write


class TestPhases2And3Refactors(unittest.TestCase):
    """Tests for Phase 2 & 3 architectural refactor modules."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_hierarchical_diff_and_scrap_extraction(self) -> None:
        long_cut = " ".join(f"word{i}" for i in range(60))
        old_md = f"---\ntitle: Ch 1\n---\nUnchanged opening paragraph.\n\n{long_cut}\n\nThird paragraph old text.\n"
        new_md = "---\ntitle: Ch 1\n---\nUnchanged opening paragraph.\n\nThird paragraph new revised text here.\n"

        scraps_dir = self.root / "Scraps"
        report = compare_chapter_hierarchical(
            "01_Chapter",
            old_md,
            new_md,
            scraps_dir=scraps_dir,
            vault_root=self.root,
            min_scrap_words=50,
        )
        self.assertEqual(report.unchanged_paragraphs, 1)
        self.assertEqual(len(report.scraps_extracted), 1)
        self.assertTrue(Path(report.scraps_extracted[0]).exists())
        self.assertGreater(report.words_deleted, 55)

    def test_promote_draft_hardlinked_and_parent_lock(self) -> None:
        d1_chap = self.root / "Draft-01" / "01_Act_I" / "01_Chapter.md"
        atomic_write(d1_chap, "Draft 1 canonical text.")

        meta = promote_draft_hardlinked(
            self.root,
            "Draft-01",
            "Draft-02",
            milestone_tag="Structural Edit",
            lock_parent=True,
        )
        self.assertEqual(meta["hardlinked_files"], 1)
        self.assertTrue((self.root / "Draft-01" / ".locked").exists())
        d2_chap = self.root / "Draft-02" / "01_Act_I" / "01_Chapter.md"
        self.assertTrue(d2_chap.exists())

        # Atomic edit in Draft-02 must not mutate locked Draft-01
        atomic_write(d2_chap, "Draft 2 updated text.")
        self.assertEqual(d1_chap.read_text(encoding="utf-8"), "Draft 1 canonical text.")

    def test_typed_constitution_cascade_with_rule_negation(self) -> None:
        global_cfg = {"rules": ["REV-101", "REV-102", "EPI-201"], "banned_idioms": ["suddenly", "very"]}
        world_cfg = {"rules": ["!REV-101", "TIME-301"], "banned_idioms": ["!very", "literally"]}
        manuscript_cfg = {
            "scope_name": "Prisoner of Sand Sea",
            "rules": ["!EPI-201"],
            "thresholds": {"max_pov_drought_words": 18_000},
        }
        resolved = resolve_constitution_cascade(
            global_dict=global_cfg,
            world_dict=world_cfg,
            manuscript_dict=manuscript_cfg,
        )
        self.assertEqual(resolved.scope_name, "Prisoner of Sand Sea")
        self.assertFalse(resolved.is_rule_enabled("REV-101"))
        self.assertFalse(resolved.is_rule_enabled("EPI-201"))
        self.assertTrue(resolved.is_rule_enabled("REV-102"))
        self.assertTrue(resolved.is_rule_enabled("TIME-301"))
        self.assertEqual(resolved.banned_idioms, ("literally", "suddenly"))
        self.assertEqual(resolved.thresholds.max_pov_drought_words, 18_000)

    def test_docx_tracked_changes_roundtrip(self) -> None:
        source_md = (
            "# Chapter 1: The Glass Dunes\n\n"
            "Kael drew his {--rusted--}{++sun-forged++} blade{>>Editor: Great imagery!<<} across the sand.\n"
        )
        docx_file = self.root / "Export" / "ch1_tracked.docx"
        export_markdown_to_docx(source_md, docx_file, vault_root=self.root, author="Aryan")
        self.assertTrue(docx_file.exists())

        roundtrip_md = pull_docx_to_markdown(docx_file, vault_root=self.root)
        self.assertIn("# Chapter 1: The Glass Dunes", roundtrip_md)
        self.assertIn("{--rusted--}", roundtrip_md)
        self.assertIn("{++sun-forged++}", roundtrip_md)
        self.assertIn("{>>Editor: Great imagery!<<}", roundtrip_md)

    def test_plugin_sandbox_isolation_and_security(self) -> None:
        plugin_dir = self.root / ".arcanum" / "plugins"
        good_plugin = plugin_dir / "name_gen.py"
        atomic_write(
            good_plugin,
            "import json, sys\n"
            "data = json.loads(sys.stdin.read())\n"
            "print(json.dumps({'status': 'ok', 'generated': data.get('prefix', '') + 'thos'}))\n",
        )
        res = run_plugin_sandboxed(
            good_plugin,
            {"prefix": "Kael"},
            allowed_roots=(plugin_dir,),
            timeout_seconds=3.0,
        )
        self.assertEqual(res.status, "ok")
        self.assertEqual(res.output["generated"], "Kaelthos")

        outside_plugin = self.root.parent / "rogue.py"
        with self.assertRaises(PathSecurityError):
            run_plugin_sandboxed(outside_plugin, {}, allowed_roots=(plugin_dir,))

        bad_plugin = plugin_dir / "broken.py"
        atomic_write(bad_plugin, "import sys; sys.exit(2)\n")
        with self.assertRaises(PluginExecutionError):
            run_plugin_sandboxed(bad_plugin, {}, allowed_roots=(plugin_dir,))


class TestSpeculativeWorldbuilderEngines(unittest.TestCase):
    """Tests for Features 2–6 (Epistemic Firewall, Timeline Solver, Conlang Linter, Resource Ledger, Braid)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_epistemic_firewall_catches_premature_spoiler_leak(self) -> None:
        characters = [
            CharacterKnowledgeBaseline("Kael", frozenset({"desert_routes"})),
            CharacterKnowledgeBaseline("Lyra", frozenset({"imperial_code"})),
        ]
        chapters = [
            ChapterEpistemicEvent(
                chapter_index=2,
                chapter_title="The Oasis Ambush",
                pov_character="Kael",
                referenced_facts=("desert_routes", "emperor_true_heir"),  # Leak! Learned in Ch 8
                learned_facts=(),
                asserted_objective_facts=("sun_god_creation_myth",),
            ),
            ChapterEpistemicEvent(
                chapter_index=8,
                chapter_title="Vault of Whispers",
                pov_character="Kael",
                referenced_facts=("emperor_true_heir",),
                learned_facts=("emperor_true_heir", "orphan_secret"),
            ),
        ]
        report = audit_epistemic_continuity(
            characters=characters,
            chapters=chapters,
            mythic_unreliable_facts=frozenset({"sun_god_creation_myth"}),
        )
        self.assertFalse(report.passed)
        rule_ids = [v.rule_id for v in report.violations]
        self.assertIn("EPI-201", rule_ids)
        self.assertIn("EPI-202", rule_ids)
        self.assertIn("EPI-203", rule_ids)

    def test_custom_calendar_and_sand_sea_route_physics(self) -> None:
        reliquary_cal = CustomCalendarSpec(
            calendar_name="Reliquary Solar Reckoning",
            month_names=tuple(f"Month-{i}" for i in range(1, 11)),
            month_lengths=(36,) * 10,  # 360 days/year
        )
        self.assertEqual(reliquary_cal.days_per_year, 360)

        routes = [
            RouteEdge(
                origin="Sunken Citadel",
                destination="Glass Oasis",
                distance_km=240.0,
                terrain="sand_sea",  # 40 km/d * 0.60 = 24 km/d -> requires 10 days minimum
            )
        ]
        events = [
            CharacterTimelineEvent(1, "Kael", "Sunken Citadel", 1042, 1, 1, "camel_caravan"),
            CharacterTimelineEvent(2, "Kael", "Glass Oasis", 1042, 1, 4, "camel_caravan"),  # Only 3 days elapsed!
        ]
        audit = audit_timeline_and_routes(calendar=reliquary_cal, routes=routes, events=events)
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["anomalies"][0]["rule_id"], "TIME-301")

        # Relativistic time dilation check (v = 0.8c -> factor 0.6)
        proper = compute_relativistic_proper_days(100.0, 0.8)
        self.assertAlmostEqual(proper, 60.0, places=2)

    def test_polyglot_conlang_importer_and_phonotactic_linter(self) -> None:
        pgd_path = self.root / "sand_tongue.pgd"
        sample_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<dictionary><lexicon>"
            "<word><conWord>kaelthos</conWord><localWord>sun-blade</localWord>"
            "<proc>ka.ɛl.θos</proc><wordTypeId>noun</wordTypeId><etymology>kael + thos</etymology></word>"
            "</lexicon></dictionary>"
        )
        with zipfile.ZipFile(pgd_path, "w") as zf:
            zf.writestr("PGDictionary.xml", sample_xml.encode("utf-8"))

        lexemes = import_polyglot_lexicon(pgd_path)
        self.assertEqual(len(lexemes), 1)
        self.assertEqual(lexemes[0].con_word, "kaelthos")

        glossary_md = compile_glossary_markdown("Sand Tongue", lexemes)
        self.assertIn("| **kaelthos** | `/ka.ɛl.θos/` |", glossary_md)

        spec = PhonotacticSpec(
            language_name="Sand Tongue",
            allowed_consonants=("k", "l", "th", "s", "r", "n"),
            allowed_vowels=("a", "e", "o"),
            banned_clusters=("sr",),
            allow_vowel_hiatus=False,
        )
        res = audit_conlang_terms(["kales", "kaelthos", "sraX"], spec)
        self.assertFalse(res["passed"])
        violated_rules = {v["rule_id"] for v in res["violations"]}
        self.assertIn("CON-401", violated_rules)  # 'x' not in phoneme inventory
        self.assertIn("CON-402", violated_rules)  # vowel hiatus 'ae' & banned cluster 'sr'

    def test_hard_magic_resource_conservation_ledger(self) -> None:
        pools = [
            ResourcePoolSpec("Kael", "ether_vials", initial_value=3.0, min_bound=0.0, max_bound=5.0, unit="vials")
        ]
        deltas = [
            ChapterResourceDelta(1, "Dune Crossing", "Kael", "ether_vials", -2.0, "Sandstorm ward"),
            ChapterResourceDelta(2, "Citadel Siege", "Kael", "ether_vials", -2.0, "Overcharged glyph"),
        ]
        res = audit_resource_conservation(pools=pools, deltas=deltas)
        self.assertFalse(res["passed"])
        self.assertEqual(res["violations"][0]["rule_id"], "LED-501")
        self.assertEqual(res["violations"][0]["balance_after"], -1.0)

    def test_narrative_braid_drought_and_svg_render(self) -> None:
        chapters = [
            ChapterBraidNode(1, "Ch 1", "Kael", ("Citadel",), 4_000, 0.35, 6),
            ChapterBraidNode(2, "Ch 2", "Lyra", ("Court",), 15_000, 0.45, 7),
            ChapterBraidNode(3, "Ch 3", "Lyra", ("Court",), 14_000, 0.40, 8),
            ChapterBraidNode(4, "Ch 4", "Kael", ("Citadel",), 5_000, 0.30, 9),
        ]
        html_path = self.root / "braid.html"
        rendered = render_braid_html(chapters, html_path, max_drought_words=25_000)
        self.assertTrue(html_path.exists())
        self.assertIn("BRD-601", rendered)
        self.assertIn("Content-Security-Policy", rendered)

        analysis = analyze_narrative_braid(chapters, max_drought_words=25_000)
        self.assertEqual(len(analysis["drought_alerts"]), 1)
        self.assertEqual(analysis["drought_alerts"][0]["absent_words"], 29_000)


if __name__ == "__main__":
    unittest.main()
