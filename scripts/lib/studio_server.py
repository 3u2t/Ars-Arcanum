"""Sovereign Studio Web Server CLI compatibility bridge."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.arcanum.server.daemon import main, start_studio_daemon  # noqa: E402

__all__ = ["main", "start_studio_daemon"]

if __name__ == "__main__":
    raise SystemExit(main())
