#!/usr/bin/env python3
"""
Ars Arcanum Modular Front & Back Matter Publishing Builder
(scripts/lib/frontmatter_builder.py)
================================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.frontmatter.
"""

from __future__ import annotations

import sys

from src.arcanum.core.frontmatter import (
    generate_backmatter_modules,
    generate_frontmatter_modules,
    scaffold_matter,
)
from src.arcanum.core.frontmatter import (
    main_matter as main,
)

__all__ = [
    "generate_backmatter_modules",
    "generate_frontmatter_modules",
    "main",
    "scaffold_matter",
]

if __name__ == "__main__":
    sys.exit(main())
