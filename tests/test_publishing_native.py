#!/usr/bin/env python3
"""Unit tests for Native Publishing Compilers (tests/test_publishing_native.py).

Validates native `src.arcanum.publishing` modules:
1. `src.arcanum.publishing.preflight`
2. `src.arcanum.publishing.omnibus`
3. `src.arcanum.publishing.publisher`
4. `src.arcanum.publishing.docx`
5. `src.arcanum.publishing.epub`
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.arcanum.publishing import (
    VolumeData,
    build_native_epub3,
    build_tracked_document_xml,
    check_cover_and_assets,
    check_metadata,
    collect_manuscript_content,
    compile_docx,
    compile_omnibus_manuscript,
    compile_pandoc_epub,
    compile_typst_pdf,
    discover_series_volumes,
    escape_typst_text,
    export_markdown_to_docx,
    generate_omnibus_html_reader,
    generate_preflight_html_report,
    get_manuscript_metadata,
    publish_manuscript,
    pull_docx_to_markdown,
    resolve_prose_for_publication,
    run_preflight_linter,
    validate_chapter_formatting,
)


class TestNativePublishingSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # ------------------------------------------------------------------
    # 1. Preflight Linter Tests
    # ------------------------------------------------------------------
    def test_preflight_metadata_and_assets(self) -> None:
        ms_dir = self.root / "TestNovel"
        ms_dir.mkdir()

        # Missing manifest
        res_fail = check_metadata(ms_dir)
        self.assertFalse(res_fail["valid"])

        # Valid manifest
        (ms_dir / "manuscript.yaml").write_text(
            'title: "Aetheria Rising"\nauthor: "A. Author"\nisbn: "978-1-234567-89-0"\n',
            encoding="utf-8",
        )
        res_ok = check_metadata(ms_dir)
        self.assertTrue(res_ok["valid"])
        self.assertEqual(res_ok["data"]["title"], "Aetheria Rising")

        # Cover art detection
        art_dir = ms_dir / "03-Art"
        art_dir.mkdir()
        (art_dir / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        res_cover = check_cover_and_assets(ms_dir)
        self.assertTrue(res_cover["has_cover"])
        self.assertTrue(res_cover["cover_path"].endswith("cover.png"))

    def test_preflight_chapter_formatting_and_report(self) -> None:
        ms_dir = self.root / "Novel"
        ms_dir.mkdir()
        (ms_dir / "manuscript.yaml").write_text('title: "Valid Novel"\nauthor: "Author"\n', encoding="utf-8")

        ch1 = ms_dir / "01_Orphan.md"
        ch1.write_text("# Chapter 1\nSome prose text.\n# Orphan Heading At End", encoding="utf-8")
        issues = validate_chapter_formatting(ch1)
        codes = [i["code"] for i in issues]
        self.assertIn("TYP-ORPHAN-HEAD", codes)

        ch2 = ms_dir / "02_Clean.md"
        ch2.write_text("# Chapter 2\n" + ("Word " * 150), encoding="utf-8")

        report = run_preflight_linter(ms_dir)
        self.assertGreater(report["total_words"], 100)
        self.assertIn("compliance_score", report)

        html_out = ms_dir / "preflight_cert.html"
        cert_path = generate_preflight_html_report(report, html_out)
        self.assertTrue(cert_path.is_file())
        self.assertIn("Content-Security-Policy", cert_path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # 2. Omnibus Multi-Volume Compiler Tests
    # ------------------------------------------------------------------
    def test_omnibus_multi_volume_discovery_and_assembly(self) -> None:
        b1_dir = self.root / "Book-01" / "Draft-01"
        b1_dir.mkdir(parents=True)
        (b1_dir / "01_Ch1.md").write_text("@pov: Alyssa\n\nChapter 1 in Book 1.", encoding="utf-8")
        (b1_dir / "02_Ch2.md").write_text("@pov: Alyssa\n\nChapter 2 in Book 1.", encoding="utf-8")

        b2_dir = self.root / "Book-02" / "Draft-01"
        b2_dir.mkdir(parents=True)
        (b2_dir / "01_Ch1.md").write_text("@pov: Bren\n\nChapter 1 in Book 2.", encoding="utf-8")

        volumes = discover_series_volumes(self.root)
        self.assertEqual(len(volumes), 2)
        self.assertIsInstance(volumes[0], VolumeData)
        self.assertEqual(volumes[0].name, "Book-01")
        self.assertEqual(volumes[1].name, "Book-02")
        self.assertIn("index", volumes[0].to_dict())

        report = compile_omnibus_manuscript(volumes, series_title="The Chrono Epic", author="E. Quill")
        self.assertEqual(report["title"], "The Chrono Epic")
        self.assertEqual(report["total_volumes"], 2)
        self.assertEqual(report["total_chapters"], 3)
        self.assertIn("Alyssa", report["dramatis_personae"])
        self.assertIn("Bren", report["dramatis_personae"])

        html_out = self.root / "omnibus_reader.html"
        reader_path = generate_omnibus_html_reader(report, html_out)
        self.assertTrue(reader_path.is_file())
        self.assertIn("Content-Security-Policy", reader_path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # 3. Publisher Pipeline & CriticMarkup Resolution Tests
    # ------------------------------------------------------------------
    def test_critic_markup_resolution_and_typst_escaping(self) -> None:
        critic_sample = "Original {++inserted++} and {--deleted--} and {~~old~>new~~} text with [[World/Elves|Elves]]."
        clean = resolve_prose_for_publication(critic_sample)
        self.assertEqual(clean, "Original inserted and  and new text with Elves.")

        typst_sample = "Cost is $50 #1 for @author."
        esc = escape_typst_text(typst_sample)
        self.assertIn(r"\$50", esc)
        self.assertIn(r"\#1", esc)
        self.assertIn(r"\@author", esc)

    def test_publisher_manuscript_orchestration_inspect(self) -> None:
        ms_dir = self.root / "PubNovel"
        ms_dir.mkdir()
        (ms_dir / "manuscript.yaml").write_text('title: "Starborne"\nauthor: "Jane"\n', encoding="utf-8")
        ch1 = ms_dir / "01_Chapter.md"
        ch1.write_text("# Chapter 1\nProse text for testing publication pipeline.", encoding="utf-8")

        meta = get_manuscript_metadata(ms_dir)
        self.assertEqual(meta["title"], "Starborne")

        chapters, count = collect_manuscript_content(ms_dir)
        self.assertEqual(len(chapters), 1)
        self.assertGreater(count, 0)

        # Inspect mode across all formats
        res = publish_manuscript(ms_dir, output_format="all", inspect_only=True)
        self.assertEqual(res["status"], "success")
        self.assertIn("docx", res["formats"])
        self.assertIn("pdf", res["formats"])
        self.assertIn("epub", res["formats"])
        # Direct compiler tests
        out_docx = ms_dir / "Direct.docx"
        compile_docx(ms_dir, out_docx, chapters, meta)
        self.assertTrue(out_docx.is_file())

        res_pdf = compile_typst_pdf(ms_dir, ms_dir / "Direct.pdf", chapters, meta, typst_bin="typst", inspect_only=True)
        self.assertEqual(res_pdf["status"], "inspected")

        res_epub = compile_pandoc_epub(ms_dir, ms_dir / "Direct.epub", chapters, meta, pandoc_bin="pandoc", inspect_only=True)
        self.assertEqual(res_epub["status"], "inspected")

    # ------------------------------------------------------------------
    # 4. DOCX Tracked Changes Bridge Tests
    # ------------------------------------------------------------------
    def test_docx_tracked_changes_bidirectional(self) -> None:
        md_text = (
            "# Prologue\n\n"
            "This is original prose {++with additions++} and {--strike through--} and {>>Editor: Check tone<<}.\n"
        )
        doc_xml, comments_xml = build_tracked_document_xml(md_text, author="Reviewer")
        self.assertIn(b"<w:ins", doc_xml)
        self.assertIn(b"<w:del", doc_xml)
        self.assertIn(b"<w:commentReference", doc_xml)
        self.assertIn(b"<w:comment", comments_xml)
        self.assertIn(b"Check tone", comments_xml)

        out_docx = self.root / "Tracked.docx"
        export_markdown_to_docx(md_text, out_docx, author="Reviewer")
        self.assertTrue(out_docx.is_file())
        self.assertGreater(out_docx.stat().st_size, 0)

        pulled_md = pull_docx_to_markdown(out_docx)
        self.assertIn("# Prologue", pulled_md)
        self.assertIn("{++with additions++}", pulled_md)
        self.assertIn("{--strike through--}", pulled_md)
        self.assertIn("{>>Editor: Check tone<<}", pulled_md)

    # ------------------------------------------------------------------
    # 5. Native EPUB3 Builder Test
    # ------------------------------------------------------------------
    def test_native_epub3_generation(self) -> None:
        chapters = [
            {"title": "Chapter 1", "body": "It was a dark and stormy night."},
            {"title": "Chapter 2", "body": "Morning broke cold and clear."},
        ]
        meta = {
            "title": "Storm World",
            "author": "Sovereign Writer",
            "language": "en",
            "identifier": "urn:isbn:978-0-00000-000-0",
        }
        out_epub = self.root / "StormWorld.epub"
        res = build_native_epub3(out_epub, chapters, meta)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["format"], "epub")
        self.assertTrue(out_epub.is_file())
        self.assertGreater(out_epub.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
