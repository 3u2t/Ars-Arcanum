#!/usr/bin/env python3
"""
Ars Arcanum Centralized Data Access Layer (DAL) (scripts/lib/data_access.py)
===========================================================================
Backward-compatibility delegation wrapper forwarding to src.arcanum.core.cache.
"""

from __future__ import annotations

from src.arcanum.core.cache import (
    DataAccessLayer,
    get_data_access,
)

__all__ = ["DataAccessLayer", "get_data_access"]
