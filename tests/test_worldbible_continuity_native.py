"""Unit tests for native Ars Arcanum World Bible continuity compilers.

Module: tests/test_worldbible_continuity_native.py
Contracts Tested:
- 3-Tier Policy Cascade with dynamic `!RULE_ID` negation directives.
- Epistemic POV & Spoiler Firewall forward DAG sweep (EPI-201..203).
- Custom Non-Gregorian Calendar arithmetic, Dijkstra route traversal, & Relativistic Dilation (TIME-301..302).
- Hard-Magic & Sci-Fi Resource Conservation simulation (LED-501..502).
- PolyGlot Conlang Phonotactics, Markdown Glossary, & SVG Derivation Tree (CON-401..402).
- Unified Vault Continuity Runner & Live Obsidian Diagnostics Callout generation.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from src.arcanum.worldbible.conlang import (
    ConlangLexeme,
    PhonotacticSpec,
    audit_conlang_terms,
    compile_glossary_markdown,
    render_etymology_tree_svg,
    validate_word_phonotactics,
)
from src.arcanum.worldbible.constitution import (
    AuthorialConstitution,
    CraftPolicyThresholds,
    merge_rule_lists_with_negation,
    resolve_constitution_cascade,
)
from src.arcanum.worldbible.epistemics import (
    ChapterEpistemicEvent,
    CharacterKnowledgeBaseline,
    audit_epistemic_continuity,
)
from src.arcanum.worldbible.ledger import (
    ChapterResourceDelta,
    ResourcePoolSpec,
    audit_resource_conservation,
)
from src.arcanum.worldbible.runner import (
    render_obsidian_diagnostics_markdown,
    run_full_vault_continuity_suite,
)
from src.arcanum.worldbible.timeline import (
    CharacterTimelineEvent,
    CustomCalendarSpec,
    RouteEdge,
    audit_timeline_and_routes,
    compute_relativistic_proper_days,
    compute_shortest_travel_days,
    render_orbital_calendar_svg,
)


class TestWorldBibleContinuityNative(unittest.TestCase):
    """Verifies all native worldbible continuity engines."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="arcanum_test_wb_"))
        self.vault_root = self.tmp_dir / "Vault"
        self.vault_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_constitution_cascade_and_negation(self) -> None:
        # Base constitution has 8 canonical rules
        base = AuthorialConstitution(scope_name="Base")
        self.assertTrue(base.is_rule_enabled("EPI-201"))
        self.assertTrue(base.is_rule_enabled("TIME-301"))

        # Negate TIME-301 in child tier
        merged_rules = merge_rule_lists_with_negation(base.active_rules, ["!TIME-301", "CUSTOM-01"])
        self.assertNotIn("TIME-301", merged_rules)
        self.assertIn("EPI-201", merged_rules)
        self.assertIn("CUSTOM-01", merged_rules)

        # 3-tier cascade resolution
        world_layer = {
            "scope_name": "CosmereWorld",
            "rules": ["!EPI-201"],
            "thresholds": {"max_chapter_words": 8000},
        }
        ms_layer = {
            "scope_name": "MistbornMS",
            "rules": ["!LED-501"],
            "thresholds": {"min_chapter_words": 1500},
        }
        resolved = resolve_constitution_cascade(
            world_dict=world_layer,
            manuscript_dict=ms_layer,
        )
        self.assertEqual(resolved.scope_name, "MistbornMS")
        self.assertFalse(resolved.is_rule_enabled("EPI-201"))
        self.assertFalse(resolved.is_rule_enabled("LED-501"))
        self.assertTrue(resolved.is_rule_enabled("TIME-301"))
        self.assertEqual(resolved.thresholds.max_chapter_words, 8000)
        self.assertEqual(resolved.thresholds.min_chapter_words, 1500)
        self.assertIsInstance(resolved.thresholds, CraftPolicyThresholds)

    def test_epistemic_firewall_dag_sweep(self) -> None:
        characters = [
            CharacterKnowledgeBaseline(character_name="Kael", initial_known_facts=frozenset({"secret_rune"})),
            CharacterKnowledgeBaseline(character_name="Lyra", initial_known_facts=frozenset()),
        ]
        chapters = [
            # Chapter 1: Lyra references a secret she doesn't know -> EPI-201 violation
            ChapterEpistemicEvent(
                chapter_index=1,
                chapter_title="The Gate",
                pov_character="Lyra",
                referenced_facts=("forbidden_vault",),
                learned_facts=(),
            ),
            # Chapter 2: Lyra learns forbidden_vault
            ChapterEpistemicEvent(
                chapter_index=2,
                chapter_title="The Revelation",
                pov_character="Lyra",
                referenced_facts=(),
                learned_facts=("forbidden_vault",),
            ),
        ]
        report = audit_epistemic_continuity(characters=characters, chapters=chapters)
        self.assertFalse(report.passed)
        self.assertEqual(len(report.violations), 1)
        self.assertEqual(report.violations[0].rule_id, "EPI-201")
        self.assertEqual(report.violations[0].pov_character, "Lyra")

    def test_timeline_solver_routes_and_relativity(self) -> None:
        cal = CustomCalendarSpec(
            calendar_name="Solaris",
            month_names=("Primus", "Secundus", "Tertius"),
            month_lengths=(30, 30, 30),
        )
        self.assertEqual(cal.days_per_year, 90)
        self.assertEqual(cal.to_absolute_day(1, 1, 1), 0)
        self.assertEqual(cal.to_absolute_day(1, 2, 1), 30)

        # Relativistic time dilation: at 0.6c, Lorentz factor is sqrt(1 - 0.36) = 0.8
        proper_days = compute_relativistic_proper_days(coordinate_days=100.0, velocity_fraction_c=0.6)
        self.assertAlmostEqual(proper_days, 80.0, places=2)

        # Dijkstra shortest route traversal
        routes = [
            RouteEdge(origin="Oasis", destination="Citadel", distance_km=120.0, terrain="paved_road"),
            RouteEdge(origin="Citadel", destination="SunkenCity", distance_km=180.0, terrain="sand_sea"),
        ]
        shortest = compute_shortest_travel_days(routes, "Oasis", "SunkenCity", travel_mode="camel_caravan")
        self.assertIsNotNone(shortest)
        if shortest:
            days, km, path = shortest
            self.assertGreater(days, 0.0)
            self.assertEqual(path, ["Oasis", "Citadel", "SunkenCity"])
            self.assertEqual(km, 300.0)

        # Temporal regression audit (TIME-302)
        events = [
            CharacterTimelineEvent(
                chapter_index=1,
                character_name="Kael",
                location="Oasis",
                year=1,
                month=1,
                day=10,
            ),
            CharacterTimelineEvent(
                chapter_index=2,
                character_name="Kael",
                location="Oasis",
                year=1,
                month=1,
                day=5,  # Regression
                is_flashback=False,
            ),
        ]
        audit = audit_timeline_and_routes(calendar=cal, routes=routes, events=events)
        self.assertFalse(audit["passed"])
        self.assertEqual(audit["anomalies"][0]["rule_id"], "TIME-302")

        # SVG rendering
        svg = render_orbital_calendar_svg(cal)
        self.assertIn("<svg", svg)
        self.assertIn("Solaris", svg)

    def test_resource_conservation_ledger(self) -> None:
        pools = [
            ResourcePoolSpec(
                entity_name="Nautilus",
                resource_name="ether_fuel",
                initial_value=100.0,
                min_bound=0.0,
                max_bound=200.0,
                unit="liters",
            )
        ]
        deltas = [
            ChapterResourceDelta(
                chapter_index=1,
                chapter_title="Launch",
                entity_name="Nautilus",
                resource_name="ether_fuel",
                delta=-30.0,
            ),
            # Chapter 2: Overspending causing LED-501 deficit
            ChapterResourceDelta(
                chapter_index=2,
                chapter_title="Hyperspace",
                entity_name="Nautilus",
                resource_name="ether_fuel",
                delta=-80.0,  # 70 - 80 = -10.0 (below 0.0)
            ),
        ]
        report = audit_resource_conservation(pools=pools, deltas=deltas)
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["violations"]), 1)
        self.assertEqual(report["violations"][0]["rule_id"], "LED-501")

    def test_conlang_phonotactics_and_svg(self) -> None:
        spec = PhonotacticSpec(
            language_name="Valyrian",
            allowed_consonants=("k", "l", "r", "s", "t", "m", "n", "v"),
            allowed_vowels=("a", "e", "i", "o", "u"),
            banned_clusters=("sr",),
            allow_vowel_hiatus=False,
            require_vowel_nucleus=True,
        )
        # Word with illegal phoneme 'z'
        violations = validate_word_phonotactics("kelsonz", spec)
        self.assertTrue(any(v.rule_id == "CON-401" for v in violations))

        # Word with banned cluster 'sr'
        violations_cluster = validate_word_phonotactics("kasra", spec)
        self.assertTrue(any(v.rule_id == "CON-402" for v in violations_cluster))

        # Batch audit
        batch_res = audit_conlang_terms(["kela", "kelsonz"], spec)
        self.assertFalse(batch_res["passed"])

        # Lexeme glossary and derivation tree
        lexemes = [
            ConlangLexeme(con_word="kel", local_gloss="star", pronunciation="kɛl", etymology="*ka > kel"),
            ConlangLexeme(con_word="kela", local_gloss="starlight", pronunciation="kɛla", etymology="kel > kela"),
        ]
        glossary_md = compile_glossary_markdown("Valyrian", lexemes)
        self.assertIn("Valyrian Lexicon", glossary_md)
        self.assertIn("starlight", glossary_md)

        tree_svg = render_etymology_tree_svg(lexemes)
        self.assertIn("<svg", tree_svg)
        self.assertIn("CONLANG ETYMOLOGICAL DERIVATION TREE", tree_svg)

    def test_vault_continuity_runner_and_obsidian_diagnostics(self) -> None:
        (self.vault_root / "manuscript.yaml").write_text("title: Test Saga\n", encoding="utf-8")
        (self.vault_root / "Chapter_01.md").write_text(
            "---\nchapter: 1\npov: Kael\nyear: 1\nmonth: 1\nday: 1\n---\n# Chapter One\n\nProse text here.",
            encoding="utf-8",
        )
        report = run_full_vault_continuity_suite(self.vault_root, write_obsidian_dashboard=True)
        self.assertIn("documents_indexed", report)
        self.assertIn("obsidian_dashboard", report)

        custom_render = render_obsidian_diagnostics_markdown(report)
        self.assertIn("Ars Arcanum Continuity Compiler", custom_render)

        dash_file = self.vault_root / "_Arcanum_Diagnostics.md"
        self.assertTrue(dash_file.is_file())
        dash_content = dash_file.read_text(encoding="utf-8")
        self.assertIn("Ars Arcanum Continuity Compiler", dash_content)
        self.assertIn("Epistemic POV & Spoiler Firewall", dash_content)


if __name__ == "__main__":
    unittest.main()
