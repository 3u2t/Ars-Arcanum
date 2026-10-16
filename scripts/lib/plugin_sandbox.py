#!/usr/bin/env python3
"""Subprocess Capability-Sandboxed Plugin Runner for Ars Arcanum (scripts/lib/plugin_sandbox.py).

Delegated wrapper for native `src.arcanum.core.sandbox`.
Maintains 100% backward compatibility for all CLI invocations and imports.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for src.arcanum resolution
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.arcanum.core.sandbox as _native  # noqa: E402, F401
from src.arcanum.core.sandbox import (  # noqa: E402
    PluginExecutionError,
    SandboxedPluginResult,
    main,
    run_plugin_sandboxed,
)

# Register aliases into sys.modules so imports work seamlessly
for _alias in ("plugin_sandbox", "lib.plugin_sandbox", "scripts.lib.plugin_sandbox"):
    sys.modules[_alias] = sys.modules[__name__]

__all__ = [
    "PluginExecutionError",
    "SandboxedPluginResult",
    "main",
    "run_plugin_sandboxed",
]

if __name__ == "__main__":
    raise SystemExit(main())
