"""Ars Arcanum layered package hierarchy (Phase 1-5 Consolidated Facade)."""

from __future__ import annotations

from scripts.lib.audit_hardening import (
    LITE_OBSIDIAN_PLUGINS,
    HardenedArchiveLimits,
    LiteCheckReport,
    build_lite_parser,
    generate_obsidian_lite_profile,
    main_lite,
    normalize_cjk_and_unicode_prose,
    parse_frontmatter_hardened,
    render_lite_dashboard_markdown,
    run_lite_continuity_check,
    sanitize_critic_markup,
    validate_safe_zip_archive,
)

__version__ = "0.1.0"

__all__ = [
    "LITE_OBSIDIAN_PLUGINS",
    "HardenedArchiveLimits",
    "LiteCheckReport",
    "build_lite_parser",
    "generate_obsidian_lite_profile",
    "main_lite",
    "normalize_cjk_and_unicode_prose",
    "parse_frontmatter_hardened",
    "render_lite_dashboard_markdown",
    "run_lite_continuity_check",
    "sanitize_critic_markup",
    "validate_safe_zip_archive",
]
