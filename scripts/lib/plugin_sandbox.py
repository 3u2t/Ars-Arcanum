"""Subprocess Capability-Sandboxed Plugin Runner for Ars Arcanum (Phase 3B Refactor).

Hardens `scripts/lib/registry.py` by executing third-party or user plugins located in
`.arcanum/plugins/*.py` inside an isolated Python subprocess (`python3 -I`) communicating
strictly via JSON over `stdin`/`stdout` with:
- Path traversal verification (`is_safe_subpath`) so only plugins inside the vault or canonical
  `configs/plugins/` directory can be invoked.
- Isolated interpreter mode (`-I`: no user site-packages or `PYTHONPATH` injection).
- Sanitized environment variables (`LC_ALL=C.UTF-8`, `PYTHONIOENCODING=utf-8`).
- Strict wall-clock execution timeout (default: `5.0` seconds) and output byte cap.

Repository Target: `scripts/lib/plugin_sandbox.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.vault_index import PathSecurityError, is_safe_subpath
except ImportError:
    from vault_index import PathSecurityError, is_safe_subpath


class PluginExecutionError(RuntimeError):
    """Raised when a sandboxed plugin times out, exits non-zero, or emits malformed JSON."""


@dataclass(frozen=True)
class SandboxedPluginResult:
    """Validated response returned from an isolated plugin subprocess."""

    plugin_name: str
    status: str
    output: dict[str, Any]
    stderr_log: str


def run_plugin_sandboxed(
    plugin_script: Path,
    payload: dict[str, Any],
    *,
    allowed_roots: tuple[Path, ...],
    timeout_seconds: float = 5.0,
    max_stdout_bytes: int = 1_048_576,
) -> SandboxedPluginResult:
    """Execute `plugin_script` in an isolated `sys.executable -I` subprocess with a JSON payload."""
    resolved_script = plugin_script.resolve()
    if not any(is_safe_subpath(root.resolve(), resolved_script) for root in allowed_roots):
        raise PathSecurityError(
            f"Plugin script {resolved_script} is outside allowed plugin roots: {allowed_roots}"
        )
    if not resolved_script.exists() or resolved_script.suffix.lower() != ".py":
        raise FileNotFoundError(f"Invalid plugin script: {resolved_script}")

    input_json = json.dumps(payload, sort_keys=True)
    sanitized_env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONIOENCODING": "utf-8",
        "LC_ALL": "C.UTF-8",
    }

    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(resolved_script)],
            input=input_json,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=sanitized_env,
            cwd=str(resolved_script.parent),
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PluginExecutionError(
            f"Plugin '{resolved_script.stem}' exceeded timeout of {timeout_seconds}s"
        ) from exc

    if completed.returncode != 0:
        raise PluginExecutionError(
            f"Plugin '{resolved_script.stem}' failed with exit code {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )

    raw_out = completed.stdout
    if len(raw_out.encode("utf-8")) > max_stdout_bytes:
        raise PluginExecutionError(
            f"Plugin '{resolved_script.stem}' output exceeded {max_stdout_bytes} byte limit."
        )

    try:
        parsed = json.loads(raw_out) if raw_out.strip() else {}
        if not isinstance(parsed, dict):
            raise ValueError("Top-level JSON output must be an object.")
    except Exception as exc:
        raise PluginExecutionError(
            f"Plugin '{resolved_script.stem}' returned invalid JSON: {exc}"
        ) from exc

    return SandboxedPluginResult(
        plugin_name=resolved_script.stem,
        status=str(parsed.get("status", "ok")),
        output=parsed,
        stderr_log=completed.stderr.strip(),
    )
