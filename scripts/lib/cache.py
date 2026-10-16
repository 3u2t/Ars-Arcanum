#!/usr/bin/env python3
"""
Ars Arcanum Cache Engine (scripts/lib/cache.py)
==============================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.cache.
"""

from __future__ import annotations

import sys

from src.arcanum.core.cache import (
    CACHE_FILENAME,
    CACHE_VERSION,
    EXCLUDE_DIR_NAMES,
    FENCED_CODE_REGEX,
    FRONTMATTER_REGEX,
    MAX_BYTES,
    NW_TAG_LINE_REGEX,
    TAG_KEY_MAP,
    TAG_LINE_REGEX,
    TAG_REGEXES,
    WIKILINK_REGEX,
    WORD_REGEX,
    compute_wordcounts,
    count_prose_words,
    count_words,
    extract_tags,
    get_cache_path,
    load_cache,
    main,
    parse_frontmatter,
    parse_markdown_file,
    save_cache,
    scan_project,
)

__all__ = [
    "CACHE_FILENAME",
    "CACHE_VERSION",
    "EXCLUDE_DIR_NAMES",
    "FENCED_CODE_REGEX",
    "FRONTMATTER_REGEX",
    "MAX_BYTES",
    "NW_TAG_LINE_REGEX",
    "TAG_KEY_MAP",
    "TAG_LINE_REGEX",
    "TAG_REGEXES",
    "WIKILINK_REGEX",
    "WORD_REGEX",
    "compute_wordcounts",
    "count_prose_words",
    "count_words",
    "extract_tags",
    "get_cache_path",
    "load_cache",
    "main",
    "parse_frontmatter",
    "parse_markdown_file",
    "save_cache",
    "scan_project",
]

if __name__ == "__main__":
    sys.exit(main())
