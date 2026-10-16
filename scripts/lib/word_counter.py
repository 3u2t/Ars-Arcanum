#!/usr/bin/env python3
"""
Ars Arcanum Unicode Prose Word Count & Manuscript Telemetry (scripts/lib/word_counter.py)
========================================================================================
Legacy compatibility facade delegating to src.arcanum.manuscript.word_counter.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import src.arcanum.manuscript.word_counter as _native_wc  # noqa: E402
from src.arcanum.manuscript.word_counter import (  # noqa: E402
    analyze_manuscript_words,
    count_prose_words_advanced,
    count_words_prose,
    format_words_markdown,
    format_words_table,
    main,
)


def _is_interactive_tty() -> bool:
    """Return True if stdout is an interactive terminal supporting ANSI escape codes."""
    return _native_wc._is_interactive_tty()


def format_ansi_velocity(percent: float, text: str) -> str:
    """Format text with an ANSI color gradient if interactive TTY, else plain text."""
    if not _is_interactive_tty():
        return text
    if percent >= 100.0:
        return f"\033[1;32m{text}\033[0m"
    if percent >= 75.0:
        return f"\033[32m{text}\033[0m"
    if percent >= 50.0:
        return f"\033[33m{text}\033[0m"
    if percent >= 25.0:
        return f"\033[38;5;208m{text}\033[0m"
    return f"\033[31m{text}\033[0m"


__all__ = [
    "_is_interactive_tty",
    "analyze_manuscript_words",
    "count_prose_words_advanced",
    "count_words_prose",
    "format_ansi_velocity",
    "format_words_markdown",
    "format_words_table",
    "main",
]

if __name__ == "__main__":
    sys.exit(main())
