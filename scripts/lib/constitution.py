#!/usr/bin/env python3
"""Ars Arcanum Authorial Constitution & Governance Engine (`scripts/lib/constitution.py`).

Manages the Authorial Constitution, hierarchical multi-layer policy merging
(Global -> World -> Manuscript), diagnostic rule suppression, and engine switchboard.
Delegates to native `src.arcanum.core.config` while maintaining backward compatibility.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path if not present
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.arcanum.core.config import (  # noqa: E402
    DEFAULT_AUTHORIAL_POLICY,
    _deep_merge_dict,
    deep_merge_constitution,
    get_authorial_constitution,
    get_authorial_policy,
    get_disabled_engines,
    get_suppressed_rules,
    get_world_axioms,
    is_engine_enabled,
    is_rule_suppressed,
    load_authorial_constitution,
    set_authorial_policy,
    set_engine_enabled,
    set_world_axioms,
)

__all__ = [
    "DEFAULT_AUTHORIAL_POLICY",
    "_deep_merge_dict",
    "deep_merge_constitution",
    "get_authorial_constitution",
    "get_authorial_policy",
    "get_disabled_engines",
    "get_suppressed_rules",
    "get_world_axioms",
    "is_engine_enabled",
    "is_rule_suppressed",
    "load_authorial_constitution",
    "set_authorial_policy",
    "set_engine_enabled",
    "set_world_axioms",
]
