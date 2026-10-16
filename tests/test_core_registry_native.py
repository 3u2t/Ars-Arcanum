#!/usr/bin/env python3
"""
Unit tests for native Ars Arcanum Engine & Plugin Registry.
Tests src.arcanum.core.registry directly.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.arcanum.core.registry import (
    ALL_ENGINES,
    AdvisoryResolution,
    BaseCraftEngine,
    DiagnosticSeverity,
    EngineCategory,
    EngineSpec,
    disable_engine,
    discover_craft_plugins,
    discover_user_plugins,
    enable_engine,
    format_engine_doc,
    format_unified_bibliography,
    get_all_engine_docs,
    get_core_engines,
    get_craft_engines,
    get_engine,
    get_engine_catalog,
    get_engine_docs,
    get_registry,
    get_unified_bibliography,
    is_engine_enabled,
    list_engines,
    load_engine_module,
    load_user_plugin,
    register_user_engine,
    reset_registry,
    search_engine_docs,
)


class MockCustomCraftEngine(BaseCraftEngine):
    name = "astrology_lens"
    title = "Astrological Aspect Linter"
    description = "Planetary alignments and retrograde astrological aspects"
    cli_command = "craft astrology"
    aliases = ["astro", "horoscope"]
    studio_tab = "Worldbuilding"

    def execute(self, argv: list[str]) -> int:
        return 7


class TestCoreRegistryNative(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        reset_registry()

    def test_registry_initialization_and_counts(self) -> None:
        reg = get_registry()
        self.assertEqual(len(reg), len(ALL_ENGINES))
        self.assertGreaterEqual(len(reg), 17)

        core_engines = get_core_engines(enabled_only=False)
        self.assertGreater(len(core_engines), 10)
        self.assertTrue(all(e.category == EngineCategory.CORE for e in core_engines))

        craft_engines = get_craft_engines(enabled_only=False)
        self.assertGreater(len(craft_engines), 0)
        self.assertTrue(all(e.category == EngineCategory.CRAFT for e in craft_engines))

        # Test list_engines
        all_list = list_engines(enabled_only=False)
        self.assertEqual(len(all_list), len(ALL_ENGINES))

        # Test DiagnosticSeverity and AdvisoryResolution
        self.assertEqual(DiagnosticSeverity.CANON_ERROR.value, "canon_error")
        res = AdvisoryResolution(mode="Hard Realism", description="Standard physics")
        self.assertEqual(res.mode, "Hard Realism")

        # Test docs querying
        docs = get_engine_docs("config")
        self.assertIsNotNone(docs)
        assert docs is not None
        self.assertEqual(docs["name"], "config")
        all_docs = get_all_engine_docs()
        self.assertEqual(len(all_docs), len(ALL_ENGINES))

        # Test dynamic engine module loader
        mod = load_engine_module("config")
        self.assertIsNotNone(mod)

    def test_engine_lookup_and_aliases(self) -> None:
        spec = get_engine("docx_sync")
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.name, "docx_sync")

        # Test lookup by alias
        alias_spec = get_engine("docx")
        self.assertIsNotNone(alias_spec)
        assert alias_spec is not None
        self.assertEqual(alias_spec.name, "docx_sync")

        # Test hyphenated / underscored variants
        hyphen_spec = get_engine("word-sync")
        self.assertIsNotNone(hyphen_spec)

    def test_enable_disable_engine(self) -> None:
        spec_name = "diagnostics"
        self.assertTrue(is_engine_enabled(spec_name))

        self.assertTrue(disable_engine(spec_name))
        self.assertFalse(is_engine_enabled(spec_name))

        self.assertTrue(enable_engine(spec_name))
        self.assertTrue(is_engine_enabled(spec_name))

    def test_format_engine_doc_modes(self) -> None:
        spec = get_engine("revision_heatmap")
        self.assertIsNotNone(spec)
        assert spec is not None

        full_doc = format_engine_doc(spec, mode="full")
        self.assertIn("REVISION DENSITY & CHURN HEATMAP", full_doc.upper())

        math_doc = format_engine_doc(spec, mode="math")
        self.assertIn("SCIENTIFIC / MATHEMATICAL", math_doc.upper())

        why_doc = format_engine_doc(spec, mode="why")
        self.assertIn("RATIONALE", why_doc.upper())

        features_doc = format_engine_doc(spec, mode="subfeatures")
        self.assertIn("SUBFEATURES MATRIX", features_doc.upper())

        advisory_doc = format_engine_doc(spec, mode="advisory")
        self.assertIn("CREATIVE ADVISORY RESOLUTION PATHWAYS", advisory_doc.upper())

    def test_unified_bibliography_formatting(self) -> None:
        bib = get_unified_bibliography()
        self.assertIsInstance(bib, list)
        self.assertGreater(len(bib), 0)

        # JSON format
        json_output = format_unified_bibliography(format_type="json")
        parsed = json.loads(json_output)
        self.assertEqual(len(parsed), len(bib))

        # Markdown format
        md_output = format_unified_bibliography(format_type="markdown")
        self.assertIn("# Ars Arcanum Sovereign Craft Library", md_output)

        # Text format
        text_output = format_unified_bibliography(format_type="text")
        self.assertIn("ARS ARCANUM CRAFT LIBRARY", text_output)

    def test_search_and_catalog(self) -> None:
        results = search_engine_docs("diff")
        self.assertTrue(any(e.name == "manuscript_diff" for e in results))

        catalog = get_engine_catalog()
        self.assertEqual(len(catalog), len(ALL_ENGINES))
        for item in catalog:
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("cli", item)

    def test_custom_engine_registration_and_execution(self) -> None:
        engine = MockCustomCraftEngine()
        spec = engine.get_spec()
        self.assertIsInstance(spec, EngineSpec)
        self.assertEqual(spec.name, "astrology_lens")

        register_user_engine(spec)
        retrieved = get_engine("astrology_lens")
        self.assertIsNotNone(retrieved)
        assert retrieved is not None
        self.assertEqual(retrieved.title, "Astrological Aspect Linter")
        self.assertEqual(engine.execute([]), 7)

    def test_plugin_file_loading_and_discovery(self) -> None:
        plugin_file = self.root / "alchemical_flux.py"
        plugin_file.write_text(
            "from src.arcanum.core.registry import BaseCraftEngine, EngineCategory\n\n"
            "class AlchemyLens(BaseCraftEngine):\n"
            "    name = 'alchemical_flux'\n"
            "    title = 'Alchemical Flux Lens'\n"
            "    description = 'Hermetic elemental balancing'\n"
            "    cli_command = 'craft alchemy'\n"
            "    studio_tab = 'Worldbuilding'\n"
            "    def execute(self, argv):\n"
            "        return 0\n",
            encoding="utf-8",
        )

        spec = load_user_plugin(plugin_file)
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.name, "alchemical_flux")

        discovered = discover_user_plugins(extra_dirs=[self.root])
        self.assertTrue(any(s.name == "alchemical_flux" for s in discovered))

        alias_discovered = discover_craft_plugins(extra_dirs=[self.root])
        self.assertTrue(any(s.name == "alchemical_flux" for s in alias_discovered))


if __name__ == "__main__":
    unittest.main()
