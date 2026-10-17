"""Zero-Pip Multi-Threaded Daemon for Ars Arcanum Local Studio (`arcanum studio`).

Runs locally on `127.0.0.1:4242` using Python standard library `http.server.ThreadingHTTPServer`.
Sovereign, air-gapped, and zero-telemetry.
"""

from __future__ import annotations

import argparse
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import webbrowser

try:
    from .handlers import ArcanumStudioHandler
except (ImportError, ValueError):
    try:
        from src.arcanum.server.handlers import ArcanumStudioHandler
    except ImportError:
        from arcanum.server.handlers import ArcanumStudioHandler


def create_studio_server(
    vault_root: Path,
    port: int = 4242,
    session_token: str | None = None,
) -> ThreadingHTTPServer:
    """Create and configure a local ThreadingHTTPServer instance for `vault_root`."""
    resolved_root = vault_root.resolve()
    ArcanumStudioHandler.vault_root = resolved_root
    ArcanumStudioHandler.session_token = session_token
    return ThreadingHTTPServer(("127.0.0.1", port), ArcanumStudioHandler)


def start_studio_daemon(
    vault_root: Path,
    port: int = 4242,
    open_browser: bool = False,
    block: bool = True,
    session_token: str | None = None,
) -> ThreadingHTTPServer:
    """Start the local Arcanum Studio web server."""
    server = create_studio_server(vault_root, port=port, session_token=session_token)
    url = f"http://127.0.0.1:{port}"

    sys.stdout.write(f"\n✨ Ars Arcanum Visual Studio Cockpit live at: {url}\n")
    sys.stdout.write(f"📁 Sovereign Vault Root: {vault_root.resolve()}\n")
    if session_token:
        sys.stdout.write("🔒 Session Token Security: Active (X-Arcanum-Token required)\n")
    sys.stdout.write("Press Ctrl+C to stop the local studio server.\n\n")

    if open_browser:
        webbrowser.open(url)

    if block:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            sys.stdout.write("\nShutting down Ars Arcanum Studio.\n")
            server.shutdown()
            server.server_close()
    else:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

    return server


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum studio`."""
    parser = argparse.ArgumentParser(
        prog="arcanum studio",
        description="Launch sovereign local web studio and visual continuity cockpit.",
    )
    parser.add_argument("vault", nargs="?", type=Path, default=Path.cwd(), help="Vault or manuscript directory")
    parser.add_argument("--port", type=int, default=4242, help="Local port (default: 4242)")
    parser.add_argument("--token", default=None, help="Optional ephemeral session token for API authorization")
    parser.add_argument("--open", dest="open_browser", action="store_true", default=True, help="Open browser automatically")
    parser.add_argument("--no-open", dest="open_browser", action="store_false", help="Do not open browser")
    args = parser.parse_args(argv)

    try:
        start_studio_daemon(
            args.vault,
            port=args.port,
            open_browser=args.open_browser,
            block=True,
            session_token=args.token,
        )
        return 0
    except OSError as e:
        sys.stderr.write(f"Error starting studio server on port {args.port}: {e}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
