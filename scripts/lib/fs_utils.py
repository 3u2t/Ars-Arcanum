#!/usr/bin/env python3
"""Ars Arcanum Filesystem & Atomic Storage Utilities (`scripts/lib/fs_utils.py`).

Provides crash-resilient transactional file writes and secure directory operations.
Delegates to native `src.arcanum.core.storage` while maintaining backward compatibility.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Add repo root to sys.path if not present
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from src.arcanum.core.storage import (
        WINDOWS_RESERVED_NAMES,
        PathSecurityError,
        atomic_write,
        is_safe_subpath,
        sanitize_identifier,
    )
except ImportError:
    import tempfile
    import time

    class PathSecurityError(PermissionError):  # type: ignore[no-redef]
        """Raised when a candidate path attempts to escape the sovereign vault root."""

    def is_safe_subpath(root: Path | str, candidate: Path | str) -> bool:  # type: ignore[no-redef]
        try:
            resolved_root = Path(root).resolve(strict=False)
            resolved_candidate = Path(candidate).resolve(strict=False)
            return resolved_candidate == resolved_root or resolved_root in resolved_candidate.parents
        except (OSError, RuntimeError, ValueError):
            return False

    def atomic_write(path: Path | str, data: str | bytes, encoding: str = "utf-8") -> None:  # type: ignore[no-redef]
        target = Path(path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        is_bytes = isinstance(data, (bytes, bytearray))
        mode = "wb" if is_bytes else "w"
        prefix = f".{target.name}."
        fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, prefix=prefix, suffix=".tmp")
        tmp_path = Path(tmp_path_str)
        fd_closed = False
        try:
            try:
                if is_bytes:
                    with os.fdopen(fd, mode) as f:
                        fd_closed = True
                        f.write(data)
                        f.flush()
                        os.fsync(f.fileno())
                else:
                    with os.fdopen(fd, mode, encoding=encoding, newline="") as f:
                        fd_closed = True
                        f.write(data)
                        f.flush()
                        os.fsync(f.fileno())
            finally:
                if not fd_closed:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            if target.exists():
                try:
                    os.chmod(tmp_path, target.stat().st_mode & 0o7777)
                except OSError:
                    pass
            for attempt in range(5):
                try:
                    os.replace(tmp_path, target)
                    break
                except PermissionError:
                    if attempt == 4 or sys.platform != "win32":
                        raise
                    time.sleep(0.02 * (2**attempt))
            if hasattr(os, "O_DIRECTORY"):
                try:
                    dfd = os.open(str(target.parent), os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(dfd)
                    finally:
                        os.close(dfd)
                except Exception:
                    pass
        except BaseException:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass
            raise

    WINDOWS_RESERVED_NAMES = frozenset({  # type: ignore[no-redef]
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    })

    def sanitize_identifier(name: str, fallback: str = "item") -> str:  # type: ignore[no-redef]
        if not name:
            return fallback
        import re
        base = str(name).split(".")[0].upper()
        if base in WINDOWS_RESERVED_NAMES:
            return fallback
        safe = re.sub(r"[^A-Za-z0-9_-]", "", str(name))
        if not safe or safe.split(".")[0].upper() in WINDOWS_RESERVED_NAMES or safe.upper() in WINDOWS_RESERVED_NAMES:
            return fallback
        return safe


def check_filesystem(target_dir: Path | str | None = None) -> dict[str, Any]:
    """Runs diagnostics on filesystem write safety and atomic replacement guarantees.

    Calls atomic_write within this module's namespace to respect test mock patching.
    """
    base = Path(target_dir).resolve() if target_dir else Path.cwd()
    base.mkdir(parents=True, exist_ok=True)
    test_file = base / ".arcanum_fs_test.tmp"
    test_content = "Ars Arcanum Atomic Write Test\n"

    try:
        atomic_write(test_file, test_content)
        read_back = test_file.read_text(encoding="utf-8")
        is_match = read_back == test_content
        test_file.unlink(missing_ok=True)
        return {
            "path": str(base),
            "atomic_write": True,
            "atomic_write_verified": is_match,
            "integrity_verified": is_match,
            "status": "healthy" if is_match else "corrupted",
            "posix_fsync_supported": hasattr(os, "O_DIRECTORY"),
        }
    except Exception as exc:
        test_file.unlink(missing_ok=True)
        return {
            "path": str(base),
            "atomic_write": False,
            "atomic_write_verified": False,
            "integrity_verified": False,
            "status": "error",
            "error": str(exc),
            "posix_fsync_supported": hasattr(os, "O_DIRECTORY"),
        }


def main(argv: list[str] | None = None) -> int:
    """CLI diagnostic entry point for atomic filesystem guarantees."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        prog="arcanum fs",
        description="Atomic Storage & Filesystem Diagnostic Utility",
    )
    parser.add_argument("target", nargs="?", default=".", help="Target directory for filesystem audit")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON status")
    parser.add_argument("--check", action="store_true", help="Verify atomic write integrity")

    args = parser.parse_args(argv)
    res = check_filesystem(args.target)

    if args.json:
        print(json.dumps(res, indent=2))
        return 0 if res.get("atomic_write_verified") else 1

    print("Ars Arcanum Atomic Filesystem Diagnostics")
    print("=" * 55)
    print(f"Target Directory     : {res['path']}")
    print(f"Atomic Write Status  : {'✓ PASSED' if res.get('atomic_write_verified') else '✗ FAILED'}")
    print(
        f"Parent Directory Fsync: {'Supported (POSIX)' if res.get('posix_fsync_supported') else 'Emulated (Windows / Fallback)'}"
    )
    if res.get("error"):
        print(f"Error Detail         : {res['error']}")
    return 0 if res.get("atomic_write_verified") else 1


__all__ = [
    "PathSecurityError",
    "WINDOWS_RESERVED_NAMES",
    "atomic_write",
    "check_filesystem",
    "is_safe_subpath",
    "main",
    "sanitize_identifier",
]


if __name__ == "__main__":
    sys.exit(main())
