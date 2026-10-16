"""Unified CLI bridge for `arcanum-lite` and `lite-check` (`src/arcanum/cli_bridge.py`)."""

from __future__ import annotations

from scripts.lib.audit_hardening import build_lite_parser, main_lite

__all__ = ["build_lite_parser", "main_lite"]

if __name__ == "__main__":
    raise SystemExit(main_lite())
