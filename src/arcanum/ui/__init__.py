"""Static HTML/SVG visualizers, Obsidian Lite Mode dashboard, and theme integration."""

from __future__ import annotations

from scripts.lib.audit_hardening import (
    LITE_OBSIDIAN_PLUGINS,
    LiteCheckReport,
    generate_obsidian_lite_profile,
    render_lite_dashboard_markdown,
    run_lite_continuity_check,
)
from scripts.lib.narrative_braid import render_braid_html
from src.arcanum.ui.studio import render_theme_studio_html
from src.arcanum.ui.theme import (
    SOUND_PRESETS,
    VISUAL_PRESETS,
    get_theme_control_center_html,
    get_theme_engine_css,
    get_theme_engine_js,
)

__all__ = [
    "LITE_OBSIDIAN_PLUGINS",
    "LiteCheckReport",
    "SOUND_PRESETS",
    "VISUAL_PRESETS",
    "generate_obsidian_lite_profile",
    "get_theme_control_center_html",
    "get_theme_engine_css",
    "get_theme_engine_js",
    "render_braid_html",
    "render_lite_dashboard_markdown",
    "render_theme_studio_html",
    "run_lite_continuity_check",
]
