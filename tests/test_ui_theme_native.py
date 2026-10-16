#!/usr/bin/env python3
"""
Unit tests for Native Ars Arcanum UI Theme Engine & Studio (src/arcanum/ui/theme.py, studio.py).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.arcanum.ui.theme import (
    SOUND_PRESETS,
    VISUAL_PRESETS,
    get_theme_control_center_html,
    get_theme_engine_css,
    get_theme_engine_js,
)
from src.arcanum.ui.studio import render_theme_studio_html
from src.arcanum.ui import (
    SOUND_PRESETS as UI_SOUND_PRESETS,
    VISUAL_PRESETS as UI_VISUAL_PRESETS,
    get_theme_control_center_html as ui_get_control_center,
    get_theme_engine_css as ui_get_css,
    get_theme_engine_js as ui_get_js,
    render_theme_studio_html as ui_render_studio,
)


class TestUiThemeNative(unittest.TestCase):
    def test_reexports(self) -> None:
        self.assertIs(UI_SOUND_PRESETS, SOUND_PRESETS)
        self.assertIs(UI_VISUAL_PRESETS, VISUAL_PRESETS)
        self.assertIs(ui_get_control_center, get_theme_control_center_html)
        self.assertIs(ui_get_css, get_theme_engine_css)
        self.assertIs(ui_get_js, get_theme_engine_js)
        self.assertIs(ui_render_studio, render_theme_studio_html)

    def test_theme_presets_count(self) -> None:
        self.assertEqual(len(VISUAL_PRESETS), 11)
        self.assertEqual(len(SOUND_PRESETS), 10)
        self.assertIn("sovereign-dark", VISUAL_PRESETS)
        self.assertIn("remington_1890", SOUND_PRESETS)

    def test_css_generation(self) -> None:
        css = get_theme_engine_css()
        self.assertIn('[data-theme="sovereign-dark"]', css)
        self.assertIn(".crt-effect", css)

    def test_js_generation(self) -> None:
        js = get_theme_engine_js()
        self.assertIn("class TypewriterAudioEngine", js)
        self.assertIn("ArcanumAudio", js)

    def test_render_studio_html(self) -> None:
        html_str = render_theme_studio_html()
        self.assertIn("<!DOCTYPE html>", html_str)
        self.assertIn("Content-Security-Policy", html_str)
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "theme_studio.html"
            res_path = render_theme_studio_html(output_path=out_file)
            self.assertEqual(res_path, str(out_file))
            self.assertTrue(out_file.is_file())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Typewriter Sound Studio", content)


if __name__ == "__main__":
    unittest.main()
