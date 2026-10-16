"""Unit tests for Native Zero-Pip EPUB3 Package Builder and Publishing Facade."""

from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.lib.vault_index import atomic_write
from src.arcanum.publishing.epub import (
    build_native_epub3,
    clean_xml_text,
    inline_markdown_to_xhtml,
    markdown_to_xhtml_body,
)


class TestEpubBuilder(unittest.TestCase):
    """Verify standard-compliant zero-pip EPUB3 generation and XML hygiene."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clean_xml_text_and_inline_formatting(self) -> None:
        raw = "Hello \x00World & welcome to *Ars Arcanum*! **Bold text** and `code`."
        clean = clean_xml_text(raw)
        self.assertNotIn("\x00", clean)

        xhtml = inline_markdown_to_xhtml(raw)
        self.assertIn("&amp;", xhtml)
        self.assertIn("<em>Ars Arcanum</em>", xhtml)
        self.assertIn("<strong>Bold text</strong>", xhtml)
        self.assertIn("<code>code</code>", xhtml)

    def test_markdown_to_xhtml_body(self) -> None:
        md = (
            "# Section Heading\n\n"
            "@scene: desert_camp\n"
            "The cold sand shifting {--silently--}{++whispering++}.\n\n"
            "---\n\n"
            "> A word whispered across the void.\n"
        )
        body = markdown_to_xhtml_body(md)
        self.assertIn("<h2>Section Heading</h2>", body)
        self.assertNotIn("@scene", body)
        self.assertIn("whispering", body)
        self.assertNotIn("silently", body)
        self.assertIn('<hr class="thematic-break" />', body)
        self.assertIn("<blockquote><p>A word whispered across the void.</p></blockquote>", body)

    def test_build_native_epub3_package_structure(self) -> None:
        out_epub = self.tmp_dir / "Test_Novel.epub"
        chapters = [
            {
                "index": 1,
                "title": "The Awakening",
                "body": "Chapter one began under the binary suns.\n\n*Another day.*",
            },
            {
                "index": 2,
                "title": "The Gate",
                "body": "They stood before the brass archway.",
            },
        ]
        meta = {
            "title": "Chronicles of Dune",
            "author": "Sovereign Writer",
            "language": "en",
        }

        res = build_native_epub3(out_epub, chapters, meta)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["builder"], "native_zero_pip_epub3")
        self.assertTrue(out_epub.is_file())
        self.assertGreater(out_epub.stat().st_size, 0)

        # Inspect ZIP structure conforming to EPUB3 spec
        with zipfile.ZipFile(out_epub, "r") as zf:
            infolist = zf.infolist()
            # 1. mimetype MUST be first and UNCOMPRESSED (ZIP_STORED)
            self.assertEqual(infolist[0].filename, "mimetype")
            self.assertEqual(infolist[0].compress_type, zipfile.ZIP_STORED)
            self.assertEqual(zf.read("mimetype"), b"application/epub+zip")

            # 2. META-INF/container.xml must be valid XML
            container_bytes = zf.read("META-INF/container.xml")
            root_elem = ET.fromstring(container_bytes)
            self.assertIn("container", root_elem.tag)

            # 3. OEBPS/content.opf must be valid XML and declare chapters
            opf_bytes = zf.read("OEBPS/content.opf")
            opf_elem = ET.fromstring(opf_bytes)
            self.assertIn("package", opf_elem.tag)

            # 4. OEBPS/toc.xhtml
            toc_bytes = zf.read("OEBPS/toc.xhtml")
            self.assertIn(b"The Awakening", toc_bytes)
            self.assertIn(b"The Gate", toc_bytes)

            # 5. OEBPS/chapter_001.xhtml and chapter_002.xhtml
            ch1_bytes = zf.read("OEBPS/chapter_001.xhtml")
            self.assertIn(b"The Awakening", ch1_bytes)
            self.assertIn(b"binary suns", ch1_bytes)
            self.assertIn(b"<em>Another day.</em>", ch1_bytes)

            ch2_bytes = zf.read("OEBPS/chapter_002.xhtml")
            self.assertIn(b"The Gate", ch2_bytes)
            self.assertIn(b"brass archway", ch2_bytes)

    def test_build_native_epub3_with_cover_image(self) -> None:
        out_epub = self.tmp_dir / "Cover_Novel.epub"
        cover_img = self.tmp_dir / "cover.png"
        # 1x1 minimal PNG
        cover_img.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00"
            b"\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        chapters = [{"index": 1, "title": "Prologue", "body": "In the beginning..."}]
        meta = {"title": "Cover Book", "author": "Illustrator"}

        res = build_native_epub3(out_epub, chapters, meta, cover_path=cover_img)
        self.assertEqual(res["status"], "success")

        with zipfile.ZipFile(out_epub, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("OEBPS/cover.png", namelist)
            self.assertIn("OEBPS/cover.xhtml", namelist)
            opf = zf.read("OEBPS/content.opf").decode("utf-8")
            self.assertIn('properties="cover-image"', opf)

    def test_publisher_fallback_to_native_epub(self) -> None:
        from scripts.lib.publisher import publish_manuscript

        ms_dir = self.tmp_dir / "Manuscript" / "Novel-EPUB" / "Draft-01"
        ms_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(
            ms_dir / "01_Start.md",
            "---\ntitle: The Opening\n---\nFirst sentences of sovereign prose.\n",
        )

        # Mock find_tool("pandoc") returning None to test automatic zero-pip fallback
        with patch("scripts.lib.publisher.find_tool", return_value=None):
            result = publish_manuscript(ms_dir, output_format="epub")
            self.assertEqual(result["status"], "success")
            epub_res = result["formats"]["epub"]
            self.assertEqual(epub_res["status"], "success")
            self.assertEqual(epub_res["builder"], "native_zero_pip_epub3")
            out_file = Path(epub_res["output_path"])
            self.assertTrue(out_file.is_file())
            self.assertTrue(zipfile.is_zipfile(out_file))

    def test_facade_reexports_feature_parity(self) -> None:
        from src.arcanum import core, manuscript, publishing

        # Core re-exports
        self.assertTrue(callable(core.atomic_write))
        self.assertTrue(callable(core.is_safe_subpath))
        self.assertTrue(hasattr(core, "ArcanumLock"))
        self.assertTrue(hasattr(core, "PathSecurityError"))
        self.assertTrue(hasattr(core, "VaultIndex"))

        # Manuscript re-exports
        self.assertTrue(hasattr(manuscript, "DraftManager"))
        self.assertTrue(callable(manuscript.list_drafts))
        self.assertTrue(callable(manuscript.start_sprint))
        self.assertTrue(callable(manuscript.analyze_narrative_braid))

        # Publishing re-exports
        self.assertTrue(callable(publishing.build_native_epub3))
        self.assertTrue(callable(publishing.publish_manuscript))
        self.assertTrue(callable(publishing.export_markdown_to_docx))


if __name__ == "__main__":
    unittest.main()
