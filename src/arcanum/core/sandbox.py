"""Subprocess Capability-Sandboxed Plugin Runner for Ars Arcanum (src/arcanum/core/sandbox.py).

Executes third-party or user plugins located in `.arcanum/plugins/*.py` inside an
isolated Python subprocess (`python3 -I`) communicating strictly via JSON over stdin/stdout.
Enforces timeout bounds, output size caps, and vault root path confinement.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.arcanum.core.storage import PathSecurityError, is_safe_subpath


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
    plugin_script: Path | str,
    payload: dict[str, Any],
    *,
    allowed_roots: tuple[Path | str, ...],
    timeout_seconds: float = 5.0,
    max_stdout_bytes: int = 1_048_576,
) -> SandboxedPluginResult:
    """Execute `plugin_script` in an isolated `sys.executable -I` subprocess with a JSON payload."""
    resolved_script = Path(plugin_script).resolve()
    resolved_roots = tuple(Path(root).resolve() for root in allowed_roots)

    if not any(is_safe_subpath(root, resolved_script) for root in resolved_roots):
        raise PathSecurityError(
            f"Plugin script {resolved_script} is outside allowed plugin roots: {allowed_roots}"
        )
    if not resolved_script.exists() or resolved_script.suffix.lower() != ".py":
        raise FileNotFoundError(f"Invalid plugin script: {resolved_script}")

    input_json = json.dumps(payload, sort_keys=True)
    sanitized_env: dict[str, str] = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin") if sys.platform == "win32" else "/usr/bin:/bin",
        "PYTHONIOENCODING": "utf-8",
        "LC_ALL": "C.UTF-8",
    }
    if sys.platform == "win32":
        for k in ("SystemRoot", "WINDIR", "TEMP", "TMP"):
            if k in os.environ:
                sanitized_env[k] = os.environ[k]

    try:
        completed = subprocess.run(  # nosec B603
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


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum plugin-sandbox`."""
    parser = argparse.ArgumentParser(
        prog="arcanum plugin-sandbox",
        description="Execute a custom Ars Arcanum Python plugin in an isolated subprocess sandbox.",
    )
    parser.add_argument("plugin_script", type=Path, help="Path to plugin .py file")
    parser.add_argument("--payload", default="{}", help="JSON payload string passed to stdin")
    parser.add_argument("--allowed-root", type=Path, default=Path.cwd(), help="Allowed root directory")
    parser.add_argument("--timeout", type=float, default=5.0, help="Execution timeout in seconds")
    args = parser.parse_args(argv)

    payload_dict = json.loads(args.payload)
    res = run_plugin_sandboxed(
        args.plugin_script,
        payload_dict,
        allowed_roots=(args.allowed_root,),
        timeout_seconds=args.timeout,
    )
    sys.stdout.write(json.dumps(asdict(res), indent=2) + "\n")
    return 0


__all__ = [
    "PluginExecutionError",
    "SandboxedPluginResult",
    "main",
    "run_plugin_sandboxed",
]

if __name__ == "__main__":
    raise SystemExit(main())
