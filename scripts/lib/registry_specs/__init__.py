#!/usr/bin/env python3
"""
Ars Arcanum Domain Engine Specifications Package (scripts/lib/registry_specs)
=============================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.registry.specs.
"""
from __future__ import annotations

import sys

from src.arcanum.core.registry.specs import ALL_ENGINES

for _alias in ("registry_specs", "lib.registry_specs", "scripts.lib.registry_specs"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

__all__ = ["ALL_ENGINES"]
