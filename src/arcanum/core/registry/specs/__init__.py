#!/usr/bin/env python3
"""
Ars Arcanum Domain Engine Specifications Package (src/arcanum/core/registry/specs)
==================================================================================
Aggregates domain-specific EngineSpec definitions for the 17 retained core and craft engines.
"""
from __future__ import annotations

from src.arcanum.core.registry.specs.domain_editorial import ENGINES as ENGINES_EDITORIAL
from src.arcanum.core.registry.specs.domain_infrastructure import ENGINES as ENGINES_INFRASTRUCTURE
from src.arcanum.core.registry.specs.domain_portfolio import ENGINES as ENGINES_PORTFOLIO
from src.arcanum.core.registry.specs.domain_publishing import ENGINES as ENGINES_PUBLISHING

ALL_ENGINES = {
    **ENGINES_EDITORIAL,
    **ENGINES_PORTFOLIO,
    **ENGINES_INFRASTRUCTURE,
    **ENGINES_PUBLISHING,
}

__all__ = ["ALL_ENGINES"]
