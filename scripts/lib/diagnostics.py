#!/usr/bin/env python3
"""
Ars Arcanum System Diagnostics & Bug Triage Engine (scripts/lib/diagnostics.py)
=============================================================================
Legacy compatibility facade delegating to src.arcanum.core.diagnostics.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

VERSION = "0.1.0"

from src.arcanum.core.diagnostics import (  # noqa: E402
    format_diagnostic_report_markdown,
    generate_diagnostic_report,
    get_command_version,
    get_state_dir,
    get_toolchain_diagnostics,
    main,
    redact_sensitive_paths,
    run_doctor_report,
    setup_logging,
)

__all__ = [
    "VERSION",
    "format_diagnostic_report_markdown",
    "generate_diagnostic_report",
    "get_command_version",
    "get_state_dir",
    "get_toolchain_diagnostics",
    "main",
    "redact_sensitive_paths",
    "run_doctor_report",
    "setup_logging",
]

if __name__ == "__main__":
    sys.exit(main())
