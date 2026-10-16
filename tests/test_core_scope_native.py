#!/usr/bin/env python3
"""
Unit tests for Native Scope & Target Resolution Engine (tests/test_core_scope_native.py)
=======================================================================================
Directly tests `src.arcanum.core.scope` and `src.arcanum.core` scope re-exports.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
import unittest

from src.arcanum.core import (
    ChapterItem,
    EngineScope,
    LoreItem,
    ResolvedScope,
    SceneSlice,
    add_scope_arguments,
    extract_scenes_from_text,
    filter_manuscript_scope,
    filter_world_scope,
    format_scope_banner,
    parse_identifier_list,
    parse_number_ranges,
    parse_scope_args,
    parse_unified_scope_string,
    resolve_manuscript_dir,
    resolve_manuscript_path,
    resolve_scope,
    resolve_universe_dir,
    resolve_universe_path,
    resolve_world_dir,
    resolve_world_path,
    scope_main,
)


class TestCoreScopeNative(unittest.TestCase):
    """Validates native scope functions in src.arcanum.core.scope."""

    def test_parse_number_ranges_comprehensive(self):
        self.assertEqual(parse_number_ranges(None), [])
        self.assertEqual(parse_number_ranges(7), [7])
        self.assertEqual(parse_number_ranges("1, 3, 5-7"), [1, 3, 5, 6, 7])
        self.assertEqual(parse_number_ranges("ch01..ch04"), [1, 2, 3, 4])
        self.assertEqual(parse_number_ranges("sc1, sc2"), [1, 2])
        self.assertEqual(parse_number_ranges(["1-3", 5]), [1, 2, 3, 5])
        self.assertEqual(parse_number_ranges("10 to 8"), [8, 9, 10])

    def test_parse_identifier_list_and_unified_string(self):
        self.assertEqual(parse_identifier_list("BookA, BookB; BookC"), ["BookA", "BookB", "BookC"])
        parsed = parse_unified_scope_string("ms:NovelX, world:WorldY, cat:Characters, ch:1-3, sc:1-2")
        self.assertEqual(parsed["manuscript"], "NovelX")
        self.assertEqual(parsed["world"], "WorldY")
        self.assertEqual(parsed["lore_categories"], ["Characters"])
        self.assertEqual(parsed["chapters"], [1, 2, 3])
        self.assertEqual(parsed["scenes"], [1, 2])

    def test_scene_extraction_and_chapter_slicing(self):
        sample = (
            "# Chapter 1: The Gate\n\n"
            "First scene content.\n\n"
            "---\n\n"
            "@scene: Escape\nSecond scene content.\n"
        )
        scenes = extract_scenes_from_text(sample, Path("ch1.md"), chapter_num=1)
        self.assertEqual(len(scenes), 2)
        self.assertEqual(scenes[0].title, "Chapter 1: The Gate")
        self.assertEqual(scenes[1].title, "Escape")
        self.assertIn("First scene", scenes[0].content)
        self.assertIn("Second scene", scenes[1].content)

    def test_engine_scope_and_resolved_scope_lifecycle(self):
        scope = EngineScope(
            manuscript="NovelZ",
            world="Eldoria",
            chapters=[1, 2],
            scenes=[1],
            lore_categories=["Locations"],
        )
        self.assertTrue(scope.is_scoped())
        self.assertTrue(scope.is_manuscript_scoped())
        self.assertTrue(scope.is_world_scoped())
        self.assertIn("Chapters: [ch01-02]", scope.summary)

        d = scope.to_dict()
        reconstructed = EngineScope.from_dict(d)
        self.assertEqual(scope, reconstructed)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ms_dir = root / "NovelZ"
            ms_dir.mkdir()
            (ms_dir / "01_Intro.md").write_text("# Intro\n\nContent here.", encoding="utf-8")
            (ms_dir / "02_Rising.md").write_text("# Rising\n\nContent two.", encoding="utf-8")

            res = resolve_scope(EngineScope(manuscript=str(ms_dir), chapters=[1]))
            self.assertEqual(res.get_total_chapter_count(), 1)
            self.assertEqual(res.chapters[0].chapter_num, 1)
            self.assertIn("NovelZ", res.volume_names)
            res_dict = res.to_dict()
            self.assertEqual(res_dict["total_chapters"], 1)

    def test_scope_cli_argument_parsing(self):
        parser = argparse.ArgumentParser()
        add_scope_arguments(parser, target_pos_arg=True)
        args = parser.parse_args([
            "MyNovel",
            "--chapters", "1-3",
            "--scenes", "1,2",
            "--world", "Eldoria",
            "--lore-categories", "Bestiary",
            "--all",
        ])
        scope = parse_scope_args(args)
        self.assertEqual(scope.manuscript, "MyNovel")
        self.assertEqual(scope.chapters, [1, 2, 3])
        self.assertEqual(scope.scenes, [1, 2])
        self.assertEqual(scope.world, "Eldoria")
        self.assertEqual(scope.lore_categories, ["Bestiary"])
        self.assertTrue(scope.all_targets)

    def test_world_filtering_and_lore_items(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            w_dir = root / "Eldoria"
            (w_dir / "Characters").mkdir(parents=True)
            (w_dir / "Locations").mkdir(parents=True)
            (w_dir / "Characters" / "Hero.md").write_text("# Hero\nProse here.", encoding="utf-8")
            (w_dir / "Locations" / "City.md").write_text("# City\nProse here.", encoding="utf-8")

            items = filter_world_scope(w_dir, EngineScope(lore_categories=["Characters"]))
            self.assertEqual(len(items), 1)
            self.assertIsInstance(items[0], LoreItem)
            self.assertEqual(items[0].name, "Hero")
            self.assertEqual(items[0].category, "Characters")

    def test_path_and_dir_resolvers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ms_dir = root / "TestMS"
            ms_dir.mkdir()
            w_dir = root / "TestWorld"
            w_dir.mkdir()
            u_dir = root / "TestUniv"
            u_dir.mkdir()

            self.assertEqual(resolve_manuscript_path(str(ms_dir)), ms_dir)
            self.assertEqual(resolve_manuscript_dir(str(ms_dir)), str(ms_dir))
            self.assertEqual(resolve_world_path(str(w_dir)), w_dir)
            self.assertEqual(resolve_world_dir(str(w_dir)), str(w_dir))
            self.assertEqual(resolve_universe_path(str(u_dir)), u_dir)
            self.assertEqual(resolve_universe_dir(str(u_dir)), str(u_dir))

    def test_dataclass_type_integrity(self):
        ch = ChapterItem(
            chapter_num=1,
            title="Ch 1",
            file_path=Path("ch1.md"),
            volume_name="Vol 1",
            division_name="Main",
            full_content="text",
            scoped_content="text",
            scenes=[],
            tags={},
            word_count=1,
        )
        self.assertEqual(ch.index, 1)
        self.assertEqual(ch.path, Path("ch1.md"))
        self.assertEqual(ch.content, "text")

        sc = SceneSlice(
            scene_idx=1,
            global_scene_idx=1,
            scene_id="ch01_sc01",
            title="Scene 1",
            content="text",
            start_line=1,
            end_line=2,
            tags={},
            chapter_file=Path("ch1.md"),
            chapter_num=1,
            volume_name="Vol 1",
        )
        self.assertEqual(sc.word_count, 1)

        res = ResolvedScope(
            manuscript_dir=None,
            manuscript_dirs=[],
            world_dir=None,
            world_dirs=[],
            universe_dir=None,
            series_names=[],
            volume_names=[],
            chapters=[ch],
            scenes=[sc],
            lore_items=[],
            is_scoped=False,
            scope_filter=EngineScope(),
            summary="All",
        )
        self.assertEqual(res.get_markdown_files(), [Path("ch1.md")])
        self.assertEqual(res.get_lore_files(), [])
        self.assertEqual(res.get_total_scene_count(), 1)

    def test_filter_manuscript_scope_direct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ms = root / "DirectMS"
            ms.mkdir()
            (ms / "01_Prologue.md").write_text("# Prologue\nText 1.", encoding="utf-8")
            (ms / "02_Chapter2.md").write_text("# Ch 2\nText 2.", encoding="utf-8")

            chaps, _scs, _vols = filter_manuscript_scope(ms, EngineScope(chapters=[1]))
            self.assertEqual(len(chaps), 1)
            self.assertEqual(chaps[0].chapter_num, 1)

    def test_scope_cli_main_and_banner(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ms = root / "CLI_Novel"
            ms.mkdir()
            (ms / "01_Start.md").write_text("# Start\n\nWords here.", encoding="utf-8")

            ret = scope_main([str(ms), "--chapters", "1"])
            self.assertEqual(ret, 0)

            ret_json = scope_main([str(ms), "--json"])
            self.assertEqual(ret_json, 0)

            banner = format_scope_banner("Test Scope", EngineScope(chapters=[1]))
            self.assertIn("Test Scope", banner)


if __name__ == "__main__":
    unittest.main()

