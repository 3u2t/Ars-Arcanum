"""Static HTML/SVG visualizers, Obsidian Lite Mode dashboard, theme engine, and sound studio."""

from __future__ import annotations

from src.arcanum.core.hardening import (
    LITE_OBSIDIAN_PLUGINS,
    LiteCheckReport,
    generate_obsidian_lite_profile,
    render_lite_dashboard_markdown,
    run_lite_continuity_check,
)
from src.arcanum.manuscript.braid import render_braid_html
from src.arcanum.manuscript.heatmap import generate_revision_heatmap_html
from src.arcanum.ui.studio import main as theme_studio_main, render_theme_studio_html
from src.arcanum.ui.theme import (
    SOUND_PRESETS,
    VISUAL_PRESETS,
    get_theme_control_center_html,
    get_theme_engine_css,
    get_theme_engine_js,
)
from src.arcanum.worldbible.visualizers import (
    export_etymology_tree_html,
    export_orbital_calendar_html,
    render_etymology_tree_svg,
    render_orbital_calendar_svg,
    wrap_svg_in_standalone_html,
)

try:
    from scripts.lib.codex_export_template import render_codex_html
    from scripts.lib.portfolio_template import render_portfolio_html
except ImportError:
    render_codex_html = None  # type: ignore[assignment]
    render_portfolio_html = None  # type: ignore[assignment]

__all__ = [
    "LITE_OBSIDIAN_PLUGINS",
    "LiteCheckReport",
    "SOUND_PRESETS",
    "VISUAL_PRESETS",
    "export_etymology_tree_html",
    "export_orbital_calendar_html",
    "generate_obsidian_lite_profile",
    "generate_revision_heatmap_html",
    "get_theme_control_center_html",
    "get_theme_engine_css",
    "get_theme_engine_js",
    "render_braid_html",
    "render_codex_html",
    "render_etymology_tree_svg",
    "render_lite_dashboard_markdown",
    "render_orbital_calendar_svg",
    "render_portfolio_html",
    "render_theme_studio_html",
    "run_lite_continuity_check",
    "theme_studio_main",
    "wrap_svg_in_standalone_html",
]
