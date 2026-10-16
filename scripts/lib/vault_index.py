#!/usr/bin/env python3
"""
Unified VaultIndex and Inverted Document DAL for Ars Arcanum (scripts/lib/vault_index.py)
========================================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.indexer.
"""

from __future__ import annotations

import sys

from src.arcanum.core.indexer import (
    CACHE_VERSION,
    DEFAULT_EXCLUDED_DIRS,
    ProseMetrics,
    VaultDocumentNode,
    VaultIndex,
    WikilinkRef,
    compute_prose_metrics,
    main,
    parse_frontmatter,
)
from src.arcanum.core.storage import PathSecurityError, atomic_write, is_safe_subpath

for _alias in ("vault_index", "lib.vault_index", "scripts.lib.vault_index"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = [
    "CACHE_VERSION",
    "DEFAULT_EXCLUDED_DIRS",
    "PathSecurityError",
    "ProseMetrics",
    "VaultDocumentNode",
    "VaultIndex",
    "WikilinkRef",
    "atomic_write",
    "compute_prose_metrics",
    "is_safe_subpath",
    "main",
    "parse_frontmatter",
]

if __name__ == "__main__":
    raise SystemExit(main())
