#!/usr/bin/env python3
"""
Unit tests for Native YAML Frontmatter Engine & Publishing Builder (tests/test_core_frontmatter_native.py)
=======================================================================================================
Directly tests `src.arcanum.core.frontmatter` and `src.arcanum.core` frontmatter re-exports.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.arcanum.core import (
    FRONTMATTER_DELIM,
    dump_frontmatter,
    extract_frontmatter_and_body,
    generate_backmatter_modules,
    generate_frontmatter_modules,
    main_matter,
    parse_frontmatter,
    parse_yaml_document,
    parse_yaml_frontmatter,
    scaffold_matter,
    serialize_yaml_document,
    serialize_yaml_frontmatter,
)


class TestCoreFrontmatterNative(unittest.TestCase):
    """Validates native frontmatter functions in src.arcanum.core.frontmatter."""

    def test_parse_yaml_frontmatter_and_scalars(self):
        content = (
            "---\n"
            "title: The Emerald Spire\n"
            "chapters: 12\n"
            "rating: 4.85\n"
            "published: true\n"
            "tags: [fantasy, adventure]\n"
            "metadata:\n"
            "  series: Spire Cycle\n"
            "  volume: 1\n"
            "---\n\n"
            "# Chapter 1\n\nProse text goes here."
        )
        fm = parse_yaml_frontmatter(content)
        self.assertEqual(fm["title"], "The Emerald Spire")
        self.assertEqual(fm["chapters"], 12)
        self.assertEqual(fm["rating"], 4.85)
        self.assertTrue(fm["published"])
        self.assertEqual(fm["tags"], ["fantasy", "adventure"])
        self.assertEqual(fm["metadata"]["series"], "Spire Cycle")
        self.assertEqual(fm["metadata"]["volume"], 1)

        extracted_meta, body = extract_frontmatter_and_body(content)
        self.assertEqual(extracted_meta["title"], "The Emerald Spire")
        self.assertIn("# Chapter 1", body)

    def test_parse_yaml_document_without_fences(self):
        doc = (
            "name: Eldoria\n"
            "cosmology:\n"
            "  type: Heliocentric\n"
            "factions:\n"
            "  - name: Silver Order\n"
            "    alignment: Lawful\n"
            "  - name: Shadow Syndicate\n"
            "    alignment: Chaotic\n"
        )
        parsed = parse_yaml_document(doc)
        self.assertEqual(parsed["name"], "Eldoria")
        self.assertEqual(parsed["cosmology"]["type"], "Heliocentric")
        self.assertEqual(len(parsed["factions"]), 2)
        self.assertEqual(parsed["factions"][0]["name"], "Silver Order")

    def test_strict_parse_frontmatter(self):
        valid = "---\ntitle: Valid\n---\nBody"
        fm, ok = parse_frontmatter(valid)
        self.assertTrue(ok)
        self.assertEqual(fm["title"], "Valid")

        unclosed = "---\ntitle: Unclosed\nBody"
        fm_bad, ok_bad = parse_frontmatter(unclosed)
        self.assertFalse(ok_bad)
        self.assertEqual(fm_bad, {})

        no_fm = "Just markdown content"
        fm_none, ok_none = parse_frontmatter(no_fm)
        self.assertTrue(ok_none)
        self.assertEqual(fm_none, {})

    def test_yaml_serialization_roundtrip(self):
        data = {
            "title": "Aetheria",
            "volume": 3,
            "complete": False,
            "tags": ["epic", "magic"],
            "nested": {
                "key": "value",
            },
        }
        yaml_str = serialize_yaml_document(data)
        reparsed = parse_yaml_document(yaml_str)
        self.assertEqual(reparsed["title"], "Aetheria")
        self.assertEqual(reparsed["volume"], 3)
        self.assertFalse(reparsed["complete"])
        self.assertEqual(reparsed["tags"], ["epic", "magic"])
        self.assertEqual(reparsed["nested"]["key"], "value")

        fenced = serialize_yaml_frontmatter(data, body="Body text.")
        self.assertTrue(fenced.startswith(FRONTMATTER_DELIM))
        self.assertIn("Body text.", fenced)
        self.assertEqual(dump_frontmatter(data), serialize_yaml_frontmatter(data))

    def test_matter_modules_generation_and_scaffolding(self):
        meta = {
            "title": "Crown of Ash",
            "subtitle": "Song of Fire",
            "author": "Kaelen Drake",
            "copyright_year": "2026",
            "isbn": "978-0-123456-00-1",
            "edition": "Deluxe Edition",
            "dedication": "For dreamers.",
            "epigraph": "From dust to stars.",
            "epigraph_author": "Ancient Bard",
            "newsletter_url": "https://kaelendrake.com/join",
            "website_url": "https://kaelendrake.com",
        }
        front = generate_frontmatter_modules(meta)
        self.assertIn("01_Half_Title.md", front)
        self.assertIn("Crown of Ash", front["01_Half_Title.md"])
        self.assertIn("Deluxe Edition", front["03_Copyright.md"])

        back = generate_backmatter_modules(meta)
        self.assertIn("01_Acknowledgments.md", back)
        self.assertIn("https://kaelendrake.com/join", back["05_Reader_CTA.md"])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ms_dir = root / "CrownOfAsh"
            ms_dir.mkdir()

            res1 = scaffold_matter(ms_dir, meta, force=False)
            self.assertEqual(res1["created_count"], 10)
            self.assertEqual(res1["skipped_count"], 0)

            res2 = scaffold_matter(ms_dir, meta, force=False)
            self.assertEqual(res2["created_count"], 0)
            self.assertEqual(res2["skipped_count"], 10)

            res3 = scaffold_matter(ms_dir, meta, force=True)
            self.assertEqual(res3["created_count"], 10)
            self.assertEqual(res3["skipped_count"], 0)

    def test_main_matter_cli(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ms_dir = root / "CLI_Novel"
            ms_dir.mkdir()
            (ms_dir / "manuscript.yaml").write_text("title: CLI Novel\nauthor: Jane Doe\n", encoding="utf-8")

            test_args = ["frontmatter.py", "build", str(ms_dir), "--json"]
            with patch.object(sys, "argv", test_args), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                ret = main_matter()
                self.assertEqual(ret, 0)
                data = json.loads(mock_out.getvalue())
                self.assertEqual(data["created_count"], 10)


if __name__ == "__main__":
    unittest.main()
