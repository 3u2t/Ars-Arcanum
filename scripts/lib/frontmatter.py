#!/usr/bin/env python3
"""
Ars Arcanum Unified YAML Frontmatter Engine (scripts/lib/frontmatter.py)
=======================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.frontmatter.
"""

from __future__ import annotations

from src.arcanum.core.frontmatter import (
    FRONTMATTER_DELIM,
    FRONTMATTER_REGEX,
    _coerce_scalar,
    _parse_yaml_lines,
    _serialize_scalar,
    _split_comma_preserving_quotes,
    dump_frontmatter,
    extract_frontmatter_and_body,
    parse_frontmatter,
    parse_yaml_document,
    parse_yaml_frontmatter,
    serialize_yaml_document,
    serialize_yaml_frontmatter,
)

__all__ = [
    "FRONTMATTER_DELIM",
    "FRONTMATTER_REGEX",
    "_coerce_scalar",
    "_parse_yaml_lines",
    "_serialize_scalar",
    "_split_comma_preserving_quotes",
    "dump_frontmatter",
    "extract_frontmatter_and_body",
    "parse_frontmatter",
    "parse_yaml_document",
    "parse_yaml_frontmatter",
    "serialize_yaml_document",
    "serialize_yaml_frontmatter",
]
