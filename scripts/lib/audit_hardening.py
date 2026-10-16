"""Phase 5 Audit Hardening & Obsidian Lite Mode Engine (`scripts/lib/audit_hardening.py`).

Provides zero-dependency Python 3.10+ stdlib hardening for:
1. Bounded ZIP/XML validation (`.docx` & `.pgd` archives) against zip bombs, path traversal, and XML entity expansion.
2. Fuzz-resilient YAML frontmatter extraction with recursion depth, BOM, and byte-size guards.
3. CriticMarkup syntax sanitization for malformed or nested `{++...++}` and `{--...--}` runs prior to OpenXML export.
4. CJK ideograph and Unicode NFC prose normalization.
5. One-command Obsidian Lite Mode (`lite-check`) focusing on the 4 core deterministic compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`) and a 5-plugin Obsidian profile.

Delegates completely to native `src.arcanum.core.hardening` while maintaining full backward compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path if not present
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.arcanum.core.hardening import (  # noqa: E402
    CORE_COMPILER_PREFIXES,
    HardenedArchiveLimits,
    LITE_OBSIDIAN_PLUGINS,
    LiteCheckReport,
    build_lite_parser,
    export_markdown_to_docx_hardened,
    generate_obsidian_lite_profile,
    import_polyglot_lexicon_hardened,
    main_lite,
    normalize_cjk_and_unicode_prose,
    parse_frontmatter_hardened,
    parse_xml_safe_bytes,
    pull_docx_to_markdown_hardened,
    render_lite_dashboard_markdown,
    run_lite_continuity_check,
    sanitize_critic_markup,
    validate_safe_zip_archive,
)

__all__ = [
    "CORE_COMPILER_PREFIXES",
    "HardenedArchiveLimits",
    "LITE_OBSIDIAN_PLUGINS",
    "LiteCheckReport",
    "build_lite_parser",
    "export_markdown_to_docx_hardened",
    "generate_obsidian_lite_profile",
    "import_polyglot_lexicon_hardened",
    "main_lite",
    "normalize_cjk_and_unicode_prose",
    "parse_frontmatter_hardened",
    "parse_xml_safe_bytes",
    "pull_docx_to_markdown_hardened",
    "render_lite_dashboard_markdown",
    "run_lite_continuity_check",
    "sanitize_critic_markup",
    "validate_safe_zip_archive",
]

if __name__ == "__main__":
    raise SystemExit(main_lite())
