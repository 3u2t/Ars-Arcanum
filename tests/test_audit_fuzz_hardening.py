"""Fuzz and edge-case hardening tests for stdlib parsers (`tests/test_audit_fuzz_hardening.py`)."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.lib.audit_hardening import (
    HardenedArchiveLimits,
    export_markdown_to_docx_hardened,
    import_polyglot_lexicon_hardened,
    normalize_cjk_and_unicode_prose,
    parse_frontmatter_hardened,
    parse_xml_safe_bytes,
    pull_docx_to_markdown_hardened,
    sanitize_critic_markup,
    validate_safe_zip_archive,
)


class TestAuditFuzzHardening(unittest.TestCase):
    """Stress-tests YAML frontmatter, CriticMarkup/DOCX runs, PolyGlot XML/ZIP bounds, and CJK prose."""

    def test_frontmatter_bom_and_unclosed_delimiters(self) -> None:
        raw_bom = "\ufeff---\npov: Kaelen\nchapter: 3\n---\nBody prose."
        meta, body = parse_frontmatter_hardened(raw_bom)
        self.assertEqual(meta.get("pov"), "Kaelen")
        self.assertEqual(meta.get("chapter"), 3)
        self.assertEqual(body.strip(), "Body prose.")

        unclosed = "---\npov: Kaelen\nchapter: 3\nBody without closing fence."
        meta_unclosed, body_unclosed = parse_frontmatter_hardened(unclosed)
        self.assertEqual(meta_unclosed, {})
        self.assertIn("pov: Kaelen", body_unclosed)

        no_fm = "Plain markdown without frontmatter."
        meta_plain, body_plain = parse_frontmatter_hardened(no_fm)
        self.assertEqual(meta_plain, {})
        self.assertEqual(body_plain, no_fm)

        fake_fence = "---not_a_fence\nBody"
        meta_fake, _ = parse_frontmatter_hardened(fake_fence)
        self.assertEqual(meta_fake, {})

    def test_frontmatter_depth_and_size_bounds(self) -> None:
        limits = HardenedArchiveLimits(max_yaml_depth=3, max_frontmatter_bytes=128)
        deep_yaml = "---\na:\n          b: too_deep\n---\nBody"
        with self.assertRaises(ValueError):
            parse_frontmatter_hardened(deep_yaml, limits=limits)

        huge_yaml = "---\n" + ("key: " + "x" * 200 + "\n") + "---\nBody"
        with self.assertRaises(ValueError):
            parse_frontmatter_hardened(huge_yaml, limits=limits)

    def test_frontmatter_lists_booleans_and_numbers(self) -> None:
        doc = (
            "---\n"
            "# Comment line\n"
            'title: "Sand Sea"\n'
            "subtitle: 'Reliquary'\n"
            "canon: true\n"
            "draft_flag: false\n"
            "empty_val: null\n"
            "block_pipe: |\n"
            "ratio: 1.25\n"
            "empty_list: []\n"
            "tags: [desert, ether]\n"
            "items:\n"
            "  - vial\n"
            "  - compass\n"
            "...\n"
            "Chapter text."
        )
        meta, body = parse_frontmatter_hardened(doc)
        self.assertEqual(meta.get("title"), "Sand Sea")
        self.assertIs(meta.get("canon"), True)
        self.assertIs(meta.get("draft_flag"), False)
        self.assertEqual(body.strip(), "Chapter text.")

    def test_critic_markup_unclosed_and_nested_sanitization(self) -> None:
        malformed = "Start {++added {++nested++} text and {--unclosed deletion"
        sanitized = sanitize_critic_markup(malformed)
        self.assertEqual(sanitized.count("{++"), sanitized.count("++}"))
        self.assertEqual(sanitized.count("{--"), sanitized.count("--}"))
        self.assertTrue(sanitized.endswith("--}"))
        self.assertEqual(sanitize_critic_markup(""), "")

    def test_docx_tracked_changes_hardened_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            md_in = tmp_dir / "chapter_01.md"
            docx_out = tmp_dir / "chapter_01.docx"
            md_out = tmp_dir / "chapter_01_pulled.md"

            md_in.write_text("The {--old--}{++new++} desert {++unclosed", encoding="utf-8")
            export_markdown_to_docx_hardened(md_in, docx_out, author="AuditBot")
            self.assertTrue(docx_out.is_file())

            pulled = pull_docx_to_markdown_hardened(docx_out, md_out)
            self.assertIn("new", pulled)
            self.assertTrue(md_out.is_file())

            pulled_no_file = pull_docx_to_markdown_hardened(docx_out, None)
            self.assertIn("new", pulled_no_file)

            bad_docx = tmp_dir / "empty.docx"
            with zipfile.ZipFile(bad_docx, "w") as zf:
                zf.writestr("other.xml", "<root/>")
            with self.assertRaises(ValueError):
                pull_docx_to_markdown_hardened(bad_docx)

    def test_xml_entity_expansion_rejected(self) -> None:
        xxe_payload = (
            b'<?xml version="1.0"?>\n'
            b'<!DOCTYPE lolz [<!ENTITY lol "lol">]>\n'
            b"<dictionary><word><conWord>vael</conWord></word></dictionary>"
        )
        with self.assertRaises(ValueError):
            parse_xml_safe_bytes(xxe_payload)

    def test_zip_path_traversal_and_entry_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                validate_safe_zip_archive(tmp_dir / "missing.zip")

            not_a_zip = tmp_dir / "plain.txt"
            not_a_zip.write_text("not zip", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_safe_zip_archive(not_a_zip)

            bad_zip = tmp_dir / "traversal.zip"
            with zipfile.ZipFile(bad_zip, "w") as zf:
                zf.writestr("../evil.txt", "escape")
            with self.assertRaises(ValueError):
                validate_safe_zip_archive(bad_zip)

            many_zip = tmp_dir / "many.zip"
            with zipfile.ZipFile(many_zip, "w") as zf:
                for i in range(5):
                    zf.writestr(f"f_{i}.txt", "ok")
            with self.assertRaises(ValueError):
                validate_safe_zip_archive(many_zip, limits=HardenedArchiveLimits(max_entries=2))

            big_zip = tmp_dir / "big.zip"
            with zipfile.ZipFile(big_zip, "w") as zf:
                zf.writestr("big.txt", "x" * 500)
            with self.assertRaises(ValueError):
                validate_safe_zip_archive(big_zip, limits=HardenedArchiveLimits(max_uncompressed_bytes=100))

    def test_polyglot_hardened_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                import_polyglot_lexicon_hardened(tmp_dir / "missing.pgd")

            pgd_path = tmp_dir / "sand_tongue.pgd"
            xml_content = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<dictionary>"
                "<word><conWord>shai</conWord><localWord>sand</localWord><proc>ʃaɪ</proc></word>"
                "</dictionary>"
            )
            with zipfile.ZipFile(pgd_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("PGDictionary.xml", xml_content)

            lexemes = import_polyglot_lexicon_hardened(pgd_path)
            self.assertGreaterEqual(len(lexemes), 1)

            raw_xml_path = tmp_dir / "dict.xml"
            raw_xml_path.write_text(xml_content, encoding="utf-8")
            lexemes_xml = import_polyglot_lexicon_hardened(raw_xml_path)
            self.assertGreaterEqual(len(lexemes_xml), 1)

            no_xml_pgd = tmp_dir / "no_xml.pgd"
            with zipfile.ZipFile(no_xml_pgd, "w") as zf:
                zf.writestr("readme.txt", "none")
            with self.assertRaises(ValueError):
                import_polyglot_lexicon_hardened(no_xml_pgd)

    def test_cjk_and_unicode_normalization(self) -> None:
        mixed = "\ufeffHello\u200b world 「砂の海」"
        metrics = normalize_cjk_and_unicode_prose(mixed)
        self.assertEqual(metrics["latin_words"], 2)
        self.assertEqual(metrics["cjk_ideographs"], 3)
        self.assertEqual(metrics["effective_words"], 5)
        self.assertNotIn("\u200b", metrics["text"])


if __name__ == "__main__":
    unittest.main()
