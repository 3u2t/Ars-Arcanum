"""Unit tests for SVG Visualizers (Orbital Planetary Calendar & PolyGlot Etymology Trees)."""

from __future__ import annotations

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts.lib.conlang_linter import ConlangLexeme, render_etymology_tree_svg
from scripts.lib.timeline_solver import CustomCalendarSpec, render_orbital_calendar_svg
from src.arcanum import worldbible


class TestSvgVisualizers(unittest.TestCase):
    """Verify standard SVG generation, geometric correctness, and XML well-formedness."""

    def test_render_orbital_calendar_svg_structure(self) -> None:
        calendar = CustomCalendarSpec(
            calendar_name="Roshar High Calendar",
            month_names=("Jes", "Nan", "Chach", "Vev", "Palan", "Shash", "Betab", "Kak", "Tanat", "Kabs"),
            month_lengths=(50, 50, 50, 50, 50, 50, 50, 50, 50, 50),
        )

        svg = render_orbital_calendar_svg(calendar, width=600, height=600)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>"))
        self.assertIn("ROSHAR HIGH CALENDAR", svg)
        self.assertIn("500 Days per Orbital Revolution", svg)
        self.assertIn("Jes (50d)", svg)
        self.assertIn("Kabs (50d)", svg)
        self.assertIn('filter="url(#glow)"', svg)

        # Verify well-formed XML
        root = ET.fromstring(svg)
        self.assertIn("svg", root.tag)

        # Light theme verification
        svg_light = render_orbital_calendar_svg(calendar, width=600, height=600, theme="light")
        self.assertIn("background-color: #ffffff", svg_light)
        self.assertIn("#0969da", svg_light)
        root_light = ET.fromstring(svg_light)
        self.assertIn("svg", root_light.tag)

    def test_render_etymology_tree_svg_structure(self) -> None:
        lexemes = [
            ConlangLexeme(
                con_word="kael",
                local_gloss="wanderer",
                pronunciation="ka.el",
                part_of_speech="noun",
                etymology="*k'el > kela > kael",
            ),
            ConlangLexeme(
                con_word="kalar",
                local_gloss="journey",
                pronunciation="ka.lar",
                part_of_speech="noun",
                etymology="*k'el > kalar",
            ),
            ConlangLexeme(
                con_word="solis",
                local_gloss="star",
                pronunciation="so.lis",
                part_of_speech="noun",
                etymology="*sahw > sohwa > solis",
            ),
        ]

        svg = render_etymology_tree_svg(lexemes, width=800, height=500)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>"))
        self.assertIn("CONLANG ETYMOLOGICAL DERIVATION TREE", svg)
        self.assertIn("*k'el", svg)
        self.assertIn("kael", svg)
        self.assertIn('"wanderer"', svg)
        self.assertIn("kela", svg)
        self.assertIn("*sahw", svg)
        self.assertIn("solis", svg)

        # Verify well-formed XML
        root = ET.fromstring(svg)
        self.assertIn("svg", root.tag)

        # Light theme verification
        svg_light = render_etymology_tree_svg(lexemes, width=800, height=500, theme="light")
        self.assertIn("background-color: #ffffff", svg_light)
        self.assertIn("#0969da", svg_light)
        root_light = ET.fromstring(svg_light)
        self.assertIn("svg", root_light.tag)

    def test_render_etymology_tree_empty_lexemes(self) -> None:
        svg = render_etymology_tree_svg([])
        self.assertIn("No lexemes found", svg)
        root = ET.fromstring(svg)
        self.assertIn("svg", root.tag)

    def test_export_orbital_calendar_html(self) -> None:
        import tempfile
        from src.arcanum.worldbible.visualizers import export_orbital_calendar_html

        calendar = CustomCalendarSpec(
            calendar_name="Scadrial Solar Year",
            month_names=("First", "Second", "Third"),
            month_lengths=(30, 30, 30),
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "calendar.html"
            res = export_orbital_calendar_html(calendar, out_file)
            self.assertEqual(res, out_file.resolve())
            self.assertTrue(out_file.is_file())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Scadrial Solar Year — Orbital Calendar", content)
            self.assertIn("Content-Security-Policy", content)
            self.assertIn("<svg", content)
            self.assertIn("SCADRIAL SOLAR YEAR", content)
            self.assertIn("Days Per Year", content)
            self.assertIn("90", content)

    def test_export_etymology_tree_html(self) -> None:
        import tempfile
        from src.arcanum.worldbible.visualizers import export_etymology_tree_html

        lexemes = [
            ConlangLexeme(con_word="elan", local_gloss="tree", etymology="*el > elan"),
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "etymology.html"
            res = export_etymology_tree_html(lexemes, out_file)
            self.assertEqual(res, out_file.resolve())
            self.assertTrue(out_file.is_file())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("PolyGlot Conlang Etymology Tree", content)
            self.assertIn("Content-Security-Policy", content)
            self.assertIn("<svg", content)
            self.assertIn("elan", content)
            self.assertIn("Root Words", content)

    def test_worldbible_facade_reexports(self) -> None:
        self.assertTrue(callable(worldbible.render_orbital_calendar_svg))
        self.assertTrue(callable(worldbible.render_etymology_tree_svg))
        self.assertTrue(callable(worldbible.export_orbital_calendar_html))
        self.assertTrue(callable(worldbible.export_etymology_tree_html))
        self.assertTrue(callable(worldbible.wrap_svg_in_standalone_html))


if __name__ == "__main__":
    unittest.main()
